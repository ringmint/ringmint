# SEO content plan — progress tracker

Last updated: 2026-09-07. Update the counts here whenever a batch ships.

## Overall: ~28% complete

Weighted by effort, not by post count (220 posts is the long tail; the
foundation and the first batches are what actually move leads).

| Phase | Weight | Done | Contribution |
|---|---|---|---|
| 0. Foundation — template, tools, lint, calendar, publish pipeline | 15% | 100% | 15.0% |
| 1. Batch 1 — 9 posts written and wired | 15% | 85% (drafted, `noindex`, awaiting sign-off) | 12.8% |
| 2. Batch 2 — 6 posts | 15% | 0% | 0% |
| 3. Remaining backlog — 203 posts | 40% | 1% | 0.4% |
| 4. Off-page — backlinks, Trustpilot, GA4 hygiene, Apps Script redeploy | 15% | 0% | 0% |
| **Total** | **100%** | | **~28%** |

Raw post count: **11 of 220 written (5%)**, 2 of those live and indexed (0.9%).

## Calendar state

- published: 2
- drafted (noindex, blocked on bench sign-off): 9
- backlog: 209

Regenerate with:

```bash
python3 -c "import csv,collections;print(collections.Counter(r['status'] for r in csv.DictReader(open('content/calendar.csv'))))"
```

## Blocked on Chloe

1. **Bench claims sign-off** — `content/BRIEF-2026-09-07.md` section 1. Blocks all 9 batch-1 posts.
2. **Two backlinks** — teamanjewelry.com and chloealpert.com. Site has zero external links.
3. **GA4 internal traffic filter** — Bellefonte / Park Forest Village PA.
4. **Apps Script redeploy** — `apps-script/Code.gs` changed.
5. **Trustpilot reviews** — six is thin.

## Recurring tasks

| Cadence | Task |
|---|---|
| Weekly | Batch Q&A: one list of bench questions for the posts in flight |
| Weekly | Draft + lint the next 2–3 posts, ship as `noindex` drafts |
| Weekly | `python3 tools/blog-check.py SLUG` on everything touched |
| On publish | `./tools/publish-drafts.sh`, commit, push, then `./scripts/indexnow.sh` |
| Monthly | Retail price tracker refresh (the tracker post is a living page) |
| Monthly | `python3 tools/calendar-report.py` — pull GSC clicks into the calendar, re-prioritise |
| Quarterly | Refresh pass on posts past `refresh_due`; guide section 8 |
| Quarterly | Re-check competitor posts named in comparison pieces for stale claims |
