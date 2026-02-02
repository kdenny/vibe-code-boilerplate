# Multi-Environment Setup

## When to Use This Recipe

Use this recipe when you need to:
- Set up local, staging, and production environments
- Validate configurations across environments
- Manage environment-specific behavior

## Environment Tiers

### Local Development
- Fast iteration
- Mocked or local services
- Debug-friendly settings
- Real secrets in `.env.local`

### CI/Test
- Automated testing
- Isolated per-run
- Mock external services
- Test secrets only

### Staging
- Production-like environment
- Real integrations (but staging accounts)
- Used for final verification
- Subset of production data

### Production
- Real users
- Real money
- Real consequences
- Maximum observability

## Configuration Pattern

### Environment Detection
```python
import os

ENV = os.environ.get('APP_ENV', 'development')

IS_PRODUCTION = ENV == 'production'
IS_STAGING = ENV == 'staging'
IS_DEVELOPMENT = ENV == 'development'
IS_TEST = ENV == 'test'
```

### Environment-Specific Config
```python
CONFIGS = {
    'development': {
        'debug': True,
        'log_level': 'DEBUG',
        'db_pool_size': 5,
    },
    'staging': {
        'debug': False,
        'log_level': 'INFO',
        'db_pool_size': 10,
    },
    'production': {
        'debug': False,
        'log_level': 'WARNING',
        'db_pool_size': 20,
    },
}

config = CONFIGS.get(ENV, CONFIGS['development'])
```

## Feature Flags by Environment

```python
FEATURES = {
    'new_checkout': {
        'development': True,
        'staging': True,
        'production': False,  # Not yet!
    },
    'debug_mode': {
        'development': True,
        'staging': False,
        'production': False,
    },
}

def is_feature_enabled(feature_name):
    return FEATURES.get(feature_name, {}).get(ENV, False)
```

## Database Strategy

### Local
- SQLite for simplicity, or
- Docker Compose with Postgres

### Staging
- Isolated database instance
- Seeded with anonymized production data
- Regular refresh from production

### Production
- Managed database service
- Regular backups
- Read replicas if needed

## Third-Party Services

| Service | Local | Staging | Production |
|---------|-------|---------|------------|
| Stripe | Test mode | Test mode | Live mode |
| Email | Mailhog/Console | Staging inbox | Real delivery |
| Analytics | Disabled | Enabled | Enabled |
| Error tracking | Console | Sentry (staging) | Sentry (prod) |

## Validation Matrix

Before deploying to production, validate:

| Check | Staging | Production |
|-------|---------|------------|
| All env vars set | ✓ | ✓ |
| Database migrations applied | ✓ | ✓ |
| External services accessible | ✓ | ✓ |
| SSL certificates valid | ✓ | ✓ |
| Error tracking configured | ✓ | ✓ |

## Deployment Pipeline

```
Local → Push → CI Tests → Staging Deploy → Staging Tests → Production Deploy
                                  ↓
                            Manual approval
                            (for production)
```

## Best Practices

1. **Never use production credentials locally** - Even for "quick tests"
2. **Staging mirrors production** - Same infrastructure, smaller scale
3. **Feature flags for rollout** - Not environment-specific code paths
4. **Separate data completely** - No shared databases between envs
5. **Log environment on startup** - Makes debugging easier

## Extension Points

- Add environment-specific health checks
- Implement gradual rollout strategies
- Set up environment promotion workflows
