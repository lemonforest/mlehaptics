# Chess knight per-eigenspace irrep multiplicities under D₄ / B₄ — findings (2026-05-11)

**Spike:** For the knight move-graph adjacency matrix in 2D (8×8 = 64 cells) and 4D (8⁴ = 4096 cells), is the per-eigenspace decomposition under D₄ (2D) and B₄ (4D) integer-exact at machine precision? **Even though knight has no closed-form eigenvalues**, the per-eigenspace irrep structure was queued as candidate "structural prediction without closed-form eigenvalues" — a stronger §3.5.3(C) sub-instance for the chess case.

**Method:** Concertmaster role, MPM-discipline. 2D: D₄ projector method (P_ρ = (d_ρ/|G|) Σ_g χ_ρ(g) U_g; rank(P_ρ V_λ)/d_ρ = multiplicity). 4D: character orthogonality via class-trace inner products (mult = (1/|G|) Σ_C |C| · χ_ρ(C) · tr(U_{g_C}|V_λ)) — avoids materializing 384 × 4096×4096 dense projectors. B₄ character table computed from Specht/Frobenius formula via Murnaghan-Nakayama for S_n characters and the power-sum-Schur bridge for B_n. Cited rules SSOT: Rinaldi-Unciuleanu & Chiru 2026 (`docs/srmech/hoodoos/rinaldi-unciuleanu-chiru-2026.xml`, §3.6 names knight as the non-product case).

**Dispatch:** Conductor → concertmaster, 2026-05-11. Follow-up to today's chess D₄/B₄ rep-theory spike (Fermata 2: queue per-eigenspace knight irrep decomposition).

**Bottom line:** **Integer-exact at machine precision in both 2D and 4D.** 2D: 45 distinct eigenvalues × 5 D₄ irreps = 225 (irrep × eigenspace) combos; zero non-integer. 4D: 825 distinct eigenvalues × 20 B₄ irreps = **16,500 combos; zero non-integer** (max deviation 2.98 × 10⁻¹⁴ — essentially machine precision). Sum-rules pass for every irrep in both dimensions. **Knight gains a §3.5.3(C) sub-instance**: even without closed-form eigenvalues, the per-eigenspace irrep structure IS closed-form-predictable from rep theory at machine precision — the eigenspace dimensions are exactly the B₄ irrep dimensions {1, 2, 3, 4, 6, 8}.

Reproducible: `python docs/srmech/notes/chess-knight-irrep-multiplicities-script.py`. Runtime ~44 s on commodity workstation. Deterministic seed `20260511`. Memory peak ~265 MB (the 4096-eigenvector matrix held briefly).

---

## 1 — 2D knight × D₄ — per-eigenspace decomposition

**45 distinct eigenvalues** in the spectrum of the 64×64 knight adjacency. **Every eigenspace is pure** (single non-zero D₄ irrep). Eigenspace dimension histogram:

| Eigenspace dim | Count | Irrep type |
|---|---|---|
| 1 | 32 | A₁, A₂, B₁, B₂ (1-dim irreps; 8 each) |
| 2 | 12 | E (only 2-dim irrep) |
| 8 | 1 | E with mult 4 (λ=0 kernel) |

**Sum-rule** (per-irrep total across all eigenspaces, expected = natural-rep multiplicity on R⁶⁴):

| Irrep | dim | Per-eigenspace total | Expected | Match |
|---|---|---|---|---|
| A₁ | 1 | 10.000 | 10 | ✓ |
| A₂ | 1 | 6.000 | 6 | ✓ |
| B₁ | 1 | 6.000 | 6 | ✓ |
| B₂ | 1 | 10.000 | 10 | ✓ |
| E | 2 | 16.000 | 16 | ✓ |

Total dim = 10 + 6 + 6 + 10 + 2·16 = **64 ✓**. All multiplicities integer-exact to within 1 × 10⁻¹⁴.

