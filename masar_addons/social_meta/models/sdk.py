# -*- coding: utf-8 -*-
# Copyright 2026 MASAR
# License AGPL-3.0 or later.
"""Meta Facebook Business SDK adapter (official facebook-python-business-sdk).

Foundation for Graph Page / User calls. OAuth Connect still owns the browser
Login flow; this module wraps User.get_accounts, Page edges and generic Graph
calls so connectors do not hand-roll HTTP against graph.facebook.com.

References:
- https://github.com/facebook/facebook-python-business-sdk (PyPI facebook-business v26)
- examples/PageNode.py — Page node usage
- Graph User /accounts — Page ID + Page Access Token
"""
from __future__ import annotations

import logging
import os
from io import BytesIO

from odoo.addons.social.models.errors import DeliveryPermanent, DeliveryTemporary, DeliveryUncertain

_logger = logging.getLogger(__name__)

# Fallback used only if the SDK does not expose its default and no env override
# is set. The facebook-business package version tracks the Graph API version
# (SDK 26.x → Graph v26.0), so we prefer the SDK's own default at runtime.
_GRAPH_VERSION_FALLBACK = "v26.0"


def _default_graph_version():
    """Resolve the Graph API version so the SDK and our raw paths never drift.

    Order: explicit env override → the installed SDK's own API_VERSION →
    fallback constant. The SDK's ``API_VERSION`` is authoritative because a
    given facebook-business release targets one Graph version; hard-pinning a
    different string risks "unsupported version" errors after an SDK bump.
    """
    override = (os.environ.get("SOCIAL_META_GRAPH_VERSION") or "").strip()
    if override:
        return override if override.startswith("v") else f"v{override}"
    try:
        from facebook_business.api import FacebookAdsApi

        version = getattr(FacebookAdsApi, "API_VERSION", None)
        if version:
            version = str(version)
            return version if version.startswith("v") else f"v{version}"
    except Exception:
        pass
    return _GRAPH_VERSION_FALLBACK


GRAPH_VERSION = _default_graph_version()
GRAPH_BASE = f"https://graph.facebook.com/{GRAPH_VERSION}"


def _log_rate_limit(response):
    """Best-effort: warn when Meta reports high API usage (pre-empt throttling).

    Reads X-App-Usage / X-Business-Use-Case-Usage headers (percent 0-100). Never
    raises — telemetry only. Header values never contain the access token.
    """
    try:
        import json as _json

        headers = response.headers() if callable(getattr(response, "headers", None)) else {}
        peak = 0
        raw_app = headers.get("x-app-usage") or headers.get("X-App-Usage")
        if raw_app:
            usage = _json.loads(raw_app) if isinstance(raw_app, str) else raw_app
            peak = max([peak] + [int(v) for v in (usage or {}).values() if isinstance(v, (int, float))])
        raw_buc = headers.get("x-business-use-case-usage") or headers.get("X-Business-Use-Case-Usage")
        if raw_buc:
            buc = _json.loads(raw_buc) if isinstance(raw_buc, str) else raw_buc
            for entries in (buc or {}).values():
                for entry in entries or []:
                    for key in ("call_count", "total_cputime", "total_time"):
                        val = entry.get(key)
                        if isinstance(val, (int, float)):
                            peak = max(peak, int(val))
        if peak >= 90:
            _logger.warning("Meta Graph API usage high (%s%%) — throttling imminent.", peak)
    except Exception:
        pass

_RETRYABLE_CODES = frozenset({4, 17, 32, 613})


def sdk_available():
    try:
        import facebook_business  # noqa: F401

        return True
    except ImportError:
        return False


def build_api(app_id, app_secret, access_token, api_version=GRAPH_VERSION):
    """Per-call API instance (do not share a global default across Odoo workers)."""
    from facebook_business.api import FacebookAdsApi, FacebookSession

    session = FacebookSession(
        app_id=app_id or None,
        app_secret=app_secret or None,
        access_token=access_token or None,
    )
    return FacebookAdsApi(session, api_version=api_version or GRAPH_VERSION)


def raise_delivery_from_sdk(exc):
    """Map FacebookRequestError → Delivery* without leaking tokens into messages."""
    from facebook_business.exceptions import FacebookRequestError

    if not isinstance(exc, FacebookRequestError):
        raise DeliveryUncertain() from None
    status = exc.http_status()
    code = exc.api_error_code()
    if status == 429 or code in _RETRYABLE_CODES:
        raise DeliveryTemporary() from None
    try:
        if exc.api_transient_error():
            raise DeliveryTemporary() from None
    except DeliveryTemporary:
        raise
    except Exception:
        pass
    if status is not None and status >= 500:
        raise DeliveryUncertain() from None
    raise DeliveryPermanent() from None


