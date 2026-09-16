# Document Indexing & Semantic Search

A Python module that extracts text from PDF/DOCX files, splits it into
chunks using one of three strategies, generates embeddings with the
Gemini API (`gemini-embedding-001`), stores everything in PostgreSQL
using the `pgvector` extension, and supports semantic search over the
stored content.

## Project structure

```
.
├── index_documents.py   # CLI: extract -> chunk -> embed -> store
├── search.py            # CLI: embed query -> vector similarity search
├── extract.py            # PDF/DOCX text extraction
├── chunking.py            # fixed / sentence / paragraph chunking strategies
├── embeddings.py           # Gemini embedding wrapper
├── db.py                    # PostgreSQL + pgvector access layer
├── config.py                  # environment variable loading
├── requirements.txt
├── .env.example
└── docs/                        # place your input files here (optional)
```

## Requirements

- Python 3.10+
- PostgreSQL with the [`pgvector`](https://github.com/pgvector/pgvector) extension available
  (the extension is created automatically on first run if the database user has permission)
- A Gemini API key

## Installation

```bash
git clone <this-repo-url>
cd <repo-folder>
python -m venv .venv
source .venv/bin/activate   # on Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Environment variables

Copy `.env.example` to `.env` and fill in your own values:

```bash
cp .env.example .env
```

| Variable         | Description                                              |
|------------------|-----------------------------------------------------------|
| `GEMINI_API_KEY` | Your Gemini API key                                        |
| `POSTGRES_URL`   | PostgreSQL connection string, e.g. `postgresql://user:pass@localhost:5432/mydb` |
| `EMBEDDING_DIM`  | Optional. Embedding vector size (default: `3072`)          |

No secrets are hardcoded anywhere in the code - both scripts fail fast
with a clear error message if a required variable is missing.

## Usage

### 1. Index a document

```bash
python index_documents.py --file ./docs/sample.docx --strategy paragraph
```

Available `--strategy` values: `fixed`, `sentence`, `paragraph`.

**Sample output:**

```
Extracted 417 characters from './docs/sample.docx'.
Split into 4 chunks using the 'paragraph' strategy.
Generated 4 embeddings.
Successfully indexed './docs/sample.docx' (4 chunks) into the database.
```
### 2. Search indexed content

```bash
python search.py --query "What should a customer do if they cannot log in?" --top-k 3
```

**Sample output:**

```
Top 3 result(s) for query: "What should a customer do if they cannot log in?"

[1] similarity=0.8446 | file=sample.docx | strategy=paragraph | id=16
    Customers who cannot log in should first verify their email address and password. If the issue continues, they should reset their password and try again.

[2] similarity=0.7035 | file=sample.docx | strategy=paragraph | id=15
    Customer Support Guide

[3] similarity=0.6630 | file=sample.docx | strategy=paragraph | id=17
    Billing issues should be reviewed by the support team. Customers should provide their account email and relevant payment details.
```

If the database contains no indexed chunks, the tool prints:

```
No results found. The index may be empty - try running index_documents.py first.
```

## Chunking strategies

| Strategy    | Description                                                        |
|-------------|---------------------------------------------------------------------|
| `fixed`     | Fixed-size character windows with overlap between consecutive chunks (default: 800 chars, 100 overlap) |
| `sentence`  | Groups whole sentences together until a max character length is reached |
| `paragraph` | Splits on paragraph breaks (blank lines) - each paragraph becomes one chunk |

## Error handling

Both CLI tools handle the following cases with clear, non-crashing error messages:

- Missing input file
- Unsupported file type (anything other than `.pdf` / `.docx`)
- Document with no extractable text (e.g. a scanned PDF with no OCR layer)
- Embedding generation failure (e.g. invalid/expired API key, network error)
- Database connection failure (e.g. wrong `POSTGRES_URL`, database down)
- Empty search results

## Database schema

```sql
CREATE TABLE document_chunks (
    id SERIAL PRIMARY KEY,
    chunk_text TEXT NOT NULL,
    embedding VECTOR(3072) NOT NULL,
    filename TEXT NOT NULL,
    split_strategy TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);
```

The table and the `vector` extension are created automatically the
first time either script connects to the database.

## Notes

- Embeddings are generated one chunk at a time via the Gemini API.
- Vector similarity is computed using cosine distance (`<=>` operator from pgvector);
  results are ranked from most to least similar.
- No API keys, connection strings, or other secrets are ever printed to the console.
