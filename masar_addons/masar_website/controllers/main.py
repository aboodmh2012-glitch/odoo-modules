import logging
import re
from urllib.parse import urlsplit

from odoo import http
from odoo.addons.account.controllers.terms import TermsController
from odoo.http import request

_logger = logging.getLogger(__name__)

_EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class MasarNewsletter(http.Controller):
    @http.route(
        "/masar/newsletter",
        type="http",
        auth="public",
        website=True,
        methods=["POST"],
        csrf=True,
    )
    def newsletter(self, email=None, company_url=None, **kwargs):
        """Subscribe a public website visitor to the MASAR mailing list.

        Newsletter subscriptions belong to Email Marketing, not CRM. The
        honeypot field ``company_url`` is left empty by the real form.
        """
        status = "invalid"
        cleaned = (email or "").strip().lower()
        if company_url:
            status = "ok"
        elif _EMAIL.match(cleaned) and len(cleaned) <= 254:
            try:
                MailingList = request.env["mailing.list"].sudo()
                MailingContact = request.env["mailing.contact"].sudo()

                mailing_list = MailingList.search(
                    [("name", "=", "MASAR Newsletter Subscribers")], limit=1
                )
                if not mailing_list:
                    mailing_list = MailingList.create(
                        {"name": "MASAR Newsletter Subscribers"}
                    )

                contact = MailingContact.search(
                    [("email", "=ilike", cleaned)], limit=1
                )
                if not contact:
                    contact = MailingContact.create(
                        {
                            "name": cleaned,
                            "email": cleaned,
                            "list_ids": [(4, mailing_list.id)],
                        }
                    )
                elif mailing_list not in contact.list_ids:
                    contact.write({"list_ids": [(4, mailing_list.id)]})

                status = "ok"
            except Exception:
                _logger.exception("MASAR newsletter subscription was not stored")
                status = "invalid"
        return request.redirect(self._back(status))

    def _back(self, status):
        ref = request.httprequest.referrer or ""
        parts = urlsplit(ref)
        host = request.httprequest.host
        if parts.netloc and parts.netloc != host:
            path = "/"
        else:
            path = parts.path or "/"
        return "%s?newsletter=%s#newsletter" % (path, status)


class MasarLegal(http.Controller):
    @http.route("/cookie-policy", type="http", auth="public", website=True, sitemap=True)
    def cookie_policy(self, **kwargs):
        return request.render("masar_website.masar_cookie_policy_page")


class MasarTermsController(TermsController):
    @http.route()
    def terms_conditions(self, **kwargs):
        return request.redirect("/website-terms", code=302)
