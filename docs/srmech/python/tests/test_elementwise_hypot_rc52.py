"""elementwise_hypot — the |z| magnitude cascade (numpy-removal ufunc batch; rc52).

The first ufunc-bucket decrement: `laplacian.elementwise_hypot(a, b)` computes
the array Euclidean magnitude ``√(aᵢ² + bᵢ²)`` per element via the Class-N
`rational.hypot` cascade (native `srmech_rational_sqrt`-dispatched). With numpy
removed entirely (#564), the inputs are plain Python lists and the result is a
FLAT ``list[float]`` — the math is the libm-free cascade, not numpy's ufunc
engine. This lets the 5 DSP `|z| = √(re² + im²)` sites (fsk / mlse / psk_qam /
ofdm / spectral) leave `np.hypot`.

It is round-off-faithful to ``math.hypot`` (rational sqrt is floor-projected vs
IEEE round-to-nearest — a ≤1-ULP shift), and **bit-exact** whenever
``aᵢ² + bᵢ²`` is a perfect square. These tests pin the close-agreement (stdlib
``math.hypot`` oracle), the perfect-square exactness, empty handling, the
length-mismatch guard, registration, and that the routed DSP surfaces still
decode correctly.
"""
from __future__ import annotations

import math

import pytest

from srmech.amsc import laplacian
from srmech.amsc.laplacian import elementwise_hypot

_TOL = 1e-9


def test_hypot_close_to_stdlib():
    a = [3.0, -5.0, 0.0, 1.5, 8.0]
    b = [4.0, 12.0, 7.0, 2.0, 15.0]
    out = elementwise_hypot(a, b)
    assert isinstance(out, list)
    assert len(out) == len(a)
    assert all(isinstance(x, float) for x in out)
    for got, ai, bi in zip(out, a, b):
        assert abs(got - math.hypot(ai, bi)) < _TOL


def test_hypot_perfect_squares_are_exact():
    # 3-4-5, 5-12-13, 8-15-17 Pythagorean triples → √(a²+b²) is an exact integer
    a = [3.0, 5.0, 8.0]
    b = [4.0, 12.0, 15.0]
    out = elementwise_hypot(a, b)
    assert out == [5.0, 13.0, 17.0]   # bit-exact


def test_hypot_matches_complex_magnitude():
    z = [3 + 4j, 0 + 1j, -8 - 15j, 1 + 0j]
    out = elementwise_hypot([c.real for c in z], [c.imag for c in z])
    for got, c in zip(out, z):
        assert abs(got - abs(c)) < _TOL


def test_hypot_empty_is_safe():
    out = elementwise_hypot([], [])
    assert out == []


def test_hypot_length_mismatch_rejected():
    with pytest.raises(ValueError):
        elementwise_hypot([1.0, 2.0], [1.0])


# ── registration: the 3 gates + LAPLACIAN_OPS ────────────────────────────────

def test_hypot_in_all_and_laplacian_ops():
    assert "elementwise_hypot" in laplacian.__all__
    assert "elementwise_hypot" in laplacian.LAPLACIAN_OPS


def test_hypot_tool_entry_registered():
    from srmech.amsc.tool_schema import get_tool_schema

    names = {t.name for t in get_tool_schema().tools}
    assert "srmech.amsc.laplacian.elementwise_hypot" in names


def test_no_np_hypot_callsites_remain():
    # the ufunc-ratchet guarantee at the source level: no np.hypot( anywhere
    import re
    from pathlib import Path
    pkg = Path(laplacian.__file__).resolve().parent.parent
    rx = re.compile(r"\b(?:np|numpy)\.hypot\(")
    hits = []
    for p in pkg.rglob("*.py"):
        if "__pycache__" in p.parts:
            continue
        if rx.search(p.read_text(encoding="utf-8")):
            hits.append(str(p.relative_to(pkg)))
    assert hits == [], f"np.hypot( callsites remain: {hits}"


# ── the routed DSP surfaces still decode correctly ───────────────────────────

def test_psk_qam_demod_still_correct():
    from srmech.signal_processing.closed_form_ops.psk_qam import op
    idx = [0, 1, 2, 3]
    symbols = op(idx, M=4, modulation="psk")             # modulate QPSK
    recovered = op(symbols, M=4, modulation="psk", demodulate=True)
    # rc106: psk_qam is numpy-free; the nearest-symbol decision is the
    # squared-distance argmin (monotone in |·|, so no hypot/sqrt/abs).
    assert list(recovered) == idx
