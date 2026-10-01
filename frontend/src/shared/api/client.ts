/**
 * Thin fetch wrapper.
 *
 * Default is the relative path '/api', which works whenever the frontend and API
 * share an origin: Vite proxies it in dev, and FastAPI serves the built bundle in
 * a single-origin production deploy. Only set VITE_API_URL when the API lives on
 * a different host (e.g. frontend on Netlify, backend on Render) — and then the
 * backend's CORS_ORIGINS must include the frontend origin.
 *
 * The value is baked in at build time, so a split deploy needs a rebuild to
 * repoint it. It must never contain a secret.
 */

const BASE = (import.meta.env.VITE_API_URL as string | undefined)?.replace(/\/$/, '') || '/api'

export class ApiError extends Error {
  constructor(public status: number, message: string, public detail?: unknown) {
    super(message)
  }
}

let activeProfileId: string | null = null
export const setActiveProfile = (id: string | null) => {
  activeProfileId = id
}
export const getActiveProfileId = () => activeProfileId

/**
 * Bearer token for a signed-in account.
 *
 * When a token is present it is the ONLY identity sent: the server maps it to
 * exactly one profile and ignores X-Profile-Id. Sending both would invite the
 * assumption that the header still decides whose data is touched, which is the
 * hole accounts exist to close. The header path remains for a local,
 * account-free install.
 */
let authToken: string | null = null
export const setAuthToken = (token: string | null) => {
  authToken = token
}
export const getAuthToken = () => authToken

/** Called when the server rejects our token, so the app can sign the user out. */
let onUnauthorized: (() => void) | null = null
export const setUnauthorizedHandler = (fn: (() => void) | null) => {
  onUnauthorized = fn
}

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const headers: Record<string, string> = {
    ...(init.body ? { 'Content-Type': 'application/json' } : {}),
    ...((init.headers as Record<string, string>) ?? {}),
  }
  if (authToken) headers['Authorization'] = `Bearer ${authToken}`
  else if (activeProfileId) headers['X-Profile-Id'] = activeProfileId

  const response = await fetch(`${BASE}${path}`, { ...init, headers })

  if (!response.ok) {
    let detail: unknown = null
    try { detail = await response.json() } catch { /* non-JSON error body */ }
    const message = (detail as any)?.detail
    // An expired or revoked token must not leave the app making doomed calls.
    // Login itself returns 401 for bad credentials, so exempt it.
    if (response.status === 401 && !path.startsWith('/auth/login')) onUnauthorized?.()
    // FastAPI returns validation failures as an ARRAY of objects
    // ({msg, loc, type}). Joining that array stringifies each element to
    // "[object Object]", which is exactly what a confused student sees in the
    // error box. Pull the human-readable msg out of each entry instead.
    const text = Array.isArray(message)
      ? message
          .map((entry: unknown) =>
            entry && typeof entry === 'object'
              ? String((entry as { msg?: unknown }).msg ?? JSON.stringify(entry))
              : String(entry),
          )
          .join('; ')
      : String(message ?? response.statusText)
    throw new ApiError(response.status, text, detail)
  }
  if (response.status === 204) return undefined as T
  return (await response.json()) as T
}

export const api = {
  get: <T>(path: string) => request<T>(path),
  post: <T>(path: string, body?: unknown) => request<T>(path, { method: 'POST', body: body === undefined ? undefined : JSON.stringify(body) }),
  patch: <T>(path: string, body?: unknown) => request<T>(path, { method: 'PATCH', body: body === undefined ? undefined : JSON.stringify(body) }),
  del: <T>(path: string) => request<T>(path, { method: 'DELETE' }),
}
