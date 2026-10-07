# -*- coding: utf-8 -*-
# Copyright 2026 MASAR
# License AGPL-3.0 or later.
from markupsafe import Markup, escape

from odoo import http
from odoo.exceptions import AccessError, UserError
from odoo.http import request


class SocialMetaOAuthController(http.Controller):
    @http.route(
        "/social/meta/oauth/callback",
        type="http",
        auth="user",
        methods=["GET"],
        csrf=False,
    )
    def meta_oauth_callback(self, code=None, state=None, error=None, error_description=None, **kwargs):
        """Facebook redirects here after the user authorizes the Meta app."""
        Oauth = request.env["social.meta.oauth"]
        try:
            if error:
                raise UserError(error_description or error)
            if not code or not state:
                raise UserError(request.env._("Missing OAuth code from Meta."))
            payload = Oauth._parse_state(state)
            media_type = payload.get("media_type")
            company = request.env["res.company"].browse(int(payload.get("company_id") or 0))
            env = request.env
            if company and company.exists():
                env = env(context=dict(env.context, allowed_company_ids=[company.id]))
                Oauth = env["social.meta.oauth"]
            rows = Oauth.exchange_code(code, media_type)
            if len(rows) == 1:
                wiz = env["social.meta.link.wizard"].create(
                    {
                        "media_type": media_type,
                        "line_ids": [
                            (
                                0,
                                0,
                                {
                                    "name": rows[0]["name"],
                                    "external_id": rows[0]["external_id"],
                                    "page_id": rows[0].get("page_id"),
                                    "access_token": rows[0]["access_token"],
                                },
                            )
                        ],
                    }
                )
                action = wiz._link_line(wiz.line_ids[:1])
                return request.redirect(
                    "/web#id=%d&model=social.account&view_type=form" % action["res_id"]
                )
            action = Oauth.open_page_wizard(media_type, rows)
            action_id = env.ref("social_meta.action_social_meta_link_wizard").id
            return request.redirect(
                "/web#id=%d&action=%d&model=social.meta.link.wizard&view_type=form"
                % (action["res_id"], action_id)
            )
        except (UserError, AccessError) as err:
            message = escape(str(err))
            body = Markup(
                "<html><body style='font-family:sans-serif;padding:2rem'>"
                "<h2>Meta link failed</h2><p>%s</p>"
                "<p><a href='/web#action=social.action_social_media'>Back to Social Media</a></p>"
                "</body></html>"
            ) % message
            return request.make_response(body, headers=[("Content-Type", "text/html; charset=utf-8")])
