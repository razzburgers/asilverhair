#!/usr/bin/env python3
import argparse, base64, hashlib, hmac, json, os, secrets, time, urllib.parse, urllib.request, urllib.error

CREATE_POST_URL = "https://api.x.com/2/tweets"

def pct(value):
    return urllib.parse.quote(str(value), safe="~-._")

def oauth_header(method, url, consumer_key, consumer_secret, access_token, access_token_secret):
    params = {
        "oauth_consumer_key": consumer_key,
        "oauth_nonce": secrets.token_hex(16),
        "oauth_signature_method": "HMAC-SHA1",
        "oauth_timestamp": str(int(time.time())),
        "oauth_token": access_token,
        "oauth_version": "1.0",
    }
    parsed = urllib.parse.urlsplit(url)
    base_url = urllib.parse.urlunsplit((parsed.scheme, parsed.netloc, parsed.path, "", ""))
    pairs = list(params.items()) + urllib.parse.parse_qsl(parsed.query, keep_blank_values=True)
    pairs.sort(key=lambda kv: (pct(kv[0]), pct(kv[1])))
    normalized = "&".join(f"{pct(k)}={pct(v)}" for k, v in pairs)
    signature_base = "&".join([method.upper(), pct(base_url), pct(normalized)])
    signing_key = f"{pct(consumer_secret)}&{pct(access_token_secret)}"
    digest = hmac.new(signing_key.encode(), signature_base.encode(), hashlib.sha1).digest()
    params["oauth_signature"] = base64.b64encode(digest).decode()
    return "OAuth " + ", ".join(f'{pct(k)}="{pct(v)}"' for k, v in sorted(params.items()))

def require_secret(name):
    value = os.getenv(name, "").strip()
    if not value:
        raise RuntimeError(f"Missing required secret: {name}")
    return value

def post(text, dry_run=False, made_with_ai=False):
    text = text.strip()
    if not text:
        raise ValueError("Post text is empty.")
    if len(text) > 280:
        raise ValueError(f"Post is {len(text)} characters; keep it <= 280.")

    body_obj = {"text": text}
    # X currently documents this flag for AI-generated media. It is opt-in here.
    if made_with_ai:
        body_obj["made_with_ai"] = True

    if dry_run:
        print(json.dumps({"dry_run": True, "text": text, "characters": len(text),
                          "made_with_ai": made_with_ai}, indent=2))
        return None

    ck = require_secret("X_CONSUMER_KEY")
    cs = require_secret("X_CONSUMER_SECRET")
    at = require_secret("X_ACCESS_TOKEN")
    ats = require_secret("X_ACCESS_TOKEN_SECRET")

    req = urllib.request.Request(
        CREATE_POST_URL,
        data=json.dumps(body_obj).encode(),
        method="POST",
        headers={
            "Authorization": oauth_header("POST", CREATE_POST_URL, ck, cs, at, ats),
            "Content-Type": "application/json",
            "User-Agent": "ASilverHair-ViviennePublisher/1.3",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            payload = json.loads(resp.read().decode())
            print(json.dumps(payload))
            return payload
    except urllib.error.HTTPError as exc:
        error_body = exc.read().decode("utf-8", errors="replace")
        print(f"X API HTTP {exc.code}: {error_body}")
        raise

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--text", required=True)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--made-with-ai", action="store_true")
    args = ap.parse_args()
    post(args.text, args.dry_run, args.made_with_ai)

if __name__ == "__main__":
    main()
