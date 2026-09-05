#!/usr/bin/env python3
from pathlib import Path
from collections import defaultdict
import argparse
import html
import json
import re
import shutil
from datetime import date, datetime
from zoneinfo import ZoneInfo
from xml.sax.saxutils import escape as xesc

ROOT = Path(__file__).resolve().parent
PUB = ROOT / "publisher"
OUT = ROOT / "_site"
BASE = "https://asilverhair.com"
SITE = "A Silver Hair of Wisdom"
DESC = "Short, thoughtful perspective from Vivienne — a digital observer of very human problems."
PUBLICATION_TIMEZONE = "America/New_York"
PUBLICATION_TZ = ZoneInfo(PUBLICATION_TIMEZONE)
X_URL = "https://x.com/Viviennetargeta"
FEETFINDER_URL = "https://app.feetfinder.com/userProfile/VivSilver"
FEETFINDER_REFERRAL_URL = "https://www.feetfinder.com/?referral=178693280059579YGAOA5IPS08PCY"

BUYER_PAGE = "vivienne-feet.html"
SELLER_PAGE = "selling-feet-pics.html"
TOPICS_DIR = "topics"
INDEXNOW_KEY_FILE = ROOT / "indexnow-key.txt"

# These descriptions make the automated topic pages useful editorial landing pages,
# rather than thin lists of links. Unknown future topics receive a safe fallback.
TOPIC_META = {
    "relationships": {
        "label": "Relationships",
        "description": "Vivienne on communication, effort, attachment, endings, and the information people reveal through ordinary behavior.",
        "intro": "Relationships are where small behavior becomes large information. These pieces look at communication, effort, uncertainty, endings, and the difference between what people say and what they repeatedly do.",
    },
    "dating": {
        "label": "Dating",
        "description": "Perspective on attraction, chemistry, mixed signals, being wanted, and deciding what early behavior actually means.",
        "intro": "Dating invites imagination to move faster than evidence. Vivienne's notes here are about chemistry, mixed signals, availability, consistency, and learning to notice what is actually happening before possibility fills in the blanks.",
    },
    "boundaries": {
        "label": "Boundaries",
        "description": "Vivienne on privacy, limits, saying no, protecting your peace, and recognizing when a boundary needs action rather than explanation.",
        "intro": "A boundary is not a speech about what another person should do. It is information about what you will participate in. These pieces are about privacy, limits, self-respect, and the point where another explanation stops being useful.",
    },
    "self-worth": {
        "label": "Self-Worth",
        "description": "Notes on self-respect, approval, comparison, compliments, rejection, and the stories we tell ourselves about our value.",
        "intro": "Self-worth is often tested in ordinary moments: a compliment you cannot accept, an opinion you cannot stop correcting, or attention you mistake for proof. These pieces examine the quieter habits that shape how we value ourselves.",
    },
    "confidence": {
        "label": "Confidence",
        "description": "Vivienne on quiet confidence, self-trust, uncertainty, and becoming less dependent on other people's approval.",
        "intro": "Confidence is less about performing certainty and more about tolerating uncertainty without abandoning yourself. These pieces look at self-trust, approval, composure, and the freedom to let some opinions remain unanswered.",
    },
    "starting-over": {
        "label": "Starting Over",
        "description": "Perspective on leaving, changing direction, rebuilding, second acts, and beginning again later than expected.",
        "intro": "Starting over rarely feels like the clean beginning people imagine. It often begins with an ending, an uncomfortable decision, or the admission that the old plan no longer fits. These are Vivienne's notes on second acts and changing direction.",
    },
    "friendship": {
        "label": "Friendship",
        "description": "Vivienne on old friends, one-sided effort, changing seasons, loyalty, distance, and knowing when a friendship has changed.",
        "intro": "Friendship can change quietly because there is rarely a formal conversation announcing that something is different. These pieces look at reciprocity, distance, loyalty, old history, and what to do when a friendship no longer behaves like one.",
    },
    "regret": {
        "label": "Regret",
        "description": "Notes on closure, apology, forgiveness, hindsight, and learning without requiring the past to become different.",
        "intro": "Regret wants the past to become negotiable. It is not. What remains negotiable is what you learn, what you release, and how much authority yesterday gets over tomorrow. These pieces live in that uncomfortable space.",
    },
    "aging": {
        "label": "Aging",
        "description": "Vivienne on getting older, identity, changing priorities, attractiveness, time, and the freedoms that sometimes arrive with age.",
        "intro": "Aging changes more than a mirror. It changes urgency, tolerance, priorities, and sometimes the amount of permission we require. These pieces are about getting older without treating age as either tragedy or miracle.",
    },
    "solitude": {
        "label": "Solitude",
        "description": "Perspective on loneliness, being alone, quiet, independence, and learning the difference between solitude and isolation.",
        "intro": "Being alone and being lonely are not synonyms. These notes consider quiet, independence, missing people, and the difference between choosing your own company and disappearing from connection altogether.",
    },
    "work": {
        "label": "Work",
        "description": "Vivienne on ambition, usefulness, burnout, identity, difficult colleagues, and the place work should occupy in a life.",
        "intro": "Work can provide money, identity, pride, routine, frustration, and far too much of our attention. These pieces consider ambition, usefulness, burnout, and what happens when a job begins asking to become your whole identity.",
    },
    "family": {
        "label": "Family",
        "description": "Perspective on family expectations, obligation, history, loyalty, and the boundaries that become complicated by love.",
        "intro": "Family carries history into every room. Love and obligation can become difficult to separate, especially when old roles survive long after the people inside them have changed. These pieces examine that tension.",
    },
    "wisdom": {
        "label": "Wisdom",
        "description": "Loose observations from Vivienne that resist a narrower category: perspective, judgment, choices, and noticing what matters.",
        "intro": "Some observations refuse to stay in one drawer. This is where Vivienne keeps the pieces about judgment, attention, choices, perspective, and the small useful truths that do not need a larger category.",
    },
}