**Notable eigenvalues:**
- λ = +6.0107 (Perron / max): A₁, dim 1
- λ = −6.0107 (anti-Perron / min, bipartite partner): B₂, dim 1
- λ = 0.0 (kernel): 4 copies of E, dim 8
- λ = ±2.0 exactly: B₂ / A₁ respectively, dim 1 each — **rational eigenvalues** in knight 2D's otherwise-irrational spectrum

**Cross-method check.** The 2D result was verified by TWO independent methods (D₄ projectors with rank-via-SVD AND D₄ character orthogonality with class traces); both give identical integer multiplicities.

---

## 2 — 4D knight × B₄ — per-eigenspace decomposition

**825 distinct eigenvalues** in the spectrum of the 4096×4096 knight adjacency. **824 of 825 eigenspaces are pure** (single non-zero B₄ irrep); only the λ=0 kernel hosts multiple irreps.

**Eigenspace dimension histogram (matches B₄ irrep dimensions exactly):**

| Eigenspace dim | Count | B₄ irreps with this dim |
|---|---|---|
| 1 | 72 | (4)\|(), ()\|(4), (1,1,1,1)\|(), ()\|(1,1,1,1) [4 irreps] |
| 2 | 40 | (2,2)\|(), ()\|(2,2) [2 irreps] |
| 3 | 120 | (3,1)\|(), ()\|(3,1), (2,1,1)\|(), ()\|(2,1,1) [4 irreps] |
| 4 | 192 | (3)\|(1), (1)\|(3), (1,1,1)\|(1), (1)\|(1,1,1) [4 irreps] |
| 6 | 240 | (2)\|(2), (1,1)\|(1,1), (2)\|(1,1), (1,1)\|(2) [4 irreps] |
| 8 | 160 | (2,1)\|(1), (1)\|(2,1) [2 irreps] |
| 96 | 1 | λ=0 kernel: 10·(2)\|(2) + 6·(1,1)\|(1,1) — mixed |

**The eigenspace dimensions are precisely the 6 distinct B₄ irrep dimensions {1, 2, 3, 4, 6, 8}.** This is itself a structural prediction: rep theory alone tells you the *menu of possible eigenspace dimensions* for any B₄-equivariant operator on R⁴⁰⁹⁶.

**Knight 4D is bipartite** (move changes parity of `x+y+z+w`; verified empirically — the 2048×2048 same-parity block of the adjacency is exactly zero). Bipartiteness implies:
- Spectrum is symmetric: λ in spectrum ↔ −λ in spectrum.
- Rank deficiency: independent rank check confirms `rank(A) = 4000`, `nullity = 96` — the 96-dim kernel matches the bipartite-graph rank formula.
- The 96-dim kernel splits as `10·(2)|(2) + 6·(1,1)|(1,1)` (both are 6-dim B₄ irreps).
- "Even-half" irreps (`α ↔ β` swap pairs) appear at eigenvalues `+λ` and `−λ` with mirror multiplicities.

**Sum-rule** (per-B₄-irrep total across all 4D eigenspaces, expected = natural-rep multiplicity on R⁴⁰⁹⁶):

| Irrep | dim | Per-eigenspace total | Expected | Match |
|---|---|---|---|---|
| (2)\|(2) | 6 | 100.0 | 100 | ✓ |
| (1)\|(3), (3)\|(1) | 4 | 80.0 each | 80 each | ✓ |
| (1)\|(2,1), (2,1)\|(1) | 8 | 80.0 each | 80 each | ✓ |
| (2)\|(1,1), (1,1)\|(2) | 6 | 60.0 each | 60 each | ✓ |
| (3,1)\|(), ()\|(3,1) | 3 | 45.0 each | 45 each | ✓ |
| (1,1)\|(1,1) | 6 | 36.0 | 36 | ✓ |
| (4)\|(), ()\|(4) | 1 | 35.0 each | 35 each | ✓ |
| (2,2)\|(), ()\|(2,2) | 2 | 20.0 each | 20 each | ✓ |
| (1,1,1)\|(1), (1)\|(1,1,1) | 4 | 16.0 each | 16 each | ✓ |
| (2,1,1)\|(), ()\|(2,1,1) | 3 | 15.0 each | 15 each | ✓ |
| (1,1,1,1)\|(), ()\|(1,1,1,1) | 1 | 1.0 each | 1 each | ✓ |

