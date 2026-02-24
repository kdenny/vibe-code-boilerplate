"""Tests for config loading and management."""

import json
from pathlib import Path

from lib.vibe.config import (
    _deep_update,
    config_exists,
    get_config_path,
    get_value,
    load_config,
    save_config,
    update_config,
)


class TestGetConfigPath:
    """Tests for get_config_path function."""

    def test_default_path(self) -> None:
        path = get_config_path()
        assert path == Path(".vibe/config.json")

    def test_custom_base_path(self, tmp_path: Path) -> None:
        path = get_config_path(base_path=tmp_path)
        assert path == tmp_path / ".vibe" / "config.json"


class TestConfigExists:
    """Tests for config_exists function."""

    def test_config_exists_false(self, tmp_path: Path) -> None:
        assert config_exists(base_path=tmp_path) is False

    def test_config_exists_true(self, tmp_path: Path) -> None:
        vibe_dir = tmp_path / ".vibe"
        vibe_dir.mkdir()
        (vibe_dir / "config.json").write_text("{}")
        assert config_exists(base_path=tmp_path) is True


class TestLoadConfig:
    """Tests for load_config function."""

    def test_load_config_missing_file(self, tmp_path: Path) -> None:
        """load_config returns defaults when file doesn't exist."""
        config = load_config(base_path=tmp_path)
        assert config["branching"]["always_rebase"] is True
        assert config["tracker"]["type"] is None

    def test_load_config_returns_default_structure(self, tmp_path: Path) -> None:
        """Default config has expected top-level keys."""
        config = load_config(base_path=tmp_path)
        assert "version" in config
        assert "project" in config
        assert "tracker" in config
        assert "github" in config
        assert "branching" in config
        assert "labels" in config

    def test_load_config_from_file(self, tmp_path: Path) -> None:
        """load_config reads from file when it exists."""
        vibe_dir = tmp_path / ".vibe"
        vibe_dir.mkdir()
        data = {"tracker": {"type": "linear"}, "github": {"owner": "test"}}
        (vibe_dir / "config.json").write_text(json.dumps(data))

        config = load_config(base_path=tmp_path)
        assert config["tracker"]["type"] == "linear"
        assert config["github"]["owner"] == "test"


class TestSaveConfig:
    """Tests for save_config function."""

    def test_save_config_creates_directory(self, tmp_path: Path) -> None:
        """save_config creates .vibe directory if missing."""
        config = {"tracker": {"type": "linear"}}
        save_config(config, base_path=tmp_path)

        config_file = tmp_path / ".vibe" / "config.json"
        assert config_file.exists()

    def test_save_and_load_config(self, tmp_path: Path) -> None:
        """Config round-trips through save/load."""
        config = {"tracker": {"type": "linear"}, "github": {"owner": "test"}}
        save_config(config, base_path=tmp_path)

        loaded = load_config(base_path=tmp_path)
        assert loaded["tracker"]["type"] == "linear"
        assert loaded["github"]["owner"] == "test"

    def test_save_config_writes_valid_json(self, tmp_path: Path) -> None:
        """Saved config is valid JSON with trailing newline."""
        config = {"key": "value"}
        save_config(config, base_path=tmp_path)

        content = (tmp_path / ".vibe" / "config.json").read_text()
        assert content.endswith("\n")
        parsed = json.loads(content)
        assert parsed["key"] == "value"


class TestUpdateConfig:
    """Tests for update_config function."""

    def test_update_config_deep_merge(self, tmp_path: Path) -> None:
        """update_config merges nested dicts."""
        save_config(
            {"tracker": {"type": "linear", "config": {"team_id": "abc"}}},
            base_path=tmp_path,
        )

        updated = update_config(
            {"tracker": {"config": {"deployed_state": "Done"}}},
            base_path=tmp_path,
        )
        assert updated["tracker"]["type"] == "linear"
        assert updated["tracker"]["config"]["team_id"] == "abc"
        assert updated["tracker"]["config"]["deployed_state"] == "Done"

    def test_update_config_overwrites_non_dict(self, tmp_path: Path) -> None:
        """update_config overwrites non-dict values."""
        save_config({"tracker": {"type": "linear"}}, base_path=tmp_path)

        updated = update_config({"tracker": {"type": "shortcut"}}, base_path=tmp_path)
        assert updated["tracker"]["type"] == "shortcut"

    def test_update_config_adds_new_keys(self, tmp_path: Path) -> None:
        """update_config adds new keys that didn't exist before."""
        save_config({"tracker": {"type": "linear"}}, base_path=tmp_path)

        updated = update_config({"new_section": {"key": "value"}}, base_path=tmp_path)
        assert updated["new_section"]["key"] == "value"
        assert updated["tracker"]["type"] == "linear"

    def test_update_config_persists_to_disk(self, tmp_path: Path) -> None:
        """update_config writes changes to disk."""
        save_config({"tracker": {"type": "linear"}}, base_path=tmp_path)
        update_config({"tracker": {"type": "shortcut"}}, base_path=tmp_path)

        reloaded = load_config(base_path=tmp_path)
        assert reloaded["tracker"]["type"] == "shortcut"


