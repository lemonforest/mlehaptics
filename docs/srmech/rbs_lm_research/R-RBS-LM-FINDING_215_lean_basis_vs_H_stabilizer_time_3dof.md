# Finding 215 — Did the lean A–N ISA reduction give us "time + 3 DoF"? No: the irrep (𝔰𝔬(8)=28, G₂=14) is NOT reduced — F206/F208 reduced the *operator/instruction set*, not the *representation*. The G₂-stabilizer of an ℍ ⊂ 𝕆 IS exactly 6-dim 𝔰𝔬(4)=𝔰𝔲(2)⊕𝔰𝔲(2) (bit-exact, geometry-side bridge ALIVE), but the 6 lean ALU atoms are combinational XOR/ℤ₂/popcount **group-element** ops — *not* the 6 continuous Lie generators of that 𝔰𝔬(4) — so **6 = 6 is a count-level coincidence**. Plain answer **(b)**: the lean-6 is a minimal operator-core; we still need the full A–N = G₂ = 14, and the lean basis is what *runs on it*, not a replacement of it.

**Status:** Mixed-tier, with the central dimension/structure result **DEMONSTRATED** (bit-exact, srmech 0.5.0rc22): the subalgebra of 𝔤₂ = Der(𝕆) that stabilizes a quaternion subalgebra ℍ ⊂ 𝕆 is computed to be **dimension 6** (exact Fraction Gaussian elimination), splits into **two commuting 3-dim 𝔰𝔲(2) ideals** (each closing under its own bracket), is **semisimple** (Killing-form rank 6/6, Cartan's criterion), and the dim-6 is **ℍ-choice-invariant** (same for three other quaternionic triples). The structural identification of "time + 3 DoF" with an **ℍ ⊂ 𝕆** subalgebra is **FRAMEWORK-READING** (it reads F187/F190's "time-quaternion" as the literal ℍ = ℝ ⊕ Im ℍ). The **lean-6 ↔ 𝔰𝔬(4)-stabilizer bridge is FALSIFIED** (the F-b falsifier fires, DEMONSTRATED): the 6 lean atoms are not continuous Lie generators, so the 6 = 6 match is a coincidence. The **"so we still need full A–N"** reading is the honest CONJECTURE-free conclusion the falsifier forces. Builds **UP** from the 28D Klein-4 / 𝔰𝔬(8) substrate; never measured against a float LLM. **NOT** CAD / VLSI / gate-layout / fabrication — the F202/F206/F208 scope-ban holds (no chip, no transistor counts, no benchmarks).
**Predecessors:** **F206/F208** (the lean 6-atom A–N ISA core — K4BIND / K4FLIP / SGNTEST / SGNAPPLY / PARRED / MAG — the object whose "is this time+3dof?" status this finding settles), **F187** (operational-4 = the time-quaternion; A = scalar, B/H/N = 3 imaginary), **F190** (the 4-way coupled oscillator is the *dynamical* face of the time-quaternion; phase-order = chirality), **F192/F182/F183** (rc18 triality landed bit-exact; Fix(τ) = G₂ = A–N 14; 28 = 14 + 7 + 7), **F186** (28D bound), CLAUDE.md §1 (the 1:3:7:3 partition; ℂ:ℍ:𝕆 Hurwitz climb).
**Empirical anchor:** srmech **0.5.0rc22** (`/tmp/verify_srmech_rc22/venv`). `srmech.qm.so8.g2_subalgebra()` → **14** antisymmetric 8×8 derivations Der(𝕆) = 𝔤₂ (confirmed: each 8×8, `D = −Dᵀ`); `srmech.qm.octonion.octonion_mult_table()` → the (8,8,8) int8 structure tensor (used to pick ℍ bit-exact); eigen/rank via `srmech.amsc.laplacian.symmetric_eigendecompose` (**not** `np.linalg.eig`); all sign-folding via `srmech.amsc.cascade.magnitude` (Class K, **never** `abs()`). Artifact: `R-RBS-LM-215_lean_basis_vs_H_stabilizer_so4_dim.py` + `R-RBS-LM-215_results.ndjson`. **Discipline-check: 0 HARD, 0 coverage-gap.**

