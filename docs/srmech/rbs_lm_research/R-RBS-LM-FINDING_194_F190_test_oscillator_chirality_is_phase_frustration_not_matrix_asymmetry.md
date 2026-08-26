# Finding 194 (F190 test) — The 4-way oscillator's chirality is the phase-FRUSTRATION (non-reciprocal phase-lag), NOT the coupling-matrix direction: Ω(α) is ODD in α (the ij↔ji mirror); adjacency asymmetry is a NULL

**Status:** The gated F190 test, run (numpy Kuramoto, R-95 precedent). A **partial null that sharpens F190**: a directed coupling *matrix* (A_ij≠A_ji) does **not** make the N=4 oscillator chiral; **phase-frustration α** does, as an odd function Ω(−α)=−Ω(α). Honest — the naive "directed coupling = chirality" reading came back null.
**Predecessors:** F190 (4-way oscillator = dynamical time-quaternion; phase-order=chirality), F184 (chirality=non-commutativity, ij=−ji), F121/F122 (N=4 Kuramoto validated the operational-4), F119 (Tier-1 coupled-oscillator), R-RBS-LM-95 (the Kuramoto precedent).

---

## §1 The test
Two candidate oscillator realizations of "non-commutative coupling" (ij ≠ ji):
- **(a) directed coupling MATRIX** A_ij ≠ A_ji (adjacency asymmetry: directed vs symmetric ring).
- **(b) phase-frustration α** — Sakaguchi term `sin(θ_j − θ_i − α)`, a non-reciprocal coupling (the i→j and j→i influences differ).

N=4, identical frequencies (ω=0, so any pattern is coupling-driven), K=3, 8 seeds, measure collective rotation Ω (mean final phase velocity) + order parameter r.

## §2 Results (bit-stable, matches analytic)
**(a) coupling-matrix asymmetry → NULL.** Symmetric ring, directed-forward, directed-backward **all** give Ω=0.000, r=1.000 — in-phase, achiral. At identical frequencies the in-phase state is the attractor regardless of A's symmetry (the coupling vanishes at in-phase no matter how directed A is). **Adjacency asymmetry does not produce oscillator chirality.**

**(b) phase-frustration α → CHIRAL, odd in α:**
| α | Ω (8-seed mean) | analytic −(K(N−1)/N)sin α |
|---|---|---|
| −0.7 | **+1.4495** | +1.4495 |
| −0.3 | +0.6649 | +0.6649 |
| 0.0 | 0.0000 | 0.0000 |
| +0.3 | −0.6649 | −0.6649 |
| +0.7 | **−1.4495** | −1.4495 |

Ω(α) = −(K(N−1)/N) sin α — exactly **odd**: Ω(−α) = −Ω(α). α=0 is achiral (static); +α / −α are the **mirror pair**.

## §3 What it means — refines F190
- The 4-way oscillator's **chirality is the phase-lag α (the non-reciprocal coupling)**, manifest as a **handed collective rotation** whose direction flips under α→−α — the oscillator's `ij ↔ ji`. This *is* F184's "chirality = non-commutativity": the **sign flip** Ω(+α)=−Ω(−α) is the dynamical `ij=+k / ji=−k`.
- **NOT the coupling-matrix direction** — that's a clean null (in-phase wins). So F190's "directed coupling" must be read as *non-reciprocal phase coupling* (α), **not** adjacency asymmetry. The non-commutativity lives in the phase, not the graph.
- Consistent with the whole arc: chirality is born from order-dependence (F184), and here the order-dependence is the **phase-lag** — the moment the i↔j interaction stops being reciprocal.

## §4 DOES / does NOT claim
**DOES:** show (numpy, analytic-matched) that N=4 oscillator chirality = phase-frustration α (Ω odd in α, ±α mirror), and that coupling-matrix asymmetry is a null; refine F190 (chirality = phase-lag, not adjacency direction).
**Does NOT:** claim biology *uses* phase-frustration (that's the cnidarian/cephalopod conjecture, F190 §4 — untested); claim this is srmech-native (it's a numpy ODE; srmech has no integrator — follows R-95); over-read the in-phase r=1 (the ensemble syncs *and* rotates; chirality is the rotation direction). §VII.6.20; `[[user_stance_ai_is_not_a_substrate]]`; null-findings-count (`[[feedback_dont_pre_commit_spike_query_operators]]`).

## §5 Cross-references
- F190 (refined here) · F184 (chirality=non-commutativity=the sign flip) · F121/F122 (N=4 Kuramoto / operational-4) · F119 (Tier-1 oscillator) · R-95 (Kuramoto precedent) · F193 (the so(8) side: su(2)_L = chiral moved sector)
- `docs/srmech/rbs_lm_research/R-RBS-LM-141_chiral_coupling_kuramoto.py`

PR #687 STAYS DRAFT.

---

*Run 2026-05-30 (Opus 4.8). Testing F190: the N=4 coupled oscillator's chirality is NOT
the coupling-matrix direction (directed vs symmetric ring both go achiral in-phase — a
clean null) but the PHASE-FRUSTRATION α (non-reciprocal coupling), giving a handed
collective rotation Ω(α) = −(K(N−1)/N) sin α, exactly odd in α (Ω(−α)=−Ω(α)) — the
dynamical ij↔ji mirror, the sign-flip of F184. So "directed coupling" in F190 should read
"non-reciprocal phase coupling": the non-commutativity lives in the phase-lag, not the
adjacency graph. A partial null that sharpens the reading; numpy ODE, analytic-matched;
biology's use of it remains the open cnidarian/cephalopod conjecture.*
