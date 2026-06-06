"""C/Python parity for the Hamming / GF(2) block-code family (#910 / §30).

v0.7.2rc2 ships the CARRY/EC half of the sedenion front-loader (F442/F449) as a
Rosetta pair: the pure-Python spec ``srmech.amsc.cascade.hamming_*`` and the
JPL-clean C peer ``srmech_hamming_{encode,syndrome,decode_correct}``. This test
fixes the Python behaviour with a from-scratch reference (no srmech import) and
attests the C peer bit-exact against it across the 2ⁿ−1 ladder.

The C peer is exercised only when ``HAS_NATIVE`` and the loaded libsrmech
exposes the rc2 symbols (a stale lib loads fine but skips cleanly).
"""
import ctypes
import random

import pytest

from srmech.amsc import _native, cascade
from srmech.amsc._native import HAS_NATIVE


_HAMMING_NATIVE = (
    HAS_NATIVE
    and _native.LIB is not None
    and hasattr(_native.LIB, "srmech_hamming_encode")
    and hasattr(_native.LIB, "srmech_hamming_syndrome")
    and hasattr(_native.LIB, "srmech_hamming_decode_correct")
)

SKIP_IF_NO_HAMMING_NATIVE = pytest.mark.skipif(
    not _HAMMING_NATIVE,
    reason="installed libsrmech predates v0.7.2rc2 Hamming symbols",
)


# ── from-scratch reference (no srmech import) ─────────────────────────────────

def _ref_data_positions(n):
    big = (1 << n) - 1
    return [j for j in range(1, big + 1) if (j & (j - 1)) != 0]


def _ref_encode(data, n):
    big = (1 << n) - 1
    code = [0] * big
    for slot, j in enumerate(_ref_data_positions(n)):
        code[j - 1] = data[slot]
    for i in range(n):
        p = 1 << i
        par = 0
        for j in range(1, big + 1):
            if j != p and (j & p):
                par ^= code[j - 1]
        code[p - 1] = par
    return code


def _ref_syndrome(code):
    big = len(code)
    n = (big + 1).bit_length() - 1
    syn = 0
    for i in range(n):
        p = 1 << i
        s = 0
        for j in range(1, big + 1):
            if j & p:
                s ^= code[j - 1]
        if s:
            syn |= p
    return syn


# ── pure-Python correctness ───────────────────────────────────────────────────

def test_h74_known_vector():
    assert cascade.hamming_encode([1, 0, 1, 1], 3) == [0, 1, 1, 0, 0, 1, 1]


def test_clean_syndrome_is_zero():
    cw = cascade.hamming_encode([1, 0, 1, 1], 3)
    assert cascade.hamming_syndrome(cw) == 0


@pytest.mark.parametrize("n", [2, 3, 4, 5])
def test_all_position_single_error_correction(n):
    """Every single-bit error in every position is located + corrected, and the
    data payload recovers exactly — the defining contract of a distance-3 code."""
    rng = random.Random(20260606 + n)
    big = (1 << n) - 1
    k = big - n
    for _ in range(20):
        data = [rng.randint(0, 1) for _ in range(k)]
        code = cascade.hamming_encode(data, n)
        assert cascade.hamming_syndrome(code) == 0
        for pos in range(1, big + 1):
            bad = list(code)
            bad[pos - 1] ^= 1
            assert cascade.hamming_syndrome(bad) == pos
            out = cascade.hamming_decode_correct(bad)
            assert out["error_position"] == pos
            assert out["data"] == data
            assert out["corrected_codeword"] == code


def test_decode_clean_word_roundtrips():
    data = [1, 1, 0, 0, 1, 0, 1, 1, 0, 1, 0]   # 11 bits -> H(15,11)
    code = cascade.hamming_encode(data, 4)
    out = cascade.hamming_decode_correct(code)
    assert out["error_position"] == 0
    assert out["data"] == data


def test_h74_is_fano_dimension():
    """Hamming(7,4): codeword length 7, payload 4 — the octonion Fano(7) (F441)."""
    code = cascade.hamming_encode([0, 0, 0, 0], 3)
    assert len(code) == 7 and code == [0] * 7


# ── error cases ───────────────────────────────────────────────────────────────

