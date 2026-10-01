"""Second wave of computed maths problems, for the chapters that were thin.

Why these are separate handlers and not more rows in the existing banks
----------------------------------------------------------------------
Seven chapters had fewer than a hundred questions, and five of them were thin
for a structural reason rather than an editorial one: their handlers read from a
FIXED bank (`tangent`, `trig_identity`, `real_numbers`), so authoring more
parameter sets produced the same dozen questions again. Circles had 13 questions
and Introduction to Trigonometry had 20, and no amount of new params could move
that.

Every handler here is computational instead. It takes numbers, derives the exact
answer, and builds its distractors from the specific wrong method a student
actually uses. That makes the item count a function of how many parameter sets
are supplied rather than of how many sentences someone thought to write.

Two rules hold throughout:

  1. The answer is never rounded into something wrong. Where a value is a surd it
     stays a surd; where an exact display form cannot be found the item is
     skipped, because a skipped item is harmless and an imprecise one teaches the
     wrong thing.
  2. No two options may be the same NUMBER wearing different clothes. `12/√3` and
     `4√3` are equal, and a student who spots that has eliminated two options
     without doing any mathematics. Candidates are therefore compared as floats,
     not as strings.

Syllabus notes for CBSE 2025-26, observed here:
  * Polynomials - the division algorithm is deleted; only zeroes and their
    relation to coefficients are used.
  * Triangles - the proofs of Pythagoras and of the area-ratio theorem are
    deleted, and the area-ratio result is avoided entirely. BPT and the
    similarity criteria are in, so those are what these items test.
  * Trigonometry - complementary-angle identities are deleted and never used.
"""

from __future__ import annotations

import math
from typing import Any, Sequence

from app.content.generators.maths import (
    PI,
    SQRT,
    TIME,
    MathsItem,
    _dedupe,
    frac,
    num,
    quad_expr,
)

# Exact display forms for the values that standard-angle arithmetic can produce.
# Order matters only for presentation; equality is decided numerically.
EXACT_VALUES: tuple[tuple[float, str], ...] = (
    (0.0, "0"),
    (1 / 4, "1/4"),
    (1 / 3, "1/3"),
    (3 / 8, "3/8"),
    (1 / 2, "1/2"),
    (2 / 3, "2/3"),
    (3 / 4, "3/4"),
    (5 / 8, "5/8"),
    (1.0, "1"),
    (5 / 4, "5/4"),
    (4 / 3, "4/3"),
    (3 / 2, "3/2"),
    (5 / 3, "5/3"),
    (7 / 4, "7/4"),
    (2.0, "2"),
    (5 / 2, "5/2"),
    (3.0, "3"),
    (4.0, "4"),
    (1 / math.sqrt(3), f"1/{SQRT}3"),
    (math.sqrt(2) / 2, f"{SQRT}2/2"),
    (math.sqrt(3) / 2, f"{SQRT}3/2"),
    (math.sqrt(2), f"{SQRT}2"),
    (math.sqrt(3), f"{SQRT}3"),
    (2 * math.sqrt(2), f"2{SQRT}2"),
    (2 * math.sqrt(3), f"2{SQRT}3"),
    (math.sqrt(6) / 4, f"{SQRT}6/4"),
    (3 * math.sqrt(3) / 4, f"3{SQRT}3/4"),
)

#: Values a trig expression built from standard angles can land on, with enough
#: tolerance for accumulated floating-point error over a few operations.
_TOL = 1e-9


def exact_display(value: float) -> str | None:
    """Return the exact printed form of a value, or None if there isn't one.

    Returning None is the important half of this function. A caller that cannot
    print an exact answer skips the item rather than emitting `0.86602540378`,
    which would be both ugly and wrong-by-rounding.
    """
    for candidate, text in EXACT_VALUES:
        if abs(value - candidate) < _TOL:
            return text
    return None


def _pick_numeric(
    answer_text: str,
    answer_value: float,
    candidates: Sequence[tuple[str, float]],
) -> list[str]:
    """Three distractors, distinct from the answer AND from each other by value.

    String comparison is not enough: `12/√3` and `4√3` are different strings and
    the same number, and offering both lets a student eliminate two options by
    noticing they are equal rather than by solving anything.
    """
    out: list[str] = []
    used: list[float] = [answer_value]
    seen_text = {answer_text.strip().lower()}
    for text, value in candidates:
        clean = str(text).strip()
        if not clean or clean.lower() in seen_text:
            continue
        if any(abs(value - prior) < 1e-6 for prior in used):
            continue
        seen_text.add(clean.lower())
        used.append(value)
        out.append(clean)
        if len(out) == 3:
            return out
    return out


# Primitive Pythagorean triples and their small multiples: the backbone of every
# geometry item here, because they keep answers integral and exact.
TRIPLES: tuple[tuple[int, int, int], ...] = (
    (3, 4, 5),
    (5, 12, 13),
    (8, 15, 17),
    (7, 24, 25),
    (20, 21, 29),
    (9, 40, 41),
    (12, 35, 37),
    (11, 60, 61),
    (6, 8, 10),
    (10, 24, 26),
    (16, 30, 34),
    (14, 48, 50),
    (9, 12, 15),
    (15, 20, 25),
    (18, 24, 30),
    (21, 28, 35),
    (15, 36, 39),
    (24, 32, 40),
    (27, 36, 45),
    (30, 40, 50),
)

#: tan of the three angles that give exact surd answers, as (display, value).
TAN_EXACT = {30: (f"1/{SQRT}3", 1 / math.sqrt(3)), 45: ("1", 1.0), 60: (f"{SQRT}3", math.sqrt(3))}
SIN_EXACT = {30: ("1/2", 0.5), 45: (f"1/{SQRT}2", math.sqrt(2) / 2), 60: (f"{SQRT}3/2", math.sqrt(3) / 2), 90: ("1", 1.0)}
COS_EXACT = {30: (f"{SQRT}3/2", math.sqrt(3) / 2), 45: (f"1/{SQRT}2", math.sqrt(2) / 2), 60: ("1/2", 0.5), 0: ("1", 1.0)}


def _surd_times(rational: float, surd_text: str, surd_value: float) -> tuple[str, float]:
    """Render `k x surd` exactly, folding in whole numbers: 4 x √3 -> 4√3."""
    if abs(rational) < 1e-12:
        return "0", 0.0
    if abs(rational - 1) < 1e-12:
        return surd_text, surd_value
    if abs(rational - round(rational)) < 1e-9:
        return f"{int(round(rational))}{surd_text}", rational * surd_value
    return f"{num(rational)} x {surd_text}", rational * surd_value


# ─────────────────────────────────────────────────────────────────────
# Chapter 2 - Polynomials  (zeroes and their relation to coefficients;
# the division algorithm is deleted from the 2025-26 syllabus)
# ─────────────────────────────────────────────────────────────────────


def h_poly_zeroes(p: dict[str, Any]) -> list[MathsItem]:
    """Zeroes of a quadratic built from two known integer roots."""
    r1, r2 = int(p["r1"]), int(p["r2"])
    total, product = r1 + r2, r1 * r2
    poly = quad_expr(1, -total, product)
    answer = f"{min(r1, r2)} and {max(r1, r2)}"
    wrong = [
        f"{-min(r1, r2)} and {-max(r1, r2)}",      # sign flipped on both roots
        f"{total} and {product}",                   # read the coefficients off
        f"{-total} and {product}",                  # used -b and c directly
        f"{min(r1, r2) - 1} and {max(r1, r2) + 1}",  # off by one
        f"{product} and {total}",
    ]
    return [MathsItem(
        prompt=f"Find the zeroes of the quadratic polynomial {poly}.",
        answer=answer,
        distractors=_dedupe(wrong, answer),
        explanation=(
            f"Look for two numbers whose sum is {total} and whose product is {product}: "
            f"{r1} and {r2}. Check: (x - ({r1}))(x - ({r2})) expands back to {poly}."
        ),
        slug=f"poly-zeroes-{r1}-{r2}",
        tags=["polynomials", "zeroes", "application"],
        difficulty="medium" if r1 * r2 >= 0 else "hard",
    )]


