# PDF Q&A Demo — Build Plan

A retrieval-only RAG tool over plain-text PDFs, wrapped as an MCP server, with
Cursor's agent doing the answer generation. This is a **demo / rehearsal** for the
real templates project: same Path B architecture (retrieval is yours, generation is
the IDE agent's, MCP is the wire), on harmless personal PDFs.

**Build order matters:** get retrieval working *standalone* and returning good chunks
*before* you add the MCP layer. Don't wire MCP until retrieval is proven, or you'll be
debugging two things at once.

---

## Architecture (what you're building)

```
   PDFs ──> [ your tool: load → chunk → embed → store → retrieve ]  ← LlamaIndex, local
                                   │
                          returns matching chunks
                                   │
                        [ MCP server wraps the retriever ]
                                   │
        Cursor's agent calls it ───┘   → Cursor writes the answer from the chunks
```

- **Your tool** does R (retrieval). No model inside it.
- **MCP server** is a thin wrapper so Cursor can call the retriever automatically.
- **Cursor's agent** does G (generation) — stands in for Kiro in the real project.
- **Embeddings** run locally (small model, no LLM server needed for retrieval).

---

## Phase 1 — Retrieval tool (build and prove this first)

- [ ] **1. Scaffold the project**
  - Create the package layout and a `requirements.txt` with pinned versions
    (llama-index, the local embedding dependency, pypdf or similar for PDF text).
  - Add `.gitignore` excluding the vector store directory and any local data.
  - Add a `pdfs/` folder to drop test PDFs into (a few plain text PDFs to develop against).

- [ ] **2. Configuration**
  - A small config (YAML or simple Python) for: PDF folder path, vector store path,
    embedding model name, `top_k` (how many chunks to return).
  - Validate the PDF folder exists and `top_k` is sane (1–20).

- [ ] **3. PDF loading + generic chunking**
  - Use LlamaIndex's PDF reader to extract text from each PDF in the folder.
  - Use LlamaIndex's default/generic node parser to chunk (no custom rules yet —
    template-specific chunking is deliberately deferred).
  - Carry metadata per chunk: source filename + page/position, so citations work later.

- [ ] **4. Local embedding + vector store**
  - Configure LlamaIndex to use a **local** embedding model (e.g. a HuggingFace
    embedding via `llama-index-embeddings-huggingface`) — no cloud key needed.
  - Persist the index to disk in the vector store path; load it on startup without
    re-indexing.

- [ ] **5. Indexer command**
  - An `index` command/script that runs load → chunk → embed → store and reports
    how many files and chunks were processed.
  - Handle the empty-folder case (report it, don't create a broken store).

- [ ] **6. Retriever (the core deliverable of Phase 1)**
  - A `search "<question>"` command that loads the index, retrieves the top_k chunks,
    and **prints them with their source filename + page**.
  - This is the proof point: run it, eyeball the chunks, confirm they're relevant.
  - ✅ **Stop here and verify retrieval quality before moving on.** If the chunks
    coming back are wrong, fix that now — MCP won't help if retrieval is bad.

---

## Phase 2 — MCP wrapper (only after Phase 1 returns good chunks)

- [ ] **7. Expose the retriever as an MCP server**
  - Wrap the Phase 1 retriever as an MCP server exposing one tool, e.g.
    `search_pdfs(query) -> list of chunks with citations`.
  - Keep the server **editor-agnostic** — it's just an MCP server; any MCP client can
    call it. (This is what lets Kiro connect later in the real project with only config,
    no rebuild.)
  - Test the server in isolation first (most MCP setups have a way to call the tool
    directly / via an inspector) before connecting any editor.

- [ ] **8. Connect Cursor to the MCP server**
  - Add the server to Cursor's MCP configuration.
  - Confirm Cursor lists the `search_pdfs` tool as available.

- [ ] **9. End-to-end demo**
  - In Cursor, ask a natural-language question about your PDFs.
  - Confirm Cursor calls `search_pdfs`, gets your chunks, and writes an answer that
    cites the source PDFs.
  - This is the demo: "IDE agent + my MCP retrieval tool, answering from a private
    corpus." That's the pattern that transfers to templates.

---

## Deliberately deferred (layer on later, behind what you build now)

- Template-specific chunking (base-zone delimiters, x_OLD exclusion, channel
  metadata) — slots in behind the Phase 1 chunking step.
- A model *inside* the tool (Path A) — not needed; Cursor/Kiro does generation.
- Swapping Cursor → Kiro for the real project — same MCP server, re-do only the
  editor-side config.
- Team distribution.

---

## Notes on what transfers to the real templates project

- ✅ **Transfers cleanly:** the retrieval tool shape, the MCP server design, and the
  proof that "IDE agent + my MCP retrieval tool" works end to end.
- ⚠️ **Re-done per editor:** the MCP connection config (Cursor here, Kiro there). The
  *pattern* is identical; the wiring is editor-specific.
- ⚠️ **Different corpus rules:** PDFs use generic chunking; templates need custom
  chunking. Built behind the same interface, so it's an addition, not a rewrite.
- 🔒 **Governance reminder for the real one:** this demo is on personal PDFs (no
  constraint). The real project runs on Spectrum-via-Infosys template content — confirm
  with whoever owns data policy that routing retrieved template chunks through Kiro is
  approved before pointing it at real templates.

---

## How to drive Cursor through this

Prime it once, then go task by task — don't ask for the whole thing at once:

> Read PDF-RAG-DEMO-tasks.md so you understand the project. Then implement task 1
> only, and stop for my review.

After each task review, continue to the next. Verify Phase 1 retrieval returns good
chunks before letting it start Phase 2.
