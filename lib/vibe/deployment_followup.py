"""Deployment infrastructure follow-up: detect configs and build HUMAN ticket content."""

from pathlib import Path

# Files that indicate deployment/infra was added (path or path suffix)
DEPLOYMENT_INDICATORS = [
    ("fly.toml", "Fly.io", "API / worker hosting"),
    ("vercel.json", "Vercel", "Web app hosting"),
    (".env.example", "Env", "Environment variables template"),
]

# Optional: database / external services (often referenced in .env.example or docs)
NEON_INDICATORS = ("neon", "neon.ini", "NEON_DATABASE_URL")
SUPABASE_INDICATORS = ("supabase", "SUPABASE_")


def detect_deployment_platforms(
    changed_files: list[str] | None = None,
    repo_root: Path | None = None,
) -> list[tuple[str, str]]:
    """
    Detect which deployment platforms are present from changed files or repo scan.

    Args:
        changed_files: List of file paths (e.g. from git diff). If None, scan repo_root.
        repo_root: Root to scan when changed_files is None. Defaults to cwd.

    Returns:
        List of (platform_name, description) for each detected platform.
    """
    if changed_files is not None:
        return _platforms_from_files(changed_files)
    root = Path(repo_root or ".")
    found: list[tuple[str, str]] = []
    seen_platforms: set[str] = set()
    for path_spec, platform_name, desc in DEPLOYMENT_INDICATORS:
        if platform_name in seen_platforms:
            continue
        check_path = root / path_spec
        if check_path.exists():
            found.append((platform_name, desc))
            seen_platforms.add(platform_name)
    return found


def _platforms_from_files(changed_files: list[str]) -> list[tuple[str, str]]:
    """Derive platforms from a list of changed file paths."""
    found: list[tuple[str, str]] = []
    seen: set[str] = set()
    lower_files = [f.replace("\\", "/").lower() for f in changed_files]
    for path_spec, platform_name, desc in DEPLOYMENT_INDICATORS:
        if platform_name in seen:
            continue
        spec_lower = path_spec.lower()
        for cf in lower_files:
            if cf.endswith(spec_lower) or spec_lower in cf:
                found.append((platform_name, desc))
                seen.add(platform_name)
                break
    return found


def build_human_followup_body(
    platforms: list[tuple[str, str]],
    repo_owner: str = "",
    repo_name: str = "",
    parent_ticket_id: str | None = None,
    env_example_path: str = ".env.example",
) -> str:
    """
    Build the description body for a HUMAN follow-up ticket (step-by-step, checklist).

    Args:
        platforms: From detect_deployment_platforms (platform_name, description).
        repo_owner: GitHub owner (e.g. from config or GITHUB_REPOSITORY).
        repo_name: GitHub repo name.
        parent_ticket_id: Optional parent ticket ID for context.
        env_example_path: Path to .env.example for instructions.

    Returns:
        Markdown string suitable for ticket description.
    """
    repo_ref = f"{repo_owner}/{repo_name}" if (repo_owner and repo_name) else "owner/repo"
    lines = [
        "This ticket requires **human action** to complete deployment setup.",
        "",
        "## Prerequisites",
        "- Access to team password manager (e.g. 1Password)",
        "- Company credit card (for paid tiers if needed)",
        "- GitHub access to this repository",
        "",
    ]
    if parent_ticket_id:
        lines.extend([
            f"## Context",
            f"Follow-up from **{parent_ticket_id}** (deployment configs were added in that ticket).",
            "",
        ])
    lines.append("## Steps")
    lines.append("")

    if any(p[0] == "Vercel" for p in platforms):
        lines.extend([
            "### 1. Vercel (Web App Hosting)",
            "1. Go to [vercel.com](https://vercel.com) and sign in with GitHub.",
            "2. Click **Add New Project**.",
            f"3. Import the `{repo_ref}` repository.",
            "4. Set the root directory if needed (e.g. `apps/web` or `ui`).",
            f"5. Add environment variables from `{env_example_path}` (or from team secrets).",
            "6. Click **Deploy**.",
            "",
            "[Vercel docs →](https://vercel.com/docs)",
            "",
        ])
    if any(p[0] == "Fly.io" for p in platforms):
        lines.extend([
            "### 2. Fly.io (API / Worker Hosting)",
            "1. Go to [fly.io](https://fly.io) and sign up or log in.",
            "2. Install the Fly CLI: `curl -L https://fly.io/install.sh | sh` (or see [docs](https://fly.io/docs/hands-on/install-flyctl/)).",
            "3. From the repo root, run: `fly launch` (or use existing `fly.toml`).",
            "4. Set secrets: `fly secrets set KEY=value` for each variable from your env.",
            "5. Deploy: `fly deploy`.",
            "",
            "[Fly.io docs →](https://fly.io/docs)",
            "",
        ])
    if any(p[0] == "Env" for p in platforms):
        lines.extend([
            "### 3. Environment variables",
            f"1. Copy `{env_example_path}` to a local `.env` or use the team’s shared env template.",
            "2. Fill in real values (get them from the team password manager).",
            "3. Never commit real secrets; use the deployment platform’s UI or CLI for production.",
            "",
        ])

    lines.extend([
        "## Verification",
        "- [ ] Web app loads at production URL (if applicable)",
        "- [ ] API health check returns 200 (if applicable)",
        "- [ ] Worker/background jobs run (if applicable)",
        "- [ ] No secrets committed to the repo",
        "",
    ])
    return "\n".join(lines).strip()


def get_default_human_followup_title() -> str:
    """Default title for the auto-created HUMAN follow-up ticket."""
    return "Set up production infrastructure (human follow-up)"
