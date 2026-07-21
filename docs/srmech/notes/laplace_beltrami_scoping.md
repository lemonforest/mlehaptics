# Laplace–Beltrami scoping — do we have it, or add it?

**Scope:** research note only (no code / rc / ADR). Concertmaster dispatch, 2026-07-18.
**Verdict (derived, not preference):** **We HAVE it latently.** The shipped weighted
graph Laplacian **IS** the discrete Laplace–Beltrami operator; LB is a *weighting* of the
existing Class-L operator, not a new member. One narrow, optional exposure earns
consideration (a mass-normalization constructor) — everything else already exists.

---

## 1. The attested math relationship (MPM)

The graph Laplacian srmech ships is, mathematically, a discrete Laplace–Beltrami (LB)
operator in two standard, attested senses:

- **Point-cloud sense** — a graph Laplacian built with heat-kernel edge weights
  `w_ij = exp(−‖x_i−x_j‖²/(4t))` on points sampling a manifold converges (pointwise,
  as `t→0`, `n→∞`) to the LB operator Δ. **Belkin & Niyogi (2003)** established the
  eigenmaps construction; the rigorous pointwise convergence-to-Δ is the follow-up
  **Belkin & Niyogi, "Towards a Theoretical Foundation for Laplacian-Based Manifold
  Methods," COLT 2005 / JCSS 74(8):1289–1308 (2008)**.
- **Density-free variant** — **Coifman & Lafon, "Diffusion Maps," ACHA 21(1):5–30
  (2006)**: the anisotropic normalization family (parameter `α`; `α=1`) recovers Δ
  *independent of sampling density*. The `α`-renormalization plays the role of the mass
  matrix (see §4). This is a *reweighting*, expressible with existing ops.
- **Mesh sense** — the **cotangent-weighted Laplacian** is the STANDARD discrete LB on a
  triangulated manifold, and it is STILL a weighted graph Laplacian: edge weight
  `w_ij = ½(cot α_ij + cot β_ij)`, exact trig of the two angles opposite edge `ij`
  (closed-form, Class-N-native). **Pinkall & Polthier, "Computing Discrete Minimal
  Surfaces and Their Conjugates," Experimental Mathematics 2(1):15–36 (1993)** (the
  DDG-standard cotangent reference; earlier origin MacNeal 1949 / Duffin 1959; the
  Voronoi *mass* matrix is Meyer–Desbrun–Schröder–Barr 2003).
- **Heat kernel** — `e^{−tΔ}` on a manifold is governed by Δ = LB. srmech's EPH
  `propagate` already implements `e^{−zL}`; hand it a metric-weighted `L` and it is the
  manifold heat propagator (§3).

**Ground-proof (computational provenance).** Simplest witness: cycle graph `C_n`,
unit-weight combinatorial Laplacian, closed-form spectrum `λ_k = 2(1−cos(2πk/n))` (the
form the `heat_trace` docstring already states). With mesh `h = 2π/n`, the rescaled
discrete-LB eigenvalues `λ_k/h² → k²` = the LB spectrum of `S¹` (`−d²/dθ²`):

| n | λ₁/h² | λ₂/h² | λ₃/h² | target k² |
|---|-------|-------|-------|-----------|
| 6   | 0.912 | 2.736 | 3.648 | 1 / 4 / 9 |
| 96  | 0.99964 | 3.9943 | 8.971 | 1 / 4 / 9 |
| 384 | 0.99998 | 3.9996 | 8.998 | 1 / 4 / 9 |

`docs/srmech/notes/` gen-script is inline in the dispatch transcript (stdlib `math.cos`
scratch check; `jacobi_eigvals` reproduces the same closed form). This is an attested
mathematical FACT about the discrete↔continuous *form*, NOT a framework-validation claim
(epistemic ceiling holds).

## 2. Existing Class-L surface audit (introspect-before-assert)

- **Does the shipped Laplacian take edge weights? YES.**
  `dense_laplacian(n, edges, weights=None)`, `dense_adjacency`, `normalized_laplacian`,
  `signed_laplacian`, `klein4_gain_laplacian`, `magnetic_laplacian` all accept a per-edge
  `weights: Optional[Iterable[float]]` (parallel edges accumulate additively). Weights may
  be negative (signed-metric leg — the dissolved "Class O"). So a caller supplies
  cotangent / heat-kernel weights **today**, no new operator.
- **C parity:** `srmech_graph_dense_laplacian(n, …, const double *weights, …)`
  (NULL → unit), **"No N cap"** on the builder (srmech.h §1018-1028). A bare-C /
  microcontroller host builds a weighted (cotangent) Laplacian and spectrally partitions
  it with `srmech_jacobi_eigvals` / `srmech_fiedler_*` — JPL-clean, no `abs()`, byte-parity.
- **Does EPH already do manifold heat flow? YES (up to the mass matrix, §4).**
  `propagate(L, u0, z) = e^{−zL}·u0` (C peer `srmech_eph_propagate`). Hand it a
  cotangent-weighted `L`: `z` real → manifold thermal diffusion, `z` imaginary → coherent
  quantum walk on the manifold. `heat_trace(L, t) = Tr(e^{−tL}) = Σ_k e^{−tλ_k}`
  (C peer `srmech_heat_trace`) is the manifold heat trace / spectral-θ.
