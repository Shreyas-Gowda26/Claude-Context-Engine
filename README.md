<p align="center">
  <img src="docs/logo.svg" alt="Claude Context Engine" width="160">
</p>

<h1 align="center">Claude Context Engine</h1>

<p align="center">
  <strong>Index your codebase. Compress context. Cut token costs by 70%.</strong>
</p>

<p align="center">
  <a href="https://pypi.org/project/claude-context-engine/"><img src="https://img.shields.io/pypi/v/claude-context-engine?color=blue&label=PyPI" alt="PyPI"></a>
  <a href="https://www.python.org/downloads/"><img src="https://img.shields.io/badge/python-3.11+-blue.svg" alt="Python 3.11+"></a>
  <a href="https://modelcontextprotocol.io"><img src="https://img.shields.io/badge/MCP-compatible-green.svg" alt="MCP Compatible"></a>
  <a href="https://opensource.org/licenses/MIT"><img src="https://img.shields.io/badge/License-MIT-yellow.svg" alt="MIT License"></a>
  <a href="https://github.com/fazleelahhee/Claude-Context-Engine"><img src="https://img.shields.io/github/stars/fazleelahhee/Claude-Context-Engine?style=social" alt="Stars"></a>
  <a href="https://github.com/fazleelahhee/Claude-Context-Engine/issues"><img src="https://img.shields.io/github/issues/fazleelahhee/Claude-Context-Engine" alt="Issues"></a>
  <a href="https://github.com/fazleelahhee/Claude-Context-Engine/pulls"><img src="https://img.shields.io/badge/PRs-welcome-brightgreen.svg" alt="PRs Welcome"></a>
</p>

<p align="center">
  <code>pip install claude-context-engine</code>
</p>

---

