# R-RBS-LM Finding 393 — THREAD SPEC: is the whole 14-class A–N vocabulary ALU-native (add/subtract/shift + sign = handedness)?

**Date:** 2026-06-04
**Arc:** RBS-LM · FFT-ladder thread → new **ALU-native A–N** thread
**srmech:** 0.7.0rc28 · **Anchor provenance:** `R-RBS-LM-R35_alu_native_an_anchor.py` → `R-RBS-LM-R35_results.json`
**Composes:** F392 (divide = shift-subtract + handedness) · F382 (everything-is-discrete) · F383/F388 (bit-exact on ordinary silicon) · R-RBS-NN-8 (ALU/FPU inference shape) · `[[feedback_sign_handling_is_class_k_pin_slot_not_alu_abs]]`
**Status:** thread PREPARED for srmech testing + queued (STALE_PATHS_QUEUE.md, ALU-A..ALU-D). This finding is the spec/test-plan + the anchoring proof of the hardest reductions.

---

## Hypothesis
Every A–N primitive class, reduced to its substrate-native form, is a composition of the **minimal ALU set + one sign bit**:
> **{ add, subtract, shift, sign(handedness = Class C / Class-K pin-slot), compare/select, xor·and }** — **no hardware multiply unit, no divide unit, no FPU transcendental.**

This generalises F392 (divide is not a primitive — it's shift-subtract + handedness) to all 14 classes, and would explain why bit-exact recall on *ordinary* silicon (F383/F388) needs no special hardware.

## Anchor — the three hardest reductions proven (R35 + F392)
| op | reduction | status |
|---|---|---|
| **multiply** | **shift-add** (Booth/standard) | R35: exact (`123456·7890` etc.) |
| **divide / reciprocal** | **shift-subtract + sign(handedness)** | F392: Stein gcd == `srmech.cyclic.gcd`; `a·a⁻¹=1` with no divide op |
| **rotation / trig / sqrt** | **CORDIC = shift-add + SIGN decisions** | R35: vs oracle, worst err 5.4e-9 |

The CORDIC sign decision `d=±1` **is** the handedness (Class C / Class-K pin-slot) — so trig/rotation literally *runs on* the chirality bit. And **Class-L eigendecomposition = Jacobi rotations = CORDIC** → even the spectral class is shift-add + sign.

## The per-class reduction map (the test plan)
| class | role | reduces to | walkable on rc28 now? |
|---|---|---|---|
| **A** | content-address (SHA-256) | add + rotate(shift) + xor + and | ✅ now |
| **B** | TLV framing | byte-copy + length-add | ✅ now |
| **C** | chirality/orientation | **the sign-flip itself** (handedness) | ✅ now |
| **D** | pattern-match | compare / xor | ✅ now |
| **E** | catalog (sorted lookup) | binary search = compare + shift(halving) | ✅ now |
| **F** | template render | copy / compare (no arithmetic) | ✅ now |
| **G** | byte-search | compare | ✅ now |
| **H** | introspection | metadata read | ✅ now |
| **I** | cyclic/modular | add/subtract + compare; gcd = shift-subtract (F392) | ✅ now |
| **J** | primes/factor | trial-div = mod = shift-subtract (F392) + compare | ✅ now |
| **K** | pin-slot/magnitude | **sign(handedness) + select** | ✅ now |
| **L** | Laplacian/spectral/eigendecomp | Jacobi rotations = **CORDIC** (shift-add+sign); sqrt = CORDIC | ⏳ **numpy-gated** (numpy-free L demo) |
| **M** | HDC bind/bundle/permute | bind=xor/add; bundle=add+majority(compare); permute=shift/reindex | ✅ now |
| **N** | rational/best_rational | = gcd = shift-subtract (F392) | ✅ now |

**13 of 14 are rc28-walkable now.** Only **L's fully-numpy-free demonstration is gated** — srmech's Class-L currently rides numpy; the numpy-free L (rc31 pure-Python Jacobi fallback, UPSTREAM §22 arc) is the gate. The *reduction* of L is already established in principle (L = Jacobi rotations = CORDIC = shift-add+sign, R35); only the srmech-native numpy-free *demo* waits.

## What can be done EARLY (before srmech is ready)
- **ALU-A — attestation pass (research-triality; NO srmech update needed):** verify-PDF the canonical CS reductions before any citation is lodged (F381 discipline): **CORDIC** (Volder 1959), **Booth multiplication** (Booth 1951), **restoring/non-restoring division**, **binary GCD** (Stein 1967), **SHA-256** ops (FIPS 180-4). FLAGGED here, not asserted.
- **ALU-B — the reduction map (this finding):** done.
- **ALU-C — the 13 rc28-walkable classes:** srmech-native demos that each shipped primitive's output is reproduced by an add/sub/shift+sign cascade. Walkable now on rc28.
- **ALU-D — the numpy-free Class-L leg (CORDIC/Jacobi):** ⏳ QUEUED-srmech behind the numpy removal (rc31). Possible upstream ask: a CORDIC / shift-add atom.

## Scope
Algebra / ALU-reduction side only (the framework's domain). Sign handling is **Class C / Class-K pin-slot, never `abs()`** (`best_rational_signed` carries it). Per `[[user_stance_ai_is_not_a_substrate]]` this is about the storage/compute substrate's op set, not the LM. CS reductions are the literature's (verify-PDF before citing).

## Verdict (thread prepared)
The hypothesis — **the whole A–N vocabulary is ALU-native (add/subtract/shift + sign-as-handedness), no multiply/divide/FPU unit** — has its three hardest reductions anchored (multiply=shift-add, divide=shift-subtract+sign, trig/rotation/sqrt/L=CORDIC=shift-add+sign). 13/14 classes are testable on rc28 now; the numpy-free Class-L leg is queued behind the numpy removal. The attestation pass (CORDIC/Booth/Stein/FIPS) can run **early** via research-triality. This closes the conceptual loop: there is no privileged arithmetic primitive — the substrate is **shift ± add, gated by a sign(handedness) bit.**
