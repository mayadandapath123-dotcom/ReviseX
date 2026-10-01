-- 0001_init.sql — ReviseX initial schema
-- Curriculum/content, profiles, sessions, progress, SRS, leaderboard.

PRAGMA foreign_keys = ON;

-- ───────────────────────── curriculum ─────────────────────────

CREATE TABLE IF NOT EXISTS subjects (
  id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  icon TEXT,
  display_order INTEGER NOT NULL DEFAULT 0,
  is_active INTEGER NOT NULL DEFAULT 1,
  meta_json TEXT NOT NULL DEFAULT '{}'
);

CREATE TABLE IF NOT EXISTS branches (
  id TEXT PRIMARY KEY,
  subject_id TEXT NOT NULL REFERENCES subjects(id) ON DELETE CASCADE,
  name TEXT NOT NULL,
  icon TEXT,
  display_order INTEGER NOT NULL DEFAULT 0,
  is_active INTEGER NOT NULL DEFAULT 1,
  meta_json TEXT NOT NULL DEFAULT '{}'
);
CREATE INDEX IF NOT EXISTS idx_branches_subject ON branches(subject_id, display_order);

CREATE TABLE IF NOT EXISTS chapters (
  id TEXT PRIMARY KEY,
  branch_id TEXT NOT NULL REFERENCES branches(id) ON DELETE CASCADE,
  code TEXT,
  name TEXT NOT NULL,
  display_order INTEGER NOT NULL DEFAULT 0,
  syllabus_status TEXT NOT NULL DEFAULT 'core',
  exam_board TEXT NOT NULL DEFAULT 'cbse',
  meta_json TEXT NOT NULL DEFAULT '{}'
);
CREATE INDEX IF NOT EXISTS idx_chapters_branch ON chapters(branch_id, display_order);

CREATE TABLE IF NOT EXISTS topics (
  id TEXT PRIMARY KEY,
  chapter_id TEXT NOT NULL REFERENCES chapters(id) ON DELETE CASCADE,
  name TEXT NOT NULL,
  display_order INTEGER NOT NULL DEFAULT 0,
  meta_json TEXT NOT NULL DEFAULT '{}'
);
CREATE INDEX IF NOT EXISTS idx_topics_chapter ON topics(chapter_id, display_order);

CREATE TABLE IF NOT EXISTS facts (
  id TEXT PRIMARY KEY,
  chapter_id TEXT NOT NULL REFERENCES chapters(id) ON DELETE CASCADE,
  topic_id TEXT REFERENCES topics(id) ON DELETE SET NULL,
  kind TEXT NOT NULL,
  label TEXT NOT NULL,
  payload_json TEXT NOT NULL,
  source_ref TEXT NOT NULL,
  meta_json TEXT NOT NULL DEFAULT '{}'
);
CREATE INDEX IF NOT EXISTS idx_facts_chapter ON facts(chapter_id, kind);

-- ───────────────────────── test presets ─────────────────────────
-- Modes are data so new game modes need no engine change.

CREATE TABLE IF NOT EXISTS test_modes (
  key TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  description TEXT NOT NULL DEFAULT '',
  icon TEXT,
  group_name TEXT NOT NULL DEFAULT 'custom',
  is_featured INTEGER NOT NULL DEFAULT 0,
  is_quick_start INTEGER NOT NULL DEFAULT 0,
  is_active INTEGER NOT NULL DEFAULT 1,
  duration_limit_ms INTEGER,
  question_count INTEGER,
  display_order INTEGER NOT NULL DEFAULT 0,
  filters_json TEXT NOT NULL DEFAULT '{}',
  scoring_json TEXT NOT NULL DEFAULT '{}'
);
CREATE INDEX IF NOT EXISTS idx_modes_group ON test_modes(group_name, display_order);

-- ───────────────────────── question bank ─────────────────────────

