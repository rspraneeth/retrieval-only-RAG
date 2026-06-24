"""CLI for indexing PDFs and searching the vector store."""

import argparse
import sys
from pathlib import Path

from pdf_rag.config import load_config
from pdf_rag.indexer import build_index
from pdf_rag.retriever import format_results, search


def _cmd_index(config_path: Path | None) -> int:
    config = load_config(config_path)
    try:
        _, file_count, chunk_count = build_index(config)
    except ValueError as e:
        print(f"index: {e}")
        return 1
    if chunk_count == 0:
        print(f"All {file_count} PDF(s) up to date — nothing to index.")
    else:
        print(f"Indexed {file_count} PDF(s) — {chunk_count} new chunk(s).")
    print(f"Vector store: {config.vector_store}")
    return 0


def _cmd_search(config_path: Path | None, query: str) -> int:
    config = load_config(config_path)
    try:
        nodes = search(config, query)
    except FileNotFoundError as e:
        print(f"search: {e}")
        return 1
    if not nodes:
        print("No matching chunks found.")
        return 0
    print(format_results(nodes))
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="PDF retrieval tool (no generation).")
    parser.add_argument(
        "--config",
        type=Path,
        default=None,
        help="Path to config.yaml (default: project root config.yaml)",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("index", help="Load PDFs, chunk, embed, and persist the index")

    search_parser = sub.add_parser("search", help="Retrieve top-k chunks for a question")
    search_parser.add_argument("query", help="Natural-language question")

    args = parser.parse_args(argv)
    if args.command == "index":
        return _cmd_index(args.config)
    if args.command == "search":
        return _cmd_search(args.config, args.query)
    return 1


if __name__ == "__main__":
    sys.exit(main())
