"""Tests for the parts that must never be subtly wrong:
scoring guarantees, the balancing engine, and the content validators.

Run:  cd backend && python -m pytest -q
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.content.schema import QuestionDef, QuestionOption  # noqa: E402
from app.content.validators import content_hash, normalise_text, validate_question  # noqa: E402
from app.services.balancing_engine import FormulaError, hint_for, parse_formula, solve_equation, verify  # noqa: E402
from app.services.progress_service import level_for_xp, xp_for_level  # noqa: E402
from app.services.scoring_engine import (  # noqa: E402
    DIFFICULTY_POINTS,
    mastery_update,
    score_answer,
    speed_factor,
    streak_multiplier,
    summarise,
)


# ───────────────────────── scoring guarantees ─────────────────────────


def test_wrong_answer_never_outscores_correct():
    """The brief's hard rule: a fast wrong answer must never beat a slow correct one."""
    fastest_wrong = score_answer(difficulty="hard", response_ms=1, time_budget_ms=10000, streak_before=50, is_correct=False)
    slowest_correct = score_answer(difficulty="easy", response_ms=99999, time_budget_ms=10000, streak_before=0, is_correct=True)
    assert fastest_wrong.points <= 0
    assert slowest_correct.points > 0
    assert slowest_correct.points > fastest_wrong.points


def test_speed_bonus_is_capped_and_only_for_correct():
    base = DIFFICULTY_POINTS["medium"]
    instant = score_answer(difficulty="medium", response_ms=0, time_budget_ms=10000, streak_before=0, is_correct=True)
    slow = score_answer(difficulty="medium", response_ms=10000, time_budget_ms=10000, streak_before=0, is_correct=True)
    assert instant.speed_bonus <= round(0.4 * base)
    assert instant.points > slow.points
    wrong = score_answer(difficulty="medium", response_ms=0, time_budget_ms=10000, streak_before=0, is_correct=False)
    assert wrong.speed_bonus == 0


def test_speed_factor_bounds():
    assert speed_factor(0, 10000) == pytest.approx(1.0)
    assert speed_factor(10000, 10000) == 0.0
    assert speed_factor(99999, 10000) == 0.0
    assert 0.0 < speed_factor(5000, 10000) < 1.0
    assert speed_factor(1000, 0) == 0.0


def test_streak_multiplier_capped_at_one_point_five():
    assert streak_multiplier(0) == 1.0
    assert streak_multiplier(10) == 1.5
    assert streak_multiplier(10_000) == 1.5


def test_blind_clicking_has_negative_expected_value():
    """Random guessing on 4 options must not be a winning strategy.

    A wrong answer resets the streak, so sustained guessing collapses the
    multiplier while occasional correct answers earn at most the base points.
    """
    import random

    rng = random.Random(42)
    guess_score = 0
    streak = 0
    for _ in range(400):
        correct = rng.random() < 0.25
        result = score_answer(difficulty="medium", response_ms=1500, time_budget_ms=10000, streak_before=streak, is_correct=correct)
        guess_score += result.points
        streak = streak + 1 if correct else 0

    honest_score = 0
    streak = 0
    for _ in range(400):
        result = score_answer(difficulty="medium", response_ms=4000, time_budget_ms=10000, streak_before=streak, is_correct=True)
        honest_score += result.points
        streak += 1

    assert guess_score < honest_score * 0.35


def test_wrong_penalty_only_applies_when_configured():
    rush = score_answer(difficulty="medium", response_ms=1000, time_budget_ms=10000, streak_before=0, is_correct=False, wrong_penalty_factor=0.0)
    exam = score_answer(difficulty="medium", response_ms=1000, time_budget_ms=10000, streak_before=0, is_correct=False, wrong_penalty_factor=0.15)
    assert rush.points == 0
    assert exam.points < 0
    assert exam.points >= -20  # penalty is capped so it cannot dominate a session


