#!/usr/bin/env python3
"""Expand content/maths/problems.json with many more computed param sets.

Every question the Maths generator produces is *computed* from its params, so
adding param sets adds genuinely new practice without writing prose by hand and
without any risk of a wrong answer key. Params stay inside the ranges each
handler already accepts, and enum fields reuse only values that already exist.

Run:  python scripts/expand_maths.py
"""
from __future__ import annotations

import json
import random
from pathlib import Path

PATH = Path(__file__).resolve().parent.parent / "backend" / "content" / "maths" / "problems.json"
rng = random.Random(20260912)

# Pythagorean triples keep "distance between two points" answers integral.
TRIPLES = [(3, 4, 5), (6, 8, 10), (5, 12, 13), (8, 15, 17), (7, 24, 25),
           (9, 12, 15), (12, 16, 20), (20, 21, 29), (9, 40, 41), (15, 20, 25),
           (10, 24, 26), (18, 24, 30), (16, 30, 34), (21, 28, 35), (11, 60, 61)]


def item(problem: str, params: dict, chapter: str, topic: str) -> dict:
    return {"kind": "maths", "problem": problem, "params": params,
            "chapter": chapter, "topic": topic}


def build() -> list[dict]:
    out: list[dict] = []

    # ---- Real Numbers: HCF / LCM ----
    seen = set()
    tries = 0
    while len(seen) < 120 and tries < 6000:
        tries += 1
        a, b = rng.randint(12, 480), rng.randint(12, 480)
        if a == b:
            continue
        key = (min(a, b), max(a, b))
        if key in seen:
            continue
        seen.add(key)
        out.append(item("hcf_lcm", {"a": a, "b": b}, "m-real", "m-real.hcf-lcm"))

    # ---- Polynomials: zeroes and coefficients from given roots ----
    seen = set()
    tries = 0
    while len(seen) < 95 and tries < 6000:
        tries += 1
        alpha, beta = rng.randint(-9, 9), rng.randint(-9, 9)
        if alpha == 0 and beta == 0 or (alpha, beta) in seen:
            continue
        seen.add((alpha, beta))
        which = "from_roots" if len(seen) % 2 else "count_zeroes"
        p = {"which": which, "alpha": alpha, "beta": beta}
        if which == "count_zeroes":
            p["n"] = rng.randint(1, 3)
        out.append(item("polynomial", p, "m-poly",
                        "m-poly.zeroes" if which == "count_zeroes" else "m-poly.coefficients"))

    # ---- Linear equations: consistency of a pair ----
    seen = set()
    tries = 0
    while len(seen) < 95 and tries < 6000:
        tries += 1
        a1, b1 = rng.randint(1, 9), rng.randint(1, 9)
        c1 = rng.randint(-20, 20) or 5
        kind = rng.choice(["unique", "infinite", "none"])
        if kind == "unique":
            a2, b2 = rng.randint(1, 9), rng.randint(1, 9)
            if a1 * b2 == a2 * b1:
                continue
            c2 = rng.randint(-20, 20) or -7
        elif kind == "infinite":
            k = rng.randint(2, 5)
            a2, b2, c2 = a1 * k, b1 * k, c1 * k
        else:
            k = rng.randint(2, 5)
            a2, b2, c2 = a1 * k, b1 * k, c1 * k + rng.choice([1, -1, 3, -3])
        key = (a1, b1, c1, a2, b2, c2)
        if key in seen:
            continue
        seen.add(key)
        out.append(item("linear_consistency",
                        {"a1": a1, "b1": b1, "c1": c1, "a2": a2, "b2": b2, "c2": c2},
                        "m-linear", "m-linear.consistency"))

    # ---- Quadratic equations ----
    seen = set()
    tries = 0
    while len(seen) < 115 and tries < 6000:
        tries += 1
        r1, r2 = rng.randint(-9, 9), rng.randint(-9, 9)
        if (r1, r2) in seen or (r1 == 0 and r2 == 0):
            continue
        seen.add((r1, r2))
        out.append(item("quadratic_roots", {"root1": r1, "root2": r2},
                        "m-quad", "m-quad.factorisation"))

    seen = set()
    tries = 0
    while len(seen) < 85 and tries < 6000:
        tries += 1
        a = rng.choice([1, 1, 1, 2, 3, 4, 5])
        b = rng.randint(-12, 12) or 5
        c = rng.randint(-15, 15) or 3
        if (a, b, c) in seen:
            continue
        seen.add((a, b, c))
        out.append(item("quadratic_sum_product", {"a": a, "b": b, "c": c},
                        "m-quad", "m-quad.formula"))
        out.append(item("discriminant", {"a": a, "b": b, "c": c},
                        "m-quad", "m-quad.discriminant"))

    # ---- Arithmetic progressions ----
    seen = set()
    tries = 0
    while len(seen) < 95 and tries < 6000:
        tries += 1
        a, d, n = rng.randint(-15, 40), rng.choice([-7, -5, -3, 2, 3, 4, 5, 6, 7, 8, 11]), rng.randint(6, 30)
        if d == 0 or (a, d, n) in seen:
            continue
        seen.add((a, d, n))
        out.append(item("ap_term", {"a": a, "d": d, "n": n}, "m-ap", "m-ap.nth-term"))
        out.append(item("ap_sum", {"a": a, "d": d, "n": n}, "m-ap", "m-ap.sum"))

    seen = set()
    tries = 0
    while len(seen) < 75 and tries < 6000:
        tries += 1
        start, d = rng.randint(-20, 60), rng.choice([-6, -4, -3, 3, 4, 5, 6, 7, 9, 12])
        if d == 0:
            continue
        terms = [start + d * i for i in range(4)]
        key = tuple(terms)
        if key in seen:
            continue
        seen.add(key)
        out.append(item("ap_find_d", {"terms": terms}, "m-ap", "m-ap.nth-term"))

    # ---- Coordinate geometry ----
    used = set()
    scaled = []
    for p, q, h in TRIPLES:
        for k in (1, 2, 3):
            scaled.append((p * k, q * k))
    for dx0, dy0 in scaled:
        for dx, dy in ((dx0, dy0), (dy0, dx0), (-dx0, dy0), (dx0, -dy0), (-dx0, -dy0)):
            x1, y1 = rng.randint(-12, 12), rng.randint(-12, 12)
            x2, y2 = x1 + dx, y1 + dy
            key = (x1, y1, x2, y2)
            if key in used:
                continue
            used.add(key)
            out.append(item("distance", {"x1": x1, "y1": y1, "x2": x2, "y2": y2},
                            "m-coord", "m-coord.distance"))
            out.append(item("midpoint", {"x1": x1, "y1": y1, "x2": x2, "y2": y2},
                            "m-coord", "m-coord.section"))

    seen = set()
    tries = 0
    while len(seen) < 65 and tries < 6000:
        tries += 1
        m, n = rng.choice([(1, 1), (1, 2), (2, 1), (1, 3), (3, 1), (2, 3), (3, 2), (1, 4), (4, 1)])
        x1, y1 = rng.randint(-8, 8), rng.randint(-8, 8)
        # Choose x2,y2 so the internal division lands on integers.
        x2 = x1 + (m + n) * rng.randint(1, 4)
        y2 = y1 + (m + n) * rng.randint(1, 4)
        key = (x1, y1, x2, y2, m, n)
        if key in seen:
            continue
        seen.add(key)
        out.append(item("section", {"x1": x1, "y1": y1, "x2": x2, "y2": y2, "m": m, "n": n},
                        "m-coord", "m-coord.section"))

    # ---- Trigonometry: heights and distances ----
    seen = set()
    tries = 0
    while len(seen) < 33 and tries < 6000:
        tries += 1
        angle = rng.choice([30, 45, 60])
        base = rng.choice([10, 15, 20, 25, 30, 40, 50, 60, 75, 100, 120])
        if (angle, base) in seen:
            continue
        seen.add((angle, base))
        out.append(item("height_distance", {"angle": angle, "base": base},
                        "m-heights", "m-heights.elevation"))

    # ---- Mensuration (pi = 22/7, so keep r a multiple of 7) ----
    seen = set()
    tries = 0
    while len(seen) < 150 and tries < 6000:
        tries += 1
        solid = rng.choice(["cone", "cylinder", "hemisphere", "sphere"])
        r = rng.choice([7, 14, 21, 28, 35, 3.5, 10.5])
        h = rng.choice([3, 5, 6, 8, 10, 12, 14, 16, 20, 24, 28])
        key = (solid, r, h)
        if key in seen:
            continue
        seen.add(key)
        params = {"solid": solid, "r": r}
        if solid in ("cone", "cylinder"):
            params["h"] = h
        topic = f"m-sav.{solid}"
        out.append(item("mensuration", params, "m-sav", topic))

    # ---- Areas related to circles: sectors ----
    seen = set()
    tries = 0
    while len(seen) < 30 and tries < 6000:
        tries += 1
        r = rng.choice([7, 14, 21, 28])
        theta = rng.choice([30, 45, 60, 72, 90, 120, 144, 180])
        if (r, theta) in seen:
            continue
        seen.add((r, theta))
        out.append(item("sector", {"r": r, "theta": theta},
                        "m-areas-circle", "m-areas-circle.sector"))

    # ---- Statistics: mean of a data set ----
    seen = set()
    tries = 0
    while len(seen) < 95 and tries < 6000:
        tries += 1
        n = rng.randint(5, 9)
        data = sorted(rng.randint(1, 40) for _ in range(n))
        key = tuple(data)
        if key in seen:
            continue
        seen.add(key)
        out.append(item("statistics", {"data": data}, "m-stats", "m-stats.mean"))

    return out


def main() -> int:
    doc = json.loads(PATH.read_text())
    existing = {(i["problem"], json.dumps(i["params"], sort_keys=True)) for i in doc["items"]}
    fresh = [i for i in build()
             if (i["problem"], json.dumps(i["params"], sort_keys=True)) not in existing]
    doc["items"].extend(fresh)
    PATH.write_text(json.dumps(doc, indent=2, ensure_ascii=False) + "\n")
    print(f"added {len(fresh)} param sets -> {len(doc['items'])} total")
    counts: dict[str, int] = {}
    for i in doc["items"]:
        counts[i["problem"]] = counts.get(i["problem"], 0) + 1
    for k, v in sorted(counts.items(), key=lambda x: -x[1]):
        print(f"  {k:<22} {v}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
