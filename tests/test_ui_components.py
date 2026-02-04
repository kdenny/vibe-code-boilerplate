"""Tests for UI components."""

from unittest.mock import MagicMock, patch

import pytest

from lib.vibe.ui.components import (
    ConfirmWithHelp,
    MenuOption,
    MultiSelect,
    NumberedMenu,
    ProgressIndicator,
    SelectOption,
    SkillLevel,
    SkillLevelSelector,
    WhatNextFlow,
    WizardSuggestion,
)


class TestMenuOption:
    def test_default_value_is_label(self) -> None:
        opt = MenuOption(label="Test", description="A test option")
        assert opt.value == "Test"

    def test_custom_value(self) -> None:
        opt = MenuOption(label="Test", description="A test option", value="custom")
        assert opt.value == "custom"


class TestNumberedMenu:
    def test_initialization(self) -> None:
        menu = NumberedMenu(
            title="Select:",
            options=[("A", "First"), ("B", "Second")],
            default=2,
        )
        assert menu.title == "Select:"
        assert len(menu.options) == 2
        assert menu.default == 2
        assert menu.options[0].label == "A"
        assert menu.options[1].description == "Second"

    @patch("click.prompt")
    @patch("click.echo")
    def test_show_returns_valid_choice(self, mock_echo: MagicMock, mock_prompt: MagicMock) -> None:
        mock_prompt.return_value = 2
        menu = NumberedMenu(
            title="Select:",
            options=[("A", "First"), ("B", "Second")],
        )
        result = menu.show()
        assert result == 2

    @patch("click.prompt")
    @patch("click.echo")
    def test_show_uses_default(self, mock_echo: MagicMock, mock_prompt: MagicMock) -> None:
        mock_prompt.return_value = 1  # Default
        menu = NumberedMenu(
            title="Select:",
            options=[("A", "First"), ("B", "Second")],
            default=1,
        )
        result = menu.show()
        assert result == 1
        # Verify prompt was called with default=1
        mock_prompt.assert_called_once()
        assert mock_prompt.call_args[1]["default"] == 1

    def test_get_selected_label(self) -> None:
        menu = NumberedMenu(
            title="Select:",
            options=[("A", "First"), ("B", "Second")],
        )
        assert menu.get_selected_label(1) == "A"
        assert menu.get_selected_label(2) == "B"
        assert menu.get_selected_label(0) == ""
        assert menu.get_selected_label(3) == ""


class TestProgressIndicator:
    def test_initialization(self) -> None:
        progress = ProgressIndicator(total_steps=5)
        assert progress.total_steps == 5
        assert progress.current_step == 0

    @patch("click.echo")
    def test_advance_increments_step(self, mock_echo: MagicMock) -> None:
        progress = ProgressIndicator(total_steps=3)
        progress.advance("Step One")
        assert progress.current_step == 1
        progress.advance("Step Two")
        assert progress.current_step == 2

    @patch("click.echo")
    def test_advance_displays_progress(self, mock_echo: MagicMock) -> None:
        progress = ProgressIndicator(total_steps=3)
        progress.advance("GitHub Setup")
        # Check that output includes step number and name
        calls = [str(call) for call in mock_echo.call_args_list]
        assert any("Step 1 of 3" in str(call) for call in calls)
        assert any("GitHub Setup" in str(call) for call in calls)

    def test_current_returns_step(self) -> None:
        progress = ProgressIndicator(total_steps=3)
        assert progress.current() == 0
        with patch("click.echo"):
            progress.advance("Test")
        assert progress.current() == 1

    def test_reset(self) -> None:
        progress = ProgressIndicator(total_steps=3)
        with patch("click.echo"):
            progress.advance("Test")
        progress.reset()
        assert progress.current_step == 0


