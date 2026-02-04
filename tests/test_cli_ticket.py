"""Tests for ticket CLI commands."""

from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from lib.vibe.cli.ticket import (
    ensure_tracker_configured,
    get_tracker,
    main,
    print_ticket,
    print_ticket_summary,
)
from lib.vibe.trackers.base import Ticket


class TestGetTracker:
    """Tests for get_tracker function."""

    def test_get_tracker_linear(self) -> None:
        config = {"tracker": {"type": "linear", "config": {"team_id": "team123"}}}

        with patch("lib.vibe.cli.ticket.load_config", return_value=config):
            tracker = get_tracker()

        assert tracker is not None
        assert tracker.name == "linear"
        assert tracker._team_id == "team123"

    def test_get_tracker_shortcut(self) -> None:
        config = {"tracker": {"type": "shortcut", "config": {}}}

        with patch("lib.vibe.cli.ticket.load_config", return_value=config):
            tracker = get_tracker()

        assert tracker is not None
        assert tracker.name == "shortcut"

    def test_get_tracker_none_configured(self) -> None:
        config = {"tracker": {"type": None}}

        with (
            patch("lib.vibe.cli.ticket.load_config", return_value=config),
            patch.dict("os.environ", {}, clear=True),
        ):
            tracker = get_tracker()

        assert tracker is None

    def test_get_tracker_from_env_linear(self) -> None:
        config = {"tracker": {"type": None, "config": {}}}

        with (
            patch("lib.vibe.cli.ticket.load_config", return_value=config),
            patch.dict(
                "os.environ", {"LINEAR_API_KEY": "lin_api_test", "LINEAR_TEAM_ID": "team_from_env"}
            ),
        ):
            tracker = get_tracker()

        assert tracker is not None
        assert tracker.name == "linear"
        assert tracker._team_id == "team_from_env"


class TestEnsureTrackerConfigured:
    """Tests for ensure_tracker_configured function."""

    def test_ensure_tracker_configured_already_configured(self) -> None:
        mock_tracker = MagicMock()
        mock_tracker.name = "linear"

        with patch("lib.vibe.cli.ticket.get_tracker", return_value=mock_tracker):
            tracker = ensure_tracker_configured()

        assert tracker is mock_tracker

    def test_ensure_tracker_configured_wizard_success(self) -> None:
        mock_tracker = MagicMock()
        mock_tracker.name = "linear"

        call_count = {"get_tracker": 0}

        def get_tracker_side_effect():
            call_count["get_tracker"] += 1
            if call_count["get_tracker"] == 1:
                return None  # First call: not configured
            return mock_tracker  # After wizard: configured

        with (
            patch("lib.vibe.cli.ticket.get_tracker", side_effect=get_tracker_side_effect),
            patch("lib.vibe.cli.ticket.click.confirm", return_value=True),
            patch("lib.vibe.cli.ticket.load_config", return_value={}),
            patch("lib.vibe.cli.ticket.run_tracker_wizard", return_value=True),
            patch("lib.vibe.cli.ticket.save_config"),
        ):
            tracker = ensure_tracker_configured()

        assert tracker is mock_tracker

    def test_ensure_tracker_configured_user_declines(self) -> None:
        with (
            patch("lib.vibe.cli.ticket.get_tracker", return_value=None),
            patch("lib.vibe.cli.ticket.click.confirm", return_value=False),
            patch("lib.vibe.cli.ticket.click.echo"),
        ):
            with pytest.raises(SystemExit) as exc_info:
                ensure_tracker_configured()

        assert exc_info.value.code == 1

    def test_ensure_tracker_configured_wizard_fails(self) -> None:
        with (
            patch("lib.vibe.cli.ticket.get_tracker", return_value=None),
            patch("lib.vibe.cli.ticket.click.confirm", return_value=True),
            patch("lib.vibe.cli.ticket.load_config", return_value={}),
            patch("lib.vibe.cli.ticket.run_tracker_wizard", return_value=False),
            patch("lib.vibe.cli.ticket.click.echo"),
        ):
            with pytest.raises(SystemExit) as exc_info:
                ensure_tracker_configured()

        assert exc_info.value.code == 1


