# CCE v0.2 — Seven Improvements Design Spec

**Date:** 2026-04-18
**Scope:** Hybrid search, ONNX migration, token-aware packing, knowledge graph, git history search, benchmarks, web dashboard
**Branch:** `feature/cce-v02-improvements`

---

## 1. Hybrid Search (BM25 + Vector via RRF)

### Problem
Vector-only search misses exact keyword matches (e.g., searching for `calculate_tax` may rank semantically similar but wrong functions higher). All top competitors use hybrid search.

### Design

**New file:** `src/context_engine/storage/fts_store.py`

SQLite FTS5 full-text search store. Zero new dependencies (sqlite3 is stdlib).

```python
class FTSStore:
    def __init__(self, db_path: str) -> None
        # Creates SQLite DB at db_path/fts.db
        # CREATE VIRTUAL TABLE chunks_fts USING fts5(id, content, file_path, language, chunk_type)

    async def ingest(self, chunks: list[Chunk]) -> None
        # INSERT OR REPLACE into FTS table

    async def search(self, query: str, top_k: int = 30) -> list[tuple[str, float]]
        # Returns list of (chunk_id, bm25_score) using FTS5 rank function
        # SELECT id, rank FROM chunks_fts WHERE chunks_fts MATCH ? ORDER BY rank LIMIT ?

    async def delete_by_file(self, file_path: str) -> None
        # DELETE FROM chunks_fts WHERE file_path = ?
```

**Modified:** `local_backend.py`
- Initialize `FTSStore` at `base_path/fts`
- Dual-ingest: chunks go to both vector store and FTS store
- Expose `fts_search(query, top_k)` method
- `delete_by_file` deletes from both stores

**Modified:** `retriever.py`
- After getting vector results and FTS results, merge with Reciprocal Rank Fusion:
  ```
  rrf_score(doc) = sum(1 / (k + rank_i)) for each ranking that contains doc
  ```
  where k=60 (standard constant)
- Merged results then go through existing ConfidenceScorer for final ranking
- FTS results need chunk hydration (FTS returns IDs, fetch full chunks from vector store)

**Modified:** `backend.py` (protocol)
- Add `fts_search(query: str, top_k: int) -> list[tuple[str, float]]` to StorageBackend protocol

### Testing
- Test FTS ingest + search returns expected chunks
- Test RRF merging produces correct ordering
- Test that exact keyword matches rank higher than before

---

## 2. ONNX Runtime Migration + `uv tool install`

### Problem
PyTorch is ~2GB, Python 3.14 breaks .pth files for editable installs, and users struggle with venv management.

### Design

**Modified:** `src/context_engine/indexer/embedder.py`

Replace `SentenceTransformer` with ONNX Runtime inference:

```python
from optimum.onnxruntime import ORTModelForFeatureExtraction
from transformers import AutoTokenizer
import numpy as np

class Embedder:
    def __init__(self, model_name: str = "all-MiniLM-L6-v2") -> None:
        resolved = f"sentence-transformers/{model_name}" if "/" not in model_name else model_name
        self._tokenizer = AutoTokenizer.from_pretrained(resolved)
        self._model = ORTModelForFeatureExtraction.from_pretrained(resolved, export=True)
        # export=True auto-converts PyTorch weights to ONNX on first use

    def embed(self, chunks: list[Chunk]) -> None:
        texts = [c.content for c in chunks]
        inputs = self._tokenizer(texts, padding=True, truncation=True, return_tensors="np")
        outputs = self._model(**inputs)
        # Mean pooling over token embeddings
        embeddings = outputs.last_hidden_state.mean(axis=1)
        # L2 normalize
        norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
        embeddings = embeddings / norms
        for chunk, emb in zip(chunks, embeddings):
            chunk.embedding = emb.tolist()

    def embed_query(self, query: str) -> list[float]:
        inputs = self._tokenizer(query, return_tensors="np", truncation=True)
        outputs = self._model(**inputs)
        emb = outputs.last_hidden_state.mean(axis=1)[0]
        emb = emb / np.linalg.norm(emb)
        return emb.tolist()
```

