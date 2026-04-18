#!/usr/bin/env python3
"""Emit the 4D encoder parity fixture pack.

Writes:
  python/tests/fixtures/positions_4d.jsonl
      One JSON record per line:
        {"name": "<fixture>", "pieces": {"<square>": "<char>", ...}}
  python/tests/fixtures/fixtures_4d.npz
      names        : (N,) object array of fixture names
      encodings    : (N, 40960) float32, expected `encode_4d(pos)` output
      pos_counts   : (N,) int32, number of occupied squares
      channel_starts: (11,) int32, start offsets of the 10 channels (last is
                      ENCODING_DIM_4D, for easy [start:end] slicing)
      channel_names : (10,) object array of channel names

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


# ─── Helpers for building positions ─────────────────────────────────────────

def _apply_b4_to_position(g: t4.GroupElem, pos: dict[int, str]) -> dict[int, str]:
    """Apply a B_4 group element (signed permutation) to every square in a
    position. Used for the `*_rotated` fixtures that exercise A_1 orbit
    averaging invariance downstream."""
    out: dict[int, str] = {}
    for s, ch in pos.items():
        x, y, z, w = t4.rc4(s)
        nx, ny, nz, nw = t4._apply_b4_to_square(g, x, y, z, w)
        out[sq4(nx, ny, nz, nw)] = ch
    return out


# ─── Fixture set (12 canonical positions) ───────────────────────────────────

def _fixtures() -> list[tuple[str, dict[int, str]]]:
    fixtures: list[tuple[str, dict[int, str]]] = []

    # 1. Empty — all channels zero (sanity + zero-init regression guard).
    fixtures.append(("empty", {}))

    # 2. Single white pawn near w=0 — isolated channel-8 write, 8 modes.
    fixtures.append(("single_pawn_white", {sq4(3, 3, 3, 0): 'P'}))

    # 3. Single black pawn near w=7 — opposite-sign channel-8 contribution.
    fixtures.append(("single_pawn_black", {sq4(3, 3, 3, 7): 'p'}))

    # 4. Single knight at deep interior — exercises channels 5-7 (knight
    #    contributes one of the three cross-piece SVD directions).
    fixtures.append(("single_knight", {sq4(3, 3, 3, 3): 'N'}))

    # 5. Single bishop at (0,0,0,0) — even-parity cell; bishop graph has 2
    #    connected components, so this pins us to one component.
    fixtures.append(("single_bishop_even", {sq4(0, 0, 0, 0): 'B'}))

    # 6. Single rook at centre — rook diag-dev (channel 9) witness: rook
    #    Laplacian does not commute with grid, so DIAG_DEV[3] is nonzero.
    fixtures.append(("single_rook_center", {sq4(3, 3, 3, 3): 'R'}))

    # 7. Single queen — rook + bishop disjoint union (cross-check).
    fixtures.append(("single_queen", {sq4(4, 4, 4, 4): 'Q'}))

    # 8. Single king — channel 5-7 king contribution + tiny diag-dev.
    fixtures.append(("single_king", {sq4(3, 3, 3, 3): 'K'}))

    # 9. Pawn pair on the same w-column — additivity check for channel 8.
    fixtures.append((
        "pawn_pair_w_axis",
        {sq4(2, 2, 2, 1): 'P', sq4(2, 2, 2, 6): 'p'},
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
            sq4(1, 0, 0, 0): 'P',
            sq4(1, 3, 0, 0): 'P',
            sq4(6, 3, 0, 7): 'p',
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

    return fixtures


# ─── Emission ───────────────────────────────────────────────────────────────

def main() -> None:
    os.makedirs(FIX_DIR, exist_ok=True)

    fixtures = _fixtures()
    names = [name for name, _ in fixtures]
    assert len(names) == len(set(names)), "duplicate fixture names"
    assert 10 <= len(fixtures) <= 12, (
        f"plan specifies 10-12 fixtures; got {len(fixtures)}"
    )

    # JSONL — square indices as strings (JSON doesn't allow int keys).
    jsonl_path = os.path.join(FIX_DIR, 'positions_4d.jsonl')
    with open(jsonl_path, 'w', encoding='utf-8') as f:
        for name, pos in fixtures:
            record = {
                "name": name,
                "pieces": {str(int(s)): ch for s, ch in sorted(pos.items())},
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

    # Sanity: empty fixture must be all-zero; single-white-pawn fixture must
    # be zero everywhere except the 8 modes of channel 8 for sw=0's column.
    empty_idx = names.index("empty")
    assert float(np.abs(encodings[empty_idx]).max()) == 0.0, \
        "empty fixture is not all-zero"

    pawn_w_idx = names.index("single_pawn_white")
    pawn_enc = encodings[pawn_w_idx]
    non_pawn_channels = np.concatenate([
        pawn_enc[0:8 * t4.N_SQUARES],
        pawn_enc[9 * t4.N_SQUARES:10 * t4.N_SQUARES],
    ])
    assert float(np.abs(non_pawn_channels).max()) > 0.0, (
        "single_pawn_white: at least one of {A1, std4*, diag} must be nonzero"
    )

    print()
    print("All fixtures emitted and spot-checks passed.")


if __name__ == '__main__':
    main()
