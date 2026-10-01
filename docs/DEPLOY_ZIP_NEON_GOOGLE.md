# Deploy guide — zip, Neon, and Google sign-in

Written for your setup: Linux PC, the repo already on GitHub, the service already
running on Render. Follow the parts you need.

**Contents**

1. Where the zip is, and whether you even need it
2. Deploying the new question bank
3. Connecting Neon (the database)
4. Connecting Google sign-in
5. Checking it all worked

---

## 1. Where the zip is

> **Getting a zip live?** Do not copy files around by hand.
> `./scripts/deploy.sh --zip <the zip>` does it safely and refuses to run if the
> zip is older than your checkout — which would delete newer work. Setup is in
> [`docs/ONE_COMMAND_DEPLOY.md`](ONE_COMMAND_DEPLOY.md).

```
/home/user/revisex-deploy.zip
```

That is the sandbox path. To get it onto your own computer, use the download
button next to it in the file list — it lands in your normal Downloads folder.

**It contains 227 files, 723 KB**, and it is built from the committed tree, so it
holds everything: the full 12,743-question bank, the generators, the competency
items, the Dockerfile and `render.yaml`.

I verified it by extracting it to an empty folder and running the seeder from
there. It produced 12,743 questions with 0 errors. So the zip is complete.

> The two zips that were sitting there before were both **stale**. They were built
> at 11:53 and earlier, before any of this session's work, and contained the old
> 5,034-question bank with none of the new physics, chemistry or competency files.
> I deleted both and replaced them with this one. If you had downloaded either of
> those earlier, throw it away.

### You probably do not need the zip

This is the part worth reading before you do anything else.

**Render deploys from GitHub, not from a zip.** Your service is already wired to
your repo, so the normal way to deploy is:

```
edit -> commit -> push to GitHub -> Render rebuilds by itself
```

The zip is only useful if you want to:
- move the project to a different computer,
- hand it to someone,
- or upload it somewhere that asks for a file rather than a repo.

For getting the new questions live, **skip the zip entirely and go to section 2.**

---

## 2. Deploying the new question bank

### The short version

Once you have done the one-time setup in
[`docs/ONE_COMMAND_DEPLOY.md`](ONE_COMMAND_DEPLOY.md), deploying is one command
run from your repository folder:

```bash
./scripts/deploy.sh
```

or, if you would rather apply a zip first:

```bash
./scripts/deploy.sh --zip ~/revisex-deploy.zip
```

That commits, pushes, triggers the Render rebuild and then reports whether the
new question count actually went live. Run `./scripts/deploy.sh --status` at any
time to see what the site is serving right now without changing anything. The
rest of this section is the manual version, which is worth reading once so you
know what the script is doing on your behalf.

### The manual version

All the work is committed locally. Your GitHub login lives on your computer, not
in this sandbox, so the push has to happen on your machine.

### Step 2.1 — Push

Open a terminal on your Linux PC:

```bash
cd ~/path/to/ReviseX
git status
```

You should see it is on branch `main` with nothing to commit. Then:

```bash
git push origin main
```

If it asks for a password, it wants a **personal access token**, not your GitHub
password. Create one at GitHub → **Settings** → **Developer settings** →
**Personal access tokens** → **Tokens (classic)** → **Generate new token**, tick
the `repo` scope, and paste the token as the password.

### Step 2.2 — Let Render rebuild

1. Open the Render dashboard and click your **revisex** service.
2. If it says **Building** or **Deploying**, it has already noticed the push. Wait.
3. If it says **Live** and nothing is happening, click **Manual Deploy** →
   **Deploy latest commit**.

Watch the log. A successful boot ends with something like:

```
INFO  leap: Content ready: 12743 questions (12743 new, 0 updated), 36 modes in ...
INFO:  Uvicorn running on http://0.0.0.0:8000
```

The number **12743** is the one to check for.

### Step 2.3 — You do NOT need to seed Neon by hand

This is the bit that is easy to get wrong, so the app does it for you.

On every startup the backend takes a fingerprint of the content **and** the
generator code, and compares it with the fingerprint it stored last time. If they
differ, it re-imports the whole bank.

