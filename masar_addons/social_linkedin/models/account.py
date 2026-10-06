# Copyright 2026 MASAR
# License AGPL-3.0 or later.
from odoo import api, fields, models, _
from odoo.exceptions import AccessError, UserError
from odoo.addons.social.models.errors import DeliveryPermanent, DeliveryUncertain

from . import api as li_api

# LinkedIn commentary hard limit.
COMMENTARY_MAX = 3000


class SocialAccount(models.Model):
    _inherit = "social.account"

    platform = fields.Selection(
        selection_add=[("linkedin", "LinkedIn Organization")],
        ondelete={"linkedin": "set default"},
    )

    # ---- helpers -------------------------------------------------------------
    def _linkedin_author(self):
        self.ensure_one()
        return f"urn:li:organization:{self.external_account_id}"

    def _linkedin_version(self):
        return li_api.api_version(self.env)

    # ---- publish contract ----------------------------------------------------
    def _validate_target(self, target):
        if self.platform != "linkedin":
            return super()._validate_target(target)
        self._secret()  # ensure a token is present on the account
        text = (target.platform_content or target.post_id.content or "").strip()
        if target.post_id.attachment_ids:
            raise UserError(
                _("The LinkedIn connector publishes text posts only for now; remove attachments.")
            )
        if not text:
            raise UserError(_("Write the post text before publishing to LinkedIn."))
        if len(text) > COMMENTARY_MAX:
            raise UserError(_("LinkedIn text exceeds %s characters.", COMMENTARY_MAX))

    def _publish_target(self, target):
        if self.platform != "linkedin":
            return super()._publish_target(target)
        text = (target.platform_content or target.post_id.content or "").strip()
        body = {
            "author": self._linkedin_author(),
            "commentary": text,
            "visibility": "PUBLIC",
            "distribution": {
                "feedDistribution": "MAIN_FEED",
                "targetEntities": [],
                "thirdPartyDistributionChannels": [],
            },
            "lifecycleState": "PUBLISHED",
            "isReshareDisabledByAuthor": False,
        }
        resp = li_api.rest_request(
            "POST", "posts", self._secret(), self._linkedin_version(), json=body
        )
        urn = resp.headers.get("x-restli-id")
        if not urn:
            try:
                urn = (resp.json() or {}).get("id")
            except (ValueError, TypeError):
                urn = None
        if not urn:
            raise DeliveryUncertain()
        return {"id": urn, "url": f"https://www.linkedin.com/feed/update/{urn}"}

    # ---- reply contract (comments — LinkedIn has no org DM API) ---------------
    def _send_reply(self, conversation, text):
        if self.platform != "linkedin":
            return super()._send_reply(conversation, text)
        if conversation.kind not in ("comment", "mention") or not (text or "").strip():
            raise DeliveryPermanent()
        if len(text) > COMMENTARY_MAX:
            raise DeliveryPermanent()
        share_urn = conversation.external_conversation_id
        body = {
            "actor": self._linkedin_author(),
            "object": share_urn,
            "message": {"text": text},
        }
        resp = li_api.rest_request(
            "POST",
            f"socialActions/{share_urn}/comments",
            self._secret(),
            self._linkedin_version(),
            json=body,
        )
        cid = resp.headers.get("x-restli-id")
        if not cid:
            try:
                data = resp.json() or {}
                cid = data.get("$URN") or data.get("id")
            except (ValueError, TypeError):
                cid = None
        if not cid:
            raise DeliveryUncertain()
        return {"id": str(cid)}

    # ---- insights (followers) ------------------------------------------------
    def action_linkedin_followers(self):
        """Admin action: refresh follower count via networkSizes (real Insights)."""
        self.ensure_one()
        if not self.env.user.has_group("social.group_social_admin"):
            raise UserError(_("Only Social Connection Administrators can read LinkedIn insights."))
        try:
            resp = li_api.rest_request(
                "GET",
                f"networkSizes/{self._linkedin_author()}",
                self._secret(),
                self._linkedin_version(),
                params={"edgeType": "COMPANY_FOLLOWED_BY_MEMBER"},
            )
            count = (resp.json() or {}).get("firstDegreeSize")
        except (DeliveryPermanent, DeliveryUncertain):
            raise UserError(_("Could not read LinkedIn follower count. Re-link the account."))
        self.sudo().write({"last_sync_at": fields.Datetime.now(), "connection_status": "connected"})
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("LinkedIn"),
                "message": _("Followers: %s", count if count is not None else _("(not returned)")),
                "type": "success",
                "sticky": False,
            },
        }

    # ---- entry point ---------------------------------------------------------
    @api.model
    def action_connect_linkedin(self, *args, **kwargs):
        del args, kwargs
        self.env["social.account"].check_access("create")
        if "social.linkedin.oauth" not in self.env:
            raise UserError(_("Install Social · LinkedIn first."))
        return self.env["social.linkedin.oauth"].action_start()

    def action_connect_provider(self, *args, **kwargs):
        if self.platform == "linkedin" and "social.linkedin.oauth" in self.env:
            if not self.env.user.has_group("social.group_social_admin"):
                raise AccessError(_("Only Social Connection Administrators can link accounts."))
            return self.env["social.linkedin.oauth"].action_start()
        return super().action_connect_provider(*args, **kwargs)
