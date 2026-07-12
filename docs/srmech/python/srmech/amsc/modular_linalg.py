"""srmech.amsc.modular_linalg — Class I modular linear algebra over GF(p).

The swell-free core of the CRT-QMat re-fibration arc (srmech 0.9.0rc44, rung 1).
The exact-ℚ :class:`~srmech.amsc.qmat.QMat` Gauss-Jordan (rc40) reserves a
malloc-free arena sized by the **Hadamard worst-case fraction envelope** — on the
order-2 Franel Zeilberger system that is ~1.5 GB for a 17-bit answer (a ~369:1
over-reservation), because exact-rational elimination grows the numerators and
denominators at every pivot. The fix is to re-fibrate the dense solve onto **CRT**:
solve mod several machine-int primes (each a bounded GF(p) elimination with **zero
coefficient swell**), CRT-combine, rational-reconstruct once. This module is the
bottom of that stack — :func:`gf_rref`, reduced row-echelon form over the finite
field GF(p), in **bounded machine-int arithmetic only** (no fraction growth, no
bignum — that bound is the whole point).

:func:`gf_rref` is Class I: it composes the cyclic-group modular primitives
:func:`srmech.amsc.cyclic.mod_inv` / :func:`~srmech.amsc.cyclic.mod_mul` /
:func:`~srmech.amsc.cyclic.mod_add` over residues already reduced into ``[0, p)``.
Sign/zero handling is **Class K** — every decision is a compare-to-0 over those
non-negative residues; there is no ``abs()`` anywhere, no float, no numpy, no
``math``.

The ``p < 2**31`` bound is load-bearing: with ``2 < p < 2**31`` every ``a * b``
fits a 64-bit unsigned intermediate, so the native kernel's modular multiply
needs no russian-peasant doubling — a single 64-bit multiply-then-reduce. This is
exactly the int64 matrix that contrasts the dense-ℚ path's GB-scale arena.

C peer: ``srmech_gf_rref`` (``c/src/srmech_modular_linalg.c``) — an in-place
int64/uint64 GF(p) RREF, caller-arena (no malloc), JPL-clean. :func:`gf_rref`
routes through it when ``HAS_NATIVE``
(:func:`srmech.amsc._native.has_native_gf_rref`); the pure-Python body here is the
COMPLETE alternative (and the byte-identical parity oracle): both emit the same
reduced matrix + rank + pivot list at every shape.
"""

from __future__ import annotations

import ctypes
from typing import Dict, List

from . import _native
from .cyclic import mod_add as _mod_add
from .cyclic import mod_inv as _mod_inv
from .cyclic import mod_mul as _mod_mul

__all__ = ["gf_rref", "crt_combine"]

# Field bound: 2 < p < 2**31 keeps a*b inside uint64 with no doubling needed.
_P_CEILING: int = 1 << 31


def _check_field(p: int) -> None:
    if not isinstance(p, int) or isinstance(p, bool):
        raise TypeError(f"gf_rref: p must be int; got {type(p).__name__}")
    if p <= 2 or p >= _P_CEILING:
        raise ValueError(
            f"gf_rref: p must be an odd prime with 2 < p < 2**31; got {p}"
        )


def _check_rows(rows) -> tuple[int, int]:
    if not isinstance(rows, (list, tuple)):
        raise TypeError("gf_rref: rows must be a list of lists of int")
    n_rows = len(rows)
    if n_rows == 0:
        return 0, 0
    n_cols = len(rows[0])
    for r in rows:
        if not isinstance(r, (list, tuple)):
            raise TypeError("gf_rref: each row must be a list of int")
        if len(r) != n_cols:
            raise ValueError("gf_rref: all rows must have equal length")
        for v in r:
            if not isinstance(v, int) or isinstance(v, bool):
                raise TypeError("gf_rref: every entry must be int")
    return n_rows, n_cols


def _gf_rref_c(flat: List[int], n_rows: int, n_cols: int, p: int):
    """Native GF(p) RREF over a row-major int64 buffer → (rref_flat, pivots,
    rank), or ``None`` if the native symbol is absent / an entry is out of the
    int64 domain (the pure-Python body is the complete fallback)."""
    if not _native.has_native_gf_rref():
        return None
    _i64_min, _i64_max = -(1 << 63), (1 << 63) - 1
    for v in flat:
        if v < _i64_min or v > _i64_max:
            return None
    n = max(n_rows * n_cols, 1)
    buf = (ctypes.c_int64 * n)(*(flat if flat else [0]))
    n_piv = max(min(n_rows, n_cols), 1)
    pivots = (ctypes.c_uint32 * n_piv)()
    rank = ctypes.c_uint32(0)
    rc = _native.LIB.srmech_gf_rref(
        buf,
        ctypes.c_uint32(n_rows),
        ctypes.c_uint32(n_cols),
        ctypes.c_uint64(p),
        pivots,
        ctypes.byref(rank),
    )
    if rc != _native.SRMECH_OK:
        raise RuntimeError(f"srmech_gf_rref returned non-OK status {rc}")
    rk = int(rank.value)
    out_flat = [int(buf[i]) for i in range(n_rows * n_cols)]
    out_pivots = [int(pivots[i]) for i in range(rk)]
    return out_flat, out_pivots, rk