def test_summarise_tracks_streak_and_accuracy():
    attempts = [
        {"difficulty": "easy", "response_ms": 1000, "time_budget_ms": 8000, "is_correct": True, "topic_id": "t1"},
        {"difficulty": "easy", "response_ms": 2000, "time_budget_ms": 8000, "is_correct": True, "topic_id": "t1"},
        {"difficulty": "hard", "response_ms": 3000, "time_budget_ms": 12000, "is_correct": False, "topic_id": "t2"},
        {"difficulty": "medium", "response_ms": 4000, "time_budget_ms": 10000, "is_correct": True, "topic_id": "t2"},
    ]
    summary = summarise(attempts)
    assert summary.answered == 4
    assert summary.correct == 3
    assert summary.best_streak == 2
    assert summary.accuracy == pytest.approx(0.75)
    assert summary.avg_response_ms == pytest.approx(2500)
    assert summary.fastest_response_ms == 1000
    assert summary.score > 0
    assert summary.xp == summary.score // 10
    assert summary.by_topic["t1"]["accuracy"] == pytest.approx(1.0)


def test_summarise_is_deterministic_for_parity_with_client():
    """Fixed fixture — the TypeScript mirror must produce these exact numbers."""
    result = score_answer(difficulty="medium", response_ms=2500, time_budget_ms=10000, streak_before=3, is_correct=True)
    # speed_factor(2500, 10000) = 0.75**0.75 = 0.8059 -> bonus round(0.4*150*0.8059) = 48
    # multiplier(3) = 1.15 -> points round((150+48)*1.15) = 228
    assert (result.base_points, result.speed_bonus, result.multiplier, result.points) == (150, 48, 1.15, 228)


def test_mastery_moves_toward_result_and_stays_bounded():
    assert mastery_update(0.5, True, "easy") > 0.5
    assert mastery_update(0.5, False, "easy") < 0.5
    for _ in range(50):
        value = mastery_update(0.99, True, "easy")
    assert 0.0 <= value <= 1.0
    for _ in range(50):
        value = mastery_update(0.01, False, "hard")
    assert 0.0 <= value <= 1.0


def test_level_curve_is_monotonic():
    thresholds = [xp_for_level(n) for n in range(1, 15)]
    assert thresholds == sorted(thresholds)
    assert thresholds[0] == 0
    assert level_for_xp(0) == 1
    assert level_for_xp(thresholds[4]) == 5
    assert level_for_xp(10**9) >= 15


# ───────────────────────── balancing engine ─────────────────────────


def test_parse_formula_simple_and_nested():
    assert parse_formula("H2O") == {"H": 2, "O": 1}
    assert parse_formula("Ca(OH)2") == {"Ca": 1, "O": 2, "H": 2}
    assert parse_formula("Al2(SO4)3") == {"Al": 2, "S": 3, "O": 12}
    assert parse_formula("Pb(NO3)2") == {"Pb": 1, "N": 2, "O": 6}
    assert parse_formula("Fe") == {"Fe": 1}
    assert parse_formula("C6H12O6") == {"C": 6, "H": 12, "O": 6}


def test_parse_formula_rejects_garbage():
    for bad in ["", "  ", "123", "H2O(", "(H2O", "h2o", "Xy!"]:
        with pytest.raises(FormulaError):
            parse_formula(bad)


def test_solve_equation_finds_minimal_coefficients():
    equation = solve_equation(["Fe", "O2"], ["Fe2O3"])
    assert equation.coefficients == (4, 3, 2)
    assert equation.as_text() == "4 Fe + 3 O2 \u2192 2 Fe2O3"


def test_solve_equation_already_balanced_stays_unity():
    equation = solve_equation(["CaCO3"], ["CaO", "CO2"])
    assert equation.coefficients == (1, 1, 1)


def test_solve_equation_hard_cases():
    assert solve_equation(["C6H12O6", "O2"], ["CO2", "H2O"]).coefficients == (1, 6, 6, 6)
    assert solve_equation(["Pb(NO3)2"], ["PbO", "NO2", "O2"]).coefficients == (2, 2, 4, 1)
    assert solve_equation(["Al", "HCl"], ["AlCl3", "H2"]).coefficients == (2, 6, 2, 3)


def test_verify_checks_conservation_not_strings():
    equation = solve_equation(["H2", "O2"], ["H2O"])
    assert equation.coefficients == (2, 1, 2)

    assert verify(equation, [2, 1, 2]).verdict == "balanced_simplest"
    # A valid multiple still conserves atoms -> recognised, but flagged as unsimplified.
    assert verify(equation, [4, 2, 4]).verdict == "balanced_unsimplified"
    assert verify(equation, [1, 1, 1]).verdict == "unbalanced"
    assert verify(equation, [2, 1, 2]).is_simplest is True
    assert verify(equation, [4, 2, 4]).is_balanced is True


