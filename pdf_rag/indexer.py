"""Build and persist the vector index from PDFs."""

from pathlib import Path

from llama_index.core import Settings, VectorStoreIndex, load_index_from_storage
from llama_index.core.node_parser import SentenceSplitter
from llama_index.core.storage import StorageContext
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.readers.file import PDFReader

from pdf_rag.config import Config


def _embed_model(model_name: str) -> HuggingFaceEmbedding:
    return HuggingFaceEmbedding(model_name=model_name)


def _pdf_paths(pdf_folder: Path) -> list[Path]:
    return sorted(pdf_folder.glob("*.pdf"))


def build_index(config: Config) -> tuple[VectorStoreIndex, int, int]:
    """Load PDFs, chunk, embed, and persist. Returns (index, file_count, chunk_count)."""
    pdf_paths = _pdf_paths(config.pdf_folder)
    if not pdf_paths:
        raise ValueError(f"No PDF files found in {config.pdf_folder}")

    Settings.embed_model = _embed_model(config.embedding_model)
    reader = PDFReader()
    documents = []
    for pdf_path in pdf_paths:
        docs = reader.load_data(file=pdf_path)
        for doc in docs:
            doc.metadata["file_name"] = pdf_path.name
        documents.extend(docs)

    splitter = SentenceSplitter()
    nodes = splitter.get_nodes_from_documents(documents)

    config.vector_store.mkdir(parents=True, exist_ok=True)
    index = VectorStoreIndex(nodes)
    index.storage_context.persist(persist_dir=str(config.vector_store))

    return index, len(pdf_paths), len(nodes)


def load_index(config: Config) -> VectorStoreIndex:
    """Load a persisted index from disk."""
    persist_dir = config.vector_store
    if not persist_dir.is_dir() or not any(persist_dir.iterdir()):
        raise FileNotFoundError(
            f"No vector store at {persist_dir}. Run the index command first."
        )

    Settings.embed_model = _embed_model(config.embedding_model)
    storage_context = StorageContext.from_defaults(persist_dir=str(persist_dir))
    return load_index_from_storage(storage_context)
