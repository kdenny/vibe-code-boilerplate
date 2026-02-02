# Architecture Decision Records (ADRs)

## When to Use This Recipe

Use ADRs when you need to:
- Document significant architectural decisions
- Record the context and reasoning behind technical choices
- Create a historical record for future team members
- Justify trade-offs between competing approaches

## What is an ADR?

An Architecture Decision Record (ADR) is a document that captures an important architectural decision along with its context and consequences.

## When to Write an ADR

Write an ADR when:
- Choosing between multiple frameworks, libraries, or tools
- Defining system-wide patterns or conventions
- Making infrastructure decisions
- Changing existing architectural patterns
- Making decisions that are hard or expensive to reverse

Don't write an ADR for:
- Routine bug fixes
- Minor refactoring
- Feature implementations that follow existing patterns

## ADR Format

Use the template at `technical_docs/adr-template.md`. Key sections:

### Title
- Use format: `ADR-{number}: {decision title}`
- Keep it concise but descriptive

### Status
- **Proposed**: Under discussion
- **Accepted**: Approved and implemented
- **Deprecated**: Superseded by another decision
- **Rejected**: Considered but not adopted

### Context
- What is the issue?
- What constraints exist?
- What forces are at play?

### Decision
- What is the change being made?
- State it clearly and directly

### Consequences
- What are the positive outcomes?
- What are the negative outcomes?
- What new problems does this create?

## Example ADR

```markdown
# ADR-001: Use Linear for Ticket Tracking

## Status
Accepted

## Context
We need a ticket tracking system that:
- Integrates well with GitHub
- Has a good API for automation
- Supports labels and custom fields
- The team is familiar with

Options considered:
- Linear
- Shortcut
- GitHub Issues
- Jira

## Decision
We will use Linear as our ticket tracking system.

## Consequences
### Positive
- Excellent API for automation
- Good GitHub integration
- Team already has experience

### Negative
- Additional tool to manage
- Cost per seat
- Shortcut users will need to adapt
```

## Best Practices

1. **One decision per ADR** - Keep them focused
2. **Immutable history** - Don't modify accepted ADRs; create new ones
3. **Link related ADRs** - Reference previous decisions
4. **Include alternatives** - Show what else was considered
5. **Date your decisions** - Include when the decision was made

## Extension Points

This recipe can be extended for:
- Team-specific ADR templates
- Automated ADR numbering
- ADR review workflows
