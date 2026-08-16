#!/usr/bin/env python3
from pathlib import Path
import argparse, json
from x_post import post

ROOT = Path(__file__).resolve().parent
ENTRIES = ROOT / "publisher" / "entries.json"
MANIFEST = ROOT / "_site" / "build-manifest.json"
STATE = ROOT / "publisher" / "x-state.json"
BASE = "https://asilverhair.com"
BASELINE_NUMBER = 14

def load_json(path, default):
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else default

def article_url(e):
    return f"{BASE}/entries/{e['publish_date']}-{e['slug']}.html"

def trim_for_x(prefix, url):
    limit = 275 - len(url)
    prefix = prefix.strip()
    if len(prefix) > limit:
        prefix = prefix[:max(0, limit - 1)].rstrip(" ,;:-") + "…"
    return f"{prefix}\n{url}"

def make_text(e):
    url = article_url(e)
    custom = str(e.get("x_text", "")).strip()
    if custom:
        return custom.replace("{url}", url)
    title, dek, n = e["title"].strip(), e["dek"].strip(), int(e["number"])
    mode = n % 4
    if mode == 0:
        prefix = f"{title}\n\n{dek}"
    elif mode == 1:
        prefix = f"{dek}\n\nNew from A Silver Hair: {title}"
    elif mode == 2:
        prefix = f"New from A Silver Hair:\n\n{title}\n\n{dek}"
    else:
        prefix = f"{title}\n\n{dek}\n\n— Vivienne"
    return trim_for_x(prefix, url)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    manifest = load_json(MANIFEST, {})
    if manifest.get("built_through") == "ALL":
        print("Full-queue test build detected; refusing to auto-post to X.")
        return 0

    latest = int(manifest.get("latest_number") or 0)
    if latest <= 0:
        print("No built article found; skipping.")
        return 0

    state = load_json(STATE, {"last_posted_number": BASELINE_NUMBER})
    last_posted = int(state.get("last_posted_number") or BASELINE_NUMBER)
    if latest <= last_posted:
        print(f"No new X article post needed (built #{latest}, X state #{last_posted}).")
        return 0

    entries = load_json(ENTRIES, [])
    match = next((e for e in entries if int(e["number"]) == latest), None)
    if not match:
        raise RuntimeError(f"Could not find article #{latest} in publisher/entries.json")
    if match.get("x_enabled", True) is False:
        print(f"Article #{latest} has x_enabled=false; skipping.")
        return 0

    text = make_text(match)
    if len(text) > 280:
        raise RuntimeError(f"Prepared X text is unexpectedly {len(text)} characters.")

    print(f"Prepared article #{latest}:")
    print(text)

    if args.dry_run:
        print("DRY RUN: no X request sent and no state changed.")
        return 0

    payload = post(text, made_with_ai=False)
    tweet_id = str((payload or {}).get("data", {}).get("id", "")).strip()
    if not tweet_id:
        raise RuntimeError("X returned success without a Post ID; state not advanced.")

    STATE.write_text(json.dumps({
        "last_posted_number": latest,
        "last_posted_title": match["title"],
        "last_posted_url": article_url(match),
        "last_x_post_id": tweet_id,
    }, indent=2) + "\n", encoding="utf-8")
    print(f"Recorded X state for article #{latest}, Post ID {tweet_id}.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
