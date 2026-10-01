"""Emit parameter sets for the computational maths handlers.

The seven thinnest chapters were thin because their handlers read from fixed
banks, so more params produced the same questions again. Those handlers are now
computational (see maths_extra.py), which makes question count a function of how
many valid parameter sets exist - and there are thousands.

This script enumerates the parameter space deterministically and keeps only the
sets a handler actually accepts, because a handler returns [] when a param set
would not produce three distinct plausible distractors. Writing only the
accepted sets means the seed produces exactly the number of questions this
script reports, with no silent gaps.

Nothing here is randomness in the sense of chance: a seeded shuffle over a
sorted candidate list gives the same file every run, so question ids stay stable
and a student's history keeps pointing at the same items.

Usage:  python3 scripts/expand_maths_params.py
Writes: content/maths/problems_extra.json
"""

from __future__ import annotations

import itertools
import json
import random
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))

from app.content.generators.maths import HANDLERS  # noqa: E402
from app.content.generators.maths_extra import TRIPLES, _TRIG_EXPRESSIONS  # noqa: E402

OUT = BACKEND / "content" / "maths" / "problems_extra.json"
SOURCE_REF = (
    "Class 10 Mathematics (CBSE 2025-26) - original computed problems. "
    "Every answer is derived in Python from the stated parameters and every "
    "distractor is a named misconception, never a random perturbation."
)

# Target accepted items per (problem, chapter, topic). Chosen so each of the seven
# thin chapters clears 200 questions, with the harder analytical forms weighted
# more heavily than pure recall.
PLAN: list[dict] = [
    # ── Chapter 2: Polynomials ──────────────────────────────────────────
    {"problem": "poly_zeroes", "chapter": "m-poly", "topic": "m-poly.zeroes", "target": 70},
    {"problem": "poly_sum_product", "chapter": "m-poly", "topic": "m-poly.coefficients", "target": 60},
    {"problem": "poly_find_k", "chapter": "m-poly", "topic": "m-poly.coefficients", "target": 45},
    # ── Chapter 6: Triangles ───────────────────────────────────────────
    {"problem": "bpt_solve", "chapter": "m-tri", "topic": "m-tri.bpt", "target": 55},
    {"problem": "bpt_converse", "chapter": "m-tri", "topic": "m-tri.bpt", "target": 40},
    {"problem": "similar_sides", "chapter": "m-tri", "topic": "m-tri.similarity", "target": 50},
    {"problem": "pythagoras_side", "chapter": "m-tri", "topic": "m-tri.similarity", "target": 45},
    {"problem": "similarity_criterion", "chapter": "m-tri", "topic": "m-tri.similarity", "target": 12},
    # ── Chapter 8: Introduction to Trigonometry ────────────────────────
    {"problem": "trig_from_sides", "chapter": "m-trig", "topic": "m-trig.ratios", "target": 70},
    {"problem": "trig_from_value", "chapter": "m-trig", "topic": "m-trig.ratios", "target": 45},
    {"problem": "trig_expression", "chapter": "m-trig", "topic": "m-trig.table", "target": 22},
    # ── Chapter 9: Applications of Trigonometry ────────────────────────
    {"problem": "height_distance", "chapter": "m-heights", "topic": "m-heights.elevation", "target": 60},
    {"problem": "hd_distance", "chapter": "m-heights", "topic": "m-heights.elevation", "target": 55},
    {"problem": "hd_depression", "chapter": "m-heights", "topic": "m-heights.depression", "target": 55},
    {"problem": "hd_ladder", "chapter": "m-heights", "topic": "m-heights.elevation", "target": 45},
    {"problem": "hd_string", "chapter": "m-heights", "topic": "m-heights.elevation", "target": 40},
    {"problem": "hd_two_points", "chapter": "m-heights", "topic": "m-heights.elevation", "target": 35},
    # ── Chapter 10: Circles ────────────────────────────────────────────
    {"problem": "circle_tangent_length", "chapter": "m-circles", "topic": "m-circles.tangent", "target": 75},
    {"problem": "circle_tangent_angle", "chapter": "m-circles", "topic": "m-circles.tangent", "target": 60},
    {"problem": "circle_quadrilateral", "chapter": "m-circles", "topic": "m-circles.tangent", "target": 50},
    {"problem": "circle_concepts", "chapter": "m-circles", "topic": "m-circles.tangent-count", "target": 10},
    # ── Chapter 11/12: Areas Related to Circles ────────────────────────
    {"problem": "sector", "chapter": "m-areas-circle", "topic": "m-areas-circle.sector", "target": 60},
    {"problem": "circle_measure", "chapter": "m-areas-circle", "topic": "m-areas-circle.sector", "target": 45},
    {"problem": "annulus", "chapter": "m-areas-circle", "topic": "m-areas-circle.sector", "target": 40},
    {"problem": "segment_area", "chapter": "m-areas-circle", "topic": "m-areas-circle.segment", "target": 45},
    {"problem": "square_quadrant", "chapter": "m-areas-circle", "topic": "m-areas-circle.sector", "target": 35},
    {"problem": "wheel_revolutions", "chapter": "m-areas-circle", "topic": "m-areas-circle.arc", "target": 35},
    # ── Chapter 14: Probability ────────────────────────────────────────
    {"problem": "prob_two_dice", "chapter": "m-prob", "topic": "m-prob.dice-coins", "target": 60},
    {"problem": "prob_coin", "chapter": "m-prob", "topic": "m-prob.dice-coins", "target": 30},
    {"problem": "prob_balls", "chapter": "m-prob", "topic": "m-prob.basic", "target": 55},
    {"problem": "prob_defective", "chapter": "m-prob", "topic": "m-prob.basic", "target": 45},
    {"problem": "prob_cards", "chapter": "m-prob", "topic": "m-prob.cards", "target": 24},
    {"problem": "prob_complement", "chapter": "m-prob", "topic": "m-prob.basic", "target": 40},
    {"problem": "prob_year", "chapter": "m-prob", "topic": "m-prob.basic", "target": 4},
]


