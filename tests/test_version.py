"""Tests for version management."""

from lib.vibe.version import bump_version, get_version


class TestGetVersion:
    def test_returns_string(self):
        version = get_version()
        assert isinstance(version, str)
        assert len(version.split(".")) == 3

    def test_no_whitespace(self):
        version = get_version()
        assert version == version.strip()


class TestBumpVersion:
    def test_patch_bump(self):
        assert bump_version("1.0.0", "patch") == "1.0.1"

    def test_minor_bump(self):
        assert bump_version("1.0.0", "minor") == "1.1.0"

    def test_minor_resets_patch(self):
        assert bump_version("1.2.3", "minor") == "1.3.0"

    def test_patch_increment(self):
        assert bump_version("1.2.3", "patch") == "1.2.4"

    def test_double_digit(self):
        assert bump_version("1.9.9", "patch") == "1.9.10"

    def test_minor_double_digit(self):
        assert bump_version("1.9.9", "minor") == "1.10.0"