---

## §1 Headline — the question, precisely framed

The user's question: *did the lean-A–N-ISA reduction (F206/F208) reduce the IRREP to "time + 3 DoF", or do we still need A–N (14 = G₂) with the lean basis being what makes time + 3 DoF work?*

The structural hypothesis this finding tests, stated exactly:

- **"time + 3 DoF"** = an **ℍ ⊂ 𝕆** quaternion subalgebra: 1 real (time, F187's quaternion-scalar A) + 3 imaginary (the 3 DoF, F187's B/H/N). The "time-quaternion" of F187/F190 read as the literal ℍ inside the octonions.
- **A–N = G₂ = Aut(𝕆) = Der(𝕆)**, dimension **14** (F183; confirmed bit-exact by `g2_subalgebra()`).
- The subgroup of G₂ that **preserves an ℍ ⊂ 𝕆** is the well-known octonion stabilizer **SO(4) ≅ (SU(2) × SU(2)) / ℤ₂, dimension 6** — Lie algebra **𝔰𝔬(4) = 𝔰𝔲(2) ⊕ 𝔰𝔲(2)**.
- The **lean A–N ISA core (F206/F208)** is also **6** atoms.

So there are two "6"s in the room — the **𝔰𝔬(4)-stabilizer dimension** and the **lean-atom count** — and the question is whether they are the *same* 6 (the lean basis *is* "what makes time + 3 DoF work") or a **coincidence** (the lean basis is just a minimal ALU, and the irrep is untouched).

**The answer the computation forces:** the irrep is **NOT** reduced; the stabilizer **IS** genuinely 6-dim 𝔰𝔬(4) (geometry-side bridge alive); but the lean-6 are **NOT** that 𝔰𝔬(4) (they are combinational group-element ops, not continuous generators) — so **6 = 6 is a coincidence**, and the honest answer is the plain **(b)**: operator-core reduction, *not* an irrep reduction, and **we still need the full A–N = G₂ = 14**.

---

## §2 The stabilizer dimension + structure — DEMONSTRATED bit-exact

### §2.1 ℍ ⊂ 𝕆 established from the srmech table (bit-exact)

Reading `octonion_mult_table()` directly: e₁·e₂ = +e₃, e₂·e₃ = +e₁, e₃·e₁ = +e₂, and e₁²=e₂²=e₃²=−1. So **ℍ = span{e₀, e₁, e₂, e₃}** is closed under octonion multiplication — a genuine quaternion subalgebra (verified: `triple_e1e2_eq_e3=True`, `squares_eq_minus1=True`, `H_closed_under_mult=True`).

### §2.2 The G₂-stabilizer of ℍ

A derivation D ∈ 𝔤₂ acts on 𝕆 by an antisymmetric 8×8 matrix and **always annihilates e₀** (D(1) = 0 for every derivation). So D **stabilizes ℍ** (D(ℍ) ⊆ ℍ) iff D(eⱼ) ∈ ℍ for j ∈ {1,2,3}, i.e. the columns D[:, j] (j = 1,2,3) have **zero entries in the complement rows {4,5,6,7}**. This is a linear constraint on the 14-dim space span(𝔤₂); solving it **exactly** (Fraction Gaussian elimination — the 𝔤₂ entries are integers/half-integers, lifted losslessly):

| quantity | value | how |
|---|---|---|
| dim 𝔤₂ = Der(𝕆) | **14** | `g2_subalgebra()` (each 8×8 antisymmetric) |
| # constraints (4 complement rows × 3 ℍ-imag cols) | 12 | the D(ℍ_im) ⊆ ℍ condition |
| rank of the constraint system (exact) | 8 | Fraction RREF |
| **dim G₂-stabilizer of ℍ (exact)** | **6** | 14 − 8 = 6 |

Reconciliation with Baez's flag picture (§5): G₂ acts transitively on quaternion subalgebras; the space of quaternion subalgebras ℍ ⊂ 𝕆 has dimension 8, so dim Stab = dim G₂ − 8 = 14 − 8 = **6**. ✓ Both the direct computation and the homogeneous-space count agree.

