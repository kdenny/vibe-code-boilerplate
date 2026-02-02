"""Linear.app ticket tracker integration."""

import os
from typing import Any

import requests

from lib.vibe.trackers.base import Ticket, TrackerBase

LINEAR_API_URL = "https://api.linear.app/graphql"


class LinearTracker(TrackerBase):
    """Linear.app integration."""

    def __init__(self, api_key: str | None = None, team_id: str | None = None):
        self._api_key = api_key or os.environ.get("LINEAR_API_KEY")
        self._team_id = team_id
        self._headers: dict[str, str] = {}
        if self._api_key:
            self._headers = {
                "Authorization": self._api_key,
                "Content-Type": "application/json",
            }

    @property
    def name(self) -> str:
        return "linear"

    def authenticate(self, **kwargs: Any) -> bool:
        """Authenticate with Linear API."""
        api_key = kwargs.get("api_key") or self._api_key
        if not api_key:
            return False

        self._api_key = api_key
        self._headers = {
            "Authorization": api_key,
            "Content-Type": "application/json",
        }

        # Test authentication
        query = """
        query {
            viewer {
                id
                name
            }
        }
        """
        try:
            response = self._execute_query(query)
            return "viewer" in response.get("data", {})
        except Exception:
            return False

    def _execute_query(self, query: str, variables: dict | None = None) -> dict:
        """Execute a GraphQL query against Linear API."""
        payload: dict[str, Any] = {"query": query}
        if variables:
            payload["variables"] = variables

        response = requests.post(LINEAR_API_URL, headers=self._headers, json=payload, timeout=30)
        response.raise_for_status()
        return response.json()

    def get_ticket(self, ticket_id: str) -> Ticket | None:
        """Fetch a single ticket by ID or identifier."""
        query = """
        query GetIssue($id: String!) {
            issue(id: $id) {
                id
                identifier
                title
                description
                state { name }
                labels { nodes { name } }
                url
            }
        }
        """
        try:
            result = self._execute_query(query, {"id": ticket_id})
            issue = result.get("data", {}).get("issue")
            if not issue:
                return None
            return self._parse_issue(issue)
        except Exception:
            return None

    def list_tickets(
        self,
        status: str | None = None,
        labels: list[str] | None = None,
        limit: int = 50,
    ) -> list[Ticket]:
        """List tickets with optional filters."""
        query = """
        query ListIssues($first: Int!, $filter: IssueFilter) {
            issues(first: $first, filter: $filter) {
                nodes {
                    id
                    identifier
                    title
                    description
                    state { name }
                    labels { nodes { name } }
                    url
                }
            }
        }
        """
        filter_obj: dict[str, Any] = {}
        if self._team_id:
            filter_obj["team"] = {"id": {"eq": self._team_id}}
        if status:
            filter_obj["state"] = {"name": {"eq": status}}
        if labels:
            filter_obj["labels"] = {"name": {"in": labels}}

        variables: dict[str, Any] = {"first": limit}
        if filter_obj:
            variables["filter"] = filter_obj

        try:
            result = self._execute_query(query, variables)
            issues = result.get("data", {}).get("issues", {}).get("nodes", [])
            return [self._parse_issue(issue) for issue in issues]
        except Exception:
            return []

    def create_ticket(
        self,
        title: str,
        description: str,
        labels: list[str] | None = None,
    ) -> Ticket:
        """Create a new ticket in Linear."""
        mutation = """
        mutation CreateIssue($input: IssueCreateInput!) {
            issueCreate(input: $input) {
                success
                issue {
                    id
                    identifier
                    title
                    description
                    state { name }
                    labels { nodes { name } }
                    url
                }
            }
        }
        """
        input_obj: dict[str, Any] = {
            "title": title,
            "description": description,
        }
        if self._team_id:
            input_obj["teamId"] = self._team_id

        result = self._execute_query(mutation, {"input": input_obj})
        issue = result.get("data", {}).get("issueCreate", {}).get("issue")
        if not issue:
            raise RuntimeError("Failed to create ticket")
        return self._parse_issue(issue)

    def update_ticket(
        self,
        ticket_id: str,
        title: str | None = None,
        description: str | None = None,
        status: str | None = None,
        labels: list[str] | None = None,
    ) -> Ticket:
        """Update an existing ticket."""
        mutation = """
        mutation UpdateIssue($id: String!, $input: IssueUpdateInput!) {
            issueUpdate(id: $id, input: $input) {
                success
                issue {
                    id
                    identifier
                    title
                    description
                    state { name }
                    labels { nodes { name } }
                    url
                }
            }
        }
        """
        input_obj: dict[str, Any] = {}
        if title:
            input_obj["title"] = title
        if description:
            input_obj["description"] = description
        # Note: status and labels require additional API calls to resolve IDs

        result = self._execute_query(mutation, {"id": ticket_id, "input": input_obj})
        issue = result.get("data", {}).get("issueUpdate", {}).get("issue")
        if not issue:
            raise RuntimeError("Failed to update ticket")
        return self._parse_issue(issue)

    def validate_config(self) -> tuple[bool, list[str]]:
        """Validate Linear configuration."""
        issues = []

        if not self._api_key:
            issues.append("LINEAR_API_KEY not set")

        if not self._team_id:
            issues.append("Linear team ID not configured")

        if self._api_key and not self.authenticate():
            issues.append("LINEAR_API_KEY is invalid or expired")

        return len(issues) == 0, issues

    def _parse_issue(self, issue: dict) -> Ticket:
        """Parse a Linear issue into a Ticket."""
        return Ticket(
            id=issue.get("identifier", issue.get("id", "")),
            title=issue.get("title", ""),
            description=issue.get("description", ""),
            status=issue.get("state", {}).get("name", ""),
            labels=[label["name"] for label in issue.get("labels", {}).get("nodes", [])],
            url=issue.get("url", ""),
            raw=issue,
        )
