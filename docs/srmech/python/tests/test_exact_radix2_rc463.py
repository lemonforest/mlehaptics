"""rc463 `#T1188` — the exact negacyclic radix-2 split, and what it does NOT buy.

Two things are gated here, and the second is the interesting one.

**1. Bit-identity.** ``_exact_dft_radix2`` replaced the doubly-nested
``X[k] = Σ_n x_n ζ^{nk mod N}`` loop that ``_exact_dft_core`` carried for the
power-of-two case. That loop lives on below as :func:`_py_reference` — the
reference ORACLE, copied here verbatim so the package holds exactly one
implementation and this file holds the thing it must equal. Bit-identity is
checked over real and Gaussian integers, forward and inverse, at
``N ∈ {2,4,8,16,32,64}``, including entries of ``2**53 + 1`` — a 54-bit
significand, unrepresentable in float64, so a float carrier anywhere in the
cascade shows up as a wrong integer rather than as a rounding smudge.

**2. The complexity claim, MEASURED — and it refutes the obvious hope.** The
brief this work came from expected ``O(N log N)``. It is not reachable, and the
reason is not the algorithm. An ``ExactSpectrum`` at power-of-two ``N`` is ``N``
ring elements of dimension ``N/2``, each an integer ``(real, imag)`` pair:
exactly ``N²`` integers. No procedure emits ``N²`` integers in fewer than ``N²``
writes, so Θ(N²) is the OUTPUT SIZE and no Cooley–Tukey arrangement of twiddles
can go below it. What the split DOES buy is the constant, and it buys all of it
that exists: measured ``N²`` integer additions — exactly one per output
coefficient, the floor — against the old loop's ``2N²``.

srmech ships no timing or benchmark surface, so a wall-clock "O(N log N)" would
be an unmeasurable claim. The instrument here is instead exact and countable: a
counting ``int`` subclass tallies every addition the REAL recursion performs
(not a copy of it), and that tally is asserted against the closed form in
``_radix2_ring_op_count``. The growth gate gets asserted at ``== 4.0`` per
doubling — quadratic — precisely so the docstrings cannot quietly drift back to
claiming ``N log N``, which at these sizes would show ~2.2–2.3.

**Non-vacuity.** Two ways, because an identity test that cannot fail is not a
measurement:

- ``test_oracle_discriminates_on_the_class_k_sign`` mutates the Class-K
  pin-slot sign in the oracle and asserts the shipped core DISAGREES with it.
- Manually, during the build: the ``cr = -cr`` / ``ci = -ci`` Class-C reorient
  inside the shipped ``_exact_dft_radix2`` wrap branch was deleted in place and
  the suite re-run. **Measured**, 14 failed / 56 passed:

  * ``test_bit_identity_against_reference_oracle`` — RED in 9 of its 12 cases.
    The three that stayed green are exactly the three with no wrap to sign:
    ``N = 2`` both directions (the two-point base carries its sign in the
    ``−``, not in a pin branch) and ``N = 4`` FORWARD, where ``q = 2p + k`` is
    ``0`` or ``1`` against ``h = 2`` and never reaches the wrap. ``N = 4``
    INVERSE does wrap — ``q = −k`` at ``k = 1`` — and went red. A blanket
    "green below some N" would have been the wrong reading; the boundary is
    the wrap, not the length.
  * ``test_closed_form_op_count_matches_the_real_recursion`` — RED at all five
    ``N``, through its value assertion, not its count.
  * The op-count and growth tests stayed GREEN, which is the correct shape: a
    sign mutation moves values, not the number of additions.
  * ``test_fft_matches_dft_on_integer_power_of_two`` also stayed GREEN, and
    that is worth writing down — ``fft`` and ``dft`` both run the mutated code,
    so the cross-check is a CONSISTENCY gate between two entry points and never
    a correctness gate on the core. Only the oracle identity is that.

  The mutation was reverted; it is NOT committed, and the package file carries
  the reorient.

No numpy, no ``fractions``, no ``math``, no ``abs()`` — gated below on this file
and on both package files it covers.
"""
from __future__ import annotations

