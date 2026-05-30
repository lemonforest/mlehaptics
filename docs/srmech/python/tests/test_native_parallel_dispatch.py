"""C/Python parity for the Klein-4 four-sector PARALLEL dispatch (#771).

The gap-closer for srmech MS#20 rc7: rc6 added a Python-only 4-sector
parallel cascade dispatch (``srmech.amsc.cascade.parallel_sector_dispatch``);
under srmech's full-parity commitment the C library must do the same four-
sector dispatch NATIVELY (so srmech runs on a microcontroller with no host
Python). This module proves the C dispatch's four sector results equal
rc6's Python ``parallel_sector_dispatch`` **bit-for-bit** for the same body
math, plus sector-2 == ``cascade.chiral_dual``.

GIL/CALLBACK HAZARD — how these tests avoid it. The C dispatch spawns one
thread PER sector and invokes the body callback from each; invoking a Python
``CFUNCTYPE`` callback from a C-spawned thread is unsafe. So
``_native.cascade_parallel_sector_dispatch_c`` drives the C dispatch ONE
sector at a time (``n_sectors=1`` ⇒ a single-thread, identity-transform
call), composing the Klein-4 ``T_s`` transform via the native C atoms on
each side. The threaded multi-sector fan-out is validated separately from
the **C smoke test** (``c/test/test_srmech_parallel.c``) with a C-native
body — no Python callback crosses the thread boundary there. The per-sector
results are bit-identical to the multi-sector threaded dispatch (the sectors
are independent / order-free — the F233 invariant).

These tests SKIP cleanly when ``HAS_NATIVE`` is False (pure-Python wheel /
Pyodide / sdist without a toolchain).
"""

from __future__ import annotations

import pytest

from srmech.amsc import _native
from srmech.amsc.cascade import (
    chiral_dual,
    parallel_sector_dispatch,
)


pytestmark = pytest.mark.skipif(
    not _native.HAS_NATIVE
    or _native.LIB is None
    or not hasattr(_native.LIB, "srmech_cascade_parallel_sector_dispatch"),
    reason=(
        "native srmech_cascade_parallel_sector_dispatch not available "
        "(pure-Python wheel / Pyodide / sdist without a C toolchain, or a "
        "stale dll built before #771)"
    ),
)


# ----------------------------------------------------------------------
# Representative cascade bodies — the same four the rc6 Python acceptance
# test uses (the full F233 collapse-lattice 4 / 2 / 2 / 1).
# ----------------------------------------------------------------------


def _biaxial(seq):
    """Bi-axial: commutes with NEITHER axis -> 4 distinct sectors."""
    return [v + (i + 1) for i, v in enumerate(seq)]


def _iw7_symmetric(seq):
    """iω₇-symmetric -> {0,1} and {2,3} collapse (2 distinct)."""
    return [v * (i + 1) for i, v in enumerate(seq)]


def _gamma5_symmetric(seq):
    """γ₅-symmetric -> {0,2} and {1,3} collapse (2 distinct)."""
    s = list(seq)
    return [v + 1 for v in s[::-1]]


def _bi_symmetric(seq):
    """Bi-symmetric (identity) -> all four merge (1 distinct)."""
    return list(seq)


_BODIES = (_biaxial, _iw7_symmetric, _gamma5_symmetric, _bi_symmetric)
_X = [1.0, 2.0, 4.0, 8.0]


def _py_sectors(body, x, n_sectors=4):
    """The rc6 Python dispatch's sector-result list, ordered by sector."""
    dispatch = parallel_sector_dispatch(body, x, n_sectors=n_sectors)
    sectors = dispatch["sectors"]
    return [sectors[s]["result"] for s in sorted(sectors)]


# ----------------------------------------------------------------------
# The decisive parity invariant — C dispatch == rc6 Python bit-for-bit.
# ----------------------------------------------------------------------


def test_c_dispatch_equals_python_bit_for_bit():
    """The native C four-sector dispatch's results equal rc6's Python
    ``parallel_sector_dispatch`` bit-for-bit for the same body math."""
    for body in _BODIES:
        c_sectors = _native.cascade_parallel_sector_dispatch_c(body, _X, 4)
        py_sectors = _py_sectors(body, _X, 4)
        assert len(c_sectors) == 4
        for s, (c_res, py_res) in enumerate(zip(c_sectors, py_sectors)):
            c_list = [float(v) for v in c_res]
            py_list = [float(v) for v in py_res]
            assert c_list == py_list, (
                f"{body.__name__} sector {s}: C {c_list} != Python {py_list}"
            )


def test_c_sector2_is_chiral_dual_bit_exact():
    """Sector 2 (γ₅-only) of the native dispatch IS ``cascade.chiral_dual``
    bit-for-bit (the F232 2-rung object inside the F233 4-rung)."""
    for body in _BODIES:
        c_sectors = _native.cascade_parallel_sector_dispatch_c(body, _X, 4)
        sector2 = [float(v) for v in c_sectors[2]]
        f232 = [float(v) for v in chiral_dual(body, _X)]
        assert sector2 == f232, f"{body.__name__}: sector2 {sector2} != chiral_dual {f232}"


# ----------------------------------------------------------------------
# Fewer-sector dispatch + cap-at-4 + arg validation parity.
# ----------------------------------------------------------------------


@pytest.mark.parametrize("n_sectors", [1, 2, 3, 4])
def test_c_dispatch_truncated_sector_counts_match_python(n_sectors):
    """For n_sectors in 1..4 the C dispatch's first n_sectors results match
    Python's (the Z₄ slot truncation)."""
    c_sectors = _native.cascade_parallel_sector_dispatch_c(_biaxial, _X, n_sectors)
    py_sectors = _py_sectors(_biaxial, _X, n_sectors)
    assert len(c_sectors) == n_sectors
    for c_res, py_res in zip(c_sectors, py_sectors):
        assert [float(v) for v in c_res] == [float(v) for v in py_res]


def test_c_dispatch_cap_at_4():
    """n_sectors > 4 is rejected (cap-at-4; Klein-4 has no order-4+ elem)."""
    with pytest.raises(ValueError):
        _native.cascade_parallel_sector_dispatch_c(_biaxial, _X, 5)


def test_c_dispatch_lower_bound():
    """n_sectors < 1 and bool n_sectors are rejected."""
    with pytest.raises(ValueError):
        _native.cascade_parallel_sector_dispatch_c(_biaxial, _X, 0)
    with pytest.raises(ValueError):
        _native.cascade_parallel_sector_dispatch_c(_biaxial, _X, True)


def test_c_dispatch_empty_input():
    """Empty input: every sector dual is empty (parity with Python)."""
    c_sectors = _native.cascade_parallel_sector_dispatch_c(_bi_symmetric, [], 4)
    assert c_sectors == [[], [], [], []]


def test_c_dispatch_body_exception_propagates():
    """An exception raised by the body propagates out (not swallowed)."""
    def _bad(seq):
        raise ValueError("boom")

    with pytest.raises(ValueError, match="boom"):
        _native.cascade_parallel_sector_dispatch_c(_bad, _X, 4)
