# A Silver Hair — Branded OG PNG v2 drop-in

This patch is built against the current A Silver Hair SEO/GEO-integrity `build_site.py` and the current GitHub Pages/X publishing workflow.

## Drop-in files

Replace/add exactly these repository paths:

```text
/build_site.py                    REPLACE
/og_cards.py                      ADD
/requirements.txt                 ADD
/.github/workflows/main.yml       REPLACE
```

No publisher queue/state files, X credentials, IndexNow key, article images, CSS, or existing post data are included or replaced.

## What changes

- Generates a dedicated **1200×630 PNG** social card for every published article.
- Generates `/assets/og/og-default.png` for the homepage, About page, topic hubs and other non-article pages.
- Article page `og:image` / `twitter:image` now point to the generated PNG card rather than the ordinary article cover.
- Adds `og:image:type`, width, height and alt metadata.
- Keeps `twitter:card=summary_large_image`.
- Balances short and long titles automatically using pixel-measured wrapping and stepped font sizes.
- Uses the article `dek` for social description when present; otherwise derives a clean excerpt from the article body.
- Keeps the existing website article-cover system unchanged.
- Installs Pillow in every GitHub Actions job that calls `build_site.py` (build, IndexNow rebuild, X publisher rebuild).

## Optional Vivienne portrait

The patch works immediately without another asset. If no portrait is supplied, it renders a deliberate silver-hair graphic fallback rather than a broken-image placeholder.

For a real Vivienne portrait, add **one** of these later:

```text
/publisher/static/vivienne-og-portrait.png
/publisher/static/vivienne-og-portrait.jpg
/publisher/static/vivienne-og-portrait.jpeg
/publisher/static/vivienne-og-portrait.webp
```

Recommended source: at least ~700 px tall, head-and-shoulders or waist-up, with Vivienne centered. The renderer crops it into the left portrait panel automatically. No code change is needed.

## Generated output

A normal build creates:

```text
/_site/assets/og/og-default.png
/_site/assets/og/001-<slug>.png
/_site/assets/og/002-<slug>.png
...
```

These are generated artifacts; do not hand-edit them.

## Deploy

1. Back up the four paths above if desired.
2. Drop the files into the repository at the exact paths shown.
3. Commit/push.
4. Let the existing `Publish A Silver Hair` workflow run.
5. Open one built article and inspect page source for `og:image` and `twitter:image`; both should point to an `https://asilverhair.com/assets/og/*.png` URL.

No GitHub secrets or environment variables need to change.

## Existing X posts

X may retain cached previews for URLs it has already crawled. New article URLs should use the new PNG cards immediately after the site build is live. Existing posts/cards may not refresh instantly even though the page metadata is correct.

## Local build

```bash
python3 -m pip install -r requirements.txt
python3 build_site.py --all
```

## Integrity notes

The patch deliberately does **not** change:

- publication dates / timezone handling
- topic hubs
- SEO/GEO structured data beyond pointing article `image` at the social PNG
- IndexNow behavior
- RSS behavior
- archive search
- FeetFinder pages/links
- X posting credentials or posting logic
- `publisher/state.json` / `publisher/x-state.json`
