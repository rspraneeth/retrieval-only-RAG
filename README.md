# retrieval-only-RAG

A PDF retrieval tool wrapped as an MCP server. It handles the **R** in RAG — your IDE agent (Cursor, Kiro, Claude Code) handles generation.

```
PDFs ──> [ load → chunk → embed → store → retrieve ]
                          │
                 returns matching chunks
                          │
              [ MCP server wraps the retriever ]
                          │
     IDE agent calls it ──┘  →  IDE agent writes the answer
```

No LLM inside this tool. Embeddings run locally (no cloud key needed).

---

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate        # Windows
pip install -r requirements.txt
```

---

## Usage

**Index your PDFs** — drop PDF files into `pdfs/` then run:

```bash
python -m pdf_rag.cli index
```

Only new or changed PDFs are processed on subsequent runs — unchanged files are skipped. Deleted PDFs have their chunks removed automatically.

**Search** — retrieve the top-k chunks for a question:

```bash
python -m pdf_rag.cli search "What is the difference between ArrayList and LinkedList?"
```

Output includes source filename, page number, and similarity score for each chunk.

---

## MCP Server

Exposes one tool — `search_pdfs(query)` — that any MCP-compatible IDE agent can call.

```bash
python mcp_server.py
```

### Claude Code (`.mcp.json` in project root)

A `.mcp.json` is already included in this repo:

```json
{
  "mcpServers": {
    "pdf-rag": {
      "command": "C:\\Projects\\Retrieval\\.venv\\Scripts\\python.exe",
      "args": ["C:\\Projects\\Retrieval\\mcp_server.py"],
      "cwd": "C:\\Projects\\Retrieval"
    }
  }
}
```

Update the paths to match your machine, then Claude Code picks it up automatically.

### Cursor (`.cursor/mcp.json`)

```json
{
  "mcpServers": {
    "pdf-rag": {
      "command": "path/to/.venv/Scripts/python.exe",
      "args": ["path/to/mcp_server.py"],
      "cwd": "path/to/project"
    }
  }
}
```

Once connected, ask your IDE agent a question about your PDFs — it calls `search_pdfs`, gets the chunks, and writes the answer. You own retrieval; the agent owns generation.

---

## Configuration (`config.yaml`)

```yaml
pdf_folder: pdfs              # folder to scan for PDFs
vector_store: vector_store    # where ChromaDB persists the index
embedding_model: BAAI/bge-small-en-v1.5   # local HuggingFace model
top_k: 5                      # chunks returned per query
```

---

## Project structure

```
pdf_rag/
  config.py      # load + validate config.yaml
  indexer.py     # PDF loading, chunking, embedding, ChromaDB persistence
  retriever.py   # similarity search + result formatting
  cli.py         # index / search commands
mcp_server.py    # MCP wrapper exposing search_pdfs()
config.yaml
requirements.txt
.mcp.json        # Claude Code MCP config (update paths for your machine)
pdfs/            # drop your PDFs here (not committed)
vector_store/    # ChromaDB index + manifest.json (not committed)
```

---

## How the RAG split works

| Layer | Who does it | How |
|---|---|---|
| Retrieval | This tool | LlamaIndex + ChromaDB + local embeddings |
| Augmentation | MCP protocol | Retrieved chunks injected into agent context |
| Generation | IDE agent | Cursor / Kiro / Claude Code answers from chunks |

The MCP server is editor-agnostic — swap Cursor for Kiro (or any MCP client) by changing only the connection config, no code changes needed.
