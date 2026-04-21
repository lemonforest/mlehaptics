# Claude Code: Phase-Operator Move Engine Build

## Context

Two documents are the ground truth for this task:

1. `docs/chess-maths/PHASE_OPERATOR_SUPPLEMENT.md` — the experimental specification (§11.1 through §11.9). Read it end to end before touching code.
2. `docs/chess-maths/chess_spectral_research_notebook.md` — the surrounding research context. Read §9a (640-dim architecture), §9f (coprime roll binding, currently stated mod 512), and §9r (polarization reframing) specifically.

A preflight math check was already run by a separate Claude instance. Key findings:

- **§11.3 Experiment 1 passes at 100.00%** against python-chess across all 416 (polarization, origin) pairs when implemented as specified. The phase-operator spec is arithmetically correct.
- Zero torus-wrap aliases occur under any piece operator at any origin for any k in the specified range. The "torus clip" boundary-handling claim in §11.3.3 is a theorem at this problem size, not an approximation.
- Four documentation issues exist in the supplement and need fixing before code is written. They are specified as unified diff patches below.

This prompt has two phases. **Phase 1 is document patches. Phase 2 is code.** Do Phase 1 first, in full, and commit it as its own change before starting Phase 2. Do not interleave.

---

## Phase 1 — Supplement documentation patches

Apply the four patches below to `docs/chess-maths/PHASE_OPERATOR_SUPPLEMENT.md`. Each patch has:

- A **PATCH HEADER** naming the fix and rationale.
- An **OLD** block showing the exact text to match (preserve existing whitespace, including the `\r\n` line endings already in the file).
- A **NEW** block showing the replacement text.

After applying all four patches, re-verify by grepping the supplement for the key strings from each NEW block. Do not change section numbering or anchors — downstream references (§11.3.3, §11.6.1, etc.) must continue to resolve.

### PATCH 1 — §11.2.1 clarify mod 640 vs §9f mod 512

**Rationale:** §9f in the research notebook defines the roll binding as `row * 67 + col * 7 mod 512` (512-dim encoder, 512 = 2⁹). §11 uses mod 640 (640-dim production encoder, 640 = 2⁷ × 5). Both are mathematically valid — both are injective on 8×8, both have zero aliases under piece operators — but they are different moduli. The current text implies they are the same. Explicit reconciliation needed.

OLD:
```
### §11.2.1 Coordinate conventions

Row index r ∈ {0, 1, …, 7}. Column index c ∈ {0, 1, …, 7}. The origin phase tuple for lattice node (r, c) is:

φ(r, c) = (r × 67 + c × 7) mod 640

This matches the coprime roll binding from §9f. The phase tuple is a single integer in [0, 640), but it carries two components: r × 67 mod 640 (row phase) and c × 7 mod 640 (column phase), which are individually recoverable because 67 and 7 are coprime to 640 (640 = 2⁷ × 5; 67 is prime and not 2 or 5; 7 is prime and not 2 or 5).
```

NEW:
```
### §11.2.1 Coordinate conventions

Row index r ∈ {0, 1, …, 7}. Column index c ∈ {0, 1, …, 7}. The origin phase tuple for lattice node (r, c) is:

φ(r, c) = (r × 67 + c × 7) mod 640

This extends §9f's coprime roll binding from the historical 512-dim encoder (mod 512) to the production 640-dim encoder (mod 640). Both moduli admit the same generators 67 and 7: gcd(67, 512) = gcd(67, 640) = gcd(7, 512) = gcd(7, 640) = 1. The 64-point image of Z₈ × Z₈ under φ is verified distinct (no collisions) for both moduli. §11 operates at mod 640 throughout; any reference to §9f's mod 512 formulation should be read as the antecedent of this extended form.

The phase tuple is a single integer in [0, 640), but it carries two components: r × 67 mod 640 (row phase) and c × 7 mod 640 (column phase), which are individually recoverable because 67 and 7 are coprime to 640 (640 = 2⁷ × 5; 67 is prime and not 2 or 5; 7 is prime and not 2 or 5).

**Subgroup structure.** The image set {φ(r, c) : (r, c) ∈ [0, 7]²} is *not* a subgroup of Z₆₄₀ — closure fails (e.g., 384 + 384 = 128 mod 640, which is not in the image). This is the correct structure for the problem: phase-op shifts that carry an origin off the lattice land in the off-image complement of Z₆₄₀, where §11.3.2 inversion fails, and §11.3.3 pruning catches them. A subgroup image would close under piece-operator addition and eliminate the boundary-detection mechanism.
```

