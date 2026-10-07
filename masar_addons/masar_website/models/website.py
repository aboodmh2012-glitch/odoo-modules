import logging

from odoo import api, models

from ..copy.registry import get_copy, is_current, normalize_public_path
from ..copy.careers import get_careers_copy

_logger = logging.getLogger(__name__)

# Public URLs owned by this addon, mapped to catalog page keys.
# Home is stored under ``home`` rather than ``pages``.
_PAGE_URLS = (
    ("/", "home"),
    ("/about", "about"),
    ("/solutions", "services"),
    ("/business", "business"),
    ("/individuals", "individuals"),
    ("/developers", "developers"),
    ("/support", "support"),
    ("/security-compliance", "security"),
    ("/privacy", "privacy"),
    ("/contactus", "contact"),
    ("/website-terms", "terms"),
    ("/cookie-policy", "cookies"),
    ("/leadership", "leadership"),
    ("/careers", "careers"),
    ("/news", "news"),
    ("/status", "status"),
)


class Website(models.Model):
    _inherit = "website"

    def masar_careers_copy(self):
        return get_careers_copy(self.env.lang)

    def get_masar_meta_title(self, lang_code=None):
        """Public site title used by layout and SEO helpers."""
        return get_copy(lang_code or self.env.lang)["brand"]["meta_title"]

    def _masar_lang_prefixes(self):
        prefixes = set()
        for lang in self.language_ids:
            url_code = getattr(lang, "url_code", None) or ""
            if url_code:
                prefixes.add(url_code.lower())
            code = (lang.code or "").split("_")[0].lower()
            if code:
                prefixes.add(code)
        return prefixes

    def masar_public(self):
        """Catalog for the active language, plus request-aware nav state.

        Templates read this dict only. They do not branch on language and they
        do not embed copy.
        """
        self.ensure_one()
        data = get_copy(self.env.lang)
        path = "/"
        try:
            from odoo.http import request

            httprequest = getattr(request, "httprequest", None)
            if httprequest is not None:
                path = httprequest.path or "/"
        except Exception:
            path = "/"
        path = normalize_public_path(path, self._masar_lang_prefixes())
        for item in data.get("nav", []):
            item["current"] = is_current(path, item.get("href"))
        data["_meta"]["path"] = path
        return data

    @api.model
    def masar_apply_public_identity(self):
        """Sync website name, languages, menus, and SEO from the copy catalog.

        Marked as a model method so Odoo 19 can call it from XML ``<function>``
        without a record id. Safe to run on every module update. English stays
        the website default when that language is installed; other installed
        languages are kept.
        """
        env = self.env
        Website = env["website"].sudo()
        Menu = env["website.menu"].sudo()
        Page = env["website.page"].sudo()
        Lang = env["res.lang"].sudo()

        en_copy = get_copy("en_US")
        ar_copy = get_copy("ar_001")
        en_lang = Lang.search([("code", "=", "en_US"), ("active", "=", True)], limit=1)
        ar_lang = Lang.search([("code", "=", "ar_001"), ("active", "=", True)], limit=1)

        hide_urls = {"/shop", "/event", "/slides", "/jobs"}
        Menu.search([("url", "in", list(hide_urls))]).unlink()
        Menu.search([("url", "=", "/contactus")]).write({"is_visible": False})

        ar_nav = {item["href"]: item for item in ar_copy["nav"]}

        for website in Website.search([]):
            website.write({"name": en_copy["brand"]["name"]})
            lang_ids = [lang.id for lang in (en_lang, ar_lang) if lang]
            if lang_ids and "language_ids" in website._fields:
                website.write({"language_ids": [(4, lang_id) for lang_id in lang_ids]})
            if en_lang and "default_lang_id" in website._fields:
                website.default_lang_id = en_lang.id
            elif en_lang and "default_lang_code" in website._fields:
                website.default_lang_code = en_lang.code

            root = website.menu_id
            if not root:
                continue
            for sequence, item in enumerate(en_copy["nav"], start=1):
                menu = Menu.search(
                    [
                        ("url", "=", item["href"]),
                        ("website_id", "=", website.id),
                    ],
                    limit=1,
                )
                vals = {
                    "name": item["label"],
                    "url": item["href"],
                    "parent_id": root.id,
                    "website_id": website.id,
                    "sequence": sequence * 10,
                    "is_visible": True,
                }
                if menu:
                    menu.write(vals)
                else:
                    menu = Menu.create(vals)
                ar_item = ar_nav.get(item["href"])
                if ar_item and ar_lang:
                    try:
                        menu.with_context(lang="ar_001").write({"name": ar_item["label"]})
                    except Exception:
                        _logger.warning("MASAR menu translation skipped for %s", item["href"])

        for url, key in _PAGE_URLS:
            page = Page.search([("url", "=", url)], limit=1)
            if not page:
                continue
            en_seo = _seo_pair(en_copy, key)
            page.write(en_seo)
            if ar_lang:
                try:
                    page.with_context(lang="ar_001").write(_seo_pair(ar_copy, key))
                except Exception:
                    _logger.warning("MASAR page translation skipped for %s", url)

        self._masar_restore_homepage_template()
        return True

    @api.model
    def _masar_restore_homepage_template(self):
        """Serve the module homepage instead of an empty website-specific copy.

        Odoo prefers a website-specific view with the same ``t-name`` over
        ``website.homepage``. That copy does not receive the MASAR Pay inherit,
        so ``/`` stays an empty ``oe_structure``. Deactivate those copies and
        point ``/`` pages at the module view.
        """
        homepage = self.env.ref("website.homepage", raise_if_not_found=False)
        if not homepage:
            return
        View = self.env["ir.ui.view"].sudo()
        copies = View.search(
            [
                ("id", "!=", homepage.id),
                ("website_id", "!=", False),
                ("inherit_id", "=", False),
                ("arch_db", "ilike", 't-name="website.homepage"'),
            ]
        )
        for view in copies:
            arches = [view.arch_db or ""]
            arches.extend(child.arch_db or "" for child in view.inherit_children_ids)
            if any("masar-hero--home" in arch for arch in arches):
                continue
            view.active = False
        pages = self.env["website.page"].sudo().search([("url", "=", "/")])
        for page in pages:
            view = page.view_id
            if view and (not view.active or view in copies):
                page.view_id = homepage


def _seo_pair(catalog, key):
    if key == "home":
        node = catalog["home"]
    else:
        node = catalog["pages"][key]
    return {
        "website_meta_title": node["seo_title"],
        "website_meta_description": node["seo_description"],
    }
