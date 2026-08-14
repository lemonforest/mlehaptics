"""srmech.math.modular_linalg — Class I modular linear algebra over GF(p).

The swell-free core of the CRT-QMat re-fibration arc (srmech 0.9.0rc44, rung 1).
The exact-ℚ :class:`~srmech.math.qmat.QMat` Gauss-Jordan (rc40) reserves a
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
:func:`srmech.math.cyclic.mod_inv` / :func:`~srmech.math.cyclic.mod_mul` /
:func:`~srmech.math.cyclic.mod_add` over residues already reduced into ``[0, p)``.
Sign/zero handling is **Class K** — every decision is a compare-to-0 over those
non-negative residues; there is no ``abs()`` anywhere, no float, no numpy, no
``math``.

The ``p < 2**31`` bound is load-bearing: with ``2 <= p < 2**31`` every ``a * b``
fits a 64-bit unsigned intermediate, so the native kernel's modular multiply
needs no russian-peasant doubling — a single 64-bit multiply-then-reduce. This is
exactly the int64 matrix that contrasts the dense-ℚ path's GB-scale arena.

**Characteristic 2 (srmech 0.9.0rc350, task `#T1003`).** The lower bound was
``2 < p`` from rc44 to rc349 and the message read "odd prime". That was not a
scope decision about fields — the rc44 C peer inverted a pivot by **Fermat**
(``a**(p-2) mod p``) and its own comment gave the reason as "so ``a*b`` fits
uint64 *and Fermat inversion is valid*". rc49 replaced that private power with
the extended-Euclidean :func:`~srmech.math.cyclic.mod_inv`, which dissolved the
Fermat half of the rationale; the bound was simply never revisited. Only the
**ceiling** was ever justified by the arithmetic domain. GF(2) is a field, and
:func:`gf_rref` is now defined on it: the pivot inverse is ``1⁻¹ = 1``, the row
operation is XOR, and the pure body measured **byte-identical to an independent
XOR-only oracle on 2100 random matrices before any code changed** — the
algorithm never carried an odd-``p`` assumption, only the guard did.

GF(2) is not a corner case here: it is the **grading field of every
Cayley–Dickson rung srmech ships**. ``cascade.cayley_dickson.cd_basis_product``
sends ``e_i · e_j`` to index ``i ⊕ j`` at every dim in ``CD_DIMS``, so the index
lane of ℂ / ℍ / 𝕆 / 𝕊 / … *is* ``(ℤ/2)^d`` and questions about it are GF(2)
linear algebra. See ``tests/test_gf2_modular_linalg_rc350.py``, which solves the
sedenion zero-divisor support condition ``i ⊕ j = k ⊕ l`` as an affine GF(2)
system through this op — a combinatorial construction where sampling cannot
work, zero divisors being measure-zero in 𝕊.

The same op decides the CD sign cocycle itself: ``δt = ε`` is inconsistent at
every rung (``rank([A|b]) = rank(A) + 1``, with ``nullity(A) = log2(dim)`` — the
GF(2)-linear functionals), which is what makes the sign cohomological rather
than a relabelling — see ``cascade/cd_register.py``.

C peer: ``srmech_gf_rref`` (``c/src/srmech_modular_linalg.c``) — an in-place
int64/uint64 GF(p) RREF, caller-arena (no malloc), JPL-clean. :func:`gf_rref`
routes through it when ``HAS_NATIVE``
(:func:`srmech._native.has_native_gf_rref`); the pure-Python body here is the
COMPLETE alternative (and the byte-identical parity oracle): both emit the same
reduced matrix + rank + pivot list at every shape.
"""

from __future__ import annotations

import ctypes
from typing import Dict, List

from .. import _native
from .cyclic import mod_add as _mod_add
from .cyclic import mod_inv as _mod_inv
from .cyclic import mod_mul as _mod_mul

__all__ = ["gf_rref", "gf_solve", "gf_nullspace", "crt_combine"]

# Field bound: 2 < p < 2**31 keeps a*b inside uint64 with no doubling needed.
_P_CEILING: int = 1 << 31


def _check_field(p: int, who: str = "gf_rref") -> None:
    if not isinstance(p, int) or isinstance(p, bool):
        raise TypeError(f"{who}: p must be int; got {type(p).__name__}")
    if p < 2 or p >= _P_CEILING:
        raise ValueError(
            f"{who}: p must be a prime with 2 <= p < 2**31; got {p}"
        )