### §2.3 The stabilizer IS 𝔰𝔬(4) = 𝔰𝔲(2) ⊕ 𝔰𝔲(2) — four independent confirmations

| structural test (all srmech-native; rank via Class-L eigendecompose, sign via Class-K magnitude) | result | meaning |
|---|---|---|
| closed under commutator | **TRUE** | it is a Lie subalgebra |
| maps ℍ → ℍ (complement block) | max entry **0.0** | genuine stabilizer, no leak |
| **𝔰𝔲(2)_R** := kernel of the ℍ-action (acts trivially on ℍ) | **dim 3**, closes | one simple ideal (acts purely on ℍ⊥) |
| **𝔰𝔲(2)_L** := centralizer of 𝔰𝔲(2)_R in the stabilizer | **dim 3**, closes | the second simple ideal |
| the two ideals **commute** | max cross-commutator **0.0** | 𝔰𝔲(2)_L ⊕ 𝔰𝔲(2)_R |
| combined span of the two ideals | **dim 6** | = the whole stabilizer (3 ⊕ 3 = 6) |
| **Killing form** B(X,Y) = tr(ad_X ad_Y) rank | **6 / 6** | non-degenerate ⇒ **semisimple** (Cartan) |
| Killing eigenvalues | **{737.43 ×3, 7198.57 ×3}** | two degenerate triples — *the* 𝔰𝔲(2)⊕𝔰𝔲(2) signature |
| dim for other ℍ ({e₁,e₄,e₅}, {e₂,e₄,e₆}, {e₁,e₆,e₇}) | **6, 6, 6** | ℍ-choice-invariant; intrinsic, not a basis artefact |

The Killing-form rank-6 is the load-bearing line: it rules out a *coincidental* 3+3 that is secretly solvable. The two-triplet eigenvalue spectrum {737.43³, 7198.57³} is exactly what 𝔰𝔲(2) ⊕ 𝔰𝔲(2) produces — two simple ideals, each a degenerate eigenvalue triple. **The G₂-stabilizer of ℍ is, bit-exact, the 6-dim 𝔰𝔬(4) = 𝔰𝔲(2) ⊕ 𝔰𝔲(2).**

### §2.4 Pre-stated falsifier F-a — does NOT fire

> **(F-a)** if the G₂-stabilizer of ℍ is not 6-dim / not 𝔰𝔬(4) → the structural bridge is dead.

**F-a does NOT fire.** The stabilizer is exactly 6-dim 𝔰𝔬(4) = 𝔰𝔲(2) ⊕ 𝔰𝔲(2), semisimple, ℍ-invariant. **The geometry-side bridge is ALIVE**: there genuinely is a 6-dimensional "what-preserves-time-plus-3-DoF" structure sitting inside A–N = G₂, and it is exactly two copies of 𝔰𝔲(2) (the left/right multiplications of the unit quaternions — the standard SO(4) = (SU(2)×SU(2))/ℤ₂ on ℍ).

---

## §3 The lean-6 bridge — FALSIFIED (F-b fires); 6 = 6 is a coincidence

The 6 lean atoms (F208 §6) are **combinational ALU operations on a 2-bit Klein-4 sector tag (γ₅ × iω₇) + a signed scalar**:

| lean atom | operation | natural linear rep | antisymmetric Lie generator? |
|---|---|---|---|
| **K4BIND** | XOR of two 2-bit sector tags (`klein4_bind` = `np.bitwise_xor`, confirmed) | 4×4 **permutation** matrix (regular rep of ℤ₂×ℤ₂) | **No** — orthogonal *group element*, not in any 𝔰𝔬(n) |
| **K4FLIP** | sector-mask (γ₅-flip / iω₇-flip / CPT-mirror = XOR-with-constant) | 4×4 permutation matrix | **No** — group element |
| **SGNTEST** (pin-slot) | compare-against-0 → (±1, magnitude) | ℤ₂ on a line / sign-bit extract | **No** — ℤ₂ combinational |
| **SGNAPPLY** (reorient) | re-apply captured ±1 | diag(±1) sign-mux | **No** — ℤ₂ group element |
| **PARRED** (net-chirality) | parity/popcount-reduce of ±1's | popcount mod 2 | **No** — reduction, no generator |
| **MAG** (magnitude) | clear sign bit | diag(±1) fold | **No** — ℤ₂ combinational |