def test_verify_rejects_zero_and_negative_coefficients():
    equation = solve_equation(["H2", "O2"], ["H2O"])
    assert verify(equation, [0, 1, 2]).is_balanced is False
    assert verify(equation, [-2, 1, 2]).is_balanced is False


def test_verify_reports_which_element_is_off():
    equation = solve_equation(["Fe", "O2"], ["Fe2O3"])
    result = verify(equation, [1, 1, 1])
    assert result.is_balanced is False
    assert set(result.mismatched_elements) == {"Fe", "O"}
    assert result.per_element["O"] == {"left": 2, "right": 3}


def test_hint_does_not_reveal_the_answer():
    equation = solve_equation(["Fe", "O2"], ["Fe2O3"])
    hint = hint_for(equation, [1, 1, 1])
    assert "4" not in hint and "3" not in hint.split("atoms")[0]
    assert hint  # non-empty guidance


def test_unbalanceable_equation_raises():
    with pytest.raises(FormulaError):
        solve_equation(["H2O"], ["Fe"])


# ───────────────────────── validators ─────────────────────────


def _question(**overrides) -> QuestionDef:
    base = dict(
        id="test.item.one",
        chapter="sci-chem-ch1",
        topic=None,
        question_type="mcq_single",
        prompt="What is the valency of hydrogen?",
        options=[
            QuestionOption(key="a", text="1"),
            QuestionOption(key="b", text="2"),
            QuestionOption(key="c", text="3"),
            QuestionOption(key="d", text="4"),
        ],
        answer_key="a",
        difficulty="easy",
        source_ref="test",
    )
    base.update(overrides)
    return QuestionDef.model_validate(base)


def test_valid_question_passes():
    assert validate_question(_question()).ok


def test_validator_rejects_wrong_option_count():
    assert not validate_question(_question(options=[QuestionOption(key="a", text="1")], answer_key="a")).ok


def test_validator_rejects_answer_not_in_options():
    question = _question(answer_key="d")
    result = validate_question(question)
    # 'd' exists here, so use a truly absent key
    bad = _question()
    bad.answer_key = "z"
    assert not validate_question(bad).ok
    assert result.ok


def test_validator_rejects_duplicate_options():
    question = _question(
        options=[
            QuestionOption(key="a", text="1"),
            QuestionOption(key="b", text="1"),
            QuestionOption(key="c", text="3"),
            QuestionOption(key="d", text="4"),
        ]
    )
    result = validate_question(question)
    assert not result.ok
    assert any("duplicate_option" in e for e in result.errors)


def test_validator_rejects_implausible_distractors():
    question = _question(
        options=[
            QuestionOption(key="a", text="1"),
            QuestionOption(key="b", text="banana"),
            QuestionOption(key="c", text="3"),
            QuestionOption(key="d", text="4"),
        ]
    )
    assert not validate_question(question).ok


def test_validator_rejects_markup_and_control_characters():
    assert not validate_question(_question(prompt="<script>alert(1)</script> valency?")).ok
    assert not validate_question(_question(prompt="valency?\x00")).ok


def test_validator_requires_source_reference():
    assert not validate_question(_question(source_ref="  ")).ok


def test_normalise_text_preserves_meaningful_symbols():
    """CnH2n+2 and CnH2n-2 are different answers; -1 and 1 are different answers."""
    assert normalise_text("CnH2n+2") != normalise_text("CnH2n-2")
    assert normalise_text("-1") != normalise_text("1")
    assert normalise_text("Red.") == normalise_text("red")
    assert normalise_text("  Water  ") == normalise_text("water")
    assert normalise_text("Fe₂O₃") == normalise_text("fe2o3")


def test_content_hash_ignores_option_order():
    first = _question()
    second = _question(
        options=[
            QuestionOption(key="a", text="4"),
            QuestionOption(key="b", text="3"),
            QuestionOption(key="c", text="2"),
            QuestionOption(key="d", text="1"),
        ],
        answer_key="d",
    )
    assert content_hash(first) == content_hash(second)


def test_content_hash_detects_a_changed_answer():
    """Editing the answer key (without touching option text) must be detected on reseed."""
    assert content_hash(_question()) != content_hash(_question(answer_key="b"))