You will see one of two lines in the log:

```
leap: Content ready: 12743 questions (12743 new, 0 updated), ...   <- what you want
leap: Content unchanged (fingerprint ...) - skipped reseed          <- nothing changed
```

The first line means it worked. If you get the second line on this deploy, the
commit did not arrive — go back to step 2.1.

### Step 2.4 — Your account survives

Re-seeding only writes to **content** tables: subjects, branches, chapters,
topics, facts, questions. It never deletes profiles, users, sessions, attempts,
mistakes, streaks, XP or friendships.

Where a question's id changed from an older version, the old row is marked
`archived` rather than deleted. That matters: `attempts`, `mistakes` and
`srs_cards` cascade on delete, so deleting a question would erase the history
attached to it. Archived questions vanish from quizzes and stay in the database.

Your profile `sayan` and its history carry across untouched.

---

## 3. Connecting Neon

Render needs to know where your database is. It reads one setting:
`DATABASE_URL`.

### Step 3.1 — Get the connection string

1. Go to <https://console.neon.tech> and sign in.
2. Click your project (the one whose name is in the host `ep-calm-night-...`).
3. Find the **Connection Details** panel — usually at the top of the dashboard,
   or under **Dashboard → Connect**.
4. Copy the **Pooled connection** string, not the direct one. It looks like:

   ```
   postgresql://neondb_owner:PASSWORD@ep-xxxx-pooler.c-3.ap-southeast-1.aws.neon.tech/neondb?sslmode=require
   ```

   The word **pooler** in the host is what tells you it is the pooled one. Use
   pooled because the free plan allows few direct connections and each cold start
   opens several.

> **Rotate the password first if this database is shared.** The old password was
> pasted into a chat, so treat it as exposed. In Neon: **Roles** →
> `neondb_owner` → **Reset password**. Then copy the fresh string. Do this
> *before* pasting it into Render so you only do the round trip once.

### Step 3.2 — Tell Render

1. Render dashboard → your **revisex** service.
2. Left sidebar → **Environment**.
3. Find the row named `DATABASE_URL`.
4. Paste the Neon string into its **Value** box.
5. Click **Save changes**.
6. Render will offer to redeploy — accept it, or go to **Manual Deploy** →
   **Deploy latest commit**.

That is the whole connection. There is no separate "link" step and no password to
type anywhere else.

### Step 3.3 — Confirm it took

Open this in a browser, using your own Render URL:

```
https://YOUR-SERVICE.onrender.com/api/health
```

You want to see:

```json
{
  "backend": "postgresql",
  "host": "ep-....neon.tech",
  "ssl": "require",
  "questions": 12743
}
```

Three things to check:

- `"backend": "postgresql"` — if it says `"sqlite"`, Render did not receive
  `DATABASE_URL` or it has a stray space in it. Fix it and redeploy.
- the `host` should be your Neon host, not blank.
- `questions` should read above 12,000.

### Common Neon problems

**It says `sqlite`.** The variable name is wrong, or the value has a space or a
newline. Re-paste it, save, redeploy.

**It connects but the bank is small.** The reseed fingerprint matched, so it
skipped. This only happens if the deploy did not pick up the new commit.

**"too many connections".** You copied the direct string instead of the pooled
one. Redo step 3.1 and look for `pooler` in the host.

---

## 4. Connecting Google sign-in

The app works without this. Until it is set up, the "Continue with Google"
button simply does not appear, because the server reports Google as disabled.

You need three settings: a **client id** and a **client secret** from Google, and
your public URL so the app can tell Google where to come back to.

### Step 4.1 — Create the Google credentials

1. Go to <https://console.cloud.google.com> and sign in.
2. Top bar → project picker → **New Project**. Name it something like
   `ReviseX`, and create it. Make sure it is then selected.
3. Left menu → **APIs & Services** → **OAuth consent screen**.
   - User type: **External**. Click **Create**.
   - App name: `ReviseX`. Support email: yours.
   - Developer contact email: yours.
   - Save and continue through the remaining steps. You do not need to add scopes
     for basic sign-in.
   - **Publishing status**: leave it as **Testing** for now, and under **Test
     users** add the Google address you will sign in with. While an app is in
     Testing only those listed addresses can use it. This is fine for you and a
     few friends; publish it later to open it up.
