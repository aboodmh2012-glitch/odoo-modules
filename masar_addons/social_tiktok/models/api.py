# Copyright 2026 MASAR
# License AGPL-3.0 or later.
"""TikTok API helper (OAuth v2 + Content Posting API, official REST).

- OAuth: authorize on tiktok.com, token on open.tiktokapis.com (uses client_key,
  not client_id). Access token ~24h + refresh token.
- Content Posting: creator_info/query → post/publish/video/init (FILE_UPLOAD) →
  PUT bytes → status/fetch. TikTok has no public comments or DM API, so this
  connector is publish-only.

Security: tokens only in the Authorization header / token body; never logged,
never attached to raised exceptions. Errors map to the shared Delivery* taxonomy.
"""
from __future__ import annotations

import logging

import requests

from odoo.addons.social.models.errors import (
    DeliveryPermanent,
    DeliveryTemporary,
    DeliveryUncertain,
)

_logger = logging.getLogger(__name__)

AUTH_URL = "https://www.tiktok.com/v2/auth/authorize/"
TOKEN_URL = "https://open.tiktokapis.com/v2/oauth/token/"
API_BASE = "https://open.tiktokapis.com/v2"

# user.info.basic → open_id/profile; video.publish → Direct Post.
SCOPES = "user.info.basic,video.publish"

_TEMPORARY_ERRORS = frozenset({"rate_limit_exceeded", "server_error"})
_PERMANENT_ERRORS = frozenset(
    {"access_token_invalid", "scope_not_authorized", "scope_permission_missed", "invalid_grant"}
)


def exchange_token(client_key, client_secret, code, redirect_uri):
    return _token_request(
        {
            "client_key": client_key,
            "client_secret": client_secret,
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": redirect_uri,
        }
    )


def refresh_token(client_key, client_secret, refresh):
    return _token_request(
        {
            "client_key": client_key,
            "client_secret": client_secret,
            "grant_type": "refresh_token",
            "refresh_token": refresh,
        }
    )


def _token_request(data):
    try:
        resp = requests.post(
            TOKEN_URL,
            data=data,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            timeout=(10, 45),
        )
    except requests.RequestException:
        raise DeliveryUncertain() from None
    if resp.status_code >= 500:
        raise DeliveryUncertain()
    try:
        payload = resp.json() or {}
    except (ValueError, TypeError):
        raise DeliveryUncertain() from None
    # TikTok token errors: {"error":"...","error_description":"..."}
    if resp.status_code >= 400 or payload.get("error"):
        raise DeliveryPermanent()
    return payload


def _raise_for_tiktok(payload, http_status):
    """TikTok returns HTTP 200 with an ``error`` object; inspect error.code."""
    error = (payload or {}).get("error") or {}
    code = error.get("code")
    if code in (None, "ok", ""):
        if http_status >= 500:
            raise DeliveryUncertain()
        if http_status >= 400:
            raise DeliveryPermanent()
        return
    if code in _TEMPORARY_ERRORS:
        raise DeliveryTemporary()
    if code in _PERMANENT_ERRORS:
        raise DeliveryPermanent()
    if http_status >= 500:
        raise DeliveryUncertain()
    raise DeliveryPermanent()


def api_post(path, token, json_body=None, timeout=(10, 60)):
    url = f"{API_BASE}/{path.lstrip('/')}"
    try:
        resp = requests.post(
            url,
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json; charset=UTF-8",
            },
            json=json_body or {},
            timeout=timeout,
        )
    except requests.RequestException:
        raise DeliveryUncertain() from None
    if resp.status_code == 429:
        raise DeliveryTemporary()
    if resp.status_code >= 500:
        raise DeliveryUncertain()
    try:
        payload = resp.json() or {}
    except (ValueError, TypeError):
        raise DeliveryUncertain() from None
    _raise_for_tiktok(payload, resp.status_code)
    return payload


def get_user_info(token, fields="open_id,union_id,display_name,avatar_url"):
    url = f"{API_BASE}/user/info/"
    try:
        resp = requests.get(
            url,
            headers={"Authorization": f"Bearer {token}"},
            params={"fields": fields},
            timeout=(10, 45),
        )
    except requests.RequestException:
        raise DeliveryUncertain() from None
    if resp.status_code >= 500:
        raise DeliveryUncertain()
    try:
        payload = resp.json() or {}
    except (ValueError, TypeError):
        raise DeliveryUncertain() from None
    _raise_for_tiktok(payload, resp.status_code)
    return (payload.get("data") or {}).get("user") or {}


def upload_chunk(upload_url, raw_bytes, mimetype):
    """Single-chunk PUT to the init-provided upload_url (files up to 64 MB)."""
    size = len(raw_bytes)
    try:
        resp = requests.put(
            upload_url,
            headers={
                "Content-Type": mimetype,
                "Content-Length": str(size),
                "Content-Range": f"bytes 0-{size - 1}/{size}",
            },
            data=raw_bytes,
            timeout=(10, 300),
        )
    except requests.RequestException:
        # Upload may have partially landed — never blind-retry a publish.
        raise DeliveryUncertain() from None
    if resp.status_code == 429:
        raise DeliveryTemporary()
    if resp.status_code >= 500:
        raise DeliveryUncertain()
    if resp.status_code >= 400:
        raise DeliveryPermanent()
    return True
