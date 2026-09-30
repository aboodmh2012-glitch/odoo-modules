#!/bin/bash
set -euo pipefail
COMMON_ARGS=(
  -c /etc/odoo/odoo.conf
  --db_host="${HOST:?}"
  --db_port="${DB_PORT:-5432}"
  --db_user="${USER:?}"
  --db_password="${PASSWORD:?}"
)
echo "Initializing Odoo 20 base database..."
odoo "${COMMON_ARGS[@]}" -d odoo20 -i base --without-demo=all --stop-after-init
echo "Odoo 20 base initialized; starting server..."
exec odoo "${COMMON_ARGS[@]}"
