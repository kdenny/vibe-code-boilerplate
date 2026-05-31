"""Multi-assistant support for generating instruction files."""

from vibe.agents.generator import InstructionGenerator
from vibe.agents.spec import AssistantFormat, InstructionSpec

__all__ = ["InstructionSpec", "AssistantFormat", "InstructionGenerator"]
