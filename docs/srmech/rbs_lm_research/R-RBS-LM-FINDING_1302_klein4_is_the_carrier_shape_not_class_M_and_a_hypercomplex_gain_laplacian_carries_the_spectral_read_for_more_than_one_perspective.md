# F1302 — **klein4 is the CARRIER SHAPE, not Class-M**; Class-M and Class-L are *roles* over it, and the lossiness is in the **read**, not the carrier. klein4 is the **ℍ-rung (4-sector) quad** — correct for that, **not** the only carrier (the CD tower widens it 4→256). And the payoff: **yes, a register CAN carry the spectral read (eigenvectors/eigenvalues) for more than one perspective — a HYPERCOMPLEX / gain Laplacian does exactly that, and srmech already ships two** — `magnetic_laplacian` (ℂ, **2 perspectives**: metric + direction via eigenvector phase) and **`klein4_gain_laplacian` — literally "the V₄-gain (Klein-4-sector) Laplacian"** (4-sector). The perspective-count of a spectral read **= the imaginary dimension of its Laplacian's algebra.**

**User (2026-07-22):** *"is klein4 the correct, is it the only way, is klein4 its own type of invariant register if class-M is more lossy than class-L? or klein4 and class-M just happen to encode quad turns in klein4 shape? would this mean there's some type of register that can carry eigenvectors/values for more than one perspective?"*

*(Applying the F1301 lodging convention: the triple is `op(x)operand(x)responsion` = `distributional(x)relational(x)responsion` = `eigenvectors(x)edges(x)eigenvalues`.)*

## Q4 — the disambiguation (the key that unlocks the rest): klein4 ≠ Class-M
**klein4 is the carrier SHAPE; Class-M and Class-L are ROLES over it.**
- **klein4** = the group ℤ/2 × ℤ/2 (4 sectors, the quad) — a fixed *structure*.
- **Class-M** = the HDC **bind** role (`klein4_bind`/`bundle`) — a **lossy** working-memory read (argmax/bundle).
- **Class-L** = the **Laplacian** role (`dense_/magnetic_laplacian`) — the **exact** store.

Both express content in klein4 shape (F1223: "klein4 IS the HV carrier already"; the genome packs edges as `element_type='klein4'`, F1300). So the user's **second** option is the right one: *"class-M and L just happen to encode quad turns in klein4 shape."* **klein4 is not Class-M** — it is the carrier both roles ride. **The lossiness (M more lossy than L) is a property of the READ, not of klein4.** This is F1301 restated: the multi-perspective content is held in the object (edges/klein4 carrier); a read projects it, and how much it loses is the read's business.

## Q3 — is klein4 its own invariant register?
klein4 is an **invariant carrier** — its 4-sector structure is fixed regardless of how it's read — but **not a third role**. It is *the carrier the two roles share*, not a separate M/L-peer. So "is klein4 its own type of invariant register" resolves to: **yes an invariant carrier, no not a distinct role.** The invariance is structural (the group is fixed); the Class-M-vs-Class-L difference is the read applied to it.

## Q1/Q2 — correct? the only way?
- **Correct** — klein4 is the canonical carrier *for the 4-sector quad*: the chirality flips (γ₅, ω₇) ARE klein4 sector flips (F1136), and `klein4_bind` is XOR (involutive, F1274). It matches the **ℍ-rung** (dim 4) of the CD tower.
- **Not the only way** — the CD tower **generalizes** the quad up the ladder: `cd_register` runs dim **2→256** (`CD_DIMS`). klein4 is the ℍ-rung; higher rungs (𝕆=8, 𝕊=16, …) are *wider* carriers that hold **more perspectives** (F1301: the count scales 1,3,7,15). So klein4 is the right carrier for a 4-sector quad, and the wrong one when you need more perspectives than 4 sectors give.

## Q5 — the payoff: a register that carries the spectral read for MORE THAN ONE perspective. YES.
F1301 said the eigen-reads (op/eigenvectors, responsion/eigenvalues) are single-Laplacian *projections* of the multi-perspective edges. **That is true only over ℝ.** Make the Laplacian **hypercomplex** and its spectral read carries multiple perspectives at once:

