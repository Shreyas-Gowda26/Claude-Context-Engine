<p align="center">
  <img src="docs/logo.svg" alt="Claude Context Engine" width="180">
</p>

<h1 align="center">Claude Context Engine</h1>

<p align="center">
  <strong>Index your codebase. Compress context. Cut token costs by 70%.</strong>
</p>

<p align="center">
  <a href="https://pypi.org/project/claude-context-engine/"><img src="https://img.shields.io/pypi/v/claude-context-engine?color=blue" alt="PyPI"></a>
  <a href="https://opensource.org/licenses/MIT"><img src="https://img.shields.io/badge/License-MIT-yellow.svg" alt="License: MIT"></a>
  <a href="https://www.python.org/downloads/"><img src="https://img.shields.io/badge/python-3.11+-blue.svg" alt="Python 3.11+"></a>
  <a href="https://modelcontextprotocol.io"><img src="https://img.shields.io/badge/MCP-compatible-green.svg" alt="MCP Compatible"></a>
  <a href="https://github.com/fazleelahhee/Claude-Context-Engine"><img src="https://img.shields.io/github/stars/fazleelahhee/Claude-Context-Engine?style=social" alt="GitHub stars"></a>
  <a href="https://github.com/fazleelahhee/Claude-Context-Engine/fork"><img src="https://img.shields.io/github/forks/fazleelahhee/Claude-Context-Engine?style=social" alt="GitHub forks"></a>
  <a href="https://github.com/fazleelahhee/Claude-Context-Engine/issues"><img src="https://img.shields.io/github/issues/fazleelahhee/Claude-Context-Engine" alt="GitHub issues"></a>
  <a href="https://github.com/fazleelahhee/Claude-Context-Engine/pulls"><img src="https://img.shields.io/badge/PRs-welcome-brightgreen.svg" alt="PRs Welcome"></a>
</p>

---

## Get Running in 60 Seconds

**Step 1 — Install**
```bash
brew tap fazleelahhee/tap && brew install claude-context-engine  # macOS
# or
pip install claude-context-engine                                 # all platforms
```

**Step 2 — Index your project**
```bash
cd /path/to/your/project
cce init
```

**Step 3 — Connect to Claude Code**

Paste this into `.mcp.json` in your project root:
```json
{
  "mcpServers": {
    "context-engine": {
      "command": "cce",
      "args": ["serve"]
    }
  }
}
```

Restart Claude Code. Done. Claude now searches your indexed codebase instead of re-reading files every session.

<p align="center">
  <img src="docs/demo.svg" alt="Claude Context Engine Demo" width="800">
</p>

---

## Why?

Every Claude Code session re-reads your files, re-discovers your architecture, and burns tokens on code it's seen before.

| | Without CCE | With CCE |
|---|---|---|
| Session startup | ~50k tokens | ~10k tokens |
| Finding a function | ~8k tokens | ~800 tokens |
| Cost per session (Opus 4) | ~$2.25 | ~$0.68 |
| Remembers past sessions | No | Yes |

**70% cost reduction. Zero cloud. Everything stays local.**

---

## What You Get

| Command | What It Does |
|---------|-------------|
| `cce init` | Index your project (one-time setup) |
| `cce index` | Re-index (only changed files) |
| `cce status` | Show index stats |
| `cce serve` | Start MCP server for Claude Code |

Once connected, Claude Code gets these tools automatically:

| Tool | What It Does |
|------|-------------|
| `context_search` | Semantic search across your codebase |
| `expand_chunk` | Get the full source for a compressed chunk |
| `related_context` | Find related code via knowledge graph |
| `session_recall` | Recall past decisions and discussions |
| `set_output_compression` | Adjust response verbosity (off/lite/standard/max) |

---

## How It Saves Tokens

```
Your Code → Tree-sitter → LanceDB + Kuzu → MCP Server → Claude Code
             (chunking)    (vector + graph)   (search)    (uses it)
```

**Input side** — Claude reads compressed summaries instead of full files:
- AST-aware chunking splits code into functions/classes (not raw lines)
- Vector search retrieves only relevant chunks
- LLM summarization compresses each chunk (or smart truncation without Ollama)

