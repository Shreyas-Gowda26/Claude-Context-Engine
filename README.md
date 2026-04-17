# Claude Context Engine

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![MCP Compatible](https://img.shields.io/badge/MCP-compatible-green.svg)](https://modelcontextprotocol.io)
[![GitHub stars](https://img.shields.io/github/stars/fazleelahhee/Claude-Context-Engine?style=social)](https://github.com/fazleelahhee/Claude-Context-Engine)
[![GitHub forks](https://img.shields.io/github/forks/fazleelahhee/Claude-Context-Engine?style=social)](https://github.com/fazleelahhee/Claude-Context-Engine/fork)
[![GitHub issues](https://img.shields.io/github/issues/fazleelahhee/Claude-Context-Engine)](https://github.com/fazleelahhee/Claude-Context-Engine/issues)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](https://github.com/fazleelahhee/Claude-Context-Engine/pulls)

A local context indexing system for [Claude Code](https://docs.anthropic.com/en/docs/claude-code) that indexes your codebase, compresses context, and serves it via MCP — so Claude starts every session already knowing your project.

## The Problem

Every time you start a new Claude Code session, Claude has no memory of your project. It re-reads files, re-discovers architecture, and burns tokens understanding code it has seen before. On large codebases, this startup cost adds up fast.

## How It Works

Claude Context Engine runs as a background daemon that:

1. **Indexes** your codebase using AST-aware chunking (tree-sitter) and semantic embeddings
2. **Stores** chunks in a vector database (LanceDB) with a knowledge graph (Kuzu) tracking relationships between functions, classes, and files
3. **Compresses** context using a local LLM (Ollama) or smart truncation, so Claude gets more information in fewer tokens
4. **Serves** the indexed context to Claude Code over MCP (Model Context Protocol), giving Claude instant access to search, graph traversal, and session history

```
Your Code
  │
  ▼
┌─────────────┐    ┌──────────────┐    ┌─────────────┐
│  Tree-sitter │───▶│   LanceDB    │───▶│  MCP Server │───▶ Claude Code
│  Chunker     │    │   + Kuzu     │    │  (stdio)    │
└─────────────┘    └──────────────┘    └─────────────┘
  │                                          ▲
  ▼                                          │
┌─────────────┐                    ┌─────────────────┐
│  Embedder   │                    │  Compressor      │
│  (MiniLM)   │                    │  (Ollama/trunc)  │
└─────────────┘                    └─────────────────┘
```

## Key Benefits

### Save Context Window Tokens
- Compressed summaries replace full file reads — Claude gets the same understanding in 60-80% fewer tokens
- Confidence scoring surfaces only the most relevant chunks, avoiding noise
- Progressive disclosure: Claude gets summaries first, expands to full code only when needed

### Faster Session Startup
- No more "let me read through the codebase" at the start of every conversation
- The bootstrap context gives Claude an instant project overview: architecture, recent changes, key decisions
- Incremental indexing means only changed files get re-processed

### Persistent Project Memory
- Session history captures decisions, code areas explored, and questions asked
- Graph relationships track which functions call what, which files import which modules
- Past sessions are searchable — Claude can recall "why did we choose X over Y?"

### Works Locally, No Cloud Required
- All data stays on your machine (or your own remote server)
- Embeddings run locally via sentence-transformers
- Compression uses Ollama (local LLM) with smart truncation fallback
- Optional remote mode offloads heavy computation to a more powerful machine via SSH

## Installation

### Prerequisites

- Python 3.11+
- [CMake](https://cmake.org/) (for building Kuzu graph database)

```bash
# macOS
brew install cmake

# Ubuntu/Debian
sudo apt install cmake
```

### Install

```bash
# Clone the repository
git clone git@github.com:fazleelahhee/Claude-Context-Engine.git
cd Claude-Context-Engine

# Create a virtual environment
python -m venv .venv
source .venv/bin/activate

# Install in editable mode
pip install -e .

# With dev dependencies (for running tests)
pip install -e ".[dev]"
```

### Optional: Install Ollama for LLM Compression

Without Ollama, the engine falls back to smart truncation (signature extraction + trimming). With Ollama, it produces higher-quality summaries.

```bash
# macOS
brew install ollama
ollama pull phi3:mini
```

## Quick Start

### 1. Initialize Your Project

```bash
cd /path/to/your/project
claude-context-engine init
```

This will:
- Install git hooks for automatic re-indexing on commits
- Create a storage directory at `~/.claude-context-engine/projects/<project-name>/`
- Run the initial full index

### 2. Connect to Claude Code

Add the MCP server to your project's `.mcp.json`:

```json
{
  "mcpServers": {
    "context-engine": {
      "command": "/path/to/your/.venv/bin/claude-context-engine",
      "args": ["serve"]
    }
  }
}
```

Restart Claude Code. The context engine tools will now be available.

### 3. Use It

Once connected, Claude Code automatically has access to these tools:

| Tool | What It Does |
|------|-------------|
| `context_search` | Semantic search across your indexed codebase |
| `expand_chunk` | Get the full source code for a compressed chunk |
| `related_context` | Find related code via graph relationships |
| `session_recall` | Recall past decisions and discussions |
| `index_status` | Check when the index was last updated |
| `reindex` | Trigger re-indexing of a file or the entire project |

## Configuration

### Global Config

`~/.claude-context-engine/config.yaml`:

```yaml
remote:
  enabled: false
  host: "user@your-server"
  fallback_to_local: true

compression:
  level: standard        # minimal | standard | full
  model: phi3:mini       # Ollama model for compression

embedding:
  model: all-MiniLM-L6-v2

retrieval:
  confidence_threshold: 0.5
  top_k: 20
  bootstrap_max_tokens: 10000

indexer:
  watch: true
  debounce_ms: 500
  ignore:
    - .git
    - node_modules
    - __pycache__
    - .venv
    - .env

storage:
  path: ~/.claude-context-engine/projects
```

### Per-Project Overrides

Create `.context-engine.yaml` in your project root to override any global setting:

```yaml
compression:
  level: full

indexer:
  ignore:
    - .git
    - node_modules
    - dist
    - coverage
```

### Resource Profiles

The engine auto-detects your machine's resources and adjusts accordingly:

| Profile | RAM | Behavior |
|---------|-----|----------|
| **light** | < 12 GB | Minimal compression, smaller embedding batches |
| **standard** | 12-32 GB | Full local pipeline |
| **full** | 32+ GB or remote | All features enabled, larger models |

## CLI Commands

```bash
claude-context-engine init            # Initialize project + first index
claude-context-engine index           # Re-index project
claude-context-engine index --full    # Force full re-index (ignore cache)
claude-context-engine index --path src/  # Index specific directory
claude-context-engine status          # Show index stats and config
claude-context-engine serve           # Start MCP server (used by Claude Code)
claude-context-engine serve-http      # Start HTTP API (for remote mode)
claude-context-engine remote-setup    # Set up remote server
```

## Remote Mode

For machines with limited resources, you can offload the database and LLM compression to a remote server:

```yaml
# config.yaml
remote:
  enabled: true
  host: "user@your-server"
  fallback_to_local: true

compression:
  remote_model: llama3:8b  # Use a bigger model on the server
```

The engine will SSH into the remote, run queries there, and fall back to local if the server is unreachable.

## Performance Tips

- **Run `init` once per project** — subsequent indexing is incremental (only changed files)
- **Use `standard` compression** — it balances quality and speed. `minimal` is faster but loses more detail
- **Keep `indexer.watch: true`** — the file watcher auto-reindexes on save with debouncing
- **Git hooks handle the rest** — post-commit hooks trigger re-indexing automatically
- **Remote mode for laptops** — offload heavy computation to a server and keep your local machine responsive

## Supported Languages

AST-aware chunking (tree-sitter):
- Python
- JavaScript
- TypeScript (including JSX/TSX)

Fallback chunking (full-file):
- Markdown
- Any other text file with supported extensions

## How Context Savings Work

Without the context engine, a typical Claude Code session on a medium project (~500 files) might:
- Read 20-30 files to understand the codebase (~50k tokens)
- Re-discover architecture each session
- Lose all session context between conversations

With the context engine:
- Claude gets a compressed bootstrap context (~10k tokens) covering the full project
- Semantic search retrieves only relevant chunks instead of full files
- Session decisions persist and are recallable
- Graph traversal finds related code without reading entire dependency chains

## Development

```bash
# Run tests
pytest

# Run tests with coverage
pytest --cov=context_engine

# Run a specific test
pytest tests/integration/test_end_to_end.py
```

## Contributing

Contributions are welcome! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

1. Fork the repo
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'feat: add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## Roadmap

- [ ] Tree-sitter support for Go, Rust, Java, C/C++
- [ ] Web dashboard for index inspection
- [ ] PyPI package publishing
- [ ] GitHub Actions CI pipeline
- [ ] Persistent session search across projects
- [ ] Smarter graph edge detection (call graph, import resolution)

## License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- [Claude Code](https://docs.anthropic.com/en/docs/claude-code) by Anthropic
- [Model Context Protocol (MCP)](https://modelcontextprotocol.io) for the integration standard
- [LanceDB](https://lancedb.com/) for vector storage
- [Kuzu](https://kuzudb.com/) for the graph database
- [Tree-sitter](https://tree-sitter.github.io/) for AST parsing
- [Ollama](https://ollama.com/) for local LLM compression

---

If this project helps you, give it a star! It helps others discover it.
