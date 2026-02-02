# Ticket Audit and Grandfathering

## When to Use This Recipe

Use this recipe when you need to:
- Adopt this boilerplate on an existing project
- Handle pre-existing tickets that don't follow conventions
- Perform a ticket hygiene audit

## Current Status

**⚠️ Automated grandfathering is not yet implemented.**

This is tracked in GitHub issue #2.

## What is Grandfathering?

When adopting this boilerplate, your existing tickets may not follow the new conventions:
- Missing risk labels
- Non-standard branch naming
- Missing ticket references in old PRs

"Grandfathering" means accepting these tickets as valid while applying conventions to new work.

## Manual Grandfathering Process

### Step 1: Audit Existing Tickets

List all open tickets:
```bash
# If using Linear
bin/ticket list --status "In Progress"
bin/ticket list --status "Todo"
bin/ticket list --status "Backlog"
```

### Step 2: Identify Convention Gaps

For each ticket, check:
- [ ] Has a type label (Bug, Feature, etc.)
- [ ] Has a risk label (Low/Medium/High Risk)
- [ ] Has an area label (Frontend/Backend/Infra)
- [ ] Title follows format: "Verb + Object"

### Step 3: Document Grandfathered Tickets

Add to `.vibe/grandfathered_tickets.md`:

```markdown
## ENG-42
- **Original Title**: fix the thing
- **Date Grandfathered**: 2024-01-15
- **Reason**: Pre-dates label conventions
- **Notes**: Will add labels when next touched

## ENG-99
- **Original Title**: WIP new feature
- **Date Grandfathered**: 2024-01-15
- **Reason**: Branch uses non-standard naming
- **Notes**: Branch is `johns-feature`, keeping as-is
```

### Step 4: Apply Conventions Going Forward

For all new tickets:
1. Use the PR template
2. Add required labels
3. Follow branch naming
4. Include testing instructions

## Bulk Updates

### Add Missing Labels

In Linear, use bulk edit:
1. Filter to tickets without risk labels
2. Select all
3. Add "Low Risk" as default
4. Review and adjust individually

### Via API (when implemented)
```bash
# Future: Automated label application
bin/ticket audit --fix-labels
```

## Grace Period

Consider a grace period for adoption:

**Week 1-2:** Document only
- Identify gaps
- No enforcement

**Week 3-4:** Soft enforcement
- Remind on PRs missing labels
- Help add retroactively

**Week 5+:** Full enforcement
- PR checks require labels
- Block merges without ticket refs

## Reporting

Generate audit report:

```markdown
## Ticket Audit Report - 2024-01-15

### Summary
- Total open tickets: 47
- Missing type label: 12 (25%)
- Missing risk label: 23 (49%)
- Non-standard titles: 8 (17%)

### Grandfathered
- 5 tickets added to grandfathered list

### Actions Taken
- Added type labels to 12 tickets
- Added risk labels to 18 tickets (5 need review)

### Remaining Work
- 5 tickets need risk assessment
- 8 titles need cleanup
```

## Future Automation

When GitHub issue #2 is implemented:

```bash
# Scan for non-compliant tickets
bin/ticket audit

# Interactive grandfathering
bin/ticket grandfather ENG-42 --reason "Pre-dates conventions"

# Bulk apply defaults
bin/ticket audit --fix --default-risk "Low Risk"
```

## Best Practices

1. **Don't block existing work** - Grandfather rather than demand immediate fixes
2. **Set a cutoff date** - "All tickets after DATE must comply"
3. **Make it easy to comply** - Templates, defaults, automation
4. **Lead by example** - Core team follows conventions first
5. **Regular audits** - Monthly review of ticket hygiene

## Extension Points

- Add automated compliance checking
- Create audit dashboards
- Set up Slack notifications for non-compliant tickets