import re as _re
from pathlib import Path
from typing import List, Tuple

import pytest

from srmech.cascade import exact_dft as _edft
from srmech.cascade.exact_dft import (
    ExactSpectrum,
    _exact_dft_core,
    _exact_dft_radix2,
    _radix2_ring_op_count,
    exact_dft,
)
from srmech.cascade.spectral_cascades import dft, fft

POW2 = (2, 4, 8, 16, 32, 64)
COUNT_N = (8, 16, 32, 64, 128)

#: A 54-bit significand. ``float(2**53 + 1) == float(2**53)``, so any float
#: carrier in the cascade collapses this onto its neighbour and the exact
#: spectrum comes out wrong by an integer — a loud failure, not a smudge.
BEYOND_FLOAT53 = 2 ** 53 + 1


# --------------------------------------------------------------------------
# The reference oracle: the doubly-nested loop `_exact_dft_core` carried for
# the power-of-two case before `#T1188`. Copied verbatim so exactly ONE
# implementation ships in the package and the thing it must equal lives here.
# --------------------------------------------------------------------------
def _py_reference(re_: List[int], im: List[int], n: int,
                  inverse: bool) -> ExactSpectrum:
    """``X[k] = Σ_n x_n · ζ^{±nk mod N}`` by direct summation over ``ℤ[ζ_N]``."""
    h = n // 2
    spectrum: ExactSpectrum = []
    for k in range(n):
        xr = [0] * h
        xi = [0] * h
        for idx in range(n):
            j = ((idx * k) % n) if not inverse else ((-idx * k) % n)
            sign = 1
            if j >= h:                    # Class K: ζ^{N/2} = -1 → ζ^j = -ζ^{j-h}
                j -= h
                sign = -1
            xr[j] += sign * re_[idx]
            xi[j] += sign * im[idx]
        spectrum.append((xr, xi))
    return spectrum


def _py_reference_class_k_mutant(re_: List[int], im: List[int], n: int,
                                 inverse: bool) -> ExactSpectrum:
    """:func:`_py_reference` with the Class-K pin-slot sign flip REMOVED.

    The one-token mutation ``sign = -1`` → ``sign = 1``. Exists so the identity
    assertions can be shown to discriminate rather than to hold vacuously.
    """
    h = n // 2
    spectrum: ExactSpectrum = []
    for k in range(n):
        xr = [0] * h
        xi = [0] * h
        for idx in range(n):
            j = ((idx * k) % n) if not inverse else ((-idx * k) % n)
            sign = 1
            if j >= h:
                j -= h
                sign = 1                  # MUTANT: the pin-slot flip, deleted
            xr[j] += sign * re_[idx]
            xi[j] += sign * im[idx]
        spectrum.append((xr, xi))
    return spectrum


# --------------------------------------------------------------------------
# Deterministic integer fixtures. A 3-line LCG rather than `random`, so no
# float-backed generator sits anywhere near a bit-exactness gate.
# --------------------------------------------------------------------------
def _lcg(seed: int, count: int, lo: int, hi: int) -> List[int]:
    span = hi - lo + 1
    out: List[int] = []
    s = seed
    for _ in range(count):
        s = (s * 6364136223846793005 + 1442695040888963407) % (1 << 64)
        out.append(lo + (s >> 17) % span)
    return out


def _signals(n: int) -> List[Tuple[str, List[int], List[int]]]:
    """``(label, real, imag)`` fixtures at length ``n``."""
    cases: List[Tuple[str, List[int], List[int]]] = []
    cases.append(("real_small", _lcg(n * 7 + 1, n, -99, 99), [0] * n))
    cases.append(("gaussian", _lcg(n * 7 + 2, n, -99, 99),
                  _lcg(n * 7 + 3, n, -99, 99)))
    cases.append(("pure_imag", [0] * n, _lcg(n * 7 + 4, n, -99, 99)))
    one_hot_r = [0] * n
    one_hot_r[n - 1] = 1
    cases.append(("one_hot_last", one_hot_r, [0] * n))
    cases.append(("bignum", _lcg(n * 7 + 5, n, -(2 ** 80), 2 ** 80),
                  _lcg(n * 7 + 6, n, -(2 ** 80), 2 ** 80)))
    # 54-bit significand, real AND imaginary, positive AND negative.
    cases.append(("beyond_float53",
                  [BEYOND_FLOAT53 if i % 2 == 0 else -BEYOND_FLOAT53
                   for i in range(n)],
                  [-BEYOND_FLOAT53 if i % 3 == 0 else BEYOND_FLOAT53
                   for i in range(n)]))
    return cases


