/**
 * Keyboard map for the quiz loop.
 *
 *  1-4     highlight an option (or answer it, in instant mode)
 *  arrows  move the highlight
 *  Enter   answer the highlighted option, then continue to the next question
 *  Esc     quit the test
 */

export const OPTION_KEYS = ['1', '2', '3', '4'] as const

/**
 * `1`-`4` and also `a`-`d`, because anyone who has taken a paper test reaches
 * for the letter of the option they are looking at. Both map to the same index.
 */
const KEY_INDEX: Record<string, number> = {
  '1': 0, '2': 1, '3': 2, '4': 3,
  'a': 0, 'b': 1, 'c': 2, 'd': 3,
}

export function optionIndexFromKey(key: string): number | null {
  const index = KEY_INDEX[key.toLowerCase()]
  return index === undefined ? null : index
}

/**
 * Where an arrow key moves the highlight.
 *
 * Wraps at both ends. Vertical arrows follow the visual order, which is what
 * people actually picture when they look at a list; with the two-column layout
 * on a wide screen the highlight still moves one step at a time rather than
 * skipping, which is easier to track than a true 2-D grid would be.
 */
export function arrowStep(key: string): number | null {
  switch (key) {
    case 'ArrowDown':
    case 'ArrowRight':
      return 1
    case 'ArrowUp':
    case 'ArrowLeft':
      return -1
    default:
      return null
  }
}

/** True when focus is in a field, so the quiz must not swallow the keystroke. */
export function isTypingTarget(target: EventTarget | null): boolean {
  if (!(target instanceof HTMLElement)) return false
  const tag = target.tagName
  return (
    tag === 'INPUT' ||
    tag === 'TEXTAREA' ||
    tag === 'SELECT' ||
    target.isContentEditable
  )
}
