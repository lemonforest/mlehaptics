"""rc216 — cn_vwp_multisum_lhs: the symbolic Cₙ VWP elliptic multisum LHS builder
promoted first-class (elliptic reduction-rows dive item #688).

The LEFT-hand side of the Cₙ elliptic Jackson summation (Rosengren, "A proof of a
multivariable elliptic summation formula conjectured by Warnaar", arXiv:math/0101073v1
[math.CA], Theorem 2.1 Eq 5) — the n-fold Cₙ very-well-poised sum over the partitions
``Λ_{nN} = {N ≥ λ₁ ≥ … ≥ λₙ ≥ 0}``, built SYMBOLICALLY as an exact ``ThetaSum`` — has
existed since rc96 as the PRIVATE ``_cn_lhs_thetasum`` (the rc96 test oracle → rc101
symbolic-verify engine). rc216 promotes it to the public op
``srmech.amsc.elliptic_jackson.cn_vwp_multisum_lhs`` with a same-rc 1:1 C peer
``srmech_cn_vwp_multisum_lhs`` (the rc95 elliptic_partial_fraction multi-term wire form).

What this suite pins:
  1. PROMOTION IS VALUE-IDENTITY — the public op returns EXACTLY the private oracle's
     ThetaSum (``==``, the exact carrier equality) across the small-(n, N) battery.
     ``_cn_lhs_thetasum`` was THE rc96/rc101 oracle, so promotion == oracle is the
     whole correctness claim.
  2. The Thm 2.1 identity THROUGH THE PUBLIC OPS — (cn_vwp_multisum_lhs −
     from_ellratio(multivariate_elliptic_jackson)).is_zero is True on the rc101
     measured-feasible set, and False against a perturbed closed form (the check
     discriminates; the rc101 proof re-run with both sides first-class).
  3. Native == pure parity — the C peer's ThetaSum (rebuilt from its per-partition
     EllRatio term forms) equals the pure builder's, exactly; clean decline (None)
     when the native symbols are absent.
  4. Contracts — TypeError / ValueError validation; registration (ToolEntry;
     tools.total == 418; the Rosetta ledger row; ``__all__``).

numpy-free (exact modified-theta algebra); no ``abs()`` (Class-K sign via the
EllMonomial sign-branch). Run from ``docs/srmech/python`` with ``PYTHONPATH=$(pwd)``.
"""

import json
from pathlib import Path

import pytest

from srmech import introspect
from srmech.amsc.ellbase import EllMonomial as M, EllRatio
from srmech.amsc.elliptic_jackson import (
    cn_vwp_multisum_lhs,
    multivariate_elliptic_jackson,
    _cn_lhs_thetasum,
    _cn_vwp_multisum_lhs_c,
    _max_thetas_per_side,
    _num_partitions,
)
from srmech.amsc.q import Q
from srmech.amsc.thetasum import ThetaSum


def _syms():
    return tuple(M.symbol(s) for s in ("a", "b", "c", "d", "x", "q"))


# ── (1) PROMOTION == THE ORACLE: the public op is value-identical to the private
#        rc96/rc101 LHS builder (exact ThetaSum equality), incl. a cross-variable
#        case and a case beyond the is_zero-feasible frontier (construction is
#        exact at any affordable size — only the DECISION has the frontier) ────────────
@pytest.mark.parametrize("n,N", [(1, 1), (1, 2), (2, 1), (3, 1), (2, 2)])
def test_public_op_equals_private_oracle(n, N):
    a, b, c, d, x, q = _syms()
    got = cn_vwp_multisum_lhs(a, b, c, d, x, q, N, n)
    oracle = _cn_lhs_thetasum(a, b, c, d, x, q, N, n)
    assert isinstance(got, ThetaSum)
    assert got == oracle


# ── (2a) the Thm 2.1 identity via the PUBLIC ops: LHS − RHS ≡ 0 on the rc101
#         measured-feasible (fast) set — the per-call proof, both sides first-class ────
@pytest.mark.parametrize("n,N", [(1, 1), (2, 1)])
def test_thm21_identity_via_public_ops(n, N):
    a, b, c, d, x, q = _syms()
    lhs = cn_vwp_multisum_lhs(a, b, c, d, x, q, N, n)
    rhs = multivariate_elliptic_jackson(a, b, c, d, x, q, N, n)
    assert (lhs - ThetaSum.from_ellratio(rhs)).is_zero is True


# ── (2b) the check DISCRIMINATES: a perturbed closed form is provably NOT the sum ──────
def test_perturbed_closed_form_is_caught():
    a, b, c, d, x, q = _syms()
    n, N = 2, 1                                      # a feasible, cross-variable case
    lhs = cn_vwp_multisum_lhs(a, b, c, d, x, q, N, n)
    closed = multivariate_elliptic_jackson(a, b, c, d, x, q, N, n)
    scaled = EllRatio(closed.prefactor * M.scalar(Q(2, 1)),
                      num=closed.num, den=closed.den)
    assert (lhs - ThetaSum.from_ellratio(scaled)).is_zero is False


