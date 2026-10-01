/**
 * User preferences: theme, sound, and how the keyboard answers a question.
 *
 * Kept in its own store rather than mixed into the app store because these are
 * device preferences, not account state. They belong to this phone or this
 * laptop, and they must survive signing out.
 */

import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import { applyTheme, DEFAULT_THEME, type ThemeId } from '@/shared/lib/theme'
import { sfx } from '@/shared/lib/sfx'

/**
 * How pressing 1–4 answers a question.
 *
 *  - `confirm` — the number highlights an option, arrows move the highlight,
 *    Enter answers. Lets you change your mind before committing, which matters
 *    when a wrong answer breaks a streak.
 *  - `instant` — the number answers straight away. Faster for timed rush modes.
 */
export type AnswerMode = 'confirm' | 'instant'

export const DEFAULT_ANSWER_MODE: AnswerMode = 'confirm'
export const DEFAULT_SFX_VOLUME = 0.55

interface PrefsState {
  theme: ThemeId
  sfxEnabled: boolean
  sfxVolume: number
  answerMode: AnswerMode
  /** False once the student hides the keyboard hint under the options. */
  showShortcutHint: boolean
  setTheme: (id: ThemeId) => void
  setSfxEnabled: (on: boolean) => void
  setSfxVolume: (v: number) => void
  setAnswerMode: (mode: AnswerMode) => void
  setShowShortcutHint: (show: boolean) => void
}

export const usePrefs = create<PrefsState>()(
  persist(
    (set) => ({
      theme: DEFAULT_THEME,
      // On by default: the student asked for sound, and a cue you have to go
      // looking for in a settings panel is a cue nobody hears. The mute button
      // sits in the quiz header, one tap away, for when it is unwanted.
      sfxEnabled: true,
      sfxVolume: DEFAULT_SFX_VOLUME,
      answerMode: DEFAULT_ANSWER_MODE,
      showShortcutHint: true,
      setTheme: (theme) => {
        // Apply immediately: waiting for the subscription below would leave one
        // frame of the previous palette on screen.
        applyTheme(theme)
        set({ theme })
      },
      setSfxEnabled: (sfxEnabled) => {
        sfx.setEnabled(sfxEnabled)
        set({ sfxEnabled })
      },
      setSfxVolume: (sfxVolume) => {
        sfx.setVolume(sfxVolume)
        set({ sfxVolume })
      },
      setAnswerMode: (answerMode) => set({ answerMode }),
      setShowShortcutHint: (showShortcutHint) => set({ showShortcutHint }),
    }),
    {
      name: 'leap.prefs',
      // version 2: themes were reworked from a stray `light`/unset flag into a
      // named palette set, and the answer-mode preference is new.
      version: 2,
      migrate: (persisted, version) => {
        // `theme` is read as a plain string here, not as ThemeId: this is
        // persisted state from an older build, so it can hold a value the
        // current type does not allow. That is the whole reason migrate exists.
        const state = (persisted ?? {}) as Omit<Partial<PrefsState>, 'theme'> & { theme?: string }
        if (version < 2) {
          // The old build only ever wrote `light`, or left the value unset.
          state.theme = state.theme === 'light' ? 'daylight' : DEFAULT_THEME
          state.answerMode = DEFAULT_ANSWER_MODE
        }
        return state as PrefsState
      },
      onRehydrateStorage: () => (state) => {
        // Push the restored values into the two systems that live outside React.
        applyTheme(state?.theme ?? DEFAULT_THEME)
        sfx.setEnabled(state?.sfxEnabled ?? true)
        sfx.setVolume(state?.sfxVolume ?? DEFAULT_SFX_VOLUME)
      },
    },
  ),
)