def test_content_hash_detects_a_changed_stimulus():
    assert content_hash(_question()) != content_hash(_question(stimulus={"kind": "element_symbol", "symbol": "He"}))


def test_balancing_item_skips_option_rules():
    question = _question(
        question_type="balancing",
        options=[],
        answer_key="balanced",
        stimulus={"reactants": ["Fe", "O2"], "products": ["Fe2O3"], "solution": [4, 3, 2]},
    )
    assert validate_question(question).ok


def test_balancing_item_requires_equation_shape():
    question = _question(question_type="balancing", options=[], answer_key="balanced", stimulus={})
    assert not validate_question(question).ok


class TestBuildOptionsWhitespace:
    """Regression: authored content with trailing whitespace used to crash seeding
    with a bare StopIteration, because QuestionOption strips option text while
    build_options compared against the unstripped answer."""

    def test_trailing_whitespace_still_finds_answer_key(self):
        from app.content.generators.base import build_options
        import random

        options, key = build_options("Dispose of the rest ", ["Reduce", "Reuse", "Recycle"], random.Random(1))
        assert len(options) == 4
        matched = [o for o in options if o.key == key]
        assert len(matched) == 1
        assert matched[0].text == "Dispose of the rest"

    def test_whitespace_only_difference_does_not_collide(self):
        from app.content.generators.base import build_options
        import random

        options, key = build_options(" 42 ", ["1", "2", "3"], random.Random(7))
        assert next(o.text for o in options if o.key == key) == "42"

    def test_sequence_steps_are_stripped(self):
        from app.content.generators import sequences

        items = [{
            "kind": "sequence", "name": "waste management",
            "sequence": ["Reduce the amount of waste", "Reuse items", "Recycle materials",
                         "Recover energy", "Dispose of the rest "],
            "chapter": "sci-bio-env", "topic": "sci-bio-env.waste",
        }]
        qs = sequences.generate(items, "sci-bio-env", "sci-bio-env.waste", "test")
        assert qs, "a trailing-space final step must not abort generation"
        for q in qs:
            correct = next(o for o in q.options if o.key == q.answer_key)
            assert correct.text == correct.text.strip()
            assert len(q.options) == 4
            texts = [o.text for o in q.options]
            assert len(set(texts)) == 4, "options must stay distinct after stripping"


class TestCompletionBonusGating:
    """Regression: a flat completion bonus paid 100 points at 0% accuracy,
    rewarding blind clicking against the scoring contract."""

    @staticmethod
    def _run(correct_count: int, total: int = 10):
        attempts = [
            {"question_id": f"q{i}", "is_correct": i < correct_count,
             "difficulty": "medium", "response_ms": 3000, "time_budget_ms": 10000}
            for i in range(total)
        ]
        return summarise(attempts, completion_ratio=1.0)

    def test_zero_accuracy_earns_no_completion_bonus(self):
        summary = self._run(0)
        assert summary.accuracy == 0.0
        assert summary.completion_bonus == 0, "finishing a test you got all wrong must not pay out"
        assert summary.score == 0
        assert summary.xp == 0

    def test_completion_bonus_scales_with_accuracy(self):
        assert self._run(0).completion_bonus == 0
        assert self._run(5).completion_bonus < self._run(10).completion_bonus
        assert self._run(10).completion_bonus > 0

    def test_all_wrong_never_beats_all_right(self):
        wrong = self._run(0)
        right = self._run(10)
        assert right.score > wrong.score
        assert wrong.score == 0, "a fully wrong session must score exactly zero"


