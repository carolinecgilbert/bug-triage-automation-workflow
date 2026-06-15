"""Ingest local bug triage source data into a Chroma collection."""

from __future__ import annotations

import argparse
import hashlib
import os
from pathlib import Path

import chromadb
from dotenv import load_dotenv

from rag.chunking import chunk_text
from rag.embeddings import create_embedding_client


DATA_DIR = Path("data")
SUPPORTED_EXTENSIONS = {".md", ".log", ".json"}


def main() -> None:
    load_dotenv()

    parser = argparse.ArgumentParser(description="Ingest local bug triage source data into Chroma.")
    parser.add_argument(
        "--provider",
        choices=["hash", "openai", "sentence-transformers", "local"],
        default=os.getenv("EMBEDDING_PROVIDER", "hash"),
        help=(
            "Embedding provider to use. Defaults to EMBEDDING_PROVIDER or hash. "
            "Use openai for hosted embeddings."
        ),
    )
    args = parser.parse_args()

    chroma_db_dir = os.getenv("CHROMA_DB_DIR", "chroma_db")
    collection_name = os.getenv("CHROMA_COLLECTION_NAME", "bug_triage_rag")

    documents = load_documents(DATA_DIR)
    chunk_records = build_chunk_records(documents)

    if not chunk_records:
        raise RuntimeError("No chunks were created. Check that data/ contains supported source files.")

    embedding_client = create_embedding_client(provider=args.provider)
    embeddings = embedding_client.embed_texts([record["text"] for record in chunk_records])

    chroma_client = chromadb.PersistentClient(path=chroma_db_dir)
    recreate_collection(chroma_client, collection_name)
    collection = chroma_client.create_collection(
        name=collection_name,
        metadata={
            "embedding_provider": embedding_client.provider_name,
            "embedding_model": embedding_client.model_name,
        },
    )

    collection.add(
        ids=[record["id"] for record in chunk_records],
        documents=[record["text"] for record in chunk_records],
        metadatas=[record["metadata"] for record in chunk_records],
        embeddings=embeddings,
    )

    print("RAG ingestion complete")
    print(f"Files loaded: {len(documents)}")
    print(f"Chunks created: {len(chunk_records)}")
    print(f"Embedding provider: {embedding_client.provider_name}")
    print(f"Embedding model: {embedding_client.model_name}")
    print(f"Chroma DB dir: {chroma_db_dir}")
    print(f"Collection: {collection_name}")


def load_documents(data_dir: Path) -> list[dict[str, object]]:
    """Load supported source files under data/ with retrieval metadata."""
    documents: list[dict[str, object]] = []

    for path in sorted(data_dir.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in SUPPORTED_EXTENSIONS:
            continue

        source = path.as_posix()
        metadata = {
            "source": source,
            "filename": path.name,
            "doc_type": infer_doc_type(path),
        }
        documents.append(
            {
                "text": path.read_text(encoding="utf-8"),
                "metadata": metadata,
            }
        )

    return documents


def infer_doc_type(path: Path) -> str:
    """Map a data file path to the document type used for retrieval filters."""
    parts = path.parts

    if path.name == "ownership.json":
        return "ownership"
    if "docs" in parts:
        return "docs"
    if "historical_issues" in parts:
        return "historical_issue"
    if "code_summaries" in parts:
        return "code_summary"
    if "sample_issues" in parts:
        return "sample_issue"
    if "logs" in parts:
        return "log"

    return "unknown"


def build_chunk_records(documents: list[dict[str, object]]) -> list[dict[str, object]]:
    """Chunk loaded documents and attach stable IDs plus chunk metadata."""
    records: list[dict[str, object]] = []

    for document in documents:
        text = str(document["text"])
        metadata = dict(document["metadata"])
        chunks = chunk_text(text)

        for chunk_index, chunk in enumerate(chunks):
            chunk_metadata = {
                **metadata,
                "chunk_index": chunk_index,
            }
            records.append(
                {
                    "id": make_chunk_id(str(metadata["source"]), chunk_index, chunk),
                    "text": chunk,
                    "metadata": chunk_metadata,
                }
            )

    return records


def make_chunk_id(source: str, chunk_index: int, chunk: str) -> str:
    """Create a deterministic Chroma ID for a chunk."""
    digest = hashlib.sha1(f"{source}:{chunk_index}:{chunk}".encode("utf-8")).hexdigest()
    return f"{Path(source).stem}-{chunk_index}-{digest[:12]}"


def recreate_collection(client: chromadb.PersistentClient, collection_name: str) -> None:
    """Delete any previous collection so ingestion is repeatable."""
    try:
        client.delete_collection(name=collection_name)
    except Exception:
        # Chroma raises when the collection does not exist. For this early
        # ingestion script, missing collection is the expected first-run path.
        pass


if __name__ == "__main__":
    main()
