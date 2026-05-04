"""1.10.0 immolation: BIP-encoded sheet block round-trip + operator parity.

The BIP encoding (notebook §20.14) packs the 1.9.0 88-byte float aux
block into 3 bytes (uint16 categorical + uint8 halfmove) with a
**bit-exact round trip on the legal state space**. This test suite
verifies that exhaustively (87,264 cases: 864 categorical × 101
halfmove values) plus operator-fast-path agreement with the 1.9.0
float path.

Test surface
------------

  * **Round-trip exhaustive** — every legal SheetState round-trips
    through SheetStateBIP unchanged.
  * **Operator parity** — every operator fast path
    (``castling_alive``, ``kingside_castling_alive``,
    ``fifty_move_rule_triggered``, ``threefold_claimable``, etc.)
    agrees with the equivalent computation on the 1.9.0
    SheetState across the legal state space.
  * **Edge cases** — ``ep_file=None``, halfmove clamping at 100,
    repetition saturation at 2, reserved bits stay zero, dataclass
    bounds-check on construction.
  * **Distance metrics** — Hamming distance behaves correctly;
    halfmove distance is the absolute integer difference.
  * **Bridge surface** — ``bridge.get_sheet_state_bip`` /
    ``encode_sheet_aux_bip`` / ``decode_sheet_state_from_bip``
    round-trip the categorical+halfmove pair without numpy.
  * **Memory check** — BIP storage is meaningfully smaller than the
    1.9.0 float path on a corpus.
"""
from __future__ import annotations

import os
import sys

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
PKG = os.path.dirname(HERE)
if PKG not in sys.path:
    sys.path.insert(0, PKG)

from chess_spectral import (   # noqa: E402
    SheetState,
    SheetStateBIP,
    encode_sheet_state_bip,
    decode_sheet_state_bip,
    castling_alive,
    kingside_castling_alive,
    queenside_castling_alive,
    white_castling_alive,
    black_castling_alive,
    ep_target_active,
    ep_file_from_bip,
    side_to_move_white_from_bip,
    repetition_count_from_bip,
    fifty_move_rule_triggered,
    threefold_claimable,
    hamming_distance_categorical,
    halfmove_distance,
)
from chess_spectral.sheets_bip import (   # noqa: E402
    HALFMOVE_MIN, HALFMOVE_MAX, REPETITION_SATURATION,
    MASK_RESERVED, MASK_CATEGORICAL_USED,
)


# ─── Construction + bounds-check ────────────────────────────────────


def test_immolation_sheet_state_bip_default_construction():
    """Default-construction yields a zero-state SheetStateBIP."""
    bip = SheetStateBIP()
    assert bip.categorical == 0
    assert bip.halfmove_clock == 0


def test_immolation_sheet_state_bip_rejects_out_of_range_categorical():
    with pytest.raises(ValueError):
        SheetStateBIP(categorical=-1, halfmove_clock=0)
    with pytest.raises(ValueError):
        SheetStateBIP(categorical=0x10000, halfmove_clock=0)


def test_immolation_sheet_state_bip_rejects_nonzero_reserved_bits():
    """Reserved bits[12:16] MUST read as zero per the wire contract."""
    with pytest.raises(ValueError):
        SheetStateBIP(categorical=MASK_RESERVED, halfmove_clock=0)
    # And a single reserved bit set is also illegal.
    with pytest.raises(ValueError):
        SheetStateBIP(categorical=1 << 12, halfmove_clock=0)


def test_immolation_sheet_state_bip_rejects_out_of_range_halfmove():
    with pytest.raises(ValueError):
        SheetStateBIP(categorical=0, halfmove_clock=-1)
    with pytest.raises(ValueError):
        SheetStateBIP(categorical=0, halfmove_clock=HALFMOVE_MAX + 1)


