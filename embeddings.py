"""
Embedding generation using the Gemini API (gemini-embedding-001).
"""

import google.generativeai as genai

from config import GEMINI_API_KEY, EMBEDDING_MODEL

genai.configure(api_key=GEMINI_API_KEY)


class EmbeddingError(Exception):
    """Raised when embedding generation fails."""


def embed_text(text: str, task_type: str = "retrieval_document") -> list[float]:
    """
    Generate an embedding vector for a single piece of text.

    task_type should be "retrieval_document" when indexing chunks,
    and "retrieval_query" when embedding a search query.
    """
    try:
        result = genai.embed_content(
            model=EMBEDDING_MODEL,
            content=text,
            task_type=task_type,
        )
        return result["embedding"]
    except Exception as exc:
        raise EmbeddingError(f"Failed to generate embedding: {exc}") from exc


def embed_chunks(chunks: list[str]) -> list[list[float]]:
    """Generate embeddings for a list of chunks, one request per chunk."""
    embeddings = []
    for chunk in chunks:
        embeddings.append(embed_text(chunk, task_type="retrieval_document"))
    return embeddings