# --------------------------------------------------------------------------
# The counting int: the instrument for (B).
# --------------------------------------------------------------------------
_TALLY = [0]


class _CountingInt(int):
    """An ``int`` that tallies every ADDITION or SUBTRACTION it takes part in.

    Multiplication and negation deliberately do NOT tally: the ``sign * x`` in
    the oracle and the ``-cr`` Class-C reorient in the split are orientation
    ops, not ring accumulations, and counting them would blur the one number
    this file is about. They still return ``_CountingInt`` so the countedness
    propagates into the accumulate that follows.

    Because this subclasses ``int``, Python gives its reflected slots priority
    over ``int``'s own, so ``0 + counting`` is counted just as
    ``counting + counting`` is — the accumulator starting life as a plain ``0``
    does not create a blind spot.
    """
    __slots__ = ()

    def __add__(self, other):
        _TALLY[0] += 1
        return _CountingInt(int(self) + int(other))

    __radd__ = __add__                    # addition commutes; same tally

    def __sub__(self, other):
        _TALLY[0] += 1
        return _CountingInt(int(self) - int(other))

    def __rsub__(self, other):
        _TALLY[0] += 1
        return _CountingInt(int(other) - int(self))

    def __mul__(self, other):
        return _CountingInt(int(self) * int(other))

    __rmul__ = __mul__

    def __neg__(self):
        return _CountingInt(-int(self))


def _wrap(xs: List[int]) -> List[_CountingInt]:
    return [_CountingInt(v) for v in xs]


def _recount(spectrum: ExactSpectrum) -> ExactSpectrum:
    """Re-wrap every coefficient of a sub-transform result as ``_CountingInt``.

    Load-bearing, and the reason is a blind spot that a first cut of this file
    shipped with. The split allocates its accumulators as ``[0] * h`` — plain
    ``int`` zeros — and the slots that take no contribution at a given bin stay
    plain zeros all the way out. Those propagate upward as sub-transform
    coefficients, and an add whose BOTH operands are plain ``int`` never reaches
    ``_CountingInt``'s slots at all. Measured before this re-wrap: 60 adds at
    N=8 against the true 64, and 228 at N=16 against 256 — an instrument
    quietly reading ~11% low and drifting worse with N, which would have
    "measured" a fictitious sub-quadratic constant. Re-wrapping at the recursion
    boundary makes every operand counted without touching the shipped code or
    changing a single value (``_CountingInt`` is an ``int``, exactly equal).
    """
    return [([_CountingInt(c) for c in xr], [_CountingInt(c) for c in xi])
            for xr, xi in spectrum]


def _count_radix2(n: int) -> Tuple[int, int, int, ExactSpectrum]:
    """Run the REAL ``_exact_dft_radix2`` under instrumentation.

    Returns ``(adds, calls, max_depth, spectrum)``. Depth and call count come
    from temporarily rebinding the module global the recursion resolves through
    at call time — so it is the shipped recursion being measured, not a copy of
    it. ``_exact_dft_radix2`` is called directly rather than via
    ``_exact_dft_core`` so the native int64 probe cannot intercept and leave the
    tally reading a spurious zero.
    """
    src = _lcg(n + 11, n, -99, 99)
    sim = _lcg(n + 12, n, -99, 99)
    real = _edft._exact_dft_radix2
    state = {"calls": 0, "depth": 0, "max": 0}

    def _probe(re_, im, m, *, inverse=False):
        state["calls"] += 1
        state["depth"] += 1
        if state["depth"] > state["max"]:
            state["max"] = state["depth"]
        try:
            return _recount(real(re_, im, m, inverse=inverse))
        finally:
            state["depth"] -= 1

    _TALLY[0] = 0
    _edft._exact_dft_radix2 = _probe
    try:
        spectrum = _probe(_wrap(src), _wrap(sim), n, inverse=False)
    finally:
        _edft._exact_dft_radix2 = real
    return _TALLY[0], state["calls"], state["max"], spectrum


