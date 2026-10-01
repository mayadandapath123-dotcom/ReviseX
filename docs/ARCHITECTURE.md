# ReviseX — Architecture (working name, not finalised)

Class 10 rapid-revision platform. Local-first, offline-capable, subject-agnostic core.

> Status: Phase 1 (Foundation) + Phase 2 (Quiz Engine) + start of Phase 3 (Science content).

---

## 1. System context

```
┌────────────────────────────── student's machine ──────────────────────────────┐
│                                                                               │
│   Browser (React + Vite + TS)                                                 │
│   ├── Client Quiz Engine   ← authoritative for timing & interaction           │
│   ├── Content Cache        ← preloaded question sets (0 network per question) │
│   └── Local Optimistic UI  ← streaks/XP update instantly, sync on submit      │
│              │  HTTP /json (localhost, proxied by Vite in dev)                │
│              ▼                                                                │
│   FastAPI app                                                                 │
│   ├── QuestionService   QuizEngine   ScoringEngine                            │
│   ├── ProgressService   ProfileService   LeaderboardService                   │
│   ├── RecommendationEngine   SpacedRepetitionService                          │
│   ├── ContentService (+ seeding pipeline + validators)                        │
│   ├── BalancingEngine (atom-conservation verifier)                            │
│   └── AIService → AIProvider { Local | Ollama | FreeAPI | PaidAPI | Null }    │
│              │  stdlib sqlite3 (WAL mode)                                     │
│              ▼                                                                │
│   SQLite  (data/leap.sqlite3 + versioned migrations)                          │
│                                                                               │
│   content/**.json  ──seed──►  SQLite     (human-authorable source of truth)   │
└───────────────────────────────────────────────────────────────────────────────┘
                       ⋯ optional, never required ⋯
              Online leaderboard API / Ollama / free AI endpoint
```

Two rules that shape everything else:

1. **A question never waits on the network.** Question sets are fetched once, in bulk, before a test starts. Timing, feedback, transitions and scoring previews are 100 % client-side. The backend persists the session afterwards.
2. **AI is an enhancement, never a dependency.** Every feature degrades to a deterministic local implementation (`LocalAIProvider`) or disappears gracefully.

---

## 2. Technology choices

| Layer | Choice | Why (and what was rejected) |
|---|---|---|
| Frontend | **React 18 + TypeScript + Vite** | Fastest cold start & HMR; Vite dev server proxies `/api` so browser code never hard-codes `localhost`. Svelte/Solid would be lighter but the React ecosystem gives us the cheapest path to the long feature list. |
| State | **Zustand** (ephemeral engine state) + **TanStack Query** (server cache) | A quiz session is a hot loop — Zustand gives mutation without re-render storms. Query handles caching/invalidation of dashboard stats so we don't hand-roll it. Redux rejected: boilerplate cost for no benefit here. |
| Styling | **Tailwind CSS v4** + CSS custom-property design tokens | Dark-first tokens in one place (`styles/tokens.css`) ⇒ re-branding (and the pending name change) is a token edit, not a refactor. No component library — we need a specific feel, and Bootstrap/MUI were explicitly ruled out. |
| Animation | CSS transitions/keyframes, `prefers-reduced-motion` aware | Subtle and cheap. A motion library is deliberately avoided in the hot loop. |
| Backend | **Python 3.11+ / FastAPI + Uvicorn + Pydantic v2** | Pydantic gives us request/response validation *and* doubles as the content-file validator. Node/Express was the alternative; Python wins because the science/AI work (balancing solver, distractor validation, future local models) is far more natural there. |
| DB driver | **stdlib `sqlite3`** (no ORM) | Hand-written SQL keeps queries explicit and fast, and the schema is small enough that an ORM would only add magic. Repository modules isolate SQL so an ORM/Postgres swap later is contained. |
| Database | **SQLite in WAL mode** | Required by brief (local-first, proper DB, not JSON soup). Postgres/MySQL rejected for MVP: zero-install matters. |
| Migrations | **Tiny in-repo versioned SQL migrations** | Alembic is overkill while the schema is stabilising; `migrations/0001_init.sql …` + a `schema_version` table gives the same guarantee. |
| Content authoring | **JSON files in `backend/content/`** → seeded into SQLite | Human-reviewable, diffable, zero extra dependency (YAML needs PyYAML). SQLite stays the runtime source of truth; JSON stays the authoring source. |
| AI | **Provider abstraction**, Ollama optional, deterministic local fallback | See §8. |
| Testing | **pytest** (engine, scoring, balancing, seeding) + **Vitest** (client engine, scoring parity) | Scoring must behave identically on both sides, so it is implemented twice on purpose and covered by parity tests. |

Single-command dev: `python scripts/dev.py` boots backend + frontend together.

---

## 3. Repository layout

