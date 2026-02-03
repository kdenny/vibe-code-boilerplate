---
description: Manage PromptVault prompts, snippets, and variables
allowed-tools: Bash, Read, Write, WebFetch
---

# /promptvault - Prompt Management

Manage prompts, snippets, and variables in PromptVault for LLM-powered applications.

## Subcommands

### scaffold
Interactive wizard to create prompts, snippets, and variables.

```
/promptvault scaffold
```

### validate
Validate that all prompts compile correctly with test variables.

```
/promptvault validate
/promptvault validate --prompt customer-support
```

### sync
Sync local prompt files to PromptVault.

```
/promptvault sync
/promptvault sync --file prompts/support.txt
```

### create
Create a new resource.

```
/promptvault create prompt "shortname" --description "..."
/promptvault create snippet "name" --content "..."
/promptvault create variable "name" --default "value"
```

## Instructions

When the user invokes `/promptvault`:

### For `scaffold`:

1. Check if `PROMPTVAULT_API_KEY` is set in environment or `.env.local`
2. If not set, guide user to get an API key from PromptVault settings
3. Ask what type of prompt they're creating:
   - Customer support
   - Content generation
   - Data extraction
   - Code assistance
   - Custom
4. Based on type, suggest common variables and snippets
5. Create resources via API:

```bash
# Create variable
curl -X POST https://prompt-vault-sand.vercel.app/api/variables \
  -H "X-API-Key: $PROMPTVAULT_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"name": "variable_name", "defaultValue": "default"}'

# Create snippet
curl -X POST https://prompt-vault-sand.vercel.app/api/snippets/public \
  -H "X-API-Key: $PROMPTVAULT_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"name": "snippet_name", "content": "Snippet content..."}'

# Create prompt
curl -X POST https://prompt-vault-sand.vercel.app/api/prompts/public \
  -H "X-API-Key: $PROMPTVAULT_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"shortname": "prompt-name", "content": "Prompt with {vars} and [snippets]"}'
```

### For `validate`:

1. List prompts to validate (all or specific)
2. For each prompt:
   - Fetch the prompt definition
   - Identify required variables
   - Compile with test values
   - Report success or errors

```bash
# Compile prompt
curl -X POST "https://prompt-vault-sand.vercel.app/api/prompts/public/{shortname}/compile" \
  -H "X-API-Key: $PROMPTVAULT_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"variables": {"var1": "test", "var2": "test"}}'
```

3. Output validation report:
```
Validation Results
==================
[PASS] customer-support - Compiled successfully
[PASS] summarize-article - Compiled successfully
[FAIL] data-extraction - Missing variable: schema_definition
```

### For `sync`:

1. Look for prompt files in common locations:
   - `prompts/`
   - `src/prompts/`
   - Files matching `*.prompt.txt`
2. Parse each file for prompt content
3. Extract variable references (`{var}`) and snippet references (`[snippet]`)
4. Create/update resources in PromptVault
5. Report sync results

### For `create`:

1. Validate the resource type (prompt, snippet, variable)
2. Make API call to create
3. Report success with resource URL

## Example Session

```
User: /promptvault scaffold

Claude: I'll help you scaffold prompts in PromptVault.

First, let me check if you have PromptVault configured...

✓ PROMPTVAULT_API_KEY found in .env.local

What type of prompt are you creating?
1. Customer support
2. Content generation
3. Data extraction
4. Code assistance
5. Custom

User: 1

Claude: Great! For a customer support prompt, I'll create:

**Variables:**
- `customer_name` - Customer's name
- `issue_type` - Type of issue (billing, technical, etc.)
- `context` - Additional context

**Snippets:**
- `company-context` - Your company description
- `support-guidelines` - Tone and policy guidelines

**Prompt:** `customer-support`

Let me create these now...

✓ Created variable: customer_name
✓ Created variable: issue_type
✓ Created variable: context
✓ Created snippet: company-context (you can edit at PromptVault)
✓ Created snippet: support-guidelines
✓ Created prompt: customer-support

Your prompt is ready! Edit the snippets in PromptVault to customize for your company.

To use in code:
```python
prompt = get_compiled_prompt("customer-support", {
    "customer_name": customer.name,
    "issue_type": "billing",
    "context": ticket.description
})
```
```

## Related

- `recipes/integrations/promptvault.md` - Full PromptVault documentation
- `recipes/security/secret-management.md` - Handling API keys
