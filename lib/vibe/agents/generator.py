"""Generator for assistant-specific instruction files."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from lib.vibe.agents.spec import AssistantFormat, InstructionSpec

# Placeholder patterns that indicate an uncustomized template file.
# These should ONLY be patterns that disappear once a user fills in real
# project details.  Header lines like "# Generated:" or "# DO NOT EDIT
# DIRECTLY" persist in every generated file (even customised ones) and
# must NOT be listed here – otherwise _is_generated_file() always
# returns True and customised files get overwritten.
_PLACEHOLDER_PATTERNS = [
    "(your project name)",
    "(what this project does)",
]


def _is_generated_file(content: str) -> bool:
    """Check if file content appears to be generated (not customized)."""
    return any(pattern in content for pattern in _PLACEHOLDER_PATTERNS)


def _has_project_content(file_path: Path) -> bool:
    """Check if file exists and has project-specific (non-template) content."""
    if not file_path.exists():
        return False

    try:
        content = file_path.read_text()
        # If it's empty or has placeholder patterns, it's not project-specific
        if not content.strip():
            return False
        return not _is_generated_file(content)
    except OSError:
        return False


def _render_labels_section(labels: dict[str, list[str]]) -> list[str]:
    """Render the Available Labels section from config labels.

    Returns a list of lines (without trailing newline) for embedding into
    the generated output.
    """
    lines: list[str] = []
    lines.append("## Available Labels")
    lines.append("")
    lines.append(
        "These labels are configured in `.vibe/config.json`. Apply them when creating tickets."
    )
    lines.append("")

    category_titles = {
        "type": "Type (exactly one required)",
        "risk": "Risk (exactly one required)",
        "area": "Area (at least one required)",
        "special": "Special (as needed)",
    }

    for category in ("type", "risk", "area", "special"):
        values = labels.get(category, [])
        if values:
            title = category_titles.get(category, category.title())
            lines.append(f"**{title}:** {', '.join(values)}")
            lines.append("")

    return lines


def _render_ticket_discipline_section() -> list[str]:
    """Render the Ticket Discipline section with enforcement rules.

    Returns a list of lines for embedding into generated output.
    """
    lines: list[str] = []
    lines.append("## Ticket Discipline")
    lines.append("")
    lines.append("Follow these rules for every ticket and PR:")
    lines.append("")
    lines.append("### Labels Are Required")
    lines.append("")
    lines.append("Every ticket **must** have labels when created:")
    lines.append("")
    lines.append("- **Type** (exactly one): Bug, Feature, Chore, or Refactor")
    lines.append("- **Area** (at least one): Frontend, Backend, Infra, or Docs")
    lines.append("- **Risk** (exactly one): Low Risk, Medium Risk, or High Risk")
    lines.append("")
    lines.append("```bash")
    lines.append(
        'bin/ticket create "Fix login bug" '
        '--description "Login returns 500 on special chars." '
        '--label Bug --label Frontend --label "Low Risk"'
    )
    lines.append("```")
    lines.append("")
    lines.append("### Parent/Child Relationships")
    lines.append("")
    lines.append("When creating sub-tasks, set the parent ticket:")
    lines.append("")
    lines.append("```bash")
    lines.append(
        'bin/ticket create "Add signup form" '
        '--description "React signup component." '
        "--label Feature --label Frontend --parent PROJ-100"
    )
    lines.append("```")
    lines.append("")
    lines.append("### Blocking Relationships")
    lines.append("")
    lines.append(
        "When one ticket must be completed before another can start, "
        "link them with a blocking relationship. "
        "The prerequisite ticket blocks the dependent ticket:"
    )
    lines.append("")
    lines.append("```bash")
    lines.append("bin/ticket link PROJ-101 --blocks PROJ-102")
    lines.append("```")
    lines.append("")
    lines.append("### Every PR Needs a Ticket")
    lines.append("")
    lines.append(
        "Every pull request **must** reference a ticket. Include the ticket ID in the PR title:"
    )
    lines.append("")
    lines.append("```bash")
    lines.append('bin/vibe pr --title "PROJ-123: Add user authentication"')
    lines.append("```")
    lines.append("")
    return lines


class InstructionGenerator:
    """Generates assistant-specific instruction files from a common spec."""

    def __init__(self, spec: InstructionSpec):
        """Initialize generator with instruction spec."""
        self.spec = spec

    def generate(self, format: AssistantFormat) -> str:
        """Generate instructions for the specified format."""
        generators = {
            AssistantFormat.CLAUDE: self._generate_claude,
            AssistantFormat.CURSOR: self._generate_cursor,
            AssistantFormat.COPILOT: self._generate_copilot,
            AssistantFormat.CODEX: self._generate_codex,
            AssistantFormat.GENERIC: self._generate_generic,
        }
        return generators[format]()

    def generate_all(
        self,
        output_dir: Path,
        formats: list[AssistantFormat] | None = None,
        force: bool = False,
    ) -> dict[str, Path]:
        """Generate all instruction files to the specified directory.

        Args:
            output_dir: Directory to write files to
            formats: List of formats to generate (default: CLAUDE, CURSOR, COPILOT)
            force: If True, overwrite files even if they have project-specific content

        Returns:
            Dict mapping format name to output path (only for files that were written)
        """
        if formats is None:
            formats = [
                AssistantFormat.CLAUDE,
                AssistantFormat.CURSOR,
                AssistantFormat.COPILOT,
            ]

        results: dict[str, Path] = {}
        skipped: dict[str, Path | str] = {}

        for format in formats:
            output_path = output_dir / format.output_path

            # Check if path is a directory (shouldn't be, but handle gracefully)
            if output_path.exists() and output_path.is_dir():
                # For .cursor/rules being a directory, use .cursorrules instead
                if format == AssistantFormat.CURSOR:
                    output_path = output_dir / ".cursorrules"
                else:
                    skipped[format.value] = f"{output_path} is a directory"
                    continue

            # Skip files with project-specific content unless --force
            if not force and _has_project_content(output_path):
                skipped[format.value] = output_path
                continue

            content = self.generate(format)

            # Create parent directories if needed
            output_path.parent.mkdir(parents=True, exist_ok=True)

            output_path.write_text(content)
            results[format.value] = output_path

        # Store skipped info for caller to report
        self._skipped = skipped

        return results

    @property
    def skipped_files(self) -> dict[str, Path | str]:
        """Return files that were skipped due to project-specific content."""
        return getattr(self, "_skipped", {})

    def _header(self, format_name: str) -> str:
        """Generate file header with timestamp."""
        timestamp = datetime.now().strftime("%Y-%m-%d")
        return f"""# AI Agent Instructions
