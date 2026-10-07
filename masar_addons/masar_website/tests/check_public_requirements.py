"""Exercise the publication boundary and current native requirement labels."""
import ast
from datetime import date, timedelta
from pathlib import Path
from types import SimpleNamespace as NS
import unittest

source = ast.parse((Path(__file__).resolve().parents[1] / "models/hr_job.py").read_text())
method = next(n for cls in source.body if isinstance(cls, ast.ClassDef)
              for n in cls.body if isinstance(n, ast.FunctionDef) and n.name == "masar_public_requirements")
scope = {"fields": NS(Date=NS(today=lambda: date(2026, 10, 4)))}
exec(compile(ast.Module(body=[method], type_ignores=[]), "hr_job.py", "exec"), scope)

def skill(ident=1, start=None, stop=None, active=True):
    return NS(skill_type_id=NS(id=1, name="Languages", active=active),
              skill_id=NS(id=ident, name="English"), skill_level_id=NS(name="B2"),
              valid_from=start, valid_to=stop)

class Job:
    def __init__(self, published=True, active=True, allowed=True, optional=True):
        self.website_published, self.active, self.allowed = published, active, allowed
        self._fields = {"expected_degree": True, "job_skill_ids": True} if optional else {}
        self.expected_degree = NS(name="Bachelor Degree")
        self.job_skill_ids = [skill()]
        self.elevations = 0
    def ensure_one(self): pass
    def check_access(self, mode):
        assert mode == "read"
        if not self.allowed: raise PermissionError()
    def sudo(self):
        self.elevations += 1
        return self

class Requirements(unittest.TestCase):
    def read(self, job): return scope["masar_public_requirements"](job)
    def test_selected_labels_only(self):
        item = Job(); result = self.read(item)
        self.assertEqual(result, {"degree": "Bachelor Degree", "groups": [{"name": "Languages", "skills": [{"name": "English", "level": "B2"}]}]})
        self.assertEqual(item.elevations, 1)
    def test_job_access_precedes_catalogue_read(self):
        item = Job(allowed=False)
        with self.assertRaises(PermissionError): self.read(item)
        self.assertEqual(item.elevations, 0)
    def test_no_labels_or_elevation_for_drafts_and_archives(self):
        for published, active in [(False, True), (True, False), (False, False)]:
            item = Job(published, active)
            self.assertEqual(self.read(item), {"degree": "", "groups": []})
            self.assertEqual(item.elevations, 0)
    def test_optional_native_modules_absent(self):
        self.assertEqual(self.read(Job(optional=False)), {"degree": "", "groups": []})
    def test_expired_future_and_inactive_requirements_omitted(self):
        item = Job(); today = date(2026, 10, 4)
        item.job_skill_ids = [skill(stop=today-timedelta(days=1)), skill(start=today+timedelta(days=1)), skill(active=False)]
        self.assertEqual(self.read(item)["groups"], [])
    def test_today_included_and_duplicate_skill_omitted(self):
        item = Job(); today = date(2026, 10, 4)
        item.job_skill_ids = [skill(start=today, stop=today), skill()]
        self.assertEqual(len(self.read(item)["groups"][0]["skills"]), 1)

if __name__ == "__main__": unittest.main(verbosity=2)
