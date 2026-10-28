# StoryShorts Studio · v0.1 (local-first starter)

An opinionated, GitHub-ready **single-owner MVP** for turning licensed or original stories into narrated, captioned YouTube Shorts with local AI. Contains a real Next.js admin UI, FastAPI backend, SQLite job queue, Ollama storywriter, Kokoro/Piper-alternative TTS integration (Kokoro implemented), FFmpeg renderer, optional permission-gated Reddit preview, and YouTube OAuth uploader.

> **Status: development starter, not production SaaS.** Functional modules require local model downloads, FFmpeg, Google OAuth credentials, and legal rights to inputs. This has NOT been tested against live Reddit or YouTube API credentials. Do not expose port 8000/3000 publicly: there is no authentication yet. Autopilot defaults OFF and requires explicit upload authorization to enable auto-publishing.

## Features

- Admin dashboard: stories, rights declaration, manual generation, preview, publish, status and errors.
- Admin-configured niches + subreddit allowlist, with **Reddit preview disabled until appropriate API/commercial authorization**.
- Content generation through a **local Ollama model**. Adds original commentary and content precautions; review its output.
- Local TTS via **Kokoro**, synthesized sentence-by-sentence; captions are estimated per 6 words, not forced-aligned.
- Original generative gradients with gentle camera movement, no third-party gameplay or stock-licensing dependence.
- H.264 1080×1920 MP4 with voiceover and subtitles rendered locally.
- Sequential SQLite-backed worker; failed jobs show errors in UI. Optional daily-capped autopilot processes only approved-source stories.
- Authorized YouTube uploading via OAuth. Explicit approval required per upload; default privacy is **private**.
- No artificial engagement, evasion, rate-limit circumvention or copyright workarounds.

## Architecture

```
frontend/ (Next.js, browser UI)
      │ HTTP
      ▼
backend/app/main.py (FastAPI) ──► SQLite stories/settings/jobs
                                       │
backend/app/worker.py (one local worker) ◄┘
      ├── Ollama HTTP → original script
      ├── Kokoro TTS → narration.wav
      ├── Pillow + FFmpeg → animated 9:16 MP4
      └── Google OAuth → YouTube videos.insert (optional upload)
```

## Quickstart on Windows, macOS or Linux

