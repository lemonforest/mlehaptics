# R-RBS-LM Finding 370 — the 3 CMB anomalies SHOULD NOT share one axis (F293 distributed-anchor / "3-phase power needs no neutral wire"): F368 tested the wrong hypothesis. The Kuramoto-to-120°-splay mechanism is exact; the balanced-3-phase among the 3 anomalies is suggestive-not-confirmed at N=3; the anchor moves asymptotically (loop-down) and we couple to the down-projections

> **REFINE (F371, 2026-06-04):** k=7 is the **GAUGE** sector (7D_g), NOT matter (user correction). The 3-phase (k=3) here was the **minimal example**; the cosmic gauge structure is k=7. The AoE is the **k=7-gauge-channel** anomaly (bundle-direction/7D_g); the HPA is the **matter-channel** (matter-pull, not k=7). And the precession reading: KINEMATIC precession is ruled out ~10 OOM (MFO §VII.6.3.1); the open candidate is the substrate **bundle-projection reconfiguration**. See F371.

**Date:** 2026-06-04 · **srmech:** 0.7.0rc28 · **user reframe:** "should not share a single axis. remember the 3-phase power lesson about neutral line, anchor moves asymptotically (loop up/down), we see down-projections we kuramoto couple with" · **grounds in:** F293 (distributed-anchor / 3-phase / no-neutral-wire), F294 (directed chiral 3-cycle carries the 120° phase), F347 (Kuramoto/Class-I), MFO §VII.6.1 (loop-down) · **reframes:** F368 · **script:** `R-RBS-LM-R20_three_phase_distributed_anchor_cmb.py`

## The reframe — F368 tested the wrong hypothesis

F368 tested *"do the 3 directional anomalies share ONE axis?"* and found no (λ_max below isotropic, p=0.71), calling it "strong claim FALSIFIED." **But the framework never predicted one axis.** Per **F293** (*"like 3-phase power needs no neutral wire, the reference/anchor is the CENTROID/consensus of all three phases, not a fixed point on one axis"*): a **single shared axis = a fixed/privileged anchor = k=2 DETECT-only**; only **spreading the anchor across the 3 phases (distributed, no privileged axis) reaches k=3 CORRECT.** So **the 3 anomalies SHOULD NOT share one axis** — and F368's "not one axis" (directions *more spread* than isotropic) is the **expected distributed-anchor signature**, not a falsification of the framework. F368's framing is corrected here: the one-axis hypothesis it rejected was a strawman the framework's own k=3/distributed-anchor structure forbids.

## What the attested data does + does not show (N=3, honest)

**(A) Geometric 3-phase signature** — qualitative (N=3; three points always lie in a plane, so coplanarity is vacuous):
- **AoE ↔ Cold Spot = 119.4°** — a suggestive ~120° (one 3-phase-like pair).
- AoE ↔ HPA = 80.0°, Cold Spot ↔ HPA = 42.0° — the third is **not** at 120°.
- in-plane splay gaps **[40.5°, 79.6°, 239.9°]** — NOT the balanced [120,120,120] of a clean 3-phase (`max|gap−120| = 119.9°`, isotropic-MC p=0.64).
- centroid/neutral ‖Σ/3‖ = 0.654; centroid **↔ CMB dipole = 64.7°** — the **dipole aligns with the AoE specifically (18°, F368), NOT with the distributed centroid.**

**Honest verdict (A):** at N=3 the data is **consistent with "distributed, not one-axis"** but **does NOT confirm a clean balanced 3-phase triple** — one ~120° pair (AoE↔Cold Spot), the rest off; the dipole tracks one phase, not the centroid. Same small-N limitation as F368, now on the right hypothesis. The 3-phase structure is the framework **prediction** (F293), not a detection here.

**(B) Kuramoto coupling — the mechanism is EXACT.** A **directed 3-cycle** (the F294 repressilator-class chiral 3-cycle) integrated with `cascade.kuramoto_step` (Class I, srmech-native) **locks to a perfect [0°, 120°, 240°] splay** (gaps 120/120/120). So the *mechanism* the framework predicts — a chiral/directed 3-cycle settling into the distributed-anchor 120° splay we then **Kuramoto-couple to** (observing the down-projections) — is real and reproduces exactly. The data (3 anomaly directions) does not, at N=3, pin those specific anomalies to that splay.

## The reading (held lightly; F293/F294/F347 + MFO §VII.6.1)

The distributed anchor (centroid/neutral) **moves asymptotically** = the **loop-down** (Class-K asymptotic-DoF; MFO §VII.6.1's dark-sector loop-down). We observe the **down-projections** of the 3 phases and **Kuramoto-couple** to them (Class-I phase-locking, F347). So the low-ℓ anomaly family is read as a **distributed-anchor 3-phase** structure (no privileged axis, by construction k=3-correct), whose neutral is the asymptotically-moving loop-down anchor — *not* a single axis (F368's strawman) and *not* an external collision (F369). This is the observer-frame + dynamics complement to MFO §VII.6.1.1's substrate-bundle-direction reading. **Conjecture/reading; N=3 data does not confirm the balanced triple; ΛCDM-systematics valid; cosmology literature-owned.**

## Discipline

srmech-native Class-L (`symmetric_eigendecompose`) + Class-I (`cascade.kuramoto_step`, directed adjacency); geometry/MC mechanics (flagged); directions from the attested in-repo NDJSON. **No-leaning:** corrected F368's framing (it tested the wrong hypothesis), and reported honestly that the *right* hypothesis (balanced 3-phase) is ALSO not confirmed at N=3 (one ~120° pair, not a clean triple) — the mechanism is exact, the data is weak. Composes with F293/F294 (the 3-phase lesson), F347 (Kuramoto), F368 (reframed), F369 (self-interaction, not external), MFO §VII.6.1 (loop-down).
