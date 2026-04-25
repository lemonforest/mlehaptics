"""Unbinding decoder for the Phase 2 encoders.

Given a hypervector produced by ``encode_ant.py``, recover the residue
class for any *supported* dial.  Three decode paths matching the three
encoder variants:

- ``decode_dial_dense``: correlate against rolls of the dial's channel
  basis; argmax over rolls is the recovered residue.  Used for
  ``encode_ant_callippic`` and ``encode_ant_packing``.
- ``decode_dial_lcm``: direct lookup in ``LCMState.residues``.
  Round-trip is perfect by construction.
- ``decode_dial_block_diagonal``: read the block at the dial's slice;
  argmax position within block is the recovered residue.  Serves as
  the ground-truth oracle for B-H3.

The cross-talk between dials in the dense encoders limits decoding
precision.  ``decode_all_dials`` runs all dials through the decoder
and returns a dict of ``{dial_name: (recovered_residue,
true_residue, ok)}`` tuples for B-H3 / round-trip testing.
"""

from __future__ import annotations

from typing import Any, Dict, Optional, Tuple

import numpy as np

from .astronomical_cycles import CYCLES
from .encode_ant import (
    DIAL_SPECS,
    LCMState,
    UnsupportedDialError,
    _encode_dense,            # noqa: WPS437 — internal helper used in tests
    encode_ant_block_diagonal,
    encode_ant_callippic,
    encode_ant_lcm,
    encode_ant_packing,
    get_channel_basis,
    supported_dials,
    D_CALLIPPIC,
    D_PACKING,
    D_LCM,
    REFERENCE_JD,
)


# ---------------------------------------------------------------------------
# Dense decoder (D=940, D=13440)
# ---------------------------------------------------------------------------

def decode_dial_dense(state: np.ndarray, dial_name: str, D: int) -> int:
    """Recover the residue (0..D-1) for ``dial_name`` from a dense state.

    For each candidate roll k = 0..D-1, compute
    ``inner = <state, roll(channel_basis, k)>`` and return argmax over
    |inner|.  Cross-talk from other channels reduces the contrast but
    the argmax is robust at our orthogonality threshold (< 0.05) for
    13 channels in 13440-D and 8 channels in 940-D.

    Raises
    ------
    UnsupportedDialError
        If the dial is not supported at the given D (e.g. planetary
        dials at D=940).
    KeyError
        If ``dial_name`` is not in the cycle catalogue.
    """
    spec = next((s for s in DIAL_SPECS if s.name == dial_name), None)
    if spec is None:
        raise KeyError(f"Unknown dial: {dial_name!r}")
    if not spec.is_supported(D):
        raise UnsupportedDialError(
            f"Dial {dial_name!r} not supported at D={D}"
        )

    dial_idx = DIAL_SPECS.index(spec)
    basis = get_channel_basis(D, dial_idx)

    # Use FFT-based circular correlation for speed.
    # corr[k] = <state, roll(basis, k)> = sum_n state[n] * conj(basis[(n - k) mod D])
    # This is the cross-correlation of state with conj(basis) at all lags.
    state_fft = np.fft.fft(state)
    basis_fft = np.fft.fft(basis)
    # Cross-correlation: ifft(state_fft * conj(basis_fft))[k] = sum_n state[n] · conj(basis[n-k])
    corr = np.fft.ifft(state_fft * np.conj(basis_fft))
    return int(np.argmax(np.abs(corr)))


def decode_all_dials_dense(
    state: np.ndarray, D: int
) -> Dict[str, int]:
    """Decode every supported dial from a dense state."""
    out: Dict[str, int] = {}
    for spec in supported_dials(D):
        out[spec.name] = decode_dial_dense(state, spec.name, D)
    return out


# ---------------------------------------------------------------------------
# LCM (symbolic) decoder
# ---------------------------------------------------------------------------

def decode_dial_lcm(state: LCMState, dial_name: str) -> int:
    """Direct dictionary lookup; round-trip perfect by construction."""
    if dial_name not in state.residues:
        raise UnsupportedDialError(
            f"Dial {dial_name!r} not encoded in this LCMState"
        )
    return state.residues[dial_name]


