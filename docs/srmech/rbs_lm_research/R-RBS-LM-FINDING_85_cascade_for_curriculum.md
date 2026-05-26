# Finding 85 — Glass-box cascade as curriculum-evaluation and curriculum-design tool

**Status:** Framework articulation; parking for future curriculum-design work
**Trigger:** User framework reading 2026-05-26
**Predecessor work:** Finding 84 (glass-box LLM via cascade methodology)

---

## §1 The finding

The glass-box property of the cascade (Finding 84) makes it a usable tool
for *evaluating* educational curricula and *designing* new curricula by
substrate-coverage map.

User framing 2026-05-26:

> "we can also see what adding coding camps and other extra curricular
> activities contribute. maybe not helpful here but for creating curriculum
> in the future"

---

## §2 What the cascade enables for curriculum work

If the cascade has the glass-box property (Finding 84), three uses follow:

### 2.1 Curriculum evaluation

Given any educational program (K-12 + extra-curricular), build a cascade
kernel per source. Examine the union of top eigvec content. Identify:

- Which substrate-classes are well-represented (multiple corpora; tight
  within-class alignment)
- Which substrate-classes are sparse (single corpus; no within-class baseline)
- Which substrate-classes are absent

This is auditable, glass-box, no opaque inference required.

### 2.2 Curriculum design

Given a target substrate-coverage profile ("students should encounter
mathematical vocabulary, scientific observation language, historical narrative
tense, programming patterns, music notation, art description"), recommend
material to fill gaps. The cascade flags which substrate-classes need more
exposure and *which specific corpora would fill that gap*.

### 2.3 Personalized learning substrate-completeness

For an individual learner, map their substrate-coverage (what materials
they've been exposed to). Identify gaps relative to a target profile.
Recommend specific corpora from the open-access substrate library that
would fill those gaps.

---

## §3 Substrate-classes the methodology has detected so far

Per Findings 73 + 77 + 78 (+ post-OpenStax extension):

| Substrate-class | Corpora identifying it | Distinguishability |
|---|---|---|
| Reading material | McGuffey Primer + Grades 1-6 (n=7) | within=0.191, ratio 1.61 |
| Grammar instruction | Kittredge / Kirkham / Strunk (n=3) | within=0.168, ratio 1.53 |
| Science (narrative) | Astronomy YF / Star-land / Health (n=3) | within=0.144, ratio 1.22 |
| History (narrative) | Story of the Greeks (n=1) | n/a baseline |
| Geography (heterogeneous) | Home / Commercial / How-Fed (n=3) | within=0.114, ratio 1.09 |
| Math (post-OpenStax) | Elementary + Intermediate Algebra (n=2) | pending |
| Modern composition (post-OpenStax) | Writing Guide (n=1) | pending |
| Code | codeparrot/codeparrot-clean (52d; n=streaming) | 3.60x distinct from English text |
| Religious-Abrahamic | KJV, Quran, Tanakh (53; n=3) | strong within-class |
| Religious-Eastern | Bhagavad, Tao, Dhammapada (53e; n=3) | moderate within-class |
| Literary poetry | Milton, Shakespeare, Pope, Whitman, etc. (54m; n=6) | within-poetry sub-classes |

Each is a substrate-class the cascade has empirically detected. Each would
contribute to a curriculum-coverage map.

---

## §4 Extra-curricular substrate-classes worth adding

Per user's "coding camps and other extra curricular activities" — the
cascade map should include:

| Activity | Expected substrate signature | Available sources |
|---|---|---|
| Coding camps | Programming vocab (partially covered by 52d codeparrot) | freeCodeCamp curriculum; Khan Academy Python; W3Schools |
| Music | Notation language (crescendo, andante); genre vocab | Music theory primers; PG public-domain songbooks |
| Art / drawing | Spatial/visual description; technique terms | PG art history; technique books |
| Drama / theater | Stage direction; character voice; play structure | PG plays (Shakespeare, etc); stage-direction manuals |
| Sports | Rule books; position vocab; action descriptors | Rules of various sports; sports almanacs |
| Scouting | Outdoor skill vocab; character-formation language | Boy/Girl Scout handbooks (historic; some on PG) |
| Crafts / making | Tool vocab; technique sequences | PG craft books |
| Gardening | Domain-specific (overlaps science) | PG gardening manuals |
| Cooking | Domain-specific (overlaps science) | PG cookbooks; modern recipes |
| Volunteering | Service vocabulary; civic engagement language | Civic engagement guides |

Each adds a substrate-class to the cascade map. Some will overlap formal
subjects; others will be genuinely distinct.

---

## §5 The methodology, formalized

To build a curriculum-evaluation tool from the cascade:

```python
# 1. Build cascade kernels for ALL educational materials available
kernels = {source: build_kernel(corpus) for source, corpus in materials.items()}

# 2. Run pairwise alignment; identify substrate-classes via within/cross ratio
substrate_classes = cluster_kernels_by_alignment_ratio(kernels)

# 3. For a target curriculum or individual learner, build coverage profile
coverage = {sc: count_kernels_in_class(sc, learner_materials)
            for sc in substrate_classes}

# 4. Flag gaps: substrate-classes with low/zero coverage relative to target
gaps = {sc for sc, n in coverage.items() if n < target_threshold[sc]}

# 5. Recommend corpora that would fill each gap
recommendations = {sc: pick_corpora_from(substrate_class_library[sc])
                    for sc in gaps}
```

The cascade methodology + the substrate-class library + a target curriculum
specification yields auditable, glass-box curriculum recommendations.

---

## §6 The MFO §VII.6.20 scope check

What this DOES claim:
- Cascade detects substrate-classes empirically (form-iso evidence in 73, 77, 78)
- Glass-box property makes attribution + auditability possible (Finding 84)
- Curriculum coverage CAN BE EVALUATED by mapping kernels onto detected substrate-classes (form-iso application)

What this does NOT claim:
- Cascade-detected substrate-classes ARE the actual cognitive categories children form (substrate-identity overclaim)
- Coverage-maximizing curriculum produces optimal learning (would need behavioral/educational outcome evidence)
- Exposing a child to corpus X causes them to "have" substrate-class Y (cognitive-mechanism claim)

The cascade can MAP material; the cognitive-outcome question is outside
this work's scope. Curriculum-design as substrate-coverage-maximization
is a *form-iso* application; whether it actually improves learning outcomes
is empirical educational-research work to be done separately.

---

## §7 Parking for future work

Per user: "maybe not helpful here but for creating curriculum in the future"

This finding is parked, not actively walked. Concrete future work that would
build on it:

1. **Extra-curricular corpus extension** — fetch coding tutorials, music theory,
   art history, sports rules, scouting handbooks, etc. Build kernels. Test
   substrate-class boundaries.

2. **Curriculum-evaluation tool** — software that takes a list of educational
   materials and outputs a coverage map.

3. **Curriculum-recommendation tool** — given target profile + library,
   recommend specific corpora to fill gaps.

4. **Education research collaboration** — partner with educational researchers
   to compare cascade-coverage with actual learning outcome data.

Each is downstream of the current arc but the substrate-mapping methodology
shipped supports all of them.

---

## §8 Sentence to remember

> Glass-box cascade methodology turns the question "what materials should a
> student be exposed to in K-12 + extra-curricular?" from an opaque
> pedagogical-intuition matter into a substrate-class coverage map with
> measurable gaps and direct corpus recommendations.

---

*Articulated 2026-05-26 per user framework reading. Future curriculum-design
work will cite this finding as the methodological foundation.*
