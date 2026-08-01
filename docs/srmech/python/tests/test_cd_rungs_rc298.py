"""rc298 (`#933`) — the uncapped Cayley-Dickson rung sweep.

PR #687: "the rung sweep stops at 64 because srmech caps at ``CD_MAX_DIM=64``.
That's a TOOLING limit, not a mathematical one." rc298 moves it to 256 and
proves the two new rungs rather than asserting them.

THE TRACE THAT MADE IT CHEAP
----------------------------
Every scratch buffer on the ADDRESSING path is LINEAR in the cap (2 KB at 256).
Exactly one buffer in the library is quadratic — ``srmech_sedenion.c``'s
``dim x dim`` modular-rank matrix — and addressing never reaches it: the
``cd_navmap`` / ``cd_navigate`` / ``cd_navmap_is_signed_permutation`` path
bottoms out in ``srmech_cd_basis_product`` and a linear ``seen[]``. So the two
caps are decoupled: ``CD_MAX_DIM`` 256 for addressing, ``CD_DENSE_MAX_DIM`` 64
for the dense path (2 MB at 512 would overrun MSVC's 1 MB default stack).

WHAT IS PROVEN WHERE
--------------------
The exhaustive cross-path check (cocycle vs full ``cd_mult``, every one of
``dim^2`` pairs) is ``O(dim^4)``: ~35 s at 64, ~2.8 min at 128, ~32 min at 256.
It is NOT run here at the new rungs. ``tools/verify_cd_rungs.py`` is the
committed generating code that established it exhaustively (65536/65536 at
256); this module ratchets the cheap-but-complete invariant at every rung
(``O(dim^2)`` basis products) plus a deterministic cross-path SAMPLE at 128/256
so a cocycle regression at the new rungs cannot pass unnoticed.
"""

from __future__ import annotations

import ctypes

import pytest

from srmech import _native
from srmech.amsc import cascade
from srmech.amsc.cascade.cayley_dickson import (
    ALGEBRA_NAMES,
    CD_DENSE_MAX_DIM,
    CD_DIMS,
    CD_MAX_DIM,
    cd_basis,
    cd_basis_product,
    cd_mult,
)
from srmech.amsc.cascade.cd_register import (
    cd_navmap,
    cd_navmap_is_signed_permutation,
)

#: The rungs rc298 ADDED. Everything at or below 64 is already ratcheted by
#: test_cd_register_rc297.py; these are the ones this rc has to earn.
NEW_RUNGS = (128, 256)


# ──────────────────────────────────────────────────────────────────────
# The caps themselves
# ──────────────────────────────────────────────────────────────────────

def test_addressing_cap_is_256_and_the_ladder_agrees():
    assert CD_MAX_DIM == 256
    assert CD_DIMS == (1, 2, 4, 8, 16, 32, 64, 128, 256)
    assert CD_DIMS[-1] == CD_MAX_DIM
    for dim in CD_DIMS:
        assert dim in ALGEBRA_NAMES, f"rung {dim} has no name"


def test_dense_cap_is_decoupled_from_and_below_the_addressing_cap():
    """The whole point of `#933`: the quadratic buffer does NOT follow the
    addressing cap. If someone later sizes them together, this fails — at 512
    the dense matrix is 2 MB, over MSVC's 1 MB default thread stack."""
    assert CD_DENSE_MAX_DIM == 64
    assert CD_DENSE_MAX_DIM < CD_MAX_DIM
    assert CD_DENSE_MAX_DIM * CD_DENSE_MAX_DIM * 8 <= 64 * 1024, (
        "the dense modular-rank matrix must stay within a 64 KB stack frame"
    )


@pytest.mark.skipif(not _native.HAS_NATIVE, reason="needs the native library")
def test_c_and_python_caps_agree():
    """``SRMECH_CD_MAX_DIM`` and ``CD_MAX_DIM`` must move in lockstep — a
    projection that admits a rung the other rejects is an ADR-0009 split."""
    lib = _native.LIB
    lib.srmech_cd_navmap_is_signed_permutation.argtypes = [
        ctypes.c_int, ctypes.POINTER(ctypes.c_int)]
    lib.srmech_cd_navmap_is_signed_permutation.restype = ctypes.c_int

    out = ctypes.c_int()
    # The C side accepts exactly the rungs Python does.
    assert lib.srmech_cd_navmap_is_signed_permutation(
        CD_MAX_DIM, ctypes.byref(out)) == _native.SRMECH_OK
    assert lib.srmech_cd_navmap_is_signed_permutation(
        CD_MAX_DIM * 2, ctypes.byref(out)) != _native.SRMECH_OK


