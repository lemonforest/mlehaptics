"""rc100 (F686 / F974) — ``coupling.fractal_spectrum``, the Ch-2 (quasi-periodic
/ fractal) DUAL of ``coupling.resonant_spectrum``.

Where ``resonant_spectrum(L)`` reads a symmetric coupling Laplacian's FLAT
eigenspectrum (one eigensolve), ``fractal_spectrum(R, branches)`` reads a
self-similar lattice's SPECTRAL-DECIMATION structure — the ITERATED PREIMAGE of
the renormalization ``Poly`` ``R`` (the decimation map, ``R(0)=0``), NOT a flat
list. It is PURE orchestration over already-C-backed ops (``Poly.derivative`` /
``.eval`` + Class-N ``log`` / ``best_rational`` + the F974 bit-exact ``|q|``-meter)
— NO new numerical kernel, so it ships **non_compute** (no dedicated C peer; the
``from_bodies`` / ``cooccurrence_edges`` precedent). It IS a new ToolEntry →
``tools.total`` 347 → 348.

numpy-FREE and math-FREE (the module under test is numpy-free, so this test is
too — ``[[feedback_test_for_numpy_free_module_must_itself_be_numpy_free]]``): it
exercises only the srmech carriers + plain Python arithmetic; no ``abs()`` (a
Class-K sign branch is used in test code too).

Coverage:
  (a) the Sierpinski-gasket grounding R(z)=z(5−4z), branches=3 → scale 5,
      d_s ≈ 1.36521 (= 2·log3/log5), q_octaves 3, rung 'constant',
      log_period/2π ≈ 0.6213 (= 1/ln5), spectrum_open present;
  (b) a SECOND lattice R(z)=z(3−2z), branches=5 → scale 3, a genuinely
      DIFFERENT fracton dimension d_s ≈ 2.9299, q_octaves 2;
  (c) a coefficient-sequence R is coerced (== the Poly path);
  (d) input validation (R(0)≠0 / degree<2 / scale≤1 / branches<2 reject);
  (e) the op is REGISTERED (in the tool schema; tools.total == 359);
  (f) the module source is numpy / math / abs()-free.
"""

import os
import re
import tokenize

import pytest

from srmech.amsc import coupling
from srmech.amsc.poly import Poly
from srmech.amsc.q import Q


def _abs(x):
    """Magnitude without ``abs()`` (Class-K sign branch in test code too)."""
    return -x if x < 0.0 else x


# ─────────────────────────────────────────────────────────────────────
# (a) the Sierpinski-gasket grounding (the MPM-verified anchor)
# ─────────────────────────────────────────────────────────────────────
def test_sierpinski_gasket_grounding():
    R = Poly.from_coeffs([0, 5, -4])            # 5z − 4z² = z(5 − 4z)
    fs = coupling.fractal_spectrum(R, 3)

    # dict shape
    assert set(fs.keys()) == {
        "decimation_map", "scale", "branches", "self_similarity_dim",
        "q_octaves_per_level", "rung_class", "log_period_over_2pi",
        "spectrum_open",
    }
    # the decimation map is echoed back exactly.
    assert isinstance(fs["decimation_map"], Poly)
    assert fs["decimation_map"] == R
    assert fs["branches"] == 3

    # scale = R'(0) = 5 EXACT (an exact Q, not a float).
    assert isinstance(fs["scale"], Q)
    assert fs["scale"] == Q(5, 1)

    # self-similarity (fracton) dimension d_s = 2·log3/log5 ≈ 1.36521.
    sd = fs["self_similarity_dim"]
    assert isinstance(sd, tuple) and len(sd) == 2
    assert _abs(sd[0] / sd[1] - 1.36521) < 1e-4

    # F974 |q|-meter: octaves per level = ceil(log2 5) = 3.
    assert fs["q_octaves_per_level"] == 3

    # one R iterated -> a self-similar / constant |q| rung.
    assert fs["rung_class"] == "constant"

    # complex-dimension period / 2π = 1/ln5 ≈ 0.6213.
    lp = fs["log_period_over_2pi"]
    assert isinstance(lp, tuple) and len(lp) == 2
    assert _abs(lp[0] / lp[1] - 0.62133) < 1e-4

    # the full spectrum is the honest operand-IRREPRESENTABLE OPEN (the Julia set).
    assert isinstance(fs["spectrum_open"], str)
    assert "JULIA SET" in fs["spectrum_open"]


