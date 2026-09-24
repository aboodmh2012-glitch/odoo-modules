#!/bin/bash
set -euo pipefail
# Runs as odoo after entrypoint fixed ownership.
exec odoo \
  --addons-path=/usr/lib/python3/dist-packages/odoo/addons,/mnt/extra-addons,/var/lib/odoo/extra-addons \
  --data-dir=/var/lib/odoo \
  --db_host="${HOST:?}" \
  --db_port="${DB_PORT:-5432}" \
  --db_user="${USER:?}" \
  --db_password="${PASSWORD:?}" \
  --http-port="${PORT_HTTP:-8069}" \
  --proxy-mode \
  "$@"
