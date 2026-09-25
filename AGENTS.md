# Ring Mint agent handoff instructions

## Publishing handoff — human commits and pushes

- When Chloe says “publish,” complete the authorized local preparation and relevant checks, then report **ready for your commit and push**. The human handles Git commits, pushes and the resulting deployment.
- Do not stage, commit, push, open a deployment PR, or attempt an alternative deployment unless Chloe explicitly requests that Git/deployment action. Do not check GitHub credentials, retry pushes, poll for the human's commit, or ask for permission to push as part of an ordinary publishing request.
- Summarize what is ready, checks completed and any remaining blockers, then stop and wait for the human. Record new content as `ready`, not `published`, until deployment and live verification are confirmed. Existing live articles retain their published state; pending local updates are not yet live.
- This standing preference supersedes older publishing workflow language in this repository. A later explicit request to commit or push may override it for that action.

## Content work

- Read `content/CONTENT_PLAN.md` before planning, drafting, scheduling or publishing content. It is the single active editorial plan and post-status tracker. Start with “Resume here — active work and publication tracking,” then inspect the selected inventory entries and related files.
- Preserve all existing backlog items, drafts, assets, published URLs and customer stories. Extend or improve the plan; never replace the strategy or remove work without user direction.
- For “next N blog posts,” resume unfinished batches first; otherwise select the earliest unfinished `/blog/` entries in the dated calendar. Reference guides are separate unless requested. Rebase overdue target dates into the future; never backdate publication.
- Record a batch and ownership before starting. After each meaningful step update the entry's editorial status, website publication state, artifacts, blockers and next action. End with an explicit handoff and authorization scope in the same file. Read prior handoff evidence before retrying any external write.
- Target dates are not scheduling confirmations. Website and social schedules are independent. The current static publishing script is immediate publication, not a future scheduler. Never report scheduled without external queue/job confirmation; never report a newly published website post without checking its live URL/content.
- Follow authorization already supplied by the user; do not request it again unnecessarily. A content plan alone is not authorization to publish every listed article. Never invent customer evidence, first-hand experience, tests, quotes, sourcing capabilities or price claims to fill a slot.
- Use `BLOG_PUBLISHING_GUIDE.md` for production checks. The old `content/calendar.csv`, `content/PROGRESS.md` and September 7 brief are preserved historical inputs, not active queues. The old calendar-report tool reads the legacy CSV and is not authoritative.
- Preserve others' uncommitted changes. Keep credentials and private customer details out of tracking files.

## Scope of these instructions

These instructions support continuity for agents working in this repository. Agents without access to this checkout must be given the current `content/CONTENT_PLAN.md` and relevant drafts. Local updates must be synced through the normal authorized repository workflow before another checkout can see them.
