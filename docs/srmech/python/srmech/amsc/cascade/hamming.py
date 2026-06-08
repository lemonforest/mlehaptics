"""Hamming / GF(2) linear block-code family — the CARRY/EC half of the
sedenion front-loader (#910 / §30; findings F442 + F449).

The "front-loader" is **CARRY ∘ COUPLE**:

* **COUPLE** — bind ≤7 streams reversibly into an octonion — is native
  (:func:`srmech.amsc.cascade.hypercomplex_couple`, §29 / #908). It is capped
  at 𝕆 by Hurwitz: 7 reversible imaginary slots.
* **CARRY** — hold *more than 7* data items + locate/correct an error in one
  structure, reversible **past** 𝕆 — needs the sedenion's CODE structure
  (its Fano/PG geometry), **not** its broken chirality (the sedenion has zero
  divisors, so its *product* is not reversible; its *linear code* is). This
  module ships that half: the **2ⁿ−1 Hamming ladder** Hamming(7,4) / (15,11) /
  (31,26) / … — a single-error-correcting GF(2) linear block code.

A Hamming(15,11) carrier holds **11 data + 4 EC bits** in one 15-slot
structure — 1.57× the octonion algebra's 7 reversible slots (F449) — locates
and corrects any single-bit error, and recovers exactly. The octonion's
**Fano(7)** plane nests inside: Hamming(7,4) IS the octonion's own Fano
structure (F441; PG(2,2) ⊂ PG(3,2)).

**Lean-ALU XOR-native.** GF(2) addition IS XOR IS parity IS ``add mod 2`` — the
substrate srmech already ships (``hdc._xor_buf``; the lean-ISA ``add``/``sub``).
There is no ``abs()``, no float, no libm: a block code is ``^`` and index
arithmetic only. Class home: **B** (TLV/structure framing — the parity-check
layout) ∘ **I** (cyclic index arithmetic over the 2ⁿ−1 positions) ∘ **A**
(content integrity — the syndrome IS a content-addressed error locator).

**Construction (canonical Hamming, 1-indexed).** Codeword positions ``1..N``
with ``N = 2ⁿ−1``. Parity bits sit at the power-of-two positions
``1, 2, 4, …, 2ⁿ⁻¹``; the remaining ``k = N − n`` positions carry data. The
parity bit at ``2ⁱ`` is the even-parity XOR of every position whose index has
bit ``i`` set. The **syndrome** (recompute every parity, read the failed set as
a binary number) IS the 1-indexed position of the single flipped bit — ``0``
means clean. Single-error-correcting (minimum distance 3).

**Fences (F449).** (a) This carries the octonion's **GF(2) sector/structure
bits** + EC; real-valued coefficients ride *alongside* — real-field EC (RS/BCH
over ℝ) is a separate, larger construction, NOT this op. (b) The code gives **no
multiplicative product** — bind/couple stays :func:`hypercomplex_couple`'s job
(≤𝕆); CARRY and COUPLE are distinct roles. (c) **Single**-error correction per
rung (distance 3); larger tolerance is BCH/RS, a different code.

SSoT: Hamming, R. W. (1950), *Error detecting and error correcting codes*,
Bell Syst. Tech. J. 29(2):147–160. The Rosetta C peer
(``srmech_hamming_{encode,syndrome,decode_correct}``) is attested bit-exact
against this module by ``tests/test_cascade_hamming_parity.py``.
"""
from __future__ import annotations

import ctypes
from typing import Any, Dict, List, Sequence

from srmech.amsc import _native  # rc11: native srmech_hamming_* dispatch

#: Upper bound on the parity-bit count ``n`` (codeword ``2ⁿ−1`` ≤ 65535). The C
#: peer shares this ceiling so the two surfaces accept the same domain.
HAMMING_MAX_N = 16


def _check_n(n: int) -> int:
    if type(n) is not int:
        raise TypeError(f"n must be an int (parity-bit count); got {type(n).__name__}")
    if n < 2 or n > HAMMING_MAX_N:
        raise ValueError(
            f"n (parity-bit count) must be in [2, {HAMMING_MAX_N}]; got {n}. "
            f"The codeword length is 2ⁿ−1 (Hamming(3,1)…Hamming(65535,65519))."
        )
    return n


def _infer_n(length: int) -> int:
    """Recover ``n`` from a codeword length ``N = 2ⁿ−1`` (else ValueError)."""
    n = (length + 1).bit_length() - 1
    if (1 << n) - 1 != length:
        raise ValueError(
            f"codeword length {length} is not of the form 2ⁿ−1 (a Hamming "
            f"codeword is 3, 7, 15, 31, 63, …)"
        )
    return _check_n(n)


def _as_bits(seq: Sequence[int], label: str) -> List[int]:
    out: List[int] = []
    for b in seq:
        if b != 0 and b != 1:
            raise ValueError(f"{label} must be 0/1 bits; got {b!r}")
        out.append(int(b))
    return out