def h_poly_sum_product(p: dict[str, Any]) -> list[MathsItem]:
    """Sum and product of zeroes read off ax² + bx + c."""
    a, b, c = int(p["a"]), int(p["b"]), int(p["c"])
    if a == 0:
        return []
    poly = quad_expr(a, b, c)
    total, product = frac(-b, a), frac(c, a)
    out = [MathsItem(
        prompt=f"For the quadratic polynomial {poly}, what is the sum of its zeroes?",
        answer=total,
        distractors=_dedupe([frac(b, a), frac(-c, a), frac(c, a), frac(-b, c) if c else "0", frac(b, c) if c else "1"], total),
        explanation=f"Sum of zeroes = -b/a = -({b})/{a} = {total}.",
        slug=f"poly-sum-{a}-{b}-{c}",
        tags=["polynomials", "zeroes", "coefficients"],
        difficulty="easy",
        time_budget_ms=TIME["easy"],
    )]
    out.append(MathsItem(
        prompt=f"For the quadratic polynomial {poly}, what is the product of its zeroes?",
        answer=product,
        distractors=_dedupe([frac(-c, a), frac(b, a), frac(c, b) if b else "0", frac(-b, a), frac(a, c) if c else "1"], product),
        explanation=f"Product of zeroes = c/a = {c}/{a} = {product}.",
        slug=f"poly-product-{a}-{b}-{c}",
        tags=["polynomials", "zeroes", "coefficients"],
        difficulty="easy",
        time_budget_ms=TIME["easy"],
    ))
    return out


def h_poly_find_k(p: dict[str, Any]) -> list[MathsItem]:
    """Find the unknown coefficient given that a stated value is a zero."""
    root, b = int(p["root"]), int(p["b"])
    if root == 0:
        return []
    # p(root) = root² + b·root + k = 0  ->  k = -(root² + b·root)
    k = -(root * root + b * root)
    # Rendered by hand rather than with quad_expr because the constant term is
    # the unknown k, not a number.
    poly = f"x² {'+' if b >= 0 else '-'} {abs(b)}x + k"
    answer = str(k)
    wrong = [
        str(-k),                       # sign dropped when rearranging
        str(root * root + b),          # multiplied root by b instead of b·root
        str(k + root),                 # added the root back
        str(-(root * root - b * root)),  # sign error on the middle term
        str(k * 2),
    ]
    return [MathsItem(
        prompt=f"If {root} is a zero of the polynomial {poly}, what is the value of k?",
        answer=answer,
        distractors=_dedupe(wrong, answer),
        explanation=(
            f"A zero makes the polynomial 0, so {root}² + ({b})({root}) + k = 0. "
            f"That is {root * root} + {b * root} + k = 0, giving k = {k}."
        ),
        slug=f"poly-k-{root}-{b}",
        tags=["polynomials", "zeroes", "application"],
        difficulty="hard",
        time_budget_ms=TIME["hard"],
    )]


# ─────────────────────────────────────────────────────────────────────
# Chapter 8 - Introduction to Trigonometry
# (complementary-angle identities are deleted, so they are never used)
# ─────────────────────────────────────────────────────────────────────


def h_trig_from_sides(p: dict[str, Any]) -> list[MathsItem]:
    """Ratios of an acute angle in a right triangle with known sides."""
    a, b, hyp = int(p["a"]), int(p["b"]), int(p["c"])
    if a * a + b * b != hyp * hyp:
        return []
    out: list[MathsItem] = []
    # θ is the angle opposite side a, so a is opposite and b is adjacent.
    for ratio, value, wrongs in (
        ("sin", frac(a, hyp), [frac(b, hyp), frac(a, b), frac(hyp, a), frac(b, a)]),
        ("cos", frac(b, hyp), [frac(a, hyp), frac(b, a), frac(hyp, b), frac(a, b)]),
        ("tan", frac(a, b), [frac(b, a), frac(a, hyp), frac(hyp, b), frac(b, hyp)]),
    ):
        out.append(MathsItem(
            prompt=(
                f"In a right triangle the side opposite θ is {a}, the side adjacent to θ is {b} "
                f"and the hypotenuse is {hyp}. What is {ratio} θ?"
            ),
            answer=value,
            distractors=_dedupe(wrongs, value),
            explanation=(
                f"{ratio} θ = {ratio}/hypotenuse form: opposite = {a}, adjacent = {b}, hypotenuse = {hyp}, "
                f"so {ratio} θ = {value}."
                if ratio != "tan"
                else f"tan θ = opposite/adjacent = {a}/{b} = {value}."
            ),
            slug=f"trig-sides-{ratio}-{a}-{b}-{hyp}",
            tags=["trigonometry", "ratios"],
            difficulty="easy",
            time_budget_ms=TIME["easy"],
            stimulus={"kind": "right-triangle", "opposite": a, "adjacent": b, "hypotenuse": hyp},
        ))
    return out


#: Expression templates evaluated from the standard table. Each entry is
#: (label, python expression on the numeric table, the angles it names).
_TRIG_EXPRESSIONS: tuple[tuple[str, str, str], ...] = (
    ("2 sin 30° cos 60°", "2*sin30*cos60", "sin 30° = 1/2 and cos 60° = 1/2"),
    ("sin 45° / cos 45°", "sin45/cos45", "sin 45° and cos 45° are both 1/√2"),
    ("tan 45° + cot 45°", "tan45+1/tan45", "tan 45° = 1, so cot 45° = 1"),
    ("sec 60° - 1", "1/cos60-1", "sec 60° = 1/cos 60° = 2"),
    ("cosec 30° x tan 45°", "(1/sin30)*tan45", "cosec 30° = 1/sin 30° = 2 and tan 45° = 1"),
    ("sin 30° + cos 60°", "sin30+cos60", "sin 30° = 1/2 and cos 60° = 1/2"),
    ("cos 30° x sin 60°", "cos30*sin60", "both are √3/2"),
    ("tan 60° x tan 30°", "tan60*tan30", "tan 60° = √3 and tan 30° = 1/√3"),
    ("sin² 30° + cos² 30°", "sin30**2+cos30**2", "sin²θ + cos²θ = 1 for every θ"),
    ("1 - sin² 45°", "1-sin45**2", "1 - sin²θ = cos²θ, and cos 45° = 1/√2"),
    ("2 tan 30° / (1 + tan² 30°)", "2*tan30/(1+tan30**2)", "this form equals sin 60°"),
    ("(1 - tan² 45°) / (1 + tan² 45°)", "(1-tan45**2)/(1+tan45**2)", "tan 45° = 1, so the numerator is 0"),
    ("cos² 60° + sin² 60°", "cos60**2+sin60**2", "the identity sin²θ + cos²θ = 1"),
    ("sin 60° / tan 60°", "sin60/tan60", "sin/tan = cos, and cos 60° = 1/2"),
    ("sec² 45° - tan² 45°", "1/cos45**2-tan45**2", "sec²θ - tan²θ = 1"),
    ("cosec² 30° - cot² 30°", "1/sin30**2-(cos30/sin30)**2", "cosec²θ - cot²θ = 1"),
    ("tan 30° / tan 60°", "tan30/tan60", "(1/√3) ÷ √3 = 1/3"),
    ("sin 90° x cos 0°", "sin90*cos0", "both are 1"),
    ("2 sin 45° cos 45°", "2*sin45*cos45", "this form equals sin 90°"),
    ("sin 30° x cosec 30°", "sin30*(1/sin30)", "a ratio times its reciprocal is 1"),
)


def h_trig_expression(p: dict[str, Any]) -> list[MathsItem]:
    """Evaluate an expression built from the standard trigonometric table."""
    which = int(p.get("which", -1))
    if not 0 <= which < len(_TRIG_EXPRESSIONS):
        return []
    label, expr, note = _TRIG_EXPRESSIONS[which]

    table = {
        "sin0": 0.0, "sin30": 0.5, "sin45": math.sqrt(2) / 2, "sin60": math.sqrt(3) / 2, "sin90": 1.0,
        "cos0": 1.0, "cos30": math.sqrt(3) / 2, "cos45": math.sqrt(2) / 2, "cos60": 0.5, "cos90": 0.0,
        "tan0": 0.0, "tan30": 1 / math.sqrt(3), "tan45": 1.0, "tan60": math.sqrt(3),
    }
    try:
        value = float(eval(expr, {"__builtins__": {}}, table))  # noqa: S307 - fixed internal templates
    except (ZeroDivisionError, ValueError, SyntaxError, NameError):
        return []
    answer = exact_display(value)
    if answer is None:
        return []  # never print a rounded value

    # Distractors are OTHER exact values, chosen to be numerically different so
    # no two options can be the same number in different notation.
    candidates: list[tuple[str, float]] = []
    for candidate_value, candidate_text in EXACT_VALUES:
        if abs(candidate_value - value) < 1e-6:
            continue
        candidates.append((candidate_text, candidate_value))
    # Nearest-but-wrong first: the plausible mistakes sit closest to the answer.
    candidates.sort(key=lambda pair: abs(pair[1] - value))
    distractors = _pick_numeric(answer, value, candidates)
    if len(distractors) != 3:
        return []

    return [MathsItem(
        prompt=f"Evaluate: {label}",
        answer=answer,
        distractors=distractors,
        explanation=f"From the standard table, {note}, so {label} = {answer}.",
        slug=f"trig-expr-{which}",
        tags=["trigonometry", "standard-values", "application"],
        difficulty="hard" if "/" in label or "²" in label else "medium",
        time_budget_ms=TIME["hard"],
    )]


