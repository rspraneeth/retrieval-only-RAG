"""Retrieve top-k chunks for a question."""

from llama_index.core.schema import NodeWithScore

from pdf_rag.config import Config
from pdf_rag.indexer import load_index


def search(config: Config, query: str) -> list[NodeWithScore]:
    index = load_index(config)
    retriever = index.as_retriever(similarity_top_k=config.top_k)
    return retriever.retrieve(query)


def format_results(nodes: list[NodeWithScore]) -> str:
    lines: list[str] = []
    for i, node_with_score in enumerate(nodes, start=1):
        node = node_with_score.node
        meta = node.metadata
        file_name = meta.get("file_name", meta.get("file_path", "unknown"))
        page = meta.get("page_label", meta.get("page_number", "?"))
        score = node_with_score.score
        score_str = f"{score:.4f}" if score is not None else "n/a"
        lines.append(f"--- result {i} (score {score_str}) ---")
        lines.append(f"source: {file_name}, page: {page}")
        lines.append(node.get_content())
        lines.append("")
    return "\n".join(lines)
