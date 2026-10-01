# Beginner Guide — from zero to a live website

Written for someone who has never deployed anything. Follow it top to bottom.
Every step says **what to download**, **where to click**, and **what to paste**.

You will end up with:
1. The website running on your own PC (offline, free, private)
2. The same website on a public link you can send to anyone

Total time: about 45 minutes, most of it waiting for downloads.

---

## Part 0 — Get the project files onto your PC

The code currently lives in this chat's workspace, not on your computer.

**Download the `revise` folder** from the workspace file panel (the folder that
contains `backend`, `frontend`, `docs`, `scripts`, `README.md`). Save it somewhere
simple with no spaces in the path, for example:

```
C:\revise          (Windows)
/Users/you/revise  (Mac)
```

> Avoid `C:\Users\Your Name\My Documents\revise` — spaces in the path cause
> confusing errors later.

You do **not** need the `backend/data` folder or any `node_modules` folder if they
came along. Both get recreated automatically.

---

## Part 1 — Install three programs

You need exactly three. All free.

### 1a. Python

- **Download:** https://www.python.org/downloads/
- Click the big yellow **"Download Python 3.x.x"** button.
- Run the installer.

> ⚠️ **THE MOST IMPORTANT CHECKBOX ON THIS ENTIRE PAGE**
> On the very first installer screen, tick
> **"Add python.exe to PATH"** at the bottom, *before* clicking Install Now.
> If you forget, nothing will work and the error message will not tell you why.

- Verify: open a terminal and type `python --version`
  (on Windows, if that fails, try `py --version`).
  You want `Python 3.11` or higher.

### 1b. Node.js

- **Download:** https://nodejs.org/
- Click the **LTS** button (not "Current"). LTS = the stable one.
- Run the installer, accept all defaults, click Next until finished.
- Verify: `node --version` → should print `v18` or higher (v20/v22 is fine).

### 1c. Git

- **Download:** https://git-scm.com/downloads
- Run the installer, accept all defaults.
- Verify: `git --version`

### How to open a terminal

| System | How |
|---|---|
| Windows | Press `Win` key, type **PowerShell**, press Enter. (Or "cmd".) |
| Mac | Press `Cmd + Space`, type **Terminal**, press Enter |

Then move into your project folder:

```
cd C:\revise            (Windows)
cd /Users/you/revise    (Mac)
```

Check you're in the right place:

```
dir          (Windows)
ls           (Mac)
```

You should see `backend`, `frontend`, `docs`, `scripts`, `README.md`.

---

## Part 2 — Run it on your PC

With your terminal inside the `revise` folder, type:

```
python scripts/dev.py
```

