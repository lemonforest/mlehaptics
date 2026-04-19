#!/usr/bin/env python3
"""Emit the 4D encoder parity fixture pack (v1.1.1).

Writes:
  python/tests/fixtures/positions_4d.jsonl
      One JSON record per line:
        {"name": "<fixture>", "pieces": {"<square>": "<val>", ...}}
      Pawn values are 2-char ("Pw", "Py", "pw", "py" -- color + axis);
      non-pawn values remain single-char. Parsers branch on len(value).
  python/tests/fixtures/fixtures_4d.npz
      names         : (N,) object array of fixture names
      encodings     : (N, 45056) float32, expected `encode_4d(pos)` output
                      (v1.1.1: 11 channels, FA_PAWN split into W/Y)
      pos_counts    : (N,) int32, number of occupied squares
      channel_starts: (12,) int32, start offsets of the 11 channels (last
                      entry is ENCODING_DIM_4D for easy [start:end] slicing)
      channel_names : (11,) object array of channel names

The pack is consumed by `python/tests/test_c_py_parity_4d.py` (P2b+) which
encodes each fixture with the C binary and asserts max |C - expected| < 1e-10.
"""
from __future__ import annotations

import json
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, '..'))
PY_DIR = os.path.abspath(os.path.join(REPO, 'python'))
FIX_DIR = os.path.join(PY_DIR, 'tests', 'fixtures')

sys.path.insert(0, PY_DIR)
from chess_spectral import encoder_4d as enc4     # noqa: E402
from chess_spectral import tables_4d as t4        # noqa: E402

sq4 = t4.sq4

# v1.1.1 position values: pawns are tuples ('P'|'p', 'y'|'w'); non-pawns
# remain single-char strings. We still write JSONL as strings -- pawns
# collapse to a 2-char "Pw"/"Py"/"pw"/"py" form so the C parser can
# branch on len(value).
PieceVal = str | tuple[str, str]


def _jsonl_value(val: PieceVal) -> str:
    """Serialize a position value to the JSONL 2-char-for-pawns convention."""
    if isinstance(val, tuple):
        color, axis = val
        assert color in ('P', 'p')
        assert axis in ('y', 'w')
        return color + axis
    return val


# ─── Helpers for building positions ─────────────────────────────────────────

def _apply_b4_to_position(g: t4.GroupElem,
                          pos: dict[int, PieceVal]) -> dict[int, PieceVal]:
    """Apply a B_4 group element (signed permutation) to every square in a
    position. Pawn axis tuples are preserved verbatim (axis is defined in
    lattice-coord space; Y<->W exchange is a *separate* symmetry that we
    don't apply here). Used for the `*_rotated` fixtures that exercise A_1
    orbit averaging invariance downstream."""
    out: dict[int, PieceVal] = {}
    for s, val in pos.items():
        x, y, z, w = t4.rc4(s)
        nx, ny, nz, nw = t4._apply_b4_to_square(g, x, y, z, w)
        out[sq4(nx, ny, nz, nw)] = val
    return out


# ─── Fixture set (12 canonical positions) ───────────────────────────────────

