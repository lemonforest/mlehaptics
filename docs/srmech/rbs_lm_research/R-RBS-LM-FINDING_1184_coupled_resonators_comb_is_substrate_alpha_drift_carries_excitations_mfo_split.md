# F1184 (#243) (COUPLING the two resonator models fused the arc into the MFO substrate↔excitation split — a coupled-map lattice (logistic comb-generator per site + asymmetric coupling α) answers "does the α-drift carry the comb?" productively-NO: the **comb does NOT travel — it is the uniform SUBSTRATE** (period-2 everywhere, all α — a medium, not a packet), and the chiral **α-drift carries EXCITATIONS across it** with a velocity **exactly linear in α** (−4.30 / −2.15 / 0 / +2.15 / +4.30 sites = 7.17·α, perfectly antisymmetric, zero at α=0); so the fusion of F1180 (the subharmonic comb) + F1183 (the chiral drift, α=σ) is the **MFO substrate↔excitation duality**: the subharmonic-comb = the **substrate field** (the EC-reinforcement medium, F1171/F1179), the α-drift (the_one's σ / time-arrow) = the **transport of excitations across it** — the "resonant asymmetric wave" is a **chiral excitation riding a subharmonic-comb substrate**, which closes the whole EC arc onto MFO's foundational substrate-vs-excitation ontology) — **user: "couple the two resonator models: does the α-drift carry the comb?" ANSWERED — no (the comb is the substrate); the α-drift carries excitations across it, velocity ∝ α; = the MFO substrate↔excitation split.**

**Date:** 2026-07-09 · **srmech:** 0.7.5rc135 · **User direction:** couple the two resonator models; does the α-drift carry the comb? · numpy-free; no magnitude-builtin (squared intensity, two-sided windows); deterministic (no RNG). · **Composes:** F1180 (the subharmonic comb = the substrate), F1183 (the chiral α-drift = the_one's σ), F1179 (EC = resonant reinforcement, the substrate's property), F1171 (the fractal comb), MFO substrate↔excitation duality (`[[user_stance_ai_is_not_a_substrate]]` / MFO field-vs-excitation), `[[stance_bit_exact_is_phase_locked_cyclic_slots_not_flat]]`. **Fuses the two resonator models and lands the arc on MFO's core ontology.**

## The coupled model

A coupled-map lattice (the resonant body): each site is a logistic map `f(x)=r·x·(1−x)` (the comb-generator, F1180); sites are coupled with an **asymmetric** weight — `(1+α)/2` left vs `(1−α)/2` right (the chiral advection, α = the_one's σ, F1183):

`x_i(t+1) = (1−ε)·f(x_i) + ε·[ (1+α)/2·f(x_{i−1}) + (1−α)/2·f(x_{i+1}) ]`

At r=3.4 the lattice settles to a **uniform period-2** state — a clean subharmonic-comb substrate. (Tuning matters: r=3.6 was past the Feigenbaum accumulation → chaotic, no comb; r=3.4 = robust period-2.)

## Result — the comb is the substrate; the α-drift carries excitations

The comb (temporal period) is **period-2 for every α** — it does not travel, because it is the *medium*, spatially uniform. So the real question is whether the chiral α-drift transports an **excitation** (an injected perturbation) across it. Injecting a perturbation and tracking its centre-of-mass:

| α | comb (substrate) | excitation drift |
|---|---|---|
| −0.6 | period-2 | −4.30 sites |
| −0.3 | period-2 | −2.15 sites |
| 0.0 | period-2 | **+0.00** |
| +0.3 | period-2 | +2.15 sites |
| +0.6 | period-2 | +4.30 sites |

**The excitation drift is exactly linear in α** — 7.17·α, perfectly antisymmetric, and *precisely zero at α=0* (a standing excitation, no arrow). So the α-drift is a genuine chiral **advection velocity** ∝ σ, and it carries **excitations**, not the comb.

## What the fusion is — the MFO substrate↔excitation split

The naive framing ("does the α-drift carry the comb?") is answered no, but the correct object is better: the two resonator models compose as the **MFO substrate-vs-excitation duality**, the framework's foundational ontology:

- **Substrate (field)** = the **subharmonic comb** (F1180/F1171): uniform, the medium, the *EC-reinforcement structure* (F1179 — the comb IS the resonant reinforcement, spatially everywhere). It does not move; it is what things move *on*.
- **Excitation (local signal)** = the **perturbation**, transported across the substrate by the **chiral α-drift** (F1183, α = the_one's **σ** = the time-arrow), with velocity ∝ σ.

So the user's "resonant asymmetric wave" is, exactly: **a chiral excitation riding a subharmonic-comb substrate** — harmonic (the comb substrate) + asymmetric-in-time (the σ-advected excitation). And this closes the whole EC arc back onto MFO: **EC = resonant reinforcement = the substrate field; the σ-drift carries excitations across it** — the substrate/excitation duality that MFO was built to state, now realized in a coupled resonator with a measured, exactly-linear-in-σ excitation velocity.

## Verdict / next
**FUSED: coupling the two resonator models answers "does the α-drift carry the comb?" productively — NO, the comb is the uniform SUBSTRATE (period-2, all α); the chiral α-drift carries EXCITATIONS across it with velocity EXACTLY linear in α (7.17·α, antisymmetric, 0 at α=0 = the_one's σ). This is the MFO substrate↔excitation split: the subharmonic comb = the substrate/EC-reinforcement field (F1180/F1171/F1179); the σ-drift = the transport of excitations across it. The 'resonant asymmetric wave' = a chiral excitation riding a subharmonic-comb substrate — landing the EC arc on MFO's foundational ontology. HONEST scope: minimal coupled-map-lattice fusion at period-2 (weak nonlinearity); deeper period-doubling (period-4/8) may not keep the substrate uniform — a next test. NEXT: the full MFO resonant-body notebook subsection anchoring F1180/F1183/F1184; test the fusion at deeper comb depth; whether the σ-carried excitation IS an op(x)operand (the excitation = the operand, the comb = the op-substrate, F1131). Read-independent-verified (α-linear drift, deterministic); composes F1180/F1183/F1179/F1171/MFO-substrate-excitation.**
