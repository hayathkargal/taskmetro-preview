# TaskMetro Preview Website

A static, responsive Bengaluru errand-services website. The deployed pages use
HTML, CSS and JavaScript modules, with no framework or client-side package runtime.

## Preview locally

```sh
python3 scripts/build_site.py
python3 scripts/serve.py
```

Open [the local preview](http://127.0.0.1:8765/taskmetro-preview/).
The server listens only on the local computer and reproduces the GitHub Pages
subdirectory and custom 404 behavior.

## Edit and build

- `content/site.json`: business details, published fees, form key and site origins.
- `content/services.json`: the nine service categories and their landing-page content.
- `content/reviews.json`: future verified review source and approved excerpts; currently empty.
- `content/terms.html`, `content/privacy.html`: preserved legal copy.
- `content/founder-story.html`: preserved founding story.
- `scripts/build_site.py`: shared layouts, page content and SEO generation.
- `css/styles.css`: shared responsive design, focus states and reduced-motion support.
- `js/main.mjs`, `js/booking.mjs`: navigation, booking enhancement and submission handling.
- `assets/`: existing branding and founder photos, custom city artwork and sharing image.

Rebuild after editing content or templates. The generated root HTML files, sitemap,
robots file and `js/site-config.mjs` are deployable output; direct edits are overwritten
by the next build. The build validates the requested title and description limits.

## Preview deployment

Publish the checked-in root files from the preview repository using GitHub Pages,
with branch `main` and folder `/ (root)`. The intended address is
[hayathkargal.github.io/taskmetro-preview](https://hayathkargal.github.io/taskmetro-preview/).
Leave the custom domain empty. `CNAME` is excluded and ignored.

The default build uses preview URLs and `noindex, nofollow` metadata on every page.
It allows crawling so search engines can see the exclusion directive. A `robots.txt`
inside a GitHub project subdirectory does not control the entire `github.io` host;
the page metadata is the preview indexing control. Exclusion is not access control:
the preview is publicly accessible if its repository is published.

## Preparing a live release

```sh
python3 scripts/build_site.py --production --output /tmp/taskmetro-release
```

This creates a complete static release directory with live canonical URLs,
social URLs, structured data, an updated sitemap and indexing enabled except on
the 404 page. It leaves this preview checkout in preview mode. Publishing that
release to the live repository and configuring its domain are separate actions.

## Forms and requests

The existing Web3Forms integration is retained. The form key is a public client
integration key, not a server secret. Configure provider-side domain restrictions
for each intended deployment and use the provider's spam controls as needed.

Requests are enquiries for feasibility and a quote, not confirmed purchases.
No payment processor is present. The estimator shows the service fee only and
explicitly excludes travel and third-party expenses.

JavaScript enhances the request form into two steps. With JavaScript disabled,
all fields remain visible and standard HTML submission goes to Web3Forms.
Successful delivery is shown only after a positive provider response. Errors retain
entered details; uncertain delivery is distinguished from rejection. Submissions
are not retried automatically, and simultaneous submissions are suppressed.

The preview still uses the original destination and can send real enquiries.
Automated tests substitute the sender and never contact the real form endpoint.
No personal form data is persisted to browser storage or added to URLs.

## Validation and development tools

The static build and preview server need Python 3.9+ only. Tests and sharing-image
rendering additionally use a Node version matching `package.json` and the development packages:

```sh
npm ci
npm test
npm run assets
```

The Python checks cover both deployment modes, 19 pages, metadata, semantic
headings, image dimensions, internal links, structured data, sitemap and asset size.
JavaScript tests cover pricing, parameter allowlists, form stages, contact validation,
duplicate prevention, positive confirmation, failure preservation and timeouts.

Browser rendering, real mobile-device checks, Core Web Vitals and an authorized
end-to-end email delivery check are still needed before a live release. The browser
connection was unavailable during this implementation; no Lighthouse score is claimed.

See [SEO-NOTES.md](SEO-NOTES.md) for the keyword map, structured data and launch details.
