# PromptVault Integration

[PromptVault](https://prompt-vault-sand.vercel.app) is a prompt management platform for centralized, version-controlled AI/LLM prompts. It enables teams to share prompt templates, variables, and snippets across applications.

## When to Use PromptVault

Use PromptVault when your application:
- Makes API calls to LLMs (OpenAI, Anthropic, etc.)
- Has prompts that evolve over time
- Shares context or snippets across multiple prompts
- Needs version control for prompts
- Wants to separate prompt engineering from code

## Core Concepts

### Prompts
Complete prompt templates with placeholders for variables and snippets.

```
You are a helpful assistant for {company_name}.

[system_context]

User query: {user_query}
```

### Variables
Runtime values injected into prompts using `{variable_name}` syntax.

### Snippets
Reusable prompt fragments shared across prompts, referenced as `[snippet_name]`.

### Response Schemas
JSON Schema definitions for validating structured LLM responses.

## Setup

### 1. Get API Key

1. Sign up at [PromptVault](https://prompt-vault-sand.vercel.app)
2. Go to **Settings → API Keys**
3. Click **Generate Key**
4. Copy the key

### 2. Configure Environment

```bash
# Add to .env.local (gitignored)
echo "PROMPTVAULT_API_KEY=your-key-here" >> .env.local
```

### 3. Run Setup Wizard

```bash
bin/vibe setup
```

When prompted about PromptVault, select **Yes** to enable integration.

Or run the specific wizard:
```bash
bin/vibe setup --wizard promptvault
```

### 4. Verify Setup

```bash
bin/vibe doctor
# Should show: [PASS] PromptVault configured
```

## Usage

### Creating Prompts via CLI

```bash
# Scaffold a new prompt
bin/vibe promptvault create-prompt "customer-support" \
  --description "Handle customer inquiries" \
  --variables "customer_name,issue_type,context"

# Create a snippet
bin/vibe promptvault create-snippet "company-context" \
  --content "You work for Acme Corp, a leading widget manufacturer."

# Create a variable
bin/vibe promptvault create-variable "company_name" \
  --default "Acme Corp"
```

### Using /promptvault Skill

The `/promptvault` skill provides interactive prompt management:

```
/promptvault scaffold
# Walks through creating prompts, snippets, and variables

/promptvault validate
# Validates that all prompts compile correctly

/promptvault sync
# Syncs local prompt files to PromptVault
```

### Compiling Prompts

To get a compiled prompt with all variables and snippets resolved:

```python
import requests

def get_compiled_prompt(shortname: str, variables: dict) -> str:
    response = requests.post(
        f"https://prompt-vault-sand.vercel.app/api/prompts/public/{shortname}/compile",
        headers={
            "X-API-Key": os.environ["PROMPTVAULT_API_KEY"],
            "Content-Type": "application/json"
        },
        json={"variables": variables}
    )
    return response.json()["content"]

# Usage
prompt = get_compiled_prompt("customer-support", {
    "customer_name": "John",
    "issue_type": "billing",
    "context": "Account shows incorrect charge"
})
```

### TypeScript/JavaScript Client

```typescript
async function getCompiledPrompt(shortname: string, variables: Record<string, string>) {
  const response = await fetch(
    `https://prompt-vault-sand.vercel.app/api/prompts/public/${shortname}/compile`,
    {
      method: 'POST',
      headers: {
        'X-API-Key': process.env.PROMPTVAULT_API_KEY!,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ variables })
    }
  );
  return (await response.json()).content;
}
```

## API Reference

### Base URL
```
https://prompt-vault-sand.vercel.app/api
```

### Authentication
Include API key in header:
```
X-API-Key: your-api-key
```

### Endpoints

| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `/variables` | Create variable |
| POST | `/snippets/public` | Create snippet |
| POST | `/prompts/public` | Create prompt |
| POST | `/prompts/public/{shortname}/compile` | Compile prompt |
| GET | `/prompts/public/{shortname}` | Get prompt without compilation |
| POST | `/response-schemas` | Create response schema |
| POST | `/example-responses` | Create example response |

### Response Codes

- `201` - Resource created
- `200` - Success
- `409` - Resource already exists (idempotent operations)
- `401` - Invalid API key
- `404` - Resource not found

## Best Practices

### Prompt Organization

1. **Use descriptive shortnames**: `customer-support-v2`, `summarize-article`
2. **Version prompts**: Include version in shortname or use PromptVault versioning
3. **Document variables**: Include descriptions for each variable
4. **Create shared snippets**: Extract common context into reusable snippets

### Development Workflow

1. **Local development**: Use `.env.local` for API key
2. **Prompt iteration**: Edit prompts in PromptVault UI, compile via API
3. **Version control**: Store prompt shortnames in code, not prompt content
4. **Testing**: Use `/promptvault validate` before deploying

### Production

1. **Set API key in production env**: Fly.io, Vercel, etc.
2. **Cache compiled prompts**: Reduce API calls for static prompts
3. **Handle errors gracefully**: Fall back to default prompts if API fails

## Troubleshooting

### "Unauthorized" Error
- Verify `PROMPTVAULT_API_KEY` is set correctly
- Check key hasn't expired
- Ensure key has access to the resource

### "Prompt not found"
- Verify shortname is correct (case-sensitive)
- Check prompt is published/public
- Ensure prompt exists in your workspace

### Variables not resolving
- Verify variable names match exactly (case-sensitive)
- Check all required variables are provided
- Look for typos in `{variable_name}` syntax

## Related

- [linear-setup.md](../tickets/linear-setup.md) - Linear configuration
- [secret-management.md](../security/secret-management.md) - Handling API keys
