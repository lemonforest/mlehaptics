# R-RBS-LM-73 ADDENDUM — Coverage discipline correction

**Status:** CORRECTION (no code change; claim refinement)
**Predecessor commit:** `62d778fd` (R-RBS-LM-73 — McGuffey grade ladder ASYMPTOTIC claim)
**Date:** 2026-05-26
**Correction trigger:** User pointed out that I claimed "asymptotically-organized
substrate-content ladder" without testing the upper bound. McGuffey tops at Grade 6;
no high-school or college material was included in the test.

---

## §1 The claim that was over-stated

The 73 verdict text and commit message used the word **"asymptotically-organized"**:

> "Finding 73: McGuffey Eclectic Readers form an asymptotically-organized
> substrate-content ladder of English structural complexity."

"Asymptotic" implies convergence — that adding more material at the upper end
would not significantly change the substrate. **We did not test this.**

The McGuffey Sixth Reader is the END of the McGuffey series, but in modern
pedagogical terms it's roughly middle-school-equivalent. A true "asymptotic"
ladder claim would require testing whether high-school grammar texts, college
composition, graduate academic writing, and specialty/technical material *continue*
the structural progression or break it.

---

## §2 What the test actually showed

The 73 test confirmed:

- Pairwise alignment decreases **monotonically** with grade-distance across
  Primer → Grade 6 (mean alignment 0.25 at d=1 → 0.09 at d=6)
- Top-K eigvec content visibly progresses through grades (sight-words →
  auxiliary verbs → pronouns → modal verbs → relative pronouns → literary
  prepositional phrases)
- Spelling Book is structurally distant from all reading-substrate grades
  (different educational substrate; cascade correctly detected)

This is a *valid finding about the McGuffey corpus* — but it's a finding about
a 6-grade ladder, not an asymptote.

---

## §3 The corrected claim

**Finding 73 (corrected):**

> McGuffey Eclectic Readers (Primer through Grade 6) form a **monotone-ordered**
> substrate-content ladder of English structural complexity. Pairwise alignment
> decreases monotonically with grade-distance over the tested range (Primer →
> Grade 6). Whether this ladder continues monotonically into high-school grammar
> instruction, college composition, or specialty/technical English has not been
> tested by this work.

Key changes:
- "asymptotically-organized" → "monotone-ordered over the tested range"
- Explicit acknowledgment that upper-bound was not tested

---

## §4 The discipline correction (user's broader point)

The user's framing:

> "I meant grade ordered so that we can create a structure for building a
> language lexicon, to make sure we grab all the materials. wish should have
> also identified missing college level material"

**Grade-ordering as corpus-construction discipline:** we systematically grab
material at each level so we don't miss coverage. Failure to check the upper
bound is a coverage failure.

What the discipline requires:
1. **Enumerate the structural levels** of the substrate (Pre-K → Primary → Middle
   → High School → Undergraduate → Graduate → Specialty)
2. **Identify representative open-access material** at each level
3. **Note coverage gaps explicitly** when material is unavailable
4. **Refine claims** to match actual coverage

The "asymptotic" claim violated step 4 — we made a convergence claim without
satisfying step 3 at the upper end.

---

## §5 The corpus extension (R-RBS-LM-77 candidate)

Materials staged for testing whether the ladder extends:

| Source | Approximate level | Substrate kind |
|---|---|---|
| McGuffey Primer | Pre-K | Reading material |
| McGuffey Grades 1-6 | Elementary | Reading material |
| **Kirkham "English Grammar in Familiar Lectures" (1829)** | Adult comprehensive | **Grammar instruction** |
| **Kittredge & Farley "An Advanced English Grammar" (1913)** | Late-elementary to high school | **Grammar instruction** |
| **Strunk "Elements of Style" (1918)** | College freshman composition | **Composition instruction** |

Important substrate-kind distinction: McGuffey is *reading material* (text for
children to read); Kirkham/Kittredge/Strunk are *language instruction* (rules
ABOUT language). These are qualitatively different substrate-content kinds. The
cascade may not extend cleanly between them.

R-RBS-LM-77 will test:
1. **Does the McGuffey ladder extend** structurally to Kittredge → Strunk?
2. **Or does grammar-instruction split off** into a separate substrate-class
   from reading-material?

Both findings would be valuable. Finding 1 would confirm a broader ladder.
Finding 2 would reveal that "asymptotically-accurate English language rules"
substrate is QUALITATIVELY DIFFERENT from "graded English reading material"
substrate — a substrate-kind distinction we haven't articulated yet.

---

## §6 Coverage gaps still open

Even with the extension, the corpus is incomplete:

| Level | Status |
|---|---|
| Pre-K phonics / alphabet | McGuffey Primer (have) |
| Elementary reading | McGuffey Grades 1-6 (have) |
| Middle school reading | **GAP** — no dedicated middle-school readers |
| High school literature | Partial — covered indirectly by religious / literary corpora in 53 arc |
| High school grammar | Kittredge & Farley (have; covers 7th-grade reading-ease to high school) |
| College freshman composition | Strunk (have) |
| College advanced English | **GAP** — would benefit from a rhetoric textbook |
| Graduate academic writing | **GAP** — no academic-discourse corpus |
| Specialty/technical | **GAP** — code corpus exists (52d codeparrot) but science/legal/medical missing |

The corpus is not complete. The methodology requires acknowledging this and
continuing to extend coverage as material becomes available.

---

## §7 Net effect

- 73 finding stays empirically valid — it accurately describes a monotone-
  ordered ladder over Primer→Grade 6
- The framing "asymptotic" is over-stated; corrected to "monotone-ordered
  over the tested range"
- A discipline gap was identified: corpus-construction should explicitly
  enumerate coverage levels and flag what's missing
- R-RBS-LM-77 candidate stages the corpus extension to test whether the
  ladder continues or qualitatively shifts at higher levels
- Coverage remains incomplete; partition-by-partition extension continues

The empirical findings stand; the framing tightens; the discipline
gets explicit.

---

*Correction lodged 2026-05-26 per user coverage-discipline framework reading.*
