# Local Debugging

## When to Use This Recipe

Use this recipe when you need to:
- Set up effective local debugging
- Configure IDE debugging
- Use debugging tools

## Current Status

This is a stub recipe. Extend it based on your project needs.

## Quick Start

### VS Code
```json
// .vscode/launch.json
{
  "version": "0.2.0",
  "configurations": [
    {
      "type": "node",
      "request": "launch",
      "name": "Debug",
      "program": "${workspaceFolder}/src/index.ts"
    }
  ]
}
```

### Python
```bash
python -m debugpy --listen 5678 --wait-for-client script.py
```

## Extension Points

- Configure remote debugging
- Set up log aggregation
- Configure trace collection
- Set up profiling
- Configure memory debugging

## Related Recipes

- `environments/multi-env.md` - Debug settings per environment
