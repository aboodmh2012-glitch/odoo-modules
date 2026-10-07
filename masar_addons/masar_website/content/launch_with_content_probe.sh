#!/usr/bin/env bash
set -euo pipefail
# Preserve original startup sequence and signal handling.
# Optional children only make anonymous HTTP GET requests, never form submissions.
if [[ "${MASAR_CONTENT_EN_HTTP_PROBE:-0}" == "2026-09-20-en-content-v1" ]]; then
  gosu odoo python3 -u /mnt/extra-addons/masar_website/content/probe_english.py &
elif [[ "${MASAR_CONTENT_HTTP_PROBE:-0}" == "1" ]]; then
  gosu odoo python3 -u /mnt/extra-addons/masar_website/content/probe_content.py &
fi
exec /entrypoint.sh "$@"
