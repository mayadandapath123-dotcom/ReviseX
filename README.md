# ReviseX — Class 10 rapid revision

> **Working name.** The brand is deliberately not final. Every user-facing string
> lives in `frontend/src/shared/brand.ts` and the colours in
> `frontend/src/styles/tokens.css`, so a rename is a two-file edit.

A local-first rapid-revision platform for Class 10. The goal is not to replace
studying — it is to make **recall, revision and exam speed** fast and satisfying:

> "I can revise 20 important things in 60 seconds."

**Status:** Phases 1–2 complete (foundation + quiz engine). Content seeded for
**Science, Mathematics and Social Science — 2,276 questions** from 999 structured
facts across 36 test modes. Phases 4–5 partially wired (balancing mode, mistake
book, mastery, XP/levels/badges/personal bests, SRS). Phase 6 interface-only (AI
provider abstraction with a working offline provider).

---

## Quick start

Requirements: **Python 3.11+** and **Node.js 18+**. Nothing else. No database
server, no accounts, no API keys, no internet.

```bash
git clone <this repo> && cd revise
python scripts/dev.py
```

That one command creates `backend/.venv`, installs both dependency sets, runs
migrations, seeds the content database, starts the API on **:8000** and the web
app on **:5173**. Then open <http://localhost:5173>.

First run takes ~1 minute (dependency install). Subsequent runs take ~3 seconds.

### Running the halves separately

```bash
# Backend only (auto-migrates + seeds on startup)
cd backend && python run.py

# Frontend only (proxies /api to http://127.0.0.1:8000)
cd frontend && npm install && npm run dev
```

### Useful commands

| Command | What it does |
|---|---|
| `python scripts/dev.py` | Run backend + frontend together |
| `python scripts/dev.py --reset` | Delete the local DB, reseed, then run |
| `cd backend && python run.py --seed` | Seed only, print a JSON report, exit |
| `cd backend && python run.py --reseed` | Wipe **content** tables (never progress) and re-import |
| `cd backend && python -m pytest -q` | Run the engine/scoring/balancing/validator tests |
| `cd backend && TEST_POSTGRES_URL=... python -m pytest -q` | The same suite against a real Postgres |
| `cd frontend && npx tsc --noEmit` | Typecheck the frontend |
| `open http://localhost:8000/docs` | Interactive API docs |

**The backend has two implementations, so test it twice.** SQLite locally and
Postgres in production are reached through the same facade in `app/db/connection.py`,
and anything that facade is missing only breaks in production. That is not
hypothetical: a missing `PgCursor.__iter__` meant `for row in conn.execute(...)`
ran in every local test and crashed the live site on startup. The Postgres run
needs a throwaway database and takes about 30 seconds:

```bash
cd backend
TEST_POSTGRES_URL=postgresql://user@host/scratch_db python -m pytest -q
```

`tests/test_postgres_parity.py` holds the checks that keep the two backends
swappable, including a full seed against the real server.

---

## The first milestone (working now)

Open the site → pick or create a local profile → **Science** → **Chemistry** →
a chapter → **1 Minute Sprint** → answer MCQs with keys `1`–`4` → instant
feedback → results screen with score, accuracy, average response time, best
streak, XP, personal best, and weak/strong areas → wrong answers land in
**My mistakes** and are re-drillable.

---

## Stack

| Layer | Choice | Why |
|---|---|---|
| Frontend | React 18 + TypeScript + Vite | Fast HMR; Vite proxies `/api` so browser code never hard-codes a host |
| State | Zustand + TanStack Query | Zustand for the hot loop (no re-render storms); Query for cached server reads |
| Styling | Design tokens + semantic CSS classes | Dark-first, zero-dependency, re-brandable by editing one file |
| Backend | FastAPI + Pydantic v2 | Pydantic validates both API input **and** the content files |
| Database | SQLite (WAL) via stdlib `sqlite3` | Required local-first DB, zero install; hand-written SQL keeps queries explicit |
| Migrations | Ordered `NNNN_*.sql` + `schema_version` | Alembic is overkill while the schema stabilises |
| Content | JSON fact files → generated questions | Human-reviewable authoring source; SQLite is the runtime source of truth |
| AI | `AIProvider` abstraction, Ollama optional | Deterministic local fallback means AI is never a dependency |