CREATE TABLE IF NOT EXISTS questions (
  id TEXT PRIMARY KEY,
  chapter_id TEXT NOT NULL REFERENCES chapters(id) ON DELETE CASCADE,
  topic_id TEXT REFERENCES topics(id) ON DELETE SET NULL,
  question_type TEXT NOT NULL,
  prompt TEXT NOT NULL,
  stimulus_json TEXT NOT NULL DEFAULT '{}',
  answer_key TEXT NOT NULL,
  explanation TEXT,
  hint TEXT,
  difficulty TEXT NOT NULL DEFAULT 'medium',
  time_budget_ms INTEGER NOT NULL DEFAULT 10000,
  source_ref TEXT NOT NULL,
  origin TEXT NOT NULL DEFAULT 'template',
  status TEXT NOT NULL DEFAULT 'approved',
  revision INTEGER NOT NULL DEFAULT 1,
  dedupe_hash TEXT,
  meta_json TEXT NOT NULL DEFAULT '{}',
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_q_select ON questions(status, chapter_id, question_type, difficulty);
CREATE INDEX IF NOT EXISTS idx_q_topic ON questions(topic_id, status);
CREATE UNIQUE INDEX IF NOT EXISTS idx_q_dedupe ON questions(dedupe_hash);

CREATE TABLE IF NOT EXISTS question_options (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  question_id TEXT NOT NULL REFERENCES questions(id) ON DELETE CASCADE,
  opt_key TEXT NOT NULL,
  text TEXT NOT NULL,
  render_json TEXT NOT NULL DEFAULT '{}',
  is_correct INTEGER NOT NULL DEFAULT 0,
  display_order INTEGER NOT NULL DEFAULT 0,
  UNIQUE (question_id, opt_key)
);
CREATE INDEX IF NOT EXISTS idx_options_question ON question_options(question_id, display_order);

-- ───────────────────────── profiles & progress ─────────────────────────

CREATE TABLE IF NOT EXISTS profiles (
  id TEXT PRIMARY KEY,
  display_name TEXT NOT NULL,
  avatar TEXT,
  is_active INTEGER NOT NULL DEFAULT 0,
  xp_total INTEGER NOT NULL DEFAULT 0,
  level INTEGER NOT NULL DEFAULT 1,
  streak_day_count INTEGER NOT NULL DEFAULT 0,
  last_active_day TEXT,
  online_enabled INTEGER NOT NULL DEFAULT 0,
  public_handle TEXT,
  settings_json TEXT NOT NULL DEFAULT '{}',
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS sessions (
  id TEXT PRIMARY KEY,
  profile_id TEXT NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
  mode_key TEXT NOT NULL,
  subject_id TEXT,
  branch_id TEXT,
  chapter_id TEXT,
  topic_id TEXT,
  started_at TEXT NOT NULL,
  finished_at TEXT,
  duration_limit_ms INTEGER,
  elapsed_ms INTEGER,
  questions_total INTEGER NOT NULL DEFAULT 0,
  questions_answered INTEGER NOT NULL DEFAULT 0,
  correct_count INTEGER NOT NULL DEFAULT 0,
  score INTEGER NOT NULL DEFAULT 0,
  xp_awarded INTEGER NOT NULL DEFAULT 0,
  best_streak INTEGER NOT NULL DEFAULT 0,
  accuracy REAL,
  avg_response_ms REAL,
  fastest_response_ms REAL,
  config_json TEXT NOT NULL DEFAULT '{}',
  summary_json TEXT NOT NULL DEFAULT '{}',
  client_version TEXT,
  sync_state TEXT NOT NULL DEFAULT 'local'
);
CREATE INDEX IF NOT EXISTS idx_sessions_profile ON sessions(profile_id, started_at DESC);
CREATE INDEX IF NOT EXISTS idx_sessions_day ON sessions(profile_id, substr(started_at,1,10));

CREATE TABLE IF NOT EXISTS attempts (
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
  chapter_id TEXT,
  topic_id TEXT,
  created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_attempts_session ON attempts(session_id, seq);
CREATE INDEX IF NOT EXISTS idx_attempts_question ON attempts(question_id, is_correct);
CREATE INDEX IF NOT EXISTS idx_attempts_topic ON attempts(profile_id, topic_id, created_at DESC);

CREATE TABLE IF NOT EXISTS mistakes (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  profile_id TEXT NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
  question_id TEXT NOT NULL REFERENCES questions(id) ON DELETE CASCADE,
  chapter_id TEXT,
  topic_id TEXT,
  question_type TEXT,
  wrong_count INTEGER NOT NULL DEFAULT 1,
  correct_since_count INTEGER NOT NULL DEFAULT 0,
  last_wrong_at TEXT NOT NULL,
  resolved INTEGER NOT NULL DEFAULT 0,
  UNIQUE (profile_id, question_id)
);
CREATE INDEX IF NOT EXISTS idx_mistakes_open ON mistakes(profile_id, resolved, last_wrong_at DESC);

CREATE TABLE IF NOT EXISTS topic_mastery (
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

CREATE TABLE IF NOT EXISTS srs_cards (
  profile_id TEXT NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
  question_id TEXT NOT NULL REFERENCES questions(id) ON DELETE CASCADE,
  state TEXT NOT NULL DEFAULT 'new',
  interval_days REAL NOT NULL DEFAULT 0,
  ease REAL NOT NULL DEFAULT 2.5,
  lapses INTEGER NOT NULL DEFAULT 0,
  repetitions INTEGER NOT NULL DEFAULT 0,
  due_at TEXT NOT NULL DEFAULT (datetime('now')),
  last_reviewed_at TEXT,
  PRIMARY KEY (profile_id, question_id)
);
CREATE INDEX IF NOT EXISTS idx_srs_due ON srs_cards(profile_id, due_at);

CREATE TABLE IF NOT EXISTS personal_bests (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  profile_id TEXT NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
  scope TEXT NOT NULL,
  scope_key TEXT NOT NULL,
  metric TEXT NOT NULL,
  value REAL NOT NULL,
  session_id TEXT REFERENCES sessions(id) ON DELETE SET NULL,
  achieved_at TEXT NOT NULL DEFAULT (datetime('now')),
  UNIQUE (profile_id, scope, scope_key, metric)
);
CREATE INDEX IF NOT EXISTS idx_pb_profile ON personal_bests(profile_id, scope, metric);

CREATE TABLE IF NOT EXISTS xp_events (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  profile_id TEXT NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
  amount INTEGER NOT NULL,
  reason TEXT NOT NULL,
  session_id TEXT REFERENCES sessions(id) ON DELETE SET NULL,
  created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_xp_profile ON xp_events(profile_id, created_at DESC);

CREATE TABLE IF NOT EXISTS badges (
  id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  description TEXT NOT NULL,
  icon TEXT,
  criterion_json TEXT NOT NULL DEFAULT '{}'
);

CREATE TABLE IF NOT EXISTS badge_awards (
  profile_id TEXT NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
  badge_id TEXT NOT NULL REFERENCES badges(id) ON DELETE CASCADE,
  awarded_at TEXT NOT NULL DEFAULT (datetime('now')),
  PRIMARY KEY (profile_id, badge_id)
);

CREATE TABLE IF NOT EXISTS session_events (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  session_id TEXT NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
  profile_id TEXT NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
  kind TEXT NOT NULL,
  payload_json TEXT NOT NULL DEFAULT '{}',
  created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS leaderboard_entries (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  scope TEXT NOT NULL,
  day TEXT NOT NULL,
  profile_id TEXT NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
  display_name TEXT NOT NULL,
  mode_key TEXT,
  score INTEGER NOT NULL,
  accuracy REAL,
  xp_delta INTEGER NOT NULL DEFAULT 0,
  created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_lb_scope ON leaderboard_entries(scope, day, score DESC);

CREATE TABLE IF NOT EXISTS schema_version (
  version INTEGER PRIMARY KEY,
  name TEXT NOT NULL,
  applied_at TEXT NOT NULL DEFAULT (datetime('now'))
);