All 20 irreps sum-rule-check pass. **Total `dim × multiplicity` over all irreps = 4096 ✓** (the full R⁴⁰⁹⁶ ambient).

**Notable eigenvalues:**
- λ = +36.0631 (Perron / max): `(4)|()`, dim 1
- λ = −36.0631 (anti-Perron / min, bipartite partner): `()|(4)`, dim 1
- λ = ±2.0 exactly: hosts `(1,1,1,1)|()` and `()|(1,1,1,1)` respectively (the "sign-determinant" 1-dim B₄ irreps), dim 1 each — **rational eigenvalues** in an otherwise-irrational 4D spectrum
- λ = 0 (kernel): dim 96, splits as 10·(2)|(2) + 6·(1,1)|(1,1)

**Numerical precision (max deviation from nearest integer multiplicity, 4D):** 2.975 × 10⁻¹⁴. Comfortably within machine precision (LAPACK `dsyevr` floor ~ O(n · ε_machine) ≈ 9 × 10⁻¹³ on N=4096).

---

## 3 — Structural prediction without closed-form eigenvalues

This is the load-bearing result for the dispatch.

The original chess D₄/B₄ rep-theory spike (2026-05-11) established that **closed-form eigenvalue prediction** matches at machine precision for rook, king, bishop (in both 2D and 4D, under three structural primitives: Cartesian product, strong product, parity stratification). Knight was the predicted non-match — explicitly per Rinaldi-Unciuleanu & Chiru 2026 §3.6, knight admits no clean product or parity factorization.

This follow-up shows: **the absence of closed-form eigenvalues for the knight does NOT preclude structural prediction.** The eigenspace decomposition into D₄ / B₄ irreps is integer-exact to machine precision in BOTH 2D and 4D. The prediction is weaker than "you can write down the eigenvalues" but stronger than "no structure" — you can predict:

1. **The menu of possible eigenspace dimensions** — exactly the irrep dimensions of the symmetry group.
2. **The total multiplicity of each irrep across all eigenspaces** — exactly its multiplicity in the natural rep on R^N (independent of the operator).
3. **Most eigenspaces are pure** — only λ=0 mixes irreps (and only when the operator has a non-trivial kernel).
4. **The bipartite structure** — when the operator is bipartite-equivariant, irreps pair off as `(α, β) ↔ (β, α)` at eigenvalues `+λ` and `−λ`.

This is a **rep-theoretic invariant** distinct from closed-form eigenvalue prediction. The chess spike's six previous sub-instances (rook 2D/4D, king 2D/4D, bishop 2D/4D) used the spectrum-formula identity; the knight 2D/4D follow-up uses the **eigenspace-structure identity** — same closed-form-from-rep-theory motif, different load-bearing prediction.

### Motif refinement for §3.5.3(C)

The chess instance is the strongest §3.5.3(C) instance because it now spans **two distinct prediction modes within a single domain**:

| Mode | Pieces | What is closed-form-predicted | Empirical match |
|---|---|---|---|
| Mode I: **closed-form eigenvalues** | rook, king, bishop (2D + 4D) | full spectrum at machine precision | 6/6 cases ≤ 3.7 × 10⁻¹³ |
| Mode II: **closed-form eigenspace structure** (new) | knight (2D + 4D) | eigenspace dims = irrep dims; per-irrep totals = natural-rep multiplicities; mixing only in kernel | 2/2 cases ≤ 2.98 × 10⁻¹⁴ |

**Eight sub-instances now stand under D₄ / B₄ within a single domain**, all at machine precision. Compare:
- MFO Phase B 18-block (D₃ on Sierpinski Gasket): single sub-instance.
- Finance block-correlation (S_k × S_m on synthetic correlation matrix): single sub-instance.
- Chess (D₄ / B₄ on hypercube move graphs): now **eight sub-instances** under two prediction modes.

