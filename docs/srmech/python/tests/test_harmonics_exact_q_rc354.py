"""rc354 — the chirality classifier is EXACT (Class-N ``Q``), not float.

WHAT THIS PINS, AND WHY IT IS A CORRECTNESS TEST AND NOT A STYLE TEST
====================================================================
``srmech/music/harmonics.py`` (``srmech/amsc/harmonics.py`` until the ADR-0010
rc366 slice relocated it) carried, since rc154, a comment claiming the
classifier composes "**Class-N** exact ratios". Through rc353 the code read the
vector as ``float`` at ``harmonics.py:99`` and ``:145``, so the claim was false
of the code. Three reachable defect families were reproduced against the
shipped rc353 op, and each is a case below:

1. **Entries past 2⁵³.** ``[3*(2**53-1), -(2**53-1)]`` has exact DC score
   ``2B/4B = 1/2``, which is ``>= 0.5`` and therefore harmonic 1. rc353 returned
   2 on EVERY interpreter, because the precision was lost in ``float(v)``
   *before* any summing — so no summation strategy rescues it.

2. **Interpreter-dependent verdicts.** CPython ≥ 3.12 made built-in ``sum()``
   Neumaier-compensated. An all-double vector with exact DC 1/2 therefore
   classified 2 on 3.10/3.11 and 1 on 3.12+, while ``pyproject.toml`` declares
   ``requires-python = ">=3.10"``. A C projection folds naively, so it tracked
   3.11 — under ADR-0009 (the capability is the invariant, the projections are
   co-equal) that is a live parity break, not a hypothetical.

3. **Underflow.** ``[1e-200] * 3`` is a CONSTANT vector — the flagship
   harmonic-1 shape, exact DC score 1 — and rc353's ``energy == 0.0`` guard
   fired on the underflowed squares, returning ``(0, 0, 0)`` and harmonic 2.
   At no boundary, on every interpreter.

THE HONEST NULL, ASSERTED HERE SO IT CANNOT BE OVERCLAIMED LATER
================================================================
The documented ±1-hypervector domain was NEVER at risk, and that is provable
rather than merely unobserved: ``Σx`` and ``Σ|x|`` are exact small integers for
any n < 2⁵³ and IEEE division is correctly rounded, so an exact 1/2 renders as
exactly ``0.5`` and ``>=`` is decisive. ``test_pm1_domain_was_never_at_risk``
re-derives that exhaustively. Do not read rc354 as "the classifier was
returning wrong harmonics" — it was wrong only at the three edges above.
"""

from __future__ import annotations

import itertools

import pytest

from srmech.music.harmonics import _spectral_scores, classify_chirality_harmonic
from srmech.math.mat import Mat
from srmech.math.q import Q
from srmech.math.vec import Vec


# ── the three reproduced defect families ──────────────────────────────────

def test_entries_past_2_53_classify_on_the_exact_dc():
    """(1) exact dc == 1/2 → harmonic 1, where the float read gives 0.4999…"""
    hv = [3 * (2**53 - 1), -(2**53 - 1)]
    dc, _mirror, _three = _spectral_scores(hv)
    assert dc == Q(1, 2), f"exact DC must be 1/2, got {dc!r}"
    assert classify_chirality_harmonic(hv) == 1
    # the float path this replaces, stated so the differential is visible and
    # cannot be mistaken for a rounding preference.
    a, b = float(hv[0]), float(hv[1])
    assert (a + b) / (a - b) == 0.49999999999999994


def test_verdict_does_not_depend_on_the_interpreters_sum():
    """(2) an all-double vector whose float verdict moved at CPython 3.12.

    Asserted against the EXACT score, so this test states the same thing on
    3.10 and on 3.14 — which is exactly the property that was missing.
    """
    hv = [3.0 - 2.0**-51, 2.0**-53, 2.0**-53, 2.0**-53, 2.0**-53, -1.0]
    dc, _mirror, _three = _spectral_scores(hv)
    assert dc == Q(1, 2)
    assert classify_chirality_harmonic(hv) == 1
    # the mechanism, pinned so a future reader does not have to trust the prose:
    # naive left-fold and compensated summation disagree on this shape.
    naive = 0.0
    for v in [1.0, 1e100, 1.0, -1e100]:
        naive += v
    assert naive == 0.0 and sum([1.0, 1e100, 1.0, -1e100]) in (0.0, 2.0)


def test_constant_vector_at_1e_minus_200_is_harmonic_1():
    """(3) underflow — a CONSTANT vector is the flagship harmonic-1 shape."""
    hv = [1e-200] * 3
    dc, mirror, three = _spectral_scores(hv)
    assert (dc, mirror, three) == (Q(1), Q(1), Q(1))
    assert classify_chirality_harmonic(hv) == 1
    # the float energy that rc353 tested against zero really does underflow —
    # so this is the measured cause, not a guessed one.
    assert sum(x * x for x in hv) == 0.0