**Modified:** `pyproject.toml`
- Replace dependencies:
  ```
  # Remove:
  sentence-transformers>=3.0
  
  # Add:
  optimum[onnxruntime]>=1.19
  onnxruntime>=1.17
  tokenizers>=0.19
  transformers>=4.41
  numpy>=1.24
  ```
- Change: `requires-python = ">=3.11"` (remove `<3.14` cap)
- Keep `sentence-transformers` as optional dep for backward compat:
  ```
  [project.optional-dependencies]
  torch = ["sentence-transformers>=3.0"]
  ```

**Modified:** `README.md`
- Primary install: `uv tool install claude-context-engine`
- Secondary: `pipx install claude-context-engine`
- Tertiary: `pip install claude-context-engine` (inside venv)
- Remove Python 3.14 warning (no longer needed)

**Modified:** `cli.py`
- Remove Python 3.14 version check/warning

### Testing
- Test embedding dimensions match previous (384 for MiniLM)
- Test that L2 distances are comparable to sentence-transformers output
- Test install size reduction

---

## 3. Token-Aware Packing

### Problem
Fixed `top_k` either wastes token budget (too few results) or overflows it (too many). Results should fill the available budget optimally.

### Design

**Modified:** `retriever.py`

Add `max_tokens` parameter to `retrieve()`:

```python
async def retrieve(
    self,
    query: str,
    top_k: int = 10,
    confidence_threshold: float = 0.0,
    max_tokens: int | None = None,  # NEW
) -> list[Chunk]:
    # ... existing vector search + scoring ...
    
    if max_tokens is not None:
        packed = []
        budget = max_tokens
        for chunk in scored_chunks:
            chunk_tokens = len(chunk.content) // 4  # ~4 chars per token
            if chunk_tokens <= budget:
                packed.append(chunk)
                budget -= chunk_tokens
            # Skip chunks that don't fit but keep trying smaller ones
        return packed
    
    return scored_chunks[:top_k]
```

**Modified:** `mcp_server.py`
- `context_search` tool accepts optional `max_tokens` input parameter (default: 8000)
- Pass to retriever

**Modified:** `models.py`
- Add `token_count` property to `Chunk`:
  ```python
  @property
  def token_count(self) -> int:
      text = self.compressed_content or self.content
      return len(text) // 4
  ```

### Testing
- Test that packed results total tokens <= budget
- Test that higher-confidence chunks are preferred
- Test edge case: single chunk exceeds budget

---

## 4. Knowledge Graph (SQLite)

### Problem
The graph store is fully stubbed. Nodes and edges are built during indexing but discarded. `related_context` MCP tool returns empty. Competitors use graphs for relationship-aware navigation.

### Design

**Modified:** `src/context_engine/storage/graph_store.py`

Replace no-ops with SQLite implementation:

