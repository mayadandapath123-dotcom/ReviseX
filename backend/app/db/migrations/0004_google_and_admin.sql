-- Google sign-in, account claiming, presence tracking and admin audit.
--
-- EVERY statement here is additive. Deploys must never cost a student their
-- history, so nothing in this file drops, renames or rewrites a column that
-- already holds data. New columns are nullable or carry a default, which means
-- they apply cleanly to rows that already exist.
--
-- Written in SQLite dialect; the Postgres adapter translates it. Note the
-- deliberate avoidance of two things SQLite cannot do: ALTER COLUMN (so
-- password_hash keeps its NOT NULL and Google-only accounts get a sentinel
-- instead) and inline UNIQUE on ADD COLUMN (so uniqueness is a separate
-- partial index, which also lets many rows stay NULL).

-- Google identity. `sub` is the stable pairwise-independent id Google returns;
-- it never changes for a given (account, Google project) pair, unlike email.
ALTER TABLE users ADD COLUMN google_sub TEXT;
ALTER TABLE users ADD COLUMN google_email TEXT;

-- A partial unique index: two accounts cannot claim the same Google identity,
-- but any number of accounts may have no Google identity at all (NULL).
CREATE UNIQUE INDEX IF NOT EXISTS idx_users_google_sub ON users(google_sub) WHERE google_sub IS NOT NULL;

-- Which method created the account, for the admin panel and for deciding
-- whether unlinking Google would lock someone out.
ALTER TABLE users ADD COLUMN provider TEXT NOT NULL DEFAULT 'password';

-- Presence. Updated at most once a minute per user (throttled in code) so it
-- does not add a write to every request against a remote database.
ALTER TABLE users ADD COLUMN last_seen_at TEXT;

ALTER TABLE users ADD COLUMN is_admin INTEGER NOT NULL DEFAULT 0;

CREATE INDEX IF NOT EXISTS idx_users_last_seen ON users(last_seen_at);

-- Every admin entry into another person's account is recorded here and never
-- deleted by application code. Impersonation is a support tool, and a support
-- tool that leaves no trace is indistinguishable from abuse.
CREATE TABLE IF NOT EXISTS admin_audit (
  id TEXT PRIMARY KEY,
  admin_user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  action TEXT NOT NULL,
  target_user_id TEXT REFERENCES users(id) ON DELETE SET NULL,
  detail TEXT,
  created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_admin_audit_created ON admin_audit(created_at);
CREATE INDEX IF NOT EXISTS idx_admin_audit_target ON admin_audit(target_user_id);

-- OAuth CSRF state. Short-lived, single-use, and stored server side so a
-- callback can be matched to the browser that started it.
CREATE TABLE IF NOT EXISTS oauth_states (
  state TEXT PRIMARY KEY,
  kind TEXT NOT NULL,
  user_id TEXT,
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  expires_at TEXT NOT NULL,
  consumed_at TEXT
);

CREATE INDEX IF NOT EXISTS idx_oauth_states_expires ON oauth_states(expires_at);