(Windows, if that says python isn't recognised: `py scripts/dev.py`)

**What happens:** it creates a virtual environment, installs Python packages,
installs Node packages, builds the database, loads 2,276 questions, and starts two
servers. First run takes 1–3 minutes and prints a lot of text — that is normal.

When you see lines mentioning `http://localhost:5173` and `Uvicorn running on
http://0.0.0.0:8000`, open your browser and go to:

### 👉 http://localhost:5173

Create a profile (any nickname, no email, no password) and play.

**To stop it:** click the terminal window and press `Ctrl + C`.
**To start it again later:** open terminal, `cd` into the folder, run the same command.
Second time takes ~5 seconds.

### Where your progress is saved

One file: `backend/data/revise.sqlite3`. Copy it to back up progress; delete it to
start over. The questions regenerate themselves, so you only ever lose scores.

---

## Part 3 — Put the code on GitHub

You said your GitHub is already connected to Render — good, that is the hard part.

1. Go to https://github.com/new
2. **Repository name:** `revise` (or anything)
3. Keep it **Private** if you don't want strangers seeing it yet
4. Do **NOT** tick "Add a README" — you already have one
5. Click **Create repository**

GitHub then shows a page with commands. In your terminal, inside the `revise`
folder, paste these — replacing `YOUR-USERNAME` with your actual GitHub username:

```
git add -A
git commit -m "first upload"
git branch -M main
git remote add origin https://github.com/YOUR-USERNAME/revise.git
git push -u origin main
```

It will pop up a browser window asking you to sign in to GitHub. Do that.

Refresh the GitHub page — you should now see all the files.

> **If `git commit` complains about your name/email**, paste these two first:
> ```
> git config --global user.email "you@example.com"
> git config --global user.name "Your Name"
> ```

> **If it says "remote origin already exists"**, run
> `git remote set-url origin https://github.com/YOUR-USERNAME/revise.git` instead.

---

## Part 4 — Put it on the internet (Render)

This uses the **one service** setup: Render runs both the API and the website
together, so there is no CORS, no second site, no frontend configuration.

1. Go to https://dashboard.render.com
2. Click **New +** → **Blueprint**
   (If you don't see Blueprint, click **New +** → **Web Service** and jump to step 6)
3. Choose your `revise` repository. If it isn't listed, click
   **Connect account** / **Configure account** and allow Render to see it.
4. Render finds `render.yaml` automatically and shows one service called `revisex`.
5. Click **Apply** / **Create**.

### ⚠️ One thing to delete if you are on the free plan

The `render.yaml` file asks for a **persistent disk** (so student progress survives
restarts). **Render's free plan does not allow disks** and the deploy will fail with
an error about disks not being supported.

If that happens, on GitHub open `render.yaml`, click the pencil icon, and **delete
these four lines at the bottom**:

```yaml
    disk:
      name: revisex-data
      mountPath: /data
      sizeGB: 1
```

Click **Commit changes**. Render will redeploy automatically.

Consequence: on the free plan, scores and progress reset whenever the site restarts
or redeploys. The 2,276 questions always come back on their own — only student
history is temporary. If you want history to stick, upgrade Render to Starter
(~$7/month) and put those lines back.

6. **Manual route** (if you used Web Service instead of Blueprint):
   - Runtime: **Docker**
   - Dockerfile path: `./Dockerfile`
   - Health check path: `/api/health`
   - Under **Environment**, add: `APP_ENV` = `production`, `DATA_DIR` = `/data`,
     `AUTO_APPROVE_AI_ITEMS` = `false`
   - Click **Create Web Service**

7. Wait 3–6 minutes for the build. You'll see it go **Build in progress** →
   **Deploying** → **Live**.

8. Click the URL Render gives you, e.g. `https://revisex.onrender.com`

**That's it — your site is public.**

### Free-tier quirk to expect

Render free services **go to sleep** after 15 minutes unused. The next visitor waits
about 50 seconds for it to wake up. That is normal and not a bug.

---

## Part 5 — Check it worked

Open your new URL and confirm:

- [ ] The profile screen appears; you can create a profile
- [ ] Dashboard shows subject tiles for **Science, Mathematics, Social Science**
- [ ] Science → Chemistry → a chapter → **1 Minute Sprint** starts and questions appear
- [ ] Maths Sprint serves number questions
- [ ] Answering wrongly puts items in **My mistakes**
- [ ] `https://YOUR-SITE/api/health` shows `{"status":"ok", ...}`

### If something is broken

| Symptom | Cause and fix |
|---|---|
| `python is not recognized` | You didn't tick "Add to PATH". Reinstall Python and tick it, or use `py` instead of `python` |
| `vite: not found` | Node packages missing. Run `cd frontend` then `npm install` |
| Port 5173 already in use | Something else is using it. Close it, or the app picks another port — read the URL it prints |
| Site loads but no questions | Backend still starting. Wait 30 s and refresh. Check `/api/health` |
| Render build fails mentioning disk | Delete the `disk:` block from `render.yaml` (Part 4 step 5) |
| Render says health check failed | Give it 2 minutes; the first boot builds the question bank. Check the **Logs** tab for the real error |
| Blank white page | Open browser DevTools (F12) → Console tab → screenshot the red text |

---

## Important: don't make it fully public yet

This app has **no login system**. Identity is just a nickname stored in the browser,
and profiles are addressed by a guessable ID. On a public URL, anyone who finds the
link could read or overwrite other people's progress.

Fine for:
- your own computer
- a link you share with family or a few classmates
- a classroom where everyone uses one machine

Not fine for:
- a real public launch with strangers

To make it launch-ready you need authentication, which is the next chunk of work.
Until then, keep the repo private and the URL unlisted.

Also note the content is **original questions written from the CBSE/NCERT syllabus** —
no textbook passages or copied question-bank material. Keep it that way if you add
more, especially before publishing.

---

## Quick reference

```
# run locally
cd revise
python scripts/dev.py

# wipe progress and start fresh
python scripts/dev.py --reset

# after changing code, redeploy to Render
git add -A
git commit -m "update"
git push
```

Render redeploys automatically on every push to `main`.
