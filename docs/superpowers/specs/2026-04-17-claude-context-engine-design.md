# claude-context-engine — Design Spec

A local daemon that indexes projects into vector + graph databases, uses local/remote LLM for context compression, and integrates with Claude Code via bootstrap hooks + MCP server. Reduces token cost while improving response quality.

## Architecture

Modular monolith in Python. Single daemon process with swappable modules communicating through a shared event bus.

```
Project Files / Git / Docs
        |
        v
   +-----------+
   |  Indexer   |---- file watcher / git hooks / manual CLI
   +-----+-----+
         |
         v
+------------------+
|  Storage Layer   |
|  +------------+  |
|  |  LanceDB   |  |  <- vectors (code chunks, docs, session history)
|  +------------+  |
|  +------------+  |
|  |   Kuzu     |  |  <- relationships (calls, imports, decisions, sessions)
|  +------------+  |
+--------+---------+
         |
         v
   +-----------+
   | Retriever |---- hybrid vector + graph search + confidence scoring
   +-----+-----+
         |
         v
   +-------------+
   | Compressor  |---- local/remote LLM (Ollama) summarization
   +------+------+
         |
         v
   +--------------+
   | Integration  |
   |  +--------+  |
   |  |  MCP   |  |  <- on-demand retrieval during session
   |  | Server |  |
   |  +--------+  |
   |  +--------+  |
   |  | Hooks  |  |  <- bootstrap context on session start
   |  +--------+  |
   +--------------+
```

### Remote Compute

Heavy workloads (DB queries, LLM summarization) can be offloaded to a remote server.

- Remote server: `ssh fazle@198.162.2.2`
- On session start, engine checks if remote is enabled and reachable
- If available: DB + LLM run on remote, results returned via SSH tunnel / HTTP API
- If unavailable: graceful fallback to local processing
- Remote can run larger models (7-13B) for better compression quality

## Module 1: Indexer

### Ingestion Modes

- **File watcher** — Uses `watchdog`. Debounces at 500ms. Respects `.gitignore` + `.contextignore`.
- **Git hooks** — Post-commit, post-checkout, post-merge. Targets only changed files. Installed via `claude-context-engine init`.
- **Manual CLI** — `claude-context-engine index [--full | --path <path>]`

### What Gets Indexed

- Source code — chunked by AST via tree-sitter into functions, classes, modules
- Docs — markdown, comments, docstrings
- Git metadata — commit messages, authors, file history, branch info
- Session history — past Claude conversations captured from hooks

### Chunking Strategy

AST-aware chunking using tree-sitter. Each chunk gets:

- A vector embedding (sentence-transformers `all-MiniLM-L6-v2`)
- Graph nodes/edges in Kuzu (function->calls->function, file->imports->file, etc.)
- Metadata (file path, last modified, git blame, language)

### Incremental Indexing

Only re-processes files whose content hash has changed. Maintains a manifest of `{file_path: content_hash}` to diff against.

## Module 2: Storage

### Backend Abstraction

```python
class StorageBackend(Protocol):
    async def vector_search(query, filters, top_k) -> list[Chunk]
    async def graph_query(cypher_query) -> list[Node | Edge]
    async def ingest(chunks, relationships) -> None

class LocalBackend(StorageBackend): ...   # direct DB access
class RemoteBackend(StorageBackend): ...  # SSH tunnel / HTTP API to remote
```

Engine picks the backend at startup based on config + reachability check.

### VectorStore (LanceDB)

- Stores embeddings for code chunks, docs, session history
- Supports filtered similarity search (by file, language, recency)
- Local path: `~/.claude-context-engine/projects/<project>/vectors/`
- Remote: queries forwarded to server via API

### GraphStore (Kuzu)

- **Nodes:** `Function`, `Class`, `File`, `Module`, `Doc`, `Commit`, `Session`, `Decision`
- **Edges:** `CALLS`, `IMPORTS`, `DEFINES`, `MODIFIES`, `DISCUSSED_IN`, `DECIDED`
- Enables queries like "what functions are affected by this module?" or "what did we decide about auth last session?"
- Local path: `~/.claude-context-engine/projects/<project>/graph/`
- Remote: queries forwarded to server

## Module 3: Retrieval

### Hybrid Retrieval Pipeline

**Step 1 — Query understanding:**
- Vector embedding of the query
- Keyword extraction for graph traversal
- Intent classification (code lookup vs. decision recall vs. architectural question)

**Step 2 — Dual retrieval:**
- Vector search (LanceDB) -> top-K similar chunks by embedding distance
- Graph traversal (Kuzu) -> structurally related nodes
- Results merged and deduplicated

**Step 3 — Confidence scoring (0.0 - 1.0):**
Based on:
- Vector similarity distance
- Graph hop distance from query target
- Recency (recent code/decisions weighted higher)
- Session relevance (discussed before in related sessions?)

**Step 4 — Tiered response:**

| Confidence | Action |
|---|---|
| High (>0.8) | Compress via local LLM, include in context |
| Medium (0.5-0.8) | Compress + flag as "may need drill-down" |
| Low (<0.5) | Exclude from bootstrap. Available via MCP drill-down |

