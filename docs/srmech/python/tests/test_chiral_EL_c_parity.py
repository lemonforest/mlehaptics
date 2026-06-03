"""Parity tests for the rc17 C-transpiled chiral primitives (Classes E + L).

v0.7.0rc17 ships native C peers for the last two rc12 chiral operations
that still ran Python-only:

  - ``naming.reverse_order``          — Class E harmonic-2 catalog mirror.
  - ``laplacian.three_fold_eigvec_groups`` — Class L harmonic-3 band split.

``reverse_order`` now dispatches to ``srmech_reverse_order`` (a reversed
index permutation) and ``three_fold_eigvec_groups`` to
``srmech_three_fold_bands`` (the low/mid/high band sizing) when the
native lib loaded, falling back to the pure-Python reference otherwise.

These tests force BOTH paths — once with ``_native.HAS_NATIVE`` as-is
(native if present) and once with it monkeypatched to ``False`` (pure
Python) — and assert byte-exact / shape-exact agreement, plus agreement
with the reference definition. The ``HAS_NATIVE`` toggle is wrapped in
``try``/``finally`` to restore the original flag. Discipline mirrors
``test_chiral_c_parity.py`` (rc16).
"""

from __future__ import annotations

import random

import numpy as np

from srmech.amsc import laplacian, naming, _native


_SEED = 20260602


# ---------------------------------------------------------------------
# Toggle helper: run a callable with native on (as-is) and forced off.
# ---------------------------------------------------------------------

def _both_paths(fn):
    """Return (native_result, python_result) for a zero-arg callable.

    ``native_result`` uses ``_native.HAS_NATIVE`` as it loaded (native
    when the lib is present); ``python_result`` forces the pure-Python
    fallback by temporarily setting ``HAS_NATIVE = False``. The flag is
    always restored.
    """
    native_result = fn()
    saved = _native.HAS_NATIVE
    try:
        _native.HAS_NATIVE = False
        python_result = fn()
    finally:
        _native.HAS_NATIVE = saved
    return native_result, python_result


def _rand_pairs(rng, n):
    pairs = []
    for _ in range(n):
        klen = rng.randrange(0, 8)
        vlen = rng.randrange(0, 8)
        k = bytes(rng.randrange(0, 256) for _ in range(klen))
        v = bytes(rng.randrange(0, 256) for _ in range(vlen))
        pairs.append((k, v))
    return pairs


# ---------------------------------------------------------------------
# Class E — reverse_order
# ---------------------------------------------------------------------

def test_reverse_order_empty_and_singleton():
    for pairs in ([], [(b"a", b"1")]):
        native, python = _both_paths(lambda p=pairs: naming.reverse_order(p))
        assert native == list(pairs)[::-1]
        assert python == list(pairs)[::-1]
        assert native == python


def test_reverse_order_random_sweep():
    rng = random.Random(_SEED)
    for _ in range(300):
        n = rng.randrange(0, 32)
        pairs = _rand_pairs(rng, n)
        native, python = _both_paths(lambda p=pairs: naming.reverse_order(p))
        expected = list(pairs)[::-1]
        assert native == expected
        assert python == expected
        assert native == python


def test_reverse_order_involution():
    rng = random.Random(_SEED + 1)
    for _ in range(100):
        n = rng.randrange(0, 20)
        pairs = _rand_pairs(rng, n)
        once = naming.reverse_order(pairs)
        twice = naming.reverse_order(once)
        assert twice == list(pairs)
        # Also force the pure-Python path through the same involution.
        saved = _native.HAS_NATIVE
        try:
            _native.HAS_NATIVE = False
            twice_py = naming.reverse_order(naming.reverse_order(pairs))
        finally:
            _native.HAS_NATIVE = saved
        assert twice_py == list(pairs)


# ---------------------------------------------------------------------
# Class L — three_fold_eigvec_groups
# ---------------------------------------------------------------------

def _band_shapes(d):
    return (
        d["low"].shape[1] if d["low"].ndim == 2 else 0,
        d["mid"].shape[1] if d["mid"].ndim == 2 else 0,
        d["high"].shape[1] if d["high"].ndim == 2 else 0,
    )


def test_three_fold_eigvec_groups_sweep():
    rng = np.random.default_rng(_SEED)
    for n in (1, 2, 3, 4, 5, 8, 16, 17):
        A = rng.standard_normal((n, n))
        L = A + A.T
        native, python = _both_paths(
            lambda L=L: laplacian.three_fold_eigvec_groups(L)
        )
        nat_shapes = _band_shapes(native)
        py_shapes = _band_shapes(python)
        assert nat_shapes == py_shapes, (n, nat_shapes, py_shapes)
        low, mid, high = nat_shapes
        assert low + mid + high == n, (n, nat_shapes)
        assert low <= mid <= high, (n, nat_shapes)
