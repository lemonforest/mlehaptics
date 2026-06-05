"""Parity tests for the rc16 C-transpiled chiral primitives.

v0.7.0rc16 ships native C peers for the three rc12 chiral operations:

  - ``cyclic.three_cycle``       — Class I harmonic-3 Z/3 generator.
  - ``dispatch.mirror_pattern``  — Class D harmonic-2 byte-reversed needle.
  - ``search.byte_search_backward`` — Class G harmonic-2 last-occurrence.

Each op now dispatches to ``srmech_three_cycle`` / ``srmech_mirror_pattern``
/ ``srmech_byte_search_backward`` when the native lib loaded, falling back
to the pure-Python reference otherwise.

These tests force BOTH paths — once with ``_native.HAS_NATIVE`` as-is
(native if present) and once with it monkeypatched to ``False`` (pure
Python) — and assert byte-exact agreement, plus agreement with the
reference definition. The ``HAS_NATIVE`` toggle is wrapped in
``try``/``finally`` to restore the original flag. Discipline mirrors
``test_cyclic_parity.py`` / ``test_native_sha256.py`` from Task #201
Phase B3.
"""

from __future__ import annotations

import random

from srmech.amsc import cyclic, dispatch, search, _native


_SEED = 20260602


# ---------------------------------------------------------------------
# Toggle helpers: run a callable with native on (as-is) and forced off.
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


# ---------------------------------------------------------------------
# Class I — three_cycle
# ---------------------------------------------------------------------

def test_three_cycle_boundaries():
    boundaries = [0, 1, 2, 3, 2**64 - 1]
    for v in boundaries:
        native, python = _both_paths(lambda v=v: cyclic.three_cycle(v))
        assert native == (v + 1) % 3
        assert python == (v + 1) % 3
        assert native == python


def test_three_cycle_random_sweep():
    rng = random.Random(_SEED)
    for _ in range(500):
        v = rng.randrange(0, 2**64)
        native, python = _both_paths(lambda v=v: cyclic.three_cycle(v))
        assert native == (v + 1) % 3
        assert native == python


def test_three_cycle_period_three():
    rng = random.Random(_SEED + 1)
    for _ in range(200):
        v = rng.randrange(0, 2**64)
        # Three applications return to the value's own residue class.
        once = cyclic.three_cycle(v)
        twice = cyclic.three_cycle(once)
        thrice = cyclic.three_cycle(twice)
        assert thrice == v % 3


# ---------------------------------------------------------------------
# Class D — mirror_pattern
# ---------------------------------------------------------------------

def test_mirror_pattern_fixed_cases():
    cases = [b"", b"a", b"ab", b"abc", b"\x00\x01\x02\x03", b"racecar"]
    for p in cases:
        native, python = _both_paths(lambda p=p: dispatch.mirror_pattern(p))
        assert native == p[::-1]
        assert python == p[::-1]
        assert native == python


def test_mirror_pattern_random_sweep():
    rng = random.Random(_SEED + 2)
    for _ in range(300):
        length = rng.randrange(0, 65)
        p = bytes(rng.randrange(0, 256) for _ in range(length))
        native, python = _both_paths(lambda p=p: dispatch.mirror_pattern(p))
        assert native == p[::-1]
        assert native == python


def test_mirror_pattern_involution():
    rng = random.Random(_SEED + 3)
    for _ in range(300):
        length = rng.randrange(0, 65)
        p = bytes(rng.randrange(0, 256) for _ in range(length))
        # mirror(mirror(p)) == p (period 2) on both paths.
        native, python = _both_paths(
            lambda p=p: dispatch.mirror_pattern(dispatch.mirror_pattern(p))
        )
        assert native == p
        assert python == p
        assert native == python


# ---------------------------------------------------------------------
# Class G — byte_search_backward
# ---------------------------------------------------------------------

def test_byte_search_backward_fixed_cases():
    # (haystack, needle, expected) — empty needle -> len, absent -> None,
    # multi-occurrence -> last (highest) offset wins.
    cases = [
        (b"abcabc", b"", 6),
        (b"", b"", 0),
        (b"abcabc", b"abc", 3),
        (b"abcabc", b"bc", 4),
        (b"abcabc", b"xyz", None),
        (b"abc", b"abcd", None),
        (b"aaaa", b"a", 3),
        (b"aaaa", b"aa", 2),
        (b"a", b"a", 0),
    ]
    for h, n, expected in cases:
        native, python = _both_paths(
            lambda h=h, n=n: search.byte_search_backward(h, n)
        )
        assert native == expected, (h, n, native, expected)
        assert python == expected, (h, n, python, expected)
        assert native == python


def test_byte_search_backward_random_sweep():
    rng = random.Random(_SEED + 4)
    alphabet = b"abc"  # tiny alphabet -> frequent multi-occurrence matches
    for _ in range(400):
        h_len = rng.randrange(0, 40)
        n_len = rng.randrange(0, 6)
        h = bytes(alphabet[rng.randrange(0, len(alphabet))] for _ in range(h_len))
        n = bytes(alphabet[rng.randrange(0, len(alphabet))] for _ in range(n_len))
        native, python = _both_paths(
            lambda h=h, n=n: search.byte_search_backward(h, n)
        )
        ref = h.rfind(n)
        ref_opt = ref if ref >= 0 else None
        assert native == ref_opt, (h, n, native, ref_opt)
        assert native == python


def test_byte_search_backward_empty_needle_returns_len():
    rng = random.Random(_SEED + 5)
    for _ in range(50):
        h_len = rng.randrange(0, 30)
        h = bytes(rng.randrange(0, 256) for _ in range(h_len))
        native, python = _both_paths(
            lambda h=h: search.byte_search_backward(h, b"")
        )
        assert native == len(h)
        assert python == len(h)
        assert native == python
