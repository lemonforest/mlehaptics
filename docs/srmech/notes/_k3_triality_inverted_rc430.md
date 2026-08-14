# rc430 — the INVERTED k=3 triality: does the LENS carry the signal, or the TIER?

**Task** `#T1127` · **build** v0.9.0rc430 · **branch** `srmech-rc430` @ `302543f6b` ·
**adjudicated** 2026-08-13 · **registry** 655 · **ABI** 14 · numpy ABSENT · `SRMECH_EXPECT_PURE=1`

This note reports the EXPERIMENT (Job 2). The merged defect list (Job 1) is returned inline to the
orchestrator and is not duplicated here; only the findings-counts it produced are used below.

Round 1 (rc429) assigned the low tier to the fixture-PERMITTED arm. Round 2 (rc430) **inverted the
assignment on purpose**, so that lens and tier — confounded in round 1 — could be separated.

| round | forbidden-fixtures | scope-and-population | fixture-permitted |
|---|---|---|---|
| rc429 | sonnet → **6** | opus → **6** | haiku → **0** (and wrong on a pin) |
| rc430 | **haiku → 0** | **sonnet → 2** | **opus → 6** |

---

## H1 — LENS vs TIER. Verdict: **TIER DOMINATES.**

### Unique confirmed findings this round

Counted after independent adjudication; a finding counts only if the adjudicator reproduced it with
its own command. A finding seen by two reps is credited to both but counted once in the merged list.

| rep | lens | model | unique confirmed | of which CI-red |
|---|---|---|---|---|
| VECTOR (8v) | forbidden-fixtures | haiku | **0** | 0 |
| SPINOR (8s) | scope and population | sonnet | **2** | 0 |
| CONJUGATE (8c) | execution control, fixture-permitted | opus | **6** | 4 |

VECTOR returned an explicit `PASS (zero findings)`. SPINOR returned the `frame_probe` false negative
(confirmed) and an incompleteness in the shipped `cannot_express` blind-spot list (confirmed, soft).
CONJUGATE returned four CI-red failures, the `frame_probe` escape (shared with SPINOR, not
double-counted), a false measured number shipped inside the public C header, and the vacuity of the
rc's own two self-declared falsifiers.

### The two decisive comparisons the design was built to make

**Q1 — did haiku-under-forbidden-fixtures produce real findings?** **No. Zero.** The lens that
carried 6 findings for sonnet in round 1 carried 0 for haiku in round 2. Withholding the fixtures did
not manufacture scrutiny.

**Q2 — did opus-under-fixture-permission get misled the way haiku was in round 1?** **No — the
opposite.** CONJUGATE distrusted the fixtures, drove four of its own declaration mutations with
`git diff --numstat` proof-of-mutation before each run, and then **caught the shipped fixtures being
vacuous**: `test_every_false_scope_fails_the_ratchet` (F-1) computes
`passes = [s for s in FRAME_SCOPES if s != entry.frame_scope and s == measured]` while §2 has already
asserted `measured == entry.frame_scope`, so `passes` is empty **by construction** — the test cannot
return otherwise. `test_gate_fires_on_a_planted_defect` (F-2) advertises itself as "the LIVE gate
node, driven with an injected lie" but re-spells §2's assertion inline rather than driving the gate.
Both confirmed by reading `tests/test_frame_scope_rc430.py:455-496`.

### Read across both rounds, by MODEL rather than by lens

| model | round 1 (lens) | round 2 (lens) | findings |
|---|---|---|---|
| opus | scope → 6 | permitted → 6 | **high under both** |
| sonnet | forbidden → 6 | scope → 2 | **mid under both** |
| haiku | permitted → 0 | forbidden → 0 | **zero under both** |

Findings track the MODEL across a deliberate lens inversion. Round 1's apparent lens effect was
**confounded**: haiku's cell happened to be the permitted one, so "permitted arm produced nothing"
and "low tier produced nothing" were the same observation. Inverting separated them, and the tier
kept the signal while the lens did not.

**The premise of H1 is also partly reframed by Q2.** Fixture permission is not a hazard in itself; it
is a hazard *conditional on the reader not auditing the fixture*. Given to a rep that audits, the
fixtures became a **finding surface** rather than a trap — F-1 and F-2 were caught *because* that rep
was allowed to look at them. The forbidden-fixtures lens forecloses that.

