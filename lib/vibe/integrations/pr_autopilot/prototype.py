"""Prototype PR Autopilot configuration DX.

This is intentionally a thin artifact/status layer. It does not run the future
PR automation engine; it prepares the declarative files the engine will consume
and shows the native provider checks Claude should narrate to the human.
"""

from __future__ import annotations

import json
import os
import subprocess
import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from lib.vibe.config import load_config

VIBE_DIR = Path(".vibe")
CORE_CONFIG_PATH = VIBE_DIR / "config.toml"
INTEGRATION_CONFIG_PATH = VIBE_DIR / "pr-autopilot.toml"
DISABLED_CONFIG_PATH = VIBE_DIR / "pr-autopilot.toml.disabled"
ANTHROPIC_SECRET_NAME = "ANTHROPIC_API_KEY"
ANTHROPIC_SECRET_REF = f"gh:{ANTHROPIC_SECRET_NAME}"


@dataclass(frozen=True)
class ToolResult:
    """Captured native-provider command result."""

    command: tuple[str, ...]
    returncode: int
    stdout: str = ""
    stderr: str = ""

    @property
    def display(self) -> str:
        return "$ " + " ".join(self.command)

    @property
    def ok(self) -> bool:
        return self.returncode == 0


ProviderRunner = Any


def configure_pr_autopilot(*, runner: ProviderRunner | None = None) -> str:
    """Write the layered prototype artifacts and report native-provider checks."""

    run_tool = runner or _run_provider_tool
    VIBE_DIR.mkdir(exist_ok=True)

    repo_probe = run_tool(("gh", "repo", "view", "--json", "owner,name"))
    secrets_probe = run_tool(("gh", "secret", "list", "--json", "name"))
    github_owner, github_repo = _infer_github_identity(repo_probe)
    linear_team = _infer_linear_team()

    existing_core = _read_toml(CORE_CONFIG_PATH)
    existing_integration = _read_toml(INTEGRATION_CONFIG_PATH)
    if not existing_integration and DISABLED_CONFIG_PATH.exists():
        existing_integration = _read_toml(DISABLED_CONFIG_PATH)

    core_config = _core_config(existing_core, github_owner, github_repo, linear_team)
    integration_config = _integration_config(existing_integration)

    changed: list[str] = []
    if _write_toml_if_changed(CORE_CONFIG_PATH, core_config):
        changed.append(str(CORE_CONFIG_PATH))
    if _write_toml_if_changed(INTEGRATION_CONFIG_PATH, integration_config):
        changed.append(str(INTEGRATION_CONFIG_PATH))
    if DISABLED_CONFIG_PATH.exists():
        DISABLED_CONFIG_PATH.unlink()
        changed.append(str(DISABLED_CONFIG_PATH))

    return _format_configure_report(changed, repo_probe, secrets_probe, core_config)


def enable_pr_autopilot(*, runner: ProviderRunner | None = None) -> str:
    """Enable PR Autopilot by ensuring the per-integration TOML is present."""

    if INTEGRATION_CONFIG_PATH.exists():
        config = _read_toml(INTEGRATION_CONFIG_PATH)
        config.setdefault("integration", {})["enabled"] = True
        _write_toml_if_changed(INTEGRATION_CONFIG_PATH, config)
        return _format_enable_report("PR Autopilot already enabled.")

    if DISABLED_CONFIG_PATH.exists():
        config = _read_toml(DISABLED_CONFIG_PATH)
        config.setdefault("integration", {})["enabled"] = True
        VIBE_DIR.mkdir(exist_ok=True)
        _write_toml_if_changed(INTEGRATION_CONFIG_PATH, config)
        DISABLED_CONFIG_PATH.unlink()
        return _format_enable_report(
            f"Restored {INTEGRATION_CONFIG_PATH} from {DISABLED_CONFIG_PATH}."
        )

    configure_report = configure_pr_autopilot(runner=runner)
    return _format_enable_report("Created and enabled PR Autopilot.") + "\n\n" + configure_report


