# UAT (User Acceptance Testing) Workflow

Some teams require a manual testing step between "code merged" and "ticket closed." This ensures bugs aren't prematurely marked as done before a human verifies the fix in a deployed environment.

## Standard vs UAT Workflow

### Standard (default)

```
Backlog → In Progress → In Review → Deployed/Done
                         (PR open)   (PR merged)
```

The PR merge marks the ticket as complete. Simple and fast.

### UAT Workflow (optional)

```
Backlog → In Progress → In Review → To Test → Done
                         (PR open)   (merged)  (manual)
```

After merge, the ticket moves to **To Test** (or **QA**, **Staging**, etc.). A human verifies the change works in production/staging, then manually moves it to **Done**.

## When to Use UAT

**Use UAT when:**
- Bug fixes need verification before closing
- Features require manual testing in production
- Stakeholders need to sign off on changes
- Compliance requires documented acceptance

**Skip UAT when:**
- Changes are low-risk (docs, config)
- Automated tests provide sufficient coverage
- Fast iteration is more important than manual verification
- Solo developer with immediate production access

## Configuration

### 1. Linear Workflow States

Ensure your Linear team has the required states:
1. **To Test** (or **QA**, **Staging**) - between In Review and Done
2. **Done** - final completed state

### 2. GitHub Repository Variable

Add a variable for the post-merge state:

1. Go to **Settings → Secrets and variables → Actions → Variables**
2. Click **New repository variable**
3. Name: `LINEAR_DEPLOYED_STATE`
4. Value: `To Test` (or your equivalent state name)

This overrides the default "Deployed" state used by `pr-merged.yml`.

### 3. Local Config (optional)

In `.vibe/config.json`, document the UAT state for local scripts:

```json
{
  "tracker": {
    "type": "linear",
    "config": {
      "deployed_state": "To Test",
      "done_state": "Done"
    }
  }
}
```

## Workflow in Practice

### Automated (PR Events)

1. **PR opened** → Ticket moves to **In Review** (automatic via `pr-opened.yml`)
2. **PR merged** → Ticket moves to **To Test** (automatic via `pr-merged.yml` with `LINEAR_DEPLOYED_STATE=To Test`)

### Manual (Human Verification)

3. Human tests the change in production/staging
4. If it works: Human moves ticket to **Done** in Linear
5. If it fails: Human reopens or creates a new bug ticket

### CLI Fallback

If you need to manually update ticket status:

```bash
# Move to To Test
bin/ticket update PROJ-123 --status "To Test"

# Move to Done after verification
bin/ticket update PROJ-123 --status "Done"
```

## Multiple Environments

For teams with staging → production pipelines:

```
In Review → Staging → Production → Done
             (merge)   (deploy)    (verify)
```

Consider:
- `LINEAR_DEPLOYED_STATE=Staging` on merge
- Separate deployment workflow that updates to `Production`
- Manual move to `Done` after production verification

## Notifications

To remind testers when tickets hit "To Test":

1. **Linear Automations**: Create a Linear automation that posts to Slack when tickets enter "To Test"
2. **GitHub Actions**: Add a step to `pr-merged.yml` that pings a channel
3. **Linear Views**: Create a view filtering for "To Test" tickets

## Example: Bug Fix UAT

1. Bug reported: `PROJ-456 - Login button doesn't work on mobile`
2. Developer creates worktree: `bin/vibe do PROJ-456`
3. Fix implemented, PR opened → Ticket: **In Review**
4. PR reviewed and merged → Ticket: **To Test**
5. QA tests on staging/production mobile device
6. Verified fixed → QA moves ticket to **Done**

If the bug isn't fixed:
- QA adds comment explaining the failure
- QA either reopens the ticket or creates a follow-up
- Developer investigates and creates another PR

## Metrics

UAT workflows enable tracking:
- **Time in To Test**: How long items wait for verification
- **Reopen rate**: How often items fail UAT
- **Bottlenecks**: If "To Test" queue grows, testing capacity is insufficient

## Related

- [pr-merge-linear.md](pr-merge-linear.md) - How PR merge triggers state updates
- [pr-opened-linear.md](pr-opened-linear.md) - How PR open triggers In Review
- [linear-setup.md](../tickets/linear-setup.md) - Initial Linear configuration
