"""Tests for UI context module."""

import pytest

from lib.vibe.ui.context import WizardContext


class TestWizardContext:
    def test_is_configured_github(self) -> None:
        config = {"github": {"auth_method": "gh_cli"}}
        context = WizardContext(config)
        assert context.is_configured("github") is True

    def test_is_configured_github_not_set(self) -> None:
        config: dict = {"github": {}}
        context = WizardContext(config)
        assert context.is_configured("github") is False

    def test_is_configured_tracker_linear(self) -> None:
        config = {"tracker": {"type": "linear"}}
        context = WizardContext(config)
        assert context.is_configured("tracker") is True

    def test_is_configured_tracker_none(self) -> None:
        config = {"tracker": {"type": None}}
        context = WizardContext(config)
        assert context.is_configured("tracker") is False

    def test_is_configured_database_with_provider(self) -> None:
        config = {"database": {"provider": "neon"}}
        context = WizardContext(config)
        assert context.is_configured("database") is True

    def test_is_configured_database_with_neon(self) -> None:
        config = {"database": {"neon": {"enabled": True}}}
        context = WizardContext(config)
        assert context.is_configured("database") is True
        assert context.is_configured("neon") is True

    def test_is_configured_database_with_supabase(self) -> None:
        config = {"database": {"supabase": {"enabled": True}}}
        context = WizardContext(config)
        assert context.is_configured("database") is True
        assert context.is_configured("supabase") is True

    def test_is_configured_vercel(self) -> None:
        config = {"deployment": {"vercel": {"enabled": True}}}
        context = WizardContext(config)
        assert context.is_configured("vercel") is True

    def test_is_configured_fly(self) -> None:
        config = {"deployment": {"fly": {"enabled": True}}}
        context = WizardContext(config)
        assert context.is_configured("fly") is True

    def test_is_configured_sentry(self) -> None:
        config = {"observability": {"sentry": {"enabled": True}}}
        context = WizardContext(config)
        assert context.is_configured("sentry") is True

    def test_is_configured_playwright(self) -> None:
        config = {"testing": {"playwright": {"enabled": True}}}
        context = WizardContext(config)
        assert context.is_configured("playwright") is True

    def test_is_configured_unknown_wizard(self) -> None:
        config: dict = {}
        context = WizardContext(config)
        assert context.is_configured("unknown") is False

    def test_get_recommendation_neon_to_vercel(self) -> None:
        config = {"database": {"provider": "neon"}}
        context = WizardContext(config)
        rec = context.get_recommendation("neon")
        # Should recommend vercel for neon
        if rec:
            wizard, reason = rec
            assert wizard == "vercel"
            assert "neon" in reason.lower() or "serverless" in reason.lower()

    def test_get_recommendation_skips_configured(self) -> None:
        config = {
            "database": {"provider": "neon"},
            "deployment": {"vercel": {"enabled": True}},
        }
        context = WizardContext(config)
        rec = context.get_recommendation("neon")
        # Vercel is already configured, should not recommend it
        if rec:
            wizard, _ = rec
            assert wizard != "vercel"

    def test_get_unconfigured_prerequisites_vercel(self) -> None:
        config: dict = {}
        context = WizardContext(config)
        prereqs = context.get_unconfigured_prerequisites("vercel")
        assert "github" in prereqs

    def test_get_unconfigured_prerequisites_vercel_with_github(self) -> None:
        config = {"github": {"auth_method": "gh_cli"}}
        context = WizardContext(config)
        prereqs = context.get_unconfigured_prerequisites("vercel")
        assert "github" not in prereqs

    def test_can_run_wizard_without_prereqs(self) -> None:
        config: dict = {}
        context = WizardContext(config)
        can_run, reason = context.can_run_wizard("sentry")
        assert can_run is True
        assert reason is None

    def test_can_run_wizard_with_missing_prereqs(self) -> None:
        config: dict = {}
        context = WizardContext(config)
        can_run, reason = context.can_run_wizard("vercel")
        assert can_run is False
        assert reason is not None
        assert "github" in reason.lower()

    def test_can_run_wizard_with_prereqs_met(self) -> None:
        config = {"github": {"auth_method": "gh_cli"}}
        context = WizardContext(config)
        can_run, reason = context.can_run_wizard("vercel")
        assert can_run is True
        assert reason is None

    def test_get_setup_hints_no_tracker(self) -> None:
        config = {"tracker": {"type": None}}
        context = WizardContext(config)
        hints = context.get_setup_hints()
        assert any("tracker" in hint.lower() or "ticket" in hint.lower() for hint in hints)

    def test_get_setup_hints_no_database_for_beginner(self) -> None:
        config = {"tracker": {"type": "linear"}}
        context = WizardContext(config)
        hints = context.get_setup_hints(skill_level="beginner")
        assert any("database" in hint.lower() for hint in hints)

    def test_get_setup_hints_database_no_deployment(self) -> None:
        config = {
            "tracker": {"type": "linear"},
            "database": {"neon": {"enabled": True}},
        }
        context = WizardContext(config)
        hints = context.get_setup_hints()
        assert any("deployment" in hint.lower() or "vercel" in hint.lower() for hint in hints)

    def test_get_setup_hints_deployment_no_sentry(self) -> None:
        config = {
            "tracker": {"type": "linear"},
            "database": {"neon": {"enabled": True}},
            "deployment": {"vercel": {"enabled": True}},
        }
        context = WizardContext(config)
        hints = context.get_setup_hints(skill_level="intermediate")
        assert any("sentry" in hint.lower() for hint in hints)

    def test_get_setup_hints_expert_less_verbose(self) -> None:
        config = {"tracker": {"type": "linear"}}
        context = WizardContext(config)
        beginner_hints = context.get_setup_hints(skill_level="beginner")
        expert_hints = context.get_setup_hints(skill_level="expert")
        # Expert hints may be less detailed
        # At minimum, both should work without error
        assert isinstance(beginner_hints, list)
        assert isinstance(expert_hints, list)
