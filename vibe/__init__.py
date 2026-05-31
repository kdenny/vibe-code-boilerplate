"""Public package root for Vibe workflow automation."""

from vibe.version import get_version

from . import cli, config, errors

__version__ = get_version()

__all__ = ["__version__", "cli", "config", "errors"]