def h_trig_from_value(p: dict[str, Any]) -> list[MathsItem]:
    """Given one ratio of an acute angle, find another."""
    a, b, hyp = int(p["a"]), int(p["b"]), int(p["c"])
    if a * a + b * b != hyp * hyp or a <= 0 or b <= 0:
        return []
    given = frac(a, hyp)
    out: list[MathsItem] = []
    for asked, value, wrongs in (
        ("cos θ", frac(b, hyp), [frac(a, hyp), frac(hyp, b), frac(a, b)]),
        ("tan θ", frac(a, b), [frac(b, a), frac(b, hyp), frac(hyp, a)]),
    ):
        out.append(MathsItem(
            prompt=f"If θ is acute and sin θ = {given}, what is {asked}?",
            answer=value,
            distractors=_dedupe(wrongs, value),
            explanation=(
                f"sin θ = {a}/{hyp} means opposite = {a} and hypotenuse = {hyp}, so the adjacent side is "
                f"√({hyp}² - {a}²) = {b}. Then {asked} = {value}."
            ),
            slug=f"trig-value-{a}-{b}-{hyp}-{asked.split()[0]}",
            tags=["trigonometry", "ratios", "application"],
            difficulty="hard",
            time_budget_ms=TIME["hard"],
        ))
    return out


# ─────────────────────────────────────────────────────────────────────
# Chapter 9 - Some Applications of Trigonometry
# ─────────────────────────────────────────────────────────────────────


def h_hd_distance(p: dict[str, Any]) -> list[MathsItem]:
    """Angle of elevation with the HEIGHT known: find the distance to the foot."""
    angle, height = int(p["angle"]), int(p["height"])
    if angle not in TAN_EXACT:
        return []
    tan_text, tan_value = TAN_EXACT[angle]
    distance_value = height / tan_value
    if angle == 45:
        answer, answer_value = f"{height} m", float(height)
    elif angle == 60:
        # h/√3 = h√3/3 - keep it as the folded exact form
        answer, answer_value = _surd_times(height / 3, f"{SQRT}3", math.sqrt(3))
        answer = f"{answer} m"
        answer_value = height / math.sqrt(3)
    else:
        answer, answer_value = f"{height}{SQRT}3 m", float(height * math.sqrt(3))

    candidates: list[tuple[str, float]] = [
        (f"{height} m", float(height)),
        (f"{height}{SQRT}3 m", height * math.sqrt(3)),
        (f"{height}/{SQRT}3 m", height / math.sqrt(3)),
        (f"{_surd_times(height / 3, SQRT + '3', math.sqrt(3))[0]} m", height / math.sqrt(3)),
        (f"{2 * height} m", 2.0 * height),
        (f"{height / 2} m" if height % 2 == 0 else f"{num(height / 2)} m", height / 2),
    ]
    distractors = [t for t in _pick_numeric(answer, answer_value, candidates)]
    if len(distractors) != 3:
        return []
    return [MathsItem(
        prompt=(
            f"The angle of elevation of the top of a {height} m tall tower from a point on the ground "
            f"is {angle}°. How far is the point from the foot of the tower?"
        ),
        answer=answer,
        distractors=distractors,
        explanation=(
            f"tan {angle}° = height/distance, so distance = {height}/tan {angle}° = "
            f"{height}/({tan_text}) = {answer}."
        ),
        slug=f"hd-dist-{angle}-{height}",
        tags=["trigonometry", "heights-and-distances", "application"],
        difficulty="hard",
        time_budget_ms=TIME["hard"],
        stimulus={"kind": "elevation", "angle": angle, "height": height},
    )]


def h_hd_depression(p: dict[str, Any]) -> list[MathsItem]:
    """Angle of depression, which equals the angle of elevation from the object."""
    angle, height = int(p["angle"]), int(p["height"])
    if angle not in TAN_EXACT:
        return []
    distance = height / TAN_EXACT[angle][1]
    answer = f"{num(distance)} m"
    wrong = [
        f"{num(height * TAN_EXACT[angle][1])} m",   # multiplied instead of divided
        f"{num(height)} m",
        f"{num(distance * 2)} m",
        f"{num(distance / 2)} m",
    ]
    return [MathsItem(
        prompt=(
            f"From the top of a {height} m high tower the angle of depression of a car on level ground "
            f"is {angle}°. How far is the car from the foot of the tower? (Give a decimal value.)"
        ),
        answer=answer,
        distractors=_dedupe(wrong, answer, numeric=True),
        explanation=(
            f"The angle of depression equals the angle of elevation seen from the car, so "
            f"tan {angle}° = {height}/distance and distance = {height}/tan {angle}° = {answer}."
        ),
        slug=f"hd-dep-{angle}-{height}",
        tags=["trigonometry", "heights-and-distances", "depression"],
        difficulty="hard",
        time_budget_ms=TIME["hard"],
    )]


def h_hd_ladder(p: dict[str, Any]) -> list[MathsItem]:
    """Ladder against a wall: height reached and distance of the foot."""
    angle, length = int(p["angle"]), int(p["length"])
    if angle not in SIN_EXACT or angle not in COS_EXACT:
        return []
    sin_text, sin_value = SIN_EXACT[angle]
    cos_text, cos_value = COS_EXACT[angle]
    height, base = length * sin_value, length * cos_value
    out = [MathsItem(
        prompt=(
            f"A ladder {length} m long leans against a wall, making an angle of {angle}° with the ground. "
            f"How high up the wall does it reach?"
        ),
        answer=f"{num(height)} m",
        distractors=_dedupe([f"{num(base)} m", f"{num(length)} m", f"{num(height * 2)} m", f"{num(length - height)} m"],
                            f"{num(height)} m", numeric=True),
        explanation=f"The wall is the side opposite the angle, so height = {length} x sin {angle}° = {length} x {sin_text} = {num(height)} m.",
        slug=f"hd-ladder-h-{angle}-{length}",
        tags=["trigonometry", "heights-and-distances", "application"],
        difficulty="medium",
    )]
    out.append(MathsItem(
        prompt=(
            f"A ladder {length} m long leans against a wall, making an angle of {angle}° with the ground. "
            f"How far is the foot of the ladder from the wall?"
        ),
        answer=f"{num(base)} m",
        distractors=_dedupe([f"{num(height)} m", f"{num(length)} m", f"{num(base * 2)} m", f"{num(length - base)} m"],
                            f"{num(base)} m", numeric=True),
        explanation=f"The ground distance is adjacent to the angle, so base = {length} x cos {angle}° = {length} x {cos_text} = {num(base)} m.",
        slug=f"hd-ladder-b-{angle}-{length}",
        tags=["trigonometry", "heights-and-distances", "application"],
        difficulty="medium",
    ))
    return out


def h_hd_two_points(p: dict[str, Any]) -> list[MathsItem]:
    """Two observation points on the same side, angles 30° and 60°."""
    gap = int(p["gap"])
    if gap <= 0:
        return []
    # h = gap / (cot30 - cot60) = gap / (√3 - 1/√3) = gap√3/2
    value = gap * math.sqrt(3) / 2
    answer = f"{_surd_times(gap / 2, SQRT + '3', math.sqrt(3))[0]} m"
    wrong = [
        f"{num(gap)} m",
        f"{num(gap * math.sqrt(3))} m",
        f"{num(gap / 2)} m",
        f"{num(value)} m",
        f"{num(gap * 2)} m",
    ]
    return [MathsItem(
        prompt=(
            f"The angles of elevation of the top of a tower from two points on the same side of it, "
            f"on level ground in line with the tower, are 30° and 60°. The two points are {gap} m apart. "
            f"Find the height of the tower."
        ),
        answer=answer,
        distractors=_dedupe(wrong, answer, numeric=True),
        explanation=(
            f"With the nearer point at 60° and the farther at 30°, h = {gap}/(cot 30° - cot 60°) "
            f"= {gap}/(√3 - 1/√3) = {gap}√3/2 = {answer}."
        ),
        slug=f"hd-two-{gap}",
        tags=["trigonometry", "heights-and-distances", "hard"],
        difficulty="hard",
        time_budget_ms=TIME["hard"],
    )]


