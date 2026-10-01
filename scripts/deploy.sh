#!/usr/bin/env bash
#
# deploy.sh — get the current code onto the live site in one command.
#
#   ./scripts/deploy.sh                     commit any changes, push, deploy, verify
#   ./scripts/deploy.sh --zip FILE.zip      replace the working tree from a zip first
#   ./scripts/deploy.sh --trigger-only      skip git, just ask Render to rebuild
#   ./scripts/deploy.sh --status            show what is live right now, change nothing
#
# Why it works this way: Render does not accept an uploaded zip. It builds from a
# git repository. So "deploy a zip" always means the same three steps underneath —
# get the files into git, push to GitHub, ask Render to rebuild. This script does
# all three and then checks the result, so a failure is reported rather than
# discovered later on the site.
#
# Setup, once:
#   1. Render dashboard -> your service -> Settings -> Deploy Hook -> copy the URL.
#   2. Save it, either in a file or an environment variable:
#        echo 'https://api.render.com/deploy/srv-XXXX?key=YYYY' > ~/.render_deploy_hook
#        chmod 600 ~/.render_deploy_hook
#   The hook URL is a secret — anyone holding it can trigger a deploy. Keep it out
#   of the repo, which is why it lives in your home directory.
#
set -euo pipefail

# ── configuration ────────────────────────────────────────────────────────────

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
HOOK_FILE="${RENDER_DEPLOY_HOOK_FILE:-$HOME/.render_deploy_hook}"
# Change this if you rename the service on Render.
SITE_URL="${REVISE_SITE_URL:-https://revisex-2i5g.onrender.com}"
BRANCH="${REVISE_BRANCH:-main}"

# ── pretty output ────────────────────────────────────────────────────────────

if [ -t 1 ]; then
  BOLD=$'\033[1m'; DIM=$'\033[2m'; RED=$'\033[31m'; GREEN=$'\033[32m'
  YELLOW=$'\033[33m'; BLUE=$'\033[34m'; OFF=$'\033[0m'
else
  BOLD=''; DIM=''; RED=''; GREEN=''; YELLOW=''; BLUE=''; OFF=''
fi

step()  { printf '%s\n' "${BOLD}${BLUE}==>${OFF} ${BOLD}$*${OFF}"; }
info()  { printf '%s\n' "    $*"; }
ok()    { printf '%s\n' "    ${GREEN}OK${OFF}   $*"; }
warn()  { printf '%s\n' "    ${YELLOW}WARN${OFF} $*"; }
fail()  { printf '%s\n' "    ${RED}FAIL${OFF} $*" >&2; exit 1; }
die()   { printf '\n%s\n\n' "${RED}${BOLD}$*${OFF}" >&2; exit 1; }

# ── helpers ──────────────────────────────────────────────────────────────────

need() {
  command -v "$1" >/dev/null 2>&1 || die "'$1' is not installed.

Install it and run this script again. On Debian or Ubuntu:
    sudo apt install $2"
}

hook_url() {
  if [ -n "${RENDER_DEPLOY_HOOK:-}" ]; then
    printf '%s' "$RENDER_DEPLOY_HOOK"
  elif [ -f "$HOOK_FILE" ]; then
    tr -d '\r\n ' < "$HOOK_FILE"
  else
    printf ''
  fi
}

# Poll the live health endpoint and print what it reports.
show_live_state() {
  local body
  body="$(curl -fsS --max-time 60 "$SITE_URL/api/health" 2>/dev/null || true)"
  if [ -z "$body" ]; then
    warn "could not reach $SITE_URL/api/health"
    info "a free Render service sleeps after ~15 minutes idle; the first"
    info "request wakes it and can take 30-60 seconds. Try again."
    return 1
  fi
  python3 - "$body" <<'PY'
import json, sys
try:
    d = json.loads(sys.argv[1])
except Exception:
    print("    could not parse the health response"); raise SystemExit(1)
db = d.get("database", {})
print(f"    backend    {db.get('backend')}")
print(f"    host       {db.get('host')}")
print(f"    questions  {d.get('questions')}")
print(f"    profiles   {d.get('profiles')}   accounts {d.get('accounts')}")
n = d.get("questions") or 0
if n >= 12000:
    print(f"    \033[32mOK\033[0m   the current bank is live ({n} questions)")
elif n >= 5000:
    print(f"    \033[33mWARN\033[0m this is the OLD bank ({n}); the new commit is not deployed")
else:
    print(f"    \033[33mWARN\033[0m only {n} questions reported")
PY
}