def graph_call(api, method, path, params=None, files=None):
    """Versioned Graph call via FacebookAdsApi.call (official SDK).

    ``path`` is relative to ``/{api_version}/`` (e.g. ``me/accounts``,
    ``{page_id}/feed``).
    """
    from facebook_business.exceptions import FacebookRequestError

    parts = tuple(p for p in str(path).lstrip("/").split("/") if p)
    try:
        response = api.call(method.upper(), parts, params=dict(params or {}), files=files or {})
    except FacebookRequestError as err:
        raise_delivery_from_sdk(err)
    except Exception:
        _logger.warning("Meta Business SDK Graph call failed for %s", path)
        raise DeliveryUncertain() from None
    if response is None:
        raise DeliveryUncertain() from None
    try:
        if response.is_failure():
            err = response.error()
            if err:
                raise_delivery_from_sdk(err)
            raise DeliveryUncertain() from None
        _log_rate_limit(response)
        return response.json() or {}
    except (DeliveryTemporary, DeliveryPermanent, DeliveryUncertain):
        raise
    except (ValueError, TypeError):
        raise DeliveryUncertain() from None


def list_user_pages(api, fields=None):
    """Official ``User.get_accounts`` — same data as ``GET /me/accounts``.

    Returns plain dicts: id, name, access_token, tasks, instagram_business_account.
    ``tasks`` enables CREATE_CONTENT filtering (BrightBean meta_accounts pattern).
    """
    from facebook_business.adobjects.user import User
    from facebook_business.exceptions import FacebookRequestError

    field_list = fields or [
        "id",
        "name",
        "access_token",
        "tasks",
        "instagram_business_account{id,username,name}",
    ]
    try:
        pages = list(User(fbid="me", api=api).get_accounts(fields=field_list))
    except FacebookRequestError as err:
        raise_delivery_from_sdk(err)
    except (DeliveryTemporary, DeliveryPermanent, DeliveryUncertain):
        raise
    except Exception:
        _logger.warning("Meta Business SDK User.get_accounts failed")
        raise DeliveryUncertain() from None

    rows = []
    for page in pages:
        ig = page.get("instagram_business_account") or {}
        if hasattr(ig, "export_all_data"):
            try:
                ig = ig.export_all_data()
            except Exception:
                ig = dict(ig) if ig else {}
        elif not isinstance(ig, dict):
            try:
                ig = dict(ig)
            except Exception:
                ig = {}
        tasks = page.get("tasks")
        if tasks is not None and not isinstance(tasks, list):
            try:
                tasks = list(tasks)
            except Exception:
                tasks = None
        row = {
            "id": page.get("id"),
            "name": page.get("name"),
            "access_token": page.get("access_token"),
            "instagram_business_account": ig or {},
        }
        if tasks is not None:
            row["tasks"] = tasks
        rows.append(row)
    return rows


def subscribe_apps(api, object_id, subscribed_fields):
    """POST /{id}/subscribed_apps — register webhook fields (BrightBean pattern)."""
    fields = (
        ",".join(subscribed_fields)
        if isinstance(subscribed_fields, (list, tuple))
        else str(subscribed_fields or "")
    )
    return graph_call(
        api,
        "POST",
        f"{object_id}/subscribed_apps",
        params={"subscribed_fields": fields},
    )


def debug_token(api, input_token, app_id, app_secret):
    """Inspect token validity / scopes via /debug_token (app access token)."""
    app_token = f"{app_id}|{app_secret}"
    # Temporary API with app token for debug_token edge.
    debug_api = build_api(app_id, app_secret, app_token)
    return graph_call(
        debug_api,
        "GET",
        "debug_token",
        params={"input_token": input_token},
    )


def page_create_feed(api, page_id, message):
    """Page.create_feed — official Page node publish (text)."""
    from facebook_business.adobjects.page import Page
    from facebook_business.exceptions import FacebookRequestError

    try:
        result = Page(str(page_id), api=api).create_feed(params={"message": message or ""})
    except FacebookRequestError as err:
        raise_delivery_from_sdk(err)
    except Exception:
        raise DeliveryUncertain() from None
    if result is None:
        return {}
    try:
        return dict(result)
    except Exception:
        return {"id": result.get("id") if hasattr(result, "get") else None}


def page_create_photo(api, page_id, caption, raw_bytes, filename="image.jpg", mimetype="image/jpeg"):
    """Multipart photo upload on the Page photos edge (SDK ``api.call`` + files)."""
    buf = BytesIO(raw_bytes)
    return graph_call(
        api,
        "POST",
        f"{page_id}/photos",
        params={"caption": caption or "", "published": "true"},
        files={"source": (filename, buf, mimetype)},
    )


def page_create_video(api, page_id, description, raw_bytes, filename="video.mp4", mimetype="video/mp4"):
    """Multipart video upload on the Page videos edge."""
    buf = BytesIO(raw_bytes)
    return graph_call(
        api,
        "POST",
        f"{page_id}/videos",
        params={"description": description or ""},
        files={"source": (filename, buf, mimetype)},
    )


def comment_create(api, object_id, message):
    """Comment.create_comment on a post / comment id."""
    from facebook_business.adobjects.comment import Comment
    from facebook_business.exceptions import FacebookRequestError

    try:
        result = Comment(str(object_id), api=api).create_comment(params={"message": message or ""})
    except FacebookRequestError as err:
        raise_delivery_from_sdk(err)
    except Exception:
        return graph_call(api, "POST", f"{object_id}/comments", params={"message": message or ""})
    if result is None:
        return {}
    try:
        return dict(result)
    except Exception:
        return {"id": result.get("id") if hasattr(result, "get") else None}
