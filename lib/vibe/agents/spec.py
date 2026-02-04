"""Instruction specification models for multi-assistant support."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any


class AssistantFormat(Enum):
    """Supported AI assistant formats."""

    CLAUDE = "claude"  # CLAUDE.md (Claude Code)
    CURSOR = "cursor"  # .cursor/rules or .cursorrules
    COPILOT = "copilot"  # .github/copilot-instructions.md
    CODEX = "codex"  # AGENTS.md
    GENERIC = "generic"  # Generic AGENTS.md format

    @property
    def output_path(self) -> str:
        """Get the default output path for this format."""
        paths = {
            AssistantFormat.CLAUDE: "CLAUDE.md",
            AssistantFormat.CURSOR: ".cursor/rules",
            AssistantFormat.COPILOT: ".github/copilot-instructions.md",
            AssistantFormat.CODEX: "AGENTS.md",
            AssistantFormat.GENERIC: "AGENTS.md",
        }
        return paths[self]

    @property
    def description(self) -> str:
        """Human-readable description of this format."""
        descriptions = {
            AssistantFormat.CLAUDE: "Claude Code (Anthropic)",
            AssistantFormat.CURSOR: "Cursor IDE",
            AssistantFormat.COPILOT: "GitHub Copilot",
            AssistantFormat.CODEX: "OpenAI Codex",
            AssistantFormat.GENERIC: "Generic AI Assistant",
        }
        return descriptions[self]


@dataclass
class CommandSpec:
    """Specification for a command available to agents."""

    name: str
    description: str
    usage: str
    examples: list[str] = field(default_factory=list)
    category: str = "general"


@dataclass
class WorkflowStep:
    """A step in a workflow."""

    title: str
    description: str
    commands: list[str] = field(default_factory=list)


@dataclass
class InstructionSpec:
    """Core instruction specification that gets transformed into assistant-specific formats.

    This is the single source of truth for agent instructions.
    """

    # Project context
    project_name: str = ""
    project_description: str = ""
    tech_stack: dict[str, str] = field(default_factory=dict)

    # Core rules (must follow)
    core_rules: list[str] = field(default_factory=list)

    # Available commands
    commands: list[CommandSpec] = field(default_factory=list)

    # Workflows
    workflows: dict[str, list[WorkflowStep]] = field(default_factory=dict)

    # File patterns to watch
    important_files: list[str] = field(default_factory=list)

    # Anti-patterns to avoid
    anti_patterns: list[str] = field(default_factory=list)

    # Custom sections (format-specific additions)
    custom_sections: dict[str, str] = field(default_factory=dict)

    @classmethod
    def from_files(cls, instructions_dir: Path) -> InstructionSpec:
        """Load instruction spec from markdown files in a directory.

        Expected files:
        - CORE.md - Core rules and context
        - COMMANDS.md - Available commands
        - WORKFLOW.md - Workflow definitions
        """
        spec = cls()

        # Load CORE.md
        core_path = instructions_dir / "CORE.md"
        if core_path.exists():
            spec._parse_core(core_path.read_text())

        # Load COMMANDS.md
        commands_path = instructions_dir / "COMMANDS.md"
        if commands_path.exists():
            spec._parse_commands(commands_path.read_text())

        # Load WORKFLOW.md
        workflow_path = instructions_dir / "WORKFLOW.md"
        if workflow_path.exists():
            spec._parse_workflow(workflow_path.read_text())

        return spec

    def _parse_core(self, content: str) -> None:
        """Parse CORE.md content."""
        lines = content.split("\n")
        current_section = None
        section_content: list[str] = []

        for line in lines:
            # Handle both # and ## as section headers
            if line.startswith("## "):
                if current_section and section_content:
                    self._process_core_section(current_section, section_content)
                current_section = line[3:].strip()
                section_content = []
            elif line.startswith("# ") and not line.startswith("## "):
                # Top-level header - skip but reset section
                if current_section and section_content:
                    self._process_core_section(current_section, section_content)
                current_section = None
                section_content = []
            elif current_section:
                section_content.append(line)

        if current_section and section_content:
            self._process_core_section(current_section, section_content)

    def _process_core_section(self, section: str, content: list[str]) -> None:
        """Process a section from CORE.md."""
        text = "\n".join(content).strip()
        section_lower = section.lower()

        if "project" in section_lower:
            # Extract project info
            for line in content:
                if line.startswith("- **Name**:"):
                    self.project_name = line.split(":", 1)[1].strip()
                elif line.startswith("- **Description**:"):
                    self.project_description = line.split(":", 1)[1].strip()
        elif "tech stack" in section_lower:
            for line in content:
                if line.startswith("- "):
                    parts = line[2:].split(":", 1)
                    if len(parts) == 2:
                        self.tech_stack[parts[0].strip()] = parts[1].strip()
        elif "rules" in section_lower or "must" in section_lower:
            for line in content:
                if line.startswith("- ") or line.startswith("* "):
                    rule = line[2:].strip()
                    if rule:
                        self.core_rules.append(rule)
        elif "anti-pattern" in section_lower or "avoid" in section_lower:
            for line in content:
                if line.startswith("- ") or line.startswith("* "):
                    pattern = line[2:].strip()
                    if pattern:
                        self.anti_patterns.append(pattern)
        elif "important files" in section_lower:
            for line in content:
                if line.startswith("- ") or line.startswith("* "):
                    file_path = line[2:].strip()
                    if file_path:
                        self.important_files.append(file_path)
        else:
            # Store as custom section
            self.custom_sections[section] = text

    def _parse_commands(self, content: str) -> None:
        """Parse COMMANDS.md content."""
        lines = content.split("\n")
        current_command = None
        current_category = "general"

        i = 0
        while i < len(lines):
            line = lines[i]

            # Category header
            if line.startswith("## "):
                current_category = line[3:].strip().lower()

            # Command definition
            elif line.startswith("### "):
                if current_command:
                    self.commands.append(current_command)

                name = line[4:].strip()
                description = ""
                usage = ""
                examples: list[str] = []

                # Look for description and usage in following lines
                i += 1
                while i < len(lines) and not lines[i].startswith("### "):
                    subline = lines[i]
                    if subline.startswith("**Usage**:"):
                        usage = subline.split(":", 1)[1].strip().strip("`")
                    elif subline.startswith("**Examples**:"):
                        # Collect examples
                        i += 1
                        while i < len(lines) and lines[i].startswith("- "):
                            examples.append(lines[i][2:].strip().strip("`"))
                            i += 1
                        i -= 1  # Back up since we'll increment at loop end
                    elif subline and not subline.startswith("**"):
                        if not description:
                            description = subline.strip()
                    i += 1
                i -= 1  # Back up since outer loop increments

                current_command = CommandSpec(
                    name=name,
                    description=description,
                    usage=usage,
                    examples=examples,
                    category=current_category,
                )

            i += 1

        if current_command:
            self.commands.append(current_command)

    def _parse_workflow(self, content: str) -> None:
        """Parse WORKFLOW.md content."""
        lines = content.split("\n")
        current_workflow = None
        current_steps: list[WorkflowStep] = []

        i = 0
        while i < len(lines):
            line = lines[i]

            # Workflow header
            if line.startswith("## "):
                if current_workflow and current_steps:
                    self.workflows[current_workflow] = current_steps
                current_workflow = line[3:].strip()
                current_steps = []

            # Step
            elif line.startswith("### "):
                step_title = line[4:].strip()
                step_description = ""
                step_commands: list[str] = []

                # Collect step content
                i += 1
                while (
                    i < len(lines)
                    and not lines[i].startswith("## ")
                    and not lines[i].startswith("### ")
                ):
                    subline = lines[i]
                    if subline.startswith("```"):
                        # Code block - collect commands
                        i += 1
                        while i < len(lines) and not lines[i].startswith("```"):
                            cmd = lines[i].strip()
                            if cmd and not cmd.startswith("#"):
                                step_commands.append(cmd)
                            i += 1
                    elif subline and not step_description:
                        step_description = subline.strip()
                    i += 1
                i -= 1

                current_steps.append(
                    WorkflowStep(
                        title=step_title,
                        description=step_description,
                        commands=step_commands,
                    )
                )

            i += 1

        if current_workflow and current_steps:
            self.workflows[current_workflow] = current_steps

    def to_dict(self) -> dict[str, Any]:
        """Convert spec to dictionary for serialization."""
        return {
            "project_name": self.project_name,
            "project_description": self.project_description,
            "tech_stack": self.tech_stack,
            "core_rules": self.core_rules,
            "commands": [
                {
                    "name": c.name,
                    "description": c.description,
                    "usage": c.usage,
                    "examples": c.examples,
                    "category": c.category,
                }
                for c in self.commands
            ],
            "workflows": {
                name: [
                    {"title": s.title, "description": s.description, "commands": s.commands}
                    for s in steps
                ]
                for name, steps in self.workflows.items()
            },
            "important_files": self.important_files,
            "anti_patterns": self.anti_patterns,
        }
