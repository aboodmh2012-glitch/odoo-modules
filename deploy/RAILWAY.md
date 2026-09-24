# Railway — Odoo 18 (project smart)

This repository deploys as the **Odoo** service image for the existing Railway
project `smart`. Modules are copied into `/mnt/extra-addons` at **build** time
so restarts do not re-clone GitHub.

## Required volumes (existing services only)

| Volume        | Service    | Mount path                   |
|---------------|------------|------------------------------|
| postgres-data | PostgreSQL | `/var/lib/postgresql/data`   |
| odoo-data     | Odoo       | `/var/lib/odoo`              |

## Environment variables (Odoo service)

Wire Railway Postgres references (names may already exist):

- `HOST` = `${{Postgres.PGHOST}}` (or private hostname)
- `PORT` = `${{Postgres.PGPORT}}`
- `USER` = `${{Postgres.PGUSER}}`
- `PASSWORD` = `${{Postgres.PGPASSWORD}}`
- Optional: `ODOO_ADMIN_PASSWORD` for master password

## Database

After volumes are attached and verified, create Odoo database name: `smart`.

## First modules

Start with LGPL-3 modules that only depend on `web` / `mail`, e.g. `bf_apps_menu`.
Do not install 200+ modules in one batch. Prefer `bf_productivity_pack` after
dependencies are validated.