google_enabled() {
  curl -fsS --max-time 60 "$SITE_URL/api/auth/google/status" 2>/dev/null \
    | python3 -c 'import json,sys; print("yes" if json.load(sys.stdin).get("enabled") else "no")' \
    2>/dev/null || echo "?"
}

# ── git identity ─────────────────────────────────────────────────────────────

ensure_git_identity() {
  # A fresh clone or a restored workspace often has no identity, and git then
  # refuses to commit with "Author identity unknown". Set it here rather than
  # letting the script die halfway through.
  if [ -z "$(git -C "$REPO_ROOT" config user.email || true)" ]; then
    git -C "$REPO_ROOT" config user.email "deploy@localhost"
    info "set git user.email for this repo"
  fi
  if [ -z "$(git -C "$REPO_ROOT" config user.name || true)" ]; then
    git -C "$REPO_ROOT" config user.name "deploy"
    info "set git user.name for this repo"
  fi
}

# ── secret safety ────────────────────────────────────────────────────────────

forbid_secrets() {
  # Committing a connection string or a client secret is the one mistake that is
  # expensive to undo: the value stays in the git history even after the file is
  # deleted. Check before the commit, not after the push.
  #
  # .env.example and friends are templates and belong in the repo, so they are
  # allowed through. Blocking them would make the script cry wolf the first time
  # anyone documented a new setting, and a safety check that fires on safe input
  # is worse than no check.
  local hits
  hits="$(git -C "$REPO_ROOT" diff --cached --name-only \
          | grep -E '(^|/)\.env($|\.)|neon_url|\.pem$|credentials\.json$' \
          | grep -vE '\.env\.(example|sample|template|dist)$' || true)"
  if [ -n "$hits" ]; then
    die "These staged files look like secrets and must not be committed:
$(printf '      %s\n' $hits)

Remove them from the commit:
    git reset HEAD <file>
and add the pattern to .gitignore."
  fi

  # A pasted Postgres URL inside any staged file is also a leak.
  #
  # Placeholders are not. .env.example documents the shape of the URL with
  # USER:PASSWORD@HOST-REGION, and without the filter below every future edit to
  # that file would block the deploy with a false alarm — which is how people
  # learn to pass --force and stop reading the warning.
  local dblines
  # Only the password half is inspected. Filtering on the whole match would
  # also skip a username like 'someuser', hiding a genuine credential.
  dblines="$(git -C "$REPO_ROOT" diff --cached -U0 2>/dev/null \
    | grep -E '^\+.*postgres(ql)?://[^ :/]+:[^ @]+@' \
    | grep -viE ':(PASSWORD|YOUR_?PASSWORD|DB_?PASSWORD|PLACEHOLDER|EXAMPLE|CHANGE_?ME|SECRET|XXXX+|[A-Z]*PASS|\*+)@' || true)"
  if [ -n "$dblines" ]; then
    printf '%s\n' "$dblines" | head -3 | sed 's/^/        /' >&2
    die "A staged change contains what looks like a full database URL with a
password. Move it to an environment variable and commit again.

If that URL is a placeholder, reword it so it does not look like a real
credential — for example postgresql://USER:PASSWORD@HOST/DBNAME."
  fi
  if git -C "$REPO_ROOT" diff --cached -U0 2>/dev/null \
     | grep -E '^\+.*(GOCSPX-|googleusercontent\.com)' >/dev/null; then
    warn "a staged change mentions a Google credential; make sure it is not the secret"
  fi
}

