"""
Chunking strategies.

Three strategies are implemented, selectable by name:
    - "fixed"     : fixed-size character windows with overlap
    - "sentence"  : groups whole sentences until a max size is reached
    - "paragraph" : splits on paragraph breaks (blank lines)

Every strategy returns a list[str] of non-empty chunks.
"""

import re

VALID_STRATEGIES = ("fixed", "sentence", "paragraph")


def fixed_size_chunking(text: str, chunk_size: int = 800, overlap: int = 100) -> list[str]:
    """Split text into fixed-size character windows with overlap between consecutive chunks."""
    if chunk_size <= 0:
        raise ValueError("chunk_size must be positive")
    if overlap >= chunk_size:
        raise ValueError("overlap must be smaller than chunk_size")

    chunks = []
    start = 0
    text_length = len(text)

    while start < text_length:
        end = min(start + chunk_size, text_length)
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        if end == text_length:
            break
        start = end - overlap

    return chunks


_SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?])\s+")


def sentence_based_chunking(text: str, max_chars: int = 800) -> list[str]:
    """Group whole sentences together until adding another sentence would exceed max_chars."""
    sentences = [s.strip() for s in _SENTENCE_SPLIT_RE.split(text) if s.strip()]

    chunks = []
    current = []
    current_len = 0

    for sentence in sentences:
        sentence_len = len(sentence) + 1
        if current and current_len + sentence_len > max_chars:
            chunks.append(" ".join(current))
            current = [sentence]
            current_len = sentence_len
        else:
            current.append(sentence)
            current_len += sentence_len

    if current:
        chunks.append(" ".join(current))

    return chunks


def paragraph_based_chunking(text: str) -> list[str]:
    """Split text on paragraph breaks (one or more blank lines)."""
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    return paragraphs


def chunk_text(text: str, strategy: str, **kwargs) -> list[str]:
    """Dispatch to the requested chunking strategy."""
    if strategy == "fixed":
        return fixed_size_chunking(text, **kwargs)
    if strategy == "sentence":
        return sentence_based_chunking(text, **kwargs)
    if strategy == "paragraph":
        return paragraph_based_chunking(text)
    raise ValueError(f"Unknown chunking strategy '{strategy}'. Valid options: {VALID_STRATEGIES}")
