"""MCP server exposing PDF retrieval as a tool for IDE agents."""

from mcp.server.fastmcp import FastMCP

from pdf_rag.config import load_config
from pdf_rag.retriever import format_results, search

mcp = FastMCP("pdf-rag")


@mcp.tool()
def search_pdfs(query: str) -> str:
    """Search indexed PDFs and return the most relevant text chunks with source citations."""
    config = load_config()
    try:
        nodes = search(config, query)
    except FileNotFoundError as e:
        return f"Index not found: {e}. Run `python -m pdf_rag.cli index` first."
    if not nodes:
        return "No matching chunks found."
    return format_results(nodes)


if __name__ == "__main__":
    mcp.run()