def _check_rows(rows, who: str = "gf_rref") -> tuple[int, int]:
    if not isinstance(rows, (list, tuple)):
        raise TypeError(f"{who}: rows must be a list of lists of int")
    n_rows = len(rows)
    if n_rows == 0:
        return 0, 0
    n_cols = len(rows[0])
    for r in rows:
        if not isinstance(r, (list, tuple)):
            raise TypeError(f"{who}: each row must be a list of int")
        if len(r) != n_cols:
            raise ValueError(f"{who}: all rows must have equal length")
        for v in r:
            if not isinstance(v, int) or isinstance(v, bool):
                raise TypeError(f"{who}: every entry must be int")
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
    negative — they are reduced into ``[0, p)`` first). ``p`` must be a
    **prime** with ``2 <= p < 2**31`` (the arithmetic-domain bound; primality is
    the caller's contract). ``p = 2`` is in domain as of rc350 (task `#T1003`):
    characteristic 2 needs no division (``1⁻¹ = 1``) and the row operation is
    XOR, so it is the *easy* end of the field range, not an excluded one — the
    module docstring records why the old bound said "odd".

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
# Class I — the two READS the RREF was always for (rc360, task `#T1024`).
#
# ``gf_rref`` shipped the elimination and stopped there, so every caller that
# wanted the two things one actually asks a linear system — "is it solvable,
# and what is a solution" and "what is the kernel" — did the back-substitution
# by hand. In-tree that hand-rolling is not hypothetical: the CD sign-cocycle
# question ``δt = ε`` is decided by rank comparison at every rung, and the
# GF(2) support condition ``i ⊕ j = k ⊕ l`` for the sedenion zero divisors is
# an affine GF(2) system. Both are these two ops.
#
# Both are pure composition over the c_dispatched ``gf_rref`` + the Class-I
# ``mod_*`` primitives — NO new C symbol, and no kernel that is not already in
# ``libsrmech``: the augmentation is a concatenation, the consistency decision
# is "is there a pivot in the last column", and the particular / kernel vectors
# are reads off the reduced matrix. That is why they are ``composition_of_c``
# and not a new C rung.
# ──────────────────────────────────────────────────────────────────────────


def gf_nullspace(A, p: int) -> List[List[int]]:
    """A basis of the kernel ``{x : A·x ≡ 0 (mod p)}`` over GF(p).

    ``A`` is a list of equal-length lists of ``int`` (entries may be negative —
    they are reduced into ``[0, p)`` first); ``p`` is a **prime** with
    ``2 <= p < 2**31`` (the arithmetic-domain bound; primality is the caller's
    contract, exactly as for :func:`gf_rref`).

    Returns the CLASSICAL free-variable basis, in ascending free-column order:
    one vector per non-pivot column, carrying ``1`` in that column and
    ``(-rref[r][free]) mod p`` in the pivot column of each pivot row ``r``.
    The list has exactly ``n_cols - rank(A)`` entries — empty iff ``A`` has
    full column rank. Every entry of every vector is in ``[0, p)``.

    This is the SAME construction :func:`srmech.cascade.cayley_dickson.
    left_mult_kernel` uses over exact ℚ (leading-1 RREF, free variables set to
    a unit column), taken over GF(p) instead — so the two are directly
    comparable on an integer system, which is what makes the cross-field
    differential a real check and not a tautology.

    Class I over the ``c_dispatched`` :func:`gf_rref`; Class-K compare-to-0
    sign handling (never ``abs()``). Exact ints, bounded machine-int
    arithmetic, no float, no numpy, no ``fractions``. ``composition_of_c`` —
    no new C symbol.
    """
    _check_field(p, "gf_nullspace")
    n_rows, n_cols = _check_rows(A, "gf_nullspace")
    if n_rows == 0 or n_cols == 0:
        return []
    red = gf_rref(A, p)
    rref = red["rref"]
    pivots = red["pivots"]
    pivot_set = set(pivots)
    basis: List[List[int]] = []
    for free in range(n_cols):
        if free in pivot_set:
            continue
        vec = [0] * n_cols
        vec[free] = 1 % p
        for r, pc in enumerate(pivots):
            # −rref[r][free] (mod p) == (p − v) mod p; Class-K compare-to-0,
            # no abs(), and the residue never leaves [0, p).
            v = rref[r][free]
            vec[pc] = 0 if v == 0 else p - v
        basis.append(vec)
    return basis


def gf_solve(A, b, p: int) -> Dict[str, object]:
    """Solve ``A·x ≡ b (mod p)`` over GF(p) — the FULL solution set.

    ``A`` is a list of equal-length lists of ``int``; ``b`` is a list of
    ``int`` with ``len(b) == len(A)``; ``p`` is a **prime** with
    ``2 <= p < 2**31``.

    Returns::

        {"consistent": bool,          # rank([A|b]) == rank(A)
         "particular": list[int]|None, # one solution, or None when inconsistent
         "nullspace": list[list[int]], # kernel basis (ALWAYS returned)
         "rank": int}                  # rank(A) — NOT rank([A|b])

    The full solution set is ``particular + span(nullspace)``, so
    ``len(nullspace) == n_cols - rank`` counts the free directions and the
    system has a UNIQUE solution iff ``consistent`` and ``nullspace == []``.
    ``rank`` is always ``rank(A)``; ``rank([A|b])`` is ``rank`` when consistent
    and ``rank + 1`` when not — that ONE-step gap IS the inconsistency, and
    returning ``rank(A)`` keeps the number comparable between the two cases.

    **The nullspace is returned even when the system is inconsistent.** That is
    deliberate: an inconsistent system still has a kernel, and the cohomology
    reads that motivate this op (a coboundary equation ``δt = ε`` that is
    inconsistent at every Cayley–Dickson rung) need the rank pair AND the
    kernel dimension from the same call.

    **Worked regression fixture — STATE THE MATRIX ENCODING.** For the CD sign
    cocycle ``δt = ε`` over GF(2), ``consistent`` is ``False`` at every rung and
    ``rank(A) / rank([A|b])`` runs::

        dim                          2     4     8    16     32     64
        keeping column t(e₀)        1/2   2/3   5/6  12/13  27/28  58/59
        eliminating t(e₀)           0/1   1/2   4/5  11/12  26/27  57/58
        nullity(A)                   1     2     3     4      5      6

    ⚠️ **This is an ENCODING difference, NOT a gauge choice** — ``t(e₀) = 0`` is
    a THEOREM of the system, not a convention imposed on it: ``e₀·e₀ = +e₀``, so
    the ``(i, j) = (0, 0)`` row IS literally ``t(e₀) = 0``, and adding it as an
    extra constraint changes no rank. Substituting it and dropping column 0
    removes that redundant row with it, which is why both ranks shift down by
    exactly one. Same system, same conclusion, different matrix; see
    :mod:`srmech.cascade.cd_register` for the full statement.

    The INVARIANT worth quoting is ``nullity(A) = log2(dim)`` — the homogeneous
    solutions are precisely the GF(2)-LINEAR functionals, so
    ``rank(A) = dim - log2(dim)`` in closed form and the rank pair is the
    frame-relative shadow of it. The ``+1`` defect that carries the conclusion
    (the cocycle is not a coboundary — the CD sign is cohomological, not a
    relabelling) is invariant under both encodings.

    Class I over the ``c_dispatched`` :func:`gf_rref` (the augmented matrix is
    eliminated ONCE — ``rank(A)`` is the count of pivots landing left of the
    augmented column, so no second elimination is needed to compare the two
    ranks) plus :func:`gf_nullspace`. Class-K compare-to-0 sign handling, never
    ``abs()``. Exact ints, no float, no numpy, no ``fractions``.
    ``composition_of_c`` — no new C symbol.
    """
    _check_field(p, "gf_solve")
    n_rows, n_cols = _check_rows(A, "gf_solve")
    if not isinstance(b, (list, tuple)):
        raise TypeError("gf_solve: b must be a list of int")
    if len(b) != n_rows:
        raise ValueError(
            f"gf_solve: b must have one entry per row of A; got {len(b)} "
            f"for {n_rows} row(s)")
    for v in b:
        if not isinstance(v, int) or isinstance(v, bool):
            raise TypeError("gf_solve: every entry of b must be int")

    nullspace = gf_nullspace(A, p)
    if n_rows == 0:
        return {"consistent": True, "particular": [], "nullspace": nullspace,
                "rank": 0}

    aug = [list(A[r]) + [b[r]] for r in range(n_rows)]
    red = gf_rref(aug, p)
    pivots = red["pivots"]
    # A pivot in the augmented column is the inconsistency, and it can only be
    # the LAST pivot (RREF pivots ascend), so this comparison is exact.
    rank_a = sum(1 for c in pivots if c < n_cols)
    consistent = (rank_a == len(pivots))
    if not consistent:
        return {"consistent": False, "particular": None,
                "nullspace": nullspace, "rank": rank_a}
    particular = [0] * n_cols
    for r, pc in enumerate(pivots):
        particular[pc] = red["rref"][r][n_cols]
    return {"consistent": True, "particular": particular,
            "nullspace": nullspace, "rank": rank_a}


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
    :func:`~srmech.math.cyclic.mod_mul`. The combined modulus exceeds 64 bits
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
