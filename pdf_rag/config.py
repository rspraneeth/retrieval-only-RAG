"""Load and validate project configuration."""

from dataclasses import dataclass
from pathlib import Path

import yaml

DEFAULT_CONFIG_PATH = Path(__file__).resolve().parent.parent / "config.yaml"


@dataclass(frozen=True)
class Config:
    pdf_folder: Path
    vector_store: Path
    embedding_model: str
    top_k: int


def load_config(config_path: Path | None = None) -> Config:
    path = config_path or DEFAULT_CONFIG_PATH
    if not path.is_file():
        raise FileNotFoundError(f"Config file not found: {path}")

    with path.open(encoding="utf-8") as f:
        raw = yaml.safe_load(f) or {}

    project_root = path.parent
    pdf_folder = Path(raw.get("pdf_folder", "pdfs"))
    vector_store = Path(raw.get("vector_store", "vector_store"))
    if not pdf_folder.is_absolute():
        pdf_folder = project_root / pdf_folder
    if not vector_store.is_absolute():
        vector_store = project_root / vector_store
    embedding_model = raw.get("embedding_model", "BAAI/bge-small-en-v1.5")
    top_k = raw.get("top_k", 5)

    if not pdf_folder.is_dir():
        raise ValueError(f"PDF folder does not exist: {pdf_folder}")

    if not isinstance(top_k, int) or top_k < 1 or top_k > 20:
        raise ValueError(f"top_k must be an integer between 1 and 20, got {top_k!r}")

    return Config(
        pdf_folder=pdf_folder,
        vector_store=vector_store,
        embedding_model=embedding_model,
        top_k=top_k,
    )
