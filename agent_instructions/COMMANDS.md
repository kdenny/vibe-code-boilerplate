# Agent Commands Reference

These commands are available to AI agents working on this project.

## Setup

### doctor
Check project health and configuration.
**Usage**: `bin/vibe doctor`
**Examples:**
- `bin/vibe doctor`
- `bin/vibe doctor --verbose`

### setup
Run the setup wizard to configure your project.
**Usage**: `bin/vibe setup`
**Examples:**
- `bin/vibe setup`
- `bin/vibe setup --force`
- `bin/vibe setup --wizard tracker`

## Ticket Operations

### do
Start working on a ticket (creates worktree and branch).
**Usage**: `bin/vibe do <ticket-id>`
**Examples:**
- `bin/vibe do PROJ-123`
- `bin/vibe do 45`

### ticket list
List tickets from the tracker.
**Usage**: `bin/ticket list`
**Examples:**
- `bin/ticket list`
- `bin/ticket list --status "In Progress"`

### ticket get
Get details for a specific ticket.
**Usage**: `bin/ticket get <ticket-id>`
**Examples:**
- `bin/ticket get PROJ-123`

### ticket create
Create a new ticket. **A description is REQUIRED** — never create a ticket without one. **Labels are REQUIRED** — always include at least one type label and one area label. Use --parent to set a parent ticket for sub-tasks.
**Usage**: `bin/ticket create "<title>" --description "<description>" --label "<type>" --label "<area>"`
**Examples:**
- `bin/ticket create "Add user authentication" --description "Add OAuth2 login flow with Google and GitHub providers." --label Feature --label Backend`
- `bin/ticket create "Fix login bug" --description "Login form returns 500 when password contains special chars." --label Bug --label "High Risk" --label Frontend`
- `bin/ticket create "Add signup form" --description "Create the signup form component." --label Feature --label Frontend --parent PROJ-100`

### ticket update
Update a ticket's status, title, description, or labels.
**Usage**: `bin/ticket update <ticket-id> [OPTIONS]`
**Examples:**
- `bin/ticket update PROJ-123 --status "In Progress"`
- `bin/ticket update PROJ-123 --title "New title" --description "Updated description"`
- `bin/ticket update PROJ-123 --label Feature --label Backend`

### ticket close
Close a ticket (set status to Done or Canceled).
**Usage**: `bin/ticket close <ticket-id> [--reason canceled]`
**Examples:**
- `bin/ticket close PROJ-123`
- `bin/ticket close PROJ-123 --reason canceled`

### ticket comment
Add a comment to a ticket.
**Usage**: `bin/ticket comment <ticket-id> "<comment>"`
**Examples:**
- `bin/ticket comment PROJ-123 "PR opened, ready for review"`

### ticket relate
Link two tickets with a blocking relationship. The prerequisite ticket blocks the dependent ticket.
**Usage**: `bin/ticket relate <blocker-id> --blocks <dependent-id>`
**Examples:**
- `bin/ticket relate PROJ-101 --blocks PROJ-102`

### ticket labels
List all labels with their IDs.
**Usage**: `bin/ticket labels`
**Examples:**
- `bin/ticket labels`

### ticket projects
List all projects.
**Usage**: `bin/ticket projects`
**Examples:**
- `bin/ticket projects`

### ticket create-human-followup
Create a HUMAN-labeled follow-up ticket for deployment infrastructure that requires human action.
**Usage**: `bin/ticket create-human-followup [--parent <ticket-id>] [--files <file>...]`
**Examples:**
- `bin/ticket create-human-followup`
- `bin/ticket create-human-followup --parent PROJ-123`
- `bin/ticket create-human-followup --parent PROJ-123 --files fly.toml --files vercel.json`

## Pull Requests

### pr
Create a pull request for the current branch. PR titles must include the ticket reference.
**Usage**: `bin/vibe pr`
**Examples:**
- `bin/vibe pr`
- `bin/vibe pr --title "PROJ-123: Add feature X"`
- `bin/vibe pr --web`

## Design

### figma analyze
Analyze frontend codebase for design system context.
**Usage**: `bin/vibe figma analyze`
**Examples:**
- `bin/vibe figma analyze`
- `bin/vibe figma analyze --figma-context`
- `bin/vibe figma analyze --json`

## Agent Instructions

### generate-agent-instructions
Generate assistant-specific instruction files.
**Usage**: `bin/vibe generate-agent-instructions`
**Examples:**
- `bin/vibe generate-agent-instructions`
- `bin/vibe generate-agent-instructions --format cursor`
- `bin/vibe generate-agent-instructions --dry-run`