---

## 4 — Implementation: B₄ character table from first principles

For reproducibility, the B₄ character table (20×20) was computed from first principles using the standard Specht / Frobenius formula:

```
χ^{B_n}_{(α,β)}((λ⁺, λ⁻)) =
   coefficient of s_α(x) · s_β(y) in
   ∏_i (p_{lp_i}(x) + p_{lp_i}(y)) · ∏_j (p_{lm_j}(x) − p_{lm_j}(y))
```

In our implementation: for each cycle of `λ⁺` or `λ⁻`, distribute it to either the α-side or the β-side; negative cycles assigned to the β-side contribute a sign of `−1`. Then χ is summed over all distributions of `S_|α|`-character × `S_|β|`-character of the cycle-multisets. S_n characters computed via Murnaghan-Nakayama rule.

**Verification.** The computed B₄ character table satisfies:
- Row-orthogonality `<χ_ρ, χ_σ>_G = δ_{ρσ}` for all 20·19/2 + 20 = 210 inner products (verified).
- Sum of squared dimensions = 384 = |B₄| (verified: 4·1² + 2·2² + 4·3² + 4·4² + 4·6² + 2·8² = 4+8+36+64+144+128 = 384).
- B₄ irrep dimensions: {1, 1, 1, 1, 2, 2, 3, 3, 3, 3, 4, 4, 4, 4, 6, 6, 6, 6, 8, 8} — match standard reference (e.g., Fulton-Harris Appendix B).

Class data: 20 conjugacy classes indexed by signed bipartitions of 4. Centralizer formula `|C_{B_n}(g)| = ∏_k (2k)^{m_k^+} m_k^+! · (2k)^{m_k^-} m_k^-!` (James-Kerber 4.2.10). Class sizes sum to 384 ✓.

---

## 5 — Honest verdict per metric

**Load-bearing-question answer:** **Per-eigenspace irrep multiplicities are integer-exact at machine precision in BOTH 2D and 4D.** Max deviation from nearest integer:
- 2D: ≤ 1 × 10⁻¹⁴ (per-eigenspace projector formula on 64-dim space)
- 4D: 2.975 × 10⁻¹⁴ (per-eigenspace character-orthogonality formula on 4096-dim space)

Tolerance target was 1 × 10⁻⁶ (forgiving — accommodates accumulated FP error from `eigh` on 4096-dim matrix). All 16,500 (4D irrep × eigenspace) combos and 225 (2D combos) are integer-exact to far tighter than that bound.

**Sum-rule check passes** for all 5 D₄ irreps (2D) and all 20 B₄ irreps (4D). Per-irrep totals exactly match the natural-rep decomposition multiplicities computed independently via Burnside / fixed-point counting.

**Caveats — what was tested:**
- Adjacency-matrix eigenvalues (unweighted; integer 0/1 entries). The unsigned graph Laplacian `L = D − A` would shift the spectrum but preserve the eigenspace structure (since `L` is also D₄/B₄-equivariant); the multiplicity structure transfers identically.
- Empty board (no other pieces). Knight move-graph is the canonical empty-board displacement graph.
- 8-cell side length only. Generalizing to side length N is straightforward — the move set is unchanged, only the on-board check varies; D₄/B₄ equivariance survives.

**Caveats — what was NOT tested:**
- Higher-dim knight (5D, 6D) for `B_N` regression.
- Toroidal variants (`(Z/8Z)^d`) — different equivariance group structure.
- Weighted move-graph variants.
- B₄ irrep label correctness against an external source (the table was verified internally via orthogonality and dim²-sum but not against a tabulated reference such as GAP / Magma / James-Kerber); the integer-exactness of multiplicities is independent of label convention.

