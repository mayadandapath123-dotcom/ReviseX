"""Maths generator: parameterised problems -> computed MCQs.

Why this exists separately from the fact generators
---------------------------------------------------
Science items recall a stored value. Maths items must be *computed*, and the
distractors have to be the answers a student gets by applying a real but wrong
method. A random +-1 perturbation would make the item trivially solvable by
elimination, so every distractor here is a named misconception:

    hcf_lcm        -> swapping HCF and LCM, or forgetting to divide the product
    ap_term        -> using n*d instead of (n-1)*d
    quadratic      -> sign error on the roots, or reading off coefficients
    distance       -> adding the legs instead of Pythagoras, or forgetting sqrt
    trig_ratio     -> a different row of the standard table, or sin/cos confusion
    mensuration    -> forgetting the 1/3 on a cone, or using diameter for radius

Handlers return exact strings (fractions and surds included) so nothing is
rounded into a wrong answer. If a handler cannot produce three distinct
plausible distractors it returns None and the item is skipped: a skipped item is
harmless, a padded one is a bad question.

All items are `mcq_single`. The rapid-revision loop is built for four-option
recall, and `numeric_input` would need its own UI path.
"""

from __future__ import annotations

import hashlib
import math
from dataclasses import dataclass, field
from typing import Any, Callable, Sequence

from app.content.generators.base import (
    build_options,
    make_question,
    question_id,
    resolve_location,
    slugify,
    stable_rng,
)
from app.content.schema import QuestionDef
from app.content.validators import content_hash

TIME = {"easy": 12000, "medium": 20000, "hard": 30000}
PI = "22/7"


@dataclass
class MathsItem:
    prompt: str
    answer: str
    distractors: list[str]
    explanation: str
    slug: str
    tags: list[str] = field(default_factory=list)
    difficulty: str = "medium"
    time_budget_ms: int = 20000
    stimulus: dict[str, Any] = field(default_factory=dict)


# --------------------------------------------------------------------------
# numeric formatting
# --------------------------------------------------------------------------

def num(value: float) -> str:
    """Exact-ish rendering: ints stay ints, others keep 2 decimals."""
    if isinstance(value, str):
        return value
    if abs(value - round(value)) < 1e-9:
        return str(int(round(value)))
    return f"{round(value, 2):g}"


def quad_expr(a: int, b: int, c: int) -> str:
    """Render ax^2 + bx + c the way a textbook does (no '1x', no '+ -6')."""
    lead = "x\u00b2" if a == 1 else ("-x\u00b2" if a == -1 else f"{a}x\u00b2")
    if b == 0:
        mid = ""
    else:
        mag = abs(b)
        mid = f" {'+' if b > 0 else '-'} {'x' if mag == 1 else f'{mag}x'}"
    tail = "" if c == 0 else f" {'+' if c > 0 else '-'} {abs(c)}"
    return f"{lead}{mid}{tail}"


def lin_expr(a: int, b: int, c: int) -> str:
    """Render ax + by + c the way a textbook does (coefficients 1 and signs folded)."""
    xterm = "" if a == 0 else ("x" if a == 1 else "-x" if a == -1 else f"{a}x")
    if b == 0:
        yterm = ""
    else:
        mag = "y" if abs(b) == 1 else f"{abs(b)}y"
        yterm = (f" + {mag}" if b > 0 else f" - {mag}") if xterm else (("-" if b < 0 else "") + mag)
    if c == 0:
        cterm = ""
    else:
        cterm = f" {'+' if c > 0 else '-'} {abs(c)}" if (xterm or yterm) else str(c)
    return f"{xterm}{yterm}{cterm}"


