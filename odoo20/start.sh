#!/bin/bash
# SMART Odoo 20 — serve only.
# Module installs must be run deliberately (module-by-module), never on every boot.
# Forbidden here: -i all, -u all, and unconditional -i of app bundles.
set -euo pipefail

mkdir -p /var/lib/odoo /var/lib/odoo/sessions /mnt/extra-addons
chown -R odoo:odoo /var/lib/odoo || true

COMMON_ARGS=(
  -c /etc/odoo/odoo.conf
  --db_host="${HOST:?}"
  --db_port="${DB_PORT:-5432}"
  --db_user="${USER:?}"
  --db_password="${PASSWORD:?}"
)

# Optional one-shot install when operator sets SMART_INSTALL_MODULES explicitly, e.g.:
#   SMART_INSTALL_MODULES=hr,hr_recruitment
# Never set this permanently on the primary service.
if [[ -n "${SMART_INSTALL_MODULES:-}" ]]; then
  DB_NAME="${SMART_DB_NAME:-odoo20}"
  echo "One-shot module install requested for DB=${DB_NAME}: ${SMART_INSTALL_MODULES}"
  gosu odoo odoo "${COMMON_ARGS[@]}" \
    -d "${DB_NAME}" \
    -i "${SMART_INSTALL_MODULES}" \
    --without-demo \
    --stop-after-init
  echo "One-shot install finished; starting server..."
fi

exec gosu odoo odoo "${COMMON_ARGS[@]}"