4. Left menu → **APIs & Services** → **Credentials**.
5. **Create Credentials** → **OAuth client ID**.
6. Application type: **Web application**. Name: `ReviseX web`.
7. Under **Authorised redirect URIs**, click **Add URI** and paste **exactly**:

   ```
   https://YOUR-SERVICE.onrender.com/api/auth/google/callback
   ```

   Replace `YOUR-SERVICE.onrender.com` with your real Render hostname. Note the
   two details people get wrong: the path ends in **`/callback`**, and it sits
   under **`/api`**. No trailing slash.
8. Click **Create**. A box appears with your **Client ID** and **Client secret**.
   Copy both. There is no way to view the secret again later.

### Step 4.2 — Give them to Render

Back in Render → your service → **Environment**, set these three:

| Key | Value |
|---|---|
| `GOOGLE_CLIENT_ID` | the client id, looks like `1234567890-abc.apps.googleusercontent.com` |
| `GOOGLE_CLIENT_SECRET` | the secret, looks like `GOCSPX-...` |
| `PUBLIC_BASE_URL` | `https://YOUR-SERVICE.onrender.com` — **no trailing slash** |

Then **Save changes** and redeploy.

`PUBLIC_BASE_URL` is used to work out the redirect URI, and the result has to
match what you typed into Google character for character. If they disagree, Google
shows `redirect_uri_mismatch` and refuses.

### Step 4.3 — Confirm it took

Open, with your own URL:

```
https://YOUR-SERVICE.onrender.com/api/auth/google/status
```

It should say `"enabled": true`. If it says `false`, one of the two credentials is
missing or has a stray space.

Then open the sign-in page. The **Continue with Google** button should now be
there, below the password form.

### Was the button already showing before you set this up?

Then `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET` were already set from an
earlier attempt. In that case just check the redirect URI in Google Cloud matches
your current Render hostname — Render hostnames can change, and a stale one
produces exactly the `redirect_uri_mismatch` error above.

### Common Google problems

**`redirect_uri_mismatch`.** The URI in Google Cloud and the one the app derives
disagree. They must match exactly: same scheme (`https`), same host, no trailing
slash, path `/api/auth/google/callback`. `PUBLIC_BASE_URL` is the usual culprit —
check it has no trailing slash.

**The button is missing.** `google/status` is returning `false`. In Render →
Environment, confirm both credentials are set and saved, then redeploy.
Environment variables are only read at startup.

**"Access blocked: this app has not completed verification".** You are signed in
with a Google address that is not on the Test users list. Add it in the OAuth
consent screen, or publish the app.

**Sign-in succeeds but lands back on the sign-in page.** The redirect URI points
at an old hostname. Render can change it; re-copy the current one from the
service page and update Google Cloud.

---

## 5. Final check

Work through this on the deployed site:

1. `/api/health` says `postgresql` and a question count above 12,000.
2. The Render log shows `Content ready: 12743 questions`.
3. `/api/auth/google/status` says `enabled: true`.
4. The sign-in page shows **12,743 questions** in its description line, and the
   Google button is visible.
5. Sign in with your existing account. Your streak and XP are still there.
6. Start a Science test and confirm a question loads.

If the question count on the sign-in page still shows the old figure, that is a
cached response in your browser. Hard-refresh with `Ctrl` + `Shift` + `R`.

---

## If you would rather not use GitHub at all

You can deploy the zip directly, but it is more work and you lose automatic
deploys. The short version: unzip it, `git init` inside it, create a new GitHub
repo, and push that. Every future change then needs the same manual step. Keeping
your existing repo and pushing to it is simpler in every way.

---

## A note on the password

Never commit a real `DATABASE_URL`, `GOOGLE_CLIENT_SECRET` or Neon password into
the repo. `render.yaml` deliberately uses `sync: false` for all of them, which
makes Render prompt for the value instead of storing it in the file. Keep it that
way, and keep `~/.neon_url` on your own machine only — it is already in
`.gitignore`.
