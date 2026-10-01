"""Write the competency-based Science items.

Usage:  python3 scripts/author_science_competency.py
Writes: content/competency/science.json

CBSE's 2025-26 design puts roughly half the paper on competency-based items, and
every question the bank had was generated from a fact table. Fact tables are good
at recall - "what is the focal length", "which metal displaces which" - but they
cannot ask a student to reason about why, or to read a table of observations and
draw a conclusion from it. That judgement lives in the item itself, so these are
authored directly and handed to the competency generator, which supplies the
fixed assertion-reason scaffold, carries each passage into its sub-questions and
validates the option sets.

Three shapes are used:

  assertion_reason  An assertion and a reason, with CBSE's standard four verdicts.
                    Items pick a verdict rather than retyping the four options, so
                    the scaffold cannot drift between items. Roughly a third are
                    deliberately not "both true and R explains A" - a bank of only
                    that verdict trains a student to click the first option.

  case_study        A short passage or a table of observations, with four or five
                    sub-questions that each carry the passage, because the student
                    must see it on the same screen.

  application       A single question set in a real situation - a bulb rating, a
                    water-hardness problem, a prescription - where the answer needs
                    a step of calculation or a decision rather than a memory.

Nothing here is copied from a textbook or a question bank. The situations are
ordinary ones from the syllabus and the numbers are chosen so the arithmetic is
clean: 60 W at 220 V, 4 ohm resistors in parallel, 10,000 J at the producer level,
787 tall against 277 dwarf.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))

OUT = BACKEND / "content" / "competency" / "science.json"

SOURCE_REF = (
    "Original competency-based items written for the CBSE/NCERT Class 10 Science "
    "(2025-26) syllabus. Passages, data tables and situations are composed here; "
    "no question is reproduced from a textbook, guide or question bank."
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
         competency: str = "analysis", case_sensitive: bool = False) -> dict:
    """One passage with its sub-questions."""
    for q in questions:
        q.setdefault("chapter", chapter)
        q.setdefault("topic", topic)
        q.setdefault("competency", competency)
    return {"kind": "case_study", "chapter": chapter, "topic": topic,
            "stem": stem, "questions": questions,
            **({"case_sensitive": True} if case_sensitive else {})}


def app(chapter: str, topic: str, prompt: str, options: list[str], answer: int,
        explanation: str, difficulty: str = "medium",
        competency: str = "application", stem: str = "") -> dict:
    """One application or analytical item, with its own four options."""
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
        **({"stem": stem} if stem else {}),
    }


# ══════════════════════════════════════════════════════════════════════
# Assertion and Reason
# ══════════════════════════════════════════════════════════════════════

ASSERTION_REASON = [
    # ── Light: Reflection and Refraction ─────────────────────────────
    ar("sci-phy-light", "sci-phy-light.mirrors",
       "A convex mirror is preferred over a plane mirror as a rear-view mirror in vehicles.",
       "A convex mirror always forms an erect and diminished image, and it covers a wider field of view.",
       "both_true_explains",
       "Both statements are true and the reason fully explains the assertion: the erect image can be "
       "read at a glance and the wider field lets the driver see more of the traffic behind."),

    ar("sci-phy-light", "sci-phy-light.mirrors",
       "A large concave mirror is used to build a solar furnace.",
       "A concave mirror diverges the rays of light falling on it.",
       "a_true_r_false",
       "The assertion is true but the reason is false. A concave mirror is converging, not diverging; "
       "it brings the sun's parallel rays together at one point, which is exactly why it produces heat."),

    ar("sci-phy-light", "sci-phy-light.refraction",
       "A pencil partly dipped in water appears bent at the water surface.",
       "Light changes its path when it passes from one medium into another of different optical density.",
       "both_true_explains",
       "Both are true and the reason explains the assertion: the rays from the part under water bend "
       "on leaving it, so that part appears to be at a different position from the part above."),

    ar("sci-phy-light", "sci-phy-light.refraction",
       "The refractive index of diamond is very high, about 2.42.",
       "The speed of light in diamond is very much lower than its speed in vacuum.",
       "both_true_explains",
       "Refractive index is the ratio of the speed of light in vacuum to its speed in the medium, so a "
       "high index and a low speed inside the medium are the same statement made twice."),

    ar("sci-phy-light", "sci-phy-light.refraction",
       "A ray of light travelling from water into air bends towards the normal.",
       "The speed of light increases as the ray leaves water and enters air.",
       "a_false_r_true",
       "The reason is true - light travels faster in air than in water - but the assertion is false. "
       "Going from a denser to a rarer medium, the ray bends away from the normal."),

    # ── The Human Eye ────────────────────────────────────────────────
    ar("sci-phy-eye", "sci-phy-eye.defects",
       "A person with myopia cannot see distant objects clearly.",
       "In myopia the image of a distant object is formed behind the retina.",
       "a_true_r_false",
       "The assertion is true but the reason describes hypermetropia. In myopia the image is formed in "
       "front of the retina, which is why a concave lens, spreading the rays out first, corrects it."),

    ar("sci-phy-eye", "sci-phy-eye.defects",
       "Hypermetropia can be corrected by using a convex lens of suitable power.",
       "A convex lens converges the rays so that the image is formed on the retina rather than behind it.",
       "both_true_explains",
       "Both are true and the reason explains the assertion: the extra convergence brings the image "
       "forward onto the retina."),

    ar("sci-phy-eye", "sci-phy-eye.phenomena",
       "Stars appear to twinkle, while planets generally do not.",
       "Atmospheric refraction makes the apparent position of a star fluctuate slightly from moment to moment.",
       "both_true_explains",
       "Both are true and the reason explains the assertion. A planet is much closer and acts as an "
       "extended source, so the fluctuations from its many points average out."),

    ar("sci-phy-eye", "sci-phy-eye.dispersion",
       "Danger signals installed on tall buildings are red in colour.",
       "Red light is scattered the most by smoke or fog.",
       "a_true_r_false",
       "The assertion is true but the reason is the opposite of the truth. Red has the longest "
       "wavelength in the visible range and is scattered the least, so it travels farthest through "
       "smoke or fog and stays visible."),

    ar("sci-phy-eye", "sci-phy-eye.dispersion",
       "The sky appears blue during the day.",
       "Air particles scatter light of shorter wavelength more strongly than light of longer wavelength.",
       "both_true_explains",
       "Both are true and the reason explains the assertion: blue and violet are scattered most, and "
       "our eyes are more sensitive to blue, so the scattered light reaching us looks blue."),

    ar("sci-phy-eye", "sci-phy-eye.parts",
       "The ciliary muscles of the eye change the focal length of the eye lens.",
       "The ciliary muscles change the size of the pupil.",
       "a_true_r_false",
       "The assertion is true but the reason describes a different part. The iris controls the size of "
       "the pupil; the ciliary muscles change the curvature, and so the focal length, of the lens."),

    # ── Electricity ──────────────────────────────────────────────────
    ar("sci-phy-electricity", "sci-phy-electricity.combinations",
       "Resistors connected in series carry the same current.",
       "In a series circuit there is only one path along which the current can flow.",
       "both_true_explains",
       "Both are true and the reason explains the assertion: with no branching, charge cannot "
       "accumulate anywhere, so the same current passes through every resistor."),

    ar("sci-phy-electricity", "sci-phy-electricity.combinations",
       "The equivalent resistance of a parallel combination is less than the smallest resistance in it.",
       "In a parallel combination the same current flows through each of the resistors.",
       "a_true_r_false",
       "The assertion is true but the reason describes a series circuit. In parallel the potential "
       "difference is the same across each branch while the current divides, and adding a branch gives "
       "the current another path, which lowers the overall resistance."),

    ar("sci-phy-electricity", "sci-phy-electricity.ohms-law",
       "The heating element of an electric heater is made of an alloy such as nichrome rather than a pure metal.",
       "Nichrome has high resistivity and does not oxidise readily even at high temperature.",
       "both_true_explains",
       "Both are true and the reason explains the assertion: high resistivity produces more heat for a "
       "given length, and resistance to oxidation lets it glow red without burning away."),

    ar("sci-phy-electricity", "sci-phy-electricity.current",
       "A fuse wire is always connected in series with the appliance it protects.",
       "A fuse wire has a low melting point and melts when the current exceeds a safe value.",
       "both_true_explains",
       "Both are true and the reason explains the assertion: being in series means the whole circuit "
       "current passes through it, so when it melts the supply to the appliance is broken."),

    ar("sci-phy-electricity", "sci-phy-electricity.power",
       "Two bulbs rated 60 W and 100 W, both for 220 V, glow brighter when connected in parallel than when connected in series.",
       "In parallel each bulb gets the full 220 V, while in series that potential difference is shared between them.",
       "both_true_explains",
       "Both are true and the reason explains the assertion: a bulb's brightness depends on the power "
       "it actually dissipates, and that falls sharply when the voltage across it falls."),

    ar("sci-phy-electricity", "sci-phy-electricity.current",
       "The resistance of a wire doubles when its length is doubled, keeping the material and the area of cross-section the same.",
       "Resistance is inversely proportional to the length of the conductor.",
       "a_true_r_false",
       "The assertion is true but the reason states the wrong relationship. Resistance is directly "
       "proportional to length and inversely proportional to the area of cross-section."),

    # ── Magnetic Effects of Electric Current ─────────────────────────
    ar("sci-phy-magnetic", "sci-phy-magnetic.field",
       "Two magnetic field lines never intersect each other.",
       "If they did, a compass needle placed at the point of intersection would point in two directions at once.",
       "both_true_explains",
       "Both are true and the reason explains the assertion: at any point the field has one definite "
       "direction, so two lines crossing there would mean two directions for the same point."),

    ar("sci-phy-magnetic", "sci-phy-magnetic.rules",
       "The direction of the magnetic field produced around a straight current-carrying conductor is given by Fleming's left-hand rule.",
       "Fleming's left-hand rule gives the direction of the force on a current-carrying conductor placed in a magnetic field.",
       "a_false_r_true",
       "The reason is a correct statement, which is exactly why the assertion is false. The field "
       "around a straight conductor is given by the right-hand thumb rule; Fleming's left-hand rule is "
       "for the force, and his right-hand rule is for induced current."),

    ar("sci-phy-magnetic", "sci-phy-magnetic.motor",
       "An electric motor converts electrical energy into mechanical energy.",
       "An electric motor works on the principle of electromagnetic induction.",
       "a_true_r_false",
       "The assertion is true but the reason belongs to the generator. A motor works on the force "
       "experienced by a current-carrying conductor in a magnetic field; electromagnetic induction is "
       "what an electric generator uses."),

    ar("sci-phy-magnetic", "sci-phy-magnetic.field",
       "The core of an electromagnet is made of soft iron.",
       "Soft iron loses almost all of its magnetism as soon as the current is switched off.",
       "both_true_explains",
       "Both are true and the reason explains the assertion: an electromagnet must be a temporary "
       "magnet, so its core has to give up its magnetism the moment it is no longer needed."),

    ar("sci-phy-magnetic", "sci-phy-magnetic.domestic",
       "In domestic wiring, the earth wire is connected to a metal plate buried deep in the earth near the house.",
       "Earthing provides a low-resistance path for a leakage current, so that a person touching the appliance is not shocked.",
       "both_true_explains",
       "Both are true and the reason explains the assertion: the earth connection carries a leaking "
       "current safely away through the body of the appliance instead of through a person."),

    # ── Chemical Reactions and Equations ─────────────────────────────
    ar("sci-chem-ch1", "sci-chem-ch1.balancing",
       "Every chemical equation must be balanced.",
       "Mass can neither be created nor destroyed in a chemical reaction.",
       "both_true_explains",
       "Both are true and the reason explains the assertion: balancing makes the number of atoms of "
       "each element the same on both sides, which is what conservation of mass requires."),

    ar("sci-chem-ch1", "sci-chem-ch1.effects",
       "Respiration is considered an exothermic reaction.",
       "Energy is released when glucose combines with oxygen in the cells of the body.",
       "both_true_explains",
       "Both are true and the reason explains the assertion: the breakdown of glucose in the presence "
       "of oxygen gives out energy, and any reaction that gives out heat is exothermic."),

    ar("sci-chem-ch1", "sci-chem-ch1.observations",
       "Silver chloride turns grey when it is kept in sunlight.",
       "Sunlight decomposes silver chloride into silver metal and chlorine.",
       "both_true_explains",
       "Both are true and the reason explains the assertion: the grey colour is that of the finely "
       "divided silver metal left behind. This is why silver chloride is stored in dark bottles."),

    ar("sci-chem-ch1", "sci-chem-ch1.reaction-types",
       "The reaction between barium chloride and sodium sulphate is a double displacement reaction.",
       "In this reaction the two compounds exchange their ions to form a precipitate of barium sulphate.",
       "both_true_explains",
       "Both are true and the reason explains the assertion: Ba2+ and Na+ swap partners, and barium "
       "sulphate is insoluble, so it separates as a white precipitate."),

    ar("sci-chem-ch1", "sci-chem-ch1.redox",
       "When copper oxide is heated with hydrogen, copper oxide is said to be reduced.",
       "Copper oxide loses oxygen to hydrogen during the reaction.",
       "both_true_explains",
       "Both are true and the reason explains the assertion: losing oxygen is reduction, and the "
       "hydrogen that takes the oxygen away is itself oxidised."),

    # ── Acids, Bases and Salts ───────────────────────────────────────
    ar("sci-chem-ch2", "sci-chem-ch2.ph",
       "A solution of sodium chloride in water is neutral, while a solution of ammonium chloride is acidic.",
       "Sodium chloride is a salt of a strong acid and a strong base, whereas ammonium chloride is a salt of a strong acid and a weak base.",
       "both_true_explains",
       "Both are true and the reason explains the assertion: when the parent base is weak, the salt's "
       "solution is left with an excess of hydrogen ions and turns blue litmus red."),

    ar("sci-chem-ch2", "sci-chem-ch2.compounds",
       "Plaster of Paris must be stored in a moisture-proof container.",
       "Plaster of Paris absorbs water from the air and turns into gypsum, a hard solid mass.",
       "both_true_explains",
       "Both are true and the reason explains the assertion: adding water to the hemihydrate reverses "
       "the heating that made it, so it sets in the container and becomes useless."),

    ar("sci-chem-ch2", "sci-chem-ch2.acids",
       "Dry hydrochloric acid gas does not change the colour of dry litmus paper.",
       "Acids produce hydrogen ions only in the presence of water.",
       "both_true_explains",
       "Both are true and the reason explains the assertion: without water there are no free hydrogen "
       "ions, and it is the hydrogen ion that makes a substance acidic."),

    ar("sci-chem-ch2", "sci-chem-ch2.indicators",
       "Detergents are better cleansing agents than soaps when the water is hard.",
       "Detergents form insoluble precipitates with the calcium and magnesium ions in hard water.",
       "a_true_r_false",
       "The assertion is true but the reason states the behaviour of soap. Soap forms the insoluble "
       "scum; the calcium and magnesium salts of a detergent stay soluble, which is why a detergent "
       "still lathers."),

    ar("sci-chem-ch2", "sci-chem-ch2.acids",
       "Ethanol reacts with sodium metal to give hydrogen gas.",
       "Ethanol is a strong acid.",
       "a_true_r_false",
       "The assertion is true - sodium ethoxide and hydrogen are formed - but ethanol is not an acid "
       "at all in any useful sense; it is a neutral compound, which is why the reaction is far gentler "
       "than sodium's reaction with water."),

    # ── Metals and Non-metals ────────────────────────────────────────
    ar("sci-chem-ch3", "sci-chem-ch3.displacement",
       "Zinc displaces copper from a solution of copper sulphate.",
       "Zinc is more reactive than copper.",
       "both_true_explains",
       "Both are true and the reason explains the assertion: a more reactive metal can push a less "
       "reactive one out of its salt solution, which is how the reactivity series is confirmed."),

    ar("sci-chem-ch3", "sci-chem-ch3.displacement",
       "Copper displaces zinc from a solution of zinc sulphate.",
       "Copper is less reactive than zinc.",
       "a_false_r_true",
       "The reason is a correct statement, and it is precisely why the assertion is false. Because "
       "copper is the less reactive of the two, nothing happens when it is added to zinc sulphate."),

    ar("sci-chem-ch3", "sci-chem-ch3.ionic",
       "Ionic compounds have high melting and boiling points.",
       "A large amount of energy is needed to overcome the strong attraction between oppositely charged ions.",
       "both_true_explains",
       "Both are true and the reason explains the assertion: the electrostatic force between ions in a "
       "crystal is strong, so the crystal holds together until it is heated strongly."),

    ar("sci-chem-ch3", "sci-chem-ch3.properties",
       "Sodium and potassium are stored under kerosene.",
       "They react vigorously with the oxygen and moisture present in air.",
       "both_true_explains",
       "Both are true and the reason explains the assertion: left in the open they would catch fire, "
       "so kerosene keeps air and water away from them."),

    ar("sci-chem-ch3", "sci-chem-ch3.alloys",
       "Galvanisation protects iron from rusting even if the zinc layer is scratched.",
       "Zinc is less reactive than iron.",
       "a_true_r_false",
       "The assertion is true but the reason is backwards. Zinc is more reactive than iron, so it "
       "corrodes in place of the iron and keeps protecting it even where the coating is broken."),

    ar("sci-chem-ch3", "sci-chem-ch3.alloys",
       "Aluminium is widely used for making cooking utensils.",
       "Aluminium has good thermal conductivity and a high melting point.",
       "both_true_explains",
       "Both are true and the reason explains the assertion: it spreads heat quickly and evenly, and "
       "it does not soften on a stove. A thin oxide layer also stops it corroding further."),

    ar("sci-chem-ch3", "sci-chem-ch3.properties",
       "Graphite is used for making electrodes.",
       "Graphite is a non-metal that conducts electricity.",
       "both_true_explains",
       "Both are true and the reason explains the assertion: graphite is the usual exception among "
       "non-metals, and it also withstands high temperature, which electrodes must."),

    # ── Carbon and its Compounds ─────────────────────────────────────
    ar("sci-chem-ch4", "sci-chem-ch4.bonding",
       "Carbon forms compounds by sharing electrons rather than by transferring them.",
       "Gaining four electrons or losing four electrons would both need far too much energy.",
       "both_true_explains",
       "Both are true and the reason explains the assertion: a C4- ion could not hold six protons "
       "against ten electrons, and removing four electrons from a carbon atom takes more energy than "
       "any reaction would repay."),

    ar("sci-chem-ch4", "sci-chem-ch4.bonding",
       "Covalent compounds are generally poor conductors of electricity.",
       "Covalent compounds contain no ions to carry the current.",
       "both_true_explains",
       "Both are true and the reason explains the assertion: conduction needs charged particles free "
       "to move, and in a covalent compound the electrons are held in shared pairs."),

    ar("sci-chem-ch4", "sci-chem-ch4.properties",
       "Ethene decolourises bromine water.",
       "Ethene is an unsaturated compound and undergoes an addition reaction with bromine.",
       "both_true_explains",
       "Both are true and the reason explains the assertion: bromine adds across the double bond, "
       "which removes the brown colour. This is the standard test for unsaturation."),

    ar("sci-chem-ch4", "sci-chem-ch4.properties",
       "Saturated hydrocarbons such as methane burn with a clean blue flame when the air supply is enough.",
       "Combustion is complete, so only carbon dioxide and water are formed.",
       "both_true_explains",
       "Both are true and the reason explains the assertion: with no unburnt carbon left over there is "
       "no soot, and the flame stays blue."),

    ar("sci-chem-ch4", "sci-chem-ch4.properties",
       "Unsaturated hydrocarbons burn with a sooty flame.",
       "Unsaturated hydrocarbons have a lower proportion of carbon in their molecules.",
       "a_true_r_false",
       "The assertion is true but the reason is wrong. Unsaturated compounds have a higher proportion "
       "of carbon, so the air supply is not enough to burn all of it and the excess escapes as soot."),

    ar("sci-chem-ch4", "sci-chem-ch4.homologous",
       "All members of a homologous series show similar chemical properties.",
       "All members of a homologous series contain the same functional group.",
       "both_true_explains",
       "Both are true and the reason explains the assertion: chemical behaviour comes from the "
       "functional group, so a series sharing one group reacts in one way while its physical "
       "properties grade with molecular mass."),

    # ── Life Processes ───────────────────────────────────────────────
    ar("sci-bio-life", "sci-bio-life.transport",
       "The walls of the left ventricle are thicker than those of the right ventricle.",
       "The left ventricle has to pump blood to all parts of the body, against a much greater resistance.",
       "both_true_explains",
       "Both are true and the reason explains the assertion: pushing blood all the way round the body "
       "needs far more pressure than pushing it the short distance to the lungs."),

    ar("sci-bio-life", "sci-bio-life.transport",
       "Arteries have thick and elastic walls.",
       "Arteries carry blood away from the heart under high pressure.",
       "both_true_explains",
       "Both are true and the reason explains the assertion: the wall has to withstand the pressure "
       "and the elasticity smooths the flow between beats. Veins, under low pressure, have thin walls "
       "and valves instead."),

    ar("sci-bio-life", "sci-bio-life.respiration",
       "Diffusion alone cannot meet the oxygen requirements of a human being.",
       "Diffusion is a slow process and works only over very short distances.",
       "both_true_explains",
       "Both are true and the reason explains the assertion: no cell in the body is close enough to "
       "the outside air for diffusion to reach it in time, which is why a transport system is needed."),

    ar("sci-bio-life", "sci-bio-life.nutrition",
       "The small intestine of a herbivore is much longer than that of a carnivore.",
       "Herbivores eat grass, which is rich in cellulose and takes a long time to be digested.",
       "both_true_explains",
       "Both are true and the reason explains the assertion: a longer tube gives the slow digestion of "
       "plant material the time and surface it needs. Meat is digested quickly, so a carnivore's "
       "intestine is shorter."),

    ar("sci-bio-life", "sci-bio-life.nutrition",
       "The inner lining of the small intestine has finger-like projections called villi.",
       "Villi increase the surface area available for the absorption of digested food.",
       "both_true_explains",
       "Both are true and the reason explains the assertion: they are also richly supplied with blood "
       "vessels, which carry the absorbed food away quickly."),

    ar("sci-bio-life", "sci-bio-life.excretion",
       "The tubular part of a nephron reabsorbs most of the water from the filtrate.",
       "How much water is reabsorbed depends on how much the body has already taken in and how much is dissolved in the blood.",
       "both_true_explains",
       "Both are true and the reason explains the assertion: reabsorption is adjusted to the body's "
       "need, which is why urine is concentrated when little water has been drunk."),

    # ── Control and Coordination ─────────────────────────────────────
    ar("sci-bio-control", "sci-bio-control.nervous",
       "A neuron has a long, thin extension called an axon.",
       "The axon carries the electrical impulse away from the cell body towards the next neuron.",
       "both_true_explains",
       "Both are true and the reason explains the assertion: dendrites pick the information up and the "
       "axon carries it on, ending in a junction where a chemical crosses to the next cell."),

    ar("sci-bio-control", "sci-bio-control.plants",
       "Plants do not have a nervous system.",
       "Plants use electrical impulses and chemical signals to coordinate their responses.",
       "both_true_not_explains",
       "Both statements are true, but the reason does not explain the assertion - it describes what "
       "plants use instead. Plants have no nervous system because their cells are not organised into "
       "nerve tissue, and they rely on growth movements and hormones."),

    ar("sci-bio-control", "sci-bio-control.reflex",
       "A reflex action is involuntary and does not involve thinking.",
       "In a reflex action the impulse from a receptor travels to the spinal cord and back to a muscle without going to the brain first.",
       "both_true_explains",
       "Both are true and the reason explains the assertion: the shorter path through the spinal cord "
       "is what makes the response immediate, and the brain is informed afterwards."),

    ar("sci-bio-control", "sci-bio-control.hormones",
       "Adrenaline is called the emergency hormone.",
       "It is secreted in large amounts during fear, anger or danger and prepares the body to act.",
       "both_true_explains",
       "Both are true and the reason explains the assertion: it raises the heart rate and breathing "
       "rate and sends more blood to the muscles, which is exactly what a sudden demand needs."),

    ar("sci-bio-control", "sci-bio-control.hormones",
       "Iodine is important in our diet.",
       "Iodine is needed for the manufacture of thyroxine, which controls the metabolism of carbohydrates, proteins and fats.",
       "both_true_explains",
       "Both are true and the reason explains the assertion: without iodine the thyroid cannot make "
       "thyroxine, and the gland swells, which is the condition called goitre."),

    # ── Reproduction ─────────────────────────────────────────────────
    ar("sci-bio-repro", "sci-bio-repro.sexual-humans",
       "The sex of a human child is determined by the father and not by the mother.",
       "The mother always contributes an X chromosome, while the father contributes either an X or a Y.",
       "both_true_explains",
       "Both are true and the reason explains the assertion: since the mother's contribution is fixed, "
       "it is the chromosome the father passes on that decides the sex of the child."),

    ar("sci-bio-repro", "sci-bio-repro.sexual-plants",
       "Pollination and fertilisation are two different processes.",
       "Pollination is the transfer of pollen to the stigma, while fertilisation is the fusion of a male and a female gamete.",
       "both_true_explains",
       "Both are true and the reason explains the assertion: one is a transfer that can happen without "
       "the other following, the other is the actual union of gametes."),

    ar("sci-bio-repro", "sci-bio-repro.asexual",
       "Offspring produced by asexual reproduction are genetically identical to the parent.",
       "Asexual reproduction involves only one parent and no gametes fuse.",
       "both_true_explains",
       "Both are true and the reason explains the assertion: with a single parent and no mixing of "
       "genetic material, the DNA is simply copied, so the offspring are clones."),

    ar("sci-bio-repro", "sci-bio-repro.sexual-humans",
       "The embryo gets nutrition from the mother's blood.",
       "The placenta, a disc of tissue between the mother and the embryo, allows this exchange to take place.",
       "both_true_explains",
       "Both are true and the reason explains the assertion: the placenta has villi on the embryo's "
       "side, giving a large area over which oxygen and food pass from the mother's blood."),

    # ── Heredity ─────────────────────────────────────────────────────
    ar("sci-bio-heredity", "sci-bio-heredity.mendel",
       "A recessive trait may be inherited by an organism but not expressed.",
       "When a dominant and a recessive version of a trait are both present, only the dominant one is expressed.",
       "both_true_explains",
       "Both are true and the reason explains the assertion: the recessive version is carried in the "
       "organism's genetic makeup and can reappear in a later generation, as the dwarf plants did in "
       "Mendel's F2."),

    ar("sci-bio-heredity", "sci-bio-heredity.terms",
       "Acquired traits are not passed on to the next generation.",
       "Acquired traits do not bring about any change in the DNA of the germ cells.",
       "both_true_explains",
       "Both are true and the reason explains the assertion: only changes in the DNA of germ cells are "
       "inherited, so a muscle built by exercise or knowledge gained by study dies with the "
       "individual."),

    ar("sci-bio-heredity", "sci-bio-heredity.mendel",
       "In a monohybrid cross between two heterozygous tall pea plants, about a quarter of the offspring are dwarf.",
       "The recessive trait reappears in the F2 generation because the two versions of the trait separate when the gametes are formed.",
       "both_true_explains",
       "Both are true and the reason explains the assertion: each parent passes on either the tall or "
       "the dwarf version, and the one in four offspring that receives the dwarf version from both "
       "shows it."),

    # ── Our Environment ──────────────────────────────────────────────
    ar("sci-bio-env", "sci-bio-env.energy-flow",
       "A food chain usually has only three or four steps.",
       "At each step a large part of the energy is lost as heat, so very little is left for the levels above.",
       "both_true_explains",
       "Both are true and the reason explains the assertion: only about ten per cent passes from one "
       "trophic level to the next, and by the fourth or fifth step there is not enough energy left to "
       "support a population."),

    ar("sci-bio-env", "sci-bio-env.ecosystem",
       "Decomposers are essential components of an ecosystem.",
       "They break down dead organisms and return their nutrients to the soil.",
       "both_true_explains",
       "Both are true and the reason explains the assertion: without them nutrients would stay locked "
       "in dead bodies and the soil would be exhausted, and they also clean up the environment."),

    ar("sci-bio-env", "sci-bio-env.waste",
       "Ozone layer depletion is a matter of great concern.",
       "Chlorofluorocarbons used in refrigeration and air conditioning break down ozone molecules in the upper atmosphere.",
       "both_true_explains",
       "Both are true and the reason explains the assertion: the ozone layer absorbs harmful "
       "ultraviolet radiation, so thinning it lets more of that radiation reach the surface."),

    ar("sci-bio-env", "sci-bio-env.waste",
       "Plastic bags are a serious problem for the environment.",
       "Plastic is biodegradable and is broken down quickly by micro-organisms.",
       "a_true_r_false",
       "The assertion is true but the reason is the opposite of the truth. Plastic is non-biodegradable, "
       "which is exactly why it accumulates; it can also choke drains and be swallowed by animals."),

    ar("sci-bio-env", "sci-bio-env.ecosystem",
       "A garden is an artificial ecosystem.",
       "It is created and maintained by human beings, who decide which plants and animals are kept in it.",
       "both_true_explains",
       "Both are true and the reason explains the assertion: unlike a forest or a pond, its balance is "
       "held in place by human intervention rather than by natural processes alone."),
]


# ══════════════════════════════════════════════════════════════════════
# Case studies and source-based items
# ══════════════════════════════════════════════════════════════════════

CASE_STUDIES = [
    case("sci-phy-light", "sci-phy-light.mirrors",
         "A student places a candle flame in front of a concave mirror whose focal length is 12 cm, and "
         "tries to catch its image on a white screen. She moves the flame to different distances from "
         "the mirror and records what she sees.\n\n"
         "At 40 cm the image on the screen is small and inverted. At 24 cm it is inverted and exactly "
         "the same size as the flame. At 18 cm it is inverted and larger than the flame. At 8 cm she "
         "can get no image on the screen at all, however far she moves it.",
         [
             {"prompt": "At 24 cm from the mirror, the flame is at which position?",
              "options": ["At the centre of curvature", "At the principal focus",
                          "Between the focus and the pole", "Beyond the centre of curvature"],
              "answer": 0, "difficulty": "easy",
              "explanation": "For a concave mirror the centre of curvature is at twice the focal "
                             "length, so at 2 x 12 = 24 cm. An object there gives an image at the same "
                             "distance, of the same size, real and inverted."},

             {"prompt": "Why could the student get no image on the screen when the flame was at 8 cm?",
              "options": ["The image formed was virtual and cannot be taken on a screen",
                          "The image was formed at infinity",
                          "The mirror could not form any image at that distance",
                          "The image was too small to be seen"],
              "answer": 0, "difficulty": "medium",
              "explanation": "At 8 cm the flame is between the focus and the pole. A concave mirror "
                             "then gives a virtual, erect and magnified image behind the mirror, and a "
                             "virtual image cannot be caught on a screen - it is seen by looking into "
                             "the mirror."},

             {"prompt": "To obtain a magnified image on the screen, the flame must be placed",
              "options": ["Between the focus and the centre of curvature",
                          "Beyond the centre of curvature",
                          "Between the pole and the focus",
                          "Exactly at the principal focus"],
              "answer": 0, "difficulty": "medium",
              "explanation": "Between F and C, that is between 12 cm and 24 cm here, the image is real, "
                             "inverted, magnified and formed beyond C. That is what she saw at 18 cm. "
                             "Exactly at F no image is formed on the screen at all, since the rays come "
                             "out parallel."},

             {"prompt": "As the student moves the flame steadily away from the mirror, the image on the screen",
              "options": ["Moves towards the mirror and becomes smaller",
                          "Moves away from the mirror and becomes larger",
                          "Stays at the same distance but becomes smaller",
                          "Moves towards the mirror and becomes larger"],
              "answer": 0, "difficulty": "hard",
              "explanation": "For a real image formed by a concave mirror, moving the object further "
                             "away brings the image closer to the focus and makes it smaller. At an "
                             "infinite object distance the image is at the focus and is a point."},

             {"prompt": "The power of this mirror is",
              "options": ["About -8.3 D", "About +8.3 D", "About -0.08 D", "About +12 D"],
              "answer": 0, "difficulty": "hard",
              "explanation": "f = 12 cm = 0.12 m, and P = 1/f in metres. A concave mirror has a "
                             "negative focal length, so P = 1/(-0.12) = about -8.3 D."},
         ]),

    case("sci-phy-electricity", "sci-phy-electricity.combinations",
         "An electrician has a 220 V domestic supply. He is asked about two different loads.\n\n"
         "Load 1: a single bulb marked 60 W, 220 V.\n\n"
         "Load 2: three resistors of 4 ohm each connected in parallel, and this combination connected "
         "in series with a 2 ohm resistor, all across the same 220 V supply.",
         [
             {"prompt": "The current drawn by the 60 W bulb working at its rated voltage is about",
              "options": ["0.27 A", "0.37 A", "2.7 A", "13.2 A"],
              "answer": 0, "difficulty": "medium",
              "explanation": "P = VI, so I = P/V = 60/220 = 0.27 A. The 13.2 A figure is what you get "
                             "by multiplying instead of dividing."},

             {"prompt": "The resistance of the bulb when it is glowing normally is about",
              "options": ["807 ohm", "267 ohm", "132 ohm", "3.7 ohm"],
              "answer": 0, "difficulty": "hard",
              "explanation": "P = V^2/R, so R = V^2/P = 220 x 220 / 60 = 48400/60 = about 807 ohm."},

             {"prompt": "The equivalent resistance of the three 4 ohm resistors in parallel is",
              "options": ["About 1.33 ohm", "About 4 ohm", "About 12 ohm", "About 0.75 ohm"],
              "answer": 0, "difficulty": "medium",
              "explanation": "1/R = 1/4 + 1/4 + 1/4 = 3/4, so R = 4/3 = about 1.33 ohm. Three equal "
                             "resistors in parallel give one third of each. 12 ohm is the series answer."},

             {"prompt": "The total resistance of Load 2, and the current it draws from the 220 V supply, are",
              "options": ["About 3.33 ohm and 66 A", "About 14 ohm and 15.7 A",
                          "About 3.33 ohm and 0.66 A", "About 1.33 ohm and 165 A"],
              "answer": 0, "difficulty": "hard",
              "explanation": "Total R = 1.33 + 2 = about 3.33 ohm, since the parallel combination is "
                             "in series with the 2 ohm resistor. I = V/R = 220/3.33 = about 66 A. Such a "
                             "current would blow a domestic fuse at once, which is the practical point "
                             "of the question."},

             {"prompt": "The energy used by the 60 W bulb in 2 hours, and its cost at 5 rupees per unit, are",
              "options": ["0.12 kWh and 60 paise", "1.2 kWh and 6 rupees",
                          "0.12 kWh and 6 rupees", "120 kWh and 600 rupees"],
              "answer": 0, "difficulty": "medium",
              "explanation": "Energy = 60 W x 2 h = 120 Wh = 0.12 kWh, and one unit is one kWh. Cost = "
                             "0.12 x 5 = 0.60 rupees, that is 60 paise."},
         ]),

    case("sci-chem-ch3", "sci-chem-ch3.displacement",
         "Four students are each given an unlabelled metal strip, P, Q, R and S, and asked to test it. "
         "The results are shown below.\n\n"
         "P: no bubbles with dilute hydrochloric acid; no change when dipped in copper sulphate solution.\n"
         "Q: steady bubbles with dilute hydrochloric acid; the blue colour of copper sulphate fades and "
         "a brown coating forms on it; no change in zinc sulphate solution.\n"
         "R: reacts violently with cold water, giving a gas that burns with a pop.\n"
         "S: no reaction with cold water, but reacts with steam to give a gas that burns with a pop.",
         [
             {"prompt": "Which strip is the least reactive?",
              "options": ["P", "Q", "R", "S"],
              "answer": 0, "difficulty": "easy",
              "explanation": "P does nothing with dilute acid and cannot displace copper, so it lies "
                             "below copper in the reactivity series. It could be copper itself, silver "
                             "or gold."},

             {"prompt": "The brown coating formed on Q in copper sulphate solution is",
              "options": ["Copper, displaced by Q", "Rust formed on Q",
                          "Copper sulphate that has crystallised out", "An oxide of Q"],
              "answer": 0, "difficulty": "medium",
              "explanation": "Q is more reactive than copper and pushes it out of solution as the free "
                             "metal, which deposits as a reddish-brown layer. The fading blue colour is "
                             "the copper sulphate being used up."},

             {"prompt": "Q could be",
              "options": ["Iron", "Sodium", "Copper", "Gold"],
              "answer": 0, "difficulty": "medium",
              "explanation": "Q displaces copper but not zinc, so it lies between them in the series. "
                             "Iron does exactly that. Sodium is far too reactive, being above zinc, and "
                             "copper and gold are below it."},

             {"prompt": "The gas that burns with a pop in the tests on R and S is",
              "options": ["Hydrogen", "Oxygen", "Carbon dioxide", "Chlorine"],
              "answer": 0, "difficulty": "easy",
              "explanation": "Both reactions release hydrogen, which burns with a characteristic pop "
                             "when a lighted splinter is brought to it."},

             {"prompt": "Which of the four strips is most likely to be magnesium or aluminium?",
              "options": ["S", "R", "Q", "P"],
              "answer": 0, "difficulty": "hard",
              "explanation": "S does not react with cold water but does react with steam, which is the "
                             "behaviour of magnesium and aluminium. R reacts with cold water itself and "
                             "so is higher in the series, nearer sodium or potassium."},
         ]),

    case("sci-chem-ch2", "sci-chem-ch2.ph",
         "A student tests six unlabelled household liquids with universal indicator and records the "
         "colours and pH values.\n\n"
         "A: red, pH 2\n"
         "B: green, pH 7\n"
         "C: blue, pH 9\n"
         "D: violet, pH 13\n"
         "E: orange, pH 5\n"
         "F: yellow, pH 6",
         [
             {"prompt": "Which liquid is most likely to be a solution of soap?",
              "options": ["D", "A", "B", "E"],
              "answer": 0, "difficulty": "medium",
              "explanation": "Soap is made by the reaction of a strong base with a fatty acid and its "
                             "solution is basic, usually around pH 9 to 10, but a strong soap solution "
                             "can be higher. Of these, D is the clearly basic one. A is acidic, B is "
                             "neutral and E is weakly acidic."},

             {"prompt": "Which liquid would turn blue litmus paper red?",
              "options": ["A and E only", "A, E and F", "C and D", "B only"],
              "answer": 0, "difficulty": "easy",
              "explanation": "Blue litmus turns red only in an acid. A (pH 2) and E (pH 5) are clearly "
                             "acidic; F at pH 6 is very close to neutral and would barely change it, "
                             "and B at pH 7 would not change it at all."},

             {"prompt": "Which liquid could be the gastric juice found in the stomach?",
              "options": ["A", "C", "B", "F"],
              "answer": 0, "difficulty": "easy",
              "explanation": "Gastric juice contains hydrochloric acid and has a pH of about 1.2, so A "
                             "at pH 2 is the closest match. The others are far too mild or basic."},

             {"prompt": "Which liquid is neutral?",
              "options": ["B", "F", "C", "E"],
              "answer": 0, "difficulty": "easy",
              "explanation": "A pH of exactly 7 is neutral, and universal indicator shows green at that "
                             "point. B is neutral, which is what pure water gives."},

             {"prompt": "The liquids arranged in order of increasing acidity are",
              "options": ["D, C, B, F, E, A", "A, E, F, B, C, D",
                          "D, C, F, B, E, A", "A, E, F, C, B, D"],
              "answer": 0, "difficulty": "hard",
              "explanation": "Acidity increases as pH falls, so the order of increasing acidity is the "
                             "order of decreasing pH: D (13), C (9), B (7), F (6), E (5), A (2). The "
                             "second option is the order of increasing basicity instead."},
         ]),

    case("sci-bio-life", "sci-bio-life.transport",
         "Blood passes through the human heart twice in one complete circuit of the body. The right "
         "side receives blood that has given up its oxygen to the body's cells and sends it to the "
         "lungs. The left side receives blood that has just picked up oxygen in the lungs and sends it "
         "out to the rest of the body.\n\n"
         "Birds and mammals keep the two kinds of blood completely separate, while fish have a heart "
         "with only two chambers and a single circulation.",
         [
             {"prompt": "The separation of the right and left sides of the human heart is important because it",
              "options": ["Prevents oxygen-rich and oxygen-poor blood from mixing, so that the body gets a steady supply of oxygen",
                          "Allows the heart to beat more slowly",
                          "Reduces the amount of blood in the body",
                          "Makes the blood flow in only one direction"],
              "answer": 0, "difficulty": "medium",
              "explanation": "Mixing would deliver partly used blood to the tissues. Warm-blooded "
                             "animals such as birds and mammals spend a great deal of energy keeping "
                             "their body temperature steady, so they need a highly efficient oxygen "
                             "supply."},

             {"prompt": "The chamber that pumps blood to all parts of the body is the",
              "options": ["Left ventricle", "Right ventricle", "Left auricle", "Right auricle"],
              "answer": 0, "difficulty": "easy",
              "explanation": "The left ventricle pumps oxygen-rich blood into the aorta and out to the "
                             "whole body, which is why its wall is the thickest of the four chambers. "
                             "The auricles only receive blood."},

             {"prompt": "Blood reaching the lungs from the heart is",
              "options": ["Rich in carbon dioxide and low in oxygen",
                          "Rich in oxygen and low in carbon dioxide",
                          "Rich in both oxygen and carbon dioxide",
                          "Free of both oxygen and carbon dioxide"],
              "answer": 0, "difficulty": "medium",
              "explanation": "The pulmonary artery carries deoxygenated blood from the right ventricle "
                             "to the lungs. It is the only artery in the body that carries "
                             "deoxygenated blood."},

             {"prompt": "A fish needs only a two-chambered heart because",
              "options": ["Its blood passes to the gills and then straight on to the body, so a single circuit is enough",
                          "It lives in water, which contains more oxygen than air",
                          "It does not need oxygen at all",
                          "Its body temperature changes with the water around it"],
              "answer": 0, "difficulty": "hard",
              "explanation": "In a fish the heart pumps blood to the gills, where it is oxygenated, and "
                             "it then continues to the body without returning to the heart first. Fish "
                             "are cold-blooded and do not spend energy on keeping warm, so this single "
                             "circulation meets their needs."},

             {"prompt": "Valves are present between the auricles and the ventricles, and in the veins. Their function is to",
              "options": ["Prevent the backflow of blood",
                          "Increase the pressure of blood",
                          "Slow down the heart rate",
                          "Separate oxygen-rich from oxygen-poor blood"],
              "answer": 0, "difficulty": "easy",
              "explanation": "Valves are one-way structures. Those in the heart stop blood flowing back "
                             "into an auricle when a ventricle contracts, and those in the veins help "
                             "return blood against gravity."},
         ]),

    case("sci-bio-heredity", "sci-bio-heredity.mendel", case_sensitive=True,
         stem="Mendel crossed pure-breeding tall pea plants with pure-breeding dwarf ones. Every plant in "
         "the first generation, F1, was tall. He then allowed the F1 plants to self-pollinate and "
         "counted the second generation, F2: 787 tall plants and 277 dwarf plants.\n\n"
         "He repeated the experiment with other pairs of contrasting traits and each time found the "
         "same pattern in F1 and a similar ratio in F2.",
         questions=[
             {"prompt": "The ratio of tall to dwarf plants in F2 is closest to",
              "options": ["3 : 1", "1 : 1", "9 : 3 : 3 : 1", "2 : 1"],
              "answer": 0, "difficulty": "easy",
              "explanation": "787/277 = 2.84, which rounds to 3. Mendel's monohybrid F2 ratio is 3 : 1."},

             {"prompt": "All the F1 plants were tall because",
              "options": ["The tall trait is dominant over the dwarf trait",
                          "The dwarf trait was destroyed in F1",
                          "The F1 plants received only the tall version of the trait",
                          "Height in pea plants is decided by the environment"],
              "answer": 0, "difficulty": "medium",
              "explanation": "Each F1 plant carried one version for tallness and one for dwarfness, but "
                             "only the dominant one was expressed. The dwarf version was not lost - it "
                             "reappeared in F2."},

             {"prompt": "If the tall version is written T and the dwarf version t, the genetic makeup of an F1 plant is",
              "options": ["Tt", "TT", "tt", "TTtt"],
              "answer": 0, "difficulty": "easy",
              "explanation": "A pure tall parent gives T and a pure dwarf parent gives t, so every F1 "
                             "plant is Tt - heterozygous, and tall because T is dominant."},

             {"prompt": "The dwarf plants reappearing in F2 shows that",
              "options": ["A trait can be inherited but not expressed in a generation",
                          "The dwarf trait is stronger than the tall trait",
                          "Mendel's plants were not pure-breeding",
                          "Traits are acquired during an organism's lifetime"],
              "answer": 0, "difficulty": "medium",
              "explanation": "The dwarf version was carried through F1 without showing. When two F1 "
                             "plants each passed it on, the tt combination appeared again and the trait "
                             "was expressed."},

             {"prompt": "In F2, the proportion of plants that are heterozygous tall is",
              "options": ["One half", "One quarter", "Three quarters", "All of them"],
              "answer": 0, "difficulty": "hard",
              "explanation": "Of the four possible combinations, TT, Tt, tT and tt, two are "
                             "heterozygous. So half of all F2 plants are Tt: one quarter TT, one half "
                             "Tt, one quarter tt. Of the tall plants alone, two out of three are "
                             "heterozygous."},
         ]),

    case("sci-bio-env", "sci-bio-env.energy-flow",
         "In a grassland, grass traps energy from sunlight. Grasshoppers eat the grass, frogs eat the "
         "grasshoppers, snakes eat the frogs, and hawks eat the snakes.\n\n"
         "Suppose the grass in a particular area has 10,000 J of energy stored in it. Only a small "
         "part of the sunlight falling on the grass is captured at all, and at every step from one "
         "organism to the next most of the energy taken in is used up or lost as heat.",
         [
             {"prompt": "The energy available to the grasshoppers is about",
              "options": ["1,000 J", "10,000 J", "100 J", "9,000 J"],
              "answer": 0, "difficulty": "easy",
              "explanation": "By the ten per cent rule, only about a tenth of the energy at one "
                             "trophic level reaches the next. 10,000 x 0.1 = 1,000 J."},

             {"prompt": "The energy available to the frogs, and then to the snakes, is about",
              "options": ["100 J and 10 J", "1,000 J and 100 J", "10 J and 1 J", "100 J and 100 J"],
              "answer": 0, "difficulty": "easy",
              "explanation": "Applying the ten per cent rule again: frogs get 1,000 x 0.1 = 100 J and "
                             "snakes get 100 x 0.1 = 10 J."},

             {"prompt": "The energy available to the hawk at the top of this chain is about",
              "options": ["1 J", "10 J", "100 J", "1,000 J"],
              "answer": 0, "difficulty": "easy",
              "explanation": "Snakes have 10 J, so the hawk gets about 10 x 0.1 = 1 J. This is why "
                             "chains rarely run beyond four or five steps."},

             {"prompt": "The grass in this food chain is a",
              "options": ["Producer", "Primary consumer", "Decomposer", "Secondary consumer"],
              "answer": 0, "difficulty": "easy",
              "explanation": "Grass makes its own food from sunlight by photosynthesis, so it is the "
                             "producer and the first trophic level. The grasshopper that eats it is the "
                             "primary consumer."},

             {"prompt": "If all the frogs in this grassland were removed by a disease, the most likely immediate effect is that",
              "options": ["The grasshopper population would rise and the snake population would fall",
                          "The grass would die out",
                          "The hawk population would rise",
                          "Nothing would change, since other food chains exist"],
              "answer": 0, "difficulty": "hard",
              "explanation": "With no frogs to eat them, grasshoppers would increase and could strip "
                             "the grass; with no frogs to eat, snakes would lose a food source and "
                             "decline. Removing one link disturbs the whole chain, which is why "
                             "biodiversity matters."},

             {"prompt": "The loss of energy between two trophic levels happens mainly because",
              "options": ["Organisms use much of the energy they take in for their own life processes, and some is lost as heat",
                          "The energy is destroyed when an organism is eaten",
                          "Only the bones and hard parts of an organism are eaten",
                          "Decomposers take the energy out of the chain entirely"],
              "answer": 0, "difficulty": "medium",
              "explanation": "Energy is never destroyed. Most of it is used for respiration, movement "
                             "and repair, and leaves the chain as heat; some parts of an organism are "
                             "simply not eaten. Only about a tenth is built into new tissue."},
         ]),
]


# ══════════════════════════════════════════════════════════════════════
# Application and analytical items
# ══════════════════════════════════════════════════════════════════════

APPLICATION = [
    app("sci-phy-light", "sci-phy-light.mirrors",
        "A driver wants a mirror that will let her see the whole of the road behind the car. Which "
        "mirror should she use, and why?",
        ["A convex mirror, because it gives an erect image and a wide field of view",
         "A concave mirror, because it gives a magnified image",
         "A plane mirror, because it gives an image of exactly the same size",
         "A convex mirror, because it gives a real and inverted image"],
        0,
        "A convex mirror always forms a virtual, erect and diminished image, and because it curves "
        "outward it takes in a much wider field of view than a plane mirror of the same size. The "
        "image is never real, so the last option is wrong.",
        difficulty="medium"),

    app("sci-phy-eye", "sci-phy-eye.defects",
        "A student can read the text of his book comfortably but cannot read what is written on the "
        "blackboard from the back bench. What is the likely defect and its correction?",
        ["Myopia, corrected with a concave lens of suitable power",
         "Hypermetropia, corrected with a convex lens of suitable power",
         "Presbyopia, corrected with bifocal lenses",
         "Myopia, corrected with a convex lens of suitable power"],
        0,
        "He sees near objects clearly but not distant ones, which is myopia: the image of a distant "
        "object falls in front of the retina. A concave lens diverges the rays before they enter the "
        "eye so that the image falls back on the retina.",
        difficulty="easy"),

    app("sci-phy-electricity", "sci-phy-electricity.power",
        "A household uses a 1.5 kW electric heater for 4 hours every day. At 6 rupees per unit, the "
        "cost of running the heater for a 30-day month is",
        ["1,080 rupees", "108 rupees", "540 rupees", "216 rupees"],
        0,
        "Energy per day = 1.5 kW x 4 h = 6 kWh = 6 units. For 30 days that is 180 units, and at 6 "
        "rupees a unit the cost is 180 x 6 = 1,080 rupees.",
        difficulty="medium"),

    app("sci-phy-magnetic", "sci-phy-magnetic.domestic",
        "A house has a 5 A fuse on the lighting circuit. Why would replacing it with a 15 A fuse be "
        "dangerous?",
        ["The wiring is rated for the lower current, so it could overheat and start a fire before the fuse blows",
         "The appliances would receive more than 220 V and be damaged",
         "The 15 A fuse would blow immediately under normal load",
         "The circuit would draw less current and the lights would dim"],
        0,
        "A fuse is chosen to match the current-carrying capacity of the wiring it protects. A 15 A "
        "fuse would allow the lighting wires to heat far beyond their rating before melting, and "
        "overheated wiring is a common cause of domestic fires. The supply voltage is unchanged.",
        difficulty="hard"),

    app("sci-chem-ch2", "sci-chem-ch2.compounds",
        "A family finds that soap does not lather in their tap water and a sticky deposit forms on "
        "their clothes. What is the cause and the practical remedy?",
        ["The water is hard, containing calcium or magnesium salts; washing soda can be added to soften it",
         "The water is acidic; a small amount of acid should be added to it",
         "The soap has gone bad and must be replaced with a different brand",
         "The water is soft; boiling it will make the soap lather better"],
        0,
        "Calcium and magnesium ions in hard water react with soap to form an insoluble scum, which "
        "wastes the soap and settles on cloth. Washing soda precipitates those ions out of the water. "
        "A detergent would also work, since its calcium and magnesium salts stay soluble.",
        difficulty="medium"),

    app("sci-chem-ch2", "sci-chem-ch2.acids",
        "A bottle of concentrated acid has to be diluted for a school experiment. The safe procedure is to",
        ["Add the acid to water slowly with constant stirring",
         "Add water to the concentrated acid quickly",
         "Mix equal volumes of acid and water at once in a closed flask",
         "Heat the acid first and then add water to it"],
        0,
        "Dilution is strongly exothermic. Adding acid to water lets the heat spread through the large "
        "volume of water. Adding water to acid produces the heat in a small volume, which can boil and "
        "splash the concentrated acid out of the vessel.",
        difficulty="medium"),

    app("sci-chem-ch3", "sci-chem-ch3.alloys",
        "An iron railing near the coast keeps rusting even though it is painted. Which measure would "
        "protect it best for the longest time?",
        ["Galvanising it before painting",
         "Repainting it more often with a thicker coat",
         "Wiping it with oil every week",
         "Making it from pure iron instead of steel"],
        0,
        "Galvanising coats the iron with zinc, which corrodes in place of the iron even where the "
        "coating is scratched, because zinc is the more reactive metal. Painting alone only delays "
        "rusting, and any crack lets moisture reach the iron. Pure iron rusts just as readily.",
        difficulty="hard"),

    app("sci-chem-ch4", "sci-chem-ch4.soaps",
        "A student has to wash an oily cloth in water known to be hard. Which should she use and why?",
        ["A detergent, because it does not form an insoluble scum with calcium and magnesium ions",
         "A soap, because it cleans better than any detergent",
         "A soap, because hard water makes soap lather more easily",
         "Either one, since hard water has no effect on cleansing"],
        0,
        "Soap reacts with the calcium and magnesium ions in hard water to form an insoluble scum, so "
        "much of it is wasted before it can lather. Detergents form salts that stay soluble, so they "
        "clean normally in hard water.",
        difficulty="medium"),

    app("sci-chem-ch1", "sci-chem-ch1.effects",
        "Chips sold in packets are flushed with nitrogen before the packet is sealed. The reason is that nitrogen",
        ["Prevents the fats and oils from being oxidised, which would make the chips taste rancid",
         "Keeps the packet stiff so the chips are not crushed",
         "Is cheaper than air and easier to pump in",
         "Stops bacteria from growing by making the packet acidic"],
        0,
        "Fats and oils oxidise in air and turn rancid, changing smell and taste. Nitrogen is "
        "unreactive, so it displaces the oxygen in the packet and prevents the oxidation. Keeping the "
        "packet full is a secondary benefit.",
        difficulty="medium"),

    app("sci-bio-life", "sci-bio-life.respiration",
        "A jar of dough left in a warm place rises and gives off a smell of alcohol. The process "
        "responsible is",
        ["Anaerobic respiration by yeast, producing ethanol and carbon dioxide",
         "Aerobic respiration by yeast, producing water and carbon dioxide",
         "Photosynthesis by the yeast, producing oxygen",
         "Decomposition of flour by bacteria, producing methane"],
        0,
        "Yeast in the dough respires without oxygen, breaking glucose into ethanol and carbon dioxide. "
        "The gas forms bubbles that make the dough rise, and the ethanol gives the smell. This is the "
        "basis of baking and brewing.",
        difficulty="medium"),

    app("sci-bio-control", "sci-bio-control.hormones",
        "A doctor advises a patient with a swollen neck to use iodised salt. The swelling and the "
        "advice are connected because iodine is needed to make",
        ["Thyroxine, which is produced by the thyroid gland and controls metabolism",
         "Insulin, which is produced by the pancreas and controls blood sugar",
         "Adrenaline, which is produced by the adrenal gland and acts in emergencies",
         "Testosterone, which controls the development of male features"],
        0,
        "A swollen neck suggests goitre, an enlarged thyroid caused by too little thyroxine. Iodine is "
        "a raw material for thyroxine, so iodised salt prevents the deficiency. Insulin, adrenaline "
        "and testosterone need no iodine.",
        difficulty="medium"),

    app("sci-bio-env", "sci-bio-env.waste",
        "A city wants to cut the amount of waste going to its landfill. Which single step would reduce "
        "the landfill load most?",
        ["Separating biodegradable waste for composting at source",
         "Burning all waste in the open",
         "Burying plastic waste in deeper trenches",
         "Collecting all waste together in one bin"],
        0,
        "Kitchen and garden waste is biodegradable and forms the largest share of household waste by "
        "weight; composting it at source keeps it out of the landfill and returns nutrients to the "
        "soil. Open burning pollutes the air, and plastic is non-biodegradable wherever it is buried.",
        difficulty="medium"),

    app("sci-chem-ch4", "sci-chem-ch4.nomenclature",
        "A compound has three carbon atoms in a straight chain and a -OH group at the end. Its IUPAC "
        "name and molecular formula are",
        ["Propan-1-ol, C3H7OH", "Propanone, C3H6O",
         "Propanoic acid, C2H5COOH", "Propene, C3H6"],
        0,
        "Three carbons give the root prop-, and an alcohol gives the suffix -ol, so propan-1-ol. A "
        "ketone would need the carbonyl group between two carbons, and an acid would need -COOH. "
        "Propene is an unsaturated hydrocarbon with no -OH group at all.",
        difficulty="hard"),

    app("sci-bio-heredity", "sci-bio-heredity.sex",
        "A couple already have three daughters and are told that the fourth child is more likely to be "
        "a boy. Is this correct?",
        ["No, because the chance of a boy or a girl is about equal at every pregnancy",
         "Yes, because the pattern of previous children decides the next one",
         "No, because the sex of a child is decided by the mother's chromosome",
         "Yes, because a family cannot have four children of the same sex"],
        0,
        "Each pregnancy is an independent event with roughly a one in two chance of either sex, "
        "because the father contributes an X or a Y chromosome at random. Previous children have no "
        "effect on the next, and the sex is decided by the father's contribution, not the mother's.",
        difficulty="medium"),

    app("sci-phy-light", "sci-phy-light.refraction",
        "A fish in a pond appears to be nearer the surface than it actually is. This happens because "
        "light from the fish",
        ["Bends away from the normal as it leaves the water, so the fish appears higher than it is",
         "Bends towards the normal as it leaves the water, so the fish appears higher than it is",
         "Travels in a straight line and is reflected by the surface",
         "Is absorbed by the water before it reaches the eye"],
        0,
        "Going from water, which is optically denser, into air, the ray speeds up and bends away from "
        "the normal. Tracing the bent ray back in a straight line puts the fish higher, and so "
        "nearer, than it really is. This is why a spear aimed straight at the fish would miss it.",
        difficulty="hard"),
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
                    "generator supplies CBSE's fixed four-option scaffold; case studies carry one "
                    "passage into every sub-question. Each item names its own chapter and topic."
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
        f"{len(CASE_STUDIES)} passages with {subs} sub-questions, "
        f"{len(APPLICATION)} application items = "
        f"{len(ASSERTION_REASON) + subs + len(APPLICATION)} questions"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