def _count_reference(n: int) -> int:
    """Additions performed by the direct doubly-nested oracle at length ``n``."""
    src = _lcg(n + 11, n, -99, 99)
    sim = _lcg(n + 12, n, -99, 99)
    _TALLY[0] = 0
    _py_reference(_wrap(src), _wrap(sim), n, False)
    return _TALLY[0]


# ==========================================================================
# 1. Bit-identity
# ==========================================================================
@pytest.mark.parametrize("n", POW2)
@pytest.mark.parametrize("inverse", [False, True])
def test_bit_identity_against_reference_oracle(n, inverse):
    """The split equals the doubly-nested loop it replaced, coefficient for
    coefficient, on every fixture — including the 54-bit-significand one."""
    for label, rr, ii in _signals(n):
        got = _exact_dft_core(rr, ii, inverse=inverse)
        want = _py_reference(rr, ii, n, inverse)
        assert got == want, f"N={n} inverse={inverse} fixture={label}"


@pytest.mark.parametrize("n", POW2)
def test_split_is_reached_and_is_the_thing_compared(n):
    """Non-vacuity of the fixture routing: the power-of-two branch really does
    land in ``_exact_dft_radix2`` and really does return an ``N``-bin spectrum
    of dimension ``N/2``, so the identity above is comparing transforms rather
    than two empty lists."""
    rr, ii = _signals(n)[1][1], _signals(n)[1][2]
    spectrum = _exact_dft_radix2(rr, ii, n, inverse=False)
    assert len(spectrum) == n
    for xr, xi in spectrum:
        assert len(xr) == n // 2
        assert len(xi) == n // 2
    assert any(any(c != 0 for c in xr) for xr, _ in spectrum)


def test_beyond_float53_entry_survives_exactly():
    """``2**53 + 1`` is not representable in float64. Bin 0 of the forward
    transform is ``Σ x_n`` in coefficient slot 0, so the exact sum is a direct
    read — if any float carrier existed it would come back short by one."""
    n = 8
    rr = [BEYOND_FLOAT53] * n
    ii = [0] * n
    spectrum = _exact_dft_core(rr, ii, inverse=False)
    assert spectrum[0][0][0] == n * BEYOND_FLOAT53
    assert spectrum[0][0][0] != n * (2 ** 53)      # the float64 collapse
    assert isinstance(spectrum[0][0][0], int)


@pytest.mark.parametrize("n", POW2)
def test_oracle_discriminates_on_the_class_k_sign(n):
    """The identity assertion is a MEASUREMENT, not a tautology: drop the
    Class-K pin-slot sign flip from the oracle and the shipped core stops
    agreeing with it — at EVERY power-of-two length including ``N = 2``.

    ``N = 2`` was written here as an expected-equal exemption on the reasoning
    that the two-point base has no wrap to sign. That reasoning was about the
    SPLIT's base case, and the oracle is not the split: at ``N = 2`` the oracle
    still evaluates ``ζ^{1·1 mod 2}`` with ``j = 1 ≥ h = 1``, wraps, and signs.
    The exemption was wrong and the test said so on the first run.
    """
    rr, ii = _signals(n)[1][1], _signals(n)[1][2]
    got = _exact_dft_core(rr, ii, inverse=False)
    mutant = _py_reference_class_k_mutant(rr, ii, n, False)
    assert got != mutant, f"N={n}: the Class-K mutation changed nothing"


