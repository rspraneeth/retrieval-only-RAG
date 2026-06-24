"""MCP server exposing PDF retrieval as a tool for IDE agents."""

from mcp.server.fastmcp import FastMCP
from llama_index.core import VectorStoreIndex

from pdf_rag.config import load_config
from pdf_rag.indexer import load_index
from pdf_rag.retriever import format_results

mcp = FastMCP("pdf-rag")

_index: VectorStoreIndex | None = None


def _get_index() -> VectorStoreIndex:
    global _index
    if _index is None:
        _index = load_index(load_config())
    return _index


@mcp.tool()
def search_pdfs(query: str) -> str:
    """Search indexed PDFs and return the most relevant text chunks with source citations."""
    config = load_config()
    try:
        index = _get_index()
    except FileNotFoundError as e:
        return f"Index not found: {e}. Run `python -m pdf_rag.cli index` first."
    retriever = index.as_retriever(similarity_top_k=config.top_k)
    nodes = retriever.retrieve(query)
    if not nodes:
        return "No matching chunks found."
    return format_results(nodes)


if __name__ == "__main__":
    mcp.run()