```
revise/
├── docs/
│   ├── ARCHITECTURE.md          ← this file
│   ├── DATABASE.md              ← schema rationale, indexes, migration policy
│   ├── SCIENCE_MODULE.md        ← syllabus map, question-type matrix, content spec
│   └── SCORING.md               ← exact scoring/streak/mastery/SRS formulas
├── backend/
│   ├── app/
│   │   ├── main.py              ← FastAPI app factory, CORS, routers, lifespan
│   │   ├── config/settings.py   ← env-driven config (pydantic-settings)
│   │   ├── db/
│   │   │   ├── connection.py    ← sqlite3 connection, WAL, row factory
│   │   │   ├── migrate.py       ← applies migrations in order, records version
│   │   │   ├── seed.py          ← content pipeline: load → validate → upsert
│   │   │   ├── schema.sql       ← consolidated reference schema (docs/dev)
│   │   │   └── migrations/0001_init.sql
│   │   ├── content/             ← validators, id conventions, fact→question generation
│   │   │   ├── validators.py
│   │   │   └── generators.py
│   │   ├── services/
│   │   │   ├── question_service.py
│   │   │   ├── quiz_engine.py       ← test generation / selection policy
│   │   │   ├── scoring_engine.py    ← canonical scoring (mirrored in TS)
│   │   │   ├── progress_service.py  ← XP, levels, badges, personal bests
│   │   │   ├── profile_service.py
│   │   │   ├── leaderboard_service.py
│   │   │   ├── recommendation_engine.py
│   │   │   ├── spaced_repetition_service.py
│   │   │   └── balancing_engine.py
│   │   ├── ai/
│   │   │   ├── base.py          ← AIProvider protocol + schemas
│   │   │   ├── local.py         ← deterministic template generator (no model)
│   │   │   ├── ollama.py
│   │   │   ├── free_api.py      ← placeholder, opt-in
│   │   │   ├── paid_api.py      ← placeholder, keys server-side only
│   │   │   ├── validation.py    ← anti-hallucination gate
│   │   │   └── service.py       ← provider selection, caching, degradation
│   │   └── api/
│   │       ├── deps.py          ← DI: get_db, get_services
│   │       ├── routers/{profiles,content,quiz,progress,mistakes,leaderboard,admin,ai}.py
│   │       └── schemas/{content,quiz,progress,profile}.py
│   ├── content/                 ← authorable curriculum data (see SCIENCE_MODULE.md)
│   │   ├── curriculum.json      ← subjects → branches → chapters → topics (+ syllabus flags)
│   │   ├── science/{chemistry,physics,biology,fundamentals}/*.json
│   │   ├── maths/ sst/ english/ hindi/     ← empty scaffolds, same contract
│   │   └── modes.json           ← quick-start mode presets
│   ├── data/                    ← generated SQLite db (gitignored)
│   ├── tests/
│   ├── requirements.txt
│   └── run.py
├── frontend/
│   ├── src/
│   │   ├── main.tsx / App.tsx
│   │   ├── app/{router.tsx,providers.tsx}
│   │   ├── shared/
│   │   │   ├── api/{client.ts,endpoints.ts}
│   │   │   ├── types/{curriculum.ts,quiz.ts,progress.ts}
│   │   │   ├── lib/{scoring.ts,format.ts,keyboard.ts,storage.ts,time.ts}
│   │   │   └── ui/{Button,Card,Option,ProgressRing,Timer,StatTile,Modal,EmptyState,Skeleton}
│   │   ├── features/
│   │   │   ├── profiles/        ← profile picker + create (local, no accounts)
│   │   │   ├── dashboard/       ← today's progress, quick start, continue, weak topics
│   │   │   ├── science/         ← subject → branch → chapter drill-down with mastery
│   │   │   ├── quiz/            ← THE hot loop (engine store, question screen, results)
│   │   │   ├── balancing/       ← interactive coefficient steppers
│   │   │   ├── mistakes/        ← mistake book + practice-mistakes modes
│   │   │   ├── progress/        ← XP, levels, badges, personal bests, mastery table
│   │   │   └── content-studio/  ← local admin/content editor (dev-gated)
│   │   └── styles/{tokens.css,base.css,animations.css}
│   ├── index.html, vite.config.ts, tsconfig.json, tailwind/postcss config
│   └── package.json
├── scripts/dev.py               ← one command: seed + backend + frontend
├── .env.example  .gitignore  README.md
```

Nothing is a "giant file": services are ≤ ~300 lines each, feature folders own their components/hooks, and SQL lives in one repository layer per aggregate.

---

## 4. Core loop (the product)

