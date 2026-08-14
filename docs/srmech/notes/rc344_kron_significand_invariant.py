#!/usr/bin/env python3
"""rc344 / task T973 — GENERATING SCRIPT for the ``kron`` significand invariant.

Computational-provenance discipline: the significand-width invariant is a
load-bearing number, so the code that derives it is committed alongside the
claim it supports.

THE CLAIM UNDER TEST
--------------------
Through rc343, ``srmech.amsc.cascade.spectral_cascades.kron`` documented itself
as BYTE-IDENTICAL to the exact-integer parity oracle ``_kron_ref``
(``tests/test_residue_c_rc155.py``) for integer / Gaussian-integer input. The
oracle multiplies ``a[i][j] * b[k][ell]`` in native Python integer arithmetic —
exact at any magnitude. ``kron`` routed those products through
``laplacian.mat_matmul``, which is ``array('d')``-backed on BOTH its native and
its pure-Python branch. The claim was therefore FALSE in general.

THE MEASURED INVARIANT
----------------------
The governing quantity is **significand width**, NOT operand scale::

    "kron is exact"  ==  "every entrywise product is float64-representable"

An integer ``n`` is float64-representable iff, writing ``n = m · 2^e`` with ``m``
odd, ``m`` has at most 53 bits. So a HUGE product with a SHORT significand is
exact, while a much smaller product with a 54-bit significand is not. Two
framings that this script REFUTES:

  * "goes wrong at operand scale 2**28"  — refuted: 401-bit operands are exact.
  * "goes wrong at 2**53 on the product" — closer, but still wrong: a 806-bit
    product is exact when its significand is 6 bits.

Run against a PRE-rc344 tree to reproduce the defect; against rc344+ every case
is exact because the op was fixed (an exact ℤ cascade for integer input), not
because the claim was weakened.

Usage::

    cd docs/srmech/python && PYTHONPATH=$PWD python3 ../notes/rc344_kron_significand_invariant.py
"""
from __future__ import annotations

import os
import sys

# Resolve the sibling ``python/`` source tree and put it FIRST on sys.path. A
# stale namespace-package ``srmech`` in site-packages otherwise shadows the tree
# under test when this file is run as a script (sys.path[0] becomes notes/, not
# the package root) — the documented namespace-shadowing trap. Pinning the path
# here keeps the script runnable from any cwd, which a provenance artefact must be.
_PKG_ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), os.pardir, "python")
sys.path.insert(0, os.path.normpath(_PKG_ROOT))

from srmech.amsc.cascade.spectral_cascades import kron  # noqa: E402


def kron_ref(a, b):
    """The exact-integer parity oracle, verbatim from tests/test_residue_c_rc155.py."""
    ma, na = len(a), len(a[0])
    mb, nb = len(b), len(b[0])
    out = [[0 for _ in range(na * nb)] for _ in range(ma * mb)]
    for i in range(ma):
        for j in range(na):
            for k in range(mb):
                for ell in range(nb):
                    out[i * mb + k][j * nb + ell] = a[i][j] * b[k][ell]
    return out


def significand_bits(n: int) -> int:
    """Width of ``n``'s odd part — the quantity float64 caps at 53.

    Class-K sign branch, never ``abs()`` (cascade-honesty discipline).
    """
    n = -n if n < 0 else n
    if n == 0:
        return 0
    while n % 2 == 0:
        n //= 2
    return n.bit_length()


def float64_representable(n: int) -> bool:
    """An integer is exactly float64-representable iff its odd part fits in 53 bits."""
    return significand_bits(n) <= 53


def eq_exact(got, want) -> bool:
    """Compare WITHOUT rounding either side through float64.

    ``complex(got) == complex(want)`` — the comparison the rc343 ratchet used —
    coerces the exact oracle value into float64 and so can never observe the
    loss. Python's int-vs-float comparison is exact, so comparing components
    directly keeps the evidence.
    """
    gr = got.real if hasattr(got, "real") else got
    gi = got.imag if hasattr(got, "imag") else 0
    wr = want.real if hasattr(want, "real") else want
    wi = want.imag if hasattr(want, "imag") else 0
    return gr == wr and gi == wi


def _int_parts(p):
    """The integer component(s) of an oracle product (real → 1, Gaussian → 2)."""
    if isinstance(p, int):
        return [p]
    pr, pi = p.real, p.imag
    out = []
    for c in (pr, pi):
        ic = int(c)
        if ic == c:
            out.append(ic)
    return out


def probe(label, a, b):
    got = kron(a, b)
    want = kron_ref(a, b)
    prods = [want[i][j] for i in range(len(want)) for j in range(len(want[0]))]
    parts = [c for p in prods for c in _int_parts(p)]
    widths = [significand_bits(c) for c in parts] or [0]
    bits = [c.bit_length() for c in parts] or [0]
    exact = all(eq_exact(g, w)
                for grow, wrow in zip(got, want) for g, w in zip(grow, wrow))
    predicted = all(float64_representable(c) for c in parts)
    print(f"  {label:34s} max_prod_bits={max(bits):4d} "
          f"max_significand={max(widths):3d} f64_repr={predicted!s:5s} "
          f"exact={exact!s:5s} {'OK' if exact == predicted or exact else 'MISMATCH'}")
    return exact, predicted


def main() -> int:
    big = 1 << 400
    odd = (1 << 31) + 1
    half = 3002399751580331          # 3 * half == 2**53 + 1

    print(__doc__.split("Usage")[0].strip()[:0] or "", end="")
    print("rc344 / T973 — kron exactness vs float64 significand width")
    print("=" * 78)
    print("\n[A] INSIDE the float64 significand band (the only regime rc343 tested):")
    cases_in = [
        ("small_int", [[1, 2], [3, 4]], [[0, 5], [6, 7]]),
        ("gaussian_small", [[1 + 1j, 2], [0, -1j]], [[1, 0], [0, 1]]),
        ("806bit_product_sig6", [[7 * big]], [[9 * big]]),
    ]
    print("\n[B] OUTSIDE it — significand > 53 (invisible to the rc343 ratchet):")
    cases_out = [
        ("2**53+1_significand_54", [[3]], [[half]]),
        ("odd_square_significand_63", [[odd]], [[odd]]),
    ]

    results = []
    print("\n  --- [A] ---")
    for label, a, b in cases_in:
        results.append((label, *probe(label, a, b)))
    print("\n  --- [B] ---")
    for label, a, b in cases_out:
        results.append((label, *probe(label, a, b)))

    print("\n" + "=" * 78)
    print("INVARIANT: 'kron exact' == 'every entrywise product is float64-representable'")
    print("  Refuted framing 'operand scale 2**28': the 806-bit-product case uses")
    print("  401-bit OPERANDS and is exact — because its significand is 6 bits.")
    print("  Refuted framing 'product exceeds 2**53': same case, 806-bit product, exact.")

    n_exact = sum(1 for _, e, _ in results if e)
    print(f"\nRESULT on this tree: {n_exact}/{len(results)} cases exact.")
    if n_exact == len(results):
        print("  -> ALL exact: this is an rc344+ tree (kron runs the exact ℤ cascade).")
    else:
        print("  -> Some INEXACT: this is a PRE-rc344 tree; the defect reproduces.")
        for label, e, pred in results:
            if not e:
                print(f"     REPRODUCED: {label} (float64_representable={pred})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