# ==========================================================================
# 2. The fft / dft cross-check contract
# ==========================================================================
@pytest.mark.parametrize("n", POW2)
def test_fft_matches_dft_on_integer_power_of_two(n):
    """Both entry points hand an integer signal to ``_exact_transform`` before
    either butterfly, so on integer input they are not merely equal-valued —
    they run the same code, and the agreement is exact rather than to-round-off."""
    for label, rr, ii in _signals(n):
        sig = [complex(a, b) for a, b in zip(rr, ii)]
        assert fft(sig) == dft(sig), f"N={n} fixture={label} forward"
        assert fft(sig, inverse=True) == dft(sig, inverse=True), \
            f"N={n} fixture={label} inverse"


@pytest.mark.parametrize("n", (3, 5, 6, 7, 9, 10, 12))
def test_fft_matches_dft_on_integer_non_power_of_two(n):
    """The prose fix of `#T1188` in evidence: a non-power-of-two INTEGER signal
    takes the exact general-``Φ_N`` engine, not the float ``cexp`` path, and
    ``exact_dft`` does not raise on it — which is what both docstrings denied."""
    rr = _lcg(n * 13 + 1, n, -40, 40)
    sig = [complex(v, 0) for v in rr]
    assert fft(sig) == dft(sig)
    spectrum = exact_dft(rr)
    assert len(spectrum) == n
    assert all(isinstance(c, int) for xr, _ in spectrum for c in xr)


# ==========================================================================
# 3. The operation-count instrument (B)
# ==========================================================================
@pytest.mark.parametrize("n", COUNT_N)
def test_closed_form_op_count_matches_the_real_recursion(n):
    """The closed form is MEASURED against the running code, not asserted
    beside it: instrument the real ``_exact_dft_radix2`` and require the tally,
    the call count and the nesting depth to land on
    ``_radix2_ring_op_count``'s numbers exactly."""
    adds, calls, depth, spectrum = _count_radix2(n)
    want_adds, want_out, want_depth = _radix2_ring_op_count(n)
    assert adds == want_adds, f"N={n}: measured {adds} adds, closed form {want_adds}"
    assert depth == want_depth
    assert calls == n - 1                 # 1 + 2·calls(n/2), calls(2) = 1
    assert adds > 0                       # the instrument did fire
    # ...and the instrumented run is a REAL transform, not a counting no-op.
    src = _lcg(n + 11, n, -99, 99)
    sim = _lcg(n + 12, n, -99, 99)
    assert spectrum == _py_reference(src, sim, n, False)


