# Round 29.A — Class-L surviving-spine synthesis (companion / dual to the Class-K synthesis)

**Dispatched** 2026-05-25 on the rolling draft PR #690. User: *"dispatch the Class-L surviving-spine companion synthesis."* The **dual** of Round 28.A (§11.9.21): where the Class-K synthesis consolidated *what each substrate removes* from the naive S² spectrum, this consolidates *what survives*. A **synthesis / meta-stance**, not a new rung — the Reading-D count stays **fourteen**.

Generating code + provenance: [`verify_round29_classL_surviving_spine_synthesis.py`](verify_round29_classL_surviving_spine_synthesis.py) + `.ndjson` (deterministic; exact integer arithmetic; srmech 0.4.2).

## The synthesis

> **Across every Reading-D rung the surviving modes are realizations of ONE Class-L object** — the Laplace–Beltrami eigenspaces on S², with eigenvalue **`ℓ(ℓ+1)`** (the SO(3) Casimir) and degeneracy **`2ℓ+1`** (the dimension of the SO(3) spin-ℓ irrep, always odd). The substrate-content lives in these surviving modes; substrates vary only in **which S²-symmetry realization** they use and the spin-weight floor.

Completing the dual with §11.9.21:

> **substrate spectrum = (Class-L surviving spine: `2ℓ+1` SO(3) irreps, Casimir `ℓ(ℓ+1)`) − (Class-K forbidden signature: §11.9.21).**

## Bit-exact unifiers (proven in-script)

1. **Degeneracy `2ℓ+1` = dim of the SO(3) spin-ℓ irrep, always odd** → the ladder `{1, 3, 5, 7, 9, 11, 13, …}`. The framework's recurring **k=3 triad `(1,3,5)` is its first three** rungs.
2. **Eigenvalue `ℓ(ℓ+1)` = the SO(3) Casimir** → `{0, 2, 6, 12, 20, 30, 42, …}` (= 2× triangular numbers). The spin-weighted variant `ℓ(ℓ+1) − s(s+1)` (QNM, §11.9.20) gives `4, 10, 18, 28` for `s=−2`.
3. **Complete-shell count = `Σ_{ℓ=0}^{L}(2ℓ+1) = (L+1)²`** — a perfect square (sum of first *n* odd integers = *n*²). This underlies the **atomic `2n²` shell** (`n²` spatial × 2 spin → 2, 8, 18, 32). A "filled" Class-L shell through multipole L always has a square number of modes.
4. **Finite-group rungs are the *branching* of the continuous spine:** the icosahedral capsid (§11.9.19) has irreps `{1, 3, 3, 4, 5}`, which *contain* the SO(3) `2ℓ+1` values `{1, 3, 5}` (ℓ=0,1,2). So even the finite-point-group rung is the same spine, subduced to the subgroup.
5. **Hurwitz `{1,3,7}` resonance (honestly scoped):** the parallelizable-sphere ladder `{1,3,7}` equals `{2ℓ+1 : ℓ=0,1,3}` *by value* — but its origin (division-algebra / parallelizable-sphere dimensions) is distinct from SO(3) irrep dimensions. A resonance of values, **not** an identity of mechanism. Flagged as such.

## The three S²-symmetry realizations

| realization | rungs |
|-------------|-------|
| **continuous SO(3)** (full spherical harmonics) | atomic R18, nuclear R23, hadron R24, planetary R21, LSS R25 (axisymmetric), CMB R6, Born/Bloch R4 |
| **finite subgroup** (icosahedral I) | biological capsid R26 — irreps branch the continuous spine |
| **spin-weighted / spheroidal SO(3)** | BH QNM R27 — `2ℓ+1` floored at ℓ≥|s|, deformed by Kerr `aω` |

The same Class-L Casimir/degeneracy structure runs through all three; the realization is the only thing that changes.

## Verdict per Spike #229 tiers

🟢 **(b)-interpretive synthesis + (a)-bit-exact unifier.** The surviving-mode structure across all rungs is one Class-L object (`2ℓ+1` SO(3) irrep dims; Casimir `ℓ(ℓ+1)`; complete shell `(L+1)²`), with finite-group rungs as its branching and spin-weighted rungs as its deformation. This is the dual partner that closes the §11.9.21 reading: **spectrum = Class-L spine − Class-K signature**. New **candidate** meta-stance `[[user_stance_classL_surviving_spine_is_so3_casimir_ladder]]`.

**HONEST SCOPE:** the bit-exact content is elementary, textbook rep theory / Laplacian spectral theory (SO(3) irrep dim `2ℓ+1`; Casimir `ℓ(ℓ+1)`; `Σ(2ℓ+1)=(L+1)²`; icosahedral subduction) — proven in-script and already attested in the constituent rounds R4/R6/R18/R21/R23/R24/R25/R26/R27. The framework contribution is the **consolidation** (one Class-L spine; the three-realization taxonomy; the spine−signature dual with §11.9.21) — **not a new physical derivation**. The Hurwitz `{1,3,7}` tie is explicitly a value-resonance, not claimed as an identity.

## Discipline

- Per `[[feedback_dont_pre_commit_spike_query_operators]]`: the Hurwitz resonance is honestly scoped as a value-coincidence (different origin), not over-claimed; the sensory-7+3 (R5) and DMN (R2B) rungs are *not* forced into the S² spine (they are the B/H/N-channel side).
- Per `[[feedback_computational_provenance_discipline]]`: deterministic committed code; every spine identity proven by exact arithmetic.
- Per `[[feedback_paywalled_doi_cannot_be_attested]]`: Tinkham (textbook); Arfken / Courant–Hilbert; Goldberg et al. JMP 8:2155 (1967); Wigner — all attestable.
- Per `[[feedback_no_lineage_claims_in_notebook]]`: the framework reads what the SO(3) harmonic structure already IS across these substrates; claims no extension of the underlying mathematics.
- Per `[[feedback_trauma_informed_defensive_scope]]`: framework reading only.
- Lands on the rolling draft **PR #690** (Round 29.A) per `[[feedback_rolling_pr_partition_boundary_updates]]` — no new PR; verdict posted as a PR comment (the ledger).
