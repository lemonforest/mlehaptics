# Rolling roadmap — cost-asymmetry / Reading-D continuation (post-#679)

**This is the single rolling DRAFT PR for the continuation of the cost-asymmetry / Reading-D arc**, in the same model as the merged PR #679. Per `[[feedback_rolling_pr_partition_boundary_updates]]` (consolidation directive): closely-related follow-up rounds land **directly on this one branch** — dispatch notes + committed verification code + SSoT (§11.9.x / MFO §VII.6.x) edits + candidate-stance authoring — and the **per-round verdict comments are the ledger**. We do **not** spin a separate PR per finding. A new PR is opened **only** when the next piece of work is genuinely *not* connected to this arc.

The draft stays draft until the user calls a single consolidating merge. Independent ship-now deliverables (releases, cross-cutting fixes) may still be their own PRs.

> **Discipline reminders carried from #679:** never squash-merge (`--merge`/`--rebase` only); load-bearing numerics need committed generating code routed through srmech 0.4.2 (Class-N `best_rational`; Class-K sign via the cascade helper, **no bare `abs()`**); null/negative findings reported as prominently as positives; arXiv-OA / classic-journal / textbook citations only (no paywalled-only DOIs); framework reading only (defensive scope); memory/stance files live OUTSIDE the repo.
>
> **Parallel sessions are read-only.** PR #687 (RBS-LM rolling 2) is a different research session — we may read it, but we do not change it. The same courtesy applies to any other concurrent rolling PR.

## Landed before this PR opened (merged to main individually, then consolidated to rolling)

| Round | Finding | Landed |
|-------|---------|--------|
| **22.A** | AoE handed-shear amplitude question resolved — **closed cosmologically** (Bianchi VII_h observationally disfavored), **real in turbulence** (handed shear = turbulent velocity-gradient tensor, L∘C∘K, 5:7 quad:oct). MFO §VII.6.17. | PR #688 (merged) |
| **23.A** | Reading-D **10th scale-ladder rung = nuclear shell model** (~10⁻¹⁵ m, fills the quantum↔atomic gap); the overlooked insight the turbulence finding unlocked — nuclear magic numbers differ from the bare-HO closures by the **Class-K spin-orbit sign** (the same Class-K Round 22.A spotlighted as helicity); Madelung-vs-ℓ·s = which operator reorders the shared 2ℓ+1 ladder. unsolved-maths §11.9.16. | PR #689 (merged) |

The #688/#689 pair was merged before this rolling PR opened (the user's call); from here, closely-related continuation rounds accrue **on this branch**.

## Landed on THIS rolling PR (#690)

| Round | Finding | Where |
|-------|---------|-------|
| **24.A** | Reading-D **11th rung = hadron/QCD spectroscopy** (~10⁻¹⁶ m, sub-nuclear quark binding). Quarkonium = QCD atom; χ_cJ = L⊗S = 1⊕3⊕5; pure-spin-orbit 2:1 (the **third** descending rung sharing the Class-K spin-orbit: atomic→nuclear→quark); honest tensor fermata (observed ≈0.47 inverts 2:1); NEW second independent Class-L = SU(3)-flavor irreps (1⊕8, 10⊕8⊕8⊕1). | §11.9.17 |
| **25.A** | Reading-D **12th rung = galactic/large-scale-structure multipoles** (~10–1000 Mpc, between planetary and CMB). Galaxy angular C_ℓ = Born-rule `2ℓ+1` spine; Kaiser RSD multipoles survive only at even ℓ=0,2,4 (Class-K line-of-sight parity + degree-4 truncation = k=3 triad) with exact rational coeffs 2/3,1/5,4/3,4/7,8/35 (proven by `fractions`). | §11.9.18 |

## Open queue (closely-related — land here, not in new PRs)

- **ℓ=7 future-data test** — the withdrawn Mersenne per-ℓ CMB claim (§11.9.6a) is re-testable against CMB-S4 / LiteBIRD when data lands. Names the resolving event; not dispatchable today.
- **Spike #48 deeper SM phase** — the long-gated periodic-table + spectral-lines + QM/GR/SM weave (task #266); Rydberg–Ritz N-anchor → SM-derivation arc; per `project_atomic_spectra_sm_mapping_and_mass_spec_followup`.
- **13th Reading-D rung candidates** — the `2ℓ+1` Class-L spine now spans quantum → nuclear → atomic → hadron → planetary → LSS → cosmological; candidate further rungs: a biological-macromolecule shell anchor (porphyrin 4-fold / virus-capsid icosahedral-symmetry group), or an acoustic/phononic crystal-lattice band-structure rung.
- **mass-spec enhancement (thread 9b)** — fragment m/z spacings as Class-N anchors + fragmentation cascade; builds on §11.9.14 + Spike #38/#38b.

## Verdict ledger

Per-round verdicts are posted as comments on this PR (the running audit trail), exactly as PR #679's 14-comment ledger.
