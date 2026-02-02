# Supply Chain Security

## When to Use This Recipe

Use this recipe when you need to:
- Secure your project's dependencies
- Choose between Dependabot and Renovate
- Understand lockfile best practices
- Set up SBOM generation

## The Threat Model

Supply chain attacks target:
- **Direct dependencies** - Libraries you import
- **Transitive dependencies** - Libraries your libraries import
- **Build tools** - npm, pip, compilers
- **CI/CD infrastructure** - GitHub Actions, runners

## Lockfile Best Practices

### Always Commit Lockfiles

| Language | Lockfile | Commit? |
|----------|----------|---------|
| Python | `requirements.txt` or `uv.lock` | Yes |
| Node.js | `package-lock.json` / `pnpm-lock.yaml` | Yes |
| Go | `go.sum` | Yes |
| Rust | `Cargo.lock` | Yes (for apps) |

### Why Lockfiles Matter
- Reproducible builds across environments
- Defense against dependency confusion attacks
- Audit trail for security reviews
- CI builds same as local

### Keep Lockfiles Updated
```bash
# Node.js
npm update && npm audit fix

# Python (with pip-tools)
pip-compile --upgrade requirements.in
```

## Dependabot vs Renovate

### Dependabot (GitHub Native)
**Pros:**
- Zero setup (GitHub built-in)
- Good for simple projects
- Free for all repos

**Cons:**
- Less configurable
- Basic grouping options
- Limited scheduling

```yaml
# .github/dependabot.yml
version: 2
updates:
  - package-ecosystem: "npm"
    directory: "/"
    schedule:
      interval: "weekly"
```

### Renovate
**Pros:**
- Highly configurable
- Auto-merge low-risk updates
- Better monorepo support
- Grouping by type/scope

**Cons:**
- More setup required
- Learning curve

```json
// renovate.json
{
  "extends": ["config:base"],
  "automerge": true,
  "automergeType": "pr",
  "packageRules": [
    {
      "matchUpdateTypes": ["patch", "minor"],
      "automerge": true
    }
  ]
}
```

### Recommendation
- **Small projects**: Dependabot (simpler)
- **Large/complex projects**: Renovate (more control)

## SBOM Generation

Software Bill of Materials (SBOM) lists all components in your software.

### Why Generate SBOMs?
- Regulatory compliance (executive orders)
- Vulnerability correlation
- License compliance
- Supply chain transparency

### Tools
- **Syft** (recommended) - Fast, accurate
- **Trivy** - Security-focused
- **GitHub Dependency Graph** - Built-in, basic

### Example with Syft
```yaml
# .github/workflows/sbom.yml
- name: Generate SBOM
  run: syft . -o spdx-json > sbom.spdx.json

- name: Upload SBOM
  uses: actions/upload-artifact@v4
  with:
    name: sbom
    path: sbom.spdx.json
```

## Vulnerability Scanning

### GitHub Native
- Dependabot alerts (automatic)
- Code scanning with CodeQL
- Secret scanning

### Additional Tools
- `npm audit` / `pip-audit`
- Snyk (more comprehensive)
- Trivy (container-focused)

## Best Practices Checklist

- [ ] Lockfiles committed and reviewed
- [ ] Dependabot or Renovate configured
- [ ] Vulnerability alerts enabled
- [ ] SBOM generated on releases
- [ ] Dependencies reviewed before adding
- [ ] Minimal dependency philosophy

## Extension Points

- Add custom vulnerability thresholds
- Configure auto-merge rules
- Set up dependency review gates