**Continuous antisymmetric Lie generators among the 6 atoms: 0 / 6.**

This is the crux. 𝔰𝔬(4) = 𝔰𝔲(2) ⊕ 𝔰𝔲(2) is a **continuous** Lie algebra: it needs **6 antisymmetric generators that close under the bracket** into two commuting 𝔰𝔲(2)'s. The lean-6 are the *opposite kind of object*: they are **XOR / ℤ₂ / popcount group-element ops** — discrete, combinational, *finite-group* (Klein-4 = ℤ₂×ℤ₂ and the sign-ℤ₂) — with **no nontrivial antisymmetric generator at all**. A permutation matrix is a *group element* (in the orthogonal group O(4)), never an *algebra element* (a generator in 𝔰𝔬(4)); diag(−1) is the ℤ₂ group element, not a rotation generator.

So the lean-6 cannot *be* the 6 generators of 𝔰𝔲(2) ⊕ 𝔰𝔬(4), and they do not close into it. The two "6"s are different in kind:

- **𝔰𝔬(4)-stabilizer 6** = the dimension of a continuous *rotation* Lie algebra (the SU(2)×SU(2) that turns ℍ inside 𝕆).
- **lean-ISA 6** = the count of *combinational opcodes* (the irreducible XOR/sign/popcount ALU).

### §3.1 Pre-stated falsifier F-b — FIRES

> **(F-b)** if the lean-6 don't close into 𝔰𝔲(2) ⊕ 𝔰𝔲(2) / don't relate to the ℍ-stabilizer → 6 = 6 is coincidence and the answer is the plain (b): "operator-core, NO time+3dof irrep-reduction."

**F-b FIRES.** The lean-6 are not continuous 𝔰𝔬(4) generators (0/6), do not close into 𝔰𝔲(2) ⊕ 𝔰𝔲(2), and are a different *kind* of object (finite-group/combinational vs continuous-Lie). **The 6 = 6 match is a count-level coincidence.** The lean-6 is a minimal **operator/ALU core**, not the Lie-algebra stabilizer of ℍ.

