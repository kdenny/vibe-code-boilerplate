"""GitHub Issues tracker integration.

Uses the `gh` CLI for all API interactions, which handles authentication
via `gh auth login`. No API keys needed.
"""

import json
import os
import subprocess
from typing import Any

from lib.vibe.trackers.base import Ticket, TrackerBase


def _gh(args: list[str], check: bool = True) -> subprocess.CompletedProcess[str]:
    """Run a gh CLI command and return the result."""
    result = subprocess.run(
        ["gh", *args],
        capture_output=True,
        text=True,
        timeout=30,
    )
    if check and result.returncode != 0:
        raise RuntimeError(f"gh {' '.join(args[:3])}... failed: {result.stderr.strip()}")
    return result


class GitHubIssuesTracker(TrackerBase):
    """GitHub Issues integration via the `gh` CLI.

    Requires:
      - `gh` CLI installed and authenticated (`gh auth login`)
      - A GitHub repository (detected from git remote or config)

    Config (.vibe/config.json):
      {
        "tracker": {
          "type": "github",
          "config": { "repo": "owner/repo" }
        }
      }

    If "repo" is not set, falls back to the current git remote origin.
    """

    def __init__(self, repo: str | None = None):
        self._repo = repo or os.environ.get("GITHUB_REPOSITORY")

    @property
    def name(self) -> str:
        return "github"

    def _get_repo(self) -> str:
        """Resolve the repo in owner/repo format."""
        if self._repo:
            return self._repo
        # Auto-detect from git remote
        result = _gh(["repo", "view", "--json", "nameWithOwner", "-q", ".nameWithOwner"], check=False)
        if result.returncode == 0 and result.stdout.strip():
            self._repo = result.stdout.strip()
            return self._repo
        raise RuntimeError(
            "Cannot determine GitHub repo. Set 'repo' in tracker config "
            "or run from inside a git repo with a GitHub remote."
        )

    def _repo_flag(self) -> list[str]:
        """Return ['--repo', 'owner/repo'] for gh commands."""
        return ["--repo", self._get_repo()]

    def authenticate(self, **kwargs: Any) -> bool:
        """Check that gh CLI is authenticated."""
        result = _gh(["auth", "status"], check=False)
        return result.returncode == 0

    def get_ticket(self, ticket_id: str, include_children: bool = False) -> Ticket | None:
        """Fetch a single issue by number."""
        issue_num = self._normalize_id(ticket_id)
        result = _gh(
            [
                "issue",
                "view",
                str(issue_num),
                *self._repo_flag(),
                "--json",
                "number,title,body,state,labels,url,assignees,milestone",
            ],
            check=False,
        )
        if result.returncode != 0:
            return None
        try:
            data = json.loads(result.stdout)
            return self._parse_issue(data)
        except (json.JSONDecodeError, KeyError):
            return None

    def list_tickets(
        self,
        status: str | None = None,
        labels: list[str] | None = None,
        limit: int = 50,
        assignee: str | None = None,
    ) -> list[Ticket]:
        """List issues with optional filters."""
        args = ["issue", "list", *self._repo_flag(), "--json",
                "number,title,body,state,labels,url,assignees,milestone",
                "--limit", str(limit)]

        # Map status names to GitHub state
        if status:
            gh_state = self._status_to_state(status)
            args.extend(["--state", gh_state])
        else:
            args.extend(["--state", "open"])

        if labels:
            for label in labels:
                args.extend(["--label", label])

        if assignee:
            if assignee.lower() == "me":
                args.extend(["--assignee", "@me"])
            else:
                args.extend(["--assignee", assignee])

        result = _gh(args, check=False)
        if result.returncode != 0:
            return []
        try:
            issues = json.loads(result.stdout)
            return [self._parse_issue(issue) for issue in issues]
        except (json.JSONDecodeError, KeyError):
            return []

    def create_ticket(
        self,
        title: str,
        description: str,
        labels: list[str] | None = None,
        assignee: str | None = None,
    ) -> Ticket:
        """Create a new issue."""
        args = ["issue", "create", *self._repo_flag(),
                "--title", title, "--body", description]

        if labels:
            for label in labels:
                args.extend(["--label", label])

        if assignee:
            if assignee.lower() == "me":
                args.extend(["--assignee", "@me"])
            else:
                args.extend(["--assignee", assignee])

        result = _gh(args)

        # gh issue create outputs the URL of the new issue
        issue_url = result.stdout.strip()
        # Extract issue number from URL
        issue_num = issue_url.rstrip("/").split("/")[-1]

        # Fetch the created issue to return full Ticket
        ticket = self.get_ticket(issue_num)
        if ticket is None:
            raise RuntimeError(f"Created issue but could not fetch it: {issue_url}")
        return ticket

    def update_ticket(
        self,
        ticket_id: str,
        title: str | None = None,
        description: str | None = None,
        status: str | None = None,
        labels: list[str] | None = None,
        assignee: str | None = None,
        unassign: bool = False,
    ) -> Ticket:
        """Update an existing issue."""
        issue_num = self._normalize_id(ticket_id)

        # Handle status changes (open/close)
        if status:
            state = self._status_to_state(status)
            if state == "closed":
                _gh(["issue", "close", str(issue_num), *self._repo_flag()])
            elif state == "open":
                _gh(["issue", "reopen", str(issue_num), *self._repo_flag()])

        # Handle field updates via gh issue edit
        edit_args: list[str] = []
        if title:
            edit_args.extend(["--title", title])
        if description:
            edit_args.extend(["--body", description])
        if labels:
            for label in labels:
                edit_args.extend(["--add-label", label])
        if assignee:
            if assignee.lower() == "me":
                edit_args.extend(["--add-assignee", "@me"])
            else:
                edit_args.extend(["--add-assignee", assignee])
        if unassign:
            # gh issue edit doesn't have --remove-assignee for all,
            # so we remove via the API
            edit_args.extend(["--remove-assignee", "@me"])

        if edit_args:
            _gh(["issue", "edit", str(issue_num), *self._repo_flag(), *edit_args])

        ticket = self.get_ticket(str(issue_num))
        if ticket is None:
            raise RuntimeError(f"Updated issue #{issue_num} but could not fetch it")
        return ticket

    def comment_ticket(self, ticket_id: str, body: str) -> None:
        """Add a comment to an issue."""
        issue_num = self._normalize_id(ticket_id)
        _gh(["issue", "comment", str(issue_num), *self._repo_flag(), "--body", body])

    def list_labels(self) -> list[dict[str, str]]:
        """List all labels in the repo."""
        result = _gh(
            ["label", "list", *self._repo_flag(), "--json", "name,color,description", "--limit", "100"],
            check=False,
        )
        if result.returncode != 0:
            return []
        try:
            labels = json.loads(result.stdout)
            return [
                {
                    "id": label.get("name", ""),  # GitHub labels use name as ID
                    "name": label.get("name", ""),
                    "color": label.get("color", ""),
                }
                for label in labels
            ]
        except json.JSONDecodeError:
            return []

    def validate_config(self) -> tuple[bool, list[str]]:
        """Validate GitHub Issues configuration."""
        issues: list[str] = []

        # Check gh CLI is available
        try:
            subprocess.run(["gh", "--version"], capture_output=True, check=True, timeout=10)
        except (subprocess.CalledProcessError, FileNotFoundError):
            issues.append("gh CLI is not installed. Install from https://cli.github.com/")
            return False, issues

        # Check gh is authenticated
        if not self.authenticate():
            issues.append("gh CLI is not authenticated. Run: gh auth login")

        # Check repo is accessible
        try:
            self._get_repo()
        except RuntimeError as e:
            issues.append(str(e))

        return len(issues) == 0, issues

    @staticmethod
    def _normalize_id(ticket_id: str) -> int:
        """Normalize issue ID: '#123' or '123' → 123."""
        cleaned = ticket_id.lstrip("#")
        try:
            return int(cleaned)
        except ValueError:
            raise RuntimeError(
                f"Invalid GitHub issue number: '{ticket_id}'. "
                "Expected a number like '123' or '#123'."
            ) from None

    @staticmethod
    def _status_to_state(status: str) -> str:
        """Map human-readable status names to GitHub issue states."""
        status_lower = status.lower()
        closed_statuses = {"done", "closed", "canceled", "cancelled", "deployed", "released"}
        if status_lower in closed_statuses:
            return "closed"
        # "all" is a valid gh state filter
        if status_lower == "all":
            return "all"
        return "open"

    @staticmethod
    def _parse_issue(issue: dict) -> Ticket:
        """Parse a GitHub issue JSON into a Ticket."""
        number = issue.get("number", 0)
        labels = [label.get("name", "") for label in issue.get("labels", [])]
        assignees = issue.get("assignees", [])
        assignee = assignees[0].get("login", "") if assignees else None

        return Ticket(
            id=f"#{number}",
            title=issue.get("title", ""),
            description=issue.get("body", "") or "",
            status=issue.get("state", "OPEN").capitalize(),
            labels=labels,
            url=issue.get("url", ""),
            raw=issue,
            assignee=assignee,
        )
