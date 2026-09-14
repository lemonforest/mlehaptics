# F1365 — **preserved: ephemerides notebook §17 per-body spectral catalog scoping, and the rewrite that dropped its minimum-viable framing — already on this branch through PR #236**

Consolidation record (2026-09-14). Source: local branch `research/v0.20.x-per-body-spectral-catalog-scoping`, two commits on no remote (2026-05-06).

## What the commits carried (their own words)

- `3a12b113f` — *"Three parallel research subagents converged on Option B"*: each independently landed on the state-at-epoch lookup pattern, *"NOT BIP-encoded propagation"*. The scopes are §17.1 solid-body geodesy (→ Sol Geodetic Catalog), §17.2 magnetic multipoles (→ MagneticMultipoleCatalog) and §17.3 fluid envelope (→ SolFluidInstrument), and §17.4 integrates them. About 10,000 words; *"No code, no version bump."* Its message closes issue #103.
- `9c097aa1b` — **User (2026-05-06), quoted in the commit:** *"minimum viable shipping has entered our vocabulary again in this PR. that isn't okay. What would make it okay is expanding our v0.20.x and v0.21.x plans, as they pertain, in both our documents and the PR verbiage."* The rewrite commits to full-coverage per-version deliverables:
  - v0.20.0 Sol Geodetic Catalog, *"~38 bodies × 3 channels"* (was *"6 bodies × 3 channels = 18 entries"*);
  - v0.20.1 MagneticMultipoleCatalog with the full published roster;
  - v0.20.2 SolFluidInstrument with all three Option-D layers;
  - v0.21.0 SphericalHarmonicCatalog unification;
  - v0.21.1+ three cross-channel couplings, one per minor version.

## Where it lives on PR #687

- This branch carries PR #236's merge `9c7558bad` (*"notebook: §17 per-body spectral catalog scoping (solid-body geodesy + magnetic multipoles + fluid envelope; closes #103) (#236)"*). The path-limited `git diff 9c7558bad 9c097aa1b` on the notebook is empty, so the branch's final state is already here. Nothing was cherry-picked.
- Archive: `preserved_branches/research__v0.20.x-per-body-spectral-catalog-scoping/`.

## DIFFERS

- `docs/antikythera-maths/ephemerides_spectral_research_notebook.md` — the notebook has moved on since `9c7558bad`, whose version equals this branch's tip.

Branch safe to delete once this commit is on origin: yes

Integrated 2026-09-14: see F1373.