def disable_pr_autopilot() -> str:
    """Disable PR Autopilot by removing the enabling TOML from the active set."""

    if not INTEGRATION_CONFIG_PATH.exists():
        return _format_disable_report("PR Autopilot already disabled.")

    config = _read_toml(INTEGRATION_CONFIG_PATH)
    config.setdefault("integration", {})["enabled"] = False
    VIBE_DIR.mkdir(exist_ok=True)
    _write_toml_if_changed(DISABLED_CONFIG_PATH, config)
    INTEGRATION_CONFIG_PATH.unlink()
    return _format_disable_report(
        f"Moved {INTEGRATION_CONFIG_PATH} to {DISABLED_CONFIG_PATH}; "
        "the active .toml file is absent, so the integration is off."
    )


def format_pr_autopilot_status(*, runner: ProviderRunner | None = None) -> str:
    """Reconcile the declarative PR Autopilot artifact against local reality."""

    run_tool = runner or _run_provider_tool
    active_config = _read_toml(INTEGRATION_CONFIG_PATH)
    disabled_config = _read_toml(DISABLED_CONFIG_PATH)
    core_config = _read_toml(CORE_CONFIG_PATH)
    config = active_config or disabled_config

    configured = bool(config)
    enabled = bool(active_config and config.get("integration", {}).get("enabled", True))
    auth_probe = run_tool(("gh", "auth", "status"))
    secrets_probe = run_tool(("gh", "secret", "list", "--json", "name")) if enabled else None
    secret_present = _secret_present(secrets_probe) if secrets_probe else None
    drift = _status_drift(enabled, secret_present, auth_probe)

    lines = [
        "PR Autopilot",
        f"  configured: {_yes_no(configured)}",
        f"  enabled: {_yes_no(enabled)}",
        f"  artifact: {_artifact_label(active_config, disabled_config)}",
        f"  github: {_github_label(core_config)}",
        f"  gh auth: {_probe_label(auth_probe)}",
        f"  secret {ANTHROPIC_SECRET_NAME}: {_secret_label(secret_present, enabled)}",
        f"  health: {_health_label(enabled, auth_probe, secret_present)}",
        f"  drift: {', '.join(drift) if drift else 'none'}",
    ]
    if not configured:
        lines.append("  next: bin/vibe pr-autopilot configure")
    elif enabled and secret_present is False:
        lines.append(f"  next: gh secret set {ANTHROPIC_SECRET_NAME}")
    lines.append("  engine: not installed (prototype config/status only)")
    return "\n".join(lines)


def inspect_pr_autopilot() -> str:
    """Print the reviewable artifact contents without secret values."""

    paths = [CORE_CONFIG_PATH, INTEGRATION_CONFIG_PATH]
    if not INTEGRATION_CONFIG_PATH.exists() and DISABLED_CONFIG_PATH.exists():
        paths[1] = DISABLED_CONFIG_PATH

    chunks = ["PR Autopilot artifacts", "Secrets are stored as provider refs, never values."]
    for path in paths:
        if not path.exists():
            chunks.append(f"\n# {path}\n(missing)")
            continue
        chunks.append(f"\n# {path}\n{path.read_text().rstrip()}")
    return "\n".join(chunks)


def _run_provider_tool(command: tuple[str, ...]) -> ToolResult:
    try:
        result = subprocess.run(
            list(command),
            capture_output=True,
            text=True,
            timeout=20,
            check=False,
        )
    except FileNotFoundError as exc:
        return ToolResult(command=command, returncode=127, stderr=str(exc))
    except subprocess.TimeoutExpired as exc:
        return ToolResult(
            command=command,
            returncode=124,
            stdout=exc.stdout or "",
            stderr=exc.stderr or "command timed out",
        )
    return ToolResult(
        command=command,
        returncode=result.returncode,
        stdout=result.stdout,
        stderr=result.stderr,
    )


