#!/usr/bin/env python3
"""Generate crawlable static pages. Preview is the default; no runtime framework."""
import argparse
from html import escape
import json
from pathlib import Path
import re
import shutil
from urllib.parse import urljoin, urlsplit
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
SITE = json.loads((ROOT / 'content/site.json').read_text())
SERVICES = json.loads((ROOT / 'content/services.json').read_text())
REVIEWS = json.loads((ROOT / 'content/reviews.json').read_text())
BASE = SITE['preview_url']
PRODUCTION = False
UPDATED = '2026-11-03'


def e(value):
    return escape(str(value), quote=True)


def rupees(amount):
    value=float(amount)
    return '₹'+(f'{value:,.0f}' if value.is_integer() else f'{value:,.2f}')


def icon(name, cls=''):
    return f'<svg class="icon {cls}" width="24" height="24" aria-hidden="true" focusable="false"><use href="assets/icons.svg#{e(name)}"></use></svg>'


def link_button(label, href, style='primary', arrow=True):
    return f'<a class="button button-{style}" href="{e(href)}">{e(label)}{icon("arrow") if arrow else ""}</a>'


def whatsapp(label='Chat on WhatsApp', style='text'):
    return f'<a class="{e(style)}" href="https://wa.me/{SITE["whatsapp"]}?text=Hi%20TaskMetro%2C%20I%20need%20help%20with%20a%20Bengaluru%20task">{icon("chat")}{e(label)}</a>'


def service_options(blank=True):
    return ('<option value="">Choose a service</option>' if blank else '') + ''.join(f'<option value="{s["id"]}">{e(s["name"])}</option>' for s in SERVICES)


def header(current):
    links = [('services.html', 'Our services'), ('index.html#how-it-works', 'How it works'),
             ('pricing.html', 'Pricing'), ('about.html', 'Our story')]
    nav = ''.join(f'<a href="{href}"'+ (' aria-current="page"' if href == current else '') + f'>{label}</a>' for href, label in links)
    return f'''<a class="skip-link" href="#main">Skip to content</a>
<div class="utility-bar"><div class="container utility-inner"><span>{icon('pin')} Your trusted local presence in Bengaluru</span><a href="tel:{SITE['telephone']}">Let’s talk: {SITE['telephone_display']}</a></div></div>
<header class="site-header"><div class="container header-inner">
 <a class="brand" href="index.html" aria-label="TaskMetro home"><img src="assets/png.png" width="1563" height="313" alt="TaskMetro — Naav Iddeve" decoding="async"></a>
 <button class="nav-toggle" type="button" aria-expanded="false" aria-controls="site-navigation" aria-label="Open navigation" hidden>{icon('menu')}</button>
 <nav class="site-nav" id="site-navigation" aria-label="Main navigation">{nav}<a class="button button-primary nav-cta" href="request.html">Get a quote {icon('diagonal')}</a></nav>
</div></header>'''


def footer():
    links = ''.join(f'<a href="{s["slug"]}">{e(s["name"])}</a>' for s in SERVICES[:6])
    return f'''<footer class="site-footer"><div class="container footer-grid">
 <div class="footer-brand"><a class="brand" href="index.html" aria-label="TaskMetro home"><img src="assets/png.png" width="1563" height="313" alt="TaskMetro" loading="lazy" decoding="async"></a><p>A little local help.<br>A lot less on your mind.</p><span class="footer-location">{icon('pin')} Bengaluru, Karnataka, India</span></div>
 <div><h2>What we help with</h2>{links}</div>
 <div><h2>Get to know us</h2><a href="about.html">Our story & people</a><a href="pricing.html">Pricing explained</a><a href="faq.html">Common questions</a><a href="contact.html">Contact us</a><a href="request.html">Request a task</a></div>
 <div><h2>Let’s take it from here.</h2><a href="tel:{SITE['telephone']}">{SITE['telephone_display']}</a><a href="mailto:{SITE['email']}">{SITE['email']}</a><p class="small">{SITE['hours']}</p>{whatsapp('Say hello on WhatsApp','footer-chat')}</div>
 </div><div class="container footer-bottom"><span>© <span data-year>2026</span> TaskMetro. All rights reserved.</span><span><a href="privacy.html">Privacy</a><a href="terms.html">Terms of service</a></span></div></footer>
<div class="mobile-action">{whatsapp('WhatsApp','mobile-chat')}<a class="button button-primary" href="request.html">Get a quote {icon('arrow')}</a></div>'''


def breadcrumb(name, service=False):
    mid = '<li><a href="services.html">Services</a></li>' if service else ''
    return f'<nav class="breadcrumb" aria-label="Breadcrumb"><ol><li><a href="index.html">Home</a></li>{mid}<li aria-current="page">{e(name)}</li></ol></nav>'


