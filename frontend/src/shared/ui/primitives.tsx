import { useId, useState } from 'react'
import type { ButtonHTMLAttributes, InputHTMLAttributes, ReactNode } from 'react'

/* Small, reusable primitives. No component library — the product needs a
   specific feel and every one of these is < 30 lines. */

type ButtonProps = ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: 'primary' | 'default' | 'ghost'
  size?: 'sm' | 'md' | 'lg'
  block?: boolean
}

export function Button({ variant = 'default', size = 'md', block, className = '', children, ...rest }: ButtonProps) {
  const classes = [
    'btn',
    variant === 'primary' ? 'btn-primary' : '',
    variant === 'ghost' ? 'btn-ghost' : '',
    size === 'sm' ? 'btn-sm' : '',
    size === 'lg' ? 'btn-lg' : '',
    block ? 'btn-block' : '',
    className,
  ]
    .filter(Boolean)
    .join(' ')
  return (
    <button className={classes} {...rest}>
      {children}
    </button>
  )
}

export function Card({ className = '', children, flat, pad }: { className?: string; children: ReactNode; flat?: boolean; pad?: 'sm' }) {
  const classes = ['card', flat ? 'card-flat' : '', pad === 'sm' ? 'card-pad-sm' : '', className].filter(Boolean).join(' ')
  return <div className={classes}>{children}</div>
}

export function Stat({ label, value, accent }: { label: string; value: ReactNode; accent?: boolean }) {
  return (
    <div className="stat">
      <span className="stat-value" style={accent ? { color: 'var(--accent)' } : undefined}>
        {value}
      </span>
      <span className="stat-label">{label}</span>
    </div>
  )
}

export function Bar({ value, tone = 'accent' }: { value: number; tone?: 'accent' | 'success' | 'error' }) {
  const pct = Math.max(0, Math.min(1, value)) * 100
  const fill = tone === 'success' ? 'bar-fill-success' : tone === 'error' ? 'bar-fill-error' : ''
  return (
    <div className="bar" role="progressbar" aria-valuenow={Math.round(pct)} aria-valuemin={0} aria-valuemax={100}>
      <div className={`bar-fill ${fill}`} style={{ width: `${pct}%` }} />
    </div>
  )
}

export function Chip({ children, tone }: { children: ReactNode; tone?: 'accent' | 'success' | 'error' | 'info' }) {
  const cls = tone ? `chip-${tone}` : ''
  return <span className={`chip ${cls}`}>{children}</span>
}

export function Section({ title, action, children }: { title: string; action?: ReactNode; children: ReactNode }) {
  return (
    <section className="section">
      <div className="section-head">
        <h3 className="section-title">{title}</h3>
        {action}
      </div>
      {children}
    </section>
  )
}

export function Empty({ title, hint, action }: { title: string; hint?: string; action?: ReactNode }) {
  return (
    <div className="empty">
      <p style={{ fontWeight: 600, color: 'var(--text-muted)' }}>{title}</p>
      {hint && <p className="tiny" style={{ marginTop: 4 }}>{hint}</p>}
      {action && <div style={{ marginTop: 14 }}>{action}</div>}
    </div>
  )
}

export function Skeleton({ height = 80, count = 1 }: { height?: number; count?: number }) {
  return (
    <>
      {Array.from({ length: count }).map((_, i) => (
        <div key={i} className="skeleton" style={{ height }} />
      ))}
    </>
  )
}

export function ErrorNote({ message, onRetry }: { message: string; onRetry?: () => void }) {
  return (
    <div className="card" style={{ borderColor: 'var(--error)', background: 'var(--error-dim)' }}>
      <p className="small" style={{ color: 'var(--error)', fontWeight: 600 }}>{message}</p>
      {onRetry && (
        <Button size="sm" variant="ghost" onClick={onRetry} style={{ marginTop: 10 }}>
          Try again
        </Button>
      )}
    </div>
  )
}

/* ─────────────────────────── form fields ───────────────────────────
   Every form in the app was hand-rolling its label spacing, and most inputs had
   no styling hook at all. These three primitives give a field one consistent
   shape: uppercase label above, control, help text below. */

export function Field({
  id,
  label,
  hint,
  invalid,
  children,
}: {
  id?: string
  label?: ReactNode
  hint?: ReactNode
  invalid?: boolean
  children: ReactNode
}) {
  return (
    <div className={`field${invalid ? ' field-invalid' : ''}`}>
      {label ? (
        <label className="field-label" htmlFor={id}>
          {label}
        </label>
      ) : null}
      {children}
      {hint ? (
        <span className="field-hint" data-invalid={invalid ? 'true' : undefined}>
          {hint}
        </span>
      ) : null}
    </div>
  )
}

type TextFieldProps = Omit<InputHTMLAttributes<HTMLInputElement>, 'id'> & {
  label?: ReactNode
  hint?: ReactNode
  invalid?: boolean
}

/** Text, search or number field with a label and help text. */
export function TextField({ label, hint, invalid, ...rest }: TextFieldProps) {
  const autoId = useId()
  const id = (rest as { id?: string }).id ?? autoId
  return (
    <Field id={id} label={label} hint={hint} invalid={invalid}>
      <input {...rest} id={id} />
    </Field>
  )
}

/**
 * Password field with a reveal toggle.
 *
 * The toggle matters here more than anywhere else in the app: on a phone a
 * mistyped password is invisible, and the only feedback is "wrong password",
 * which reads as a broken account rather than as a typo.
 */
export function PasswordField({
  label,
  hint,
  invalid,
  ...rest
}: Omit<TextFieldProps, 'type'>) {
  const autoId = useId()
  const id = (rest as { id?: string }).id ?? autoId
  const [shown, setShown] = useState(false)
  return (
    <Field id={id} label={label} hint={hint} invalid={invalid}>
      <span className="field-affix">
        <input {...rest} id={id} type={shown ? 'text' : 'password'} />
        <button
          type="button"
          className="affix-btn"
          onClick={() => setShown((was) => !was)}
          aria-label={shown ? 'Hide password' : 'Show password'}
          aria-pressed={shown}
        >
          {shown ? 'Hide' : 'Show'}
        </button>
      </span>
    </Field>
  )
}

/** Two-or-more-way switch that reads as one control, not as separate links. */
export function Segmented<T extends string>({
  options,
  value,
  onChange,
  ariaLabel,
}: {
  options: { value: T; label: string }[]
  value: T
  onChange: (next: T) => void
  ariaLabel?: string
}) {
  return (
    <div className="segmented" role="tablist" aria-label={ariaLabel}>
      {options.map((option) => (
        <button
          key={option.value}
          type="button"
          role="tab"
          aria-selected={value === option.value}
          className="segmented-btn"
          data-active={value === option.value}
          onClick={() => onChange(option.value)}
        >
          {option.label}
        </button>
      ))}
    </div>
  )
}

/** Divider with a word in it, between a form and an alternative method. */
export function RuleText({ children }: { children: ReactNode }) {
  return (
    <div className="rule-text">
      <span>{children}</span>
    </div>
  )
}