def _infer_github_identity(repo_probe: ToolResult) -> tuple[str, str]:
    if repo_probe.ok and repo_probe.stdout.strip():
        try:
            payload = json.loads(repo_probe.stdout)
            owner = payload.get("owner", {})
            owner_login = owner.get("login") if isinstance(owner, dict) else str(owner)
            repo_name = str(payload.get("name") or "")
            if owner_login and repo_name:
                return str(owner_login), repo_name
        except json.JSONDecodeError:
            pass

    legacy = load_config()
    github = legacy.get("github", {})
    owner = str(github.get("owner") or "")
    repo = str(github.get("repo") or "")
    if owner and repo:
        return owner, repo

    remote = _remote_origin_slug()
    if remote:
        return remote
    return "", ""


def _infer_linear_team() -> str:
    if os.environ.get("LINEAR_TEAM"):
        return os.environ["LINEAR_TEAM"]
    legacy = load_config()
    tracker = legacy.get("tracker", {})
    config = tracker.get("config", {}) if isinstance(tracker, dict) else {}
    for key in ("team_name", "team_key", "team_id"):
        value = config.get(key)
        if value:
            return str(value)
    return ""


def _remote_origin_slug() -> tuple[str, str] | None:
    result = _run_provider_tool(("git", "remote", "get-url", "origin"))
    if not result.ok:
        return None
    remote = result.stdout.strip()
    if remote.endswith(".git"):
        remote = remote[:-4]
    if remote.startswith("git@") and ":" in remote:
        remote = remote.split(":", 1)[1]
    elif "://" in remote:
        remote = remote.rstrip("/").rsplit("/", 2)
        if len(remote) >= 2:
            return remote[-2], remote[-1]
        return None
    parts = remote.rsplit("/", 1)
    if len(parts) == 2:
        return parts[0].split("/")[-1], parts[1]
    return None


def _core_config(
    existing: dict[str, Any],
    github_owner: str,
    github_repo: str,
    linear_team: str,
) -> dict[str, Any]:
    config = dict(existing)
    github = dict(config.get("github", {}))
    if github_owner:
        github["owner"] = github_owner
    if github_repo:
        github["repo"] = github_repo
    config["github"] = github

    linear = dict(config.get("linear", {}))
    if linear_team:
        linear["team"] = linear_team
    config["linear"] = linear
    return config


def _integration_config(existing: dict[str, Any]) -> dict[str, Any]:
    config = dict(existing)
    config["integration"] = {
        **dict(config.get("integration", {})),
        "name": "pr-autopilot",
        "enabled": True,
        "prototype": True,
    }
    config["secrets"] = {
        **dict(config.get("secrets", {})),
        "anthropic_api_key": ANTHROPIC_SECRET_REF,
    }
    config["automation"] = {
        **{
            "base_branch": "main",
            "human_merge_gate": True,
            "max_watch_minutes": 90,
        },
        **dict(config.get("automation", {})),
    }
    config["providers"] = {
        **dict(config.get("providers", {})),
        "github_cli": "gh",
    }
    return config


def _read_toml(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return tomllib.loads(path.read_text())


def _write_toml_if_changed(path: Path, data: dict[str, Any]) -> bool:
    rendered = _render_toml(data)
    if path.exists() and path.read_text() == rendered:
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(rendered)
    return True


def _render_toml(data: dict[str, Any]) -> str:
    chunks: list[str] = []
    for section in sorted(data):
        value = data[section]
        if not isinstance(value, dict):
            continue
        chunks.append(f"[{section}]")
        for key in sorted(value):
            chunks.append(f"{key} = {_toml_value(value[key])}")
        chunks.append("")
    return "\n".join(chunks).rstrip() + "\n"


def _toml_value(value: Any) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int | float):
        return str(value)
    if value is None:
        return '""'
    return json.dumps(str(value))


