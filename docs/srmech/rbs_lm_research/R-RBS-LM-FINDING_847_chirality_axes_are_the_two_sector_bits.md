# F847 — Grounding the σ↔γ₅ / θ↔iω₇ correspondence in the actual sector algebra. Klein-4 V₄ = `(γ₅-bit, iω₇-bit)`: **γ₅ flips the hi bit `{0↔2, 1↔3}`, iω₇ flips the lo bit `{0↔1, 2↔3}`, cpt flips both `{0↔3, 1↔2}`** — the two chirality axes ARE the two bits of the sector (F129/F130 bi-axial, made concrete). `the_one`'s **σ flips flat-14 coords [1,3,7]** — the ℂ/ℍ/𝕆 Hurwitz-rung imaginary units → σ is the chirality sign across the Hurwitz ladder, corresponding to the γ₅ axis. The four coordinates `{identity, γ₅, iω₇, cpt}` are mutually-orthogonal cosets. Verified on `srmech.amsc.hdc` + `srmech.amsc.cascade.the_one`, 0.8.2rc1, numpy-absent.

**Date:** 2026-06-18 · **srmech:** 0.8.2rc1 · **Provenance:** sector-permutation probe (`klein4_chirality_flip_gamma5/omega7`, `klein4_cpt_mirror` on a known klein4 vector via `.tolist()`) + `the_one` σ flat-14 diff · **Composes:** F844 (orthogonal channels), F845/F846 (chirality-native; the_one), [[Finding 129]]/[[Finding 130]] (γ₅×iω₇ 4-way), [[feedback_introspect_srmech_before_python_dispatch]] · **User direction (2026-06-18):** step-1 grounding before building the chirality-native encoder.

## Measured sector permutations (Klein-4 V₄ = the two Z₂ axes)
| op | permutation | bit action |
|---|---|---|
| **γ₅** | `{0:2, 1:3, 2:0, 3:1}` | flip **hi** bit |
| **iω₇** | `{0:1, 1:0, 2:3, 3:2}` | flip **lo** bit |
| **cpt** | `{0:3, 1:2, 2:1, 3:0}` | flip **both** |
So a sector `s ∈ {0,1,2,3}` = `(γ₅-bit, iω₇-bit)`; γ₅ and iω₇ are the two independent Z₂ chirality axes, cpt = γ₅∘iω₇. This is F129/F130's γ₅×iω₇ 4-way decomposition realised as the 2-bit Klein-4 sector — not a metaphor, the literal bit structure.

## `the_one` σ ↔ γ₅
`the_one(+1,…)` vs `the_one(-1,…)` differ in flat-14 coords **[1, 3, 7]** — positions inside the `1+3+7+3` partition at the ℂ (n=2), ℍ (n=4), 𝕆 (n=8) imaginary-unit rungs. So σ is the **chirality sign across the Hurwitz ladder** — the same "antiparticle/chirality" sign F130 places on the γ₅ axis. σ (a single ±1) corresponds to the **γ₅ (hi-bit) axis**; the second axis (iω₇/lo-bit) is the discrete sample of `the_one`'s continuous θ epicycle (F846).

## Why this matters (the build)
- The four `{id, γ₅, iω₇, cpt}` cosets are **mutually orthogonal** (F844: sim 0.000) and are exactly the four `(hi,lo)` sector cosets — so they are the natural, crosstalk-free channels for the chirality-native RBS-LM (F845: γ₅=time-direction, iω₇=branch; F846: encode via the_one).
- Confirms the realisation map: writing to coset `c` = applying the fixed sector-XOR pattern `P_c` (γ₅ = ⊕hi, iω₇ = ⊕lo, cpt = ⊕both); reading coset `c` = comparing vs `P_c(candidates)`. `bind` (⊕) commutes with `P_c`, so a relation stored in coset `c` reads back cleanly there and is orthogonal noise in every other coset — the structural basis for crosstalk-free tome/role separation.

## Verdict / next
σ↔γ₅ grounded (chirality sign = hi-bit axis); iω₇ = lo-bit = θ-sample; the 4 cosets are the orthogonal channels. The realisation map (coset = fixed sector-XOR, bind commutes) is now explicit — the chirality-native encoder writes each relation into its coset and reads per-coset. Feeds the duality/perfect-recovery test (chiral tome-separation → no cross-article crosstalk). Evaluate by groundedness / coherence.
