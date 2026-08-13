# Instagram feed: one-time setup

The homepage Instagram section is filled by a scheduled GitHub Action
(`.github/workflows/instagram-sync.yml`). Every 6 hours it pulls your latest
posts, optimises the photos, and commits them to the repo, so the site stays
plain static HTML with no third-party script.

**Until the steps below are done, the section shows placeholder photos.**

Meta shut down the old Instagram Basic Display API on 4 December 2024. The
replacement requires a Business or Creator account and an access token. There
is no supported way to read a personal account.

---

## 1. Switch the Instagram account to Business or Creator

In the Instagram app: **Settings → Account type and tools → Switch to
professional account**. Free, reversible, and takes about a minute. Creator is
the usual choice for a brand like this.

## 2. Create a Meta app and get a token

1. Go to <https://developers.facebook.com/apps> and **Create app**.
2. When asked for the app type, choose **Business**. (Other types cannot use
   this API.)
3. Add the **Instagram** product to the app.
4. In the left menu open **Instagram → API setup with Instagram business
   login**.
5. In the section for generating access tokens, connect the `theringmint`
   account, then click **Generate token** beside it and authenticate.
6. Copy the token.

Tokens generated here in the App Dashboard are **long-lived, valid 60 days**.
(Tokens from the Business Login *flow* are short-lived, one hour. Use the
dashboard, not the login flow.) The workflow refreshes the token on each run,
so it keeps working past 60 days as long as `GH_PAT` is set. See step 3.

The token carries the `instagram_business_basic` scope. That is read-only:
it can list your media and nothing else.

Meta moves this UI around. Current reference:
<https://developers.facebook.com/docs/instagram-platform/instagram-api-with-instagram-login/get-started>

**Never commit the token or paste it anywhere public. It goes only into
GitHub Secrets.**

## 3. Add the repo secrets

In GitHub: **Settings → Secrets and variables → Actions → New repository secret**.

| Secret | Required | What it is |
|---|---|---|
| `IG_ACCESS_TOKEN` | yes | The long-lived token from step 2 |
| `GH_PAT` | recommended | A fine-grained personal access token, scoped to this repo only, with **Secrets: read and write** |

`GH_PAT` exists so the workflow can write the refreshed Instagram token back
into `IG_ACCESS_TOKEN` every run. Without it everything still works, but the
token expires after 60 days and you would have to paste a new one in by hand.

Create the PAT at **Settings → Developer settings → Personal access tokens →
Fine-grained tokens**, scoped to `ringmint` only.

## 4. Run it once

**Actions → Sync Instagram feed → Run workflow.** It should finish in under a
minute and commit something like `Update Instagram feed`. Reload the site and
your real photos will be in the grid.

---

## How it behaves

- **Cadence:** every 6 hours, plus any manual run. Change the `cron` line in the
  workflow if you want it more or less often.
- **Count:** 6 tiles. Change `IG_POST_COUNT` in the workflow.
- **Photos:** centre-cropped to square, 700×700, written as AVIF + JPEG into
  `assets/instagram/`. Tiles that drop out of the feed are deleted.
- **Videos and carousels:** the cover frame / first image is used.
- **Alt text:** derived from the caption, with hashtags, @mentions, and emoji
  stripped. Falls back to a generic description if a post has no caption.
- **If a run fails,** the site is untouched; it keeps serving the last
  successful set of photos. It will never render an empty grid.

## Local test

```bash
pip install Pillow pillow-avif-plugin
IG_ACCESS_TOKEN=your_token python3 scripts/sync_instagram.py
```

## Troubleshooting

- **"the API returned no media"**: the account is still personal rather than
  Business/Creator, or the wrong account was connected in step 2.
- **"Invalid OAuth access token"**: the token was truncated when copied, or it
  came from the Business Login flow (1 hour) rather than the App Dashboard
  (60 days). Regenerate from the dashboard.
- **Token expired**: if `GH_PAT` is not set, tokens die after 60 days. Add the
  PAT, or generate a fresh token and update `IG_ACCESS_TOKEN`.
- **Workflow cannot push**: confirm **Settings → Actions → General → Workflow
  permissions** is set to *Read and write permissions*.
