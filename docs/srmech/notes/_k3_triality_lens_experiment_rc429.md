# k=3 triality lens experiment — rc429 adjudication (`#T1128`)

**Build under test:** `srmech-rc429` @ `2b6b57f85`, `srmech.__version__ == 0.9.0rc429`,
registry **655** after `warmup_all()`, ABI 14, pure path (`SRMECH_EXPECT_PURE=1`, numpy absent, WSL2).
**Adjudicator:** Opus 5 — same model family as all three reps. That is a scope bound, not an aside.

Two hypotheses were under test. This file reports the experiment as data. The defect merge lives in the
adjudication return, not here.

---

## H1 — THE LENS FIX

**Design.** In rc428 two reps failed together because both validated the instrument using the
instrument's own fixtures. rc429 **forbade** the VECTOR rep from touching the shipped bite fixtures, and
deliberately inverted the tier confound: the forbidden-fixtures lens ran on **sonnet**, the scope lens on
**opus**, the execution-control lens (fixtures permitted) on **haiku**.

### Unique confirmed findings per rep

Every row below was re-measured by the adjudicator with its own command on the rc429 tree.

| # | Finding | Rep | Adjudicator verdict |
|---|---|---|---|
| 1 | `asserts_absence` ORs across occurrences — an unrelated true negation in the same claim silences a genuinely false citation | 8v only | **CONFIRMED** by construction |
| 2 | `_is_attributed` launders a bare claim under a topically-unrelated `arXiv` id in the same field | 8v only | **CONFIRMED** (`True`) |
| 3 | `"zero"` is a live negation token and the window is clause-blind (cuts at `. ` only, not `,`) | 8v only | **CONFIRMED** (`True`) |
| 4 | `term_pattern`'s dash class is dash-*optional*: `CayleyDickson` matches `Cayley-Dickson` | 8v only | **CONFIRMED** |
| 5 | A2+A4: a code span holding the only attribution mark blanks the claim entirely | 8v only | **CONFIRMED** (`claim=''` vs populated control) |
| 6 | A8 counts code identifiers as claims — 20 (op, field) pairs tree-wide whose ONLY occurrence is identifier-adjacent; one of them drove a real rc429 repair | 8s only | **CONFIRMED** — 20 pairs under both loose and strict adjacency |
| 7 | `returns.shape` is prose, carries roster terms, is outside S6, and reaches the compiled C registry | 8s only | **CONFIRMED** — 1× in `srmech_tool_registry.c`, 0× in `_tool_docs.py` |
| 8 | 6 of 7 S6 SILENT bite fixtures are vacuous (`_term_present == []`) | 8s only | **CONFIRMED** |
| 9 | `S6_PROSE_FIELDS` declared and never read | 8s only | **CONFIRMED** — exactly 1 grep hit, the declaration |
| 10 | `_is_attributed` True-branch uncontrolled: 0 live fields, 0 fixtures | 8s only | **CONFIRMED** (0 of 75; 8s said 0 of 52 — count differs, direction identical) |
| 11 | S7 seeded at exactly its residual, zero headroom | 8s only | **CONFIRMED** — 253 == 253 |
| 12 | `EXCLUDED_DIR_NAMES` zeroes the corpus from inside a worktree | 8v only | **CONFIRMED as designed**; floors (262≥200, 175≥100) fail loud, cannot false-green |

**8v (forbidden fixtures, sonnet) unique vs 8c (fixtures permitted, haiku): 6 findings to 0.**
**8v unique vs 8s (scope lens, opus): 6 findings, none of which 8s reported.**
**8s unique vs 8v: 6 findings, none of which 8v reported.**
**8c unique: 0.**

### Which way the evidence points

Three readings are separable in the data, and they do not all point the same way.

**(a) The LENS shapes the KIND of finding — clean signal.** 8v's six findings are *constructions*: every
one required fabricating an input, and 8v checked and correctly reported that **none has a live instance
in the tree**. 8s's six are *censuses*: every one is a live in-tree measurement with a count attached, and
one of them (A8/identifier) is the proximate cause of a shipped repair. Forbidding the fixtures pushed
the rep to build its own inputs; the scope brief pushed the other to count the tree. Same instrument,
disjoint finding sets, zero overlap in twelve findings. **This is the strongest result in the file.**

