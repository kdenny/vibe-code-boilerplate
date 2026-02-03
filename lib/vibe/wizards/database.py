"""Intelligent database selection wizard (Neon vs Supabase)."""

from typing import Any

import click

from lib.vibe.tools import require_interactive
from lib.vibe.wizards.neon import run_neon_wizard
from lib.vibe.wizards.supabase import run_supabase_wizard


def _ask_features() -> dict[str, bool]:
    """Ask about app feature requirements."""
    click.echo("\nWhat features does your app need?")
    click.echo("(Select all that apply with y/n)")
    click.echo()

    features = {}

    features["auth"] = click.confirm(
        "  User authentication (login, signup, OAuth)?",
        default=False,
    )

    features["storage"] = click.confirm(
        "  File/image uploads and storage?",
        default=False,
    )

    features["realtime"] = click.confirm(
        "  Real-time updates (live data, presence)?",
        default=False,
    )

    features["edge_functions"] = click.confirm(
        "  Edge functions (serverless compute)?",
        default=False,
    )

    features["just_database"] = click.confirm(
        "  Just a database (I'll build the rest myself)?",
        default=True,
    )

    return features


def _ask_branching() -> str:
    """Ask about database branching preferences."""
    click.echo("\nWhat's your database branching strategy?")
    click.echo()
    click.echo("  1. One database branch per git branch (isolated testing)")
    click.echo("  2. Separate staging/production databases")
    click.echo("  3. Single database for everything")
    click.echo()

    choice = click.prompt(
        "  Select",
        type=click.Choice(["1", "2", "3"]),
        default="2",
    )

    return {
        "1": "per_branch",
        "2": "staging_prod",
        "3": "single",
    }[choice]


def _calculate_recommendation(features: dict[str, bool], branching: str) -> tuple[str, list[str]]:
    """
    Calculate recommendation based on answers.

    Returns:
        Tuple of (recommendation, reasons)
    """
    supabase_features = 0
    reasons = []

    # Count Supabase features
    if features.get("auth"):
        supabase_features += 1
        reasons.append("You need user authentication → Supabase Auth")

    if features.get("storage"):
        supabase_features += 1
        reasons.append("You need file uploads → Supabase Storage")

    if features.get("realtime"):
        supabase_features += 1
        reasons.append("You need real-time updates → Supabase Realtime")

    if features.get("edge_functions"):
        supabase_features += 1
        reasons.append("You need edge functions → Supabase Edge Functions")

    # Neon strengths
    neon_reasons = []

    if features.get("just_database") and supabase_features == 0:
        neon_reasons.append("You just need a database → Neon is simpler and focused")

    if branching == "per_branch":
        neon_reasons.append("You want per-branch databases → Neon has instant branching")

    # Decision logic
    if supabase_features >= 2:
        # Strong Supabase recommendation
        return "supabase", reasons + ["Full Postgres access included"]

    if supabase_features == 1 and branching != "per_branch":
        # Slight Supabase lean
        return "supabase", reasons + ["Database included with full Postgres access"]

    if branching == "per_branch":
        # Neon wins on branching
        neon_reasons.append("Neon's branching matches your git workflow perfectly")
        return "neon", neon_reasons

    if features.get("just_database") and supabase_features == 0:
        # Pure database use case
        return "neon", neon_reasons or ["Simpler setup focused on Postgres"]

    # Default: slight Neon preference for simplicity
    if not neon_reasons:
        neon_reasons = ["Serverless Postgres with excellent developer experience"]

    return "neon", neon_reasons


def _print_recommendation(
    recommendation: str,
    reasons: list[str],
    features: dict[str, bool],
    branching: str,
) -> None:
    """Print the recommendation with reasoning."""
    click.echo("\n" + "=" * 50)
    click.echo(f"  Based on your requirements, we recommend: {recommendation.title()}")
    click.echo("=" * 50)
    click.echo()

    click.echo("Why:")
    for reason in reasons:
        click.echo(f"  ✓ {reason}")
    click.echo()

    # Show alternative
    alternative = "Supabase" if recommendation == "neon" else "Neon"
    if recommendation == "neon":
        click.echo(f"Alternative: {alternative} offers auth, storage, and realtime")
        click.echo("  if you later need those built-in features.")
    else:
        click.echo(f"Alternative: {alternative} offers instant database branching")
        click.echo("  if per-branch isolated databases become important.")
    click.echo()


def run_database_wizard(config: dict[str, Any]) -> bool:
    """
    Intelligent database selection wizard.

    Asks questions about app requirements and recommends
    either Neon or Supabase based on the answers.

    Args:
        config: Configuration dict to update

    Returns:
        True if configuration was successful
    """
    # Check prerequisites
    ok, error = require_interactive("Database selection")
    if not ok:
        click.echo(f"\n{error}")
        return False

    click.echo("\n" + "=" * 50)
    click.echo("  Database Selection Wizard")
    click.echo("=" * 50)
    click.echo()
    click.echo("This wizard helps you choose between Neon and Supabase.")
    click.echo()
    click.echo("Both are excellent Postgres options:")
    click.echo("  • Neon: Pure serverless Postgres with instant branching")
    click.echo("  • Supabase: Full backend platform (auth, storage, realtime)")

    # Gather requirements
    features = _ask_features()
    branching = _ask_branching()

    # Calculate and show recommendation
    recommendation, reasons = _calculate_recommendation(features, branching)
    _print_recommendation(recommendation, reasons, features, branching)

    # Confirm or override
    proceed = click.prompt(
        f"Proceed with {recommendation.title()} setup?",
        type=click.Choice(["yes", "neon", "supabase", "skip"]),
        default="yes",
    )

    if proceed == "skip":
        click.echo("\nDatabase setup skipped. Configure later with:")
        click.echo("  bin/vibe setup -w database")
        click.echo("  bin/vibe setup -w neon")
        click.echo("  bin/vibe setup -w supabase")
        return True

    # Override if user chose differently
    if proceed in ["neon", "supabase"]:
        final_choice = proceed
    else:
        final_choice = recommendation

    # Store the choice
    if "database" not in config:
        config["database"] = {}
    config["database"]["provider"] = final_choice

    # Run the appropriate wizard
    click.echo()
    if final_choice == "neon":
        return run_neon_wizard(config)
    else:
        return run_supabase_wizard(config)