**Residual lens signal, weak and unreplicated.** The only within-model lens contrast available is
sonnet: 6 (forbidden, rc429) → 2 (scope, rc430). It points weakly toward the forbidden lens helping
at mid tier, but the two rounds audit different builds of different difficulty, so build-difficulty
is uncontrolled and this contrast cannot be separated from it. Reported, not relied on.

---

## H2 — ORACLE-BACKED vs PRIOR-ONLY. Verdict: rc429's inversion **did NOT replicate — it reversed.**

Class A = A1-A3, independently checkable. Class B = B1-B2, prior-only as posed.

| | rc429 unanimity | rc430 unanimity | rc429 pairwise | rc430 pairwise |
|---|---|---|---|---|
| **Class A** (oracle-backed) | 33% | **100%** (3/3) | 56% | **100%** (9/9) |
| **Class B** (prior-only) | 50% | **0%** (0/2) | 67% | **33%** (2/6) |

rc429 showed *higher* agreement where nothing could be checked — the signature of a correlated prior
rather than convergent measurement. rc430 shows the **healthy** pattern instead: agreement is total
where an oracle exists and collapses where none does.

**Two rounds pointing opposite ways is not a trend, and the honest reading is that the rc429 signal
is now UNSUPPORTED as a stable property**, not that it has been overturned in the other direction.

Two qualifications, both against taking rc430's Class A 100% at face value:

- **The unanimity is CHEAP.** A3 (`ABI == 14`) is a `#define` greppable in both trees and stated in
  the artifact's own text; A2's `ZERO-INVENTED` follows from an ABSENCE (`git diff` adds **0** `P(`
  lines; `ToolParameter` untouched — adjudicator-confirmed) that costs one command to see.
- **The unanimity CONCEALED a defect.** All three agreed `AGREE-AT-14` and all three were right, but
  the sentence in the public header that *justifies* not bumping the ABI ships a false measured
  number — `offsetof(srmech_tool_entry_t, params)` "measured old 8, new 8", actually **32 on both**
  (adjudicator compiled `origin/main` and rc430 headers side by side: 32/32, `sizeof` 160→184).
  Two of three reps asserted the offsets were unchanged **without measuring**. A unanimous correct
  verdict sat directly on top of a shipped falsehood, and only the rep that compiled found it.

---

## H3 — DOES CREDITING ABSTENTION BREAK FALSE CONSENSUS? Verdict: **BOUNDED — the instruction barely took, and where it took it produced a LABEL split without a SUBSTANCE split.**

Every rep was told explicitly that UNDECIDABLE is first-class and would be scored as correct
behaviour on Class B without independent work.

| | abstentions | rate |
|---|---|---|
| Class A | 0 of 9 | 0% |
| Class B | **1 of 6** | 17% |
| overall | **1 of 15** | 6.7% (rc429: 0 of 15) |

**Did Class B agreement fall toward Class A?** Class B pairwise fell 67% → 33%. But Class A *rose*
56% → 100%, so B did not converge on A — the gap **inverted**, with B now far below A.

**The fall is not evidence the instruction worked.** Exactly one abstention was taken (VECTOR on B2),
and that single abstention is the whole of B2's split: SPINOR and CONJUGATE both answered
`DOES-NOT-EARN`, and VECTOR's own prose states *"The frame field alone does NOT make the census
decidable"* — which **is** the `DOES-NOT-EARN` answer — before labelling the verdict `UNDECIDABLE`.
Had it pinned what it had already written, B2 would have been **unanimous**. So the abstention credit
bought a hedge on a question where the three agreed in substance: it let a rep assert a conclusion and
then decline responsibility for the label.

**Did any rep abstain *and* name the work required?** VECTOR did — "would require independent census
re-run to verify" — which formally hits the target behaviour. But because it had already asserted the
conclusion, the abstention is **decorative**: structurally the same defect as F-2, a falsifier that
announces a check it does not perform. Target behaviour was met in form, not in function.

---

## Reps WRONG on a pinned question

Checked as claims, not by model label.

- **No rep is wrong on a pinned VERDICT.** A1/A2/A3 are correct as adjudicated; B1's split is a
  referent disagreement (below) and B2's substance is unanimous.
- **VECTOR reached A1 by testing the wrong verb.** Its stated route is four invalid *shapes*
  (invalid scope value, scope-without-axis, axis-without-scope, empty-axis-with-scope) rejected with
  `ToolSchemaValidationError` — that is the **registration type-validator**, not the behavioural
  ratchet A1 asks about. Right answer, wrong instrument; the gate that actually had to bite was never
  driven. Only CONJUGATE (4 mutations) and SPINOR (1) drove it.
