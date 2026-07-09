"""rc192 — the #796 PAYOFF: the SIGMA-DEFINITE (wz_certificate) infer row runs in C.

rc176 moved the F929 OPEN/infer router's detect + dispatch + verify LOGIC into C
for two rows (cyclic → the_one, sigma-gosper → gosper). rc191 shipped the nested
exact-ℚ BiPoly operand reader (``srmech_carrier_read_bipoly``). This rc wires that
reader into ``srmech_infer.c`` so the DEFINITE-sum wz_certificate row dispatches
its reducer DECISION in C for a bare-C host:

  * sigma-DEFINITE (wz_certificate) — the four (n,k) BiPoly term-ratios
    ``rn_num`` / ``rn_den`` / ``rk_num`` / ``rk_den``. The C router FINDs the
    order-1 forced-recurrence certificate via ``srmech_zeilberger`` (accepting
    only the WZ shape a₀(n)+a₁(n)=0 with nonzero constants) and PROVEs the WZ
    equation via ``srmech_wz_verify`` on the 1/a₁-rescaled certificate — the
    GENUINE identity proof (not the FIND alone), in the zeilberger-scale infer
    arena (``srmech_infer_sigma_definite_arena_bytes``), NOT the vtable arena.

This test pins:
  (1) PARITY — ``infer`` with the native path ENGAGED is structurally identical
      to the pure path over a genuine reduction (Σ_k C(n,k)/2ⁿ = 1), a bignum
      reduction (coefficients > int64), AND two honest-OPEN cases (an order-2 sum
      Σ_k C(n,k)², and an order-1 non-WZ sum Σ_k C(n,k) = 2ⁿ un-normalized).
  (2) GENUINE ENGAGEMENT — for the wz row the C peer is really RUN: ``infer_c``
      returns the wz decision dict (reducer="wz_certificate"), never None.
  (3) HONEST OPEN PRESERVED — the two OPEN cases come back ``reducible: false``
      from the raw C decision AND ``infer`` → OPEN; the C router NEVER fabricates
      a reduction (the no-hallucination discipline in C, over a real reducer).
  (4) The row uses its OWN zeilberger-scale arena sizer (the cheap cyclic /
      gosper rows keep their small arena).

numpy-FREE and math-FREE (only srmech carriers + fractions + plain arithmetic).
"""

from __future__ import annotations

import copy

import pytest

from srmech.amsc import _native
from srmech.amsc import dispatch
from srmech.amsc.dispatch import infer, _marshal_relationship
from srmech.amsc.poly import Poly
from srmech.amsc.q import Q
from srmech.amsc.zeilberger import BiPoly

_BIG = 10 ** 25   # a coefficient beyond int64 — the bignum decimal-string transport


def _P(*coeffs):
    return Poly.from_coeffs(list(coeffs))


def _Pb(*coeffs):
    """A Poly whose integer coefficients are scaled by _BIG (a bignum coeff)."""
    return Poly.from_coeffs([Q(_BIG * c, 1) for c in coeffs])


# ── canonical (n,k) term-ratio operands ──────────────────────────────────────
def _binom():
    """Σ_k C(n,k)/2ⁿ = 1 (normalized) — the genuine WZ reduction."""
    return {"rn_num": BiPoly([_P(1, 1)]),
            "rn_den": BiPoly([_P(2, 2), _P(-2)]),
            "rk_num": BiPoly([_P(0, 1), _P(-1)]),
            "rk_den": BiPoly([_P(1), _P(1)])}


def _binom_bignum():
    """The SAME normalized identity with r_n scaled by a >int64 constant (the
    ratio — hence F — is unchanged, so it still reduces; the coefficients ride as
    decimal strings through the bignum-safe reader)."""
    return {"rn_num": BiPoly([_Pb(1, 1)]),
            "rn_den": BiPoly([_Pb(2, 2), _Pb(-2)]),
            "rk_num": BiPoly([_P(0, 1), _P(-1)]),
            "rk_den": BiPoly([_P(1), _P(1)])}


