"""Tests for multi-assistant instruction generation."""

from lib.vibe.agents.generator import InstructionGenerator
from lib.vibe.agents.spec import (
    AssistantFormat,
    CommandSpec,
    InstructionSpec,
    WorkflowStep,
)

SAMPLE_LABELS = {
    "type": ["Bug", "Feature", "Chore", "Refactor"],
    "risk": ["Low Risk", "Medium Risk", "High Risk"],
    "area": ["Frontend", "Backend", "Infra", "Docs"],
    "special": ["HUMAN", "Milestone", "Blocked"],
}


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
        assert spec.labels == {}

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

    def test_from_files_with_labels(self, tmp_path):
        """Test loading spec from files with config labels."""
        core_md = """# Core Instructions

## Core Rules

- Read files before modifying
"""
        (tmp_path / "CORE.md").write_text(core_md)

        spec = InstructionSpec.from_files(tmp_path, config_labels=SAMPLE_LABELS)

        assert spec.labels == SAMPLE_LABELS
        assert "Bug" in spec.labels["type"]
        assert "Frontend" in spec.labels["area"]

    def test_from_files_without_labels(self, tmp_path):
        """Test loading spec from files without config labels."""
        core_md = """# Core Instructions

## Core Rules

- Read files before modifying
"""
        (tmp_path / "CORE.md").write_text(core_md)

        spec = InstructionSpec.from_files(tmp_path)

        assert spec.labels == {}

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
            labels=SAMPLE_LABELS,
        )

        data = spec.to_dict()
        assert data["project_name"] == "Test"
        assert len(data["core_rules"]) == 2
        assert len(data["commands"]) == 1
        assert data["commands"][0]["name"] == "test"
        assert data["labels"] == SAMPLE_LABELS


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
            labels=SAMPLE_LABELS,
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

    def test_generate_claude_includes_labels(self):
        """Test Claude format includes Available Labels section."""
        content = self.generator.generate(AssistantFormat.CLAUDE)

        assert "## Available Labels" in content
        assert "Bug, Feature, Chore, Refactor" in content
        assert "Low Risk, Medium Risk, High Risk" in content
        assert "Frontend, Backend, Infra, Docs" in content
        assert "HUMAN, Milestone, Blocked" in content

    def test_generate_claude_includes_ticket_discipline(self):
        """Test Claude format includes Ticket Discipline section."""
        content = self.generator.generate(AssistantFormat.CLAUDE)

        assert "## Ticket Discipline" in content
        assert "### Labels Are Required" in content
        assert "### Parent/Child Relationships" in content
        assert "### Blocking Relationships" in content
        assert "### Every PR Needs a Ticket" in content
        assert "--parent PROJ-100" in content
        assert "bin/ticket relate PROJ-101 --blocks PROJ-102" in content

    def test_generate_claude_no_labels_no_label_section(self):
        """Test Claude format omits labels section when no labels configured."""
        spec = InstructionSpec(
            project_name="No Labels Project",
            core_rules=["Rule 1"],
        )
        generator = InstructionGenerator(spec)
        content = generator.generate(AssistantFormat.CLAUDE)

        assert "## Available Labels" not in content
        # Ticket discipline should still appear since core_rules exist
        assert "## Ticket Discipline" in content

    def test_generate_claude_no_rules_no_labels_no_discipline(self):
        """Test Claude format omits discipline when no rules and no labels."""
        spec = InstructionSpec(
            project_name="Empty Project",
        )
        generator = InstructionGenerator(spec)
        content = generator.generate(AssistantFormat.CLAUDE)

        assert "## Available Labels" not in content
        assert "## Ticket Discipline" not in content

    def test_generate_cursor(self):
        """Test Cursor format generation."""
        content = self.generator.generate(AssistantFormat.CURSOR)

        assert "Cursor" in content
        assert "Test Project" in content
        assert "Read files before modifying" in content
        assert "bin/vibe doctor" in content

    def test_generate_cursor_includes_labels(self):
        """Test Cursor format includes labels and discipline."""
        content = self.generator.generate(AssistantFormat.CURSOR)

        assert "# Available Labels" in content
        assert "# Ticket Discipline" in content
        assert "Type: Bug, Feature, Chore, Refactor" in content

    def test_generate_copilot(self):
        """Test Copilot format generation."""
        content = self.generator.generate(AssistantFormat.COPILOT)

        assert "Copilot" in content
        assert "Test Project" in content
        assert "Coding Guidelines" in content
        assert "Read files before modifying" in content

    def test_generate_copilot_includes_labels(self):
        """Test Copilot format includes labels and discipline."""
        content = self.generator.generate(AssistantFormat.COPILOT)

        assert "## Available Labels" in content
        assert "## Ticket Discipline" in content
        assert "Bug, Feature, Chore, Refactor" in content

    def test_generate_generic(self):
        """Test generic AGENTS.md format generation."""
        content = self.generator.generate(AssistantFormat.GENERIC)

        assert "AGENTS.md" in content
        assert "Test Project" in content
        assert "Read files before modifying" in content

    def test_generate_generic_includes_labels(self):
        """Test generic format includes labels and discipline."""
        content = self.generator.generate(AssistantFormat.GENERIC)

        assert "## Available Labels" in content
        assert "## Ticket Discipline" in content

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
        assert "Available Labels" in claude_content
        assert "Ticket Discipline" in claude_content

    def test_header_includes_timestamp(self):
        """Test that generated files include timestamp."""
        content = self.generator.generate(AssistantFormat.CLAUDE)
        assert "Generated:" in content
        assert "DO NOT EDIT DIRECTLY" in content

    def test_ticket_discipline_examples_show_labels(self):
        """Test that ticket discipline section has examples with labels."""
        content = self.generator.generate(AssistantFormat.CLAUDE)

        assert "--label Bug" in content
        assert "--label Frontend" in content
        assert "--label Feature" in content

    def test_ticket_discipline_examples_show_parent(self):
        """Test that ticket discipline section has examples with --parent."""
        content = self.generator.generate(AssistantFormat.CLAUDE)

        assert "--parent PROJ-100" in content

    def test_ticket_discipline_examples_show_blocking(self):
        """Test that ticket discipline section has blocking link example."""
        content = self.generator.generate(AssistantFormat.CLAUDE)

        assert "bin/ticket relate PROJ-101 --blocks PROJ-102" in content


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


