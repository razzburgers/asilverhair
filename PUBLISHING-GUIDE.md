# A Silver Hair v1.2 — Publishing Engine

## Required GitHub setting
After committing this release: Repository → Settings → Pages → Build and deployment → Source → **GitHub Actions**.

## Schedule
Automatic checks at **10:05 AM America/New_York** every Monday, Wednesday, and Saturday. The builder publishes every due post, so delayed runs still publish the correct content.

#001–#013 are live through Aug 13, 2026. #014–#050 are queued.

## Manual rebuild
Actions → **Publish A Silver Hair** → **Run workflow**. Leave `build_all=false` normally. `build_all=true` intentionally exposes the full queue for testing.

## Images
Each post automatically receives a branded 1600×900 silver editorial SVG cover. To replace it, upload JPG/JPEG/PNG/WEBP/SVG into `publisher/images/`, then set the entry's `image` filename in `publisher/entries.json`. The custom image becomes the article hero, Open Graph/X preview, and BlogPosting image.

## Google
The existing sitemap remains `https://asilverhair.com/sitemap.xml` and is regenerated automatically. No resubmission is needed after each post.

## Long-running reliability

GitHub may disable scheduled workflows in public repositories after 60 days with no repository activity. This release records `publisher/state.json` on scheduled publication runs and commits that state with `GITHUB_TOKEN`, keeping a visible publication history in the repository. GitHub does not start a recursive workflow from pushes made with the repository `GITHUB_TOKEN`.