```
Dashboard ──quick start──► QuizEngine.buildTest(config)
                                 │  one bulk GET /api/quiz/sessions
                                 ▼
                    Client receives prefetched set (Q+A+explanations)
                                 ▼
                    ┌──── Client Quiz Engine (hot loop) ────┐
                    │ render → input(1-4 / click) →         │
                    │ grade → feedback(150-600ms) → next    │
                    │ records: response_ms, is_correct,     │
                    │          selected, streak, points     │
                    └───────────────────────────────────────┘
                                 ▼
                    POST /api/quiz/sessions/{id}/submit (single batched write)
                                 ▼
        ScoringEngine → ProgressService (XP/level/badges/PB)
                      → mastery upsert → mistakes upsert → SRS schedule
                                 ▼
                    Results screen (score, accuracy, avg speed,
                    best streak, weak/strong areas, PB delta)
```

Why this split: the brief demands instant transitions and offline operation. Per-question network calls would add 5–50 ms jitter and break offline. Batched submit keeps SQLite writes cheap and transactions atomic.

Offline behaviour: if the backend is unreachable the UI shows a banner, tests already loaded keep working, and completed sessions queue in `localStorage` for later sync.

---

## 5. Question model (content engine)

Every record carries full metadata, so filters, mastery rollups and analytics never need to parse text:

```json
{
  "id": "sci.chem.mnm.fact.valency.hydrogen.valency_of_element",
  "subject": "science",
  "branch": "chemistry",
  "chapter": "sci-chem-ch3",
  "topic": "valency",
  "question_type": "valency_of_element",
  "prompt": "What is the valency of hydrogen (H)?",
  "stimulus": { "kind": "element_symbol", "symbol": "H" },
  "options": [
    { "key": "a", "text": "1" },
    { "key": "b", "text": "2" },
    { "key": "c", "text": "3" },
    { "key": "d", "text": "4" }
  ],
  "answer_key": "a",
  "explanation": "Hydrogen has one valence electron, which it can lose or share ⇒ valency 1.",
  "difficulty": "easy",
  "time_budget_ms": 8000,
  "tags": ["recall", "fundamentals"],
  "source_ref": "NCERT Class 10 Science (2025-26 rationalised) — syllabus-aligned original item",
  "origin": "template",
  "status": "approved"
}
```

Question types are a registry, not an enum hard-coded in components. Each type declares: renderer, grading strategy, option-generation strategy, and time budget. `mcq_single` covers ~90 % of the brief's list; `balancing` and (later) `numeric_input` are separate strategies.

**Facts drive questions.** `content/science/fundamentals/elements.json` holds structured facts (`symbol`, `atomic_number`, `valency`, `electronic_configuration`, `metal`). `generators.py` expands each fact across several templates (symbol→valency, valency→element, name→symbol, atomic number, configuration) with distractors drawn from *plausible neighbours in the same fact table* — never from a random-word list. This is the same contract the AI pipeline uses, so AI-generated items and template items are interchangeable in the DB.

Syllabus safety: each chapter row has `syllabus_status ∈ {core, optional, removed}` and `exam_board`. Selection queries default to `core`; `optional` content is only reachable from explicitly-labelled "Advanced / Off-syllabus" modes. Every item keeps `source_ref`. No textbook passages are stored — only atomic facts and original items.

---

## 6. Scoring (full spec in `docs/SCORING.md`)

```
difficulty_points = { easy: 100, medium: 150, hard: 220 }

speed_factor   = clamp((time_budget_ms − response_ms) / time_budget_ms, 0, 1) ^ 0.75
speed_bonus    = round(0.40 × difficulty_points × speed_factor)      // only if correct

streak_mult    = 1 + 0.10 × min(streak_before_answer, 10) / 2        // 1.0 → 1.5, capped

points         = round((difficulty_points + speed_bonus) × streak_mult)   // correct
points         = 0                                                    // wrong (rush modes)
               = −min(20, 0.15 × difficulty_points)                   // wrong (exam-sim mode only)
```

Guarantees: a wrong answer can **never** outscore a correct one (max wrong penalty is negative, max speed bonus is 40 % of base), and blind clicking has negative expected value because a 4-option guess is right 25 % of the time while a wrong answer resets the streak multiplier and re-schedules the card.

Session score = Σ points + completion bonus + accuracy bonus (`round(500 × (acc − 0.6)) if acc ≥ 0.6`).
XP = `floor(session_score / 10)` + mastery/first-clear/PB awards, so XP tracks demonstrated skill rather than volume alone.

Levels: `xp_for_level(n) = 300 · n^1.6` (rounded to 10). Level names are data (`progress/levels.json`), not code.

---

## 7. Adaptive revision + spaced repetition (deliberately simple in V1)

Topic mastery is a leaky, recency-weighted estimate, recomputed per attempt:

```
mastery_new = mastery_old + k × (result − expected)     k = 0.25
result      = 1 (correct) / 0 (wrong)
expected    = difficulty prior { easy: .85, medium: .70, hard: .55 }
```

