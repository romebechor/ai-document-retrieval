"""
index_documents.py

CLI tool that extracts text from a PDF/DOCX file, splits it into chunks
using the selected strategy, generates embeddings via the Gemini API,
and stores everything in PostgreSQL (pgvector).

Example:
    python index_documents.py --file ./docs/example.pdf --strategy paragraph
"""

import argparse
import os
import sys

from config import require_config
from extract import (
    extract_text,
    FileNotFoundExtractionError,
    UnsupportedFileTypeError,
    NoTextExtractedError,
)
from chunking import chunk_text, VALID_STRATEGIES
from embeddings import embed_chunks, EmbeddingError
from db import get_connection, ensure_schema, insert_chunks, DatabaseConnectionError


def parse_args():
    parser = argparse.ArgumentParser(description="Index a PDF/DOCX file into PostgreSQL with pgvector.")
    parser.add_argument("--file", required=True, help="Path to the PDF or DOCX file to index.")
    parser.add_argument(
        "--strategy",
        required=True,
        choices=VALID_STRATEGIES,
        help="Chunking strategy to use.",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    require_config()

    # 1. Extract text
    try:
        text = extract_text(args.file)
    except FileNotFoundExtractionError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)
    except UnsupportedFileTypeError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)
    except NoTextExtractedError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)

    print(f"Extracted {len(text)} characters from '{args.file}'.")

    # 2. Chunk text
    chunks = chunk_text(text, args.strategy)
    if not chunks:
        print("Error: chunking produced no chunks - the document may be too short or empty.", file=sys.stderr)
        sys.exit(1)

    print(f"Split into {len(chunks)} chunks using the '{args.strategy}' strategy.")

    # 3. Generate embeddings
    try:
        embeddings = embed_chunks(chunks)
    except EmbeddingError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)

    print(f"Generated {len(embeddings)} embeddings.")

    # 4. Store in database
    try:
        conn = get_connection()
    except DatabaseConnectionError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)

    try:
        ensure_schema(conn)
        filename = os.path.basename(args.file)
        insert_chunks(conn, filename, args.strategy, chunks, embeddings)
    finally:
        conn.close()

    print(f"Successfully indexed '{args.file}' ({len(chunks)} chunks) into the database.")


if __name__ == "__main__":
    main()