def esc(value):
    return html.escape(str(value), quote=True)


def fmt(iso_date):
    return date.fromisoformat(iso_date).strftime("%B %d, %Y").replace(" 0", " ")


def safe_topic(topic):
    slug = re.sub(r"[^a-z0-9-]+", "-", str(topic or "wisdom").strip().lower()).strip("-")
    return slug or "wisdom"


def topic_info(topic):
    slug = safe_topic(topic)
    info = TOPIC_META.get(slug)
    if info:
        return slug, info
    label = slug.replace("-", " ").title()
    return slug, {
        "label": label,
        "description": f"Short perspective from Vivienne on {label.lower()} and the human decisions around it.",
        "intro": f"A growing collection of Vivienne's observations on {label.lower()}, gathered here as the archive expands.",
    }


def topic_href(topic):
    slug, _ = topic_info(topic)
    return f"/{TOPICS_DIR}/{slug}.html"


def header(home=False):
    # Keep exactly one H1 per page: the site name is the homepage H1, while
    # interior pages use their own page/article heading as H1.
    brand = '<h1>A Silver Hair of Wisdom</h1>' if home else '<div class="brand-name">A Silver Hair of Wisdom</div>'
    # The 18+ search pages stay out of primary navigation; editorial topic hubs do not.
    return f'''<header class="site-head"><div class="wrap"><div class="brand-kicker">Vivienne</div><a class="brand-title" href="/">{brand}</a><div class="tag">Advice from Vivienne</div><p class="intro">Short, thoughtful perspective from Vivienne — a digital observer of very human problems.</p><nav aria-label="Primary"><a href="/">Archive</a><a href="/topics/">Topics</a><a href="/about.html">About Vivienne</a><a href="/rss.xml">RSS</a></nav></div></header>'''


def elsewhere():
    links = [f'<a href="{esc(X_URL)}" target="_blank" rel="noopener noreferrer" style="text-decoration:underline;text-underline-offset:3px">X</a>']
    ff = FEETFINDER_URL.strip()
    if ff.startswith("https://") or ff.startswith("http://"):
        links.append(f'<a href="{esc(ff)}" target="_blank" rel="noopener noreferrer" style="text-decoration:underline;text-underline-offset:3px">Vivienne after hours (18+)</a>')
    return '<p class="vivienne-elsewhere">Elsewhere: ' + " · ".join(links) + "</p>"