- **VECTOR ships one refuted supporting claim on B1**: *"No vocabulary term is unused."* Measured by
  the adjudicator: of the 20 declarers, `frame_axis` is `modulus` **20 times and `generator` zero
  times**. `generator` is EMPTY, not merely rare.
- **VECTOR's A2 quoted comment is REAL, not fabricated.** The adjudicator's first grep returned 0 and
  appeared to convict it; the comment is line-wrapped across two source lines and occurs exactly
  **20** times. Recorded because the near-miss is the point: a single-line grep is an instrument that
  can return a false REFUTED.
- **CONJUGATE's B2 overlap number does not survive re-slicing.** It reported 2 of 20 declarers inside
  the census's decided set. Slicing on "any decided ladder bucket" instead gives **11 of 20**
  (adjudicator-measured). Its *conclusion* strengthens rather than weakens — all 11 land in
  `SEMIGROUP_NOT_GROUP`, the bucket the rc's own deferral memo says instrument v1 got **wrong**
  (`cyclic_mod_add` is provably a permutation and must read GROUP) — but the number itself is a
  presentation count, not an invariant. Counts are not sets.

---

## CORRELATED FAILURE — the third channel

rc429's correlated failure MOVED rather than vanished: channel 1 (both reps believing the shipped
fixtures) closed, and channel 2 opened (both reps believing the gate's own docstring about its
scope). The instruction was to look for a **third**.

**Channel 3: the ripple manifest treated as a complete map of the blast radius.**

All three reps deferred to `tools/ripple_check.py` / `tools/ripple_gates.txt` as the authority on what
this change could break.

- **SPINOR** measured the new surface — it reports `describe()` at **13 keys with `frames` new**,
  reproduced from a clean import — filed it under *"What PASSES"*, and never asked **what pins that
  key set**. Observing a surface change without searching for its pins is the whole failure.
- **VECTOR** did not examine the ripple question at all and returned zero findings.
- **CONJUGATE** partially escaped: it *read the manifest's comments*, found that `test_mcp.py` is
  excluded as a whole file with only three node IDs carved out, and correctly predicted a green sweep
  over a red CI. But having escaped the manifest's **green**, it then accepted the manifest's
  **universe** — it searched inside `test_mcp.py` and stopped there.

The adjudicator grepped for the key set instead of consulting the manifest and found **two further
CI-red failures in files the manifest never names**:

```
tests/test_describe_registry_pointer_rc407.py::test_top_level_key_set_is_untouched   FAILED
tests/test_domain_classes_rc298.py::test_describe_still_reports_the_rest_unchanged   FAILED
```

Neither file appears in `ripple_gates.txt`. So the true CI-red count for this rc is **6, not 4**, and
the two extra reds are the proof that channel 3 is real: every rep's model of the blast radius was
bounded by a curated coverage artifact, and the artifact is incomplete.

Channel 3 is a genuinely new kind. Channels 1 and 2 were **trusting a claim** (a fixture's, a
docstring's). Channel 3 is **trusting a curated map of where to look** — it does not assert anything
false, it merely omits, and omission survives every check that reads what is present.

---

## Classification

| hypothesis | verdict |
|---|---|
| **H1 LENS vs TIER** | **BOUNDED — TIER DOMINATES.** Both decisive comparisons point the same way under a deliberate inversion. Not REFUTED for the lens: a weak within-model contrast (sonnet 6→2) survives, confounded with build difficulty. |
| **H2 oracle-backed vs prior-only** | **UNSUPPORTED at n=2.** rc429's inversion did not replicate; it reversed. Two rounds pointing opposite ways is not a trend, and rc430's Class A unanimity is cheap and concealed a shipped falsehood. |
| **H3 crediting abstention** | **BOUNDED.** 1 of 15 abstentions, and that one is a label/substance mismatch. Class B agreement fell, but the fall is one rep's labelling on a question where substance agreed — not evidence that the false consensus was a format artifact. |
| **correlated failure** | **CONFIRMED, third channel identified** — the ripple manifest as an assumed-complete blast-radius map, evidenced by 2 CI-red failures outside it. |

**Scope bound.** n=1 build per cell, one task (`#T1127`), three reps, one model family — **including
the adjudicator**, which is the binding limitation: an adjudicator drawn from the same family shares
whatever prior it is measuring, and the two extra CI-reds it found were reachable by a grep any rep
could have run. Nothing here generalises past this build, this task shape, and this family without
replication on a build the adjudicator did not also audit.