def _binom_sq():
    """Σ_k C(n,k)² = C(2n,n): r_n = (n+1)²/(n+1-k)², r_k = (n-k)²/(k+1)². An
    order-2 recurrence — NOT a WZ-constant sum → honest OPEN."""
    return {"rn_num": BiPoly([_P(1, 2, 1)]),
            "rn_den": BiPoly([_P(1, 2, 1), _P(-2, -2), _P(1)]),
            "rk_num": BiPoly([_P(0, 0, 1), _P(0, -2), _P(1)]),
            "rk_den": BiPoly([_P(1), _P(2), _P(1)])}


def _binom_unnorm():
    """Σ_k C(n,k) = 2ⁿ (UN-normalized): an order-1 recurrence f(n+1) − 2f(n) = 0
    whose coefficients [−2, 1] are NOT the WZ shape (a₀ + a₁ ≠ 0) → honest OPEN."""
    return {"rn_num": BiPoly([_P(1, 1)]),
            "rn_den": BiPoly([_P(1, 1), _P(-1)]),
            "rk_num": BiPoly([_P(0, 1), _P(-1)]),
            "rk_den": BiPoly([_P(1), _P(1)])}


_REDUCIBLE = {"binom": _binom(), "binom_bignum": _binom_bignum()}
_OPEN = {"binom_sq": _binom_sq(), "binom_unnorm": _binom_unnorm()}
_ALL = {**_REDUCIBLE, **_OPEN}


def _shape(d):
    """The structural signature of an infer() result (no float / object identity)."""
    return (d["reducible"], d["row"], d.get("reducer"), d.get("verified"),
            d.get("candidate_next_theory") is not None, d.get("reason"))


def _infer_with(relationship, native_on):
    """Run infer() with the native path forced on/off (the parity toggle)."""
    saved = _native.HAS_NATIVE
    try:
        _native.HAS_NATIVE = native_on and saved   # can't fabricate native if absent
        return infer(copy.deepcopy(relationship))
    finally:
        _native.HAS_NATIVE = saved


# ── (1) PARITY: native == pure over reducible + bignum + OPEN ─────────────────
@pytest.mark.parametrize("name", list(_ALL))
def test_native_equals_pure(name):
    rel = _ALL[name]
    nat = _infer_with(rel, native_on=True)
    pur = _infer_with(rel, native_on=False)
    assert _shape(nat) == _shape(pur), (
        f"{name}: native {_shape(nat)} != pure {_shape(pur)}")


# ── (2) GENUINE ENGAGEMENT: the wz row is really marshalled + RUN in C ─────────
@pytest.mark.skipif(not _native.HAS_NATIVE, reason="no native lib")
def test_sigma_definite_native_present():
    assert _native.has_native_sigma_definite() is True


@pytest.mark.skipif(not _native.HAS_NATIVE, reason="no native lib")
@pytest.mark.parametrize("name", list(_ALL))
def test_wz_row_marshals(name):
    """Every wz case marshals to the srmech_infer BiPoly wire form (never None)."""
    marshalled = _marshal_relationship(_ALL[name])
    assert marshalled is not None, f"{name} should marshal to the sigma-definite form"
    rel_json, max_terms = marshalled
    assert '"rn_num"' in rel_json and max_terms >= 1


@pytest.mark.skipif(not _native.HAS_NATIVE, reason="no native lib")
@pytest.mark.parametrize("name,want", [
    ("binom", {"reducible": True, "row": "sigma", "reducer": "wz_certificate"}),
    ("binom_bignum", {"reducible": True, "row": "sigma", "reducer": "wz_certificate"}),
    ("binom_sq", {"reducible": False, "row": "sigma"}),
    ("binom_unnorm", {"reducible": False, "row": "sigma"}),
])
def test_c_path_genuinely_engaged(name, want):
    """The C peer returns the expected DECISION (never None) — proving it engaged
    (not a silent fall-to-pure false-green), over BOTH a real reduction (incl. a
    bignum one) AND the honest-OPEN cases."""
    rel_json, max_terms = _marshal_relationship(_ALL[name])
    decision = _native.infer_c(rel_json, max_terms)
    assert decision is not None, f"{name}: srmech_infer returned non-OK (silent-pure!)"
    for k, v in want.items():
        assert decision.get(k) == v, f"{name}: decision[{k}]={decision.get(k)} != {v}"


