"""rc59 — the EllBase theta-factor foundation of the ELLIPTIC F929 reduction row.

Numpy-free + math-free: the exact ``EllMonomial`` Laurent-monomial algebra and
the ``Theta`` quasi-periodicity / inversion canonicalization, cross-checked
against the exact-ℚ truncated modified-theta product (no float in the carrier;
the ``float(...)`` here is only the test's convergence tolerance on the
quasi-periodicity-by-one limit)."""

import io
import os
import re
import tokenize

from srmech.amsc.ellbase import EllMonomial as M, Theta, _modified_theta_trunc
from srmech.amsc.q import Q

_VALS = {"q": Q(2, 1), "p": Q(1, 9), "a": Q(3, 5), "b": Q(4, 7)}
_N = 60


# ── EllMonomial exact multiplicative algebra ──────────────────────────────────
def test_ellmonomial_algebra():
    a, q, p = M.symbol("a"), M.symbol("q"), M.symbol("p")
    assert (a * q).inv() == a.inv() * q.inv()
    assert (a * q * a) == a ** 2 * q                       # exponents merge
    assert (q ** 2 * p ** -1).eval({"q": Q(3, 1), "p": Q(2, 1)}) == Q(9, 2)
    assert (M.scalar(Q(-2, 3)) * a ** 2).eval({"a": Q(3, 1)}) == Q(-6, 1)
    assert M.one().is_unit and (a * a.inv()).is_unit
    assert a.exp_of("a") == 1 and a.exp_of("z") == 0


def test_ellmonomial_pow_and_inverse_identities():
    z = M.symbol("a", 2) * M.symbol("q", -3) * M.scalar(Q(5, 2))
    assert z ** 0 == M.one()
    assert z ** -1 == z.inv()
    assert (z ** 3) * (z ** -3) == M.one()
    assert z * z.inv() == M.one()


# ── Theta.canonicalize PRESERVES the modified-theta value (load-bearing) ──────
def test_theta_canonicalize_preserves_value():
    a, q, p = M.symbol("a"), M.symbol("q"), M.symbol("p")
    z = p ** 3 * a * q ** 2                                # p-exponent 3
    pref, th0 = Theta(z).canonicalize()
    assert th0.arg.exp_of("p") == 0                        # canonical: p-exp 0
    direct = Theta(z).eval_trunc(_VALS, _N)
    via = pref.eval(_VALS) * th0.eval_trunc(_VALS, _N)
    assert abs(float(via / direct) - 1.0) < 1e-9          # the rewrite holds


def test_theta_orientation_shared_rep():
    """θ(z₀) and θ(z₀⁻¹) canonicalize to the SAME theta (the inversion rewrite),
    each with its own value-preserving prefactor."""
    a, q = M.symbol("a"), M.symbol("q")
    z0 = a * q ** 2
    pa, ta = Theta(z0).canonicalize()
    pb, tb = Theta(z0.inv()).canonicalize()
    assert ta == tb
    ra = (pa.eval(_VALS) * ta.eval_trunc(_VALS, _N)) / Theta(z0).eval_trunc(_VALS, _N)
    rb = (pb.eval(_VALS) * tb.eval_trunc(_VALS, _N)) / Theta(z0.inv()).eval_trunc(_VALS, _N)
    assert abs(float(ra) - 1.0) < 1e-9 and abs(float(rb) - 1.0) < 1e-9


def test_theta_canonical_unique_and_general_k():
    a, p = M.symbol("a"), M.symbol("p")
    # same argument by two construction routes → identical (prefactor, theta)
    assert Theta(p ** 2 * a).canonicalize() == Theta(a * p ** 2).canonicalize()
    # the general-k prefactor sign/p-power: θ(p²a) reduces to θ(a) with p-exp 0
    pref, th0 = Theta(p ** 2 * a).canonicalize()
    assert th0 == Theta(a) or th0 == Theta(a.inv())


# ── the elliptic shifted factorial (theta-Pochhammer) ─────────────────────────
def test_theta_pochhammer():
    a, q = M.symbol("a"), M.symbol("q")
    assert Theta.pochhammer(a, 0) == ()
    assert Theta.pochhammer(a, 3) == (Theta(a), Theta(a * q), Theta(a * q ** 2))


# ── the exact-ℚ truncated modified theta (the eval oracle) ────────────────────
def test_modified_theta_trunc_quasiperiodicity():
    """θ(p·z) = −z⁻¹·θ(z) in the truncation limit (the build-pin, re-asserted)."""
    z, p = Q(3, 5), Q(1, 8)
    th_z = _modified_theta_trunc(z, p, _N)
    th_pz = _modified_theta_trunc(z * p, p, _N)
    assert abs(float(th_pz / (-(Q(1, 1) / z) * th_z)) - 1.0) < 1e-9
    assert _modified_theta_trunc(z, p, 0) == Q(1, 1)      # empty product


# ── discipline: no numpy / no math / no abs() in the carrier source ───────────
def test_ellbase_source_is_numpy_math_abs_free():
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    src = os.path.join(here, "srmech", "amsc", "ellbase.py")
    with tokenize.open(src) as fh:
        text = fh.read()
    assert "import numpy" not in text
    assert "import math" not in text
    assert re.search(r"abs\([^)]", text) is None          # no bare abs() CALL
