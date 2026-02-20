"""Linear.app ticket tracker integration."""

import os
from typing import Any

import requests

from lib.vibe.trackers.base import Project, Ticket, TrackerBase

LINEAR_API_URL = "https://api.linear.app/graphql"

# Priority mapping: Linear uses integers, we expose friendly names
PRIORITY_MAP = {
    "none": 0,
    "urgent": 1,
    "high": 2,
    "medium": 3,
    "low": 4,
}
PRIORITY_NAMES = {v: k for k, v in PRIORITY_MAP.items()}


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

    def get_ticket(self, ticket_id: str, include_children: bool = False) -> Ticket | None:
        """Fetch a single ticket by ID or identifier.

        Args:
            ticket_id: The ticket ID or identifier (e.g., "PROJ-123")
            include_children: If True, fetch sub-tasks (children)
        """
        # Build children fragment conditionally
        children_fragment = (
            """
                children {
                    nodes {
                        id
                        identifier
                        title
                        state { name }
                    }
                }
        """
            if include_children
            else ""
        )

        query = f"""
        query GetIssue($id: String!) {{
            issue(id: $id) {{
                id
                identifier
                title
                description
                state {{ id name }}
                team {{ id }}
                labels {{ nodes {{ name }} }}
                url
                priority
                assignee {{ id name email }}
                project {{ id name }}
                parent {{ id identifier title }}
                {children_fragment}
            }}
        }}
        """
        try:
            result = self._execute_query(query, {"id": ticket_id})
            issue = result.get("data", {}).get("issue")
            if not issue:
                return None
            return self._parse_issue(issue, include_children=include_children)
        except Exception:
            return None

    def list_tickets(
        self,
        status: str | None = None,
        labels: list[str] | None = None,
        limit: int = 50,
        project: str | None = None,
        parent: str | None = None,
        priority: str | None = None,
        assignee: str | None = None,
        unassigned: bool = False,
    ) -> list[Ticket]:
        """List tickets with optional filters.

        Args:
            status: Filter by status name (e.g., "In Progress", "Done")
            labels: Filter by label names
            limit: Maximum number of tickets to return
            project: Filter by project name
            parent: Filter by parent ticket identifier (shows sub-tasks)
            priority: Filter by priority ("urgent", "high", "medium", "low", "none")
            assignee: Filter by assignee name or "me" for current user
            unassigned: If True, show only unassigned tickets
        """
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
                    priority
                    assignee { name }
                    project { name }
                    parent { identifier }
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
        if project:
            # Need to resolve project name to ID
            project_id = self._get_project_id(project)
            if project_id:
                filter_obj["project"] = {"id": {"eq": project_id}}
        if parent:
            # Resolve parent identifier to UUID
            parent_ticket = self.get_ticket(parent)
            if parent_ticket:
                parent_uuid = parent_ticket.raw.get("id")
                if parent_uuid:
                    filter_obj["parent"] = {"id": {"eq": parent_uuid}}
        if priority:
            priority_int = PRIORITY_MAP.get(priority.lower())
            if priority_int is not None:
                filter_obj["priority"] = {"eq": priority_int}
        if unassigned:
            filter_obj["assignee"] = {"null": True}
        elif assignee:
            if assignee.lower() == "me":
                # Use viewer's ID
                viewer_id = self._get_viewer_id()
                if viewer_id:
                    filter_obj["assignee"] = {"id": {"eq": viewer_id}}
            else:
                # Search by name
                user_id = self._get_user_id_by_name(assignee)
                if user_id:
                    filter_obj["assignee"] = {"id": {"eq": user_id}}

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
        project: str | None = None,
        project_id: str | None = None,
        parent: str | None = None,
        parent_id: str | None = None,
        priority: str | None = None,
        assignee: str | None = None,
    ) -> Ticket:
        """Create a new ticket in Linear.

        Args:
            title: Ticket title
            description: Ticket description
            labels: List of label names to apply
            project: Project name to add ticket to
            project_id: Project UUID (alternative to name)
            parent: Parent ticket identifier (e.g., "PROJ-100") for sub-task
            parent_id: Parent ticket UUID (alternative to identifier)
            priority: Priority level ("urgent", "high", "medium", "low", "none")
            assignee: Assignee name or "me" for self-assignment
        """
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
                    priority
                    assignee { name }
                    project { id name }
                    parent { identifier title }
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
        if labels:
            label_ids = self._get_label_ids(self._team_id, labels)
            if label_ids:
                input_obj["labelIds"] = label_ids

        # Project support
        if project_id:
            input_obj["projectId"] = project_id
        elif project:
            resolved_project_id = self._get_project_id(project)
            if resolved_project_id:
                input_obj["projectId"] = resolved_project_id

        # Parent (sub-task) support
        if parent_id:
            input_obj["parentId"] = parent_id
        elif parent:
            parent_ticket = self.get_ticket(parent)
            if parent_ticket:
                parent_uuid = parent_ticket.raw.get("id")
                if parent_uuid:
                    input_obj["parentId"] = parent_uuid

        # Priority support
        if priority:
            priority_int = PRIORITY_MAP.get(priority.lower())
            if priority_int is not None:
                input_obj["priority"] = priority_int

        # Assignee support
        if assignee:
            if assignee.lower() == "me":
                viewer_id = self._get_viewer_id()
                if viewer_id:
                    input_obj["assigneeId"] = viewer_id
            else:
                user_id = self._get_user_id_by_name(assignee)
                if user_id:
                    input_obj["assigneeId"] = user_id

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
        project: str | None = None,
        project_id: str | None = None,
        remove_project: bool = False,
        parent: str | None = None,
        parent_id: str | None = None,
        remove_parent: bool = False,
        priority: str | None = None,
        assignee: str | None = None,
        unassign: bool = False,
    ) -> Ticket:
        """Update an existing ticket.

        Args:
            ticket_id: The ticket ID or identifier
            title: New title
            description: New description
            status: New status name
            labels: New labels (replaces existing)
            project: Project name to add ticket to
            project_id: Project UUID
            remove_project: If True, remove from current project
            parent: Parent ticket identifier for sub-task
            parent_id: Parent ticket UUID
            remove_parent: If True, remove parent (make standalone)
            priority: Priority level
            assignee: Assignee name or "me"
            unassign: If True, remove assignee
        """
        input_obj: dict[str, Any] = {}
        if title:
            input_obj["title"] = title
        if description:
            input_obj["description"] = description
        if status:
            # Resolve status name to workflow state ID
            issue = self.get_ticket(ticket_id)
            if not issue:
                raise RuntimeError(f"Ticket not found: {ticket_id}")
            team_id = (issue.raw.get("team") or {}).get("id") or self._team_id
            if not team_id:
                raise RuntimeError("Cannot resolve status: issue has no team")
            state_id = self._get_workflow_state_id(team_id, status)
            if not state_id:
                raise RuntimeError(
                    f"No workflow state named '{status}' for this team. "
                    "Check state name in Linear (e.g. Done, Canceled, In Progress)."
                )
            input_obj["stateId"] = state_id

        # Project support
        if remove_project:
            input_obj["projectId"] = None
        elif project_id:
            input_obj["projectId"] = project_id
        elif project:
            resolved_project_id = self._get_project_id(project)
            if resolved_project_id:
                input_obj["projectId"] = resolved_project_id

        # Parent (sub-task) support
        if remove_parent:
            input_obj["parentId"] = None
        elif parent_id:
            input_obj["parentId"] = parent_id
        elif parent:
            parent_ticket = self.get_ticket(parent)
            if parent_ticket:
                parent_uuid = parent_ticket.raw.get("id")
                if parent_uuid:
                    input_obj["parentId"] = parent_uuid

        # Priority support
        if priority:
            priority_int = PRIORITY_MAP.get(priority.lower())
            if priority_int is not None:
                input_obj["priority"] = priority_int

        # Assignee support
        if unassign:
            input_obj["assigneeId"] = None
        elif assignee:
            if assignee.lower() == "me":
                viewer_id = self._get_viewer_id()
                if viewer_id:
                    input_obj["assigneeId"] = viewer_id
            else:
                user_id = self._get_user_id_by_name(assignee)
                if user_id:
                    input_obj["assigneeId"] = user_id

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
                    priority
                    assignee { name }
                    project { id name }
                    parent { identifier title }
                }
            }
        }
        """
        result = self._execute_query(mutation, {"id": ticket_id, "input": input_obj})
        issue = result.get("data", {}).get("issueUpdate", {}).get("issue")
        if not issue:
            raise RuntimeError("Failed to update ticket")
        return self._parse_issue(issue)

    def comment_ticket(self, ticket_id: str, body: str) -> None:
        """Add a comment to a Linear issue."""
        issue = self.get_ticket(ticket_id)
        if not issue:
            raise RuntimeError(f"Ticket not found: {ticket_id}")
        issue_uuid = issue.raw.get("id")
        if not issue_uuid:
            raise RuntimeError("Cannot comment: issue has no id")

        mutation = """
        mutation CreateComment($input: CommentCreateInput!) {
            commentCreate(input: $input) {
                success
                comment { id }
            }
        }
        """
        self._execute_query(
            mutation,
            {"input": {"issueId": issue_uuid, "body": body}},
        )

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

    def _get_label_ids(self, team_id: str | None, label_names: list[str]) -> list[str]:
        """Resolve label names to Linear label IDs for the team."""
        if not team_id or not label_names:
            return []
        query = """
        query TeamLabels($teamId: String!) {
            team(id: $teamId) {
                labels { nodes { id name } }
            }
        }
        """
        try:
            result = self._execute_query(query, {"teamId": team_id})
            nodes = result.get("data", {}).get("team", {}).get("labels", {}).get("nodes", [])
            name_to_id = {n.get("name", ""): n["id"] for n in nodes if n.get("id")}
            return [name_to_id[n] for n in label_names if n in name_to_id]
        except Exception:
            return []

    def list_labels(self) -> list[dict[str, str]]:
        """List all labels with their IDs for the configured team."""
        query = """
        query ListLabels($teamId: String) {
            issueLabels(filter: { team: { id: { eq: $teamId } } }, first: 100) {
                nodes {
                    id
                    name
                    color
                }
            }
        }
        """
        variables = {}
        if self._team_id:
            variables["teamId"] = self._team_id

        try:
            result = self._execute_query(query, variables if variables else None)
            nodes = result.get("data", {}).get("issueLabels", {}).get("nodes", [])
            return [
                {
                    "id": node.get("id", ""),
                    "name": node.get("name", ""),
                    "color": node.get("color", ""),
                }
                for node in nodes
            ]
        except Exception:
            return []

    def _get_workflow_state_id(self, team_id: str, state_name: str) -> str | None:
        """Resolve workflow state name to state ID for a team."""
        query = """
        query WorkflowStates($teamId: String!) {
            team(id: $teamId) {
                states {
                    nodes {
                        id
                        name
                    }
                }
            }
        }
        """
        try:
            result = self._execute_query(query, {"teamId": team_id})
            nodes = result.get("data", {}).get("team", {}).get("states", {}).get("nodes", [])
            for node in nodes:
                if node.get("name", "").lower() == state_name.lower():
                    return node.get("id")
            return None
        except Exception:
            return None

    def create_relation(
        self,
        blocker_id: str,
        blocked_id: str,
        relation_type: str = "blocks",
    ) -> bool:
        """Create a blocking relationship between two issues.

        Args:
            blocker_id: The issue that blocks (prerequisite)
            blocked_id: The issue that is blocked (dependent)
            relation_type: Type of relation ("blocks" or "related")

        Returns:
            True if relation was created successfully
        """
        # First resolve identifiers to UUIDs if needed
        blocker = self.get_ticket(blocker_id)
        blocked = self.get_ticket(blocked_id)

        if not blocker:
            raise RuntimeError(f"Ticket not found: {blocker_id}")
        if not blocked:
            raise RuntimeError(f"Ticket not found: {blocked_id}")

        blocker_uuid = blocker.raw.get("id")
        blocked_uuid = blocked.raw.get("id")

        if not blocker_uuid or not blocked_uuid:
            raise RuntimeError("Cannot create relation: missing issue UUIDs")

        mutation = """
        mutation CreateIssueRelation($input: IssueRelationCreateInput!) {
            issueRelationCreate(input: $input) {
                success
                issueRelation {
                    id
                    type
                }
            }
        }
        """

        input_obj = {
            "issueId": blocker_uuid,
            "relatedIssueId": blocked_uuid,
            "type": relation_type,
        }

        try:
            result = self._execute_query(mutation, {"input": input_obj})
            success = result.get("data", {}).get("issueRelationCreate", {}).get("success", False)
            return success
        except Exception as e:
            raise RuntimeError(f"Failed to create relation: {e}") from e

    def _parse_issue(self, issue: dict, include_children: bool = False) -> Ticket:
        """Parse a Linear issue into a Ticket."""
        state = issue.get("state") or {}
        assignee = issue.get("assignee") or {}
        project = issue.get("project") or {}
        parent = issue.get("parent") or {}

        # Parse children if present
        children: list[Ticket] = []
        if include_children and "children" in issue:
            children_nodes = issue.get("children", {}).get("nodes", [])
            children = [self._parse_issue(child) for child in children_nodes]

        return Ticket(
            id=issue.get("identifier", issue.get("id", "")),
            title=issue.get("title", ""),
            description=issue.get("description", ""),
            status=state.get("name", ""),
            labels=[label["name"] for label in issue.get("labels", {}).get("nodes", [])],
            url=issue.get("url", ""),
            raw=issue,
            priority=issue.get("priority"),
            assignee=assignee.get("name"),
            project=project.get("name"),
            project_id=project.get("id"),
            parent_id=parent.get("identifier"),
            parent_title=parent.get("title"),
            children=children,
        )

    # -------------------------------------------------------------------------
    # Project Management
    # -------------------------------------------------------------------------

    def list_projects(
        self,
        state: str | None = None,
        limit: int = 50,
    ) -> list[Project]:
        """List projects accessible to the team.

        Args:
            state: Filter by project state ("planned", "started", "completed", "canceled")
            limit: Maximum number of projects to return
        """
        query = """
        query ListProjects($first: Int!, $filter: ProjectFilter) {
            projects(first: $first, filter: $filter) {
                nodes {
                    id
                    name
                    description
                    state
                    url
                    startDate
                    targetDate
                }
            }
        }
        """
        filter_obj: dict[str, Any] = {}
        if self._team_id:
            filter_obj["accessibleTeams"] = {"id": {"eq": self._team_id}}
        if state:
            filter_obj["state"] = {"eq": state}

        variables: dict[str, Any] = {"first": limit}
        if filter_obj:
            variables["filter"] = filter_obj

        try:
            result = self._execute_query(query, variables)
            nodes = result.get("data", {}).get("projects", {}).get("nodes", [])
            return [self._parse_project(p) for p in nodes]
        except Exception:
            return []

    def get_project(self, project_id: str) -> Project | None:
        """Get a project by ID or name.

        Args:
            project_id: Project UUID or name
        """
        # Try by ID first
        query = """
        query GetProject($id: String!) {
            project(id: $id) {
                id
                name
                description
                state
                url
                startDate
                targetDate
            }
        }
        """
        try:
            result = self._execute_query(query, {"id": project_id})
            project = result.get("data", {}).get("project")
            if project:
                return self._parse_project(project)
        except Exception:
            pass

        # Try by name
        projects = self.list_projects()
        for p in projects:
            if p.name.lower() == project_id.lower():
                return p
        return None

    def create_project(
        self,
        name: str,
        description: str = "",
        state: str = "planned",
    ) -> Project:
        """Create a new project.

        Args:
            name: Project name
            description: Project description
            state: Initial state ("planned", "started", "completed", "canceled")
        """
        mutation = """
        mutation CreateProject($input: ProjectCreateInput!) {
            projectCreate(input: $input) {
                success
                project {
                    id
                    name
                    description
                    state
                    url
                }
            }
        }
        """
        input_obj: dict[str, Any] = {
            "name": name,
            "description": description,
            "state": state,
        }
        if self._team_id:
            input_obj["teamIds"] = [self._team_id]

        result = self._execute_query(mutation, {"input": input_obj})
        project = result.get("data", {}).get("projectCreate", {}).get("project")
        if not project:
            raise RuntimeError("Failed to create project")
        return self._parse_project(project)

    def _parse_project(self, project: dict) -> Project:
        """Parse a Linear project into a Project."""
        return Project(
            id=project.get("id", ""),
            name=project.get("name", ""),
            description=project.get("description", ""),
            state=project.get("state", ""),
            url=project.get("url", ""),
            raw=project,
        )

    def _get_project_id(self, project_name: str) -> str | None:
        """Resolve project name to ID."""
        projects = self.list_projects()
        for p in projects:
            if p.name.lower() == project_name.lower():
                return p.id
        return None

    # -------------------------------------------------------------------------
    # User Management (for assignee support)
    # -------------------------------------------------------------------------

    def _get_viewer_id(self) -> str | None:
        """Get the current authenticated user's ID."""
        query = """
        query {
            viewer {
                id
            }
        }
        """
        try:
            result = self._execute_query(query)
            return result.get("data", {}).get("viewer", {}).get("id")
        except Exception:
            return None

    def _get_user_id_by_name(self, name: str) -> str | None:
        """Find a user ID by name or email."""
        query = """
        query {
            users {
                nodes {
                    id
                    name
                    email
                    displayName
                }
            }
        }
        """
        try:
            result = self._execute_query(query)
            users = result.get("data", {}).get("users", {}).get("nodes", [])
            name_lower = name.lower()
            for user in users:
                if (
                    user.get("name", "").lower() == name_lower
                    or user.get("email", "").lower() == name_lower
                    or user.get("displayName", "").lower() == name_lower
                ):
                    return user.get("id")
            return None
        except Exception:
            return None

    def list_users(self) -> list[dict[str, str]]:
        """List all users in the organization."""
        query = """
        query {
            users {
                nodes {
                    id
                    name
                    email
                    displayName
                    active
                }
            }
        }
        """
        try:
            result = self._execute_query(query)
            users = result.get("data", {}).get("users", {}).get("nodes", [])
            return [
                {
                    "id": u.get("id", ""),
                    "name": u.get("name", ""),
                    "email": u.get("email", ""),
                    "display_name": u.get("displayName", ""),
                    "active": u.get("active", True),
                }
                for u in users
            ]
        except Exception:
            return []