def _format_configure_report(
    changed: list[str],
    repo_probe: ToolResult,
    secrets_probe: ToolResult,
    core_config: dict[str, Any],
) -> str:
    secret_present = _secret_present(secrets_probe)
    lines = [
        "PR Autopilot configure",
        "Native provider commands shown:",
        f"  {repo_probe.display} -> {_probe_label(repo_probe)}",
        f"  {secrets_probe.display} -> {_probe_label(secrets_probe)}",
        "Artifacts:",
        f"  changed: {', '.join(changed) if changed else 'none (already up to date)'}",
        f"  github: {_github_label(core_config)}",
        f"  secret ref: {ANTHROPIC_SECRET_REF}",
    ]
    if secret_present is True:
        lines.append(f"  secret check: {ANTHROPIC_SECRET_NAME} exists in GitHub Actions.")
    elif secret_present is False:
        lines.append("Human handoff:")
        lines.append(f"  Ask for the Anthropic key, then run: gh secret set {ANTHROPIC_SECRET_NAME}")
    else:
        lines.append("Human handoff:")
        lines.append("  Verify GitHub CLI auth, then rerun: bin/vibe pr-autopilot status")
    lines.append("Next:")
    lines.append("  bin/vibe pr-autopilot status")
    return "\n".join(lines)


def _format_enable_report(message: str) -> str:
    return "\n".join(["PR Autopilot enable", message, "Next: bin/vibe pr-autopilot status"])


def _format_disable_report(message: str) -> str:
    return "\n".join(["PR Autopilot disable", message, "Next: bin/vibe status"])


def _secret_present(result: ToolResult | None) -> bool | None:
    if result is None or not result.ok:
        return None
    try:
        payload = json.loads(result.stdout or "[]")
    except json.JSONDecodeError:
        return None
    if not isinstance(payload, list):
        return None
    names = {
        str(item.get("name"))
        for item in payload
        if isinstance(item, dict) and item.get("name") is not None
    }
    return ANTHROPIC_SECRET_NAME in names


def _status_drift(
    enabled: bool,
    secret_present: bool | None,
    auth_probe: ToolResult,
) -> list[str]:
    drift: list[str] = []
    if enabled and not auth_probe.ok:
        drift.append("github auth unavailable")
    if enabled and secret_present is False:
        drift.append(f"missing GitHub secret {ANTHROPIC_SECRET_NAME}")
    if enabled and secret_present is None:
        drift.append("secret state unknown")
    return drift


def _artifact_label(active_config: dict[str, Any], disabled_config: dict[str, Any]) -> str:
    if active_config:
        return str(INTEGRATION_CONFIG_PATH)
    if disabled_config:
        return str(DISABLED_CONFIG_PATH)
    return "missing"


def _github_label(core_config: dict[str, Any]) -> str:
    github = core_config.get("github", {})
    owner = github.get("owner") if isinstance(github, dict) else ""
    repo = github.get("repo") if isinstance(github, dict) else ""
    if owner and repo:
        return f"{owner}/{repo}"
    return "unknown"


def _probe_label(result: ToolResult) -> str:
    if result.ok:
        return "ok"
    if result.returncode == 127:
        return "tool missing"
    if result.returncode == 124:
        return "timed out"
    return f"exit {result.returncode}"


def _secret_label(secret_present: bool | None, enabled: bool) -> str:
    if not enabled:
        return "not checked while disabled"
    if secret_present is True:
        return "present"
    if secret_present is False:
        return f"missing ({ANTHROPIC_SECRET_REF})"
    return f"unknown ({ANTHROPIC_SECRET_REF})"


def _health_label(
    enabled: bool,
    auth_probe: ToolResult,
    secret_present: bool | None,
) -> str:
    if not enabled:
        return "disabled"
    if auth_probe.ok and secret_present is True:
        return "configured; engine pending"
    if secret_present is False:
        return "needs human secret handoff"
    return "needs provider verification"


def _yes_no(value: bool) -> str:
    return "yes" if value else "no"
