#!/bin/bash
set -euo pipefail
exec odoo -c /etc/odoo/odoo.conf   --db_host="${HOST:?}"   --db_port="${DB_PORT:-5432}"   --db_user="${USER:?}"   --db_password="${PASSWORD:?}"
