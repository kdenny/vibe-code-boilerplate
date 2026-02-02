# BYO Postgres Setup

## When to Use This Recipe

Use this recipe when you need to:
- Use your own PostgreSQL instance
- Configure for self-hosted or managed Postgres
- Set up connection for various providers

## Current Status

This is a stub recipe. Extend it based on your project needs.

## Supported Providers

- Self-hosted PostgreSQL
- AWS RDS
- Google Cloud SQL
- Azure Database for PostgreSQL
- DigitalOcean Managed Databases
- Railway

## Quick Start

```bash
# Connection string format
DATABASE_URL=postgresql://user:password@host:5432/database?sslmode=require
```

## Extension Points

- Configure SSL/TLS
- Set up connection pooling (PgBouncer)
- Configure read replicas
- Set up automated backups
- Configure monitoring

## Related Recipes

- `security/secret-management.md` - Managing credentials
- `environments/multi-env.md` - Multi-environment setup