# ── modes ────────────────────────────────────────────────────────────────────

sync_from_zip() {
  local zip="$1"
  [ -f "$zip" ] || die "no such file: $zip"
  need unzip unzip

  step "Replacing the working tree from $(basename "$zip")"

  if [ -n "$(git -C "$REPO_ROOT" status --porcelain -- . ':(exclude)backend/data' 2>/dev/null)" ]; then
    die "You have uncommitted changes in $REPO_ROOT, and syncing a zip replaces
the working tree, which would discard them.

Commit or stash them first:
    git -C $REPO_ROOT stash
or run with --force to discard them deliberately."
  fi

  local tmp
  tmp="$(mktemp -d)"
  # EXIT, not RETURN: a RETURN trap set inside a function also fires on every
  # later function's return, and it does not fire at all when die calls exit,
  # which is exactly the path that would leak this directory.
  # shellcheck disable=SC2064
  trap "rm -rf '$tmp'" EXIT

  unzip -q "$zip" -d "$tmp"
  info "extracted $(find "$tmp" -type f | wc -l | tr -d ' ') files"

  # Rehearse first. The check that matters: a zip built from an older commit
  # would DELETE the files added since, and losing new work to a stale download
  # is the one failure this script must not allow quietly.
  local plan tracked
  plan="$(python3 "$REPO_ROOT/scripts/sync_zip.py" "$tmp" "$REPO_ROOT" --dry-run --json)"
  tracked="$(printf '%s' "$plan" | python3 -c '
import json, sys
plan = json.load(sys.stdin)
print("\n".join(plan["deleted"]))
' | while IFS= read -r f; do
      [ -n "$f" ] || continue
      if git -C "$REPO_ROOT" ls-files --error-unmatch -- "$f" >/dev/null 2>&1; then
        printf '%s\n' "$f"
      fi
    done)"

  if [ -n "$tracked" ]; then
    if [ "$FORCE" = "1" ]; then
      warn "this zip is older than your checkout; --force was given, so these go:"
      printf '%s\n' "$tracked" | sed 's/^/        /'
    else
      die "This zip is OLDER than your checkout. Applying it would delete work
that is newer than the zip:

$(printf '      %s\n' $tracked)

That usually means the zip was built before the latest commits. Build a fresh
one instead:

    git -C $REPO_ROOT archive --format=zip -o /tmp/revisex-deploy.zip HEAD
    ./scripts/deploy.sh --zip /tmp/revisex-deploy.zip

If you genuinely mean to roll back to the zip's state, pass --force."
    fi
  fi

  python3 "$REPO_ROOT/scripts/sync_zip.py" "$tmp" "$REPO_ROOT"

  # The zip is built from the repository root, so it carries backend/, frontend/
  # and render.yaml. Syncing makes the working tree match it exactly, deletions
  # included, so a file removed upstream does not linger and get committed again.
  ok "working tree now matches the zip"
}

trigger_deploy() {
  local hook
  hook="$(hook_url)"
  if [ -z "$hook" ]; then
    warn "no Render deploy hook configured, so I cannot ask Render to rebuild"
    info "Render rebuilds by itself when you push, so this usually does not matter."
    info "To trigger one from here, copy the hook URL from"
    info "  Render dashboard -> your service -> Settings -> Deploy Hook"
    info "and save it:"
    info "  echo 'https://api.render.com/deploy/srv-...?key=...' > $HOOK_FILE"
    info "  chmod 600 $HOOK_FILE"
    return 0
  fi

  step "Asking Render to rebuild"
  local code
  code="$(curl -s -o /dev/null -w '%{http_code}' -X POST --max-time 60 "$hook" || true)"
  case "$code" in
    200|201|202) ok "deploy triggered (HTTP $code)" ;;
    401|403)     fail "Render refused the hook (HTTP $code). The URL may have been regenerated." ;;
    *)           fail "unexpected response from the deploy hook: HTTP $code" ;;
  esac
}