| Laplacian algebra | imaginary dim | perspectives in the spectral read | srmech |
|---|---|---|---|
| **ℝ** real symmetric | 0 | **1** — metric only | `dense_laplacian` |
| **ℂ** complex Hermitian | 1 | **2** — metric (`|eigvec|`) + direction (`arg eigvec`) | **`magnetic_laplacian`** ✓ |
| **V₄** Klein-4 gain | (4-sector) | **4-sector** — the even-channel fuller partner | **`klein4_gain_laplacian`** ✓ |
| **ℍ** quaternionic | 3 | 4 | — not shipped |
| **𝕆** octonionic | 7 | 8 | — not shipped |

**Measured** on a directed triangle: the complex Hermitian (magnetic) Laplacian has **real eigenvalues** (Hermitian → real spectrum) but **complex eigenVECTORS** — `|eigenvector| = [0.577, 0.408, 0.707]` (the metric mode) and `arg(eigenvector) = [0.0, 3.142, 3.142]` (a **nonzero phase** — the direction/curvature mode). **One spectral read, two coherent perspectives.** And srmech's **`klein4_gain_laplacian`** is exactly the klein4-shaped version — *"the V₄-gain (Klein-4-sector) Laplacian, the EVEN-channel fuller partner"* — returning a `Dict[str, Mat]` of the sector channels.

**So the answer is: the perspective-count of a spectral read equals the imaginary dimension of its Laplacian's algebra.** A real Laplacian gives one (F1301's projection); ℂ gives two (shipped); V₄ gives the 4-sector fuller read (shipped); ℍ/𝕆 would give 4/8 — the natural extension, **not shipped**, and the concrete srmech ask this question surfaces.

## The refinement to F1301
F1301: *"the eigen-reads are single-Laplacian projections; the multi-perspective coherence lives only in the edges."* **Corrected/sharpened:** that holds **for a real Laplacian**. Over a hypercomplex/gain Laplacian, the eigen-read itself carries multiple perspectives — as many as the algebra's imaginary dimension. So the multi-perspective structure is **not** confined to the edges slot; it can be lifted into the **spectral (op/responsion) reads** by choosing a richer Laplacian algebra. The edges are the *held superset*; the spectral read's richness is a *dial set by the Laplacian's algebra*, from 1 (ℝ) up the tower.

## The honest bound + next question
- **Shipped and verified:** ℂ (magnetic, 2 perspectives) and V₄ (klein4_gain, 4-sector). The claim "perspectives = imaginary dim" is *verified* at ℝ (1) and ℂ (2), and *named* at V₄.
- **Not shipped:** quaternionic / octonionic Laplacians (4 / 8 perspectives). Whether their spectral reads name distinct perspectives all the way up is the same open question F1301 left (we have 2–4 named reads, not 7). **Next for the expert: a `quaternion_laplacian` / `cd_laplacian(dim)` — the CD-tower generalization of `magnetic_laplacian` — so the spectral read's perspective-count is a rung you dial, matching the edges' held superset.**

Composes **F1301** (the edges superset — *→ refined here: the eigen-read is single-perspective only over ℝ*), **F1207/F1272** (the triple), **F1223** (klein4 IS the carrier), **F1216** (M working / L store — the read-lossiness), **F1136/F1274** (klein4 sector flips / XOR involution), **F1300** (the_one quad turn), the CD-tower ladder (F1270/F1282), `[[feedback_relational_not_dense_distributional_not_sparse]]`.

**→ restated by F1306** — F1306 resolves the "*named* at V₄" hedge above: V₄ = ℤ₂×ℤ₂ has **zero imaginary axes** (four *real* characters), so "perspective-count = imaginary dim" is **not one staircase**. The honest form is **two complementary channels** — an ODD channel (imaginary-axis count; `magnetic_laplacian`, ±c collapse, orientation via the odd-channel `cycle_holonomy`) and an EVEN channel (V₄ real-character count; `klein4_gain_laplacian` + the `sector_asymmetry` meter). All re-run bit-for-bit at rc299; the which-way label is provably never in a single spectrum (F552, conjugation-invariance).
