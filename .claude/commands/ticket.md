---
description: Manage tickets in Linear or Shortcut (list, get, create, update)
---

# /ticket - Ticket operations

Manage tickets in Linear or Shortcut.

## Usage

```
/ticket list
/ticket list --status "In Progress"
/ticket get PROJ-123
/ticket create "Add user authentication" --description "Add OAuth2 login flow"
/ticket update PROJ-123 --status "Done"
```

## Subcommands

### list
List tickets from the configured tracker.

```
/ticket list                    # All open tickets
/ticket list --status "Todo"    # Filter by status
/ticket list --label "Bug"      # Filter by label
```

### get
Get details for a specific ticket.

```
/ticket get PROJ-123
```

Shows: title, description, status, labels, assignee, blocking relationships.

### create
Create a new ticket. **A description is REQUIRED** — never create a ticket without one.

**IMPORTANT:** The description must include: what the problem/feature is, root cause (for bugs), affected code, and acceptance criteria.

```
/ticket create "Title" --description "Detailed description of the issue" --label Feature --label Backend
```

### update
Update an existing ticket.

```
/ticket update PROJ-123 --status "In Progress"
/ticket update PROJ-123 --add-label "High Risk"
```

### labels
List available labels with their IDs.

```
/ticket labels
```

## Instructions

When the user invokes `/ticket <subcommand>`:

1. Map to the appropriate `bin/ticket` command
2. Run the command and capture output
3. Format the output nicely for the user
4. For `create`, confirm the ticket ID created
5. For errors, suggest fixes (e.g., "Run `bin/vibe setup` to configure tracker")

## Examples

```bash
# List tickets
bin/ticket list

# Get ticket details
bin/ticket get PROJ-123

# Create ticket (description is required, use --label for each label)
bin/ticket create "Add login button" --description "Add login button to header nav" --label Feature --label Frontend

# Update status
bin/ticket update PROJ-123 --status "Done"
```
