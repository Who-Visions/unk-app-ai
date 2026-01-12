"""
Thread Persistence Layer
========================
Handles saving and loading Thread state to/from storage (Firestore).
Falls back to local file storage if Firestore is not available.
"""

import json
import logging
import os
from typing import Optional
from .models import Thread

logger = logging.getLogger("thread_runner.persistence")

# Placeholder for Firestore client
firestore_client = None

try:
    from google.cloud import firestore
    # Check if we should initialize (only if project ID is set)
    if os.environ.get("GOOGLE_CLOUD_PROJECT"):
         # Lazy init in actual use usually, but here checking library availability
         pass
except ImportError:
    pass

class ThreadStore:
    def __init__(self):
        self.use_firestore = False
        self.local_dir = "threads_db"
        if not os.path.exists(self.local_dir):
            os.makedirs(self.local_dir)

        # Try to init Firestore
        if os.environ.get("GOOGLE_CLOUD_PROJECT") and 'firestore' in globals():
            try:
                global firestore_client
                if not firestore_client:
                    firestore_client = firestore.Client()
                self.use_firestore = True
                self.db = firestore_client
                self.collection = self.db.collection("threads")
                logger.info("✅ ThreadStore: Using Firestore")
            except Exception as e:  # pylint: disable=W0718
                logger.warning(f"⚠️ ThreadStore: Firestore init failed ({e}), falling back to local files.")
        else:
            logger.info("ℹ️ ThreadStore: Using Local File Storage")

    async def save_thread(self, thread: Thread):
        """Saves a thread state."""
        data = thread.dict()
        # Convert datetime objects to string if using JSON
        data["created_at"] = data["created_at"].isoformat()
        if data["updated_at"]:
            data["updated_at"] = data["updated_at"].isoformat()

        if self.use_firestore:
            try:
                # Firestore handles datetime, but Pydantic .dict() might need robust serialization
                # For simplicity, we save the dict directly.
                doc_ref = self.collection.document(thread.thread_id)
                doc_ref.set(data)
                return
            except Exception as e:  # pylint: disable=W0718
                logger.error(f"Firestore save error: {e}")
                # Fallback to local

        # Local Save
        path = os.path.join(self.local_dir, f"{thread.thread_id}.json")
        with open(path, "w") as f:
            json.dump(data, f, indent=2, default=str)

    async def load_thread(self, thread_id: str) -> Optional[Thread]:
        """Loads a thread by ID."""
        if self.use_firestore:
            try:
                doc = self.collection.document(thread_id).get()
                if doc.exists:
                    data = doc.to_dict()
                    return Thread(**data)
            except Exception as e:  # pylint: disable=W0718
                 logger.error(f"Firestore load error: {e}")

        # Local Load
        path = os.path.join(self.local_dir, f"{thread_id}.json")
        if os.path.exists(path):
             with open(path, "r") as f:
                data = json.load(f)
                return Thread(**data)
        return None

store = ThreadStore()