Full rationale in [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md).
Scoring/XP/SRS rules in [`docs/SCORING.md`](docs/SCORING.md); syllabus map and
question inventory in [`docs/SCIENCE_MODULE.md`](docs/SCIENCE_MODULE.md).

**Deploying it?** See [`docs/DEPLOYMENT.md`](docs/DEPLOYMENT.md) — running on your
own PC, publishing to Render as a single service, or splitting Netlify +
Render, plus the auth/persistence caveats that apply to a public URL.

**Want it live in one command?** [`docs/ONE_COMMAND_DEPLOY.md`](docs/ONE_COMMAND_DEPLOY.md)
covers `scripts/deploy.sh`, which commits, pushes, triggers the Render rebuild and
then verifies the live question count. For Neon and Google sign-in setup, see
[`docs/DEPLOY_ZIP_NEON_GOOGLE.md`](docs/DEPLOY_ZIP_NEON_GOOGLE.md).

---

## Layout

```
revise/
├── docs/            ARCHITECTURE.md · DATABASE.md · SCIENCE_MODULE.md · SCORING.md
│                    DEPLOYMENT.md · ONE_COMMAND_DEPLOY.md · GOOGLE_SIGNIN.md
├── backend/
│   ├── app/
│   │   ├── main.py            FastAPI factory (migrate + seed on startup)
│   │   ├── config/            env-driven settings
│   │   ├── db/                connection, migrations, seed pipeline
│   │   ├── content/           schema, validators, generators (facts -> questions)
│   │   ├── services/          quiz, scoring, progress, profile, leaderboard,
│   │   │                      recommendation, SRS, balancing, content
│   │   ├── ai/                provider abstraction + anti-hallucination gate
│   │   └── api/               thin routers + request schemas
│   ├── content/               authorable curriculum data (JSON)
│   │   ├── curriculum.json    subjects -> branches -> chapters -> topics
│   │   ├── modes.json         20 test presets
│   │   └── science/{chemistry,physics,biology,fundamentals}/*.json
│   ├── data/                  generated SQLite DB (gitignored)
│   └── tests/test_core.py
├── frontend/src/
│   ├── app/                   router, providers, persisted profile store
│   ├── shared/                api client, types, scoring mirror, UI primitives
│   ├── features/              profiles, dashboard, science, quiz, balancing,
│   │                          mistakes, progress
│   └── styles/                tokens.css (design language) + base.css
└── scripts/dev.py             one-command dev runner
```

---

## Configuration

Copy `.env.example` to `.env` if you want to change anything — **every value has
a working default and the app runs with no `.env` at all.**

| Variable | Default | Notes |
|---|---|---|
| `PORT` / `HOST` | `8000` / `0.0.0.0` | API bind address |
| `CORS_ORIGINS` | localhost:5173 | Comma-separated |
| `DATA_DIR`, `DB_FILENAME` | `backend/data`, `revise.sqlite3` | Delete to reset progress |
| `ALLOW_OFF_SYLLABUS` | `false` | Include off-syllabus chapters in default tests |
| `AUTO_APPROVE_AI_ITEMS` | `false` | **Keep false.** AI items go to a review queue |
| `AI_PROVIDER` | `local` | `local` \| `ollama` \| `free_api` \| `paid_api` \| `none` |
| `OLLAMA_URL`, `OLLAMA_MODEL` | `127.0.0.1:11434`, `llama3.2:3b` | Used only when `AI_PROVIDER=ollama` |
| `FREE_AI_API_KEY`, `PAID_AI_API_KEY` | unset | Read **server-side only**, never sent to the browser |
| `VITE_API_BASE_URL` | `http://127.0.0.1:8000` | Vite proxy target |

### Optional local AI

```bash
# install Ollama from https://ollama.com, then:
ollama pull llama3.2:3b
AI_PROVIDER=ollama python scripts/dev.py
```

