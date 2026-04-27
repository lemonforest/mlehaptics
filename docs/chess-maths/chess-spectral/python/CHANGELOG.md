# Changelog

All notable changes to this package will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.2.6] — 2026-04-27

Security patch closing CodeQL alert
[#26](https://github.com/lemonforest/mlehaptics/security/code-scanning/26)
(`cpp/command-line-injection`, severity: critical).

### Fixed

- **PGN bridge is no longer launched through a shell.** The C `encode`
  command's PGN ingestion path historically built a command line with
  `snprintf` (interpolating user-supplied `--url` and `--input`
  arguments) and ran it via `popen()`, which routes through `cmd.exe
  /c` on Windows and `/bin/sh -c` on POSIX. CodeQL correctly flagged
  this as `cpp/command-line-injection`: a `--url` containing shell
  metacharacters (`&`, `;`, backtick, `"`, …) would be interpreted as
  shell syntax. The bridge now spawns directly via `fork()` +
  `execvp()` on POSIX and `_pipe()` + `_dup2()` + `_spawnvp()` on
  Windows, with each token (interpreter, script path, flag, value)
  passed as one opaque element of an argv array. No shell is ever
  involved, so user-supplied input cannot escape into command syntax.
  Verified by a negative test: a URL containing `" & echo PWNED & "`
  is now passed verbatim to `pgn_bridge.py` (which rejects it as a
  malformed URL) instead of executing the embedded `echo`.
  ([`src/main.c`](src/main.c) — new `bridge_proc_t`, `bridge_open()`,
  `bridge_close()`; `CS_POPEN` / `CS_PCLOSE` macros removed.)

### No behavior change for legitimate inputs

All 230 Python tests pass against the rebuilt binary with the new
spawn path. PGN file ingestion, stdin PGN ingestion, URL fetch,
`--pgn-start` / `--pgn-count` slicing, and the bridge's exit-code
propagation all behave identically to 1.2.5; only the underlying
process-launch mechanism changed.

## [1.2.5] — 2026-04-27

Re-attempt of the v1.2.4 release. The 1.2.4 tag's publish workflow
hung indefinitely on GitHub Actions' macos-13 (Intel) runner queue
and never reached the PyPI upload step. No 1.2.4 wheels exist on
PyPI. v1.2.5 is the same package contents as v1.2.4 with a working
publish pipeline.

### Fixed

- **Publish workflow drops macos-13 from the wheel matrix.** Apple's
  Intel Mac line is in deprecation; GitHub Actions macos-13 runner
  capacity is severely constrained — runs queue 1+ hour without ever
  starting. Matrix shrinks 4 OS × 4 Python = 16 cells to 3 OS × 4
  Python = 12 cells (`ubuntu-latest`, `macos-14`, `windows-latest`).
  The chess-spectral source still works on Intel Macs; users on that
  platform get the sdist (compiles in ~20 s with cmake + a C
  compiler) instead of a pre-built wheel.

- **CodeQL Default Setup → Advanced Setup.** Default Setup was
  triggering a parse-error status on
  `docs/chess-maths/chess_d4_direct.py` — a research script that's
  not part of any released package. The file parses cleanly under
  CPython 3.9–3.14 (`py_compile` + `ast.parse` succeed at every
  feature_version); CodeQL's specific Python extractor has a quirk
  with it. Default Setup also ran `c-cpp` analysis with
  `build-mode: none` (buildless extraction → less accurate results)
  because our `CMakeLists.txt` isn't at the repo root. New
  `.github/workflows/codeql.yml` runs CodeQL with `build-mode:
  manual` for c-cpp (full cmake build before extract → tracing
  extraction → full type/include coverage) and honors
  `.github/codeql/codeql-config.yml`, which scopes Python analysis
  to the actual shipped packages (`chess_spectral/**`,
  `chess_spectral_4d/**`) plus the antikythera-maths package.
  Research scripts under `docs/chess-maths/` are out of scope.

### No source changes from 1.2.4

The chess-spectral source tree (encoder math, CLI commands, table
data, immolation suite) is byte-identical to 1.2.4. Only CI/release
infrastructure changed.

## [1.2.4] — 2026-04-25

Wires every advertised CLI command and ships the native binaries inside
the wheel. Patch-level because every wired command was already in the
help text and module docstrings — `1.2.3` users had a reasonable
expectation they worked. This release closes the gap between what was
promised and what shipped.

See [ROADMAP.md](../ROADMAP.md) for the current command surface.

### Added — Phase A (FEN4 + single-position encoding)

- **FEN4 v1 placement-literal format** — see [docs/FEN4_FORMAT.md](../docs/FEN4_FORMAT.md).
  Compact, human-readable 4D position literal: `4d-fen v1: K@0,0,0,0;
  k@7,7,7,7; Pw@1,2,3,4`. Pawn axis (W or Y) is mandatory per
  Oana & Chiru Definition 11.
- **C FEN4 parser** in `include/cs_fen_4d.h` + `src/cs_fen_4d.c`.
- **Python FEN4 parser** in `chess_spectral.fen_4d` (`parse`,
  `Fen4ParseError`, `parse_to_jsonl_obj`).
- **C 4D frame I/O** in `include/cs_frame_4d.h` + `src/cs_frame_4d.c`
  (header + frame + read/write helpers, byte-equivalent to
  `python/chess_spectral/frame_4d.py`).
- **`spectral_4d encode-fen4`** (was `cmd_todo` stub) and
  **`chess-spectral-4d encode-fen4`** (was `_not_implemented` stub).
  Both produce byte-identical 1-frame v4 `.spectralz4` files.
- **57 FEN4 parity tests** in `tests/test_fen4_parity.py` covering
  parser accept/reject + C↔Python byte equivalence (plain + gzipped).

### Added — Phase B (bulk encoding + corpus)

- **NDJSON4 ply-log format** — see [docs/NDJSON4_FORMAT.md](../docs/NDJSON4_FORMAT.md).
  One FEN4 per line + optional move metadata. No move replay (mirrors
  the 2D NDJSON pipeline).
- **`spectral_4d encode`** (was stub) — NDJSON4 → v4 `.spectralz4` bulk
  encoder. Header backfill, optional gzip via `cs_gzip`.
- **`spectral_4d csv`** (was stub) — per-ply 11-channel energies +
  dist/cos/dA1 + 8-coord move metadata.
- **`chess-spectral-4d encode-moves4`** (was stub) — Python sibling of
  the C `encode`. Renamed `--fen` → `--fen4` in `encode-fen4` for clarity.
- **`chess-spectral-4d corpus-gen`** (was stub) — wraps N NDJSON4
  ply-logs into a corpus folder + manifest.json.
- **15 e2e parity tests** in `tests/test_e2e_spectralz4_parity.py`
  covering bulk encode + csv determinism.

### Added — Phase C (2D CLI completion)

- **`spectral compare`** — cosine-similarity report between two
  .spectral files (min/mean/max + ply with min cosine).
- **`spectral query`** — 10-channel energy breakdown at a given ply.
- **`spectral heatmap`** — ANSI 8×8 heatmap of one channel at one ply.
- **`spectral analyze`** — JSON summary of A1 peak / drop / crisis ply.
  Heuristics from `chess_spectral_research_notebook.md` §p.1636-1648
  (ΔA₁ derivative analysis).
- **`spectral export`** — full .spectral → JSON dump for the web viewer.
- **`spectral play`** — ply-by-ply listing (non-interactive; defers
  the interactive viewer to a follow-up).
- **Python wrappers** for all five (compare, query, heatmap, analyze,
  export) registered as `spectral_py` subcommands. Output byte-identical
  to the C side.
- **14 2D CLI parity tests** in `tests/test_2d_cli_parity.py`.

### Fixed

- **`compute_safety_field(include_pawns=True)` no longer silently
  produces the `False` answer**. The `include_pawns` parameter was
  previously discarded with `del include_pawns # TODO: ...` (AUDIT
  inventory item #14). It now raises `NotImplementedError` with a
  pointer to the tracking issue. Default behavior (`include_pawns=False`)
  is unchanged.
- **`test_encoder_starting_position_channel_energies` had stale expected
  values** for B1 / B2 (45.2825 / 45.2825 — likely from a pre-PATCH-6
  audit version). Both C and Python encoders now agree on
  B1=0.0 / B2=19.8450; the test was updated to match (AUDIT #24b).
- **Parity test no longer silently skips when fixtures absent**
  (AUDIT #22). `tests/test_parity.py` now generates a synthetic
  3-ply fixture using the C binary if the Carlsen-Caruana cache isn't
  available, ensuring real assertions run in CI.

### Changed

- **Build system: hatchling → scikit-build-core**. The wheel now
  includes the `spectral` and `spectral_4d` native binaries inside
  `chess_spectral/_native/`. PyPI users get the ~38× C encoder
  speedup automatically.
- **`_find_c_binary` extended** to look in the wheel `_native/` dir
  before falling back to repo build paths. New `_find_c_binary_4d` for
  the 4D binary.
- **CMakePresets.json** added with `release` / `dev-debug` / `asan` /
  `msvc-release` presets (per [AUDIT_2026-04.md F-07](../AUDIT_2026-04.md)).
- **GitHub Actions**: existing `chess-spectral-publish.yml` rewritten
  in place to use cibuildwheel (matrix: linux/macos/windows ×
  py3.10–3.13) — preserves the trusted-publisher binding and the
  autotag dispatch path. New `chess-spectral-ci.yml` adds per-PR
  build + test on representative cells PLUS a `verify-wheels` job
  that runs cibuildwheel (cp312 only, all 3 OSes) on every PR — this
  catches wheel-build regressions before tag-push so the publish
  workflow doesn't discover scikit-build-core / cibuildwheel config
  bugs at release time.
- **`STUBBED_CHANNELS` machinery removed** from
  `tests/test_c_py_parity_4d.py` (~40 lines) — no channels have been
  stubbed since v1.1.1/P6 (AUDIT #17).
- **Stale scaffolding comments removed** from `CMakeLists.txt`,
  `src/cs_encoder_4d.c`, and `python/chess_spectral/tables_4d.py`
  (AUDIT #15, #16, #18).
- **Broken plan-file references** (`when-we-need-to-spicy-seahorse.md`,
  `ticklish-dreaming-platypus.md`) replaced with pointers to the
  new [ROADMAP.md](../ROADMAP.md) (AUDIT #19, #20, #21).
- **`miniz` dependency surface documented** at the top of
  `src/cs_gzip.c` — explicitly lists which miniz APIs we use and
  which we deliberately avoid (AUDIT #25).

### Tests

- Total: **156 passing**, 0 skipped (was 27 + 3 skipped before this
  release). 86 of those are new in v1.2.4 (FEN4 + e2e + 2D CLI parity).
- C↔Python byte-for-byte parity now gated end-to-end for both 2D and
  4D encoders, including 1-frame and N-frame `.spectralz` / `.spectralz4`
  files.

## [1.2.3] — 2026-04-24

Restores the `[corpus]`-optional contract documented in 1.2.x.
`spectral-chess4d-oana-chiru` (and any other 4D-only consumer) can
now `pip install chess-spectral` without the `[corpus]` extra and
still `import chess_spectral` cleanly.

### Fixed

- **Eager-import regression in `chess_spectral.phase_operators`.**
  Six submodules (`castling`, `occupation_field`, `occupation_aware_a/b/c`,
  `phase_check_detection`) had a top-level `import chess` that ran
  during `from chess_spectral import ...`, transitively forcing
  python-chess (~1.5 MB) as a hard dependency even though the
  project declares `chess` as `[corpus]`-optional.  All six now use
  `TYPE_CHECKING`-gated annotations and function-body lazy imports.

  `castling.py` additionally replaced the module-level
  `chess.WHITE` / `chess.BLACK` references (used as keys in the
  `CASTLES` dict literal) with explicit `_WHITE = True` /
  `_BLACK = False` constants — documented as matching the stable
  python-chess API where `chess.Color is bool`.

### Measured impact

- `import chess_spectral` with python-chess **blocked from
  sys.meta_path**: succeeds in ~3.1 s (was `ImportError` before).
- `import chess_spectral` with python-chess available: 3590 ms →
  3174 ms (−416 ms, 11 % faster; python-chess no longer loaded
  eagerly).
- `sys.modules` count after import: 555 → 554.

### API surface

No public API changes.  All names re-exported from
`chess_spectral` and `chess_spectral.phase_operators` continue to
work identically when python-chess is installed.  Calling a chess-
dependent function (e.g. `occupation_aware_moves_a`, `available_
castles`) without python-chess installed raises `ImportError` at
call time with a clear message, instead of at import time.

### Tests

All 161 tests pass (92 phase_operators + 69 core).
`tests/test_parity.py::test_encoder_starting_position_channel_energies`
is a known pre-existing failure unrelated to this change
(expected values in the fixture have not been updated since the
1.2.1 B₁/B₂ character fix); it fails identically on `main` at
1.2.2.

## [1.2.2] — 2026-04-23

Source-tree consistency follow-up to 1.2.1.  The 1.2.1 release corrected
`chess_spectral.tables.CHARS` in the Python package but did not
regenerate the companion C data file `src/cs_tables_data.c`, which
continued to hold the pre-fix B₁/B₂ rows.  The PyPI wheel is pure-Python
and therefore was already correct at 1.2.1 — users who `pip install
chess-spectral==1.2.1` saw the fix via `tables.py`.  **Users who rebuild
the companion `spectral.exe` / `spectral_4d.exe` C binaries from source
(CMake Release) at the 1.2.1 tag would get the old broken B₁/B₂ values**
and the C ↔ Python parity test (`tests/test_c_py_parity.py`) would
diverge.  1.2.2 closes that gap.

### Fixed

- Regenerated `src/cs_tables_data.c` from the corrected Python
  `tables.CHARS` by re-running `codegen/emit_tables.py`.  Delta vs
  1.2.1 is 2 lines (only the CHARS[3] and CHARS[4] rows), matching
  the Python delta committed in 1.2.1:

      B₁: {1,-1, 1,-1, 1,-1, 1,-1}   →  {1,-1, 1,-1, +1,+1,-1,-1}
      B₂: {1,-1, 1,-1,-1, 1,-1, 1}   →  {1,-1, 1,-1,-1,-1,+1,+1}

- Rebuilt `spectral.exe` locally (CMake Release target) against the
  regenerated C source and re-ran the committed parity test:

      OK: 88 frames × 640 dims, max |delta| = 0 (byte-identical),
      move metadata identical

  End-to-end regression: Python fix (from 1.2.1) → codegen →
  regenerated C source (this release) → rebuilt C binary →
  spectralz v4 frames all agree.

### No PyPI wheel changes

- The pure-Python wheel produced by hatchling at 1.2.2 is byte-
  identical to the wheel produced at 1.2.1.  The release exists to
  keep the tagged source tree internally consistent and so that
  `git diff chess-spectral-v1.2.1 chess-spectral-v1.2.2 -- chess-spectral/src/`
  is a legible 2-line C data delta.  Same pattern as the 1.1.3
  "pipeline-exercise" release that drove the autotag → PyPI chain
  end-to-end without changing behaviour.

### Advisory for spectralz users

Any `.spectralz` v4 frames produced by a C binary built from source at
or before 1.2.1 have stale B₁/B₂ dims (640-dim encoding, channels
128-191 and 192-255).  Pure-Python-encoded frames are unaffected.
Affected users should re-encode their corpora with a 1.2.2-built C
binary (or any Python-backed encoder at 1.2.1+).

### Changed

- Version bumped 1.2.1 → 1.2.2 (semver patch; source-tree
  consistency; no public-API change).

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
