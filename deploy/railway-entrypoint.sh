#!/bin/bash
set -euo pipefail

# Railway volumes are often root-owned; Odoo runs as uid odoo.
if [ "$(id -u)" = "0" ]; then
  mkdir -p /var/lib/odoo /mnt/extra-addons
  chown -R odoo:odoo /var/lib/odoo || true
  # Drop privileges for the rest of startup.
  if command -v gosu >/dev/null 2>&1; then
    exec gosu odoo /railway-odoo-start.sh "$@"
  fi
  if command -v su-exec >/dev/null 2>&1; then
    exec su-exec odoo /railway-odoo-start.sh "$@"
  fi
  exec su -s /bin/bash -c "/railway-odoo-start.sh $*" odoo
fi

exec /railway-odoo-start.sh "$@"
