# DB migrations

Versioned migrations are stored in:
- `migrations/up` - forward migrations
- `migrations/down` - rollback migrations

Current version:
- `001_init`

## Auto-apply on fresh DB

`docker-compose.yml` mounts only `migrations/up` into `/docker-entrypoint-initdb.d`, so new databases are initialized automatically from the latest `up` scripts.

## Manual apply

From repository root:

```bash
docker compose exec db psql -U postgres -d emeeting -f /docker-entrypoint-initdb.d/001_init.sql
```

## Manual rollback

Rollback is kept in source under:
- `code/emeeting-backend/migrations/down/001_init.sql`

Run from host (example with local psql):

```bash
psql "postgres://postgres:1040@localhost:5432/emeeting?sslmode=disable" -f code/emeeting-backend/migrations/down/001_init.sql
```
