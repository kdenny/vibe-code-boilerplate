# Asking Clarifying Questions

## When to Use This Recipe

Use this recipe when you need to:
- Understand when AI agents should ask for clarification
- Provide examples for agent prompting
- Define question-asking policies for your project

## The Problem

Agents that never ask questions make wrong assumptions.
Agents that always ask questions are annoying and slow.

The goal: Ask the right questions at the right time.

## When to Ask

### Always Ask When:
- Requirements are ambiguous
- Multiple valid interpretations exist
- Security/data implications are unclear
- The task would take >30 minutes if wrong
- Destructive operations are involved

### Never Ask When:
- The answer is in the codebase
- Standard patterns apply
- The question was answered earlier in context
- It's a trivial decision with easy reversal

## Good vs Bad Questions

### Bad: Too Vague
> "How should I implement this?"

### Good: Specific Options
> "For the user authentication, should I:
> 1. Use JWT with refresh tokens (more complex, better for mobile)
> 2. Use session cookies (simpler, standard for web)
> Which approach fits your needs?"

### Bad: Already Answered
> "What language is this project using?"

### Good: Clarifying Edge Cases
> "The spec says 'validate email addresses'. Should I:
> 1. Just check for @ symbol (fast, permissive)
> 2. Full RFC 5322 validation (strict, may reject valid emails)
> 3. Send verification email (most reliable, requires email service)"

### Bad: Obvious from Context
> "Should I use tabs or spaces?"

### Good: Highlighting Trade-offs
> "Implementing real-time updates. Options:
> 1. WebSockets - bidirectional, more complex
> 2. Server-Sent Events - simpler, one-way
> 3. Polling - simplest, higher latency
> What's acceptable latency for this feature?"

## Question Templates

### Architecture Decision
```
For [feature], there are [N] approaches:

1. [Option A]: [brief description]
   - Pros: [benefits]
   - Cons: [drawbacks]

2. [Option B]: [brief description]
   - Pros: [benefits]
   - Cons: [drawbacks]

Which direction should I take?
```

### Scope Clarification
```
The task mentions [X]. This could mean:
1. [Interpretation A] - [what this would involve]
2. [Interpretation B] - [what this would involve]

Which interpretation is correct?
```

### Missing Information
```
To implement [feature], I need to know:
- [Specific question 1]
- [Specific question 2]

Currently I'm assuming [assumption]. Is that correct?
```

## Response to Ambiguity

### Step 1: Check Context
- Re-read the original request
- Look at similar code in the project
- Check related documentation

### Step 2: Make Informed Assumption
- If confidence > 80%, proceed with note
- Document the assumption made
- Make it easy to change later

### Step 3: Ask If Still Unclear
- Provide options, not open-ended questions
- Explain implications of each option
- Suggest a default if you have a preference

## For Agent Developers

When building agents, configure question-asking:

```python
QUESTION_POLICY = {
    # Always ask about these
    "require_confirmation": [
        "database_schema_changes",
        "destructive_operations",
        "external_api_integration",
        "security_implementations",
    ],

    # Never ask about these
    "auto_decide": [
        "code_formatting",
        "import_ordering",
        "variable_naming",
    ],

    # Ask if uncertain
    "ask_if_uncertain": [
        "architecture_decisions",
        "library_choices",
        "testing_strategy",
    ],
}
```

## Extension Points

- Add domain-specific question policies
- Configure question frequency limits
- Implement question batching
