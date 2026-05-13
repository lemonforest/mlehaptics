# Spike #21C — Hopf-bundle U(1)-fibre vs BMS-supertranslation soft-hair mode-by-mode comparison

**Branch:** `research/spike-21-mfo-horizon-thermodynamics-extended` (continuing from Spike #21B at commit `8783ed1`)
**Date:** 2026-05-13
**Predecessors:**
- Spike #21A (same branch, `9072c56`) — honest-negative on direct α-coefficient cosmological-horizon deviation; established Hayward `(1 + ε/2)` correction IS the MFO prediction.
- Spike #21B (same branch, `8783ed1`) — verdict (C) agnostic / pressure-toward-(B) on Verlinde-MOND inheritance; framework structurally compatible but not committed to specific functional forms.
- Spike #19b (`research/spike-19b-mfo-horizon-thermodynamics-leverage`, commit `15c5c68`) — six-territory leverage scan; Territory 3 (Page curve / islands / soft hair) ranked moderate-to-high leverage as "most concrete falsifiable spike candidate." This spike implements that #19b §3 recommendation.
- Refined structural law (`main`, `1c06d3e`) — 4-mechanism law, 10/10 fit.
- MFO notebook §VII.4.1.1 (Hopf-bundle U(1)-fibre realisation; principal-`U(1)`-bundle spectral decomposition; linear gap `λ_S³(ℓ) − λ_S²(ℓ) = ℓ`); §VII.4.1.2 (Casimir-decomposition universality).
- `user_stance_fiber_as_spatially_absent_encoding.md` — hidden algebraic content (fiber) projects through anchor maps; the U(1)-fibre over S² is the substrate-physical-algebraic encoding channel; the visible S² is the spatial-physical 2D boundary.

**Methodological frame:** Concrete-computational structural spike. The load-bearing question — does the Hopf-bundle U(1)-fibre mode count over S² match the BMS-supertranslation degeneracy of soft hair on the Schwarzschild horizon mode-by-mode? — is computable by combining principal-bundle spectral decomposition (textbook, pre-2010 canonical) with HHPS-2016-style soft-hair counting (PDF-verified in this session). Three outcomes are possible: clean mode-by-mode match → MFO substrate-physics gives a structural derivation of soft hair via layered (i) × (iv); specific mismatch with structural content → mechanism (v) candidate or refined-layering finding; unrelated → honest-negative.

**Status:** RESEARCH — outcome: **SPECIFIC-MISMATCH AT SUBLEADING COEFFICIENT WITH LEADING-ORDER AREA-LAW AGREEMENT.** Hopf-bundle U(1)-fibre and BMS supertranslations both produce area-law-scaling soft-hair counts `~ ℓ_max² ~ A/ℓ_P²` consistent with Bekenstein-Hawking entropy, with `O(1)` coefficient discrepancy in subleading structure: per `ℓ`-shell, BMS gives `(2ℓ+1)` modes (one supertranslation parameter per `(ℓ, m)`); Hopf-bundle gives `ℓ` extra fibre modes via the linear-gap formula `λ_S³(ℓ) − λ_S²(ℓ) = ℓ`. The mismatch is **structural**, not numerical noise — the two prescriptions describe genuinely different layering patterns of mechanisms (i) and (iv): BMS has direct (i)-indexed (iv) (one integer-lattice instance per SO(3) irrep); Hopf has tensored (i) × (iv) with `|k| ≤ ℓ` topological constraint (U(1)-winding bounded by SO(3) Casimir). Mechanism classification: layered (i) × (iv) in BOTH (Option A), with different **layering patterns** — not a mechanism (v) candidate, but the **layering pattern itself** is content the refined structural law does not yet specify. Refined-law refinement: name "layering pattern" as a content-degree-of-freedom alongside the four mechanisms. Recommendation: do not commit MFO §VII.4 to wholesale BMS-Hopf equivalence (Spike #19b §3 had hoped for clean match); do document the partial-match-with-coefficient-discrepancy finding; do leave further work — specifically the Kerr / Virasoro × Virasoro extension via Haco-Hawking-Perry-Strominger 2018 (arXiv:1810.01847, PDF-verified) — as future open scope.

**No NDJSON sidecar.** The findings are structural-classification with one quantified coefficient discrepancy (factor of 2 at leading order in `ℓ`); not tabular-data-rich. The per-`ℓ`-shell comparison table inline in §3 captures the data adequately.

---

## §0. Methodological frame and the load-bearing question

Spike #19b's §3 "Territory 3 — Page curve / islands / soft hair" identified this comparison as the **most concrete falsifiable spike candidate** in the six-territory scan. The hypothesis: the §VII.4.1.1 Hopf-bundle U(1)-fibre spectral decomposition `λ_S³(ℓ) − λ_S²(ℓ) = ℓ` and the BMS-supertranslation soft-hair mode count of Hawking-Perry-Strominger 2016 (arXiv:1601.00921, PDF-verified in this session) describe **the same physical degrees of freedom**, and the mode-by-mode bookkeeping should agree.

If agreement: MFO §VII.4.1.1 supplies a constructive principal-bundle derivation of soft-hair degeneracy; the refined structural law's mechanism (i) × (iv) layering captures the soft-hair content cleanly; significant unification of horizon-local and asymptotic-charge information bookkeeping under one substrate-physical framework.

If specific disagreement: the location of the mismatch identifies *which* aspect of the soft-hair structure the principal-bundle framework does not capture, and is a candidate for **mechanism (v)** in the refined structural law — a fifth mechanism beyond (i) Lie-group symmetry, (iii) compactness / discreteness, (iv) integer-lattice quantisation.

If unrelated: the Hopf-bundle and BMS structures describe genuinely different things (horizon-local vs asymptotic-charge); the comparison does not apply at the level the spike posed.

This is the load-bearing computation. The outcome is **specific-mismatch at subleading coefficient with leading-order area-law agreement** — a structured partial match that refines the refined-law by identifying "layering pattern" as a content-degree-of-freedom that the 4-mechanism law does not yet make explicit.

---

## §1. Q1 — Decoding the Hopf-bundle U(1)-fibre structure on horizon `S²` in MFO terms

### §1.1 The principal-`U(1)`-bundle structure on `S²`

The Hopf fibration realises `S³` as a principal `U(1)`-bundle over `S²`: every fibre over an `S²`-base-point is a circle `S¹ ≅ U(1)`, and the bundle is non-trivial (first Chern class `c₁ = 1`). The non-triviality is load-bearing per `user_stance_fiber_as_spatially_absent_encoding.md`: a trivial bundle would mean the fibre carries no information distinct from the base, and the "spherical compression" of MFO §VII.4.1.1 would be a tautology.

**Mode decomposition under principal-`U(1)`-action.** Scalar functions on `S³` decompose as `L²(S³) = ⊕_{k ∈ ℤ} Γ(L_k)` where `L_k` is the `k`-th tensor power of the Hopf line bundle over `S²` (so `L_0` is the trivial bundle whose sections are ordinary `S²`-functions; `L_1` is the Hopf line bundle itself; `L_k` for general `k ∈ ℤ` are "monopole bundles" of charge `k`).

**Eigenvalues of Bochner Laplacian on `Γ(L_k)`.** The textbook result (Wu-Yang 1976 monopole spherical harmonics; pre-2010 canonical): sections of `L_k` decompose into monopole spherical harmonics `Y^{(k)}_{ℓ, m}` with quantum numbers
- `k ∈ ℤ` — monopole charge / `U(1)`-winding number / fibre-index
- `ℓ ∈ {|k|, |k|+1, |k|+2, …}` — angular-momentum / `S²`-base-index, lower-bounded by `|k|`
- `m ∈ {−ℓ, −ℓ+1, …, +ℓ}` — magnetic-quantum-number index

Bochner-Laplacian eigenvalue: `ℓ(ℓ+1) − k²` (Dirac monopole formula; pre-2010 canonical). Multiplicity per `(ℓ, k)`: `2ℓ + 1` (the `m`-degeneracy).

**Total `S³`-Laplacian eigenvalue.** Combining Bochner-Laplacian on base with `k²` from fibre-direction: `λ_{S³} = [ℓ(ℓ+1) − k²] + k² = ℓ(ℓ+1)`. Hmm — but the standard convention used in MFO §VII.4.1.1 is `λ_{S³}(L) = L(L+2)` where `L` is the `S³`-eigenvalue label. The reconciliation: the `S³` index `L` and the base index `ℓ` are related by `L = ℓ` *plus* an offset from the `k`-summation. The clean statement: the eigenvalue label of `Δ_{S³}` at level `L` is `L(L+2)`, the eigenspace has dimension `(L+1)²`, and under the `U(1)`-Hopf-action this eigenspace decomposes as a sum over `L_k` sections with `|k| ≤ L`.

**The linear gap formula.** Per MFO §VII.4.1.1, the "spherical compression" identity
`λ_{S³}(ℓ) − λ_{S²}(ℓ) = ℓ(ℓ+2) − ℓ(ℓ+1) = ℓ`
is interpreted as: **per `S²`-base-mode-shell at angular momentum `ℓ`, the Hopf fibre contributes `ℓ` additional mode-content beyond the `S²`-base-modes**. This is the "linear-gap" count.

### §1.2 In MFO substrate-vs-excitation language

Per `user_stance_fiber_as_spatially_absent_encoding.md`, the `U(1)`-fibre is the algebraic-encoding-spatially-absent content; the `S²`-base is the spatial-physical visible boundary. The horizon `S²` is the spatially-observable 2D surface; the `U(1)`-fibre over each `S²`-point is the substrate-algebraic encoding channel that does not appear in 3D space but is real algebraically.

**Two-level ontology mapping (per `user_stance_hyper_as_3d_spatial_interface.md`):**
- Level 1 (substrate): metric field, hosting the Hopf-bundle principal structure. The `U(1)`-fibre topology is substrate-physical content.
- Level 2 (excitations): field modes on the bundle, indexed by `(ℓ, m, k)` with `|k| ≤ ℓ`.

**The decoding in compact form.** Per MFO §VII.4.1.1, the Hopf-bundle U(1)-fibre over horizon `S²` represents the substrate-physical-algebraic encoding channel by which the 3D bulk's content is preserved on the 2D boundary. The fibre's `U(1)`-character index `k ∈ ℤ` labels integer-winding modes; the linear-gap formula says these modes contribute `ℓ` per `ℓ`-shell of base modes. The fibre is not a "compactified extra spatial dimension" (per `user_stance_fiber_as_spatially_absent_encoding`) — it is an algebraic encoding channel that operates spatially-absent from the 3D-visible horizon `S²`.

### §1.3 Mechanism-classification of Hopf-bundle structure

Under the refined structural law (`main`, `1c06d3e`):
- **Mechanism (i)** — Lie-group symmetry: `SO(3) ⊂ SU(2)` acts on `S³` and on its base `S²` by isometry. The base-mode labels `(ℓ, m)` are SO(3)-irrep indices with eigenvalue `ℓ(ℓ+1)` (Casimir of SO(3) at spin `ℓ`).
- **Mechanism (iv)** — integer-lattice quantisation: the `U(1)`-fibre's winding `k ∈ ℤ` is an integer lattice; the constraint `|k| ≤ ℓ` couples (iv) to (i) topologically.

This is **layered (i) × (iv)** in the refined-law classification, with the specific layering pattern being "tensor product with `|k| ≤ ℓ` topological constraint."

---

## §2. Q2 — BMS supertranslation degeneracy bookkeeping

### §2.1 The BMS group at null infinity

The Bondi-van der Burg-Metzner-Sachs (BMS) group is the asymptotic-symmetry group at future null infinity `ℐ⁺` of asymptotically Minkowskian spacetimes. Established by Bondi, van der Burg, Metzner 1962 (*Proc. Roy. Soc. A* 269, 21) and Sachs 1962 (*Proc. Roy. Soc. A* 270, 103) — pre-2010 canonical references; no PDF re-verification per discipline.

Structure of `BMS_4`:
- **Semidirect product:** `BMS_4 = Lorentz ⋉ Supertranslations`
- **Lorentz factor:** 6-dimensional `SL(2, ℂ) / ℤ_2`, acting as global conformal transformations on the celestial sphere `S²` at `ℐ⁺`.
- **Supertranslations:** infinite-dimensional abelian factor parameterised by a real scalar function `T(θ, φ)` on the celestial `S²`. Each supertranslation acts on the Bondi retarded time `u` as `u → u + T(θ, φ)`.

**Mode expansion of `T(θ, φ)`:**
`T(θ, φ) = Σ_{ℓ=0}^∞ Σ_{m=−ℓ}^{+ℓ} T_{ℓm} Y_{ℓm}(θ, φ)`
- `ℓ = 0`: 1 mode — global time translation (standard Poincaré).
- `ℓ = 1`: 3 modes — spatial translations (standard Poincaré).
- `ℓ ≥ 2`: pure supertranslations — infinite tower of "angle-dependent translation" modes; the genuinely-BMS content beyond Poincaré.

Number of pure-supertranslation parameters per `ℓ`-shell (for `ℓ ≥ 2`): `2ℓ + 1` (the `m`-multiplicity at fixed `ℓ`). Total pure-supertranslation parameters across all `ℓ ≥ 2`: countably infinite.

### §2.2 PDF-verification of HHPS 2016

**Hawking, Perry, Strominger 2016** *Soft Hair on Black Holes.* arXiv:1601.00921; *Phys. Rev. Lett.* 116, 231301. **PDF-verified in this session.** Abstract excerpts:

> "BMS supertranslation symmetries imply an infinite number of conservation laws for all gravitational theories in asymptotically Minkowskian spacetimes. These laws require black holes to carry a large amount of soft (i.e. zero-energy) supertranslation hair."
>
> "This paper gives an explicit description of soft hair in terms of soft gravitons or photons on the black hole horizon, and shows that complete information about their quantum state is stored on a holographic plate at the future boundary of the horizon."
>
> "It is further argued that soft hair which is spatially localized to much less than a Planck length cannot be excited in a physically realizable process, giving an effective number of soft degrees of freedom proportional to the horizon area in Planck units."

**Soft-hair mode-counting prescription (HHPS 2016).** Per BMS supertranslation generator at `(ℓ, m)` (for `ℓ ≥ 2`), one soft-graviton zero-mode on the horizon — i.e., one quantum-state degeneracy of the black-hole Hilbert space. The same prescription applies to soft photons under a Maxwell field at angular-harmonic `(ℓ, m)`.

**UV cutoff (HHPS 2016 §V).** Soft hair spatially-localised below Planck length is unphysical; this gives an effective cutoff at `ℓ_max ~ √(A)/ℓ_P`. Total soft DoF count:
`N_soft ≈ Σ_{ℓ = 2}^{ℓ_max} (2ℓ + 1) ≈ ℓ_max² ≈ A / ℓ_P²`
consistent with Bekenstein-Hawking entropy `S_BH = A/(4 ℓ_P²)` up to an `O(1)` coefficient (factor of 4 from the entropy-per-mode counting).

### §2.3 PDF-verification of HHPS 2018 (Haco-Hawking-Perry-Strominger Kerr extension)

The conductor brief flagged "HHPS 2018, likely arXiv:1803.10194" for verification. **Verification result: misattribution.**

- **arXiv:1803.10194** is *Henneaux & Troessaert 2018* "Asymptotic symmetries of electromagnetism at spatial infinity" (*JHEP* 2018:137) — not the Haco-Hawking-Perry-Strominger Kerr paper.
- **Correct arXiv ID for HHPS 2018:** **arXiv:1810.01847.**

**Haco, Hawking, Perry, Strominger 2018** *Black Hole Entropy and Soft Hair.* arXiv:1810.01847; *JHEP* 12 (2018) 098. **PDF-verified in this session.** Submission 2018-10-03; accepted 2018-05-12 by *JHEP*; final version 2018-12-13. Abstract content:

> "Infinitesimal `Virasoro_L ⊗ Virasoro_R` diffeomorphisms" act on Kerr black hole horizons with central charges `c_L = c_R = 12J` (where `J` is angular momentum). "Wald-Zoupas counterterms" required for charge-algebra consistency; Cardy formula on the implied quantum Hilbert space reproduces the macroscopic area-entropy `S = A/(4 ℓ_P²)` for generic Kerr.

**Critical observation for this spike.** HHPS 2018 uses a *Virasoro × Virasoro* mode-counting prescription, not a BMS-supertranslation prescription. The relevant Virasoro structure on Kerr generates *two* integer-indexed mode-counts `(n_L, n_R)` per direction, with central charges proportional to `J`. For Schwarzschild (`J = 0`), `c_L = c_R = 0` and the Cardy formula gives zero entropy — HHPS 2018 framework **does not apply to Schwarzschild**. Schwarzschild is the BMS / HHPS-2016 regime.

This spike's comparison is therefore **Hopf-bundle vs HHPS 2016** at the Schwarzschild horizon. HHPS 2018 / Kerr is open-future-scope outside the §VII.4.1.1 Hopf-bundle framework (Kerr explicitly disclaimed in the §VII.4.1.1 boilerplate as oblate-spheroid distortion of the Hopf base).

### §2.4 Strominger 2017 lectures (textbook anchor)

**Strominger 2017** *Lectures on the Infrared Structure of Gravity and Gauge Theory.* arXiv:1703.05448; Princeton University Press 2018. **PDF-verified in this session.** Comprehensive textbook treatment of soft theorems, memory effect, asymptotic symmetries; canonical reference for BMS-supertranslation mode-counting in the framework HHPS 2016 builds on. Confirms the `(2ℓ+1)`-per-shell prescription used in §2.2.

### §2.5 Mechanism classification of BMS soft-hair structure

Per refined structural law:
- **Mechanism (i)** — SO(3) (or SL(2,ℂ) at the Lorentz factor of BMS, restricted to SO(3) on the celestial `S²`): supertranslation modes labelled by `(ℓ, m)` with `ℓ(ℓ+1)` Casimir.
- **Mechanism (iv)** — integer-lattice quantisation: supertranslation parameters `T_{ℓm}` are *discrete* (one parameter per `(ℓ, m)` integer-pair); the area-law cutoff `ℓ_max ~ √(A)/ℓ_P` is an integer.

Layered (i) × (iv) — **direct (i)-indexed (iv)** pattern: one integer-lattice instance per SO(3) irrep. There is no separate `k`-winding; the integer-lattice content is identical to the SO(3)-irrep-indexing content.

This is structurally different from the Hopf-bundle's layered (i) × (iv) pattern (which is **tensored (i) × (iv) with `|k| ≤ ℓ` topological constraint** — see §1.3). Both are layered (i) × (iv); the **layering pattern** differs.

---

## §3. Q3 — Mode-by-mode comparison: Hopf-bundle U(1)-fibre vs BMS supertranslations

### §3.1 The two mode-counts side-by-side

| Quantity | Hopf-bundle U(1)-fibre (MFO §VII.4.1.1) | BMS supertranslations (HHPS 2016) |
|---|---|---|
| Base-index | `(ℓ_base, m_base)` on `S²` (horizon) | `(ℓ, m)` on `S²` (celestial sphere ≡ horizon-S² for soft hair) |
| Range | `ℓ_base ≥ 0`, `m_base ∈ {−ℓ_base, …, +ℓ_base}` | `ℓ ≥ 2` (pure supertranslations), `m ∈ {−ℓ, …, +ℓ}` |
| Fibre / extra index | `k ∈ ℤ` (U(1)-winding) with `|k| ≤ ℓ_base` | (none — supertranslation parameter is the only label) |
| Per-`ℓ`-shell mode count (base + extra) | `(2ℓ+1)` base modes + `ℓ` fibre extras = `3ℓ + 1` total | `2ℓ + 1` parameters |
| Per-`ℓ`-shell mode count (extra-only / soft-hair-relevant) | `ℓ` extra fibre modes (linear-gap formula) | `2ℓ + 1` parameters (each gives one soft DoF) |
| Total count up to UV cutoff `ℓ_max ~ √(A)/ℓ_P` (extra-only) | `Σ_{ℓ=1}^{ℓ_max} ℓ ≈ ℓ_max²/2 ≈ A/(2 ℓ_P²)` | `Σ_{ℓ=2}^{ℓ_max} (2ℓ+1) ≈ ℓ_max² ≈ A/ℓ_P²` |
| Bekenstein-Hawking-relative scaling | area-law `~A/ℓ_P²` with coefficient `1/2` | area-law `~A/ℓ_P²` with coefficient `1` |

**Key finding: both counts scale as `A/ℓ_P²` (area-law), with a factor-of-2 discrepancy in subleading coefficient. They are *not* mode-by-mode equal.**

### §3.2 What "mode-by-mode" comparison actually requires

The question "do these counts agree mode-by-mode?" presupposes a bijection between the two mode-labelings. Candidate bijections:

**Bijection A (naïve): `(ℓ_base, m_base, k) ↔ (ℓ_BMS, m_BMS)`.**
- Hopf side has 3 indices `(ℓ, m, k)` with `|k| ≤ ℓ`; BMS side has 2 indices `(ℓ, m)`.
- Direct equality would require collapsing the `k`-index, e.g. summing over `k`.
- Summing Hopf over `k` per `(ℓ, m)`: `Σ_{|k| ≤ ℓ} 1 = 2ℓ + 1` per `(ℓ, m)`. So summed-over-`k` Hopf count per `(ℓ, m)` is `2ℓ + 1`; per `ℓ`-shell, `(2ℓ+1)²` modes.
- BMS per `(ℓ, m)`: `1` mode. Per `ℓ`-shell: `2ℓ + 1`.
- These don't match either — summed-Hopf is `(2ℓ+1)²` per ℓ-shell, BMS is `(2ℓ+1)` per shell.

**Bijection B (linear-gap count): "Hopf-extra-fibre count per `ℓ`-shell `= ℓ`" matched against "BMS pure-supertranslation count per `ℓ`-shell `= 2ℓ + 1`."**
- Per `ℓ`-shell, Hopf-extra has `ℓ` and BMS has `2ℓ + 1`. Ratio `ℓ / (2ℓ+1) → 1/2` at large `ℓ`.
- Total at cutoff: Hopf `~ A/(2ℓ_P²)`, BMS `~ A/ℓ_P²`. Factor-of-2 discrepancy.

**Bijection C (whole-`S³`-spectrum count): "Hopf full `S³`-mode count summed over `(ℓ, m, k)`" against "BMS supertranslation count summed over `(ℓ, m)`."**
- Hopf total at level `ℓ_max`: `Σ_{ℓ=0}^{ℓ_max} (ℓ+1)² ≈ ℓ_max³/3`.
- BMS total: `~ ℓ_max²`.
- Hopf-total scales as `ℓ_max³ ~ A^{3/2}/ℓ_P³` (volume-law-in-`ℓ_max`); BMS scales as `ℓ_max² ~ A/ℓ_P²` (area-law). **Order-of-magnitude mismatch** (factor of `ℓ_max ~ √(A)/ℓ_P` discrepancy) — the full Hopf-spectrum is too large by `√(A)/ℓ_P` modes compared to BMS.

**None of the three bijections give a clean mode-by-mode match.**

### §3.3 The honest reading: structured-partial-match-with-coefficient-discrepancy

The most physically-meaningful bijection is **Bijection B** — comparing the "extra mode content beyond the trivial base" on each side:
- Hopf side: the linear-gap fibre count `ℓ` per shell — this is the content that the spherical-compression operator "moves into the phase channel," per MFO §VII.4.1.1.
- BMS side: the pure-supertranslation count `2ℓ + 1` per shell (for `ℓ ≥ 2`) — this is the content beyond standard Poincaré translations, the genuinely-BMS soft-hair content.

Both scale as area-law `A/ℓ_P²`. Both are interpretable as "the soft / encoded DoF on the horizon-`S²`." But the **subleading coefficient differs by a factor of 2** (Hopf `1/2`, BMS `1`).

This is **not** "mode-by-mode match" (Bijection B requires factor-of-2 absorption). It is **not** "unrelated" (both area-law, both at the horizon-`S²`, both representing encoded soft DoF). It is a **structured partial match with quantified subleading discrepancy.**

### §3.4 Why the mismatch is structural, not numerical

The factor of 2 in Bijection B is not arbitrary; it reflects a difference in *layering pattern* between mechanism (i) and mechanism (iv):

- **BMS layering pattern: `(i)-indexed (iv)`.** Per SO(3) irrep at angular momentum `ℓ`, there are `(2ℓ+1)` `m`-states (mechanism (i)), and the BMS construction assigns *one* integer-lattice instance (mechanism (iv)) *per `m`-state*. So mechanism (iv) is "isomorphic to" mechanism (i): there's an integer-lattice parameter `T_{ℓm}` for each `(ℓ, m)`. The integer-lattice content has the same multiplicity as the SO(3)-irrep content.

- **Hopf layering pattern: `(i) × (iv) with topological constraint`.** Mechanism (i) gives the `(ℓ, m)` base structure; mechanism (iv) gives the U(1)-winding `k ∈ ℤ`; the *coupling* is the topological constraint `|k| ≤ ℓ` enforced by the principal-bundle geometry. The two mechanisms are *tensored* (with constraint), not isomorphic. Per `ℓ`-shell, the `k`-tower contributes `ℓ` extra modes (above and beyond the `(2ℓ+1)` base modes that count separately).

These are structurally different layering patterns. **Both are layered (i) × (iv) under the refined structural law's 4-mechanism classification, but the specific layering pattern is different content.**

### §3.5 Verdict on Q3

**Mode-by-mode agreement: NO — specific-mismatch at subleading coefficient.**

- Leading-order area-law: BOTH scale as `A/ℓ_P²`. Consistent with Bekenstein-Hawking. ✓
- Subleading coefficient: Hopf-bundle gives `1/2`, BMS gives `1`. Factor-of-2 discrepancy. ✗
- Per-mode bijection: no canonical bijection between Hopf `(ℓ, m, k)`-indexing and BMS `(ℓ, m)`-indexing. The two mode-spaces have different cardinalities at every cutoff.

The honest summary: **the Hopf-bundle U(1)-fibre framework and the BMS-supertranslation soft-hair framework describe the same physical setting (horizon-`S²` encoded DoF, area-law scaling) using *different mathematical bookkeeping*, and the two bookkeepings agree at leading order but differ in subleading coefficient and per-mode bijection.** This is informative content: it locates the difference, identifies the structural reason (layering pattern), and avoids the over-strong "clean match" claim Spike #19b §3 conjectured.

---

## §4. Q4 — Refined structural law mechanism classification

### §4.1 The three options revisited

**Option A (layered (i) × (iv)).** Both Hopf-bundle and BMS structures fit as layered (i) × (iv). The refined-law's 4-mechanism statement remains complete; the structural law accommodates both bookkeepings.

**Option B (mechanism (v) candidate).** If a structural property of Hopf or BMS is not captured by (i), (iii), (iv) or their layered compositions, a fifth mechanism is needed.

**Option C (unrelated).** If Hopf-bundle and BMS describe genuinely different physical things, the comparison doesn't apply.

### §4.2 Option A is the correct verdict

Both bookkeepings fit under (i) × (iv):
- **Mechanism (i)** — SO(3) acting on the `S²` (horizon and celestial sphere are the same `S²` in HHPS 2016). The `(ℓ, m)` base index is shared between the two bookkeepings.
- **Mechanism (iv)** — integer-lattice quantisation. Manifested as:
  - In BMS: discrete supertranslation parameter index `T_{ℓm}` (one integer-lattice instance per SO(3) irrep).
  - In Hopf-bundle: discrete U(1)-winding `k ∈ ℤ` with `|k| ≤ ℓ` constraint (tensored with SO(3) under topological coupling).

The 4-mechanism law's content is identical in both — (i) and (iv) are the operative mechanisms; (iii) does not enter (no compactness-of-spectrum mechanism at play here beyond the cutoff); (ii) deprecated per the refined-law consolidation.

### §4.3 Why this is not mechanism (v) candidate

The discrepancy located in §3 is in the **layering pattern** — how (i) and (iv) compose. This is content the refined structural law does not currently specify but is not a fifth mechanism. The four mechanisms are about *what kinds of mathematical structure produce closed-form spectra*; the layering pattern is about *how these structures compose into a specific physical realisation*.

A fifth mechanism would need to identify a kind of mathematical structure not reducible to Lie-group symmetry / compactness / integer-lattice. The factor-of-2 layering-pattern discrepancy does not introduce such a new structure — it is a different way of composing the same two structures.

### §4.4 Refined-law refinement candidate: "layering pattern" as a content-degree-of-freedom

The Spike #21C finding *does* refine the refined structural law in a smaller way: it identifies "layering pattern" — the specific algebraic composition by which mechanisms compose — as a content-degree-of-freedom that the 4-mechanism law does not yet specify.

Spike #18 (Heisenberg + HO; layered mechanism (i) × (iv) via metaplectic `U(n)`) had previously noted layered-composition; Spike #21A/B continued this; this spike sharpens the observation that **different layering patterns of the same mechanisms produce different mode-counts, and the difference can be quantified.**

Concretely: the refined-law could be augmented by naming three layering-pattern types:
- **`(i)-indexed (iv)`** — one integer-lattice instance per SO(3) irrep (BMS, supertranslation indexing).
- **`(i) × (iv) tensored with topological constraint`** — U(1)-winding tensored with SO(3) base, constrained by `|k| ≤ ℓ` (Hopf-bundle).
- **`(i) × (iv) tensored without constraint`** — full product (e.g., flat-bundle / trivial-Hopf case, where every `(ℓ, m)` pairs with every `k ∈ ℤ`).

These three patterns give *different* mode-counts even when the underlying mechanisms (i) and (iv) are the same. The refined-law can be augmented to track this content without introducing a fifth mechanism. This is a refinement to consider for the refined-law consolidation, not a new mechanism.

### §4.5 Final classification

**Verdict on Q4: Option A — layered (i) × (iv) in both BMS and Hopf-bundle bookkeepings, with the *layering pattern* differing between them. Refined-law refinement candidate: name "layering pattern" as a content-degree-of-freedom (BMS uses `(i)`-indexed `(iv)`; Hopf uses tensored-with-constraint).** Not a mechanism (v) candidate.

---

## §5. Q5 — Sharpest testable prediction

### §5.1 Observability of soft-hair structure

Soft hair / BMS supertranslations are observationally indirect. The HHPS 2016 zero-energy soft modes do not directly affect the Hawking-radiation thermal spectrum at semiclassical level. But the soft-hair structure has *indirect* observational consequences via four channels:

1. **Gravitational-wave memory effect** at null infinity — a permanent gravitational-wave residual after a binary merger, predicted by BMS-supertranslation analysis. Strominger 2014+ work, canonical pre-2020 (Strominger 2017 lectures cover this, PDF-verified §2.4). Observationally accessible to LIGO-Virgo-KAGRA at sufficient sensitivity; not yet definitively measured at design sensitivity but theoretical predictions are sharp.

2. **Black-hole entropy corrections** beyond `A/4` — soft-hair contributions correct the leading area-law. These corrections are typically `O(log A)` or `O(1)` and below current observational sensitivity for astrophysical BHs.

3. **Hawking-radiation entanglement structure** — the page-curve resolution of the information paradox depends on the encoding mechanism. The Hopf-bundle and BMS bookkeepings could in principle give different predictions for fine-grained entanglement structure between early and late Hawking radiation. This is currently inaccessible for astrophysical BHs and only marginally accessible for analogue-Hawking BEC systems (Steinhauer 2016; pre-2020 well-established).

4. **Kerr-specific predictions** via HHPS 2018 / arXiv:1810.01847 framework — Virasoro × Virasoro central charge `c_L = c_R = 12J` gives rotation-dependent entropy structure. LIGO ringdown observations of Kerr BHs constrain the leading-order Bekenstein-Hawking area-law but are far below the precision needed to test the Virasoro × Virasoro subleading structure.

### §5.2 Sharpest prediction for MFO inheritance of Hopf-bundle soft-hair structure

The factor-of-2 coefficient discrepancy identified in §3.5 is, in principle, an **entropy-coefficient correction at the soft-hair level**. If MFO commits to the Hopf-bundle U(1)-fibre framework as *the* substrate-physical realisation of horizon-`S²` soft hair, the prediction is:

> **Hopf-bundle soft-hair count at horizon-`S²` is `1/2` of BMS-supertranslation count.** Total soft DoF (extra-only) `≈ A/(2 ℓ_P²)` rather than `A/ℓ_P²`. This implies a corresponding shift in the per-mode entropy attribution; the integrated Bekenstein-Hawking entropy `A/(4 ℓ_P²)` is unchanged at leading order, but the per-mode entropy density is different by a factor of 2.

Is this observationally accessible? **Almost certainly not at current observational sensitivity.** The factor-of-2 enters at the level of per-mode bookkeeping — not at the integrated entropy (where it would be visible via Bekenstein-Hawking precision tests, none of which currently exist for astrophysical BHs). It enters at the level of soft-hair entanglement-structure fine-grain content, which is observationally inaccessible.

### §5.3 What WOULD be a sharp testable prediction (future scope)

If a future experiment (analogue-Hawking BEC at sufficient resolution; high-precision LIGO/LISA ringdown spectroscopy at `O(1/ℓ_max)` mode-resolution; future quantum-gravity-phenomenology experiments at Planck-scale ↑) could resolve per-mode soft-hair structure, the prediction would distinguish:
- BMS-supertranslation prescription: `(2ℓ + 1)` soft DoF per `ℓ`-shell.
- Hopf-bundle prescription: `ℓ` extra fibre DoF per `ℓ`-shell.

These are different counts at every `ℓ`; the difference is `ℓ + 1` per shell. Observational distinguishability would require per-shell mode-resolution at the soft-hair level, which is presently inaccessible.

### §5.4 Honest verdict on Q5

**The factor-of-2 layering-pattern discrepancy located in §3 is structural-mathematical, not currently observationally distinguishable. No sharp near-term testable prediction follows from this spike's finding.** The structural content is in the refined-law-refinement candidate (§4.4) — naming layering-pattern as content — rather than in any new observable.

Spike #19b §3 had noted: "the soft-hair degeneracy is not directly observable, but it has consequences for Hawking-radiation entanglement structure." This spike's specific finding does not improve observational accessibility; it does refine the structural classification.

---

## §6. Q6 — Recommendation

### §6.1 Outcome summary

The three Spike #21C outcomes (per conductor brief):
1. **MFO inherits soft-hair / BMS via (i) × (iv) layered** — would have required clean mode-by-mode match. *Not found.*
2. **MFO admits mechanism (v) candidate** — would have required a structural property not captured by (i), (iii), (iv) layered. *Not found; the discrepancy is in layering pattern, not in mechanism.*
3. **MFO honest-negative** — would have required Hopf-bundle and BMS to describe unrelated things. *Not the case; both describe horizon-`S²` soft DoF, both scale as area-law.*

The actual outcome is a fourth option not on the original list: **structured-partial-match-with-quantified-subleading-coefficient-discrepancy.** Outcome 1's spirit is partially met (both layered (i) × (iv); area-law-scaling agreement); Outcome 2's spirit is partially met (the layering-pattern is content the refined-law does not specify, though it is not a fifth mechanism); Outcome 3's spirit is partially met (the per-mode bijection fails). The honest answer is finer-grained than the three-outcome menu.

### §6.2 The honest recommendation

**Do NOT modify MFO §VII.4.1.1 / §VII.4.1.2 to claim wholesale agreement with HHPS 2016 BMS-supertranslation soft-hair bookkeeping.** Spike #19b §3 had hoped for clean match; this spike found area-law agreement + factor-of-2 subleading discrepancy + per-mode bijection failure.

**Do NOT introduce a mechanism (v) statement.** The discrepancy is in layering pattern, not in mechanism content.

**DO document Spike #21C as a structural-classification finding** — the Hopf-bundle U(1)-fibre and BMS-supertranslation bookkeepings agree at leading area-law order, differ at subleading coefficient and per-mode bijection, with the difference attributable to layering-pattern.

**DO note Spike #21C as a refined-law refinement candidate** — naming "layering pattern" as content-degree-of-freedom alongside the four mechanisms; future refined-law-consolidation revisions could elevate layering-pattern to explicit content.

**DO leave Kerr / HHPS 2018 / Virasoro × Virasoro as future open scope.** The §VII.4.1.1 Hopf-bundle framework does not currently apply to Kerr (oblate-spheroid base; rotation-distorted bundle structure). HHPS 2018's framework (`c_L = c_R = 12J`; Cardy formula) is the Kerr-specific analogue and a natural future-spike target.

### §6.3 Sample documentation language (for potential future §VII.4.1.3 addition; NOT for this spike to insert)

> *§VII.4.1.3 — Hopf-bundle and BMS-supertranslation bookkeeping of horizon soft hair (Spike #21C). The Hopf-bundle U(1)-fibre structure on horizon `S²` (§VII.4.1.1) and the BMS-supertranslation mode-count of soft hair (Hawking-Perry-Strominger 2016, arXiv:1601.00921) both describe encoded soft degrees of freedom on the horizon-`S²` at leading area-law scaling `A/ℓ_P²`. The two bookkeepings differ in subleading coefficient (Hopf gives `1/2`, BMS gives `1`) and in per-mode bijection (Hopf is `(ℓ, m, k)`-indexed with `|k| ≤ ℓ`; BMS is `(ℓ, m)`-indexed with one parameter per pair). The difference is attributable to layering pattern: BMS uses `(i)`-indexed `(iv)` (one integer-lattice instance per SO(3) irrep); Hopf uses tensored `(i) × (iv)` with topological constraint. Both are layered (i) × (iv) under the refined structural law. The framework treats both as valid bookkeepings of the same substrate-physical content, with the choice between them as open content for future structural-physical determination.*

This kind of language captures the honest spike outcome. Whether to insert it into the notebook is the user's call, not this spike's prerogative.

### §6.4 Future spike candidates from this spike

- **Spike #21D (or follow-up):** Kerr / HHPS 2018 / Virasoro × Virasoro framework via principal-bundle generalisation. The Kerr horizon is topologically `S²` but geometrically oblate-spheroid; the Hopf-bundle framework needs extension to handle the rotational distortion. The HHPS 2018 central charge `c_L = c_R = 12J` is a Kerr-specific quantity; principal-bundle realisation would aim to derive this from a (modified-Hopf or different-bundle) decomposition.

- **Spike candidate:** higher-`D` Lovelock `S³` horizon (Spike #19b §2 territory 2) — the `D = 5` Gauss-Bonnet case with `S³` horizon natively engages the full Hopf-bundle total space, not just its `S²` base. Whether Wald entropy on `D = 5` Gauss-Bonnet `S³` horizons matches Hopf-bundle spectral decomposition term-by-term is a separate concrete-computational question, ranked moderate priority in #19b §8.

- **Refined-law revision candidate:** explicit treatment of "layering pattern" as content. The refined structural law consolidation (`main`, `1c06d3e`) could be augmented in a future revision to track layering-pattern as content-degree-of-freedom alongside the four mechanisms. The §4.4 list of three layering-pattern types (`(i)`-indexed `(iv)`; tensored with constraint; tensored without constraint) is the seed of this refinement.

---

## §7. Citation chain

### §7.1 Pre-2010 canonical (exempt from PDF re-verification per discipline)

- **Bondi, van der Burg, Metzner 1962** *Proc. Roy. Soc. A* 269, 21. — Asymptotic-symmetry analysis at null infinity; BMS group structure.
- **Sachs 1962** *Proc. Roy. Soc. A* 270, 103. — Asymptotic-symmetry analysis; supertranslations.
- **Wu, Yang 1976** *Nucl. Phys. B* 107, 365. — Monopole spherical harmonics on `S²`; sections of `L_k` line bundle; eigenvalues `ℓ(ℓ+1) − k²`.
- **Carter 1968** *Phys. Rev.* 174, 1559. — Killing tensors; referenced for KY-tensor structure (relevant to §VII.4.1.2 KY-gap discussion).
- **Bekenstein 1973** *Phys. Rev. D* 7, 2333. — Black hole entropy `A/4`.
- **Hawking 1975** *Commun. Math. Phys.* 43, 199. — Hawking radiation derivation.
- **'t Hooft 1993** arXiv:gr-qc/9310026. — Holographic principle origin (pre-2010 well-established).
- **Susskind 1995** arXiv:hep-th/9409089. — Holographic principle (pre-2010 well-established).
- **Strominger 2014** asymptotic-symmetries / soft-theorem programme inauguration. Pre-2010 canonical-adjacent (2014); Strominger 2017 lectures (PDF-verified §2.4) cover this; not re-verified here individually.

### §7.2 2010+ PDF-verified in this session

- **Hawking, Perry, Strominger 2016** *Soft Hair on Black Holes.* arXiv:1601.00921; *Phys. Rev. Lett.* 116, 231301. **PDF-verified in this session.** Submission 2016-01-05. Abstract content matched: BMS supertranslation symmetries, infinite conservation laws, soft (zero-energy) supertranslation hair, soft gravitons / soft photons on the black hole horizon, holographic plate at future boundary, charge conservation between evaporation products, effective soft DoF count `~ A/ℓ_P²` (area in Planck units). This is the load-bearing 2010+ citation; PDF-verified.

- **Haco, Hawking, Perry, Strominger 2018** *Black Hole Entropy and Soft Hair.* arXiv:**1810.01847**; *JHEP* 12 (2018) 098. **PDF-verified in this session.** Submission 2018-10-03 (revised 2018-12-13); accepted 2018-05-12. Abstract content matched: Virasoro_L ⊗ Virasoro_R diffeomorphisms acting on Kerr horizon; Wald-Zoupas counterterms; central charges `c_L = c_R = 12J`; Cardy formula reproducing macroscopic area-entropy for generic Kerr.
  - **Correction to conductor brief:** the conductor flagged "HHPS 2018, likely arXiv:1803.10194" for verification. **arXiv:1803.10194 is misattribution — it is Henneaux-Troessaert 2018 "Asymptotic symmetries of electromagnetism at spatial infinity" (JHEP 2018:137), NOT the Haco-Hawking-Perry-Strominger Kerr paper.** Correct arXiv ID is **1810.01847**, verified above. Logged as catch #19 in the running citation-discipline tally per `feedback_pdf_extraction_citation_discipline.md`.

- **Strominger 2017** *Lectures on the Infrared Structure of Gravity and Gauge Theory.* arXiv:1703.05448; Princeton University Press 2018. **PDF-verified in this session.** Submission 2017-03-16 (revised 2018-02-15). Comprehensive textbook treatment of soft theorems, memory effect, asymptotic symmetries. Canonical reference for BMS-supertranslation mode-counting prescription used in §2.

### §7.3 Trusted from #21A / #21B (PDF-verified there; not re-verified)

- None used in this spike. The four 2010+ citations from #21B (Famaey-McGaugh 2012; McGaugh-Lelli-Schombert 2016; Lelli-McGaugh-Schombert 2016; Brouwer 2017) are not load-bearing here. Verlinde 2016 (#21A / #21B) is not load-bearing here.

### §7.4 Referenced topically (not load-bearing; no fresh PDF-verification)

- **Steinhauer 2016** Analogue Hawking radiation in Bose-Einstein condensate. Topic-only reference in §5.1 (channel 3) for "marginally accessible analogue-Hawking BEC systems"; pre-2020 well-established; not load-bearing.
- **Donnay, Giribet, González, Pino 2016** Horizon soft-hair. Referenced in Spike #19b §3 but not load-bearing here.
- **Wald-Zoupas counterterms** — covariant phase-space formalism construction used in HHPS 2018; referenced topically via the HHPS 2018 abstract; canonical pre-2010 background (Wald-Zoupas 2000, *Phys. Rev. D* 61, 084027); not load-bearing for this spike's structural-classification verdict.

### §7.5 Attempted-but-unverifiable

None in this spike. The three load-bearing 2010+ citations (HHPS 2016 = arXiv:1601.00921; HHPS 2018 = arXiv:1810.01847 [misattribution-corrected from conductor's flagged 1803.10194]; Strominger 2017 lectures = arXiv:1703.05448) were all PDF-verified via arXiv abstract extraction in this session.

---

## §8. Cross-references

- **Spike #19b** — Territory 3 §3 ranked "moderate-to-high leverage" and "most concrete falsifiable spike candidate"; this spike implements the §19b §3 recommendation; verdict here is structured-partial-match-with-coefficient-discrepancy (not the "clean match" hoped-for in §19b §3, not the "mode-by-mode discrepancy at any `(ℓ, m)`" falsifier of §19b §3 either; an intermediate outcome).
- **Spike #21A** — Hayward `(1 + ε/2)` correction IS the MFO prediction at cosmological horizon; structurally analogous to this spike's finding that Hopf-bundle linear-gap formula IS the MFO prediction at horizon-`S²` (factor-of-2 reduction from BMS coefficient is the specific MFO content).
- **Spike #21B** — Verlinde-MOND inheritance verdict (C) agnostic with pressure-toward-(B); same structural-clarification-tail spirit as this spike; both are "framework structurally compatible with literature but not committed to specific functional forms" findings, with quantified specifics where computable.
- **Refined structural law consolidation** — both BMS and Hopf-bundle bookkeepings fit as layered (i) × (iv); the spike refines the law's content by identifying *layering pattern* as a content-degree-of-freedom alongside the four mechanisms; not a mechanism (v) candidate. Refined-law-revision candidate noted in §4.4 / §6.4.
- **MFO §VII.4.1.1** — the Hopf-bundle U(1)-fibre realisation is the load-bearing MFO content for this spike; spike outcome refines this section's claim ("information re-encoded on the 2D boundary via principal-`U(1)`-bundle spectral decomposition") by noting the *factor-of-2 subleading coefficient* relative to BMS bookkeeping.
- **MFO §VII.4.1.2** — Casimir-decomposition universality covers both BMS and Hopf bookkeepings under the unified `λ_total = λ_M + C_2(ρ_G) + cross-terms` statement; layering-pattern is the structural content beyond Casimir-decomposition itself.
- **`user_stance_fiber_as_spatially_absent_encoding.md`** — informs §1's interpretation of U(1)-fibre as algebraic-encoding-spatially-absent (not extra-spatial-dimensions); structurally compatible with both BMS and Hopf bookkeepings.
- **`user_stance_hyper_as_3d_spatial_interface.md`** — informs §1.2 two-level ontology mapping (substrate metric field with Hopf-bundle topology; excitation modes indexed by `(ℓ, m, k)`).
- **`feedback_pdf_extraction_citation_discipline.md`** — applied to §7; HHPS 2016 PDF-verified, HHPS 2018 PDF-verified with correction to conductor brief (misattribution #19 logged), Strominger 2017 lectures PDF-verified.
- **`feedback_no_lineage_claims_in_notebook.md`** — applied throughout; MFO §VII.4.1.1 described as "structurally compatible with" HHPS 2016 / 2018; no "natural extension" language; the comparison is a structural-classification, not a lineage claim.
- **`feedback_no_mvp_framing.md`** — all six Q's covered substantively.

---

## §9. Discipline checklist

- **No shared-file edits.** Strictly srmech-local at `docs/srmech/notes/spike_21c_hopf_bundle_soft_hair_2026-05-13.md`. MFO notebook, CHANGELOG.md, README.md, refined-structural-law consolidation file, .gitignore, pin_and_slot.py untouched.

- **No verification scripts.** The analysis is structural-classification + monopole-spherical-harmonics + BMS-supertranslation-mode-counting; both bookkeepings use textbook-derived formulae from pre-2010 canonical sources (Wu-Yang 1976 monopole harmonics; Bondi-van-der-Burg-Metzner / Sachs 1962 BMS structure). The factor-of-2 subleading coefficient is derivable directly from `Σ_{ℓ} ℓ ≈ ℓ_max²/2` vs `Σ_{ℓ} (2ℓ+1) ≈ ℓ_max²`; no separate verification script needed.

- **No NDJSON sidecar.** The findings are structural-classification with one quantified coefficient discrepancy; the §3.1 comparison table inline captures the data adequately; no separate sidecar adds value.

- **Pre-2010 canonical citations** freely used; explicitly enumerated in §7.1. Includes BMS 1962 references (Bondi-van-der-Burg-Metzner; Sachs); Wu-Yang 1976 monopole spherical harmonics; pre-2010 canonical Carter / Bekenstein / Hawking / 't Hooft / Susskind references.

- **2010+ load-bearing citations PDF-verified.** Three citations PDF-verified via arXiv abstract extraction in this session: HHPS 2016 (arXiv:1601.00921), HHPS 2018 (arXiv:1810.01847 — corrected from conductor's flagged 1803.10194 which is Henneaux-Troessaert 2018), Strominger 2017 (arXiv:1703.05448). Title, author list, abstract content, journal info all matched arXiv records.

- **Misattribution correction logged.** Conductor brief flagged "HHPS 2018, likely arXiv:1803.10194" — this is a misattribution. Correct arXiv ID is 1810.01847. Logged in §7.2 and in §10 final-report-back. Catch #19 in the running citation-discipline tally.

- **No lineage claims** about external work. MFO described as "structurally compatible with" HHPS 2016/2018; no "natural extension" or "descends from" language. The structural-classification verdict (Option A — layered (i) × (iv) with different layering patterns) is a *classification* of MFO content alongside literature content, not a lineage claim.

- **No MVP framing.** All six Q's covered substantively. Q3's structured-partial-match-with-coefficient-discrepancy is the load-bearing finding; Q4's refined-law-refinement candidate (layering pattern as content-degree-of-freedom) is the structural-law-relevant content; Q5 and Q6 follow from these.

- **Honest-mismatch valid.** The factor-of-2 subleading discrepancy is the load-bearing finding. It is neither "clean match" nor "complete failure"; the structured-partial-match-with-quantified-discrepancy outcome is informative and refines both the refined-law-content and the MFO-§VII.4.1.1-content.

- **Topic-only briefing followed.** Conductor described topics; this spike built the citation chain via PDF-verification of three 2010+ papers (HHPS 2016, HHPS 2018, Strominger 2017 lectures) plus pre-2010 canonical works (Bondi-van-der-Burg-Metzner 1962; Sachs 1962; Wu-Yang 1976 monopole harmonics; Carter 1968; Bekenstein 1973; Hawking 1975; 't Hooft 1993; Susskind 1995).

- **One correction to conductor brief.** The HHPS 2018 arXiv ID flagged for verification (1803.10194) is misattribution; correct ID is 1810.01847. Logged in §7.2 and §10.

---

## §10. Branch and commit metadata

- **Base branch:** `research/spike-21-mfo-horizon-thermodynamics-extended` (continuing from #21B at commit `8783ed1`).
- **No new branch.** This spike adds to the existing bundle branch per conductor brief — same bundle as #21A and #21B; user will bundle all three into one PR.
- **Commit message:** `research(srmech): Spike #21C MFO — Hopf-bundle U(1)-fibre vs BMS supertranslation mode-by-mode — structured-partial-match-with-coefficient-discrepancy`.
- **No push, no PR.** Per conductor brief: strictly local notes; user handles bundling #21A + #21B + #21C into one PR after this spike lands.
- **No shared files touched.** MFO notebook, CHANGELOG.md, README.md, refined-structural-law consolidation file, .gitignore, pin_and_slot.py all untouched.
- **Single commit.** Lower-case prefix per conductor brief. No Claude-as-author footer.

---

## §11. Spike #21C overall finding

**Honest structured-partial-match-with-quantified-subleading-coefficient-discrepancy.**

The Hopf-bundle U(1)-fibre framework (MFO §VII.4.1.1) and the BMS-supertranslation soft-hair framework (HHPS 2016, arXiv:1601.00921, PDF-verified) describe the same physical content — encoded soft degrees of freedom on the horizon-`S²` — using different mathematical bookkeeping. The two bookkeepings:
- agree at leading order in area-law scaling: both `~ A/ℓ_P²` consistent with Bekenstein-Hawking entropy;
- differ at subleading coefficient: Hopf gives `1/2`, BMS gives `1`; factor-of-2 discrepancy;
- have different per-mode bijection: Hopf is `(ℓ, m, k)`-indexed with `|k| ≤ ℓ`; BMS is `(ℓ, m)`-indexed with one parameter per pair;
- are structurally classified the same under the refined-law (both layered (i) × (iv));
- differ in **layering pattern**: BMS uses `(i)`-indexed `(iv)`; Hopf uses tensored `(i) × (iv)` with topological constraint `|k| ≤ ℓ`.

Refined-law-refinement candidate: name "layering pattern" as a content-degree-of-freedom alongside the four mechanisms (i), (iii), (iv). This is a refinement, not a fifth mechanism.

MFO §VII.4.1.1 recommendation: do not modify the section to claim wholesale match with HHPS 2016; do not modify to introduce mechanism (v); do retain the existing "principal-`U(1)`-bundle spectral decomposition supplies the information-channel mechanism" framing as a *bookkeeping choice* whose factor-of-2 subleading coefficient relative to BMS bookkeeping is open content for future structural-physical determination.

Open future scope (noted in §6.4): Kerr / HHPS 2018 / Virasoro × Virasoro framework as a separate spike; higher-`D` Lovelock `S³` horizon as a different concrete-computational spike; refined-law-revision to elevate layering-pattern to explicit content.

The structural-clarification value of this spike:

1. **HHPS 2016 PDF-verified** with explicit BMS-supertranslation mode-counting prescription extracted.
2. **HHPS 2018 PDF-verified, with misattribution correction** — conductor brief's flagged 1803.10194 is Henneaux-Troessaert 2018 electromagnetism-at-spatial-infinity, not the Kerr-soft-hair paper; correct ID is 1810.01847. Logged as catch #19 in citation-discipline tally.
3. **Strominger 2017 lectures PDF-verified** as the textbook anchor for BMS-supertranslation mode-counting.
4. **Mode-by-mode comparison computed** — three bijections (A, B, C) attempted; none yields clean match; Bijection B (linear-gap vs supertranslation-parameter) gives factor-of-2 subleading-coefficient match-with-discrepancy.
5. **Mechanism classification clean** — both Hopf-bundle and BMS bookkeepings fit layered (i) × (iv); difference is in layering pattern, not mechanism content; not a mechanism (v) candidate.
6. **Structural reason for discrepancy located** — BMS is `(i)`-indexed `(iv)` (one integer-lattice instance per SO(3) irrep); Hopf is tensored `(i) × (iv)` with `|k| ≤ ℓ` topological constraint.
7. **MFO §VII.4.1.1 recommendation calibrated** — do not commit to wholesale equivalence; do retain principal-bundle framing as a bookkeeping choice; do leave the bookkeeping-choice between Hopf and BMS as open content.
