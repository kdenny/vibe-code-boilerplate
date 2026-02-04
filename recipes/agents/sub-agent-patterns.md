# Sub-Agent Patterns

How to break complex tasks into specialized components using Claude Code's Task tool.

## When to Use Sub-Agents

**Use sub-agents when:**
- A task requires deep expertise in multiple domains (research + implementation + testing)
- You need parallel exploration of different approaches
- The task is complex enough that a single context window struggles
- You want to isolate risky operations (exploratory code changes)

**Don't use sub-agents when:**
- The task is straightforward and fits in one context
- Communication overhead would exceed benefits
- The sub-tasks are tightly coupled and can't be parallelized

## The Task Tool

Claude Code's Task tool spawns specialized agents for specific work. Each agent runs in its own context with focused instructions.

### Available Agent Types

| Type | Purpose | Best For |
|------|---------|----------|
| `Explore` | Codebase exploration | Finding files, understanding structure |
| `Plan` | Architecture and planning | Designing implementation approaches |
| `Bash` | Command execution | Git operations, running tests |
| `general-purpose` | Multi-step tasks | Research, complex searches |

### Basic Pattern

```
User: "Add authentication to this app"

Main Agent:
1. Spawn Explore agent → "Find existing auth patterns in codebase"
2. Spawn Plan agent → "Design auth implementation approach"
3. Implement based on plan
4. Spawn Bash agent → "Run tests"
```

## Common Workflows

### Feature Implementation

```
1. RESEARCH (Explore agent)
   - Find related code
   - Understand existing patterns
   - Identify dependencies

2. PLAN (Plan agent)
   - Design approach
   - Identify files to change
   - Consider edge cases

3. IMPLEMENT (main agent)
   - Make changes
   - Follow the plan

4. VERIFY (Bash agent)
   - Run tests
   - Check linting
```

### Bug Investigation

```
1. REPRODUCE (Bash agent)
   - Run failing tests
   - Capture error output

2. DIAGNOSE (Explore agent)
   - Search for error patterns
   - Find related code
   - Check recent changes

3. FIX (main agent)
   - Implement fix
   - Add regression test

4. VERIFY (Bash agent)
   - Confirm fix works
   - Check no regressions
```

### Refactoring

```
1. ANALYZE (Explore agent)
   - Find all usages
   - Map dependencies
   - Identify test coverage

2. PLAN (Plan agent)
   - Design new structure
   - Plan migration steps
   - Identify breaking changes

3. EXECUTE (main agent)
   - Refactor incrementally
   - Update tests along the way

4. VALIDATE (Bash agent)
   - Run full test suite
   - Check for type errors
```

## Context Passing

### What to Include in Sub-Agent Prompts

**Good context:**
```
"Find all files that import UserService and check how authentication
is handled. The codebase uses Next.js 14 with App Router."
```

**Bad context (too vague):**
```
"Look at the auth stuff"
```

### Passing Results Back

Sub-agents return a summary. Use that summary in subsequent work:

```
Main Agent receives:
  "Found 5 files importing UserService. Authentication uses JWT tokens
   stored in cookies. Main auth logic is in lib/auth/session.ts."

Main Agent then:
  1. Reads lib/auth/session.ts
  2. Implements changes following discovered pattern
```

## Best Practices

### 1. Keep Sub-Tasks Focused

Each sub-agent should have ONE clear objective:
- "Find all React components using the old Button API"
- "Create a migration plan for the database schema"
- "Run the test suite and report failures"

### 2. Use Explore for Discovery

Before implementing, spawn an Explore agent to understand the codebase:
```
"Search for existing error handling patterns.
Look for try/catch usage, error boundaries, and custom error classes."
```

### 3. Use Plan for Design

For non-trivial changes, get a plan first:
```
"Design an approach to add rate limiting. Consider:
- Where to add middleware
- How to configure limits
- How to handle limit exceeded
- How to test"
```

### 4. Verify with Bash

After making changes, verify with Bash:
```
"Run: npm test && npm run lint && npm run typecheck"
```

### 5. Don't Over-Parallelize

Sub-agents have overhead. Only parallelize when:
- Tasks are truly independent
- Each task takes significant time
- Results don't depend on each other

## Anti-Patterns

### 1. Spawning Agents for Simple Lookups

**Wrong:**
```
Spawn agent to find config file
```

**Right:**
```
Use Glob to find config file directly
```

### 2. Passing Incomplete Context

**Wrong:**
```
"Fix the auth bug"
```

**Right:**
```
"Fix the authentication bug where JWT tokens expire during long sessions.
The error 'TokenExpiredError' appears in lib/auth/verify.ts:45"
```

### 3. Sequential When Parallel is Possible

**Wrong:**
```
1. Research auth patterns (wait)
2. Research database patterns (wait)
3. Research API patterns (wait)
```

**Right:**
```
Spawn 3 agents in parallel:
- Research auth patterns
- Research database patterns
- Research API patterns
Combine results
```

### 4. Not Using Results

**Wrong:**
```
Spawn explore agent
Ignore results
Implement from scratch
```

**Right:**
```
Spawn explore agent
Review findings
Implement based on discovered patterns
```

## Integration with Worktrees

Sub-agents share the same worktree as the main agent. This means:
- All agents see the same file state
- Changes made by one agent are visible to others
- Lock files and temporary state are shared

For isolated exploration (testing destructive changes):
1. Create a separate worktree for exploration
2. Have sub-agent work there
3. Cherry-pick changes if successful

## Example: Full Feature Implementation

Task: "Add password reset functionality"

```
1. Explore Agent: "Find existing email sending code and auth patterns"
   → Returns: "Email via SendGrid in lib/email/. Auth uses JWT in lib/auth/."

2. Plan Agent: "Design password reset flow given:
   - Email via SendGrid
   - JWT authentication
   - Next.js API routes"
   → Returns: Step-by-step implementation plan

3. Main Agent: Implements plan
   - Creates /api/auth/forgot-password
   - Creates /api/auth/reset-password
   - Adds email template

4. Bash Agent: "Run tests related to auth"
   → Returns: Test results

5. Main Agent: Opens PR with all changes
```

## See Also

- `recipes/workflows/multi-agent-coordination.md` - Coordinating multiple human-controlled agents
- `recipes/agents/asking-clarifying-questions.md` - When to ask vs. proceed
- Claude Code documentation on Task tool