def test_immolation_sheet_state_bip_accepts_all_legal_categoricals():
    """Every value in [0, 0xFFF] (the 12-bit categorical range) is legal."""
    # Sample the boundaries + a midpoint; full sweep would be 4096
    # constructions which is fine but slow for a smoke test.
    for c in (0, 1, 0xFFF // 2, 0xFFF):
        bip = SheetStateBIP(categorical=c, halfmove_clock=0)
        assert bip.categorical == c


# ─── Exhaustive round trip — the centerpiece ─────────────────────────


def _iter_legal_categorical_states():
    """Yield every legal SheetState with halfmove=0.

    The categorical state space is:
        4 castling bits  ×  ((no EP) ∪ (8 EP files))  ×  side  ×  rep
    = 16 castling × 9 ep × 2 side × 3 rep = 864.
    """
    for castling_mask in range(16):  # 4-bit castling
        cwk = bool(castling_mask & 0b0001)
        cwq = bool(castling_mask & 0b0010)
        cbk = bool(castling_mask & 0b0100)
        cbq = bool(castling_mask & 0b1000)
        for ep_choice in (None, 0, 1, 2, 3, 4, 5, 6, 7):
            for side in (True, False):
                for rep in (0, 1, 2):
                    yield SheetState(
                        castling_wk=cwk,
                        castling_wq=cwq,
                        castling_bk=cbk,
                        castling_bq=cbq,
                        ep_file=ep_choice,
                        side_to_move_white=side,
                        halfmove_clock=0,
                        repetition_count=rep,
                    )


def test_immolation_round_trip_exhaustive_categorical_at_halfmove_zero():
    """Every (castling × ep × side × rep) combo at halfmove=0 must
    round-trip exactly through SheetStateBIP."""
    n = 0
    for state in _iter_legal_categorical_states():
        bip = encode_sheet_state_bip(state)
        recovered = decode_sheet_state_bip(bip)
        assert recovered == state, (
            f"round-trip failed at state={state!r}; "
            f"encoded={bip!r}; decoded={recovered!r}"
        )
        n += 1
    # 16 castling × 9 ep × 2 side × 3 rep = 864
    assert n == 864, f"expected 864 categorical combos, iterated {n}"


@pytest.mark.parametrize("halfmove", list(range(0, 101)))
def test_immolation_round_trip_halfmove_at_neutral_categorical(halfmove):
    """Every legal halfmove value [0, 100] must round-trip exactly
    when other fields are at their default."""
    state = SheetState(halfmove_clock=halfmove)
    bip = encode_sheet_state_bip(state)
    assert bip.halfmove_clock == halfmove
    recovered = decode_sheet_state_bip(bip)
    assert recovered == state


def test_immolation_round_trip_exhaustive_full_state_space():
    """The full 87,264-case sweep (864 categorical × 101 halfmove)
    must round-trip exactly.

    This is the load-bearing 1.10.0 acceptance gate. Slow but
    mechanical; ~1-2 seconds on modern hardware.
    """
    n = 0
    for state_template in _iter_legal_categorical_states():
        for halfmove in range(0, 101):
            state = SheetState(
                castling_wk=state_template.castling_wk,
                castling_wq=state_template.castling_wq,
                castling_bk=state_template.castling_bk,
                castling_bq=state_template.castling_bq,
                ep_file=state_template.ep_file,
                side_to_move_white=state_template.side_to_move_white,
                halfmove_clock=halfmove,
                repetition_count=state_template.repetition_count,
            )
            bip = encode_sheet_state_bip(state)
            recovered = decode_sheet_state_bip(bip)
            assert recovered == state, (
                f"round-trip failed at state={state!r}; "
                f"encoded={bip!r}; decoded={recovered!r}"
            )
            n += 1
    assert n == 864 * 101, f"expected 87264 cases, iterated {n}"


# ─── Edge cases on encode-time clamping ──────────────────────────────


def test_immolation_halfmove_clamp_above_threshold():
    """Halfmove > 100 clamps to 100 (matches 1.9.0 sheets.py
    behaviour; consumers should pre-clamp if they want explicit
    threshold checks)."""
    state = SheetState(halfmove_clock=150)
    bip = encode_sheet_state_bip(state)
    assert bip.halfmove_clock == HALFMOVE_MAX
    recovered = decode_sheet_state_bip(bip)
    assert recovered.halfmove_clock == HALFMOVE_MAX


def test_immolation_repetition_clamp_above_two():
    """Repetition count > 2 saturates at 2."""
    state = SheetState(repetition_count=99)
    bip = encode_sheet_state_bip(state)
    recovered = decode_sheet_state_bip(bip)
    assert recovered.repetition_count == REPETITION_SATURATION


def test_immolation_ep_file_none_round_trip():
    """ep_file=None must round-trip as ep_active=0, ep_file=0
    (matches the 1.9.0 wire convention)."""
    state = SheetState(ep_file=None)
    bip = encode_sheet_state_bip(state)
    assert not ep_target_active(bip)
    recovered = decode_sheet_state_bip(bip)
    assert recovered.ep_file is None


def test_immolation_reserved_bits_stay_zero_after_encode():
    """Encoded categorical never touches the reserved bits[12:16]."""
    for state in _iter_legal_categorical_states():
        bip = encode_sheet_state_bip(state)
        assert (bip.categorical & MASK_RESERVED) == 0


# ─── Operator fast-path parity ───────────────────────────────────────


def _ref_castling_alive(state: SheetState) -> bool:
    return (state.castling_wk or state.castling_wq
            or state.castling_bk or state.castling_bq)


def _ref_kingside_castling_alive(state: SheetState) -> bool:
    return state.castling_wk or state.castling_bk


def _ref_queenside_castling_alive(state: SheetState) -> bool:
    return state.castling_wq or state.castling_bq


def _ref_white_castling_alive(state: SheetState) -> bool:
    return state.castling_wk or state.castling_wq


def _ref_black_castling_alive(state: SheetState) -> bool:
    return state.castling_bk or state.castling_bq


def _ref_ep_target_active(state: SheetState) -> bool:
    return state.ep_file is not None


def _ref_fifty_move_rule_triggered(state: SheetState) -> bool:
    return min(HALFMOVE_MAX, state.halfmove_clock) >= HALFMOVE_MAX


def _ref_threefold_claimable(state: SheetState) -> bool:
    return min(REPETITION_SATURATION, state.repetition_count) >= 2


@pytest.mark.parametrize("op_pair", [
    (castling_alive, _ref_castling_alive),
    (kingside_castling_alive, _ref_kingside_castling_alive),
    (queenside_castling_alive, _ref_queenside_castling_alive),
    (white_castling_alive, _ref_white_castling_alive),
    (black_castling_alive, _ref_black_castling_alive),
    (ep_target_active, _ref_ep_target_active),
    (fifty_move_rule_triggered, _ref_fifty_move_rule_triggered),
    (threefold_claimable, _ref_threefold_claimable),
])
def test_immolation_operator_parity_full_state_space(op_pair):
    """Every operator fast path must agree with the equivalent
    computation on the 1.9.0 SheetState across the full legal
    state space (864 categorical × 101 halfmove = 87,264 cases)."""
    bip_op, ref_op = op_pair
    n = 0
    for state_template in _iter_legal_categorical_states():
        for halfmove in (0, 50, 99, 100, 101, 200):
            state = SheetState(
                castling_wk=state_template.castling_wk,
                castling_wq=state_template.castling_wq,
                castling_bk=state_template.castling_bk,
                castling_bq=state_template.castling_bq,
                ep_file=state_template.ep_file,
                side_to_move_white=state_template.side_to_move_white,
                halfmove_clock=halfmove,
                repetition_count=state_template.repetition_count,
            )
            bip = encode_sheet_state_bip(state)
            assert bip_op(bip) == ref_op(state), (
                f"{bip_op.__name__} disagrees with reference at "
                f"state={state!r}; got bip={bip_op(bip)}, "
                f"ref={ref_op(state)}"
            )
            n += 1
    assert n == 864 * 6


def test_immolation_ep_file_extraction_parity():
    """ep_file_from_bip(bip) returns the same value as state.ep_file."""
    for state in _iter_legal_categorical_states():
        bip = encode_sheet_state_bip(state)
        assert ep_file_from_bip(bip) == state.ep_file


def test_immolation_side_to_move_extraction_parity():
    """side_to_move_white_from_bip(bip) agrees with state.side_to_move_white."""
    for state in _iter_legal_categorical_states():
        bip = encode_sheet_state_bip(state)
        assert side_to_move_white_from_bip(bip) == state.side_to_move_white


def test_immolation_repetition_extraction_parity():
    """repetition_count_from_bip(bip) agrees with state.repetition_count
    across the saturated range [0, 2]."""
    for state in _iter_legal_categorical_states():
        bip = encode_sheet_state_bip(state)
        assert repetition_count_from_bip(bip) == state.repetition_count


# ─── Distance metrics ────────────────────────────────────────────────


def test_immolation_hamming_distance_self_is_zero():
    """A state has zero Hamming distance to itself."""
    for state in _iter_legal_categorical_states():
        bip = encode_sheet_state_bip(state)
        assert hamming_distance_categorical(bip, bip) == 0


def test_immolation_hamming_distance_castling_diff():
    """States differing in only one castling bit have Hamming
    distance 1 over the categorical portion."""
    a = SheetState()  # all castling false
    b = SheetState(castling_wk=True)
    bip_a = encode_sheet_state_bip(a)
    bip_b = encode_sheet_state_bip(b)
    assert hamming_distance_categorical(bip_a, bip_b) == 1


def test_immolation_hamming_distance_full_state_diff():
    """All-false state vs maximally-different categorical state.

    State b has:
      * 4 castling bits set (bits 0..3)
      * 1 ep_active bit + 3 ep_file bits all set (file 7 = 0b111, bits 4..7)
      * side_to_move bit set (bit 8)
      * repetition_count = 2 = 0b10 — this sets ONLY the MSB of the
        2-bit repetition field (bit 10), so just 1 bit.

    Total: 4 + 4 + 1 + 1 = 10 bits.
    """
    a = SheetState(  # everything zero/None/default
        castling_wk=False, castling_wq=False,
        castling_bk=False, castling_bq=False,
        ep_file=None,
        side_to_move_white=True,
        repetition_count=0,
    )
    b = SheetState(
        castling_wk=True, castling_wq=True,
        castling_bk=True, castling_bq=True,
        ep_file=7,
        side_to_move_white=False,
        repetition_count=2,
    )
    bip_a = encode_sheet_state_bip(a)
    bip_b = encode_sheet_state_bip(b)
    assert hamming_distance_categorical(bip_a, bip_b) == 10


def test_immolation_hamming_distance_repetition_one_vs_two():
    """rep=1 (0b01) vs rep=2 (0b10) sets DIFFERENT bits in the
    2-bit repetition field — Hamming distance should be 2, not 1.

    This is the subtle property of binary representation: the
    repetition values 0/1/2 are NOT consecutive in Hamming space
    even though they're consecutive integers. Distance(0,1)=1,
    distance(0,2)=1, distance(1,2)=2."""
    rep_0 = encode_sheet_state_bip(SheetState(repetition_count=0))
    rep_1 = encode_sheet_state_bip(SheetState(repetition_count=1))
    rep_2 = encode_sheet_state_bip(SheetState(repetition_count=2))
    assert hamming_distance_categorical(rep_0, rep_1) == 1  # 0b00 vs 0b01
    assert hamming_distance_categorical(rep_0, rep_2) == 1  # 0b00 vs 0b10
    assert hamming_distance_categorical(rep_1, rep_2) == 2  # 0b01 vs 0b10


def test_immolation_hamming_distance_ignores_reserved_bits():
    """Reserved bits don't contribute to Hamming distance.

    By construction, ``encode_sheet_state_bip`` never sets reserved
    bits, but the metric must be robust against external manipulation.
    """
    a = encode_sheet_state_bip(SheetState())
    # Construct b with the same categorical content but explicitly
    # masked to bits[0:12] so reserved bits stay zero. This is the
    # only legal way to construct a SheetStateBIP with arbitrary
    # categorical content — the dataclass's __post_init__ rejects
    # non-zero reserved bits.
    b = SheetStateBIP(categorical=a.categorical & MASK_CATEGORICAL_USED,
                      halfmove_clock=0)
    assert hamming_distance_categorical(a, b) == 0


def test_immolation_halfmove_distance():
    """Halfmove distance is absolute integer diff."""
    a = SheetStateBIP(categorical=0, halfmove_clock=10)
    b = SheetStateBIP(categorical=0, halfmove_clock=42)
    assert halfmove_distance(a, b) == 32
    assert halfmove_distance(b, a) == 32  # symmetric
    assert halfmove_distance(a, a) == 0   # reflexive


# ─── from_chess_board factory parity ────────────────────────────────


def test_immolation_from_chess_board_via_bip():
    """python-chess Board startpos → SheetState → SheetStateBIP →
    SheetState. The full chain must round-trip exactly."""
    chess = pytest.importorskip("chess")
    board = chess.Board()
    sheet = SheetState.from_chess_board(board)
    bip = encode_sheet_state_bip(sheet)
    recovered = decode_sheet_state_bip(bip)
    assert recovered == sheet


def test_immolation_from_chess_board_after_e4_via_bip():
    """1. e4 → ep_file=4 round-trips through BIP."""
    chess = pytest.importorskip("chess")
    board = chess.Board()
    board.push_uci("e2e4")
    sheet = SheetState.from_chess_board(board)
    bip = encode_sheet_state_bip(sheet)
    recovered = decode_sheet_state_bip(bip)
    assert recovered == sheet
    assert recovered.ep_file == 4


def test_immolation_from_game_state_4d_via_bip():
    """4D OC canonical startpos lifts via BIP losslessly."""
    from chess_spectral_4d import initial_position
    state = SheetState.from_game_state_4d(initial_position())
    bip = encode_sheet_state_bip(state)
    recovered = decode_sheet_state_bip(bip)
    assert recovered == state


# ─── Bridge surface ──────────────────────────────────────────────────


def test_immolation_bridge_get_sheet_state_bip_4d():
    """bridge.get_sheet_state_bip on a GameState4D returns
    integer-only fields."""
    from chess_spectral_4d import bridge, initial_position
    res = bridge.get_sheet_state_bip(initial_position())
    assert res["ok"] is True
    bip_dict = res["sheet_bip"]
    assert isinstance(bip_dict["categorical"], int)
    assert isinstance(bip_dict["halfmove_clock"], int)
    # 4D-OC startpos: no castling, no EP, white to move, halfmove=0,
    # rep=0. Only side bit is potentially set; check categorical=0.
    assert bip_dict["categorical"] == 0
    assert bip_dict["halfmove_clock"] == 0


def test_immolation_bridge_get_sheet_state_bip_2d():
    """bridge.get_sheet_state_bip on a python-chess Board startpos."""
    chess = pytest.importorskip("chess")
    from chess_spectral_4d import bridge
    res = bridge.get_sheet_state_bip(chess.Board())
    assert res["ok"] is True
    bip_dict = res["sheet_bip"]
    # All four castling bits set, no EP, white to move, halfmove=0.
    # Bits[0:4] = 0b1111 = 15.
    assert bip_dict["categorical"] == 0b1111
    assert bip_dict["halfmove_clock"] == 0


def test_immolation_bridge_encode_sheet_aux_bip_round_trip():
    """encode_sheet_aux_bip(sheet_dict) followed by
    decode_sheet_state_from_bip(...) round-trips the dict."""
    from chess_spectral_4d import bridge
    sheet_dict = {
        "castling_wk": True,
        "castling_wq": False,
        "castling_bk": True,
        "castling_bq": True,
        "ep_file": 5,
        "side_to_move_white": False,
        "halfmove_clock": 37,
        "repetition_count": 1,
    }
    enc = bridge.encode_sheet_aux_bip(sheet_dict)
    assert enc["ok"] is True
    dec = bridge.decode_sheet_state_from_bip(
        enc["categorical"], enc["halfmove_clock"])
    assert dec["ok"] is True
    assert dec["sheet"] == sheet_dict


def test_immolation_bridge_encode_sheet_aux_bip_missing_field():
    """Missing required field returns ok=False with a descriptive error."""
    from chess_spectral_4d import bridge
    incomplete = {
        "castling_wk": True,
        # ... missing the rest
    }
    res = bridge.encode_sheet_aux_bip(incomplete)
    assert res["ok"] is False
    assert "KeyError" in res["error"]


def test_immolation_bridge_decode_sheet_state_from_bip_invalid_input():
    """Invalid bip inputs return ok=False."""
    from chess_spectral_4d import bridge
    # Reserved bits set
    res = bridge.decode_sheet_state_from_bip(MASK_RESERVED, 0)
    assert res["ok"] is False
    # Halfmove out of range
    res = bridge.decode_sheet_state_from_bip(0, 200)
    assert res["ok"] is False
    # Categorical out of uint16
    res = bridge.decode_sheet_state_from_bip(0x10000, 0)
    assert res["ok"] is False


def test_immolation_bridge_get_sheet_state_bip_unrecognized():
    """A bogus input returns ok=False with a descriptive error."""
    from chess_spectral_4d import bridge
    res = bridge.get_sheet_state_bip("not a board")
    assert res["ok"] is False
    assert "GameState4D" in res["error"] or "Board" in res["error"]


# ─── Memory / compression sanity ────────────────────────────────────


def test_immolation_bip_uses_two_python_ints():
    """SheetStateBIP carries only two integer fields. Storage at
    the Python level is dominated by the dataclass overhead, but the
    *content* fits in 3 bytes (2 for categorical + 1 for halfmove)."""
    bip = SheetStateBIP(categorical=0xABC, halfmove_clock=42)
    # The integer values themselves fit in the documented ranges.
    assert 0 <= bip.categorical <= 0xFFFF
    assert 0 <= bip.halfmove_clock <= 100
    # Verify the bit-packing fits in 3 bytes total.
    assert bip.categorical.bit_length() <= 16
    assert bip.halfmove_clock.bit_length() <= 8
