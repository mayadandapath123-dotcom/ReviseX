/**
 * Sound effects, synthesised in the browser.
 *
 * There are no .mp3 files here on purpose. Three reasons:
 *   - a revision app is used on school wifi and mobile data, so anything that
 *     adds a download to the critical path is a liability;
 *   - the app must work offline, and a missing asset would 404 into silence;
 *   - the Web Audio API can make these tones in a few hundred bytes of code,
 *     and they are then consistent across every device.
 *
 * Every sound is deliberately short. This is a speed-training app: a cue that
 * outlasts the moment it describes is worse than no cue at all.
 *
 * Browsers refuse to start audio until the user has interacted with the page,
 * so the context is created lazily on the first sound and resumed if it was
 * suspended. Nothing plays during the initial render, which is exactly right.
 */

export type SoundName = 'click' | 'select' | 'correct' | 'wrong' | 'streak' | 'finish' | 'tick'

type AudioContextCtor = typeof AudioContext

let ctx: AudioContext | null = null
let master: GainNode | null = null

let enabled = true
let volume = 0.55

/** Some browsers (older iOS Safari) only expose the prefixed constructor. */
function contextCtor(): AudioContextCtor | null {
  if (typeof window === 'undefined') return null
  const w = window as unknown as {
    AudioContext?: AudioContextCtor
    webkitAudioContext?: AudioContextCtor
  }
  return w.AudioContext ?? w.webkitAudioContext ?? null
}

/**
 * Returns a running context, or null when audio is unavailable or switched off.
 *
 * `resume()` is fire-and-forget: a suspended context that is resumed a moment
 * late still plays the tone, because the scheduled start time is in the future.
 */
function ensure(): AudioContext | null {
  if (!enabled) return null
  const Ctor = contextCtor()
  if (!Ctor) return null

  if (!ctx) {
    try {
      ctx = new Ctor()
      master = ctx.createGain()
      master.gain.value = volume
      master.connect(ctx.destination)
    } catch {
      // Autoplay policy or no audio device. Silence is the correct fallback.
      ctx = null
      master = null
      return null
    }
  }
  if (ctx.state === 'suspended') void ctx.resume()
  return ctx
}

function setVolume(next: number) {
  volume = Math.max(0, Math.min(1, next))
  if (master) master.gain.value = volume
}

function setEnabled(next: boolean) {
  enabled = next
  if (!next && ctx && ctx.state === 'running') {
    // Nothing queued should survive the switch being turned off.
    void ctx.suspend()
  } else if (next && ctx && ctx.state === 'suspended') {
    void ctx.resume()
  }
}

/** Call from the first real user gesture so iOS unlocks playback. */
function unlock() {
  const c = ensure()
  if (c && c.state === 'suspended') void c.resume()
}

type ToneSpec = {
  freq: number
  /** Seconds from now. */
  at?: number
  /** Duration in seconds. */
  dur?: number
  type?: OscillatorType
  gain?: number
  /** Glide to this frequency across the note. */
  sweepTo?: number
  /** Low-pass cutoff, to take the edge off the square/saw shapes. */
  cutoff?: number
}

function tone(c: AudioContext, dest: AudioNode, spec: ToneSpec) {
  const { freq, at = 0, dur = 0.12, type = 'sine', gain = 0.16, sweepTo, cutoff } = spec
  const start = c.currentTime + at + 0.001

  const osc = c.createOscillator()
  osc.type = type
  osc.frequency.setValueAtTime(freq, start)
  if (sweepTo) osc.frequency.exponentialRampToValueAtTime(sweepTo, start + dur)

  const env = c.createGain()
  // A short attack avoids the click you get from starting at full gain, and the
  // exponential tail sounds like a note ending rather than being cut off.
  const attack = Math.min(0.012, dur * 0.25)
  env.gain.setValueAtTime(0.0001, start)
  env.gain.exponentialRampToValueAtTime(gain, start + attack)
  env.gain.exponentialRampToValueAtTime(0.0001, start + dur)

  let node: AudioNode = env
  if (cutoff) {
    const filter = c.createBiquadFilter()
    filter.type = 'lowpass'
    filter.frequency.setValueAtTime(cutoff, start)
    env.connect(filter)
    node = filter
  }

  osc.connect(env)
  node.connect(dest)
  osc.start(start)
  osc.stop(start + dur + 0.03)
}

/**
 * The sounds themselves.
 *
 * Pitches move in the direction of their meaning: correct answers rise, wrong
 * answers fall. A wrong answer is a low, soft buzz rather than a harsh alarm —
 * the student is already being told they were wrong, and the app should not
 * feel like it is scolding them.
 */
const RECIPES: Record<SoundName, (c: AudioContext, dest: AudioNode) => void> = {
  // Restrained UI tick. Quiet enough to hear ten times a minute.
  click: (c, d) => tone(c, d, { freq: 1400, dur: 0.035, type: 'triangle', gain: 0.06 }),

  // Moving the highlight between options: a touch lower and softer than a click,
  // so the two are distinguishable without looking at the screen.
  select: (c, d) => tone(c, d, { freq: 660, dur: 0.045, type: 'sine', gain: 0.07 }),

  // G5 then D6, a rising fourth.
  correct: (c, d) => {
    tone(c, d, { freq: 784, dur: 0.1, type: 'sine', gain: 0.14 })
    tone(c, d, { freq: 1175, at: 0.075, dur: 0.16, type: 'sine', gain: 0.12 })
  },

  // Drop of a fifth, low and short. No buzzer.
  wrong: (c, d) => {
    tone(c, d, { freq: 233, dur: 0.2, type: 'triangle', gain: 0.11, sweepTo: 155, cutoff: 900 })
  },

  // Three quick notes up, for a streak worth noticing.
  streak: (c, d) => {
    tone(c, d, { freq: 698, dur: 0.07, type: 'triangle', gain: 0.1 })
    tone(c, d, { freq: 880, at: 0.06, dur: 0.07, type: 'triangle', gain: 0.1 })
    tone(c, d, { freq: 1175, at: 0.12, dur: 0.12, type: 'triangle', gain: 0.09 })
  },

  // Session over: a C major arpeggio, the only sound long enough to register
  // as a phrase rather than a blip.
  finish: (c, d) => {
    ;[523, 659, 784, 1047].forEach((freq, i) =>
      tone(c, d, { freq, at: i * 0.085, dur: 0.22, type: 'sine', gain: 0.11 }),
    )
  },

  // One second of a timed test running out. Must be unobtrusive: it repeats.
  tick: (c, d) => tone(c, d, { freq: 1568, dur: 0.03, type: 'square', gain: 0.04, cutoff: 2600 }),
}

/** Play a sound. Safe to call before any user gesture: it simply stays silent. */
export function play(name: SoundName) {
  const c = ensure()
  if (!c || !master) return
  try {
    RECIPES[name](c, master)
  } catch {
    // Never let a UI sound break the quiz loop.
  }
}

export const sfx = { play, setEnabled, setVolume, unlock }