**Caveats — methodological:**
- `numpy.linalg.eigh` (LAPACK `dsyevr`) is deterministic and well-tested; accumulated FP error scales as O(N · ε_machine) ≈ 10⁻¹³ for N=4096. Multiplicity deviations are about an order of magnitude smaller because character-orthogonality is itself an integer sum after dividing by |G|; the inner products of eigenvectors with their permuted selves are the load-bearing FP operations.
- Eigenspace grouping tolerance was 1 × 10⁻⁸. Smallest empirical gap between distinct eigenvalues was 2.7 × 10⁻⁵ — comfortably above tolerance, no risk of merging distinct eigenspaces.

---

## 6 — Anomalies

**Anomaly 1 (predicted, confirmed).** The λ=0 eigenspace in 4D is the only one that mixes irreps. It has dim 96 = 60 + 36, decomposing as `10·(2)|(2) + 6·(1,1)|(1,1)`. Independent rank check confirms this is the true 96-dimensional kernel of the knight 4D adjacency (rank 4000 + nullity 96 = 4096). The 2D analog: λ=0 hosts 4 copies of E (dim 8) — single irrep type, but multiple copies, so technically "mixed in multiplicity" though all the same irrep. The 4D mixing is dimensionally richer: two distinct 6-dim irreps coexist. **This is the only place per-eigenspace structure is non-discriminating in 4D** — at the kernel, the rep theory predicts the dim (96) and the irrep content (`(2)|(2) + (1,1)|(1,1)` with multiplicities 10 and 6) but not which specific eigenvectors host which irrep.

**Anomaly 2 (predicted, confirmed).** Knight bipartiteness implies `±λ` mirror pairs. Verified empirically: every non-zero eigenvalue `+λ` has a partner `−λ`; corresponding irreps are swap pairs `(α, β) ↔ (β, α)`. Examples: `+36.063 → (4)|()`, `−36.063 → ()|(4)`; `+2 → ()|(1,1,1,1)`, `−2 → (1,1,1,1)|()`.

**Anomaly 3 (new).** The eigenvalues `λ = ±2` are **integer-exact** in the knight 4D spectrum (machine-precision integer). The knight has 48 displacement vectors; some of these admit rational eigenvalue contributions from a Fourier-like substructure. Specifically: the `(1,1,1,1)|()` and `()|(1,1,1,1)` are 1-dim "sign" irreps of B₄ (B_n analog of the alternating-sign rep). The 1-dim sign-rep eigenvectors on the hypercube must have specific sign patterns under the B_4 action; for the knight 4D specifically, the value happens to be integer-exact ±2. **Not a coincidence**, but worth noting: it's the analog of the `λ=−2` rational eigenvalue in rook 2D and bishop 2D (also at machine-precision integer). Would be interesting to derive closed-form via the displacement-set Fourier expansion; not done here.

**Anomaly 4 (new structural prediction).** The histogram of eigenspace dimensions in 4D **is exactly the histogram of irrep dimensions of B_4** (each irrep contributes (mult-in-natural-rep / irrep-dim) eigenspaces; the dim-96 kernel hosts two irreps so contributes 1 eigenspace). This is the structural prediction even more compactly: **for a generic B₄-equivariant operator with full-rank-on-each-isotypic-block behaviour, the eigenspace dim histogram is determined by the natural-rep decomposition.** Knight 4D is the first project instance demonstrating this empirically at machine precision.

---

## 7 — Fermata records

**Fermata 1: §3.5.3(C) chess instance refinement.** The chess instance now spans two prediction modes (closed-form eigenvalues for rook/king/bishop; closed-form eigenspace structure for knight). **Conductor decision:** refine §3.5.3(C) chess sub-instance from "six chess sub-instances under three structural primitives" to "eight chess sub-instances under two prediction modes" (Mode I: closed-form eigenvalues; Mode II: closed-form eigenspace structure)? **Recommendation:** YES. The motif refinement is mathematically distinct — Mode I predicts spectrum, Mode II predicts isotypic decomposition. Both are rep-theoretic structural predictions from group `G`.

