# Deploying the current build

Everything is committed on your machine. Nothing here needs a password typed into
a chat, and nothing is pushed from the sandbox — your GitHub login lives on your
own computer, so the push runs there.

---

## What changed since the last deploy

| | Before | Now |
|---|---|---|
| Approved questions | 5,034 | **12,743** |
| Chapters under 100 questions | 6 | **0** |
| Competency items | 0 | **370** |
| Subjects | 3 | 3 |

The deployed site still shows the old bank. The next deploy brings it up to date
on its own — see step 3.

---

## Step 1 — Push from your computer

Open a terminal on your Linux machine and run these one at a time.

```bash
cd ~/path/to/ReviseX        # wherever you cloned the repo
git status
```

`git status` should say you are on branch `main` and there is nothing to
commit. If it lists modified files, run `git add -A` and then
`git commit -m "Local changes"` first.

```bash
git push origin main
```

If it asks for a username and password, the password is a **personal access
token**, not your GitHub password. If you do not have one saved, GitHub will
reject a plain password — create a token at GitHub → Settings → Developer
settings → Personal access tokens, give it `repo` scope, and paste that as the
password.

---

## Step 2 — Let Render redeploy

Render watches the `main` branch and rebuilds when new commits appear.

1. Open your Render dashboard.
2. Click the ReviseX service.
3. If the top of the page says **Building** or **Deploying**, it is already
   happening. Wait.
4. If it says **Live** and nothing is happening, click **Manual Deploy** →
   **Deploy latest commit**.

The build takes a few minutes. Watch the log; it ends with something like
`Uvicorn running on http://0.0.0.0:...`.

---

## Step 3 — The question bank updates itself

You do **not** need to run any seed command against Neon. This is the part that
is easy to get wrong by hand, so the app does it.

On every startup the backend hashes all the content JSON *and* all the generator
code together, and compares that hash with the one it stored in the database last
time. If anything differs, it re-imports the whole bank and stores the new hash.

In the Render log you will see one of two lines:

```
leap: Content unchanged (fingerprint 6db4b0d61fce) - skipped reseed
```

```
leap: Content ready: 12743 questions (12743 new, 0 updated), ...
```

The second line is what you want on this deploy. The first would mean the deploy
did not pick up the new commit — go back to step 1.

You can confirm from the log line itself: it prints the approved count. Look for
**12743**.

### Your account is not touched

Re-seeding only ever writes to content tables — subjects, branches, chapters,
topics, facts and questions. It does not delete profiles, users, sessions,
attempts, mistakes, streaks, XP or friendships.

The one thing it does to existing rows is *archive* questions whose id changed
from an earlier version. Archiving sets `status = 'archived'` rather than deleting
the row, because `attempts`, `mistakes` and `srs_cards` cascade on delete —
deleting a question would erase the history attached to it. Archived questions
disappear from quizzes and stay in the database.

Your profile `sayan` and its history carry across unchanged.

---

## Step 4 — Check it worked

Open the deployed site. On the sign-in screen the description line reads its
count from the server, so it should now say:

> **12,743 questions** across Science, Mathematics, Social Science, mapped to the
> CBSE 2025-26 curriculum.

If it still shows the old number, the browser is serving a cached config
response. Hard-refresh with `Ctrl` + `Shift` + `R`.

---

## If something goes wrong

**Render says `DATABASE_URL` is missing.** Settings → Environment, add it, then
Manual Deploy → Deploy latest commit. Environment variables are only applied when
a service is created from the blueprint; adding them later needs a redeploy.

**The log shows a migration or seed error.** The startup log names the file and
the question id. Paste that line and it can be traced to one item.

**The site loads but shows no questions.** Check that the log printed a question
count above zero. If it printed `0`, the content folder did not reach Render —
confirm `backend/content/` is committed and not listed in `.gitignore`.

---

## Rotating the Neon password

The Neon connection string was pasted into a chat earlier, so its password should
be treated as exposed. You do not have to do this now, but do it before the site
is shared with anyone.

1. Neon dashboard → your project → **Roles** (or **Connection Details**).
2. Reset the password for `neondb_owner`.
3. Copy the new connection string.
4. Render → your service → **Settings** → **Environment** → edit `DATABASE_URL`
   → paste the new string.
5. **Manual Deploy → Deploy latest commit.**

Update `~/.neon_url` on your own machine too, so your local tools still connect.
Never commit that file.