Requires **Python 3.11 or 3.12**, Node.js 22, FFmpeg (with libass/libx264), [Ollama](https://ollama.com/), plus `espeak-ng` for Kokoro's phonemization. 16GB RAM recommended for the local model workflow; GPU optional. Use recent FFmpeg. Suggested model: `llama3.2` (or edit `OLLAMA_MODEL`).

1. Clone/unzip repo, copy `.env.example` to `.env`. The backend loads this file via python-dotenv; you can also override variables in your shell. **Defaults work without `.env`** for the initial manual workflow.
2. Start the local LLM:

   ```bash
   ollama pull llama3.2
   ollama serve
   ```

3. From repository root, create the Python environment and install libraries:

   ```bash
   python -m venv .venv
   # Linux/macOS: source .venv/bin/activate
   # Windows PowerShell: .venv\Scripts\Activate.ps1
   pip install -r backend/requirements.txt
   ```

4. In terminal A (from repository root):

   ```bash
   uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000
   ```

5. In terminal B (from repository root):

   ```bash
   PYTHONPATH=backend python -m app.worker
   # On Windows PowerShell: $env:PYTHONPATH='backend'; python -m app.worker
   ```

6. In terminal C:

   ```bash
   cd frontend
   npm install
   npm run dev
   ```

7. Open <http://localhost:3000>. Add an **original or explicitly licensed** story (at least 50 characters), check rights confirmation, click **Render video**, and watch the job. The first Kokoro run may download weights. A CPU render might take minutes.

8. For a quick *audio pipeline smoke test without Kokoro*, install `espeak-ng` and set `TTS_ENGINE=espeak` in the worker terminal. This is robotic but fully local. Example: `TTS_ENGINE=espeak PYTHONPATH=backend python -m app.worker` (Linux/macOS). Switch to Kokoro for publication.

## YouTube upload integration

1. In [Google Cloud Console](https://console.cloud.google.com/) create a project and enable **YouTube Data API v3**.
2. Configure an OAuth consent screen and create an **OAuth desktop application** for this local MVP.
3. Download its client JSON to `secrets/client_secret.json` (never commit it).
4. Install backend requirements and from repository root run:

   ```bash
   python scripts/youtube_auth.py
   ```

   The program opens the system browser to connect **your own channel**, requesting only the `youtube.upload` scope and storing refresh tokens in `secrets/youtube_token.json` (gitignored). Follow Google's testing/verification requirements. If using a testing-mode OAuth consent screen, refresh tokens may expire quickly.

5. Once a render has completed, click **Upload**, choose visibility and explicitly consent. Default **private**. The worker uploads using resumable `videos.insert`; if the API refuses public upload due to app review or permission restrictions, comply with Google's process—do not work around it.

### Reddit discovery (optional and disabled)

Reddit requires API approval for many uses and **separate approval/contracts for commercial purposes**. Obtain the permissions that apply to your use, then set `REDDIT_AUTHORIZED=true`, OAuth application credentials and a distinct `REDDIT_USER_AGENT`. The dashboard previews **candidate metadata and short excerpts**, not a license to republish. You still need appropriate rights to each story. Do not automatically publish unlicensed content. Respect author deletion requests and Reddit API terms. Do not scrape around access limits.

## Defaults and security

- Bind FastAPI only to `127.0.0.1`. No authentication, per-user access controls, encryption at rest, or hosted SaaS infrastructure yet.
- `data/`, `outputs/`, and `secrets/` are ignored by Git. Never commit API keys, Google OAuth tokens, story data or private videos.
- Only one worker is supported by this minimal SQLite queue. A process crash can leave a job in `running`; manually mark failed in local DB during development. For production: Postgres + Redis/Celery, leases, retries and idempotency.
- Input rights confirmation is a user declaration, **not** automated rights verification. AI output and music/visuals need your review.
- The `status.containsSyntheticMedia` field defaults false because current pipeline generates abstract graphics and a synthetic narration, not fabricated realistic real-world footage. Update disclosure logic when adding photorealistic AI scenes, realistic impersonations or AI music.
- The uploader assumes a single local channel; do **not** distribute that credential to other users. A SaaS needs per-user OAuth and secure token storage.
- Source selection scores rank user-permitted candidates; they do not predict YouTube distribution.

## Next development milestones

1. **Production security:** NextAuth/Clerk or equivalent, RBAC, HTTPS, CSRF, rate limiting, encrypted per-user OAuth tokens, background jobs.
2. **Rights workflows:** documented consent, licensed-source agreements, audit and delete requests, author attribution.
3. **Visual templates:** licensed user media, beat-synced transitions, forced-aligned word captions, thumbnail variants, branded compositions.
4. **Autopilot opt-in:** scheduling, per-channel posting limits, quotas and express authorization with visible controls and easy pause.
5. **Analytics:** per-channel Shorts `engagedViews`, average view duration, viewer retention, production cost, A/B testing based on actual creator metrics.
6. **Commercial platform:** Postgres tenant IDs, worker isolation, usage/billing, audit logs, licensing and Terms/Privacy.

## Test

```bash
PYTHONPATH=backend pytest backend/tests -q
cd frontend && npm run build
```

## Commercial/legal note

The **software's source** can be licensed independently from Reddit content, stock footage, model weights, and YouTube API access. Verify each dependency and external source license before distribution. This skeleton does not declare an open-source license intentionally: choose a suitable permissive/copyleft/commercial license after deciding your business model. No guaranteed algorithm growth, monetization, or API permissions.

## Optional autopilot (local single-owner only)

Open **Niche settings → Approved-source autopilot**. Turn on automatic rendering, choose a limit of 1–3 renders per UTC day, and save. The worker picks **only rights-confirmed creator-supplied stories** that have never been rendered. To enable publishing, connect YouTube OAuth first, check the express ongoing upload consent, choose `private`, `unlisted`, or `public`, then save. The consent is stored locally; switching off auto-upload or autopilot prevents *queued automatic* uploads from executing. **Manual queued uploads remain individually authorized.** A crash can strand a job because this is only an MVP queue.

This is not an unrestricted Reddit story autopublisher: Reddit requires the relevant data and commercial permissions; using a Reddit post as inspiration does not transfer the underlying story's publication rights.
