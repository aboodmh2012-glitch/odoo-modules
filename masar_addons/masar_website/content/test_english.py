"""Offline checks required before inspecting or applying the English release."""
import copy
import re
import unittest
from lxml import etree
from content_engine import (
    PUBLIC_SLUGS, VERSION as AR_VERSION, load_source, build_arch, target_url, view_key,
)
from english_content import (
    EN_VERSION, ARABIC, load_english, english_layout, bilingual_arch,
    arabic_layout, layout_bytes,
)


class EnglishTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.en = load_english()
        cls.ar = load_source()
        cls.original = {p['slug']: p for p in cls.ar['pages']}

    def test_31_pages_exact_scope_and_headings(self):
        self.assertEqual(len(self.en['pages']), 31)
        self.assertEqual(sum(p['slug'] in PUBLIC_SLUGS for p in self.en['pages']), 17)
        self.assertEqual(len({p['slug'] for p in self.en['pages']}), 31)

    def test_every_translated_page_compiles_as_xml(self):
        for page in self.en['pages']:
            with self.subTest(slug=page['slug']):
                tree = english_layout(page, self.en)
                xml = etree.tostring(tree)
                etree.fromstring(xml)
                wrap = tree.find("div[@id='wrap']")
                self.assertEqual(wrap.get('lang'), 'en')
                self.assertEqual(wrap.get('dir'), 'ltr')
                self.assertEqual(wrap.get('data-masar-content-version'), EN_VERSION)
                self.assertFalse(ARABIC.search(''.join(wrap.itertext())))
                self.assertEqual(len(wrap.xpath('.//h1')), 1)
                self.assertEqual(len(wrap.xpath('.//h2|.//summary')), page['body'].count('\n## '))
                self.assertNotIn('This page is currently available in Arabic', xml.decode())

    def test_both_previous_layout_variants_preserve_arabic(self):
        for page in self.en['pages']:
            for fallback in (None, 'website.previous_english'):
                with self.subTest(slug=page['slug'], fallback=fallback):
                    original = build_arch(self.original[page['slug']], self.ar, existing_english_key=fallback)
                    combined = bilingual_arch(original, page, self.en)
                    self.assertEqual(layout_bytes(arabic_layout(original)), layout_bytes(arabic_layout(combined)))
                    root = etree.fromstring(combined.encode())
                    self.assertEqual(root.get('t-name'), view_key(page['slug']))
                    self.assertEqual(len(root.xpath('.//div[@id="wrap"]')), 2)
                    self.assertEqual(len(root.xpath('.//div[@dir="ltr"]')), 1)
                    self.assertEqual(len(root.xpath('.//div[@dir="rtl"]')), 1)

    def test_all_body_text_retained(self):
        for page in self.en['pages']:
            tree = english_layout(page, self.en)
            text = re.sub(r'\s+', ' ', ''.join(tree.itertext()))
            for line in page['body'].splitlines():
                line = re.sub(r'^#{1,2} ', '', line).replace('**', '').strip()
                if line:
                    self.assertIn(re.sub(r'\s+', ' ', line), text, page['slug'])

    def test_links_keep_english_and_respect_gates(self):
        allowed = {'/en' if p == '/' else '/en' + p for p in PUBLIC_SLUGS} | {'/en/contactus'}
        for page in self.en['pages']:
            tree = english_layout(page, self.en)
            for href in tree.xpath('.//a/@href'):
                self.assertIn(href, allowed)
            review = tree.xpath('.//aside[contains(@class,"masar-editorial-review")]')
            self.assertEqual(bool(review), page['slug'] not in PUBLIC_SLUGS)

    def test_no_contact_cta_when_original_form_unavailable(self):
        for page in self.en['pages']:
            self.assertNotIn('/en/contactus', english_layout(page, self.en, contact_available=False).xpath('.//a/@href'))

    def test_input_escaped(self):
        page = copy.deepcopy(self.en['pages'][0])
        page['body'] = '# <script>alert(1)</script>\n<img src=x onerror=alert(1)>\n\n## Title\nA & B'
        tree = english_layout(page, self.en)
        self.assertFalse(tree.xpath('.//script|.//img'))
        self.assertIn('<script>alert(1)</script>', ''.join(tree.itertext()))

    def test_no_false_launch_or_unconditional_service_claims_added(self):
        by_slug = {p['slug']: p for p in self.en['pages']}
        self.assertIn('does not authorize the commencement of business', by_slug['/help/faq']['body'])
        self.assertIn('does not mean that every payment has reached its recipient', by_slug['/solutions/payouts']['body'])
        self.assertIn('not a final policy', by_slug['/privacy']['body'])
        self.assertEqual(by_slug['/help/faq']['body'].count('\n## '), 14)


if __name__ == '__main__':
    unittest.main()
