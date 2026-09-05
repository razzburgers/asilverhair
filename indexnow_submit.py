#!/usr/bin/env python3
"""Notify IndexNow after A Silver Hair has successfully deployed.

No secret is required: the IndexNow key is intentionally published on the same host.
Use --all after structural/content pushes and --latest after normal scheduled publishing.
"""
from pathlib import Path
import argparse
import json
import re
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "_site"
PUB = ROOT / "publisher"
BASE = "https://asilverhair.com"
HOST = "asilverhair.com"
ENDPOINT = "https://api.indexnow.org/indexnow"
KEY_FILE = ROOT / "indexnow-key.txt"
TOPICS_DIR = "topics"


def safe_topic(topic):
    slug = re.sub(r"[^a-z0-9-]+", "-", str(topic or "wisdom").strip().lower()).strip("-")
    return slug or "wisdom"


def load_key():
    key = KEY_FILE.read_text(encoding="utf-8").strip()
    if not re.fullmatch(r"[A-Za-z0-9-]{8,128}", key):
        raise RuntimeError("Invalid IndexNow key in indexnow-key.txt")
    return key


def sitemap_urls():
    tree = ET.parse(OUT / "sitemap.xml")
    ns = {"s": "http://www.sitemaps.org/schemas/sitemap/0.9"}
    urls = []
    for loc in tree.findall("s:url/s:loc", ns):
        if loc.text:
            urls.append(loc.text.strip())
    return urls


def latest_urls():
    manifest = json.loads((OUT / "build-manifest.json").read_text(encoding="utf-8"))
    latest_number = int(manifest.get("latest_number") or 0)
    entries = json.loads((PUB / "entries.json").read_text(encoding="utf-8"))
    entry = next((e for e in entries if int(e["number"]) == latest_number), None)
    if not entry:
        return [BASE + "/", BASE + "/topics/"]
    topic = safe_topic(entry.get("topic"))
    return [
        BASE + "/",
        BASE + "/topics/",
        f"{BASE}/topics/{topic}.html",
        f"{BASE}/entries/{entry['publish_date']}-{entry['slug']}.html",
    ]


def submit(urls):
    urls = list(dict.fromkeys(urls))
    if not urls:
        print("No URLs to submit.")
        return 0
    if len(urls) > 10000:
        raise RuntimeError("IndexNow supports at most 10,000 URLs per request")

    key = load_key()
    payload = {
        "host": HOST,
        "key": key,
        "keyLocation": f"{BASE}/{key}.txt",
        "urlList": urls,
    }
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        ENDPOINT,
        data=data,
        method="POST",
        headers={"Content-Type": "application/json; charset=utf-8", "User-Agent": "A-Silver-Hair-IndexNow/1.0"},
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            code = response.getcode()
            body = response.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as exc:
        code = exc.code
        body = exc.read().decode("utf-8", errors="replace")
    except urllib.error.URLError as exc:
        print(f"IndexNow network error: {exc}")
        return 1

    print(f"IndexNow HTTP {code}: submitted {len(urls)} URL(s)")
    if body.strip():
        print(body.strip()[:1000])
    # 202 can occur while a new key is being verified.
    return 0 if code in (200, 202) else 1


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true", help="Print the URLs without making a network request")
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--all", action="store_true", help="Submit every URL in the generated sitemap")
    mode.add_argument("--latest", action="store_true", help="Submit homepage, topic index, latest topic hub and latest article")
    args = parser.parse_args()
    urls = sitemap_urls() if args.all else latest_urls()
    if args.dry_run:
        print(f"DRY RUN: {len(urls)} URL(s)")
        for url in urls:
            print(url)
        return 0
    return submit(urls)


if __name__ == "__main__":
    raise SystemExit(main())
