"""Dependency-light contract checks. Run directly; no production data writes.

Framework boundaries are mocked. Live rendering is checked separately after
deployment. Full native recruitment submit/attachment tests belong to Odoo.
"""
import importlib.util
from pathlib import Path
import sys
from types import ModuleType, SimpleNamespace
import unittest
from xml.etree import ElementTree

ROOT = Path(__file__).resolve().parents[1]


class NativeModel:
    def _search_get_detail(self, website, order, options):
        return {"base_domain": [[("website_id", "in", [False, website])]],
                "search_fields": ["name", "description"], "mapping": {"name": "native"}}


class NativeController:
    def jobs(self, **kwargs):
        return SimpleNamespace(qcontext={"jobs": "native results", "pager": {"page_count": 2},
                                        "search": kwargs.get("search"), "page": kwargs.get("page")})

    def job(self, job, **kwargs):
        return SimpleNamespace(qcontext={"job": job, "main_object": job})


def route(*args, **kwargs):
    def decorate(fn):
        fn.test_route = (args, kwargs)
        return fn
    return decorate


odoo = ModuleType("odoo")
odoo.models = SimpleNamespace(Model=NativeModel)
odoo.api = SimpleNamespace(model=lambda method: method)
odoo.fields = SimpleNamespace(Date=SimpleNamespace(today=lambda: None))
odoo.http = SimpleNamespace(route=route)
sys.modules["odoo"] = odoo
sys.modules["odoo.http"] = SimpleNamespace(request=SimpleNamespace(render=lambda template, context: (template, context)))
sys.modules["odoo.http"].request.session = {}
sys.modules["odoo.addons.website_hr_recruitment.controllers.main"] = SimpleNamespace(WebsiteHrRecruitment=NativeController)


def load(path):
    spec = importlib.util.spec_from_file_location(path.stem, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


model = load(ROOT / "models/hr_job.py")
controller = load(ROOT / "controllers/careers.py")
copy = load(ROOT / "copy/careers.py")


class CareersContract(unittest.TestCase):
    def test_definition_list_fields_use_supported_widget_containers(self):
        tree = ElementTree.parse(ROOT / "views/templates_careers.xml")
        for node in tree.iter():
            self.assertFalse(node.tag in {"dd", "dt"} and "t-field" in node.attrib)

    def test_published_only_before_search_and_pager(self):
        detail = model.HrJob()._search_get_detail(7, "sequence", {})
        records = [dict(website_id=7, website_published=True, active=True),
                   dict(website_id=7, website_published=False, active=True),
                   dict(website_id=7, website_published=True, active=False),
                   dict(website_id=8, website_published=True, active=True)]
        def matches(row):
            return all((row[field] in value if op == "in" else row[field] == value)
                       for group in detail["base_domain"] for field, op, value in group)
        self.assertEqual([row for row in records if matches(row)], records[:1])
        self.assertEqual(detail["search_fields"], ["name", "description"])
        self.assertEqual(detail["mapping"], {"name": "native"})

    def test_careers_preserves_native_context_and_pagination(self):
        template, context = controller.MasarCareers().careers(page=2, search="analyst")
        self.assertEqual(template, "masar_website.masar_jobs")
        self.assertEqual(context["page"], 2)
        self.assertEqual(context["search"], "analyst")
        self.assertEqual(context["jobs"], "native results")

    def test_detail_keeps_native_main_object(self):
        job = object()
        template, context = controller.MasarCareers().job(job)
        self.assertEqual(template, "masar_website.masar_job_detail")
        self.assertIs(context["job"], job)
        self.assertIs(context["main_object"], job)

    def test_no_override_of_native_application_or_submission(self):
        self.assertNotIn("jobs_apply", controller.MasarCareers.__dict__)
        self.assertNotIn("insert_record", controller.MasarCareers.__dict__)

    def test_public_careers_and_pagination_routes(self):
        args, kwargs = controller.MasarCareers.careers.test_route
        self.assertEqual(args[0], ["/careers", "/careers/page/<int:page>"])
        self.assertEqual(kwargs["auth"], "public")
        self.assertTrue(kwargs["website"])

    def test_confirmation_does_not_claim_success_without_submission_session(self):
        sys.modules["odoo.http"].request.session = {}
        template, context = controller.MasarCareers().application_confirmation()
        self.assertEqual(template, "masar_website.masar_job_confirmation")
        self.assertFalse(context["application_received"])
        sys.modules["odoo.http"].request.session = {"form_builder_model_model": "hr.applicant"}
        self.assertTrue(controller.MasarCareers().application_confirmation()[1]["application_received"])
        sys.modules["odoo.http"].request.session = {"form_builder_model_model": "crm.lead"}
        self.assertFalse(controller.MasarCareers().application_confirmation()[1]["application_received"])

    def test_default_copy_comparison_ignores_markup_and_entities(self):
        self.assertEqual(model.normalized_copy('<p data-oe-id="5">Hello&nbsp; <b>world</b></p>'),
                         model.normalized_copy('<div>Hello world</div>'))
        self.assertNotEqual(model.normalized_copy('<p>Specific requirements</p>'),
                            model.normalized_copy('<p>Demo requirements</p>'))

    def test_default_copy_uses_both_supported_languages(self):
        item = model.HrJob()
        item.env = SimpleNamespace(lang="ar_001")
        item.with_context = lambda lang: SimpleNamespace(reference=lambda: "English demo" if lang == "en_US" else "نص تجريبي")
        self.assertTrue(item._masar_is_default_copy('<p>English demo</p>', "reference"))
        self.assertTrue(item._masar_is_default_copy('<p>نص تجريبي</p>', "reference"))
        self.assertFalse(item._masar_is_default_copy('<p>Actual role requirements</p>', "reference"))
        self.assertTrue(item._masar_is_default_copy('', "reference"))

    def test_bilingual_copy_keys_match_and_returns_fresh_dict(self):
        self.assertEqual(set(copy.EN), set(copy.AR))
        self.assertEqual(copy.get_careers_copy("ar_001")["submit"], "إرسال طلب التوظيف")
        result = copy.get_careers_copy("en_US")
        result["submit"] = "changed"
        self.assertEqual(copy.get_careers_copy("en_US")["submit"], "Submit application")


if __name__ == "__main__":
    unittest.main(verbosity=2)
