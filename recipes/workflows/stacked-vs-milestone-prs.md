# Stacked vs Milestone PRs

## When to Use This Recipe

Use this recipe when you need to:
- Break down large features into reviewable chunks
- Decide between stacked PRs and milestone-based approaches
- Manage dependencies between related PRs

## The Problem

Large PRs are:
- Hard to review (reviewer fatigue)
- Risky to merge (big blast radius)
- Slow to get feedback on
- Prone to merge conflicts

Solution: Break them into smaller, related PRs.

## Approach 1: Stacked PRs

### What They Are
Sequential PRs where each builds on the previous:

```
main
└── feature-part-1 (PR #1)
    └── feature-part-2 (PR #2)
        └── feature-part-3 (PR #3)
```

### When to Use
- Linear feature development
- Each part is useful on its own
- Clear sequential dependencies
- You want early review feedback

### Workflow

```bash
# Create first PR
git checkout -b PROJ-123-part1
# ... work ...
git push -u origin PROJ-123-part1
gh pr create --base main

# Create stacked PR
git checkout -b PROJ-123-part2  # Branches from part1
# ... work ...
git push -u origin PROJ-123-part2
gh pr create --base PROJ-123-part1  # Note: base is part1, not main

# After part1 merges, rebase part2
git checkout PROJ-123-part2
git rebase main
git push --force-with-lease
gh pr edit --base main  # Update PR base
```

### Pros
- Early review feedback
- Small, focused reviews
- Incremental merging
- Clear dependency chain

### Cons
- Rebasing required when earlier PRs merge
- More PR management overhead
- Reviewers need to understand the stack

## Approach 2: Milestone PRs

### What They Are
Parallel PRs that together complete a milestone:

```
main
├── feature-api (PR #1)
├── feature-ui (PR #2)
└── feature-tests (PR #3)
        ↓
    All merge together
```

### When to Use
- Parallel workstreams
- Different team members on each part
- Parts are independent until integration
- Feature flag protects unfinished work

### Workflow

```bash
# Each PR branches from main
git checkout main
git checkout -b PROJ-123-api
# ... work on API ...

git checkout main
git checkout -b PROJ-123-ui
# ... work on UI ...

# Use a milestone branch to integrate
git checkout main
git checkout -b PROJ-123-milestone
git merge PROJ-123-api
git merge PROJ-123-ui

# Or merge directly to main behind a feature flag
```

### Pros
- Parallel development
- Independent reviews
- No rebase chains
- Team can divide work

### Cons
- Integration risk at the end
- Feature flags needed
- More complex coordination

## Decision Matrix

| Situation | Recommendation |
|-----------|----------------|
| Solo developer, linear work | Stacked PRs |
| Multiple developers, parallel work | Milestone PRs |
| Unclear requirements, need feedback | Stacked PRs |
| Well-defined parts, tight deadline | Milestone PRs |
| Experimental feature | Stacked PRs |
| Critical feature, needs testing | Milestone PRs |

## Labeling and Tracking

### For Stacked PRs
```markdown
Title: [1/3] PROJ-123: Add data models

Part of a stack:
- [x] #101 - [1/3] Add data models (this PR)
- [ ] #102 - [2/3] Add API endpoints
- [ ] #103 - [3/3] Add UI components
```

### For Milestone PRs
```markdown
Title: PROJ-123: API for new feature (Milestone: User Auth)

This PR is part of the User Auth milestone:
- [ ] #101 - API endpoints (this PR)
- [ ] #102 - UI components
- [ ] #103 - Integration tests

All PRs must merge before feature goes live.
```

## Tools for Stacked PRs

### Graphite
```bash
# Create stack
gt create -m "Part 1: Add models"
# ... work ...
gt create -m "Part 2: Add API"
# ... work ...

# Update entire stack
gt sync
```

### Stacked PRs CLI (spr)
```bash
spr diff  # Create PR for each commit
spr update  # Update stack after changes
```

### Manual (with aliases)
```bash
# Add to .gitconfig
[alias]
    stack-rebase = "!f() { git rebase origin/main && git push --force-with-lease; }; f"
```

## Best Practices

1. **Label the stack** - Make dependencies clear
2. **Keep PRs small** - Under 400 lines changed
3. **Test each PR** - Don't rely on later PRs to fix issues
4. **Communicate** - Let reviewers know the big picture
5. **Feature flag** - Protect incomplete features

## Extension Points

- Add automated stack management
- Configure merge queue for stacks
- Implement milestone tracking in tickets