**Output side** — Claude responds concisely:
- Built-in output compression reduces response verbosity by 65-75%
- Output tokens cost **5x more** than input — this saves the most money
- Toggle mid-session: just ask Claude to "switch to max compression"

---

<details>
<summary><h2>Configuration</h2></summary>

Works with zero config. Customize if you want:

**Global** — `~/.claude-context-engine/config.yaml`:
```yaml
compression:
  level: standard        # minimal | standard | full (input)
  output: standard       # off | lite | standard | max (output)
  model: phi3:mini       # Ollama model (optional)

indexer:
  watch: true            # Auto-reindex on file save
  ignore: [.git, node_modules, __pycache__, .venv]

retrieval:
  top_k: 20
  confidence_threshold: 0.5
```

**Per-project** — `.context-engine.yaml` in project root (overrides global):
```yaml
compression:
  level: full
indexer:
  ignore: [.git, node_modules, dist, coverage]
```

The engine auto-detects your machine resources:
| RAM | Profile | Behavior |
|-----|---------|----------|
| < 12 GB | light | Truncation only, small batches |
| 12-32 GB | standard | Full pipeline (default) |
| 32+ GB | full | Larger models, all features |

</details>

<details>
<summary><h2>Output Compression Levels</h2></summary>

Output tokens cost **5x more** than input. The engine includes built-in output compression:

| Level | Style | Savings | Example |
|-------|-------|---------|---------|
| **off** | Normal Claude | 0% | "I'll fix the bug in the authentication module. The issue is..." |
| **lite** | No filler/hedging | ~30% | "Bug is in auth module. Session token validation doesn't check..." |
| **standard** | Fragments, short words | ~65% | "Bug in auth module. Session token missing expiration check..." |
| **max** | Telegraphic | ~75% | "auth bug → session token no expiry check..." |

Toggle mid-session:
```
"Switch to max output compression"
"Turn off output compression"
```

Code blocks, file paths, commands, and error messages are **never** compressed. Security warnings always use full clarity.

</details>

<details>
<summary><h2>How Token Compression Works</h2></summary>

### Layer 1: AST-Aware Chunking

Tree-sitter parses your code into semantic chunks — functions, classes, modules. No raw file reads.

```
Raw file (800 lines, ~12k tokens)
  → 15 function chunks + 3 class chunks
  → Only relevant chunks retrieved, not the whole file
```

### Layer 2: LLM Summarization (Ollama)

Each chunk is summarized using type-specific prompts:

| Chunk Type | Example Output |
|-----------|----------------|
| Function/Class | `"process_payment(order, method): Validates payment, charges via Stripe, returns PaymentResult."` |
| Architecture | `"API gateway — routes HTTP to service handlers, applies auth + rate limiting."` |
| Decision | `"Chose PostgreSQL over MongoDB. Reason: relational queries for billing."` |

A quality checker ensures 40%+ of key identifiers survive compression.

### Layer 3: Smart Truncation (Fallback)

Without Ollama: extracts function signatures + docstrings, drops bodies.

```python
# Original (45 lines, ~600 tokens)
def calculate_shipping(order, warehouse, method="standard"):
    """Calculate shipping cost based on order weight and location."""
    total_weight = sum(item.weight * item.quantity for item in order.items)
    # ... 40 more lines ...

# Compressed (2 lines, ~40 tokens)
def calculate_shipping(order, warehouse, method="standard"):
    """Calculate shipping cost based on order weight and location."""
```

### Confidence-Based Retrieval

Every chunk is scored: 50% vector similarity + 30% graph distance + 20% recency. Only high-confidence chunks are returned.

### Progressive Disclosure

```
Session start:     Project overview              → 10k tokens
Search:            "Find payment processing"     → 800 tokens
Drill-down:        "Show full calculate_shipping" → 600 tokens
                                           Total: 11.4k tokens

Without engine:    Read payments.py + shipping.py → 45k tokens
```

</details>

<details>
<summary><h2>Remote Mode</h2></summary>

Offload heavy computation to a remote server:

```yaml
remote:
  enabled: true
  host: "user@your-server"
  fallback_to_local: true
compression:
  remote_model: llama3:8b
```

```bash
cce serve-http --host 0.0.0.0 --port 8765  # Run on server
```

Falls back to local if server is unreachable.

</details>

