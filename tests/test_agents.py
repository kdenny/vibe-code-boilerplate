"""Tests for multi-assistant instruction generation."""

from lib.vibe.agents.generator import InstructionGenerator
from lib.vibe.agents.spec import (
    AssistantFormat,
    CommandSpec,
    InstructionSpec,
    WorkflowStep,
)


class TestAssistantFormat:
    """Tests for AssistantFormat enum."""

    def test_output_paths(self):
        """Test output path mapping."""
        assert AssistantFormat.CLAUDE.output_path == "CLAUDE.md"
        assert AssistantFormat.CURSOR.output_path == ".cursor/rules"
        assert AssistantFormat.COPILOT.output_path == ".github/copilot-instructions.md"

    def test_descriptions(self):
        """Test format descriptions."""
        assert "Claude" in AssistantFormat.CLAUDE.description
        assert "Cursor" in AssistantFormat.CURSOR.description
        assert "Copilot" in AssistantFormat.COPILOT.description


class TestInstructionSpec:
    """Tests for InstructionSpec dataclass."""

    def test_empty_spec(self):
        """Test empty spec initialization."""
        spec = InstructionSpec()
        assert spec.project_name == ""
        assert spec.core_rules == []
        assert spec.commands == []
        assert spec.workflows == {}

    def test_from_files(self, tmp_path):
        """Test loading spec from markdown files."""
        # Create CORE.md
        core_md = """# Core Instructions

## Project Overview

- **Name**: Test Project
- **Description**: A test project

## Tech Stack

- Backend: FastAPI
- Frontend: React

## Core Rules

- Read files before modifying
- Use existing patterns
- Keep changes minimal

## Anti-Patterns

- Guessing file contents
- Over-engineering
"""
        (tmp_path / "CORE.md").write_text(core_md)

        # Create COMMANDS.md
        commands_md = """# Commands

## Setup

### doctor
Check project health.
**Usage**: `bin/vibe doctor`
**Examples:**
- `bin/vibe doctor`
- `bin/vibe doctor --verbose`

## Tickets

### do
Start work on a ticket.
**Usage**: `bin/vibe do <ticket>`
**Examples:**
- `bin/vibe do PROJ-123`
"""
        (tmp_path / "COMMANDS.md").write_text(commands_md)

        # Load spec
        spec = InstructionSpec.from_files(tmp_path)

        assert spec.project_name == "Test Project"
        assert spec.project_description == "A test project"
        assert "Backend" in spec.tech_stack
        assert spec.tech_stack["Backend"] == "FastAPI"
        assert len(spec.core_rules) == 3
        assert "Read files before modifying" in spec.core_rules
        assert len(spec.anti_patterns) == 2

    def test_to_dict(self):
        """Test serialization to dict."""
        spec = InstructionSpec(
            project_name="Test",
            core_rules=["Rule 1", "Rule 2"],
            commands=[
                CommandSpec(
                    name="test",
                    description="Test command",
                    usage="bin/test",
                )
            ],
        )

        data = spec.to_dict()
        assert data["project_name"] == "Test"
        assert len(data["core_rules"]) == 2
        assert len(data["commands"]) == 1
        assert data["commands"][0]["name"] == "test"


class TestInstructionGenerator:
    """Tests for InstructionGenerator."""

    def setup_method(self):
        """Set up test spec."""
        self.spec = InstructionSpec(
            project_name="Test Project",
            project_description="A test project for testing",
            tech_stack={"Backend": "Python", "Frontend": "React"},
            core_rules=[
                "Read files before modifying",
                "Use existing patterns",
            ],
            commands=[
                CommandSpec(
                    name="doctor",
                    description="Check health",
                    usage="bin/vibe doctor",
                    examples=["bin/vibe doctor", "bin/vibe doctor --verbose"],
                ),
                CommandSpec(
                    name="do",
                    description="Start ticket work",
                    usage="bin/vibe do <ticket>",
                ),
            ],
            workflows={
                "Start Work": [
                    WorkflowStep(
                        title="Create Worktree",
                        description="Create workspace",
                        commands=["bin/vibe do PROJ-123"],
                    ),
                    WorkflowStep(
                        title="Implement",
                        description="Make changes",
                        commands=[],
                    ),
                ]
            },
            anti_patterns=["Guessing file contents", "Over-engineering"],
        )
        self.generator = InstructionGenerator(self.spec)

    def test_generate_claude(self):
        """Test Claude format generation."""
        content = self.generator.generate(AssistantFormat.CLAUDE)

        assert "CLAUDE.md" in content
        assert "Test Project" in content
        assert "Read files before modifying" in content
        assert "bin/vibe doctor" in content
        assert "Guessing file contents" in content

    def test_generate_cursor(self):
        """Test Cursor format generation."""
        content = self.generator.generate(AssistantFormat.CURSOR)

        assert "Cursor" in content
        assert "Test Project" in content
        assert "Read files before modifying" in content
        assert "bin/vibe doctor" in content

    def test_generate_copilot(self):
        """Test Copilot format generation."""
        content = self.generator.generate(AssistantFormat.COPILOT)

        assert "Copilot" in content
        assert "Test Project" in content
        assert "Coding Guidelines" in content
        assert "Read files before modifying" in content

    def test_generate_generic(self):
        """Test generic AGENTS.md format generation."""
        content = self.generator.generate(AssistantFormat.GENERIC)

        assert "AGENTS.md" in content
        assert "Test Project" in content
        assert "Read files before modifying" in content

    def test_generate_all(self, tmp_path):
        """Test generating all formats to directory."""
        formats = [AssistantFormat.CLAUDE, AssistantFormat.CURSOR]
        results = self.generator.generate_all(tmp_path, formats)

        assert "claude" in results
        assert "cursor" in results

        # Verify files exist
        assert (tmp_path / "CLAUDE.md").exists()
        assert (tmp_path / ".cursor" / "rules").exists()

        # Verify content
        claude_content = (tmp_path / "CLAUDE.md").read_text()
        assert "Test Project" in claude_content

    def test_header_includes_timestamp(self):
        """Test that generated files include timestamp."""
        content = self.generator.generate(AssistantFormat.CLAUDE)
        assert "Generated:" in content
        assert "DO NOT EDIT DIRECTLY" in content


class TestCommandSpec:
    """Tests for CommandSpec dataclass."""

    def test_command_spec(self):
        """Test CommandSpec creation."""
        cmd = CommandSpec(
            name="test",
            description="Test command",
            usage="bin/test arg",
            examples=["bin/test foo", "bin/test bar"],
            category="testing",
        )
        assert cmd.name == "test"
        assert cmd.category == "testing"
        assert len(cmd.examples) == 2


class TestWorkflowStep:
    """Tests for WorkflowStep dataclass."""

    def test_workflow_step(self):
        """Test WorkflowStep creation."""
        step = WorkflowStep(
            title="Create PR",
            description="Open a pull request",
            commands=["git push", "gh pr create"],
        )
        assert step.title == "Create PR"
        assert len(step.commands) == 2
