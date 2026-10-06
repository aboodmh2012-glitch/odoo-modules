import importlib.util
import unittest
from pathlib import Path

_PATH = Path(__file__).resolve().parents[1] / "visual_pass.py"
_spec = importlib.util.spec_from_file_location("masar_visual_pass", _PATH)
visual = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(visual)


class VisualPassTests(unittest.TestCase):
    def test_solution_images_follow_each_heading(self):
        arch = """
        <img src="/web/image/website.s_card_default_image_1"/>
        <h2>الحسابات والبطاقات</h2>
        <img src="/web/image/website.s_key_images_default_image_2"/>
        <h2>نقاط البيع وقبول الدفع داخل المتجر</h2>
        <img src="/web/image/website.s_key_images_default_image_4"/>
        <h2>المدفوعات الجماعية</h2>
        <img src="/web/image/website.s_key_images_default_image_4"/>
        <h2>سداد الفواتير والتحصيل الإلكتروني</h2>
        <img src="/web/image/website.s_key_images_default_image_4"/>
        <h2>الصرافات الآلية والخدمات النقدية</h2>
        """
        out = visual.retarget_solution_images(arch)
        self.assertIn('src="/masar_website/static/src/img/solutions/accounts.jpg"', out)
        self.assertIn('src="/masar_website/static/src/img/solutions/pos.jpg"', out)
        self.assertIn('src="/masar_website/static/src/img/solutions/payouts.jpg"', out)
        self.assertIn('src="/masar_website/static/src/img/solutions/bills.jpg"', out)
        self.assertIn('src="/masar_website/static/src/img/solutions/atm.jpg"', out)
        self.assertNotIn("s_key_images_default_image", out)
        again = visual.retarget_solution_images(out)
        self.assertEqual(again, out)

    def test_hero_class_skips_inner_hooks(self):
        arch = '<section class="masar-hero o_colored_level"><p class="masar-hero__inner">'
        out = visual.ensure_hero_class(arch, "business")
        self.assertIn('class="masar-hero o_colored_level masar-hero--business"', out)
        self.assertIn('class="masar-hero__inner"', out)
        self.assertEqual(visual.ensure_hero_class(out, "business"), out)
        wrapped = visual.ensure_hero_class(
            '<div class="masar-site">' + arch,
            "solutions",
        )
        self.assertIn("masar-hero--solutions", wrapped)
        self.assertIn('class="masar-site"', wrapped)

    def test_banner_overlay_lightens_once(self):
        arch = """
        .masar-banner__bg { opacity: .55; }
        .masar-banner__overlay { background: linear-gradient(100deg, rgba(0,0,0,.92) 0%, rgba(0,0,0,.78) 42%, rgba(0,0,0,.35) 70%, rgba(0,0,0,.15) 100%); }
        /* ===== Banner slider ===== */
        """
        once = visual.lighten_banner_css(arch)
        self.assertIn("opacity: .68", once)
        self.assertIn("rgba(0,0,0,.78)", once)
        self.assertIn("rgba(0,0,0,.60)", once)
        self.assertNotIn(".92", once)
        self.assertEqual(visual.lighten_banner_css(once), once)

    def test_forced_font_family_is_removed(self):
        arch = (
            "<style>@import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400&display=swap');"
            ".masar-site{font-family:'Cairo',system-ui,sans-serif !important;}"
            "h1{font-family: var(--masar-display);}</style>"
        )
        out = visual.strip_forced_fonts(arch)
        self.assertNotIn("font-family", out)
        self.assertNotIn("Cairo", out)

    def test_about_gains_banner_and_highlights_once(self):
        arch = '<div id="wrap" class="masar-site"><section class="masar-section" id="about"><h2>About</h2></section></div>'
        out = visual.transform_page("/about", arch)
        self.assertIn("masar-hero--about", out)
        self.assertIn("masar-highlights", out)
        self.assertEqual(out.count('id="about"'), 1)
        self.assertEqual(visual.transform_page("/about", out), out)


    def test_stored_dark_theme_is_retinted_to_brand(self):
        arch = """<style id="masar-site-overrides">:root {
          --masar-orange: #ff5a1f; --masar-bg-0: #0a0a0a; --masar-text: #ffffff;
        }
        header, footer { background: #000 !important; }
        </style>"""
        out = visual.retint_stored_brand(arch)
        self.assertIn("#FF7A00", out)
        self.assertIn("#0a0a0a", out)
        self.assertIn("#ffffff", out)
        self.assertNotIn("#ff5a1f", out)
        self.assertEqual(visual.retint_stored_brand(out), out)


if __name__ == "__main__":
    unittest.main()