### PATCH 2 — §11.2.6 knight angle note

**Rationale:** The header says "θ = arctan(1/2) ≈ 26.57°" as if the knight has one angle. It has 8, one per D4 orbit element of (1, 2). §9r already uses the correct "knight-offset θ class" language. Lift it.

OLD:
```
### §11.2.6 Phase operator for the knight (tunneling, θ = arctan(1/2) ≈ 26.57°, T-symmetric)

The knight tunnels to a discrete shell at the phase-shifted angle. The 8 knight destinations correspond to 8 distinct linear combinations of the row and column generators:
```

NEW:
```
### §11.2.6 Phase operator for the knight (tunneling, knight-offset θ class, T-symmetric)

The knight occupies its own θ class in the §9r polarization framework — disjoint from {axial, diagonal}. Its 8 destinations are the D4 orbit of (1, 2), with angles {26.57°, 63.43°, 116.57°, 153.43°, 206.57°, 243.43°, 296.57°, 333.43°} (arctan(1/2) is one representative, not the full class). The 8 destinations correspond to 8 distinct linear combinations of the row and column generators:
```

### PATCH 3 — §11.2.7 explicit empty-board comparison rule

**Rationale:** python-chess does not report pawn captures as legal on an empty board (no target piece), so §11.3 comparison breaks if the phase-op set includes capture destinations. The preflight handled this by excluding captures from the empty-board comparison. Make the rule explicit in the spec.

OLD:
```
### §11.2.7 Phase operator for the pawn (massive, forward-only, T-violating, Z₂-charge-dependent)

The pawn operator depends on Z₂ charge. For white (charge +V):

**P_pawn_white(φ_origin, move_type)** = 
- if move_type = advance and on starting rank: {φ_origin + 67, φ_origin + 2×67} mod 640
- if move_type = advance: {φ_origin + 67} mod 640
- if move_type = capture: {φ_origin + 67 + 7, φ_origin + 67 − 7} mod 640

For black (charge −V): replace +67 with −67 throughout.

The T-violation is explicit: there is no inverse operator. The phase operator is non-Hermitian, consistent with §9m's identification of the pawn's antisymmetric fiber.
```

NEW:
```
### §11.2.7 Phase operator for the pawn (massive, forward-only, T-violating, Z₂-charge-dependent)

The pawn operator depends on Z₂ charge. For white (charge +V):

**P_pawn_white(φ_origin, move_type)** = 
- if move_type = advance and on starting rank: {φ_origin + 67, φ_origin + 2×67} mod 640
- if move_type = advance: {φ_origin + 67} mod 640
- if move_type = capture: {φ_origin + 67 + 7, φ_origin + 67 − 7} mod 640

For black (charge −V): replace +67 with −67 throughout.

The T-violation is explicit: there is no inverse operator. The phase operator is non-Hermitian, consistent with §9m's identification of the pawn's antisymmetric fiber.

**Empty-board comparison caveat (§11.3).** python-chess does not report diagonal captures as legal moves when no enemy piece occupies the target square. The §11.3 equivalence check against python-chess therefore compares *advance* destinations only; capture destinations are validated in §11.4 (occupation-aware) where enemy pieces are present on the board. This is a quirk of the reference implementation, not of the phase operator — the capture phases are arithmetically correct, they just lack validation targets on an empty board.
```

### PATCH 4 — §11.6.1 rename CRT framing to be mathematically honest

**Rationale:** UTLP S4's CRT aliasing horizon is the literal Chinese Remainder Theorem operating on coprime temporal moduli. §11.6's "CRT cell" language applies the same word to similarity-below-threshold in a bundled HDC superposition — a high-dimensional noise-floor crossing, not a CRT recovery event. The analogy is suggestive but overclaimed. Reword to "spatial similarity horizon" and note the analytical tool that would make it rigorous.

OLD:
```
### §11.6.1 The UTLP S4 mechanism, applied spatially

In UTLP S4, partition detection uses HD vector similarity between nodes. When similarity drops below threshold, the nodes have drifted beyond the CRT aliasing horizon and phase-lock fallback becomes necessary.

Spatial analog: consider two positions P₁ and P₂. Compute similarity(enc_640(P₁), enc_640(P₂)). If the positions are close in phase space (high similarity), they are in the same "CRT cell" — field-theoretically similar and expected to have similar thermodynamic gradients. If similarity drops below threshold, the positions are in different CRT cells — the phase representation cannot reliably extrapolate between them.

This gives a partition detector for phase space. Positions within the same partition should have consistent local gradients. Positions across a partition boundary should have discontinuous gradients.
```

