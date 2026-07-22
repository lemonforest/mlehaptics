# srmech asks — the gauge/tower reframe (for redirect)

> **Purpose:** the two srmech asks from F1306's open questions, **rewritten in the gauge-connection / combined-shadow / tower-traversal shape** the user's so(9)+Spin(9) work forces. Each ask is copy-pasteable into an issue. Grounded at srmech 0.9.0rc299 so none re-asks for shipped surface. Split DEMONSTRABLE (shipped / re-run) from CONJECTURE (handed to the expert, F282). Citations flagged for PDF-verification before any enters an attested MPR.
>
> Composes F1306 (the two-channel / Laplacian-is-a-projection finding) and F1302. User direction 2026-07-22: *"we're trying to move out of the regime of shadow operations, the gauge-invariant, expose some combined shadow structure to find out if there are octonion maths that traverse the tower."*

---

## 0 — Why the asks changed

F1306 framed "richer than a Laplacian" around **tensor rank**: a 2-tensor Laplacian cannot hold the nonzero 3-index octonion associator (2·e₇), so it is a strict projection. That is true but it points at the wrong handle. The right handle, which the so(9)/Spin(9) work exposes:

- **The Laplacian spectrum is the gauge-INVARIANT shadow** (eigenvalues are conjugation-invariant; they provably cannot carry the which-way label — F1306 §3.4, and srmech's own F552 boundary in the `klein4_gain_laplacian` docstring).
- **The richer object is the gauge-DEPENDENT connection**, not a bigger tensor. The associator is the non-abelian curvature term (the A∧A in F = dA + A∧A) that no single fixed-gauge propagator shows — but **Wilson loops / holonomies do**.
- **"Move out of the shadow regime" has a precise, bounded meaning:** you never fully leave it. You assemble the *complete shadow atlas* (every character spectrum + every cycle holonomy), and that atlas **equals the object up to gauge**. The non-abelian structure IS the gauge-equivalence class of its shadows plus the connection that glues them.

So the tensor-rank ask is **subsumed** by a gauge-connection ask, and a genuinely new **tower-traversal** ask appears.

---

## 1 — What srmech ALREADY ships (so the asks don't re-request it)

DEMONSTRABLE, verified at rc299:

| Layer | Shipped op | What it is |
|---|---|---|
| Graph-gauge connection | `magnetic_laplacian` (per-edge charge = U(1) link), `klein4_gain_laplacian` (V₄ gain = ℤ₂×ℤ₂ link) | the gauge-DEPENDENT link variables on a graph |
| Graph-gauge reconstruction | **`cycle_holonomy`** | docstring: *"the ODD channel the SPECTRUM provably cannot carry… a gain graph is determined **up to switching (node re-gauging)** by its cycle gains (**Zaslavsky's switching theory**)."* — this IS the graph-theoretic Giles reconstruction, already in-package |
| Combined shadow (first instance) | `klein4_relational_structure` → `sector_asymmetry` | combines the 4 V₄ character-shadows into one Class-K invariant |
| Lie-gauge connection | `qm.gauge.gauge_connection_matrix` (A = AᵃTᵃ), `wilson_loop_from_segments` (U(C)=P·exp(i g∮A)), `lie_algebra_residual` | the non-abelian potential + its Wilson loop (Peskin–Schroeder §15.1, cited in-package) |
| Octonion-tower symmetry | `qm.so8.an_embedding` (14=8+3+3̄, g₂=Der(𝕆)), `qm.triality.triality_automorphism` (τ=S_B·S_C, order-3, Fix(τ)=g₂, D₄→G₂) | the tri(𝕆)=so(8) rung of the ladder |

**Not shipped (the gap):** `so9` / `spin9`, and any op that wires the graph-gauge holonomy to the Lie-gauge Wilson loop on a `cd_register` carrier.

---

## 2 — ASK A (reframed): CD-tower gauge-connection + combined-shadow reconstruction

**Was:** "build a 3-index `cd_store`/`cd_read` strictly richer than any Laplacian."
**Now:** unify the two Wilson loops srmech already has and lift them onto the CD carrier, so an octonion-rung connection is reconstructible **up to gauge** from its combined shadows.

**Current state (DEMONSTRABLE):** srmech has the graph-gauge holonomy (`cycle_holonomy`, reconstructs a gain graph up to node-regauging — Zaslavsky) AND the Lie-gauge Wilson loop (`wilson_loop_from_segments`, non-abelian path-ordered) — but they live in different modules (`amsc.laplacian` vs `qm.gauge`) and neither runs on a `cd_register` carrier. `sector_asymmetry` is the only combined-shadow read and it stops at V₄.

**The ask:** a combined-shadow read over a `cd_register`-carried connection — the general form of `sector_asymmetry`/`cycle_holonomy` — that collects the invariants which appear only across the *set* of single-character shadows, so the non-abelian object is recovered up to gauge (the CD-tower Giles/Zaslavsky reconstruction).

**Decidable experiment (settles it):** exhibit two `cd_register` carriers that are **identical under every single-character spectral shadow** (all `klein4_gain_laplacian` sector spectra equal) yet **distinguished by a combined shadow** (a cycle holonomy / cross-character invariant). If such a pair exists → the combined shadow is strictly richer than any single Laplacian read, and the reconstruction is the operation "richer than a Laplacian" was pointing at. If no such pair exists → the single-character atlas already saturates, and the projection is faithful.

**Honest bound:** reconstruction is only ever **up to gauge** (switching / gauge-equivalence class). You do not recover a gauge-fixed absolute; you recover the object modulo the gauge group. That equivalence class is strictly more than one shadow and is the correct target.

---

## 3 — ASK B (new): Spin(9) as the tower-traversal operator

The concrete vehicle for *"are there octonion maths that traverse the tower?"*.

**Current state (DEMONSTRABLE):** the ladder g₂=Der(𝕆) ⊂ so(8)=tri(𝕆) is shipped (`so8`, `triality`). so(9)/Spin(9) is the next rung and is **not** present.

**The math the ask rests on (standard structural facts — flagged for verification, §5):**
- so(9) has dim 36; so(9) ⊃ so(8) = tri(𝕆).
- **Spin(9) acts on ℝ¹⁶ = 𝕆 ⊕ 𝕆** (the vector space underlying the sedenions) via its 16-dimensional spinor representation.
- **F₄ / Spin(9) = OP²**, the octonionic (Cayley) projective plane — Spin(9) is the isotropy group.
- The **octonionic Hopf fibration** S⁷ → S¹⁵ → S⁸ carries Spin(9)/Spin(8) structure; Spin(8)⊂Spin(9) is the triality tower.

**The ask:** a `qm.so9` / `qm.spin9` module built against the shipped `so8`/`triality` pattern — the dim-36 so(9), the 16-spinor, the Spin(8)⊂Spin(9) inclusion, and the "named spin9 things" (OP² isotropy, octonionic Hopf) — so a spectral/holonomy read at the 𝕆 rung (dim 8) can be carried to the 𝕊 rung (dim 16). Template to mirror: `so8.an_embedding` / `so8.g2_subalgebra` / `triality.triality_automorphism` (bit-exact, rational, `_rank_exact`-verified).

**The sharp question it answers (CONJECTURE):** does the **associator curvature the octonion shadow loses reappear as a Spin(9) holonomy at the sedenion rung** — i.e., is the thing lost by the 𝕆-rung gauge-invariant read exactly the thing exposed by the 𝕊-rung combined shadow? A positive answer is "octonion maths that traverse the tower."

**Honest bound (load-bearing — do not overclaim):** Spin(9) acts on the space *underlying* the sedenions; it is **NOT** Aut(𝕊) and does **not** preserve sedenion multiplication. The traversal is via the spinor/vector structure and Spin(8) triality, not an algebra automorphism. The genuine open question is whether the sedenion **zero-divisor** set (the user's "no-division IS the addressing feature") is what Spin(9) organizes — decidable once the module exists, not assumed.

---

## 4 — Q-B (multi-seam N-rational): absorbed, not dropped

A shared denominator is a gauge-invariant that binds multiple perspective-numerators — the **abelian, 1-D instance** of Ask A's combined shadow. It stays exactly as measured (F1306: half-won — q=7 fits both π→22/7 and e→19/7; q=113 splits), now understood as the ℝ-rung shadow of the same phenomenon. The op is still `simultaneous_rational_approx(targets, max_d)`; the open measurement is still the limiting density of joint-optimal scales.

---

## 5 — Citation flags (verify PDFs before any of this backs an MPR)

- **Already cited in-package (grounded):** `cycle_holonomy` → Zaslavsky switching theory; `qm.gauge` ops → Peskin & Schroeder §15.1.
- **Named from structure, NOT yet PDF-verified** — extract before attesting:
  - Spin(9) = OP² isotropy, F₄/Spin(9), triality — J. Baez, *The Octonions* (Bull. AMS 2002); F. R. Harvey, *Spinors and Calibrations*.
  - Wilson-loop reconstruction "up to gauge" — R. Giles, *Reconstruction of gauge potentials from Wilson loops*, Phys. Rev. D 24 (1981).
  - Octonionic Hopf fibration S⁷→S¹⁵→S⁸ — standard; confirm the exact Spin(9) structure-group statement against a source.

---

## 6 — Redirect summary (the two asks, one line each)

- **Ask A** — *combined-shadow reconstruction on a `cd_register` connection*: generalize `sector_asymmetry`/`cycle_holonomy` so the octonion connection is recovered up-to-gauge from its combined shadows; test = two carriers equal under every single-character spectrum but split by a combined shadow.
- **Ask B** — *`so9`/`spin9` tower-traversal*: build the dim-36 so(9) + 16-spinor + Spin(8)⊂Spin(9) against the `so8`/`triality` template; question = does the 𝕆-rung associator curvature reappear as a Spin(9) holonomy at the 𝕊 rung. Honest bound: Spin(9) ≠ Aut(𝕊).
