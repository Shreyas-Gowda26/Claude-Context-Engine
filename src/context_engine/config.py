"""Configuration loading — global + per-project with defaults."""
import os
from dataclasses import dataclass, field
from pathlib import Path

import yaml


DEFAULT_GLOBAL_PATH = Path.home() / ".claude-context-engine" / "config.yaml"
PROJECT_CONFIG_NAME = ".context-engine.yaml"

DEFAULT_IGNORE = [".git", "node_modules", "__pycache__", ".venv", ".env"]


@dataclass
class Config:
    # Remote
    remote_enabled: bool = False
    remote_host: str = ""
    remote_fallback_to_local: bool = True

    # Compression
    compression_level: str = "standard"
    compression_model: str = "phi3:mini"
    remote_compression_model: str = "llama3:8b"

    # Embedding
    embedding_model: str = "all-MiniLM-L6-v2"

    # Retrieval
    retrieval_confidence_threshold: float = 0.5
    retrieval_top_k: int = 20
    bootstrap_max_tokens: int = 10000

    # Indexer
    indexer_watch: bool = True
    indexer_debounce_ms: int = 500
    indexer_ignore: list[str] = field(default_factory=lambda: list(DEFAULT_IGNORE))
    indexer_languages: list[str] = field(default_factory=list)

    # Storage
    storage_path: str = str(Path.home() / ".claude-context-engine" / "projects")

    def detect_resource_profile(self) -> str:
        """Auto-detect resource profile based on available RAM."""
        try:
            import psutil
            ram_gb = psutil.virtual_memory().total / (1024**3)
        except ImportError:
            ram_gb = 16  # assume standard if psutil unavailable

        if self.remote_enabled:
            return "full"
        if ram_gb >= 32:
            return "full"
        if ram_gb >= 12:
            return "standard"
        return "light"


def _deep_merge(base: dict, override: dict) -> dict:
    """Merge override into base, recursing into nested dicts."""
    result = base.copy()
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result


def _apply_dict_to_config(config: Config, data: dict) -> None:
    """Apply a nested YAML dict to a flat Config dataclass."""
    mapping = {
        ("remote", "enabled"): "remote_enabled",
        ("remote", "host"): "remote_host",
        ("remote", "fallback_to_local"): "remote_fallback_to_local",
        ("compression", "level"): "compression_level",
        ("compression", "model"): "compression_model",
        ("compression", "remote_model"): "remote_compression_model",
        ("embedding", "model"): "embedding_model",
        ("retrieval", "confidence_threshold"): "retrieval_confidence_threshold",
        ("retrieval", "top_k"): "retrieval_top_k",
        ("retrieval", "bootstrap_max_tokens"): "bootstrap_max_tokens",
        ("indexer", "watch"): "indexer_watch",
        ("indexer", "debounce_ms"): "indexer_debounce_ms",
        ("indexer", "ignore"): "indexer_ignore",
        ("indexer", "languages"): "indexer_languages",
        ("storage", "path"): "storage_path",
    }
    for (section, key), attr in mapping.items():
        if section in data and key in data[section]:
            setattr(config, attr, data[section][key])


def load_config(
    global_path: Path | None = None,
    project_path: Path | None = None,
) -> Config:
    """Load config from global file, then overlay project overrides."""
    global_path = global_path or DEFAULT_GLOBAL_PATH
    config = Config()

    global_data = {}
    if global_path.exists():
        with open(global_path) as f:
            global_data = yaml.safe_load(f) or {}

    project_data = {}
    if project_path and project_path.exists():
        with open(project_path) as f:
            project_data = yaml.safe_load(f) or {}

    merged = _deep_merge(global_data, project_data)
    _apply_dict_to_config(config, merged)
    return config