NEW:
```
### §11.6.1 The UTLP S4 mechanism, applied spatially

In UTLP S4, partition detection uses HD vector similarity between nodes. When similarity drops below threshold, the nodes have drifted beyond the CRT aliasing horizon and phase-lock fallback becomes necessary. S4's "CRT aliasing horizon" is the literal Chinese Remainder Theorem — coprime temporal moduli lose unambiguous recovery past a specific range.

Spatial analog (as framework, not theorem): consider two positions P₁ and P₂. Compute similarity(enc_640(P₁), enc_640(P₂)). If the positions are close in phase space (high similarity), they are in the same *similarity cell* — field-theoretically similar and expected to have similar thermodynamic gradients. If similarity drops below threshold, the positions are in different similarity cells — the phase representation cannot reliably extrapolate between them.

This gives a partition detector for phase space. Positions within the same partition should have consistent local gradients. Positions across a partition boundary should have discontinuous gradients.

**Mathematical honesty caveat.** The enc_640 vector is a bundled HDC superposition of piece states, not a literal coprime-residue encoding of position. A similarity drop is a high-dimensional noise-floor crossing in that bundled representation, not a CRT-recovery ambiguity event. The "similarity cell" framing is metaphorically useful and S4-analogous, but claiming CRT-specific partition-detection guarantees requires either (a) a proof that the bundled HDC similarity structure factorizes into per-axis aliasing kernels — the Vector Function Architecture product-kernel result from Frady et al. 2022 (arXiv:2109.03429) and the Residue HDC kernel theorem from Kymn et al. 2024 (arXiv:2311.04872) are the relevant tools, or (b) reframing §11.6 as an empirical partition-detection experiment with no appeal to CRT guarantees. This supplement takes path (b) for the experimental phase and flags (a) as a downstream analytical task.
```

### Phase 1 verification

After applying all four patches, run these greps from `docs/chess-maths/`:

```bash
grep -c "Subgroup structure" PHASE_OPERATOR_SUPPLEMENT.md      # expect 1
grep -c "knight-offset θ class" PHASE_OPERATOR_SUPPLEMENT.md   # expect 1
grep -c "Empty-board comparison caveat" PHASE_OPERATOR_SUPPLEMENT.md  # expect 1
grep -c "Mathematical honesty caveat" PHASE_OPERATOR_SUPPLEMENT.md    # expect 1
```

All four should return 1. If any return 0, the patch did not apply — do not proceed to Phase 2.

Commit Phase 1 with message: `§11 supplement: reconcile mod 512/640, tighten knight/pawn/CRT language per preflight`

---

## Phase 2 — Code build

**Scope:** §11.7.1 items 1–3 (`phase_operators.py`, `phase_to_coords.py`, `equivalence_check.py`). Stop there. Do not build §11.4 / §11.5 / §11.6 infrastructure yet — §11.3 must pass end to end on our actual code before the occupation, similarity, and partition experiments get wired up. Each of those downstream files depends on §11.3 being green.

### Directory layout

All code goes under `docs/chess-maths/phase_operators/`. Create the directory. Use this layout:

```
docs/chess-maths/phase_operators/
├── __init__.py
├── phase_operators.py     # §11.2 operators as pure arithmetic on Z_640
├── phase_to_coords.py     # §11.3.2 inversion table + §11.3.3 boundary clip
├── equivalence_check.py   # §11.3 experimental protocol; CLI entrypoint
├── README.md              # minimal — points at supplement §11
└── tests/
    ├── __init__.py
    └── test_phase_operators.py  # unit tests for the operator specs
```

### File-level specifications

#### `phase_operators.py`

Pure-arithmetic operator functions. No numpy, no python-chess, no dependencies beyond stdlib. The module must be importable in under 50ms.

Required symbols:

