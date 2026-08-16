#!/usr/bin/env python3
"""
Minimal X API OAuth 1.0a poster for A Silver Hair / Vivienne.

Required environment variables:
  X_CONSUMER_KEY
  X_CONSUMER_SECRET
  X_ACCESS_TOKEN
  X_ACCESS_TOKEN_SECRET
"""

import argparse
import base64
import hashlib
import hmac
import json
import os
import secrets
import time
import urllib.parse
import urllib.request
import urllib.error

CREATE_POST_URL = "https://api.x.com/2/tweets"


def pct(value: str) -> str:
    return urllib.parse.quote(str(value), safe="~-._")


def oauth_header(method: str, url: str, consumer_key: str, consumer_secret: str,
                 access_token: str, access_token_secret: str) -> str:
    params = {
        "oauth_consumer_key": consumer_key,
        "oauth_nonce": secrets.token_hex(16),
        "oauth_signature_method": "HMAC-SHA1",
        "oauth_timestamp": str(int(time.time())),
        "oauth_token": access_token,
        "oauth_version": "1.0",
    }

    # No URL query parameters are currently used, but include them correctly if added.
    parsed = urllib.parse.urlsplit(url)
    base_url = urllib.parse.urlunsplit((parsed.scheme, parsed.netloc, parsed.path, "", ""))
    query_params = urllib.parse.parse_qsl(parsed.query, keep_blank_values=True)
    signature_params = list(params.items()) + query_params
    signature_params.sort(key=lambda kv: (pct(kv[0]), pct(kv[1])))

    normalized = "&".join(f"{pct(k)}={pct(v)}" for k, v in signature_params)
    signature_base = "&".join([method.upper(), pct(base_url), pct(normalized)])
    signing_key = f"{pct(consumer_secret)}&{pct(access_token_secret)}"

    digest = hmac.new(
        signing_key.encode("utf-8"),
        signature_base.encode("utf-8"),
        hashlib.sha1,
    ).digest()
    params["oauth_signature"] = base64.b64encode(digest).decode("ascii")

    return "OAuth " + ", ".join(
        f'{pct(k)}="{pct(v)}"' for k, v in sorted(params.items())
    )


def require_secret(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise RuntimeError(f"Missing required secret: {name}")
    return value


def post(text: str, dry_run: bool = False):
    text = text.strip()
    if not text:
        raise ValueError("Post text is empty.")
    if len(text) > 280:
        raise ValueError(f"Post is {len(text)} characters; keep the first test <= 280.")

    if dry_run:
        print(json.dumps({"dry_run": True, "text": text, "characters": len(text)}, indent=2))
        return

    consumer_key = require_secret("X_CONSUMER_KEY")
    consumer_secret = require_secret("X_CONSUMER_SECRET")
    access_token = require_secret("X_ACCESS_TOKEN")
    access_token_secret = require_secret("X_ACCESS_TOKEN_SECRET")

    body = json.dumps({
        "text": text,
        "made_with_ai": True
    }).encode("utf-8")

    req = urllib.request.Request(
        CREATE_POST_URL,
        data=body,
        method="POST",
        headers={
            "Authorization": oauth_header(
                "POST", CREATE_POST_URL,
                consumer_key, consumer_secret,
                access_token, access_token_secret
            ),
            "Content-Type": "application/json",
            "User-Agent": "ASilverHair-ViviennePublisher/1.0",
        },
    )

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            payload = resp.read().decode("utf-8")
            print(payload)
    except urllib.error.HTTPError as exc:
        error_body = exc.read().decode("utf-8", errors="replace")
        print(f"X API HTTP {exc.code}: {error_body}")
        raise


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--text", required=True)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    post(args.text, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
