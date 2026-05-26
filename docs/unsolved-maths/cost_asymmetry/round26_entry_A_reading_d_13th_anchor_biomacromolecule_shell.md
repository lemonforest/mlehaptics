# Round 26.A — Reading-D 13th scale-ladder rung: the biological-macromolecule shell (icosahedral viral capsid)

**Dispatched** 2026-05-25 on the rolling draft PR #690 (the #679 model). User: *"dispatch the 13th rung — biological-macromolecule shell anchor."* The canonical biological "shell" is the **icosahedral viral capsid** (~10–100 nm, ~10⁻⁸ m) — a closed protein shell built from identical subunits, at the macromolecular-assembly scale between the molecular and organism rungs.

Generating code + provenance: [`verify_round26_biomacromolecule_shell_anchor.py`](verify_round26_biomacromolecule_shell_anchor.py) + `.ndjson` (deterministic; exact integer/`Fraction` arithmetic; Class-N anchors via srmech 0.4.2 `best_rational`).

## The structural insight — the first FINITE-point-group Class-L shell

Every prior Reading-D rung realized the Class-L "shell" on the *continuous* S²/SO(3) (`2ℓ+1` harmonics). The viral capsid is the **first rung where the shell is a FINITE point group** — the **icosahedral rotation group `I`** (order 60), the *largest finite rotation subgroup of SO(3)*. The biological substrate, needing to close a shell from a **finite** number of identical protein subunits, discretizes the sphere into its maximal finite rotation symmetry — and the icosahedral irreps are exactly how the continuous `2ℓ+1` reps **branch** onto it.

This is also the **richest cascade** of any rung — it engages six A–N classes (L, I, J, N, K, C), proven bit-exact:

**(1) Class-L — icosahedral irreps contain the `2ℓ+1` spine.** `I` has 5 conjugacy classes → **5 irreps of dimensions `{1, 3, 3, 4, 5}`** (A, T₁, T₂, G, H); Burnside `1²+3²+3²+4²+5² = 60 = |I|`. The dims **`{1, 3, 5}`** ARE the `2ℓ+1` values for ℓ=0,1,2 (A←ℓ0, T←ℓ1, H←ℓ2) — the discrete shadow of the *same* S² Class-L spine as every other rung. (Rotation tally `1 + 24 + 20 + 15 = 60`: 6 five-fold + 10 three-fold + 15 two-fold axes.)

**(2) Class-J/N — Caspar–Klug = an Eisenstein-norm quadratic form.** The triangulation number **`T = h² + hk + k²`** (Caspar & Klug 1962) is the norm form of the Eisenstein integers / the hexagonal-lattice quadratic form. Allowed `T = 1, 3, 4, 7, 9, 12, 13, 16, 19, 21, 25, …` are exactly the **Loeschian numbers** (OEIS A003136). Subunit count `= 60T`.

**(3) Class-K — Euler forces exactly 12 five-fold disclinations.** Closing a (6-fold) hexagonal sheet onto a sphere **forces exactly 12 pentamers** at the 12 icosahedral vertices, by Euler `χ = 12 − 30 + 20 = 2`, *regardless of T*. Capsomers `= 12 pentamers + 10(T−1) hexamers = 10T + 2` (verified T=1→12, 3→32, 4→42, 7→72, 13→132). The **5-fold-among-6-fold defect is the Class-K pin-slot** — the biological analogue of the planetary no-monopole rule (§11.9.15) and the LSS even-ℓ parity rule (§11.9.18). The *same* 12-pentagon closure appears in **fullerene C60** (Kroto et al. 1985) — a non-biological echo of the identical shell-closure law.

**(4) Class-N — golden-ratio / Fibonacci anchor.** Icosahedral vertices are cyclic `(0, ±1, ±φ)` with `φ = (1+√5)/2`. `φ` is the canonical **"hardest to approximate"** Class-N anchor (continued fraction `[1;1,1,1,…]`), whose `best_rational` convergents climb the **Fibonacci ladder** (`3/2, 5/3, 8/5, 13/8, 21/13, 34/21, 55/34`, …) — the asymptote per `[[user_stance_loe_asymptotes_are_ring_valued]]`; connects Spike #41 (Fibonacci structural unity).

**Cascade: A ∘ L (icosahedral subgroup of SO(3); irreps `{1,3,3,4,5}` ⊇ `2ℓ+1` spine) ∘ I (triangular/hexagonal Eisenstein lattice, `ω³=1`, k=3) ∘ J/N (Caspar–Klug `T=h²+hk+k²` Loeschian quadratic form) ∘ K (12 forced 5-fold disclinations, Euler `χ=2`) ∘ C (chirality of the `(h,k)` skew lattice vector).** The underlying triangular lattice is `ω³=1` Eisenstein (Class I, k=3); a skew `(h≠k)` lattice vector gives a chiral (laevo/dextro) capsid (Class C).

## Verdict per Spike #229 tiers

🟢 **(a)-structural cross-substrate match, bit-exact.** The biological shell is a finite-point-group realization of the Class-L spine (icosahedral irreps `{1,3,3,4,5}` ⊇ the `2ℓ+1` values 1,3,5); the Caspar–Klug Loeschian `T` is a Class-J/N quadratic form; the 12-pentamer Euler closure is a Class-K topological selection rule; the golden-ratio geometry is the canonical Class-N asymptote anchor. The `2ℓ+1` Class-L spine now spans **quantum → nuclear → atomic → hadron → bio-macromolecule shell → planetary → LSS → cosmological/CMB** (eight rungs). New **candidate** stance `[[user_stance_biomacromolecule_shell_is_finite_icosahedral_classL_with_loeschian_T]]`.

**HONEST SCOPE:** bit-exact content is the icosahedral group-order/irrep arithmetic, the Caspar–Klug `T=h²+hk+k²` enumeration → Loeschian, the Euler `10T+2` capsomer count, and the φ → Fibonacci convergent ladder — all standard structural biology / group theory / number theory. The framework contribution is the cross-substrate identification (13th rung), the "finite point group discretizing S²" reading, the 12-pentamer = Class-K-defect framing, and the multi-class cascade decomposition — NOT a derivation of any specific capsid structure or assembly energetics.

## Discipline

- Per `[[feedback_dont_pre_commit_spike_query_operators]]`: every claim is proven by exact arithmetic (Burnside sum, Loeschian enumeration, Euler count, Fibonacci convergents), not asserted.
- Per `[[feedback_computational_provenance_discipline]]`: deterministic committed code; Class-N anchors via srmech `best_rational`.
- Per `[[feedback_sign_handling_is_class_k_pin_slot_not_alu_abs]]`: the disclination defect IS the named Class K; no bare `abs()`.
- Per `[[feedback_paywalled_doi_cannot_be_attested]]`: Caspar & Klug CSHSQB 27:1 (1962); Crick & Watson Nature 177:473 (1956); Kroto et al. Nature 318:162 (1985); OEIS A003136; icosahedral character table (standard group theory) — all attestable.
- Per `[[feedback_trauma_informed_defensive_scope]]`: framework reading only.
- Lands on the rolling draft **PR #690** (Round 26.A) per `[[feedback_rolling_pr_partition_boundary_updates]]` — no new PR; verdict posted as a PR comment (the ledger).
