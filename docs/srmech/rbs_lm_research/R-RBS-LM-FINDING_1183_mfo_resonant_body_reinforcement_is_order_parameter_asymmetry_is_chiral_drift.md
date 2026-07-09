# F1183 (#243) (the MFO resonant-BODY probe, srmech-native — a multi-mode resonant body (coupled Kuramoto oscillators via `srmech.amsc.cascade.kuramoto_step`) makes the two halves of the "resonant asymmetric wave" MEASURABLE and physical: (A) the **reinforcement** = the Kuramoto **order parameter r** (phase-coherence) rises through a synchronization transition as coupling grows (0.88→0.95→0.98→0.99) — F1179's *harmonic reinforcement* made continuous and physical: the body LOCKS = reinforces a common rhythm above a critical coupling, and the asymmetry lowers/delays it; (B) the **asymmetry** (Sakaguchi **α** = the_one's **σ** / chirality) breaks forward↔backward symmetry — at α=0 the collective phase does **not drift** (no arrow, drift=+0.000), at α=−0.9 it drifts **+1.12 (forward)** and at α=+0.9 **−1.14 (backward)** — a **chiral traveling reinforcement** whose direction is set by the sign of α, exactly F1180's honest correction that the "asymmetric" is the *temporal/causal arrow*, now demonstrated as the drift-sign of a real resonant body) — **user: "mfo resonant body probe." DONE — the resonant body reinforces (r rises), and the asymmetry (α=σ) is the chirality that makes the reinforcement travel one way = the resonant asymmetric wave, srmech-native.**

**Date:** 2026-07-09 · **srmech:** 0.7.5rc135 · **User direction:** the MFO resonant-body probe. · srmech `cascade.kuramoto_step` is the cascade; the order-parameter read-out uses `math` (a diagnostic, not a cascade); no magnitude-builtin on a cascade; deterministic init (no RNG). · **Composes:** F1180 (upgrades the minimal 1D logistic model to a multi-mode resonant body; demonstrates its "asymmetry = time-arrow" correction), F1179 (the reinforcement, now = the order parameter r), the_one σ (the chirality = α), `[[stance_bit_exact_is_phase_locked_cyclic_slots_not_flat]]` (r = the phase-lock). **Advances #243's resonant-BODY half; the full MFO-notebook subsection still needs the MFO notebook read.**

## A — the reinforcement is the order parameter r (F1179 made continuous & physical)

A resonant body of N=24 coupled modes (Kuramoto oscillators, frequencies spread over a mode-ladder). The **reinforcement** = the order parameter **r** (phase-coherence, r→1 = fully locked):

| coupling | r (symmetric α=0) | r (asymmetric α=0.9) |
|---|---|---|
| 1.5 | 0.884 | 0.439 |
| 2.0 | 0.947 | 0.785 |
| 3.0 | 0.979 | 0.875 |
| 4.0 | 0.988 | 0.963 |

r rises through a synchronization transition — **the resonant body reinforces (locks) a common rhythm above a critical coupling**. This is F1179's "harmonic reinforcement" as a continuous physical quantity on a real multi-mode resonant body (not the F1179 discrete k-copy vote, its analog read-out). The **asymmetry (α=0.9) lowers r at every coupling** — frustration impedes the lock, so reinforcement needs stronger coupling. (Weak-coupling r is noisy/non-monotone from finite-size transients; the clean transition is from coupling 1.5 up.)

## B — the asymmetry is the chiral time-arrow (F1180's correction, demonstrated)

Holding coupling fixed and varying only the Sakaguchi asymmetry α, measuring the collective-phase **drift** (signed = a preferred direction):

| α | r | drift | direction |
|---|---|---|---|
| −0.9 | 0.874 | **+1.118** | → forward |
| 0.0 | 0.979 | **+0.000** | · none (symmetric) |
| +0.9 | 0.875 | **−1.143** | ← backward |

**At α=0 the reinforcement is a standing wave — no drift, no arrow.** At α≠0 it becomes a **traveling** wave whose direction is set by the *sign* of α — a chiral reinforcement. This is exactly F1180's honest correction made concrete: the "asymmetric" in the user's "resonant asymmetric wave" is not a spatial asymmetry but the **temporal/causal chirality** (the_one's σ), and here it is literally the sign of the collective drift on a physical resonant body. σ = the time-arrow that makes the past's reinforcement travel *into* the present.

## The picture, complete

The arc's reframe is now grounded on two complementary physical models:
- **F1180 (1D logistic map):** the *nonlinearity* generates the fractal subharmonic comb (Feigenbaum-attested) = F1171's temporal EC; the asymmetry is the iteration's causal arrow.
- **F1183 (multi-mode resonant body):** the *coupling* generates the reinforcement (order parameter r rising through the sync transition) = F1179's harmonic reinforcement; the *asymmetry* α=σ makes it a chiral traveling wave (drift sign).
Together: **EC = resonant reinforcement (r), harmonic (the subharmonic comb) + asymmetric-in-time (the chiral drift, α=σ)** — the resonant asymmetric wave, measured on both a minimal map and a real resonant body, srmech-native.

## Verdict / next
**MEASURED srmech-native: the MFO resonant body (coupled Kuramoto) reinforces — its order parameter r (= F1179's harmonic reinforcement, continuous) rises through a synchronization transition (0.88→0.99), lowered by the asymmetry; and the asymmetry (Sakaguchi α = the_one's σ) breaks forward↔backward symmetry — at α=0 no drift (standing wave), at α≠0 a signed chiral drift (traveling wave, direction = sign of α). This demonstrates F1180's correction on a real resonant body: the "asymmetric" is the temporal/chiral arrow, physically the drift sign. HONEST scope: this is a coupled-oscillator MODEL of the resonant body (srmech-native), not the full MFO resonant body — writing the MFO-notebook resonant-BODY subsection still needs the MFO notebook read first (flagged, not fabricated). NEXT: read the MFO notebook + write the resonant-BODY subsection anchoring these two probes (F1180+F1183); test whether the α-driven chiral drift carries the subharmonic comb (couple the two models). Read-independent-verified (r-transition + α-drift, deterministic); srmech kuramoto_step; composes F1180/F1179/the_one-σ.**