@pytest.mark.parametrize("n", COUNT_N)
def test_split_hits_the_output_size_floor_and_the_direct_loop_does_not(n):
    """The whole result in one assertion pair.

    ``output_coefficients`` is ``N`` bins × ``N/2`` basis slots × 2 components
    = ``N²`` integers, and they must all be written. The split performs exactly
    that many additions — one per output coefficient, the information-theoretic
    floor. The doubly-nested loop performs exactly twice that. Reverting the
    core to the old loop turns the first assertion RED.
    """
    adds, _, _, _ = _count_radix2(n)
    _, out_coeffs, _ = _radix2_ring_op_count(n)
    direct = _count_reference(n)

    assert out_coeffs == n * (n // 2) * 2          # the representation's size
    assert adds == out_coeffs                      # exactly one add per coeff
    assert direct == 2 * out_coeffs                # the loop it replaced
    assert adds * 2 == direct                      # strictly below, by 2x


def test_growth_is_quadratic_not_n_log_n():
    """The refutation, gated so the docstrings cannot drift back.

    ``count(2N)/count(N)`` is exactly 4 for both the split and the direct loop.
    A genuine ``O(N log N)`` would give ``2·(log N + 1)/log N`` — 2.33 at
    N=64, 2.29 at N=128 — so the ``== 4`` assertion excludes it outright. It is
    excluded because it is IMPOSSIBLE, not because the split is poor: the
    output is ``N²`` integers. If this ever goes red the output shape changed,
    and every complexity sentence in ``exact_dft`` / ``fft`` must be re-derived.
    """
    prev_split = None
    prev_direct = None
    for n in COUNT_N:
        split, _, _, _ = _count_radix2(n)
        direct = _count_reference(n)
        if prev_split is not None:
            assert split == 4 * prev_split, f"N={n}: split growth is not 4x"
            assert direct == 4 * prev_direct, f"N={n}: direct growth is not 4x"
        prev_split, prev_direct = split, direct

    # Explicitly strictly ABOVE a (generous, 2x-constant) N log N budget, at
    # every measured N — so "it is not N log N" is asserted numerically and not
    # only inferred from the growth ratio.
    for n in COUNT_N:
        split, _, depth, _ = _count_radix2(n)
        assert split > 2 * n * depth, \
            f"N={n}: {split} adds is within an N log N budget — re-derive the docs"


def test_op_count_refuses_the_lengths_it_cannot_describe():
    """``_radix2_ring_op_count`` is about the radix-2 split and says so: the
    general-``Φ_N`` path has no butterfly, so there is no count to hand back
    and it raises rather than returning a number that would be wrong."""
    for bad in (0, 1, 3, 6, 10, 12, -8):
        with pytest.raises(ValueError):
            _radix2_ring_op_count(bad)
    for good in POW2:
        assert _radix2_ring_op_count(good)[0] == good * good


# ==========================================================================
# 4. Carrier discipline
# ==========================================================================
_BARE_ABS = _re.compile(r"(?<![0-9A-Za-z_.])abs\s*\(")
_BANNED_IMPORT = _re.compile(r"^\s*(?:import|from)\s+(numpy|fractions|math)\b",
                             _re.MULTILINE)


CASCADE_FILES = ("srmech/cascade/exact_dft.py",
                 "srmech/cascade/spectral_cascades.py")


@pytest.mark.parametrize("relpath", CASCADE_FILES)
def test_no_abs_in_the_exact_cascade(relpath):
    """Cascade honesty, mechanically. ``abs()`` is banned in cascade code
    because sign-flip is canonical **Class K** pin-slot + **Class C** reorient
    and must be spelled as that composition, so the cascade count matches the
    cascade shape claimed."""
    root = Path(__file__).resolve().parents[1]
    text = (root / relpath).read_text(encoding="utf-8")
    assert not _BARE_ABS.search(text), f"{relpath}: bare abs( — use Class K + Class C"


@pytest.mark.parametrize("relpath", CASCADE_FILES + (
    "tests/test_exact_radix2_rc463.py",))
def test_no_float_carrier_imports(relpath):
    """``numpy`` / ``fractions`` / ``math`` are banned in the exact cascade AND
    in this file, because the whole claim of the exact path is that it is
    integer arithmetic on the ALU — a test for a float-free module that
    imported a float library would be measuring the wrong thing.

    This file is deliberately absent from the ``abs(`` scan above: the only
    ``abs(`` text it contains is inside the detector's own fixture strings a
    few lines below, which is the one place the token has to appear.
    """
    root = Path(__file__).resolve().parents[1]
    text = (root / relpath).read_text(encoding="utf-8")
    hit = _BANNED_IMPORT.search(text)
    assert hit is None, f"{relpath}: banned import {hit.group(1) if hit else ''}"


def test_the_abs_detector_is_not_vacuous():
    """The guard above would be worthless if its pattern never matched; check
    that it fires on a bare call and stays quiet on the identifiers that
    legitimately contain the letters (``maxabs``, ``m.abs(``, ``_abs(``)."""
    assert _BARE_ABS.search("x = abs(y)")
    assert _BARE_ABS.search("    return abs (v)")
    assert not _BARE_ABS.search("maxabs = 0")
    assert not _BARE_ABS.search("a > maxabs")
    assert not _BARE_ABS.search("v = m.abs(y)")
    assert not _BARE_ABS.search("v = _abs(y)")
    assert _BANNED_IMPORT.search("import numpy as np")
    assert _BANNED_IMPORT.search("from math import pi")
    assert not _BANNED_IMPORT.search("# import numpy would be a defect")
