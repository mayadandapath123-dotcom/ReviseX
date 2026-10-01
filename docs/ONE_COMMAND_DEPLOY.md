# Deploying with one command

`scripts/deploy.sh` puts the current code on the live site. Instead of jumping
between the terminal, the Render website and a browser tab to check whether it
worked, you run one command and it reports what happened.

You need to read this page once to copy a URL into a file. After that you only
ever run one command.

---

## First, the thing that surprises everyone

**Render cannot deploy a zip file.** There is no button anywhere in Render that
accepts an upload. Render builds the site by pulling code from your GitHub
repository. Every time.

So "deploy the zip" is really three steps, always in this order:

1. get the zip's files into the git working copy
2. push that to GitHub
3. ask Render to rebuild

`deploy.sh` does all three and then checks the live site to confirm the new
content actually arrived. The zip is just a convenient way to refresh the files;
the git push is what actually deploys.

If you have already pushed your latest commit from your own computer, you can
skip the zip entirely — `deploy.sh` will find nothing new to commit and will go
straight to pushing and rebuilding.

---

## Getting these scripts onto your computer

`scripts/deploy.sh` is new, and **your computer probably does not have it yet**.
That is not a mistake. Everything in the workspace is committed in the sandbox,
but the sandbox has no GitHub password, so nothing has been pushed. Your PC only
gets these files when you put them there.

Check first:

```bash
cd ~/ReviseX
ls scripts/
```

If `deploy.sh` is listed, you are done and can skip to the next section.

If it is not, extract the workspace zip over your project folder:

```bash
cd ~/ReviseX
unzip -o ~/Downloads/revisex-deploy.zip -d .
chmod +x scripts/deploy.sh
ls scripts/
```

`unzip -o` overwrites the files that are in the zip and leaves everything else
alone. The zip contains only files tracked in git, so it **cannot** touch your
local `backend/data/` database, your `frontend/dist/` build, or your `.env`.
Those are deliberately excluded. Your local history and settings are safe.

Adjust `~/Downloads/` to wherever your browser actually saved the zip. If you
are not sure, this finds it:

```bash
find ~ -name 'revisex-deploy.zip' 2>/dev/null
```

Once `ls scripts/` shows both `deploy.sh` and `sync_zip.py`, continue below. From
here on this is a normal git repository, and `deploy.sh` keeps it up to date on
its own.

---

## One-time setup

You need two things: `git` and a Render deploy hook URL.

### 1. Check the tools are installed

Open a terminal and run:

```bash
git --version
curl --version
python3 --version
unzip -v
```

Each line should print a version number. If `unzip` says **command not found**:

```bash
sudo apt update
sudo apt install unzip
```

Nothing else needs installing. The script uses only `git`, `curl`, `unzip`,
`python3` and the standard shell tools that Ubuntu already has. In particular it
does **not** need `rsync`.

### 2. Copy your Render deploy hook URL

1. Open <https://dashboard.render.com> and sign in.
2. Click your **revisex** service.
3. In the left-hand menu click **Settings**.
4. Scroll down to the **Deploy Hook** section.
5. Copy the URL. It looks like this:

   ```
   https://api.render.com/deploy/srv-abc123def456?key=Xy9ZzQ
   ```

**Treat this URL like a password.** Anyone who has it can ask Render to rebuild
your site. Do not paste it into a file inside the repository, into a screenshot,
or into a chat with anyone.

Render also offers a **Regenerate Hook** button on that same page. If the URL
ever leaks, click that button and the old URL stops working immediately.

### 3. Save the URL where the script looks for it

Run this on your computer, replacing the URL with yours. Keep the single quotes
exactly as shown — they stop the shell from eating the `?` and `&` characters:

```bash
echo 'https://api.render.com/deploy/srv-abc123def456?key=Xy9ZzQ' > ~/.render_deploy_hook
```

Then lock the file so only you can read it:

```bash
chmod 600 ~/.render_deploy_hook
```

The file lives in your home directory (`~`), **not** in the repository, so there
is no way for it to be committed and pushed to GitHub by accident.

### 4. Check it worked

```bash
./scripts/deploy.sh --status
```

This changes nothing. It just asks the live site what it currently has. You
should see something like:

```
==> What is live right now
    backend    postgresql
    host       ep-calm-night-azyrv5ye-pooler.c-3.ap-southeast-1.aws.neon.tech
    questions  12743
    profiles   2   accounts 1
    OK   the current bank is live (12743 questions)

    Google sign-in: yes
```

If you see a warning instead of `OK`, that is the script telling you the new
commit is not live yet. Read the line above it — it names the problem.

Render's free tier puts the site to sleep after about 15 minutes of no visitors.
The first request wakes it up and can take 30-60 seconds. If you run `--status`
and it says it could not reach the site, just run it again.