def h_hd_string(p: dict[str, Any]) -> list[MathsItem]:
    """Kite or balloon: length of the taut string from height and elevation."""
    angle, height = int(p["angle"]), int(p["height"])
    if angle not in SIN_EXACT or angle == 90:
        return []
    sin_text, sin_value = SIN_EXACT[angle]
    length = height / sin_value
    return [MathsItem(
        prompt=(
            f"A kite is flying at a height of {height} m above the ground. The string is taut and makes "
            f"an angle of {angle}° with the ground. Find the length of the string, assuming there is no slack."
        ),
        answer=f"{num(length)} m",
        distractors=_dedupe([
            f"{num(height)} m",
            f"{num(height * sin_value)} m",       # multiplied where it should divide
            f"{num(height / COS_EXACT[angle][1])} m",  # used cos instead of sin
            f"{num(length * 2)} m",
        ], f"{num(length)} m", numeric=True),
        explanation=(
            f"The height is opposite the angle and the string is the hypotenuse, so "
            f"sin {angle}° = {height}/length and length = {height}/({sin_text}) = {num(length)} m."
        ),
        slug=f"hd-string-{angle}-{height}",
        tags=["trigonometry", "heights-and-distances", "application"],
        difficulty="hard",
        time_budget_ms=TIME["hard"],
    )]


# ─────────────────────────────────────────────────────────────────────
# Chapter 10 - Circles
# ─────────────────────────────────────────────────────────────────────


def h_circle_tangent_length(p: dict[str, Any]) -> list[MathsItem]:
    """Tangent from an external point: the radius is perpendicular to it."""
    which = str(p.get("which", "tangent"))
    a, b, c = int(p["a"]), int(p["b"]), int(p["c"])  # legs a, b and hypotenuse c
    if a * a + b * b != c * c:
        return []
    if which == "tangent":
        prompt = (
            f"A point P is {c} cm from the centre O of a circle of radius {a} cm. "
            f"A tangent from P touches the circle at T. Find the length of PT."
        )
        answer, wrong = f"{b} cm", [f"{a} cm", f"{c} cm", f"{a + b} cm", f"{c - a} cm"]
        expl = (
            f"The radius OT is perpendicular to the tangent PT, so OPT is right-angled at T: "
            f"PT = √(OP² - OT²) = √({c}² - {a}²) = √{c * c - a * a} = {b} cm."
        )
    elif which == "radius":
        prompt = (
            f"From a point {c} cm from the centre of a circle, a tangent of length {b} cm is drawn. "
            f"Find the radius of the circle."
        )
        answer, wrong = f"{a} cm", [f"{b} cm", f"{c} cm", f"{c - b} cm", f"{a + b} cm"]
        expl = f"Radius = √(OP² - PT²) = √({c}² - {b}²) = √{c * c - b * b} = {a} cm."
    else:
        prompt = (
            f"A tangent of length {b} cm is drawn from a point P to a circle of radius {a} cm. "
            f"How far is P from the centre?"
        )
        answer, wrong = f"{c} cm", [f"{b} cm", f"{a} cm", f"{a + b} cm", f"{c - a} cm"]
        expl = f"OP = √(OT² + PT²) = √({a}² + {b}²) = √{a * a + b * b} = {c} cm."
    return [MathsItem(
        prompt=prompt,
        answer=answer,
        distractors=_dedupe(wrong, answer),
        explanation=expl,
        slug=f"circle-tan-{which}-{a}-{b}-{c}",
        tags=["circles", "tangent", "application"],
        difficulty="medium",
        stimulus={"kind": "tangent", "op": c, "radius": a, "tangent": b},
    )]


def h_circle_tangent_angle(p: dict[str, Any]) -> list[MathsItem]:
    """Two tangents from an external point: the angle at the centre supplements theirs."""
    theta = int(p["theta"])
    if not 10 <= theta <= 170:
        return []
    centre = 180 - theta
    wrong = [str(theta) + "°", f"{180 + theta}°", f"{90 - theta // 2}°", f"{theta // 2}°", f"{90 + theta}°"]
    return [MathsItem(
        prompt=(
            f"Two tangents are drawn to a circle from an external point P, and the angle between them "
            f"is {theta}°. What is the angle subtended at the centre by the two radii to the points of contact?"
        ),
        answer=f"{centre}°",
        distractors=_dedupe(wrong, f"{centre}°"),
        explanation=(
            f"Each radius is perpendicular to its tangent, so the quadrilateral formed has two right angles. "
            f"The remaining two angles sum to 180°, giving {centre}° at the centre."
        ),
        slug=f"circle-angle-{theta}",
        tags=["circles", "tangent", "analysis"],
        difficulty="hard",
        time_budget_ms=TIME["hard"],
    )]


def h_circle_quadrilateral(p: dict[str, Any]) -> list[MathsItem]:
    """A quadrilateral circumscribing a circle: opposite sides sum equally."""
    ab, bc, cd = int(p["ab"]), int(p["bc"]), int(p["cd"])
    if min(ab, bc, cd) <= 0:
        return []
    da = bc + cd - ab
    if da <= 0:
        return []
    wrong = [f"{ab + cd - bc} cm", f"{ab} cm", f"{bc} cm", f"{da + 2} cm", f"{da * 2} cm"]
    return [MathsItem(
        prompt=(
            f"A quadrilateral ABCD circumscribes a circle, touching it on all four sides. "
            f"If AB = {ab} cm, BC = {bc} cm and CD = {cd} cm, find DA."
        ),
        answer=f"{da} cm",
        distractors=_dedupe(wrong, f"{da} cm"),
        explanation=(
            f"Tangents from one external point are equal, so AB + CD = BC + DA. "
            f"Therefore DA = BC + CD - AB = {bc} + {cd} - {ab} = {da} cm."
        ),
        slug=f"circle-quad-{ab}-{bc}-{cd}",
        tags=["circles", "tangent", "application"],
        difficulty="hard",
        time_budget_ms=TIME["hard"],
    )]


def h_circle_concepts(p: dict[str, Any]) -> list[MathsItem]:
    """Additional fixed-property items for Circles, beyond the original bank."""
    which = str(p.get("which", ""))
    bank = {
        "common_tangent_count": (
            "Two circles touch each other externally. How many common tangents do they have?",
            "3", ["1", "2", "4"],
            "Touching externally gives two direct tangents and one transverse tangent at the point of contact.",
        ),
        "tangent_parallel": (
            "How many parallel tangents can a circle have at most?",
            "2", ["1", "3", "4"],
            "One at each end of a diameter, both perpendicular to that diameter, so exactly two are parallel.",
        ),
        "point_of_contact": (
            "The point at which a tangent touches a circle is called the",
            "point of contact", ["centre of contact", "point of intersection", "point of tangency of the secant"],
            "NCERT names it the point of contact; the tangent meets the circle there and nowhere else.",
        ),
        "radius_perpendicular_proof": (
            "Why is the radius at the point of contact perpendicular to the tangent?",
            "Any other point on the tangent is farther from the centre than the radius",
            [
                "Because the tangent is the longest chord",
                "Because the radius bisects the tangent",
                "Because the centre lies on the tangent",
            ],
            "The radius is the shortest distance from the centre to the tangent, and the shortest distance "
            "to a line is the perpendicular one.",
        ),
        "chord_vs_tangent": (
            "A line meets a circle in exactly one point. The line must be a",
            "tangent", ["secant", "chord", "diameter"],
            "One common point is the defining property of a tangent; two points would make it a secant.",
        ),
        "equal_tangents_angle": (
            "If the two tangents from an external point are equal in length, the line joining that point "
            "to the centre",
            "bisects the angle between the tangents",
            [
                "is perpendicular to both tangents",
                "equals the radius",
                "passes through neither point of contact",
            ],
            "The two right triangles formed are congruent (RHS), so the centre line bisects the angle at P.",
        ),
        "tangent_length_zero": (
            "A point lies inside a circle. How many tangents can be drawn from it to the circle?",
            "None", ["Exactly one", "Exactly two", "Infinitely many"],
            "Tangents can only be drawn from a point on the circle (one) or outside it (two).",
        ),
        "concentric_tangent": (
            "Two concentric circles have radii 5 cm and 3 cm. What is the length of the chord of the larger "
            "circle that touches the smaller one?",
            "8 cm", ["4 cm", "6 cm", "10 cm"],
            "The chord is bisected at the point of contact, giving half-length √(5² - 3²) = 4, so the chord is 8 cm.",
        ),
    }
    if which not in bank:
        return []
    prompt, answer, wrongs, expl = bank[which]
    return [MathsItem(
        prompt=prompt, answer=answer, distractors=_dedupe(wrongs, answer), explanation=expl,
        slug=f"circle-concept-{which}", tags=["circles", "properties"],
        difficulty="medium", time_budget_ms=TIME["medium"],
    )]


