import asyncio
import datetime
import json
import logging
import os
from typing import Any, Dict, List, Optional

import aiosqlite
import firebase_admin
# from firebase_admin import credentials # Unused
from google.cloud import bigquery, firestore

logger = logging.getLogger(__name__)

DB_PATH = "loredb.sqlite"


class LoreDB:
    """
    Local Memory Store backed by SQLite.
    Handles persistent storage of agent memories and sync status.
    """
    _instance = None
    db_path: str = DB_PATH

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(LoreDB, cls).__new__(cls)
            cls._instance.db_path = DB_PATH
        return cls._instance

    async def init_db(self):
        """Initialize the database schema."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS memories (
                    id TEXT PRIMARY KEY,
                    content TEXT NOT NULL,
                    source TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    sync_status TEXT DEFAULT 'pending',
                    remote_id TEXT,
                    metadata JSON
                );
            """)
            await db.execute("""
                CREATE INDEX IF NOT EXISTS idx_sync_status ON memories(sync_status);
            """)
            await db.execute("""
                CREATE INDEX IF NOT EXISTS idx_created_at ON memories(created_at DESC);
            """)
            await db.commit()
            logger.info("LoreDB initialized at %s", self.db_path)

    async def sync_memory(self, memory_id: str, content: str,
                          source: str, metadata: Dict[str, Any]):
        """Dispatcher to sync memory to remote remote destinations."""
        # 1. Firestore (Hot Memory) - High Priority
        asyncio.create_task(self._sync_firestore(memory_id, content, source, metadata))

        # 2. BigQuery (Cold Memory) - Async Archival
        asyncio.create_task(self._sync_bigquery(memory_id, content, source, metadata))

        # 3. Notion (Human Memory) - Curated for readability
        asyncio.create_task(self._sync_notion(memory_id, content, source, metadata))

    async def _sync_notion(self, memory_id: str, content: str, source: str, metadata: Dict[str, Any]):
        """Sync memory to Notion Database."""
        try:
            from notion_client import Client
            token = os.environ.get("NOTION_OBSERVATORY_SECRET")
            # Default to a specific DB ID for memories or fallback to generic env
            database_id = os.environ.get("NOTION_MEMORY_DB_ID")

            if not token or not database_id:
                # Silent skip if not configured, as Notion is optional/human-layer
                logger.debug("Skipping Notion Sync: Token or DB ID missing.")
                return

            notion = Client(auth=token)

            # Create a new page in the Memories database
            # Truncate title if content is long
            title = content[:100] + "..." if len(content) > 100 else content

            properties = {
                "Name": {"title": [{"text": {"content": title}}]},
                "ID": {"rich_text": [{"text": {"content": memory_id}}]},
                "Source": {"select": {"name": source}},
                # "Created": {"date": {"start": datetime.datetime.now().isoformat()}}
            }

            # Append content as children blocks
            children = [
                {
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [{"type": "text", "text": {"content": content}}]
                    }
                }
            ]

            response = await asyncio.to_thread(
                notion.pages.create,
                parent={"database_id": database_id},
                properties=properties,
                children=children
            )

            logger.info(f"✅ Synced memory {memory_id} to Notion (Page ID: {response['id']}).")

        except Exception as e:
            logger.error(f"❌ Notion Sync Failed for {memory_id}: {e}")
            # We don't mark as 'failed' global sync status because Notion is secondary

    async def _sync_firestore(self, memory_id: str, content: str,
                              source: str, metadata: Dict[str, Any]):
        """Sync memory to Google Cloud Firestore."""
        try:
            # Check if Firestore client is available via firebase_admin or google.cloud
            # We use the PROJECT_ID from env
            project_id = os.environ.get("GOOGLE_CLOUD_PROJECT")
            if not project_id:
                logger.warning("Skipping Firestore Sync: GOOGLE_CLOUD_PROJECT not set.")
                return

            # Init client (lightweight if reusing connection pool)
            db = firestore.Client(project=project_id)

            doc_ref = db.collection("memories").document(memory_id)
            doc_ref.set({
                "id": memory_id,
                "content": content,
                "source": source,
                "created_at": firestore.SERVER_TIMESTAMP,
                "metadata": metadata
            })

            # Update local status to synced
            await self.update_sync_status(memory_id, "synced", remote_id=doc_ref.path)
            logger.info(f"✅ Synced memory {memory_id} to Firestore.")

        except Exception as e:
            logger.error(f"❌ Firestore Sync Failed for {memory_id}: {e}")
            await self.update_sync_status(memory_id, "failed_firestore")

    async def _sync_bigquery(self, memory_id: str, content: str,
                             source: str, metadata: Dict[str, Any]):
        """Sync memory to Google BigQuery."""
        try:
            project_id = os.environ.get("GOOGLE_CLOUD_PROJECT")
            if not project_id:
                logger.warning("Skipping BigQuery Sync: GOOGLE_CLOUD_PROJECT not set.")
                return

            client = bigquery.Client(project=project_id)
            table_id = f"{project_id}.analytics.memories"  # Assumes 'analytics' dataset exists

            rows_to_insert = [{
                "id": memory_id,
                "content": content,
                "source": source,
                "metadata": json.dumps(metadata),
                "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat()
            }]

            errors = client.insert_rows_json(table_id, rows_to_insert)
            if errors == []:
                logger.info(f"✅ Synced memory {memory_id} to BigQuery.")
            else:
                logger.error(f"❌ BigQuery Sync Errors for {memory_id}: {errors}")

        except Exception as e:
            # Don't fail hard if BQ is missing, just log
            logger.warning(f"⚠️ BigQuery Sync Skipped/Failed for {memory_id}: {e}")

    async def add_memory(self, content: str, source: str = "user",
                         metadata: Dict[str, Any] = None) -> str:
        """
        Add a new memory to the local store and trigger async sync.
        Returns the local ID of the memory.
        """
        import uuid
        memory_id = str(uuid.uuid4())
        metadata_json = json.dumps(metadata or {})

        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """
                INSERT INTO memories (id, content, source, sync_status, metadata)
                VALUES (?, ?, ?, 'pending', ?)
                """,
                (memory_id, content, source, metadata_json)
            )
            await db.commit()
            logger.debug("Memory added to LoreDB: %s", memory_id)

        # Trigger Async Sync
        await self.sync_memory(memory_id, content, source, metadata or {})

        return memory_id

    async def get_recent_memories(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Retrieve the most recent memories."""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                "SELECT * FROM memories ORDER BY created_at DESC LIMIT ?",
                (limit,)
            )
            rows = await cursor.fetchall()

            memories = []
            for row in rows:
                memories.append({
                    "id": row["id"],
                    "content": row["content"],
                    "source": row["source"],
                    "created_at": row["created_at"],
                    "sync_status": row["sync_status"],
                    "metadata": json.loads(row["metadata"] or "{}")
                })
            return memories

    async def search_memories(self, query: str) -> List[Dict[str, Any]]:
        """
        Basic semantic search stub (MVP implementation uses LIKE).
        Real implementation would use vector search or FTS5.
        """
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            wildcard_query = f"%{query}%"
            cursor = await db.execute(
                "SELECT * FROM memories WHERE content LIKE ? ORDER BY created_at DESC LIMIT 20",
                (wildcard_query,)
            )
            rows = await cursor.fetchall()

            memories = []
            for row in rows:
                memories.append({
                    "id": row["id"],
                    "content": row["content"],
                    "source": row["source"],
                    "created_at": row["created_at"],
                    "sync_status": row["sync_status"],
                    "metadata": json.loads(row["metadata"] or "{}")
                })
            return memories

    async def get_pending_sync(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get memories waiting to be synced to remote."""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                "SELECT * FROM memories WHERE sync_status = 'pending' LIMIT ?",
                (limit,)
            )
            rows = await cursor.fetchall()

            memories = []
            for row in rows:
                memories.append({
                    "id": row["id"],
                    "content": row["content"],
                    "metadata": json.loads(row["metadata"] or "{}")
                })
            return memories

    async def update_sync_status(self, memory_id: str, status: str,
                                 remote_id: Optional[str] = None):
        """Update the sync status of a memory."""
        async with aiosqlite.connect(self.db_path) as db:
            if remote_id:
                await db.execute(
                    "UPDATE memories SET sync_status = ?, remote_id = ? WHERE id = ?",
                    (status, remote_id, memory_id)
                )
            else:
                await db.execute(
                    "UPDATE memories SET sync_status = ? WHERE id = ?",
                    (status, memory_id)
                )
            await db.commit()


# Global instance
loredb = LoreDB()
