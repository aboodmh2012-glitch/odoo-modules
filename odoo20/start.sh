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
APPS="account,crm,sale_management,purchase,stock,point_of_sale,project,hr,hr_recruitment,hr_holidays,hr_attendance,hr_expense,website,website_sale,website_slides,website_event,mass_mailing,mass_mailing_sms,calendar,contacts,survey,fleet,maintenance,repair,mrp,lunch,im_livechat,project_todo"
echo "Installing selected Odoo 20 Community applications..."
gosu odoo odoo "${COMMON_ARGS[@]}" -d odoo20 -i "${APPS}" --without-demo --stop-after-init
echo "Selected Odoo 20 applications installed; starting server..."
exec gosu odoo odoo "${COMMON_ARGS[@]}"
