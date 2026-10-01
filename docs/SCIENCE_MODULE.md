# Science module — syllabus map and content spec

Board: **CBSE / NCERT Class 10, session 2025-26** (rationalised syllabus).
Everything below is data in `backend/content/curriculum.json` — no chapter list
is hard-coded in application code.

## Syllabus status policy

| Status | Meaning | In default tests? |
|---|---|---|
| `core` | In the current board syllabus | Yes |
| `foundation` | Class 9 prerequisite recall needed to attempt Class 10 items (symbols, valency, formulae) | Yes, labelled "fundamentals" |
| `optional` | Stored for completeness, **not** in the current exam syllabus | Only from explicitly-labelled Advanced modes |
| `removed` | Deleted from the syllabus | No, unless `ALLOW_OFF_SYLLABUS=true` |

`Periodic Classification of Elements` is `optional` and `Sources of Energy` is
`removed`, matching the 2025-26 rationalisation. Element symbols, valency, atomic
number and electronic configuration live in a `foundation` chapter
("Element & Formula Fundamentals") because Class 10 items depend on them.

## Chapter map and seeded bank

| Branch | Chapter | Status | Questions |
|---|---|---|---|
| Chemistry | Element & Formula Fundamentals | foundation | 276 |
| Chemistry | 1. Chemical Reactions and Equations | core | 171 |
| Chemistry | 2. Acids, Bases and Salts | core | 156 |
| Chemistry | 3. Metals and Non-metals | core | 95 |
| Chemistry | 4. Carbon and its Compounds | core | 95 |
| Chemistry | Periodic Classification of Elements | optional | 0 |
| Physics | Light — Reflection and Refraction | core | 85 |
| Physics | The Human Eye and the Colourful World | core | 47 |
| Physics | Electricity | core | 120 |
| Physics | Magnetic Effects of Electric Current | core | 22 |
| Physics | Sources of Energy | removed | 0 |
| Biology | Life Processes | core | 82 |
| Biology | Control and Coordination | core | 67 |
| Biology | How Do Organisms Reproduce? | core | 41 |
| Biology | Heredity | core | 21 |
| Biology | Our Environment | core | 25 |
| Biology | Management of Natural Resources | optional | 0 |

**Total: 1,304 approved items generated from 482 structured facts.**
Counts shift as content is added; read them live from `GET /api/content/tree`.

## Question-type coverage

Chemistry — valency (both directions), element symbols (both directions), atomic
number, electronic configuration, metal/non-metal classification, "which is NOT",
formula recognition (both directions), common names, acid/base/salt
classification, definitions (both directions), reaction type, observation,
product identification, exo/endothermic, interactive balancing, subject/attribute
facts (indicators, pH, compounds and uses, alloys, ores, extraction, functional
groups, homologous series).

Physics — formula recognition (both directions), variable identification, SI
units, definitions, numerical speed drills (Ohm's law, power, current, potential
difference, refractive index, lens power with the classic cm/m trap, series
resistance, radius of curvature), image formation, eye defects and corrections,
refraction phenomena, dispersion, magnetic rules and domestic circuits.

Biology — definitions, organ/structure functions, processes, terminology,
hormones and glands, tropisms, reproduction modes and examples, Mendelian ratios
and sex determination, ecosystem and energy-flow facts, and correct-order
sequence questions (alimentary canal, airway, urine path, circulation, reflex arc,
flower reproduction, trophic levels, urine formation).

## Fact file contract

```jsonc
{
  "chapter": "sci-chem-ch2",       // default chapter for items in this file
  "topic": "sci-chem-ch2.ph",      // default topic (may be null)
  "kind": "fact",                  // default kind -> selects the generator
  "source_ref": "…",               // required on every generated item
  "generator": null,               // optional explicit generator override
  "items": [ { "kind": "fact", "chapter": "…", "topic": "…", … } ]
}
```

Per-item `kind`, `chapter` and `topic` override the file defaults, so one file can
mix definitions, facts and sequences (as `science/biology/facts.json` does). If an
item overrides `chapter` but not `topic`, the inherited topic is dropped rather
than creating a topic that belongs to a different chapter.

## Content safety rules

* Only atomic facts and **original** item wording are stored — no textbook
  passages, no reproduced prose, no scanned content.
* Every item carries `source_ref` for traceability.
* Items stay inside the Class 10 boundary. Advanced material is only reachable
  through chapters flagged `optional`/`removed`, which default modes exclude.
* AI-generated items are quarantined as `pending_review` and must be approved
  before they can be served. The grounding gate rejects any item whose correct
  answer contains a number or chemical symbol absent from the facts it was given.
