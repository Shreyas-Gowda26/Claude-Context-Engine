"""Tests for project commands — .cce/commands.yaml management."""
import pytest
import yaml
from pathlib import Path

from context_engine.project_commands import (
    load_commands,
    save_commands,
    add_command,
    add_custom_command,
    remove_command,
    format_for_prompt,
    VALID_HOOKS,
)


# ── load_commands ──────────────────────────────────────────────────────

class TestLoadCommands:
    def test_returns_empty_dict_when_no_file(self, tmp_path):
        assert load_commands(str(tmp_path)) == {}

    def test_returns_empty_dict_for_empty_file(self, tmp_path):
        (tmp_path / ".cce").mkdir()
        (tmp_path / ".cce" / "commands.yaml").write_text("")
        assert load_commands(str(tmp_path)) == {}

    def test_loads_valid_yaml(self, tmp_path):
        (tmp_path / ".cce").mkdir()
        (tmp_path / ".cce" / "commands.yaml").write_text(
            "before_push:\n  - composer test\n  - phpstan analyse\n"
        )
        result = load_commands(str(tmp_path))
        assert result == {"before_push": ["composer test", "phpstan analyse"]}

    def test_handles_corrupt_yaml(self, tmp_path):
        (tmp_path / ".cce").mkdir()
        (tmp_path / ".cce" / "commands.yaml").write_text(": : : invalid yaml [[[")
        assert load_commands(str(tmp_path)) == {}

    def test_handles_non_dict_yaml(self, tmp_path):
        (tmp_path / ".cce").mkdir()
        (tmp_path / ".cce" / "commands.yaml").write_text("- just a list\n- not a dict\n")
        assert load_commands(str(tmp_path)) == {}

    def test_loads_all_hook_types(self, tmp_path):
        (tmp_path / ".cce").mkdir()
        data = {
            "before_push": ["test"],
            "before_commit": ["lint"],
            "on_start": ["echo hello"],
            "custom": {"deploy": "kubectl apply"},
        }
        (tmp_path / ".cce" / "commands.yaml").write_text(yaml.dump(data))
        result = load_commands(str(tmp_path))
        assert result == data


# ── save_commands ──────────────────────────────────────────────────────

class TestSaveCommands:
    def test_creates_directory_and_file(self, tmp_path):
        save_commands(str(tmp_path), {"before_push": ["test"]})
        path = tmp_path / ".cce" / "commands.yaml"
        assert path.exists()
        assert "before_push" in path.read_text()

    def test_roundtrip(self, tmp_path):
        data = {"before_push": ["a", "b"], "custom": {"x": "y"}}
        save_commands(str(tmp_path), data)
        assert load_commands(str(tmp_path)) == data


# ── add_command ────────────────────────────────────────────────────────

class TestAddCommand:
    def test_add_to_empty_project(self, tmp_path):
        add_command(str(tmp_path), "before_push", "composer test")
        result = load_commands(str(tmp_path))
        assert result == {"before_push": ["composer test"]}

    def test_add_multiple_commands(self, tmp_path):
        add_command(str(tmp_path), "before_push", "composer test")
        add_command(str(tmp_path), "before_push", "phpstan analyse")
        result = load_commands(str(tmp_path))
        assert result["before_push"] == ["composer test", "phpstan analyse"]

    def test_add_to_different_hooks(self, tmp_path):
        add_command(str(tmp_path), "before_push", "test")
        add_command(str(tmp_path), "before_commit", "lint")
        add_command(str(tmp_path), "on_start", "echo hi")
        result = load_commands(str(tmp_path))
        assert "before_push" in result
        assert "before_commit" in result
        assert "on_start" in result

    def test_duplicate_command_ignored(self, tmp_path):
        add_command(str(tmp_path), "before_push", "composer test")
        add_command(str(tmp_path), "before_push", "composer test")
        result = load_commands(str(tmp_path))
        assert result["before_push"] == ["composer test"]

    def test_invalid_hook_raises(self, tmp_path):
        with pytest.raises(ValueError, match="Invalid hook"):
            add_command(str(tmp_path), "invalid_hook", "test")

    def test_custom_hook_raises(self, tmp_path):
        with pytest.raises(ValueError, match="add_custom_command"):
            add_command(str(tmp_path), "custom", "test")


# ── add_custom_command ─────────────────────────────────────────────────

class TestAddCustomCommand:
    def test_add_custom(self, tmp_path):
        add_custom_command(str(tmp_path), "deploy", "kubectl apply -f k8s/")
        result = load_commands(str(tmp_path))
        assert result == {"custom": {"deploy": "kubectl apply -f k8s/"}}

    def test_add_multiple_custom(self, tmp_path):
        add_custom_command(str(tmp_path), "deploy", "kubectl apply")
        add_custom_command(str(tmp_path), "migrate", "php artisan migrate")
        result = load_commands(str(tmp_path))
        assert result["custom"]["deploy"] == "kubectl apply"
        assert result["custom"]["migrate"] == "php artisan migrate"

    def test_overwrite_existing_custom(self, tmp_path):
        add_custom_command(str(tmp_path), "deploy", "v1")
        add_custom_command(str(tmp_path), "deploy", "v2")
        result = load_commands(str(tmp_path))
        assert result["custom"]["deploy"] == "v2"


