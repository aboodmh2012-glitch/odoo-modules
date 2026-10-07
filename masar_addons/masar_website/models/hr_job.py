"""Public listings and display-only filtering of Odoo's demo recruitment copy."""

import os
import re
import unicodedata
from html import unescape
from urllib.parse import quote, unquote, urlencode

from odoo import api, fields, models


def normalized_copy(value):
    """Compare template copy despite editor attributes and whitespace changes."""
    return " ".join(unescape(re.sub(r"<[^>]+>", " ", value or "")).split())


def english_job_slug(name, identifier):
    """Keep the English part of bilingual job names; never encode Arabic slugs."""
    ascii_name = unicodedata.normalize("NFKD", name or "").encode("ascii", "ignore").decode()
    slug_name = re.sub(r"[^a-z0-9]+", "-", ascii_name.lower()).strip("-")
    if not re.search(r"[a-z]", slug_name):
        slug_name = "job"
    return f"{slug_name}-{identifier}"


class HrJob(models.Model):
    _inherit = "hr.job"

    def masar_public_requirements(self):
        """Publish only selected qualification catalogue labels, never HR records."""
        self.ensure_one()
        self.check_access("read")
        result = {"degree": "", "groups": []}
        if not self.website_published or not self.active:
            return result
        selected = self.sudo()
        if "expected_degree" in self._fields:
            result["degree"] = selected.expected_degree.name or ""
        if "job_skill_ids" not in self._fields:
            return result
        today = fields.Date.today()
        groups = {}
        seen = set()
        for requirement in selected.job_skill_ids:
            if (not requirement.skill_type_id.active
                    or (requirement.valid_from and requirement.valid_from > today)
                    or (requirement.valid_to and requirement.valid_to < today)):
                continue
            skill = requirement.skill_id
            if not skill or skill.id in seen:
                continue
            seen.add(skill.id)
            group = groups.setdefault(requirement.skill_type_id.id, {
                "name": requirement.skill_type_id.name or "", "skills": []})
            group["skills"].append({"name": skill.name or "",
                                    "level": requirement.skill_level_id.name or ""})
        result["groups"] = list(groups.values())
        return result

    def masar_english_slug(self):
        self.ensure_one()
        if not self.id:
            raise ValueError("Cannot slug a job without an ID")
        # Fixed language keeps the native converter, sitemap and copied URL in
        # agreement, including while the visitor reads the Arabic page.
        return english_job_slug(self.with_context(lang="en_US").name, self.id)

    def masar_public_contract_type_name(self):
        self.ensure_one()
        self.check_access("read")
        contract_type = self.contract_type_id
        if not contract_type:
            return ""
        # Only a published role's selected catalogue label is public. Keep the
        # job, other HR records and all write access under their native ACLs.
        if self.website_published and self.active:
            return contract_type.sudo().name
        return contract_type.name

    @api.model
    def _search_get_detail(self, website, order, options):
        detail = super()._search_get_detail(website, order, options)
        # Admins can preview a draft's own URL, but the public careers list must
        # never advertise drafts. Apply before search, counts and pagination.
        detail["base_domain"].append([("website_published", "=", True), ("active", "=", True)])
        return detail

    def _masar_is_default_copy(self, value, factory):
        if not normalized_copy(value):
            return True
        for language in dict.fromkeys((self.env.lang, "en_US", "ar_001")):
            reference = getattr(self.with_context(lang=language), factory)()
            if normalized_copy(value) == normalized_copy(reference):
                return True
        return False

    def masar_has_website_description(self):
        self.ensure_one()
        return not self._masar_is_default_copy(
            self.website_description, "_get_default_website_description")

    def masar_has_process_details(self):
        self.ensure_one()
        return not self._masar_is_default_copy(self.job_details, "_get_default_job_details")

    def masar_facebook_share_url(self):
        """Share this published role, rather than the careers listing page."""
        self.ensure_one()
        if not self.website_published or not self.active:
            return False
        url = self.masar_public_share_url()
        return "https://www.facebook.com/sharer/sharer.php?" + urlencode({"u": url})

    def masar_public_share_url(self):
        self.ensure_one()
        website = self.env["website"].get_current_website()
        path = self.env["ir.http"]._url_for(self.website_url)
        # Copy an ASCII URL so mobile composers do not split a mixed RTL/LTR
        # slug. Normalize existing escapes before quoting to avoid %25 encoding.
        path = quote(unquote(path), safe="/")
        return website.get_base_url().rstrip("/") + path

    def masar_share_description(self, limit=300):
        self.ensure_one()
        value = self.description or (self.website_description if self.masar_has_website_description() else "")
        text = normalized_copy(value)
        if limit is not None and len(text) > limit:
            return text[:limit].rsplit(" ", 1)[0] + "…"
        return text

    def _default_website_meta(self):
        meta = super()._default_website_meta()
        self.ensure_one()
        description = self.masar_share_description()
        image = self.env["website"].get_current_website().get_base_url().rstrip("/") + "/masar_website/static/src/img/careers-share-20261004.png"
        title = self.name + " | MASAR Pay"
        meta["default_opengraph"].update({"og:title": title, "og:description": description, "og:url": self.masar_public_share_url(), "og:image": image, "og:image:type": "image/png", "og:image:width": "1734", "og:image:height": "907", "og:image:alt": "وظيفة شاغرة | JOB VACANCY | MASAR Pay"})
        meta["default_twitter"].update({"twitter:title": title, "twitter:description": description, "twitter:image": image})
        # Reuse MASAR's real Meta application ID. Never substitute a Page ID,
        # app secret or placeholder just to suppress the debugger warning.
        app_id = (os.environ.get("SOCIAL_META_APP_ID") or "").strip() or (
            self.env["ir.config_parameter"].sudo().get_param("social.meta_app_id") or ""
        ).strip()
        if re.fullmatch(r"[0-9]+", app_id):
            meta["default_opengraph"]["fb:app_id"] = app_id
        meta["default_meta_description"] = description
        return meta
