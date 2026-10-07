import unittest
from lxml import etree
from content_engine import *


class EditorialTests(unittest.TestCase):
    def setUp(self):
        self.source = load_source()

    def test_source_archive_integrity_and_scope(self):
        self.assertEqual(len(self.source['pages']), 31)
        self.assertEqual(len(PUBLIC_SLUGS), 17)
        self.assertEqual(len(self.source['pages']) - len(PUBLIC_SLUGS), 14)

    def test_every_page_compiles_as_xml(self):
        for p in self.source['pages']:
            with self.subTest(slug=p['slug']):
                xml = build_arch(p, self.source, contact_available=True)
                root = etree.fromstring(xml.encode())
                self.assertEqual(len(root.xpath('//h1')), 1)
                self.assertEqual(root.xpath('//h1')[0].text, p['body'].splitlines()[0][2:].strip())
                self.assertEqual(len(root.xpath('//*[@id="wrap"]')), 1)
                if p['slug'] in PUBLIC_SLUGS:
                    self.assertNotIn(p['editorial_notes'], xml)
                    self.assertNotIn('مسودة داخلية', xml)
                else:
                    self.assertTrue(target_url(p).startswith(REVIEW_PREFIX))

    def test_all_source_paragraphs_retained(self):
        for p in self.source['pages']:
            root = etree.fromstring(build_arch(p, self.source).encode())
            text = ''.join(root.itertext())
            for line in p['body'].splitlines():
                plain = line.removeprefix('## ').removeprefix('# ').replace('**', '')
                if plain.strip():
                    self.assertIn(plain, text, p['slug'])

    def test_english_fallback_and_no_hardcoded_ids(self):
        root = etree.fromstring(build_arch(self.source['pages'][0], self.source,
                                          existing_english_key='website.homepage').encode())
        self.assertEqual(root.xpath('//t[@t-else]/@t-call'), ['website.homepage'])

    def test_links_never_point_to_gated_pages(self):
        for p in self.source['pages']:
            root = etree.fromstring(build_arch(p, self.source, contact_available=True).encode())
            for link in root.xpath('//a/@href'):
                self.assertIn(link, PUBLIC_SLUGS | {'/contactus'})

    def test_html_is_escaped_and_source_not_executable(self):
        self.assertEqual(inline('<script>bad()</script>'), '&lt;script&gt;bad()&lt;/script&gt;')
        etree.fromstring(style_arch().encode())


if __name__ == '__main__':
    unittest.main()
