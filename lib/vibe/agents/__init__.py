"""Multi-assistant support for generating instruction files."""

from lib.vibe.agents.generator import InstructionGenerator
from lib.vibe.agents.spec import AssistantFormat, InstructionSpec

__all__ = ["InstructionSpec", "AssistantFormat", "InstructionGenerator"]
