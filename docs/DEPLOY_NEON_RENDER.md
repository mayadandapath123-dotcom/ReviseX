# Deploying ReviseX — Neon + Render (beginner guide, Linux)

Everything below runs in your normal terminal on your Linux PC. Copy each
command exactly. Nothing here needs admin rights except where `sudo` is shown.

Total time: about 20 minutes. Cost: ₹0.

---

## What you are about to build

| Piece | What it does | Where it lives |
|---|---|---|
| **Neon** | The Postgres database — accounts, passwords, progress, streaks, friends | neon.tech (free) |
| **Render** | Runs the app (API + website together) | render.com (free) |
| **GitHub** | Your code, which Render reads to build the app | already done |

Render builds one Docker image that serves **both** the API and the website on
one address. That matters: the website calls `/api` with a relative path, so
there is no cross-origin setup and no second service to keep in sync.

---

## Step 0 — Get your local code up to date on GitHub

The auth, friends and Postgres work was committed locally. Push it.

```bash
cd ~/revise
git status
```

If it says `nothing to commit, working tree clean`, continue. If it lists
changes, run:

```bash
git add -A
git commit -m "sync"
```

Then push:

```bash
git push origin main
```

**Confirm on GitHub:** open https://github.com/mayadandapath123-dotcom/ReviseX
and check the latest commit message reads *"Point the deploy config at Neon
Postgres"*. If it does not, the push did not happen — re-run it and read the
error.

While you are there: **Settings → General → Danger Zone → Change visibility →
Private**, if you have not already.

---

## Step 1 — Create the Neon database

1. Go to **https://neon.tech** and click **Sign Up**.
2. Sign up with your GitHub account (fastest — no new password to remember).
3. It asks you to create a project. Fill in:
   - **Project name:** `revisex`
   - **Database name:** `revisex`
   - **Region:** pick **Asia Pacific (Singapore)** — closest to Delhi, and it
     matters because Render will talk to this database on every request.
4. Click **Create project**.
5. Neon immediately shows a **Connection Details** panel. Look for the
   connection string. It looks like:

   ```
   postgresql://neondb_owner:npg_abc123XYZ@ep-cool-name-123456-pooler.ap-southeast-1.aws.neon.tech/neondb?sslmode=require
   ```

6. **Copy that whole string** into a text file on your PC right now. You will
   paste it twice, and Neon hides the password after you leave the page.

```bash
nano ~/neon-url.txt
```

Paste it, then save with `Ctrl+O`, `Enter`, `Ctrl+X`.

> **Important notes**
> - Use the string ending in `-pooler` if Neon gives you a choice between
>   *Pooled* and *Direct*. Pooled shares connections, which the free Render
>   plan needs — it allows very few simultaneous connections and a cold start
>   opens several.
> - Keep `?sslmode=require` at the end. Do not remove it.
> - This string **is a password**. Never paste it into GitHub, a chat, or a
>   screenshot.
> - If the database name shown is `neondb` rather than `revisex`, that is fine
>   — use whatever Neon gives you.

**Do not create any tables.** The app runs its own migrations and seeds all
12,743 questions automatically the first time it starts. An empty database is
exactly what it expects.

---

## Step 2 — Create a Render account

1. Go to **https://render.com** → **Get Started for Free**.
2. Sign up with **GitHub** (this is important — it lets Render read your
   private repo without you copying code anywhere).
3. It will ask for permission to access your repositories. Choose
   **Only select repositories** and pick **ReviseX**. That is safer than
   granting access to all of them.

---

## Step 3 — Deploy with the Blueprint

Your repo contains a file called `render.yaml`. Render reads it and creates the
service with the right settings automatically — you do not have to configure
Docker, ports, health checks or build commands by hand.

1. In the Render dashboard, click **New +** (top right).
2. Click **Blueprint**.
3. Click **Connect account** next to GitHub if asked, then select your
   **ReviseX** repository.
4. Click **Apply** / **Create Blueprint**.
5. Render shows a form for the environment variables it could not fill in
   itself. You will see **`DATABASE_URL`** with an empty box.
   → **Paste your Neon connection string** from `~/neon-url.txt`.
6. Leave `CORS_ORIGINS` **empty**. The app is single-origin, so it is unused.
7. Click **Apply** / **Create**.

Render now builds the Docker image. Watch the log panel.

---

## Step 4 — Wait for the first build (this one is slow — normal)

The first deploy does four things in order:

1. Builds the React website (`npm ci && npm run build`)
2. Installs the Python dependencies
3. Runs every database migration against your empty Neon database
4. **Seeds the full question bank and 36 test modes into Neon**

Expect **3 to 5 minutes**, most of it the Docker build. Step 4 was measured
against a real Neon database in Singapore: **81 seconds**.

Writes are batched, which is why that is 81 seconds and not an hour. Seeding
row by row means one network round trip per row, and at ~180 ms each, 30,000
rows would take 25 minutes and still not finish. The seed reads what already
exists in one query and flushes inserts as single batched statements.

**Success looks like this in the log** (first boot):

