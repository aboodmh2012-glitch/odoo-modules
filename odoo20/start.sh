#!/bin/bash
set -euo pipefail
mkdir -p /var/lib/odoo /var/lib/odoo/sessions
chown -R odoo:odoo /var/lib/odoo
exec gosu odoo odoo -c /etc/odoo/odoo.conf   --db_host="${HOST:?}"   --db_port="${DB_PORT:-5432}"   --db_user="${USER:?}"   --db_password="${PASSWORD:?}"