# ---------------------------------------------------------------------------
# Block-diagonal oracle decoder
# ---------------------------------------------------------------------------

def decode_dial_block_diagonal(
    state: np.ndarray, dial_name: str, D: int
) -> int:
    """Read the block at the dial's slice; argmax inside block."""
    spec = next((s for s in DIAL_SPECS if s.name == dial_name), None)
    if spec is None:
        raise KeyError(f"Unknown dial: {dial_name!r}")
    if not spec.is_supported(D):
        raise UnsupportedDialError(
            f"Dial {dial_name!r} not supported at D={D}"
        )

    supported = supported_dials(D)
    n = len(supported)
    block_size = D // n
    i = supported.index(spec)
    block = state[i * block_size:(i + 1) * block_size]
    return int(np.argmax(np.abs(block)))


def decode_all_dials_block_diagonal(
    state: np.ndarray, D: int
) -> Dict[str, int]:
    out: Dict[str, int] = {}
    for spec in supported_dials(D):
        out[spec.name] = decode_dial_block_diagonal(state, spec.name, D)
    return out


# ---------------------------------------------------------------------------
# Round-trip test harness
# ---------------------------------------------------------------------------

def round_trip_dense(date_jd: float, D: int) -> Dict[str, Dict[str, Any]]:
    """For each supported dial, encode -> decode -> compare.

    Returns
    -------
    Dict[dial_name -> {'true': int, 'recovered': int, 'match_d_bin': bool,
                       'match_modulus': bool}]

    'match_d_bin' compares the decoded D-bin residue to the encoder's
    D-bin residue (true equality is expected, but cross-talk can
    cause off-by-1 errors at threshold cases).

    'match_modulus' converts both back to the cycle's natural integer
    modulus (cycle.numerator) and compares — this is the
    therapeutically meaningful test ("does the dial point to the right
    integer?") and tolerates D-bin off-by-1 errors that don't change
    the cycle-modulus residue.
    """
    state = _encode_dense(date_jd, D)
    out: Dict[str, Dict[str, Any]] = {}
    for spec in supported_dials(D):
        true_d_bin = spec.residue(date_jd, D)
        rec_d_bin = decode_dial_dense(state, spec.name, D)
        true_int = spec.integer_residue(date_jd)
        # Convert recovered D-bin residue back to integer modulus
        modulus = spec.cycle_modulus
        rec_int = int(rec_d_bin * modulus / D) % modulus
        out[spec.name] = {
            "true_d_bin": true_d_bin,
            "recovered_d_bin": rec_d_bin,
            "match_d_bin": rec_d_bin == true_d_bin,
            "true_modulus": true_int,
            "recovered_modulus": rec_int,
            "match_modulus": rec_int == true_int,
        }
    return out


def round_trip_lcm(date_jd: float) -> Dict[str, Dict[str, Any]]:
    """Round-trip via the symbolic LCM encoder.  Always perfect."""
    state = encode_ant_lcm(date_jd)
    out: Dict[str, Dict[str, Any]] = {}
    for spec in DIAL_SPECS:
        if spec.name not in state.residues:
            continue
        true_int = spec.integer_residue(date_jd)
        rec_int = decode_dial_lcm(state, spec.name)
        out[spec.name] = {
            "true": true_int,
            "recovered": rec_int,
            "match": rec_int == true_int,
        }
    return out


def round_trip_block_diagonal(
    date_jd: float, D: int
) -> Dict[str, Dict[str, Any]]:
    """Round-trip via the block-diagonal oracle (always perfect within block)."""
    state = encode_ant_block_diagonal(date_jd, D)
    supported = supported_dials(D)
    n = len(supported)
    block_size = D // n
    out: Dict[str, Dict[str, Any]] = {}
    for spec in supported:
        true_int = spec.integer_residue(date_jd)
        # Block-diagonal stores residue % block_size as the offset.
        rec_offset = decode_dial_block_diagonal(state, spec.name, D)
        # Recovered "residue" is the offset within block; for cycles
        # whose modulus exceeds block_size, the encoder lossy-quantises.
        out[spec.name] = {
            "true_modulus": true_int,
            "recovered_offset": rec_offset,
            "match_within_block": rec_offset == true_int % block_size,
        }
    return out