def frac(n: int, d: int) -> str:
    if d == 0:
        return "undefined"
    if n % d == 0:
        return str(n // d)
    sign = "-" if (n < 0) != (d < 0) else ""
    g = math.gcd(abs(n), abs(d))
    return f"{sign}{abs(n) // g}/{abs(d) // g}"


# --------------------------------------------------------------------------
# standard trigonometric table (Class 10, Introduction to Trigonometry)
# --------------------------------------------------------------------------

SQRT = "\u221a"
TRIG_TABLE: dict[str, dict[int, str]] = {
    "sin": {0: "0", 30: "1/2", 45: f"1/{SQRT}2", 60: f"{SQRT}3/2", 90: "1"},
    "cos": {0: "1", 30: f"{SQRT}3/2", 45: f"1/{SQRT}2", 60: "1/2", 90: "0"},
    "tan": {0: "0", 30: f"1/{SQRT}3", 45: "1", 60: f"{SQRT}3", 90: "not defined"},
}


# --------------------------------------------------------------------------
# handlers. Each returns a list of MathsItem from one parameter set.
# --------------------------------------------------------------------------

def h_hcf_lcm(p: dict[str, Any]) -> list[MathsItem]:
    a, b = int(p["a"]), int(p["b"])
    h = math.gcd(a, b)
    l = a * b // h
    out = []

    out.append(MathsItem(
        prompt=f"What is the HCF of {a} and {b}?",
        answer=num(h),
        # LCM is the classic swap; 2 is the "smallest common factor" trap;
        # product//l*2 catches students who halve instead of dividing properly.
        distractors=_dedupe([num(l), num(2 if h != 2 else 3), num(h * 2)], num(h), numeric=True),
        explanation=f"Prime factorisation gives HCF({a}, {b}) = {h}. The LCM is {l}, not the HCF.",
        slug=f"hcf-{a}-{b}", tags=["hcf", "number-system"], difficulty="easy",
        time_budget_ms=TIME["easy"],
    ))

    out.append(MathsItem(
        prompt=f"What is the LCM of {a} and {b}?",
        answer=num(l),
        distractors=_dedupe([num(h), num(a * b), num(l // 2 if l % 2 == 0 else l * 2)], num(l), numeric=True),
        explanation=f"LCM({a}, {b}) = {l}. Note HCF x LCM = {h} x {l} = {a * b} = product of the numbers.",
        slug=f"lcm-{a}-{b}", tags=["lcm", "number-system"], difficulty="easy",
        time_budget_ms=TIME["easy"],
    ))

    out.append(MathsItem(
        prompt=f"For two numbers, HCF = {h} and LCM = {l}. What is their product?",
        answer=num(h * l),
        distractors=_dedupe([num(l), num(h + l), num(h * l * 2)], num(h * l), numeric=True),
        explanation=f"Product of two numbers = HCF x LCM = {h} x {l} = {h * l}.",
        slug=f"product-{h}-{l}", tags=["hcf", "lcm", "property"], difficulty="medium",
    ))
    return out


def h_ap_term(p: dict[str, Any]) -> list[MathsItem]:
    a, d, n = int(p["a"]), int(p["d"]), int(p["n"])
    term = a + (n - 1) * d
    shown = ", ".join(str(a + i * d) for i in range(4))
    return [MathsItem(
        prompt=f"Find the {n}th term of the AP: {a}, {a + d}, {a + 2 * d}, ...",
        answer=num(term),
        # n*d instead of (n-1)*d is the single most common AP error.
        distractors=_dedupe(
            [num(a + n * d), num(a - (n - 1) * d), num(term + d), num(term - d), num(a * n)],
            num(term), numeric=True,
        ),
        explanation=f"a{n} = a + (n-1)d = {a} + ({n}-1)({d}) = {a} + {(n - 1) * d} = {term}. Shown AP: {shown}, ...",
        slug=f"ap-term-{a}-{d}-{n}", tags=["ap", "nth-term"], difficulty="medium",
        stimulus={"kind": "ap", "a": a, "d": d, "n": n},
    )]


def h_ap_sum(p: dict[str, Any]) -> list[MathsItem]:
    a, d, n = int(p["a"]), int(p["d"]), int(p["n"])
    total = n * (2 * a + (n - 1) * d) / 2
    return [MathsItem(
        prompt=f"Find the sum of the first {n} terms of the AP with first term {a} and common difference {d}.",
        answer=num(total),
        distractors=_dedupe([
            num(n * (2 * a + (n - 1) * d)),          # forgot the /2
            num(n * (2 * a + n * d) / 2),            # used n*d instead of (n-1)*d
            num(a * n),                              # ignored d entirely
        ], num(total), numeric=True),
        explanation=f"S{n} = n/2 [2a + (n-1)d] = {n}/2 [{2 * a} + {(n - 1) * d}] = {num(total)}.",
        slug=f"ap-sum-{a}-{d}-{n}", tags=["ap", "sum"], difficulty="medium",
        stimulus={"kind": "ap", "a": a, "d": d, "n": n},
    )]


def h_ap_find_d(p: dict[str, Any]) -> list[MathsItem]:
    terms = [int(t) for t in p["terms"]]
    if len(terms) < 3:
        return []
    d = terms[1] - terms[0]
    return [MathsItem(
        prompt=f"What is the common difference of the AP: {', '.join(map(str, terms))}, ...?",
        answer=num(d),
        distractors=_dedupe([num(-d), num(terms[2] - terms[0]), num(d + 1)], num(d)),
        explanation=f"d = a2 - a1 = {terms[1]} - {terms[0]} = {d}.",
        slug=f"ap-d-{terms[0]}-{terms[1]}", tags=["ap", "common-difference"], difficulty="easy",
        time_budget_ms=TIME["easy"],
    )]


def h_quadratic_roots(p: dict[str, Any]) -> list[MathsItem]:
    r1, r2 = int(p["root1"]), int(p["root2"])
    # (x - r1)(x - r2) = x^2 - (r1+r2)x + r1*r2
    b, c = -(r1 + r2), r1 * r2
    expr = quad_expr(1, b, c)
    def pair(u: int, v: int) -> str:
        lo, hi = sorted((u, v))
        return f"{lo}, {hi}" if lo != hi else str(lo)

    answer = pair(r1, r2)
    return [MathsItem(
        prompt=f"Find the roots of the quadratic equation {expr} = 0.",
        answer=answer,
        distractors=_dedupe([
            pair(-r1, -r2),          # sign error: solved x + r = 0 as x = r
            f"{r1 + r2}, {r1 * r2}",  # reported the sum and product instead
            pair(r1 + 1, r2 + 1),    # off-by-one on both roots
            pair(r1, r1),            # treated a repeated root
            pair(r1 * r2, r1 + r2),  # sum/product reversed
        ], answer),
        explanation=(
            f"Split the middle term: {expr} = 0 factors as (x - {r1})(x - {r2}) = 0, "
            f"so x = {r1} or x = {r2}. Sum of roots = {-b}, product = {c}."
        ),
        slug=f"quad-roots-{r1}-{r2}", tags=["quadratic", "roots", "factorisation"],
        difficulty="medium", time_budget_ms=25000,
        stimulus={"kind": "quadratic", "a": 1, "b": b, "c": c},
    )]


def h_quadratic_sum_product(p: dict[str, Any]) -> list[MathsItem]:
    a, b, c = int(p["a"]), int(p["b"]), int(p["c"])
    s, prod = frac(-b, a), frac(c, a)
    out = [MathsItem(
        prompt=f"For {quad_expr(a, b, c)} = 0, what is the sum of the roots?",
        answer=s,
        distractors=_dedupe([frac(b, a), prod, frac(-c, a)], s),
        explanation=f"Sum of roots = -b/a = {-b}/{a} = {s}.",
        slug=f"quad-sum-{a}-{b}-{c}", tags=["quadratic", "sum-of-roots"], difficulty="medium",
    )]
    out.append(MathsItem(
        prompt=f"For {quad_expr(a, b, c)} = 0, what is the product of the roots?",
        answer=prod,
        distractors=_dedupe([frac(-c, a), s, frac(b, c) if c else "0"], prod),
        explanation=f"Product of roots = c/a = {c}/{a} = {prod}.",
        slug=f"quad-prod-{a}-{b}-{c}", tags=["quadratic", "product-of-roots"], difficulty="medium",
    ))
    return out


def h_discriminant(p: dict[str, Any]) -> list[MathsItem]:
    a, b, c = int(p["a"]), int(p["b"]), int(p["c"])
    disc = b * b - 4 * a * c
    nature = ("two distinct real roots" if disc > 0
              else "two equal real roots" if disc == 0
              else "no real roots")
    # Only three natures exist, so a 4-option nature MCQ would need a filler
    # option. Ask for the computed discriminant instead, and state the
    # consequence in the explanation.
    return [MathsItem(
        prompt=f"What is the discriminant of {quad_expr(a, b, c)} = 0?",
        answer=num(disc),
        distractors=_dedupe(
            [num(b * b + 4 * a * c), num(4 * a * c - b * b), num(b * b - 2 * a * c), num(disc + 1)],
            num(disc), numeric=True,
        ),
        explanation=(
            f"D = b\u00b2 - 4ac = {b * b} - {4 * a * c} = {disc}. "
            f"Since D {'>' if disc > 0 else ('=' if disc == 0 else '<')} 0, the equation has {nature}."
        ),
        slug=f"disc-{a}-{b}-{c}", tags=["quadratic", "discriminant"],
        difficulty="medium",
        stimulus={"kind": "discriminant", "a": a, "b": b, "c": c, "D": disc, "nature": nature},
    )]


def h_linear_consistency(p: dict[str, Any]) -> list[MathsItem]:
    a1, b1, c1 = int(p["a1"]), int(p["b1"]), int(p["c1"])
    a2, b2, c2 = int(p["a2"]), int(p["b2"]), int(p["c2"])
    # a1x + b1y + c1 = 0 ; a2x + b2y + c2 = 0
    if a1 * b2 - a2 * b1 != 0:
        verdict = "consistent, with a unique solution"
    elif a1 * c2 - a2 * c1 == 0 and b1 * c2 - b2 * c1 == 0:
        verdict = "consistent, with infinitely many solutions"
    else:
        verdict = "inconsistent, with no solution"
    others = [x for x in [
        "consistent, with a unique solution",
        "consistent, with infinitely many solutions",
        "inconsistent, with no solution",
    ] if x != verdict]
    return [MathsItem(
        prompt=(
            f"For the pair {lin_expr(a1, b1, c1)} = 0 and {lin_expr(a2, b2, c2)} = 0, "
            f"which statement is correct?"
        ),
        answer=verdict,
        distractors=others + [f"a1/a2 = b1/b2 = c1/c2"],
        explanation=(
            f"Compare a1/a2 = {frac(a1, a2)}, b1/b2 = {frac(b1, b2)}, c1/c2 = {frac(c1, c2)}. "
            f"The pair is {verdict}."
        ),
        slug=f"linear-{a1}-{b1}-{c1}-{a2}-{b2}-{c2}", tags=["linear-equations", "consistency"],
        difficulty="hard", time_budget_ms=TIME["hard"],
    )]


def h_distance(p: dict[str, Any]) -> list[MathsItem]:
    x1, y1, x2, y2 = int(p["x1"]), int(p["y1"]), int(p["x2"]), int(p["y2"])
    dx, dy = x2 - x1, y2 - y1
    sq = dx * dx + dy * dy
    root = math.isqrt(sq)
    if root * root != sq:
        return []  # keep answers exact
    return [MathsItem(
        prompt=f"Find the distance between the points ({x1}, {y1}) and ({x2}, {y2}).",
        answer=f"{root} units",
        distractors=_dedupe([
            f"{abs(dx) + abs(dy)} units",   # added the legs
            f"{sq} units",                  # forgot the square root
            f"{abs(dx * dy)} units",
            f"{root + 1} units",
        ], f"{root} units", numeric=True),
        explanation=f"d = {SQRT}[({x2} - ({x1}))\u00b2 + ({y2} - ({y1}))\u00b2] = {SQRT}[{dx * dx} + {dy * dy}] = {SQRT}{sq} = {root}.",
        slug=f"dist-{x1}-{y1}-{x2}-{y2}", tags=["coordinate-geometry", "distance-formula"],
        difficulty="easy", time_budget_ms=TIME["easy"],
    )]


def h_midpoint(p: dict[str, Any]) -> list[MathsItem]:
    x1, y1, x2, y2 = int(p["x1"]), int(p["y1"]), int(p["x2"]), int(p["y2"])
    mx, my = frac(x1 + x2, 2), frac(y1 + y2, 2)
    answer = f"({mx}, {my})"
    return [MathsItem(
        prompt=f"Find the midpoint of the segment joining ({x1}, {y1}) and ({x2}, {y2}).",
        answer=answer,
        distractors=_dedupe([
            f"({x1 + x2}, {y1 + y2})",            # forgot to divide by 2
            f"({x2 - x1}, {y2 - y1})",            # subtracted instead of adding
            f"({my}, {mx})",                      # swapped coordinates
            f"({frac(x1 - x2, 2)}, {frac(y1 - y2, 2)})",   # reversed subtraction
            f"({mx}, {-int(my) if my.lstrip('-').isdigit() else my})",  # sign slip on y
        ], answer, numeric=True),
        explanation=f"Midpoint = ((x1+x2)/2, (y1+y2)/2) = (({x1 + x2})/2, ({y1 + y2})/2) = {answer}.",
        slug=f"mid-{x1}-{y1}-{x2}-{y2}", tags=["coordinate-geometry", "section-formula"],
        difficulty="easy", time_budget_ms=TIME["easy"],
    )]


def h_section(p: dict[str, Any]) -> list[MathsItem]:
    x1, y1, x2, y2 = int(p["x1"]), int(p["y1"]), int(p["x2"]), int(p["y2"])
    m, n = int(p["m"]), int(p["n"])
    px, py = frac(m * x2 + n * x1, m + n), frac(m * y2 + n * y1, m + n)
    answer = f"({px}, {py})"
    return [MathsItem(
        prompt=f"Find the point that divides the segment joining ({x1}, {y1}) and ({x2}, {y2}) internally in the ratio {m}:{n}.",
        answer=answer,
        distractors=_dedupe([
            f"({frac(n * x2 + m * x1, m + n)}, {frac(n * y2 + m * y1, m + n)})",  # ratio reversed
            f"({m * x2 + n * x1}, {m * y2 + n * y1})",                            # forgot /(m+n)
            f"({py}, {px})",
        ], answer, numeric=True),
        explanation=f"Section formula: ((m x2 + n x1)/(m+n), (m y2 + n y1)/(m+n)) = {answer}.",
        slug=f"sec-{m}-{n}-{x1}-{y1}-{x2}-{y2}", tags=["coordinate-geometry", "section-formula"],
        difficulty="medium",
    )]


def h_trig_ratio(p: dict[str, Any]) -> list[MathsItem]:
    angle = int(p["angle"])
    if angle not in TRIG_TABLE["sin"]:
        return []
    out = []
    for ratio in ("sin", "cos", "tan"):
        answer = TRIG_TABLE[ratio][angle]
        row = [TRIG_TABLE[ratio][a] for a in TRIG_TABLE["sin"] if a != angle]
        other = "cos" if ratio == "sin" else ("sin" if ratio == "cos" else "cot")
        co_value = TRIG_TABLE.get(other, {}).get(angle)
        pool = ([co_value] if co_value else []) + row
        out.append(MathsItem(
            prompt=f"What is the value of {ratio} {angle}\u00b0?",
            answer=answer,
            distractors=_dedupe(pool, answer),
            explanation=f"From the standard trigonometric table, {ratio} {angle}\u00b0 = {answer}.",
            slug=f"trig-{ratio}-{angle}", tags=["trigonometry", "trig-table", "recall"],
            difficulty="easy", time_budget_ms=TIME["easy"],
        ))
    return out


def h_trig_identity(p: dict[str, Any]) -> list[MathsItem]:
    which = str(p.get("which", "pythagoras"))
    bank = {
        "pythagoras": (
            "sin\u00b2\u03b8 + cos\u00b2\u03b8 is equal to",
            "1",
            ["0", "2", "sin\u03b8 cos\u03b8"],
            "The fundamental identity sin\u00b2\u03b8 + cos\u00b2\u03b8 = 1 holds for every \u03b8.",
        ),
        "sec_tan": (
            "sec\u00b2\u03b8 - tan\u00b2\u03b8 is equal to",
            "1",
            ["0", "-1", "sec\u03b8 tan\u03b8"],
            "sec\u00b2\u03b8 - tan\u00b2\u03b8 = 1, so sec\u00b2\u03b8 = 1 + tan\u00b2\u03b8.",
        ),
        "cosec_cot": (
            "cosec\u00b2\u03b8 - cot\u00b2\u03b8 is equal to",
            "1",
            ["0", "-1", "cosec\u03b8 cot\u03b8"],
            "cosec\u00b2\u03b8 - cot\u00b2\u03b8 = 1, so cosec\u00b2\u03b8 = 1 + cot\u00b2\u03b8.",
        ),
        "tan_ratio": (
            "tan\u03b8 is equal to",
            "sin\u03b8 / cos\u03b8",
            ["cos\u03b8 / sin\u03b8", "sin\u03b8 cos\u03b8", "1 / sin\u03b8"],
            "tan\u03b8 = opposite/adjacent = (opposite/hypotenuse) / (adjacent/hypotenuse) = sin\u03b8 / cos\u03b8.",
        ),
        "reciprocal_sec": (
            "The reciprocal of cos\u03b8 is",
            "sec\u03b8",
            ["cosec\u03b8", "cot\u03b8", "tan\u03b8"],
            "sec\u03b8 = 1/cos\u03b8. The three reciprocal pairs are sin-cosec, cos-sec, tan-cot.",
        ),
    }
    if which not in bank:
        return []
    prompt, answer, wrongs, expl = bank[which]
    return [MathsItem(
        prompt=prompt, answer=answer, distractors=wrongs, explanation=expl,
        slug=f"trig-identity-{which}", tags=["trigonometry", "identity"], difficulty="easy",
        time_budget_ms=TIME["easy"],
    )]


def h_height_distance(p: dict[str, Any]) -> list[MathsItem]:
    angle = int(p["angle"])
    base = int(p["base"])
    # tan(angle) = height / base  -> height = base * tan(angle)
    if angle not in (30, 45, 60):
        return []
    if angle == 45:
        h_text = f"{base} m"
        wrong = [f"{base} {SQRT}3 m", f"{base}/{SQRT}3 m", f"{2 * base} m"]
    elif angle == 60:
        height = base * math.sqrt(3)
        h_text = f"{base}{SQRT}3 m"
        wrong = [f"{base}/{SQRT}3 m", f"{base} m", f"{2 * base}{SQRT}3 m"]
    else:  # 30
        h_text = f"{base}/{SQRT}3 m"
        wrong = [f"{base}{SQRT}3 m", f"{base} m", f"{base}/2 m"]
    return [MathsItem(
        prompt=(
            f"The angle of elevation of the top of a tower from a point {base} m away from its foot "
            f"is {angle}\u00b0. Find the height of the tower."
        ),
        answer=h_text,
        distractors=_dedupe(wrong, h_text),
        explanation=(
            f"tan {angle}\u00b0 = height/{base}, so height = {base} x tan {angle}\u00b0 = {h_text}."
        ),
        slug=f"height-{angle}-{base}", tags=["trigonometry", "heights-and-distances"],
        difficulty="medium", time_budget_ms=25000,
        stimulus={"kind": "elevation", "angle": angle, "base": base},
    )]


def h_tangent(p: dict[str, Any]) -> list[MathsItem]:
    kind = str(p.get("which", "perpendicular"))
    bank = {
        "perpendicular": (
            "A tangent to a circle is ________ to the radius at the point of contact.",
            "perpendicular", ["parallel", "equal", "bisecting"],
            "The tangent at any point of a circle is perpendicular to the radius through the point of contact.",
        ),
        "one_point": (
            "How many tangents can be drawn to a circle from a point ON the circle?",
            "Exactly one", ["Exactly two", "Infinitely many", "None"],
            "From a point on the circle there is exactly one tangent; from an external point there are exactly two.",
        ),
        "external_equal": (
            "Two tangents drawn to a circle from an external point are",
            "equal in length", ["perpendicular to each other", "unequal in length", "parallel to each other"],
            "The lengths of tangents drawn from an external point to a circle are equal.",
        ),
        "secant_points": (
            "A line that intersects a circle at exactly two points is called a",
            "secant", ["tangent", "chord", "diameter"],
            "A secant cuts the circle at two points. A chord is the segment joining those two points.",
        ),
        "tangent_length": (
            "From an external point 13 cm from the centre, a tangent of length 12 cm is drawn. What is the radius?",
            "5 cm", ["12 cm", "13 cm", "25 cm"],
            "Radius is perpendicular to the tangent, so r = sqrt(13\u00b2 - 12\u00b2) = sqrt(169 - 144) = sqrt25 = 5 cm.",
        ),
        "external_two": (
            "How many tangents can be drawn to a circle from a point OUTSIDE the circle?",
            "Exactly two", ["Exactly one", "Infinitely many", "None"],
            "From an external point exactly two tangents can be drawn, and they are equal in length.",
        ),
        "touches_at": (
            "A tangent to a circle touches it at how many points?",
            "Exactly one", ["Two", "Zero", "Infinitely many"],
            "By definition a tangent meets the circle at exactly one point, the point of contact.",
        ),
        "angle_semicircle": (
            "What is the angle subtended by a diameter (an angle in a semicircle)?",
            "90\u00b0", ["180\u00b0", "60\u00b0", "45\u00b0"],
            "The angle in a semicircle is always a right angle (90\u00b0).",
        ),
        "longest_chord": (
            "What is the longest chord of a circle?",
            "The diameter", ["Any chord through the centre", "The radius", "The tangent"],
            "The diameter passes through the centre and is the longest chord; the radius is not a chord.",
        ),
        "concentric": (
            "Circles that have the same centre but different radii are called",
            "concentric circles", ["congruent circles", "tangent circles", "coplanar circles"],
            "Concentric circles share a centre. Congruent circles have equal radii.",
        ),
        "cyclic_quadrilateral": (
            "In a cyclic quadrilateral, what is the sum of a pair of opposite angles?",
            "180\u00b0", ["90\u00b0", "360\u00b0", "270\u00b0"],
            "Opposite angles of a cyclic quadrilateral are supplementary: they sum to 180\u00b0.",
        ),
        "centre_angle": (
            "The angle subtended by an arc at the centre is how much the angle subtended by it at any point on the remaining part of the circle?",
            "Double", ["Half", "Equal to", "Triple"],
            "The angle at the centre is twice the angle at the circumference standing on the same arc.",
        ),
        "chord_definition": (
            "A line segment joining any two points on a circle is called a",
            "chord", ["secant", "tangent", "arc"],
            "A chord joins two points on the circle; a secant is the whole line, which extends beyond.",
        ),
    }
    if kind not in bank:
        return []
    prompt, answer, wrongs, expl = bank[kind]
    return [MathsItem(
        prompt=prompt, answer=answer, distractors=wrongs, explanation=expl,
        slug=f"circle-{kind}", tags=["circles", "tangent", "theorem"], difficulty="easy",
        time_budget_ms=TIME["easy"],
    )]


def h_sector(p: dict[str, Any]) -> list[MathsItem]:
    r, theta = int(p["r"]), int(p["theta"])
    arc = theta / 360 * 2 * (22 / 7) * r
    area = theta / 360 * (22 / 7) * r * r
    out = [MathsItem(
        prompt=f"Find the length of an arc of a sector with radius {r} cm and central angle {theta}\u00b0. (Use \u03c0 = {PI})",
        answer=f"{num(arc)} cm",
        distractors=_dedupe([
            f"{num(theta / 360 * (22 / 7) * r * r)} cm",   # used the area formula
            f"{num(2 * (22 / 7) * r)} cm",                 # full circumference
            f"{num(arc * 2)} cm",
        ], f"{num(arc)} cm", numeric=True),
        explanation=f"Arc length = (\u03b8/360) x 2\u03c0r = ({theta}/360) x 2 x {PI} x {r} = {num(arc)} cm.",
        slug=f"arc-{r}-{theta}", tags=["mensuration", "area-of-circle", "arc"], difficulty="medium",
    )]
    out.append(MathsItem(
        prompt=f"Find the area of a sector with radius {r} cm and central angle {theta}\u00b0. (Use \u03c0 = {PI})",
        answer=f"{num(area)} cm\u00b2",
        distractors=_dedupe([
            f"{num(theta / 360 * 2 * (22 / 7) * r)} cm\u00b2",  # used the arc formula
            f"{num((22 / 7) * r * r)} cm\u00b2",                 # full circle
            f"{num(area * 2)} cm\u00b2",
        ], f"{num(area)} cm\u00b2", numeric=True),
        explanation=f"Sector area = (\u03b8/360) x \u03c0r\u00b2 = ({theta}/360) x {PI} x {r}\u00b2 = {num(area)} cm\u00b2.",
        slug=f"sector-{r}-{theta}", tags=["mensuration", "area-of-circle", "sector"],
        difficulty="medium",
    ))
    return out


def h_mensuration(p: dict[str, Any]) -> list[MathsItem]:
    solid = str(p["solid"])
    out: list[MathsItem] = []
    pi = 22 / 7

    if solid == "cylinder":
        r, h = int(p["r"]), int(p["h"])
        v, cs, ts = pi * r * r * h, 2 * pi * r * h, 2 * pi * r * (r + h)
        out += [
            MathsItem(f"Find the volume of a cylinder with radius {r} cm and height {h} cm. (\u03c0 = {PI})",
                      f"{num(v)} cm\u00b3",
                      _dedupe([f"{num(cs)} cm\u00b3", f"{num(v / 3)} cm\u00b3", f"{num(pi * r * h)} cm\u00b3", f"{num(v * 2)} cm\u00b3"],
                      f"{num(v)} cm\u00b3", numeric=True),
                      f"V = \u03c0r\u00b2h = {PI} x {r}\u00b2 x {h} = {num(v)} cm\u00b3.",
                      f"cyl-vol-{r}-{h}", ["mensuration", "cylinder", "volume"]),
            MathsItem(f"Find the curved surface area of a cylinder with radius {r} cm and height {h} cm. (\u03c0 = {PI})",
                      f"{num(cs)} cm\u00b2",
                      _dedupe([f"{num(ts)} cm\u00b2", f"{num(2 * pi * r)} cm\u00b2", f"{num(pi * r * r)} cm\u00b2", f"{num(cs * 2)} cm\u00b2"],
                      f"{num(cs)} cm\u00b2", numeric=True),
                      f"CSA = 2\u03c0rh = 2 x {PI} x {r} x {h} = {num(cs)} cm\u00b2.",
                      f"cyl-csa-{r}-{h}", ["mensuration", "cylinder", "surface-area"]),
            MathsItem(f"Find the total surface area of a cylinder with radius {r} cm and height {h} cm. (\u03c0 = {PI})",
                      f"{num(ts)} cm\u00b2",
                      _dedupe([f"{num(cs)} cm\u00b2", f"{num(2 * pi * r * r)} cm\u00b2", f"{num(pi * r * (r + h))} cm\u00b2"],
                      f"{num(ts)} cm\u00b2", numeric=True),
                      f"TSA = 2\u03c0r(r + h) = 2 x {PI} x {r} x {r + h} = {num(ts)} cm\u00b2.",
                      f"cyl-tsa-{r}-{h}", ["mensuration", "cylinder", "surface-area"]),
        ]

    elif solid == "cone":
        r, h = int(p["r"]), int(p["h"])
        slant = math.sqrt(r * r + h * h)
        if abs(slant - round(slant)) > 1e-9:
            return []
        l = int(round(slant))
        v, cs, ts = pi * r * r * h / 3, pi * r * l, pi * r * (l + r)
        out += [
            MathsItem(f"Find the volume of a cone with radius {r} cm and height {h} cm. (\u03c0 = {PI})",
                      f"{num(v)} cm\u00b3",
                      _dedupe([f"{num(v * 3)} cm\u00b3", f"{num(r * r * h)} cm\u00b3", f"{num(v * 2)} cm\u00b3"],
                              f"{num(v)} cm\u00b3", numeric=True),
                      f"V = (1/3)\u03c0r\u00b2h. Forgetting the 1/3 gives {num(v * 3)}, the cylinder's volume.",
                      f"cone-vol-{r}-{h}", ["mensuration", "cone", "volume"]),
            MathsItem(f"A cone has radius {r} cm and height {h} cm. What is its slant height?",
                      f"{l} cm",
                      _dedupe([f"{r + h} cm", f"{h} cm", f"{l + 1} cm", f"{l - 1} cm"], f"{l} cm", numeric=True),
                      f"l = {SQRT}(r\u00b2 + h\u00b2) = {SQRT}({r * r} + {h * h}) = {SQRT}{r * r + h * h} = {l} cm.",
                      f"cone-slant-{r}-{h}", ["mensuration", "cone", "slant-height"], "easy"),
            MathsItem(f"Find the curved surface area of a cone with radius {r} cm and slant height {l} cm. (\u03c0 = {PI})",
                      f"{num(cs)} cm\u00b2",
                      _dedupe([f"{num(pi * r * r)} cm\u00b2", f"{num(ts)} cm\u00b2", f"{num(2 * pi * r * l)} cm\u00b2"],
                      f"{num(cs)} cm\u00b2", numeric=True),
                      f"CSA = \u03c0rl = {PI} x {r} x {l} = {num(cs)} cm\u00b2.",
                      f"cone-csa-{r}-{l}", ["mensuration", "cone", "surface-area"]),
        ]

    elif solid in ("sphere", "hemisphere"):
        r = int(p["r"])
        if solid == "sphere":
            v, sa = 4 / 3 * pi * r ** 3, 4 * pi * r * r
            out += [
                MathsItem(f"Find the volume of a sphere of radius {r} cm. (\u03c0 = {PI})",
                          f"{num(v)} cm\u00b3",
                          _dedupe([f"{num(sa)} cm\u00b3", f"{num(4 / 3 * pi * r ** 2)} cm\u00b3", f"{num(v / 2)} cm\u00b3"],
                          f"{num(v)} cm\u00b3", numeric=True),
                          f"V = (4/3)\u03c0r\u00b3 = (4/3) x {PI} x {r}\u00b3 = {num(v)} cm\u00b3.",
                          f"sphere-vol-{r}", ["mensuration", "sphere", "volume"]),
                MathsItem(f"Find the surface area of a sphere of radius {r} cm. (\u03c0 = {PI})",
                          f"{num(sa)} cm\u00b2",
                          _dedupe([f"{num(2 * pi * r * r)} cm\u00b2", f"{num(pi * r * r)} cm\u00b2", f"{num(v)} cm\u00b2"],
                          f"{num(sa)} cm\u00b2", numeric=True),
                          f"Surface area = 4\u03c0r\u00b2 = 4 x {PI} x {r}\u00b2 = {num(sa)} cm\u00b2.",
                          f"sphere-sa-{r}", ["mensuration", "sphere", "surface-area"]),
            ]
        else:
            v, cs, ts = 2 / 3 * pi * r ** 3, 2 * pi * r * r, 3 * pi * r * r
            out += [
                MathsItem(f"Find the volume of a hemisphere of radius {r} cm. (\u03c0 = {PI})",
                          f"{num(v)} cm\u00b3",
                          _dedupe([f"{num(4 / 3 * pi * r ** 3)} cm\u00b3", f"{num(cs)} cm\u00b3", f"{num(v / 2)} cm\u00b3"],
                          f"{num(v)} cm\u00b3", numeric=True),
                          f"V = (2/3)\u03c0r\u00b3, exactly half the sphere's (4/3)\u03c0r\u00b3.",
                          f"hemi-vol-{r}", ["mensuration", "hemisphere", "volume"]),
                MathsItem(f"Find the total surface area of a hemisphere of radius {r} cm. (\u03c0 = {PI})",
                          f"{num(ts)} cm\u00b2",
                          _dedupe([f"{num(cs)} cm\u00b2", f"{num(4 * pi * r * r)} cm\u00b2", f"{num(pi * r * r)} cm\u00b2"],
                          f"{num(ts)} cm\u00b2", numeric=True),
                          f"TSA = curved (2\u03c0r\u00b2) + base (\u03c0r\u00b2) = 3\u03c0r\u00b2 = {num(ts)} cm\u00b2. Using only 2\u03c0r\u00b2 forgets the flat base.",
                          f"hemi-tsa-{r}", ["mensuration", "hemisphere", "surface-area"]),
            ]
    return out


def h_statistics(p: dict[str, Any]) -> list[MathsItem]:
    data = sorted(int(x) for x in p["data"])
    n = len(data)
    if n < 3:
        return []
    # The slug has to identify the whole data set. Naming only the first value
    # and the count let "2, 3, 4, 4, 7, 9" and "2, 2, 4, 4, 6, 6" share the id
    # "mean-2-6", so the seeder kept one and silently dropped the other.
    data_tag = hashlib.sha1(",".join(map(str, data)).encode("utf-8")).hexdigest()[:8]
    mean = sum(data) / n
    median = data[n // 2] if n % 2 else (data[n // 2 - 1] + data[n // 2]) / 2
    counts: dict[int, int] = {}
    for v in data:
        counts[v] = counts.get(v, 0) + 1
    mode = max(counts, key=lambda k: (counts[k], -k))
    out = [
        MathsItem(f"Find the mean of the data: {', '.join(map(str, data))}.", num(mean),
                  _dedupe([num(median), num(mode), num(sum(data)), num(sum(data) / (n - 1))],
                          num(mean), numeric=True),
                  f"Mean = sum/n = {sum(data)}/{n} = {num(mean)}.", f"mean-{data_tag}",
                  ["statistics", "mean"], "easy"),
        MathsItem(f"Find the median of the data: {', '.join(map(str, data))}.", num(median),
                  _dedupe([num(mean), num(mode), num(data[0]), num(data[-1])], num(median), numeric=True),
                  f"With n = {n}, the median is the middle value after sorting = {num(median)}.",
                  f"median-{data_tag}", ["statistics", "median"], "easy"),
    ]
    if counts[mode] > 1:
        out.append(MathsItem(
            f"Find the mode of the data: {', '.join(map(str, data))}.", num(mode),
            _dedupe([num(mean), num(median), num(data[-1] if data[-1] != mode else data[0])],
                    num(mode), numeric=True),
            f"Mode = the most frequent value = {mode} (appears {counts[mode]} times).",
            f"mode-{data_tag}", ["statistics", "mode"], "easy"))
    return out


def h_probability(p: dict[str, Any]) -> list[MathsItem]:
    which = str(p["which"])
    bank = {
        "die_prime": ("A die is thrown once. What is the probability of getting a prime number?",
                      "1/2", ["1/3", "2/3", "1/6"],
                      "Primes on a die are 2, 3, 5 -> 3 favourable of 6 outcomes = 3/6 = 1/2. (1 is not prime.)"),
        "die_even": ("A die is thrown once. What is the probability of getting an even number?",
                     "1/2", ["1/3", "1/6", "2/3"], "Even outcomes are 2, 4, 6 -> 3/6 = 1/2."),
        "die_gt4": ("A die is thrown once. What is the probability of getting a number greater than 4?",
                    "1/3", ["1/2", "2/3", "1/6"], "Only 5 and 6 qualify -> 2/6 = 1/3."),
        "coin_two_heads": ("Two coins are tossed together. What is the probability of getting two heads?",
                           "1/4", ["1/2", "1/3", "3/4"],
                           "Outcomes are HH, HT, TH, TT -> 1 favourable of 4 = 1/4."),
        "coin_at_least_one": ("Two coins are tossed. What is the probability of getting at least one head?",
                              "3/4", ["1/2", "1/4", "1"], "HH, HT, TH qualify; only TT fails -> 3/4."),
        "card_red": ("One card is drawn from a well-shuffled deck of 52 cards. What is the probability that it is red?",
                     "1/2", ["1/4", "1/13", "1/26"], "26 red cards of 52 -> 26/52 = 1/2."),
        "card_face": ("One card is drawn from a deck of 52. What is the probability that it is a face card?",
                      "3/13", ["1/13", "1/4", "4/13"],
                      "Face cards are J, Q, K of each suit = 12 -> 12/52 = 3/13. Aces are not face cards."),
        "card_ace": ("One card is drawn from a deck of 52. What is the probability that it is an ace?",
                     "1/13", ["1/52", "1/4", "4/13"], "There are 4 aces -> 4/52 = 1/13."),
        "certain": ("What is the probability of an event that is certain to happen?",
                    "1", ["0", "0.5", "undefined"], "P(certain) = 1 and P(impossible) = 0; 0 <= P(E) <= 1."),
        "complement": ("If P(E) = 0.35, what is P(not E)?",
                       "0.65", ["0.35", "-0.35", "1.35"], "P(not E) = 1 - P(E) = 1 - 0.35 = 0.65."),
        "die_8": ("A die is thrown once. What is the probability of getting the number 8?",
                  "0", ["1/6", "1/8", "1"], "A die has no 8, so this is an impossible event and P = 0."),
        "die_odd": ("A die is thrown once. What is the probability of getting an odd number?",
                    "1/2", ["1/3", "2/3", "1/6"], "Odd outcomes are 1, 3, 5 -> 3/6 = 1/2."),
        "die_lt3": ("A die is thrown once. What is the probability of getting a number less than 3?",
                    "1/3", ["1/2", "1/6", "2/3"], "Only 1 and 2 qualify -> 2/6 = 1/3."),
        "die_multiple3": ("A die is thrown once. What is the probability of getting a multiple of 3?",
                          "1/3", ["1/2", "1/6", "2/3"], "Multiples of 3 are 3 and 6 -> 2/6 = 1/3."),
        "die_perfect_square": ("A die is thrown once. What is the probability of getting a perfect square?",
                               "1/3", ["1/2", "1/6", "2/3"],
                               "Perfect squares on a die are 1 and 4 -> 2/6 = 1/3. (9 is not on a die.)"),
        "die_le4": ("A die is thrown once. What is the probability of getting a number at most 4?",
                    "2/3", ["1/2", "1/3", "4/6"], "Outcomes 1, 2, 3, 4 qualify -> 4/6 = 2/3."),
        "die_ge5": ("A die is thrown once. What is the probability of getting a number at least 5?",
                    "1/3", ["1/2", "2/3", "1/6"], "Only 5 and 6 qualify -> 2/6 = 1/3."),
        "coin_one_each": ("Two coins are tossed together. What is the probability of getting one head and one tail?",
                          "1/2", ["1/4", "1/3", "3/4"],
                          "Outcomes HH, HT, TH, TT. HT and TH qualify -> 2/4 = 1/2."),
        "coin_no_head": ("Two coins are tossed together. What is the probability of getting no head?",
                         "1/4", ["1/2", "3/4", "0"], "Only TT qualifies -> 1/4."),
        "coin_three_heads": ("Three coins are tossed together. What is the probability of getting all heads?",
                             "1/8", ["1/4", "1/6", "3/8"],
                             "Three coins give 2^3 = 8 outcomes; only HHH qualifies -> 1/8."),
        "coin_at_least_two_heads": ("Three coins are tossed. What is the probability of getting at least two heads?",
                                    "1/2", ["3/8", "1/4", "5/8"],
                                    "HHH, HHT, HTH, THH qualify -> 4/8 = 1/2."),
        "card_king": ("One card is drawn from a deck of 52. What is the probability that it is a king?",
                      "1/13", ["1/4", "4/13", "1/52"], "There are 4 kings -> 4/52 = 1/13."),
        "card_black": ("One card is drawn from a deck of 52. What is the probability that it is black?",
                       "1/2", ["1/4", "1/13", "1/26"], "26 black cards of 52 -> 1/2."),
        "card_heart": ("One card is drawn from a deck of 52. What is the probability that it is a heart?",
                       "1/4", ["1/13", "1/2", "13/52"], "13 hearts of 52 -> 13/52 = 1/4."),
        "card_not_face": ("One card is drawn from a deck of 52. What is the probability that it is NOT a face card?",
                          "10/13", ["3/13", "1/13", "4/13"],
                          "12 face cards, so 40 are not -> 40/52 = 10/13."),
        "dice_sum7": ("Two dice are thrown together. What is the probability that the sum is 7?",
                      "1/6", ["1/12", "7/36", "1/36"],
                      "36 outcomes total; sums of 7 are (1,6),(2,5),(3,4),(4,3),(5,2),(6,1) -> 6/36 = 1/6."),
        "dice_doublet": ("Two dice are thrown together. What is the probability of getting a doublet (same number on both)?",
                         "1/6", ["1/12", "1/36", "6/11"],
                         "Doublets are (1,1)...(6,6) = 6 of 36 -> 1/6."),
        "dice_sum_gt9": ("Two dice are thrown together. What is the probability that the sum is greater than 9?",
                         "1/6", ["1/12", "1/4", "5/36"],
                         "Sums of 10, 11, 12: (4,6),(5,5),(6,4),(5,6),(6,5),(6,6) = 6 of 36 -> 1/6."),
        "impossible": ("What is the probability of an impossible event?",
                       "0", ["1", "0.5", "undefined"], "P(impossible) = 0 and P(certain) = 1."),
    }
    if which not in bank:
        return []
    prompt, answer, wrongs, expl = bank[which]
    return [MathsItem(prompt=prompt, answer=answer, distractors=wrongs, explanation=expl,
                      slug=f"prob-{which}", tags=["probability"], difficulty="easy",
                      time_budget_ms=TIME["easy"])]


def h_polynomial(p: dict[str, Any]) -> list[MathsItem]:
    which = str(p.get("which", "from_roots"))
    if which == "from_roots":
        alpha, beta = int(p["alpha"]), int(p["beta"])
        s, pr = alpha + beta, alpha * beta
        poly = quad_expr(1, -s, pr)
        return [MathsItem(
            prompt=f"If the sum of the zeroes of a quadratic polynomial is {s} and their product is {pr}, which polynomial is it?",
            answer=poly,
            distractors=_dedupe([
                quad_expr(1, s, pr),      # forgot to negate the sum
                quad_expr(1, -s, -pr),    # sign error on the product
                quad_expr(1, -pr, s),     # sum and product swapped
                quad_expr(1, s, -pr),     # both signs wrong
                quad_expr(1, -s - 1, pr), # off-by-one on the middle term
            ], poly),
            explanation=f"The polynomial is x\u00b2 - (sum)x + (product) = x\u00b2 - ({s})x + ({pr}) = {poly}.",
            slug=f"poly-roots-{alpha}-{beta}", tags=["polynomials", "zeroes"], difficulty="medium",
        )]
    if which == "count_zeroes":
        n = int(p["n"])
        if n != 2:
            return []
        return [MathsItem(
            prompt="How many zeroes does a quadratic polynomial have at most?",
            answer="2",
            distractors=["1", "3", "0"],
            explanation="A polynomial of degree n has at most n zeroes, so a quadratic (degree 2) has at most 2.",
            slug="poly-count",
            tags=["polynomials", "zeroes"],
            difficulty="easy",
            time_budget_ms=TIME["easy"],
        )]
    return []


def h_real_numbers(p: dict[str, Any]) -> list[MathsItem]:
    which = str(p["which"])
    bank = {
        "irrational": ("Which of the following is an irrational number?",
                       f"{SQRT}5", ["0.75", "7/2", f"{SQRT}4"],
                       f"{SQRT}5 cannot be written as p/q with q \u2260 0. Note {SQRT}4 = 2, which is rational."),
        "rational": ("Which of the following is a rational number?",
                     "0.333...", [f"{SQRT}7", f"{SQRT}2", "\u03c0"],
                     "0.333... = 1/3, a non-terminating repeating decimal, which is always rational."),
        "fta": ("The Fundamental Theorem of Arithmetic states that every composite number can be expressed as a product of primes, and this factorisation is",
                "unique, apart from the order of the primes",
                ["never unique", "unique only for even numbers", "always the same including order"],
                "The theorem guarantees a unique prime factorisation up to the order of the factors."),
        "sqrt2": ("Which statement about \u221a2 is correct?",
                  "It is irrational", ["It is rational", "It equals 1.4 exactly", "It is a whole number"],
                  "\u221a2 \u2248 1.41421... is non-terminating and non-repeating, so it is irrational."),
        "hcf_prime": ("What is the HCF of two distinct prime numbers p and q?",
                      "1", ["p", "q", "pq"],
                      "Distinct primes share no common factor other than 1, so HCF = 1 and LCM = pq."),
    }
    if which not in bank:
        return []
    prompt, answer, wrongs, expl = bank[which]
    return [MathsItem(prompt=prompt, answer=answer, distractors=wrongs, explanation=expl,
                      slug=f"real-{which}", tags=["real-numbers"], difficulty="easy",
                      time_budget_ms=TIME["easy"])]


def h_triangles(p: dict[str, Any]) -> list[MathsItem]:
    which = str(p["which"])
    if which == "bpt":
        return [MathsItem(
            prompt="The Basic Proportionality Theorem (Thales) states that if a line is drawn parallel to one side of a triangle, it divides the other two sides",
            answer="in the same ratio",
            distractors=["into equal halves", "in the ratio 2:1", "perpendicularly"],
            explanation="BPT: a line parallel to one side of a triangle divides the other two sides in the same ratio.",
            slug="tri-bpt",
            tags=["triangles", "bpt", "theorem"],
            difficulty="easy",
            time_budget_ms=TIME["easy"],
        )]
    if which == "similarity":
        return [MathsItem(
            prompt="Two triangles are similar if two angles of one are respectively equal to two angles of the other. This criterion is called",
            answer="AA (Angle-Angle)",
            distractors=["SSS", "SAS", "ASA"],
            explanation="AA similarity: equal angles force the third angles to be equal too, so the sides are proportional.",
            slug="tri-aa",
            tags=["triangles", "similarity", "criterion"],
            difficulty="easy",
            time_budget_ms=TIME["easy"],
        )]
    if which == "ratio_sides":
        k = int(p.get("k", 3))
        return [MathsItem(
            prompt=f"Two similar triangles have corresponding sides in the ratio 1:{k}. What is the ratio of their areas?",
            answer=f"1:{k * k}",
            distractors=_dedupe([f"1:{k}", f"1:{2 * k}", f"1:{k * k * k}", f"{k}:{k * k}", f"1:{k + k * k}"],
                                f"1:{k * k}"),
            explanation=f"The ratio of areas of similar triangles is the square of the ratio of corresponding sides: 1\u00b2:{k}\u00b2 = 1:{k * k}.",
            slug=f"tri-area-{k}",
            tags=["triangles", "similarity", "area-ratio"],
            difficulty="medium",
        )]
    if which == "pythagoras":
        return [MathsItem(
            prompt="In a right triangle with legs 6 cm and 8 cm, what is the hypotenuse?",
            answer="10 cm",
            distractors=["14 cm", "12 cm", "100 cm"],
            explanation=f"Hypotenuse = {SQRT}(6\u00b2 + 8\u00b2) = {SQRT}(36 + 64) = {SQRT}100 = 10 cm. Adding the legs gives 14, which is wrong.",
            slug="tri-pyth",
            tags=["triangles", "pythagoras"],
            difficulty="easy",
            time_budget_ms=TIME["easy"],
        )]
    extra = {
        "sss_criterion": ("Two triangles are similar if the three sides of one are proportional to the three sides of the other. This criterion is called",
                          "SSS (Side-Side-Side)", ["AA", "SAS", "ASA"],
                          "SSS similarity: all three pairs of corresponding sides in the same ratio forces equal angles."),
        "sas_criterion": ("Two triangles are similar if one angle is equal and the sides including that angle are proportional. This criterion is called",
                          "SAS (Side-Angle-Side)", ["SSS", "AA", "RHS"],
                          "SAS similarity needs the equal angle to be BETWEEN the proportional sides."),
        "midpoint_theorem": ("The Midpoint Theorem states that the segment joining the midpoints of two sides of a triangle is",
                             "parallel to the third side and half of it",
                             ["equal to the third side", "perpendicular to the third side", "twice the third side"],
                             "The midpoint segment is parallel to the third side and equals half its length."),
        "congruent_vs_similar": ("All congruent triangles are similar, but",
                                 "not all similar triangles are congruent",
                                 ["all similar triangles are congruent", "similar triangles must have equal areas", "congruent triangles need not be similar"],
                                 "Congruence means same shape AND size; similarity means same shape only."),
        "bpt_converse": ("The converse of the Basic Proportionality Theorem states that a line dividing two sides of a triangle in the same ratio is",
                         "parallel to the third side", ["perpendicular to the third side", "equal to the third side", "a median"],
                         "Converse of BPT: if a line divides two sides proportionally, it is parallel to the third side."),
        "area_ratio_proof": ("For two similar triangles, the ratio of their areas equals",
                             "the ratio of the squares of their corresponding sides",
                             ["the ratio of their corresponding sides", "the ratio of their perimeters squared divided by two", "the square of the ratio of their angles"],
                             "Area ratio = (side ratio)^2. Perimeter ratio equals the side ratio itself."),
        "equilateral_similar": ("Two equilateral triangles are always",
                                "similar", ["congruent", "neither similar nor congruent", "equal in area"],
                                "Every equilateral triangle has all angles 60\u00b0, so any two are similar by AA."),
        "pythagoras_5_12": ("In a right triangle with legs 5 cm and 12 cm, what is the hypotenuse?",
                            "13 cm", ["17 cm", "7 cm", "169 cm"],
                            "Hypotenuse = \u221a(5\u00b2 + 12\u00b2) = \u221a(25 + 144) = \u221a169 = 13 cm."),
        "pythagoras_9_12": ("In a right triangle with legs 9 cm and 12 cm, what is the hypotenuse?",
                            "15 cm", ["21 cm", "10.5 cm", "225 cm"],
                            "Hypotenuse = \u221a(81 + 144) = \u221a225 = 15 cm (a 3-4-5 triple scaled by 3)."),
        "similar_perimeter": ("Two similar triangles have sides in the ratio 2:5. What is the ratio of their perimeters?",
                              "2:5", ["4:25", "2:25", "5:2"],
                              "Perimeter is a length, so the perimeter ratio equals the side ratio 2:5."),
    }
    if which in extra:
        prompt, answer, wrongs, expl = extra[which]
        return [MathsItem(prompt=prompt, answer=answer, distractors=wrongs, explanation=expl,
                          slug=f"tri-{which}", tags=["triangles", "theorem"], difficulty="medium",
                          time_budget_ms=TIME["medium"])]
    if which == "ratio_sides_k":
        k = int(p.get("k", 2))
        return [MathsItem(
            prompt=f"The perimeters of two similar triangles are in the ratio 1:{k}. What is the ratio of their areas?",
            answer=f"1:{k * k}",
            distractors=_dedupe([f"1:{k}", f"1:{2 * k}", f"1:{k * k * k}", f"{k}:1"], f"1:{k * k}"),
            explanation=f"Perimeter ratio equals the side ratio, so the area ratio is its square: 1:{k * k}.",
            slug=f"tri-perim-area-{k}", tags=["triangles", "similarity", "area-ratio"], difficulty="medium")]
    return []


HANDLERS: dict[str, Callable[[dict[str, Any]], list[MathsItem]]] = {
    "hcf_lcm": h_hcf_lcm,
    "ap_term": h_ap_term,
    "ap_sum": h_ap_sum,
    "ap_find_d": h_ap_find_d,
    "quadratic_roots": h_quadratic_roots,
    "quadratic_sum_product": h_quadratic_sum_product,
    "discriminant": h_discriminant,
    "linear_consistency": h_linear_consistency,
    "distance": h_distance,
    "midpoint": h_midpoint,
    "section": h_section,
    "trig_ratio": h_trig_ratio,
    "trig_identity": h_trig_identity,
    "height_distance": h_height_distance,
    "tangent": h_tangent,
    "sector": h_sector,
    "mensuration": h_mensuration,
    "statistics": h_statistics,
    "probability": h_probability,
    "polynomial": h_polynomial,
    "real_numbers": h_real_numbers,
    "triangles": h_triangles,
}


def _split_number(text: str) -> tuple[str, str]:
    """Split '1232 cm\u00b3' into ('1232', ' cm\u00b3') so units survive padding."""
    for i, ch in enumerate(text):
        if not (ch.isdigit() or ch in ".-/"):
            return text[:i].strip(), text[i:]
    return text.strip(), ""


def _dedupe(candidates: Sequence[str], answer: str, numeric: bool = False) -> list[str]:
    """Keep three distractors distinct from each other and from the answer.

    `numeric=True` allows near-miss padding (+-1, x2, /2). For a *computed* value
    a near miss is exactly what a student who slips produces, so it is plausible
    rather than filler. Text answers never pad: they simply get skipped upstream.
    """
    seen = {answer.strip().lower()}
    out: list[str] = []
    for c in candidates:
        text = str(c).strip()
        key = text.lower()
        if not text or key in seen:
            continue
        seen.add(key)
        out.append(text)
        if len(out) == 3:
            return out

    if numeric and len(out) < 3:
        head, unit = _split_number(answer)
        try:
            value = float(eval(head)) if "/" in head else float(head)
        except (ValueError, SyntaxError, ZeroDivisionError):
            return out
        pool = [value + 1, value - 1, value * 2, value / 2 if value else value + 2, value * 10]
        for cand in pool:
            text = f"{num(cand)}{unit}"
            if text.lower() in seen:
                continue
            seen.add(text.lower())
            out.append(text)
            if len(out) == 3:
                break
    return out  # caller skips the item if this is still short


def generate(items: Sequence[dict[str, Any]], chapter: str, topic: str, source_ref: str) -> list[QuestionDef]:
    questions: list[QuestionDef] = []

    for item in items:
        problem = str(item.get("problem", ""))
        handler = HANDLERS.get(problem)
        if handler is None:
            continue
        item_chapter, item_topic = resolve_location(item, chapter, topic)
        try:
            produced = handler(item.get("params", {}))
        except (KeyError, ValueError, TypeError, ZeroDivisionError):
            continue  # a malformed param set never reaches a student

        for spec in produced:
            distractors = list(spec.distractors)[:3]
            if len(distractors) != 3:
                continue  # refuse to pad with filler options

            rng = stable_rng("maths", spec.slug, item_chapter)
            options, answer_key = build_options(spec.answer, distractors, rng)
            questions.append(make_question(
                qid=question_id(item_chapter, item_topic, "maths", slugify(spec.slug, 60)),
                chapter=item_chapter,
                topic=item_topic,
                question_type="mcq_single",
                prompt=spec.prompt,
                stimulus={"kind": "maths", "problem": problem, **spec.stimulus},
                options=options,
                answer_key=answer_key,
                explanation=spec.explanation,
                difficulty=spec.difficulty,
                time_budget_ms=spec.time_budget_ms,
                source_ref=source_ref,
                tags=["maths", *spec.tags],
            ))

    return _dedupe_questions(questions)


def _dedupe_questions(questions: list[QuestionDef]) -> list[QuestionDef]:
    seen: set[str] = set()
    out: list[QuestionDef] = []
    for q in questions:
        digest = content_hash(q)
        if digest in seen:
            continue
        seen.add(digest)
        out.append(q)
    return out

# Second-wave handlers live in maths_extra so this file stays readable. Imported
# at the bottom, after every name maths_extra needs is defined, because that
# module borrows the helpers above; the two share one `problem` namespace, so
# problems.json does not have to know which file implements a given problem.
from app.content.generators.maths_extra import EXTRA_HANDLERS  # noqa: E402

HANDLERS.update(EXTRA_HANDLERS)
