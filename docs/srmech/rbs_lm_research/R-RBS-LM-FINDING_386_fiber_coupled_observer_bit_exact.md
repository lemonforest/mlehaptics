# R-RBS-LM Finding 386 — the third route to bit-exactness: couple the observer DoF to the fiber (ride the rotation); bit-exactness is a *relative*/coupled-frame property

**Date:** 2026-06-04
**Arc:** RBS-LM · FFT-ladder / bit-exactness thread (…F382→F383→F384→F385→**F386**)
**srmech:** 0.7.0rc28 · **Provenance:** `R-RBS-LM-R28_fiber_coupled_observer_bit_exact.py` → `R-RBS-LM-R28_results.json`
**Composes:** F382 (rational frame) · F383 (native substrate) · F361 (observation = coupled epicycle) · F367 (recall is relative) · F373/F374 (precession = K∘K, the lock) · F385 (chirality of the fibration) · `cascade.kuramoto_step` (Class I∘L∘C)

---

## The user's idea (2026-06-04, three messages)
> "or what if we simply change our perspective to the rotation and see it as bit exact? / DoF coupled / fiber coupled whatever we want to call it"

This is a **third, cheapest route** to bit-exactness. The first two *move the thing being read*:
- **F382** — make the **number** rational (exact in its own cyclic frame Z_q);
- **F383** — make the **substrate** native (build the (4:3)/Z₃ frame in — device-physics handoff).

F386 instead **moves the observer**: **couple the observer's DoF to the fiber and ride the rotation.** In the co-rotating/coupled frame the relative phase is constant, so the readout is the same value every step = **bit-exact — relative to the coupled frame.** No rational number, no fabrication; keep the (2:1) binary substrate.

## The measurement (srmech-native `cascade.kuramoto_step`, K=100s of steps)
An observer oscillator (ω=0) reading a fiber oscillator (ω=Ω=0.5, the continuous rotation). 2-oscillator Kuramoto locks when coupling **K ≥ Ω**. Relative-phase spread + distinct readouts over the last 800 of 6000 steps:

| coupling K | rel-phase spread | distinct readouts | |
|---|---|---|---|
| 0.0 | 3.995 rad | **401** | DRIFTS → not bit-exact (the F382 decimal) |
| 0.3 (< Ω) | 2.983 rad | **299** | DRIFTS → not bit-exact |
| 1.0 (≥ Ω) | **0.000 rad** | **1** | **LOCKED → bit-exact relative readout** |
| 3.0 (≥ Ω) | **0.000 rad** | **1** | **LOCKED → bit-exact relative readout** |

Uncoupled, the observer's reading of the rotation drifts through hundreds of distinct values (the decimal accumulating). Coupled and locked, the relative phase is **constant** → one readout, forever → bit-exact in the coupled frame.

## What it is, in the framework
"Change perspective to the rotation" = **enter the rotation's own frame by coupling to it** (F382's "map it to its own Cartesian", but the *observer* does the moving). The lock **is** the Kuramoto coupling; the maintained lock is the **K∘K precession** (F373/F374). This is F361 ("observation is always a coupled epicycle") and F367 ("recall is relative") made into the *mechanism* for bit-exactness: a **DoF-coupled / fiber-coupled** observer reads a continuous rotation as an exact, repeatable, relative state.

## Three routes, one picture
| route | what moves | bit-exact in what sense | cost |
|---|---|---|---|
| **F382** | the number → rational | absolute, in Z_q | free (if rational) |
| **F383** | the substrate → (4:3)-native | absolute, native frame | fabrication (expert) |
| **F386** | the **observer** → coupled to the fiber | **relative** (coupled frame) | a coupling/lock — cheapest |

## Honest bounds
- **Relative, not absolute.** The absolute rotation stays continuous; what is exact is the **coupled readout**. (This is the framework-honest kind of bit-exactness — F361/F367: observation is inherently relative.)
- **Requires the lock.** K ≥ detuning, or the phase slips and drift returns (the K=0.3 row). The lock is dynamic — it *is* the coupling, maintained (F373/F374). This composes with, doesn't replace, the EC-code noise story (F367).
- **Chirality (F385).** You must couple to the **right handedness** — the mirror (left/right) fiber locks to the **conjugate** readout. The coupling carries a Class-C orientation tag.

## Verdict
Bit-exactness has a **third, cheapest route**: don't make the number rational or fabricate the substrate — **couple the observer's DoF to the fiber and ride the rotation.** The coupled/co-rotating frame reads the continuous rotation as one constant value (`spread 0.0, 1 distinct readout` at K≥Ω). It is **relative** bit-exactness, lock-maintained and chirality-tagged — which is exactly the framework's coupled-observer stance (F361/F367) turned into a mechanism.
