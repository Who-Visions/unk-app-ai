# gemini_agent/memory.py
"""
Vector Memory System
=====================
Cognitive persistence layer using Firestore Vector Search.
Enables RAG and long-term memory for the Unk Agent.

Who Visions LLC - AI with Dav3
"""

import os
import asyncio
from datetime import datetime
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum

from google.cloud import firestore
from google.cloud.firestore_v1.vector import Vector
from google.cloud.firestore_v1.base_vector_query import DistanceMeasure
from google import genai


class MemoryType(str, Enum):
    """Categories of memory for retrieval filtering."""
    FACT = "fact"
    PROCEDURE = "procedure"
    EPISODIC = "episodic"
    SEMANTIC = "semantic"
    USER_PREFERENCE = "user_preference"
    SYSTEM_KNOWLEDGE = "system_knowledge"


@dataclass
class MemoryEntry:
    """Structured memory entry."""
    content: str
    memory_type: MemoryType
    metadata: Dict[str, Any]
    embedding: Optional[List[float]] = None
    timestamp: Optional[datetime] = None
    similarity_score: Optional[float] = None
    document_id: Optional[str] = None


class VectorMemory:
    """
    Firestore-backed vector memory system.
    
    Features:
    - Semantic search with cosine similarity
    - Memory type filtering
    - User-scoped memories
    - Batch operations
    """
    
    # Firestore vector dimensionality limit
    MAX_DIMENSIONS = 2048
    
    def __init__(
        self,
        project_id: Optional[str] = None,
        collection_name: str = "unk_memory",
        embedding_model: str = "text-embedding-004"
    ):
        """
        Initialize the vector memory system.
        
        Args:
            project_id: GCP project ID
            collection_name: Firestore collection for memories
            embedding_model: Model for generating embeddings
        """
        self.project_id = project_id or os.environ.get("GOOGLE_CLOUD_PROJECT")
        self.collection_name = collection_name
        self.embedding_model = embedding_model
        
        # Initialize Firestore client
        self.db = firestore.Client(project=self.project_id)
        
        # Initialize GenAI client for embeddings
        self.genai_client = genai.Client(
            vertexai=True,
            project=self.project_id,
            location="us-central1"
        )
        
    def _generate_embedding(self, text: str) -> List[float]:
        """
        Generate vector embedding for text.
        
        Args:
            text: Text to embed
            
        Returns:
            List of floats representing the embedding vector
        """
        result = self.genai_client.models.embed_content(
            model=self.embedding_model,
            contents=text
        )
        
        embedding = result.embeddings[0].values
        
        # Validate dimensions
        if len(embedding) > self.MAX_DIMENSIONS:
            raise ValueError(
                f"Embedding dimensions ({len(embedding)}) exceed "
                f"Firestore limit ({self.MAX_DIMENSIONS})"
            )
            
        return embedding
        
    async def _generate_embedding_async(self, text: str) -> List[float]:
        """Async wrapper for embedding generation."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None, 
            self._generate_embedding, 
            text
        )
        
    def store_memory(
        self,
        content: str,
        memory_type: MemoryType = MemoryType.FACT,
        metadata: Optional[Dict[str, Any]] = None,
        user_id: Optional[str] = None
    ) -> str:
        """
        Store a memory with its vector embedding.
        
        Args:
            content: The text content to store
            memory_type: Category of this memory
            metadata: Additional metadata to store
            user_id: Optional user scope
            
        Returns:
            Document ID of the stored memory
        """
        embedding = self._generate_embedding(content)
        
        doc_data = {
            "content": content,
            "embedding": Vector(embedding),
            "memory_type": memory_type.value,
            "user_id": user_id,
            "metadata": metadata or {},
            "created_at": firestore.SERVER_TIMESTAMP,
            "updated_at": firestore.SERVER_TIMESTAMP
        }
        
        doc_ref = self.db.collection(self.collection_name).add(doc_data)
        return doc_ref[1].id
        
    async def store_memory_async(
        self,
        content: str,
        memory_type: MemoryType = MemoryType.FACT,
        metadata: Optional[Dict[str, Any]] = None,
        user_id: Optional[str] = None
    ) -> str:
        """Async version of store_memory."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            lambda: self.store_memory(content, memory_type, metadata, user_id)
        )
        
    def store_batch(
        self,
        entries: List[MemoryEntry],
        user_id: Optional[str] = None
    ) -> List[str]:
        """
        Store multiple memories in a batch.
        
        Args:
            entries: List of MemoryEntry objects
            user_id: Optional user scope for all entries
            
        Returns:
            List of document IDs
        """
        batch = self.db.batch()
        doc_ids = []
        
        for entry in entries:
            embedding = self._generate_embedding(entry.content)
            
            doc_ref = self.db.collection(self.collection_name).document()
            doc_ids.append(doc_ref.id)
            
            batch.set(doc_ref, {
                "content": entry.content,
                "embedding": Vector(embedding),
                "memory_type": entry.memory_type.value,
                "user_id": user_id,
                "metadata": entry.metadata,
                "created_at": firestore.SERVER_TIMESTAMP,
                "updated_at": firestore.SERVER_TIMESTAMP
            })
            
        batch.commit()
        return doc_ids
        
    def retrieve_relevant(
        self,
        query: str,
        limit: int = 5,
        memory_type: Optional[MemoryType] = None,
        user_id: Optional[str] = None,
        min_similarity: float = 0.0
    ) -> List[MemoryEntry]:
        """
        Retrieve memories most relevant to the query.
        
        Args:
            query: Search query
            limit: Maximum number of results
            memory_type: Filter by memory type
            user_id: Filter by user scope
            min_similarity: Minimum similarity threshold
            
        Returns:
            List of relevant MemoryEntry objects
        """
        query_vector = self._generate_embedding(query)
        
        collection_ref = self.db.collection(self.collection_name)
        
        # Build the vector query
        vector_query = collection_ref.find_nearest(
            vector_field="embedding",
            query_vector=Vector(query_vector),
            distance_measure=DistanceMeasure.COSINE,
            limit=limit,
            distance_result_field="similarity_score"
        )
        
        results = vector_query.get()
        
        memories = []
        for doc in results:
            data = doc.to_dict()
            
            # Apply filters
            if memory_type and data.get("memory_type") != memory_type.value:
                continue
            if user_id and data.get("user_id") != user_id:
                continue
                
            # Convert cosine distance to similarity (1 - distance)
            similarity = 1 - data.get("similarity_score", 1)
            if similarity < min_similarity:
                continue
                
            memories.append(MemoryEntry(
                content=data.get("content", ""),
                memory_type=MemoryType(data.get("memory_type", "fact")),
                metadata=data.get("metadata", {}),
                timestamp=data.get("created_at"),
                similarity_score=similarity,
                document_id=doc.id
            ))
            
        return memories
        
    async def retrieve_relevant_async(
        self,
        query: str,
        limit: int = 5,
        memory_type: Optional[MemoryType] = None,
        user_id: Optional[str] = None,
        min_similarity: float = 0.0
    ) -> List[MemoryEntry]:
        """Async version of retrieve_relevant."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            lambda: self.retrieve_relevant(
                query, limit, memory_type, user_id, min_similarity
            )
        )
        
    def delete_memory(self, document_id: str) -> bool:
        """
        Delete a specific memory.
        
        Args:
            document_id: The Firestore document ID
            
        Returns:
            True if successful
        """
        try:
            self.db.collection(self.collection_name).document(document_id).delete()
            return True
        except Exception:
            return False
            
    def clear_user_memories(self, user_id: str) -> int:
        """
        Delete all memories for a specific user.
        
        Args:
            user_id: The user ID to clear
            
        Returns:
            Number of deleted documents
        """
        query = self.db.collection(self.collection_name).where(
            "user_id", "==", user_id
        )
        
        docs = query.stream()
        count = 0
        
        for doc in docs:
            doc.reference.delete()
            count += 1
            
        return count


# ═══════════════════════════════════════════════════════════════════════════
# TOOL FACTORY
# ═══════════════════════════════════════════════════════════════════════════

def create_memory_search_tool(
    project_id: str,
    collection_name: str = "unk_memory"
) -> callable:
    """
    Create a memory search tool for agent registration.
    
    Args:
        project_id: GCP project ID
        collection_name: Firestore collection name
        
    Returns:
        Callable tool function
    """
    memory = VectorMemory(project_id, collection_name)
    
    def search_knowledge_base(query: str, limit: int = 5) -> str:
        """
        Search the internal knowledge base for relevant information.
        Use this when the user asks about specific policies, past data,
        or stored knowledge.
        
        Args:
            query: The search query
            limit: Maximum number of results to return
            
        Returns:
            Formatted string of search results
        """
        results = memory.retrieve_relevant(query, limit=limit)
        
        if not results:
            return "No relevant information found in the knowledge base."
            
        output = "Found the following relevant information:\n\n"
        for i, entry in enumerate(results, 1):
            output += f"{i}. [{entry.memory_type.value.upper()}] "
            output += f"(Score: {entry.similarity_score:.2f})\n"
            output += f"   {entry.content}\n\n"
            
        return output
        
    return search_knowledge_base


def create_memory_store_tool(
    project_id: str,
    collection_name: str = "unk_memory"
) -> callable:
    """
    Create a memory storage tool for agent registration.
    
    Args:
        project_id: GCP project ID
        collection_name: Firestore collection name
        
    Returns:
        Callable tool function
    """
    memory = VectorMemory(project_id, collection_name)
    
    def store_information(
        content: str,
        category: str = "fact"
    ) -> str:
        """
        Store new information in the knowledge base for future reference.
        
        Args:
            content: The information to store
            category: Type of information (fact, procedure, preference)
            
        Returns:
            Confirmation message
        """
        type_map = {
            "fact": MemoryType.FACT,
            "procedure": MemoryType.PROCEDURE,
            "preference": MemoryType.USER_PREFERENCE,
            "knowledge": MemoryType.SYSTEM_KNOWLEDGE
        }
        
        memory_type = type_map.get(category.lower(), MemoryType.FACT)
        doc_id = memory.store_memory(content, memory_type)
        
        return f"Successfully stored information (ID: {doc_id})"
        
    return store_information