```python
import sqlite3
import json

class GraphStore:
    def __init__(self, db_path: str) -> None:
        self._db_path = os.path.join(db_path, "graph.db")
        self._conn = sqlite3.connect(self._db_path)
        self._conn.execute("""
            CREATE TABLE IF NOT EXISTS nodes (
                id TEXT PRIMARY KEY,
                node_type TEXT NOT NULL,
                name TEXT NOT NULL,
                file_path TEXT NOT NULL,
                properties TEXT DEFAULT '{}'
            )
        """)
        self._conn.execute("""
            CREATE TABLE IF NOT EXISTS edges (
                source_id TEXT NOT NULL,
                target_id TEXT NOT NULL,
                edge_type TEXT NOT NULL,
                properties TEXT DEFAULT '{}',
                PRIMARY KEY (source_id, target_id, edge_type)
            )
        """)
        self._conn.execute("CREATE INDEX IF NOT EXISTS idx_edges_source ON edges(source_id)")
        self._conn.execute("CREATE INDEX IF NOT EXISTS idx_edges_target ON edges(target_id)")
        self._conn.execute("CREATE INDEX IF NOT EXISTS idx_nodes_file ON nodes(file_path)")
        self._conn.commit()

    async def ingest(self, nodes: list[GraphNode], edges: list[GraphEdge]) -> None:
        # INSERT OR REPLACE for both

    async def get_neighbors(self, node_id: str, edge_type: EdgeType | None = None) -> list[GraphNode]:
        # JOIN edges with nodes, optional edge_type filter

    async def get_nodes_by_file(self, file_path: str) -> list[GraphNode]:
        # SELECT WHERE file_path = ?

    async def get_nodes_by_type(self, node_type: NodeType) -> list[GraphNode]:
        # SELECT WHERE node_type = ?

    async def delete_by_file(self, file_path: str) -> None:
        # DELETE nodes and edges by file_path
```

**Modified:** `local_backend.py`
- Initialize `GraphStore` at `base_path/graph`
- Pass nodes/edges during ingest (currently discarded)
- Delegate `graph_neighbors()` to graph store (currently returns [])

**Modified:** `pipeline.py`
- Add `IMPORTS` edge detection:
  - Python: parse `import X` / `from X import Y` statements
  - JS/TS: parse `import ... from 'X'` / `require('X')` statements
  - Use regex (not AST) for simplicity — good enough for import patterns

**Modified:** `mcp_server.py`
- `related_context` tool now returns actual graph neighbors
- Format: list of related nodes with edge types

### Testing
- Test node/edge ingest and retrieval
- Test neighbor queries with edge type filtering
- Test delete_by_file removes associated nodes and edges
- Test import detection for Python and JS/TS

---

## 5. Git History Search

### Problem
No temporal context. Developers ask "what changed recently?" or "who modified the auth module?" and CCE can't answer.

### Design

**New file:** `src/context_engine/indexer/git_indexer.py`

```python
import subprocess
from context_engine.models import Chunk, ChunkType, GraphNode, NodeType, GraphEdge, EdgeType

def index_commits(
    project_dir: Path,
    max_commits: int = 200,
) -> tuple[list[Chunk], list[GraphNode], list[GraphEdge]]:
    """Parse recent git history into searchable chunks."""
    result = subprocess.run(
        ["git", "log", f"-{max_commits}",
         "--format=%H%n%an%n%ai%n%s%n%b%n---END---",
         "--stat"],
        cwd=project_dir, capture_output=True, text=True
    )
    # Parse output into Chunk objects:
    # - chunk_type = ChunkType.COMMIT
    # - content = commit message + file stats
    # - file_path = "git:SHORTHASH"
    # - metadata = {"author": ..., "date": ..., "hash": ...}
    #
    # Create GraphNode (NodeType.COMMIT) for each commit
    # Create MODIFIES edges from commit node to file nodes
```

**Modified:** `pipeline.py`
- During `full=True` indexing, call `git_indexer.index_commits()`
- Add resulting chunks to the embedding + ingest pipeline
- Add nodes/edges to graph store

**No MCP changes needed:** `context_search` already returns all chunk types. Commit chunks surface naturally for queries like "recent changes to auth" or "who modified payment logic."

### Testing
- Test parsing of git log output
- Test chunk creation with correct types and metadata
- Test integration with pipeline (commit chunks appear in search)

---

## 6. Benchmarks

### Problem
No published performance data. Competitors like SocratiCode publish concrete numbers that drive adoption.

### Design

**New directory:** `benchmarks/`

**New file:** `benchmarks/run_benchmark.py`