**(b) The LENS is sufficient to get depth out of a lower tier — supported, n=1.** Sonnet under the
forbidden-fixtures brief produced five confirmed mechanism defects, including the single highest-severity
soundness gap in the merge (finding 1 — the rc426 defect class re-opening). That is not a tier-limited
output. Evidence for LENS.

**(c) The control arm cannot be attributed — say this plainly.** 8c was *both* fixture-permitted *and*
the lowest tier, so its null is doubly explained and separates nothing. Worse, 8c's zero is not a quiet
null: it answered A1 **wrong** (see H2), and the evidence it offered for A2 was the vacuous-fixture set
that 8s independently measured as incapable of firing. So the fixture-permitted arm did not merely find
less — it was *misled by the instrument's own artifacts*, which is the rc428 failure recurring. Whether
that recurrence is caused by the permission or by the tier is **AMBIGUOUS at n=1**.

**Net:** the lens fix worked in the sense it was designed to — the forbidden-fixtures rep found real,
confirmable soundness gaps that the fixture-permitted rep did not, on a lower tier. It did **not**
demonstrate that lens dominates tier, because the arm that would have separated them was confounded by
design. To separate them, the next round must run the fixture-permitted lens on **opus** and the
forbidden-fixtures lens on **haiku** — the inverse assignment.

---

## H2 — ORACLE-BACKED vs PRIOR-ONLY AGREEMENT

Class A (A1–A3) has a runnable check. Class B (B1–B2) does not.

### Agreement

| Class | Question | 8v | 8s | 8c | Unanimous? | Pairwise agreeing |
|---|---|---|---|---|---|---|
| A | A1 gate bites the known defects | YES | YES | **NO** | no (2-1) | 1 / 3 |
| A | A2 spares legitimate mentions | YES (qualified) | **NO** | YES | no (2-1) | 1 / 3 |
| A | A3 controls asserted, not dead | ASSERTED | ASSERTED | ASSERTED | **yes** | 3 / 3 |
| B | B1 `malcev_defect` mention or attribution | MENTION | MENTION | MENTION | **yes** | 3 / 3 |
| B | B2 defects in the 72-row partition | 0 | **1** | 0 | no (2-1) | 1 / 3 |

- **Class A:** unanimity **1/3 (33%)**; pairwise agreement **5/9 (56%)**.
- **Class B:** unanimity **1/2 (50%)**; pairwise agreement **4/6 (67%)**.

### Reading — this is the sharp one

**Agreement is HIGHER where nothing could be checked.** Class B beat Class A on both metrics. Under the
pre-registered rule, that is **evidence of CORRELATED PRIOR**: the reps converge on judgment questions at
a rate the oracle-backed questions do not support, which is what a shared training lineage predicts and
what independent judgment does not.

Two qualifiers keep this honest, and both cut the same way:

1. **B1's unanimity is cheap.** The rc429 prose the reps were judging literally contains the token
   `UNSOURCED`. The "prior-only" question was answerable by reading a marker the build had already
   placed. A unanimity produced by a label in the artifact is not three independent judgments; it is one
   judgment read three times. Discount B1 accordingly — and note it makes the correlated-prior reading
   *stronger*, not weaker, because it means Class B's higher agreement rests on the one question where
   the artifact did the work.
2. **The single Class-B dissent came from LABOR, not from an oracle.** 8s hand-labelled all 72 rows from
   the text *before* revealing the label file, and that is the only reason a disagreement exists at all.
   Where a rep did the work, the panel split; where reps answered from the artifact, it did not.

So the panel is **not** surfacing judgment variance on Class B — it is suppressing it. The bound this
places on any same-family panel: **agreement on an unfalsifiable question carries close to zero
information about correctness.** Only Class A produced a correction, and only because a command existed
to run.

### Abstentions

