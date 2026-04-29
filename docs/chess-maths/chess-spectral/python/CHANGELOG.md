# Changelog

All notable changes to this package will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.4.0] — API gaps for Phase 5b / chess4D-OC bridge surface

Closes the nine API gaps captured in research notebook §16.9 + §17.3
(the chess4D-OC consumer's wish-list before Phase 6 engine work
begins). All of v1.3.x's existing API and tests remain green; this
release is purely additive.

### Added

- **FEN4 round-trip — `chess_spectral.fen_4d.serialize(pos) -> str`.**
  Inverse of `parse`. Round-trip property: `parse(serialize(p)) == p`
  for any valid position. Output is canonical (pieces sorted by
  ascending square index, separated by `"; "`); empty positions
  serialize to just `"4d-fen v1:"` (the bare prefix). Closes §16.9
  #4. Tested in `tests/test_fen4_round_trip.py` against:
  the 15 fixture positions (`tests/fixtures/positions_4d.jsonl`),
  100 seeded random self-play positions, the 4096-piece
  every-cell stress case, and the empty-position + canonical-form
  invariants.

- **State-load API — `chess_spectral_4d.bridge.load_state(fen4)`.**
  Wraps `fen_4d.parse` + `GameState4D.from_fen4` and returns either
  `{"ok": True, "state": GameState4D}` on success or `{"ok":
  False, "error": "..."}` on parse failure. Closes §16.9 #5.
  Tested in `tests/test_load_state_4d.py` with encoding-parity vs
  direct `parse()` on 4 fixture FENs and round-trip via
  `state.to_fen4()`.

- **Promotion-piece argument — `apply_move(state, from_sq, to_sq,
  *, promote_to='Q')`** (new module
  `chess_spectral_4d.apply_move`). Default `'Q'` matches the
  v1.3.x silent auto-queen behavior; accepts any of `'Q'`, `'R'`,
  `'B'`, `'N'` (case-insensitive). Color is inferred from the
  moving pawn (white pawn → uppercase, black pawn → lowercase).
  Promotion is triggered iff the moving piece is a pawn and the
  destination is on the appropriate "promotion rank" for the
  pawn's `(color, axis)`; `promote_to` is silently ignored on
  non-promotion moves (matches python-chess semantics). Closes
  §16.9 #1. Tested in `tests/test_apply_move_promotion_4d.py`
  with all four targets × white/black × W-axis/Y-axis pawns,
  plus encoded-vector reflects-promoted-piece checks.

- **Move-history plumbing — `chess_spectral_4d.move_history`.**
  New `Move4D` (frozen dataclass record), `MoveHistory4D`
  (append-only ply list with side-to-move, half-move-clock, and
  position-hash table), and `GameState4D` (position + history
  bundle). Position hashing for repetition tracking uses SHA-256
  of `serialize(pos)` plus the side-to-move byte (deterministic,
  collision-resistant in practice; no Zobrist tables to maintain).
  Side-to-move and half-move clock are tracked **on the history
  container, not on the position dict** — keeps the encoder's
  input contract unchanged. Closes §16.9 #2 prerequisite.

- **Threefold-repetition detection.** Triggered when any
  `(position, side-to-move)` hash count reaches
  `THREEFOLD_THRESHOLD = 3`. Reachable via
  `gs.history.repetition_count(pos)` and through
  `bridge.get_draw_status` (priority: threefold > 50-move >
  insufficient > stalemate). Closes §16.9 #2. Tested in
  `tests/test_game_state_4d.py` with a deterministic 8-ply A→B→A→B
  cycle (3 occurrences of the starting position) — draw fires at
  ply 8.

- **50-move-rule detection.** `MoveHistory4D.half_move_clock`
  resets to 0 on any pawn move OR capture (FIDE Article 9.3) and
  increments otherwise. Threshold `FIFTY_MOVE_THRESHOLD = 100`
  (50 full moves). Reachable via `gs.history.half_move_clock` and
  through `bridge.get_draw_status`. Closes §16.9 #3. Tested with
  a 100-half-move two-king walk through 51 unique squares per
  side (no threefold contamination).