def _fixtures() -> list[tuple[str, dict[int, PieceVal]]]:
    fixtures: list[tuple[str, dict[int, PieceVal]]] = []

    # 1. Empty — all channels zero (sanity + zero-init regression guard).
    fixtures.append(("empty", {}))

    # 2. Single W-axis white pawn near w=0 — isolated FA_PAWN_W write,
    #    8 modes; FA_PAWN_Y stays at zero.
    fixtures.append(("single_pawn_white", {sq4(3, 3, 3, 0): ('P', 'w')}))

    # 3. Single W-axis black pawn near w=7 — opposite-sign FA_PAWN_W
    #    contribution; FA_PAWN_Y stays at zero.
    fixtures.append(("single_pawn_black", {sq4(3, 3, 3, 7): ('p', 'w')}))

    # 4. Single knight at deep interior — exercises channels 5-7 (knight
    #    contributes one of the three cross-piece SVD directions).
    fixtures.append(("single_knight", {sq4(3, 3, 3, 3): 'N'}))

    # 5. Single bishop at (0,0,0,0) — even-parity cell; bishop graph has 2
    #    connected components, so this pins us to one component.
    fixtures.append(("single_bishop_even", {sq4(0, 0, 0, 0): 'B'}))

    # 6. Single rook at centre — rook diag-dev (FD_DIAG) witness: rook
    #    Laplacian does not commute with grid, so DIAG_DEV[3] is nonzero.
    fixtures.append(("single_rook_center", {sq4(3, 3, 3, 3): 'R'}))

    # 7. Single queen — rook + bishop disjoint union (cross-check).
    fixtures.append(("single_queen", {sq4(4, 4, 4, 4): 'Q'}))

    # 8. Single king — channel 5-7 king contribution + tiny diag-dev.
    fixtures.append(("single_king", {sq4(3, 3, 3, 3): 'K'}))

    # 9. Pawn pair on the same w-column — additivity check for FA_PAWN_W.
    fixtures.append((
        "pawn_pair_w_axis",
        {sq4(2, 2, 2, 1): ('P', 'w'), sq4(2, 2, 2, 6): ('p', 'w')},
    ))

    # 10. Four rooks at B_4-symmetric corners — tests A_1 orbit averaging
    #     with multi-piece mass in one orbit.
    fixtures.append((
        "four_rooks_corners",
        {
            sq4(0, 0, 0, 0): 'R',
            sq4(7, 0, 0, 0): 'R',
            sq4(0, 7, 0, 0): 'R',
            sq4(7, 7, 0, 0): 'R',
        },
    ))

    # 11. Mixed-signal "starting-like": 1 king + 1 queen + 2 rooks + 2 knights
    #     + 2 bishops + 4 pawns spread across colors, plus a black king.
    #     All pawns W-axis (v1.0-compatible layout).
    fixtures.append((
        "starting_like_mini",
        {
            sq4(0, 0, 0, 0): 'R',
            sq4(0, 7, 0, 0): 'R',
            sq4(0, 3, 0, 0): 'K',
            sq4(0, 4, 0, 0): 'Q',
            sq4(0, 2, 0, 0): 'B',
            sq4(0, 5, 0, 0): 'B',
            sq4(0, 1, 0, 0): 'N',
            sq4(0, 6, 0, 0): 'N',
            sq4(1, 0, 0, 0): ('P', 'w'),
            sq4(1, 3, 0, 0): ('P', 'w'),
            sq4(6, 3, 0, 7): ('p', 'w'),
            sq4(7, 3, 0, 7): 'k',
        },
    ))

    # 12. Starting-like rotated by a B_4 element (axis-permutation + sign
    #     flip). Exercises the same signal content under a nontrivial
    #     lattice reshuffle; C and Python must agree to 1e-10.
    #     Element: permute (x,y,z,w) -> (w,x,y,z) with no sign flip.
    g_rot = ((3, 0, 1, 2), (1, 1, 1, 1))
    start_pos = dict(fixtures[-1][1])
    fixtures.append(("starting_like_rotated", _apply_b4_to_position(g_rot, start_pos)))

    # ── v1.1.1 Y-axis fixtures (≥2 Y-only + ≥1 mixed per plan) ──────────

    # 13. Single Y-axis white pawn near y=0 — isolated FA_PAWN_Y write;
    #     FA_PAWN_W stays at zero. Parity-twin of fixture #2.
    fixtures.append(("single_pawn_white_y", {sq4(3, 0, 3, 3): ('P', 'y')}))

    # 14. Y-axis pawn pair on the same y-column — additivity check for
    #     FA_PAWN_Y. Analogue of fixture #9 on the y-leg.
    fixtures.append((
        "pawn_pair_y_axis",
        {sq4(2, 1, 2, 2): ('P', 'y'), sq4(2, 6, 2, 2): ('p', 'y')},
    ))

    # 15. Mixed W + Y pawn fixture — exercises both FA_PAWN_W and
    #     FA_PAWN_Y simultaneously with non-trivial energy in each slab.
    #     No non-pawn pieces, so the split is unambiguous.
    fixtures.append((
        "pawn_mixed_axes",
        {
            sq4(1, 1, 1, 0): ('P', 'w'),  # W-axis
            sq4(1, 1, 1, 7): ('p', 'w'),
            sq4(5, 0, 5, 5): ('P', 'y'),  # Y-axis
            sq4(5, 7, 5, 5): ('p', 'y'),
        },
    ))

    return fixtures


# ─── Emission ───────────────────────────────────────────────────────────────