---

## The commands, from safest to broadest

### Look, without changing anything

```bash
./scripts/deploy.sh --status
```

Prints what the live site is serving right now. Never modifies anything. Use this
when you only want to know whether the deploy you did earlier actually landed.

### The normal deploy

```bash
./scripts/deploy.sh
```

1. shows any uncommitted files, commits them
2. pushes to GitHub
3. asks Render to rebuild
4. waits for the site to come back and confirms the question count

### Deploy from a zip

```bash
./scripts/deploy.sh --zip ~/revisex-deploy.zip
```

Same as above, but first it extracts the zip and makes your working copy match
it exactly. This is the command for "I was given a zip and I want it live."

There is a safety check here that will stop the run, explained in the next
section.

### Just ask Render to rebuild

```bash
./scripts/deploy.sh --trigger-only
```

Skips git entirely. Only useful when you already pushed and Render did not
notice.

---

## When the script refuses to run

If you run `--zip` and it stops with a message like this:

```
This zip is OLDER than your checkout. Applying it would delete work
that is newer than the zip:

      backend/app/newfeature.py
```

...**the script is protecting you.** It means the zip was built from an older
commit than the code sitting in your folder. Making the folder match that zip
would delete files that are newer than the zip, and that work would be gone.

This is very easy to do by accident — build a zip, keep working, commit more,
then run `--zip` on the old file. It looks identical in every way to a correct
run.

The fix is to build the zip from the current commit:

```bash
git archive --format=zip -o ~/revisex-deploy.zip HEAD
./scripts/deploy.sh --zip ~/revisex-deploy.zip
```

If you genuinely want to throw away the newer work and go back to exactly what
the zip contains, add `--force`:

```bash
./scripts/deploy.sh --zip ~/revisex-deploy.zip --force
```

`--force` deletes files without asking again. Only use it when rolling back on
purpose.

The same zip check also stops a run when you have uncommitted changes, because
syncing a zip overwrites the working copy. Commit them, or:

```bash
git stash
```

---

## What a good run looks like

```
ReviseX deploy  https://revisex-2i5g.onrender.com

==> Checking what is committed
    OK   working tree is clean, nothing new to commit
==> Pushing to GitHub
    remote: https://github.com/mayadandapath123-dotcom/ReviseX.git
    branch: main
    OK   pushed
==> Asking Render to rebuild
    OK   deploy triggered (HTTP 200)
==> Waiting for the site to come up with the new content
    the first build after a code change takes roughly 3-6 minutes
    site is answering, reporting 12743 questions
    OK   the new bank is live: 12743 questions

==> Done
    backend    postgresql
    questions  12743
    profiles   2   accounts 1

    Sign in and confirm your streak and XP are still there.
```

Two warnings that are normal and **not** a problem:

- **"no Render deploy hook configured"** — you have not done the one-time setup
  above. The push still happened, and Render rebuilds on a push anyway, so the
  deploy still works. The hook only saves the extra minute.
- **"gave up waiting"** — the build took longer than 10 minutes, which happens on
  the very first build, because the whole question bank is written into Neon over
  the network during startup. Open the Render log and look for the `Content
  ready:` line, or just run `--status` again in a few minutes.

---

## Things this script will never do

- It will not print your deploy hook or your database password.
- It will not commit `.env` files, `~/.neon_url`, `*.pem` files or a Postgres URL
  containing a password. It checks the staged changes and stops if it finds one.
  A committed secret stays in the git history forever, so it is worth being
  strict about this before the push rather than after.
- It will not delete your account, your progress, your XP or your streaks. It
  only replaces code files. See `docs/DEPLOY_NOW.md` for why reseeding the
  question bank leaves user history untouched.

---

## If something goes wrong

`deploy.sh` reports the problem in plain words rather than a stack trace. The
message is written to be the fix, so read it before searching the web.

| What you see | What it means |
| --- | --- |
| `'git' is not installed` | Run `sudo apt install git`. |
| `no 'origin' remote is configured` | Your repository has no GitHub address. The message prints the exact `git remote add` command to run. |
| `the push failed` and it asks for a password | GitHub wants a **personal access token**, not your account password. Create one at GitHub → Settings → Developer settings → Personal access tokens, with the `repo` scope, and paste it as the password. |
| `Render refused the hook (HTTP 403)` | The hook URL was regenerated or copied wrong. Copy it again from the Settings page. |
| `could not reach .../api/health` | The free-tier site is asleep or still building. Wait and retry. |
| `not a git repository` | You are running the script from somewhere its copy of `scripts/` does not sit inside the repo. Run it from the repository folder. |

For the wider picture — connecting Neon, setting up Google sign-in, and what to
do if the site will not boot at all — see `docs/DEPLOY_ZIP_NEON_GOOGLE.md`.