- **Insufficient-material classification (2D) —
  `bridge.is_insufficient_material_2d(pos_2d)`.** Matches
  python-chess: K-vs-K, K+B-vs-K, K+N-vs-K, and K+B-vs-K+B with
  bishops on same-color squares all classify as `True`; K+P,
  K+R, K+Q, two-knights-one-side, and opposite-color KBKB all
  classify as `False`. Closes the 2D half of the new §17.3 row.
  4D analog (`is_insufficient_material_4d`) raises
  `NotImplementedError` — the bishop "color class" rule on Z_8^4
  is an open design question deferred to a future ADR.

- **`getDrawStatus()` bridge method —
  `bridge.get_draw_status(state, *, has_legal_moves=...)`.**
  Returns `{"ok": True, "status": <one of 'none', 'threefold',
  'fifty-move', 'insufficient', 'stalemate'>}`. Detection priority:
  threefold > 50-move > insufficient > stalemate. Stalemate
  detection requires the caller to pass `has_legal_moves=True`
  or `False`; if `None` is passed (default) and no other draw
  fires, the function raises `NotImplementedError` rather than
  silently mis-classifying a stalemate as `'none'`. The 4D
  legal-moves observable is wired in v1.5+ (Track A's QM
  roadmap); 2D callers can compute the boolean via python-chess
  and pass it through. Closes §17.3 row 1.

- **`getMoveHistory()` bridge method —
  `bridge.get_move_history(state)`.** Returns
  `{"ok": True, "moves": [<Move4D.to_dict()>, ...]}`. Each entry
  carries `ply`, `from`, `to`, `piece`, `halfMoveClock`, plus
  optional `promoteTo` and `capturedPiece` keys. Pyodide-bridge
  friendly (no internal types leak out; pure-Python lists +
  dicts + ints). Closes §17.3 row 2.

- **Castling + en-passant regression suite — chess4d 0.4 audit.**
  `tests/test_castling_ep_4d_regression.py` (8 tests; ~7 pass + 1
  path-dependent skip on a typical run) exercises chess4d's
  castling-rights bookkeeping, EP-target tracking, and Move4D flag
  surface. Findings documented in
  `python/research/chess4d_castling_ep_audit.md`: chess4d 0.4
  handles both edge cases correctly through its `legal_moves()`
  generator; no silent-corruption bugs found, no regression patch
  needed. Closes §17.3 castling + EP rows.

### Test count delta

The new test files add **210 passing tests + 1 path-dependent
skip** on top of the v1.3.2 baseline. Breakdown:

| File | Passing | Skipped |
|---|---|---|
| `test_fen4_round_trip.py` | 130 | 0 |
| `test_load_state_4d.py` | 16 | 0 |
| `test_apply_move_promotion_4d.py` | 26 | 0 |
| `test_game_state_4d.py` | 31 | 0 |
| `test_castling_ep_4d_regression.py` | 7 | 1 |
| **Total** | **210** | **1** |

All v1.3.2 tests continue to pass — 102 tests in the fast subset
(`test_version_consistency`, `test_roundtrip_4d`, `test_fen4_parity`,
`test_encoder_4d`); 44 876 in the parametric phase-operator suites;
260 in the pawn-axis / phase-4d-check / phase-4d-unobstructed
suites; 92 in the 2D phase_operators suite. No regressions.

### Bridge contract pinned in `chess_spectral_4d/__init__.py`

The new public surface is exposed at the top level:

    GameState4D, Move4D, MoveHistory4D       # game-state types
    SIDE_WHITE, SIDE_BLACK                   # side-to-move
    coord_to_sq, sq_to_coord                 # 4D ↔ linear index
    position_hash_key                        # repetition hash
    apply_move                               # state-application
    bridge                                   # Pyodide-bridge module

with the FEN4 serializer at `chess_spectral.fen_4d.serialize`.

### Deferred to future minors

- **4D insufficient-material classification.** Open design question
  on the bishop "color class" rule for Z_8^4. v1.4.0 ships the 2D
  version (`is_insufficient_material_2d`) and a placeholder
  `is_insufficient_material_4d` that raises `NotImplementedError`.
  Tracked for a v1.5.x or v1.6.x ADR.
