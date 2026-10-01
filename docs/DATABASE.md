# ReviseX — Database design

Engine: **SQLite 3** (stdlib `sqlite3`), WAL journal mode, `PRAGMA foreign_keys=ON`.
File: `backend/data/revise.sqlite3` (created on first run, gitignored).
Migrations: ordered `backend/app/db/migrations/NNNN_*.sql`, tracked in `schema_version`.

## Design principles

1. **Curriculum is data.** subjects → branches → chapters → topics are rows, so adding Maths/SST/English/Hindi is an insert, not a code change.
2. **Content is immutable-ish and versioned.** Questions carry `revision`, `origin` (`template` / `ai` / `manual`) and `status` (`draft` / `pending_review` / `approved` / `archived`). Only `approved` items are selectable in a test.
3. **Answer order is per-attempt.** Options are stored with a stable `key` (`a`–`d`); the shuffled display order is recorded on the attempt, so results stay reproducible and options can be shuffled per student.
4. **Progress is derived but materialised.** `topic_mastery`, `personal_bests` and `profile_stats` are rollups maintained on write, so the dashboard is one cheap query, never an aggregate over thousands of attempts.
5. **No PII by default.** Profiles are local nicknames. Online sync columns exist but default to off and store only a public handle.

## Table map

```
subjects ──< branches ──< chapters ──< topics ──< questions ──< question_options
                                    └─< facts (structured knowledge, drives generation)

profiles ──< sessions ──< attempts >── questions
   │            │
   │            └── session_events (level_up, badge, pb)
   ├──< mistakes            (per question, with wrong_count, last_wrong_at)
   ├──< topic_mastery       (per topic: mastery, attempts, correct, streak, due_at)
   ├──< srs_cards           (interval, ease, due_at, state)
   ├──< personal_bests      (per scope: mode/chapter/branch/day)
   ├──< xp_events           (append-only XP ledger)
   └──< badge_awards
leaderboard_entries (local, day-scoped) — denormalised for fast reads
```

## Schema (DDL)

Authoritative copy: `backend/app/db/migrations/0001_init.sql`.

