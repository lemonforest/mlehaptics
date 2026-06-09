"""elementwise_hypot — the |z| magnitude cascade (numpy-removal ufunc batch; rc52).

The first ufunc-bucket decrement: `laplacian.elementwise_hypot(a, b)` computes
the array Euclidean magnitude ``√(aᵢ² + bᵢ²)`` per element via the Class-N
`rational.hypot` cascade (native `srmech_rational_sqrt`-dispatched), so numpy
carries the array only — the math is the libm-free cascade, not numpy's ufunc
engine. This lets the 5 DSP `|z| = √(re² + im²)` sites (fsk / mlse / psk_qam /
ofdm / spectral) leave `np.hypot` (ufunc 48 → 43).

It is round-off-faithful to numpy (rational sqrt is floor-projected vs IEEE
round-to-nearest — a ≤1-ULP shift), and **bit-exact** whenever ``aᵢ² + bᵢ²`` is
a perfect square. These tests pin the close-agreement, the perfect-square
exactness, shape/empty handling, the shape-mismatch guard, registration, and
that the routed DSP surfaces still decode correctly.
"""
from __future__ import annotations

import numpy as np
import pytest

from srmech.amsc import laplacian
from srmech.amsc.laplacian import elementwise_hypot


def test_hypot_close_to_numpy():
    a = np.array([3.0, -5.0, 0.0, 1.5, 8.0])
    b = np.array([4.0, 12.0, 7.0, 2.0, 15.0])
    out = elementwise_hypot(a, b)
    assert out.dtype == np.float64
    assert out.shape == a.shape
    assert np.allclose(out, np.hypot(a, b), rtol=0, atol=1e-9)


def test_hypot_perfect_squares_are_exact():
    # 3-4-5, 5-12-13, 8-15-17 Pythagorean triples → √(a²+b²) is an exact integer
    a = np.array([3.0, 5.0, 8.0])
    b = np.array([4.0, 12.0, 15.0])
    out = elementwise_hypot(a, b)
    assert np.array_equal(out, np.array([5.0, 13.0, 17.0]))   # bit-exact


def test_hypot_matches_complex_magnitude():
    z = np.array([3 + 4j, 0 + 1j, -8 - 15j, 1 + 0j])
    out = elementwise_hypot(z.real, z.imag)
    assert np.allclose(out, np.abs(z), rtol=0, atol=1e-9)


def test_hypot_preserves_2d_shape():
    a = np.array([[3.0, 5.0], [8.0, 0.0]])
    b = np.array([[4.0, 12.0], [15.0, 2.0]])
    out = elementwise_hypot(a, b)
    assert out.shape == (2, 2)
    assert np.allclose(out, np.hypot(a, b), rtol=0, atol=1e-9)


def test_hypot_empty_is_safe():
    out = elementwise_hypot(np.array([]), np.array([]))
    assert out.shape == (0,)


def test_hypot_shape_mismatch_rejected():
    with pytest.raises(ValueError):
        elementwise_hypot(np.array([1.0, 2.0]), np.array([1.0]))


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
    idx = np.array([0, 1, 2, 3])
    symbols = op(idx, M=4, modulation="psk")             # modulate QPSK
    recovered = op(symbols, M=4, modulation="psk", demodulate=True)
    # the nearest-symbol decision now runs through elementwise_hypot
    assert np.array_equal(recovered, idx)
