# PR merged → Linear ticket status

> **This functionality is now handled by Linear's native GitHub integration.**
>
> See [linear-github-integration.md](../tickets/linear-github-integration.md) for setup instructions.

## What Changed

Previously, this boilerplate used a custom GitHub Actions workflow (`pr-merged.yml`) to update Linear tickets when PRs were merged. This has been replaced by Linear's native GitHub integration, which:

- Is simpler to set up (one OAuth click)
- Is maintained by Linear (not you)
- Automatically moves tickets to Done/Deployed on merge
- Requires no API keys in GitHub

## Migration

If you were using the old workflow:

1. Delete `.github/workflows/pr-merged.yml` (if it exists)
2. Remove the `LINEAR_API_KEY` repo secret (unless needed for other purposes)
3. Remove the `LINEAR_DEPLOYED_STATE` repo variable
4. Follow the [native integration setup guide](../tickets/linear-github-integration.md)
5. Configure auto-close in Linear to use your desired target state (Done, Deployed, etc.)

## Local Hooks (Optional)

For even faster feedback during development, you can enable local Claude Code hooks that mark tickets "Done" when you commit.

See [linear-hooks.md](linear-hooks.md) for details.

## UAT Workflow

If your team uses a testing/verification step before marking tickets as Done, configure Linear's auto-close to use an intermediate state (e.g., "To Test") and manually move tickets to Done after verification.

See [uat-testing.md](uat-testing.md) for details.
