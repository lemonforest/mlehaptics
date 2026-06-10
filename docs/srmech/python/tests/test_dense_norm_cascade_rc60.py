"""rc60 — the dense_norm cascade (the Euclidean / Frobenius norm decrement).

``srmech.amsc.laplacian.dense_norm`` replaces the default ``np.linalg.norm``
2-norm / Frobenius-norm callsites across the QM self-consistency residuals and
the signal-processing taper normalisations. It is Class N (the rational sqrt)
of the Class M self-bind ``sum |x|^2`` (via ``dense_dot_complex`` / the real
peer) — numpy is a carrier only (flatten + sum reduction). This test pins it
value-faithful to NumPy across every shape and dtype, and asserts the routed
qm modules carry no ``np.linalg.norm`` token.
"""

from __future__ import annotations

import re
import pathlib

import numpy as np
import pytest

from srmech.amsc.laplacian import dense_norm


_SHAPES = [(1,), (3,), (7,), (16,), (4, 4), (3, 6), (8, 3), (2, 2, 2)]


@pytest.mark.parametrize("shape", _SHAPES)
@pytest.mark.parametrize("complex_input", [False, True])
def test_dense_norm_matches_numpy(shape, complex_input):
    rng = np.random.default_rng(hash(shape) % 2**31 + complex_input)
    x = rng.standard_normal(shape)
    if complex_input:
        x = x + 1j * rng.standard_normal(shape)
    got = dense_norm(x)
    ref = float(np.linalg.norm(x))
    assert isinstance(got, float)
    assert np.isclose(got, ref, rtol=1e-12, atol=1e-12)


def test_dense_norm_empty_is_zero():
    assert dense_norm(np.array([])) == 0.0


def test_dense_norm_zero_vector_is_zero():
    assert dense_norm(np.zeros(5)) == 0.0


def test_dense_norm_normalisation_roundtrip():
    rng = np.random.default_rng(7)
    v = rng.standard_normal(9)
    unit = v / dense_norm(v)
    assert np.isclose(dense_norm(unit), 1.0, atol=1e-12)


def test_dense_norm_in_public_surface():
    from srmech.amsc import laplacian
    assert "dense_norm" in laplacian.__all__
    assert "dense_norm" in laplacian.LAPLACIAN_OPS


def test_routed_qm_modules_carry_no_linalg_norm_token():
    """The 8 routed modules no longer reference the numpy norm engine."""
    pat = re.compile(r"\b(?:np|numpy)\.linalg\.norm\b")
    root = pathlib.Path(dense_norm.__module__.replace(".", "/")).parent.parent  # srmech/amsc -> srmech
    base = pathlib.Path(__import__("srmech").__file__).parent
    routed = [
        "qm/gauge.py", "qm/pseudo_hermitian.py", "qm/relativistic.py",
        "qm/sm.py", "qm/so8.py", "qm/spin.py", "qm/triality.py",
        "signal_processing/closed_form_ops/multitaper.py",
    ]
    for rel in routed:
        text = (base / rel).read_text(encoding="utf-8")
        assert not pat.search(text), f"{rel} still references the numpy norm engine"
