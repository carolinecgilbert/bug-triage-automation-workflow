"""Command-line retriever for the local bug triage Chroma collection."""

from __future__ import annotations

import argparse
import os

import chromadb
from dotenv import load_dotenv

from rag.embeddings import create_embedding_client

DEFAULT_TOP_K = 5


def main() -> None:
    parser = argparse.ArgumentParser(description="Retrieve relevant RAG chunks for a bug triage query.")
    parser.add_argument("query", help="Bug report, symptom, log line, or triage question to search for.")
    parser.add_argument("--top-k", type=int, default=DEFAULT_TOP_K, help="Number of chunks to return.")
    args = parser.parse_args()

    load_dotenv()

    chroma_db_dir = os.getenv("CHROMA_DB_DIR", "chroma_db")
    collection_name = os.getenv("CHROMA_COLLECTION_NAME", "bug_triage_rag")

    embedding_client = create_embedding_client()
    query_embedding = embedding_client.embed_query(args.query)

    chroma_client = chromadb.PersistentClient(path=chroma_db_dir)
    collection = chroma_client.get_collection(name=collection_name)

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=args.top_k,
        include=["documents", "metadatas", "distances"],
    )

    print(f"Top {args.top_k} results from collection '{collection_name}'")
    print(f"Embedding provider: {embedding_client.provider_name}")
    print(f"Embedding model: {embedding_client.model_name}")
    print()

    documents = results.get("documents", [[]])[0]
    metadatas = results.get("metadatas", [[]])[0]
    distances = results.get("distances", [[]])[0]

    for index, (document, metadata, distance) in enumerate(zip(documents, metadatas, distances), start=1):
        preview = make_preview(document)
        print(f"{index}. {metadata.get('source')} [{metadata.get('doc_type')}] distance={distance:.4f}")
        print(f"   {preview}")
        print()


def make_preview(text: str, max_length: int = 240) -> str:
    """Create a compact one-line preview for terminal output."""
    preview = " ".join(text.split())
    if len(preview) <= max_length:
        return preview
    return f"{preview[: max_length - 3]}..."


if __name__ == "__main__":
    main()
