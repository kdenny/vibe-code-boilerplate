# PR Risk Assessment

## When to Use This Recipe

Use this recipe when you need to:
- Classify PRs by risk level
- Determine appropriate review requirements
- Guide testing and rollback planning

## Risk Levels

### Low Risk
Changes unlikely to cause issues in production.

**Characteristics:**
- Documentation updates
- Test-only changes
- Typo fixes
- Minor UI tweaks (non-critical paths)
- Dependency patch updates
- Code comments

**Review Requirements:**
- One reviewer
- Standard CI passing
- Can merge without manual testing

**Example:**
```markdown
## Risk: Low

Changes:
- Fixed typo in error message
- Updated README with new setup instructions
- Added unit tests for existing function

No production code logic changes.
```

### Medium Risk
Changes that could cause issues but are contained.

**Characteristics:**
- New features (behind feature flags)
- Bug fixes in non-critical paths
- Refactoring of isolated modules
- Minor dependency updates
- API changes (non-breaking)
- Configuration changes

**Review Requirements:**
- One or two reviewers
- CI passing with good test coverage
- Manual testing in staging recommended
- Rollback plan identified

**Example:**
```markdown
## Risk: Medium

Changes:
- Added new notification preferences endpoint
- Refactored email service (no behavior change)
- Updated authentication library

Testing:
- Unit tests added
- Tested in staging environment
- Rollback: Revert commit and redeploy
```

### High Risk
Changes that could significantly impact production.

**Characteristics:**
- Database migrations
- Authentication/authorization changes
- Payment processing changes
- Core business logic changes
- Infrastructure changes
- Breaking API changes
- Major dependency updates
- Performance-critical paths

**Review Requirements:**
- Two or more reviewers
- Security review (if auth/payment)
- Comprehensive test coverage
- Mandatory staging testing
- Detailed rollback plan
- Consider phased rollout

**Example:**
```markdown
## Risk: High

Changes:
- Modified user authentication flow
- Added new database migration
- Changed payment retry logic

Mitigation:
- Feature flag: `NEW_AUTH_FLOW`
- Database migration is additive (backward compatible)
- Tested with subset of staging users

Rollback Plan:
1. Disable feature flag
2. Run reverse migration (sql/rollback_20240101.sql)
3. Redeploy previous version

Monitoring:
- Watch auth failure rates
- Monitor payment success rates
- Alert if login latency > 2s
```

## Risk Assessment Checklist

Ask these questions to determine risk:

### Impact Questions
- [ ] Does this touch authentication/authorization?
- [ ] Does this modify payment/billing logic?
- [ ] Does this change database schema?
- [ ] Is this on a critical user path?
- [ ] Could this cause data loss?

### Scope Questions
- [ ] How many files changed?
- [ ] How many users affected?
- [ ] What's the blast radius if it fails?
- [ ] Is this easily reversible?

### Confidence Questions
- [ ] Is there good test coverage?
- [ ] Has this been tested in staging?
- [ ] Do we understand all the edge cases?
- [ ] Are dependencies well understood?

## Label Guidelines

| Risk Level | Changes Required | Testing Required |
|------------|-----------------|------------------|
| Low Risk | 1 reviewer | CI passing |
| Medium Risk | 1-2 reviewers | CI + staging |
| High Risk | 2+ reviewers | CI + staging + load testing |

## PR Template Integration

Add risk to your PR template:

```markdown
## Risk Assessment

- [ ] **Low Risk** - Docs, tests, typos
- [ ] **Medium Risk** - New features (flagged), refactoring
- [ ] **High Risk** - Auth, payments, data, infrastructure

<!-- For Medium/High Risk, fill out: -->

### Testing Performed
-

### Rollback Plan
-

### Monitoring
-
```

## GitHub Actions Integration

The PR policy workflow checks for risk labels:

```yaml
- name: Check risk label
  uses: actions/github-script@v7
  with:
    script: |
      const labels = context.payload.pull_request.labels;
      const hasRisk = labels.some(l =>
        ['Low Risk', 'Medium Risk', 'High Risk'].includes(l.name)
      );
      if (!hasRisk) {
        core.setFailed('PR must have a risk label');
      }
```

## Extension Points

- Add automated risk scoring based on files changed
- Require additional approvers for high risk
- Block high-risk merges without staging test
