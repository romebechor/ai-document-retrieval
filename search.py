"""
search.py

CLI tool that embeds a natural-language query and performs a vector
similarity search against the document_chunks table.

Example:
    python search.py --query "login issue"
"""

import argparse
import sys

from config import require_config
from embeddings import embed_text, EmbeddingError
from db import get_connection, ensure_schema, search_similar_chunks, DatabaseConnectionError


def parse_args():
    parser = argparse.ArgumentParser(description="Semantic search over indexed document chunks.")
    parser.add_argument("--query", required=True, help="Natural language search query.")
    parser.add_argument("--top-k", type=int, default=5, help="Number of results to return (default: 5).")
    return parser.parse_args()


def main():
    args = parse_args()
    require_config()

    # 1. Embed the query
    try:
        query_embedding = embed_text(args.query, task_type="retrieval_query")
    except EmbeddingError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)

    # 2. Connect to the database
    try:
        conn = get_connection()
    except DatabaseConnectionError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)

    try:
        ensure_schema(conn)
        results = search_similar_chunks(conn, query_embedding, top_k=args.top_k)
    finally:
        conn.close()

    # 3. Display results
    if not results:
        print("No results found. The index may be empty - try running index_documents.py first.")
        return

    print(f"Top {len(results)} result(s) for query: \"{args.query}\"\n")
    for rank, (chunk_id, chunk_text, filename, split_strategy, created_at, distance) in enumerate(results, start=1):
        similarity = 1 - distance  # cosine distance -> similarity score
        print(f"[{rank}] similarity={similarity:.4f} | file={filename} | strategy={split_strategy} | id={chunk_id}")
        preview = chunk_text[:300] + ("..." if len(chunk_text) > 300 else "")
        print(f"    {preview}\n")


if __name__ == "__main__":
    main()