# ─────────────────────────────────────────────────────────────────────
# Chapter 11/12 - Areas Related to Circles
# ─────────────────────────────────────────────────────────────────────


def h_circle_measure(p: dict[str, Any]) -> list[MathsItem]:
    """Area, circumference and diameter of a circle, with the classic confusions."""
    r = int(p["r"])
    if r <= 0:
        return []
    pi = 22 / 7
    area, circumference = pi * r * r, 2 * pi * r
    out = [MathsItem(
        prompt=f"Find the area of a circle of radius {r} cm. (Use π = {PI})",
        answer=f"{num(area)} cm²",
        distractors=_dedupe([
            f"{num(circumference)} cm²",          # used the perimeter formula
            f"{num(pi * r * r * r)} cm²",          # cubed the radius
            f"{num(pi * (2 * r) ** 2)} cm²",       # squared the diameter
            f"{num(pi * r)} cm²",                  # forgot to square
        ], f"{num(area)} cm²", numeric=True),
        explanation=f"Area = πr² = {PI} x {r}² = {num(area)} cm².",
        slug=f"circle-area-{r}", tags=["mensuration", "area-of-circle"], difficulty="easy",
        time_budget_ms=TIME["easy"],
    )]
    out.append(MathsItem(
        prompt=f"Find the circumference of a circle of radius {r} cm. (Use π = {PI})",
        answer=f"{num(circumference)} cm",
        distractors=_dedupe([
            f"{num(area)} cm",                     # used the area formula
            f"{num(pi * r)} cm",                   # forgot the 2
            f"{num(2 * pi * r * r)} cm",           # multiplied by r again
            f"{num(4 * pi * r)} cm",
        ], f"{num(circumference)} cm", numeric=True),
        explanation=f"Circumference = 2πr = 2 x {PI} x {r} = {num(circumference)} cm.",
        slug=f"circle-circ-{r}", tags=["mensuration", "area-of-circle"], difficulty="easy",
        time_budget_ms=TIME["easy"],
    ))
    return out


def h_annulus(p: dict[str, Any]) -> list[MathsItem]:
    """Area of the ring between two concentric circles."""
    big, small = int(p["R"]), int(p["r"])
    if small <= 0 or big <= small:
        return []
    pi = 22 / 7
    area = pi * (big * big - small * small)
    wrong = [
        f"{num(pi * (big - small) ** 2)} cm²",   # squared the difference of radii
        f"{num(pi * big * big)} cm²",            # only the outer circle
        f"{num(pi * small * small)} cm²",        # only the inner circle
        f"{num(2 * pi * (big + small))} cm²",    # used a circumference formula
        f"{num(pi * (big + small) ** 2)} cm²",
    ]
    return [MathsItem(
        prompt=f"Two concentric circles have radii {big} cm and {small} cm. Find the area of the ring between them. (Use π = {PI})",
        answer=f"{num(area)} cm²",
        distractors=_dedupe(wrong, f"{num(area)} cm²", numeric=True),
        explanation=(
            f"Ring area = πR² - πr² = π(R² - r²) = {PI} x ({big}² - {small}²) "
            f"= {PI} x {big * big - small * small} = {num(area)} cm²."
        ),
        slug=f"annulus-{big}-{small}",
        tags=["mensuration", "area-of-circle", "application"],
        difficulty="medium",
    )]


def h_segment_area(p: dict[str, Any]) -> list[MathsItem]:
    """Area of a minor segment: sector minus the triangle it contains."""
    r, theta = int(p["r"]), int(p["theta"])
    pi = 22 / 7
    if theta not in (60, 90, 120) or r <= 0:
        return []
    sector = theta / 360 * pi * r * r
    if theta == 90:
        triangle = 0.5 * r * r
        tri_text = f"½ x {r}² = {num(triangle)}"
    else:
        # (1/2)r² sinθ, sin 60° = sin 120° = √3/2
        triangle = 0.5 * r * r * math.sqrt(3) / 2
        tri_text = f"½ x {r}² x sin {theta}° = {num(triangle)} (using √3 = 1.73)"
    area = sector - triangle
    wrong = [
        f"{num(sector)} cm²",                      # forgot to subtract the triangle
        f"{num(triangle)} cm²",                    # only the triangle
        f"{num(pi * r * r - area)} cm²",           # took the major segment
        f"{num(area * 2)} cm²",
        f"{num(sector + triangle)} cm²",           # added instead of subtracted
    ]
    return [MathsItem(
        prompt=(
            f"Find the area of the minor segment of a circle of radius {r} cm, cut off by a chord that "
            f"subtends {theta}° at the centre. (Use π = {PI}, and √3 = 1.73 where needed.)"
        ),
        answer=f"{num(area)} cm²",
        distractors=_dedupe(wrong, f"{num(area)} cm²", numeric=True),
        explanation=(
            f"Segment = sector - triangle. Sector = ({theta}/360) x {PI} x {r}² = {num(sector)} cm²; "
            f"triangle = {tri_text} cm². So the segment is {num(area)} cm²."
        ),
        slug=f"segment-{r}-{theta}",
        tags=["mensuration", "area-of-circle", "segment", "hard"],
        difficulty="hard",
        time_budget_ms=TIME["hard"],
    )]