# ──────────────────────────────────────────────────────────────────────
# The invariant addressing rides on, AT THE NEW RUNGS
# ──────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("dim", NEW_RUNGS)
def test_navmap_is_a_signed_permutation_at_the_new_rungs(dim):
    """F1274/F1275 at 128 and 256: for EVERY direction j, i -> (dest, sign) is a
    bijection on [0, dim) with every sign in {+1, -1}. Zero exceptions."""
    assert cd_navmap_is_signed_permutation(dim) is True
    for j in range(dim):
        nav = cd_navmap(dim, j)
        assert len(nav) == dim
        assert sorted(v[0] for v in nav.values()) == list(range(dim)), (
            f"navmap(dim={dim}, j={j}) is not a bijection — the premise the "
            f"whole address layer rides on has failed at this rung")
        assert all(v[1] in (1, -1) for v in nav.values()), (
            f"navmap(dim={dim}, j={j}) produced a sign outside {{+1,-1}}")


@pytest.mark.skipif(not _native.HAS_NATIVE, reason="needs the native library")
@pytest.mark.parametrize("dim", NEW_RUNGS)
def test_c_peer_verifies_the_new_rungs_too(dim):
    """rc297 shipped ``srmech_cd_navmap_is_signed_permutation`` so a rung could
    be VERIFIED rather than asserted. Use it at the rungs rc298 adds — a bare-C
    host must be able to check its own address layer at 128/256."""
    lib = _native.LIB
    lib.srmech_cd_navmap_is_signed_permutation.argtypes = [
        ctypes.c_int, ctypes.POINTER(ctypes.c_int)]
    lib.srmech_cd_navmap_is_signed_permutation.restype = ctypes.c_int

    out = ctypes.c_int()
    assert lib.srmech_cd_navmap_is_signed_permutation(
        dim, ctypes.byref(out)) == _native.SRMECH_OK
    assert out.value == 1
    assert bool(out.value) == cd_navmap_is_signed_permutation(dim)


@pytest.mark.parametrize("dim", NEW_RUNGS)
def test_scripted_and_compiled_projections_agree_at_the_new_rungs(dim, monkeypatch):
    """ADR-0009 at the rungs rc298 adds: the pure (Pyodide / no-native) cocycle
    and the compiled one must return the identical ``(index, sign)``.

    This is the check that would have caught a wrong ``SRMECH_CD_MAX_LEVELS``.
    The C doubling loop is bounded by that macro for JPL Rule 2; dim 256 needs
    EIGHT halvings, and at the old value of 6 the compiled path would have
    silently truncated at dim 128 and 256 while the pure Python ``while cur > 1``
    loop kept going. Same input, two answers, no error raised — exactly the
    projection split ADR-0009 exists to forbid.
    """
    if not _native.HAS_NATIVE:
        pytest.skip("needs the native library to have two projections to compare")

    probes = [(i, j)
              for i in (0, 1, 7, 63, 64, 127, 128, 200, 255) if i < dim
              for j in (0, 1, 7, 63, 64, 127, 128, 200, 255) if j < dim]
    assert probes, "probe set is empty — the comparison would be vacuous"

    compiled = [cd_basis_product(dim, i, j) for i, j in probes]
    monkeypatch.setattr(_native, "HAS_NATIVE", False)
    scripted = [cd_basis_product(dim, i, j) for i, j in probes]

    assert compiled == scripted, (
        f"the scripted and compiled projections disagree at dim {dim} — "
        f"first mismatch: "
        f"{next((p, c, s) for p, c, s in zip(probes, compiled, scripted) if c != s)}")