# ─────────────────────────── candidate param sets ───────────────────────────
# Each function yields candidates in a deterministic order. The caller keeps the
# first `target` that the handler accepts, so variety comes from breadth of the
# space rather than from chance.


def _triples(limit: int = 60):
    """Pythagorean triples, smallest first, including scaled ones."""
    seen = set()
    for a, b, c in sorted(TRIPLES, key=lambda t: t[2]):
        for pair in ((a, b, c), (b, a, c)):
            if pair not in seen and pair[2] <= limit * 2:
                seen.add(pair)
                yield pair


def candidates(problem: str):
    rng = random.Random(20260930)  # fixed seed: the same file every run

    if problem == "poly_zeroes":
        pairs = [(r1, r2) for r1 in range(-9, 10) for r2 in range(-9, 10) if r1 != 0 or r2 != 0]
        rng.shuffle(pairs)
        for r1, r2 in pairs:
            yield {"r1": r1, "r2": r2}

    elif problem == "poly_sum_product":
        combos = [(a, b, c) for a in (1, 2, 3, 4, 5) for b in range(-9, 10) for c in range(-9, 10) if b and c]
        rng.shuffle(combos)
        for a, b, c in combos:
            yield {"a": a, "b": b, "c": c}

    elif problem == "poly_find_k":
        combos = [(root, b) for root in range(-8, 9) if root for b in range(-9, 10)]
        rng.shuffle(combos)
        for root, b in combos:
            yield {"root": root, "b": b}

    elif problem == "bpt_solve":
        combos = [
            (ad, db, ae)
            for ad in range(1, 13)
            for db in range(1, 13)
            for ae in range(1, 16)
            if (ae * db) % ad == 0
        ]
        rng.shuffle(combos)
        for ad, db, ae in combos:
            yield {"ad": ad, "db": db, "ae": ae}

    elif problem == "bpt_converse":
        combos = []
        # Half parallel, half not: an item set where every answer is "Yes" teaches
        # a student to guess.
        for ad in range(2, 10):
            for db in range(2, 10):
                for ae in range(2, 12):
                    ec_parallel = ae * db // ad if (ae * db) % ad == 0 else None
                    if ec_parallel:
                        combos.append((ad, db, ae, ec_parallel))
                        combos.append((ad, db, ae, ec_parallel + 1))
        rng.shuffle(combos)
        for ad, db, ae, ec in combos:
            yield {"ad": ad, "db": db, "ae": ae, "ec": ec}

    elif problem == "similar_sides":
        combos = [
            (a1, b1, k)
            for a1 in range(2, 11)
            for b1 in range(2, 13)
            for k in range(2, 6)
        ]
        rng.shuffle(combos)
        for a1, b1, k in combos:
            yield {"a1": a1, "b1": b1, "a2": a1 * k}

    elif problem == "pythagoras_side":
        for a, b, c in _triples(30):
            yield {"which": "hypotenuse", "a": a, "b": b, "c": c}
        for a, b, c in _triples(30):
            yield {"which": "leg", "a": a, "b": b, "c": c}

    elif problem == "similarity_criterion":
        for which in ("aa", "sss", "sas", "not_sufficient", "bpt_statement", "parallel_line_ratio",
                      "equilateral_similar", "congruent_similar", "similar_not_congruent"):
            yield {"which": which}

    elif problem == "trig_from_sides":
        for a, b, c in _triples(40):
            yield {"a": a, "b": b, "c": c}

    elif problem == "trig_from_value":
        for a, b, c in _triples(40):
            yield {"a": a, "b": b, "c": c}

    elif problem == "trig_expression":
        for which in range(len(_TRIG_EXPRESSIONS)):
            yield {"which": which}

    elif problem == "height_distance":
        for angle in (30, 45, 60):
            for base in range(1, 61):
                yield {"angle": angle, "base": base}

    elif problem == "hd_distance":
        for angle in (30, 45, 60):
            for height in list(range(2, 41)) + [45, 50, 60, 75, 80, 90, 100, 120]:
                yield {"angle": angle, "height": height}

    elif problem == "hd_depression":
        for angle in (30, 45, 60):
            for height in list(range(5, 105, 5)) + [12, 18, 24, 36, 48, 72, 96]:
                yield {"angle": angle, "height": height}

    elif problem == "hd_ladder":
        for angle in (30, 45, 60):
            for length in list(range(4, 65, 2)) + [70, 80, 100]:
                yield {"angle": angle, "length": length}

    elif problem == "hd_string":
        for angle in (30, 45, 60):
            for height in list(range(4, 61, 2)) + [75, 90, 100, 150]:
                yield {"angle": angle, "height": height}

    elif problem == "hd_two_points":
        for gap in list(range(2, 101, 2)):
            yield {"gap": gap}

    elif problem == "circle_tangent_length":
        for which in ("tangent", "radius", "op"):
            for a, b, c in _triples(40):
                yield {"which": which, "a": a, "b": b, "c": c}

    elif problem == "circle_tangent_angle":
        for theta in range(10, 171, 5):
            yield {"theta": theta}
        for theta in range(12, 170, 7):
            yield {"theta": theta}

    elif problem == "circle_quadrilateral":
        combos = [
            (ab, bc, cd)
            for ab in range(3, 16)
            for bc in range(4, 18)
            for cd in range(3, 16)
            if bc + cd - ab > 0
        ]
        rng.shuffle(combos)
        for ab, bc, cd in combos:
            yield {"ab": ab, "bc": bc, "cd": cd}

    elif problem == "circle_concepts":
        for which in ("common_tangent_count", "tangent_parallel", "point_of_contact",
                      "radius_perpendicular_proof", "chord_vs_tangent", "equal_tangents_angle",
                      "tangent_length_zero", "concentric_tangent"):
            yield {"which": which}

    elif problem == "sector":
        for r in list(range(3, 30)) + [35, 40, 42, 49, 56]:
            for theta in (30, 45, 60, 90, 120, 150, 180, 210, 240, 270, 300, 315):
                yield {"r": r, "theta": theta}

    elif problem == "circle_measure":
        for r in list(range(1, 41)) + [42, 49, 56, 63, 70, 77, 84, 91, 98, 105]:
            yield {"r": r}

    elif problem == "annulus":
        combos = [(R, r) for R in range(4, 31) for r in range(1, R) if R - r >= 2]
        rng.shuffle(combos)
        for R, r in combos:
            yield {"R": R, "r": r}

    elif problem == "segment_area":
        for r in (6, 7, 8, 10, 12, 14, 15, 16, 20, 21, 24, 28, 30, 35, 42, 49, 56):
            for theta in (60, 90, 120):
                yield {"r": r, "theta": theta}

    elif problem == "square_quadrant":
        for side in (7, 14, 21, 28, 35, 42, 49, 56, 63, 70, 2, 4, 6, 8, 10, 12, 16, 20, 24):
            yield {"side": side}

    elif problem == "wheel_revolutions":
        # Only distances that are an exact multiple of the circumference, so the
        # answer is a whole number of revolutions and nobody has to guess a
        # rounding rule.
        for d in (7, 14, 21, 28, 35, 42, 49, 56, 70, 84, 98, 105, 140):
            circumference = 22 / 7 * d
            for rev in range(2, 26):
                yield {"d": d, "distance": int(round(circumference * rev))}

    elif problem == "prob_two_dice":
        for relation in ("equals", "more_than", "at_least", "less_than", "at_most"):
            for target in range(2, 13):
                yield {"sum": target, "relation": relation}

    elif problem == "prob_coin":
        for coins in (2, 3):
            for heads in range(0, coins + 1):
                for relation in ("exactly", "at_least", "at_most"):
                    yield {"coins": coins, "heads": heads, "relation": relation}

    elif problem == "prob_balls":
        combos = [
            (r, b, g)
            for r in range(1, 11)
            for b in range(1, 11)
            for g in range(0, 9)
            if r + b + g >= 5
        ]
        rng.shuffle(combos)
        for r, b, g in combos:
            for colour in ("red", "blue", "green"):
                if colour == "green" and g == 0:
                    continue
                yield {"red": r, "blue": b, "green": g, "colour": colour}

    elif problem == "prob_defective":
        combos = [(total, defective) for total in range(5, 61) for defective in range(1, total)]
        rng.shuffle(combos)
        for total, defective in combos:
            yield {"total": total, "defective": defective}

    elif problem == "prob_cards":
        for which in ("king", "queen", "jack", "ace", "spade", "heart", "diamond", "club",
                      "red", "black", "face", "honour", "red_king", "king_hearts", "not_ace",
                      "ten", "even_red", "spade_or_ace"):
            yield {"which": which}

    elif problem == "prob_complement":
        for hundredths in range(1, 100):
            yield {"hundredths": hundredths}
        for n, d in ((1, 2), (1, 3), (2, 3), (1, 4), (3, 4), (1, 5), (2, 5), (3, 5), (4, 5),
                     (1, 6), (5, 6), (1, 7), (2, 7), (3, 7), (1, 8), (3, 8), (5, 8), (7, 8),
                     (1, 9), (2, 9), (4, 9), (5, 9), (1, 10), (3, 10), (7, 10), (9, 10)):
            yield {"num": n, "den": d}

    elif problem == "prob_year":
        yield {"leap": False}
        yield {"leap": True}

    else:
        raise SystemExit(f"no candidate generator for problem {problem!r}")


