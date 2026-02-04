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
Create a new ticket.
**Usage**: `bin/ticket create "<title>"`
**Examples:**
- `bin/ticket create "Add user authentication"`
- `bin/ticket create "Fix login bug" --label Bug --label "High Risk"`

## Pull Requests

### pr
Create a pull request for the current branch.
**Usage**: `bin/vibe pr`
**Examples:**
- `bin/vibe pr`
- `bin/vibe pr --title "Add feature X"`
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
