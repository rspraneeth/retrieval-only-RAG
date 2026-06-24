"""Build and persist the vector index from PDFs."""

import hashlib
import json
from pathlib import Path

import chromadb
from llama_index.core import Settings, StorageContext, VectorStoreIndex
from llama_index.core.node_parser import SentenceSplitter
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.readers.file import PDFReader
from llama_index.vector_stores.chroma import ChromaVectorStore

from pdf_rag.config import Config

_COLLECTION = "pdf_rag"
_MANIFEST = "manifest.json"


def _embed_model(model_name: str) -> HuggingFaceEmbedding:
    return HuggingFaceEmbedding(model_name=model_name)


def _pdf_paths(pdf_folder: Path) -> list[Path]:
    return sorted(pdf_folder.glob("*.pdf"))


def _file_hash(path: Path) -> str:
    return hashlib.md5(path.read_bytes()).hexdigest()


def _load_manifest(store_dir: Path) -> dict[str, str]:
    p = store_dir / _MANIFEST
    return json.loads(p.read_text()) if p.exists() else {}


def _save_manifest(store_dir: Path, manifest: dict[str, str]) -> None:
    (store_dir / _MANIFEST).write_text(json.dumps(manifest, indent=2))


def _chroma_store(store_dir: Path) -> tuple[chromadb.Collection, ChromaVectorStore]:
    client = chromadb.PersistentClient(path=str(store_dir))
    collection = client.get_or_create_collection(_COLLECTION)
    return collection, ChromaVectorStore(chroma_collection=collection)


def build_index(config: Config) -> tuple[VectorStoreIndex, int, int]:
    """Incrementally index PDFs — only new or changed files are processed.

    Returns (index, total_file_count, new_chunk_count).
    """
    config.vector_store.mkdir(parents=True, exist_ok=True)

    pdf_paths = _pdf_paths(config.pdf_folder)
    if not pdf_paths:
        raise ValueError(f"No PDF files found in {config.pdf_folder}")

    Settings.embed_model = _embed_model(config.embedding_model)

    collection, vector_store = _chroma_store(config.vector_store)
    storage_context = StorageContext.from_defaults(vector_store=vector_store)

    manifest = _load_manifest(config.vector_store)
    current = {p.name: _file_hash(p) for p in pdf_paths}

    # Remove chunks for deleted PDFs
    for name in set(manifest) - set(current):
        collection.delete(where={"file_name": name})

    # Only process new or changed PDFs
    to_index = [p for p in pdf_paths if current[p.name] != manifest.get(p.name)]

    reader = PDFReader()
    splitter = SentenceSplitter()
    new_nodes = []

    for pdf_path in to_index:
        if pdf_path.name in manifest:  # changed file — remove stale chunks first
            collection.delete(where={"file_name": pdf_path.name})
        docs = reader.load_data(file=pdf_path)
        for doc in docs:
            doc.metadata["file_name"] = pdf_path.name
        new_nodes.extend(splitter.get_nodes_from_documents(docs))

    if new_nodes:
        index = VectorStoreIndex(new_nodes, storage_context=storage_context)
    else:
        index = VectorStoreIndex.from_vector_store(vector_store)

    _save_manifest(config.vector_store, current)

    return index, len(pdf_paths), len(new_nodes)


def load_index(config: Config) -> VectorStoreIndex:
    """Connect to the persisted ChromaDB index."""
    store_dir = config.vector_store
    if not (store_dir / _MANIFEST).exists():
        raise FileNotFoundError(
            f"No index at {store_dir}. Run `python -m pdf_rag.cli index` first."
        )
    Settings.embed_model = _embed_model(config.embedding_model)
    _, vector_store = _chroma_store(store_dir)
    return VectorStoreIndex.from_vector_store(vector_store)