A local context indexing system for [Claude Code](https://docs.anthropic.com/en/docs/claude-code) that indexes your codebase, compresses context, and serves it via MCP. Claude starts every session already knowing your project.

<p align="center">
  <img src="docs/demo.svg" alt="Demo" width="800">
</p>

---

## Install and Set Up

Two commands. That's it.

```bash
pip install claude-context-engine

cd /path/to/your/project
cce init
```

`cce init` does everything automatically:

1. Indexes your codebase
2. Installs git hooks (auto re-index on commit)
3. Writes the MCP server config to `.mcp.json`

Restart Claude Code and it will have full context of your project.

### Homebrew (macOS)

```bash
brew tap fazleelahhee/tap
brew install claude-context-engine

cd /path/to/your/project
cce init
```

---

## How It Works

```
Your Code
  │
  ▼
┌──────────────┐    ┌──────────────┐    ┌─────────────┐
│  Tree-sitter  │───▶│   LanceDB    │───▶│  MCP Server │───▶ Claude Code
│  Chunker      │    │  (vectors)   │    │  (stdio)    │
└──────────────┘    └──────────────┘    └─────────────┘
  │                                           ▲
  ▼                                           │
┌──────────────┐                   ┌──────────────────┐
│  Embedder    │                   │  Compressor       │
│  (MiniLM)    │                   │  (truncation)     │
└──────────────┘                   └──────────────────┘
```

| Stage | What it does |
|-------|-------------|
| **Index** | AST-aware chunking (tree-sitter) and semantic embeddings |
| **Store** | LanceDB vector database for fast similarity search |
| **Compress** | Smart truncation (or Ollama if installed) to fit more in fewer tokens |
| **Serve** | MCP server gives Claude search, chunk expansion, and session history |

---

## What Claude Gets

Once connected, Claude Code has access to these tools automatically:

| Tool | Description |
|------|-------------|
| `context_search` | Semantic search across your indexed codebase |
| `expand_chunk` | Get full source code for a compressed chunk |
| `related_context` | Find related code by proximity |
| `session_recall` | Recall past decisions and discussions |
| `index_status` | Check when the index was last updated |
| `reindex` | Trigger re-indexing of a file or full project |
| `set_output_compression` | Change output verbosity mid-session |

---

## Token Savings

| Scenario | Without | With | Savings |
|----------|---------|------|---------|
| Session startup (small project) | ~8k tokens | ~2k tokens | **75%** |
| Session startup (large project) | ~100k+ tokens | ~10k tokens | **90%+** |
| Finding a function | ~8k tokens | ~800 tokens | **90%** |
| Cross-session recall | ~20k tokens | ~1k tokens | **95%** |

Both input and output tokens are compressed in a single tool.

---

## CLI Reference

```bash
cce init              # Initialize project, index, and connect to Claude Code
cce index             # Re-index project (incremental)
cce index --full      # Force full re-index
cce index --path src/ # Index a specific directory
cce status            # Show index stats and config
cce serve             # Start MCP server (Claude Code calls this automatically)
```

Verbose mode works with any command:

```bash
cce --verbose index
  [skip] README.md (unchanged)
  [index] src/app.py — 12 chunks (0.021s)
Indexing complete.
```

---

## Configuration

Global config at `~/.claude-context-engine/config.yaml` (created automatically on first run):

```yaml
compression:
  level: standard        # minimal | standard | full
  output: standard       # off | lite | standard | max

embedding:
  model: all-MiniLM-L6-v2

retrieval:
  confidence_threshold: 0.5
  top_k: 20

indexer:
  ignore:
    - .git
    - node_modules
    - __pycache__
    - .venv
```

Per-project overrides go in `.context-engine.yaml` at the project root.

### Optional: LLM Compression (Ollama)

By default, compression uses smart truncation (signature extraction). If you have [Ollama](https://ollama.com/) running on your machine, the engine detects it automatically and uses it for higher-quality summaries. No extra config needed.

```bash
brew install ollama
ollama pull phi3:mini
# that's it — cce will use it automatically
```

---

## How Compression Works

### Input Compression (3 layers)

1. **AST chunking** — tree-sitter splits files into functions, classes, and modules. Only relevant chunks are retrieved, not full files.

2. **LLM summarization** (optional, requires Ollama) — each chunk is summarized using type-specific prompts. A quality check ensures key identifiers survive compression.

3. **Smart truncation** (fallback) — extracts function signatures and docstrings, drops implementation bodies.

```python
# Original (45 lines, ~600 tokens)
def calculate_shipping(order, warehouse, method="standard"):
    """Calculate shipping cost based on weight, location, and method."""
    total_weight = sum(item.weight * item.quantity for item in order.items)
    # ... 40 more lines ...

# Compressed (3 lines, ~50 tokens)
def calculate_shipping(order, warehouse, method="standard"):
    """Calculate shipping cost based on weight, location, and method."""
```

### Output Compression

| Level | Savings | Style |
|-------|---------|-------|
| **off** | 0% | Normal Claude responses |
| **lite** | ~30% | No filler or hedging |
| **standard** | ~65% | Fragments, short synonyms (default) |
| **max** | ~75% | Telegraphic with abbreviations |

Code blocks, file paths, commands, and security warnings are never compressed.

Toggle mid-session by asking Claude to call `set_output_compression`.

---

## Cost Example (Claude Opus 4)

| Config | Input | Output | Total | Savings |
|--------|-------|--------|-------|---------|
| No engine | 50k | 20k | **$2.25** | |
| Input only | 10k | 20k | **$1.65** | 27% |
| Output only | 50k | 7k | **$1.28** | 43% |
| Both (default) | 10k | 7k | **$0.68** | **70%** |

---

## Supported Languages

**AST-aware:** Python, JavaScript, TypeScript, JSX, TSX

**Full-file fallback:** Markdown and other text files

---

## Development

```bash
git clone git@github.com:fazleelahhee/Claude-Context-Engine.git
cd Claude-Context-Engine
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"

pytest                           # run tests
pytest --cov=context_engine     # with coverage
```

---

## Contributing

1. Fork the repo
2. Create a branch (`git checkout -b feature/my-feature`)
3. Commit your changes
4. Open a Pull Request

---

## Roadmap

- [ ] Tree-sitter support for Go, Rust, Java, C/C++
- [ ] Web dashboard for index inspection
- [ ] Persistent session search across projects

---

## License

MIT. See [LICENSE](LICENSE).

---

## Acknowledgments

[Claude Code](https://docs.anthropic.com/en/docs/claude-code) by Anthropic,
[MCP](https://modelcontextprotocol.io),
[LanceDB](https://lancedb.com/),
[Tree-sitter](https://tree-sitter.github.io/),
[Ollama](https://ollama.com/) (optional)

---

<p align="center">If this project helps you, consider giving it a star.</p>