def schema(path, title, description, service=None, faqs=None):
    url = urljoin(BASE, '' if path == 'index.html' else path)
    business = {'@type': 'LocalBusiness', '@id': BASE + '#business', 'name': SITE['name'], 'url': BASE,
                'description': 'Authorized errand facilitation, local assistance and concierge services in Bengaluru.',
                'telephone': SITE['telephone'], 'email': SITE['email'], 'logo': BASE + 'assets/png.png',
                'image': BASE + 'assets/social-card.png',
                'address': {'@type': 'PostalAddress', 'addressLocality': SITE['city'], 'addressRegion': SITE['region'], 'addressCountry': SITE['country']},
                'areaServed': {'@type': 'City', 'name': SITE['city']},
                'openingHoursSpecification': {'@type': 'OpeningHoursSpecification', 'dayOfWeek': ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'], 'opens': '09:00', 'closes': '18:00'},
                'priceRange': f'{rupees(SITE["base_fee"])} base fee + {rupees(SITE["runner_hourly"])}/hour + applicable expenses',
                'hasOfferCatalog': {'@type': 'OfferCatalog', 'name': 'Bengaluru errand services', 'itemListElement': [
                    {'@type': 'Offer', 'itemOffered': {'@type': 'Service', 'name': s['name'] + ' in Bengaluru', 'url': BASE + s['slug']}} for s in SERVICES]}}
    if REVIEWS.get('url'):
        business['sameAs'] = [REVIEWS['url']]
    webpage = {'@type': 'WebPage', '@id': url + '#page', 'url': url, 'name': title, 'description': description,
               'inLanguage': 'en-IN', 'isPartOf': {'@id': BASE + '#website'}, 'about': {'@id': BASE + '#business'}}
    graph = [business, {'@type': 'WebSite', '@id': BASE + '#website', 'name': SITE['name'], 'url': BASE, 'inLanguage': 'en-IN'}, webpage]
    if path != 'index.html':
        crumbs = [{'@type': 'ListItem', 'position': 1, 'name': 'Home', 'item': BASE}]
        if service:
            crumbs.append({'@type': 'ListItem', 'position': 2, 'name': 'Services', 'item': BASE + 'services.html'})
        crumbs.append({'@type': 'ListItem', 'position': len(crumbs) + 1, 'name': service['name'] if service else title.split(' | ')[0], 'item': url})
        graph.append({'@type': 'BreadcrumbList', '@id': url + '#breadcrumb', 'itemListElement': crumbs})
        webpage['breadcrumb'] = {'@id': url + '#breadcrumb'}
    if service:
        graph.append({'@type': 'Service', '@id': url + '#service', 'name': service['name'] + ' in Bengaluru',
                      'serviceType': service['name'], 'description': service['description'], 'url': url,
                      'areaServed': {'@type': 'City', 'name': SITE['city']}, 'provider': {'@id': BASE + '#business'}})
        webpage['mainEntity'] = {'@id': url + '#service'}
    if faqs:
        graph.append({'@type': 'FAQPage', '@id': url + '#faq', 'mainEntity': [
            {'@type': 'Question', 'name': q, 'acceptedAnswer': {'@type': 'Answer', 'text': a}} for q, a in faqs]})
    return json.dumps({'@context': 'https://schema.org', '@graph': graph}, ensure_ascii=False, separators=(',', ':')).replace('<', '\\u003c')


def write_page(path, title, description, content, service=None, faqs=None, page_class=''):
    if not 0 < len(title) < 60:
        raise ValueError(f'Title must be under 60 characters: {title}')
    if not 0 < len(description) < 150:
        raise ValueError(f'Description must be under 150 characters: {description}')
    url = urljoin(BASE, '' if path == 'index.html' else path)
    robots = 'index, follow, max-image-preview:large' if PRODUCTION and path != '404.html' else 'noindex, nofollow'
    base = ''
    preload = '<link rel="preload" href="assets/bengaluru-illustration.svg" as="image" type="image/svg+xml">' if path == 'index.html' else ''
    html = f'''<!doctype html>
<html lang="en-IN">
<head>
 <meta charset="utf-8">{base}
 <meta name="viewport" content="width=device-width, initial-scale=1">
 <title>{e(title)}</title>
 <meta name="description" content="{e(description)}">
 <meta name="robots" content="{robots}">
 <meta name="theme-color" content="#183e32">
 <link rel="canonical" href="{e(url)}">
 <meta property="og:type" content="website">
 <meta property="og:locale" content="en_IN">
 <meta property="og:site_name" content="TaskMetro">
 <meta property="og:title" content="{e(title)}">
 <meta property="og:description" content="{e(description)}">
 <meta property="og:url" content="{e(url)}">
 <meta property="og:image" content="{BASE}assets/social-card.png">
 <meta property="og:image:width" content="1200">
 <meta property="og:image:height" content="630">
 <meta property="og:image:alt" content="TaskMetro: your trusted local presence for Bengaluru errands and concierge services.">
 <meta name="twitter:card" content="summary_large_image">
 <meta name="twitter:title" content="{e(title)}">
 <meta name="twitter:description" content="{e(description)}">
 <meta name="twitter:image" content="{BASE}assets/social-card.png">
 <meta name="twitter:image:alt" content="TaskMetro: Bengaluru errands, handled with care.">
 <link rel="icon" href="assets/favicon.svg" type="image/svg+xml">
 {preload}<link rel="stylesheet" href="css/styles.css">
 <script type="application/ld+json">{schema(path,title,description,service,faqs)}</script>
 <script type="module" src="js/main.mjs"></script>
</head>
<body class="{e(page_class)}">{header(path)}
<main id="main" tabindex="-1">{content}</main>
{footer()}
</body>
</html>
'''
    if path == '404.html':
        # Root-relative resources work at arbitrary missing paths, while #main
        # stays in this error document for keyboard skip navigation.
        def prefix_reference(match):
            attribute, reference = match.groups()
            parsed = urlsplit(reference)
            if parsed.scheme or parsed.netloc or reference.startswith(('/', '#')):
                return match.group(0)
            return f'{attribute}="{e(urlsplit(BASE).path+reference)}"'
        html = re.sub(r'(href|src)="([^"]+)"', prefix_reference, html)
    (ROOT / path).write_text(html.replace('><', '>\n<'))


def quick_start(service=None):
    options = service_options()
    if service:
        options = options.replace(f'value="{service["id"]}"', f'value="{service["id"]}" selected')
    return f'''<section class="quick-start container" aria-labelledby="start-heading"><div><span class="eyebrow">ONE LESS THING TO DO</span><h2 id="start-heading">What can we take off your list?</h2></div>
 <form class="quick-form" action="request.html" method="get"><div class="field"><label for="quick-service">I need help with</label><select id="quick-service" name="category" required>{options}</select></div><div class="field"><label for="quick-urgency">When do you need it?</label><select id="quick-urgency" name="urgency"><option value="flexible">I’m flexible</option><option value="48-hours">Within 48 hours</option><option value="same-day">As soon as possible</option></select></div><button class="button button-primary" type="submit">Get started {icon('arrow')}</button></form><p class="small quick-note">A clear quote before we begin. No payment required to send a request.</p></section>'''


def service_card(s, index=0):
    return f'''<article class="service-card"><span class="service-icon">{icon(s['icon'])}</span><span class="card-index">{index+1:02d}</span><h3><a href="{s['slug']}">{e(s['name'])}</a></h3><p>{e(s['intro'])}</p><a class="card-link" href="{s['slug']}">Explore service {icon('diagonal')}</a></article>'''


def steps():
    items = [('Tell us what’s on your list','Choose a service and share a few details. We’ll check the practicalities.'), ('Know the plan. Know the price.','We confirm what’s possible and share a quote before any work begins.'), ('Carry on with your day.','We handle the agreed task and keep you updated with photos and receipts.')]
    return '<ol class="process-grid">' + ''.join(f'<li><span class="step-number">0{i+1}</span><h3>{title}</h3><p>{body}</p></li>' for i,(title,body) in enumerate(items)) + '</ol>'


def faq_list(items):
    return '<div class="faq-list">' + ''.join(f'<details><summary>{e(q)}<span aria-hidden="true">+</span></summary><p>{e(a)}</p></details>' for q,a in items) + '</div>'


FAQS = [
 ('Can I book from outside Bengaluru or India?', 'Yes. TaskMetro helps NRIs, people living in other cities, businesses and local residents coordinate tasks in Bengaluru. Share your requirement and we will confirm feasibility.'),
 ('What will my task cost?', f'The base fee is {rupees(SITE["base_fee"])}, plus runner time at {rupees(SITE["runner_hourly"])} per hour billed in 30-minute increments. Travel, parking, institutional fees and any special handling are additional. You receive a quote before work begins.'),
 ('How will I know what is happening?', 'We share updates through your preferred contact channel, with photos, receipts and a summary of the agreed work. GPS logs are shared where relevant.'),
 ('Can you complete a task the same day?', 'Urgent requests are assessed against runner availability, opening hours and third-party requirements. Same-day completion is not guaranteed, and urgent tasks may have additional charges.'),
 ('Do you handle original or sensitive documents?', 'Document handling is agreed in advance, including authorization, identity checks and sealed handovers where needed. Special handling charges may apply. Do not send passwords, OTPs or unnecessary sensitive records in the request form.'),
 ('Do I need to be present for official work?', 'Some government offices, banks and institutions require your presence or specific authorization. We check which collection, submission or coordination steps can be handled on your behalf.'),
 ('How do payment and refunds work?', 'The base fee initiates planning and is non-refundable once planning begins. Runner time, travel and third-party charges follow the agreed quote. UPI and bank transfer are available. See the Terms of Service for refund and cancellation conditions.'),
 ('Which areas do you cover?', 'We cover Bengaluru urban limits. For outskirts or nearby cities, share the location so we can assess feasibility and travel costs.'),
 ('Can you help with recurring or business tasks?', 'Yes. Recurring errands, property checks and corporate task coordination can be discussed for a tailored quote. Tell us the frequency, scope and locations.'),
 ('Do you provide legal, financial or medical advice?', 'TaskMetro provides errand facilitation, authorized paperwork coordination and logistics. We do not provide legal, financial or medical advisory services, or replace emergency services.')]


def trust_section():
    reviews = ''
    if REVIEWS.get('url'):
        quotes = ''.join(f'<figure class="review-card"><blockquote>“{e(r["quote"])}”</blockquote><figcaption>{e(r["author"])}<span>Google review · {e(r["date"])}</span></figcaption></figure>' for r in REVIEWS.get('items', []))
        reviews = f'<section class="section reviews-section"><div class="container"><div class="section-heading"><div><span class="eyebrow">FROM OUR CUSTOMERS</span><h2>Trust, in their own words.</h2></div><a class="text-link" href="{e(REVIEWS["url"])}">Read reviews on Google {icon("diagonal")}</a></div><div class="review-grid">{quotes}</div></div></section>'
    return f'''<section class="section trust-section"><div class="container trust-layout"><div><span class="eyebrow">YOUR TRUST IS THE WHOLE POINT</span><h2>Real people.<br>Clear communication.<br><em>Care at every step.</em></h2><p>Handing over a task is personal. We make the plan, the price and the progress easy to understand.</p>{link_button('Meet the people behind TaskMetro','about.html','secondary')}</div><div class="trust-points">
 <article>{icon('shield')}<div><h3>Permission comes first</h3><p>We check authorization and agree how your documents or items should be handled.</p></div></article>
 <article>{icon('document')}<div><h3>A quote you can understand</h3><p>Know the service fee and applicable expenses before the task begins.</p></div></article>
 <article>{icon('chat')}<div><h3>You’re kept in the loop</h3><p>Human support, task updates, and photos or receipts for the work carried out.</p></div></article>
 </div></div></section>{reviews}'''


def cta():
    return f'''<section class="container closing-cta"><div><span class="eyebrow">WHEREVER LIFE TAKES YOU</span><h2>Leave the Bengaluru<br>to-do list with us.</h2><p>A document, a deadline, a little help back home. Let’s start with what you need.</p></div><div>{link_button('Tell us your task','request.html')}{whatsapp('Or, talk to a real person','cta-chat')}<span class="small">Quote first. Work begins with your approval.</span></div></section>'''


def home():
    cards = ''.join(service_card(s,i) for i,s in enumerate(SERVICES[:6]))
    more = ''.join(f'<a href="{s["slug"]}">{icon(s["icon"])}{e(s["name"])}{icon("diagonal")}</a>' for s in SERVICES[6:])
    return f'''<section class="hero"><div class="container hero-grid"><div class="hero-content"><span class="eyebrow"><span class="live-dot"></span> BENGALURU ERRAND & CONCIERGE SERVICES</span><h1>Your person<br>in Bengaluru.<br><em>Wherever you are.</em></h1><p class="hero-description">From collecting documents to checking on your property, we handle the Bengaluru errands you can’t be here for.</p><div class="hero-actions">{link_button('Get my task done','request.html')}{whatsapp('Let’s talk','button button-secondary')}</div><p class="hero-price">From <strong>{rupees(SITE["base_fee"])} base fee</strong> + runner time & actuals. <a href="pricing.html">See how pricing works</a></p><div class="hero-assurances"><span>{icon('check')} Upfront quotes</span><span>{icon('check')} Photos & receipts</span><span>{icon('check')} Human support</span></div></div>
 <div class="hero-visual"><div class="hero-art"><img src="assets/bengaluru-illustration.svg" width="720" height="660" fetchpriority="high" alt="Illustration of Bengaluru architecture, leafy streets and a document delivery route."><span class="art-caption">LOCAL KNOW-HOW. A LITTLE PEACE OF MIND.</span></div><div class="city-label">{icon('pin')}<div><strong>Bengaluru, sorted.</strong><span>Your errands. Our local hands.</span></div></div><div class="care-label">{icon('heart')} Handled with care.</div></div></div></section>
 {quick_start()}
 <section class="audience-strip container" aria-label="Who we help"><span>For the city you’re<br>still connected to.</span><span>Living abroad</span><span>Working elsewhere</span><span>Managing a business</span><span>Simply short on time</span></section>
 <section class="section services-section" id="services"><div class="container"><div class="section-heading"><div><span class="eyebrow">BIG RESPONSIBILITIES. SMALL ERRANDS.</span><h2>Life happens here.<br><em>We’ll help you handle it.</em></h2></div><div><p>A local helping hand for the things that still need someone on the ground.</p><a class="text-link" href="services.html">Find your service {icon('arrow')}</a></div></div><div class="service-grid">{cards}</div><div class="more-services"><span>And a little more:</span>{more}</div></div></section>
 <section class="section process-section" id="how-it-works"><div class="container"><div class="section-heading"><div><span class="eyebrow">A SIMPLE WAY TO GET THINGS DONE</span><h2>Less back-and-forth.<br><em>More peace of mind.</em></h2></div><p>Start from wherever you are.<br>We’ll take it from there.</p></div>{steps()}</div></section>
 {trust_section()}
 <section class="section pricing-teaser"><div class="container split-layout"><div><span class="eyebrow">NO GUESSWORK IN THE BILL</span><h2>Small task?<br>Big relief.<br><em>Clear pricing.</em></h2><p>Every task is different. The way we price it shouldn’t be a mystery.</p><a class="text-link" href="pricing.html">See the full breakdown {icon('arrow')}</a></div><div class="price-receipt"><span class="receipt-eyebrow">YOUR TASK, BROKEN DOWN</span><dl><div><dt>Planning & coordination</dt><dd>{rupees(SITE["base_fee"])}<span>base fee / task</span></dd></div><div><dt>Time on the ground</dt><dd>{rupees(SITE["runner_hourly"])}<span>per hour · 30-min increments</span></dd></div><div><dt>Travel & other expenses</dt><dd>At cost<span>agreed in your quote</span></dd></div></dl><p>{icon('check')} You approve the quote before we begin.</p>{link_button('Get my quote','request.html')}</div></div></section>
 <section class="section"><div class="container faq-layout"><div><span class="eyebrow">A FEW THINGS YOU MIGHT BE WONDERING</span><h2>Good questions.<br><em>Clear answers.</em></h2><a class="text-link" href="faq.html">All questions {icon('arrow')}</a></div>{faq_list(FAQS[:4])}</div></section>{cta()}'''


def services_page():
    sections = ''
    for i,s in enumerate(SERVICES):
        sections += f'''<section class="service-detail" id="{s['id']}"><div class="service-detail-heading"><span class="service-icon">{icon(s['icon'])}</span><div><span class="eyebrow">SERVICE {i+1:02d}</span><h2>{e(s['name'])}</h2></div></div><div><p>{e(s['intro'])}</p><ul class="check-list">{''.join('<li>'+icon('check')+e(item)+'</li>' for item in s['items'])}</ul><p class="scope-note">{e(s['scope'])}</p><div class="inline-actions">{link_button('Request this service','request.html?category='+s['id'])}<a class="text-link" href="{s['slug']}">More about this service {icon('arrow')}</a></div></div></section>'''
    return f'''<div class="container">{breadcrumb('Our services')}<header class="page-heading"><span class="eyebrow">YOUR LOCAL HELP, IN MORE WAYS THAN ONE</span><h1>Bengaluru errands.<br><em>Consider them handled.</em></h1><p>From essential paperwork to everyday peace of mind, find the local support you need. Every task starts with a feasibility check and a clear quote.</p></header><nav class="category-links" aria-label="Service categories">{''.join(f'<a href="#{s["id"]}">{e(s["name"])}</a>' for s in SERVICES)}</nav>{sections}</div>{quick_start()}{cta()}'''


def service_page(s):
    related = [other for other in SERVICES if other['id'] != s['id']][:3]
    return f'''<div class="container">{breadcrumb(s['name'],True)}<header class="page-heading service-hero"><span class="eyebrow">{e(s['name'].upper())} IN BENGALURU</span><h1>{e(s['heading'])}</h1><p>{e(s['intro'])}</p><div class="inline-actions">{link_button('Request this service','request.html?category='+s['id'])}{whatsapp()}</div><p class="small">{rupees(SITE["base_fee"])} base fee + {rupees(SITE["runner_hourly"])}/hour runner time + applicable expenses.</p></header><section class="service-content split-layout"><div><h2>Local help with the practical steps.</h2><p>{e(s['context'])}</p><h3>What we can help with</h3><ul class="check-list">{''.join('<li>'+icon('check')+e(item)+'</li>' for item in s['items'])}</ul></div><aside class="prepare-card"><span class="service-icon">{icon(s['icon'])}</span><h2>Let’s make a plan.</h2><h3>What to share</h3><p>{e(s['prepare'])}</p><h3>A quick note</h3><p>{e(s['scope'])}</p>{link_button('Get a clear quote','request.html?category='+s['id'])}<p class="small">Do not include passwords, OTPs or sensitive document scans in the enquiry.</p></aside></section><section class="section"><span class="eyebrow">FROM REQUEST TO RELIEF</span><h2>How your errand gets done.</h2>{steps()}</section><section class="section"><div class="section-heading"><h2>You might also need</h2><a class="text-link" href="services.html">All services {icon('arrow')}</a></div><div class="service-grid">{''.join(service_card(r,i) for i,r in enumerate(related))}</div></section></div>{cta()}'''


def calculator():
    return f'''<section class="calculator" aria-labelledby="calculator-heading"><div><span class="eyebrow">A QUICK SERVICE-FEE ESTIMATE</span><h2 id="calculator-heading">Put a number to the legwork.</h2><p>Choose the expected time on the ground. We’ll confirm the actual scope and cost in your quote.</p><form id="estimate-form"><div class="field"><label for="estimate-hours">Estimated runner time</label><select id="estimate-hours" name="hours">{''.join(f'<option value="{v}"'+(' selected' if v==1 else '')+f'>{v:g} '+('hour' if v==1 else 'hours')+'</option>' for v in [.5,1,1.5,2,3,4])}</select></div><button class="button button-secondary" type="submit">Calculate estimate {icon('arrow')}</button></form></div><div class="estimate-result"><span>ESTIMATED SERVICE FEE</span><output id="estimate-total" for="estimate-hours" aria-live="polite">{rupees(SITE["base_fee"]+SITE["runner_hourly"])}</output><p id="estimate-breakdown">{rupees(SITE["base_fee"])} base fee + {rupees(SITE["runner_hourly"])} for 1 hour</p><p class="small">Excludes travel, parking, courier, government or institutional fees, urgent premiums and special handling. This is an estimate, not a confirmed quote.</p>{link_button('Get a confirmed quote','request.html')}</div></section>'''


def pricing_page():
    return f'''<div class="container">{breadcrumb('Pricing')}<header class="page-heading"><span class="eyebrow">CLEAR BEFORE WE START</span><h1>A helping hand.<br><em>An upfront price.</em></h1><p>Know what you’re paying for, from the first conversation to the final receipt. Every task gets an agreed quote before the work begins.</p></header><section class="price-grid" aria-label="Pricing breakdown"><article class="price-card"><span class="eyebrow">01 · GETTING IT PLANNED</span><h2>Base fee</h2><p class="price-amount">{rupees(SITE["base_fee"])}<span>/ task</span></p><p>Intake, feasibility, planning and coordination for your task.</p></article><article class="price-card featured"><span class="eyebrow">02 · GETTING IT DONE</span><h2>Runner time</h2><p class="price-amount">{rupees(SITE["runner_hourly"])}<span>/ hour</span></p><p>Time on the ground, billed in 30-minute increments, with standard updates.</p></article><article class="price-card"><span class="eyebrow">03 · THE OTHER BITS</span><h2>Expenses</h2><p class="price-amount price-word">At cost</p><p>Travel, parking, courier and institutional fees. Special handling is quoted separately.</p></article></section>{calculator()}<section class="section"><div class="section-heading"><div><span class="eyebrow">WHAT THAT CAN LOOK LIKE</span><h2>Two everyday examples.</h2></div><p>Illustrative costs only.<br>Your task gets its own quote.</p></div><div class="example-grid"><article class="example-card"><span class="service-icon">{icon('document')}</span><h3>RTO challan payment</h3><dl><div><dt>Base fee</dt><dd>{rupees(SITE["base_fee"])}</dd></div><div><dt>Runner · 1 hour</dt><dd>{rupees(SITE["runner_hourly"])}</dd></div><div><dt>Illustrative travel</dt><dd>₹100</dd></div><div><dt>Example challan</dt><dd>₹500</dd></div><div class="total"><dt>Illustrative total</dt><dd>{rupees(SITE["base_fee"]+SITE["runner_hourly"]+600)}</dd></div></dl></article><article class="example-card"><span class="service-icon">{icon('package')}</span><h3>Document pickup & courier</h3><dl><div><dt>Base fee</dt><dd>{rupees(SITE["base_fee"])}</dd></div><div><dt>Runner · 1.5 hours</dt><dd>{rupees(SITE["runner_hourly"]*1.5)}</dd></div><div><dt>Illustrative travel</dt><dd>₹150</dd></div><div><dt>Example courier cost</dt><dd>₹200</dd></div><div class="total"><dt>Illustrative total</dt><dd>{rupees(SITE["base_fee"]+SITE["runner_hourly"]*1.5+350)}</dd></div></dl></article></div></section><section class="section pricing-notes"><h2>A few things to know.</h2><ul><li>The base fee is non-refundable once task planning begins.</li><li>Government and institutional fees are additional, with receipts.</li><li>Urgent, multi-stop and sensitive-item tasks may require a special quote.</li><li>Cancellation within two hours of the task start may incur charges.</li><li>Recurring tasks and corporate accounts can be quoted for your specific needs.</li></ul><a class="text-link" href="terms.html">Read the terms {icon('arrow')}</a></section></div>{cta()}'''


def integration_fields(subject):
    return f'''<input type="hidden" name="access_key" value="{e(SITE['web3forms_key'])}"><input type="hidden" name="subject" value="{e(subject)}"><input type="hidden" name="from_name" value="TaskMetro website"><input class="honeypot" type="checkbox" name="botcheck" tabindex="-1" autocomplete="off" aria-hidden="true">'''


def request_page():
    return f'''<div class="container">{breadcrumb('Request a task')}<header class="page-heading compact"><span class="eyebrow">LET’S TAKE SOMETHING OFF YOUR LIST</span><h1>What do you need<br><em>done in Bengaluru?</em></h1><p>A few details now. A clear plan and quote next. No payment is collected through this form.</p></header><div class="booking-layout"><section class="booking-card" aria-labelledby="booking-heading"><h2 id="booking-heading" class="sr-only">Request a task</h2><ol class="form-progress" aria-label="Request progress" hidden><li data-progress="1" aria-current="step"><span>1</span> Your task</li><li data-progress="2"><span>2</span> Your details</li></ol><form id="request-form" class="request-form" action="https://api.web3forms.com/submit" method="post" data-remote-form data-success="Thanks. Your task request has been received. We’ll review feasibility and contact you with the next steps within 24 hours. Your booking is not confirmed until the plan and quote are agreed.">
 {integration_fields('TaskMetro task request')}
 <fieldset data-step="1"><legend>Your task</legend><p class="step-intro">Start with what you need. We’ll figure out the practicalities with you.</p><div class="field"><label for="category">What can we help with?</label><select id="category" name="category" required>{service_options()}</select></div><div class="field"><label for="details">Tell us a little about the task</label><textarea id="details" name="details" rows="4" minlength="15" maxlength="3000" required placeholder="For example: collect a university transcript in Bengaluru and arrange a courier to Mumbai." aria-describedby="details-help"></textarea><p class="field-help" id="details-help">Share the outcome you need. Please leave out passwords, OTPs and sensitive document scans.</p></div><div class="field"><label for="location">Where in Bengaluru? <span>(optional)</span></label><input id="location" name="location" autocomplete="off" maxlength="160" placeholder="Area, institution or office name"></div><div class="field-grid"><div class="field"><label for="urgency">When do you need it?</label><select id="urgency" name="urgency"><option value="flexible">I’m flexible</option><option value="48-hours">Within 48 hours</option><option value="same-day">As soon as possible</option></select></div><div class="field"><label for="date">Preferred date <span>(optional)</span></label><input id="date" type="date" name="date"></div></div><p class="form-note">Urgent requests depend on availability. We’ll confirm what’s possible.</p><button type="button" class="button button-primary step-next" hidden>Continue to my details {icon('arrow')}</button></fieldset>
 <fieldset data-step="2"><legend>Your details</legend><p class="step-intro">So a real person can get back to you with a plan.</p><div class="field"><label for="name">Your name</label><input id="name" name="name" autocomplete="name" maxlength="100" required></div><div class="field"><label for="email">Email address</label><input id="email" name="email" type="email" autocomplete="email" maxlength="254" required></div><div class="field-grid"><div class="field"><label for="contact-method">Preferred way to reach you</label><select id="contact-method" name="contactMethod"><option value="email">Email</option><option value="whatsapp">WhatsApp</option><option value="phone">Phone</option></select></div><div class="field"><label for="phone">Phone number <span id="phone-optional">(optional)</span></label><input id="phone" name="phone" type="tel" autocomplete="tel" maxlength="30" placeholder="Include country code, e.g. +91" aria-describedby="phone-help"></div></div><p class="field-help" id="phone-help">A phone number is needed if you prefer WhatsApp or a call.</p><div class="request-summary" aria-live="polite"><strong>Your request</strong><span id="request-summary">Share your task details above.</span></div><label class="checkbox-label"><input type="checkbox" name="agreeTerms" required><span>I agree to the <a href="terms.html" target="_blank" rel="noopener">Terms of Service</a> and have read the <a href="privacy.html" target="_blank" rel="noopener">Privacy Policy</a>.</span></label><div class="form-actions"><button type="button" class="button button-quiet step-back" hidden>Back</button><button type="submit" class="button button-primary">Send my request {icon('arrow')}</button></div><p class="small">No card details. No payment now. We’ll confirm the quote with you first.</p></fieldset><p class="form-status" role="status" aria-live="polite" tabindex="-1"></p></form><noscript><p class="form-note">All fields are shown above. Submit the form to continue securely with our form provider, Web3Forms.</p></noscript></section><aside class="booking-aside"><span class="eyebrow">YOU’RE IN LOCAL HANDS</span><h2>A request today.<br>A little relief next.</h2><ul class="check-list"><li>{icon('check')} A response within 24 hours</li><li>{icon('check')} Feasibility checked before work</li><li>{icon('check')} A clear quote for your approval</li><li>{icon('check')} Human support along the way</li></ul><div class="aside-price"><span>THE PRICING STARTS WITH</span><strong>{rupees(SITE["base_fee"])} <small>base fee</small></strong><p>+ {rupees(SITE["runner_hourly"])}/hour runner time & applicable expenses.</p><a href="pricing.html">Understand the pricing</a></div><p>Would you rather talk it through?</p>{whatsapp()}</aside></div></div>'''


def contact_page():
    return f'''<div class="container">{breadcrumb('Contact')}<header class="page-heading"><span class="eyebrow">A REAL PERSON AT THE OTHER END</span><h1>Let’s talk about<br><em>your Bengaluru task.</em></h1><p>Have a question, a recurring requirement or something unusual on your list? We’re happy to hear it.</p></header><div class="contact-methods"><article>{icon('chat')}<h2>Start a conversation.</h2><p>For task questions and time-sensitive enquiries.</p>{whatsapp()}</article><article>{icon('phone')}<h2>Give us a call.</h2><a class="contact-value" href="tel:{SITE['telephone']}">{SITE['telephone_display']}</a><p>{SITE['hours']}</p></article><article>{icon('mail')}<h2>Drop us a note.</h2><a class="contact-value" href="mailto:{SITE['email']}">{SITE['email']}</a><p>We aim to respond within 24 hours.</p></article></div><section class="contact-form-layout section"><div><span class="eyebrow">SOMETHING ON YOUR MIND?</span><h2>Send a quick hello.</h2><p>For a specific task, our short request form gives us a head start.</p>{link_button('Request a task instead','request.html','secondary')}</div><form class="contact-form booking-card" id="contact-form" action="https://api.web3forms.com/submit" method="post" data-remote-form data-success="Thanks. Your message has been received. We’ll get back to you within 24 hours.">{integration_fields('TaskMetro contact message')}<div class="field"><label for="contact-name">Your name</label><input id="contact-name" name="name" autocomplete="name" maxlength="100" required></div><div class="field"><label for="contact-email">Email address</label><input id="contact-email" name="email" type="email" autocomplete="email" maxlength="254" required></div><div class="field"><label for="message">How can we help?</label><textarea id="message" name="message" rows="5" maxlength="3000" required aria-describedby="message-help"></textarea><p class="field-help" id="message-help">Please leave out passwords, OTPs and sensitive documents.</p></div><p class="small">We use your details to respond to this enquiry. Read our <a href="privacy.html">Privacy Policy</a>.</p><button type="submit" class="button button-primary">Send my message {icon('arrow')}</button><p class="form-status" role="status" aria-live="polite" tabindex="-1"></p></form></section></div>'''


def about_page():
    story=(ROOT/'content/founder-story.html').read_text()
    return f'''<div class="container">{breadcrumb('Our story')}<header class="page-heading"><span class="eyebrow">ROOTED IN BENGALURU. CONNECTED TO YOU.</span><h1>Distance happens.<br><em>Care travels further.</em></h1><p>Life can take you anywhere. Your responsibilities don’t always come along. TaskMetro exists to bridge that distance with local knowledge and a very human helping hand.</p></header><section class="story-intro split-layout"><div><h2>Someone here,<br>when you can’t be.</h2><p>A pending document. A property to check. A small errand that suddenly needs a long journey. We believe you should have someone you can turn to in Bengaluru.</p><p>Our mission is to make those everyday responsibilities easier through clear communication, thoughtful coordination and care in the details.</p></div><div class="story-quote"><span class="eyebrow">OUR VISION</span><blockquote>“To be the most trusted extended family in Bengaluru for people living anywhere in the world.”</blockquote><span>From the TaskMetro founding story</span></div></section><section class="section"><div class="section-heading"><div><span class="eyebrow">THE PEOPLE BEHIND THE PROMISE</span><h2>Local roots. Personal commitment.</h2></div></div><div class="team-grid"><article class="team-card"><img src="assets/founder.jpeg" width="1280" height="1280" alt="Hayath Kargal, founder and CEO of TaskMetro" loading="lazy" decoding="async"><div><span class="eyebrow">FOUNDER & CEO</span><h3>Hayath Kargal</h3><p>From Kargal to Bengaluru, Hayath’s journey combines community values, local experience and entrepreneurship. TaskMetro grew from his observation that important responsibilities still need a trusted physical presence.</p><details class="founder-story"><summary>Read the story behind TaskMetro</summary><div>{story}</div></details></div></article><article class="team-card"><img src="assets/Raghavendra.jpeg" width="557" height="579" alt="Raghavendra Neelekani, co-founder and software engineer" loading="lazy" decoding="async"><div><span class="eyebrow">CO-FOUNDER & SOFTWARE ENGINEER</span><h3>Raghavendra Neelekani</h3><p>Originally from Sirsi, Karnataka, Raghavendra brings software engineering experience and an entrepreneurial approach to TaskMetro. His work supports a practical goal: making remote coordination simpler for people with tasks in Bengaluru.</p></div></article></div></section><section class="section values-section"><span class="eyebrow">WHAT GUIDES THE WORK</span><h2>Good service starts with care.</h2><div class="values-grid"><article>{icon('shield')}<h3>Trust</h3><p>Clear expectations and responsible handling.</p></article><article>{icon('heart')}<h3>Care</h3><p>Attention to the details that matter to you.</p></article><article>{icon('pin')}<h3>Local knowledge</h3><p>A practical understanding of the city.</p></article><article>{icon('chat')}<h3>Clarity</h3><p>Human communication from start to finish.</p></article></div></section></div>{cta()}'''


def build(production=False, output=None):
    global BASE, PRODUCTION, ROOT
    PRODUCTION = production
    BASE = SITE['production_url'] if production else SITE['preview_url']
    original_root = ROOT
    # Content is read from the source tree; alternate output is used by validation.
    pages = [
        ('index.html','Bengaluru Errand & Concierge Services | TaskMetro','Get Bengaluru errands done from anywhere. Document pickups, property checks and local assistance with upfront quotes and human support.',home(),None,FAQS[:4]),
        ('services.html','Errand Services in Bengaluru | TaskMetro','Explore Bengaluru errand services: RTO paperwork, property checks, document delivery, medical pickups and personal concierge support.',services_page(),None,None),
        ('pricing.html','Errand Service Pricing Bengaluru | TaskMetro',f'Clear TaskMetro pricing: {rupees(SITE["base_fee"])} base fee + {rupees(SITE["runner_hourly"])}/hour runner time and expenses. Estimate your service fee and request an upfront quote.',pricing_page(),None,None),
        ('request.html','Request a Bengaluru Errand | TaskMetro','Tell TaskMetro what you need done in Bengaluru. Share your task in two simple steps and get an upfront quote. No online payment required.',request_page(),None,None),
        ('contact.html','Contact TaskMetro | Bengaluru Errand Help','Call, email or WhatsApp TaskMetro for Bengaluru errand assistance. Ask about task feasibility, recurring support and upfront quotes.',contact_page(),None,None),
        ('about.html','About TaskMetro | Your Local Bengaluru Helping Hand','Meet the people behind TaskMetro. Learn how local knowledge and human support help you handle Bengaluru errands from wherever you are.',about_page(),None,None),
        ('faq.html','Bengaluru Errand Service FAQs | TaskMetro','Questions about Bengaluru errands? Understand TaskMetro pricing, coverage, task updates, authorizations and service timelines.',f'<div class="container">{breadcrumb("FAQs")}<header class="page-heading"><span class="eyebrow">LET’S CLEAR THINGS UP</span><h1>Good questions.<br><em>Thoughtful answers.</em></h1><p>A little clarity goes a long way. Here’s what to know before we take on your Bengaluru task.</p></header><section class="faq-page" aria-label="Frequently asked questions">{faq_list(FAQS)}</section></div>{cta()}',None,FAQS),
    ]
    for name,title,desc in [('terms','Terms of Service | TaskMetro','Read TaskMetro service terms for Bengaluru errands, including scope, payments, cancellation, refunds and responsibilities.'),('privacy','Privacy Policy | TaskMetro','Learn how TaskMetro collects, uses and protects information shared for Bengaluru errand enquiries and service coordination.')]:
        body=f'<div class="container">{breadcrumb(title.split(" | ")[0])}<header class="page-heading compact"><span class="eyebrow">THE DETAILS MATTER</span><h1>{title.split(" | ")[0]}</h1></header><article class="legal-content">{(original_root/("content/"+name+".html")).read_text()}</article></div>'
        pages.append((name+'.html',title,desc,body,None,None))
    pages.append(('404.html','Page Not Found | TaskMetro','This page could not be found. Explore TaskMetro services or get help with your Bengaluru task.',f'<section class="container error-page"><span class="eyebrow">404 · A SMALL DETOUR</span><h1>This one’s<br><em>off the map.</em></h1><p>We couldn’t find that page. Let’s get you back to something useful.</p><div class="inline-actions">{link_button("Back to home","index.html")}{link_button("Explore services","services.html","secondary")}</div></section>',None,None))
    pages.extend((s['slug'],s['title'],s['description'],service_page(s),s,None) for s in SERVICES)
    if output:
        ROOT=Path(output);ROOT.mkdir(parents=True,exist_ok=True)
        if ROOT.resolve()!=original_root.resolve():
            for directory in ('assets','css','js'):
                shutil.copytree(original_root/directory,ROOT/directory,dirs_exist_ok=True)
    (ROOT/'js').mkdir(exist_ok=True)
    config={'baseFee':SITE['base_fee'],'hourlyRate':SITE['runner_hourly'],'categories':[s['id'] for s in SERVICES]}
    (ROOT/'js/site-config.mjs').write_text('// Generated by scripts/build_site.py. Edit content/site.json instead.\nexport const SITE = Object.freeze('+json.dumps(config,separators=(',',':'))+');\n')
    for path,title,desc,body,service,faqs in pages:
        write_page(path,title,desc,body,service,faqs,'booking-page' if path=='request.html' else '')
    ns='http://www.sitemaps.org/schemas/sitemap/0.9'
    ET.register_namespace('',ns)
    xml=ET.Element('{'+ns+'}urlset')
    for path,*rest in pages:
        if path=='404.html':continue
        element=ET.SubElement(xml,'{'+ns+'}url')
        ET.SubElement(element,'{'+ns+'}loc').text=urljoin(BASE,'' if path=='index.html' else path)
        ET.SubElement(element,'{'+ns+'}lastmod').text=UPDATED
    ET.indent(xml)
    ET.ElementTree(xml).write(ROOT/'sitemap.xml',encoding='UTF-8',xml_declaration=True)
    robots='User-agent: *\nAllow: /\n'
    if production:robots+='\nSitemap: '+BASE+'sitemap.xml\n'
    (ROOT/'robots.txt').write_text(robots)
    (ROOT/'.nojekyll').write_text('')
    print(f'Built {len(pages)} static pages for {BASE} (indexing {"enabled" if production else "disabled"}).')
    ROOT=original_root


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--production',action='store_true',help='Use the live origin and enable indexing. Only run for promotion to the live site.')
    parser.add_argument('--output',type=Path,help='Write pages to a separate output directory, for validation.')
    args=parser.parse_args()
    build(args.production,args.output)