class TestSkillLevelSelector:
    @patch("click.prompt")
    @patch("click.echo")
    def test_show_returns_beginner(self, mock_echo: MagicMock, mock_prompt: MagicMock) -> None:
        mock_prompt.return_value = 1
        selector = SkillLevelSelector()
        result = selector.show()
        assert result == SkillLevel.BEGINNER

    @patch("click.prompt")
    @patch("click.echo")
    def test_show_returns_intermediate(
        self, mock_echo: MagicMock, mock_prompt: MagicMock
    ) -> None:
        mock_prompt.return_value = 2
        selector = SkillLevelSelector()
        result = selector.show()
        assert result == SkillLevel.INTERMEDIATE

    @patch("click.prompt")
    @patch("click.echo")
    def test_show_returns_expert(self, mock_echo: MagicMock, mock_prompt: MagicMock) -> None:
        mock_prompt.return_value = 3
        selector = SkillLevelSelector()
        result = selector.show()
        assert result == SkillLevel.EXPERT

    def test_custom_prompt(self) -> None:
        selector = SkillLevelSelector(prompt_text="How good are you?")
        assert selector.prompt_text == "How good are you?"


class TestConfirmWithHelp:
    @patch("click.confirm")
    def test_show_without_help(self, mock_confirm: MagicMock) -> None:
        mock_confirm.return_value = True
        confirm = ConfirmWithHelp(message="Continue?")
        result = confirm.show()
        assert result is True

    @patch("click.confirm")
    @patch("click.echo")
    def test_show_with_help_for_beginner(
        self, mock_echo: MagicMock, mock_confirm: MagicMock
    ) -> None:
        mock_confirm.return_value = True
        confirm = ConfirmWithHelp(
            message="Enable feature?",
            help_text="This feature does X.",
        )
        confirm.show(skill_level=SkillLevel.BEGINNER)
        # Help text should be displayed for beginners
        calls = [str(call) for call in mock_echo.call_args_list]
        assert any("This feature does X" in str(call) for call in calls)

    @patch("click.confirm")
    @patch("click.echo")
    def test_show_without_help_for_expert(
        self, mock_echo: MagicMock, mock_confirm: MagicMock
    ) -> None:
        mock_confirm.return_value = True
        confirm = ConfirmWithHelp(
            message="Enable feature?",
            help_text="This feature does X.",
        )
        confirm.show(skill_level=SkillLevel.EXPERT)
        # Help text should not be displayed for experts
        calls = [str(call) for call in mock_echo.call_args_list]
        assert not any("This feature does X" in str(call) for call in calls)


class TestSelectOption:
    def test_default_value_is_label(self) -> None:
        opt = SelectOption(label="Test", description="A test", selected=True)
        assert opt.value == "Test"

    def test_custom_value(self) -> None:
        opt = SelectOption(label="Test", description="A test", selected=True, value="custom")
        assert opt.value == "custom"


class TestMultiSelect:
    def test_initialization(self) -> None:
        multi = MultiSelect(
            title="Select:",
            options=[
                ("A", "First", True),
                ("B", "Second", False),
            ],
        )
        assert len(multi.options) == 2
        assert multi.options[0].selected is True
        assert multi.options[1].selected is False

    @patch("click.prompt")
    @patch("click.echo")
    def test_show_returns_selected_indices(
        self, mock_echo: MagicMock, mock_prompt: MagicMock
    ) -> None:
        # Simulate user pressing Enter to confirm
        mock_prompt.return_value = ""
        multi = MultiSelect(
            title="Select:",
            options=[
                ("A", "First", True),
                ("B", "Second", True),
                ("C", "Third", False),
            ],
        )
        result = multi.show()
        assert result == [1, 2]  # A and B are selected

    @patch("click.prompt")
    @patch("click.echo")
    def test_show_toggle_selection(
        self, mock_echo: MagicMock, mock_prompt: MagicMock
    ) -> None:
        # First prompt: toggle option 1 (A off), second prompt: toggle option 2 (B on), third: confirm
        mock_prompt.side_effect = ["1", "2", ""]
        multi = MultiSelect(
            title="Select:",
            options=[
                ("A", "First", True),
                ("B", "Second", False),
            ],
        )
        result = multi.show()
        assert result == [2]  # A was toggled off, B was toggled on

    @patch("click.prompt")
    @patch("click.echo")
    def test_show_select_all(self, mock_echo: MagicMock, mock_prompt: MagicMock) -> None:
        # First prompt: select all, second prompt: confirm
        mock_prompt.side_effect = ["a", ""]
        multi = MultiSelect(
            title="Select:",
            options=[
                ("A", "First", False),
                ("B", "Second", False),
            ],
        )
        result = multi.show()
        assert result == [1, 2]

    @patch("click.prompt")
    @patch("click.echo")
    def test_show_select_none(self, mock_echo: MagicMock, mock_prompt: MagicMock) -> None:
        # First prompt: select none, second prompt: confirm
        mock_prompt.side_effect = ["n", ""]
        multi = MultiSelect(
            title="Select:",
            options=[
                ("A", "First", True),
                ("B", "Second", True),
            ],
        )
        result = multi.show()
        assert result == []

    def test_get_selected_labels(self) -> None:
        multi = MultiSelect(
            title="Select:",
            options=[
                ("A", "First", True),
                ("B", "Second", False),
                ("C", "Third", True),
            ],
        )
        labels = multi.get_selected_labels()
        assert labels == ["A", "C"]


