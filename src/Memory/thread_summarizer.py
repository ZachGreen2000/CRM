"""
Incremental Email Thread Summarization System
Maintains cached summaries that can be updated efficiently with new emails.
"""

import json
import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime
import httpx
from src.Memory.vector_store import get_vector_store

MODEL = "qwen3:8b"

class ThreadSummarizer:
    def __init__(self, model: str = MODEL):
        self.vector_store = get_vector_store()
        self.ollama_url = "http://localhost:11434/api/chat"
        self.model = model

    async def generate_incremental_summary(self, thread_id: str, contact_id: str,
                                         new_email_content: str, email_metadata: Dict[str, Any]) -> str:
        """
        Generate or update a thread summary incrementally.
        If thread already has a summary, update it with the new email.
        Otherwise, create a new summary.
        """
        print(f"[THREAD_SUMMARIZER] Processing thread {thread_id} for contact {contact_id}")

        # Get existing thread summary
        existing_summary = await self.vector_store.get_thread_summary(thread_id)

        if existing_summary:
            # Update existing summary
            updated_summary = await self._update_existing_summary(
                existing_summary['summary'],
                new_email_content,
                email_metadata
            )
        else:
            # Create new summary
            updated_summary = await self._create_new_summary(
                new_email_content,
                email_metadata
            )

        # Generate embedding for the summary
        summary_embedding = await self._generate_embedding(updated_summary)

        # Store/update in vector store
        metadata = {
            'thread_id': thread_id,
            'contact_id': contact_id,
            'last_updated': datetime.now().isoformat(),
            'email_count': existing_summary['metadata'].get('email_count', 0) + 1 if existing_summary else 1
        }

        await self.vector_store.update_thread_summary(
            thread_id, updated_summary, summary_embedding, metadata
        )

        print(f"[THREAD_SUMMARIZER] Updated summary for thread {thread_id}")
        return updated_summary

    async def _update_existing_summary(self, current_summary: str, new_email: str,
                                     email_metadata: Dict[str, Any]) -> str:
        """Update existing summary with new email content."""
        prompt = f"""You have an existing email thread summary. Update it to include this new email.

EXISTING SUMMARY:
{current_summary}

NEW EMAIL:
Subject: {email_metadata.get('subject', 'No subject')}
From: {email_metadata.get('direction', 'unknown')} - {email_metadata.get('sender', 'unknown')}
Content: {new_email[:1000]}...

Please provide an updated summary that incorporates this new information while maintaining the key points from the existing summary. Keep it concise but comprehensive.

UPDATED SUMMARY:"""

        return await self._call_llm(prompt)

    async def _create_new_summary(self, email_content: str, email_metadata: Dict[str, Any]) -> str:
        """Create initial summary for a new thread."""
        prompt = f"""Please summarize this email for CRM purposes.

EMAIL DETAILS:
Subject: {email_metadata.get('subject', 'No subject')}
From: {email_metadata.get('direction', 'unknown')} - {email_metadata.get('sender', 'unknown')}
Content: {email_content[:2000]}...

Provide a concise summary covering:
- Main topic/purpose
- Key information or requests
- Any action items or deadlines
- Overall tone/sentiment

SUMMARY:"""

        return await self._call_llm(prompt)

    async def _call_llm(self, prompt: str) -> str:
        """Call Ollama LLM for summarization."""
        try:
            async with httpx.AsyncClient(timeout=60) as client:
                response = await client.post(self.ollama_url, json={
                    "model": self.model,
                    "messages": [{"role": "user", "content": prompt}],
                    "stream": False
                })

                result = response.json()
                return result["message"]["content"].strip()
        except Exception as e:
            print(f"[THREAD_SUMMARIZER] Error calling LLM: {e}")
            return f"Summary generation failed: {str(e)}"

    async def _generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for summary text."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "http://localhost:11434/api/embeddings",
                    json={
                        "model": "nomic-embed-text",
                        "input": text[:8000]
                    }
                )
                result = response.json()
                embedding = result.get("embedding")
                if embedding is None and isinstance(result.get("data"), list) and result["data"]:
                    embedding = result["data"][0].get("embedding")

                if embedding is None:
                    raise ValueError(f"Embedding response missing expected field: {result}")

                return embedding
        except Exception as e:
            print(f"[THREAD_SUMMARIZER] Error generating embedding: {e}")
            return []

    async def get_thread_context(self, thread_id: str, max_related: int = 3) -> Dict[str, Any]:
        """Get thread summary and related context for AI processing."""
        summary = await self.vector_store.get_thread_summary(thread_id)

        if not summary:
            return {"summary": None, "related_threads": []}

        # Find related threads by vector similarity
        if summary.get('embedding'):
            related = await self.vector_store.search_similar_summaries(
                summary['embedding'], limit=max_related
            )
        else:
            related = []

        return {
            "summary": summary['summary'],
            "metadata": summary['metadata'],
            "related_threads": related
        }


# Global instance
_thread_summarizer = None

def get_thread_summarizer(model: str | None = None) -> ThreadSummarizer:
    """Get or create global thread summarizer instance.

    If a specific model is requested, return a fresh thread summarizer
    instance configured for that model. Otherwise reuse the default singleton.
    """
    global _thread_summarizer
    if model is None:
        if _thread_summarizer is None:
            _thread_summarizer = ThreadSummarizer()
        return _thread_summarizer

    return ThreadSummarizer(model=model)