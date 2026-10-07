#!/bin/bash
# SMART Odoo 20 — primary runtime.
# Avoid -i all / unconditional bulk -i on every boot.
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
DB_NAME="${SMART_DB_NAME:-odoo20}"

# Optional one-shot installs (comma-separated). Never use "all".
if [[ -n "${SMART_INSTALL_MODULES:-}" ]]; then
  if [[ "${SMART_INSTALL_MODULES}" == "all" ]]; then
    echo "Refusing SMART_INSTALL_MODULES=all"
    exit 1
  fi
  echo "One-shot install: ${SMART_INSTALL_MODULES}"
  gosu odoo odoo "${COMMON_ARGS[@]}" -d "${DB_NAME}" -i "${SMART_INSTALL_MODULES}" --without-demo --stop-after-init
fi

# Optional MASAR->SMART reference seed (departments/jobs). Idempotent.
if [[ "${SMART_SEED_MASAR_REFERENCE:-1}" == "1" ]] && [[ -f /opt/masar/seed_masar_reference.py ]]; then
  echo "Seeding MASAR reference data into SMART only..."
  gosu odoo odoo shell "${COMMON_ARGS[@]}" -d "${DB_NAME}" --no-http < /opt/masar/seed_masar_reference.py
fi

echo "Starting Odoo 20..."
exec gosu odoo odoo "${COMMON_ARGS[@]}"
