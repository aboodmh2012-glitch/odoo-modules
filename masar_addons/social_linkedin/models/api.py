# Copyright 2026 MASAR
# License AGPL-3.0 or later.
"""LinkedIn REST helper (Community Management API, versioned /rest endpoints).

Uses the official LinkedIn REST API directly (no third-party SDK):
- Versioned host ``https://api.linkedin.com/rest`` with ``LinkedIn-Version`` and
  ``X-Restli-Protocol-Version: 2.0.0`` headers.
- OAuth 2.0 authorization-code flow on ``https://www.linkedin.com/oauth/v2``.

Security: the bearer token is only ever placed in the Authorization header; it is
never logged and never included in raised exception text (LinkedIn error bodies
do not echo the token, but we still avoid attaching response text to exceptions).
Errors map to the shared Delivery* taxonomy so the queue publish path handles
retries / permanent failures / uncertain outcomes uniformly.
"""
from __future__ import annotations

import logging
import os

import requests

from odoo.addons.social.models.errors import (
    DeliveryPermanent,
    DeliveryTemporary,
    DeliveryUncertain,
)

_logger = logging.getLogger(__name__)

API_BASE = "https://api.linkedin.com/rest"
AUTH_BASE = "https://www.linkedin.com/oauth/v2"
# LinkedIn versioned APIs use a YYYYMM month tag; keep current via env override.
DEFAULT_VERSION = "202506"

# Organization page posting + reading + admin (analytics). No DM scope exists
# for organizations, so this connector never advertises DMs.
SCOPES = "w_organization_social r_organization_social rw_organization_admin"


def api_version(env):
    return (
        (os.environ.get("SOCIAL_LINKEDIN_VERSION") or "").strip()
        or (env["ir.config_parameter"].sudo().get_str("social.linkedin_version") or "").strip()
        or DEFAULT_VERSION
    )


def _headers(token, version, write=False):
    headers = {
        "Authorization": f"Bearer {token}",
        "LinkedIn-Version": version,
        "X-Restli-Protocol-Version": "2.0.0",
    }
    if write:
        headers["Content-Type"] = "application/json"
    return headers


def rest_request(method, path, token, version, json=None, params=None, timeout=(10, 45)):
    """Call a versioned /rest endpoint. Returns the ``requests.Response``.

    ``path`` is relative to API_BASE (e.g. ``posts``, ``organizationAcls``).
    Raises Delivery* on transport/HTTP errors — never leaks the token.
    """
    url = f"{API_BASE}/{path.lstrip('/')}"
    try:
        resp = requests.request(
            method,
            url,
            headers=_headers(token, version, write=json is not None),
            json=json,
            params=params,
            timeout=timeout,
        )
    except requests.RequestException:
        raise DeliveryUncertain() from None
    if resp.status_code == 429:
        raise DeliveryTemporary()
    if resp.status_code >= 500:
        raise DeliveryUncertain()
    if resp.status_code in (401, 403):
        # Token revoked / missing scope / expired — needs a re-link, not a retry.
        raise DeliveryPermanent()
    if resp.status_code >= 400:
        raise DeliveryPermanent()
    return resp


def exchange_token(client_id, client_secret, code, redirect_uri):
    """Authorization-code → access token (form-encoded, non-versioned endpoint)."""
    try:
        resp = requests.post(
            f"{AUTH_BASE}/accessToken",
            data={
                "grant_type": "authorization_code",
                "code": code,
                "client_id": client_id,
                "client_secret": client_secret,
                "redirect_uri": redirect_uri,
            },
            timeout=(10, 45),
        )
    except requests.RequestException:
        raise DeliveryUncertain() from None
    if resp.status_code >= 500:
        raise DeliveryUncertain()
    if resp.status_code >= 400:
        raise DeliveryPermanent()
    try:
        return resp.json() or {}
    except (ValueError, TypeError):
        raise DeliveryUncertain() from None
