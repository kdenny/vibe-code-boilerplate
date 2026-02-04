"""Context-aware wizard recommendations."""

from typing import Any


class WizardContext:
    """Smart recommendations based on configuration.

    Provides context-aware suggestions for wizard flows based on
    what's already configured and common integration pairings.

    Example:
        context = WizardContext(config)
        rec = context.get_recommendation("database")
        if rec:
            wizard, reason = rec
            print(f"Recommended: {wizard} - {reason}")
    """

    # Known good pairings: (category, provider) -> (recommended_wizard, reason)
    PAIRINGS: dict[tuple[str, str], tuple[str, str]] = {
        # Database -> Deployment pairings
        ("database", "neon"): ("vercel", "Neon works great with Vercel serverless functions"),
        ("database", "supabase"): ("vercel", "Supabase + Vercel is a popular production stack"),
        ("database", "postgres"): ("fly", "Fly.io provides easy Postgres hosting alongside your app"),
        # Deployment -> Monitoring pairings
        ("deployment", "vercel"): ("sentry", "Sentry integrates well with Vercel for error tracking"),
        ("deployment", "fly"): ("sentry", "Sentry helps monitor your Fly.io deployments"),
        # Framework -> Deployment pairings
        ("framework", "nextjs"): ("vercel", "Next.js is optimized for Vercel deployment"),
        ("framework", "remix"): ("fly", "Remix works well with Fly.io for edge deployment"),
        ("framework", "django"): ("fly", "Django apps deploy easily on Fly.io containers"),
        ("framework", "fastapi"): ("fly", "FastAPI works great with Fly.io containers"),
    }

    # Wizard dependencies: what should be configured before what
    PREREQUISITES: dict[str, list[str]] = {
        "vercel": ["github"],
        "fly": ["github"],
        "sentry": [],
        "neon": [],
        "supabase": [],
        "tracker": ["github"],
        "playwright": [],
    }

    def __init__(self, config: dict[str, Any]):
        """Initialize context.

        Args:
            config: Current project configuration
        """
        self.config = config

    def get_recommendation(self, completed_wizard: str) -> tuple[str, str] | None:
        """Get a recommendation based on what was just configured.

        Args:
            completed_wizard: Name of the wizard that just completed

        Returns:
            Tuple of (recommended_wizard, reason) or None
        """
        # Determine what category/provider was just configured
        provider = self._get_provider(completed_wizard)
        if provider:
            key = (completed_wizard, provider)
            if key in self.PAIRINGS:
                wizard, reason = self.PAIRINGS[key]
                if not self.is_configured(wizard):
                    return (wizard, reason)

        # Check category-based pairings
        category = self._get_category(completed_wizard)
        if category:
            for (cat, prov), (wizard, reason) in self.PAIRINGS.items():
                if cat == category and not self.is_configured(wizard):
                    return (wizard, reason)

        return None

    def _get_provider(self, wizard_name: str) -> str | None:
        """Get the provider name from config for a wizard category."""
        providers = {
            "database": lambda: self.config.get("database", {}).get("provider"),
            "neon": lambda: "neon",
            "supabase": lambda: "supabase",
            "vercel": lambda: "vercel",
            "fly": lambda: "fly",
        }
        fn = providers.get(wizard_name)
        return fn() if fn else None

    def _get_category(self, wizard_name: str) -> str | None:
        """Map wizard name to category."""
        categories = {
            "neon": "database",
            "supabase": "database",
            "database": "database",
            "vercel": "deployment",
            "fly": "deployment",
            "sentry": "monitoring",
            "playwright": "testing",
        }
        return categories.get(wizard_name)

    def is_configured(self, wizard: str) -> bool:
        """Check if a wizard's integration is already configured.

        Args:
            wizard: Wizard name to check

        Returns:
            True if configured, False otherwise
        """
        checks = {
            "github": lambda: bool(self.config.get("github", {}).get("auth_method")),
            "tracker": lambda: self.config.get("tracker", {}).get("type") is not None,
            "database": lambda: bool(
                self.config.get("database", {}).get("provider")
                or self.config.get("database", {}).get("neon", {}).get("enabled")
                or self.config.get("database", {}).get("supabase", {}).get("enabled")
            ),
            "neon": lambda: bool(self.config.get("database", {}).get("neon", {}).get("enabled")),
            "supabase": lambda: bool(
                self.config.get("database", {}).get("supabase", {}).get("enabled")
            ),
            "vercel": lambda: bool(
                self.config.get("deployment", {}).get("vercel", {}).get("enabled")
            ),
            "fly": lambda: bool(
                self.config.get("deployment", {}).get("fly", {}).get("enabled")
            ),
            "sentry": lambda: bool(
                self.config.get("observability", {}).get("sentry", {}).get("enabled")
            ),
            "playwright": lambda: bool(
                self.config.get("testing", {}).get("playwright", {}).get("enabled")
            ),
        }

        check_fn = checks.get(wizard)
        return check_fn() if check_fn else False

    def get_unconfigured_prerequisites(self, wizard: str) -> list[str]:
        """Get list of prerequisites that aren't configured yet.

        Args:
            wizard: Wizard to check prerequisites for

        Returns:
            List of unconfigured prerequisite wizard names
        """
        prereqs = self.PREREQUISITES.get(wizard, [])
        return [p for p in prereqs if not self.is_configured(p)]

    def can_run_wizard(self, wizard: str) -> tuple[bool, str | None]:
        """Check if a wizard can be run (prerequisites met).

        Args:
            wizard: Wizard name to check

        Returns:
            Tuple of (can_run, blocking_reason)
        """
        missing = self.get_unconfigured_prerequisites(wizard)
        if missing:
            return (False, f"Configure {', '.join(missing)} first")
        return (True, None)

    def get_setup_hints(self, skill_level: str = "intermediate") -> list[str]:
        """Get helpful hints based on current configuration.

        Args:
            skill_level: User's skill level (beginner, intermediate, expert)

        Returns:
            List of hint strings
        """
        hints = []

        # Check for common missing configurations
        if not self.is_configured("tracker"):
            hints.append("Tip: Configure ticket tracking to link PRs to tickets")

        if not self.is_configured("database"):
            if skill_level == "beginner":
                hints.append(
                    "Tip: Most apps need a database. Run 'bin/vibe setup -w database' "
                    "to configure Neon (serverless) or Supabase (full platform)"
                )

        if self.is_configured("database") and not (
            self.is_configured("vercel") or self.is_configured("fly")
        ):
            hints.append("Tip: Database configured but no deployment. Consider Vercel or Fly.io")

        if (self.is_configured("vercel") or self.is_configured("fly")) and not self.is_configured(
            "sentry"
        ):
            if skill_level != "expert":
                hints.append("Tip: Consider adding Sentry for production error monitoring")

        return hints
