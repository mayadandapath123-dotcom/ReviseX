import { useEffect, useRef } from 'react'
import { THEMES, type ThemeId } from '@/shared/lib/theme'
import { sfx } from '@/shared/lib/sfx'
import { usePrefs } from '@/app/prefs'
import { Icon } from './icons'
import { Segmented } from './primitives'

/**
 * Settings: theme, sound, and how the keyboard answers.
 *
 * Rendered as a bottom sheet on a phone and a floating panel on desktop — the
 * same markup, two CSS layouts. A modal dialog on a phone would cover the whole
 * screen for three settings, and the bottom sheet is where a thumb already is.
 */
export function SettingsSheet({ open, onClose }: { open: boolean; onClose: () => void }) {
  const theme = usePrefs((s) => s.theme)
  const setTheme = usePrefs((s) => s.setTheme)
  const sfxEnabled = usePrefs((s) => s.sfxEnabled)
  const setSfxEnabled = usePrefs((s) => s.setSfxEnabled)
  const sfxVolume = usePrefs((s) => s.sfxVolume)
  const setSfxVolume = usePrefs((s) => s.setSfxVolume)
  const answerMode = usePrefs((s) => s.answerMode)
  const setAnswerMode = usePrefs((s) => s.setAnswerMode)
  const panel = useRef<HTMLDivElement>(null)

  // Escape closes, and the page behind must not scroll while a sheet is open.
  useEffect(() => {
    if (!open) return
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        e.stopPropagation()
        onClose()
      }
    }
    window.addEventListener('keydown', onKey, true)
    const previous = document.body.style.overflow
    document.body.style.overflow = 'hidden'
    panel.current?.focus()
    return () => {
      window.removeEventListener('keydown', onKey, true)
      document.body.style.overflow = previous
    }
  }, [open, onClose])

  if (!open) return null

  const preview = (id: ThemeId) => {
    setTheme(id)
    sfx.play('click')
  }

  return (
    <>
      <div className="sheet-backdrop" onClick={onClose} aria-hidden="true" />
      <div
        className="sheet"
        role="dialog"
        aria-modal="true"
        aria-label="Settings"
        tabIndex={-1}
        ref={panel}
      >
        <div className="sheet-grip" />
        <div className="sheet-head">
          <span className="sheet-title">Settings</span>
          <button className="icon-btn" onClick={onClose} aria-label="Close settings">
            <Icon name="close" size={17} />
          </button>
        </div>

        <div className="sheet-group">
          <div className="sheet-group-title">Theme</div>
          <div className="theme-grid">
            {THEMES.map((t) => {
              const active = t.id === theme
              return (
                <button
                  key={t.id}
                  className="theme-swatch"
                  data-active={active}
                  onClick={() => preview(t.id)}
                  aria-pressed={active}
                >
                  {active && <span className="theme-check">✓</span>}
                  <span className="theme-preview" aria-hidden="true">
                    {t.swatch.map((colour, i) => (
                      <span key={i} style={{ background: colour }} />
                    ))}
                  </span>
                  <span className="theme-swatch-name">{t.label}</span>
                  <span className="theme-swatch-note">{t.note}</span>
                </button>
              )
            })}
          </div>
        </div>

        <div className="sheet-group">
          <div className="sheet-group-title">Sound</div>
          <div className="pref-row">
            <span>
              <span className="pref-label">Sound effects</span>
              <span className="pref-hint">
                A tick on taps, a rising pair of notes when you are right, a low one when you
                are not.
              </span>
            </span>
            <label className="switch">
              <input
                type="checkbox"
                checked={sfxEnabled}
                onChange={(e) => {
                  setSfxEnabled(e.target.checked)
                  // Play after enabling so the change is audible immediately.
                  if (e.target.checked) sfx.play('correct')
                }}
                aria-label="Sound effects"
              />
              <span className="switch-track" />
              <span className="switch-thumb" />
            </label>
          </div>

          {sfxEnabled && (
            <div className="pref-row">
              <span>
                <span className="pref-label">Volume</span>
                <span className="pref-hint">Preview: the right-answer cue.</span>
              </span>
              <span style={{ display: 'flex', alignItems: 'center', gap: 10, width: 168 }}>
                <input
                  type="range"
                  min={0}
                  max={1}
                  step={0.05}
                  value={sfxVolume}
                  aria-label="Sound volume"
                  onChange={(e) => setSfxVolume(Number(e.target.value))}
                  onMouseUp={() => sfx.play('correct')}
                  onTouchEnd={() => sfx.play('correct')}
                />
                <button
                  className="icon-btn"
                  data-on={sfxEnabled}
                  onClick={() => sfx.play('correct')}
                  aria-label="Test sound"
                  title="Test sound"
                >
                  <Icon name="sound" size={17} />
                </button>
              </span>
            </div>
          )}
        </div>

        <div className="sheet-group" style={{ marginBottom: 4 }}>
          <div className="sheet-group-title">Answering with the keyboard</div>
          <Segmented
            ariaLabel="Keyboard answer mode"
            value={answerMode}
            onChange={(next) => {
              setAnswerMode(next)
              sfx.play('click')
            }}
            options={[
              { value: 'confirm', label: 'Select, then Enter' },
              { value: 'instant', label: 'Instant' },
            ]}
          />
          <p className="pref-hint" style={{ marginTop: 9, maxWidth: 'none' }}>
            {answerMode === 'confirm' ? (
              <>
                Press <span className="kbd">1</span>–<span className="kbd">4</span> to highlight an
                option, arrow keys to change it, then <span className="kbd">Enter</span> to answer.
                Nothing is submitted until you commit, so a wrong key costs nothing.
              </>
            ) : (
              <>
                Pressing <span className="kbd">1</span>–<span className="kbd">4</span> answers
                immediately. Faster, but there is no chance to change your mind.
              </>
            )}
          </p>
        </div>
      </div>
    </>
  )
}