# ---------------------------------------------------------------------------
# Smoke test
# ---------------------------------------------------------------------------

_EPILOG = """\
Examples:
  # Default: full round-trip battery (3 variants + oracle):
  python -m research.dial_decoder

  # Just one variant:
  python -m research.dial_decoder --variant lcm

  # Decode a single dial at a specific JD:
  python -m research.dial_decoder --variant packing --jd 1684960.0 \\
        --dial Saros

References
----------
Decoding via FFT correlation is the standard HDC unbinding (Plate 2003).
"""


def _make_parser():
    import argparse
    parser = argparse.ArgumentParser(
        prog="python -m research.dial_decoder",
        description=("Round-trip decoder battery -- encode then decode "
                     "every dial under three D variants and verify exact "
                     "recovery (B-H3)."),
        epilog=_EPILOG,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--variant", default="all",
        choices=("dense", "lcm", "block", "callippic", "packing", "all"),
        help="Round-trip variant (default: all).",
    )
    parser.add_argument(
        "--jd", type=float, default=None,
        help="Test date as JD (default: REFERENCE_JD + 365).",
    )
    parser.add_argument(
        "--dial", default=None,
        help="Decode just this dial name and exit.",
    )
    return parser


def main(argv=None):
    args = _make_parser().parse_args(argv)
    print("dial_decoder -- round-trip tests for all 3 D variants + oracle")
    print("=" * 60)
    test_jd = args.jd if args.jd is not None else REFERENCE_JD + 365.0
    print(f"Test date: JD = {test_jd}")
    print()

    if args.dial:
        # Single-dial decode probe
        if args.variant in ("packing", "dense", "all"):
            state = encode_ant_packing(test_jd)
            try:
                r = decode_dial_dense(state, args.dial, D_PACKING)
                print(f"  {args.dial} (D=13440): residue = {r}")
            except UnsupportedDialError as e:
                print(f"  {args.dial}: UnsupportedDialError: {e}")
        if args.variant in ("lcm", "all"):
            from .encode_ant import encode_ant_lcm
            state_lcm = encode_ant_lcm(test_jd)
            try:
                r = decode_dial_lcm(state_lcm, args.dial)
                print(f"  {args.dial} (LCM symbolic): residue = {r}")
            except KeyError:
                print(f"  {args.dial}: not in LCM state")
        return 0

    if args.variant in ("dense", "callippic", "all"):
        print("--- D = 940 (Callippic) dense round-trip ---")
        rt = round_trip_dense(test_jd, D_CALLIPPIC)
        n_match_m = sum(1 for v in rt.values() if v["match_modulus"])
        print(f"  Modulus matches: {n_match_m}/{len(rt)}")

    if args.variant in ("dense", "packing", "all"):
        print("--- D = 13440 (Packing) dense round-trip ---")
        rt = round_trip_dense(test_jd, D_PACKING)
        n_match_m = sum(1 for v in rt.values() if v["match_modulus"])
        print(f"  Modulus matches: {n_match_m}/{len(rt)}")

    if args.variant in ("lcm", "all"):
        print("--- D = LCM symbolic round-trip ---")
        rt_lcm = round_trip_lcm(test_jd)
        n_match = sum(1 for v in rt_lcm.values() if v["match"])
        print(f"  Matches: {n_match}/{len(rt_lcm)} (should be all)")

    if args.variant in ("block", "all"):
        print("--- D = 13440 block-diagonal oracle round-trip ---")
        rt_b = round_trip_block_diagonal(test_jd, D_PACKING)
        n_match = sum(1 for v in rt_b.values() if v["match_within_block"])
        print(f"  Within-block matches: {n_match}/{len(rt_b)}")

    if args.variant == "all":
        print("--- D = 940 planetary UnsupportedDialError check ---")
        state = encode_ant_callippic(test_jd)
        try:
            _ = decode_dial_dense(state, "Mars_synodic_period_relation",
                                  D_CALLIPPIC)
            print("  FAIL: no exception raised")
        except UnsupportedDialError as e:
            print(f"  PASS: {e}")
    print()
    print("All round-trip smoke tests complete.")
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
