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
#
# Runs ONCE per (database, module list): the result is recorded on the
# persistent volume (/var/lib/odoo), so a variable left set no longer re-runs
# `-i` on every restart. A failed install is recorded too and does NOT stop
# Odoo from starting (previously `set -e` exited the container, and Railway's
# restart policy turned that into a crash loop).
#   - change the list            -> runs once for the new list
#   - SMART_INSTALL_FORCE=1      -> re-run even if already recorded
#   - rm the marker in $MARKER_DIR -> same, by hand
MARKER_DIR="${SMART_INSTALL_MARKER_DIR:-/var/lib/odoo/.smart-install}"
if [[ -n "${SMART_INSTALL_MODULES:-}" ]]; then
  # normalise: drop spaces, sort, dedupe -> stable key for the same set
  MODULES="$(echo "${SMART_INSTALL_MODULES}" | tr -d '[:space:]' | tr ',' '\n' | sed '/^$/d' | sort -u | paste -sd, -)"
  # A rejected list is skipped (not exit 1): exiting here would crash-loop prod.
  if [[ ",${MODULES}," == *",all,"* ]]; then
    echo "ERROR: refusing SMART_INSTALL_MODULES=all; skipping the one-shot install"
    MODULES=""
  elif [[ ! "${MODULES}" =~ ^[a-z0-9_]+(,[a-z0-9_]+)*$ ]]; then
    echo "ERROR: refusing SMART_INSTALL_MODULES='${SMART_INSTALL_MODULES}' (only comma-separated module names); skipping the one-shot install"
    MODULES=""
  fi
fi
if [[ -n "${MODULES:-}" ]]; then
  KEY="${DB_NAME}-$(printf '%s' "${MODULES}" | sha256sum | cut -c1-16)"
  mkdir -p "${MARKER_DIR}"
  chown odoo:odoo "${MARKER_DIR}" || true
  if [[ "${SMART_INSTALL_FORCE:-0}" != "1" && -f "${MARKER_DIR}/${KEY}.done" ]]; then
    echo "One-shot install already done for [${MODULES}] on ${DB_NAME} ($(head -1 "${MARKER_DIR}/${KEY}.done")); skipping. Clear SMART_INSTALL_MODULES, or set SMART_INSTALL_FORCE=1 to re-run."
  elif [[ "${SMART_INSTALL_FORCE:-0}" != "1" && -f "${MARKER_DIR}/${KEY}.failed" ]]; then
    echo "One-shot install for [${MODULES}] on ${DB_NAME} FAILED earlier ($(head -1 "${MARKER_DIR}/${KEY}.failed")); not retrying on every boot. Fix the cause, then set SMART_INSTALL_FORCE=1 or change the list."
  else
    echo "One-shot install: ${MODULES}"
    if gosu odoo odoo "${COMMON_ARGS[@]}" -d "${DB_NAME}" -i "${MODULES}" --without-demo --stop-after-init; then
      printf '%s\n%s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "${MODULES}" > "${MARKER_DIR}/${KEY}.done"
      rm -f "${MARKER_DIR}/${KEY}.failed"
      echo "One-shot install OK: ${MODULES} (recorded ${MARKER_DIR}/${KEY}.done)"
    else
      rc=$?
      printf '%s exit=%s\n%s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "${rc}" "${MODULES}" > "${MARKER_DIR}/${KEY}.failed"
      echo "ERROR: one-shot install of [${MODULES}] failed (exit ${rc}); starting Odoo anyway. See the log above."
    fi
  fi
fi

# Optional MASAR->SMART reference seed (departments/jobs). Idempotent.
if [[ "${SMART_SEED_MASAR_REFERENCE:-1}" == "1" ]] && [[ -f /opt/masar/seed_masar_reference.py ]]; then
  echo "Seeding MASAR reference data into SMART only..."
  gosu odoo odoo shell "${COMMON_ARGS[@]}" -d "${DB_NAME}" --no-http < /opt/masar/seed_masar_reference.py
fi

echo "Starting Odoo 20..."
exec gosu odoo odoo "${COMMON_ARGS[@]}"
