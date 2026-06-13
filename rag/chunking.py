"""Text chunking helpers for retrieval ingestion."""

from __future__ import annotations


def chunk_text(text: str, chunk_size: int = 1000, chunk_overlap: int = 150) -> list[str]:
    """Split text into overlapping character chunks with readable boundaries.

    The chunker is intentionally simple for early RAG development. It prefers to
    end chunks at paragraph, line, sentence, or word boundaries when those
    boundaries are close enough to the target chunk size.
    """
    if chunk_size <= 0:
        raise ValueError("chunk_size must be greater than 0")
    if chunk_overlap < 0:
        raise ValueError("chunk_overlap must be 0 or greater")
    if chunk_overlap >= chunk_size:
        raise ValueError("chunk_overlap must be smaller than chunk_size")

    normalized_text = text.strip()
    if not normalized_text:
        return []

    chunks: list[str] = []
    text_length = len(normalized_text)
    start = 0

    while start < text_length:
        target_end = min(start + chunk_size, text_length)
        end = _find_readable_boundary(normalized_text, start, target_end, chunk_size)

        chunk = normalized_text[start:end].strip()
        if chunk:
            chunks.append(chunk)

        if end >= text_length:
            break

        # Step back by the overlap, then skip whitespace so previews and chunks
        # do not start with ragged indentation.
        next_start = max(end - chunk_overlap, start + 1)
        while next_start < text_length and normalized_text[next_start].isspace():
            next_start += 1
        start = next_start

    return chunks


def _find_readable_boundary(text: str, start: int, target_end: int, chunk_size: int) -> int:
    """Find a natural chunk boundary near target_end."""
    if target_end >= len(text):
        return len(text)

    min_boundary = start + max(chunk_size // 2, 1)
    boundary_markers = ("\n\n", "\n", ". ", "? ", "! ", " ")

    for marker in boundary_markers:
        boundary = text.rfind(marker, start, target_end)
        if boundary >= min_boundary:
            return boundary + len(marker)

    return target_end