class TestIsGeneratedFile:
    """Tests for _is_generated_file detection logic."""

    def test_uncustomized_template_detected_as_generated(self):
        """A file with template placeholders is detected as generated."""
        from lib.vibe.agents.generator import _is_generated_file

        content = (
            "# AI Agent Instructions\n"
            "# Generated: 2026-01-15\n"
            "# Source: agent_instructions/\n"
            "#\n"
            "# DO NOT EDIT DIRECTLY - regenerate with: bin/vibe generate-agent-instructions\n"
            "\n"
            "## Project Overview\n"
            "**Project:** (your project name)\n"
        )
        assert _is_generated_file(content) is True

    def test_customized_file_with_headers_not_detected_as_generated(self):
        """A file with real project content but generated headers is NOT generated."""
        from lib.vibe.agents.generator import _is_generated_file

        content = (
            "# AI Agent Instructions\n"
            "# Generated: 2026-01-15\n"
            "# Source: agent_instructions/\n"
            "#\n"
            "# DO NOT EDIT DIRECTLY - regenerate with: bin/vibe generate-agent-instructions\n"
            "\n"
            "## Project Overview\n"
            "**Project:** My Awesome SaaS App\n"
            "**Description:** A dashboard for inventory management\n"
        )
        assert _is_generated_file(content) is False

    def test_placeholder_what_this_project_does_detected(self):
        """A file with '(what this project does)' placeholder is detected as generated."""
        from lib.vibe.agents.generator import _is_generated_file

        content = (
            "# AI Agent Instructions\n"
            "## Project Overview\n"
            "**Description:** (what this project does)\n"
        )
        assert _is_generated_file(content) is True

    def test_empty_content_not_detected_as_generated(self):
        """Empty content does not match any placeholder patterns."""
        from lib.vibe.agents.generator import _is_generated_file

        assert _is_generated_file("") is False

    def test_headers_only_not_detected_as_generated(self):
        """A file containing only header lines (no placeholders) is NOT generated."""
        from lib.vibe.agents.generator import _is_generated_file

        content = (
            "# AI Agent Instructions\n"
            "# Generated: 2026-01-15\n"
            "# Source: agent_instructions/\n"
            "# DO NOT EDIT DIRECTLY - regenerate with: bin/vibe generate-agent-instructions\n"
        )
        assert _is_generated_file(content) is False


class TestHasProjectContent:
    """Tests for _has_project_content detection logic."""

    def test_customized_file_has_project_content(self, tmp_path):
        """A file with real project content (no placeholders) has project content."""
        from lib.vibe.agents.generator import _has_project_content

        f = tmp_path / "CLAUDE.md"
        f.write_text(
            "# AI Agent Instructions\n"
            "# Generated: 2026-01-15\n"
            "# DO NOT EDIT DIRECTLY - regenerate with: bin/vibe generate-agent-instructions\n"
            "\n"
            "## Project Overview\n"
            "**Project:** My Real Project\n"
        )
        assert _has_project_content(f) is True

    def test_uncustomized_template_no_project_content(self, tmp_path):
        """A file with template placeholders does NOT have project content."""
        from lib.vibe.agents.generator import _has_project_content

        f = tmp_path / "CLAUDE.md"
        f.write_text(
            "# AI Agent Instructions\n"
            "# Generated: 2026-01-15\n"
            "## Project Overview\n"
            "**Project:** (your project name)\n"
        )
        assert _has_project_content(f) is False

    def test_missing_file_no_project_content(self, tmp_path):
        """A nonexistent file does NOT have project content."""
        from lib.vibe.agents.generator import _has_project_content

        f = tmp_path / "nonexistent.md"
        assert _has_project_content(f) is False

    def test_empty_file_no_project_content(self, tmp_path):
        """An empty file does NOT have project content."""
        from lib.vibe.agents.generator import _has_project_content

        f = tmp_path / "empty.md"
        f.write_text("")
        assert _has_project_content(f) is False