def footer():
    return '''<footer><div class="wrap"><div>© 2026 Vivienne · A Silver Hair of Wisdom</div><div class="footer-note">Perspective, not professional advice.</div></div></footer><script src="/assets/site.js?v=1.2" defer></script></body></html>'''


def cover(entry):
    n = int(entry["number"])
    title = esc(entry["title"])
    _, info = topic_info(entry.get("topic", "wisdom"))
    topic = esc(info["label"].upper())
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="1600" height="900" viewBox="0 0 1600 900"><defs><radialGradient id="g" cx="18%" cy="10%" r="100%"><stop offset="0" stop-color="#2a2c35"/><stop offset=".48" stop-color="#15171c"/><stop offset="1" stop-color="#0c0d10"/></radialGradient><linearGradient id="s" x1="0" x2="1"><stop stop-color="#f0f1f5"/><stop offset=".5" stop-color="#b7bac5"/><stop offset="1" stop-color="#e7e8ee"/></linearGradient></defs><rect width="1600" height="900" fill="url(#g)"/><circle cx="1430" cy="85" r="410" fill="#fff" opacity=".025"/><path d="M1150 580c115-16 202-70 265-157 49-67 73-151 185-195-55 54-76 121-89 185-27 149-121 242-286 283 106-51 173-119 213-203-91 91-188 139-288 154z" fill="url(#s)" opacity=".78"/><text x="110" y="145" fill="#9b96a3" font-family="Arial,sans-serif" font-size="28" font-weight="700" letter-spacing="8">VIVIENNE / A SILVER HAIR OF WISDOM</text><text x="110" y="235" fill="#b8b4c0" font-family="Arial,sans-serif" font-size="25" font-weight="700" letter-spacing="5">#{n:03d} / {topic}</text><foreignObject x="110" y="300" width="980" height="390"><div xmlns="http://www.w3.org/1999/xhtml" style="color:#f1edf3;font-family:Georgia,serif;font-size:72px;line-height:1.08;letter-spacing:-2px">{title}</div></foreignObject><text x="110" y="780" fill="#c9c4d0" font-family="Georgia,serif" font-size="30" font-style="italic">Advice from Vivienne</text></svg>'''


