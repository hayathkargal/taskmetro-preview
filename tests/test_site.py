import importlib.util
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import struct
import tempfile
import unittest
from urllib.parse import urljoin, urlsplit, unquote
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('builder', ROOT/'scripts/build_site.py')
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)


class Page(HTMLParser):
    def __init__(self, html):
        super().__init__(convert_charrefs=True)
        self.meta = {}; self.links = []; self.images = []; self.ids = []; self.tags = []
        self.title = ''; self.in_title = False; self.json_text = None; self.schemas = []
        self.canonical = []; self.base = None; self.headings = []; self.current_heading = None
        self.inputs = []; self.labels = []; self.heading_text = []; self.in_main = False; self.h1 = []
        self.feed(html)

    def handle_starttag(self, tag, attrs):
        a = dict(attrs); self.tags.append(tag)
        if 'id' in a: self.ids.append(a['id'])
        if tag == 'main': self.in_main = True
        if tag == 'base': self.base = a.get('href')
        if tag == 'title': self.in_title = True
        if re.fullmatch(r'h[1-6]', tag):
            self.headings.append(int(tag[1])); self.current_heading = tag
            if tag == 'h1': self.h1.append('')
        if tag == 'meta': self.meta[a.get('name') or a.get('property')] = a.get('content')
        if tag == 'link' and a.get('rel') == 'canonical': self.canonical.append(a['href'])
        if tag != 'base':
            self.links.extend(a[key] for key in ('href', 'src') if a.get(key))
        if tag == 'meta' and (a.get('property') in ('og:image','og:url') or a.get('name') == 'twitter:image'):
            self.links.append(a['content'])
        if tag == 'img': self.images.append(a)
        if tag in ('input','select','textarea') and a.get('type') not in ('hidden','checkbox'): self.inputs.append(a)
        if tag == 'label' and 'for' in a: self.labels.append(a['for'])
        if tag == 'script' and a.get('type') == 'application/ld+json': self.json_text = ''

    def handle_data(self, data):
        if self.in_title: self.title += data
        if self.json_text is not None: self.json_text += data
        if self.current_heading == 'h1': self.h1[-1] += data

    def handle_endtag(self, tag):
        if tag == 'title': self.in_title = False
        if tag == 'main': self.in_main = False
        if re.fullmatch(r'h[1-6]', tag): self.current_heading = None
        if tag == 'script' and self.json_text is not None:
            self.schemas.append(json.loads(self.json_text)); self.json_text = None


class SiteTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.preview_dir = tempfile.TemporaryDirectory(prefix='taskmetro-preview-test-')
        cls.production_dir = tempfile.TemporaryDirectory(prefix='taskmetro-production-test-')
        builder.build(False, cls.preview_dir.name)
        builder.build(True, cls.production_dir.name)
        cls.preview = Path(cls.preview_dir.name); cls.production = Path(cls.production_dir.name)
        cls.pages = {p.name: Page(p.read_text()) for p in cls.preview.glob('*.html')}

    @classmethod
    def tearDownClass(cls):
        cls.preview_dir.cleanup(); cls.production_dir.cleanup()

    def test_unique_concise_metadata_and_social_cards(self):
        self.assertEqual(len(self.pages), 19)
        self.assertEqual(len({p.title for p in self.pages.values()}), 19)
        for name, p in self.pages.items():
            with self.subTest(page=name):
                self.assertTrue(0 < len(p.title) < 60)
                self.assertTrue(0 < len(p.meta['description']) < 150)
                self.assertEqual(len(p.canonical), 1)
                for key in ['og:title','og:description','og:image','og:url','og:image:alt','twitter:title','twitter:description','twitter:image','twitter:image:alt']:
                    self.assertTrue(p.meta[key], key)
                self.assertEqual(p.meta['twitter:card'], 'summary_large_image')
                self.assertEqual(p.meta['og:title'], p.title)
                self.assertEqual(p.meta['og:description'], p.meta['description'])

    def test_semantics_and_accessible_images(self):
        for name,p in self.pages.items():
            with self.subTest(page=name):
                self.assertEqual(p.tags.count('main'), 1)
                self.assertEqual(len(p.h1), 1)
                self.assertEqual(len(p.ids),len(set(p.ids)))
                last = 0
                for level in p.headings:
                    self.assertLessEqual(level, last+1)
                    last = level
                for image in p.images:
                    self.assertTrue(image.get('alt'))
                    self.assertGreater(int(image['width']),0)
                    self.assertGreater(int(image['height']),0)

    def test_internal_routes_assets_and_nested_error_page(self):
        prefix = '/taskmetro-preview/'
        for name,p in self.pages.items():
            locations = [builder.SITE['preview_url']+name]
            if name == '404.html': locations.append(builder.SITE['preview_url']+'missing/nested/page')
            for location in locations:
                context = urljoin(location,p.base) if p.base else location
                for ref in p.links:
                    if ref.startswith('#'):
                        self.assertIn(unquote(ref[1:]),p.ids)
                        continue
                    url = urlsplit(urljoin(context,ref))
                    if url.netloc != 'hayathkargal.github.io': continue
                    with self.subTest(page=name,ref=ref):
                        self.assertTrue(url.path.startswith(prefix))
                        relative = unquote(url.path[len(prefix):]) or 'index.html'
                        self.assertTrue((self.preview/relative).is_file(),relative)
                        if relative.endswith('.html') and url.fragment:
                            self.assertIn(unquote(url.fragment),self.pages[relative].ids)
                        if relative == 'assets/icons.svg' and url.fragment:
                            self.assertIn('id="'+url.fragment+'"',(self.preview/relative).read_text())

    def test_preview_and_production_are_separate(self):
        for name,p in self.pages.items():
            self.assertIn('noindex',p.meta['robots'])
            self.assertTrue(p.canonical[0].startswith(builder.SITE['preview_url']))
            live = Page((self.production/name).read_text())
            self.assertEqual('noindex' in live.meta['robots'],name=='404.html')
            self.assertTrue(live.canonical[0].startswith(builder.SITE['production_url']))
        self.assertNotIn('Disallow: /',(self.preview/'robots.txt').read_text())
        self.assertIn('Sitemap: https://taskmetro.com/sitemap.xml',(self.production/'robots.txt').read_text())
        self.assertFalse((self.preview/'CNAME').exists())
        self.assertIsNone(Page((self.production/'404.html').read_text()).base)

    def test_error_page_skip_link_stays_on_current_missing_url(self):
        page=self.pages['404.html']
        missing=builder.SITE['preview_url']+'missing/nested/page'
        context=urljoin(missing,page.base) if page.base else missing
        self.assertEqual(urljoin(context,'#main'),missing+'#main')
        self.assertIn('main',page.ids)

    def test_sitemap_matches_canonical_pages(self):
        ns={'s':'http://www.sitemaps.org/schemas/sitemap/0.9'}
        urls=ET.parse(self.preview/'sitemap.xml').findall('s:url/s:loc',ns)
        self.assertEqual({n.text for n in urls},{p.canonical[0] for name,p in self.pages.items() if name!='404.html'})

    def test_structured_data_is_valid_and_matches_service_pages(self):
        for name,p in self.pages.items():
            self.assertEqual(len(p.schemas),1)
            graph=p.schemas[0]['@graph']
            self.assertEqual(p.schemas[0]['@context'],'https://schema.org')
            self.assertTrue(any(n['@type']=='LocalBusiness' for n in graph))
            self.assertNotIn('aggregateRating',json.dumps(graph))
            self.assertNotIn('reviewCount',json.dumps(graph))
            ids=[n['@id'] for n in graph]
            self.assertEqual(len(ids),len(set(ids)))
        for service in builder.SERVICES:
            p=self.pages[service['slug']]
            node=next(n for n in p.schemas[0]['@graph'] if n['@type']=='Service')
            self.assertEqual(node['description'],p.meta['description'])
            self.assertIn(service['name'],node['name'])

    def test_faq_markup_matches_visible_questions(self):
        page=self.pages['faq.html']
        faq=next(n for n in page.schemas[0]['@graph'] if n['@type']=='FAQPage')
        source=(self.preview/'faq.html').read_text()
        for question in faq['mainEntity']:
            self.assertIn(question['name'],source)
            self.assertTrue(question['acceptedAnswer']['text'])

    def test_forms_have_labels_and_work_without_javascript(self):
        for name in ['index.html','request.html','contact.html','pricing.html','services.html']:
            p=self.pages[name]
            for field in p.inputs:
                self.assertIn(field.get('id'),p.labels)
        for name in ['request.html','contact.html']:
            text=(self.preview/name).read_text()
            self.assertIn('action="https://api.web3forms.com/submit" method="post"',text)
            self.assertIn('name="botcheck"',text)
            self.assertNotIn('onsubmit=',text)
        text=(self.preview/'request.html').read_text()
        self.assertNotRegex(text,r'<fieldset[^>]+hidden')
        for service in builder.SERVICES:
            self.assertIn('value="'+service['id']+'"',text)

    def test_social_card_dimensions_and_static_asset_budget(self):
        png=(self.preview/'assets/social-card.png').read_bytes()
        self.assertEqual(struct.unpack('>II',png[16:24]),(1200,630))
        total=sum((self.preview/p).stat().st_size for p in ['index.html','css/styles.css','js/main.mjs','js/booking.mjs','js/site-config.mjs','assets/png.png','assets/bengaluru-illustration.svg','assets/icons.svg'])
        self.assertLess(total,200_000)


if __name__=='__main__':
    unittest.main()
