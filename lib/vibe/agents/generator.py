"""Generator for assistant-specific instruction files."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from lib.vibe.agents.spec import AssistantFormat, InstructionSpec


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
        self, output_dir: Path, formats: list[AssistantFormat] | None = None
    ) -> dict[str, Path]:
        """Generate all instruction files to the specified directory.

        Returns a dict mapping format name to output path.
        """
        if formats is None:
            formats = [
                AssistantFormat.CLAUDE,
                AssistantFormat.CURSOR,
                AssistantFormat.COPILOT,
            ]

        results = {}
        for format in formats:
            content = self.generate(format)
            output_path = output_dir / format.output_path

            # Create parent directories if needed
            output_path.parent.mkdir(parents=True, exist_ok=True)

            output_path.write_text(content)
            results[format.value] = output_path

        return results

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

        # Commands
        if self.spec.commands:
            lines.append("## Available Commands")
            lines.append("")
            lines.append("| Command | Description |")
            lines.append("|---------|-------------|")
            for cmd in self.spec.commands:
                lines.append(f"| `{cmd.usage or cmd.name}` | {cmd.description} |")
            lines.append("")

            # Detailed command reference
            lines.append("### Command Details")
            lines.append("")
            for cmd in self.spec.commands:
                lines.append(f"#### {cmd.name}")
                lines.append("")
                lines.append(cmd.description)
                if cmd.usage:
                    lines.append("")
                    lines.append(f"**Usage:** `{cmd.usage}`")
                if cmd.examples:
                    lines.append("")
                    lines.append("**Examples:**")
                    for ex in cmd.examples:
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
                        for cmd in step.commands:
                            lines.append(cmd)
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
            for cmd in self.spec.commands:
                lines.append(f"# {cmd.name}: {cmd.usage or cmd.description}")
            lines.append("")

        # Workflows - condensed
        if self.spec.workflows:
            lines.append("# Workflows")
            for workflow_name, steps in self.spec.workflows.items():
                lines.append(f"# {workflow_name}:")
                for step in steps:
                    if step.commands:
                        for cmd in step.commands:
                            lines.append(f"#   {cmd}")
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
            for cmd in self.spec.commands:
                if cmd.usage:
                    lines.append(f"- `{cmd.usage}` - {cmd.description}")
                else:
                    lines.append(f"- **{cmd.name}**: {cmd.description}")
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

        # Commands
        if self.spec.commands:
            lines.append("## Commands")
            lines.append("")
            lines.append("Use these commands:")
            lines.append("")
            lines.append("```")
            for cmd in self.spec.commands:
                if cmd.usage:
                    lines.append(f"{cmd.usage}  # {cmd.description}")
                else:
                    lines.append(f"{cmd.name}: {cmd.description}")
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
                        for cmd in step.commands:
                            lines.append(f"   {cmd}")
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