- **4D stalemate detection.** Requires the QM legal-moves
  observable currently being built in Track A. v1.4.0's
  `get_draw_status` accepts `has_legal_moves: bool` to defer the
  decision to the caller; the boolean will become a `state.has_legal_moves`
  property in v1.5+ when the legal-move generator is wired
  through.

## [1.3.2] — 2026-04-28

Two correctness fixes that ride together: the v1.3.1 corpus-encoding
bug (the user-reported `FEN4 parse error -4` truncation) and the
long-running `__version__` string drift. No API change.

### Fixed

- **`spectral_4d encode` (NDJSON4 → .spectralz4) no longer truncates
  FEN4 input at 2048 bytes.** Pre-1.3.2 the bulk encode path used a
  2 KiB stack buffer for each FEN4 string, plus an 8 KiB stack
  buffer for each NDJSON line. Real chess4d positions serialize to
  ~9.4 KiB at startpos and well above for any in-game position, so
  the bulk path was effectively unusable for the chess4d corpus —
  it produced a header-only `.spectralz4` (256 bytes) and a
  misleading `FEN4 parse error -4` (`CODE_BAD_COORD`) on stderr.
  The single-position writer (`encode-fen4`) was unaffected because
  it points directly at `argv` with no buffer copy. Fix:
    - The internal FEN4 buffer in `cmd_encode` grew from 2 KiB stack
      to 64 KiB heap; the line buffer grew from 8 KiB stack to 80
      KiB heap. Both buffers are paired with `free()` calls on every
      exit path.
    - `json_str_field4` now returns `-2` on overflow (instead of
      silently truncating to fit). The caller emits a clear
      `"FEN4 string longer than 64 KiB"` error, so any future
      hypothetical overflow surfaces as actionable diagnostic
      output rather than as a misleading parse failure downstream.
    - The same fix is applied to the 2D `spectral encode` path
      (`json_str_field` returns `-2` on overflow; the 2D `fen[]`
      buffer grew from 128 to 8192 bytes — 2D FENs are short, but
      the silent-truncate failure mode was identical).
  New regression tests: [`test_encode_long_fen4.py`](tests/test_encode_long_fen4.py)
  pins the 193-piece originally-broken case and the 4096-piece
  worst-case fully-loaded board. The immolation suite
  ([`test_smoke_e2e.py`](tests/test_smoke_e2e.py)) now asserts
  byte-equivalence between the two C 4D encode paths
  (`encode-fen4 --fen4 STRING` vs `encode -i NDJSON4`) at both
  short and long-FEN4 sizes — the invariant that makes the
  truncation bug impossible to ship again.

- **`chess_spectral.__version__` no longer drifts from the dist
  version.** Pre-1.3.2 the string was hardcoded at `"1.2.3"` and
  never updated across six successive `pyproject.toml` bumps
  (1.2.4, 1.2.5, 1.2.6, 1.3.0, 1.3.1). Users on v1.3.1 who imported
  `chess_spectral.__version__` saw "1.2.3" while
  `importlib.metadata.version("chess-spectral")` correctly reported
  "1.3.1". Both `chess_spectral.__version__` and
  `chess_spectral_4d.__version__` now derive dynamically from
  `importlib.metadata`; they cannot drift again.

### Changed

- **`chess_spectral_4d.VERSION` is now an alias for
  `__version__`** (the dist version). Pre-1.3.2 it carried a
  separate "encoder format version" string ("1.1.3") that bumped on
  protocol changes — but the two version concepts caused more
  confusion than the artifact-protocol distinction was worth, with
  multiple dist releases shipping while VERSION stayed pinned.
  Collapsed to a single source of truth (the dist version in
  `pyproject.toml`). `chess-spectral-4d version` will now print the
  dist version in its banner instead of "1.1.3".

### Added (continued)

- **`tests/test_version_consistency.py`** pins three regression
  assertions: `chess_spectral.__version__`,
  `chess_spectral_4d.__version__`, and `chess_spectral_4d.VERSION`
  must all equal `importlib.metadata.version("chess-spectral")`.
  Future hardcoding regressions fail at test time.

