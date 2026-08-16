# Vivienne X API — Controlled First Test

This release does **not** turn on autonomous X posting yet.

It adds a manual GitHub Actions workflow named:

**Test Vivienne X Connection**

That workflow uses the four repository secrets already configured:

- `X_CONSUMER_KEY`
- `X_CONSUMER_SECRET`
- `X_ACCESS_TOKEN`
- `X_ACCESS_TOKEN_SECRET`

## Deploy

Upload/merge this package into the existing `asilverhair` repo root.

Important new files:

- `x_post.py`
- `.github/workflows/x-test.yml`

Do not replace/delete your working Silver Hair publishing workflow.

## Run the first test

GitHub → Actions → **Test Vivienne X Connection** → **Run workflow**

The default test text is:

> A small test from Vivienne's publishing desk. If you can read this, the machinery works. — V

You can edit that text before pressing Run workflow.

The workflow first performs a local dry-run, then sends exactly one post through
X's `POST /2/tweets` endpoint.

## Why this is separate

The website publisher is already proven in production. This test keeps X isolated
until authentication and account permissions are confirmed.

After one successful live post, the next release can connect X to the article
publishing pipeline with:

- one post per newly published Silver Hair entry
- duplicate prevention
- prepared Vivienne teaser copy
- article URL
- optional article image/media upload
- separate non-promotional Vivienne post queue

## Security

Never place X credentials in source files. Keep them only in GitHub Actions Secrets.

If a credential is ever exposed publicly, regenerate/revoke it in the X Developer Console.
