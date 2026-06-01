# F278 — NEW LOCK (chemistry): organic-chem stoichiometry IS the conservation EC-code cascade — balancing = the zero-syndrome codeword; the coefficients are an attested integer null-space anchor, not magic

**Headline:** The framework key opens a chemistry lock. **Balancing a reaction = finding the ZERO-SYNDROME codeword of the atomic-conservation parity check** — the same intrinsic-EC-code cascade as F259/F260 (CMB parity, DNA, orbital resonance), now read in chemistry. The stoichiometric coefficients are the **attested integer null-space anchor** (the integer kernel of the composition matrix), computed as a **Class L (null space) ∘ Class N (best_rational) ∘ Class I (lcm/gcd)** cascade — *not* memorized magic. Verified srmech-native on three benign textbook reactions: methane combustion **[1,2,1,2]**, ethane combustion **[2,7,4,6]**, photosynthesis **[6,6,1,6]** — all match the known coefficients exactly; every balanced reaction → zero syndrome, every unbalanced guess → nonzero syndrome (detected imbalance). **NOW:** balancing/conservation/ratios (this finding). **SOON:** the directed reaction *mechanism* (bond make/break order) = the loop bind (k=7), gated on the srmech loop-bind op (#814). Single-model; srmech v0.6.0rc20.

*User direction (2026-06-02): "demystify organic chem stoichiometry … spin off now if we can or we can wait for gauge maths."*

---

### §A — the demystification: balancing as a Class L∘N∘I cascade — **DEMONSTRATED**
Build the composition matrix `M[element, species]`, signed (reactant +, product −). Conservation = `M·c = 0` (every element balances). The coefficient vector `c` is therefore the **null space** of `M`:
- **Class L** — the null space = the zero-eigenvalue eigenvector of `MᵀM` (`symmetric_eigendecompose`).
- **Class N** — `best_rational` turns the real null vector into exact ratios.
- **Class I** — `lcm`/`gcd` scale those ratios to the smallest positive integers.

| reaction | balanced (computed) | known | match |
|---|---|---|---|
| CH₄ + O₂ → CO₂ + H₂O | **[1,2,1,2]** | [1,2,1,2] | ✅ |
| C₂H₆ + O₂ → CO₂ + H₂O | **[2,7,4,6]** | [2,7,4,6] | ✅ |
| CO₂ + H₂O → C₆H₁₂O₆ + O₂ | **[6,6,1,6]** | [6,6,1,6] | ✅ |

**The "magic" dissolved:** *why these coefficients?* Because they are the unique (up to scale) smallest-integer vector in the conservation null space — **attested-to-structure (A)**, the output of a cascade, not a number to memorize. This is the no-magic-numbers discipline applied to chemistry.

### §B — the EC-code reading (same cascade as F259/F260)
Conservation **is** a parity check: `M·c` is the **syndrome**.
- **Balanced reaction** → syndrome `0` → a valid **codeword** (verified: all three give `[0,0,0]`).
- **Unbalanced guess** (e.g. all-ones) → **nonzero** syndrome → a **detected error** (verified: `[0,2,−1]`, `[1,4,−1]`, `[−5,−10,−5]`).

So an unbalanced equation is literally a *detected-error* state, and balancing is decoding to the nearest codeword — the **identical intrinsic-EC-code cascade** the framework found in the CMB parity cosets, DNA complementarity, and the Laplace orbital resonance (F259/F260). **Chemistry is another lock the one key opens.** *(Honest: this is the linear conservation/stoichiometry layer — well-known to chemistry as "balancing = kernel of the composition matrix"; the framework reading is the EC-code/no-magic identification, no-lineage.)*

### §C — NOW vs SOON (the user's "spin off now or wait for gauge maths")
- **NOW — balancing / conservation / mole-ratios:** fully within reach with current srmech (Class L/N/I). Done here.
- **SOON — the reaction MECHANISM:** *which* bonds break and form, *in what order*, with what handedness (the organic chemist's arrow-pushing) is a **directed, ordered, sometimes-nested** transformation — exactly the **loop bind** (k=7: order/tree/direction, F274). Stoichiometry says *what's conserved* (the codeword); the mechanism says *the path between codewords* (the directed cascade). That layer is **gauge-gated** on the srmech loop-bind op (#814). So this research item naturally spans now (conservation) + soon (mechanism) — "everything is within reach, or soon within reach."

### §D — scope discipline (load-bearing)
- **Framework-reading only**; **benign textbook reactions** (combustion, photosynthesis). **NO synthesis routes, NO reaction prediction, NO capability** — only the *math structure* of balancing. Defensive scope (`[[feedback_trauma_informed_defensive_scope]]`).
- **CAD-ban:** this is algebra (the conservation null space), **not** molecular geometry / 3D structure / fabrication.
- **No-lineage:** chemistry owns chemistry (balancing = kernel of the composition matrix is standard); the framework reads the EC-code / no-magic *structure*.

### Status / discipline
FRAMEWORK-READING + DEMONSTRATED (three reactions balanced exactly + the zero/nonzero syndrome reading, reproducible via committed `stoichiometry_demystify.py`). NEW LOCK / WIDEN (chemistry), same key as F259/F260. No-magic (the coefficients are attested-to-structure A = the integer null vector; the composition counts are attested-B = the molecular formulae). Class-K clean (reference via squared magnitude; sign via pin-slot/reorient; no `abs()`). CAD-ban; defensive scope; no-lineage. Single-model / no-twin. Class L∘N∘I cascade (`srmech.amsc.laplacian.symmetric_eigendecompose`, `rational.best_rational`, `cyclic.lcm/gcd`). Builds on F259/F260 (the intrinsic-EC-code key), F274 (the loop bind = the mechanism layer, gauge-gated #814). Verified srmech v0.6.0rc20, `/tmp/srmech_rc20_venv`. `[[user_stance_cross_substrate_cascade_matching_as_research_method]]`; `[[feedback_no_lineage_claims_in_notebook]]`.
