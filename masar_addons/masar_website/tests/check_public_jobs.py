"""Public ACL boundary and native English slug regression checks (no DB)."""
import ast
from pathlib import Path
from types import SimpleNamespace as NS
import re
import unicodedata
import unittest
from xml.etree import ElementTree

ROOT = Path(__file__).resolve().parents[1]
tree = ast.parse((ROOT / "models/hr_job.py").read_text())
cls = next(n for n in tree.body if isinstance(n, ast.ClassDef))
methods = [n for n in cls.body if isinstance(n, ast.FunctionDef)
           and n.name in {"masar_public_contract_type_name", "masar_english_slug"}]
helper = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "english_job_slug")
ns = {"re": re, "unicodedata": unicodedata}
exec(compile(ast.Module(body=[helper, *methods], type_ignores=[]), "hr_job.py", "exec"), ns)


class AccessDenied(Exception):
    pass


class ContractType:
    def __init__(self):
        self.elevations = 0

    @property
    def name(self):
        raise AccessDenied("Public cannot read hr.contract.type")

    def sudo(self):
        self.elevations += 1
        return NS(name="دائم | Permanent")


def job(published=True, active=True, allowed=True):
    def check(mode):
        if mode != "read" or not allowed:
            raise AccessDenied("Job is private")
    return NS(ensure_one=lambda: None, check_access=check,
              website_published=published, active=active, contract_type_id=ContractType())


class PublicJobs(unittest.TestCase):
    def test_published_selected_label_without_public_catalogue_access(self):
        item = job()
        self.assertEqual(ns["masar_public_contract_type_name"](item), "دائم | Permanent")
        self.assertEqual(item.contract_type_id.elevations, 1)
        with self.assertRaises(AccessDenied):
            item.contract_type_id.name

    def test_inaccessible_job_denied_before_label_elevation(self):
        item = job(allowed=False)
        with self.assertRaises(AccessDenied):
            ns["masar_public_contract_type_name"](item)
        self.assertEqual(item.contract_type_id.elevations, 0)

    def test_drafts_and_archived_roles_never_elevate_label_read(self):
        for published, active in [(False, True), (True, False), (False, False)]:
            item = job(published, active)
            with self.assertRaises(AccessDenied):
                ns["masar_public_contract_type_name"](item)
            self.assertEqual(item.contract_type_id.elevations, 0)

    def test_untyped_job_omits_label(self):
        item = job(); item.contract_type_id = False
        self.assertEqual(ns["masar_public_contract_type_name"](item), "")

    def test_actual_bilingual_titles_have_english_slugs(self):
        for name, ident, expected in [
            ("مدير التدقيق الداخلي | Head of Internal Audit", 1, "head-of-internal-audit-1"),
            ("مسؤول مكافحة غسل الأموال | MLRO", 4, "mlro-4"),
            ("مدير عمليات الدفع والتجار | Head of Payments & Merchant Operations", 2,
             "head-of-payments-merchant-operations-2"),
        ]:
            self.assertEqual(ns["english_job_slug"](name, ident), expected)

    def test_arabic_only_fallback_and_distinct_ids_are_route_safe(self):
        for ident in [1, 2]:
            self.assertEqual(ns["english_job_slug"]("مدير عمليات", ident), f"job-{ident}")
        self.assertEqual(ns["english_job_slug"]("Risk / Compliance & Audit", 3), "risk-compliance-audit-3")

    def test_slug_uses_fixed_language_and_never_elevates_job(self):
        languages = []
        item = NS(id=1, ensure_one=lambda: None)
        def translated(**kwargs):
            languages.append(kwargs)
            return NS(name="مدير التدقيق الداخلي | Head of Internal Audit")
        item.with_context = translated
        self.assertEqual(ns["masar_english_slug"](item), "head-of-internal-audit-1")
        self.assertEqual(languages, [{"lang": "en_US"}])
        item.id = False
        with self.assertRaises(ValueError):
            ns["masar_english_slug"](item)

    def test_native_slug_override_is_limited_to_job_records(self):
        class Native:
            @classmethod
            def _slug(cls, value): return "native-slug"
        scope = {"models": NS(AbstractModel=Native)}
        module = ast.parse((ROOT / "models/ir_http.py").read_text())
        exec(compile(ast.Module(body=[n for n in module.body if isinstance(n, ast.ClassDef)],
                               type_ignores=[]), "ir_http.py", "exec"), scope)
        self.assertEqual(scope["IrHttp"]._slug(NS(_name="hr.job", masar_english_slug=lambda: "head-of-internal-audit-1")),
                         "head-of-internal-audit-1")
        for value in [NS(_name="product.template"), (1, "Product")]:
            self.assertEqual(scope["IrHttp"]._slug(value), "native-slug")

    def test_template_uses_escaped_scalar_and_native_apply_slug(self):
        root = ElementTree.parse(ROOT / "views/templates_careers.xml")
        labels = [n for n in root.iter() if n.attrib.get("t-out") == "job.masar_public_contract_type_name()"]
        self.assertEqual(len(labels), 1)
        self.assertFalse(any(n.attrib.get("t-field") == "job.contract_type_id.name" for n in root.iter()))
        self.assertEqual(sum(n.attrib.get("t-attf-href") == "/jobs/apply/#{slug(job)}" for n in root.iter()), 2)


if __name__ == "__main__":
    unittest.main(verbosity=2)