def test_all_zero_vector_still_scores_zero():
    """The one input for which ``(0, 0, 0)`` is CORRECT stays correct.

    Exact integers make ``energy == 0`` true iff every entry is 0, so this is
    now the only vector that takes that branch.
    """
    assert _spectral_scores([0.0, 0.0, 0.0]) == (Q(0), Q(0), Q(0))
    assert classify_chirality_harmonic([0.0, 0.0, 0.0]) == 2


# ── the carrier contract ──────────────────────────────────────────────────

def test_scores_are_exact_q_not_float():
    scores = _spectral_scores([1.0, 1.0, -1.0])
    assert all(isinstance(s, Q) for s in scores), [type(s).__name__ for s in scores]
    # a rendering is still one call away, and matches the old float reading.
    assert tuple(float(s) for s in scores) == (1 / 3, 1 / 3, 1 / 3)


def test_dc_threshold_accepts_int_float_and_q_identically():
    """0.5 is exactly ``Q(1, 2)``, so all three spellings must agree."""
    hv = [3 * (2**53 - 1), -(2**53 - 1)]          # exact dc == 1/2
    assert classify_chirality_harmonic(hv, 0.5) == 1
    assert classify_chirality_harmonic(hv, Q(1, 2)) == 1
    assert classify_chirality_harmonic(hv, 1) == 2   # dc 1/2 < 1 → not harmonic 1
    # and the knob really is exact: one ulp above 1/2 flips the verdict.
    just_over = Q(1, 2) + Q(1, 10**18)
    assert classify_chirality_harmonic(hv, just_over) == 2


def test_mat_input_no_longer_raises():
    """rc353 advertised a ``Mat`` input and raised ``TypeError`` on one.

    ``Mat`` iterates row-wise (``srmech/amsc/mat.py:192`` yields lists), so
    ``[float(v) for v in hv]`` hit ``float(list)``. The docstring claim is now
    backed by ``harmonics._flat_scalars``.
    """
    rows = [[1.0, -1.0, 1.0], [1.0, 1.0, -1.0]]
    flat = [x for row in rows for x in row]
    assert classify_chirality_harmonic(Mat.from_rows(rows)) == \
        classify_chirality_harmonic(flat)
    assert classify_chirality_harmonic(Vec.from_sequence(flat)) == \
        classify_chirality_harmonic(flat)


def test_empty_still_raises():
    with pytest.raises(ValueError, match="empty vector"):
        classify_chirality_harmonic([])


# ── the null, re-derived rather than asserted ─────────────────────────────

def test_pm1_domain_was_never_at_risk():
    """EXHAUSTIVE over every ±1 vector, n = 2..14: exact and float agree.

    This is the test that keeps the changelog honest. If it ever goes red the
    null in this module's docstring is wrong and the prose must change with it.
    """
    for n in range(2, 15):
        for bits in itertools.product((1.0, -1.0), repeat=n):
            hv = list(bits)
            exact = classify_chirality_harmonic(hv)
            # the rc353 float classifier, reproduced inline as a LABELLED
            # oracle (never as the subject under test).
            energy = sum(x * x for x in hv)
            total_mag = sum(x if x >= 0.0 else -x for x in hv)
            s = sum(hv)
            dc = (s if s >= 0.0 else -s) / total_mag
            d_mirror = sum(hv[i] * hv[n - 1 - i] for i in range(n))
            mirror = (d_mirror if d_mirror >= 0.0 else -d_mirror) / energy
            if n % 3 == 0:
                k = n // 3
                d_three = sum(hv[i] * hv[(i - k) % n] for i in range(n))
                three = (d_three if d_three >= 0.0 else -d_three) / energy
            else:
                three = 0.0
            legacy = 1 if dc >= 0.5 else (3 if three > mirror else 2)
            assert exact == legacy, (n, hv, exact, legacy)


def test_worked_domain_verdicts_are_unchanged_from_rc353():
    """The six DNA vectors in the shipped worked example keep their verdicts.

    A correctness repair that moved the documented outputs would be a
    behaviour change wearing a bug-fix label; this pins that it is not.
    """
    code = {"G": 1.0, "C": 1.0, "A": -1.0, "T": -1.0}
    v = lambda s: [code[b] for b in s]          # noqa: E731 — mirrors the doc
    expect = {
        "AAAAAAAAA": 1, "GAATTC": 2, "AAGAAGAAG": 3,
        "AAGAAGAAGAAGAAGAAG": 3, "GCTGCCGCAGCGGCTGCCGCAGCG": 1,
        "AAGAAGAA": 1,
    }
    for seq, harmonic in expect.items():
        assert classify_chirality_harmonic(v(seq)) == harmonic, seq
    assert classify_chirality_harmonic(v("AAGAAGAAG"), dc_threshold=0.3) == 1
