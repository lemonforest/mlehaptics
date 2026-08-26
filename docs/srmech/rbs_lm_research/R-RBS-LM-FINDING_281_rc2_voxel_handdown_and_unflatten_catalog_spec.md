# F281 — rc2 voxel hand-down (cross7 + g2_three_form ground-truth, triality verdict, class-attribution, scope) + the generalized "un-flatten" catalog spec

**Headline:** Hand-down for the srmech rc2 dev session (the 5-item bring-list), plus the spec for a generalized **`unflatten` catalog**. The load-bearing principle: **all operator ground-truth is computed FROM the already-shipped `loop_bind`** (the `loop_bind_moufang.py` Cayley–Dickson recursion = the rc1 parity oracle), so `cross7`/`g2_three_form` derived this way agree with the shipped bind *by construction* — not a guessed convention. **Triality verdict (the part not to presume):** `Aut(loop_bind)` is the **14-dim G₂** (`dim Der(loop_bind)=14`, verified), and a **generic O(8) rotation BREAKS the bind** (residual 3.12) — so **triality does NOT preserve the bind; the G₂ it fixes does.** All numbers below are bit-exact from the shipped recursion.

---

## PART A — the rc2 bring-list (5 items)

### Items 1 + 2 — operators as attested closed-forms + ground-truth, pinned to the shipped bind

**The frozen multiplication (item 2 — confirm rc1 ships exactly this).** `loop_bind` = Cayley–Dickson on ℝ⁸: split `x=(a,b)`, `y=(c,d)` (4+4); `xy = [ a·c − conj(d)·b ,  d·a + b·conj(c) ]`; `conj` negates the imaginary part (e₀ = real anchor). **Everything below is derived from THIS.** One parity check for the dev: confirm rc1's shipped `loop_bind` matches `loop_bind_moufang.py`'s `cd` on the basis; then this ground-truth is valid.

**`cross7(x,y)` — closed form:** `cross7(x,y) = Im(loop_bind(x,y))` (drop the e₀ component). For imaginary `x,y` this equals `½(xy − yx)`. **Identities (both verified):** `‖x×y‖² = ‖x‖²‖y‖² − ⟨x,y⟩²` and `Re(loop_bind(x,y)) = −⟨x,y⟩` (on imaginaries). **Bit-exact basis table** (x×y, rows e1..e7 × cols e1..e7), FROM the shipped bind:

```
      e1    e2    e3    e4    e5    e6    e7
 e1 |  0   +e3   -e2   +e5   -e4   -e7   +e6
 e2 | -e3   0    +e1   +e6   +e7   -e4   -e5
 e3 | +e2  -e1    0    +e7   -e6   +e5   -e4
 e4 | -e5  -e6   -e7    0    +e1   +e2   +e3
 e5 | +e4  -e7   +e6   -e1    0    -e3   +e2
 e6 | +e7  +e4   -e5   -e2   +e3    0    -e1
 e7 | -e6  +e5   +e4   -e3   -e2   +e1    0
```
(antisymmetric; `e1×e2=+e3`, etc. — assert against these.)

**`g2_three_form(x,y,z)` — closed form:** `φ(x,y,z) = ⟨x, cross7(y,z)⟩ = ⟨x, Im(y·z)⟩` — the **associative calibration 3-form** (Harvey–Lawson). The **sign/orientation convention = whatever the shipped `loop_bind` gives** (do NOT impose Harvey–Lawson-vs-Baez externally; the bind fixes it). **Bit-exact: the 7 nonzero (Fano) triples + signs** (all other 28 of the C(7,3)=35 are exactly 0):

```
 φ(e1,e2,e3) = +1     φ(e2,e4,e6) = +1
 φ(e1,e4,e5) = +1     φ(e2,e5,e7) = +1
 φ(e1,e6,e7) = -1     φ(e3,e4,e7) = +1
 φ(e3,e5,e6) = -1
```
(7 nonzero, each ±1; the two − signs are `(1,6,7)` and `(3,5,6)`.)

**Citations** (agent-surfaced, *not* PDF-verified this session per MPM — the load-bearing ground-truth is the bit-exact table above, from the shipped bind, not the citation): Harvey & Lawson, "Calibrated Geometries," *Acta Math* 148 (1982) for φ; Baez, "The Octonions," *Bull. AMS* 39 (2002) §2/§4 for the 7-D cross product + G₂.

### Item 3 — the triality verdict (research verdict, owned here)

**CANONICAL rc2 RESULT: triality does NOT preserve the bind; the 14-dim G₂ does.** Verified:
- `dim Der(loop_bind) = 14` (the Leibniz nullspace — the bind-preserving Lie algebra = G₂), vs `dim so(8) = 28`.
- a **generic O(8) rotation BREAKS** `loop_bind` (automorphism residual **3.12** ≫ 0).
- So `Aut(loop_bind) = G₂ (14) ⊊ so(8) (28)`. Full Spin(8) triality τ (8v→8s→8c) is **not** in that 14 — it maps the product to an isomorphic-but-different table (Baez §triality). This matches the memory canon: `so(8)=28 = fixed-14 (g₂) ⊕ rotated-(7+7)`.