def main() -> None:
    os.makedirs(FIX_DIR, exist_ok=True)

    fixtures = _fixtures()
    names = [name for name, _ in fixtures]
    assert len(names) == len(set(names)), "duplicate fixture names"
    # v1.1.1 grew to 15 (12 legacy + 3 Y-axis coverage fixtures).
    assert 12 <= len(fixtures) <= 20, (
        f"v1.1.1 expects 12-20 fixtures; got {len(fixtures)}"
    )

    # JSONL — square indices as strings (JSON doesn't allow int keys).
    # Pawn values are 2-char (color + axis); non-pawns stay single-char.
    jsonl_path = os.path.join(FIX_DIR, 'positions_4d.jsonl')
    with open(jsonl_path, 'w', encoding='utf-8') as f:
        for name, pos in fixtures:
            record = {
                "name": name,
                "pieces": {
                    str(int(s)): _jsonl_value(val)
                    for s, val in sorted(pos.items())
                },
            }
            f.write(json.dumps(record, ensure_ascii=True) + "\n")
    print(f"Wrote {jsonl_path}  ({len(fixtures)} fixtures)")

    # Encode each fixture through the Python reference.
    print("Encoding fixtures through Python reference "
          "(first call builds 128 MB U tensor; subsequent calls are cached) ...",
          flush=True)
    n = len(fixtures)
    encodings = np.zeros((n, enc4.ENCODING_DIM_4D), dtype=np.float32)
    for i, (name, pos) in enumerate(fixtures):
        encodings[i] = enc4.encode_4d(pos)
        energies = enc4.channel_energies_4d(encodings[i])
        active = [ch for ch, e in energies.items() if e > 0.0]
        print(f"  [{i:2d}] {name:<24s} {len(pos):3d} pieces, "
              f"active channels: {active}")

    pos_counts = np.array([len(p) for _, p in fixtures], dtype=np.int32)
    channel_starts = np.array(
        [start for _, start in enc4.CHANNELS_4D] + [enc4.ENCODING_DIM_4D],
        dtype=np.int32,
    )
    channel_names = np.array([n for n, _ in enc4.CHANNELS_4D], dtype=object)

    npz_path = os.path.join(FIX_DIR, 'fixtures_4d.npz')
    np.savez_compressed(
        npz_path,
        names=np.array(names, dtype=object),
        encodings=encodings,
        pos_counts=pos_counts,
        channel_starts=channel_starts,
        channel_names=channel_names,
    )
    sz = os.path.getsize(npz_path)
    print(f"Wrote {npz_path}  ({sz:,} bytes, {sz / 1024 / 1024:.2f} MB)")

    # Sanity: empty fixture must be all-zero.
    empty_idx = names.index("empty")
    assert float(np.abs(encodings[empty_idx]).max()) == 0.0, \
        "empty fixture is not all-zero"

    # single_pawn_white (W-axis): FA_PAWN_W (slot 8) nonzero, FA_PAWN_Y
    # (slot 9) must be exactly zero -- pins the per-axis split.
    pw_idx = names.index("single_pawn_white")
    pw_enc = encodings[pw_idx]
    pw_fa_w = pw_enc[8 * t4.N_SQUARES:9 * t4.N_SQUARES]
    pw_fa_y = pw_enc[9 * t4.N_SQUARES:10 * t4.N_SQUARES]
    assert float(np.abs(pw_fa_w).max()) > 0.0, \
        "single_pawn_white: FA_PAWN_W (slot 8) must be nonzero"
    assert float(np.abs(pw_fa_y).max()) == 0.0, \
        "single_pawn_white: FA_PAWN_Y (slot 9) must be exactly zero"

    # single_pawn_white_y (Y-axis): the mirror check -- FA_PAWN_Y nonzero,
    # FA_PAWN_W exactly zero. This is the v1.1.1 feasibility signal.
    py_idx = names.index("single_pawn_white_y")
    py_enc = encodings[py_idx]
    py_fa_w = py_enc[8 * t4.N_SQUARES:9 * t4.N_SQUARES]
    py_fa_y = py_enc[9 * t4.N_SQUARES:10 * t4.N_SQUARES]
    assert float(np.abs(py_fa_y).max()) > 0.0, \
        "single_pawn_white_y: FA_PAWN_Y (slot 9) must be nonzero"
    assert float(np.abs(py_fa_w).max()) == 0.0, \
        "single_pawn_white_y: FA_PAWN_W (slot 8) must be exactly zero"

    # pawn_mixed_axes: both pawn channels must carry energy simultaneously.
    mix_idx = names.index("pawn_mixed_axes")
    mix_enc = encodings[mix_idx]
    mix_fa_w = mix_enc[8 * t4.N_SQUARES:9 * t4.N_SQUARES]
    mix_fa_y = mix_enc[9 * t4.N_SQUARES:10 * t4.N_SQUARES]
    assert float(np.abs(mix_fa_w).max()) > 0.0, \
        "pawn_mixed_axes: FA_PAWN_W must be nonzero"
    assert float(np.abs(mix_fa_y).max()) > 0.0, \
        "pawn_mixed_axes: FA_PAWN_Y must be nonzero"

    print()
    print("All fixtures emitted and spot-checks passed.")


if __name__ == '__main__':
    main()
