#!/bin/bash
set -euo pipefail
mkdir -p /var/lib/odoo /var/lib/odoo/sessions
chown -R odoo:odoo /var/lib/odoo
COMMON_ARGS=(
  -c /etc/odoo/odoo.conf
  --db_host="${HOST:?}"
  --db_port="${DB_PORT:-5432}"
  --db_user="${USER:?}"
  --db_password="${PASSWORD:?}"
)
echo "Installing all available Odoo 20 Community modules..."
gosu odoo odoo "${COMMON_ARGS[@]}" -d odoo20 -i all --without-demo --stop-after-init
echo "All-module installation pass completed; starting Odoo normally..."
exec gosu odoo odoo "${COMMON_ARGS[@]}"
