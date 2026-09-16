"""
Database access layer - PostgreSQL with the pgvector extension.

Handles connection, schema creation, inserting chunks, and vector
similarity search.
"""

import psycopg2
from pgvector.psycopg2 import register_vector

from config import POSTGRES_URL, EMBEDDING_DIM


class DatabaseConnectionError(Exception):
    """Raised when the database cannot be reached."""


def get_connection():
    """Open a new database connection and register the pgvector type."""
    try:
        conn = psycopg2.connect(POSTGRES_URL)
    except psycopg2.OperationalError as exc:
        raise DatabaseConnectionError(f"Could not connect to the database: {exc}") from exc

    conn.autocommit = False

    with conn.cursor() as cur:
        cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")
    conn.commit()

    register_vector(conn)
    return conn


def ensure_schema(conn):
    """Create the document_chunks table if it does not already exist."""
    with conn.cursor() as cur:
        cur.execute(
            f"""
            CREATE TABLE IF NOT EXISTS document_chunks (
                id SERIAL PRIMARY KEY,
                chunk_text TEXT NOT NULL,
                embedding VECTOR({EMBEDDING_DIM}) NOT NULL,
                filename TEXT NOT NULL,
                split_strategy TEXT NOT NULL,
                created_at TIMESTAMP NOT NULL DEFAULT NOW()
            );
            """
        )
    conn.commit()


def insert_chunks(conn, filename: str, split_strategy: str, chunks: list[str], embeddings: list[list[float]]):
    """Insert chunk rows in a single transaction."""
    with conn.cursor() as cur:
        for chunk_text, embedding in zip(chunks, embeddings):
            cur.execute(
                """
                INSERT INTO document_chunks (chunk_text, embedding, filename, split_strategy)
                VALUES (%s, %s, %s, %s);
                """,
                (chunk_text, embedding, filename, split_strategy),
            )
    conn.commit()


def search_similar_chunks(conn, query_embedding: list[float], top_k: int = 5):
    """
    Return the top_k most similar chunks to the given query embedding,
    ordered by cosine distance (smaller = more similar).
    """
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT id, chunk_text, filename, split_strategy, created_at,
                   embedding <=> %s::vector AS distance
            FROM document_chunks
            ORDER BY embedding <=> %s::vector
            LIMIT %s;
            """,
            (query_embedding, query_embedding, top_k),
        )
        return cur.fetchall()