# Format: {format_name}
# Generated: {timestamp}
# Source: agent_instructions/
#
# DO NOT EDIT DIRECTLY - regenerate with: bin/vibe generate-agent-instructions
"""

    def _generate_claude(self) -> str:
        """Generate CLAUDE.md format."""
        lines = [self._header("Claude Code")]
        lines.append("")
        lines.append("# CLAUDE.md - AI Agent Instructions")
        lines.append("")

        # Project overview
        if self.spec.project_name or self.spec.project_description:
            lines.append("## Project Overview")
            lines.append("")
            if self.spec.project_name:
                lines.append(f"**Project:** {self.spec.project_name}")
            if self.spec.project_description:
                lines.append(f"**Description:** {self.spec.project_description}")
            if self.spec.tech_stack:
                lines.append("")
                lines.append("**Tech Stack:**")
                for key, value in self.spec.tech_stack.items():
                    lines.append(f"- {key}: {value}")
            lines.append("")
            lines.append("---")
            lines.append("")

        # Core rules
        if self.spec.core_rules:
            lines.append("## Core Rules")
            lines.append("")
            for rule in self.spec.core_rules:
                lines.append(f"- {rule}")
            lines.append("")
            lines.append("---")
            lines.append("")

        # Available Labels (from config)
        if self.spec.labels:
            lines.extend(_render_labels_section(self.spec.labels))
            lines.append("---")
            lines.append("")

        # Ticket Discipline
        if self.spec.labels or self.spec.core_rules:
            lines.extend(_render_ticket_discipline_section())
            lines.append("---")
            lines.append("")

        # Commands
        if self.spec.commands:
            lines.append("## Available Commands")
            lines.append("")
            lines.append("| Command | Description |")
            lines.append("|---------|-------------|")
            for cmd_spec in self.spec.commands:
                lines.append(f"| `{cmd_spec.usage or cmd_spec.name}` | {cmd_spec.description} |")
            lines.append("")

            # Detailed command reference
            lines.append("### Command Details")
            lines.append("")
            for cmd_spec in self.spec.commands:
                lines.append(f"#### {cmd_spec.name}")
                lines.append("")
                lines.append(cmd_spec.description)
                if cmd_spec.usage:
                    lines.append("")
                    lines.append(f"**Usage:** `{cmd_spec.usage}`")
                if cmd_spec.examples:
                    lines.append("")
                    lines.append("**Examples:**")
                    for ex in cmd_spec.examples:
                        lines.append("```bash")
                        lines.append(ex)
                        lines.append("```")
                lines.append("")
            lines.append("---")
            lines.append("")

        # Workflows
        if self.spec.workflows:
            lines.append("## Workflows")
            lines.append("")
            for workflow_name, steps in self.spec.workflows.items():
                lines.append(f"### {workflow_name}")
                lines.append("")
                for i, step in enumerate(steps, 1):
                    lines.append(f"**Step {i}: {step.title}**")
                    if step.description:
                        lines.append(step.description)
                    if step.commands:
                        lines.append("")
                        lines.append("```bash")
                        for step_cmd in step.commands:
                            lines.append(step_cmd)
                        lines.append("```")
                    lines.append("")
            lines.append("---")
            lines.append("")

        # Anti-patterns
        if self.spec.anti_patterns:
            lines.append("## Anti-Patterns to Avoid")
            lines.append("")
            for pattern in self.spec.anti_patterns:
                lines.append(f"- **Don't:** {pattern}")
            lines.append("")
            lines.append("---")
            lines.append("")

        # Important files
        if self.spec.important_files:
            lines.append("## Important Files")
            lines.append("")
            for file_path in self.spec.important_files:
                lines.append(f"- `{file_path}`")
            lines.append("")

        # Custom sections
        for section_name, content in self.spec.custom_sections.items():
            lines.append(f"## {section_name}")
            lines.append("")
            lines.append(content)
            lines.append("")

        return "\n".join(lines)

    def _generate_cursor(self) -> str:
        """Generate .cursor/rules format.

        Cursor uses a more concise format focused on rules.
        """
        lines = [self._header("Cursor IDE")]
        lines.append("")

        # Project context (brief)
        if self.spec.project_name:
            lines.append(f"# Project: {self.spec.project_name}")
        if self.spec.project_description:
            lines.append(f"# {self.spec.project_description}")
        lines.append("")

        # Tech stack as context
        if self.spec.tech_stack:
            lines.append("# Tech Stack")
            for key, value in self.spec.tech_stack.items():
                lines.append(f"# - {key}: {value}")
            lines.append("")

        # Core rules - Cursor format prefers direct statements
        if self.spec.core_rules:
            lines.append("# Rules")
            lines.append("")
            for rule in self.spec.core_rules:
                lines.append(f"{rule}")
            lines.append("")

        # Available Labels (from config)
        if self.spec.labels:
            lines.append("# Available Labels")
            for category in ("type", "risk", "area", "special"):
                values = self.spec.labels.get(category, [])
                if values:
                    lines.append(f"# {category.title()}: {', '.join(values)}")
            lines.append("")

        # Ticket Discipline (concise for Cursor)
        if self.spec.labels or self.spec.core_rules:
            lines.append("# Ticket Discipline")
            lines.append(
                "Every ticket must have type and area labels. "
                "Every PR title must include the ticket ID. "
                "Use --parent for sub-tasks and bin/ticket link for blocking."
            )
            lines.append("")

        # Anti-patterns
        if self.spec.anti_patterns:
            lines.append("# Avoid")
            lines.append("")
            for pattern in self.spec.anti_patterns:
                lines.append(f"Do not: {pattern}")
            lines.append("")

        # Commands - brief reference
        if self.spec.commands:
            lines.append("# Available Commands")
            lines.append("")
            for cmd_spec in self.spec.commands:
                lines.append(f"# {cmd_spec.name}: {cmd_spec.usage or cmd_spec.description}")
            lines.append("")

        # Workflows - condensed
        if self.spec.workflows:
            lines.append("# Workflows")
            for workflow_name, steps in self.spec.workflows.items():
                lines.append(f"# {workflow_name}:")
                for step in steps:
                    if step.commands:
                        for step_cmd in step.commands:
                            lines.append(f"#   {step_cmd}")
            lines.append("")

        return "\n".join(lines)

    def _generate_copilot(self) -> str:
        """Generate .github/copilot-instructions.md format.

        GitHub Copilot uses markdown with specific conventions.
        """
        lines = [self._header("GitHub Copilot")]
        lines.append("")
        lines.append("# Copilot Instructions")
        lines.append("")

        # Project context
        if self.spec.project_name or self.spec.project_description:
            lines.append("## About This Project")
            lines.append("")
            if self.spec.project_name:
                lines.append(f"This is **{self.spec.project_name}**.")
            if self.spec.project_description:
                lines.append(self.spec.project_description)
            lines.append("")

        # Tech stack
        if self.spec.tech_stack:
            lines.append("## Technology Stack")
            lines.append("")
            for key, value in self.spec.tech_stack.items():
                lines.append(f"- **{key}**: {value}")
            lines.append("")

        # Guidelines (Copilot's term for rules)
        if self.spec.core_rules:
            lines.append("## Coding Guidelines")
            lines.append("")
            lines.append("Follow these guidelines when generating code:")
            lines.append("")
            for rule in self.spec.core_rules:
                lines.append(f"- {rule}")
            lines.append("")

        # Available Labels (from config)
        if self.spec.labels:
            lines.extend(_render_labels_section(self.spec.labels))

        # Ticket Discipline
        if self.spec.labels or self.spec.core_rules:
            lines.extend(_render_ticket_discipline_section())

        # What to avoid
        if self.spec.anti_patterns:
            lines.append("## Patterns to Avoid")
            lines.append("")
            for pattern in self.spec.anti_patterns:
                lines.append(f"- {pattern}")
            lines.append("")

        # Project structure / important files
        if self.spec.important_files:
            lines.append("## Key Files")
            lines.append("")
            for file_path in self.spec.important_files:
                lines.append(f"- `{file_path}`")
            lines.append("")

        # CLI commands reference
        if self.spec.commands:
            lines.append("## CLI Commands")
            lines.append("")
            lines.append("Use these commands for common operations:")
            lines.append("")
            for cmd_spec in self.spec.commands:
                if cmd_spec.usage:
                    lines.append(f"- `{cmd_spec.usage}` - {cmd_spec.description}")
                else:
                    lines.append(f"- **{cmd_spec.name}**: {cmd_spec.description}")
            lines.append("")

        return "\n".join(lines)

    def _generate_codex(self) -> str:
        """Generate AGENTS.md format for OpenAI Codex/ChatGPT."""
        # Similar to Claude but with different conventions
        return self._generate_generic()

    def _generate_generic(self) -> str:
        """Generate generic AGENTS.md format."""
        lines = [self._header("Generic AI Assistant")]
        lines.append("")
        lines.append("# AGENTS.md - AI Agent Instructions")
        lines.append("")
        lines.append(
            "This file provides instructions for AI coding assistants working on this project."
        )
        lines.append("")

        # Project overview
        if self.spec.project_name or self.spec.project_description:
            lines.append("## Project")
            lines.append("")
            if self.spec.project_name:
                lines.append(f"**Name:** {self.spec.project_name}")
            if self.spec.project_description:
                lines.append(f"**Description:** {self.spec.project_description}")
            lines.append("")

        # Tech stack
        if self.spec.tech_stack:
            lines.append("## Tech Stack")
            lines.append("")
            for key, value in self.spec.tech_stack.items():
                lines.append(f"- {key}: {value}")
            lines.append("")

        # Rules
        if self.spec.core_rules:
            lines.append("## Rules")
            lines.append("")
            lines.append("You MUST follow these rules:")
            lines.append("")
            for i, rule in enumerate(self.spec.core_rules, 1):
                lines.append(f"{i}. {rule}")
            lines.append("")

        # Available Labels (from config)
        if self.spec.labels:
            lines.extend(_render_labels_section(self.spec.labels))

        # Ticket Discipline
        if self.spec.labels or self.spec.core_rules:
            lines.extend(_render_ticket_discipline_section())

        # Commands
        if self.spec.commands:
            lines.append("## Commands")
            lines.append("")
            lines.append("Use these commands:")
            lines.append("")
            lines.append("```")
            for cmd_spec in self.spec.commands:
                if cmd_spec.usage:
                    lines.append(f"{cmd_spec.usage}  # {cmd_spec.description}")
                else:
                    lines.append(f"{cmd_spec.name}: {cmd_spec.description}")
            lines.append("```")
            lines.append("")

        # Workflows
        if self.spec.workflows:
            lines.append("## Workflows")
            lines.append("")
            for workflow_name, steps in self.spec.workflows.items():
                lines.append(f"### {workflow_name}")
                lines.append("")
                for i, step in enumerate(steps, 1):
                    lines.append(f"{i}. **{step.title}**")
                    if step.description:
                        lines.append(f"   {step.description}")
                    if step.commands:
                        lines.append("   ```")
                        for step_cmd in step.commands:
                            lines.append(f"   {step_cmd}")
                        lines.append("   ```")
                lines.append("")

        # Anti-patterns
        if self.spec.anti_patterns:
            lines.append("## Avoid")
            lines.append("")
            for pattern in self.spec.anti_patterns:
                lines.append(f"- DO NOT: {pattern}")
            lines.append("")

        return "\n".join(lines)
