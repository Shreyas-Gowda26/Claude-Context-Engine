"""Project-specific commands that CCE loads at every session start.

Stored in .cce/commands.yaml per project. These are instructions for Claude
about what commands to run at specific points in the workflow (before push,
before commit, on session start, etc.).

Example .cce/commands.yaml:
    before_push:
      - composer test
      - php artisan lint
    before_commit:
      - npm run lint
    on_start:
      - echo "Remember: staging branch requires PR approval"
    custom:
      deploy: "kubectl apply -f k8s/"
      db_migrate: "php artisan migrate"
"""
import logging
from pathlib import Path

import yaml

log = logging.getLogger(__name__)

COMMANDS_DIR = ".cce"
COMMANDS_FILE = "commands.yaml"

VALID_HOOKS = {"before_push", "before_commit", "on_start", "custom"}


def _commands_path(project_dir: str) -> Path:
    return Path(project_dir) / COMMANDS_DIR / COMMANDS_FILE


def load_commands(project_dir: str) -> dict:
    """Load project commands from .cce/commands.yaml. Returns {} if missing."""
    path = _commands_path(project_dir)
    if not path.exists():
        return {}
    try:
        data = yaml.safe_load(path.read_text()) or {}
    except (yaml.YAMLError, OSError) as exc:
        log.warning("Failed to parse %s: %s", path, exc)
        return {}
    if not isinstance(data, dict):
        log.warning("%s is not a valid YAML mapping", path)
        return {}
    return data


def save_commands(project_dir: str, commands: dict) -> None:
    """Save project commands to .cce/commands.yaml."""
    path = _commands_path(project_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.dump(commands, default_flow_style=False, sort_keys=False))


def add_command(project_dir: str, hook: str, command: str) -> None:
    """Add a command to a hook. Creates the file if it doesn't exist."""
    if hook not in VALID_HOOKS:
        raise ValueError(f"Invalid hook '{hook}'. Valid hooks: {', '.join(sorted(VALID_HOOKS))}")
    commands = load_commands(project_dir)
    if hook == "custom":
        raise ValueError("Use add_custom_command() for custom commands")
    hook_list = commands.setdefault(hook, [])
    if not isinstance(hook_list, list):
        raise ValueError(f"Hook '{hook}' is not a list in commands.yaml")
    if command in hook_list:
        return  # already exists
    hook_list.append(command)
    save_commands(project_dir, commands)


def add_custom_command(project_dir: str, name: str, command: str) -> None:
    """Add a named custom command."""
    commands = load_commands(project_dir)
    custom = commands.setdefault("custom", {})
    if not isinstance(custom, dict):
        raise ValueError("'custom' section must be a mapping in commands.yaml")
    custom[name] = command
    save_commands(project_dir, commands)


def remove_command(project_dir: str, hook: str, command: str) -> bool:
    """Remove a command from a hook. Returns True if removed."""
    commands = load_commands(project_dir)
    if hook not in commands:
        return False
    if hook == "custom":
        custom = commands.get("custom", {})
        if command in custom:
            del custom[command]
            if not custom:
                del commands["custom"]
            save_commands(project_dir, commands)
            return True
        return False
    hook_list = commands.get(hook, [])
    if not isinstance(hook_list, list):
        return False
    if command in hook_list:
        hook_list.remove(command)
        if not hook_list:
            del commands[hook]
        save_commands(project_dir, commands)
        return True
    return False


def format_for_prompt(commands: dict) -> str:
    """Format commands as markdown for the init prompt."""
    if not commands:
        return ""
    lines = ["### Project Commands"]
    hook_labels = {
        "before_push": "Before push",
        "before_commit": "Before commit",
        "on_start": "On session start",
    }
    for hook, label in hook_labels.items():
        cmds = commands.get(hook, [])
        if cmds and isinstance(cmds, list):
            cmd_str = ", ".join(f"`{c}`" for c in cmds)
            lines.append(f"- **{label}:** {cmd_str}")
    custom = commands.get("custom", {})
    if custom and isinstance(custom, dict):
        lines.append("- **Custom commands:**")
        for name, cmd in custom.items():
            lines.append(f"  - `{name}`: `{cmd}`")
    return "\n".join(lines) if len(lines) > 1 else ""