class TestWizardSuggestion:
    def test_creation(self) -> None:
        suggestion = WizardSuggestion(
            wizard_name="tracker",
            reason="Set up ticket tracking",
            priority=1,
        )
        assert suggestion.wizard_name == "tracker"
        assert suggestion.reason == "Set up ticket tracking"
        assert suggestion.priority == 1


class TestWhatNextFlow:
    def test_get_suggestions_for_github(self) -> None:
        config: dict = {"tracker": {"type": None}}
        flow = WhatNextFlow("github", config)
        suggestions = flow.get_suggestions()
        wizard_names = [s.wizard_name for s in suggestions]
        assert "tracker" in wizard_names

    def test_get_suggestions_filters_configured(self) -> None:
        config = {"tracker": {"type": "linear"}}  # Already configured
        flow = WhatNextFlow("github", config)
        suggestions = flow.get_suggestions()
        wizard_names = [s.wizard_name for s in suggestions]
        assert "tracker" not in wizard_names

    def test_get_suggestions_sorted_by_priority(self) -> None:
        config: dict = {}
        flow = WhatNextFlow("database", config)
        suggestions = flow.get_suggestions()
        if len(suggestions) > 1:
            # Higher priority items should come first (lower number)
            priorities = [s.priority for s in suggestions]
            assert priorities == sorted(priorities)

    def test_is_configured_github(self) -> None:
        flow = WhatNextFlow("github", {"github": {"auth_method": "gh_cli"}})
        assert flow._is_configured("github") is True

        flow = WhatNextFlow("github", {"github": {}})
        assert flow._is_configured("github") is False

    def test_is_configured_tracker(self) -> None:
        flow = WhatNextFlow("github", {"tracker": {"type": "linear"}})
        assert flow._is_configured("tracker") is True

        flow = WhatNextFlow("github", {"tracker": {"type": None}})
        assert flow._is_configured("tracker") is False

    def test_is_configured_vercel(self) -> None:
        flow = WhatNextFlow("github", {"deployment": {"vercel": {"enabled": True}}})
        assert flow._is_configured("vercel") is True

        flow = WhatNextFlow("github", {"deployment": {}})
        assert flow._is_configured("vercel") is False

    @patch("click.prompt")
    @patch("click.echo")
    def test_show_returns_wizard_name(
        self, mock_echo: MagicMock, mock_prompt: MagicMock
    ) -> None:
        mock_prompt.return_value = 1  # Select first option
        config: dict = {"tracker": {"type": None}}
        flow = WhatNextFlow("github", config)
        result = flow.show()
        # First suggestion for github is tracker
        assert result == "tracker"

    @patch("click.prompt")
    @patch("click.echo")
    def test_show_returns_none_for_done(
        self, mock_echo: MagicMock, mock_prompt: MagicMock
    ) -> None:
        # Select last option which is "Done"
        mock_prompt.return_value = 3  # tracker, database, Done
        config: dict = {"tracker": {"type": None}}
        flow = WhatNextFlow("github", config)
        result = flow.show()
        assert result is None

    @patch("click.echo")
    def test_show_when_all_configured(self, mock_echo: MagicMock) -> None:
        config = {
            "tracker": {"type": "linear"},
            "database": {"neon": {"enabled": True}},
            "deployment": {"vercel": {"enabled": True}},
            "observability": {"sentry": {"enabled": True}},
            "testing": {"playwright": {"enabled": True}},
        }
        flow = WhatNextFlow("github", config)
        result = flow.show()
        assert result is None  # No suggestions available
