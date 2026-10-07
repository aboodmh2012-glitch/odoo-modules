"""MASAR presentation over Odoo's native recruitment routes and form."""

from odoo import http
from odoo.addons.website_hr_recruitment.controllers.main import WebsiteHrRecruitment
from odoo.http import request


class MasarCareers(WebsiteHrRecruitment):
    @http.route()
    def jobs(self, **kwargs):
        # Keep native fuzzy search, filters, website scoping and pagination.
        response = super().jobs(**kwargs)
        return request.render("masar_website.masar_jobs", response.qcontext)

    @http.route(["/careers", "/careers/page/<int:page>"], type="http",
                auth="public", website=True, sitemap=True)
    def careers(self, page=1, **kwargs):
        return self.jobs(page=page, **kwargs)

    @http.route()
    def job(self, job, **kwargs):
        response = super().job(job, **kwargs)
        return request.render("masar_website.masar_job_detail", response.qcontext)

    @http.route("/job-thank-you", type="http", auth="public", website=True, sitemap=False)
    def application_confirmation(self, **kwargs):
        return request.render("masar_website.masar_job_confirmation", {
            "application_received": request.session.get("form_builder_model_model") == "hr.applicant",
        })