wait_for_site() {
  step "Waiting for the site to come up with the new content"
  info "the first build after a code change takes roughly 3-6 minutes"

  local deadline=$(( $(date +%s) + 600 ))
  local last=""
  while [ "$(date +%s)" -lt "$deadline" ]; do
    local body
    body="$(curl -fsS --max-time 45 "$SITE_URL/api/health" 2>/dev/null || true)"
    if [ -n "$body" ]; then
      local n
      n="$(printf '%s' "$body" | python3 -c \
            'import json,sys; print(json.load(sys.stdin).get("questions",0))' 2>/dev/null || echo 0)"
      if [ "$n" != "$last" ]; then
        info "site is answering, reporting $n questions"
        last="$n"
      fi
      if [ "$n" -ge 12000 ] 2>/dev/null; then
        ok "the new bank is live: $n questions"
        return 0
      fi
    fi
    printf '%s' "."
    sleep 15
  done
  printf '\n'
  warn "gave up waiting. Check the Render log for the 'Content ready:' line."
  info "It is normal to wait longer on the very first build, because the whole"
  info "bank is seeded into Neon over the network during startup."
  return 1
}

# ── argument parsing ─────────────────────────────────────────────────────────

MODE="deploy"
ZIP=""
FORCE=0

while [ $# -gt 0 ]; do
  case "$1" in
    --zip)          MODE="zip"; ZIP="${2:-}"; [ -n "$ZIP" ] || die "--zip needs a file path"; shift 2 ;;
    --trigger-only) MODE="trigger"; shift ;;
    --status)       MODE="status"; shift ;;
    --force)        FORCE=1; shift ;;
    -h|--help)      sed -n '2,20p' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
    *)              die "unknown option: $1   (try --help)" ;;
  esac
done

# ── run ──────────────────────────────────────────────────────────────────────

printf '\n%s\n\n' "${BOLD}ReviseX deploy${OFF}  ${DIM}$SITE_URL${OFF}"

if [ "$MODE" = "status" ]; then
  step "What is live right now"
  show_live_state || true
  printf '\n'
  info "Google sign-in: $(google_enabled)"
  printf '\n'
  exit 0
fi

need git git
need curl curl
need python3 python3

cd "$REPO_ROOT"
[ -d .git ] || die "$REPO_ROOT is not a git repository."

if [ "$MODE" = "zip" ]; then
  sync_from_zip "$ZIP"
fi

ensure_git_identity

step "Checking what is committed"
if [ -n "$(git status --porcelain)" ]; then
  info "changed files:"
  git status --short | sed 's/^/      /'
  git add -A
  forbid_secrets
  local_subject="${REVISE_COMMIT_MESSAGE:-Deploy $(date -u '+%Y-%m-%d %H:%M UTC')}"
  git commit -q -m "$local_subject"
  ok "committed"
else
  ok "working tree is clean, nothing new to commit"
fi

if [ "$MODE" != "trigger" ]; then
  step "Pushing to GitHub"
  if [ -z "$(git remote get-url origin 2>/dev/null || true)" ]; then
    die "no 'origin' remote is configured.

Add one:
    git remote add origin https://github.com/mayadandapath123-dotcom/ReviseX.git"
  fi
  info "remote: $(git remote get-url origin)"
  info "branch: $BRANCH"

  git push origin "$BRANCH" || die "the push failed.

If it asked for a password, GitHub wants a personal access token, not your
account password. Create one at:
  GitHub -> Settings -> Developer settings -> Personal access tokens
Give it the 'repo' scope and paste it as the password."
  ok "pushed"
else
  info "skipping the push (--trigger-only)"
fi

trigger_deploy
wait_for_site || true

step "Done"
show_live_state || true
printf '\n'
info "Sign in and confirm your streak and XP are still there."
printf '\n'
