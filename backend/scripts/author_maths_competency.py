"""Write the competency-based Mathematics items.

Usage:  python3 scripts/author_maths_competency.py
Writes: content/competency/maths.json

Every maths question in the bank so far came from a parameterised generator: the
generator picks numbers, the handler computes an answer, and the distractors are
built from the mistakes a student makes. That is strong coverage for the skills
and weak for the two things the paper also tests - setting a problem up from a
description, and reading several linked results off one situation.

These items are authored directly. A single case carries its situation into every
sub-question, so a student works one problem through several steps instead of
meeting four unrelated sums, which is how a case study is set on the paper.

The numbers are chosen so the arithmetic is exact and the answer choices are the
mistakes actually worth catching: using the diameter where the radius is needed,
forgetting the slant height, taking n to be n - 1, or reading the mean off a
frequency table without weighting by the frequencies. Distractors that merely
differ in magnitude teach nothing.

Nothing is copied from a textbook or a question bank. The situations - a garden,
a savings scheme, a toy, a coordinate map of a park - are composed here.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))

OUT = BACKEND / "content" / "competency" / "maths.json"

SOURCE_REF = (
    "Original competency-based items written for the CBSE/NCERT Class 10 "
    "Mathematics (2025-26) syllabus. Situations, figures and question wording are "
    "composed here; no question is reproduced from a textbook, guide or question "
    "bank."
)


def ar(chapter: str, topic: str, assertion: str, reason: str, verdict: str,
       explanation: str, difficulty: str = "medium", competency: str = "analysis") -> dict:
    """One assertion-reason item. The four options come from the generator."""
    return {
        "kind": "assertion_reason",
        "chapter": chapter,
        "topic": topic,
        "assertion": assertion,
        "reason": reason,
        "verdict": verdict,
        "explanation": explanation,
        "difficulty": difficulty,
        "competency": competency,
    }


def case(chapter: str, topic: str, stem: str, questions: list[dict],
         competency: str = "analysis") -> dict:
    """One situation with its linked sub-questions."""
    for q in questions:
        q.setdefault("chapter", chapter)
        q.setdefault("topic", topic)
        q.setdefault("competency", competency)
    return {"kind": "case_study", "chapter": chapter, "topic": topic,
            "stem": stem, "questions": questions}


def app(chapter: str, topic: str, prompt: str, options: list[str], answer: int,
        explanation: str, difficulty: str = "medium",
        competency: str = "application") -> dict:
    """One standalone application or analytical item."""
    return {
        "kind": "competency",
        "format": "application",
        "chapter": chapter,
        "topic": topic,
        "prompt": prompt,
        "options": options,
        "answer": answer,
        "explanation": explanation,
        "difficulty": difficulty,
        "competency": competency,
    }


# ══════════════════════════════════════════════════════════════════════
# Assertion and Reason
# ══════════════════════════════════════════════════════════════════════

ASSERTION_REASON = [
    ar("m-real", "m-real.irrational",
       "The square root of 2 is an irrational number.",
       "It cannot be written in the form p by q, where p and q are integers and q is not zero.",
       "both_true_explains",
       "Both are true and the reason is the definition the assertion rests on. The proof assumes "
       "that the square root of 2 can be written in lowest terms and shows that both p and q would "
       "then have to be even, contradicting that they share no common factor."),

    ar("m-real", "m-real.hcf-lcm",
       "The product of the HCF and the LCM of two positive integers equals the product of the two integers.",
       "Every prime factor of either integer appears in the HCF to the lower of its two powers, and in the LCM to the higher.",
       "both_true_explains",
       "Both are true and the reason explains the assertion: between them, the lower power and the "
       "higher power account for the factor exactly once in each integer, so the two products match. "
       "This is why it is a quick way to find the LCM of two numbers."),

    ar("m-real", "m-real.hcf-lcm",
       "The rule that the product of the HCF and LCM equals the product of the numbers holds for three numbers as well.",
       "For two positive integers, every prime factor is counted once at its lowest power in the HCF and once at its highest power in the LCM.",
       "a_false_r_true",
       "The reason is correct in stating the rule for two numbers, and that is exactly why the "
       "assertion fails: with three numbers a prime's middle power is counted in the LCM but is left "
       "out of the HCF entirely, so the two products no longer match."),

    ar("m-real", "m-real.fta",
       "The prime factorisation of a composite number is unique apart from the order of the factors.",
       "The Fundamental Theorem of Arithmetic guarantees that every composite number can be expressed as a product of primes in only one way.",
       "both_true_explains",
       "Both are true and the reason is the theorem that the assertion restates. It is what makes "
       "prime factorisation a reliable tool for HCF and LCM."),

    ar("m-poly", "m-poly.zeroes",
       "A quadratic polynomial has at most two zeroes.",
       "The graph of a quadratic polynomial is a parabola, and a parabola meets the x-axis in at most two points.",
       "both_true_explains",
       "Both are true and the reason explains the assertion: a zero is a point where the graph "
       "crosses or touches the x-axis, and a parabola can do that at two points, at one, or at none."),

    ar("m-poly", "m-poly.coefficients",
       "The sum of the zeroes of x squared minus 5x plus 6 is 5.",
       "For a quadratic polynomial, the sum of the zeroes is the negative of the coefficient of x divided by the coefficient of x squared.",
       "both_true_explains",
       "Both are true and the reason explains the assertion: here the coefficient of x is minus 5, "
       "so the sum is minus minus 5, which is 5. The zeroes are 2 and 3, and indeed 2 plus 3 is 5."),

    ar("m-linear", "m-linear.consistency",
       "A pair of linear equations in two variables can have exactly two solutions.",
       "Two straight lines in a plane can meet at only one point, be parallel, or coincide.",
       "a_false_r_true",
       "The reason is correct - those are the only three possibilities - and it is precisely why the "
       "assertion is false. One point gives a unique solution, no point gives none, and infinitely "
       "many points give infinitely many solutions. Two is impossible."),

    ar("m-linear", "m-linear.graphical",
       "The pair of equations 2x plus 3y equals 7 and 4x plus 6y equals 14 has infinitely many solutions.",
       "The second equation is obtained by multiplying the first by 2, so the two represent the same line.",
       "both_true_explains",
       "Both are true and the reason explains the assertion: one equation is a multiple of the other, "
       "so they coincide rather than intersect at a single point, and every point on the common line "
       "satisfies both."),

    ar("m-quad", "m-quad.discriminant",
       "The equation x squared plus 4x plus 5 equals zero has no real roots.",
       "Its discriminant is minus 4, and a negative discriminant means the equation has no real roots.",
       "both_true_explains",
       "Both are true and the reason explains the assertion: the discriminant is 16 minus 20, which "
       "is minus 4. Since a real root needs the square root of the discriminant, and the square root "
       "of a negative number is not real, no real root exists."),

    ar("m-quad", "m-quad.discriminant",
       "The equation x squared minus 6x plus 9 equals zero has two distinct real roots.",
       "Its discriminant is zero.",
       "a_false_r_true",
       "The reason is true but it contradicts the assertion rather than supporting it. A zero "
       "discriminant gives two equal roots, not two distinct ones; the equation factors as x minus 3 "
       "all squared, so 3 is the only root."),

    ar("m-quad", "m-quad.formula",
       "A quadratic equation whose roots are irrational and distinct has real roots.",
       "If the roots are irrational, the discriminant must be positive but not a perfect square.",
       "a_false_r_true",
       "Both parts are true, but the reason does not explain the assertion - it adds a further "
       "condition. Roots are real whenever the discriminant is not negative, and irrational distinct "
       "roots are simply the case where that discriminant is positive without being a perfect square."),

    ar("m-ap", "m-ap.nth-term",
       "The nth term of an arithmetic progression is a linear expression in n.",
       "The nth term equals a plus n minus 1 times d, which rearranges to dn plus the quantity a minus d.",
       "both_true_explains",
       "Both are true and the reason explains the assertion: dn plus a constant is exactly the form "
       "of a linear expression in n, with d as its slope. This is why the terms of an AP lie on a "
       "straight line when plotted against n."),

    ar("m-ap", "m-ap.sum",
       "The sum of the first n terms of an arithmetic progression is a quadratic expression in n.",
       "The sum is n by 2 times the quantity 2a plus n minus 1 times d, which expands to give a term in n squared.",
       "both_true_explains",
       "Both are true and the reason explains the assertion: expanding gives half d times n squared "
       "plus a term in n with no constant, which is a quadratic in n."),

    ar("m-ap", "m-ap.nth-term",
       "In an arithmetic progression, the difference between any term and the term before it is the same throughout.",
       "Each term after the first is obtained by adding a fixed number to the term before it.",
       "both_true_explains",
       "Both are true and the reason is the definition behind the assertion. The fixed number is the "
       "common difference, and it may be positive, negative or zero."),

    ar("m-tri", "m-tri.similarity",
       "All similar triangles are congruent.",
       "Similar triangles have equal corresponding angles and their corresponding sides are in the same ratio.",
       "a_false_r_true",
       "The reason is a correct statement and it is why the assertion fails: similarity fixes the "
       "shape but not the size, so the sides need only be in a common ratio. Congruence is the "
       "special case where that ratio is 1."),

    ar("m-tri", "m-tri.similarity",
       "All congruent triangles are similar.",
       "Congruent triangles have equal corresponding angles and equal corresponding sides.",
       "both_true_explains",
       "Both are true and the reason explains the assertion: equal sides means the ratio of "
       "corresponding sides is 1, which is a valid common ratio, and the angles are equal as well. So "
       "the conditions for similarity are met."),

    ar("m-tri", "m-tri.bpt",
       "A line drawn parallel to one side of a triangle to intersect the other two sides divides those two sides in the same ratio.",
       "The triangles formed on either side of the parallel line are similar, so their corresponding sides are proportional.",
       "both_true_explains",
       "Both are true and the reason explains the assertion, since equal corresponding angles give "
       "similarity and similar triangles give proportional sides. This is the Basic Proportionality "
       "Theorem."),

    ar("m-coord", "m-coord.distance",
       "The distance between two points is the same whichever point is taken first in the formula.",
       "The formula squares the differences of the coordinates, and squaring removes any negative sign.",
       "both_true_explains",
       "Both are true and the reason explains the assertion: swapping the points reverses the sign of "
       "each difference, but both differences are squared before being added, so the result is unchanged."),

    ar("m-trig", "m-trig.ratios",
       "The value of sin theta increases as theta increases from 0 to 90 degrees.",
       "In a right triangle, sin theta is the ratio of the side opposite theta to the hypotenuse, and as theta grows the opposite side grows while the hypotenuse stays fixed.",
       "both_true_explains",
       "Both are true and the reason explains the assertion: sin 0 is 0 and sin 90 is 1, and the "
       "ratio rises steadily in between. The opposite side can never exceed the hypotenuse, which is "
       "why the value never passes 1."),

    ar("m-trig", "m-trig.identities",
       "For every acute angle theta, sin squared theta plus cos squared theta equals 1.",
       "In a right triangle with hypotenuse c and the other two sides a and b, Pythagoras gives a squared plus b squared equals c squared, and dividing by c squared gives the identity.",
       "both_true_explains",
       "Both are true and the reason is the proof: sin theta is a over c and cos theta is b over c, "
       "so their squares are a squared over c squared and b squared over c squared, which add to "
       "exactly 1."),

    ar("m-circles", "m-circles.tangent",
       "The tangent drawn at any point of a circle is perpendicular to the radius through the point of contact.",
       "If the tangent were not perpendicular to that radius, another line through the point would be nearer the centre and would cut the circle at two points, contradicting that the tangent meets it at exactly one.",
       "both_true_explains",
       "Both are true and the reason is the standard proof by contradiction: among all lines through "
       "the point of contact, the radius is the shortest path to the centre, and the shortest line "
       "from a point to a line is the perpendicular."),

    ar("m-circles", "m-circles.tangent-count",
       "From a point outside a circle, exactly two tangents can be drawn, and they are equal in length.",
       "The two right triangles formed with the radius to each point of contact and the line joining the centre to the external point are congruent.",
       "both_true_explains",
       "Both are true and the reason explains the assertion: the triangles share the hypotenuse, "
       "have equal radii, and each has a right angle, so they are congruent by RHS. Congruence gives "
       "both the equality of the tangent lengths and the fact that there are exactly two."),

    ar("m-areas-circle", "m-areas-circle.sector",
       "The area of a sector of a circle is a fraction of the area of the whole circle.",
       "The angle of the sector is that same fraction of 360 degrees.",
       "both_true_explains",
       "Both are true and the reason explains the assertion: the sector is cut from the circle by two "
       "radii, and the share of the area is determined only by the share of the full turn the angle "
       "takes up."),

    ar("m-sav", "m-sav.sphere",
       "If the radius of a sphere is doubled, its volume becomes eight times as large.",
       "The volume of a sphere is proportional to the cube of its radius.",
       "both_true_explains",
       "Both are true and the reason explains the assertion: doubling the radius multiplies the cube "
       "by 2 cubed, which is 8, and the constant in front is unchanged."),

    ar("m-sav", "m-sav.sphere",
       "If the radius of a sphere is doubled, its surface area becomes eight times as large.",
       "The surface area of a sphere is proportional to the square of its radius.",
       "a_false_r_true",
       "The reason is true, and it is exactly what makes the assertion wrong: doubling the radius "
       "multiplies the square by 4, so the surface area becomes four times as large, not eight. The "
       "value eight would be right for the volume, which depends on the cube."),

    ar("m-stats", "m-stats.mean",
       "The mean of a set of observations is affected by a single very large value, while the median is not.",
       "The mean uses the size of every observation, whereas the median depends only on where an observation stands in the ordered list.",
       "both_true_explains",
       "Both are true and the reason explains the assertion: a very large value pulls the total, and "
       "so the mean, upward, but it only shifts one position in the ordered list, which barely moves "
       "the median. This is why the median is preferred for data such as house prices or incomes."),

    ar("m-prob", "m-prob.basic",
       "The probability of any event lies between 0 and 1, both values included.",
       "The number of outcomes favourable to an event cannot be negative and cannot be greater than the total number of possible outcomes.",
       "both_true_explains",
       "Both are true and the reason explains the assertion: dividing a count by the total gives 0 "
       "when there are no favourable outcomes, 1 when all of them are favourable, and something in "
       "between otherwise."),

    ar("m-prob", "m-prob.dice-coins",
       "The probability of getting a number greater than 6 on a single throw of an ordinary die is 0.",
       "An ordinary die has faces numbered 1 to 6, so there is no outcome greater than 6.",
       "both_true_explains",
       "Both are true and the reason explains the assertion: with no favourable outcome the "
       "probability is 0 divided by 6, which is 0. Such an event is called an impossible event."),

    ar("m-prob", "m-prob.basic",
       "The probability that a fair coin lands showing a head is one half.",
       "A fair coin has two equally likely outcomes, head and tail.",
       "both_true_explains",
       "Both are true and the reason explains the assertion: when outcomes are equally likely, the "
       "probability of an event is the number of favourable outcomes divided by the total, which here "
       "is 1 over 2."),
]


# ══════════════════════════════════════════════════════════════════════
# Case studies
# ══════════════════════════════════════════════════════════════════════

CASE_STUDIES = [
    case("m-real", "m-real.hcf-lcm",
         "Three bells in a school begin tolling together at 6:00 in the morning. After that, the "
         "first bell tolls every 8 minutes, the second every 12 minutes and the third every 18 "
         "minutes. A fourth bell, installed later, tolls every 24 minutes, and it was started at the "
         "same moment as the other three.\n\n"
         "The gardener wants to know when he will next hear all the bells at once, so that he can "
         "plan his watering round.",
         [
             {"prompt": "After how many minutes will all the bells toll together again?",
              "options": ["72 minutes", "38 minutes", "24 minutes", "48 minutes"],
              "answer": 0, "difficulty": "medium",
              "explanation": "The bells toll together at the least common multiple of the intervals. "
                             "8 is 2 cubed, 12 is 2 squared times 3, 18 is 2 times 3 squared, so the "
                             "LCM is 2 cubed times 3 squared, which is 72. 38 is the sum of the "
                             "intervals and 24 is only the largest of them."},

             {"prompt": "Counting the 6:00 toll, how many times do all four bells toll together in the next 12 hours?",
              "options": ["10 times", "11 times", "9 times", "12 times"],
              "answer": 0, "difficulty": "hard",
              "explanation": "Adding a bell every 24 minutes does not change the LCM, since 24 is "
                             "2 cubed times 3 and is already covered by 72. Twelve hours is 720 "
                             "minutes, and 720 divided by 72 is 10, so there are ten such moments "
                             "including the first."},

             {"prompt": "The HCF of 8, 12 and 18 is",
              "options": ["2", "1", "6", "4"],
              "answer": 0, "difficulty": "easy",
              "explanation": "The only prime dividing all three is 2, and it appears to the first "
                             "power in 18, so the HCF is 2. A common slip is to give the HCF of just "
                             "two of the numbers."},

             {"prompt": "For the two numbers 8 and 18, the product of the HCF and the LCM is",
              "options": ["144", "26", "72", "288"],
              "answer": 0, "difficulty": "medium",
              "explanation": "For two numbers, the HCF times the LCM equals the product of the "
                             "numbers. Here that product is 8 times 18, which is 144, and indeed the "
                             "HCF is 2, the LCM is 72, and 2 times 72 is 144. 288 doubles it, and 26 "
                             "is the sum of the numbers mistakenly combined with the LCM."},

             {"prompt": "The gardener claims that 8/6 written in lowest terms has a terminating decimal expansion. He is",
              "options": ["correct, because in lowest terms the denominator is 3",
                          "correct, because the denominator was 6",
                          "wrong, because the denominator is even",
                          "wrong, because the numerator is even"],
              "answer": 0, "difficulty": "hard",
              "explanation": "8/6 in lowest terms is 4/3, and the denominator 3 has a prime factor "
                             "other than 2 or 5, so the expansion is non-terminating and recurring. "
                             "The claim is wrong, and the correct reason is that the reduced "
                             "denominator is 3, not the parity of either number."},
         ]),

    case("m-poly", "m-poly.zeroes",
         "A rectangular garden has a perimeter of 60 metres and an area of 200 square metres. Ravi "
         "writes the length as x metres and works out that x must satisfy\n\n"
         "x squared minus 30x plus 200 equals zero.\n\n"
         "His friend Meera points out that for a fixed perimeter, the area of a rectangle cannot be "
         "made as large as one likes.",
         [
             {"prompt": "The length and breadth of the garden are",
              "options": ["20 m and 10 m", "25 m and 5 m", "30 m and 0 m", "15 m and 15 m"],
              "answer": 0, "difficulty": "easy",
              "explanation": "The two numbers must add to 30 and multiply to 200, and 20 and 10 do "
                             "both. 25 and 5 add to 30 but multiply to only 125, and 15 and 15 would "
                             "give an area of 225."},

             {"prompt": "The discriminant of x squared minus 30x plus 200 equals zero is",
              "options": ["100", "200", "-100", "900"],
              "answer": 0, "difficulty": "easy",
              "explanation": "The discriminant is b squared minus 4ac, so 30 squared minus 4 times 200 "
                             "equals 900 minus 800, which is 100. 900 is b squared alone and 800 is "
                             "4ac alone."},

             {"prompt": "The larger possible area for a rectangle with a perimeter of 60 metres is",
              "options": ["225 square metres", "200 square metres", "900 square metres", "300 square metres"],
              "answer": 0, "difficulty": "medium",
              "explanation": "Writing the sides as 15 plus t and 15 minus t, the area is 225 minus t "
                             "squared, which is greatest when t is 0. So the square of side 15 gives "
                             "the largest area, 225 square metres. Any other rectangle with this "
                             "perimeter has a smaller area."},

             {"prompt": "The equation x squared minus 30x plus 225 equals zero has",
              "options": ["two equal real roots", "two distinct real roots",
                          "no real roots", "exactly one root of zero"],
              "answer": 0, "difficulty": "medium",
              "explanation": "Its discriminant is 900 minus 900, which is 0, and a zero discriminant "
                             "gives two equal roots. Here that repeated root is 15, which matches the "
                             "square of side 15 found above."},

             {"prompt": "For which of these areas would there be no rectangle with this perimeter?",
              "options": ["240 square metres", "225 square metres", "200 square metres", "100 square metres"],
              "answer": 0, "difficulty": "hard",
              "explanation": "The equation x squared minus 30x plus A equals zero has a negative "
                             "discriminant when 900 minus 4A is negative, that is when A exceeds 225. "
                             "So no rectangle with a perimeter of 60 m can enclose 240 square "
                             "metres, which agrees with 225 being the largest possible area."},
         ]),

    case("m-quad", "m-quad.discriminant",
         "A rectangular hall is to be built with a perimeter of 60 metres and a floor area of A "
         "square metres. The architect writes the sides as 15 plus t and 15 minus t metres, where t "
         "is a positive number, and finds that the area is 225 minus t squared.",
         [
             {"prompt": "As t increases from 0, the area of the hall",
              "options": ["Decreases from 225 square metres",
                          "Increases without limit",
                          "Stays the same at 225 square metres",
                          "Increases at first and then decreases"],
              "answer": 0, "difficulty": "medium",
              "explanation": "The area is 225 minus t squared, so subtracting more as t grows makes it "
                             "smaller. It is largest at t equals 0, and at t equals 15 one side would "
                             "collapse to zero."},

             {"prompt": "The largest area the architect can achieve is",
              "options": ["225 square metres", "900 square metres", "60 square metres", "450 square metres"],
              "answer": 0, "difficulty": "easy",
              "explanation": "The area 225 minus t squared is greatest when t is 0, giving 225 square "
                             "metres. The hall would then be a square of side 15 metres."},

             {"prompt": "If the architect wants an area of 216 square metres, the value of t is",
              "options": ["3", "9", "6", "12"],
              "answer": 0, "difficulty": "medium",
              "explanation": "225 minus t squared equals 216, so t squared is 9 and t is 3. The sides "
                             "are then 18 metres and 12 metres, whose product is 216."},

             {"prompt": "If the architect wants an area of 250 square metres, then",
              "options": ["It is impossible, since the largest possible area is 225 square metres",
                          "t is 5 and the sides are 20 m and 10 m",
                          "t is 25 and the sides are 40 m and 10 m",
                          "It is possible but only for a non-rectangular hall"],
              "answer": 0, "difficulty": "medium",
              "explanation": "250 exceeds the maximum of 225, so no rectangle with a perimeter of 60 "
                             "metres can have that floor area. Trying to solve 225 minus t squared "
                             "equals 250 would need t squared to be negative, which is impossible."},

             {"prompt": "The equation that gives the sides for an area of 216 square metres is",
              "options": ["x squared minus 30x plus 216 equals zero",
                          "x squared plus 30x plus 216 equals zero",
                          "x squared minus 216x plus 30 equals zero",
                          "x squared minus 30x minus 216 equals zero"],
              "answer": 0, "difficulty": "hard",
              "explanation": "The two sides add to 30 and multiply to 216, so they are the roots of "
                             "x squared minus the sum times x plus the product, that is x squared "
                             "minus 30x plus 216 equals zero. Its roots are 18 and 12."},
         ]),

    case("m-linear", "m-linear.elimination",
         "A stationery shop sells two kinds of pen. One kind costs 10 rupees and the other costs 15 "
         "rupees. In one day the shop sells 25 pens in all and takes 320 rupees.\n\n"
         "The owner writes x for the number of cheaper pens sold and y for the number of dearer ones.",
         [
             {"prompt": "The pair of equations describing the day's sales is",
              "options": ["x plus y equals 25 and 10x plus 15y equals 320",
                          "x plus y equals 320 and 10x plus 15y equals 25",
                          "x plus y equals 25 and 15x plus 10y equals 320",
                          "x minus y equals 25 and 10x plus 15y equals 320"],
              "answer": 0, "difficulty": "easy",
              "explanation": "The first equation counts the pens and the second values them. The "
                             "third option swaps the prices, which would make the cheaper pen cost 15 "
                             "rupees, and the fourth replaces the count with a difference."},

             {"prompt": "The number of pens sold at 15 rupees each was",
              "options": ["14", "11", "15", "12"],
              "answer": 0, "difficulty": "medium",
              "explanation": "Substituting x equals 25 minus y into the second equation gives 250 plus "
                             "5y equals 320, so 5y is 70 and y is 14. Then x is 11."},

             {"prompt": "The number of pens sold at 10 rupees each was",
              "options": ["11", "14", "10", "13"],
              "answer": 0, "difficulty": "easy",
              "explanation": "Since the total is 25 pens and 14 were the dearer kind, 11 were the "
                             "cheaper kind. Checking the money, 11 times 10 plus 14 times 15 is 110 "
                             "plus 210, which is 320."},

             {"prompt": "If all 25 pens had been the dearer kind, the day's takings would have exceeded the actual figure by",
              "options": ["55 rupees", "70 rupees", "35 rupees", "25 rupees"],
              "answer": 0, "difficulty": "hard",
              "explanation": "Twenty-five pens at 15 rupees would bring 375 rupees against the actual "
                             "320, so the excess is 55. Dividing 55 by the 5 rupee difference in "
                             "price recovers the 11 cheaper pens, which is a quick check of the answer."},

             {"prompt": "The two lines represented by these equations",
              "options": ["Intersect at exactly one point, so the pair is consistent",
                          "Are parallel, so the pair has no solution",
                          "Coincide, so the pair has infinitely many solutions",
                          "Intersect at two points, so the pair has two solutions"],
              "answer": 0, "difficulty": "medium",
              "explanation": "The ratio of the coefficients of x, 1 to 10, differs from the ratio of "
                             "the coefficients of y, 1 to 15, so the lines are not parallel and cannot "
                             "coincide. Two straight lines that are not parallel meet at exactly one "
                             "point, which is the solution 11 and 14."},
         ]),

    case("m-ap", "m-ap.sum",
         "Rita decides to save money every week. She puts aside 100 rupees in the first week, and "
         "each week after that she saves 25 rupees more than she did the week before, so her weekly "
         "savings form an arithmetic progression.\n\n"
         "Her brother decides to save a fixed 250 rupees every week instead.",
         [
             {"prompt": "Rita's saving in the tenth week is",
              "options": ["325 rupees", "350 rupees", "300 rupees", "225 rupees"],
              "answer": 0, "difficulty": "easy",
              "explanation": "The tenth term is 100 plus 9 times 25, which is 100 plus 225, giving "
                             "325. Using 10 times 25 instead of 9 times 25 gives 350, a common slip."},

             {"prompt": "In which week does Rita's weekly saving first reach 500 rupees?",
              "options": ["The 17th week", "The 16th week", "The 20th week", "The 21st week"],
              "answer": 0, "difficulty": "medium",
              "explanation": "100 plus n minus 1 times 25 equals 500 gives n minus 1 equal to 16, so n "
                             "is 17. The 16th week gives only 475 rupees."},

             {"prompt": "Rita's total saving over the first 12 weeks is",
              "options": ["2,850 rupees", "3,000 rupees", "2,700 rupees", "3,300 rupees"],
              "answer": 0, "difficulty": "medium",
              "explanation": "The sum of the first 12 terms is 12 by 2 times the quantity 200 plus 11 "
                             "times 25, which is 6 times 475, giving 2,850. Using 12 times 25 inside "
                             "the bracket instead of 11 times 25 overstates the total."},

             {"prompt": "After 20 weeks, Rita has saved",
              "options": ["6,750 rupees", "7,000 rupees", "6,000 rupees", "5,000 rupees"],
              "answer": 0, "difficulty": "medium",
              "explanation": "The sum of the first 20 terms is 10 times the quantity 200 plus 19 times "
                             "25, which is 10 times 675, giving 6,750 rupees."},

             {"prompt": "By the end of the 20th week, Rita has saved more than her brother by",
              "options": ["1,750 rupees", "1,000 rupees", "2,000 rupees", "750 rupees"],
              "answer": 0, "difficulty": "hard",
              "explanation": "Her brother has saved 250 times 20, which is 5,000 rupees. Rita has "
                             "6,750, so the difference is 1,750. Her weekly amount overtakes his only "
                             "in the seventh week, after which she pulls steadily ahead."},
         ]),

    case("m-tri", "m-tri.bpt",
         "In a triangular park, a straight path DE is laid parallel to the side BC, with D on AB and "
         "E on AC. A surveyor measures AD as 4 metres, DB as 6 metres and AE as 5 metres, and is "
         "asked to work out the remaining distances.\n\n"
         "He also measures the area of the small triangle ADE as 16 square metres.",
         [
             {"prompt": "The length of EC is",
              "options": ["7.5 metres", "6 metres", "8 metres", "5 metres"],
              "answer": 0, "difficulty": "medium",
              "explanation": "The parallel line divides AB and AC in the same ratio, so AD over DB "
                             "equals AE over EC. That gives 4 over 6 equals 5 over EC, so EC is 7.5 "
                             "metres."},

             {"prompt": "The length of AC is",
              "options": ["12.5 metres", "13 metres", "11.5 metres", "15 metres"],
              "answer": 0, "difficulty": "easy",
              "explanation": "AC is AE plus EC, which is 5 plus 7.5, giving 12.5 metres."},

             {"prompt": "The ratio AD to AB is",
              "options": ["2 to 5", "4 to 6", "5 to 12.5", "2 to 3"],
              "answer": 0, "difficulty": "medium",
              "explanation": "AB is 4 plus 6, which is 10 metres, so AD over AB is 4 over 10, which "
                             "simplifies to 2 to 5. The ratio 4 to 6 is AD to DB, which is a different "
                             "ratio; the ratio 5 to 12.5 simplifies to the same 2 to 5, and 2 to 3 is "
                             "AD to DB in lowest terms, also a different ratio."},

             {"prompt": "The area of triangle ABC is",
              "options": ["100 square metres", "40 square metres", "64 square metres", "80 square metres"],
              "answer": 0, "difficulty": "hard",
              "explanation": "Since DE is parallel to BC, triangles ADE and ABC are similar with "
                             "ratio of sides 2 to 5. Areas of similar triangles are in the ratio of "
                             "the squares of the sides, that is 4 to 25, so 16 over the area of ABC "
                             "equals 4 over 25, giving 100 square metres."},

             {"prompt": "The two triangles ADE and ABC are similar because",
              "options": ["Angle A is common and the angles at D and B are equal, since DE is parallel to BC",
                          "All three sides of ADE are equal to those of ABC",
                          "Both triangles are right-angled",
                          "The area of ADE is a fixed fraction of the area of ABC"],
              "answer": 0, "difficulty": "medium",
              "explanation": "The parallel line makes the angle at D equal to the angle at B and the "
                             "angle at E equal to the angle at C, since they are corresponding "
                             "angles. With the shared angle A, the triangles are similar by the AA "
                             "criterion; the sides are proportional, not equal."},
         ]),

    case("m-heights", "m-heights.elevation",
         "A vertical tower stands on level ground. A student stands at various distances from the "
         "foot of the tower and measures the angle of elevation of its top. The height of the tower "
         "is 30 metres, and the student's instrument is at ground level.\n\n"
         "She records what she sees at three positions, and then walks steadily towards the tower.",
         [
             {"prompt": "Standing 30 metres from the foot, the angle of elevation of the top is",
              "options": ["45 degrees", "30 degrees", "60 degrees", "90 degrees"],
              "answer": 0, "difficulty": "easy",
              "explanation": "The tangent of the angle is the height over the distance, that is 30 "
                             "over 30, which is 1. The angle whose tangent is 1 is 45 degrees."},

             {"prompt": "Standing 30 times the square root of 3 metres from the foot, the angle of elevation is",
              "options": ["30 degrees", "45 degrees", "60 degrees", "15 degrees"],
              "answer": 0, "difficulty": "medium",
              "explanation": "The tangent is 30 divided by 30 root 3, which is 1 over root 3. The "
                             "angle whose tangent is 1 over root 3 is 30 degrees."},

             {"prompt": "From how far must the student stand for the angle of elevation to be 60 degrees?",
              "options": ["10 times the square root of 3 metres",
                          "30 times the square root of 3 metres",
                          "15 metres", "30 metres"],
              "answer": 0, "difficulty": "medium",
              "explanation": "The tangent of 60 degrees is root 3, so 30 over the distance equals root "
                             "3, giving a distance of 30 over root 3, which simplifies to 10 root 3 "
                             "metres, about 17.3 metres."},

             {"prompt": "The distance needed for an elevation of 30 degrees is how many times the distance needed for 60 degrees?",
              "options": ["3 times", "2 times", "Root 3 times", "6 times"],
              "answer": 0, "difficulty": "hard",
              "explanation": "The two distances are 30 root 3 and 10 root 3 metres, and their ratio is "
                             "3. Cutting the distance to a third triples the tangent and so takes the "
                             "angle from 30 to 60 degrees."},

             {"prompt": "As the student walks steadily towards the tower, the angle of elevation of the top",
              "options": ["Increases, and would approach 90 degrees as she reached the foot",
                          "Decreases, because she sees the top at a sharper angle",
                          "Stays the same, since the tower does not change height",
                          "Increases, and would reach 90 degrees at the halfway point"],
              "answer": 0, "difficulty": "medium",
              "explanation": "For a fixed height, the tangent of the angle is the height divided by "
                             "the distance, so the angle grows as the distance shrinks. As the "
                             "distance approaches zero the angle approaches 90 degrees, though it "
                             "never quite reaches it."},
         ]),

    case("m-coord", "m-coord.distance",
         "A square park is drawn on a coordinate map of a town, in which each unit stands for 10 "
         "metres. The four corners of the park are at A(1,2), B(5,6), C(9,2) and D(5,-2).\n\n"
         "The town council wants to put a gate at the midpoint of each side and a fountain at the "
         "centre of the park.",
         [
             {"prompt": "The length of the side AB is",
              "options": ["4 times the square root of 2 units, about 5.66 units",
                          "4 units", "8 units", "6 units"],
              "answer": 0, "difficulty": "medium",
              "explanation": "The distance formula gives the square root of the quantity 5 minus 1 "
                             "squared plus 6 minus 2 squared, which is the square root of 16 plus 16, "
                             "or 4 root 2, about 5.66 units."},

             {"prompt": "The midpoint of the side AC is",
              "options": ["(5,2)", "(5,4)", "(4,2)", "(10,4)"],
              "answer": 0, "difficulty": "easy",
              "explanation": "The midpoint has coordinates averaging those of the two ends, so the x "
                             "coordinate is the average of 1 and 9, which is 5, and the y coordinate "
                             "is the average of 2 and 2, which is 2."},

             {"prompt": "The midpoint of the side AB is",
              "options": ["(3,4)", "(4,3)", "(2,3)", "(6,8)"],
              "answer": 0, "difficulty": "easy",
              "explanation": "Averaging A(1,2) and B(5,6) gives x equal to 3 and y equal to 4. The "
                             "point (6,8) is the sum of the coordinates rather than their average."},

             {"prompt": "The park ABCD is",
              "options": ["A square, since all four sides are equal and both diagonals are 8 units",
                          "A rectangle that is not a square",
                          "A rhombus that is not a square",
                          "A parallelogram that is neither a rhombus nor a rectangle"],
              "answer": 0, "difficulty": "hard",
              "explanation": "Each side works out to 4 root 2 units, so all four are equal. The "
                             "diagonals AC and BD are each 8 units, and a rhombus with equal "
                             "diagonals is a square. Its area is half the product of the diagonals, "
                             "which is 32 square units."},

             {"prompt": "The area of the park in square metres is",
              "options": ["3,200 square metres", "32 square metres",
                          "320 square metres", "1,600 square metres"],
              "answer": 0, "difficulty": "hard",
              "explanation": "One unit stands for 10 metres, so one square unit stands for 100 square "
                             "metres. The area in map units is half of 8 times 8, which is 32, so in "
                             "real terms it is 32 times 100, that is 3,200 square metres."},
         ]),

    case("m-circles", "m-circles.tangent-count",
         "A circular park has a radius of 5 metres and its centre is at O. A lamp post stands at a "
         "point P, 10 metres from O. Two straight paths are laid from P, each just touching the "
         "boundary of the park at a single point, A and B.\n\n"
         "The gardener wants to know the length of each path and the angle between them.",
         [
             {"prompt": "The angle between the radius OA and the path PA is",
              "options": ["90 degrees", "60 degrees", "45 degrees", "30 degrees"],
              "answer": 0, "difficulty": "easy",
              "explanation": "A tangent meets the radius at the point of contact at a right angle. "
                             "This is the theorem that makes the lengths calculable, since it turns "
                             "triangle OAP into a right triangle."},

             {"prompt": "The length of the path PA is",
              "options": ["5 times the square root of 3 metres, about 8.66 metres",
                          "5 metres", "15 metres", "10 metres"],
              "answer": 0, "difficulty": "medium",
              "explanation": "Triangle OAP is right-angled at A, so by Pythagoras PA squared is OP "
                             "squared minus OA squared, which is 100 minus 25, giving 75. So PA is 5 "
                             "root 3, about 8.66 metres."},

             {"prompt": "The angle APB between the two paths is",
              "options": ["60 degrees", "30 degrees", "90 degrees", "120 degrees"],
              "answer": 0, "difficulty": "hard",
              "explanation": "In triangle OAP, the sine of angle APO is 5 over 10, which is one half, "
                             "so that angle is 30 degrees. The two paths are symmetrically placed "
                             "about OP, so the full angle APB is twice 30, that is 60 degrees."},

             {"prompt": "The angle AOB at the centre is",
              "options": ["120 degrees", "60 degrees", "90 degrees", "180 degrees"],
              "answer": 0, "difficulty": "medium",
              "explanation": "The four angles of quadrilateral OAPB add to 360 degrees. The angles at "
                             "A and B are both 90 degrees and the angle at P is 60, so the angle at O "
                             "is 360 minus 240, which is 120 degrees."},

             {"prompt": "The area of the quadrilateral OAPB is",
              "options": ["25 times the square root of 3 square metres, about 43.3 square metres",
                          "50 square metres", "25 square metres", "100 square metres"],
              "answer": 0, "difficulty": "hard",
              "explanation": "The quadrilateral is made of two congruent right triangles. One has "
                             "area one half times 5 times 5 root 3, which is 25 root 3 over 2, so the "
                             "pair is 25 root 3, about 43.3 square metres."},
         ]),

    case("m-areas-circle", "m-areas-circle.sector",
         "A circular flower bed has a radius of 14 metres. The gardener marks out a quarter of it, "
         "sweeping an angle of 90 degrees at the centre, for roses, and plans to fence the curved "
         "edge of that quarter separately.\n\n"
         "He also intends to leave a small triangular lawn inside that quarter, formed by joining "
         "the centre to the two ends of the curved edge.",
         [
             {"prompt": "The area of the whole circular bed is",
              "options": ["616 square metres", "154 square metres",
                          "88 square metres", "308 square metres"],
              "answer": 0, "difficulty": "easy",
              "explanation": "The area is pi r squared, which with pi taken as 22 over 7 and r as 14 "
                             "gives 22 over 7 times 196, that is 616 square metres."},

             {"prompt": "The area of the quarter set aside for roses is",
              "options": ["154 square metres", "616 square metres", "308 square metres", "77 square metres"],
              "answer": 0, "difficulty": "easy",
              "explanation": "A 90 degree sector is a quarter of the circle, so its area is 616 "
                             "divided by 4, which is 154 square metres."},

             {"prompt": "The length of the curved edge of that quarter is",
              "options": ["22 metres", "44 metres", "88 metres", "11 metres"],
              "answer": 0, "difficulty": "medium",
              "explanation": "The arc length is a quarter of the circumference. The circumference is "
                             "2 times 22 over 7 times 14, which is 88 metres, and a quarter of that "
                             "is 22 metres."},

             {"prompt": "The area of the triangular lawn inside the quarter is",
              "options": ["98 square metres", "154 square metres", "49 square metres", "196 square metres"],
              "answer": 0, "difficulty": "medium",
              "explanation": "The triangle has the two radii as its equal sides, each 14 metres, and "
                             "they meet at a right angle. Its area is one half times 14 times 14, "
                             "which is 98 square metres."},

             {"prompt": "The area between the curved edge and the triangle, that is the circular segment, is",
              "options": ["56 square metres", "154 square metres", "98 square metres", "112 square metres"],
              "answer": 0, "difficulty": "hard",
              "explanation": "The segment is the sector minus the triangle, so 154 minus 98, which is "
                             "56 square metres. 154 is the sector alone and 98 the triangle alone."},
         ]),

    case("m-sav", "m-sav.combined",
         "A wooden toy is shaped like a cone sitting on top of a hemisphere, with the flat circular "
         "face of the hemisphere joined to the base of the cone. The radius of both the cone and the "
         "hemisphere is 3.5 cm, and the total height of the toy from the flat base to the tip is "
         "15.5 cm.\n\n"
         "A toy maker wants to know the surface area that must be painted and the volume of wood used.",
         [
             {"prompt": "The height of the cone alone is",
              "options": ["12 cm", "15.5 cm", "3.5 cm", "19 cm"],
              "answer": 0, "difficulty": "easy",
              "explanation": "The total height is the cone's height plus the hemisphere's radius, "
                             "since the hemisphere is 3.5 cm tall. So the cone is 15.5 minus 3.5, "
                             "which is 12 cm."},

             {"prompt": "The slant height of the cone is",
              "options": ["12.5 cm", "15.5 cm", "12 cm", "13.5 cm"],
              "answer": 0, "difficulty": "medium",
              "explanation": "The slant height is the square root of the sum of the squares of the "
                             "height and the radius, so the square root of 144 plus 12.25, which is "
                             "the square root of 156.25, giving 12.5 cm."},

             {"prompt": "The curved surface area of the cone, taking pi as 22 over 7, is",
              "options": ["137.5 square cm", "154 square cm",
                          "77 square cm", "214.5 square cm"],
              "answer": 0, "difficulty": "medium",
              "explanation": "The curved surface is pi times r times the slant height, which is 22 "
                             "over 7 times 3.5 times 12.5, giving 11 times 12.5, that is 137.5 square "
                             "cm. Forgetting to use the slant height instead of the height gives the "
                             "wrong figure."},

             {"prompt": "The total surface area to be painted is",
              "options": ["214.5 square cm", "137.5 square cm",
                          "292 square cm", "176 square cm"],
              "answer": 0, "difficulty": "hard",
              "explanation": "Only the curved surface of the hemisphere is painted, since the flat "
                             "face is joined to the cone. The hemisphere contributes 2 pi r squared, "
                             "which is 2 times 22 over 7 times 12.25, giving 77 square cm. Adding "
                             "137.5 gives 214.5 square cm."},

             {"prompt": "The volume of wood in the toy is closest to",
              "options": ["243.8 cubic cm", "154 cubic cm",
                          "89.8 cubic cm", "231 cubic cm"],
              "answer": 0, "difficulty": "hard",
              "explanation": "The cone holds one third times 22 over 7 times 12.25 times 12, which is "
                             "154 cubic cm. The hemisphere holds two thirds times 22 over 7 times "
                             "42.875, which is about 89.8 cubic cm. The total is about 243.8 cubic cm; "
                             "154 and 89.8 are the two parts separately."},
         ]),

    case("m-stats", "m-stats.median",
         "The marks out of 50 obtained by 30 students of a class are grouped into a frequency table.\n\n"
         "0 to 10: 3 students\n"
         "10 to 20: 5 students\n"
         "20 to 30: 8 students\n"
         "30 to 40: 9 students\n"
         "40 to 50: 5 students\n\n"
         "The teacher wants the mean, the median and the modal class of these marks.",
         [
             {"prompt": "The total number of students is",
              "options": ["30", "25", "50", "35"],
              "answer": 0, "difficulty": "easy",
              "explanation": "Adding the frequencies gives 3 plus 5 plus 8 plus 9 plus 5, which is "
                             "30. This total is needed before the median position can be found."},

             {"prompt": "The mean marks, using the midpoints of the classes, is about",
              "options": ["27.7", "25", "30", "32.3"],
              "answer": 0, "difficulty": "medium",
              "explanation": "Multiplying each midpoint by its frequency gives 15, 75, 200, 315 and "
                             "225, which total 830. Dividing by 30 gives about 27.7. Taking 25, the "
                             "middle of the whole range, ignores that more students scored highly."},

             {"prompt": "The modal class of these marks is",
              "options": ["30 to 40", "20 to 30", "40 to 50", "10 to 20"],
              "answer": 0, "difficulty": "easy",
              "explanation": "The modal class is the one with the highest frequency, and 9 is the "
                             "largest frequency, so the modal class is 30 to 40."},

             {"prompt": "The median marks are about",
              "options": ["28.75", "25", "27.67", "30"],
              "answer": 0, "difficulty": "hard",
              "explanation": "Half of 30 is 15, and the cumulative frequencies are 3, 8, 16, 25 and "
                             "30, so the median class is 20 to 30, whose cumulative frequency first "
                             "passes 15. The median is 20 plus 15 minus 8 over 8, all times 10, which "
                             "gives 20 plus 8.75, or 28.75. The 27.67 figure is the mean, not the "
                             "median."},

             {"prompt": "The mean and the median of these marks differ, and the reason is that",
              "options": ["The distribution is not perfectly symmetric, so the mean is pulled towards the students who scored higher",
                          "The median was calculated wrongly",
                          "The mean and the median of grouped data can never be equal",
                          "The modal class is above the median class"],
              "answer": 0, "difficulty": "hard",
              "explanation": "The mean takes account of the size of every mark and the median only of "
                             "position, so they agree exactly only for a symmetric distribution. "
                             "Here the heavier frequencies lie at the upper end, which pulls the "
                             "mean slightly below the median."},
         ]),

    case("m-prob", "m-prob.dice-coins",
         "A board game is played with two ordinary dice, each numbered 1 to 6. A player rolls both "
         "dice at once and adds the two numbers showing. The game has 36 equally likely outcomes in "
         "all, since each of the six faces of the first die can be paired with each of the six faces "
         "of the second.\n\n"
         "The rules of the game depend on the total shown.",
         [
             {"prompt": "The probability that the total is 7 is",
              "options": ["One sixth", "One twelfth", "One thirty-sixth", "One ninth"],
              "answer": 0, "difficulty": "medium",
              "explanation": "Six outcomes give a total of 7: 1 and 6, 6 and 1, 2 and 5, 5 and 2, 3 "
                             "and 4, 4 and 3. So the probability is 6 over 36, which is one sixth, the "
                             "highest of any total."},

             {"prompt": "The probability that the total is 12 is",
              "options": ["One thirty-sixth", "One sixth", "One eighteenth", "One twelfth"],
              "answer": 0, "difficulty": "easy",
              "explanation": "Only one outcome gives 12, namely a 6 on each die. So the probability is "
                             "1 over 36, the lowest of any total except 1, which is impossible."},

             {"prompt": "The probability that both dice show the same number is",
              "options": ["One sixth", "One third", "One twelfth", "One thirty-sixth"],
              "answer": 0, "difficulty": "medium",
              "explanation": "The six outcomes 1 and 1, 2 and 2, and so on, all show the same number, "
                             "so the probability is 6 over 36, which is one sixth."},

             {"prompt": "The probability that the total is a prime number is",
              "options": ["Five twelfths", "One half", "One third", "One sixth"],
              "answer": 0, "difficulty": "hard",
              "explanation": "The primes possible are 2, 3, 5, 7 and 11, and their counts are 1, 2, 4, "
                             "6 and 2, adding to 15. So the probability is 15 over 36, which "
                             "simplifies to five twelfths. Note that 1 is not prime and 9 is not "
                             "prime, which are the two errors that shift this answer."},

             {"prompt": "The probability that the total is less than or equal to 4 is",
              "options": ["One sixth", "One ninth", "One twelfth", "One third"],
              "answer": 0, "difficulty": "hard",
              "explanation": "Totals of 2, 3 and 4 occur 1, 2 and 3 times, adding to 6 outcomes. So "
                             "the probability is 6 over 36, which is one sixth."},
         ]),
]


# ══════════════════════════════════════════════════════════════════════
# Application and analytical items
# ══════════════════════════════════════════════════════════════════════

APPLICATION = [
    app("m-real", "m-real.hcf-lcm",
        "The decimal expansion of 13/3125 is",
        ["Terminating, because 3125 is 5 raised to the power 5",
         "Non-terminating and recurring, because the numerator is odd",
         "Terminating, because 13 is a prime number",
         "Non-terminating, because 3125 is not a power of 2"],
        0,
        "A rational number in lowest terms has a terminating decimal expansion exactly when its "
        "denominator has no prime factor other than 2 and 5. Here 3125 is 5 to the power 5, and 13 "
        "and 3125 share no factor, so the expansion terminates.",
        difficulty="medium"),

    app("m-real", "m-real.hcf-lcm",
        "The HCF of 96 and 404, found by Euclid's division algorithm, is",
        ["4", "2", "8", "12"],
        0,
        "404 divided by 96 leaves 20, 96 divided by 20 leaves 16, 20 divided by 16 leaves 4, and 16 "
        "divided by 4 leaves 0. The last non-zero remainder is 4, so the HCF is 4.",
        difficulty="hard"),

    app("m-real", "m-real.irrational",
        "Which of the following is an irrational number?",
        ["The square root of 7", "The square root of 16",
         "7/9 written as a decimal", "0.125"],
        0,
        "The square root of 16 is 4, an integer. 7/9 is a recurring decimal and 0.125 terminates, so "
        "both are rational. The square root of 7 is not a perfect square of any rational number, so "
        "it cannot be written as a fraction of integers.",
        difficulty="easy"),

    app("m-poly", "m-poly.zeroes",
        "A quadratic polynomial has zeroes 2 and 3. The polynomial is",
        ["x squared minus 5x plus 6", "x squared plus 5x plus 6",
         "x squared minus 5x minus 6", "x squared minus 6x plus 5"],
        0,
        "A quadratic with zeroes a and b is x squared minus the sum times x plus the product. The sum "
        "is 5 and the product is 6, so the polynomial is x squared minus 5x plus 6.",
        difficulty="easy"),

    app("m-poly", "m-poly.coefficients",
        "If the sum of the zeroes of a quadratic polynomial is 3 and their product is 2, then the "
        "polynomial is",
        ["x squared minus 3x plus 2", "x squared plus 3x plus 2",
         "x squared minus 2x plus 3", "x squared minus 3x minus 2"],
        0,
        "The sum of the zeroes is the negative of the coefficient of x divided by the coefficient of "
        "x squared, and the product is the constant term divided by it. With the leading coefficient "
        "taken as 1, the coefficient of x is minus 3 and the constant is 2.",
        difficulty="medium"),

    app("m-quad", "m-quad.factorisation",
        "The roots of 2x squared minus 7x plus 3 equals zero are",
        ["3 and one half", "3 and 2", "one half and 2", "minus 3 and minus one half"],
        0,
        "Using the quadratic formula, the roots are 7 plus or minus the square root of 49 minus 24, "
        "all over 4. The square root of 25 is 5, so the roots are 12 over 4, which is 3, and 2 over 4, "
        "which is one half. Checking, their sum is 3.5, which is 7 over 2 as required.",
        difficulty="medium"),

    app("m-quad", "m-quad.discriminant",
        "For what value of k does kx squared minus 4x plus 1 equals zero have two equal roots?",
        ["4", "2", "-4", "0"],
        0,
        "Equal roots need a zero discriminant, so 16 minus 4k is 0 and k is 4. The equation then "
        "becomes 4x squared minus 4x plus 1 equals zero, which is 2x minus 1 all squared, giving the "
        "repeated root one half.",
        difficulty="hard"),

    app("m-quad", "m-quad.discriminant",
        "The nature of the roots of x squared plus x plus 1 equals zero is that they are",
        ["Not real, because the discriminant is minus 3",
         "Real and equal, because the discriminant is 0",
         "Real and distinct, because the discriminant is positive",
         "Real and equal to 1"],
        0,
        "The discriminant is 1 minus 4, which is minus 3. A negative discriminant means the square "
        "root involved is not real, so the equation has no real roots, and its graph lies entirely "
        "above the x-axis.",
        difficulty="medium"),

    app("m-linear", "m-linear.substitution",
        "Solving x plus y equals 10 and x minus y equals 2 together gives",
        ["x equals 6 and y equals 4", "x equals 4 and y equals 6",
         "x equals 8 and y equals 2", "x equals 5 and y equals 5"],
        0,
        "Adding the two equations eliminates y and gives 2x equals 12, so x is 6. Substituting back, "
        "y is 4. The pair 4 and 6 satisfies the second equation in reverse and does not satisfy the "
        "first.",
        difficulty="easy"),

    app("m-linear", "m-linear.consistency",
        "The pair of equations 3x minus y equals 5 and 6x minus 2y equals 10 has",
        ["Infinitely many solutions, because the lines coincide",
         "Exactly one solution, because the lines meet at one point",
         "No solution, because the lines are parallel",
         "Exactly two solutions"],
        0,
        "The second equation is the first multiplied by 2, so both describe the same line. A pair of "
        "coincident lines has infinitely many common points, and the pair is called dependent as well "
        "as consistent.",
        difficulty="medium"),

    app("m-ap", "m-ap.nth-term",
        "The tenth term of the arithmetic progression 3, 7, 11, and so on, is",
        ["39", "43", "36", "40"],
        0,
        "The first term is 3 and the common difference is 4, so the tenth term is 3 plus 9 times 4, "
        "which is 39. Using 10 instead of 9 gives 43, a common slip.",
        difficulty="easy"),

    app("m-ap", "m-ap.sum",
        "The sum of the first 20 natural numbers is",
        ["210", "190", "200", "220"],
        0,
        "This is an arithmetic progression with first term 1 and common difference 1. The sum is 20 "
        "by 2 times the quantity 2 plus 19, which is 10 times 21, giving 210.",
        difficulty="easy"),

    app("m-ap", "m-ap.nth-term",
        "Which term of the arithmetic progression 5, 8, 11, and so on, is 50?",
        ["The 16th term", "The 15th term", "The 17th term", "The 10th term"],
        0,
        "Setting the nth term equal to 50 gives 5 plus n minus 1 times 3 equals 50, so n minus 1 is "
        "15 and n is 16. The 15th term is 47 and the 17th is 53.",
        difficulty="medium"),

    app("m-tri", "m-tri.bpt",
        "In triangle ABC, the line DE is parallel to BC, with D on AB and E on AC. If AD is 2 cm, DB "
        "is 3 cm and AE is 4 cm, then AC is",
        ["10 cm", "6 cm", "8 cm", "9 cm"],
        0,
        "The parallel line divides the two sides in the same ratio, so AD over DB equals AE over EC. "
        "That gives 2 over 3 equals 4 over EC, so EC is 6 cm. AC is AE plus EC, which is 10 cm.",
        difficulty="medium"),

    app("m-tri", "m-tri.similarity",
        "Two triangles are similar and their areas are in the ratio 9 to 16. The ratio of their "
        "corresponding sides is",
        ["3 to 4", "9 to 16", "81 to 256", "4 to 3"],
        0,
        "The areas of similar triangles are in the ratio of the squares of their corresponding sides. "
        "The square roots of 9 and 16 are 3 and 4, so the sides are in the ratio 3 to 4.",
        difficulty="medium"),

    app("m-coord", "m-coord.distance",
        "The distance between the points (3,4) and (0,0) is",
        ["5 units", "7 units", "12 units", "25 units"],
        0,
        "The distance is the square root of the sum of the squares of the differences of the "
        "coordinates, which is the square root of 9 plus 16, giving 5. Note that 25 is the square of "
        "the distance and not the distance itself.",
        difficulty="easy"),

    app("m-coord", "m-coord.section",
        "The point dividing the line segment joining (2,4) and (6,8) in the ratio 1 to 1 is",
        ["(4,6)", "(8,12)", "(2,4)", "(3,5)"],
        0,
        "A ratio of 1 to 1 means the midpoint. Averaging the coordinates gives x equal to 4 and y "
        "equal to 6. The point (8,12) is the sum of the coordinates rather than their average.",
        difficulty="easy"),

    app("m-trig", "m-trig.table",
        "The value of sin 30 degrees plus cos 60 degrees is",
        ["1", "0", "one half", "root 3 over 2"],
        0,
        "Both sin 30 and cos 60 are one half, so their sum is 1. This pair of values comes from the "
        "same triangle and is worth remembering together.",
        difficulty="easy"),

    app("m-trig", "m-trig.identities",
        "If sin theta is 3 over 5 and theta is acute, then cos theta is",
        ["4 over 5", "4 over 3", "5 over 4", "3 over 4"],
        0,
        "Using sin squared plus cos squared equals 1, cos squared is 1 minus 9 over 25, which is 16 "
        "over 25, so cos theta is 4 over 5. It is positive because theta is acute. The value 4 over 3 "
        "is tan theta, and 5 over 4 is cosec theta.",
        difficulty="medium"),

    app("m-trig", "m-trig.table",
        "The value of tan 45 degrees plus cot 45 degrees is",
        ["2", "1", "0", "root 2"],
        0,
        "Both tan 45 and cot 45 equal 1, since at 45 degrees the opposite and adjacent sides of the "
        "right triangle are equal. Their sum is therefore 2.",
        difficulty="easy"),

    app("m-heights", "m-heights.elevation",
        "A ladder 10 metres long leans against a vertical wall and makes an angle of 60 degrees with "
        "the ground. The height it reaches on the wall is",
        ["5 times the square root of 3 metres, about 8.7 metres",
         "5 metres", "10 metres", "10 times the square root of 3 metres"],
        0,
        "The ladder is the hypotenuse and the wall is the side opposite the angle, so the height is "
        "10 sin 60, which is 10 times root 3 over 2, giving 5 root 3, about 8.7 metres. Using cos 60 "
        "instead gives 5, which is the distance of the foot from the wall.",
        difficulty="medium"),

    app("m-heights", "m-heights.depression",
        "From the top of a cliff 60 metres high, the angle of depression of a boat on the water is 30 "
        "degrees. The distance of the boat from the foot of the cliff is",
        ["60 times the square root of 3 metres, about 104 metres",
         "30 metres", "60 metres", "20 times the square root of 3 metres"],
        0,
        "The angle of depression equals the angle of elevation of the cliff top from the boat. So the "
        "tangent of 30 degrees equals 60 over the distance, giving the distance as 60 over the "
        "tangent of 30, which is 60 root 3, about 104 metres.",
        difficulty="hard"),

    app("m-circles", "m-circles.tangent",
        "A tangent is drawn from a point 13 cm from the centre of a circle of radius 5 cm. The "
        "length of the tangent is",
        ["12 cm", "8 cm", "18 cm", "13 cm"],
        0,
        "The radius to the point of contact is perpendicular to the tangent, so the triangle is "
        "right-angled with the line to the centre as hypotenuse. The tangent length is the square "
        "root of 169 minus 25, which is the square root of 144, giving 12 cm.",
        difficulty="medium"),

    app("m-circles", "m-circles.tangent-count",
        "From a point outside a circle, how many tangents can be drawn to the circle?",
        ["Exactly two, and they are equal in length",
         "Exactly one", "Exactly three", "Infinitely many"],
        0,
        "For a point outside a circle there are exactly two tangents, one on either side of the line "
        "joining the point to the centre. They are equal in length because the two right triangles "
        "formed with the radii are congruent.",
        difficulty="easy"),

    app("m-areas-circle", "m-areas-circle.sector",
        "The area of a sector of angle 90 degrees in a circle of radius 7 cm, taking pi as 22 over 7, "
        "is",
        ["38.5 square cm", "154 square cm", "77 square cm", "49 square cm"],
        0,
        "The sector is a quarter of the circle, whose area is 22 over 7 times 49, which is 154 square "
        "cm. A quarter of that is 38.5 square cm.",
        difficulty="easy"),

    app("m-areas-circle", "m-areas-circle.arc",
        "The length of the arc of a sector of angle 90 degrees in a circle of radius 14 cm, taking pi "
        "as 22 over 7, is",
        ["22 cm", "44 cm", "88 cm", "11 cm"],
        0,
        "The circumference is 2 times 22 over 7 times 14, which is 88 cm. A quarter of that, since 90 "
        "degrees is a quarter of 360, is 22 cm.",
        difficulty="medium"),

    app("m-sav", "m-sav.cylinder",
        "The volume of a cylinder of radius 7 cm and height 10 cm, taking pi as 22 over 7, is",
        ["1,540 cubic cm", "440 cubic cm", "4,620 cubic cm", "154 cubic cm"],
        0,
        "The volume is pi r squared h, which is 22 over 7 times 49 times 10. The 7 and the 49 give 7, "
        "so the volume is 22 times 7 times 10, which is 1,540 cubic cm.",
        difficulty="medium"),

    app("m-sav", "m-sav.sphere",
        "The surface area of a sphere of radius 7 cm, taking pi as 22 over 7, is",
        ["616 square cm", "154 square cm", "1,232 square cm", "308 square cm"],
        0,
        "The surface area of a sphere is 4 pi r squared, which is 4 times 22 over 7 times 49, giving "
        "4 times 154, which is 616 square cm. The figure 154 is the area of a great circle, not of "
        "the whole surface.",
        difficulty="medium"),

    app("m-sav", "m-sav.cone",
        "A cone has a base radius of 3 cm and a height of 4 cm. Its volume, taking pi as 22 over 7, "
        "is about",
        ["37.7 cubic cm", "113.1 cubic cm", "12 cubic cm", "25.1 cubic cm"],
        0,
        "The volume is one third pi r squared h, which is one third times 22 over 7 times 9 times 4. "
        "That is one third of about 113.1, giving about 37.7 cubic cm. Forgetting the one third gives "
        "the volume of the cylinder instead.",
        difficulty="hard"),

    app("m-sav", "m-sav.hemisphere",
        "The curved surface area of a hemisphere of radius 7 cm, taking pi as 22 over 7, is",
        ["308 square cm", "616 square cm", "154 square cm", "462 square cm"],
        0,
        "The curved surface of a hemisphere is 2 pi r squared, which is half the surface of the "
        "sphere, so half of 616, giving 308 square cm. The total surface area including the flat "
        "circular face would be 462 square cm.",
        difficulty="medium"),

    app("m-stats", "m-stats.mean",
        "The mean of the observations 5, 8, 12, 15 and 10 is",
        ["10", "12", "8", "50"],
        0,
        "The sum of the observations is 50 and there are five of them, so the mean is 10. Reporting "
        "50 is the common slip of giving the total instead of dividing by the number of observations.",
        difficulty="easy"),

    app("m-stats", "m-stats.median",
        "The median of the observations 3, 5, 7, 9, 11 and 13 is",
        ["8", "7", "9", "10"],
        0,
        "There are six observations, an even number, so the median is the mean of the third and "
        "fourth when arranged in order. Those are 7 and 9, giving 8.",
        difficulty="medium"),

    app("m-stats", "m-stats.mode",
        "The mode of the observations 2, 3, 4, 4, 5, 4 and 6 is",
        ["4", "3", "5", "There is no mode"],
        0,
        "The mode is the observation that occurs most often. The value 4 occurs three times and no "
        "other value occurs more than once, so the mode is 4.",
        difficulty="easy"),

    app("m-prob", "m-prob.cards",
        "A card is drawn at random from a well-shuffled pack of 52 playing cards. The probability "
        "that it is a king is",
        ["One thirteenth", "One fourth", "One fifty-second", "One twenty-sixth"],
        0,
        "There are four kings in the pack, so the probability is 4 over 52, which simplifies to one "
        "thirteenth. One fourth is the probability of drawing a card of a particular suit.",
        difficulty="medium"),

    app("m-prob", "m-prob.dice-coins",
        "A fair coin is tossed twice. The probability of getting a head both times is",
        ["One fourth", "One half", "One third", "One eighth"],
        0,
        "The four equally likely outcomes are head head, head tail, tail head and tail tail, and only "
        "one of them is two heads. So the probability is 1 over 4. Adding the two separate "
        "probabilities of a half would give 1, which is impossible.",
        difficulty="easy"),

    app("m-prob", "m-prob.basic",
        "A fair die is thrown once. The probability of getting a prime number is",
        ["One half", "One third", "Two thirds", "One sixth"],
        0,
        "The primes among 1 to 6 are 2, 3 and 5, giving three favourable outcomes out of six. So the "
        "probability is 3 over 6, which is one half. Counting 1 as prime, a common error, would give "
        "two thirds.",
        difficulty="medium"),
]


def main() -> int:
    items = ASSERTION_REASON + CASE_STUDIES + APPLICATION
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(
        json.dumps(
            {
                "chapter": ASSERTION_REASON[0]["chapter"],
                "kind": "competency",
                "source_ref": SOURCE_REF,
                "generator_note": (
                    "Hand-authored competency items. Assertion-reason items carry a verdict and the "
                    "generator supplies CBSE's fixed four-option scaffold; each case study carries "
                    "its situation into every linked sub-question. Items name their own chapter and "
                    "topic."
                ),
                "items": items,
            },
            indent=1,
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )

    subs = sum(len(i["questions"]) for i in CASE_STUDIES)
    print(
        f"{OUT.relative_to(BACKEND)}: {len(items)} items -> "
        f"{len(ASSERTION_REASON)} assertion-reason, "
        f"{len(CASE_STUDIES)} situations with {subs} sub-questions, "
        f"{len(APPLICATION)} application items = "
        f"{len(ASSERTION_REASON) + subs + len(APPLICATION)} questions"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