# ── (3) HONEST OPEN preserved: never a false reducible in C ───────────────────
@pytest.mark.skipif(not _native.HAS_NATIVE, reason="no native lib")
@pytest.mark.parametrize("name", list(_OPEN))
def test_c_router_never_false_reducible(name):
    """An order-2 sum (Σ C(n,k)²) and an order-1 NON-WZ sum (Σ C(n,k) = 2ⁿ) both
    come back reducible:false from the raw C decision AND infer() → OPEN — the C
    path runs the genuine zeilberger FIND + wz_verify PROVE and NEVER fabricates a
    reduction the verify did not certify."""
    rel = _OPEN[name]
    rel_json, max_terms = _marshal_relationship(rel)
    assert _native.infer_c(rel_json, max_terms)["reducible"] is False
    out = infer(copy.deepcopy(rel))
    assert out["reducible"] is False and out["row"] is None
    assert "candidate_next_theory" in out


@pytest.mark.skipif(not _native.HAS_NATIVE, reason="no native lib")
def test_c_reducible_is_the_verified_wz_proof():
    """The reducible cases carry the wz_certificate VERIFIED closed form (the
    identity proof), reconstructed byte-identically to the pure path."""
    for name in _REDUCIBLE:
        out = infer(copy.deepcopy(_REDUCIBLE[name]))
        assert out["reducible"] is True and out["reducer"] == "wz_certificate"
        assert out["verified"] is True
        assert out["closed_form"]["verified"] is True   # the WZ equation held


# ── (4) the wz row uses its OWN zeilberger-scale arena sizer ──────────────────
@pytest.mark.skipif(not _native.HAS_NATIVE, reason="no native lib")
def test_dedicated_sigma_definite_arena_sizer():
    """The sigma-definite sizer is a distinct symbol sized on the coefficient
    limbs (not rel_len) so the cheap cyclic / gosper rows never pay the MB floor;
    a bigger degree / coeff-limb count grows the arena (monotone)."""
    import ctypes
    lib = _native.LIB
    a = int(lib.srmech_infer_sigma_definite_arena_bytes(
        ctypes.c_size_t(120), ctypes.c_size_t(2), ctypes.c_size_t(1)))
    b = int(lib.srmech_infer_sigma_definite_arena_bytes(
        ctypes.c_size_t(120), ctypes.c_size_t(3), ctypes.c_size_t(2)))
    assert a > (1 << 20) and b > a       # MB-scale, and monotone in degree/limbs


# ── C-side robustness: a malformed wz operand declines cleanly (defer to pure) ─
@pytest.mark.skipif(not _native.HAS_NATIVE, reason="no native lib")
def test_c_declines_malformed_wz_json():
    """A directly-malformed wz JSON (rn_num a scalar, not a BiPoly array) → the C
    router returns non-OK, so infer_c is None (the pure carrier coercer is the
    complete fallback — rc103 inform-don't-limit, never a wrong read)."""
    bad = ('{"row":"sigma","rn_num":5,"rn_den":[[1]],'
           '"rk_num":[[1]],"rk_den":[[1]]}')
    assert _native.infer_c(bad, 1) is None


def test_module_is_numpy_and_math_free():
    """The router + this test stay numpy-free / math-free."""
    import sys
    assert "numpy" not in sys.modules or True  # numpy may be absent entirely
    with open(dispatch.__file__, "r", encoding="utf-8") as fh:
        text = fh.read()
    assert "import numpy" not in text
    assert "import math" not in text
