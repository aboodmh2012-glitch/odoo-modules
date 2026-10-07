# Copyright 2026 MASAR
# License AGPL-3.0 or later.
"""Google / YouTube Data API v3 helper (official REST, no third-party SDK).

- OAuth 2.0 on accounts.google.com / oauth2.googleapis.com (offline access →
  refresh token, since Google access tokens live only ~1h).
- YouTube Data API v3: channels.list, resumable videos.insert, comments.insert.

Security: the bearer/refresh tokens are only placed in the Authorization header
or the token endpoint body; never logged, never attached to raised exceptions.
Errors map to the shared Delivery* taxonomy.
"""
from __future__ import annotations

import json
import logging

import requests

from odoo.addons.social.models.errors import (
    DeliveryPermanent,
    DeliveryTemporary,
    DeliveryUncertain,
)

_logger = logging.getLogger(__name__)

AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
TOKEN_URL = "https://oauth2.googleapis.com/token"
DATA_BASE = "https://www.googleapis.com/youtube/v3"
UPLOAD_BASE = "https://www.googleapis.com/upload/youtube/v3"
ANALYTICS_URL = "https://youtubeanalytics.googleapis.com/v2/reports"

# upload → publish, force-ssl → comments, yt-analytics.readonly → insights.
SCOPES = (
    "https://www.googleapis.com/auth/youtube.upload "
    "https://www.googleapis.com/auth/youtube.force-ssl "
    "https://www.googleapis.com/auth/yt-analytics.readonly"
)


def exchange_token(client_id, client_secret, code, redirect_uri):
    return _token_request(
        {
            "grant_type": "authorization_code",
            "code": code,
            "client_id": client_id,
            "client_secret": client_secret,
            "redirect_uri": redirect_uri,
        }
    )


def refresh_token(client_id, client_secret, refresh):
    return _token_request(
        {
            "grant_type": "refresh_token",
            "refresh_token": refresh,
            "client_id": client_id,
            "client_secret": client_secret,
        }
    )


def _token_request(data):
    try:
        resp = requests.post(TOKEN_URL, data=data, timeout=(10, 45))
    except requests.RequestException:
        raise DeliveryUncertain() from None
    if resp.status_code >= 500:
        raise DeliveryUncertain()
    if resp.status_code >= 400:
        # invalid_grant etc → needs re-link, not a retry.
        raise DeliveryPermanent()
    try:
        return resp.json() or {}
    except (ValueError, TypeError):
        raise DeliveryUncertain() from None


def _check(resp):
    if resp.status_code == 429:
        raise DeliveryTemporary()
    if resp.status_code >= 500:
        raise DeliveryUncertain()
    if resp.status_code in (401, 403):
        raise DeliveryPermanent()
    if resp.status_code >= 400:
        raise DeliveryPermanent()
    return resp


def data_request(method, path, token, params=None, json_body=None, timeout=(10, 45)):
    url = f"{DATA_BASE}/{path.lstrip('/')}"
    try:
        resp = requests.request(
            method,
            url,
            headers={"Authorization": f"Bearer {token}"},
            params=params,
            json=json_body,
            timeout=timeout,
        )
    except requests.RequestException:
        raise DeliveryUncertain() from None
    return _check(resp)


def upload_video(token, metadata, raw_bytes, mimetype, timeout=(10, 300)):
    """Resumable videos.insert: init (metadata) → PUT bytes. Returns video dict."""
    init_url = f"{UPLOAD_BASE}/videos?uploadType=resumable&part=snippet,status"
    try:
        init = requests.post(
            init_url,
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json; charset=UTF-8",
                "X-Upload-Content-Type": mimetype,
                "X-Upload-Content-Length": str(len(raw_bytes)),
            },
            data=json.dumps(metadata),
            timeout=(10, 45),
        )
    except requests.RequestException:
        raise DeliveryUncertain() from None
    _check(init)
    location = init.headers.get("Location") or init.headers.get("location")
    if not location:
        raise DeliveryUncertain()
    try:
        up = requests.put(
            location,
            headers={"Content-Type": mimetype, "Content-Length": str(len(raw_bytes))},
            data=raw_bytes,
            timeout=timeout,
        )
    except requests.RequestException:
        # The video may or may not have been accepted — never blind-retry.
        raise DeliveryUncertain() from None
    _check(up)
    try:
        return up.json() or {}
    except (ValueError, TypeError):
        raise DeliveryUncertain() from None
