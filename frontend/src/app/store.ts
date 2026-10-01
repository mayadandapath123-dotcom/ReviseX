import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import { setActiveProfile, setAuthToken, setUnauthorizedHandler } from '@/shared/api/client'
import type { Profile } from '@/shared/types'

export interface AuthUser {
  id: string
  username: string
  created_at?: string | null
}

export interface Impersonation {
  /** The admin's own token, kept so leaving impersonation is always possible. */
  adminToken: string
  adminUsername: string
  targetUsername: string
  expiresAt: number
}

interface AppState {
  profile: Profile | null
  online: boolean
  /** Signed-in account. null means local, account-free mode. */
  auth: { token: string; user: AuthUser } | null
  /** Set once the student picks "continue without an account". */
  localMode: boolean
  /** Present only while an admin is viewing someone else's account. */
  impersonating: Impersonation | null
  setProfile: (p: Profile | null) => void
  setOnline: (v: boolean) => void
  setAuth: (a: { token: string; user: AuthUser } | null) => void
  setLocalMode: (v: boolean) => void
  setImpersonating: (i: Impersonation | null) => void
}

/**
 * Profile choice is persisted locally so a returning student lands straight in.
 * Progress itself lives in SQLite — this store only remembers *who* is playing.
 */
export const useAppStore = create<AppState>()(
  persist(
    (set, get) => ({
      profile: null,
      online: navigator.onLine,
      auth: null,
      localMode: false,
      impersonating: null,
      setProfile: (p) => {
        setActiveProfile(p?.id ?? null)
        set({ profile: p })
      },
      setOnline: (online) => set({ online }),
      setAuth: (a) => {
        // Keep the client's header logic and the persisted state in one place,
        // so nothing can end up holding a token the store has already dropped.
        setAuthToken(a?.token ?? null)
        set({ auth: a })
      },
      setLocalMode: (localMode) => set({ localMode }),
      setImpersonating: (impersonating) => {
        // The client's header has to follow immediately, or the next request
        // would still be made as whoever was signed in a moment ago.
        setAuthToken(impersonating ? null : (get().auth?.token ?? null))
        set({ impersonating })
      },
    }),
    {
      name: 'leap.app',
      onRehydrateStorage: () => (state) => {
        if (state?.profile) setActiveProfile(state.profile.id)
        if (state?.auth) setAuthToken(state.auth.token)
        // A rejected token anywhere in the app signs the student out rather
        // than leaving them staring at errors on every request.
        setUnauthorizedHandler(() => {
          setAuthToken(null)
          useAppStore.setState({ auth: null })
        })
      },
    },
  ),
)
