# Changelog

All notable changes to this package will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.2.1] — 2026-04-23

Bug-fix release.  The `CHARS` character table in `chess_spectral.tables`
had a class-constancy violation on the B₁ and B₂ rows that silently
broke idempotence of `project_irrep` on those two irreps.  Sanity tests
(A₁ D₄-invariance, fiber reconstruction) were unaffected and did not
catch the bug.  The defect was discovered by the Othello Phase 1 pass
(`docs/othello-maths/`) which lifted the table to D₄×Z₂, at which point
the failure surfaced as a loud idempotence violation (error ~0.64 on
B₁⁻ and B₂⁻ projections).

### Fixed

- **D₄ character table class-constancy bug in `tables.py` (CHARS).**
  Prior B₁ row `[1,-1, 1,-1, 1,-1, 1,-1]` and B₂ row
  `[1,-1, 1,-1,-1, 1,-1, 1]` failed class-constancy on the conjugacy
  classes `{g=4, g=5}` (axis reflections — σ_v and σ_h) and
  `{g=6, g=7}` (diagonal reflections — σ_d and σ_d').  Verified by
  direct conjugation on `D4_PERMS`: `g₁ · g₄ · g₁⁻¹ = g₅` and
  `g₁ · g₆ · g₁⁻¹ = g₇`, so each reflection pair is conjugate and
  every valid character row must assign them the same value.
- Corrected rows: `B₁ = [1,-1, 1,-1, +1, +1, -1, -1]` (axis reflections
  +1, diagonal −1), `B₂ = [1,-1, 1,-1, -1, -1, +1, +1]` (axis −1,
  diagonal +1).  Post-fix `project_irrep` sanity: idempotence max
  error 2.2×10⁻¹⁶, completeness max error 4.4×10⁻¹⁶ (both at machine
  precision).

### Numerical impact (for users depending on B₁/B₂ projections)

At chess starting position with traditional piece values
(P=1, N=3, B=3.5, R=5, Q=9, K=100):

| Channel | Pre-fix energy | Post-fix energy |
|---------|---------------:|----------------:|
| A₁      | 0.000          | 0.000           |
| A₂      | 4140.500       | 4140.500        |
| **B₁**  | **2545.375**   | **0.000**       |
| **B₂**  | **2545.375**   | **4140.500**    |
| E       | (unchanged)    | (unchanged)     |

Pre-fix B₁ and B₂ frequently coincided numerically because the non-
class-constant character rows collapsed both projections onto the same
linear combination.  Any downstream statistic that distinguished B₁
from B₂ (or combined them in a "breaking" sum) was affected.

Reprocessed chess §9h' depth-gap experiment (55 Stockfish d=1 vs d=20
positions, re-run against the corrected table on 2026-04-23) shows:

- B₁ partial ρ: +0.461 (pre) → +0.303 (post)
- B₂ partial ρ: +0.461 (pre) → +0.490 (post) — now outperforms A₁
  partial +0.456 as a complexity predictor
