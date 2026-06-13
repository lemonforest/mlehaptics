"""rc60 — the mat_norm cascade (the Euclidean / Frobenius norm decrement).

``srmech.amsc.laplacian.mat_norm`` replaces the default 2-norm /
Frobenius-norm callsites across the QM self-consistency residuals and the
signal-processing taper normalisations. It is Class N (the rational sqrt) of
the Class M self-bind ``sum |x|^2`` (via ``dense_dot_complex`` / the real
peer). Post-#564 numpy is GONE from srmech entirely; ``mat_norm`` takes a
plain (possibly nested) Python sequence and returns a ``float``. This test
pins it value-faithful with a stdlib hand-computed oracle across every shape
and dtype, and asserts the routed qm modules carry no ``np.linalg.norm`` token.
"""

from __future__ import annotations

import math
import re
import pathlib
import random

import pytest

from srmech.amsc.laplacian import mat_norm


# ---------------------------------------------------------------------
# stdlib reference: flatten any nested sequence + sqrt(sum |x|^2).
# (math/cmath in TEST code is fine — the no-libm discipline is SOURCE-only.)
# ---------------------------------------------------------------------

def _flatten(x):
    if isinstance(x, (list, tuple)):
        for item in x:
            yield from _flatten(item)
    else:
        yield x


def _ref_norm(x):
    total = 0.0
    for v in _flatten(x):
        total += abs(v) ** 2  # abs() of a value for the TEST oracle is fine
    return math.sqrt(total)


def _make_nested(shape, rng, complex_input):
    """Build a nested list of the given shape filled with random values."""
    if len(shape) == 1:
        out = []
        for _ in range(shape[0]):
            val = rng.gauss(0.0, 1.0)
            if complex_input:
                val = complex(val, rng.gauss(0.0, 1.0))
            out.append(val)
        return out
    return [_make_nested(shape[1:], rng, complex_input) for _ in range(shape[0])]


# Post-#564 mat_norm flattens vectors (1-D) and matrices (2-D); the old
# numpy (2,2,2) 3-D shape is no longer a supported carrier.
_SHAPES = [(1,), (3,), (7,), (16,), (4, 4), (3, 6), (8, 3), (2, 4)]


@pytest.mark.parametrize("shape", _SHAPES)
@pytest.mark.parametrize("complex_input", [False, True])
def test_mat_norm_matches_hand_computed(shape, complex_input):
    rng = random.Random((hash(shape) % 2 ** 31) + int(complex_input))
    x = _make_nested(shape, rng, complex_input)
    got = mat_norm(x)
    ref = _ref_norm(x)
    assert isinstance(got, float)
    assert math.isclose(got, ref, rel_tol=1e-12, abs_tol=1e-12)


def test_mat_norm_pythagorean_triple():
    # [3, 4] -> 5 exactly; the simplest closed-form anchor.
    assert mat_norm([3.0, 4.0]) == pytest.approx(5.0)


def test_mat_norm_complex_closed_form():
    # |3+4j| = 5, |0+0j| = 0 -> norm = 5
    assert mat_norm([3 + 4j, 0 + 0j]) == pytest.approx(5.0)


def test_mat_norm_empty_is_zero():
    assert mat_norm([]) == 0.0


def test_mat_norm_zero_vector_is_zero():
    assert mat_norm([0.0, 0.0, 0.0, 0.0, 0.0]) == 0.0


def test_mat_norm_normalisation_roundtrip():
    rng = random.Random(7)
    v = [rng.gauss(0.0, 1.0) for _ in range(9)]
    nrm = mat_norm(v)
    unit = [vi / nrm for vi in v]
    assert math.isclose(mat_norm(unit), 1.0, abs_tol=1e-12)


def test_mat_norm_in_public_surface():
    from srmech.amsc import laplacian
    assert "mat_norm" in laplacian.__all__
    assert "mat_norm" in laplacian.LAPLACIAN_OPS


def test_routed_qm_modules_carry_no_linalg_norm_token():
    """The routed modules no longer reference the numpy norm engine."""
    pat = re.compile(r"\b(?:np|numpy)\.linalg\.norm\b")
    base = pathlib.Path(__import__("srmech").__file__).parent
    routed = [
        "qm/gauge.py", "qm/pseudo_hermitian.py", "qm/relativistic.py",
        "qm/sm.py", "qm/so8.py", "qm/spin.py", "qm/triality.py",
        "signal_processing/closed_form_ops/multitaper.py",
    ]
    for rel in routed:
        text = (base / rel).read_text(encoding="utf-8")
        assert not pat.search(text), f"{rel} still references the numpy norm engine"