- **Immolation suite version-drift guard**
  ([`test_smoke_e2e.py::test_no_hardcoded_version_strings_drift_in_shipped_python`](tests/test_smoke_e2e.py)).
  Walks shipped Python sources and fails on any
  `__version__ = "X.Y.Z"` literal other than the documented
  `"0.0.0+unknown"` fallback, AND asserts that `pyproject.toml` and
  `pyproject-pure.toml` agree on the dist version. This is the
  structural backstop for the `__version__` drift bug: even if a
  future contributor reintroduces a hardcoded literal, the release
  gate catches it. Pre-1.3.2 our drift-catching only ran when the
  package was pip-installed; this one runs against the source tree.

- **README's stale `('1.1.3', '1.1.3')` literal example output**
  replaced with a bump-resistant equality check (`__version__ ==
  __version__` between the two packages, plus a comment pointing at
  `importlib.metadata`). The literal was already wrong by 1.1.4; the
  drift was invisible because no test scrutinised README contents.

## [1.3.1] — 2026-04-28

Two distribution improvements riding on one patch release. No API
or behavior change for users on supported platforms; this is purely
about widening the set of *installable* environments.

### Added

- **`py3-none-any` pure-Python wheel.** The chess-spectral release
  now ships a pure-Python wheel alongside the platform-specific
  wheels. This unblocks installation in environments that can't run
  our bundled `_native/spectral{.exe}` binaries:
  - **Pyodide / micropip** in browsers (mobile + desktop). The
    Pyodide runtime is single-process WASM with no `fork`/`exec`,
    so even a WASM build of our binaries couldn't be `subprocess`'d.
    The pure wheel uses the Python encoder paths exclusively —
    bit-for-bit equivalent to the C output (verified by
    `test_c_py_parity*`).
  - **Less-common platforms** where we don't ship a platform wheel
    (fresh Linux ARM, BSDs, etc.). pip falls through to the pure
    wheel after exhausting platform candidates.

  Per-release artifact count goes from 15 platform wheels + sdist
  (16) to 15 platform wheels + 1 pure wheel + sdist (17). Built via
  hatchling (a separate [`pyproject-pure.toml`](pyproject-pure.toml))
  because scikit-build-core's primary contract is platform wheels.
  See the new `build-pure-wheel` job in
  [`chess-spectral-publish.yml`](../../../.github/workflows/chess-spectral-publish.yml)
  for the build invocation. Verified locally: the pure wheel
  installs cleanly in a fresh venv; CLI commands work via Python
  fallback; `_find_c_binary()` correctly returns `None`; 4D phase
  ops + encoder produce expected outputs.

  **Performance note for pure-wheel users.** The Python encoder is
  ~30-60× slower than the C binary on most workloads. For Pyodide
  hover-renderer use cases (one preview encoding per hover, often
  with delta caching per
  [`bench_incremental_encoding.py`](research/bench_incremental_encoding.py)),
  this is well within interactive budget. For batch corpus encoding
  on a fresh ARM box, users will notice the slowdown; we recommend
  building from sdist (which the platform wheel pipeline does)
  instead.

- **Python 3.14 wheels.** The cibuildwheel matrix in
  [`.github/workflows/chess-spectral-publish.yml`](../../../.github/workflows/chess-spectral-publish.yml)
  was missing a cp314 entry — an oversight from the v1.2.4 publish-
  pipeline build-out (set up before 3.14 was released). Adding 314
  to the matrix grows the per-release platform-wheel count from 12
  to 15 (3 OS × 5 Python). The corresponding
  `Programming Language :: Python :: 3.14` classifier is added to
  `pyproject.toml` and `pyproject-pure.toml`.

## [1.3.0] — 2026-04-28

