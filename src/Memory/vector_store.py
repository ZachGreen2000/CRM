"""
Vector Store Implementation using ChromaDB
Handles embeddings for emails and contact summaries with efficient retrieval.
"""

import chromadb
from chromadb.config import Settings
import os
import json
from typing import List, Dict, Any, Optional, Tuple
import asyncio
from pathlib import Path


class VectorStore:
    def __init__(self, persist_directory: str = "./chroma_db"):
        """Initialize ChromaDB vector store."""
        self.persist_directory = persist_directory
        Path(persist_directory).mkdir(exist_ok=True)

        self.client = chromadb.PersistentClient(
            path=persist_directory,
            settings=Settings(anonymized_telemetry=False)
        )

        # Collections for different types of content
        self.email_collection = self.client.get_or_create_collection(
            name="emails",
            metadata={"description": "Email content embeddings for retrieval"}
        )

        self.contact_summary_collection = self.client.get_or_create_collection(
            name="contact_summaries",
            metadata={"description": "Contact summary embeddings for retrieval"}
        )

        self.thread_summary_collection = self.client.get_or_create_collection(
            name="thread_summaries",
            metadata={"description": "Email thread summary embeddings"}
        )

    async def store_email_embedding(self, email_id: str, content: str, embedding: List[float],
                                   metadata: Dict[str, Any]) -> bool:
        """Store email embedding with metadata."""
        try:
            self.email_collection.add(
                embeddings=[embedding],
                documents=[content],
                metadatas=[metadata],
                ids=[email_id]
            )
            return True
        except Exception as e:
            print(f"[VECTOR_STORE] Error storing email embedding: {e}")
            return False

    async def store_contact_summary_embedding(self, contact_id: str, summary: str,
                                            embedding: List[float], metadata: Dict[str, Any]) -> bool:
        """Store or update contact summary embedding."""
        try:
            # Check if summary already exists
            existing = self.contact_summary_collection.get(ids=[contact_id])

            if existing['ids']:
                # Update existing
                self.contact_summary_collection.update(
                    embeddings=[embedding],
                    documents=[summary],
                    metadatas=[metadata],
                    ids=[contact_id]
                )
            else:
                # Create new
                self.contact_summary_collection.add(
                    embeddings=[embedding],
                    documents=[summary],
                    metadatas=[metadata],
                    ids=[contact_id]
                )
            return True
        except Exception as e:
            print(f"[VECTOR_STORE] Error storing contact summary embedding: {e}")
            return False

    async def store_thread_summary_embedding(self, thread_id: str, summary: str,
                                           embedding: List[float], metadata: Dict[str, Any]) -> bool:
        """Store email thread summary embedding."""
        try:
            self.thread_summary_collection.add(
                embeddings=[embedding],
                documents=[summary],
                metadatas=[metadata],
                ids=[thread_id]
            )
            return True
        except Exception as e:
            print(f"[VECTOR_STORE] Error storing thread summary embedding: {e}")
            return False

    async def search_similar_emails(self, query_embedding: List[float], contact_id: str = None,
                                   limit: int = 5) -> List[Dict[str, Any]]:
        """Search for similar emails using vector similarity."""
        try:
            where_clause = {"contact_id": contact_id} if contact_id else None

            results = self.email_collection.query(
                query_embeddings=[query_embedding],
                n_results=limit,
                where=where_clause
            )

            return self._format_results(results)
        except Exception as e:
            print(f"[VECTOR_STORE] Error searching emails: {e}")
            return []

    async def search_similar_summaries(self, query_embedding: List[float], limit: int = 3) -> List[Dict[str, Any]]:
        """Search for similar contact summaries."""
        try:
            results = self.contact_summary_collection.query(
                query_embeddings=[query_embedding],
                n_results=limit
            )

            return self._format_results(results)
        except Exception as e:
            print(f"[VECTOR_STORE] Error searching summaries: {e}")
            return []

    async def get_thread_summary(self, thread_id: str) -> Optional[Dict[str, Any]]:
        """Get existing thread summary."""
        try:
            results = self.thread_summary_collection.get(ids=[thread_id])
            if results['ids']:
                return {
                    'id': results['ids'][0],
                    'summary': results['documents'][0],
                    'metadata': results['metadatas'][0]
                }
            return None
        except Exception as e:
            print(f"[VECTOR_STORE] Error getting thread summary: {e}")
            return None

    async def update_thread_summary(self, thread_id: str, new_summary: str,
                                   embedding: List[float], metadata: Dict[str, Any]) -> bool:
        """Update existing thread summary."""
        try:
            existing = await self.get_thread_summary(thread_id)
            if existing:
                self.thread_summary_collection.update(
                    embeddings=[embedding],
                    documents=[new_summary],
                    metadatas=[metadata],
                    ids=[thread_id]
                )
            else:
                await self.store_thread_summary_embedding(thread_id, new_summary, embedding, metadata)
            return True
        except Exception as e:
            print(f"[VECTOR_STORE] Error updating thread summary: {e}")
            return False

    def _format_results(self, results: Dict) -> List[Dict[str, Any]]:
        """Format ChromaDB results into consistent format."""
        formatted = []
        if results['ids'] and results['documents'] and results['metadatas']:
            for i in range(len(results['ids'])):
                formatted.append({
                    'id': results['ids'][i],
                    'content': results['documents'][i],
                    'metadata': results['metadatas'][i],
                    'distance': results['distances'][i] if 'distances' in results else None
                })
        return formatted

    async def get_collection_stats(self) -> Dict[str, int]:
        """Get statistics about stored vectors."""
        try:
            email_count = self.email_collection.count()
            summary_count = self.contact_summary_collection.count()
            thread_count = self.thread_summary_collection.count()

            return {
                'emails': email_count,
                'contact_summaries': summary_count,
                'thread_summaries': thread_count,
                'total': email_count + summary_count + thread_count
            }
        except Exception as e:
            print(f"[VECTOR_STORE] Error getting stats: {e}")
            return {'emails': 0, 'contact_summaries': 0, 'thread_summaries': 0, 'total': 0}


# Global instance
_vector_store = None

def get_vector_store() -> VectorStore:
    """Get or create global vector store instance."""
    global _vector_store
    if _vector_store is None:
        # Use project root for persistence
        project_root = Path(__file__).parent.parent.parent
        persist_dir = project_root / "chroma_db"
        _vector_store = VectorStore(str(persist_dir))
    return _vector_store