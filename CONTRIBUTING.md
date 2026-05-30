# Contributing to Vibe Code Boilerplate

Thank you for your interest in contributing! This document provides guidelines for contributing to the project.

## Code of Conduct

By participating in this project, you agree to abide by our [Code of Conduct](CODE_OF_CONDUCT.md).

## How to Contribute

### Reporting Issues

- Check if the issue already exists
- Use a clear, descriptive title
- Provide steps to reproduce (for bugs)
- Include your environment details (OS, Python version, etc.)

### Suggesting Features

- Open an issue with the "Feature" label
- Describe the use case and expected behavior
- Explain why this would be useful

### Pull Requests

1. **Fork and create a branch**
   ```bash
   git checkout -b PROJ-123-my-feature
   ```

2. **Follow the workflow**
   - Use `bin/vibe do PROJ-123` for ticket-linked work
   - Follow branch naming conventions
   - Keep commits focused and atomic

3. **Write good commit messages**
   ```
   PROJ-123: Add feature X

   - Detailed explanation of what changed
   - Why it was needed

   Co-Authored-By: Your Name <email@example.com>
   ```

4. **Ensure quality**
   - Run `bin/vibe doctor` to check health
   - Run tests: `pytest`
   - Run linter: `ruff check .`
   - No secrets in code

5. **Open a PR**
   - Fill out the PR template completely
   - Add appropriate risk label
   - Link to the related issue/ticket

## Development Setup

### Prerequisites

- Python 3.11+
- Git
- GitHub CLI (`gh`)
- [direnv](https://direnv.net/docs/installation.html) (optional but recommended)

### Setup

```bash
# Clone the repo
git clone https://github.com/kdenny/vibe-code-boilerplate.git
cd vibe-code-boilerplate

# Run setup
bin/vibe setup

# Verify
bin/vibe doctor
```

### direnv (recommended)

This repo ships a committed [`.envrc`](.envrc). With `direnv` installed, `cd`ing
into the project automatically:

- loads `.env` / `.env.local` (your secrets live in `.env.local`, gitignored),
- activates a project-local Python virtualenv (under `.direnv/`), and
- puts `bin/` on `PATH` so `vibe`, `ci-local`, `ticket`, and `doctor` are
  callable without the `bin/` prefix.

```bash
direnv allow            # one-time, in the project root
pip install -e ".[dev]" # into the direnv-managed venv
```

direnv is optional — without it, `bin/*` and `lib/vibe/env.py` still load
`.env.local` on their own; you just run commands via the `bin/` prefix and
manage your own virtualenv. `bin/vibe doctor` reports direnv status either way.

### Running Tests

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run with coverage
pytest --cov=lib/vibe
```

### Code Style

We use:
- **ruff** for linting and formatting
- **mypy** for type checking

```bash
# Lint
ruff check .

# Format
ruff format .

# Type check
mypy lib/vibe
```

## Project Structure

```
.
├── bin/           # CLI scripts
├── lib/vibe/      # Python library
│   ├── cli/       # Click commands
│   ├── trackers/  # Linear, Shortcut integrations
│   ├── git/       # Git operations
│   ├── secrets/   # Secret management
│   └── wizards/   # Setup wizards
├── recipes/       # Best practice guides
├── tests/         # Test suite
└── .github/       # GitHub Actions
```

## Recipe Contributions

Recipes are markdown guides in `recipes/`. To add a new recipe:

1. Choose the appropriate subdirectory
2. Use existing recipes as templates
3. Include:
   - When to use
   - Step-by-step instructions
   - Related recipes section

## Questions?

- Open a discussion on GitHub
- Check existing issues and PRs

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
