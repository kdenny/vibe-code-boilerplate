"""Core UI components for interactive wizards."""

import sys
import threading
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

import click


class SkillLevel(Enum):
    """User skill level for adapting wizard verbosity."""

    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    EXPERT = "expert"


@dataclass
class MenuOption:
    """A single menu option."""

    label: str
    description: str
    value: Any = None

    def __post_init__(self) -> None:
        if self.value is None:
            self.value = self.label


class NumberedMenu:
    """Consistent numbered menu selection.

    Example:
        menu = NumberedMenu(
            title="Select your tracker:",
            options=[
                ("Linear", "Full integration"),
                ("Shortcut", "Coming soon"),
                ("None", "Skip"),
            ]
        )
        choice = menu.show()  # Returns 1-based index
    """

    def __init__(
        self,
        title: str,
        options: list[tuple[str, str]],
        default: int = 1,
        show_numbers: bool = True,
    ):
        """Initialize menu.

        Args:
            title: Menu title/prompt
            options: List of (label, description) tuples
            default: Default option (1-based)
            show_numbers: Whether to show option numbers
        """
        self.title = title
        self.options = [MenuOption(label=opt[0], description=opt[1]) for opt in options]
        self.default = default
        self.show_numbers = show_numbers

    def show(self) -> int:
        """Display menu and get user selection.

        Returns:
            1-based index of selected option
        """
        click.echo(self.title)
        click.echo()

        for i, opt in enumerate(self.options, 1):
            if self.show_numbers:
                click.echo(f"  {i}. {opt.label} - {opt.description}")
            else:
                click.echo(f"  • {opt.label} - {opt.description}")

        click.echo()

        while True:
            choice: int = click.prompt(
                "Select option",
                type=int,
                default=self.default,
            )

            if 1 <= choice <= len(self.options):
                return choice

            click.echo(f"Please enter a number between 1 and {len(self.options)}")

    def get_selected_label(self, choice: int) -> str:
        """Get the label of the selected option."""
        if 1 <= choice <= len(self.options):
            return self.options[choice - 1].label
        return ""


class ProgressIndicator:
    """Step X of Y progress indicator.

    Example:
        progress = ProgressIndicator(total_steps=4)
        progress.advance("GitHub Setup")  # Shows: Step 1 of 4: GitHub Setup
        # ... do work ...
        progress.advance("Tracker Setup")  # Shows: Step 2 of 4: Tracker Setup
    """

    def __init__(self, total_steps: int):
        """Initialize progress indicator.

        Args:
            total_steps: Total number of steps in the wizard
        """
        self.total_steps = total_steps
        self.current_step = 0

    def advance(self, step_name: str) -> None:
        """Advance to the next step and display progress.

        Args:
            step_name: Name of the current step
        """
        self.current_step += 1
        click.echo()
        click.echo(f"Step {self.current_step} of {self.total_steps}: {step_name}")
        click.echo("-" * 40)

    def current(self) -> int:
        """Return the current step number."""
        return self.current_step

    def reset(self) -> None:
        """Reset progress to beginning."""
        self.current_step = 0


class Spinner:
    """Context manager that shows a spinner during long operations.

    Example:
        with Spinner("Fetching tickets from Linear"):
            tickets = api.list_tickets()
        # Prints: Fetching tickets from Linear... ✓

    Suppressed when stdout is not a TTY (piped output) or --quiet is set.
    """

    FRAMES = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]

    def __init__(self, message: str, quiet: bool = False):
        self.message = message
        self.quiet = quiet or not sys.stderr.isatty()
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None

    def __enter__(self) -> "Spinner":
        if self.quiet:
            return self
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._spin, daemon=True)
        self._thread.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=1)
        if not self.quiet:
            if exc_type is None:
                sys.stderr.write(f"\r{self.message}... ✓\n")
            else:
                sys.stderr.write(f"\r{self.message}... ✗\n")
            sys.stderr.flush()

    def _spin(self) -> None:
        i = 0
        while not self._stop_event.is_set():
            frame = self.FRAMES[i % len(self.FRAMES)]
            sys.stderr.write(f"\r{frame} {self.message}...")
            sys.stderr.flush()
            i += 1
            self._stop_event.wait(0.1)


class CommandSummary:
    """Collects and displays a post-command summary.

    Example:
        summary = CommandSummary()
        summary.add("Created", "3 tickets")
        summary.add("Skipped", "1 (already exists)")
        summary.show()
    """

    def __init__(self) -> None:
        self._items: list[tuple[str, str]] = []

    def add(self, label: str, value: str) -> None:
        """Add a summary item."""
        self._items.append((label, value))

    def show(self) -> None:
        """Display the summary."""
        if not self._items:
            return
        click.echo()
        max_label = max(len(label) for label, _ in self._items)
        for label, value in self._items:
            click.echo(f"  {label:<{max_label}}  {value}")


