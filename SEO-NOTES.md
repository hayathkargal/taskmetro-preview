# SEO and conversion implementation

## Search intent and page map

Each service has a crawlable HTML landing page with its own description, scope,
preparation guidance and request CTA. These are relevant content pages, not duplicated
city-keyword variants. Bengaluru is the current service area; Bangalore is used
naturally where appropriate in the source business context.

| Page | Main search intent |
| --- | --- |
| `index.html` | Bengaluru errand services; Bengaluru concierge services; remote local assistance |
| `rto-government-errands-bengaluru.html` | RTO assistance Bengaluru; government-document errands |
| `property-errands-bengaluru.html` | Property checks Bengaluru; utility and key-handover errands |
| `medical-errands-bengaluru.html` | Prescription pickup Bengaluru; lab-report collection |
| `document-pickup-delivery-bengaluru.html` | Document pickup and delivery Bengaluru |
| `banking-paperwork-bengaluru.html` | Banking and insurance paperwork assistance Bengaluru |
| `transcript-collection-bengaluru.html` | University transcript collection Bengaluru |
| `urgent-errands-bengaluru.html` | Urgent errand services Bengaluru |
| `concierge-services-bengaluru.html` | Personal concierge services Bengaluru |
| `custom-errands-bengaluru.html` | Custom Bengaluru errands and local coordination |
| `pricing.html` | Bengaluru errand-service pricing and cost estimates |

## Metadata and discovery

- Titles are unique and under 60 characters; descriptions are under 150 characters.
- Metadata is generated into the HTML rather than depending on JavaScript execution.
- Every page has a canonical URL, Open Graph metadata, Twitter card and a local
  1200×630 sharing image with alternative text.
- Shared templates produce one main landmark and one H1, followed by ordered headings.
- Service cards, breadcrumbs, navigation and contextual links expose the service pages.
- The XML sitemap contains every canonical content page and excludes the 404 page.
- Preview and production builds use separate origins and indexing policies.

## JSON-LD

The linked graph includes `LocalBusiness`, `WebSite`, `WebPage`, `BreadcrumbList`,
`OfferCatalog`/`Offer` and service-specific `Service` nodes. FAQ pages also include
`FAQPage` with the questions and answers visible on that page.

Only published business details are used. No street address, coordinates, review
count, ratings or certification is invented. A verified public street address and
postal code have not been supplied, so Google Local Business rich-result eligibility
is not asserted. The city-level address is valid descriptive Schema.org data but
does not satisfy every Google feature's required fields. FAQ rich results are also
restricted by Google and are not promised for this business.

Reviews are deferred until the exact public source and usable excerpts are supplied.
There is no `AggregateRating` or review-star markup. Google excludes self-serving
LocalBusiness reviews from review-star eligibility, including embedded third-party
reviews. Visible customer feedback can be added later with attribution and a link.

## Conversion and performance

- A homepage service selector leads directly to the preselected request category.
- Service-page CTAs carry the chosen category into the same form.
- The request form uses two short stages, with accessible validation, Back navigation
  and an explicit quote-before-booking confirmation.
- Actual published base and hourly fees drive the estimate; 30-minute billing and
  excluded expenses are clear. There are no invented package prices or guarantees.
- Pricing, process commitments, named founders and contact channels provide factual
  trust signals while reviews are deferred.
- Mobile navigation, a mobile CTA bar, skip link, focus states, form labels,
  reduced-motion styles and no-JavaScript form fallbacks are included.
- System fonts, a small SVG hero, deferred JavaScript modules, explicit image dimensions
  and lazy-loaded founder photos limit dependencies and layout shifts.
- There are no trackers, browser-storage drafts or automatic submission retries.

## Before promoting to the live site

Build a production release, verify the final business details and form-provider domain
settings, then check mobile rendering, performance and real delivery with approval.
Validate the deployed pages with Google's Rich Results Test and URL Inspection,
and submit the production sitemap in Search Console. The preview stays `noindex`.
Code improvements cannot guarantee a ranking position, rich result, or measured
Core Web Vitals score; those require external validation and ongoing observation.

References: [Google title guidance](https://developers.google.com/search/docs/appearance/title-link),
[Local Business structured data](https://developers.google.com/search/docs/appearance/structured-data/local-business),
[structured-data policies](https://developers.google.com/search/docs/appearance/structured-data/sd-policies),
[review snippet guidance](https://developers.google.com/search/docs/appearance/structured-data/review-snippet).