```python
"""Benchmark suite for CCE token savings, retrieval quality, and latency."""

def benchmark_token_savings(project_dir, queries):
    """Compare tokens served by CCE vs reading full files."""
    # For each query:
    # 1. Measure full-file token cost (sum of all file sizes in project)
    # 2. Run CCE context_search, measure served tokens
    # 3. Calculate savings percentage

def benchmark_precision_recall(project_dir, queries_with_expected):
    """Measure precision@k and recall@k against known-relevant files."""
    # For each query with expected file list:
    # 1. Run context_search
    # 2. Check if expected files appear in results
    # 3. Calculate precision = relevant_in_results / total_results
    # 4. Calculate recall = relevant_in_results / total_relevant

def benchmark_latency(project_dir, queries, iterations=50):
    """Measure search latency p50/p95/p99."""
    # Time each query, report percentiles

if __name__ == "__main__":
    # Run against sample repos, output markdown table
```

**New file:** `benchmarks/sample_queries.json`
- Curated queries with expected relevant files for CCE's own repo

**New file:** `docs/benchmarks.md`
- Published results table with methodology description

**No core code changes.** Benchmarks consume existing APIs.

### Testing
- Benchmarks are self-validating (assert non-zero savings, assert latency < threshold)

---

## 7. Web Dashboard

### Problem
No visual way to inspect the index, debug search results, or view savings. Competitors offer web UIs.

### Design

**New directory:** `src/context_engine/dashboard/`

**New file:** `src/context_engine/dashboard/app.py`

FastAPI application with API routes:

```python
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

app = FastAPI(title="CCE Dashboard")

@app.get("/api/stats")
async def get_stats():
    """Return query count, token savings, index info."""

@app.get("/api/search")
async def search(q: str, top_k: int = 10):
    """Run context_search and return results with scores."""

@app.get("/api/chunks")
async def get_chunks(file: str):
    """Return all indexed chunks for a given file."""

@app.get("/api/graph")
async def get_graph(node_id: str):
    """Return graph neighbors for a node."""

@app.get("/api/files")
async def list_files():
    """Return all indexed files with chunk counts."""

@app.get("/")
async def index():
    return FileResponse("static/index.html")
```

**New file:** `src/context_engine/dashboard/static/index.html`

Single-page app with vanilla JS + CSS:
- **Search tab:** Query input, results with highlighted scores, expandable chunks
- **Files tab:** File tree with chunk counts, click to view chunks
- **Graph tab:** Node list, click to see neighbors and edges
- **Stats tab:** Savings chart (queries over time), token usage breakdown

**Modified:** `cli.py`
- Add `cce dashboard` command:
  ```python
  @cli.command()
  @click.option("--port", default=9400)
  def dashboard(port):
      """Launch the CCE web dashboard."""
      import uvicorn
      from context_engine.dashboard.app import create_app
      app = create_app(storage_base=..., config=...)
      uvicorn.run(app, host="127.0.0.1", port=port)
  ```

**Modified:** `pyproject.toml`
- Add optional dependency group:
  ```toml
  [project.optional-dependencies]
  dashboard = ["fastapi>=0.110", "uvicorn>=0.29"]
  ```

### Testing
- Test API endpoints return correct status codes and shapes
- Test that dashboard starts and serves index.html

---

## Implementation Order

These features are independent and can be implemented in parallel. Suggested order for serial execution:

1. **ONNX migration** (unblocks Python 3.14 users, reduces install friction)
2. **Hybrid search** (biggest search quality improvement)
3. **Token-aware packing** (small change, high impact)
4. **Knowledge graph** (enables related_context tool)
5. **Git history search** (small, depends on graph store for edges)
6. **Benchmarks** (validates all search improvements)
7. **Web dashboard** (nice-to-have, depends on graph + search working)

---

## Out of Scope

- Remote backend implementation (future work)
- Additional language support beyond current 7 (separate PR)
- Authentication/multi-user for dashboard (local-only tool)
- CI/CD changes beyond benchmark publishing
