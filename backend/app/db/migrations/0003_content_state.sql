-- Bookkeeping about the content load itself, not the content.
--
-- Booting used to re-derive and re-diff all 5,034 questions against the
-- database every single time. On a local file that is ~2s and invisible; on a
-- remote database it is ~74s of round trips, paid on every Render cold start.
-- Storing a fingerprint of the inputs lets boot skip the whole pass when
-- nothing that could change the output has changed.
CREATE TABLE IF NOT EXISTS content_state (
  key TEXT PRIMARY KEY,
  value TEXT NOT NULL,
  updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);
