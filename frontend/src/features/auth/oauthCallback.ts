/**
 * Consumes the redirect that lands on `/#auth={json}` after Google sends the
 * browser back.
 *
 * The result arrives in the URL FRAGMENT rather than as a query parameter on
 * purpose: fragments are never sent to a server, so the session token cannot
 * appear in Render's access logs or in anyone's proxy history.
 *
 * Everything is cleared from the address bar immediately, because a token left
 * in the URL survives a copy-paste of the link and browser history.
 */

export interface OAuthResult {
  ok: boolean
  mode?: 'signin' | 'link'
  token?: string
  user?: { id: string; username: string; created_at?: string | null }
  profile_id?: string | null
  google_email?: string | null
  error?: string
}

const NOTICE_KEY = 'revisex.oauth.notice'

/** Read and consume the callback. Returns null when there was none. */
export function consumeOAuthCallback(): OAuthResult | null {
  const hash = window.location.hash
  if (!hash.startsWith('#auth=')) return null

  let parsed: OAuthResult | null = null
  try {
    parsed = JSON.parse(decodeURIComponent(hash.slice('#auth='.length))) as OAuthResult
  } catch {
    parsed = { ok: false, error: 'The sign-in response from Google was malformed.' }
  }

  // Wipe the fragment without a navigation entry, so Back does not re-replay it.
  const clean = window.location.pathname + window.location.search
  window.history.replaceState(null, '', clean)

  return parsed
}

/**
 * Park a message for the account or sign-in screen to show after the redirect.
 * React state does not survive a full-page navigation to Google and back, so
 * sessionStorage carries it across.
 */
export function setOAuthNotice(kind: 'ok' | 'err', text: string) {
  try {
    sessionStorage.setItem(NOTICE_KEY, JSON.stringify({ kind, text }))
  } catch {
    /* private mode: the notice is a nicety, not a requirement */
  }
}

export function takeOAuthNotice(): { kind: 'ok' | 'err'; text: string } | null {
  try {
    const raw = sessionStorage.getItem(NOTICE_KEY)
    if (!raw) return null
    sessionStorage.removeItem(NOTICE_KEY)
    return JSON.parse(raw)
  } catch {
    return null
  }
}
