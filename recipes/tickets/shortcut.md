# Shortcut Setup

## When to Use This Recipe

Use this recipe when you need to:
- Set up Shortcut as your ticket tracking system
- Understand the current integration status

## Current Status

**⚠️ Shortcut integration is not yet implemented.**

This is tracked in GitHub issue #1.

## Planned Features

When implemented, Shortcut integration will support:

- API authentication
- Creating and updating stories
- Listing stories with filters
- Label management
- Workflow state mapping
- GitHub integration

## Workaround

Until Shortcut integration is complete, you can:

### Option 1: Use Linear Instead
Linear is fully supported. See `recipes/tickets/linear-setup.md`.

### Option 2: Manual Workflow
1. Create tickets directly in Shortcut
2. Use the ticket ID in your branch names manually:
   ```bash
   git checkout -b sc-12345-feature-name
   ```
3. Reference ticket in PR descriptions:
   ```markdown
   Closes [sc-12345](https://app.shortcut.com/yourorg/story/12345)
   ```

### Option 3: Shortcut GitHub Integration
Enable Shortcut's native GitHub integration:
1. In Shortcut: Settings → Integrations → GitHub
2. Connect your GitHub organization
3. Branch names with `sc-12345` will auto-link

## Contributing

If you'd like to help implement Shortcut integration:

1. Check GitHub issue #1 for current status
2. Reference the Linear implementation in `lib/vibe/trackers/linear.py`
3. Shortcut API docs: https://developer.shortcut.com/api/rest/v3

### Implementation Outline

```python
# lib/vibe/trackers/shortcut.py

class ShortcutTracker(TrackerBase):
    def authenticate(self, api_token: str) -> bool:
        # POST to /api/v3/member
        pass

    def get_ticket(self, story_id: str) -> Ticket:
        # GET /api/v3/stories/{story_id}
        pass

    def list_tickets(self, ...) -> list[Ticket]:
        # POST /api/v3/search/stories
        pass

    def create_ticket(self, ...) -> Ticket:
        # POST /api/v3/stories
        pass
```

## Timeline

Check GitHub issue #1 for updates on implementation timeline.

## Extension Points

When implemented:
- Custom field mapping
- Milestone/Epic integration
- Iteration support