<details>
<summary><h2>Token Savings: Detailed Breakdown</h2></summary>

### By Project Size

| | Without CCE | With CCE | Savings |
|---|---|---|---|
| **Small** (~50 files) | ~8k tokens startup | ~2k tokens | 75% |
| **Medium** (~500 files) | ~50k tokens startup | ~10k tokens | 80% |
| **Large** (~2000+ files) | ~100k+ tokens | ~10k tokens | 90%+ |

### Cost Comparison (Opus 4: $15/1M input, $75/1M output)

| Scenario | Input | Output | **Total Cost** | **Savings** |
|---|---|---|---|---|
| No tool | 50k | 20k | **$2.25** | — |
| CCE (both compressions, default) | 10k | 7k | **$0.68** | **70%** |

### Where Savings Come From

```
Without:  ████████████████████ Full file reads (60%)
          ██████████          Re-discovery (25%)
          █████               Irrelevant results (15%)
          Total: ~50k tokens

With CCE: █████ Bootstrap (40%)
          ████  Targeted retrieval (35%)
          ██    Graph traversal (15%)
          █     Session recall (10%)
          Total: ~10k tokens
```

</details>

<details>
<summary><h2>Comparison: CCE vs Caveman</h2></summary>

[Caveman](https://github.com/JuliusBrussee/caveman) (36k+ stars) is a popular output-compression plugin.

| | **CCE** | **Caveman** |
|---|---|---|
| Compresses input tokens | Yes | No |
| Compresses output tokens | Yes | Yes (only focus) |
| Codebase indexing | Yes — AST + vector + graph | No |
| Session memory | Yes | No |
| Setup | `pip install` + `cce init` | Plugin install, zero config |
| Agent support | MCP-compatible agents | 40+ agents |

### Cost Comparison (Opus 4, medium project)

| Tool | Total Cost | Savings |
|---|---|---|
| No tool | $2.25 | — |
| Caveman only | $1.28 | 43% |
| **CCE (default)** | **$0.68** | **70%** |

**Caveman** = makes Claude talk less. Zero setup.
**CCE** = makes Claude read less AND talk less. Deeper savings over time.

</details>

<details>
<summary><h2>Supported Languages</h2></summary>

**AST-aware chunking** (tree-sitter):
- Python
- JavaScript
- TypeScript (JSX/TSX)

**Fallback chunking** (full-file):
- Markdown, and any text file with supported extensions

Want more? See issues [#1](https://github.com/fazleelahhee/Claude-Context-Engine/issues/1) (Go), [#2](https://github.com/fazleelahhee/Claude-Context-Engine/issues/2) (Rust), [#3](https://github.com/fazleelahhee/Claude-Context-Engine/issues/3) (Java).

</details>

<details>
<summary><h2>Optional: Ollama for Better Compression</h2></summary>

Without Ollama, the engine uses smart truncation (signatures + docstrings). With Ollama, it produces LLM-quality summaries.

```bash
brew install ollama       # macOS
ollama pull phi3:mini     # Small, fast model
```

No config change needed — the engine auto-detects Ollama.

</details>

---

## Contributing

We welcome contributions! See [CONTRIBUTING.md](CONTRIBUTING.md) for setup instructions.

Check out the [good first issues](https://github.com/fazleelahhee/Claude-Context-Engine/issues?q=is%3Aissue+is%3Aopen+label%3A%22good+first+issue%22) to get started.

## Roadmap

- [ ] Tree-sitter support for Go, Rust, Java, C/C++
- [ ] Web dashboard for index inspection
- [ ] Persistent session search across projects
- [ ] Smarter graph edge detection (call graph, import resolution)
- [x] ~~PyPI package publishing~~
- [x] ~~GitHub Actions CI pipeline~~

## License

MIT — see [LICENSE](LICENSE).

## Acknowledgments

[Claude Code](https://docs.anthropic.com/en/docs/claude-code) | [MCP](https://modelcontextprotocol.io) | [LanceDB](https://lancedb.com/) | [Kuzu](https://kuzudb.com/) | [Tree-sitter](https://tree-sitter.github.io/) | [Ollama](https://ollama.com/)

---

<p align="center">
  If this saves you tokens, give it a star — it helps others find it.
</p>