```sql
CREATE TABLE subjects (
  id TEXT PRIMARY KEY, name TEXT NOT NULL, icon TEXT,
  display_order INTEGER NOT NULL DEFAULT 0, is_active INTEGER NOT NULL DEFAULT 1,
  meta_json TEXT NOT NULL DEFAULT '{}'
);

CREATE TABLE branches (
  id TEXT PRIMARY KEY, subject_id TEXT NOT NULL REFERENCES subjects(id) ON DELETE CASCADE,
  name TEXT NOT NULL, icon TEXT, display_order INTEGER NOT NULL DEFAULT 0,
  is_active INTEGER NOT NULL DEFAULT 1, meta_json TEXT NOT NULL DEFAULT '{}'
);
CREATE INDEX idx_branches_subject ON branches(subject_id, display_order);

CREATE TABLE chapters (
  id TEXT PRIMARY KEY, branch_id TEXT NOT NULL REFERENCES branches(id) ON DELETE CASCADE,
  code TEXT, name TEXT NOT NULL, display_order INTEGER NOT NULL DEFAULT 0,
  syllabus_status TEXT NOT NULL DEFAULT 'core',   -- core | optional | removed
  exam_board TEXT NOT NULL DEFAULT 'cbse',
  meta_json TEXT NOT NULL DEFAULT '{}'
);
CREATE INDEX idx_chapters_branch ON chapters(branch_id, display_order);

CREATE TABLE topics (
  id TEXT PRIMARY KEY, chapter_id TEXT NOT NULL REFERENCES chapters(id) ON DELETE CASCADE,
  name TEXT NOT NULL, display_order INTEGER NOT NULL DEFAULT 0,
  meta_json TEXT NOT NULL DEFAULT '{}'
);
CREATE INDEX idx_topics_chapter ON topics(chapter_id, display_order);

-- Atomic, vetted knowledge. The only legal input to question generation.
CREATE TABLE facts (
  id TEXT PRIMARY KEY, chapter_id TEXT NOT NULL REFERENCES chapters(id) ON DELETE CASCADE,
  topic_id TEXT REFERENCES topics(id) ON DELETE SET NULL,
  kind TEXT NOT NULL,                -- element | formula | definition | reaction | unit | law | event ...
  label TEXT NOT NULL,
  payload_json TEXT NOT NULL,        -- e.g. {"symbol":"H","valency":1,"atomic_number":1}
  source_ref TEXT NOT NULL,
  meta_json TEXT NOT NULL DEFAULT '{}'
);
CREATE INDEX idx_facts_chapter ON facts(chapter_id, kind);

CREATE TABLE questions (
  id TEXT PRIMARY KEY,
  chapter_id TEXT NOT NULL REFERENCES chapters(id) ON DELETE CASCADE,
  topic_id TEXT REFERENCES topics(id) ON DELETE SET NULL,
  question_type TEXT NOT NULL,
  prompt TEXT NOT NULL,
  stimulus_json TEXT NOT NULL DEFAULT '{}',   -- big centre-screen element (symbol, equation, graph)
  answer_key TEXT NOT NULL,
  explanation TEXT,
  hint TEXT,
  difficulty TEXT NOT NULL DEFAULT 'medium',  -- easy | medium | hard
  time_budget_ms INTEGER NOT NULL DEFAULT 10000,
  source_ref TEXT NOT NULL,
  origin TEXT NOT NULL DEFAULT 'template',    -- template | ai | manual
  status TEXT NOT NULL DEFAULT 'approved',    -- draft | pending_review | approved | archived
  revision INTEGER NOT NULL DEFAULT 1,
  dedupe_hash TEXT,
  meta_json TEXT NOT NULL DEFAULT '{}',
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX idx_q_select ON questions(status, chapter_id, question_type, difficulty);
CREATE INDEX idx_q_topic ON questions(topic_id, status);
CREATE UNIQUE INDEX idx_q_dedupe ON questions(dedupe_hash);

CREATE TABLE question_options (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  question_id TEXT NOT NULL REFERENCES questions(id) ON DELETE CASCADE,
  opt_key TEXT NOT NULL,              -- a|b|c|d
  text TEXT NOT NULL,
  render_json TEXT NOT NULL DEFAULT '{}',
  is_correct INTEGER NOT NULL DEFAULT 0,
  display_order INTEGER NOT NULL DEFAULT 0,
  UNIQUE (question_id, opt_key)
);
CREATE INDEX idx_options_question ON question_options(question_id, display_order);

CREATE TABLE profiles (
  id TEXT PRIMARY KEY,
  display_name TEXT NOT NULL,
  avatar TEXT,
  is_active INTEGER NOT NULL DEFAULT 0,
  xp_total INTEGER NOT NULL DEFAULT 0,
  level INTEGER NOT NULL DEFAULT 1,
  streak_day_count INTEGER NOT NULL DEFAULT 0,
  last_active_day TEXT,
  online_enabled INTEGER NOT NULL DEFAULT 0,   -- opt-in only
  public_handle TEXT,
  settings_json TEXT NOT NULL DEFAULT '{}',
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE sessions (
  id TEXT PRIMARY KEY,
  profile_id TEXT NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
  mode_key TEXT NOT NULL,                       -- rush_60s | chapter_test | mistakes ...
  subject_id TEXT, branch_id TEXT, chapter_id TEXT, topic_id TEXT,
  started_at TEXT NOT NULL, finished_at TEXT,
  duration_limit_ms INTEGER, elapsed_ms INTEGER,
  questions_total INTEGER NOT NULL DEFAULT 0,
  questions_answered INTEGER NOT NULL DEFAULT 0,
  correct_count INTEGER NOT NULL DEFAULT 0,
  score INTEGER NOT NULL DEFAULT 0,
  xp_awarded INTEGER NOT NULL DEFAULT 0,
  best_streak INTEGER NOT NULL DEFAULT 0,
  accuracy REAL, avg_response_ms REAL, fastest_response_ms REAL,
  config_json TEXT NOT NULL DEFAULT '{}',
  summary_json TEXT NOT NULL DEFAULT '{}',      -- weak/strong areas, pb deltas
  client_version TEXT,
  sync_state TEXT NOT NULL DEFAULT 'local'
);
CREATE INDEX idx_sessions_profile ON sessions(profile_id, started_at DESC);
CREATE INDEX idx_sessions_day ON sessions(profile_id, substr(started_at,1,10));

CREATE TABLE attempts (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  session_id TEXT NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
  question_id TEXT NOT NULL REFERENCES questions(id) ON DELETE CASCADE,
  profile_id TEXT NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
  seq INTEGER NOT NULL,
  selected_key TEXT,
  option_order_json TEXT NOT NULL DEFAULT '[]',
  is_correct INTEGER NOT NULL DEFAULT 0,
  response_ms INTEGER NOT NULL DEFAULT 0,
  shown_ms INTEGER NOT NULL DEFAULT 0,
  points_awarded INTEGER NOT NULL DEFAULT 0,
  streak_at_answer INTEGER NOT NULL DEFAULT 0,
  difficulty TEXT NOT NULL,
  question_type TEXT NOT NULL,
  chapter_id TEXT, topic_id TEXT,
  created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX idx_attempts_session ON attempts(session_id, seq);
CREATE INDEX idx_attempts_question ON attempts(question_id, is_correct);
CREATE INDEX idx_attempts_topic ON attempts(profile_id, topic_id, created_at DESC);

CREATE TABLE mistakes (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  profile_id TEXT NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
  question_id TEXT NOT NULL REFERENCES questions(id) ON DELETE CASCADE,
  chapter_id TEXT, topic_id TEXT, question_type TEXT,
  wrong_count INTEGER NOT NULL DEFAULT 1,
  correct_since_count INTEGER NOT NULL DEFAULT 0,
  last_wrong_at TEXT NOT NULL,
  resolved INTEGER NOT NULL DEFAULT 0,
  UNIQUE (profile_id, question_id)
);
CREATE INDEX idx_mistakes_open ON mistakes(profile_id, resolved, last_wrong_at DESC);

CREATE TABLE topic_mastery (
  profile_id TEXT NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
  topic_id TEXT NOT NULL REFERENCES topics(id) ON DELETE CASCADE,
  chapter_id TEXT,
  attempts INTEGER NOT NULL DEFAULT 0,
  correct INTEGER NOT NULL DEFAULT 0,
  mastery REAL NOT NULL DEFAULT 0.5,
  last_result REAL,
  updated_at TEXT NOT NULL DEFAULT (datetime('now')),
  PRIMARY KEY (profile_id, topic_id)
);

CREATE TABLE srs_cards (
  profile_id TEXT NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
  question_id TEXT NOT NULL REFERENCES questions(id) ON DELETE CASCADE,
  state TEXT NOT NULL DEFAULT 'new',   -- new | learning | review | mastered
  interval_days REAL NOT NULL DEFAULT 0,
  ease REAL NOT NULL DEFAULT 2.5,
  lapses INTEGER NOT NULL DEFAULT 0,
  repetitions INTEGER NOT NULL DEFAULT 0,
  due_at TEXT NOT NULL DEFAULT (datetime('now')),
  last_reviewed_at TEXT,
  PRIMARY KEY (profile_id, question_id)
);
CREATE INDEX idx_srs_due ON srs_cards(profile_id, due_at);

CREATE TABLE personal_bests (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  profile_id TEXT NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
  scope TEXT NOT NULL,        -- mode | chapter | branch | subject | day
  scope_key TEXT NOT NULL,    -- rush_60s | sci-chem-ch1 | ...
  metric TEXT NOT NULL,       -- score | accuracy | fastest_avg | longest_streak | most_questions
  value REAL NOT NULL,
  session_id TEXT REFERENCES sessions(id) ON DELETE SET NULL,
  achieved_at TEXT NOT NULL DEFAULT (datetime('now')),
  UNIQUE (profile_id, scope, scope_key, metric)
);
CREATE INDEX idx_pb_profile ON personal_bests(profile_id, scope, metric);

CREATE TABLE xp_events (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  profile_id TEXT NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
  amount INTEGER NOT NULL,
  reason TEXT NOT NULL,       -- session | mastery | personal_best | streak | badge
  session_id TEXT REFERENCES sessions(id) ON DELETE SET NULL,
  created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX idx_xp_profile ON xp_events(profile_id, created_at DESC);

CREATE TABLE badges (
  id TEXT PRIMARY KEY, name TEXT NOT NULL, description TEXT NOT NULL,
  icon TEXT, criterion_json TEXT NOT NULL DEFAULT '{}'
);
CREATE TABLE badge_awards (
  profile_id TEXT NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
  badge_id TEXT NOT NULL REFERENCES badges(id) ON DELETE CASCADE,
  awarded_at TEXT NOT NULL DEFAULT (datetime('now')),
  PRIMARY KEY (profile_id, badge_id)
);

CREATE TABLE session_events (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  session_id TEXT NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
  profile_id TEXT NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
  kind TEXT NOT NULL,         -- level_up | badge | personal_best | streak_milestone
  payload_json TEXT NOT NULL DEFAULT '{}',
  created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE leaderboard_entries (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  scope TEXT NOT NULL,        -- local_today | local_week | local_all
  day TEXT NOT NULL,
  profile_id TEXT NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
  display_name TEXT NOT NULL,
  mode_key TEXT,
  score INTEGER NOT NULL,
  accuracy REAL,
  xp_delta INTEGER NOT NULL DEFAULT 0,
  created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX idx_lb_scope ON leaderboard_entries(scope, day, score DESC);

CREATE TABLE schema_version (
  version INTEGER PRIMARY KEY, name TEXT NOT NULL,
  applied_at TEXT NOT NULL DEFAULT (datetime('now'))
);
```

## Index / performance notes

* Test generation is one query against `idx_q_select` with `status='approved'`; sets are bulk-loaded (see ARCHITECTURE §4), so the hot loop performs **zero** DB access.
* `sessions(profile_id, substr(started_at,1,10))` — SQLite uses the index for the `date(started_at)` filter via the substring form; dashboard "today" stays O(log n).
* Rollups (`profile_stats` via `xp_events` + `sessions` aggregates, `topic_mastery`, `personal_bests`) are updated inside the same transaction as session submission — one write burst per test, not per question.
* Expected scale for MVP: ~10⁴ questions, ~10⁶ attempts. Comfortably inside SQLite's fast range; Postgres swap would only touch `db/connection.py` + repositories.

## Migration policy

* Never edit an applied migration; add `NNNN_description.sql`.
* `migrate.py` applies pending files in order inside a transaction and records the version.
* `seed.py` is **idempotent**: upserts by primary key, bumps `revision` only when content hash changes, and never deletes user progress. `--reset-content` clears content tables only.
