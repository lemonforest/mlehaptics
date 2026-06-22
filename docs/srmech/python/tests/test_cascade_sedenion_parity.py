"""Sedenion address-layer C/Python parity (v0.9.0rc12; UPSTREAM §31 / F465+F468).

rc12 ships the C peer of the SedenionRegister "address algebra" — the navigation
+ reversibility-gate a C-only host needs to run Siona's address layer:

  * ``srmech_sedenion_navmap``     vs  ``SedenionRegister.navmap``
  * ``srmech_sedenion_navigate``   vs  ``SedenionRegister.navigate`` routing
  * ``srmech_sedenion_is_navigable`` vs the exact-rational ``left_mult_kernel``
    emptiness oracle (the C side decides invertibility by BIGNUM-FREE modular rank;
    this attests the bool is bit-identical to the Fraction-nullspace reference).

The C peer is exercised only when ``HAS_NATIVE`` and the loaded libsrmech exposes
the rc12 symbols (a stale lib loads fine but skips cleanly). numpy-free.
"""
import ctypes
from fractions import Fraction

import pytest

from srmech.amsc import _native
from srmech.amsc._native import HAS_NATIVE
from srmech.amsc.cascade import cayley_dickson as cd
from srmech.amsc.cascade.sedenion_register import SedenionRegister, NUM_SLOTS

_SED_NATIVE = (
    HAS_NATIVE
    and _native.LIB is not None
    and hasattr(_native.LIB, "srmech_sedenion_navmap")
    and hasattr(_native.LIB, "srmech_sedenion_navigate")
    and hasattr(_native.LIB, "srmech_sedenion_is_navigable")
)

SKIP_IF_NO_SED_NATIVE = pytest.mark.skipif(
    not _SED_NATIVE, reason="installed libsrmech predates the v0.9.0rc12 sedenion symbols"
)


def _c_navmap(j):
    dest = (ctypes.c_int * NUM_SLOTS)()
    sign = (ctypes.c_int * NUM_SLOTS)()
    rc = _native.LIB.srmech_sedenion_navmap(j, dest, sign)
    assert rc == _native.SRMECH_OK
    return {i: (dest[i], sign[i]) for i in range(NUM_SLOTS)}


def _c_navigate(j, slots):
    in_s = sorted(slots.items())
    cnt = len(in_s)
    isl = (ctypes.c_int * cnt)(*[s for s, _ in in_s])
    isg = (ctypes.c_int * cnt)(*[g for _, (k, g) in in_s])
    keys = [k for _, (k, g) in in_s]
    osl = (ctypes.c_int * cnt)()
    osg = (ctypes.c_int * cnt)()
    rc = _native.LIB.srmech_sedenion_navigate(j, isl, isg, cnt, osl, osg)
    assert rc == _native.SRMECH_OK
    return {osl[m]: (keys[m], osg[m]) for m in range(cnt)}


def _c_is_navigable(int_vec):
    n = len(int_vec)
    arr = (ctypes.c_int64 * n)(*int_vec)
    out = ctypes.c_int()
    rc = _native.LIB.srmech_sedenion_is_navigable(arr, n, ctypes.byref(out))
    assert rc == _native.SRMECH_OK, f"rc={rc} for {int_vec}"
    return out.value == 1


def _clear_denominators(x):
    from srmech.amsc.cyclic import gcd
    den = 1
    for v in x:
        den = den * v.denominator // gcd(den, v.denominator)
    return [int(v * den) for v in x]


# ── structural facts that hold regardless of native (pure-Python references) ──

def test_navmap_is_xor_permutation():
    for j in range(NUM_SLOTS):
        m = SedenionRegister().navmap(j)
        assert sorted(k for k, _ in m.values()) == list(range(NUM_SLOTS))  # permutation
        for i, (k, s) in m.items():
            assert k == (i ^ j) and s in (1, -1)


def test_basis_units_navigable_zero_vector_not():
    for j in range(NUM_SLOTS):
        e = [Fraction(0)] * NUM_SLOTS
        e[j] = Fraction(1)
        assert cd.left_mult_is_invertible(e) is True            # any unit e_j is navigable
    assert cd.left_mult_is_invertible([Fraction(0)] * NUM_SLOTS) is False


# ── C/Python parity (skips cleanly when the rc12 native symbols are absent) ──

@SKIP_IF_NO_SED_NATIVE
def test_navmap_parity():
    for j in range(NUM_SLOTS):
        assert _c_navmap(j) == SedenionRegister().navmap(j)


@SKIP_IF_NO_SED_NATIVE
def test_navigate_parity():
    r = SedenionRegister()
    r.write(0, "a"); r.write(3, "b", sign=-1); r.write(10, "c"); r.write(7, "d", sign=-1)
    for j in range(NUM_SLOTS):
        assert _c_navigate(j, r.slots()) == r.navigate(j)._slots


@SKIP_IF_NO_SED_NATIVE
def test_is_navigable_parity_vs_fraction_oracle():
    cases = []
    for j in range(NUM_SLOTS):                                   # basis units
        cases.append(cd.cd_basis(NUM_SLOTS, j))
    for i in range(NUM_SLOTS):                                   # e_i ± e_j sums
        for j in range(i + 1, NUM_SLOTS):
            for s in (1, -1):
                v = [Fraction(0)] * NUM_SLOTS
                v[i] = Fraction(1); v[j] = Fraction(s)
                cases.append(tuple(v))
    w = cd.sedenion_zero_divisor_witness()                      # the zero divisor (False)
    cases.append(w["x"]); cases.append(w["y"])
    for x in cases:
        # the Fraction-nullspace reference (NOT the dispatching wrapper).
        oracle = len(cd.left_mult_kernel(x)) == 0
        assert _c_is_navigable(_clear_denominators(x)) == oracle