class TestQuestionIdUniqueness:
    """Regression: question ids are the seeder's upsert key, so two different
    questions sharing one id means one of them is silently overwritten and never
    reaches a student. Two separate bugs did exactly that."""

    def test_slugify_preserves_a_negative_sign(self):
        # "poly-roots-3--2" and "poly-roots--3-2" both collapsed to
        # "poly-roots-3-2" once the dash run was squeezed, so alpha=3/beta=-2 and
        # alpha=-3/beta=2 minted the same id.
        from app.content.generators.base import slugify

        assert slugify("poly-roots-3--2") != slugify("poly-roots--3-2")
        assert slugify("poly-roots-3--2") != slugify("poly-roots-3-2")
        assert slugify("poly-roots-3--2") == "poly-roots-3-neg2"

    def test_slugify_leaves_ordinary_text_alone(self):
        from app.content.generators.base import slugify

        assert slugify("The Silk Route - connected") == "the-silk-route-connected"
        assert slugify("Insulin / secreted by") == "insulin-secreted-by"

    def test_whole_content_bank_has_unique_ids_and_valid_questions(self):
        """Every content file, generated the way the seeder generates it.

        Catches the two id bugs above plus any wording regression, because a
        malformed stem passes structural validation while still reading badly.
        """
        import json
        import re
        from collections import Counter

        from app.content.generators import generate_from_fact_file
        from app.content.schema import FactFile
        from scripts.lint_content import load_index

        content_dir = Path(__file__).resolve().parents[1] / "content"
        index = load_index()
        owners: dict[str, str] = {}
        clashes: list[str] = []
        errors: list[str] = []
        bad_wording: list[str] = []
        counts: Counter = Counter()

        # Reuse the linter's own checks rather than restating them here, so the
        # test and scripts/lint_content.py cannot drift apart. Each check carries
        # a flag saying whether equation files are exempt: `x + 2y - 5 = 0` and
        # `1/v - 1/u = 1/f` are correct content, not malformed stems.
        from scripts.lint_content import CHECKS, CheckContext, is_equation_file

        for path in sorted(content_dir.rglob("*.json")):
            if path.name in {"curriculum.json", "modes.json"}:
                continue
            fact_file = FactFile.model_validate(json.loads(path.read_text()))
            is_equation = is_equation_file(path)
            per_file_ids: Counter = Counter()
            for question in generate_from_fact_file(fact_file):
                counts[path.name] += 1
                per_file_ids[question.id] += 1
                if question.id in owners and owners[question.id] != path.name:
                    clashes.append(f"{question.id} in {owners[question.id]} and {path.name}")
                owners.setdefault(question.id, path.name)
                result = validate_question(question, index)
                errors.extend(f"{question.id}: {e}" for e in result.errors)
                ctx = CheckContext(is_equation=is_equation, tags=tuple(question.tags or ()))
                for label, pattern, skip in CHECKS:
                    if skip(question.prompt, ctx):
                        continue
                    if pattern.search(question.prompt):
                        bad_wording.append(f"[{label}] {question.prompt}")
            clashes.extend(
                f"{qid} twice in {path.name}"
                for qid, n in per_file_ids.items() if n > 1
            )

        assert sum(counts.values()) > 9000, "the bank should stay above the 10k target's floor"
        assert not errors, f"{len(errors)} invalid question(s): {errors[:3]}"
        assert not clashes, f"{len(clashes)} id collision(s): {clashes[:3]}"
        assert not bad_wording, f"{len(bad_wording)} malformed prompt(s): {bad_wording[:3]}"

    def test_seeding_reaches_a_fixed_point(self):
        """Seeding the same content twice into the same database writes nothing.

        Clashing question ids used to make this impossible: two files took turns
        overwriting one row, so every run reported those questions as updated and
        bumped their revision forever.
        """
        import sqlite3

        from app.db.migrate import migrate
        from app.db.seed import seed_all

        content_dir = Path(__file__).resolve().parents[1] / "content"
        # isolation_level=None matches how the app opens SQLite: autocommit, with
        # transactions started explicitly. Without it the driver opens an implicit
        # transaction and `transaction()` cannot BEGIN inside it.
        conn = sqlite3.connect(":memory:", isolation_level=None)
        conn.row_factory = sqlite3.Row
        migrate(conn)

        first = seed_all(conn, content_dir)
        assert not first.errors, first.errors[:3]
        assert first.questions_inserted > 9000, "the bank should stay above 9k questions"
        assert first.questions_archived == 0, "a fresh database has no orphans to retire"

        second = seed_all(conn, content_dir)
        assert second.questions_inserted == 0, "nothing new should appear on a re-seed"
        assert second.questions_updated == 0, (
            f"{second.questions_updated} row(s) churned - a question id is being "
            f"claimed by two definitions"
        )
        assert second.questions_archived == 0, "a re-seed must not retire anything"
        assert second.questions_unchanged == first.questions_inserted

        # User history sits in other tables and must survive content reseeding.
        assert conn.execute("SELECT COUNT(*) FROM questions WHERE status='approved'").fetchone()[0] \
            == first.questions_inserted
