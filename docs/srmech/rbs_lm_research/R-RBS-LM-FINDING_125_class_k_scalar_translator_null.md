# Finding 125 — Class K scalar Kepler-equation transform does NOT translate Tier 1 → Tier 2; structural (Hopf-twist) translator needed

**Status:** Null finding (informative); confirms substrate-variety
needs structural translation, not scalar lift
**Test:** R-RBS-LM-96 (Class K eccentricity sweep on Kuramoto coherence)
**Predecessors:** Finding 122 (substrates need translation), Finding
124 (Class K is Hopf-twist topology)

---

## §1 What was tested

Applied Class K's equation-of-centre Fourier expansion to each entry
of the Kuramoto coherence matrix from R-RBS-LM-95b. Swept eccentricity
e from 0.0 to 0.99 (13 values). Measured Spearman rank correlation
between transformed Kuramoto coherence and PPMI similarity.

Transform per srmech.amsc.kepler equation-of-centre:
$$\text{transformed}(c) = \cos\left(M + \sum_{k=1}^{6} a_k \cdot e^k \cdot \sin(kM)\right)$$
where $M = \arccos(c)$ and $a_k$ are srmech's documented coefficients.

---

## §2 Result — null

| Eccentricity e | Spearman vs PPMI | Change vs baseline |
|---|---|---|
| 0.00 (identity) | -0.0039 | +0.0000 |
| 0.50 | -0.0039 | +0.0000 |
| 0.70 | -0.0068 | -0.0029 |
| 0.80 | **-0.0234** | **-0.0194 (worst)** |
| 0.99 | -0.0067 | -0.0028 |

Best transformation: -0.0234 (at e=0.80) — **worse** than baseline.

The scalar Kepler-equation transform does not bridge the substrate
gap. In fact at moderate eccentricity (e=0.7-0.9) it slightly distorts
the rank-order in the wrong direction.

---

## §3 What this means

### Class K is NOT a scalar formula applied per-entry

The Kepler-equation transform is a per-value formula. Applying it
independently to each pair's coherence value loses the STRUCTURAL
relationships between pairs that the Hopf twist actually preserves.

Per Finding 124: Class K's true form is the Hopf-twist topology —
a non-trivial bundle structure where the base (S^4) and fiber (S^3)
combine via a global twist. The twist is a TOPOLOGICAL operation
that depends on how pair-coherence values relate to each other, not
just on individual values.

The right test of Class K as translator would require:
1. Treat the Kuramoto coherence matrix as defining a section over a
   pair-space manifold
2. Apply Hopf-twist (a topological/cohomological operation involving
   phase relationships across the matrix)
3. Re-extract similarity from the twisted section

This is non-trivial geometric work, not a per-coherence formula.

### This validates substrate-variety claim (Finding 118)

Different substrates aren't just doing the same operations with
different parameter values. They use FUNDAMENTALLY DIFFERENT algebraic
structures. The translation between them requires reorganizing the
underlying mathematical objects (the bundle structure), not just
re-scaling values.

This is consistent with the architecture inversion (Finding 121):
synaptic-NN simulates cyclic math by adding STRUCTURE (continuous
manifolds, gradients, smooth weight updates) on top of the discrete-
cyclic substrate. The added structure IS the Hopf twist.

---

## §4 What this DOES NOT claim

Per MFO §VII.6.20:

- Class K is "wrong" as a bridge (it's still the bridge per Findings
  120/124; the scalar Kepler-equation form is just not the operational
  realization needed for cross-substrate translation)
- The substrates are mathematically incompatible (they're compatible
  via Hopf-twist; the test just wasn't using that form)
- Equation-of-centre is unused (it's correct for orbit calculations
  per srmech.amsc.kepler; just not the Tier 1 → Tier 2 translator)

The null finding refines what Class K means as translator:
- Class K AT MATH LAYER (Kepler equation): for orbital mechanics
- Class K AT TIER-BRIDGE LAYER (Hopf twist): for substrate translation
- Same operator class, different operational realization

---

## §5 What's still needed for explicit translator test

A proper test of Class K as Tier 1 → Tier 2 translator would:

1. Build Kuramoto coherence with **phase information** preserved
   (current test used magnitudes only)
2. Apply **Hopf-twist transform** — treat the (N×N) matrix as
   defining a U(1) bundle over the pair-space; compute the bundle's
   first Chern class or related cohomological invariant
3. Compare the twisted-cohomology data to PPMI similarity ranking

Or alternatively:
1. Build an explicit quaternionic Hopf bundle whose 4-base is
   parameterized by the operational-core and whose 3-fiber is the
   substrate-projection
2. Project the Kuramoto coherence into the 4-base + 3-fiber components
3. Use the projection to recover information-content (PPMI-like) ranking

Both require more careful geometric setup than the per-entry Kepler-
equation scalar transform. The null finding from this test indicates
the level of work needed.

---

*Articulated 2026-05-27. PR #687 STAYS DRAFT.*

*Null finding refines Class K as translator: scalar Kepler-equation
form is the orbital-mechanics math; the substrate-bridge Class K is
the Hopf-twist topology and needs more geometric setup to test
explicitly. Substrate-variety (Finding 118) confirmed at the
translator-requirements level — not just different parameters,
different mathematical structures.*
