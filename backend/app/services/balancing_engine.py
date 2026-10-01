"""BalancingEngine — chemical formula parsing, balancing solver and verifier.

Design goals from the brief:
  * verify **chemical conservation**, never compare against a stored string;
  * be data-driven so new equations can be added without code changes.

Public API
  parse_formula("Ca(OH)2")                 -> {"Ca": 1, "O": 2, "H": 2}
  solve_equation(reactants, products)      -> Equation (minimal integer coefficients)
  verify(equation, coefficients)           -> VerificationResult
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from fractions import Fraction
from math import gcd
from typing import Iterable, Sequence

_TOKEN_RE = re.compile(r"(?P<paren>[()])(?P<mult>\d*)|(?P<sym>[A-Z][a-z]?)(?P<count>\d*)")
_VALID_FORMULA_RE = re.compile(r"^[A-Za-z0-9()\[\]]+$")


class FormulaError(ValueError):
    """Raised when a chemical formula cannot be parsed."""


# ─────────────────────────── parsing ───────────────────────────


def parse_formula(formula: str) -> dict[str, int]:
    """Parse a chemical formula into {element: atom_count}.

    Supports nested parentheses and multipliers, e.g. Ca(OH)2, Al2(SO4)3, K4[Fe(CN)6].
    Raises FormulaError for anything malformed so bad content fails at seed time,
    not in front of a student.
    """
    if not formula or not isinstance(formula, str):
        raise FormulaError("Formula must be a non-empty string")

    cleaned = formula.replace(" ", "").replace("[", "(").replace("]", ")")
    if not cleaned or not _VALID_FORMULA_RE.match(cleaned):
        raise FormulaError(f"Unsupported characters in formula: {formula!r}")

    pos, atoms = _parse_group(cleaned, 0, len(cleaned))
    if pos != len(cleaned):
        raise FormulaError(f"Unexpected trailing characters in formula: {formula!r}")
    if not atoms:
        raise FormulaError(f"Formula contains no elements: {formula!r}")
    return atoms


def _parse_group(text: str, start: int, end: int) -> tuple[int, dict[str, int]]:
    atoms: dict[str, int] = {}
    pos = start

    while pos < end:
        char = text[pos]
        if char == "(":
            inner_end = _find_matching_paren(text, pos, end)
            pos, inner = _parse_group(text, pos + 1, inner_end)
            pos += 1  # consume ')'
            multiplier = _read_int(text, pos, end)
            pos = multiplier.pos
            _merge(atoms, inner, multiplier.value)
            continue

        if char == ")":
            break  # closing paren handled by caller

        if not char.isupper():
            raise FormulaError(f"Expected an element symbol at position {pos} in {text!r}")

        match = re.match(r"[A-Z][a-z]?", text[pos:end])
        if not match:
            raise FormulaError(f"Malformed element symbol at position {pos} in {text!r}")
        symbol = match.group(0)
        pos += len(symbol)
        count = _read_int(text, pos, end)
        pos = count.pos
        atoms[symbol] = atoms.get(symbol, 0) + count.value

    return pos, atoms


def _find_matching_paren(text: str, open_pos: int, end: int) -> int:
    depth = 0
    for index in range(open_pos, end):
        if text[index] == "(":
            depth += 1
        elif text[index] == ")":
            depth -= 1
            if depth == 0:
                return index
    raise FormulaError(f"Unbalanced parenthesis in {text!r}")


@dataclass(frozen=True)
class _IntRead:
    value: int
    pos: int


def _read_int(text: str, pos: int, end: int) -> _IntRead:
    digits = ""
    while pos < end and text[pos].isdigit():
        digits += text[pos]
        pos += 1
    return _IntRead(value=int(digits) if digits else 1, pos=pos)


def _merge(target: dict[str, int], source: dict[str, int], multiplier: int) -> None:
    for element, count in source.items():
        target[element] = target.get(element, 0) + count * multiplier


# ─────────────────────────── solving ───────────────────────────


@dataclass(frozen=True)
class Equation:
    """A balanced equation with minimal whole-number coefficients."""

    reactants: tuple[str, ...]
    products: tuple[str, ...]
    coefficients: tuple[int, ...]  # reactants then products, same order

    @property
    def reactant_coefficients(self) -> tuple[int, ...]:
        return self.coefficients[: len(self.reactants)]

    @property
    def product_coefficients(self) -> tuple[int, ...]:
        return self.coefficients[len(self.reactants) :]

    @property
    def elements(self) -> tuple[str, ...]:
        seen: list[str] = []
        for formula in (*self.reactants, *self.products):
            for element in parse_formula(formula):
                if element not in seen:
                    seen.append(element)
        return tuple(sorted(seen))

    def as_text(self, with_coefficients: bool = True) -> str:
        def render(formulas: Sequence[str], coeffs: Sequence[int]) -> str:
            parts = []
            for formula, coeff in zip(formulas, coeffs):
                parts.append(formula if (coeff == 1 or not with_coefficients) else f"{coeff} {formula}")
            return " + ".join(parts)

        return (
            f"{render(self.reactants, self.reactant_coefficients)} "
            f"\u2192 {render(self.products, self.product_coefficients)}"
        )


def solve_equation(reactants: Iterable[str], products: Iterable[str]) -> Equation:
    """Find the minimal positive integer coefficients that conserve every element."""
    left = [r.strip() for r in reactants if r and r.strip()]
    right = [p.strip() for p in products if p and p.strip()]
    if not left or not right:
        raise FormulaError("An equation needs at least one reactant and one product")

    species = left + right
    parsed = [parse_formula(f) for f in species]
    elements = sorted({e for atoms in parsed for e in atoms})

    # Matrix A (elements x species): reactants positive, products negative.
    matrix = [[Fraction(atoms.get(el, 0)) * (1 if i < len(left) else -1) for i, atoms in enumerate(parsed)] for el in elements]

    solution = _nullspace_vector(matrix, len(species))
    if solution is None:
        raise FormulaError(f"Equation cannot be balanced: {' + '.join(left)} -> {' + '.join(right)}")

    coefficients = _to_minimal_integers(solution)
    if any(c <= 0 for c in coefficients):
        raise FormulaError(f"Equation has no physically meaningful balance: {' + '.join(left)} -> {' + '.join(right)}")

    return Equation(reactants=tuple(left), products=tuple(right), coefficients=tuple(coefficients))


def _nullspace_vector(matrix: list[list[Fraction]], columns: int) -> list[Fraction] | None:
    """Return a single nullspace basis vector, or None if the solution is not unique up to scale."""
    rows = [row[:] for row in matrix]
    pivots: list[int] = []
    row_index = 0

    for col in range(columns):
        pivot_row = next((r for r in range(row_index, len(rows)) if rows[r][col] != 0), None)
        if pivot_row is None:
            continue
        rows[row_index], rows[pivot_row] = rows[pivot_row], rows[row_index]
        scale = rows[row_index][col]
        rows[row_index] = [v / scale for v in rows[row_index]]
        for r in range(len(rows)):
            if r != row_index and rows[r][col] != 0:
                factor = rows[r][col]
                rows[r] = [a - factor * b for a, b in zip(rows[r], rows[row_index])]
        pivots.append(col)
        row_index += 1

    free_columns = [c for c in range(columns) if c not in pivots]
    if len(free_columns) != 1:
        # More than one free variable means the equation is ambiguous (or over-constrained
        # with no unique ratio). Class 10 equations always have exactly one.
        return None

    free = free_columns[0]
    vector = [Fraction(0)] * columns
    vector[free] = Fraction(1)
    for pivot in pivots:
        vector[pivot] = -rows[pivots.index(pivot)][free]
    return vector


def _to_minimal_integers(vector: Sequence[Fraction]) -> list[int]:
    denominator = 1
    for value in vector:
        denominator = denominator * value.denominator // gcd(denominator, value.denominator)
    integers = [int(value * denominator) for value in vector]

    if all(i < 0 for i in integers):
        integers = [-i for i in integers]

    common = 0
    for value in integers:
        common = gcd(common, abs(value))
    if common > 1:
        integers = [value // common for value in integers]
    return integers


# ─────────────────────────── verifying ───────────────────────────


@dataclass
class VerificationResult:
    is_balanced: bool
    is_simplest: bool
    per_element: dict[str, dict[str, int]] = field(default_factory=dict)
    mismatched_elements: list[str] = field(default_factory=list)
    message: str = ""

    @property
    def verdict(self) -> str:
        if not self.is_balanced:
            return "unbalanced"
        return "balanced_simplest" if self.is_simplest else "balanced_unsimplified"


def verify(equation: Equation, coefficients: Sequence[int]) -> VerificationResult:
    """Check a student's coefficients by counting atoms on both sides."""
    species = (*equation.reactants, *equation.products)
    if len(coefficients) != len(species):
        raise FormulaError(f"Expected {len(species)} coefficients, got {len(coefficients)}")

    counts = [int(c) for c in coefficients]
    if any(c < 0 for c in counts):
        return VerificationResult(is_balanced=False, is_simplest=False, message="Coefficients cannot be negative.")
    if any(c == 0 for c in counts):
        return VerificationResult(
            is_balanced=False,
            is_simplest=False,
            message="Every substance in the reaction takes part, so no coefficient can be zero.",
        )

    per_element: dict[str, dict[str, int]] = {}
    mismatched: list[str] = []

    for element in equation.elements:
        left = sum(c * parse_formula(f).get(element, 0) for f, c in zip(equation.reactants, counts[: len(equation.reactants)]))
        right = sum(c * parse_formula(f).get(element, 0) for f, c in zip(equation.products, counts[len(equation.reactants) :]))
        per_element[element] = {"left": left, "right": right}
        if left != right:
            mismatched.append(element)

    if mismatched:
        detail = ", ".join(f"{el}: {per_element[el]['left']} vs {per_element[el]['right']}" for el in mismatched)
        return VerificationResult(
            is_balanced=False,
            is_simplest=False,
            per_element=per_element,
            mismatched_elements=mismatched,
            message=f"Not balanced yet. Atom count differs for {detail}.",
        )

    # Balanced — now check whether it is the simplest whole-number ratio.
    common = 0
    for value in counts:
        common = gcd(common, value)
    is_simplest = common <= 1

    message = "Balanced." if is_simplest else "Balanced, but divide every coefficient by the common factor to get the simplest ratio."
    return VerificationResult(
        is_balanced=True,
        is_simplest=is_simplest,
        per_element=per_element,
        mismatched_elements=[],
        message=message,
    )


def hint_for(equation: Equation, coefficients: Sequence[int]) -> str:
    """Produce a short, non-spoiling hint based on which element is currently off."""
    result = verify(equation, coefficients)
    if result.is_balanced:
        return "It balances now — check whether all coefficients share a common factor."
    element = result.mismatched_elements[0]
    counts = result.per_element[element]
    side = "reactant" if counts["left"] < counts["right"] else "product"
    return f"{element} atoms do not match ({counts['left']} on the left, {counts['right']} on the right). Try adjusting a coefficient on the {side} side that contains {element}."


def atom_counts(formula: str) -> dict[str, int]:
    """Convenience wrapper used by the API to render an atom table in the UI."""
    return parse_formula(formula)