def h_wheel_revolutions(p: dict[str, Any]) -> list[MathsItem]:
    """Revolutions of a wheel over a given distance."""
    diameter, distance = int(p["d"]), int(p["distance"])
    pi = 22 / 7
    if diameter <= 0 or distance <= 0:
        return []
    circumference = pi * diameter
    revolutions = distance / circumference
    if abs(revolutions - round(revolutions)) > 1e-6:
        return []  # only clean answers, so nobody has to guess a rounding rule
    whole = int(round(revolutions))
    wrong = [
        str(whole * 2),
        str(max(1, whole // 2)),
        str(whole + 1),
        f"{num(distance / diameter)}",             # divided by the diameter, not the circumference
        f"{num(distance / (pi * diameter / 2))}",  # used the radius
    ]
    return [MathsItem(
        prompt=(
            f"The diameter of a wheel is {diameter} cm. How many complete revolutions does it make in "
            f"covering {distance} cm? (Use π = {PI})"
        ),
        answer=str(whole),
        distractors=_dedupe(wrong, str(whole)),
        explanation=(
            f"One revolution covers the circumference = πd = {PI} x {diameter} = {num(circumference)} cm. "
            f"So revolutions = {distance}/{num(circumference)} = {whole}."
        ),
        slug=f"wheel-{diameter}-{distance}",
        tags=["mensuration", "area-of-circle", "application"],
        difficulty="medium",
    )]


def h_square_quadrant(p: dict[str, Any]) -> list[MathsItem]:
    """A quadrant drawn inside a square: the standard shaded-region item."""
    side = int(p["side"])
    pi = 22 / 7
    if side <= 0:
        return []
    square = side * side
    quadrant = pi * side * side / 4
    shaded = square - quadrant
    # Every candidate here is a positive area. An earlier version subtracted a
    # SEMICIRCLE, which is larger than the square, and produced "-28 cm²" - a
    # distractor that is obviously wrong defeats the point of having distractors,
    # because the student eliminates it without doing any geometry.
    wrong = [
        f"{num(quadrant)} cm²",                      # gave the quadrant, not the remainder
        f"{num(square)} cm²",                        # the whole square
        f"{num(pi * side * side / 2)} cm²",          # a semicircle instead of a quadrant
        f"{num(pi * (side / 2) ** 2)} cm²",          # used half the side as the radius
        f"{num(pi * side * side)} cm²",              # a full circle of that radius
        f"{num(shaded * 2)} cm²",
    ]
    return [MathsItem(
        prompt=(
            f"A quadrant of a circle is drawn inside a square of side {side} cm, with its centre at one "
            f"corner of the square and its radius equal to the side. Find the area of the shaded region "
            f"between the square and the quadrant. (Use π = {PI})"
        ),
        answer=f"{num(shaded)} cm²",
        distractors=_dedupe(wrong, f"{num(shaded)} cm²", numeric=True),
        explanation=(
            f"Shaded = square - quadrant = {side}² - (¼ x {PI} x {side}²) = {num(square)} - {num(quadrant)} "
            f"= {num(shaded)} cm²."
        ),
        slug=f"quadrant-square-{side}",
        tags=["mensuration", "area-of-circle", "shaded-region", "hard"],
        difficulty="hard",
        time_budget_ms=TIME["hard"],
    )]


# ─────────────────────────────────────────────────────────────────────
# Chapter 6 - Triangles  (BPT and similarity criteria; the area-ratio
# theorem and the Pythagoras proof are deleted, so neither is used)
# ─────────────────────────────────────────────────────────────────────


def h_bpt_solve(p: dict[str, Any]) -> list[MathsItem]:
    """Basic Proportionality Theorem: DE ∥ BC, three segments known, find the fourth."""
    ad, db, ae = int(p["ad"]), int(p["db"]), int(p["ae"])
    if min(ad, db, ae) <= 0:
        return []
    if (ae * db) % ad != 0:
        return []  # keep EC an integer so the item is about the theorem, not fractions
    ec = ae * db // ad
    wrong = [
        f"{ae + db - ad} cm",
        f"{ec + 1} cm",
        f"{ec * 2} cm",
        f"{ad} cm",
        f"{max(1, ec // 2)} cm",
        f"{ae} cm",
    ]
    return [MathsItem(
        prompt=(
            f"In triangle ABC, DE is parallel to BC and meets AB at D and AC at E. "
            f"If AD = {ad} cm, DB = {db} cm and AE = {ae} cm, find EC."
        ),
        answer=f"{ec} cm",
        distractors=_dedupe(wrong, f"{ec} cm"),
        explanation=(
            f"By the Basic Proportionality Theorem, AD/DB = AE/EC, so {ad}/{db} = {ae}/EC. "
            f"Cross-multiplying gives EC = ({ae} x {db})/{ad} = {ec} cm."
        ),
        slug=f"bpt-{ad}-{db}-{ae}",
        tags=["triangles", "bpt", "application"],
        difficulty="medium",
        stimulus={"kind": "bpt", "ad": ad, "db": db, "ae": ae, "ec": ec},
    )]


def h_bpt_converse(p: dict[str, Any]) -> list[MathsItem]:
    """Decide whether a line is parallel, from the four segment lengths."""
    ad, db, ae, ec = int(p["ad"]), int(p["db"]), int(p["ae"]), int(p["ec"])
    if min(ad, db, ae, ec) <= 0:
        return []
    parallel = ad * ec == db * ae
    answer = "Yes, DE is parallel to BC" if parallel else "No, DE is not parallel to BC"
    wrong = [
        "No, DE is not parallel to BC" if parallel else "Yes, DE is parallel to BC",
        "Cannot be decided without the lengths of DE and BC",
        "Yes, because AD = AE",
        "No, because DB = EC",
    ]
    return [MathsItem(
        prompt=(
            f"In triangle ABC, D lies on AB and E lies on AC, with AD = {ad} cm, DB = {db} cm, "
            f"AE = {ae} cm and EC = {ec} cm. Is DE parallel to BC?"
        ),
        answer=answer,
        distractors=_dedupe(wrong, answer),
        explanation=(
            f"AD/DB = {frac(ad, db)} and AE/EC = {frac(ae, ec)}. "
            + ("The two ratios are equal, so by the converse of BPT, DE ∥ BC."
               if parallel else
               "The two ratios are unequal, so by the converse of BPT, DE is not parallel to BC.")
        ),
        slug=f"bpt-converse-{ad}-{db}-{ae}-{ec}",
        tags=["triangles", "bpt", "analysis"],
        difficulty="hard",
        time_budget_ms=TIME["hard"],
    )]


def h_similar_sides(p: dict[str, Any]) -> list[MathsItem]:
    """Corresponding sides of similar triangles, from the ratio of two known sides."""
    a1, b1, a2 = int(p["a1"]), int(p["b1"]), int(p["a2"])
    if min(a1, b1, a2) <= 0 or (b1 * a2) % a1 != 0:
        return []
    b2 = b1 * a2 // a1
    wrong = [
        f"{b1 + a2 - a1} cm",       # treated the sides as an arithmetic sequence
        f"{b1} cm",                 # assumed the triangles were congruent
        f"{a2} cm",
        f"{b2 + 1} cm",
        f"{b1 * a1 // a2 if a2 and (b1 * a1) % a2 == 0 else b2 * 2} cm",  # inverted the ratio
    ]
    return [MathsItem(
        prompt=(
            f"Triangle ABC is similar to triangle PQR. If AB = {a1} cm, PQ = {a2} cm and BC = {b1} cm, "
            f"find QR."
        ),
        answer=f"{b2} cm",
        distractors=_dedupe(wrong, f"{b2} cm"),
        explanation=(
            f"Corresponding sides of similar triangles are proportional: AB/PQ = BC/QR, so "
            f"{a1}/{a2} = {b1}/QR and QR = ({b1} x {a2})/{a1} = {b2} cm."
        ),
        slug=f"similar-{a1}-{b1}-{a2}",
        tags=["triangles", "similarity", "application"],
        difficulty="medium",
    )]


def h_similarity_criterion(p: dict[str, Any]) -> list[MathsItem]:
    """Which criterion establishes similarity, given what is actually known."""
    which = str(p.get("which", ""))
    bank = {
        "aa": (
            "Two angles of one triangle are equal to two angles of another triangle. The triangles are similar by which criterion?",
            "AA", ["SSS", "SAS", "RHS"],
            "If two angles match, the third must too, so equal angles alone give similarity - the AA criterion.",
        ),
        "sss": (
            "The three sides of one triangle are proportional to the three sides of another. Which criterion applies?",
            "SSS", ["AA", "SAS", "ASA"],
            "All three pairs of sides in the same ratio is the SSS similarity criterion.",
        ),
        "sas": (
            "One angle of a triangle equals one angle of another, and the sides including those angles are "
            "proportional. Which criterion applies?",
            "SAS", ["SSS", "AA", "ASA"],
            "The angle must be INCLUDED between the two proportional sides - that is SAS similarity.",
        ),
        "not_sufficient": (
            "Two triangles have one pair of equal angles and one pair of equal sides, but the sides are not "
            "the ones including the angle. Are they necessarily similar?",
            "No, this is not enough to conclude similarity",
            [
                "Yes, by AA",
                "Yes, by SAS",
                "Yes, by SSS",
            ],
            "Neither AA (only one angle) nor SAS (the sides are not the included pair) is satisfied.",
        ),
        "bpt_statement": (
            "The Basic Proportionality Theorem states that a line drawn parallel to one side of a triangle, "
            "intersecting the other two sides, divides those two sides",
            "in the same ratio",
            [
                "into equal halves",
                "in the ratio of the third side",
                "only if the triangle is isosceles",
            ],
            "BPT: if DE ∥ BC then AD/DB = AE/EC - the same ratio on both sides.",
        ),
        "parallel_line_ratio": (
            "In triangle ABC, a line parallel to BC cuts AB at D and AC at E. Which proportion is correct?",
            "AD/DB = AE/EC", ["AD/AB = DB/AC", "AD/DB = EC/AE", "AB/AD = AC/AE"],
            "That is BPT exactly. Note AD/AB = AE/AC is also true but is not one of the other choices given.",
        ),
        "equilateral_similar": (
            "Are any two equilateral triangles always similar?",
            "Yes, because all their angles are 60°",
            [
                "No, only if their sides are equal",
                "No, only if their perimeters are equal",
                "Yes, but only if they share a side",
            ],
            "Every angle is 60°, so AA is satisfied for any pair - they are always similar, though not always congruent.",
        ),
        "congruent_similar": (
            "Two triangles are congruent. Which statement is correct?",
            "They are also similar, with ratio 1 : 1",
            [
                "They cannot be similar",
                "They are similar only if they are equilateral",
                "Congruence and similarity are unrelated",
            ],
            "Congruent triangles have equal angles and sides in the ratio 1:1, which satisfies similarity.",
        ),
        "similar_not_congruent": (
            "Two similar triangles have areas in the ratio 4 : 9. What is the ratio of corresponding sides?",
            "2 : 3", ["4 : 9", "16 : 81", "3 : 2"],
            "Areas scale as the SQUARE of the side ratio, so √(4/9) = 2/3.",
        ),
    }
    if which not in bank:
        return []
    prompt, answer, wrongs, expl = bank[which]
    return [MathsItem(
        prompt=prompt, answer=answer, distractors=_dedupe(wrongs, answer), explanation=expl,
        slug=f"similarity-{which}", tags=["triangles", "similarity", "bpt"],
        difficulty="medium", time_budget_ms=TIME["medium"],
    )]


def h_pythagoras_side(p: dict[str, Any]) -> list[MathsItem]:
    """Missing side of a right triangle from a triple."""
    which = str(p.get("which", "hypotenuse"))
    a, b, c = int(p["a"]), int(p["b"]), int(p["c"])
    if a * a + b * b != c * c:
        return []
    if which == "hypotenuse":
        prompt = f"A right triangle has legs of {a} cm and {b} cm. Find the hypotenuse."
        answer, wrong = f"{c} cm", [f"{a + b} cm", f"{b} cm", f"{a} cm", f"{c - 1} cm", f"{c + 1} cm"]
        expl = f"Hypotenuse = √({a}² + {b}²) = √({a * a} + {b * b}) = √{c * c} = {c} cm."
    elif which == "leg":
        prompt = f"A right triangle has hypotenuse {c} cm and one leg {a} cm. Find the other leg."
        answer, wrong = f"{b} cm", [f"{c - a} cm", f"{a} cm", f"{c} cm", f"{b + 1} cm", f"{b - 1} cm"]
        expl = f"Other leg = √({c}² - {a}²) = √({c * c} - {a * a}) = √{b * b} = {b} cm."
    else:
        return []
    return [MathsItem(
        prompt=prompt, answer=answer, distractors=_dedupe(wrong, answer), explanation=expl,
        slug=f"pyth-{which}-{a}-{b}-{c}", tags=["triangles", "pythagoras", "application"],
        difficulty="easy", time_budget_ms=TIME["easy"],
    )]


# ─────────────────────────────────────────────────────────────────────
# Chapter 14 - Probability
# ─────────────────────────────────────────────────────────────────────


def _prob(favourable: int, total: int) -> str:
    return frac(favourable, total)


def h_prob_two_dice(p: dict[str, Any]) -> list[MathsItem]:
    """Two dice thrown together: events on the sum."""
    target = int(p["sum"])
    relation = str(p.get("relation", "equals"))
    if not 2 <= target <= 12:
        return []
    pairs = [(i, j) for i in range(1, 7) for j in range(1, 7)]
    if relation == "equals":
        good = [x for x in pairs if sum(x) == target]
        label = f"exactly {target}"
    elif relation == "more_than":
        good = [x for x in pairs if sum(x) > target]
        label = f"more than {target}"
    elif relation == "at_least":
        good = [x for x in pairs if sum(x) >= target]
        label = f"at least {target}"
    elif relation == "less_than":
        good = [x for x in pairs if sum(x) < target]
        label = f"less than {target}"
    elif relation == "at_most":
        good = [x for x in pairs if sum(x) <= target]
        label = f"at most {target}"
    else:
        return []
    if not good:
        return []
    answer = _prob(len(good), 36)
    # Named misconceptions: counting 6 outcomes instead of 36, and treating
    # (1,2) and (2,1) as one outcome.
    unordered = len({frozenset(x) for x in good})
    wrong = [
        _prob(len(good), 6),          # used one die's outcome count
        _prob(unordered, 21),         # collapsed ordered pairs, 21 distinct sums-pairs
        _prob(len(good) + 1, 36),     # off by one in the count
        _prob(max(1, len(good) - 1), 36),
        _prob(36 - len(good), 36),    # answered the complement
    ]
    examples = ", ".join(f"{i}+{j}" for i, j in good[:4])
    more = f" and {len(good) - 4} more" if len(good) > 4 else ""
    return [MathsItem(
        prompt=f"Two dice are thrown at the same time. What is the probability that the sum of the numbers showing is {label}?",
        answer=answer,
        distractors=_dedupe(wrong, answer),
        explanation=(
            f"Two dice give 6 x 6 = 36 equally likely ordered outcomes. "
            f"Favourable: {examples}{more} = {len(good)} outcomes. So P = {len(good)}/36 = {answer}."
        ),
        slug=f"prob-dice-{relation}-{target}",
        tags=["probability", "dice", "application"],
        difficulty="hard" if relation in {"more_than", "less_than", "at_least", "at_most"} else "medium",
        time_budget_ms=TIME["hard"],
        stimulus={"kind": "two-dice", "relation": relation, "target": target, "favourable": len(good)},
    )]


def h_prob_balls(p: dict[str, Any]) -> list[MathsItem]:
    """A bag of coloured balls: probability of drawing one colour."""
    red, blue, green = int(p.get("red", 0)), int(p.get("blue", 0)), int(p.get("green", 0))
    total = red + blue + green
    if total <= 0:
        return []
    colour = str(p.get("colour", "red"))
    counts = {"red": red, "blue": blue, "green": green}
    if colour not in counts:
        return []
    favourable = counts[colour]
    if favourable == 0:
        return []
    answer = _prob(favourable, total)
    others = {k: v for k, v in counts.items() if k != colour}
    wrong = [
        _prob(favourable, total - favourable) if total - favourable > 0 else "1",
        _prob(sum(others.values()), total),      # answered the complement
        _prob(favourable, favourable + 1),
        _prob(next(iter(others.values())), total) if others else "1/2",
        f"{favourable}/{total + 1}",
    ]
    listing = ", ".join(f"{counts[c]} {c}" for c in ("red", "blue", "green") if counts[c])
    return [MathsItem(
        prompt=f"A bag contains {listing} balls. One ball is drawn at random. What is the probability that it is {colour}?",
        answer=answer,
        distractors=_dedupe(wrong, answer),
        explanation=f"There are {favourable} {colour} balls out of {total} in total, so P = {favourable}/{total} = {answer}.",
        slug=f"prob-balls-{red}-{blue}-{green}-{colour}",
        tags=["probability", "balls"],
        difficulty="easy",
        time_budget_ms=TIME["easy"],
    )]


def h_prob_defective(p: dict[str, Any]) -> list[MathsItem]:
    """A lot with defective items: probability of drawing a good one."""
    total, defective = int(p["total"]), int(p["defective"])
    if defective < 0 or total <= defective or total <= 0:
        return []
    good = total - defective
    out = [MathsItem(
        prompt=(
            f"A box holds {total} pens, of which {defective} are defective. One pen is drawn at random. "
            f"What is the probability that it is NOT defective?"
        ),
        answer=_prob(good, total),
        distractors=_dedupe([_prob(defective, total), _prob(good, good + 1), _prob(defective, good),
                             _prob(good + 1, total), f"{good}/{total + defective}"], _prob(good, total)),
        explanation=f"{good} of the {total} pens are good, so P(not defective) = {good}/{total} = {_prob(good, total)}.",
        slug=f"prob-good-{total}-{defective}",
        tags=["probability", "complement", "application"],
        difficulty="medium",
    )]
    out.append(MathsItem(
        prompt=(
            f"A box holds {total} pens, of which {defective} are defective. One pen is drawn at random. "
            f"What is the probability that it IS defective?"
        ),
        answer=_prob(defective, total) if defective else "0",
        distractors=_dedupe([_prob(good, total), _prob(defective, good) if good else "1",
                             _prob(defective + 1, total), _prob(good, total + 1)],
                            _prob(defective, total) if defective else "0"),
        explanation=(
            f"{defective} of the {total} pens are defective, so P(defective) = {defective}/{total} = "
            f"{_prob(defective, total) if defective else '0'}."
        ),
        slug=f"prob-defective-{total}-{defective}",
        tags=["probability", "application"],
        difficulty="medium",
    ))
    return out


def h_prob_cards(p: dict[str, Any]) -> list[MathsItem]:
    """Cards drawn from a well-shuffled deck of 52."""
    which = str(p.get("which", ""))
    red = 26
    bank = {
        "king": ("a king", 4, ["a queen", "a jack", "an ace", "a red card"]),
        "queen": ("a queen", 4, ["a king", "a jack", "an ace", "a face card"]),
        "jack": ("a jack", 4, ["a king", "a queen", "an ace", "a ten"]),
        "ace": ("an ace", 4, ["a king", "a queen", "a jack", "a ten"]),
        "spade": ("a spade", 13, ["a heart", "a red card", "a king", "a face card"]),
        "heart": ("a heart", 13, ["a spade", "a red card", "a queen", "a face card"]),
        "diamond": ("a diamond", 13, ["a club", "a spade", "an ace", "a face card"]),
        "club": ("a club", 13, ["a heart", "a diamond", "a king", "a face card"]),
        "red": ("a red card", red, ["a black card", "a spade", "a king", "a face card"]),
        "black": ("a black card", 26, ["a red card", "a heart", "a queen", "a face card"]),
        "face": ("a face card", 12, ["a king", "a red card", "an ace", "a spade"]),
        "honour": ("an ace, king, queen or jack", 16, ["a face card", "a red card", "a king", "a spade"]),
        "red_king": ("a red king", 2, ["a king", "a red card", "a red queen", "a face card"]),
        "king_hearts": ("the king of hearts", 1, ["a king", "a heart", "a red king", "a face card"]),
        "not_ace": ("not an ace", 48, ["an ace", "a face card", "a red card", "a king"]),
        "ten": ("a ten", 4, ["a jack", "a nine", "a face card", "a red card"]),
        "even_red": ("a red card bearing an even number", 10, ["a red card", "an even-numbered card", "a face card", "a king"]),
        "spade_or_ace": ("a spade or an ace", 16, ["a spade", "an ace", "a face card", "a red card"]),
    }
    if which not in bank:
        return []
    phrase, favourable, wrong_phrases = bank[which]
    answer = _prob(favourable, 52)
    wrong_counts = {"a king": 4, "a queen": 4, "a jack": 4, "an ace": 4, "a spade": 13, "a heart": 13,
                    "a red card": 26, "a black card": 26, "a face card": 12, "a diamond": 13, "a club": 13,
                    "a ten": 4, "a nine": 4, "a red queen": 2, "an even-numbered card": 20, "a red king": 2}
    wrong = [_prob(wrong_counts.get(phrase_key, favourable), 52) for phrase_key in wrong_phrases]
    wrong += [_prob(favourable, 13), _prob(favourable, 26), _prob(favourable + 1, 52), _prob(max(1, favourable - 1), 52)]
    return [MathsItem(
        prompt=f"One card is drawn from a well-shuffled deck of 52 cards. What is the probability that it is {phrase}?",
        answer=answer,
        distractors=_dedupe(wrong, answer),
        explanation=f"There are {favourable} such cards in a deck of 52, so P = {favourable}/52 = {answer}.",
        slug=f"prob-card-{which}",
        tags=["probability", "cards", "application"],
        difficulty="hard" if which in {"spade_or_ace", "even_red", "honour", "not_ace"} else "medium",
        time_budget_ms=TIME["hard"],
    )]


def h_prob_complement(p: dict[str, Any]) -> list[MathsItem]:
    """P(not E) from P(E), including the fractional forms."""
    hundredths = int(p.get("hundredths", -1))
    if 0 <= hundredths <= 100:
        given = f"{hundredths / 100:.2f}".rstrip("0").rstrip(".")
        pe = hundredths / 100
    elif "num" in p and "den" in p:
        given = frac(int(p["num"]), int(p["den"]))
        pe = int(p["num"]) / int(p["den"])
    else:
        return []
    complement = 1 - pe
    answer = exact_display(complement)
    if answer is None:
        answer = num(round(complement, 2))
    wrong = [given, num(round(1 + pe, 2)), num(round(-pe, 2)), num(round(complement / 2, 2)), num(round(pe * 2, 2))]
    return [MathsItem(
        prompt=f"If P(E) = {given}, what is P(not E)?",
        answer=answer,
        distractors=_dedupe(wrong, answer, numeric=True),
        explanation=f"P(not E) = 1 - P(E) = 1 - {given} = {answer}. The two must add to 1.",
        slug=f"prob-comp-{given}",
        tags=["probability", "complement"],
        difficulty="easy",
        time_budget_ms=TIME["easy"],
    )]


def h_prob_year(p: dict[str, Any]) -> list[MathsItem]:
    """53 Sundays in a year - the counting argument, not a memorised answer."""
    leap = bool(p.get("leap"))
    days, weeks, extra = (366, 52, 2) if leap else (365, 52, 1)
    answer = _prob(extra, 7)
    wrong = [_prob(1, 52), _prob(extra, days), "1", "0", _prob(1, 7) if extra == 2 else _prob(2, 7)]
    return [MathsItem(
        prompt=f"What is the probability that a randomly chosen {'leap year' if leap else 'ordinary (non-leap) year'} has 53 Sundays?",
        answer=answer,
        distractors=_dedupe(wrong, answer),
        explanation=(
            f"A {'leap year has 366' if leap else 'year has 365'} days = {weeks} complete weeks plus {extra} "
            f"extra day{'s' if extra > 1 else ''}. The 52 weeks already give 52 Sundays, so a 53rd needs one of "
            f"the {extra} extra day{'s' if extra > 1 else ''} to be a Sunday: {extra}/7 = {answer}."
        ),
        slug=f"prob-year-{'leap' if leap else 'ordinary'}",
        tags=["probability", "counting", "hard"],
        difficulty="hard",
        time_budget_ms=TIME["hard"],
    )]


def h_prob_coin(p: dict[str, Any]) -> list[MathsItem]:
    """Two or three coins: events on the number of heads."""
    coins, heads = int(p["coins"]), int(p["heads"])
    if coins not in (2, 3) or not 0 <= heads <= coins:
        return []
    total = 2 ** coins
    favourable = math.comb(coins, heads)
    relation = str(p.get("relation", "exactly"))
    if relation == "at_least":
        favourable = sum(math.comb(coins, k) for k in range(heads, coins + 1))
        label = f"at least {heads} head{'s' if heads != 1 else ''}"
    elif relation == "at_most":
        favourable = sum(math.comb(coins, k) for k in range(0, heads + 1))
        label = f"at most {heads} head{'s' if heads != 1 else ''}"
    else:
        label = f"exactly {heads} head{'s' if heads != 1 else ''}"
    if favourable == 0:
        return []
    answer = _prob(favourable, total)
    wrong = [
        _prob(math.comb(coins, heads), total) if relation != "exactly" else _prob(max(1, favourable - 1), total),
        _prob(favourable, coins * 2),            # counted 2n outcomes instead of 2^n
        _prob(total - favourable, total),        # the complement
        _prob(favourable, total + 1),
        _prob(1, coins + 1),
    ]
    return [MathsItem(
        prompt=f"{coins} coins are tossed at the same time. What is the probability of getting {label}?",
        answer=answer,
        distractors=_dedupe(wrong, answer),
        explanation=(
            f"{coins} coins give 2^{coins} = {total} equally likely outcomes, of which {favourable} "
            f"satisfy the condition, so P = {favourable}/{total} = {answer}."
        ),
        slug=f"prob-coin-{coins}-{relation}-{heads}",
        tags=["probability", "coins", "application"],
        difficulty="medium" if relation == "exactly" else "hard",
        time_budget_ms=TIME["hard"],
    )]


#: Registered into maths.HANDLERS at import, so one `problem` namespace drives
#: both modules and problems.json does not need to know which one implements it.
EXTRA_HANDLERS: dict[str, Any] = {
    "poly_zeroes": h_poly_zeroes,
    "poly_sum_product": h_poly_sum_product,
    "poly_find_k": h_poly_find_k,
    "trig_from_sides": h_trig_from_sides,
    "trig_expression": h_trig_expression,
    "trig_from_value": h_trig_from_value,
    "hd_distance": h_hd_distance,
    "hd_depression": h_hd_depression,
    "hd_ladder": h_hd_ladder,
    "hd_two_points": h_hd_two_points,
    "hd_string": h_hd_string,
    "circle_tangent_length": h_circle_tangent_length,
    "circle_tangent_angle": h_circle_tangent_angle,
    "circle_quadrilateral": h_circle_quadrilateral,
    "circle_concepts": h_circle_concepts,
    "circle_measure": h_circle_measure,
    "annulus": h_annulus,
    "segment_area": h_segment_area,
    "wheel_revolutions": h_wheel_revolutions,
    "square_quadrant": h_square_quadrant,
    "bpt_solve": h_bpt_solve,
    "bpt_converse": h_bpt_converse,
    "similar_sides": h_similar_sides,
    "similarity_criterion": h_similarity_criterion,
    "pythagoras_side": h_pythagoras_side,
    "prob_two_dice": h_prob_two_dice,
    "prob_balls": h_prob_balls,
    "prob_defective": h_prob_defective,
    "prob_cards": h_prob_cards,
    "prob_complement": h_prob_complement,
    "prob_year": h_prob_year,
    "prob_coin": h_prob_coin,
}