# ── remove_command ─────────────────────────────────────────────────────

class TestRemoveCommand:
    def test_remove_existing(self, tmp_path):
        add_command(str(tmp_path), "before_push", "test")
        assert remove_command(str(tmp_path), "before_push", "test") is True
        assert load_commands(str(tmp_path)) == {}

    def test_remove_nonexistent_returns_false(self, tmp_path):
        assert remove_command(str(tmp_path), "before_push", "test") is False

    def test_remove_from_empty_hook(self, tmp_path):
        add_command(str(tmp_path), "before_push", "a")
        assert remove_command(str(tmp_path), "before_commit", "a") is False

    def test_remove_custom(self, tmp_path):
        add_custom_command(str(tmp_path), "deploy", "kubectl apply")
        assert remove_command(str(tmp_path), "custom", "deploy") is True
        assert load_commands(str(tmp_path)) == {}

    def test_remove_preserves_other_commands(self, tmp_path):
        add_command(str(tmp_path), "before_push", "test")
        add_command(str(tmp_path), "before_push", "lint")
        remove_command(str(tmp_path), "before_push", "test")
        result = load_commands(str(tmp_path))
        assert result == {"before_push": ["lint"]}


# ── format_for_prompt ──────────────────────────────────────────────────

class TestFormatForPrompt:
    def test_empty_returns_empty(self):
        assert format_for_prompt({}) == ""

    def test_single_hook(self):
        result = format_for_prompt({"before_push": ["composer test"]})
        assert "### Project Commands" in result
        assert "Before push" in result
        assert "`composer test`" in result

    def test_multiple_hooks(self):
        result = format_for_prompt({
            "before_push": ["test", "lint"],
            "before_commit": ["format"],
        })
        assert "Before push" in result
        assert "`test`" in result
        assert "`lint`" in result
        assert "Before commit" in result
        assert "`format`" in result

    def test_custom_commands(self):
        result = format_for_prompt({"custom": {"deploy": "kubectl apply"}})
        assert "Custom commands" in result
        assert "`deploy`" in result
        assert "`kubectl apply`" in result

    def test_all_sections(self):
        result = format_for_prompt({
            "before_push": ["test"],
            "before_commit": ["lint"],
            "on_start": ["echo hi"],
            "custom": {"deploy": "go"},
        })
        assert "Before push" in result
        assert "Before commit" in result
        assert "On session start" in result
        assert "Custom commands" in result

    def test_ignores_invalid_hook_types(self):
        """If someone hand-edits the YAML with a non-list hook, don't crash."""
        result = format_for_prompt({"before_push": "not a list"})
        assert "Before push" not in result

    def test_ignores_invalid_custom_type(self):
        result = format_for_prompt({"custom": "not a dict"})
        assert "Custom" not in result


# ── Edge cases ─────────────────────────────────────────────────────────

class TestEdgeCases:
    def test_commands_with_special_characters(self, tmp_path):
        add_command(str(tmp_path), "before_push", "echo 'hello world' && exit 0")
        result = load_commands(str(tmp_path))
        assert result["before_push"] == ["echo 'hello world' && exit 0"]

    def test_commands_with_pipes(self, tmp_path):
        add_command(str(tmp_path), "before_push", "grep -r TODO src/ | wc -l")
        result = load_commands(str(tmp_path))
        assert "grep -r TODO src/ | wc -l" in result["before_push"]

    def test_very_long_command(self, tmp_path):
        long_cmd = "x" * 10000
        add_command(str(tmp_path), "before_push", long_cmd)
        result = load_commands(str(tmp_path))
        assert result["before_push"] == [long_cmd]

    def test_concurrent_add_doesnt_lose_data(self, tmp_path):
        """Simulate rapid adds — each should survive."""
        for i in range(20):
            add_command(str(tmp_path), "before_push", f"cmd_{i}")
        result = load_commands(str(tmp_path))
        assert len(result["before_push"]) == 20

    def test_mixed_hooks_and_custom(self, tmp_path):
        add_command(str(tmp_path), "before_push", "test")
        add_custom_command(str(tmp_path), "deploy", "go")
        add_command(str(tmp_path), "on_start", "echo hi")
        result = load_commands(str(tmp_path))
        assert result["before_push"] == ["test"]
        assert result["custom"]["deploy"] == "go"
        assert result["on_start"] == ["echo hi"]