```python
ROW_GEN = 67
COL_GEN = 7
MODULUS = 640

DIAG_NE_SW_GEN = 74   # 67 + 7
DIAG_NW_SE_GEN = 60   # 67 - 7

KNIGHT_SHIFTS = (141, 127, 81, 53, -141, -127, -81, -53)
KING_SHIFTS = (67, 7, 74, 60, -67, -7, -74, -60)

def phi(r: int, c: int) -> int: ...
def P_rook(origin_phi: int) -> frozenset[int]: ...
def P_bishop(origin_phi: int) -> frozenset[int]: ...
def P_queen(origin_phi: int) -> frozenset[int]: ...
def P_king(origin_phi: int) -> frozenset[int]: ...
def P_knight(origin_phi: int) -> frozenset[int]: ...
def P_pawn_white(origin_phi: int, *, on_starting_rank: bool, include_captures: bool) -> frozenset[int]: ...
def P_pawn_black(origin_phi: int, *, on_starting_rank: bool, include_captures: bool) -> frozenset[int]: ...
```

Implementation notes:

- Each `P_*` function returns a `frozenset[int]` of phase values in [0, 640). Do not include the origin phase itself.
- Use plain integer arithmetic: `(origin_phi + k * ROW_GEN) % MODULUS`. No numpy.
- Rook, bishop, queen iterate k ∈ {±1, …, ±7} per §11.2.2 / §11.2.3 / §11.2.4.
- Pawn `include_captures=False` is the §11.3 mode per PATCH 3. `include_captures=True` is the full operator for §11.4.
- Do not accept `move_type` string arguments — the split advance/capture into separate helpers inside the function and union them based on `include_captures` is cleaner.

Constants must be module-level and typed as shown. Do not recompute the knight offsets at call time.

#### `phase_to_coords.py`

Inversion table from phase to `(row, col)` and back.

Required symbols:

```python
PHI_TO_RC: dict[int, tuple[int, int]]  # 64-entry lookup; frozen at import
RC_TO_PHI: dict[tuple[int, int], int]  # 64-entry lookup; frozen at import

def invert(phase: int) -> tuple[int, int] | None:
    """Return (row, col) if phase is on the board image, else None.
    §11.3.2 + §11.3.3 combined: inversion with built-in boundary clip."""

def phase_set_to_board(phase_set: frozenset[int]) -> frozenset[tuple[int, int]]:
    """Vectorize invert() over a phase-op output set. Drops off-image phases."""
```

Implementation notes:

- Build `PHI_TO_RC` once at module load from `phase_operators.phi`. Do not recompute per call.
- `invert()` is a `dict.get(phase % MODULUS)` — one dict lookup, no search loop, no numpy.
- `phase_set_to_board` must return a `frozenset[tuple[int, int]]`, not a list or set, for downstream set-equality semantics in `equivalence_check.py`.

#### `equivalence_check.py`

The §11.3 experiment as a runnable CLI. Depends on python-chess.

Required shape:

```python
"""§11.3 Experiment 1: Equivalence on Empty Board.

Compares phase-operator reachable sets against python-chess legal moves
on empty-board-with-one-piece positions. Writes CSV per §11.3.5 schema.
"""
import argparse
import csv
import sys
from pathlib import Path

import chess

from phase_operators import (
    phi, P_rook, P_bishop, P_queen, P_king, P_knight,
    P_pawn_white, P_pawn_black,
)
from phase_to_coords import phase_set_to_board


def legal_dests_for(piece_char: str, r: int, c: int,
                    color: chess.Color = chess.WHITE) -> frozenset[tuple[int, int]]:
    """Empty-board-with-one-piece python-chess reference set.
    (r, c) is (rank, file) in our convention; matches chess.square(c, r)."""
    ...

def run_experiment_1() -> list[dict]:
    """Yield one row per (polarization, origin) pair per §11.3.5.
    Columns: polarization, origin_row, origin_col, phase_op_destinations,
             geometric_destinations, set_equal, missing, extra."""
    ...

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path,
                        default=Path("results/phase_operator_experiments/exp1_equivalence.csv"),
                        help="Output CSV path (parents created).")
    parser.add_argument("--fail-on-mismatch", action="store_true",
                        help="Exit nonzero if any (polarization, origin) mismatches.")
    args = parser.parse_args()
    ...
```

Implementation notes:

