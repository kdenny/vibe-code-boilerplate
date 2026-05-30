"""Tests for CLI fault signalling (vibe/cli/errors.py, VIBE-206)."""

import sys

import click
import pytest

from vibe.cli.errors import (
    FAULT_MARKER,
    TOOLING_FAULT_EXIT_CODE,
    normalize_signature,
    run_cli,
)


class TestNormalizeSignature:
    """The dedup fingerprint must ignore volatile detail."""

    def test_same_fault_with_different_paths_lines_hex_matches(self) -> None:
        a = normalize_signature("RuntimeError: boom at /Users/x/y.py line 42 0xdeadbeef")
        b = normalize_signature("RuntimeError: boom at /tmp/other/z.py line 7 0xfeed")
        assert a == b

    def test_collapses_whitespace_and_lowercases(self) -> None:
        assert normalize_signature("  Foo   Bar\n") == "foo bar"

    def test_uuid_is_normalized(self) -> None:
        s = normalize_signature("task 12345678-1234-1234-1234-123456789abc failed")
        assert "<uuid>" in s
        assert "12345678" not in s


@click.command()
def _ok_cmd() -> None:
    click.echo("ok")


@click.command()
def _boom_cmd() -> None:
    raise RuntimeError("kaboom at /tmp/a.py line 5")


@click.command()
@click.argument("name")
def _needs_arg_cmd(name: str) -> None:
    click.echo(name)


class TestRunCli:
    """run_cli self-classifies unexpected crashes; passes user errors through."""

    def test_crash_emits_marker_and_fault_exit_code(self, capsys, monkeypatch) -> None:
        monkeypatch.setattr(sys, "argv", ["prog"])
        with pytest.raises(SystemExit) as exc:
            run_cli(_boom_cmd, "vibe.cli.test")
        assert exc.value.code == TOOLING_FAULT_EXIT_CODE
        assert FAULT_MARKER in capsys.readouterr().err

    def test_normal_completion_passes_through_without_marker(self, capsys, monkeypatch) -> None:
        monkeypatch.setattr(sys, "argv", ["prog"])
        with pytest.raises(SystemExit) as exc:
            run_cli(_ok_cmd, "vibe.cli.test")
        assert exc.value.code == 0
        captured = capsys.readouterr()
        assert FAULT_MARKER not in (captured.out + captured.err)

    def test_usage_error_is_not_a_tooling_fault(self, capsys, monkeypatch) -> None:
        monkeypatch.setattr(sys, "argv", ["prog"])  # required NAME missing
        with pytest.raises(SystemExit) as exc:
            run_cli(_needs_arg_cmd, "vibe.cli.test")
        assert exc.value.code == 2  # click usage error
        assert FAULT_MARKER not in capsys.readouterr().err