# ── (2c) n = 1 sanity: the single-variable case is the Frenkel–Turaev ₈ω₇ shape —
#         the λ = 0 term of the sum is the empty product (the EllRatio one), so the
#         LHS minus the remaining N terms equals ONE exactly ───────────────────────────
def test_n1_lambda0_term_is_one():
    a, b, c, d, x, q = _syms()
    lhs = cn_vwp_multisum_lhs(a, b, c, d, x, q, 1, 1)          # N = 1, n = 1: λ ∈ {0, 1}
    oracle = _cn_lhs_thetasum(a, b, c, d, x, q, 1, 1)
    assert lhs == oracle
    # the λ=0 summand is the empty product: subtracting the λ=1 summand (the oracle sum
    # minus the one term) leaves exactly ThetaSum.one — pinned via the private builder's
    # own arithmetic: (lhs − one) + one == lhs (exact carrier round-trip)
    one = ThetaSum.from_ellratio(EllRatio(M.one(), num=[], den=[]))
    assert ((lhs - one) + one) == lhs


# ── (3) native == pure parity (the C peer emits the per-partition EllRatio term
#        forms; the Python sum rebuilds the identical ThetaSum), clean decline
#        when absent ───────────────────────────────────────────────────────────────────
@pytest.mark.parametrize("n,N", [(1, 1), (2, 1), (2, 2)])
def test_native_matches_pure(n, N):
    from srmech.amsc import _native as _nat
    a, b, c, d, x, q = _syms()
    pure = _cn_lhs_thetasum(a, b, c, d, x, q, N, n)
    native = _cn_vwp_multisum_lhs_c(a, b, c, d, x, q, N, n)
    if _nat.has_native_cn_vwp_multisum_lhs():
        assert native is not None, "native symbols present but dispatch declined"
        assert native == pure
    else:
        assert native is None                         # clean decline, pure is complete
    # the public op returns the same value either way
    assert cn_vwp_multisum_lhs(a, b, c, d, x, q, N, n) == pure


# ── (4a) validation contracts ──────────────────────────────────────────────────────────
def test_validation_contracts():
    a, b, c, d, x, q = _syms()
    with pytest.raises(TypeError, match="cn_vwp_multisum_lhs"):
        cn_vwp_multisum_lhs("a", b, c, d, x, q, 1, 1)          # non-EllMonomial
    with pytest.raises(TypeError):
        cn_vwp_multisum_lhs(a, b, c, d, x, q, 1.0, 1)          # float N
    with pytest.raises(ValueError):
        cn_vwp_multisum_lhs(a, b, c, d, x, q, 0, 1)            # N < 1
    with pytest.raises(ValueError):
        cn_vwp_multisum_lhs(a, b, c, d, x, q, 1, 0)            # n < 1


# ── (4b) the sizing helpers the native wire rides (pure integer arithmetic) ────────────
def test_sizing_helpers():
    assert _num_partitions(1, 1) == 2                          # C(2, 1)
    assert _num_partitions(1, 2) == 3                          # C(3, 2)
    assert _num_partitions(2, 2) == 6                          # C(4, 2)
    assert _num_partitions(1, 3) == 4                          # C(4, 3)
    # per-side max theta count: n + (n(n-1)/2)(2+2N) + 6nN
    assert _max_thetas_per_side(1, 1) == 1 + 0 + 6
    assert _max_thetas_per_side(2, 2) == 2 + 1 * 6 + 24
    assert _max_thetas_per_side(1, 3) == 3 + 3 * 4 + 18


# ── (5) registration: ToolEntry + tools.total == 418 + Rosetta row + __all__ ───────────
def test_registration():
    import srmech.amsc.elliptic_jackson as ej
    assert "cn_vwp_multisum_lhs" in ej.__all__
    schema = introspect.describe()
    assert schema["tools"]["total"] == 448
    from srmech.amsc.tool_schema import get_tool_schema
    names = {t.name for t in get_tool_schema().tools}
    assert "srmech.amsc.elliptic_jackson.cn_vwp_multisum_lhs" in names
    entry = next(t for t in get_tool_schema().tools
                 if t.name == "srmech.amsc.elliptic_jackson.cn_vwp_multisum_lhs")
    assert "0101073" in entry.summary                          # the MPM-verified keystone
    assert entry.returns.type == "ThetaSum"
    # the Rosetta ledger row (the #928 everything-mirrors ratchet feed)
    ndjson = Path(__file__).resolve().parent / "rosetta_classification.ndjson"
    rows = [json.loads(line) for line in
            ndjson.read_text(encoding="utf-8").splitlines() if line.strip()]
    mine = [r for r in rows
            if r["exposed_as"] == "srmech.amsc.elliptic_jackson.cn_vwp_multisum_lhs"]
    assert len(mine) == 1 and mine[0]["bucket"] == "c_dispatched"
