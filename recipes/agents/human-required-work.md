# HUMAN Label Usage

## When to Use This Recipe

Use this recipe when you need to:
- Understand when to mark tickets as requiring human intervention
- Define boundaries for AI agent capabilities
- Ensure critical decisions get human review

## The HUMAN Label

The `HUMAN` label marks tickets or tasks that require human decision-making, expertise, or action that an AI agent cannot or should not perform.

## When to Apply HUMAN

### Security Decisions
- Production secrets rotation
- Access control changes
- Security incident response
- Audit log review

### Financial/Legal
- Payment integration testing with real money
- Terms of service changes
- Licensing decisions
- Contract-related code changes

### External Communications
- User-facing error messages (tone/branding)
- Email templates to customers
- Public documentation changes
- API deprecation notices

### Architecture Decisions
- Major framework migrations
- Database technology changes
- Infrastructure provider switches
- Breaking API changes

### Subjective Judgment
- UI/UX design decisions
- Brand voice and copy
- Feature prioritization
- Trade-off decisions without clear criteria

### Access-Required Tasks
- Tasks requiring credentials the agent doesn't have
- Physical access requirements
- Third-party account management
- Manual verification steps

## How to Use HUMAN

### In Tickets
```markdown
Title: [HUMAN] Review and approve new authentication flow

The authentication flow changes are implemented. Requires human review for:
- Security implications
- UX flow approval
- Error message copy
```

### In Code Comments
```python
# HUMAN: This retry logic needs review. Is 5 retries appropriate
# for our use case? Too many could mask underlying issues.
```

### In PR Descriptions
```markdown
## Requires Human Review

- [ ] Security team: Review token handling
- [ ] Product: Approve user-facing messages
- [ ] Legal: Verify GDPR compliance of data handling
```

## Workflow with HUMAN Label

```
Agent creates ticket with HUMAN label
         ↓
Ticket appears in human review queue
         ↓
Human makes decision or takes action
         ↓
Human removes HUMAN label and updates ticket
         ↓
Agent can proceed with implementation
```

## Agent Behavior

When an agent encounters a HUMAN-labeled task:

1. **Don't attempt to complete it** - Wait for human input
2. **Provide context** - Explain why human input is needed
3. **Suggest options** - If possible, provide choices for human
4. **Continue other work** - Work on non-blocked tasks

### Example Agent Response
```
This task requires human decision-making:

Reason: Security implications of new API scope

Options I've identified:
1. Read-only scope (safer, limited functionality)
2. Read-write scope (full functionality, higher risk)
3. Separate scopes per feature (complex, most flexible)

I'll proceed with other tasks while awaiting your decision.
```

## Review Queue

Maintain a view of HUMAN-labeled items:

```bash
# In Linear
Filter: Label = HUMAN AND Status != Done

# In GitHub
Label: HUMAN
is:open
```

## Best Practices

1. **Be specific** - Say exactly what human input is needed
2. **Provide context** - Explain why agent can't proceed
3. **Suggest next steps** - Make it easy for human to act
4. **Time-box reviews** - Don't let HUMAN items languish
5. **Document decisions** - Record why decisions were made

## Anti-Patterns

### Overuse
Don't mark everything as HUMAN. Agents should:
- Make routine code decisions
- Choose between equivalent options
- Handle standard patterns

### Underuse
Do mark tasks HUMAN when:
- You're uncertain about security implications
- The decision is irreversible
- Business logic requires human judgment

## Extension Points

- Add team-specific HUMAN triggers
- Implement escalation timelines
- Set up HUMAN item notifications
