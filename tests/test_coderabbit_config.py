"""Schema-validity guard for .coderabbit.yaml.

CodeRabbit silently falls back to its DEFAULT config if any field in
.coderabbit.yaml exceeds the schema's maxLength — so an over-limit edit can
quietly disable the entire review firewall with no error anywhere. These tests
fail loudly instead, and additionally pin the few policy invariants that make the
config a guardrail rather than a roadblock (see docs/review/coderabbit-policy.md).
"""

from pathlib import Path

import pytest

yaml = pytest.importorskip("yaml")

CONFIG_PATH = Path(__file__).resolve().parents[1] / ".coderabbit.yaml"

# maxLength limits from the CodeRabbit config schema. Over any of these, the WHOLE
# config silently reverts to defaults. Values verified against the published schema
# (https://storage.googleapis.com/coderabbit_public_assets/schema.v2.json):
# tone_instructions=250, path_instructions[].instructions=20000,
# pre_merge_checks.custom_checks[].instructions=10000. NOTE: the custom-checks cap
# (10k) is deliberately DIFFERENT from the path-instructions cap (20k) — do not
# "align" them. Docs informally suggest ~1k for custom checks, but the schema's hard
# maxLength is 10k; this guard tracks the hard limit that triggers the silent revert.
MAX_TONE_INSTRUCTIONS = 250
MAX_PATH_INSTRUCTIONS = 20_000
MAX_CUSTOM_CHECK_INSTRUCTIONS = 10_000


@pytest.fixture(scope="module")
def config() -> dict:
    assert CONFIG_PATH.exists(), f"missing {CONFIG_PATH}"
    return yaml.safe_load(CONFIG_PATH.read_text())


def test_yaml_parses(config: dict) -> None:
    assert isinstance(config, dict) and config, "config must parse to a non-empty mapping"


def test_tone_instructions_within_limit(config: dict) -> None:
    tone = config.get("tone_instructions", "")
    assert len(tone) <= MAX_TONE_INSTRUCTIONS, (
        f"tone_instructions is {len(tone)} chars (>{MAX_TONE_INSTRUCTIONS}); "
        "CodeRabbit would silently fall back to its default config."
    )


def test_path_instructions_within_limit(config: dict) -> None:
    for entry in config["reviews"]["path_instructions"]:
        text = entry.get("instructions", "")
        assert len(text) <= MAX_PATH_INSTRUCTIONS, (
            f"path_instructions for {entry.get('path')!r} is {len(text)} chars "
            f"(>{MAX_PATH_INSTRUCTIONS})."
        )


def test_custom_check_instructions_within_limit(config: dict) -> None:
    checks = config["reviews"]["pre_merge_checks"].get("custom_checks", [])
    for check in checks:
        text = check.get("instructions", "")
        assert len(text) <= MAX_CUSTOM_CHECK_INSTRUCTIONS, (
            f"custom_check {check.get('name')!r} is {len(text)} chars "
            f"(>{MAX_CUSTOM_CHECK_INSTRUCTIONS})."
        )


def test_guardrail_invariants_retained(config: dict) -> None:
    """The blocking set must still hard-block: request_changes_workflow on, ticket
    title still an error gate."""
    reviews = config["reviews"]
    assert reviews["request_changes_workflow"] is True
    assert reviews["pre_merge_checks"]["title"]["mode"] == "error"


def test_global_verdict_policy_present(config: dict) -> None:
    """The approve-by-default / block-only-what-compounds policy lives in the
    catch-all '**' path instruction; losing it would silently make review strict
    again."""
    paths = {e.get("path") for e in config["reviews"]["path_instructions"]}
    assert "**" in paths, "global '**' verdict-policy path_instruction is missing"
