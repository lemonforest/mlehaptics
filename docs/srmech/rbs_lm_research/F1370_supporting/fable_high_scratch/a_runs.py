"""Task A - the book's worked claims re-run through SHIPPED ops (functional equivalents) at HEAD, pure cell."""
import sys, math, importlib.util
from fractions import Fraction as F
sys.path.insert(0, "D:/GitHub/mlehaptics/docs/srmech/python")
import srmech
from srmech import _native
print("srmech", srmech.__version__, "HAS_NATIVE", _native.HAS_NATIVE, "numpy", "present" if importlib.util.find_spec("numpy") else "ABSENT")

print("\n[p.69 Ex 8.4] srmech.kepler.solve -> srmech.math.kepler.kepler_solve (moved; the book's spelling never existed)")
from srmech.math import kepler
for M in (1.0, math.pi / 3, 0.5):
    print(f"   kepler_solve(M={M:.6f}, e=0.3) = {kepler.kepler_solve(M, 0.3):.6f}")
print("   (the book's E3 = 0.99622 at unstated M; kepler_solve returns E only, no iteration trace)")

print("\n[p.48/p.195 Ex 5.9] srmech.cascade.shifted_circle_eigenvalues(n) -> NEVER SHIPPED; equivalent: 1 + cos_sin_2pi_k_over_n(n,k) (exact turn, Qalg)")
from srmech.math.qalg import cos_sin_2pi_k_over_n
for n in (4, 6):
    ok = True
    for k in range(n):
        c, s = cos_sin_2pi_k_over_n(n, k)
        re_, im = 1 + c, s                      # lambda_k = 1 + zeta^k
        lhs = im * im; rhs = 2 * re_ - re_ * re_   # Im^2 = 2Re - Re^2  <=> |lambda-1| = 1
        ok = ok and (lhs == rhs)
    print(f"   n={n}: Im^2 == 2Re - Re^2 exactly for all k: {ok} (exact cyclotomic carrier, no float)")

print("\n[p.184/p.223] srmech.qm.bell.chsh_operator_norm -> srmech.physics.qm.bell.chsh_operator_norm (moved rc381; alias dropped rc382)")
try:
    from srmech.physics.qm.bell import chsh_operator_norm
    v = chsh_operator_norm()
    print(f"   chsh_operator_norm() = {v!r}; 2*sqrt(2) = {2 * math.sqrt(2):.15f}; diff = {abs(float(v) - 2 * math.sqrt(2)):.1e}")
except Exception as ex:
    print("   FAILED in pure cell:", type(ex).__name__, ex)

print("\n[p.184] srmech.qm.relativistic.schwarzschild_isco_efficiency -> NEVER SHIPPED (not at 0.4.2, not at HEAD); closed form via Class-N sqrt:")
from srmech.math.rational import sqrt as nsqrt
r = nsqrt(F(8, 9), precision=60) if True else None
try:
    val = 1 - F(r.numerator, r.denominator)
    print(f"   1 - sqrt(8/9) via srmech.math.rational.sqrt = {float(val):.10f} (book: 0.0571909584)")
except Exception as ex:
    print("   sqrt carrier:", type(r).__name__, r, ex)

print("\n[p.60/p.200 Thm 7.2] srmech.asymptotic_dof.toy_modulation_time -> NEVER SHIPPED; the closed-form integral, exact rational:")
from srmech.math.rational import rational_div, rational_pow_uint
def T(alpha, c, eps, gap):
    # T = (1/c) * (1/(alpha-1)) * (eps^(1-alpha) - gap^(1-alpha)); exact Fraction (Class N)
    return F(1, c) * F(1, alpha - 1) * (F(1, eps ** (alpha - 1)) - F(1, gap ** (alpha - 1)))
print(f"   alpha=2, c=1, eps=1/1000, gap=1: T = {T(2, 1, F(1, 1000), F(1))}   (book: 999)")
print(f"   alpha=3, c=1, eps=1/1000, gap=1: T = {T(3, 1, F(1, 1000), F(1))}   (book: 499999.5)")
print("   -> the claim is DERIVED-verifiable without the op; it is the elementary integral of (gap)^-alpha")

print("\n[p.94/p.211] srmech.precession.omega_sub -> NEVER SHIPPED; 2*pi/T_sub with srmech's own pi:")
from srmech.math.rational import _pi_rational
pn, pd = _pi_rational(30)
T_sub_s = F(10984, 100) * 10 ** 9 * F(31557, 10000) * 10 ** 7
w = 2 * F(pn, pd) / T_sub_s
print(f"   omega_sub = {float(w):.4e} rad/s (book: 1.81e-18); spike163 constant OMEGA_SUB in docs/srmech/notes/spike163_cross_substrate_scale_test.py")

print("\n[p.125] srmech.catalogue.class_frequency -> NEVER SHIPPED; shipped census: srmech.describe()['classes'] and the class catalog")
import srmech.introspect as I
d = I.describe()
print("   describe()['classes'] =", d.get("classes"))

print("\n[p.149-150/p.229] srmech.amsc.verify_attestation -> NEVER SHIPPED under that name; shipped: srmech.amsc.catalog.attestation_audit + srmech.amsc.format.validate_mpr_record")
from srmech.amsc.catalog import attestation_audit
try:
    a = attestation_audit("cosmos_validation")
    keys = sorted(a.keys())[:8]
    print("   attestation_audit('cosmos_validation') keys:", keys)
    for k in ("n_records", "ok", "all_ok", "status", "verified"):
        if k in a: print(f"   {k} = {a[k]}")
except Exception as ex:
    print("   attestation_audit failed:", type(ex).__name__, ex)

print("\n[p.183 Table 1] the fourteen amsc.<module> spellings -> srmech.math.<module> (rc372/rc373) except A (amsc.format, still there), H (amsc._native -> srmech._native, rc376), E (amsc.naming -> srmech.introspect.naming, rc367)")
import srmech.math.cyclic as cy, srmech.math.primes as pr, srmech.math.tlv as tlv, srmech.math.dispatch as dp, srmech.math.search as se, srmech.math.template as tp, srmech.introspect.naming as nm
print("   I mod_add/gcd/lcm:", all(hasattr(cy, f) for f in ("mod_add", "mod_mul", "mod_pow", "mod_inv", "gcd", "lcm")), "| J is_prime/factor/cyclic_period:", all(hasattr(pr, f) for f in ("is_prime", "factor", "cyclic_period")),
      "| B tlv_pack:", hasattr(tlv, "tlv_pack"), "| D match:", hasattr(dp, "match"), "| G byte_search:", hasattr(se, "byte_search"), "| F render:", hasattr(tp, "render"), "| E lookup:", hasattr(nm, "lookup"))
from srmech.amsc.format import read_ndjson
print("   C read_ndjson in srmech.amsc.format:", callable(read_ndjson), "| H srmech_version():", hasattr(_native, "srmech_version") or [n for n in dir(_native) if "version" in n][:3])
