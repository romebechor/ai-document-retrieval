"""
Configuration module.

Loads required environment variables from a local .env file.
No secrets are hardcoded anywhere in this project - see .env.example
for the variables you need to set.
"""

import os
import sys

from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
POSTGRES_URL = os.getenv("POSTGRES_URL")

# Dimensionality of the embedding vectors produced by gemini-embedding-001.
# Adjust this if you configure the model to output a different dimension.
EMBEDDING_DIM = int(os.getenv("EMBEDDING_DIM", "3072"))

EMBEDDING_MODEL = "models/gemini-embedding-001"


def require_config():
    """Fail fast with a clear message if required env vars are missing."""
    missing = []
    if not GEMINI_API_KEY:
        missing.append("GEMINI_API_KEY")
    if not POSTGRES_URL:
        missing.append("POSTGRES_URL")

    if missing:
        print(
            f"Error: missing required environment variable(s): {', '.join(missing)}.\n"
            f"Create a .env file based on .env.example and set them.",
            file=sys.stderr,
        )
        sys.exit(1)