- "breaking signed" partial ρ: +0.101 non-significant (pre) → −0.310
  p=0.022 (post) — a previously-null hypothesis ("breaking channels
  signed sum predicts advantage after material control") is now
  confirmed

Full audit note with numerical delta table in
`docs/chess-maths/chess_spectral_research_notebook.md` §9a, and the
updated §9h′ Tables 1 and 2.

### No other changes

- No encoder output changes on A₁, A₂, or E channels (those character
  rows were already class-consistent).
- Phase-operator subpackage (`chess_spectral.phase_operators`) does
  not use `tables.CHARS` — unaffected.
- spectralz v4 frame format unchanged.
- Public API surface unchanged (only the numerical values returned
  by `project_irrep(sig, 'B1')` and `project_irrep(sig, 'B2')` move,
  and they move to the correct values).

### Changed

- Version bumped 1.2.0 → 1.2.1 (semver patch; behavioural correction
  to a public numerical API).

## [1.2.0] — 2026-04-22

Feature release. Adds the §11 phase-space move generator and check
detector as the `chess_spectral.phase_operators` subpackage. Previously
these modules lived at `docs/chess-maths/phase_operators/` with no PyPI
distribution; users had to import via `sys.path` tricks. They are now
first-class `chess_spectral` API, installable via
`pip install chess-spectral`.

### Added

- `chess_spectral.phase_operators` subpackage exposing the validated
  §11 primitives:
  - Phase arithmetic on Z_640 (`phi`, `P_rook`, `P_bishop`, `P_queen`,
    `P_king`, `P_knight`, `P_pawn_white`, `P_pawn_black`, and the
    generator constants `ROW_GEN`, `COL_GEN`, `DIAG_NE_SW_GEN`,
    `DIAG_NW_SE_GEN`, `MODULUS`, `KNIGHT_SHIFTS`, `KING_SHIFTS`).
  - Inverse lookup (`invert`, `PHI_TO_RC`, `RC_TO_PHI`,
    `phase_set_to_board`).
  - Occupation-aware move generation in three equivalent solutions
    (`occupation_aware_moves_a/b/c`) including en passant via
    `ep_phase_from_board` and castling via `available_castles` /
    `castle_king_destinations` / `CASTLES`.
  - Phase-native check detection (`phasecast_is_check`,
    `move_leaves_king_in_check`) — validated 100% against
    python-chess's `is_check` over 3393 pseudo-legal transitions in
    the §11.5 experiment.
- Top-level re-exports for the high-traffic primitives so
  `from chess_spectral import phasecast_is_check,
  occupation_aware_moves_c, phi, ...` works without the subpackage
  path. Full API remains accessible at
  `chess_spectral.phase_operators.*`.
- 92 unit tests migrated from the research tree into the packaged
  suite at `tests/phase_operators/`, runnable via
  `pytest tests/phase_operators/`. Existing `chess_spectral` tests
  (encoder parity, roundtrip, edge support) unchanged.

### Changed

- Version bumped 1.1.3 → 1.2.0 (feature addition; semver minor).
- No changes to encoder, `spectralz` wire format, frame I/O, CLI,
  safety field, corpus processing, or any existing public API. All
  pre-1.2.0 call sites continue to work unchanged.

### Research artifacts (unaffected)

The following §11/§12 research modules remain at their original
`docs/chess-maths/` paths because they are experiment-scoped, not
library surface:

- `docs/chess-maths/phase_operators/{equivalence_check,
  occupation_equivalence_check, benchmark_solutions, phase_similarity,
  similarity_experiment, partition_detector, partition_experiment}.py`
- `docs/chess-maths/king_attack_encoder/` (§12 Phase A2)

Their imports now reference `chess_spectral.phase_operators` rather
than relying on `sys.path` manipulation. A `pip install` of
`chess-spectral` is now a prerequisite for running them.

## [1.1.3] — 2026-04-20

Pipeline-exercise release. Functionally identical to 1.1.2; exists to
drive the full autotag → dispatch → PyPI-publish chain end-to-end after
the `workflow_dispatch` + explicit `gh workflow run` fix in
`.github/workflows/chess-spectral-{autotag,publish}.yml` landed on main.
`chess-spectral-v1.1.2` never produced a PyPI artifact (autotag ran
before the dispatch fix and the GITHUB_TOKEN anti-recursion guard
silently swallowed the publish trigger); the dangling tag has been
deleted.

### Changed

- Version bumped 1.1.2 → 1.1.3. No encoder, wire-format, or public-API
  changes.

## [1.1.2] — 2026-04-20

Packaging release. First version published to PyPI under the distribution
name `chess-spectral`. No runtime behavior changes; encoder outputs and
spectralz v4 frame bytes are identical to 1.1.1.

### Added

- `CHANGELOG.md` (this file).
- `py.typed` markers in both `chess_spectral/` and `chess_spectral_4d/`
  so downstream mypy users see the in-tree type hints.
- `Typing :: Typed` classifier and `Homepage` / `Issues` / `Changelog`
  entries in `[project.urls]`.
- Repo-level CI: `.github/workflows/chess-spectral-autotag.yml` watches
  the package subtree for version bumps and creates annotated
  `chess-spectral-v{X.Y.Z}` tags + GitHub Releases, and
  `.github/workflows/chess-spectral-publish.yml` builds the sdist +
  wheel and publishes to PyPI via trusted publishing (OIDC) on tag
  push.

### Changed

- Build backend switched from `setuptools` to `hatchling` to match the
  sibling `python-chess4d-oana-chiru` project's convention. Package
  contents (wheel layout, console scripts, runtime imports) are
  unchanged.
- Version bumped from 1.1.1 → 1.1.2. The encoder, wire formats, and
  public API are identical to 1.1.1; the bump exists because the
  `chess-spectral-v1.1.1` git tag is already in place (downstream
  pins to it via `git+` direct reference) and the autotag workflow
  won't re-tag the same version.

## [1.1.1] — 2026-04-19

Initial pip-installable release (via `git+https://` direct reference;
not yet on PyPI). Ships the 2D 640-dim and 4D 45 056-dim spectral
encoders together under a single distribution.

### Added

- `pyproject.toml` at `docs/chess-maths/chess-spectral/python/` — name
  `chess-spectral`, two packages (`chess_spectral`, `chess_spectral_4d`),
  two console scripts (`chess-spectral`, `chess-spectral-4d`), `[corpus]`
  extra for `python-chess`.
- `chess_spectral_4d` facade re-exports (`encode_4d`, `frame_4d`,
  `write_spectralz_v4`, …) so downstream code can import from the
  top-level package without reaching into `chess_spectral.encoder_4d`.
- 4D encoder v1.1.1 pawn-axis split: `FA_PAWN_W` (W-axis) and
  `FA_PAWN_Y` (Y-axis) sub-channels per Oana & Chiru Definition 11;
  `encoding_dim` grew from 40 960 to 45 056 (11 channels × 4096
  eigenmodes).
- spectralz v4 frame format (bumped from v3); readers still accept v3
  for backward compatibility.
- Full C ↔ Python parity gate on all 11 4D channels at TOL=1e-10
  (see `tests/test_c_py_parity_4d.py`).

### Changed

- 4D encoder: channel slot 9 (previously `FA_PAWN`) is now split;
  `FD_DIAG` moved from slot 9 to slot 10.
- `chess_spectral.corpus` dependency now under the `[corpus]` extra
  rather than required at base install.