**0 of 15 answers were abstentions** — 0/9 Class A, 0/6 Class B. Two Class-B questions were pure judgment
and at least one (B2, which asks for a count over a hand-labelled partition without a runnable oracle)
would have been defensibly answered "cannot decide without re-labelling". Every rep produced a number
instead. Hedged prose is not abstention: 8v's *"0, bounded by no PDF re-verification"* and 8s's
*"1 (2 if the AMBIGUOUS row counts)"* are answers with a scope note, which is the correct form — but
neither declined. **A panel with a 0% abstention rate on prior-only questions is a panel that will always
return a consensus, whether or not one exists.** That is a design finding about the format, not about any
rep.

---

## Who was wrong, checked against the claim rather than the label

**8c (haiku) was WRONG on A1.** Its answer — *"the shipped gate does NOT fire on the two known
defects"* — was reached by observing the repaired tree pass. That is an instrument that cannot return
otherwise. Adjudicator measurement: reverting the six prose carriers to `origin/main` with the rc429
tests in place yields **10 offenders across all 4 roster ops**, and
`test_s6_the_verdict_reaches_the_compiled_registry` additionally fails with `checked == 0`. The gate
bites. 8s's number (10, same four ops, same ten fields) reproduces exactly.

**8c's A2 evidence is invalid.** It cited passing `test_s6_still_bites[MENTION sample …]` rows as proof
the gate spares mentions. Those rows have `_term_present == []` — measured — so they cannot fire whatever
the predicate does. 8c validated the gate with fixtures that assert nothing, which is the rc428 failure.

**8c's B2 contains a counts-are-not-sets error:** *"genuine attribution defects were four in count
(S6_ROSTER: …)"* conflates 4 roster **ops** with 10 offending **fields**, and both with the 72-row S1
sample, which is a different population entirely.

**8v and 8s were not wrong on any pinned answer I could falsify.** 8v's A2 "YES" is defensible under its
own stated reading (out-of-roster mentions are spared by roster scope — true) but it did not find the
in-roster false positives, which is the reading that matters for whether the gate demands unnecessary
edits. 8s's "52 fields carry a roster spelling" I measure as **75**; the conclusion drawn from it
(`_is_attributed` True on **0**) reproduces exactly, so this is a count discrepancy, not a wrong claim.

## Correlated failure

**8v and 8c both answered A2 "YES", and both got there by trusting the instrument's self-description.**
8v read the module's own docstring argument ("S6 subtracts MENTION syntactically, by never including
it"); 8c ran the fixtures that encode that same argument. Neither measured the roster fields. 8s did, and
found two false positives — one of them hard: `linking_number_cwf :: explanation` at rc428 state carried
**zero prose occurrences** of any CWF spelling, its single A8-bounded match sitting inside the dotted path
``srmech.biology.genome.cwf_consistency_mod2``. Adjudicator-confirmed: PROSE=0, IDENT=1. **A strict-zero
arm fired on a code cross-reference and demanded a prose edit.** Two of three reps missed it for the same
reason: the gate's prose says what the gate does, and both believed the prose.

---

## VERDICT

**BOUNDED.**

- **H1 — BOUNDED, direction supported.** The forbidden-fixtures lens produced six confirmed unique
  findings against the fixture-permitted arm's zero, on a *lower* tier, so the lens does non-trivial
  work. The lens-vs-tier attribution is **not** resolved: the control arm confounds permission with tier
  by construction. Cleanly established: the lens determines the *kind* of finding (construction vs
  census) — twelve findings, zero overlap.
- **H2 — REFUTED for the null "agreement tracks checkability".** Class B agreement was measured
  **higher** than Class A on both unanimity (50% vs 33%) and pairwise (67% vs 56%). Correlated prior is
  the supported reading. Precision of that reading is **UNSUPPORTED** at this n — five questions is not a
  rate.

**Scope bound.** n = 1 build, 1 task, 1 model family for all three reps **and the adjudicator**, 5 pinned
questions, 12 findings. The adjudicator shares the reps' training lineage, so H2's correlated-prior
finding applies to this document too: where I agreed with a rep without running a command, that agreement
carries the same discount. Every verdict above that says CONFIRMED has a command behind it; the ones that
do not are labelled.