If Ollama is missing, slow or unreachable, the app logs a notice and falls back to
the built-in offline generator. **The quiz engine never calls AI.** AI output is
validated against the approved facts it was given and quarantined as
`pending_review` until approved in the content studio — it cannot invent a fact
and cannot reach a student silently.

---

## Adding content

Content is data. Two steps, no code:

1. Declare structure in `backend/content/curriculum.json` (subject → branch →
   chapter → topic, with `syllabus_status`: `core`, `foundation`, `optional`,
   `removed`).
2. Add a fact file under `backend/content/<subject>/…` and re-seed.

Fact kinds and their generators:

| `kind` | Generator | Produces |
|---|---|---|
| `element` | `elements` | valency, symbol↔name, atomic number, configuration, metal/non-metal, "which is NOT" |
| `formula` | `chem_formula` | name↔formula, common names, acid/base/salt classification |
| `definition` | `definition` | term↔definition in both directions |
| `fact` | `fact_attribute` | subject/attribute/value recall, reverse recall, "which statement is NOT correct" |
| `reaction` | `reaction` | reaction type, observation, product, exo/endothermic |
| `equation` | `balancing` | interactive balancing items (coefficients solved + verified) |
| `formula` (physics) | `physics_formula` | formula recognition, variable ID, SI unit, numerical drills |
| `sequence` | `sequence` | correct-order questions with permuted distractors |

Distractors are always drawn from **sibling facts of the same attribute**, never
from random words — that is what keeps them plausible. The validators reject
throwaway options (`banana`, `none of these`), duplicate options, missing source
references, and markup/control characters.

### Adding a subject

Maths, SST, English and Hindi are already registered in `curriculum.json` with
`is_active: false`. Add their branches/chapters/topics and fact files, flip
`is_active`, reseed. **No engine, service, or UI change is required** — the quiz
loop, scoring, mastery, SRS, mistake book and personal bests are all
subject-agnostic and keyed off `subject_id`/`branch_id`/`chapter_id`/`topic_id`.

---

## Design guarantees

These are enforced by code and covered by tests, not just intentions:

- **A wrong answer can never outscore a correct one.** Speed bonus is capped at
  40% of base points and only applies when correct; streak multiplier caps at 1.5×.
- **Blind clicking loses.** A test asserts random guessing scores under 35% of
  honest play at the same pace (wrong answers reset the streak multiplier).
- **Balancing is verified by atom conservation,** not string comparison. Valid
  but unsimplified multiples are detected and explained rather than silently
  accepted.
- **No question waits on the network.** Sets are bulk-fetched before a test
  starts; one batched POST persists it. The loop works offline.
- **Scoring is authoritative server-side.** Client points are for display only;
  the server re-grades every attempt and re-verifies balancing coefficients.
- **Nothing enters the bank unvalidated.** Seeded, manual and AI-generated items
  all pass the same validator before they can be served.
- **Local-first, no PII.** Nicknames only. Online sync columns exist but default
  to off and would carry a public handle, never an email.

---

## Roadmap

| Phase | Deliverable | State |
|---|---|---|
| 1 | Monorepo, FastAPI+SQLite, migrations, seeding, theme, profiles, dashboard | ✅ |
| 2 | MCQ hot loop, timer, instant feedback, scoring, results | ✅ |
| 3 | Science content: Chemistry, Physics + Biology seeded, rapid tests | ✅ 1,498 questions |
| 4 | Balancing mode, weak-topic practice, mistake book, adaptive tests | 🟡 |
| 5 | XP, levels, streaks, badges, personal bests, mastery | 🟡 |
| 6 | AI provider interface, local provider, Ollama, review queue | 🟡 interface + offline provider working |
| 7 | Maths + SST on the same engine | ✅ 242 Maths / 444 SST questions · English & Hindi still scaffolded |
| 8 | Optional cloud accounts, online leaderboard, challenges | ⬜ schema-ready |

Known gaps at this commit: the content studio UI is not built yet (the admin API
is), frontend unit tests are not written (backend tests are), and Physics
"Magnetic Effects" plus two Biology chapters have thinner banks than Chemistry.
Those are the next work items, in that order.
