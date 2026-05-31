# Changelog

All notable changes to the private `vibe` package are recorded here.

## 0.1.0

- Establish the first Packaged Vibe release rail: dist name `vibe`, import
  package `vibe`, uv-locked installs, and build-gated private git-tag releases.
# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Claude Code skills (`/do`, `/pr`, `/doctor`, `/ticket`, `/cleanup`)
- Multi-agent terminal workflow documentation
- UAT (User Acceptance Testing) workflow documentation
- Ticket triage workflow in CLAUDE.md
- Shortcut.com tracker integration
- Fly.io and Vercel secrets providers
- Grandfathered ticket support for legacy projects
- CONTRIBUTING.md with contribution guidelines
- CODE_OF_CONDUCT.md
- Dependabot configuration

### Changed
- Improved error messages with actionable suggestions
- Updated CLAUDE.md with comprehensive agent instructions

### Fixed
- PR policy now supports grandfathered ticket patterns

## [1.0.0] - 2026-02-01

### Added
- Initial release
- Linear integration with full CRUD operations
- Automatic ticket status updates (PR opened → In Review, PR merged → Deployed)
- Git worktree management for parallel development
- PR policy enforcement (ticket references, risk labels)
- GitHub Actions workflows (security, tests, PR policy)
- 39 recipe guides covering workflows, security, architecture
- Local hooks for Linear automation
- Secret management with Gitleaks scanning
- HUMAN ticket workflow for deployment setup
- Multi-agent coordination guidelines

### Security
- Gitleaks integration for secret scanning
- SBOM generation with Syft
- CodeQL analysis
- Dependency review on PRs

[Unreleased]: https://github.com/kdenny/vibe-code-boilerplate/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/kdenny/vibe-code-boilerplate/releases/tag/v1.0.0