Confidence = `attempts / (attempts + 6)`; UI shows mastery only when confidence ≥ 0.3 to avoid "44 %" from one lucky guess.

SRS (in-session + cross-session, one table):

| outcome | interval |
|---|---|
| wrong | re-appear after 3–6 questions in the same session |
| 1st correct | +1 day |
| 2nd | +3 days |
| 3rd | +7 days |
| 4th+ | ×2.5, cap 30 days |

Weak-topic selection = `score = (1 − mastery) × 0.7 + recency_penalty × 0.2 + error_rate × 0.1`, top-N by score. This is intentionally not a full SM-2/FSRS implementation — the brief says don't over-engineer V1, and the `srs_cards` table can absorb a better algorithm later without a migration.

---

## 8. AI integration

```python
class AIProvider(Protocol):
    name: str
    def available(self) -> bool: ...
    def generate_items(self, facts, spec) -> list[GeneratedItem]: ...
    def generate_explanation(self, item) -> str | None: ...
    def generate_hints(self, item) -> list[str]: ...
    def analyse_session(self, session) -> Insights: ...
```

`LocalAIProvider` (default, always available, zero cost): deterministic template + fact-table expansion, distractor selection by numeric/symbolic proximity, hint generation from templates. `OllamaProvider`: opt-in via `AI_PROVIDER=ollama`, `OLLAMA_URL`, `OLLAMA_MODEL`; failures fall back to Local. `FreeAPIProvider` / `PaidAPIProvider`: placeholders with the same interface; keys are read **server-side only** from env and never serialised into any response.

Pipeline (the AI may never invent a fact):

```
content/*.json facts (approved)  →  AIService.generate(facts, spec)
        →  provider output  →  validation.py  →  questions(origin='ai', status='pending_review')
        →  content-studio review  →  status='approved'  →  eligible for tests
```

Validation gate rejects an item if: any fact/number/symbol in the answer is not present in the supplied fact record; options count ≠ 4; `answer_key` not among option keys; duplicate option text; prompt references a chapter outside the item's own chapter; language/difficulty out of spec; or near-duplicate of an existing item (normalised-text hash). AI items are quarantined in `pending_review` — they cannot reach a student without approval. No AI output is ever `eval`'d or executed.

---

## 9. Online leaderboard (future-ready, not built)

`profiles` carries `online_enabled` (default 0), `public_handle`, and `sync_cursor`. `personal_bests` rows have `submit_status ∈ {local_only, pending, submitted, rejected}`. The future online path submits only `{public_handle, mode_key, score, accuracy, avg_response_ms, client_version, checksum}` — no name, no email, no per-question data. Anti-cheat is designed in from the start: the server already stores per-attempt `response_ms` and `session_id`, so a submission can be re-derived and compared against physically plausible timings (e.g. min 300 ms/answer, streak distribution). No cloud infrastructure is required by the MVP; the local leaderboard (`GET /api/leaderboard/local?scope=today`) works across profiles on the same install.

---

## 10. Phase plan

| Phase | Deliverable | State |
|---|---|---|
| 1 Foundation | Monorepo, FastAPI+SQLite, migrations, seeding, routing, theme, profiles, dashboard shell | ✅ this turn |
| 2 Quiz engine | MCQ hot loop, timer, instant feedback, scoring, results | ✅ this turn |
| 3 Science content | Chemistry Ch 1–3 seeded, valency/symbol/formula/definition/reaction modes, rapid tests | 🟡 seeded subset this turn, expanding next |
| 4 Advanced modes | Balancing mode, weak-topic practice, mistake book, adaptive tests | 🟡 balancing engine + mistake book wired |
| 5 Progress | XP, levels, streaks, badges, personal bests, mastery | 🟡 core in, badges next |
| 6 AI | Provider interface, local provider, Ollama, generation + review queue | ⬜ interface only |
| 7 Other subjects | Maths (incl. rapid calculation), SST, English, Hindi on the same engine | ⬜ empty content scaffolds exist |
| 8 Online | Optional accounts, online leaderboard, challenges | ⬜ schema-ready |

---

## 11. Risks & open decisions

| Risk | Mitigation |
|---|---|
| Brand name not final | All strings live in `frontend/src/shared/brand.ts` + tokens; no hard-coded name in components. |
| Syllabus drift between boards | `curriculum.json` is data; chapter set is configurable, `syllabus_status` filters selection. |
| Client/server scoring divergence | Shared spec in `docs/SCORING.md`, mirrored implementations, parity tests with fixed fixtures. |
| SQLite concurrency on writes | WAL + single-writer transactions; session submit is one transaction. |
| Content volume vs quality | Template generation from vetted fact tables ⇒ breadth; AI + review queue ⇒ variety; validators ⇒ correctness. |
| Guessing games the score | Streak multiplier resets on wrong; no negative-expected-value reward curve; `exam_simulation` mode adds penalties. |