class SkillLevelSelector:
    """Beginner/Intermediate/Expert selection for adapting wizard behavior.

    Example:
        selector = SkillLevelSelector()
        skill = selector.show()  # Returns SkillLevel enum
    """

    def __init__(self, prompt_text: str | None = None):
        """Initialize selector.

        Args:
            prompt_text: Optional custom prompt text
        """
        self.prompt_text = prompt_text or "How experienced are you with this type of setup?"

    def show(self) -> SkillLevel:
        """Display skill level selector and get choice.

        Returns:
            Selected SkillLevel
        """
        menu = NumberedMenu(
            title=self.prompt_text,
            options=[
                ("Beginner", "Show detailed explanations and guidance"),
                ("Intermediate", "Show standard prompts (Recommended)"),
                ("Expert", "Minimal prompts, fastest setup"),
            ],
            default=2,
        )

        choice = menu.show()

        level_map = {
            1: SkillLevel.BEGINNER,
            2: SkillLevel.INTERMEDIATE,
            3: SkillLevel.EXPERT,
        }

        return level_map.get(choice, SkillLevel.INTERMEDIATE)


class ConfirmWithHelp:
    """Y/n confirmation with optional help text for beginners.

    Example:
        confirm = ConfirmWithHelp(
            message="Enable GitHub integration?",
            help_text="This allows automatic PR status updates.",
        )
        result = confirm.show(skill_level=SkillLevel.BEGINNER)  # Shows help
    """

    def __init__(
        self,
        message: str,
        help_text: str | None = None,
        default: bool = True,
    ):
        """Initialize confirmation.

        Args:
            message: Confirmation message
            help_text: Help text shown to beginners
            default: Default value (True for yes)
        """
        self.message = message
        self.help_text = help_text
        self.default = default

    def show(self, skill_level: SkillLevel = SkillLevel.INTERMEDIATE) -> bool:
        """Display confirmation and get response.

        Args:
            skill_level: User's skill level (affects help display)

        Returns:
            True if confirmed, False otherwise
        """
        # Show help text for beginners
        if skill_level == SkillLevel.BEGINNER and self.help_text:
            click.echo()
            click.echo(f"  Info: {self.help_text}")

        return bool(click.confirm(self.message, default=self.default))


@dataclass
class SelectOption:
    """A single option for MultiSelect."""

    label: str
    description: str
    selected: bool = False
    value: Any = None

    def __post_init__(self) -> None:
        if self.value is None:
            self.value = self.label


class MultiSelect:
    """Interactive multi-select with checkboxes.

    Example:
        multi = MultiSelect(
            title="Select actions to apply:",
            options=[
                ("Create config", "Create .vibe/config.json", True),
                ("Add labels", "Create GitHub labels", True),
                ("Add workflows", "Add GitHub Actions", False),
            ]
        )
        selected = multi.show()  # Returns list of selected indices (1-based)
    """

    def __init__(
        self,
        title: str,
        options: list[tuple[str, str, bool]],
    ):
        """Initialize multi-select.

        Args:
            title: Title/prompt
            options: List of (label, description, default_selected) tuples
        """
        self.title = title
        self.options = [
            SelectOption(label=opt[0], description=opt[1], selected=opt[2]) for opt in options
        ]

    def show(self) -> list[int]:
        """Display multi-select and get selections.

        Returns:
            List of 1-based indices of selected options
        """
        click.echo(self.title)
        click.echo()

        for i, opt in enumerate(self.options, 1):
            marker = "[x]" if opt.selected else "[ ]"
            click.echo(f"  {i}. {marker} {opt.label} - {opt.description}")

        click.echo()
        click.echo("Enter numbers to toggle (comma-separated), 'a' for all, 'n' for none,")
        click.echo("or press Enter to confirm current selection.")
        click.echo()

        while True:
            current = [i for i, opt in enumerate(self.options, 1) if opt.selected]
            prompt_text = f"Selected: {current if current else 'none'}"

            response = click.prompt(prompt_text, default="", show_default=False)

            if response == "":
                # Confirm current selection
                break
            elif response.lower() == "a":
                # Select all
                for opt in self.options:
                    opt.selected = True
            elif response.lower() == "n":
                # Select none
                for opt in self.options:
                    opt.selected = False
            else:
                # Toggle specific numbers
                try:
                    numbers = [int(n.strip()) for n in response.split(",")]
                    for num in numbers:
                        if 1 <= num <= len(self.options):
                            self.options[num - 1].selected = not self.options[num - 1].selected
                except ValueError:
                    click.echo("Invalid input. Enter numbers, 'a', or 'n'.")
                    continue

            # Show updated state
            click.echo()
            for i, opt in enumerate(self.options, 1):
                marker = "[x]" if opt.selected else "[ ]"
                click.echo(f"  {i}. {marker} {opt.label}")
            click.echo()

        return [i for i, opt in enumerate(self.options, 1) if opt.selected]

    def get_selected_labels(self) -> list[str]:
        """Get labels of all selected options."""
        return [opt.label for opt in self.options if opt.selected]