```
INFO  leap: Applied migrations: 0001_init, 0002_auth_and_friends, 0003_content_state
INFO  leap: Content ready: 12743 questions (12743 new, ...), 36 modes in 81000 ms
INFO  Uvicorn running on http://0.0.0.0:8000
==> Your service is live 🎉
```

On **later** boots you should instead see this, which is the good case:

```
INFO  leap: Content unchanged (fingerprint 1f402e733a07) - skipped reseed in 1702 ms
```

That line means startup took 1.7 seconds instead of 74. The app hashes its
content and generator code at boot and skips the whole re-seed when nothing
changed - which is what makes the free tier's cold starts tolerable.

When the status dot turns **Live**, copy your new URL — something like
`https://revisex.onrender.com`.

---

## Step 5 — Test it properly

Open your URL in a browser. Do these in order; each one tests a different layer.

| # | Do this | What it proves |
|---|---|---|
| 1 | The sign-in / create-account screen appears | Website and API are served together |
| 2 | Click **Create account**, username `sayan`, password of 6+ characters | Accounts write to Neon |
| 3 | You land on the dashboard | Your profile was created server-side |
| 4 | Play one test and finish it | Questions seeded correctly |
| 5 | Check XP and streak appeared | Scoring writes are persisting |
| 6 | Close the tab, reopen the URL | **Session survived** — this is the real test |
| 7 | Click **Friends**, add a classmate's username | Friend requests work |
| 8 | Open `/api/health` in a new tab | Must say `"backend": "postgresql"`, your Neon host, `"ssl": "require"`, and a `"questions"` count above 12,000 — **not** `"sqlite"` |

Step 6 is the one that would have failed before this work: progress used to
live in the browser, so it vanished when the database reset. It now lives in
Neon against your account.

---

## Step 6 — Free tier things to know (not bugs)

**The app goes to sleep.** After about 15 minutes with no visitors, Render
stops the container to save resources. The next person to open it waits
**roughly 30–50 seconds** for the container to start, during which the browser
looks stuck. The app's own startup adds only ~2 seconds on top, because it
detects that its content has not changed and skips re-seeding. Without that
check every wake-up would cost an extra 74 seconds.
After that it is fast. This is a Render free-tier rule and cannot be turned off
without paying. If a friend says "it didn't load", tell them to wait a minute
and refresh.

**Progress is safe.** Sleep does not touch Neon. Only your Render *filesystem*
is wiped, and nothing important is stored there any more.

**Neon free tier** also pauses your database after about a week of no activity.
Same story: the first request wakes it, slowly.

**To check it is awake** before sharing the link, open it yourself once and
wait for the dashboard.

---

## Troubleshooting

**Build fails at `npm ci`**
`package-lock.json` is out of step with `package.json`. Locally:
```bash
cd ~/revise/frontend && npm install && git add -A && git commit -m "lockfile" && git push
```
Then in Render: **Manual Deploy → Deploy latest commit**.

**`/api/health` says `"backend": "sqlite"`**
Render did not receive `DATABASE_URL`, so the app fell back to a local file that
is wiped on every restart. In Render: **Settings → Environment**, confirm
`DATABASE_URL` exists and has no stray spaces, then **Manual Deploy → Deploy
latest commit**. This is the single most common mistake and the health endpoint
exists to catch it.

**App starts but the log shows `Content seeding failed`**
Almost always a wrong `DATABASE_URL`. In Render: **Settings → Environment**,
check the value has no leading/trailing space and still ends with
`?sslmode=require`. Fix it, then **Manual Deploy → Deploy latest commit**.

**`500` errors, log mentions `connection` or `timeout`**
Neon's free tier allows limited connections. Make sure you used the **pooled**
connection string (host contains `-pooler`).

**The page loads but shows no questions**
The seed did not finish. In Render's **Shell** tab (or by redeploying) check
the log for the `Content ready:` line and read its question count. If absent, redeploy.

**"Sign in to use this feature" on the Friends page**
Correct behaviour — friends require an account. Sign in or create one.

**You locked yourself out of your own account**
There is no password reset (no email service is configured). Ask me and I will
add a reset flow, or reset the row directly in Neon's SQL editor.

---

## Changing the app later

```bash
cd ~/revise
# ...edit files...
git add -A && git commit -m "describe the change" && git push origin main
```

Render watches the repo and redeploys automatically within a minute or two.
You do not need to touch the Render dashboard.

**Never** put a real `DATABASE_URL` or password in a file you commit. Render
stores secrets separately, which is why `render.yaml` says `sync: false` for
that variable.

---

## Where your data lives

- **Neon** — `users` (username + PBKDF2 password hash), `auth_tokens`,
  `profiles` (XP, level, streak), `friend_requests`, `friendships`, plus all
  answers, attempts, mistakes and mastery scores.
- **Nothing personal in the browser** except the session token in
  localStorage, which is how you stay signed in between visits.
- Passwords are stored as `pbkdf2_sha256$210000$salt$hash`. They cannot be
  read back, including by me. If a student forgets one, it must be reset, not
  recovered.
