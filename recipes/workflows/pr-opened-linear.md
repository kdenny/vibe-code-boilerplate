# PR opened → Linear ticket status

> **This functionality is now handled by Linear's native GitHub integration.**
>
> See [linear-github-integration.md](../tickets/linear-github-integration.md) for setup instructions.

## What Changed

Previously, this boilerplate used a custom GitHub Actions workflow (`pr-opened.yml`) to update Linear tickets when PRs were opened. This has been replaced by Linear's native GitHub integration, which:

- Is simpler to set up (one OAuth click)
- Is maintained by Linear (not you)
- Provides more features (PR status badges, bidirectional sync)
- Requires no API keys in GitHub

## Migration

If you were using the old workflow:

1. Delete `.github/workflows/pr-opened.yml` (if it exists)
2. Remove the `LINEAR_API_KEY` repo secret (unless needed for other purposes)
3. Remove the `LINEAR_IN_REVIEW_STATE` repo variable
4. Follow the [native integration setup guide](../tickets/linear-github-integration.md)

## Local Hooks (Optional)

For even faster feedback during development, you can enable local Claude Code hooks that mark tickets "In Progress" when you mention them.

See [linear-hooks.md](linear-hooks.md) for details.