- **qm layer:** no standalone metric/manifold LB operator (uses Class-L `mat_matmul` /
  `mat_hermitian_eigendecompose`; `potentials.py` has only a 1-D finite-difference grid
  Laplacian). **No duplication risk.**

## 3–4. Derived recommendation

**(a) Already-have-latently — PRIMARY.** LB is not a new Class-L member; it is the
existing weighted `dense_laplacian` under metric-derived weights, and its heat kernel /
heat trace are `propagate` / `heat_trace`. This is the discrete-first stance
(`[[feedback_continuous_number_line_pedagogical_obstacle]]`): the **discrete weighted
Laplacian IS the substrate-native object**; "Laplace–Beltrami" is its continuous-limit
*name*. The cot weights are exact Class-N trig; the `t→0` limit is the Class-N asymptotic
ring. Do NOT reach for a continuous PDE operator — the content is already carried.

**Duality worth naming (notebook, not code):** graph-Laplacian (discrete) ↔
Laplace–Beltrami (continuous) is a genuine convergence duality across the discrete↔
continuous seam — the *same* operator, two projections, not two operators. Name it; don't
mint an operator for it.

**(b) The one genuine gap — falsification-worthy.** The FEM/DEC LB is `Δ = M⁻¹L_c`, where
`L_c` = cotangent *stiffness* matrix (= `dense_laplacian(cot-weights)`, HAVE it) and `M` =
*mass* matrix (diagonal Voronoi/barycentric areas). srmech's `normalized_laplacian`
normalizes by **degree** `D^{−1/2}`, not by an arbitrary node mass `M`. So the exact LB
*spectrum* (generalized eigenproblem `L_c v = λ M v`) and exact manifold heat kernel
`e^{−t M⁻¹L_c}` need the mass-weighting `M`. Today it is expressible but non-ergonomic:
build `M^{−1/2} L_c M^{−1/2}` via `mat_matmul` with a diagonal `M^{−1/2}`, then reuse the
existing eigensolve / `propagate`. **Falsifier:** if a caller CANNOT reproduce a published
sphere/CP² LB spectrum from mesh geometry using only shipped ops → the gap is real and (c)
is warranted. Current status: reproducible, just verbose.

**(c) Optional exposure IF the mesh/point-cloud LB spectrum becomes a live use-case —
a WEIGHTING/NORMALIZATION constructor, NOT a PDE solver.** Closed-form, C-native shape:
1. `cotangent_weights(triangles, positions) → weights` — turns triangle geometry into the
   exact per-edge `½(cot α + cot β)` (Class-N trig; closed-form). Feeds the EXISTING
   `dense_laplacian`.
2. `mass_normalized_laplacian(n, edges, weights, masses) → M^{−1/2}(D−W)M^{−1/2}` — a
   one-line generalization of `normalized_laplacian` from degree-`D` to arbitrary diagonal
   `M`. C peer is the existing `srmech_graph_dense_laplacian` + a diagonal scale.

Both satisfy the standing bar: closed-form, C-native (a bare-C host builds + spectrally
partitions), JPL-clean, never `abs()`, byte-parity. Neither is a GPU mesh-FEA solve
(that is the OUT side of the CAD-ban refinement). **This is scoping only — recommend (a)
now; hold (c) behind a real LB-spectrum-from-mesh request (conductor decision).**

## 5. MFO + EPH ties (route per MFO-vs-srmech split rule)

