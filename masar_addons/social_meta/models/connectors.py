# -*- coding: utf-8 -*-
# Copyright 2026 MASAR
# License AGPL-3.0 or later.
"""BrightBean-inspired Meta connector helpers (patterns only — not a BrightBean fork).

Reference: https://github.com/brightbeanxyz/brightbean-studio/tree/main/providers
(meta_oauth, meta_accounts, meta_messaging, facebook/instagram subscribed_apps).
"""
from __future__ import annotations

# Re-ask declined permissions on reconnect (BrightBean FACEBOOK_LOGIN_EXTRA_PARAMS).
FACEBOOK_LOGIN_EXTRA_PARAMS = {"auth_type": "rerequest"}

# Page webhook fields after OAuth link (BrightBean FACEBOOK_WEBHOOK_FIELDS).
FACEBOOK_WEBHOOK_FIELDS = ("feed", "mention", "messages")

# IG Business via Facebook Login — comments/mentions only on the IG user node.
# Messaging scopes for IG Direct need a separate Login path; keep publish+comments tight.
INSTAGRAM_WEBHOOK_FIELDS = ("comments", "mentions", "live_comments")

# Where the person's platform-scoped ID hides when building Messenger replies.
_RECIPIENT_KEYS = ("recipient_id", "sender", "from", "sender_id")


def facebook_login_params(*, client_id, redirect_uri, state, scopes, config_id=""):
    """Query params for facebook.com Login dialog (BrightBean meta_oauth pattern)."""
    params = {
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "state": state,
        "response_type": "code",
        **FACEBOOK_LOGIN_EXTRA_PARAMS,
    }
    if config_id:
        params["config_id"] = config_id
        # Login for Business defaults to token response; force code for our callback.
        params["override_default_response_type"] = "true"
    else:
        params["scope"] = ",".join(scopes) if isinstance(scopes, (list, tuple)) else scopes
    return params


def page_can_publish(page):
    """Reject Pages without CREATE_CONTENT (BrightBean meta_accounts.page_can_publish).

    Omitted ``tasks`` → unknown / keep historical assume-publishable.
    Empty ``tasks`` → Meta says no tasks → not publishable.
    """
    if not isinstance(page, dict):
        return True
    if "tasks" not in page:
        return True
    return "CREATE_CONTENT" in (page.get("tasks") or [])


def resolve_recipient_id(extra):
    """PSID / IGSID for Messenger Send API (BrightBean meta_messaging)."""
    extra = extra or {}
    for key in _RECIPIENT_KEYS:
        value = extra.get(key)
        if isinstance(value, dict):
            value = value.get("id")
        if value:
            return str(value)
    return ""


def build_send_payload(recipient_id, text, *, human_agent=False):
    """Messenger Send API body (BrightBean meta_messaging.build_send_payload)."""
    payload = {
        "recipient": {"id": recipient_id},
        "message": {"text": text},
        "messaging_type": "MESSAGE_TAG" if human_agent else "RESPONSE",
    }
    if human_agent:
        payload["tag"] = "HUMAN_AGENT"
    return payload