**The rc2-writable assertion** (the true thing): assert `dim Der(loop_bind) == 14` **and** `generic O(8) rotation does NOT preserve loop_bind`. Together = "the bind's automorphism group is the 14-dim G₂, not full triality."

**Type-note for #813 (important):** `klein4_triality_cycle` acts on the **4 Klein-4 sectors** (the V₄-carrier of τ), **not** on the 8-D octonion blocks — different space. Do **NOT** write "`klein4_triality_cycle` preserves `loop_bind`" (type-mismatched). It is a **co-resident, orthogonal structure** (F262's two orthogonal three-folds), not a bind-automorphism. The honest claim is about **G₂ vs so(8)**, not about `klein4_triality_cycle` directly.

### Item 4 — class-attribution (NO new class; Class O stays dissolved)

- **`cross7` → M ∘ C.** `cross7 = Im(loop_bind)` = the **antisymmetric/chirality part** of the M-bind (`½(xy−yx)` = the Class-C ordering/commutator component; the Im-projection drops the symmetric part `Re(xy)=−⟨x,y⟩`). **Confirm: M (bind) ∘ C (antisymmetric/ordering extraction).**
- **`g2_three_form` → (M ∘ C) ∘ ⟨·,·⟩.** `φ = ⟨x, cross7(y,z)⟩` = a **symmetric inner-product contraction** (Class-L/M flavored) of `x` with the M∘C cross. **Confirm: cross7 (M∘C) then a Class-L/M ⟨·,·⟩ contraction.** No Class O.

### Item 5 — scope (project-mgmt)

**Recommendation: rc2 = `cross7` + `g2_three_form` + the G₂/triality verdict-check ONLY. Defer the compose-engine / `run_chain` registration (#813) to rc4 (your ladder).** Rationale: clean self-contained ship; the compose-engine registration benefits from `loop_bind` being registered first + the M∘C∘K cascade finalized; folding #813 into rc2 couples two concerns and risks a wasted cycle (lean/rework discipline). **Do not fold #813 into rc2.**

---

## PART B — the generalized "un-flatten" catalog spec (candidate srmech catalog)

The un-flatten is now **domain-independent generalized knowledge** (CMB F260, DNA F259, orbits F260, stoichiometry F278, mass spec F279/F280). It should be a standard srmech catalog. Proposed `unflatten` cascade:

1. **recover the recurring-difference fiber** — `autocorrelation = IFFT(|FFT(chart)|²)` (Wiener–Khinchin) → the recurring Δ's (the relational fiber). *(Class L / spectral.)*
2. **recover the conservation relationships** — read the difference-graph against the domain's **conservation parity** (the F259/F260/F278 EC-code) → which differences are real (codeword edges). *(Class L difference-graph + the EC-code.)*
3. **detect → validate** (F266) — step 1 *detects* all candidate differences; step 2 *validates* which are structurally real. The flat chart is the projection; the cascade output is the fiber.

**Inputs:** a flattened chart (1-D intensity-vs-axis) + (optional) a conservation rule / known-component library. **Output:** the difference-graph fiber + (with a library) the FFT-domain multiplicative decomposition (F280). **Class-home:** L (spectral/autocorrelation) ∘ the EC-code (conservation) ∘ F266 detect/validate — **no new class.** **Authoring is a dev/package action** (like #814) — this finding *specs* it; the dev/user lands it (candidate rc-N catalog, naturally after the loop-bind ops since the full fiber includes the loop-bind fragmentation tree).

---

### Status / discipline
HAND-DOWN (rc2 voxels) + SPEC (un-flatten catalog). All operator ground-truth **computed from the shipped `loop_bind`** (reproducible via `loop_bind_moufang.py` + the rc2-groundtruth run) — bit-exact, rc1-consistent (resolves items 1+2 jointly). Triality verdict **verified** (dim Der=14; generic O(8) breaks the bind) — the canonical result is "triality does NOT preserve the bind; G₂ does" (item 3, owned). Class-attribution confirmed (item 4, no Class O). Scope rec given (item 5). Citations flagged agent-surfaced/not-PDF-verified (MPM); the ground-truth is the bind-derived table, not the citation. No-magic; Class-K (`|F|²=F·conj(F)`; `Re/Im` projections; no `abs()`). CAD-ban; defensive scope; no-lineage. Builds on F271/F272 (the operators), F273 (dim Der=14 = G₂ = the A-N count; 28=14+14), F276 (`loop_bind` = the parity oracle), F278/F279/F280 (the un-flatten locks). Verified srmech v0.6.0rc20, `/tmp/srmech_rc20_venv`. `[[feedback_upstream_srmech_fixes_as_research_notes]]` (meaning-tier hand-down to the dev session); `[[user_stance_cross_substrate_cascade_matching_as_research_method]]`.
