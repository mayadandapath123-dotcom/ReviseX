# Running ReviseX locally and putting it on the internet

Two parts: **A)** run it on your own PC, **B)** publish it.

Read the caveats in [§4](#4-read-this-before-you-make-it-public) before publishing —
this app was designed local-first and a public URL changes its security model.

---

## 1. Run it on your PC

### Prerequisites

| Tool | Version | Check with |
|---|---|---|
| Python | 3.11+ | `python --version` (Windows may need `py -3`) |
| Node.js | 18+ | `node --version` |

Nothing else. No database server, no Docker, no accounts, no API keys, no internet
after the initial dependency install.

### One command

```bash
git clone <your-repo-url>
cd revise
python scripts/dev.py
```

That creates `backend/.venv`, installs Python + Node dependencies, runs migrations,
seeds the question bank, and starts:

- **Web app** → http://localhost:5173
- **API** → http://localhost:8000 (docs at http://localhost:8000/docs)

First run takes ~1–2 minutes. Later runs take ~3 seconds.

<details>
<summary><b>Windows notes</b></summary>

```powershell
py scripts\dev.py
```

If script execution is blocked:
`Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`

`npm` on Windows is really `npm.cmd`, which `subprocess` cannot launch by bare
name. `scripts/dev.py` resolves it through `shutil.which` and runs it via
`cmd.exe /c`, and kills the whole `npm -> node -> vite` tree with
`taskkill /T` on exit so port 5173 is not left occupied.
</details>

### Other commands

| Command | Effect |
|---|---|
| `python scripts/dev.py` | Both halves |
| `python scripts/dev.py --reset` | Delete local DB, reseed, run |
| `python scripts/dev.py --backend` / `--frontend` | One half only |
| `cd backend && python run.py` | API only (auto-migrates + seeds) |
| `cd frontend && npm run dev` | UI only (proxies `/api` to :8000) |
| `cd backend && python -m pytest -q` | 33 engine/scoring tests |
| `cd frontend && npm run build` | Production bundle → `frontend/dist` |

### Where your data lives

`backend/data/revise.sqlite3` — one file. Progress, mistakes, XP, personal bests.
Delete it to start over; the 1,304-question bank regenerates from
`backend/content/*.json` on next boot. **Back up this file to back up progress.**

### Production-style local run (one port, like the deployed version)

```bash
cd frontend && npm run build          # emits frontend/dist
cd ../backend && python run.py        # now serves UI + API on :8000
```

Open http://localhost:8000. FastAPI detects `frontend/dist` and serves the SPA
with a client-routing fallback, so `/api` needs no proxy and no CORS. This is
exactly what the Docker image does.

---

## 2. Publish it — Option A: Render, one service (recommended)

The API serves the built frontend, so you deploy **one** thing and skip CORS,
split builds and frontend env vars entirely.

### Steps

1. Push this repo to GitHub/GitLab/Bitbucket.
2. Render → **New +** → **Blueprint** → pick the repo.
3. Render reads `render.yaml` and creates a `revisex` Docker web service.
4. Wait for the build (~3–5 min: Node build stage, then Python stage).
5. Open `https://revisex.onrender.com`. Done.

### Or without the Blueprint (manual)

Render → **New +** → **Web Service** →
- Runtime: **Docker**
- Dockerfile path: `./Dockerfile`
- Health check path: `/api/health`
- Env: `APP_ENV=production`, `DATA_DIR=/data`, `AUTO_APPROVE_AI_ITEMS=false`

### Local Docker test (optional but worth it)

```bash
docker build -t revisex .
docker run --rm -p 8000:8000 -v revisex-data:/data revisex
```

> The Dockerfile was **not** build-tested in the sandbox that produced it (no
> Docker available there). The two stages are standard and the runtime path was
> verified directly: a blank `DATA_DIR` boots, applies migrations, seeds 1,304
> questions and serves the SPA. If the image build fails, it will almost
> certainly be a Node/Python base-image tag issue, not an app issue.

---

## 3. Publish it — Option B: Netlify (frontend) + Render (backend)

**Netlify alone cannot host this app.** Netlify serves static files and short-lived
serverless functions; this backend is a long-lived FastAPI process holding an open
SQLite connection. Porting it to functions would mean rewriting the API layer and
still leaves you with no persistent SQLite.

So: Netlify for the UI, Render for the API.

### Backend on Render

Same as Option A, but you may skip serving static files. Set **CORS_ORIGINS** to
your Netlify URL:

```
CORS_ORIGINS=https://revisex.netlify.app
```

### Frontend on Netlify

1. Push the repo, then Netlify → **Add new site** → **Import from Git**.
2. Netlify auto-detects `frontend/netlify.toml` (base `frontend`, build
   `npm run build`, publish `dist`, SPA redirect already configured).
3. **Site configuration → Environment variables**, add:

   ```
   VITE_API_URL = https://<your-render-service>.onrender.com/api
   ```

4. **Deploy.**

### The gotcha that breaks most split deploys

`VITE_API_URL` is **inlined at build time** — it is baked into the JS bundle, not
read at runtime. So:

- Setting it *after* a build does nothing. Change it → **trigger a redeploy**.
- It must be the full origin **plus `/api`** (e.g. `.../api`), because the client
  appends paths like `/quiz/sessions`.
- It must be `https://` if your site is `https://`, or the browser blocks it as
  mixed content.
- If the backend is asleep (Render free tier cold start ≈ 50 s), the first API
  call will appear to hang. That is the free tier, not a bug.

Default with no `VITE_API_URL` is `/api`, which is why Option A needs none of this.

---

## 4. Read this before you make it public

This MVP is deliberately local-first. Three things are **not** ready for a public,
multi-stranger audience:

### 4.1 There is no authentication — profiles are guessable

Identity is a client-chosen `X-Profile-Id` header with no credentials behind it.
On a public URL, anyone can enumerate profile IDs and read or overwrite anyone
else's progress, mistakes and scores. The leaderboard also becomes global across
strangers, whereas locally it is "profiles on this device".

Fine for: your own PC, a classroom on one machine, a demo link you share with a
few people who trust each other.

Not fine for: a public launch. Real auth is Phase 8 (`online_account_id` /
`online_username` columns already exist, unused).

**Cheap mitigations available today**, in order of effort:
1. Keep the URL unlisted and treat it as a private demo.
2. Put Render's built-in **Basic Auth / password protection** (paid plans) in
   front of the service.
3. Add a shared `ACCESS_TOKEN` env check in a FastAPI dependency (~20 lines) so
   only people with the token can call `/api`. Stops casual strangers, not a
   determined one.

Say the word and I'll implement #3.

### 4.2 Free-tier disk is ephemeral — progress resets

Render's free plan wipes the filesystem on every deploy and restart. The question
bank **survives** (it reseeds from JSON on boot, verified). Student **progress does
not**.

- Demo you re-seed anyway → free tier is fine.
- Real students keeping history → attach a persistent disk (Render paid, ~$7/mo).
  `render.yaml` already declares `disk: mountPath: /data`; **delete that block to
  deploy on the free plan**, since free plans reject disks.
- Netlify has no server-side storage at all, so Option B still needs Render (or
  similar) to hold the DB.

### 4.3 SQLite and concurrency

WAL mode handles a classroom comfortably, and Render runs a single instance, so
there is no multi-process write contention. It is **not** built for hundreds of
simultaneous users. If that becomes the goal, swap `app/db/connection.py` for
Postgres and keep everything else — the SQL is standard and there is no ORM in the
way. Do **not** scale out to multiple instances while still on SQLite; they would
each keep their own divergent database.

### Also check before publishing

- [ ] `AUTO_APPROVE_AI_ITEMS=false` (default) — AI items must not reach students unreviewed
- [ ] `AI_PROVIDER=local` unless you have deliberately configured Ollama/keys
- [ ] No `.env` committed (it is gitignored) and no API keys in `render.yaml`
- [ ] `CORS_ORIGINS` set **only** for Option B; list your exact Netlify origin
- [ ] Content licensing: the bank holds original item wording and atomic facts,
      no NCERT passages — keep it that way if you add content
- [ ] The name "ReviseX" is a placeholder; rename in
      `frontend/src/shared/brand.ts` before anyone sees it publicly

---

## 5. Verifying a deployment

```bash
curl https://<your-host>/api/health
# {"status":"ok","questions":1303,"profiles":0,"offline_capable":true}
```

Then in a browser: open the site → create a profile → Science → Chemistry →
**1 Minute Sprint** → answer a few → check the results screen shows a score and
that the wrong answers appear under **My mistakes**.

If the page loads but every call fails, it is almost always one of:
`VITE_API_URL` unset/stale (Option B), CORS origin mismatch (Option B), or the
backend still cold-starting (free tier).

---

## 6. Cost summary

| Setup | Cost | Data persistence |
|---|---|---|
| Your PC | $0 | Full (local file) |
| Render free, no disk | $0 | Progress resets each deploy |
| Render Starter + 1 GB disk | ~$7/mo | Full |
| Netlify free + Render free | $0 | Progress resets each deploy |
| Netlify free + Render Starter | ~$7/mo | Full |
