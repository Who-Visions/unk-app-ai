# pylint: disable=duplicate-code
"""
BigQuery Vector Store Tool
==========================
Handles storage and retrieval of vector embeddings in BigQuery.
"""

import json
import os
import uuid
from typing import Any, Dict, List

from google.cloud import aiplatform, bigquery


class BigQueryVectorStore:
    """BigQuery-based Vector Store for unk-app-ai."""

    def __init__(self, project_id: str, location: str):
        self.project_id = project_id
        self.location = location
        self.client = bigquery.Client(project=project_id)
        self.dataset_id = "dav1d_memory"
        self.table_id = "embeddings"

        # Initialize Vertex AI for embeddings if needed
        aiplatform.init(project=project_id, location=location)

    def initialize_dataset(self):
        """Ensures the dataset and table exist."""
        dataset_ref = self.client.dataset(self.dataset_id)
        try:
            self.client.get_dataset(dataset_ref)
            print(f"Dataset {self.dataset_id} already exists.")
        except Exception: # pylint: disable=broad-exception-caught
            dataset = bigquery.Dataset(dataset_ref)
            dataset.location = self.location
            self.client.create_dataset(dataset)
            print(f"Created dataset {self.dataset_id}.")

        table_ref = dataset_ref.table(self.table_id)
        try:
            self.client.get_table(table_ref)
            print(f"Table {self.table_id} already exists.")
        except Exception: # pylint: disable=broad-exception-caught
            schema = [
                bigquery.SchemaField("id", "STRING", mode="REQUIRED"),
                bigquery.SchemaField("content", "STRING", mode="REQUIRED"),
                bigquery.SchemaField("metadata", "JSON", mode="NULLABLE"),
                bigquery.SchemaField("embedding", "FLOAT64", mode="REPEATED"),
            ]
            table = bigquery.Table(table_ref, schema=schema)
            self.client.create_table(table)
            print(f"Created table {self.table_id}.")

    def get_embedding(self, text: str) -> List[float]:
        """Generates embedding using Gen AI SDK."""
        from google import genai  # pylint: disable=import-outside-toplevel
        from tenacity import retry, wait_exponential, stop_after_attempt, retry_if_exception
        import time

        # Initialize Gen AI client
        client = genai.Client(vertexai=True, project=self.project_id, location=self.location)

        def is_retryable(e):
            return "429" in str(e) or "Quota" in str(e) or "ResourceExhausted" in str(e)

        @retry(
            retry=retry_if_exception(is_retryable),
            wait=wait_exponential(multiplier=2, min=20, max=120),
            stop=stop_after_attempt(5)
        )
        def _generate_with_model(model_name):
            return client.models.embed_content(
                model=model_name,
                contents=text
            ).embeddings[0].values

        try:
            # Try standard stable model first (text-embedding-004)
            result = _generate_with_model("text-embedding-004")
            time.sleep(10) # Ultra-conservative safety delay (User request: No 429s)
            return result
        except Exception as e:  # pylint: disable=W0718
            if is_retryable(e):
                print(
                    "⚠️ Primary embedding model rate limited. "
                    "Falling back to gemini-embedding-001..."
                )
                # Fallback to newer model which might have separate quota
                try:
                    result = _generate_with_model("gemini-embedding-001")
                    time.sleep(10) # Ultra-conservative safety delay
                    return result
                except Exception as e2:  # pylint: disable=W0718
                    print(f"❌ Fallback embedding model also failed: {e2}")
                    raise e2
            raise e

    def add_memory(self, text: str, metadata: Dict[str, Any] = None):
        """Adds a text memory with its embedding to BigQuery."""
        embedding = self.get_embedding(text)
        row = {
            "id": str(uuid.uuid4()),
            "content": text,
            "metadata": json.dumps(metadata) if metadata else None,
            "embedding": embedding
        }

        errors = self.client.insert_rows_json(
            f"{self.project_id}.{self.dataset_id}.{self.table_id}",
            [row]
        )
        if errors:
            print(f"Encountered errors while inserting rows: {errors}")
        else:
            print("Memory added successfully.")

    def search_similar(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Searches for similar memories using vector search."""
        query_embedding = self.get_embedding(query)

        # SQL for vector search using cosine distance
        sql = f"""
        SELECT
            id,
            content,
            metadata,
            1 - COSINE_DISTANCE(embedding, {query_embedding}) as similarity
        FROM
            `{self.project_id}.{self.dataset_id}.{self.table_id}`
        ORDER BY
            similarity DESC
        LIMIT {limit}
        """

        query_job = self.client.query(sql)
        results = []
        for row in query_job:
            results.append({
                "id": row.id,
                "content": row.content,
                "metadata": row.metadata,
                "similarity": row.similarity
            })
        return results

    def get_existing_video_ids(self) -> set:
        """Retrieves a set of video_ids that have already been ingested."""
        try:
            # Check if table exists first prevents 404
            table_ref = self.client.dataset(self.dataset_id).table(self.table_id)
            self.client.get_table(table_ref)

            sql = f"""
            SELECT DISTINCT JSON_VALUE(metadata, '$.video_id') as video_id
            FROM `{self.project_id}.{self.dataset_id}.{self.table_id}`
            """
            query_job = self.client.query(sql)
            return {row.video_id for row in query_job if row.video_id}
        except Exception as e:  # pylint: disable=W0718
            # Table might not exist yet or other error
            print(f"⚠️ Could not fetch existing video IDs (starting fresh?): {e}")
            return set()

# Tool function wrapper
def search_codebase_semantically(query: str) -> str:
    """
    Searches the codebase/memory semantically using BigQuery Vector Search.
    Useful for finding code patterns, understanding context, or recalling past decisions.
    """
    project_id = os.getenv("GOOGLE_CLOUD_PROJECT")
    location = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")

    if not project_id:
        return "Error: PROJECT_ID environment variable not set."

    store = BigQueryVectorStore(project_id, location)
    # Ensure initialized (lazy init)
    # store.initialize_dataset() # Commented out to avoid overhead on every search

    results = store.search_similar(query)

    if not results:
        return "No relevant memories found."

    output = "Found relevant memories:\n"
    for r in results:
        output += f"- [Similarity: {r['similarity']:.2f}] {r['content'][:200]}...\n"
        if r['metadata']:
            output += f"  Metadata: {r['metadata']}\n"

    return output
