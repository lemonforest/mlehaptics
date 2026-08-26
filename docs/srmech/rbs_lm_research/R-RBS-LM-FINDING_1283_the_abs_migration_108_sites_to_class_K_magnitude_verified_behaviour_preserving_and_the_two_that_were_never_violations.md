# F1283 — **the `abs()` migration: 108 sites → Class-K `cascade.magnitude`, `abs()` HARD now ZERO** (142 → 31 total). Verified **byte-identical output on all 11 migrated probes that run**. Two sites were **never violations** — `|z|` of a complex value is a Euclidean modulus, a *different* cascade class. And it took **three attempts**, each caught by running the probes rather than by any static check.

**User direction (2026-07-21):** *"do the 110 abs() migration on the historical probes anyway. establish the pattern that math must come from srmech and when we found it doesn't, that we correct it."*

This **overrides** the standing preserve-probes discipline (F1260/F1276) for `abs()` specifically, and the reasoning is sound: **the corpus should demonstrate the discipline, not document its violation.** Recorded as a deliberate override, not a drift.

## What the equivalence actually is — checked before rewriting anything
| input | `abs()` | `cascade.magnitude()` | |
|---|---|---|---|
| ints, floats, `Fraction`/`Q`, ±inf | same | same | safe |
| `0` (int) | `0` | **`0.0`** | **type** changes |
| **`nan`** | `nan` | **`0.0`** | **VALUE changes — NaN swallowed** |
| `complex` | modulus | **rejects (TypeError)** | different class, by contract |

**A blanket rewrite is not unconditionally safe**, which is why this was established first rather than discovered later.

## Result
| | before | after |
|---|---|---|
| `abs()` HARD | 110 | **0** |
| total HARD | 142 | **31** |
| remaining | — | `hash()` 25, `hashlib.sha256` 2, `np.linalg.*` 4 |

- **108 migrated** — 45 files given a new import, 15 reusing an existing one, **2 aliased** to `srmech_magnitude` because the file already binds the name `cascade`
- **2 marked `srmech-allow`** — `abs(z)` where `z = ⟨e^{iθ}⟩`, **the Kuramoto order parameter**. That is `|z|` of a *complex* value: a Euclidean modulus, which srmech explicitly defines as a different cascade class and `magnitude` rejects by contract. **These were never violations — the checker mis-flags them**, and marking is the correct outcome, not migration.

## Three attempts, each defect caught by *running* the probes
1. **Naive col_offset rewrite** → f-string positions (PEP 701) don't land where assumed. An assertion stopped it before corruption; caught.
2. **Name collision + missing import** → `cascade` is a *local list* in one probe, so `cascade.magnitude` became `list.magnitude` → `AttributeError`. Another file got the call but no import. **5 of 11 probes differed.**
3. **Alias-blind import detection** → `from srmech.amsc import laplacian as L, cascade as C` **contains the word "cascade" but binds `C`**. My regex saw the word, skipped the import, and produced a `NameError`. Fixed by determining the binding **from the AST**, never from the import line's text.

**Every one of these passed the static check that preceded it.** What caught them was executing the probes and diffing output — the same lesson as F1273's control B and F1276's false-pass guard, arriving a third time: *a check that never runs the thing cannot tell you the thing works.*

## Verification, with its limits stated
- **11/11 runnable probes: byte-identical output** (after normalising the harness's own directory out of one probe that prints its output path)
- **52 of the 63 changed files could NOT be run here** — they need numpy (removed at #564) or an uncommitted `/home/skirklan/...` corpus (#1454 §3). For those the guarantee is: AST-precise rewriting, an AST check that **every callee is import-bound**, and all-files-parse. **That is strong, and it is not execution.**
- **Residual risk, stated rather than buried:** `cascade.magnitude(nan) = 0.0` where `abs(nan) = nan`. A NaN reaching a migrated site would be **silently swallowed into a passing-looking 0.0**. No migrated site was observed to carry NaN, but 52 files were not run.

*Also noted en route:* `R-RBS-LM-FINDING_943_*.py` **does not parse** — and did not parse before this work either (verified against `HEAD`; I never touched it). A file that doesn't parse is **invisible to the ratchet**, which independently corroborates #1454 §3.

## The pattern this establishes
**When math is found not coming from srmech, it gets corrected — and the correction gets verified, not assumed.** The corollary matters as much: **not every flag is a violation.** Two of the 110 were the checker being wrong about a genuinely different operation, and the honest response was to mark and explain, not to force a migration that `magnitude` would have rejected anyway.

Composes **F1281** (which froze this debt; now largely paid), **F1276/F1260** (preserve-probes, here deliberately overridden by user direction), **F1273** (control-B discipline), `[[feedback_sign_handling_is_class_k_pin_slot_not_alu_abs]]`, issue **#1454** §3.