def _gf_rref_pure(rows, n_rows: int, n_cols: int, p: int):
    """Pure-Python GF(p) RREF composing the Class-I modular primitives. Returns
    (matrix, pivots, rank). Mirrors the C kernel exactly (same pivot search,
    same Class-K compare-to-0, same full reduced-echelon back-elimination)."""
    # Canonicalise every entry into [0, p) (true modulo; handles negatives).
    m: List[List[int]] = [[v % p for v in row] for row in rows]
    pivots: List[int] = []
    pivot_row = 0
    for col in range(n_cols):
        if pivot_row >= n_rows:
            break
        # Find a nonzero entry in this column at or below pivot_row (Class K).
        sel = None
        for r in range(pivot_row, n_rows):
            if m[r][col] != 0:
                sel = r
                break
        if sel is None:
            continue                            # free column, no pivot here
        if sel != pivot_row:
            m[pivot_row], m[sel] = m[sel], m[pivot_row]
        # Normalise the pivot row so its leading entry is 1.
        inv = _mod_inv(m[pivot_row][col], p)
        m[pivot_row] = [_mod_mul(v, inv, p) for v in m[pivot_row]]
        # Eliminate this column from every other row (reduced echelon).
        for r in range(n_rows):
            if r == pivot_row:
                continue
            factor = m[r][col]
            if factor == 0:
                continue
            prow = m[pivot_row]
            row_r = m[r]
            for c in range(n_cols):
                sub = _mod_mul(prow[c], factor, p)
                # row_r[c] - sub (mod p) == row_r[c] + (p - sub) (mod p).
                row_r[c] = _mod_add(row_r[c], p - sub, p)
        pivots.append(col)
        pivot_row += 1
    return m, pivots, pivot_row


def gf_rref(rows, p: int) -> Dict[str, object]:
    """Reduced row-echelon form of the integer matrix ``rows`` over GF(p).

    ``rows`` is a list of equal-length lists of ``int`` (entries may be
    negative — they are reduced into ``[0, p)`` first). ``p`` must be an **odd
    prime** with ``2 < p < 2**31`` (the arithmetic-domain bound; primality is
    the caller's contract).

    Returns ``{"rref": [[int]], "rank": int, "pivots": [int]}`` — the reduced
    matrix with every entry in ``[0, p)``, the rank (number of pivots), and the
    pivot column of each pivot row in ascending order.

    Class I (modular linear algebra) composing the cyclic-group primitives;
    Class-K sign/zero handling (compare-to-0, never ``abs()``). Bounded
    machine-int arithmetic — no fraction growth, no bignum. Dispatches to the
    native ``srmech_gf_rref`` when present; the pure-Python body is the complete,
    byte-identical alternative.
    """
    _check_field(p)
    n_rows, n_cols = _check_rows(rows)
    if n_rows == 0 or n_cols == 0:
        return {"rref": [list(r) for r in rows], "rank": 0, "pivots": []}

    flat: List[int] = [v for row in rows for v in row]
    native = _gf_rref_c(flat, n_rows, n_cols, p)
    if native is not None:
        out_flat, pivots, rank = native
        rref = [out_flat[r * n_cols:(r + 1) * n_cols] for r in range(n_rows)]
        return {"rref": rref, "rank": rank, "pivots": pivots}

    m, pivots, rank = _gf_rref_pure(rows, n_rows, n_cols, p)
    return {"rref": m, "rank": rank, "pivots": pivots}


# ──────────────────────────────────────────────────────────────────────────
# Class I — CRT combine (rc45, rung 2 of the CRT-QMat re-fibration arc).
# ──────────────────────────────────────────────────────────────────────────
# After the swell-free GF(p) elimination has produced one residue per prime,
# the per-prime results are recombined into a single residue modulo the product
# of the primes — the Chinese Remainder Theorem. The combined modulus
# ``∏ m_i`` exceeds 64 bits for k ≳ 3 of the ~31-bit reduction primes, so the
# accumulator is **bignum** (Python ``int``, no ceiling); only the per-step
# inverse ``M_i⁻¹ (mod m_i)`` stays inside ``uint64`` (it is taken modulo a
# single ~31-bit prime), so it rides the Class-I :func:`cyclic.mod_inv`.