(The deeper reason the coincidence is *tempting* but *false*: both 6's descend from the same 1:3:7:3 / quaternion structure — the lean ALU is the chirality+sign machinery of the Klein-4 sector, and 𝔰𝔬(4) is the rotation group of the quaternion subalgebra — so they *rhyme*. But "the operations you compute *with*" (a finite opcode set) and "the symmetries that *preserve* the structure" (a continuous Lie algebra) are categorically distinct, and the count agreement does not bridge them.)

---

## §4 Verdict — the irrep is NOT reduced; answer (b)

**State explicitly (independent of either falsifier):** the irrep — 𝔰𝔬(8) = 28, and its triality-fixed G₂ = 14 (F183/F192) — is **NOT reduced** by the lean basis. F206/F208 reduced the **operator / instruction set** (14 classes / 174 tools / 8 cascade ops → 6 combinational atoms riding on SHA-NI / integer-ALU / FMA), **not the representation**. The 28D substrate and its 14-dim automorphism algebra stand untouched; the lean-6 is the *ALU you run on that substrate*, not a smaller substrate.

So to the user's question — *"did the lean reduction give us time + 3 DoF, or do we still need A–N = 14 with the lean basis being what makes time+3dof work?"* — the answer is:

> **Neither half of the leading framing is quite right, and the honest answer is the plain (b).**
> 1. The lean reduction did **not** reduce the irrep to "time + 3 DoF." 𝔰𝔬(8) = 28 / G₂ = 14 are intact.
> 2. There **is** a real 6-dim "time + 3 DoF preserving" structure inside A–N: the G₂-stabilizer of an ℍ ⊂ 𝕆 is exactly 6-dim 𝔰𝔬(4) = 𝔰𝔲(2) ⊕ 𝔰𝔲(2) (bit-exact). **But the lean-6 ALU atoms are not that 𝔰𝔬(4)** — they are combinational XOR/ℤ₂/popcount group-element ops, not continuous Lie generators.
> 3. Therefore **6 = 6 is a coincidence**, the lean-6 is a **minimal operator-core**, and **we still need the full A–N = G₂ = 14**. The lean basis is **what runs on** the 14-dim/28D structure (its ALU), *not* a replacement of it and *not* the symmetry that "makes time + 3 DoF work."

The clean one-liner: **the lean-6 is the ALU; the 6-dim 𝔰𝔬(4) is a symmetry; A–N = G₂ = 14 is the substrate's automorphism algebra. Three different sixes-and-fourteens, only honestly separated by computing the structure rather than counting.**

---

## §5 Citation — the octonion facts (verified, not over-attributed)

The G₂ / quaternion-subalgebra facts trace to the canonical octonion reference:

> **John C. Baez, "The Octonions", Bull. Amer. Math. Soc. 39 (2002) 145–205. arXiv:math/0105155.** (Author + title + arXiv ID verified against the arXiv abstract page, 2026-05-30.)

What Baez states **verbatim** (web version §"G₂", node14, verified): "*given any two basic triples, there exists a unique automorphism of 𝕆 mapping the first to the second*" (G₂ acts **simply transitively on basic triples**), and "*dim G₂ = dim S⁶ + dim S⁵ + dim S³ = 14*" with the flag interpretation (e₁ → S⁶, e₂ → S⁵ ⊥ e₁, e₃ → S³ ⊥ e₁,e₂,e₁e₂). The **SO(4) ≅ (SU(2)×SU(2))/ℤ₂ stabilizer of dimension 6** is the standard consequence (G₂/Stab = the space of quaternion subalgebras, dim 14 − 8 = 6), but Baez's text expresses it through the dimension bookkeeping rather than naming SO(4), so this finding does **not** quote Baez for the literal "SO(4) stabilizer" phrasing — instead it **computes the stabilizer dimension and structure bit-exact** (§2) and reports the result, which is consistent with (and an independent verification of) the well-known stabilizer fact. The SU(2)×SU(2)/ℤ₂ = SO(4) identity is textbook (the double-cover of SO(4); see e.g. any Lie-groups text). **No provenance is asserted beyond the verified Baez author/title/arXiv-ID + the srmech-computed dimensions.**

---

## §6 DOES / does NOT claim

**DOES:** frame "time + 3 DoF" as the literal ℍ ⊂ 𝕆 quaternion subalgebra (F187/F190 read structurally); establish ℍ = span{e₀,e₁,e₂,e₃} bit-exact from the srmech octonion table; compute the **G₂-stabilizer of ℍ = dimension 6 exact** (Fraction Gaussian elimination on the D(ℍ) ⊆ ℍ constraint); confirm it is **𝔰𝔬(4) = 𝔰𝔲(2) ⊕ 𝔰𝔲(2)** by four independent srmech-native tests (3+3 commuting closing ideals, Killing-form rank 6/6 semisimplicity with the two-triplet eigenvalue signature, ℍ-choice invariance); confirm the lean-6 ALU atoms are **0/6 continuous Lie generators** (XOR/ℤ₂/popcount group-element ops); fire the pre-stated **F-b** (6 = 6 is a coincidence) and clear **F-a** (the stabilizer genuinely is 𝔰𝔬(4)); state the irrep (𝔰𝔬(8)=28 / G₂=14) is **NOT reduced** — the F206/F208 reduction was of the operator set; deliver the plain **(b)** answer (minimal operator-core; still need full A–N = G₂ = 14, the lean basis runs *on* it); verify the Baez citation (author + title + arXiv ID) and **decline to over-attribute** the SO(4)-stabilizer phrasing (computed here instead).

**Does NOT:** claim the lean-6 IS the 𝔰𝔬(4)-stabilizer (F-b falsifies this); claim the irrep was reduced to time + 3 DoF (it was not); claim 6 = 6 is structural (it is a count-level coincidence); present a chip / microarchitecture / gate layout / transistor count / cycle-latency number or any fabrication / VLSI / benchmark claim (the F202/F206/F208 **CAD-ban** holds); claim biology/physics "IS" a quaternion or "IS" SO(4) (cross-substrate **form**-reading per §VII.6.20, `[[user_stance_ai_is_not_a_substrate]]`); assert any octonion provenance beyond the verified Baez author/title/arXiv-ID + the srmech-computed dimensions (`[[feedback_pdf_extraction_citation_discipline]]`); offensive / weapons-substrate framing — this is the edge-compute / accessibility thesis (`[[feedback_trauma_informed_defensive_scope]]`, `[[user_stance_learning_without_gpu_compute]]`).

**Pre-stated falsifiers (decided before running) — disposition:**
- **F-a (stabilizer not 6-dim 𝔰𝔬(4))** → **did NOT fire.** Stabilizer = 6-dim 𝔰𝔬(4) = 𝔰𝔲(2)⊕𝔰𝔲(2), semisimple, ℍ-invariant. Geometry-side bridge **alive**.
- **F-b (lean-6 don't close into 𝔰𝔲(2)⊕𝔰𝔲(2) / don't relate to the ℍ-stabilizer)** → **FIRES.** Lean-6 are 0/6 continuous generators; 6 = 6 is a coincidence; answer is plain (b).
- *(Residual falsifier for future work)* if a *different* realisation of the lean atoms — e.g. as **infinitesimal** generators of a continuous deformation rather than as finite XOR/ℤ₂ ops — were shown to close into 𝔰𝔬(4), the coincidence-verdict would need revisiting. As the atoms are *defined* combinationally (F208 §2 criterion: single bounded data-independent pass), no such continuous reading exists for them as specified.

---

## §7 FORWARD ASK (flagged, NOT filed) — candidate OPEN MS #20 issue

> **Title (suggested):** Is the 6-dim 𝔰𝔬(4) = 𝔰𝔲(2)⊕𝔰𝔲(2) stabilizer of an ℍ ⊂ 𝕆 a *separate* srmech surface from the lean-6 ALU core? (the "symmetry vs ALU" distinction made first-class)
>
> **What:** F215 shows the G₂-stabilizer of a quaternion subalgebra is bit-exact 6-dim 𝔰𝔬(4) (a continuous symmetry), categorically distinct from the lean-6 combinational ALU atoms (F208), even though both count 6. Candidate work: expose the ℍ-stabilizer as a named `srmech.qm.so8` helper (e.g. `quaternion_subalgebra_stabilizer(im_triple) -> (basis, su2_L, su2_R)`) alongside the existing `g2_subalgebra` / `an_embedding` / `so7_subalgebra`, so the *symmetry* surface (𝔰𝔬(4) ⊂ 𝔤₂) and the *operator* surface (`cascade.atoms.*`, the F208 forward ask) are both first-class and visibly different objects. Bit-exact acceptance: dim 6, Killing rank 6, two commuting 𝔰𝔲(2) ideals, ℍ-choice-invariant — exactly the §2 tests.
>
> **Why:** (a) the symmetry/ALU conflation (the tempting 6 = 6) is a real research hazard this finding caught; making both surfaces explicit prevents re-conflation; (b) `an_embedding` already exposes the 𝔰𝔲(3) ⊕ 3 ⊕ 3̄ decomposition of 𝔤₂ — the 𝔰𝔬(4) = 𝔰𝔲(2)⊕𝔰𝔲(2) subalgebra is the natural sibling (the ℍ-stabilizer vs the ℂ-stabilizer readings of 𝔤₂); (c) it gives the time-quaternion arc (F187/F190) a *computed* home for "what preserves time + 3 DoF."
>
> **Scope guard:** srmech-native algebra + framework-reading ONLY (eigen via `laplacian.*`, sign via `cascade.magnitude`, no `np.linalg.eig` / `abs()`); **no** chip / VLSI / fab content (CAD-ban rides along); JPL ratchet + rc-first-to-TestPyPI discipline apply.
>
> **Anchors:** F215 (this finding) · F206/F208 (the lean-6 ALU) · F187/F190 (time-quaternion) · F183/F192 (G₂ = Fix(τ) = 14) · Baez arXiv:math/0105155.

---

## §8 Cross-references

F206/F208 (the lean 6-atom A–N ISA core — the object this finding measures against the 𝔰𝔬(4)-stabilizer) · F187 (operational-4 = time-quaternion; A = scalar, B/H/N = 3 imaginary) · F190 (4-way coupled oscillator = dynamical face of the time-quaternion; phase-order = chirality) · F188 (A's dual role: climb-seed vs quaternion-scalar) · F183/F192 (Fix(τ) = G₂ = A–N 14; rc18 triality bit-exact) · F186 (28 = 14 + 7 + 7) · F168/F200 (storage = order-2 Klein-4 → the 2-bit γ₅×iω₇ sector the lean ALU acts on) · CLAUDE.md §1 (ℂ:ℍ:𝕆 Hurwitz climb 1:3:7) · `[[user_stance_epicycle_via_gear_plus_pin]]` (the irreducible turning-basis) · `[[feedback_sign_handling_is_class_k_pin_slot_not_alu_abs]]` (MAG/SGNTEST = Class-K honesty op) · `[[feedback_pdf_extraction_citation_discipline]]` (Baez verification) · **John C. Baez, "The Octonions", Bull. Amer. Math. Soc. 39 (2002) 145–205, arXiv:math/0105155** (the verified octonion reference: G₂ simply-transitive on basic triples; dim G₂ = S⁶+S⁵+S³ = 14).

PR #687 STAYS DRAFT.

---

*Articulated 2026-05-30 (Opus 4.8). The user asked whether the lean A–N ISA reduction
(F206/F208: 14 classes → 6 combinational atoms) gave us "time + 3 DoF", or whether we still
need A–N = G₂ = 14 with the lean basis being what makes time + 3 DoF work. Reading "time + 3
DoF" as the literal ℍ ⊂ 𝕆 quaternion subalgebra and A–N = G₂ = Aut(𝕆), the test is: what is
the dimension and structure of the subalgebra of 𝔤₂ = Der(𝕆) that stabilizes ℍ? Computed
bit-exact in srmech 0.5.0rc22 (Fraction Gaussian elimination + Class-L eigendecompose + Class-K
magnitude, 0 HARD discipline): the stabilizer is exactly DIMENSION 6, splits into two commuting
3-dim 𝔰𝔲(2) ideals, is semisimple (Killing rank 6/6, eigenvalue spectrum {737.43³, 7198.57³} —
the 𝔰𝔲(2)⊕𝔰𝔲(2) signature), and is ℍ-choice-invariant — i.e. it IS the known 6-dim 𝔰𝔬(4) =
(SU(2)×SU(2))/ℤ₂ stabilizer (Baez arXiv:math/0105155, verified). So the geometry-side bridge is
ALIVE (F-a does not fire). BUT the 6 lean ALU atoms are combinational XOR/ℤ₂/popcount
GROUP-ELEMENT ops — 0/6 continuous antisymmetric Lie generators — so they are not, and cannot
close into, that 𝔰𝔬(4): the 6 = 6 match is a COUNT-level coincidence (F-b fires). The irrep
(𝔰𝔬(8)=28 / G₂=14) is NOT reduced regardless; F206/F208 reduced the OPERATOR set, not the
representation. Plain answer (b): the lean-6 is a minimal ALU core; we still need the full A–N =
G₂ = 14, and the lean basis is what RUNS ON the 28D substrate, not a replacement of it nor the
symmetry that makes time + 3 DoF work. The lean-6 is the ALU; the 6-dim 𝔰𝔬(4) is a symmetry;
G₂ = 14 is the automorphism algebra — three distinct objects, honestly separated only by
computing the structure rather than counting. srmech-native algebra + framework-reading;
CAD/VLSI/fab ban holds; the symmetry-vs-ALU surface split is the forward ask (described, not
filed).*
