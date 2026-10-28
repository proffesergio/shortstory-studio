# Product roadmap · StoryShorts Studio

## User story
As a creator, I want to configure niches and permitted sources; create original, rights-cleared stories; narrate and render them locally; preview; opt in to publishing; and track subsequent performance, so I can operate a channel without manually editing every video.

## Realistic 7-day milestone plan

| Day | Technical deliverable | Creator experiment |
| --- | --- | --- |
| 1 | Repo + local environment + video/channel identity | Select **one** niche and intended audience; define 3 repeatable series |
| 2 | Admin UI, settings, stories, source-rights workflow | Create a backlog of 10 original or permission-granted story ideas |
| 3 | Local Ollama narrative generation + review rubric | Test 3 opening hooks and 2 script lengths |
| 4 | Local TTS, original visuals, captions + audio checks | Produce 3 complete private Shorts for quality review |
| 5 | YouTube OAuth + private/unlisted upload validation | Check mobile legibility, pronunciation, claims and viewing experience |
| 6 | Controlled autopilot and job logs | Release 1–2 original Shorts if quality and rights are cleared |
| 7 | Analytics plan, fixes, GitHub issues and collaboration | Evaluate initial retention and select next 7 days' improvements |

Do not interpret a week as sufficient time to guarantee traffic or to complete API permission, Google OAuth app verification, monetization, billing or secure multi-tenant deployment.

## Expansion: 3 stages

### Stage 1: Reliable single-owner local product (present)
- Next.js / FastAPI / SQLite
- Owned/licensed story library; niche and subreddit allowlist
- Ollama scripts; Kokoro speech; original generated visuals; basic timed captions
- SQLite worker, opt-in owner autopilot, manually authorized uploads
- Error logs, tests and GitHub-ready structure

### Stage 2: Measurable, higher-quality studio
- Captions via forced aligner; motion graphics, transition packs and reusable licensed footage
- Hook variants + controlled A/B testing; review quality scores
- Human-in-the-loop safety and source-rights audit trail
- Postgres, Redis job queue, retries, recovery, scheduling windows and time zone handling
- YouTube Analytics API integration: engagedViews, duration/retention, subscriber conversion
- Moderate publishing, avoid duplicate templated videos

### Stage 3: SaaS commercialization
- Secure multi-tenant auth, roles, organizations and invitation flow
- Per-channel Google OAuth, token encryption, data retention controls and revoke/delete controls
- Isolated queues with quotas, abuse prevention, notifications and billing
- Multi-language TTS and licensed content partners
- Audit logs, privacy policy, YouTube API terms compliance review, appropriate Reddit commercial agreement
- Developer API, webhooks and SDK

## Honest marketing promise
**Do not sell virality.** Sell saved editing time, consistent quality, source traceability, production reproducibility and clear analytics.

## Initial experimentation metrics
Track per Short: title/hook version, intended niche, publishing time, actual duration, engagedViews, views, averageViewDuration, retention curve and rewatch signals (where available), shares, comments, subscribers gained, rendering cost and manual edits. Do not use YouTube's broadened Shorts `views` counter as your only performance signal; track engagedViews as well.

Quality gate: use a human to inspect source rights, factual accuracy and consent, TTS pronunciation, subtitle sync, audio levels, visual cadence, originality, copyright and privacy before enabling unattended uploads.
