# Documenting Alternatives Analysis

## When to Use This Recipe

Use alternatives analysis when you need to:
- Choose between multiple technical options
- Justify a decision to stakeholders
- Document rejected options for future reference
- Compare tools, frameworks, or approaches systematically

## Why Document Alternatives?

Without documentation:
- Future developers ask "why didn't we use X?"
- The same options get re-evaluated repeatedly
- Institutional knowledge is lost when people leave
- Decisions appear arbitrary

## Analysis Template

### Option Overview

| Criteria | Option A | Option B | Option C |
|----------|----------|----------|----------|
| Learning curve | Low | Medium | High |
| Maintenance burden | Medium | Low | Low |
| Community support | High | High | Medium |
| Cost | Free | $$/seat | Free |
| Team familiarity | High | Low | Medium |

### Detailed Comparison

For each option, document:

1. **What it is** - Brief description
2. **Pros** - Advantages for your use case
3. **Cons** - Disadvantages for your use case
4. **Risks** - What could go wrong
5. **Effort** - Implementation and maintenance effort

### Decision Matrix

Weight criteria by importance (1-5) and score each option (1-5):

| Criteria | Weight | Option A | Option B | Option C |
|----------|--------|----------|----------|----------|
| Performance | 5 | 4 (20) | 5 (25) | 3 (15) |
| Ease of use | 4 | 5 (20) | 3 (12) | 4 (16) |
| Cost | 3 | 5 (15) | 2 (6) | 5 (15) |
| **Total** | | **55** | **43** | **46** |

## Example: Database Selection

### Context
Need a database for a new web application with:
- Moderate read/write load
- Complex queries
- JSON data storage
- Budget constraints

### Options Considered

**Option A: PostgreSQL**
- Pros: Powerful, reliable, free, excellent JSON support
- Cons: Self-managed complexity, requires tuning
- Effort: Medium setup, ongoing maintenance

**Option B: Supabase (Managed Postgres)**
- Pros: Easy setup, real-time, auth included
- Cons: Vendor lock-in, cost at scale
- Effort: Low setup, minimal maintenance

**Option C: MongoDB**
- Pros: Flexible schema, horizontal scaling
- Cons: Less suited for complex queries, consistency trade-offs
- Effort: Medium setup, different mental model

### Decision
Selected: **Supabase**

### Reasoning
- Faster time to market
- Team can focus on product, not infrastructure
- Cost acceptable for projected scale
- Easy migration path to self-hosted if needed

### Rejected Options

**PostgreSQL (self-hosted)**: Would require dedicated DevOps time we don't have. Revisit if we outgrow Supabase.

**MongoDB**: Team more familiar with SQL. No clear advantage for our use case.

## Best Practices

1. **Be honest about trade-offs** - Every option has downsides
2. **Consider total cost of ownership** - Not just upfront cost
3. **Weight criteria explicitly** - Makes priorities clear
4. **Document rejected options** - Future you will thank you
5. **Include context** - Decisions may change if context changes

## Extension Points

- Integrate with ADR process
- Add team voting mechanisms
- Include stakeholder sign-off requirements