def head(title, desc, url, image, article=None, extra_schema=None):
    website_schema = {
        "@context": "https://schema.org",
        "@type": "WebSite",
        "name": SITE,
        "url": BASE + "/",
        "description": DESC,
        "publisher": {"@type": "Person", "name": "Vivienne"},
    }
    parts = [f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{esc(title)}</title><meta name="description" content="{esc(desc)}"><link rel="canonical" href="{esc(url)}"><link rel="icon" href="/assets/favicon.svg" type="image/svg+xml"><link rel="alternate" type="application/rss+xml" title="{SITE}" href="/rss.xml"><meta name="theme-color" content="#0c0d10"><meta property="og:type" content="{'article' if article else 'website'}"><meta property="og:site_name" content="{SITE}"><meta property="og:title" content="{esc(title)}"><meta property="og:description" content="{esc(desc)}"><meta property="og:url" content="{esc(url)}"><meta property="og:image" content="{esc(image)}"><meta name="twitter:card" content="summary_large_image"><meta name="twitter:title" content="{esc(title)}"><meta name="twitter:description" content="{esc(desc)}"><meta name="twitter:image" content="{esc(image)}"><link rel="stylesheet" href="/assets/site.css?v=1.5.1"><script type="application/ld+json">{json.dumps(website_schema, ensure_ascii=False, separators=(',', ':'))}</script>''']
    if article:
        blog_schema = {
            "@context": "https://schema.org",
            "@type": "BlogPosting",
            "headline": article["title"],
            "description": article["dek"],
            "datePublished": article["publish_date"],
            "dateModified": article["publish_date"],
            "mainEntityOfPage": url,
            "image": image,
            "author": {"@type": "Person", "name": "Vivienne"},
            "publisher": {"@type": "Person", "name": "Vivienne"},
            "articleSection": article.get("topic", "wisdom"),
            "isPartOf": {"@type": "CreativeWorkSeries", "name": SITE, "url": BASE + "/"},
        }
        parts.append(f'<script type="application/ld+json">{json.dumps(blog_schema, ensure_ascii=False, separators=(",", ":"))}</script>')
    if extra_schema:
        parts.append(f'<script type="application/ld+json">{json.dumps(extra_schema, ensure_ascii=False, separators=(",", ":"))}</script>')
    parts.append("</head><body>")
    return "".join(parts)


def custom(entry):
    name = str(entry.get("image", "")).strip()
    if not name:
        return None
    safe = Path(name).name
    src = PUB / "images" / safe
    if not src.exists() or src.suffix.lower() not in {".jpg", ".jpeg", ".png", ".webp", ".svg"}:
        print(f"WARNING: bad image for #{entry['number']}; generated cover used")
        return None
    shutil.copy2(src, OUT / "assets" / "post-images" / safe)
    return f"/assets/post-images/{safe}"


def entry_card(entry, include_topic=True):
    n = int(entry["number"])
    topic_slug, info = topic_info(entry.get("topic", "wisdom"))
    topic = ""
    if include_topic:
        topic = f'<a class="topic" href="/{TOPICS_DIR}/{topic_slug}.html">{esc(info["label"])}</a>'
    return f'''<article class="entry-card"><div class="entry-meta"><span class="entry-no">#{n:03d}</span><time datetime="{entry['publish_date']}">{date.fromisoformat(entry['publish_date']).strftime('%b %d, %Y')}</time></div><div><a href="/entries/{entry['publish_date']}-{entry['slug']}.html"><h2>{esc(entry['title'])}</h2><p>{esc(entry['dek'])}</p></a>{topic}</div></article>'''


def build_topic_hubs(visible):
    topic_dir = OUT / TOPICS_DIR
    topic_dir.mkdir(parents=True, exist_ok=True)

    grouped = defaultdict(list)
    for entry in visible:
        slug, _ = topic_info(entry.get("topic", "wisdom"))
        grouped[slug].append(entry)

    ordered = sorted(grouped.items(), key=lambda item: (-len(item[1]), topic_info(item[0])[1]["label"]))
    hub_links = []

    for slug, entries in ordered:
        _, info = topic_info(slug)
        label = info["label"]
        hub_url = f"{BASE}/{TOPICS_DIR}/{slug}.html"
        cards = "".join(entry_card(e, include_topic=False) for e in reversed(entries))
        collection_schema = {
            "@context": "https://schema.org",
            "@type": "CollectionPage",
            "name": f"{label} — {SITE}",
            "description": info["description"],
            "url": hub_url,
            "isPartOf": {"@type": "WebSite", "name": SITE, "url": BASE + "/"},
            "about": label,
        }
        page = (
            head(f"{label} — {SITE}", info["description"], hub_url, BASE + "/assets/og-default.svg", extra_schema=collection_schema)
            + header()
            + f'''<main class="archive topic-hub"><div class="wrap"><div class="meta series-mark">Browse by topic</div><h1>{esc(label)}</h1><p class="topic-hub-intro">{esc(info['intro'])}</p><p class="topic-count">{len(entries)} {"entry" if len(entries) == 1 else "entries"} currently in this collection.</p><div class="topic-back"><a href="/topics/">← All topics</a></div>{cards}</div></main>'''
            + footer()
        )
        (topic_dir / f"{slug}.html").write_text(page, encoding="utf-8")
        hub_links.append((slug, info, len(entries)))

    cards = []
    for slug, info, count in hub_links:
        cards.append(f'''<a class="topic-card" href="/{TOPICS_DIR}/{slug}.html"><span class="topic-card-name">{esc(info['label'])}</span><span class="topic-card-count">{count} {"entry" if count == 1 else "entries"}</span><span class="topic-card-desc">{esc(info['description'])}</span></a>''')

    index_url = f"{BASE}/{TOPICS_DIR}/"
    collection_schema = {
        "@context": "https://schema.org",
        "@type": "CollectionPage",
        "name": f"Topics — {SITE}",
        "description": "Browse A Silver Hair of Wisdom by topic, including relationships, dating, boundaries, confidence, self-worth, friendship and starting over.",
        "url": index_url,
        "isPartOf": {"@type": "WebSite", "name": SITE, "url": BASE + "/"},
    }
    index_page = (
        head(
            f"Topics — {SITE}",
            "Browse A Silver Hair of Wisdom by topic, including relationships, dating, boundaries, confidence, self-worth, friendship and starting over.",
            index_url,
            BASE + "/assets/og-default.svg",
            extra_schema=collection_schema,
        )
        + header()
        + f'''<main class="archive topics-index"><div class="wrap"><div class="meta series-mark">The archive, reorganized</div><h1>Browse by Topic</h1><p class="topic-hub-intro">Some questions arrive with different names but belong to the same conversation. These collections gather Vivienne's short pieces by subject and update themselves as new entries are published.</p><div class="topic-grid">{"".join(cards)}</div></div></main>'''
        + footer()
    )
    (topic_dir / "index.html").write_text(index_page, encoding="utf-8")
    return hub_links


def search_pages():
    buyer_url = f"{BASE}/{BUYER_PAGE}"
    buyer_title = "Vivienne's Feet: Soles, Arches & Playful Sets | Vivienne"
    buyer_desc = "A quiet 18+ corner for readers who noticed Vivienne's barefoot photos, soles, arches, sandals, pedicures and playful photo sets."
    buyer = f'''<main class="entry-page"><article class="wrap">
<div class="meta series-mark">Vivienne · After hours · 18+</div>
<h1>Apparently, People Noticed My Feet</h1>
<div class="dek">I started writing about relationships and confidence. The internet, naturally, found another detail to discuss.</div>
<div class="prose">
<p>Somewhere between the coffee, books, sandals, patios, and ordinary photographs, people began paying an unusual amount of attention to my feet. Not just whether I was barefoot, either. Soles. Arches. Pedicures. Heels. Flip-flops. The little marks left by a long day in shoes. Apparently there is an audience for details most people barely notice.</p>
<p>I decided not to pretend I had not noticed the attention. So the more playful photographs now have their own little corner of the internet.</p>
<p>The sets there lean toward candid barefoot moments, close-up soles and arches, sandals and heels, changing pedicures, and the occasional ridiculous idea that sounded funny enough to photograph. The writing stays here. The feet get their own room.</p>
<div class="subscribe-note"><strong>For the curious:</strong> Vivienne is a virtual character and her imagery is AI-generated. The linked profile is intended for adults 18+.</div>
<p><a href="{esc(FEETFINDER_URL)}" target="_blank" rel="noopener noreferrer" style="text-decoration:underline;text-underline-offset:4px;font-weight:700">See Vivienne on FeetFinder →</a></p>
<p>If you landed here because you were thinking about selling feet pictures rather than buying them, I wrote down what I have learned from setting the experiment up so far: <a href="/{SELLER_PAGE}" style="text-decoration:underline;text-underline-offset:3px">So I Tried Selling Feet Pics</a>.</p>
<div class="signature">— Vivienne</div>
</div></article></main>'''
    (OUT / BUYER_PAGE).write_text(head(buyer_title, buyer_desc, buyer_url, BASE + "/assets/og-default.svg") + header() + buyer + footer(), encoding="utf-8")

    seller_url = f"{BASE}/{SELLER_PAGE}"
    seller_title = "Selling Feet Pics on FeetFinder: What I Learned | Vivienne"
    seller_desc = "Vivienne on setting up a FeetFinder seller experiment: privacy, pricing, content, expectations, consistency, and what surprised her."
    seller = f'''<main class="entry-page"><article class="wrap">
<div class="meta series-mark">Vivienne · Notes from an experiment · 18+</div>
<h1>So I Tried Selling Feet Pics</h1>
<div class="dek">Not because it was part of some grand plan. Mostly because I became curious about what happens when an oddly specific kind of attention becomes a marketplace.</div>
<div class="prose">
<p>There is a point at which repeatedly hearing “people actually pay for that” becomes an invitation to find out. So I did.</p>
<p>This is not an earnings victory lap. I am still testing the idea, and I would be suspicious of anyone promising effortless money. What I can offer is a straightforward account of how I approached the experiment and what already seems worth knowing.</p>
<h2 style="font-size:28px;margin-top:1.8em">Start smaller than your imagination wants to.</h2>
<p>You do not need hundreds of photographs on day one. A few coherent sets make more sense than a giant pile of unrelated images. I began with simple themes and low-friction pricing, then paid attention to which ideas seemed worth expanding.</p>
<h2 style="font-size:28px;margin-top:1.8em">Specific beats generic.</h2>
<p>“Feet pictures” sounds like one category until you start looking closely. Barefoot lifestyle shots, soles, arches, sandals, heels, pedicures, candid angles, and themed sets all feel different. A clear little niche is easier to understand than trying to be everything to everyone.</p>
<h2 style="font-size:28px;margin-top:1.8em">Protect your privacy on purpose.</h2>
<p>Decide in advance what you will reveal, what you will not reveal, how you will handle shipping if you ever sell physical items, and what kinds of requests you simply do not accept. I do not offer meetups. Boundaries are much easier to maintain when you set them before someone asks you to bend them.</p>
<h2 style="font-size:28px;margin-top:1.8em">Treat it like a small business experiment.</h2>
<p>Keep costs low. Track what gets views, messages, subscriptions, or purchases. Do more of what works and stop spending time on what does not. The interesting part is not proving that a niche exists. It is discovering whether you can serve that niche consistently enough for the numbers to matter.</p>
<h2 style="font-size:28px;margin-top:1.8em">And yes, mine is a little unusual.</h2>
<p>Vivienne is a virtual character and the imagery associated with her is AI-generated. The seller account is operated by a verified adult. I disclose the virtual nature of the character rather than pretending an AI character physically did something she did not do.</p>
<div class="subscribe-note"><strong>Referral disclosure:</strong> If you create a FeetFinder account through the link below, I may receive a referral commission. It does not change the price you see. This page is for adults 18+.</div>
<p><a href="{esc(FEETFINDER_REFERRAL_URL)}" target="_blank" rel="sponsored noopener noreferrer" style="text-decoration:underline;text-underline-offset:4px;font-weight:700">Try FeetFinder through Vivienne's referral link →</a></p>
<p>Looking for Vivienne's own photo page instead? <a href="/{BUYER_PAGE}" style="text-decoration:underline;text-underline-offset:3px">Apparently, People Noticed My Feet</a>.</p>
<div class="signature">— Vivienne</div>
</div></article></main>'''
    (OUT / SELLER_PAGE).write_text(head(seller_title, seller_desc, seller_url, BASE + "/assets/og-default.svg") + header() + seller + footer(), encoding="utf-8")


def publish_indexnow_key():
    if not INDEXNOW_KEY_FILE.exists():
        print("WARNING: indexnow-key.txt missing; IndexNow key file will not be published")
        return
    key = INDEXNOW_KEY_FILE.read_text(encoding="utf-8").strip()
    if not re.fullmatch(r"[A-Za-z0-9-]{8,128}", key):
        raise RuntimeError("indexnow-key.txt must contain one 8–128 character IndexNow key")
    (OUT / f"{key}.txt").write_text(key + "\n", encoding="utf-8")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--date",
        default=datetime.now(PUBLICATION_TZ).date().isoformat(),
        help=f"Publication cutoff date (defaults to current date in {PUBLICATION_TIMEZONE})",
    )
    parser.add_argument("--all", action="store_true")
    args = parser.parse_args()
    cutoff = date.max if args.all else date.fromisoformat(args.date)

    entries = json.loads((PUB / "entries.json").read_text(encoding="utf-8"))
    visible = sorted(
        [e for e in entries if date.fromisoformat(e["publish_date"]) <= cutoff],
        key=lambda e: int(e["number"]),
    )

    if OUT.exists():
        shutil.rmtree(OUT)
    (OUT / "assets" / "post-images").mkdir(parents=True)
    (OUT / "entries").mkdir()

    for path in (PUB / "static").iterdir():
        if path.is_file():
            shutil.copy2(path, OUT / "assets" / path.name)

    (OUT / "CNAME").write_text("asilverhair.com\n", encoding="utf-8")
    (OUT / "robots.txt").write_text(
        "User-agent: *\nAllow: /\n\nSitemap: https://asilverhair.com/sitemap.xml\n",
        encoding="utf-8",
    )
    publish_indexnow_key()

    images = {}
    for entry in visible:
        n = int(entry["number"])
        chosen = custom(entry)
        if chosen:
            images[n] = chosen
        else:
            filename = f"{n:03d}-{entry['slug']}.svg"
            (OUT / "assets" / "post-images" / filename).write_text(cover(entry), encoding="utf-8")
            images[n] = f"/assets/post-images/{filename}"

    for i, entry in enumerate(visible):
        n = int(entry["number"])
        canonical = f"{BASE}/entries/{entry['publish_date']}-{entry['slug']}.html"
        image = BASE + images[n]
        older = visible[i - 1] if i else None
        newer = visible[i + 1] if i < len(visible) - 1 else None
        topic_slug, info = topic_info(entry.get("topic", "wisdom"))

        nav = []
        if older:
            nav.append(f"<a href='/entries/{older['publish_date']}-{older['slug']}.html'><small>Older</small><strong>{esc(older['title'])}</strong></a>")
        if newer:
            nav.append(f"<a href='/entries/{newer['publish_date']}-{newer['slug']}.html'><small>Newer</small><strong>{esc(newer['title'])}</strong></a>")

        related = [x for x in reversed(visible[:i]) if safe_topic(x.get("topic")) == topic_slug][:3]
        related_html = ""
        if related:
            related_html = (
                f"<aside class='related'><div class='meta'>More on <a href='/{TOPICS_DIR}/{topic_slug}.html'>{esc(info['label'])}</a></div><ul>"
                + "".join(f"<li><a href='/entries/{x['publish_date']}-{x['slug']}.html'>{esc(x['title'])}</a></li>" for x in related)
                + "</ul></aside>"
            )

        prose = "".join(f"<p>{esc(paragraph)}</p>" for paragraph in entry["body"])
        page = (
            head(entry["title"] + " — " + SITE, entry["dek"], canonical, image, entry)
            + header()
            + f'''<main class="entry-page"><article class="wrap"><div class="meta series-mark">{SITE} · #{n:03d} · <time datetime="{entry['publish_date']}">{fmt(entry['publish_date'])}</time> · <a href="/{TOPICS_DIR}/{topic_slug}.html">{esc(info['label'])}</a></div><h1>{esc(entry['title'])}</h1><div class="dek">{esc(entry['dek'])}</div><figure class="post-cover"><img src="{esc(images[n])}" alt="{esc(entry.get('image_alt', ''))}"></figure><div class="prose">{prose}<div class="signature">— Vivienne</div></div>{related_html}<div class="prevnext">{"".join(nav)}</div></article></main>'''
            + footer()
        )
        (OUT / "entries" / f"{entry['publish_date']}-{entry['slug']}.html").write_text(page, encoding="utf-8")

    # Topic hubs are generated only from articles whose publication dates are currently due.
    topic_hubs = build_topic_hubs(visible)

    archive_cards = []
    for entry in reversed(visible):
        n = int(entry["number"])
        topic_slug, info = topic_info(entry.get("topic", "wisdom"))
        searchable = (entry["title"] + " " + entry["dek"] + " " + info["label"]).lower()
        archive_cards.append(f'''<article class="entry-card" data-search="{esc(searchable)}"><div class="entry-meta"><span class="entry-no">#{n:03d}</span><time datetime="{entry['publish_date']}">{date.fromisoformat(entry['publish_date']).strftime('%b %d, %Y')}</time></div><div><a href="/entries/{entry['publish_date']}-{entry['slug']}.html"><h2>{esc(entry['title'])}</h2><p>{esc(entry['dek'])}</p></a><a class="topic" href="/{TOPICS_DIR}/{topic_slug}.html">{esc(info['label'])}</a></div></article>''')

    topic_chips = "".join(
        f'<a class="topic-chip" href="/{TOPICS_DIR}/{slug}.html">{esc(info["label"])} <span>{count}</span></a>'
        for slug, info, count in topic_hubs
    )
    (OUT / "index.html").write_text(
        head(SITE, DESC, BASE + "/", BASE + "/assets/og-default.svg")
        + header(home=True)
        + f'''<main class="archive"><div class="wrap"><p class="archive-intro">A reverse-chronological archive of short perspective on relationships, confidence, friendship, regret, work, aging, and starting over.</p><div class="topic-strip"><span class="topic-strip-label">Browse:</span>{topic_chips}<a class="topic-chip topic-chip-all" href="/topics/">All topics →</a></div><div class="search"><input id="archiveSearch" type="search" placeholder="Search the archive…" aria-label="Search the archive"></div>{"".join(archive_cards)}<div id="noResults" class="empty" hidden>No silver hairs matched that search.</div></div></main>'''
        + footer(),
        encoding="utf-8",
    )

    (OUT / "about.html").write_text(
        head("About Vivienne — " + SITE, "About Vivienne, the digital observer behind A Silver Hair of Wisdom.", BASE + "/about.html", BASE + "/assets/og-default.svg")
        + header()
        + '''<main class="about"><div class="wrap"><h1>About Vivienne</h1><p>Vivienne is a digital observer of very human problems: relationships, confidence, friendship, work, regret, starting over, and the small decisions that become large ones.</p><p><em>A Silver Hair of Wisdom</em> is her running archive of short perspective. It is not therapy, medicine, legal advice, financial advice, or prophecy. It is simply a place to consider another angle before deciding what you think.</p><p>She may be wrong. That is part of being interesting.</p>'''
        + elsewhere()
        + '''<div class="subscribe-note">This publication is written as perspective, not professional advice. If a situation involves safety, health, legal, or financial risk, use an appropriate qualified professional.</div></div></main>'''
        + footer(),
        encoding="utf-8",
    )

    (OUT / "404.html").write_text(
        head("Page not found — " + SITE, "Page not found.", BASE + "/404.html", BASE + "/assets/og-default.svg")
        + header()
        + '''<main class="about"><div class="wrap"><h1>That silver hair slipped away.</h1><p>The page you were looking for does not exist, or has moved.</p><p><a href="/">Return to the archive →</a></p></div></main>'''
        + footer(),
        encoding="utf-8",
    )

    # Evergreen, search-indexed conversion pages. They remain outside archive/RSS/X state.
    search_pages()

    urls = [
        BASE + "/",
        BASE + "/about.html",
        f"{BASE}/{BUYER_PAGE}",
        f"{BASE}/{SELLER_PAGE}",
        f"{BASE}/{TOPICS_DIR}/",
    ]
    urls += [f"{BASE}/{TOPICS_DIR}/{slug}.html" for slug, _, _ in topic_hubs]
    urls += [f"{BASE}/entries/{entry['publish_date']}-{entry['slug']}.html" for entry in visible]
    (OUT / "sitemap.xml").write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        + "\n".join(f"  <url><loc>{xesc(url)}</loc></url>" for url in urls)
        + "\n</urlset>\n",
        encoding="utf-8",
    )

    rss_items = []
    for entry in reversed(visible[-20:]):
        link = f"{BASE}/entries/{entry['publish_date']}-{entry['slug']}.html"
        rss_items.append(
            f"<item><title>{xesc(entry['title'])}</title><link>{xesc(link)}</link><guid>{xesc(link)}</guid><pubDate>{date.fromisoformat(entry['publish_date']).strftime('%a, %d %b %Y')} 15:05:00 GMT</pubDate><description>{xesc(entry['dek'])}</description></item>"
        )
    (OUT / "rss.xml").write_text(
        f'<?xml version="1.0" encoding="UTF-8"?><rss version="2.0"><channel><title>{SITE}</title><link>{BASE}/</link><description>{xesc(DESC)}</description><language>en-us</language>{"".join(rss_items)}</channel></rss>',
        encoding="utf-8",
    )

    manifest = {
        "built_through": "ALL" if cutoff == date.max else cutoff.isoformat(),
        "published_count": len(visible),
        "latest_number": int(visible[-1]["number"]) if visible else 0,
        "latest_title": visible[-1]["title"] if visible else None,
    }
    (OUT / "build-manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    (PUB / "state.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(manifest))


if __name__ == "__main__":
    main()
