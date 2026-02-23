# Effective Prompting for AI-Assisted Development

How to phrase requests to get the best results from Claude Code (or any AI coding assistant) working with this boilerplate.

## The Golden Rule

**Be specific about what, flexible about how.**

Tell the agent *what* you want to achieve and *why*, but let it figure out the implementation details.

## Good vs. Bad Prompts

### Bug Fixes

**Bad:** "Fix the login bug"

**Good:** "Fix the login bug: users with special characters (like @, #, &) in their password get a 500 error on POST /api/auth/login. The error is in the bcrypt comparison — the password isn't being encoded to UTF-8 before hashing."

**Why:** The good prompt tells Claude exactly where the bug is, what causes it, and what the expected behavior should be.

### New Features

**Bad:** "Add search"

**Good:** "Add full-text search to the /api/products endpoint. It should search product name and description fields, support partial matches, and return results sorted by relevance. Use the existing Postgres database (no need for Elasticsearch)."

**Why:** Specifies scope, behavior, and constraints.

### Refactoring

**Bad:** "Clean up the auth code"

**Good:** "Refactor the auth middleware to separate JWT validation from role-based access control. Currently both are in a single middleware function in src/middleware/auth.ts. Split into validateToken() and requireRole() so they can be composed independently."

**Why:** Defines the target architecture and the specific change.

## Prompt Patterns

### The Ticket Pattern

The most common and effective pattern:

```
Do ticket PROJ-123
```

This works because:
1. Claude reads the ticket details from Linear/Shortcut
2. The ticket has context, acceptance criteria, and scope
3. Work happens in an isolated worktree
4. A PR is opened when done

### The Context-First Pattern

```
In the payments module (src/payments/), add Stripe webhook handling
for the `invoice.payment_succeeded` event. We already have webhook
signature verification in src/payments/webhooks.ts — add a new
handler that updates the subscription status in our database.
```

Key elements:
- **Where:** `src/payments/`
- **What:** Stripe webhook handling
- **Context:** Verification already exists
- **Scope:** Specific event, specific action

### The Constraint Pattern

```
Add rate limiting to the API. Constraints:
- Use the existing Redis connection (config in src/config/redis.ts)
- 100 requests per minute per API key
- Return 429 with Retry-After header
- Don't rate-limit health check endpoints
- Add a bypass for internal service calls (X-Internal-Token header)
```

### The Example-Driven Pattern

```
Add input validation to the user registration endpoint.

Valid input example:
{
  "email": "user@example.com",
  "password": "Str0ngP@ss!",
  "name": "Jane Doe"
}

Should reject:
- Empty email or invalid format
- Password shorter than 8 chars or without mixed case
- Name longer than 100 chars or containing HTML
```

## Anti-Patterns

### Over-Specifying Implementation

**Bad:** "Create a file called src/utils/validator.ts. In it, export a function called validateEmail that takes a string parameter called email and returns a boolean. Use a regex pattern /^[a-zA-Z0-9...]$/."

**Better:** "Add email validation to the registration endpoint. Reject invalid email formats."

The agent knows how to write validation code — let it use the project's existing patterns.

### Asking Too Many Things at Once

**Bad:** "Add authentication, create a dashboard page, set up email notifications, and deploy to production."

**Better:** Create separate tickets for each, then: "Do ticket PROJ-101" (authentication first).

### Being Vague About Requirements

**Bad:** "Make it faster"

**Better:** "The /api/orders endpoint takes 3+ seconds for users with >1000 orders. Profile the database queries and add appropriate indexes."

## When to Intervene

Signs the agent is going down the wrong path:
- Creating files in unexpected locations
- Installing unnecessary dependencies
- Over-engineering (adding abstractions you didn't ask for)
- Modifying unrelated code

When this happens, be direct:
- "Stop. Don't modify src/config/ — that's not related to this task."
- "Use the existing UserService class instead of creating a new one."
- "Remove the abstraction layer you just added — just inline the logic."

## Review Workflow

After the agent opens a PR:
1. **Read the diff** — Don't just approve blindly
2. **Check for scope creep** — Did it modify files it shouldn't have?
3. **Verify tests** — Are they meaningful or just for coverage?
4. **Check for secrets** — No hardcoded values or exposed keys?
5. **Run locally** — Does it actually work?