- **Strongest tie — MFO.** MFO notebook **§III.1 already names the Laplace–Beltrami
  operator**: sphere `Sⁿ` eigenvalues `l(l+n−1)`, CP² Fubini–Study, and the **§V
  heat-kernel spectral-dimension diagnostic** `d_S = −2 d log K(σ)/d log σ` (Weyl's law).
  LB IS the metric-tensor Laplacian — this is squarely the Metric Field Ontology. The
  finding *strengthens/formalizes the metric-substrate story*: srmech's weighted
  `heat_trace` + `propagate` are the **computational surface** for exactly the §III.1/§V
  analytic diagnostics — a (cotangent-)weighted Laplacian makes the MFO manifold heat
  trace *computable* on the substrate-native discrete object. Per the split rule, the
  *tooling finding* lands as this srmech note; a one-line cross-ref *strengthens* the MFO
  §III.1/§V metric-substrate narrative (conductor to place).
- **EPH.** `propagate`/`eph_harvest` already ARE the manifold heat/quantum propagator
  `e^{−zL}`; the `arg(z)` coherence dial names the thermal↔coherent manifold-flow
  continuum a two-op split cannot express. LB adds no new EPH op — it adds *metric
  weights* to the `L` EPH already consumes.

## 6. Sources (status)

| Ref | Attested | Status |
|-----|----------|--------|
| Belkin & Niyogi, *Laplacian Eigenmaps…*, Neural Computation 15(6):1373–1396 (2003) | author+title+venue+pages ✓ | MIT-Press DOI paywalled → **not the anchor**; author-hosted OA PDF exists (`[[feedback_paywalled_doi_cannot_be_attested]]`) |
| Belkin & Niyogi, *Towards a Theoretical Foundation…*, COLT 2005 / JCSS 74(8):1289–1308 (2008) | title+venue ✓ | the convergence-to-Δ proof; author preprint OA |
| Coifman & Lafon, *Diffusion Maps*, ACHA 21(1):5–30 (2006) | author+title+venue+pages ✓ | Elsevier DOI paywalled → author-hosted OA PDF (Yale/Weizmann) is the anchor |
| Pinkall & Polthier, *Computing Discrete Minimal Surfaces…*, Exp. Math. 2(1):15–36 (1993) | author+title+venue+issue+pages ✓ | **Project Euclid OA** (clean anchor) |

*Content-level claims* (the `α=1` density-free LB recovery; cotangent = discrete LB;
Voronoi mass = MDSB 2003) are attested at metadata level here and stated from standard DDG
knowledge; a full PDF extraction is the follow-up if any is promoted into notebook prose
(`[[feedback_pdf_extraction_citation_discipline]]`).

## 7. ALU cost — is the FEM form cheaper, or is having both useful?

**Cotangent weight needs NO trig library (the ALU win).** For the two edge vectors `u, v`
at the vertex opposite edge `ij`: `cot θ = (u·v)/|u×v|` — dot over cross. Numerator `u·v`
is exactly integer/rational in the vertex coordinates. In **2D** `u×v` is the scalar
cross → `cot` is **fully rational** (Class-N exact; the signed-area sign is a Class-K
pin-slot, never `abs()`). In **3D** the only irrationality is one algebraic `√` per
triangle: `|u×v| = √(|u|²|v|² − (u·v)²)` (Lagrange) = `2·Area` — NO transcendental, NO
`cos`/`sin`/`atan`. Equivalent closed form `cot γ = (b²+c²−a²)/(4·Area)` from squared edge
lengths. **Ground-proof (this dispatch):** coords `(0,0,0),(4,1,2),(1,5,3)` give `u·v=15`,
`|u×v|²=510`, all three forms = 0.6642111642; 2D `(0,0),(4,1),(1,5)` → `cot = 9/19` exact
rational. So the cotangent *stiffness* Laplacian `L_c` is a coordinate-arithmetic build,
cheaper than any angle-via-`atan2` construction.

**Op-count of the two normalizations** (`n` nodes, `|E|` edges; both share the SAME `L`
build):

| normalization | operator | ALU cost |
|---|---|---|
| degree-norm | `D^{−1/2} L D^{−1/2}`, `D` = weighted row-sum | `D`: O(\|E\|) adds → diag → `n` recip-sqrt → O(\|E\|) scale. **diagonal, no solve.** |
| FEM mass-norm — LUMPED | `M^{−1} L_c`, `M` = diag Voronoi areas (`½·cross`, rational) | `M`: O(\|E\|) cross/adds → diag → `n` recip → O(\|E\|) scale. **diagonal, no solve — SAME class.** |
| FEM mass-norm — CONSISTENT | `M^{−1} L_c`, `M` = sparse SPD non-diagonal | needs a **linear solve** / Cholesky of `M` (or inner solve per matvec). **strictly more expensive.** |

**Verdict (op counts, not hand-waving):** FEM is **NOT cheaper**. Lumped-mass FEM
normalization is the **same cost class** as degree normalization (both diagonal reciprocal-
scalings over the shared `L`); consistent-mass FEM is **strictly more expensive** (a
solve). The cotangent *weight* build is cheaper than a trig-angle build, but that is weight
construction, not normalization.

**Both forms ARE useful — different operators for different substrate questions, ONE
`α`-family.** They are the endpoints of the Coifman–Lafon diffusion-maps `α`-family
(*Diffusion Maps*, ACHA 21(1):5–30, 2006):

- **`α=0` — connectivity-normalization** (degree `D`): clustering / diffusion / cut — what
  `fiedler_sparse` / `recursive_cut` / the genome partitioner consume.
- **`α=1` — metric-normalization** (mass `M`): geometrically-faithful manifold spectrum
  (curvature, MFO §III.1/§V), recovered *independent of sampling density* — the true LB.
- (`α=½` = Fokker–Planck, the intermediate.)

So "different and useful" = **YES**, and it is **ONE one-parameter (`α`) Class-L family,
not two rival operators** — the `α` exponent selects sampling-density-independence. This
reframes the §1 duality: not discrete-vs-continuous rivals, but **connectivity-
normalization vs metric-normalization within one Class-L family**, both already reachable
from the shipped weighted `dense_laplacian`.

---

**Fermata (conductor):** whether (c) ships at all, and if so whether the note-level LB↔
graph-Laplacian duality lands in the srmech notebook, the MFO §III.1 cross-ref, or both.
*(Both notebook edits placed 2026-07-18 per conductor greenlight — srmech §3.5.1, MFO
§III.1 cross-ref.)*