@dataclass
class WizardSuggestion:
    """A suggested next wizard with reason."""

    wizard_name: str
    reason: str
    priority: int = 0


class WhatNextFlow:
    """'What next?' menu after wizard completion.

    Suggests logical next steps based on completed wizard and config state.

    Example:
        what_next = WhatNextFlow("github", config)
        next_wizard = what_next.show()  # Returns wizard name or None
    """

    # Mapping of completed wizard -> suggested next wizards
    WIZARD_SUGGESTIONS: dict[str, list[tuple[str, str, int]]] = field(default_factory=lambda: {})

    def __init__(self, completed_wizard: str, config: dict[str, Any]):
        """Initialize flow.

        Args:
            completed_wizard: Name of the wizard that just completed
            config: Current configuration dict
        """
        self.completed_wizard = completed_wizard
        self.config = config

        # Define suggestions: wizard -> list of (next_wizard, reason, priority)
        self._suggestions: dict[str, list[tuple[str, str, int]]] = {
            "github": [
                ("tracker", "Set up ticket tracking", 1),
                ("database", "Configure database", 2),
            ],
            "tracker": [
                ("database", "Configure database", 1),
                ("vercel", "Deploy to Vercel", 2),
                ("fly", "Deploy to Fly.io", 2),
            ],
            "database": [
                ("vercel", "Deploy to Vercel (serverless)", 1),
                ("fly", "Deploy to Fly.io (containers)", 1),
                ("sentry", "Set up error monitoring", 2),
            ],
            "neon": [
                ("vercel", "Deploy to Vercel (works great with Neon)", 1),
                ("sentry", "Set up error monitoring", 2),
            ],
            "supabase": [
                ("vercel", "Deploy to Vercel", 1),
                ("sentry", "Set up error monitoring", 2),
            ],
            "vercel": [
                ("sentry", "Set up error monitoring", 1),
                ("playwright", "Add E2E testing", 2),
            ],
            "fly": [
                ("sentry", "Set up error monitoring", 1),
                ("playwright", "Add E2E testing", 2),
            ],
            "sentry": [
                ("playwright", "Add E2E testing", 1),
            ],
        }

    def get_suggestions(self) -> list[WizardSuggestion]:
        """Get available next wizard suggestions.

        Filters out already-configured wizards.

        Returns:
            List of WizardSuggestion objects
        """
        raw_suggestions = self._suggestions.get(self.completed_wizard, [])
        suggestions = []

        for wizard_name, reason, priority in raw_suggestions:
            if not self._is_configured(wizard_name):
                suggestions.append(
                    WizardSuggestion(
                        wizard_name=wizard_name,
                        reason=reason,
                        priority=priority,
                    )
                )

        # Sort by priority (lower = more important)
        suggestions.sort(key=lambda s: s.priority)
        return suggestions

    def _is_configured(self, wizard_name: str) -> bool:
        """Check if a wizard's integration is already configured."""
        checks = {
            "github": lambda: bool(self.config.get("github", {}).get("auth_method")),
            "tracker": lambda: self.config.get("tracker", {}).get("type") is not None,
            "database": lambda: bool(
                self.config.get("database", {}).get("provider")
                or self.config.get("database", {}).get("neon", {}).get("enabled")
                or self.config.get("database", {}).get("supabase", {}).get("enabled")
            ),
            "neon": lambda: bool(self.config.get("database", {}).get("neon", {}).get("enabled")),
            "supabase": lambda: bool(
                self.config.get("database", {}).get("supabase", {}).get("enabled")
            ),
            "vercel": lambda: bool(
                self.config.get("deployment", {}).get("vercel", {}).get("enabled")
            ),
            "fly": lambda: bool(self.config.get("deployment", {}).get("fly", {}).get("enabled")),
            "sentry": lambda: bool(
                self.config.get("observability", {}).get("sentry", {}).get("enabled")
            ),
            "playwright": lambda: bool(
                self.config.get("testing", {}).get("playwright", {}).get("enabled")
            ),
        }

        check_fn = checks.get(wizard_name)
        return check_fn() if check_fn else False

    def show(self) -> str | None:
        """Display 'what next' menu and get selection.

        Returns:
            Name of selected wizard, or None if user chooses to finish
        """
        suggestions = self.get_suggestions()

        if not suggestions:
            click.echo()
            click.echo("All recommended integrations are configured!")
            return None

        click.echo()
        click.echo("+" + "-" * 48 + "+")
        click.echo("|  What would you like to do next?               |")
        click.echo("+" + "-" * 48 + "+")
        click.echo()

        options = [(s.wizard_name.title(), s.reason) for s in suggestions]
        options.append(("Done", "Finish setup for now"))

        menu = NumberedMenu(
            title="Next steps:",
            options=options,
            default=len(options),  # Default to "Done"
        )

        choice = menu.show()

        if choice == len(options):
            return None

        return suggestions[choice - 1].wizard_name