def main() -> int:
    handler_missing = [p["problem"] for p in PLAN if p["problem"] not in HANDLERS]
    if handler_missing:
        print(f"ERROR: no handler for {handler_missing}", file=sys.stderr)
        return 1

    items: list[dict] = []
    seen_keys: set[str] = set()
    report: list[tuple[str, str, int, int]] = []

    for spec in PLAN:
        problem = spec["problem"]
        handler = HANDLERS[problem]
        accepted = 0
        tried = 0
        for params in candidates(problem):
            tried += 1
            key = json.dumps(params, sort_keys=True)
            if key in seen_keys:
                continue
            try:
                produced = handler(params)
            except Exception:  # noqa: BLE001 - a bad param set must not abort the run
                continue
            if not produced:
                continue
            # A handler that cannot build three distinct distractors returns fewer
            # than four options upstream; those items would be dropped at seed time
            # anyway, so they are dropped here and reported.
            if any(len(spec_item.distractors) != 3 for spec_item in produced):
                continue
            seen_keys.add(key)
            accepted += len(produced)
            items.append({
                "kind": "maths",
                "problem": problem,
                "params": params,
                "chapter": spec["chapter"],
                "topic": spec["topic"],
            })
            if accepted >= spec["target"]:
                break
        report.append((problem, spec["chapter"], accepted, tried))

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(
        json.dumps(
            {
                "chapter": "m-real",
                "kind": "maths",
                "generator": "maths",
                "source_ref": SOURCE_REF,
                "generator_note": (
                    "Parameter sets for the computational handlers in maths_extra.py. "
                    "Each set is enumerated deterministically and kept only if the handler "
                    "accepts it, so the seeded question count matches the script's report."
                ),
                "items": items,
            },
            indent=1,
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )

    print(f"{'problem':26} {'chapter':18} {'questions':>10} {'params tried':>13}")
    total = 0
    for problem, chapter, accepted, tried in report:
        total += accepted
        print(f"{problem:26} {chapter:18} {accepted:>10} {tried:>13}")
    print(f"\n{len(items)} param sets -> {total} questions written to {OUT.relative_to(BACKEND)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