class TestTicketCLI:
    """Tests for ticket CLI commands."""

    def test_get_command_success(self) -> None:
        runner = CliRunner()
        mock_tracker = MagicMock()
        mock_ticket = Ticket(
            id="TEST-1",
            title="Test Ticket",
            description="Description",
            status="Todo",
            labels=["Bug"],
            url="https://example.com/TEST-1",
            raw={},
        )
        mock_tracker.get_ticket.return_value = mock_ticket

        with patch("lib.vibe.cli.ticket.ensure_tracker_configured", return_value=mock_tracker):
            result = runner.invoke(main, ["get", "TEST-1"])

        assert result.exit_code == 0
        assert "TEST-1" in result.output
        assert "Test Ticket" in result.output
        assert "Todo" in result.output

    def test_get_command_not_found(self) -> None:
        runner = CliRunner()
        mock_tracker = MagicMock()
        mock_tracker.get_ticket.return_value = None

        with patch("lib.vibe.cli.ticket.ensure_tracker_configured", return_value=mock_tracker):
            result = runner.invoke(main, ["get", "NONEXISTENT"])

        assert result.exit_code == 1
        assert "not found" in result.output

    def test_list_command_success(self) -> None:
        runner = CliRunner()
        mock_tracker = MagicMock()
        mock_tickets = [
            Ticket(
                id="TEST-1",
                title="Ticket 1",
                description="",
                status="Todo",
                labels=[],
                url="",
                raw={},
            ),
            Ticket(
                id="TEST-2",
                title="Ticket 2",
                description="",
                status="In Progress",
                labels=["Bug"],
                url="",
                raw={},
            ),
        ]
        mock_tracker.list_tickets.return_value = mock_tickets

        with patch("lib.vibe.cli.ticket.ensure_tracker_configured", return_value=mock_tracker):
            result = runner.invoke(main, ["list"])

        assert result.exit_code == 0
        assert "TEST-1" in result.output
        assert "TEST-2" in result.output

    def test_list_command_with_filters(self) -> None:
        runner = CliRunner()
        mock_tracker = MagicMock()
        mock_tracker.list_tickets.return_value = []

        with patch("lib.vibe.cli.ticket.ensure_tracker_configured", return_value=mock_tracker):
            result = runner.invoke(
                main, ["list", "--status", "Done", "--label", "Bug", "--limit", "5"]
            )

        assert result.exit_code == 0
        mock_tracker.list_tickets.assert_called_once_with(status="Done", labels=["Bug"], limit=5)

    def test_list_command_empty(self) -> None:
        runner = CliRunner()
        mock_tracker = MagicMock()
        mock_tracker.list_tickets.return_value = []

        with patch("lib.vibe.cli.ticket.ensure_tracker_configured", return_value=mock_tracker):
            result = runner.invoke(main, ["list"])

        assert result.exit_code == 0
        assert "No tickets found" in result.output

    def test_create_command_success(self) -> None:
        runner = CliRunner()
        mock_tracker = MagicMock()
        mock_ticket = Ticket(
            id="TEST-100",
            title="New Ticket",
            description="Description",
            status="Backlog",
            labels=[],
            url="https://example.com/TEST-100",
            raw={},
        )
        mock_tracker.create_ticket.return_value = mock_ticket

        with patch("lib.vibe.cli.ticket.ensure_tracker_configured", return_value=mock_tracker):
            result = runner.invoke(main, ["create", "New Ticket", "-d", "Description"])

        assert result.exit_code == 0
        assert "Created ticket: TEST-100" in result.output
        mock_tracker.create_ticket.assert_called_once_with(
            title="New Ticket", description="Description", labels=None
        )

    def test_create_command_with_labels(self) -> None:
        runner = CliRunner()
        mock_tracker = MagicMock()
        mock_ticket = Ticket(
            id="TEST-101",
            title="Labeled",
            description="",
            status="Backlog",
            labels=["Bug", "High Risk"],
            url="",
            raw={},
        )
        mock_tracker.create_ticket.return_value = mock_ticket

        with patch("lib.vibe.cli.ticket.ensure_tracker_configured", return_value=mock_tracker):
            result = runner.invoke(main, ["create", "Labeled", "-l", "Bug", "-l", "High Risk"])

        assert result.exit_code == 0
        mock_tracker.create_ticket.assert_called_once_with(
            title="Labeled", description="", labels=["Bug", "High Risk"]
        )

    def test_update_command_success(self) -> None:
        runner = CliRunner()
        mock_tracker = MagicMock()
        mock_ticket = Ticket(
            id="TEST-1",
            title="Updated Title",
            description="",
            status="In Progress",
            labels=[],
            url="https://example.com/TEST-1",
            raw={},
        )
        mock_tracker.update_ticket.return_value = mock_ticket

        with patch("lib.vibe.cli.ticket.ensure_tracker_configured", return_value=mock_tracker):
            result = runner.invoke(main, ["update", "TEST-1", "-s", "In Progress"])

        assert result.exit_code == 0
        assert "Updated: TEST-1" in result.output

    def test_update_command_no_options(self) -> None:
        runner = CliRunner()
        mock_tracker = MagicMock()

        with patch("lib.vibe.cli.ticket.ensure_tracker_configured", return_value=mock_tracker):
            result = runner.invoke(main, ["update", "TEST-1"])

        assert result.exit_code == 1
        assert "Specify at least one of" in result.output

    def test_close_command_done(self) -> None:
        runner = CliRunner()
        mock_tracker = MagicMock()
        mock_ticket = Ticket(
            id="TEST-1",
            title="Title",
            description="",
            status="Done",
            labels=[],
            url="https://example.com/TEST-1",
            raw={},
        )
        mock_tracker.update_ticket.return_value = mock_ticket

        with patch("lib.vibe.cli.ticket.ensure_tracker_configured", return_value=mock_tracker):
            result = runner.invoke(main, ["close", "TEST-1"])

        assert result.exit_code == 0
        mock_tracker.update_ticket.assert_called_once_with("TEST-1", status="Done")

    def test_close_command_canceled(self) -> None:
        runner = CliRunner()
        mock_tracker = MagicMock()
        mock_ticket = Ticket(
            id="TEST-1",
            title="Title",
            description="",
            status="Canceled",
            labels=[],
            url="",
            raw={},
        )
        mock_tracker.update_ticket.return_value = mock_ticket

        with patch("lib.vibe.cli.ticket.ensure_tracker_configured", return_value=mock_tracker):
            result = runner.invoke(main, ["close", "TEST-1", "--cancel"])

        assert result.exit_code == 0
        mock_tracker.update_ticket.assert_called_once_with("TEST-1", status="Canceled")

    def test_comment_command_success(self) -> None:
        runner = CliRunner()
        mock_tracker = MagicMock()

        with patch("lib.vibe.cli.ticket.ensure_tracker_configured", return_value=mock_tracker):
            result = runner.invoke(main, ["comment", "TEST-1", "This is a comment"])

        assert result.exit_code == 0
        assert "Comment added" in result.output
        mock_tracker.comment_ticket.assert_called_once_with("TEST-1", "This is a comment")

    def test_labels_command_success(self) -> None:
        runner = CliRunner()
        mock_tracker = MagicMock()
        mock_tracker.list_labels.return_value = [
            {"id": "1", "name": "Bug", "color": "#ff0000"},
            {"id": "2", "name": "Feature", "color": "#00ff00"},
        ]

        with patch("lib.vibe.cli.ticket.ensure_tracker_configured", return_value=mock_tracker):
            result = runner.invoke(main, ["labels"])

        assert result.exit_code == 0
        assert "Bug" in result.output
        assert "Feature" in result.output

    def test_labels_command_json(self) -> None:
        runner = CliRunner()
        mock_tracker = MagicMock()
        mock_tracker.list_labels.return_value = [{"id": "1", "name": "Bug", "color": "#ff0000"}]

        with patch("lib.vibe.cli.ticket.ensure_tracker_configured", return_value=mock_tracker):
            result = runner.invoke(main, ["labels", "--json"])

        assert result.exit_code == 0
        assert '"name": "Bug"' in result.output

    def test_labels_command_not_supported(self) -> None:
        runner = CliRunner()
        mock_tracker = MagicMock(spec=[])  # No list_labels method

        with patch("lib.vibe.cli.ticket.ensure_tracker_configured", return_value=mock_tracker):
            result = runner.invoke(main, ["labels"])

        assert result.exit_code == 1
        assert "not supported" in result.output