- **Coordinate convention:** our `(r, c)` = `(rank, file)` in python-chess's sense. `chess.square(c, r)` builds the correct 0..63 index.
- **Pawn coverage:** iterate r ∈ [1, 6] for both colors (pawns cannot sit on back ranks); white starts on r=1, black on r=6. Call pawn operators with `include_captures=False` per PATCH 3.
- **Piece enumeration order** for the CSV: `["N", "B", "R", "Q", "K", "P_white", "P_black"]`. Column `polarization` takes those exact string values.
- **CSV serialization:** `missing` and `extra` columns serialize set contents as `"(r,c);(r,c)"` or empty string. `phase_op_destinations` and `geometric_destinations` likewise. `set_equal` is "true"/"false" lowercase.
- **Output directory:** defaults to `docs/chess-maths/results/phase_operator_experiments/exp1_equivalence.csv`. Create parents with `mkdir(parents=True, exist_ok=True)`.
- **Exit code:** 0 on success; if `--fail-on-mismatch` is set and any row has `set_equal=false`, exit 1 with a summary on stderr. Default mode (no flag) always exits 0 — this is a data-collection tool, not a test.
- Print one summary line to stdout at the end: `"§11.3 complete: {matches}/{total} pairs equivalent"`.

#### `tests/test_phase_operators.py`

Unit tests for the operator specs. Runs without python-chess.

Required coverage:

1. **Generator coprimality:** `gcd(67, 640) == 1`, `gcd(7, 640) == 1`, `gcd(67, 7) == 1`.
2. **φ injectivity:** the set `{phi(r, c) for all (r, c) in [0,7]²}` has exactly 64 elements.
3. **Supplement worked example (§11.3.3):**
   - `(phi(0, 0) + 7 * 67) % 640 == 469` and inverts to `(7, 0)`.
   - `(phi(7, 0) + 67) % 640 == 536` and inverts to `None`.
4. **Knight shift values:** `KNIGHT_SHIFTS` decodes to `{±141, ±127, ±81, ±53}`.
5. **King shift values:** `KING_SHIFTS` decodes to `{±67, ±7, ±74, ±60}`.
6. **Operator-size bounds** (from interior squares):
   - Rook from (4, 4): `len(P_rook(phi(4, 4))) == 14`.
   - Bishop from (4, 4): `len(P_bishop(phi(4, 4))) == 14`.
   - Queen from (4, 4): `len(P_queen(phi(4, 4))) == 28`.
   - King from (4, 4): `len(P_king(phi(4, 4))) == 8`.
   - Knight from (4, 4): `len(P_knight(phi(4, 4))) == 8`.

Use `unittest`. No pytest dependency. `python -m unittest discover` must pass from the `phase_operators/` directory.

### Phase 2 running order

1. `phase_operators.py` + unit tests; confirm tests pass.
2. `phase_to_coords.py`; extend tests to cover `invert()` behavior on the §11.3.3 worked example.
3. `equivalence_check.py`; run it.
4. Inspect the CSV output. Expected: 416 rows, all `set_equal=true`. Expected summary line: `"§11.3 complete: 416/416 pairs equivalent"`.
5. If any mismatches appear, **stop and report them** — per §11.7.4, do not tune the operator definitions to match geometric results. The preflight already proved the operators correct; any mismatch in your run is a bug in the implementation, not in the spec.

Commit Phase 2 with message: `§11.3 phase-operator equivalence: 416/416 pass`

---

## Scope guard

Explicitly do not do any of the following in this task:

- Do not start §11.4 (occupation-aware) or §11.5 / §11.6 scaffolding.
- Do not modify `chess-spectral/python/chess_spectral/encoder.py` or `tables.py`.
- Do not touch `encoder_512.py` or `encoder_v3.py`.
- Do not add a phase operator for fairy pieces, L-pieces, or any non-standard polarization. §11.2 defines the seven and only the seven that §11.3 validates.
- Do not optimize for runtime. The whole experiment runs in under a second; readability and correspondence with the supplement specification matter more than speed.
- Do not produce visualizations or dashboards. CSV + stdout summary only, per §11.7.4.
- Do not silently paper over a mismatch. If §11.3 reports <416/416, the default behavior is to record the failure and surface it, not to patch the operators.

## Success criteria

Phase 1: four patches applied, four grep checks return 1, commit landed.

Phase 2: three modules + test file created, all unit tests pass, `equivalence_check.py` runs to completion, CSV exists at the default path, stdout summary reads `§11.3 complete: 416/416 pairs equivalent`, commit landed.

If both phases succeed, the §11.4 occupation-aware build is unblocked. Do not start it in the same session — return to the researcher for the next prompt.
