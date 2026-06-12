"""elementwise_sqrt — the array √ cascade (numpy-removal ufunc batch; rc54).

The np.sqrt-bucket decrement: `laplacian.elementwise_sqrt(arr)` computes
``√arrᵢ`` per element via the Class-N `rational.sqrt` cascade (native
`srmech_rational_sqrt`-dispatched), so numpy carries the array only — the math
is the libm-free cascade, not numpy's `sqrt` ufunc. This lets the 2 array
`np.sqrt` sites (`spectral_subtraction` PSD magnitude, `ica_jade` whitening)
leave numpy's sqrt engine; the 10 scalar sites route onto `rational.sqrt`.

It is round-off-faithful to numpy (rational sqrt is floor-projected vs IEEE
round-to-nearest — a ≤1-ULP shift), and **bit-exact** whenever ``arrᵢ`` is a
perfect square. These tests pin close-agreement, perfect-square exactness,
shape/empty handling, the negative-domain guard, registration, and that the
routed DSP surfaces still decode/whiten correctly.
"""
from __future__ import annotations

import numpy as np
import pytest

from srmech.amsc import laplacian
from srmech.amsc.laplacian import elementwise_sqrt


def test_sqrt_close_to_numpy():
    a = np.array([2.0, 3.0, 5.0, 7.5, 10.0, 0.0])
    out = elementwise_sqrt(a)
    assert out.dtype == np.float64
    assert out.shape == a.shape
    assert np.allclose(out, np.sqrt(a), rtol=0, atol=1e-9)


def test_sqrt_perfect_squares_are_exact():
    a = np.array([0.0, 1.0, 4.0, 9.0, 16.0, 25.0, 144.0])
    out = elementwise_sqrt(a)
    assert np.array_equal(out, np.array([0.0, 1.0, 2.0, 3.0, 4.0, 5.0, 12.0]))


def test_sqrt_preserves_2d_shape():
    a = np.array([[4.0, 9.0], [16.0, 2.0]])
    out = elementwise_sqrt(a)
    assert out.shape == (2, 2)
    assert np.allclose(out, np.sqrt(a), rtol=0, atol=1e-9)


def test_sqrt_empty_is_safe():
    out = elementwise_sqrt(np.array([]))
    assert out.shape == (0,)


def test_sqrt_negative_rejected():
    with pytest.raises(ValueError):
        elementwise_sqrt(np.array([1.0, -2.0, 3.0]))


# ── registration gates ───────────────────────────────────────────────────────

def test_sqrt_in_all_and_laplacian_ops():
    assert "elementwise_sqrt" in laplacian.__all__
    assert "elementwise_sqrt" in laplacian.LAPLACIAN_OPS


def test_sqrt_tool_entry_registered():
    from srmech.amsc.tool_schema import get_tool_schema
    names = {t.name for t in get_tool_schema().tools}
    assert "srmech.amsc.laplacian.elementwise_sqrt" in names


def test_no_np_sqrt_callsites_remain():
    import re
    from pathlib import Path
    pkg = Path(laplacian.__file__).resolve().parent.parent
    rx = re.compile(r"\b(?:np|numpy)\.sqrt\(")
    hits = []
    for p in pkg.rglob("*.py"):
        if "__pycache__" in p.parts:
            continue
        if rx.search(p.read_text(encoding="utf-8")):
            hits.append(str(p.relative_to(pkg)))
    assert hits == [], f"np.sqrt( callsites remain: {hits}"


# ── the routed surfaces still work ───────────────────────────────────────────

def test_potentials_ladder_still_correct():
    # harmonic-oscillator creation/annihilation: the √n ladder (rational.sqrt).
    # potentials went numpy-FREE (rc121) — the ladder ops are complex `Mat`, so
    # the number operator N = a†a is the native `mat_matmul`, checked by direct
    # Mat-entry against diag(0,1,2,3,4); no numpy (the op is numpy-free, so its
    # consumer-check must be too — feedback_test_for_numpy_free_module...).
    from srmech.qm.potentials import harmonic_oscillator_ladder
    from srmech.amsc.laplacian import mat_matmul
    a, a_dag = harmonic_oscillator_ladder(5)
    N = mat_matmul(a_dag, a)
    for i in range(5):
        assert abs(N[i, i].real - i) < 1e-9
        assert abs(N[i, i].imag) < 1e-9


def test_relativistic_dispersion_still_correct():
    # E = √(|k|² + m²) via rational.sqrt; 3-4-5 → √(9+16)=5 at m=4, k=(3,0,0).
    # relativistic is numpy-free (rc118) — the 3-momentum is a plain float list.
    from srmech.qm.relativistic import klein_gordon_dispersion
    e = klein_gordon_dispersion([3.0, 0.0, 0.0], 4.0)
    assert abs(e - 5.0) < 1e-9