**Step 5 — Drill-down via MCP:**
Claude can always request more context during the session using MCP tools. No quality ceiling.

## Module 4: Compression

### Compression Pipeline

1. Retrieved chunks grouped by category (code, docs, decisions, session history)
2. Each group sent to local LLM (Ollama) with tailored prompts:
   - Code: "Summarize what this function does, its signature, inputs/outputs, and side effects"
   - Decisions: "Summarize the decision, reasoning, and outcome"
   - Architecture: "Summarize the component, its role, and dependencies"
3. Output is a structured context block with metadata

### Compression Levels

| Level | What Claude gets | Token usage |
|---|---|---|
| Minimal | Function signatures + one-line descriptions + decision summaries | ~2-5K tokens |
| Standard | Above + key implementation details + relevant session history | ~5-15K tokens |
| Full | Above + expanded code blocks + full decision context | ~15-30K tokens |

### Quality Safeguards

- **Original always preserved** — Compression is a view, never destructive. `expand_chunk` via MCP returns real code.
- **Lossy detection** — After compression, check if summary mentions the same key identifiers (function names, variables, types) as original. If not, retry with less aggressive compression.
- **Bypass option** — Critical chunks (high graph centrality, frequently accessed) skip compression and send original.

### Remote Mode

When `fazle@198.162.2.2` is available, summarization runs there with a larger model (7-13B) for better quality.

## Module 5: Integration

### Bootstrap Hook (Session Start)

On every new Claude Code session, a `SessionStart` hook:

1. Detects current project directory
2. Checks remote server reachability
3. Picks backend (remote or local)
4. Builds bootstrap context payload:
   - Project summary (architecture, key components, tech stack)
   - Recent changes (last N commits, uncommitted changes)
   - Active decisions/context from past sessions
   - Relevant open issues/TODOs
5. Compresses to configured level
6. Injects into session as system context

**Bootstrap payload structure:**
```
## Project: <name>
### Architecture
<compressed overview, key components and their relationships>

### Recent Activity
<last N commits summarized, uncommitted changes>

### Active Context
<decisions made in recent sessions, ongoing work>

### Key Relationships
<most-connected modules, critical dependencies>
```

### MCP Server (During Session)

| Tool | Purpose |
|---|---|
| `context_search(query)` | Free-text search across code, docs, history |
| `expand_chunk(chunk_id)` | Get full original for a compressed chunk |
| `related_context(chunk_id)` | Follow graph edges — what's connected |
| `session_recall(topic)` | Past discussions and decisions on a topic |
| `index_status()` | Check freshness — when was the last index run |
| `reindex(path?)` | Trigger re-indexing of a file or full project |

### Session Capture

At session end (or periodically), captures:
- Key decisions made
- Code areas discussed
- Questions asked and answers given
- Stores back into vector + graph DBs for future sessions

### CLI Commands

```
claude-context-engine init          # Set up project (install hooks, initial index)
claude-context-engine index         # Manual full/partial re-index
claude-context-engine status        # Show index freshness, DB stats, remote status
claude-context-engine config        # Set compression level, remote server, model, etc
claude-context-engine serve         # Start MCP server + daemon
claude-context-engine remote-setup  # Install engine on remote server via SSH
```

## Module 6: Configuration

### Global Config (`~/.claude-context-engine/config.yaml`)

```yaml
remote:
  enabled: true
  host: "fazle@198.162.2.2"
  fallback_to_local: true

compression:
  level: "standard"          # minimal | standard | full
  model: "phi3:mini"         # Ollama model for summarization
  remote_model: "llama3:8b"  # Larger model when using remote

embedding:
  model: "all-MiniLM-L6-v2"

retrieval:
  confidence_threshold: 0.5
  top_k: 20
  bootstrap_max_tokens: 10000

indexer:
  watch: true
  debounce_ms: 500
  ignore: [".git", "node_modules", "__pycache__", ".venv"]

storage:
  path: "~/.claude-context-engine/projects/"
```

### Per-Project Override (`.context-engine.yaml`)

```yaml
compression:
  level: "full"
indexer:
  ignore: ["dist", "build", "*.generated.ts"]
  languages: ["python", "typescript"]
```

### Resource Profiles (auto-detected or manual)

| Profile | RAM | LLM | When |
|---|---|---|---|
| Light | 8 GB machine | No local LLM, smart chunking only | Auto if <10 GB free RAM |
| Standard | 16 GB machine | 3B model local | Default |
| Full | 32 GB+ or remote | 7-13B model | Remote enabled or beefy machine |

## Technology Stack

- **Language:** Python 3.11+
- **Vector DB:** LanceDB (embedded, file-based)
- **Graph DB:** Kuzu (embedded, like SQLite for graphs)
- **Embeddings:** sentence-transformers (`all-MiniLM-L6-v2`)
- **Local LLM:** Ollama (Phi-3 Mini 3.8B default, larger on remote)
- **AST parsing:** tree-sitter
- **File watching:** watchdog
- **MCP server:** Python MCP SDK
- **Remote communication:** SSH tunnel + lightweight HTTP API
