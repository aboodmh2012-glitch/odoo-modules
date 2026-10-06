# Copyright 2026 MASAR
# License AGPL-3.0 or later.
import logging
from markupsafe import Markup, escape

from odoo import http
from odoo.exceptions import AccessError, UserError
from odoo.http import request

_logger = logging.getLogger(__name__)


class SocialTiktokOAuthController(http.Controller):
    @http.route(
        "/social/tiktok/oauth/callback",
        type="http",
        auth="user",
        methods=["GET"],
        csrf=False,
    )
    def tiktok_oauth_callback(self, code=None, state=None, error=None, **kwargs):
        Oauth = request.env["social.tiktok.oauth"]
        try:
            if error:
                raise UserError(error)
            if not code or not state:
                raise UserError(request.env._("Missing authorization code from TikTok."))
            payload = Oauth._parse_state(state)
            env = request.env
            company = env["res.company"].browse(int(payload.get("company_id") or 0))
            if company and company.exists():
                env = env(context=dict(env.context, allowed_company_ids=[company.id]))
                Oauth = env["social.tiktok.oauth"]
            access, refresh, expires_in, rows = Oauth.exchange_code(code)
            # TikTok authorizes exactly one creator account.
            wiz = env["social.tiktok.link.wizard"].create(
                {
                    "access_token": access,
                    "refresh_token": refresh,
                    "expires_in": expires_in,
                    "line_ids": [(0, 0, {"name": rows[0]["name"], "external_id": rows[0]["external_id"]})],
                }
            )
            action = wiz._link_line(wiz.line_ids[:1])
            return request.redirect(
                "/web#id=%d&model=social.account&view_type=form" % action["res_id"]
            )
        except (UserError, AccessError) as err:
            body = Markup(
                "<html><body style='font-family:sans-serif;padding:2rem;direction:rtl'>"
                "<h2>TikTok link failed</h2><p>%s</p>"
                "<p><a href='/odoo/social'>Back to Social</a></p></body></html>"
            ) % escape(str(err))
            return request.make_response(body, headers=[("Content-Type", "text/html; charset=utf-8")])
        except Exception:
            _logger.warning("TikTok OAuth callback failed", exc_info=True)
            body = Markup(
                "<html><body style='font-family:sans-serif;padding:2rem;direction:rtl'>"
                "<h2>TikTok link failed</h2><p>Could not complete TikTok linking. Try again.</p>"
                "<p><a href='/odoo/social'>Back to Social</a></p></body></html>"
            )
            return request.make_response(body, headers=[("Content-Type", "text/html; charset=utf-8")])