Adds the **chess4d-OC phase-operator move engine** — the 4D analogue
of the 2D `chess_spectral.phase_operators` package — validated
against [`python-chess4d-oana-chiru`](https://pypi.org/project/python-chess4d-oana-chiru/),
the Python reference implementation of Oana & Chiru (2026). Closes
the §11 phase-operator hypothesis arc on 4D: the φ_4d coprime
cyclic phase structure fully captures the Oana-Chiru piece geometry
on `Z_8^4`, both unobstructed and with occupancy.

Full design + experimental record:
[`docs/chess-maths/PHASE_OPERATOR_SUPPLEMENT_4D.md`](../../PHASE_OPERATOR_SUPPLEMENT_4D.md).

Minor version bump (not patch) because this adds a substantial new
public API surface (`chess_spectral.phase_operators_4d`).

### Added

- **`chess_spectral.phase_operators_4d` package** — 4D phase
  operators with the same shape as the 2D `phase_operators`
  package:
  - `MODULUS_4D = 145451`, `GEN_X = 9719`, `GEN_Y = 647`,
    `GEN_Z = 43`, `GEN_W = 3`, plus precomputed shift tuples
    and `phi4(x,y,z,w)`.
  - Piece operators: `P_rook4`, `P_bishop4`, `P_queen4`,
    `P_king4`, `P_knight4`, and pawn ops parameterized by
    `axis ∈ {'w', 'y'}` per O&C §3.10 Def 11.
  - `phase_to_coords_4d`: `PHI_TO_XYZW`, `XYZW_TO_PHI`,
    `invert(phi)`, `phase_set_to_board(phases)`.
  - `occupation_aware_moves_a_4d(state, origin, piece)` —
    Solution A: phase-op candidates ∩ chess4d oracle dests.
  - `phasecast_is_check_4d(state, color)` — pawn-aware reverse
    cast; non-pawn-only variant
    `phasecast_is_check_4d_no_pawns` retained for ablation.
  - `move_leaves_king_in_check_4d(state, move)` — pawn-aware
    move filter; non-pawn-only variant
    `move_leaves_king_in_check_4d_no_pawns` retained.

- **Pinned design** via mixed-radix tower with **ladder
  coefficient 14** (vs the 2D framework's effective 8). Phase B's
  structural gate caught a real failure at the original
  ladder-coefficient-7 attempt: the Phase A constraints (C1-C4)
  passed at `(M=12181, GEN=(1523,191,23,3))` but operator-shift
  differences span `[-14, 14]^4` and that wider box surfaced an
  integer dependency `g_y = 10·g_w + 7·g_z` (i.e.,
  `191 = 30 + 161`) that caused cross-piece destination aliasing.
  The new fifth constraint **C5: operator-aliasing freedom** is
  codified in
  [`tests/test_phase_4d_design.py::test_c5_no_integer_dependency_in_minus14_to_14_box`](tests/test_phase_4d_design.py)
  so this regression cannot recur silently. See
  [PHASE_OPERATOR_SUPPLEMENT_4D §13.1.4](../../PHASE_OPERATOR_SUPPLEMENT_4D.md)
  for the full story.

- **`research/chess4d_phase_design.py`** — design search +
  brute-force `[-14, 14]^4` dependency verifier. Ported from
  [`docs/othello-maths/research/coprime_generators.py`](../../../othello-maths/research/coprime_generators.py)
  and extended to 4 axes.

- **Test suites** (under `python/tests/`):
  - `test_phase_4d_design.py` — 15 tests: C1 coprime, C2 image
    bijection, C3 non-subgroup, C4 derived-gen distinctness,
    **C5 [-14,14]^4 integer-dep-freedom**, plus O&C-mobility
    cross-checks.
  - `test_phase_4d_unobstructed.py` — 24 tests including the
    Phase B structural gate at 4096 origins × 9 piece configs
    against `tables_4d.X_targets` (36,864 set-equality
    assertions).
  - `test_phase_4d_occupation_aware.py` — Phase C+E gate at
    44,803 (state, origin, piece) cases against the
    `python-chess4d-oana-chiru` oracle. ~3 minutes runtime.
  - `test_phase_4d_check_detection.py` — 232 tests covering both
    `_no_pawns` and pawn-aware variants, plus 7 hand-built
    targeted check constructions (rook on x-axis, knight (2,1)
    leap, bishop xy-diagonal, queen zw-diagonal, blocked rook,
    W-axis pawn check, Y-axis pawn check).

- **Cross-pollination from `docs/othello-maths/`**:
  - The *coprimality is necessary but not sufficient* discipline
    (Patch 2 of
    [`CHESS_NOTEBOOK_PHASE_1C_PATCHES.md`](../../../othello-maths/CHESS_NOTEBOOK_PHASE_1C_PATCHES.md))
    motivates Phase A's full image-bijection check.
  - The Z_2 channel framing for axis-tagged pieces (§3 Option B
    of [`OTHELLO_PHASE_OP_PREFLIGHT.md`](../../../othello-maths/OTHELLO_PHASE_OP_PREFLIGHT.md))
    aligns with the encoder's existing W/Y antisym pawn channel
    split. Phase E's pawn capture geometry (xw / xy plane) is
    the natural lift.

- **Immolation suite extensions** (`tests/test_smoke_e2e.py`):
  - `test_4d_phase_operators_smoke` — touch each P_X4 operator on
    a sample origin; assert O&C interior mobilities and
    rook ∪ bishop = queen.
  - `test_4d_phase_check_detection_smoke` — initial position has
    no check from either color, both `_no_pawns` and full paths.
  - `test_no_unwired_stubs_in_shipped_python_or_c` — meta-test
    walks the shipped sources and fails if any function still
    contains `cmd_todo("...")` (C) or `_not_implemented(...)`
    (Python) — the regression class that shipped 12 unwired CLI
    commands in v1.2.3.

### Changed

- **`safety_field.compute_safety_field` no longer accepts
  `include_pawns`**. The §9o safety-field hypothesis (ΔS tracks
  engine-Δeval) was tested in v1.0 and produced a null result
  (`ρ ≈ 0`) — see
  [`chess_spectral_research_notebook.md`](../../chess_spectral_research_notebook.md)
  §9o. The `include_pawns` parameter was originally added in
  v1.2.4 as a "future hook" for the symmetric-pawn-Laplacian
  extension (with `True` raising `NotImplementedError` to avoid
  the silent-discard mode it had in v1.2.3). With the parent
  hypothesis confirmed dead, reserving the hook adds maintenance
  cost without benefit; the parameter is removed. The default
  `include_pawns=False` math is preserved verbatim for §9o
  reproducibility. Closes v1.2.4 inventory item #14 with a
  documented "rejected — failed exploration" outcome rather than
  a deferred wiring.

- **`pyproject.toml::[project.optional-dependencies] test`** adds
  `python-chess4d-oana-chiru>=0.3.3` so the Phase C/D gates can
  import the oracle. *Not* in main `dependencies` (would create
  a circular install — `python-chess4d-oana-chiru[spectral]`
  already depends on `chess-spectral`). The phase operator
  package itself is pure-stdlib for unobstructed reach;
  `chess4d` is imported lazily inside Solution A and the
  reverse-cast functions, so the package still works without the
  test extra installed.

### Documentation

- **New: `docs/chess-maths/PHASE_OPERATOR_SUPPLEMENT_4D.md`** —
  occupies the §13 slot in the 4D notebook, mirrors the 2D
  supplement's structure (§13.1 design / §13.2 ops / §13.3
  empty-board gate / §13.4 occupation-aware / §13.5 check
  detection / §13.6 pawn axis / §13.7 transfer summary / §13.8
  cross-pollination credits).
- **`docs/chess-maths/chess_spectral_4d_notebook.md`** appends a
  high-level "Phase operators (v1.2)" pointer to the new
  supplement.
- **`docs/othello-maths/CHESS_NOTEBOOK_PHASE_1C_PATCHES.md`**
  status header updated to **FULLY APPLIED** with citations. A
  PR-closure audit confirmed all six patches were already present
  in [`chess_spectral_research_notebook.md`](../../chess_spectral_research_notebook.md)
  (Patches 1-5 at the documented section locations; Patch 6's D₄
  character-table audit was applied with the corrected B₁ / B₂
  rows in [`chess_d4_direct.py`](../../chess_d4_direct.py) and
  [`chess_spectral/tables.py`](chess_spectral/tables.py)). A
  programmatic class-constancy verifier reproducing the audit was
  run and reported PASS for all five irrep rows. The Othello
  orphan-data loop is closed; no follow-up PR needed.

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
