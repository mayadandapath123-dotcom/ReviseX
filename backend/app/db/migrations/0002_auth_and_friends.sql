-- Accounts, sessions tokens and friends.
--
-- Written in the same dialect as 0001_init.sql so the Postgres adapter in
-- app/db/connection.py translates it: INTEGER PRIMARY KEY AUTOINCREMENT and
-- DEFAULT (datetime('now')) are both rewritten on the fly.
--
-- A user owns exactly one profile. `profiles` keeps holding all learning data
-- so nothing downstream had to change; `user_id` is the new link. It stays
-- nullable so a purely local, account-free install keeps working.

CREATE TABLE IF NOT EXISTS users (
  id TEXT PRIMARY KEY,
  username TEXT NOT NULL UNIQUE,
  password_hash TEXT NOT NULL,
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  last_login_at TEXT,
  is_active INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS auth_tokens (
  token_hash TEXT PRIMARY KEY,
  user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  expires_at TEXT NOT NULL,
  last_seen_at TEXT
);

CREATE INDEX IF NOT EXISTS idx_auth_tokens_user ON auth_tokens(user_id);
CREATE INDEX IF NOT EXISTS idx_auth_tokens_expires ON auth_tokens(expires_at);

-- Friend requests: one row per invitation, accepted rows are mirrored into
-- friendships so lookups never have to filter on status.
CREATE TABLE IF NOT EXISTS friend_requests (
  id TEXT PRIMARY KEY,
  from_user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  to_user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  status TEXT NOT NULL DEFAULT 'pending',
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_friend_requests_to ON friend_requests(to_user_id, status);
CREATE INDEX IF NOT EXISTS idx_friend_requests_from ON friend_requests(from_user_id, status);

-- user_a is always the lexicographically smaller id, which makes the pair
-- unique in one direction only and removes the need to check both ways.
CREATE TABLE IF NOT EXISTS friendships (
  user_a TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  user_b TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  PRIMARY KEY (user_a, user_b)
);

CREATE INDEX IF NOT EXISTS idx_friendships_b ON friendships(user_b);

-- Link the existing learning data to an account. Nullable and unindexed at
-- first: a local install has no users at all, and migrations run exactly once
-- (tracked in schema_version) so a bare ALTER is safe on both backends.
ALTER TABLE profiles ADD COLUMN user_id TEXT;
CREATE INDEX IF NOT EXISTS idx_profiles_user ON profiles(user_id);
