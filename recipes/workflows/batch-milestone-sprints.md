# Batch Operations and Sprint Planning

How to manage multiple tickets as part of a sprint or milestone using labels.

## Planning a Sprint

### Step 1: Create Tickets

Create all tickets for the sprint, tagging them with a label:

```bash
bin/ticket create "Set up auth middleware" -d "JWT validation" -l "Feature,Backend,Medium Risk,Sprint-1"
bin/ticket create "Add login page" -d "Login form with validation" -l "Feature,Frontend,Medium Risk,Sprint-1"
bin/ticket create "Add user profile" -d "Profile page with edit" -l "Feature,Frontend,Low Risk,Sprint-1"
```

Or use batch creation from YAML (requires #185):

```yaml
# sprint-1-tickets.yaml
tickets:
  - title: "Set up auth middleware"
    description: "JWT validation and role-based access control"
    labels: [Feature, Backend, Medium Risk, Sprint-1]
    priority: high

  - title: "Add login page"
    description: "Login form with email/password validation"
    labels: [Feature, Frontend, Medium Risk, Sprint-1]

  - title: "Add user profile"
    description: "Profile page with edit capabilities"
    labels: [Feature, Frontend, Low Risk, Sprint-1]
```

```bash
bin/ticket batch create --from sprint-1-tickets.yaml
```

### Step 2: Set Up Dependencies

```bash
bin/ticket relate PROJ-201 --blocks PROJ-202  # Auth blocks login page
bin/ticket relate PROJ-202 --blocks PROJ-203  # Login blocks profile
```

### Step 3: Find Unblocked Work

```bash
bin/ticket list --label "Sprint-1" --status "Todo"
```

Work on unblocked tickets first (those not blocked by other tickets).

### Step 4: Work Through the Sprint

```bash
/do PROJ-201  # Start with the foundation ticket
# ... implement ...
/pr           # Open PR
# After merge:
/cleanup
/do PROJ-202  # Now unblocked
```

## Multi-Agent Parallel Execution

For independent tickets (no blocking relationships), multiple agents can work simultaneously:

```bash
# Terminal 1 (Agent A)
/do PROJ-205  # Error handling (independent)

# Terminal 2 (Agent B)
/do PROJ-208  # API docs (independent)
```

See `recipes/workflows/multi-agent-coordination.md` for details.

## Tracking Progress

```bash
# See sprint status
bin/ticket list --label "Sprint-1"

# Check what's still todo
bin/ticket list --label "Sprint-1" --status "Todo"

# Check what's in progress
bin/ticket list --label "Sprint-1" --status "In Progress"
```

## Handling Mid-Sprint Changes

If requirements change:
1. Update the existing ticket description
2. Add a comment explaining the change
3. If scope grows, split into a new ticket for the next sprint

If a ticket is no longer needed:
```bash
bin/ticket close PROJ-205 --cancel
```