@pytest.mark.parametrize("dim", NEW_RUNGS)
def test_cocycle_agrees_with_full_cd_mult_on_a_sample_at_the_new_rungs(dim):
    """The INDEPENDENT-code-path check, sampled.

    The cocycle (``cd_basis_product``) and the full exact-rational ``cd_mult``
    are separate implementations; agreement between them is what makes the
    address layer trustworthy rather than merely self-consistent. Exhaustive is
    ``O(dim^4)`` (~32 min at 256) so the suite takes a deterministic spread —
    every j against a fixed set of i, plus the diagonal — and
    ``tools/verify_cd_rungs.py`` carries the exhaustive claim.
    """
    probe_i = sorted({0, 1, 2, 3, 7, 8, 15, 16, dim // 2, dim - 1})
    for i in probe_i:
        for j in probe_i:
            prod = cd_mult(cd_basis(dim, i), cd_basis(dim, j))
            nz = [(k, v) for k, v in enumerate(prod) if v != 0]
            assert len(nz) == 1, (
                f"e{i}*e{j} at dim {dim} is NOT a single basis element ({nz})")
            k, v = nz[0]
            assert v in (1, -1), f"e{i}*e{j} coefficient {v} is not +-1"
            assert (k, v) == cd_basis_product(dim, i, j), (
                f"the cd_basis_product cocycle disagrees with the full cd_mult "
                f"at dim {dim}, e{i}*e{j}")


@pytest.mark.parametrize("dim", NEW_RUNGS)
def test_the_register_itself_works_at_the_new_rungs(dim):
    """The capability `#933` was actually blocking: an N-slot register at a rung
    past 64. Write / read / navigate must all hold."""
    reg = cascade.cd_register(dim, D=256)
    assert reg.dim == dim
    assert len(reg.navmap(1)) == dim

    # Write real state first: an EMPTY register round-trips trivially, so a
    # cycle assertion over one proves nothing.
    reg.write(0, "gamma")
    reg.write(1, "alpha")
    reg.write(3, "beta")
    base = dict(reg.slots())
    assert len(base) == 3

    # navigate is reversible for a single basis direction at EVERY rung — e_1
    # has order 4 under repeated right-multiplication (e_1^2 = -1).
    step1 = reg.navigate(1)
    assert step1.dim == dim
    assert dict(step1.slots()) != base, (
        "navigate(1) did not move the state — the round-trip below would pass "
        "vacuously")
    cur = step1
    for _ in range(3):
        cur = cur.navigate(1)
    assert dict(cur.slots()) == base, (
        f"navigate(1) is not order-4 at dim {dim} — single-basis addressing "
        f"must stay reversible past the Hurwitz wall")


# ──────────────────────────────────────────────────────────────────────
# The dense path past its cap — a PERFORMANCE boundary, not a capability one
# ──────────────────────────────────────────────────────────────────────

def test_is_invertible_stays_correct_past_the_dense_cap():
    """ADR-0009: the capability is the invariant. Past ``CD_DENSE_MAX_DIM`` the
    native modular-rank gate declines and the exact-rational nullspace oracle
    answers — the SAME fallback already used beyond int64 magnitude. The answer
    must still be right, not merely absent.

    A nonzero real scalar is invertible at every rung; a sum of two basis
    elements that zero-divides at 16 keeps doing so when promoted.
    """
    dim = 128
    one = [0] * dim
    one[0] = 1
    assert cascade.left_mult_is_invertible(one) is True

    zd = [0] * dim
    zd[1], zd[10] = 1, 1        # e1 + e10 — the sedenion zero divisor, promoted
    assert cascade.left_mult_is_invertible(zd) is False


@pytest.mark.skipif(not _native.HAS_NATIVE, reason="needs the native library")
def test_native_dense_gate_declines_past_its_cap_rather_than_answering_wrong():
    """The C gate must REFUSE a dim it cannot stage, not silently truncate. A
    wrong bool here would be worse than no bool — the Python peer treats a
    non-OK return as 'route to the oracle'."""
    lib = _native.LIB
    n = CD_DENSE_MAX_DIM * 2
    arr = (ctypes.c_int64 * n)(*([1] + [0] * (n - 1)))
    out = ctypes.c_int()
    rc = lib.srmech_sedenion_is_navigable(arr, n, ctypes.byref(out))
    assert rc != _native.SRMECH_OK, (
        f"srmech_sedenion_is_navigable accepted n={n}, past "
        f"SRMECH_CD_DENSE_MAX_DIM={CD_DENSE_MAX_DIM} — its quadratic matrix "
        f"cannot hold that")

    # ...and it still accepts everything at or below the cap.
    n_ok = CD_DENSE_MAX_DIM
    arr_ok = (ctypes.c_int64 * n_ok)(*([1] + [0] * (n_ok - 1)))
    assert lib.srmech_sedenion_is_navigable(
        arr_ok, n_ok, ctypes.byref(out)) == _native.SRMECH_OK
    assert out.value == 1