def _check_crt_inputs(residues, moduli) -> int:
    """Validate the CRT operand pair and return ``k`` (the prime count).

    ``residues`` / ``moduli`` must be equal-length non-empty lists of ``int``;
    each modulus must be ``>= 2``; the moduli must be **distinct** (the
    pairwise-coprimality the caller contracts comes free for distinct primes,
    and distinctness is the cheap structural check we can make here)."""
    if not isinstance(residues, (list, tuple)):
        raise TypeError("crt_combine: residues must be a list of int")
    if not isinstance(moduli, (list, tuple)):
        raise TypeError("crt_combine: moduli must be a list of int")
    k = len(moduli)
    if len(residues) != k:
        raise ValueError(
            "crt_combine: residues and moduli must have equal length; "
            f"got {len(residues)} and {k}"
        )
    if k == 0:
        raise ValueError("crt_combine: need at least one (residue, modulus)")
    for r in residues:
        if not isinstance(r, int) or isinstance(r, bool):
            raise TypeError("crt_combine: every residue must be int")
    for mod in moduli:
        if not isinstance(mod, int) or isinstance(mod, bool):
            raise TypeError("crt_combine: every modulus must be int")
        if mod < 2:
            raise ValueError(f"crt_combine: every modulus must be >= 2; got {mod}")
    if len(set(moduli)) != k:
        raise ValueError("crt_combine: moduli must be distinct (pairwise coprime)")
    return k


def _crt_combine_pure(residues, moduli):
    """Iterative (Garner) CRT over a bignum accumulator. Returns
    ``(residue, modulus)`` with ``residue`` in ``[0, modulus)`` and
    ``modulus = ∏ moduli``. Mirrors the C kernel exactly (same fold order,
    same per-step inverse modulo a single prime)."""
    # Seed with the first congruence reduced into [0, m_0).
    cur = residues[0] % moduli[0]
    modulus = moduli[0]
    for i in range(1, len(moduli)):
        m_i = moduli[i]
        # Solve cur + modulus*t ≡ r_i (mod m_i): t = (r_i - cur)·modulus⁻¹.
        # `modulus` is bignum; (modulus % m_i) is a ~31-bit residue, so the
        # inverse rides the uint64 Class-I cyclic.mod_inv.
        inv = _mod_inv(modulus % m_i, m_i)
        # (r_i - cur) reduced into [0, m_i) — Class-K sign handling lives in
        # Python's true-modulo %, which is non-negative for a positive modulus.
        diff = (residues[i] - cur) % m_i
        t = _mod_mul(diff, inv, m_i)
        cur = cur + modulus * t
        modulus = modulus * m_i
    return cur % modulus, modulus


def crt_combine(residues, moduli) -> Dict[str, int]:
    """Chinese-Remainder-combine per-prime residues into one residue mod ∏ mᵢ.

    Given ``residues = [r_0, …, r_{k-1}]`` and pairwise-coprime ``moduli =
    [m_0, …, m_{k-1}]`` (distinct primes from the CRT reduction sequence),
    return ``{"residue": int, "modulus": int}`` where ``residue ≡ r_i (mod m_i)``
    for every ``i`` and ``modulus = ∏ m_i``, with ``residue`` in
    ``[0, modulus)``.

    Iterative CRT (Garner's algorithm; cf. Knuth, *TAOCP* vol. 2, §4.3.2;
    von zur Gathen & Gerhard, *Modern Computer Algebra*, 3rd ed. 2013, §5.4),
    composing the Class-I cyclic-group primitives :func:`cyclic.mod_inv` /
    :func:`~srmech.amsc.cyclic.mod_mul`. The combined modulus exceeds 64 bits
    for ``k ≳ 3`` of the ~31-bit reduction primes, so the accumulator is
    **bignum** (Python ``int``, no ceiling); only the per-step inverse, taken
    modulo a single prime, stays inside ``uint64``. Sign/zero handling is
    Class-K (Python's non-negative ``%``, never ``abs()``); no float, no numpy,
    no ``math``.

    Dispatches to the native ``srmech_crt_combine`` (over ``srmech_bigint``)
    when present; the pure-Python body is the complete, byte-identical
    alternative (and the parity oracle).
    """
    k = _check_crt_inputs(residues, moduli)
    res_list = [int(r) for r in residues]
    mod_list = [int(mod) for mod in moduli]

    native = _native.crt_combine(res_list, mod_list)
    if native is not None:
        residue_out, modulus_out = native
        return {"residue": residue_out, "modulus": modulus_out}

    residue_out, modulus_out = _crt_combine_pure(res_list, mod_list)
    assert k >= 1
    return {"residue": residue_out, "modulus": modulus_out}
