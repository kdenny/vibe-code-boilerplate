# Business Validation Before Building

This guide covers how to use the `/assess` skill to validate your app idea before investing significant development time.

## The Problem

Vibe coding makes it dangerously easy to build things fast. But building the wrong thing fast is still building the wrong thing. Common mistakes:

1. **Building something that already exists** (and is better)
2. **Solving a problem no one actually has**
3. **No differentiation** from existing solutions
4. **Building when buying/using existing tools is better**

## The Solution: `/assess`

The `/assess` skill is an interactive business advisor that:
- Asks probing questions about your idea
- Researches competitors using web search
- Identifies market gaps and opportunities
- Provides honest recommendations

## When to Use

### Always Use `/assess` For

- **New app ideas** - Before creating the first ticket
- **Major pivots** - When changing direction significantly
- **"Better X" ideas** - When you think you can beat existing solutions
- **Scratching your own itch** - Personal tools that might become products

### Skip `/assess` For

- **Learning projects** - Building to learn, not to ship
- **Client work** - Requirements already defined
- **Bug fixes** - Existing validated product
- **OSS contributions** - Contributing to established projects

## The Assessment Flow

### Phase 1: Idea Clarity

The advisor asks:
1. What are you building?
2. What problem does this solve?
3. Who experiences this problem?
4. Why are you building this?

**Tip**: If you can't clearly articulate the problem, that's a signal to think more before building.

### Phase 2: Competitive Research

With your consent, the advisor searches for:
- Direct competitors (same problem, same solution)
- Indirect competitors (same problem, different solution)
- Adjacent products (related space)

**What good research reveals:**
- Market validation (others are solving this = real problem)
- Feature gaps in existing solutions
- Pricing benchmarks
- User complaints about competitors

### Phase 3: Differentiation Check

Hard questions:
- What's your unfair advantage?
- Why would someone switch from [competitor]?
- What makes this 10x better, not 10% better?

**Common weak answers:**
- "It'll be simpler" - Simplicity alone rarely wins
- "Better UX" - Subjective and hard to sustain
- "It's free" - Not a business model
- "AI-powered" - Everyone says this now

**Strong answers:**
- Unique data or distribution advantage
- Specific underserved niche
- Technical breakthrough enabling new capability
- Domain expertise competitors lack

### Phase 4: Recommendation

The advisor provides one of:

**PROCEED** - Clear opportunity identified
- Specific differentiators articulated
- Market gap validated
- Risks acknowledged

**RECONSIDER** - Concerns need addressing
- Existing solutions seem adequate
- Differentiation unclear
- Questions to answer before proceeding

**PIVOT** - Different angle suggested
- Original idea too crowded
- Related opportunity identified
- Niche focus recommended

## After Assessment

### If PROCEED

1. Save the competitive analysis: `docs/competitive-analysis.md`
2. Use insights to inform your PRD
3. Reference competitors when making design decisions
4. Revisit assessment quarterly as market evolves

### If RECONSIDER

1. Answer the open questions before building
2. Talk to potential users (not friends/family)
3. Consider: Could you build a plugin/extension instead?
4. Re-run `/assess` after gathering more information

### If PIVOT

1. Explore the suggested alternatives
2. Run `/assess` on the pivoted idea
3. Consider: Is the core insight still valid?

## Using on Existing Projects

For projects you've already started (with Cursor, another editor, etc.):

```
/assess

"I see you've built a recipe management app. Let me understand the current
state and check if the market has changed..."
```

The advisor will:
1. Read your codebase to understand what exists
2. Research current competitive landscape
3. Compare your features to competitors
4. Recommend: double down, pivot, or consider sunsetting

## Saving Your Analysis

The advisor can save findings to `docs/competitive-analysis.md`:

```markdown
# Competitive Analysis: [Your App]

## Problem Statement
[What you're solving]

## Target User
[Who you're building for]

## Competitive Landscape

| Product | Price | Key Features | Strengths | Weaknesses |
|---------|-------|--------------|-----------|------------|
| ...     | ...   | ...          | ...       | ...        |

## Your Differentiation
[What makes you different]

## Recommendation
[Proceed / Reconsider / Pivot]

## Open Questions
[Things to validate]

## Research Date
[When this was done]
```

## Tips for Honest Assessment

1. **Don't ask leading questions** - "Isn't my idea great?" → "What are the risks?"
2. **Welcome bad news** - Better to know now than after building
3. **Be specific about users** - "Developers" is too broad
4. **Question your assumptions** - Especially if you're the target user
5. **Consider opportunity cost** - What else could you build instead?

## Related

- [Creating Tickets](../tickets/creating-tickets.md) - After validation
- [ADR Guide](../architecture/adr-guide.md) - Documenting decisions
- [README Maintenance](./readme-maintenance.md) - Project documentation