class TestGetValue:
    """Tests for get_value function."""

    def test_get_value_dot_notation(self, tmp_path: Path) -> None:
        """get_value supports dot-notation paths."""
        save_config(
            {"github": {"owner": "test-org", "repo": "my-repo"}},
            base_path=tmp_path,
        )

        assert get_value("github.owner", base_path=tmp_path) == "test-org"
        assert get_value("github.repo", base_path=tmp_path) == "my-repo"

    def test_get_value_nonexistent_key(self, tmp_path: Path) -> None:
        """get_value returns None for missing keys."""
        save_config({"github": {"owner": "test"}}, base_path=tmp_path)
        assert get_value("nonexistent.key", base_path=tmp_path) is None

    def test_get_value_top_level_key(self, tmp_path: Path) -> None:
        """get_value works for top-level keys."""
        save_config({"version": 2}, base_path=tmp_path)
        assert get_value("version", base_path=tmp_path) == 2

    def test_get_value_deeply_nested(self, tmp_path: Path) -> None:
        """get_value works for deeply nested paths."""
        save_config(
            {"a": {"b": {"c": {"d": "deep"}}}},
            base_path=tmp_path,
        )
        assert get_value("a.b.c.d", base_path=tmp_path) == "deep"

    def test_get_value_partial_path_returns_dict(self, tmp_path: Path) -> None:
        """get_value returns a dict for partial paths."""
        save_config(
            {"github": {"owner": "test", "repo": "my-repo"}},
            base_path=tmp_path,
        )
        result = get_value("github", base_path=tmp_path)
        assert isinstance(result, dict)
        assert result["owner"] == "test"


class TestDeepUpdate:
    """Tests for _deep_update helper."""

    def test_deep_update_simple(self) -> None:
        base = {"a": 1, "b": 2}
        _deep_update(base, {"b": 3})
        assert base == {"a": 1, "b": 3}

    def test_deep_update_nested(self) -> None:
        base = {"outer": {"inner1": "a", "inner2": "b"}}
        _deep_update(base, {"outer": {"inner2": "c"}})
        assert base == {"outer": {"inner1": "a", "inner2": "c"}}

    def test_deep_update_adds_keys(self) -> None:
        base = {"a": 1}
        _deep_update(base, {"b": 2})
        assert base == {"a": 1, "b": 2}

    def test_deep_update_replaces_non_dict_with_dict(self) -> None:
        base = {"a": "string"}
        _deep_update(base, {"a": {"nested": True}})
        assert base == {"a": {"nested": True}}


# --- Migration tests ---

from lib.vibe.config_schema import migrate_config


class TestMigrateConfig:
    """Tests for migrate_config function."""

    def test_v1_to_v2_backfills_labels_risk(self) -> None:
        """v1→v2 migration adds labels.risk when labels exist but risk is missing."""
        v1_config: dict = {
            "version": "1.0.0",
            "labels": {
                "type": ["Bug", "Feature", "Chore", "Refactor"],
                "area": ["Frontend", "Backend", "Infra", "Docs"],
                "special": ["HUMAN", "Milestone", "Blocked"],
            },
        }

        migrated, notes = migrate_config(v1_config)

        assert migrated["labels"]["risk"] == ["Low Risk", "Medium Risk", "High Risk"]
        assert "Added missing labels.risk category" in notes

    def test_v1_to_v2_preserves_existing_risk_labels(self) -> None:
        """v1→v2 migration does not overwrite existing labels.risk."""
        v1_config: dict = {
            "version": "1.0.0",
            "labels": {
                "type": ["Bug", "Feature"],
                "risk": ["Custom Low", "Custom High"],
            },
        }

        migrated, notes = migrate_config(v1_config)

        assert migrated["labels"]["risk"] == ["Custom Low", "Custom High"]
        assert "Added missing labels.risk category" not in notes

    def test_v1_to_v2_backfills_risk_when_no_labels_section(self) -> None:
        """v1→v2 migration adds labels.risk even when labels section is missing entirely."""
        v1_config: dict = {
            "version": "1.0.0",
        }

        migrated, notes = migrate_config(v1_config)

        assert migrated["labels"]["risk"] == ["Low Risk", "Medium Risk", "High Risk"]
        assert "Added missing labels.risk category" in notes