def test_encode_rejects_wrong_data_length():
    with pytest.raises(ValueError):
        cascade.hamming_encode([1, 0, 1], 3)   # H(7,4) needs 4 data bits


def test_encode_rejects_non_bit():
    with pytest.raises(ValueError):
        cascade.hamming_encode([1, 0, 2, 1], 3)


def test_encode_rejects_bad_n():
    with pytest.raises(ValueError):
        cascade.hamming_encode([0], 1)         # n < 2


def test_syndrome_rejects_non_hamming_length():
    with pytest.raises(ValueError):
        cascade.hamming_syndrome([0, 1, 0, 1, 0, 1])   # 6 is not 2ⁿ−1


# ── reference cross-check (Python op == from-scratch ref) ─────────────────────

def test_python_matches_reference_sweep():
    rng = random.Random(7)
    for n in (3, 4, 5):
        big = (1 << n) - 1
        k = big - n
        for _ in range(25):
            data = [rng.randint(0, 1) for _ in range(k)]
            code = cascade.hamming_encode(data, n)
            assert code == _ref_encode(data, n)
            bad = list(code)
            flip = rng.randint(0, big)        # 0 => leave clean
            if flip:
                bad[flip - 1] ^= 1
            assert cascade.hamming_syndrome(bad) == _ref_syndrome(bad)


# ── native C peer attested bit-exact against the Python spec ──────────────────

@SKIP_IF_NO_HAMMING_NATIVE
def test_native_encode_matches_python():
    rng = random.Random(11)
    for n in (2, 3, 4, 5, 6):
        big = (1 << n) - 1
        k = big - n
        for _ in range(15):
            data = [rng.randint(0, 1) for _ in range(k)]
            py = cascade.hamming_encode(data, n)
            arr = (ctypes.c_uint8 * k)(*data)
            out = (ctypes.c_uint8 * big)()
            rc = _native.LIB.srmech_hamming_encode(
                arr, ctypes.c_size_t(k), ctypes.c_int(n), out,
            )
            assert rc == _native.SRMECH_OK
            assert list(out) == py


@SKIP_IF_NO_HAMMING_NATIVE
def test_native_syndrome_and_decode_match_python():
    rng = random.Random(13)
    for n in (3, 4, 5):
        big = (1 << n) - 1
        k = big - n
        for _ in range(15):
            data = [rng.randint(0, 1) for _ in range(k)]
            code = cascade.hamming_encode(data, n)
            for pos in (0, 1, big // 2 + 1, big):   # clean + a few positions
                bad = list(code)
                if pos:
                    bad[pos - 1] ^= 1
                arr = (ctypes.c_uint8 * big)(*bad)
                # syndrome
                out_pos = ctypes.c_int(-1)
                rc = _native.LIB.srmech_hamming_syndrome(
                    arr, ctypes.c_size_t(big), ctypes.byref(out_pos),
                )
                assert rc == _native.SRMECH_OK
                assert out_pos.value == cascade.hamming_syndrome(bad) == pos
                # decode_correct
                out_data = (ctypes.c_uint8 * k)()
                out_pos2 = ctypes.c_int(-1)
                rc = _native.LIB.srmech_hamming_decode_correct(
                    arr, ctypes.c_size_t(big), out_data, ctypes.byref(out_pos2),
                )
                assert rc == _native.SRMECH_OK
                py = cascade.hamming_decode_correct(bad)
                assert list(out_data) == py["data"]
                assert out_pos2.value == py["error_position"] == pos


@SKIP_IF_NO_HAMMING_NATIVE
def test_native_rejects_bad_length():
    arr = (ctypes.c_uint8 * 6)(0, 1, 0, 1, 0, 1)
    out_pos = ctypes.c_int(0)
    rc = _native.LIB.srmech_hamming_syndrome(
        arr, ctypes.c_size_t(6), ctypes.byref(out_pos),
    )
    assert rc == _native.SRMECH_ERR_BAD_INPUT


@SKIP_IF_NO_HAMMING_NATIVE
def test_hamming_symbols_exposed():
    for sym in ("srmech_hamming_encode", "srmech_hamming_syndrome",
                "srmech_hamming_decode_correct"):
        assert hasattr(_native.LIB, sym), f"{sym} should be exposed in libsrmech"