class TestHumanFollowupCommand:
    """Tests for create-human-followup command."""

    def test_human_followup_print_only(self, tmp_path) -> None:
        runner = CliRunner()
        # Create a fly.toml file
        fly_toml = tmp_path / "fly.toml"
        fly_toml.write_text("app = 'test'\n")

        with runner.isolated_filesystem(temp_dir=tmp_path):
            with patch("lib.vibe.cli.ticket.load_config", return_value={"github": {}}):
                result = runner.invoke(
                    main, ["create-human-followup", "--files", "fly.toml", "--print-only"]
                )

        assert result.exit_code == 0
        assert "Title:" in result.output
        assert "HUMAN" in result.output

    def test_human_followup_no_platforms(self, tmp_path) -> None:
        runner = CliRunner()

        with runner.isolated_filesystem(temp_dir=tmp_path):
            with patch("lib.vibe.cli.ticket.load_config", return_value={"github": {}}):
                result = runner.invoke(
                    main, ["create-human-followup", "--files", "nonexistent.txt"]
                )

        assert result.exit_code == 1
        assert "No deployment configs" in result.output


class TestPrintFunctions:
    """Tests for print helper functions."""

    def test_print_ticket(self, capsys) -> None:
        ticket = Ticket(
            id="TEST-1",
            title="Test Title",
            description="Test description content",
            status="In Progress",
            labels=["Bug", "High Risk"],
            url="https://example.com/TEST-1",
            raw={},
        )

        print_ticket(ticket)
        captured = capsys.readouterr()

        assert "TEST-1" in captured.out
        assert "Test Title" in captured.out
        assert "In Progress" in captured.out
        assert "Bug, High Risk" in captured.out
        assert "Test description content" in captured.out

    def test_print_ticket_no_description(self, capsys) -> None:
        ticket = Ticket(
            id="TEST-2",
            title="No Description",
            description="",
            status="Todo",
            labels=[],
            url="",
            raw={},
        )

        print_ticket(ticket)
        captured = capsys.readouterr()

        assert "TEST-2" in captured.out
        assert "Description:" not in captured.out

    def test_print_ticket_summary(self, capsys) -> None:
        ticket = Ticket(
            id="TEST-3",
            title="Summary Test",
            description="",
            status="Done",
            labels=["Feature"],
            url="",
            raw={},
        )

        print_ticket_summary(ticket)
        captured = capsys.readouterr()

        assert "TEST-3: Summary Test (Done) [Feature]" in captured.out

    def test_print_ticket_summary_no_labels(self, capsys) -> None:
        ticket = Ticket(
            id="TEST-4",
            title="No Labels",
            description="",
            status="Backlog",
            labels=[],
            url="",
            raw={},
        )

        print_ticket_summary(ticket)
        captured = capsys.readouterr()

        assert "TEST-4: No Labels (Backlog)" in captured.out
        assert "[" not in captured.out