def _data_positions(n: int) -> List[int]:
    """The non-power-of-two positions in ``1..2ⁿ−1``, in ascending order — the
    ``k = 2ⁿ−1−n`` data slots (parity bits live at the powers of two)."""
    big = (1 << n) - 1
    return [j for j in range(1, big + 1) if (j & (j - 1)) != 0]


def hamming_encode(data_bits: Sequence[int], n: int) -> List[int]:
    """Encode ``k = 2ⁿ−1−n`` data bits into a Hamming(2ⁿ−1, k) codeword.

    Parity bits at the power-of-two positions are set to the even-parity XOR of
    the data positions they cover. Lean-ALU: ``^`` only — no float, no libm.

    Parameters
    ----------
    data_bits : sequence of 0/1
        Exactly ``2ⁿ−1−n`` data bits (e.g. 4 for Hamming(7,4), 11 for (15,11)).
    n : int
        Parity-bit count (``2 ≤ n ≤ 16``); the codeword length is ``2ⁿ−1``.

    Returns
    -------
    list[int]
        The ``2ⁿ−1``-bit codeword (1-indexed positions flattened to a list).
    """
    n = _check_n(n)
    big = (1 << n) - 1
    data = _as_bits(data_bits, "data_bits")
    expected_k = big - n
    if len(data) != expected_k:
        raise ValueError(
            f"Hamming(2^{n}-1={big}, {expected_k}) needs exactly {expected_k} "
            f"data bits; got {len(data)}"
        )
    # rc11: dispatch the GF(2) encode to the C peer when present (lean-ALU XOR;
    # bit-identical to the pure-Python parity build below, which remains the
    # Pyodide / no-native fallback). Parity-attested by test_cascade_hamming_parity.
    if (_native.HAS_NATIVE and _native.LIB is not None
            and hasattr(_native.LIB, "srmech_hamming_encode")):
        data_arr = (ctypes.c_uint8 * expected_k)(*data)
        out_arr = (ctypes.c_uint8 * big)()
        rc = _native.LIB.srmech_hamming_encode(data_arr, expected_k, n, out_arr)
        if rc == _native.SRMECH_OK:
            return list(out_arr)
    code = [0] * big
    for slot, j in enumerate(_data_positions(n)):
        code[j - 1] = data[slot]
    # Each parity bit = even-parity XOR of the positions it covers (GF(2) add).
    for i in range(n):
        p = 1 << i
        par = 0
        for j in range(1, big + 1):
            if j != p and (j & p) != 0:
                par ^= code[j - 1]
        code[p - 1] = par
    return code


def hamming_syndrome(codeword: Sequence[int]) -> int:
    """Return the 1-indexed position of the single flipped bit (``0`` = clean).

    The syndrome is the binary number whose bit ``i`` is the recomputed parity
    of position ``2ⁱ`` — by Hamming's construction this IS the error position.
    """
    code = _as_bits(codeword, "codeword")
    n = _infer_n(len(code))
    big = len(code)
    # rc11: dispatch the syndrome (the content-addressed error locator) to the C
    # peer when present; bit-identical 1-indexed position. (hamming_decode_correct
    # composes this, so it becomes composition_of_c for free.)
    if (_native.HAS_NATIVE and _native.LIB is not None
            and hasattr(_native.LIB, "srmech_hamming_syndrome")):
        code_arr = (ctypes.c_uint8 * big)(*code)
        out_pos = ctypes.c_int()
        rc = _native.LIB.srmech_hamming_syndrome(code_arr, big, ctypes.byref(out_pos))
        if rc == _native.SRMECH_OK:
            return int(out_pos.value)
    syn = 0
    for i in range(n):
        p = 1 << i
        s = 0
        for j in range(1, big + 1):
            if (j & p) != 0:
                s ^= code[j - 1]
        if s:
            syn |= p
    return syn


def hamming_decode_correct(codeword: Sequence[int]) -> Dict[str, Any]:
    """Locate + correct any single-bit error and recover the data payload.

    Returns a dict ``{"data", "error_position", "corrected_codeword"}``:
    ``data`` is the ``k`` recovered data bits, ``error_position`` is the
    1-indexed flipped position (``0`` if clean), ``corrected_codeword`` is the
    repaired ``2ⁿ−1``-bit codeword. Single-error-correcting (distance 3): a
    clean or single-error word recovers exactly; a double error is beyond the
    code's distance and mis-corrects (as every distance-3 code does).
    """
    code = _as_bits(codeword, "codeword")
    n = _infer_n(len(code))
    syn = hamming_syndrome(code)
    corrected = list(code)
    if 1 <= syn <= len(corrected):
        corrected[syn - 1] ^= 1   # Class K sign-flip at the located slot (GF(2))
    data = [corrected[j - 1] for j in _data_positions(n)]
    return {"data": data, "error_position": syn, "corrected_codeword": corrected}
