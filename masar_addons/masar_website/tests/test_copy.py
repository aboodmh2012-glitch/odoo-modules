"""Catalog and template constraints. Runs without an Odoo database."""

import importlib
import sys
import types
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _load_registry():
    pkg = "masar_website"
    if pkg not in sys.modules or not hasattr(sys.modules[pkg], "__path__"):
        module = types.ModuleType(pkg)
        module.__path__ = [str(ROOT)]
        module.__package__ = pkg
        sys.modules[pkg] = module
    return importlib.import_module("masar_website.copy.registry")


registry = _load_registry()


def _same_shape(base, overlay, path):
    if isinstance(overlay, dict):
        if not isinstance(base, dict):
            raise AssertionError("%s: overlay dict does not match the base" % path)
        for key, value in overlay.items():
            if key not in base:
                raise AssertionError("%s%s is not in the English catalog" % (path, key))
            _same_shape(base[key], value, "%s%s." % (path, key))
        return
    if isinstance(overlay, list):
        if not isinstance(base, list) or len(base) != len(overlay):
            raise AssertionError("%s: list length %s != %s" % (path, len(overlay) if isinstance(overlay, list) else "?", len(base) if isinstance(base, list) else "?"))
        for index, (base_item, overlay_item) in enumerate(zip(base, overlay)):
            if isinstance(base_item, dict) or isinstance(overlay_item, dict):
                if set(base_item) != set(overlay_item):
                    raise AssertionError("%s[%s] keys differ: %s" % (path, index, set(base_item) ^ set(overlay_item)))
            _same_shape(base_item, overlay_item, "%s[%s]." % (path, index))
        return
    if not isinstance(overlay, type(base)):
        raise AssertionError("%s: %s is not %s" % (path, type(overlay).__name__, type(base).__name__))


class CopyCatalogTests(unittest.TestCase):
    def test_english_is_the_default(self):
        self.assertEqual(registry.locale_for(None), "en")
        self.assertEqual(registry.locale_for("en_US"), "en")
        self.assertEqual(registry.locale_for("fr_FR"), "en")
        copy = registry.get_copy("zz_ZZ")
        self.assertEqual(copy["actions"]["get_started"], "Request a Service")
        self.assertEqual(copy["_meta"]["dir"], "ltr")

    def test_arabic_overlay_falls_back_and_translates(self):
        copy = registry.get_copy("ar_001")
        self.assertEqual(copy["_meta"]["locale"], "ar")
        self.assertEqual(copy["_meta"]["dir"], "rtl")
        self.assertEqual(copy["actions"]["get_started"], "اطلب الخدمة")
        self.assertEqual(copy["brand"]["name"], "MASAR Pay")
        self.assertNotEqual(copy["home"]["hero"]["lead"], registry.get_copy("en")["home"]["hero"]["lead"])

    def test_arabic_matches_english_shape(self):
        _same_shape(registry.LOCALES["en"], registry.LOCALES["ar"], "")

    def test_new_language_is_a_registration(self):
        registry.register_locale("fr", {"actions": {"get_started": "Commencer"}})
        try:
            copy = registry.get_copy("fr_FR")
            self.assertEqual(copy["actions"]["get_started"], "Commencer")
            self.assertEqual(copy["actions"]["contact"], "Contact Us")
            self.assertEqual(copy["_meta"]["dir"], "ltr")
        finally:
            registry.LOCALES.pop("fr", None)

    def test_nav_path_ignores_language_prefix_and_hash(self):
        self.assertEqual(registry.normalize_public_path("/ar/about", ["ar", "en"]), "/about")
        self.assertEqual(registry.normalize_public_path("/enterprise", ["en", "ar"]), "/enterprise")
        self.assertTrue(registry.is_current("/solutions", "/solutions#gateway"))
        self.assertTrue(registry.is_current("/", "/"))
        self.assertFalse(registry.is_current("/business", "/"))
        self.assertFalse(registry.is_current("/business", "/solutions"))


class TemplateConstraintTests(unittest.TestCase):
    def test_views_use_classes_and_the_catalog(self):
        views = ROOT / "views"
        for path in views.glob("*.xml"):
            text = path.read_text(encoding="utf-8")
            ET.fromstring(text)
            lowered = text.lower()
            self.assertNotIn("<strong", lowered, path.name)
            self.assertNotIn("<b>", lowered, path.name)
            self.assertNotIn("<b ", lowered, path.name)
            self.assertNotIn("style=", lowered, path.name)
            self.assertNotIn('t-if="ar"', text, path.name)


if __name__ == "__main__":
    unittest.main()