# ─────────────────────────────────────────────────────────────────────
# (b) a second lattice — a genuinely DIFFERENT fracton dimension
# ─────────────────────────────────────────────────────────────────────
def test_second_lattice_different_dimension():
    R2 = Poly.from_coeffs([0, 3, -2])           # 3z − 2z² = z(3 − 2z)
    fs2 = coupling.fractal_spectrum(R2, 5)
    assert fs2["scale"] == Q(3, 1)              # R'(0) = 3
    # d_s = 2·log5/log3 ≈ 2.9299 — distinct from the gasket's 1.36521.
    sd = fs2["self_similarity_dim"]
    assert _abs(sd[0] / sd[1] - 2.9299) < 1e-3
    # ceil(log2 3) = 2.
    assert fs2["q_octaves_per_level"] == 2
    assert fs2["rung_class"] == "constant"


# ─────────────────────────────────────────────────────────────────────
# (c) a coefficient-sequence R is coerced (== the Poly path)
# ─────────────────────────────────────────────────────────────────────
def test_coeff_list_is_coerced():
    from_list = coupling.fractal_spectrum([0, 5, -4], 3)
    from_poly = coupling.fractal_spectrum(Poly.from_coeffs([0, 5, -4]), 3)
    assert from_list["scale"] == from_poly["scale"]
    assert from_list["self_similarity_dim"] == from_poly["self_similarity_dim"]
    assert from_list["q_octaves_per_level"] == from_poly["q_octaves_per_level"]
    assert from_list["log_period_over_2pi"] == from_poly["log_period_over_2pi"]
    assert isinstance(from_list["decimation_map"], Poly)


# ─────────────────────────────────────────────────────────────────────
# (d) input validation
# ─────────────────────────────────────────────────────────────────────
def test_rejects_nonzero_fixed_point():
    # R(0) = 1 ≠ 0 — no fixed point at the trivial eigenvalue.
    with pytest.raises(ValueError):
        coupling.fractal_spectrum(Poly.from_coeffs([1, 5, -4]), 3)


def test_rejects_degree_below_two():
    # degree 1 (5z) is not a decimation map (a linear map has no branching).
    with pytest.raises(ValueError):
        coupling.fractal_spectrum(Poly.from_coeffs([0, 5]), 3)


def test_rejects_scale_not_greater_than_one():
    # R'(0) = 1 (z − z²) — no contraction toward 0 under the preimage.
    with pytest.raises(ValueError):
        coupling.fractal_spectrum(Poly.from_coeffs([0, 1, -1]), 3)


def test_rejects_branches_below_two():
    with pytest.raises(ValueError):
        coupling.fractal_spectrum(Poly.from_coeffs([0, 5, -4]), 1)


def test_rejects_uncoercible_R():
    with pytest.raises(ValueError):
        coupling.fractal_spectrum("not a poly", 3)


# ─────────────────────────────────────────────────────────────────────
# (e) the op is REGISTERED (tool schema; tools.total == 359)
# ─────────────────────────────────────────────────────────────────────
def test_registered_in_tool_schema():
    from srmech.amsc import tool_schema

    schema = tool_schema.get_tool_schema()
    entry = schema.lookup("srmech.amsc.coupling.fractal_spectrum")
    assert entry is not None
    assert entry.owner == "srmech"
    assert entry.category == "coupling"
    # param types are MCP-coercible (Poly rides the rc41 _to_poly coercer; int
    # passes through) — the surface stays JSON-callable.
    ptypes = {p.name: p.type for p in entry.parameters}
    assert ptypes["R"] == "Poly"
    assert ptypes["branches"] == "int"


def test_tools_total_is_359():
    from srmech import introspect

    assert introspect.describe()["tools"]["total"] == 359


# ─────────────────────────────────────────────────────────────────────
# (f) discipline — no numpy / math / abs() in the coupling module source
# ─────────────────────────────────────────────────────────────────────
def test_coupling_source_is_numpy_math_abs_free():
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    src = os.path.join(here, "srmech", "amsc", "coupling.py")
    with tokenize.open(src) as fh:
        text = fh.read()
    # Real import STATEMENTS only (line-anchored) — the module docstring may name
    # ``import math`` / numpy as prose (it explains WHY the carriers are float-free).
    assert re.search(r"(?m)^\s*(import|from)\s+numpy\b", text) is None
    assert re.search(r"(?m)^\s*(import|from)\s+math\b", text) is None
    assert re.search(r"abs\([^)]", text) is None          # no bare abs() CALL