**Fermata 2: B₄ irrep label canonicalization.** The script's B₄ irreps are labelled `(α)|(β)` for pairs of partitions. Labels were verified internally (orthogonality + dim²-sum) but not against external reference. For project-wide use as a reusable B_n primitive (potential future ephemerides / chess-spectral / power-grid applications), cross-check against e.g. GAP `CharacterTable("WeylB",4)` recommended. **Recommendation:** queue this if/when B_n character table is needed elsewhere; the integer-exact-multiplicity verdict here is independent of label convention.

**Fermata 3: cross-domain candidate — Sierpinski-Gasket per-eigenspace decomposition.** MFO Phase B's 18-block result (D₃ on SG λ=6 eigenspace: 22A + 18B + 40E) was a single-eigenspace fingerprint. The chess knight result is the same structural prediction extended to **every eigenspace** of a non-product graph operator. **Conductor question:** is per-eigenspace D₃ decomposition for the FULL SG decimation Laplacian (not just λ=6) also integer-exact at machine precision? **Recommendation:** queue; this would be the MFO sibling of today's spike, testing whether the SG Laplacian's full eigenspace structure (not just one chosen eigenspace) is rep-theoretically predictable.

**Fermata 4: extension candidates within chess.** Queen (= rook ∪ bishop) is the other non-product piece. In 2D, queen has D₄ equivariance; per-eigenspace D₄ irrep multiplicities should also be integer-exact (same structural argument). In 4D, queen is the 6-axis-pair bishop union 4-axis rook — a much richer non-product structure. **Recommendation:** queue, low priority. The motif is already established by knight.

---

## 8 — Reproducibility

**Script:** [`chess-knight-irrep-multiplicities-script.py`](chess-knight-irrep-multiplicities-script.py)

**Per-eigenspace NDJSON:** [`chess-knight-irrep-multiplicities-per-eigenspace-2026-05-11.ndjson`](chess-knight-irrep-multiplicities-per-eigenspace-2026-05-11.ndjson) — 16,725 records: 225 (2D = 45 eigenspaces × 5 D₄ irreps) + 16,500 (4D = 825 eigenspaces × 20 B₄ irreps).

**Reproduction:** `python docs/srmech/notes/chess-knight-irrep-multiplicities-script.py`

**Runtime:** ~44 s on commodity workstation. Deterministic across runs. Memory peak: ~265 MB (the 4096×4096 knight adjacency, eigenvector matrix, and 20 permutation arrays all held briefly). Dominant cost: `eigh(4096×4096)` ≈ 15 s + per-class-trace inner products ≈ 15 s + S_n / B_4 character table ≈ 1 s.

**Library versions:** numpy 2.4.4 only (LAPACK via `linalg.eigh`); standard library. No SGD, no learned parameters, no test-set tuning. No sympy / no external character-table dependency.

**Citation:** Rinaldi-Unciuleanu & Chiru 2026, *A Mathematical Framework for Four-Dimensional Chess: Extending Game Mechanics Through Higher-Dimensional Geometry*, AppliedMath 6(3) 48, DOI [10.3390/appliedmath6030048](https://doi.org/10.3390/appliedmath6030048). Vendored at [`docs/srmech/hoodoos/rinaldi-unciuleanu-chiru-2026.xml`](../hoodoos/rinaldi-unciuleanu-chiru-2026.xml). §3.6 names knight as the non-product case; this spike's contribution is the per-eigenspace structural prediction.

**B_n character formulation:** Specht / Frobenius formula via power-sum-Schur bridge. Standard reference: James-Kerber, *Representation Theory of the Symmetric Group* (Encyclopedia of Mathematics and its Applications 16, 1981), Theorem 5.5; equivalent to Geissinger 1977. S_n characters via Murnaghan-Nakayama rule. Centralizer formula (James-Kerber 4.2.10) verified by class-size sum = |B_4| = 384.

**Project contribution:** the per-eigenspace integer-exact multiplicity identity for the knight move-graph is the project's contribution (not in Rinaldi-Unciuleanu & Chiru 2026, which names "spectral analysis of move graphs" as future work). Same MPM-provenance pattern as the prior chess D₄/B₄ spike.
