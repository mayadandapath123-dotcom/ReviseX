# Adding Google sign-in to your live site

Your site is `https://revisex-2i5g.onrender.com`, so every value below is
already filled in for you. Copy them exactly — Google rejects the flow on any
mismatch, including a trailing slash.

**Time: about 10 minutes. Cost: ₹0.**

The code is already written and tested. Nothing here changes the app — you are
only creating credentials and telling Render about them. Until you do, the
"Continue with Google" button simply does not appear, and username+password
keeps working exactly as it does now.

---

## Step 1 — Create a Google Cloud project

1. Go to **https://console.cloud.google.com**
2. Sign in with the Google account you want to own this (any of yours).
3. Accept the terms if asked.
4. Click the project dropdown at the top of the page → **New Project**.
5. **Project name:** `revisex` → click **Create**.
6. Wait a few seconds, then make sure `revisex` is selected in that same
   dropdown at the top.

---

## Step 2 — Configure the OAuth consent screen

Google requires this before it will issue credentials.

1. In the left menu: **APIs & Services** → **OAuth consent screen**.
   (In some layouts it is now called **Google Auth Platform → Overview**.)
2. **User type:** choose **External** → **Create**.
   (Internal is only for Google Workspace organisations.)
3. Fill in:
   - **App name:** `ReviseX`
   - **User support email:** your email (pick from the dropdown)
   - **Developer contact email:** your email
4. Click **Save and Continue** through the remaining steps. You do NOT need to
   add any scopes — the app asks only for `openid email profile`, which are
   default.
5. If you see a **Publishing status** or **Audience** section, set it to
   **In production** (or "Publish app"). While it says *Testing*, only email
   addresses you list as test users can sign in.

> If it says **Testing** and you skip this, sign-in will work for you but fail
> for your students with `access_blocked`. That is the single most common
> mistake here.

---

## Step 3 — Create the OAuth client ID

1. Left menu: **APIs & Services** → **Credentials**.
2. Click **+ Create Credentials** → **OAuth client ID**.
3. **Application type:** **Web application**
4. **Name:** `revisex-web`
5. **Authorized JavaScript origins** → click **+ Add URI** and enter:
   ```
   https://revisex-2i5g.onrender.com
   ```
6. **Authorized redirect URIs** → click **+ Add URI** and enter **exactly**:
   ```
   https://revisex-2i5g.onrender.com/api/auth/google/callback
   ```
7. Click **Create**.
8. A popup shows your **Client ID** and **Client Secret**. Click
   **Download JSON** as a backup, and copy both values somewhere safe.

- The Client ID ends in `.apps.googleusercontent.com` — it is not secret.
- The Client Secret **is** secret. It only ever goes into Render, never into
  GitHub or a chat.

---

## Step 4 — Tell Render

1. Go to **https://dashboard.render.com** → your **revisex** service.
2. Left menu: **Environment**.
3. Add these four (use **Add Environment Variable**):

| Key | Value |
|---|---|
| `GOOGLE_CLIENT_ID` | the Client ID from step 3 |
| `GOOGLE_CLIENT_SECRET` | the Client Secret from step 3 |
| `PUBLIC_BASE_URL` | `https://revisex-2i5g.onrender.com` |
| `ADMIN_USERNAMES` | your username, e.g. `sayan` |

Notes:
- `PUBLIC_BASE_URL` has **no trailing slash**. The app appends
  `/api/auth/google/callback` itself, so it must match step 3 exactly.
- `ADMIN_USERNAMES` is how you get the admin panel. It is a comma-separated
  list of usernames (lowercase). Sign up with that username and you are
  promoted automatically — no restart needed. Only list people you trust with
  every student's data.

4. Click **Save Changes**. Render redeploys automatically (2–4 minutes).

---

## Step 5 — Test it

1. Open **https://revisex-2i5g.onrender.com/api/config**
   You should see:
   ```json
   {"app_name":"ReviseX","google_sign_in":true,"allow_local_profiles":false,"max_local_profiles":12}
   ```
   If `google_sign_in` is `false`, Render did not pick up the variables —
   check the spelling and that you saved.

2. Open the site. The sign-in screen should now show **Continue with Google**.

3. Click it → choose a Google account → allow. You land back signed in.

4. Go to **Account** in the navigation. You should see both sign-in methods
   listed, and a **Disconnect** button next to Google.

---

## Linking your existing local progress

You currently have progress on the site with no account attached. To keep it:

1. On the same browser and device where that progress lives, go to the sign-in
   screen.
2. You should see a blue note: *"Progress found on this device…"*
3. Click **Create account**, choose a username and password.
4. Your existing XP, streaks and mistake book are adopted by the new account
   rather than starting from zero.

This only works from the browser that holds that progress, because the claim
uses an id stored in that browser. If you have already created an account
elsewhere, tell me and I will move the progress across directly in Neon.

---

## Troubleshooting

**`redirect_uri_mismatch`**
The URI in step 3.6 does not match what the app sent. It must be exactly
`https://revisex-2i5g.onrender.com/api/auth/google/callback` — no trailing
slash, `https`, correct spelling. Compare it against
`https://revisex-2i5g.onrender.com/api/auth/google/status`, which reports the
URI the server is actually using.

**`access_blocked` or "app not verified"**
The consent screen is still in **Testing**. Publish it (step 2.5), or add the
student's email as a test user under **Audience → Test users**.

**The Google button does not appear**
`/api/config` shows `google_sign_in: false`, so Render does not have both
`GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET`. Check spelling, then
**Manual Deploy → Deploy latest commit**.

**"This sign-in attempt expired"**
The OAuth state lives 10 minutes. You left the Google screen open too long.
Just start again.

**Signing in with Google created a second account**
Correct behaviour, and deliberate. Google sign-in never merges into an existing
username account by matching an email address — that would let anyone
controlling a colliding Google address walk into a student's progress. To join
them: sign in with your username and password, go to **Account**, and click
**Connect** next to Google.

**I want to disconnect Google**
**Account → Disconnect.** If Google is your only sign-in method the app refuses
and tells you to set a password first — otherwise disconnecting would lock you
out permanently.

**A student forgot their password**
There is no email-based reset yet. If they linked Google, they can sign in that
way. Otherwise tell me and I will add an admin reset to your panel, which for a
class is usually more practical than setting up email.
