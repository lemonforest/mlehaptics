"""rc360 (`#T1032` + `#T1024`) — the four exact ops, and their differentials.

WHAT LANDED
===========
* ``cascade.associator(x, y, z, table=None)`` — the associativity defect.
* ``cascade.random_anticommutative_table(dim, key, *, keep_xor_lane=True)`` —
  the SECOND mandatory negative control (rc352's ``algebra_table(gammas=)``
  was the first, the split half).
* ``modular_linalg.gf_solve(A, b, p)`` / ``gf_nullspace(A, p)`` — the two reads
  the GF(p) RREF was always for.

WHY EACH CHECK BELOW IS A DIFFERENTIAL AND NOT A TAUTOLOGY
==========================================================
A test that recomputes the subject with the subject proves nothing. Each block
here reaches the same number by a genuinely different route:

* the associativity census is compared against the numbers the SHIPPED PROSE
  already publishes, PARSED out of ``carrier_schema`` rather than re-typed — so
  the op and the five pin sites cannot drift apart in either direction;
* the two associator routes are a recursive doubling (``cd_mult``) against a
  triple loop over a materialised tensor (``table_product``);
* ``gf_solve`` is checked against EXHAUSTIVE ENUMERATION over ``2**unknowns``
  GF(2) vectors — not an elimination at all;
* ``gf_nullspace`` is checked against ``QMat.nullspace``, the exact-ℚ kernel,
  reduced mod p — a different field and a different implementation.

THE CONTROL MUST BREAK SOMETHING
================================
A negative control that satisfies every law the subject satisfies is not a
control. FLEXIBILITY is the law that separates them: every Cayley–Dickson
algebra is flexible, and so is every γ-twist, while the random cocycle is not.
``test_control_breaks_flexibility`` is therefore the load-bearing test in this
file — if the generator ever stops breaking it, the generator is wrong.

⚠️ STATE THE MATRIX ENCODING — AND IT IS NOT A GAUGE. rc359 adjudicated this
already (``cascade/cd_register.py`` "There is no gauge freedom here to fix"):
``t(e₀) = 0`` is a THEOREM of the cocycle system, not a convention imposed on it,
because ``e₀·e₀ = +e₀`` makes the ``(0,0)`` row literally that equation. What the
two rank tables differ by is a matrix ENCODING — keeping column ``t(e₀)`` against
eliminating the variable and dropping it, which removes that redundant row too
and so shifts BOTH ranks down by exactly one. Same system, same conclusion,
different matrix. ``nullity(A) = log2(dim)`` is the encoding-invariant number.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from srmech.amsc.cascade import (algebra_table, associator, cd_basis,
                                 cd_basis_product, cd_mult, inertia_signature,
                                 left_mult_kernel, random_anticommutative_table,
                                 table_product)
from srmech.amsc.format import sha256_bytes
from srmech.amsc.modular_linalg import gf_nullspace, gf_rref, gf_solve
from srmech.amsc.qmat import QMat

_SRMECH = Path(__file__).resolve().parents[1] / "srmech"


# ══════════════════════════════════════════════════════════════════════
# associator — the associativity defect
# ══════════════════════════════════════════════════════════════════════

def _published_census():
    """The per-rung sign-cocycle census PARSED out of the shipped prose.

    The five pin sites (``carrier_schema`` / ``introspect`` / the
    ``CD_TURN_MAX_DIM`` note / the rc343 ceiling test / the C header) all carry
    the same table. Parsing ONE of them rather than re-typing the numbers here
    is what makes this a drift gate: a change to either side fails.
    """
    text = (_SRMECH / "amsc/carrier_schema.py").read_text(encoding="utf-8")
    rows = re.findall(r"^\s*(\d+) \|.*?\|\s*(\d+)/(\d+)\s+\d+%\s*$",
                      text, re.MULTILINE)
    census = {int(d): (int(n), int(t)) for d, n, t in rows}
    assert len(census) == 5, (
        f"expected the 5-row dim 2/4/8/16/32 census in carrier_schema.py; "
        f"parsed {census}")
    return census


def test_associator_reproduces_the_published_census():
    """The census the tree pins at five sites IS count(associator == 0) over
    the ordered basis triples — MEASURED, not asserted twice.

    dim 32 is published but not re-measured here: 32768 triples × two exact-ℚ
    products is minutes, not seconds. It is checked for SHAPE only (the row is
    present and internally consistent), and the four measured rungs are what
    pin the op.
    """
    published = _published_census()
    for dim in (2, 4, 8, 16):
        basis = [cd_basis(dim, i) for i in range(dim)]
        n = sum(1 for i in range(dim) for j in range(dim) for k in range(dim)
                if all(v == 0 for v in associator(basis[i], basis[j], basis[k])))
        assert (n, dim ** 3) == published[dim], (
            f"dim {dim}: associator counts {n}/{dim ** 3} associating triples "
            f"but the shipped prose publishes {published[dim]}. One of the two "
            f"is wrong — do NOT edit whichever is easier to reach.")
    assert published[32] == (16808, 32768)


def test_associator_ladder_route_equals_table_route():
    """``table=None`` (a recursive doubling through ``cd_mult``) and ``table=``
    (a triple loop over a materialised tensor through ``table_product``) are
    different code, so agreeing on all 512 dim-8 triples is a differential."""
    tbl = algebra_table(8)
    basis = [cd_basis(8, i) for i in range(8)]
    for i in range(8):
        for j in range(8):
            for k in range(8):
                assert (associator(basis[i], basis[j], basis[k])
                        == associator(basis[i], basis[j], basis[k], table=tbl))


def test_associator_is_the_hand_rolled_difference():
    """It equals the expression every measurement used to write inline — which
    is the whole reason it ships as an op."""
    for dim in (4, 8):
        for i in range(dim):
            for j in range(dim):
                x, y, z = cd_basis(dim, i), cd_basis(dim, j), cd_basis(dim, (i + j) % dim)
                left = cd_mult(cd_mult(x, y), z)
                right = cd_mult(x, cd_mult(y, z))
                assert (associator(x, y, z)
                        == tuple(a - b for a, b in zip(left, right)))


def test_associator_reaches_a_second_algebra_through_table():
    """A split γ-twist is a DIFFERENT algebra, and the defect sees it."""
    split = algebra_table(8, [1, -1, -1])
    basis = [cd_basis(8, i) for i in range(8)]
    differ = sum(1 for i in range(8) for j in range(8) for k in range(8)
                 if associator(basis[i], basis[j], basis[k])
                 != associator(basis[i], basis[j], basis[k], table=split))
    assert differ == 96, (
        f"the split-𝕆 twist should disagree with 𝕆 on 96 of the 512 defects; "
        f"got {differ}")


def test_associator_rejects_mismatched_operands():
    with pytest.raises(ValueError, match="share dimension"):
        associator([1, 0], [1, 0, 0, 0], [1, 0])
    with pytest.raises(ValueError, match="power-of-two"):
        associator([1, 0, 0], [1, 0, 0], [1, 0, 0])
    with pytest.raises(ValueError, match="the table is dim"):
        associator([1, 0], [1, 0], [1, 0], table=algebra_table(4))


# ══════════════════════════════════════════════════════════════════════
# random_anticommutative_table — the negative control
# ══════════════════════════════════════════════════════════════════════

_KEYS = ("negative-control-A", "negative-control-B", "k3")


def test_control_is_reproducible_from_its_key_alone():
    """A KEY, not a seed. The point of hashing rather than seeding an MT19937
    is that the table is re-derivable in EVERY implementation (ADR-0009: the
    capability is the invariant, the projections co-equal), so the first thing
    to pin is that the key alone determines the table."""
    for keep in (True, False):
        a = random_anticommutative_table(8, "negative-control-A", keep_xor_lane=keep)
        assert a == random_anticommutative_table(8, "negative-control-A",
                                                 keep_xor_lane=keep)
        assert a == random_anticommutative_table(8, b"negative-control-A",
                                                 keep_xor_lane=keep)
        assert a != random_anticommutative_table(8, "negative-control-B",
                                                 keep_xor_lane=keep)
    assert (random_anticommutative_table(8, "k3", keep_xor_lane=True)
            != random_anticommutative_table(8, "k3", keep_xor_lane=False))


def test_control_signs_are_domain_separated_across_dims():
    """The bare key is never hashed alone: the material carries the op name, a
    format version, the dim and the lane mode, so one key cannot collide across
    ops or dims. The observable consequence is that the dim-16 table does not
    contain the dim-8 one as a corner."""
    small = random_anticommutative_table(8, "k3")
    big = random_anticommutative_table(16, "k3")
    assert any(big[i][j][i ^ j] != small[i][j][i ^ j]
               for i in range(1, 8) for j in range(1, 8) if i != j)


@pytest.mark.parametrize("dim", (4, 8, 16))
def test_control_is_exhaustively_anticommutative_and_unital(dim: int):
    """EXHAUSTIVE at dim 4 / 8 / 16.

    Anticommutativity is asserted on distinct IMAGINARY pairs, and ``e₀`` is
    checked separately as the two-sided unit. Those are not two weakenings of
    one law — a unital algebra CANNOT anticommute against its unit
    (``e₀·e_j = e_j = e_j·e₀``), and keeping the unit is what makes this a
    control for a unital algebra rather than a different kind of object.
    """
    for keep in (True, False):
        t = random_anticommutative_table(dim, "negative-control-A",
                                         keep_xor_lane=keep)
        assert len(t) == dim and all(len(r) == dim for r in t)
        for i in range(dim):
            assert t[0][i][i] == 1 and t[i][0][i] == 1
            assert sum(1 for k in range(dim) if t[0][i][k]) == 1
        for i in range(1, dim):
            assert t[i][i][0] == -1
            assert sum(1 for k in range(dim) if t[i][i][k]) == 1
        for i in range(1, dim):
            for j in range(1, dim):
                if i == j:
                    continue
                assert all(t[i][j][k] == -t[j][i][k] for k in range(dim))
                nz = [k for k in range(dim) if t[i][j][k]]
                assert len(nz) == 1 and t[i][j][nz[0]] in (1, -1)
                if keep:
                    assert nz[0] == i ^ j
                else:
                    assert 1 <= nz[0] < dim


def test_keep_xor_lane_false_actually_leaves_the_xor_lane():
    """``keep_xor_lane`` is load-bearing, not a convenience — so prove the two
    modes are genuinely different objects and not a renamed flag."""
    for dim in (8, 16):
        t = random_anticommutative_table(dim, "negative-control-A",
                                         keep_xor_lane=False)
        off = sum(1 for i in range(1, dim) for j in range(1, dim)
                  if i != j and t[i][j][i ^ j] == 0)
        assert off > 0, f"dim {dim}: every pair still sits on the XOR lane"


def _flex_violations(dim: int, table) -> int:
    """Violations of the LINEARISED flexible law ``(x,y,z) + (z,y,x) = 0`` over
    the ``dim**3`` ordered basis triples, counted THROUGH the shipped
    :func:`associator`. At ``i == k`` it degenerates to plain flexibility
    ``(x·y)·x == x·(y·x)``, so the trilinear form is the strictly stronger
    reading and it is the one measured."""
    basis = [cd_basis(dim, i) for i in range(dim)]
    return sum(1 for i in range(dim) for j in range(dim) for k in range(dim)
               if any((u + v) != 0 for u, v in
                      zip(associator(basis[i], basis[j], basis[k], table=table),
                          associator(basis[k], basis[j], basis[i], table=table))))


def test_control_breaks_flexibility():
    """⚠️ THE LOAD-BEARING TEST. A control that satisfies everything the subject
    satisfies is not a control.

    Every Cayley–Dickson algebra is flexible, and MEASURED here so is every
    γ-twist — 0/512 for the ladder and 0/512 for the split-𝕆 twist. The random
    cocycle is not. The exact per-key counts are pinned because the table is a
    deterministic function of its key: these are reproducible numbers, not a
    sampled range.
    """
    assert _flex_violations(8, algebra_table(8)) == 0
    assert _flex_violations(8, algebra_table(8, [1, -1, -1])) == 0

    pinned_xor = {"negative-control-A": 24, "negative-control-B": 16, "k3": 20}
    pinned_free = {"negative-control-A": 70, "negative-control-B": 70, "k3": 67}
    for key in _KEYS:
        xor = _flex_violations(8, random_anticommutative_table(
            8, key, keep_xor_lane=True))
        free = _flex_violations(8, random_anticommutative_table(
            8, key, keep_xor_lane=False))
        assert xor > 0 and free > 0, (
            f"key {key!r} produced a FLEXIBLE control at dim 8 — the generator "
            f"is wrong, not the assertion. A control that breaks no law the "
            f"ladder keeps cannot separate a claim from an artifact.")
        assert (xor, free) == (pinned_xor[key], pinned_free[key])


#: The NAMED twelve-key set every published range in this op's prose is
#: measured over. A range quoted over an unnamed key set is not reproducible,
#: which is why the set is spelled out here and in the docstrings.
_KEYS12 = tuple("control-%02d" % n for n in range(1, 13))


def test_control_at_dim_4_needs_the_free_lane():
    """The honest limit of the XOR-lane control, MEASURED rather than assumed.

    At dim 4 there are only three imaginary pairs, so ``keep_xor_lane=True``
    has few sign patterns to draw from and some of them ARE ℍ up to
    relabelling. The free lane breaks flexibility at every key. This is why the
    docstring says to control at dim ≥ 8, or with ``keep_xor_lane=False``.
    """
    keys = ("negative-control-A", "negative-control-B", "k3", "control-01")
    xor = [_flex_violations(4, random_anticommutative_table(
        4, k, keep_xor_lane=True)) for k in keys]
    free = [_flex_violations(4, random_anticommutative_table(
        4, k, keep_xor_lane=False)) for k in keys]
    assert xor == [0, 4, 4, 4]
    assert all(v > 0 for v in free), free


def test_published_twelve_key_ranges_are_what_the_prose_says():
    """⚠️ THE DRIFT GATE FOR THE PUBLISHED RANGES.

    The docstring and the ``ToolEntry`` summary both quote flexibility-violation
    RANGES over a twelve-key set. An unnamed set makes a range unfalsifiable, so
    the set is named (``control-01`` … ``control-12``) and its measured extremes
    are pinned here. If the generator changes, this fails and the prose gets
    corrected with it — which is the failure mode rc360 shipped with once
    already: the ranges first written down (16–28 / 58–80... and "4 of 12" at
    dim 4) did not match ANY reproducible key set.
    """
    x8 = {k: _flex_violations(8, random_anticommutative_table(
        8, k, keep_xor_lane=True)) for k in _KEYS12}
    f8 = {k: _flex_violations(8, random_anticommutative_table(
        8, k, keep_xor_lane=False)) for k in _KEYS12}
    assert (min(x8.values()), max(x8.values())) == (12, 28), x8
    assert (min(f8.values()), max(f8.values())) == (58, 80), f8
    # At dim 8 the control is ALWAYS a control, in both lane modes.
    assert all(v > 0 for v in x8.values()) and all(v > 0 for v in f8.values())

    x4 = {k: _flex_violations(4, random_anticommutative_table(
        4, k, keep_xor_lane=True)) for k in _KEYS12}
    f4 = {k: _flex_violations(4, random_anticommutative_table(
        4, k, keep_xor_lane=False)) for k in _KEYS12}
    assert sorted(k for k, v in x4.items() if v == 0) == [
        "control-03", "control-05", "control-09"], x4
    assert (min(f4.values()), max(f4.values())) == (7, 10), f4
    assert all(v > 0 for v in f4.values())


def test_control_drops_into_the_table_consumers_unchanged():
    """Same shape ``algebra_table`` returns, so every existing table-taking op
    accepts it with no adapter — that is what makes it usable as a control at
    all, rather than a second object needing its own plumbing."""
    t = random_anticommutative_table(8, "negative-control-A")
    e0, x, y = cd_basis(8, 0), cd_basis(8, 1), cd_basis(8, 2)

    # table_product: e0 really is the two-sided unit on this table.
    assert table_product(t, e0, x) == x and table_product(t, x, e0) == x
    # associator: any triple containing the unit associates.
    assert all(v == 0 for v in associator(x, y, e0, table=t))
    assert all(v == 0 for v in associator(e0, x, y, table=t))
    # inertia_signature + left_mult_kernel read it without complaint — and the
    # SIGNATURE IS 𝕆's, exactly. That is not a null result: the trace/norm Gram
    # is built from the DIAGONAL (e_i² = −e₀), which the control keeps
    # unchanged, so it is positive evidence that the one thing the control
    # perturbs is the off-diagonal cocycle — the difference is where it was
    # designed to be, and nowhere else. Flexibility, not inertia, is therefore
    # the law that separates them (test_control_breaks_flexibility).
    sig, ref = inertia_signature(t), inertia_signature(algebra_table(8))
    assert sig["signature"] == ref["signature"] == (1, 7, 0)
    assert sig["norm_signature"] == ref["norm_signature"] == (8, 0, 0)
    assert sig["n_plus"] == 1 and sig["n_minus"] == 7 and sig["n_zero"] == 0
    assert left_mult_kernel(x, table=t) == []      # x is not a zero divisor here


def test_control_rejects_a_bad_key_or_dim():
    with pytest.raises(ValueError, match="power of two"):
        random_anticommutative_table(6, "k")
    with pytest.raises(ValueError, match="power of two"):
        random_anticommutative_table(128, "k")
    with pytest.raises(ValueError, match="non-empty"):
        random_anticommutative_table(8, "")
    with pytest.raises(TypeError, match="str or bytes"):
        random_anticommutative_table(8, 12345)


# ══════════════════════════════════════════════════════════════════════
# gf_solve / gf_nullspace
# ══════════════════════════════════════════════════════════════════════

def _bits(tag: bytes, n: int):
    """A deterministic bit stream from the Class-A content-address — so the
    fixtures below are reproducible in every implementation, with no MT19937
    to agree about (the same reason the control takes a key)."""
    out, ctr = [], 0
    while len(out) < n:
        h = sha256_bytes(tag + b"#" + str(ctr).encode("ascii"))
        out.extend(int(c, 16) & 1 for c in h)
        ctr += 1
    return out[:n]


def _brute_force_gf2(A, b):
    """EXHAUSTIVE enumeration of the GF(2) solution set — a wholly different
    algorithm from elimination, which is what makes it an oracle."""
    n = len(A[0]) if A else 0
    sols = []
    for mask in range(1 << n):
        x = [(mask >> i) & 1 for i in range(n)]
        if all(sum(A[r][i] * x[i] for i in range(n)) % 2 == b[r]
               for r in range(len(A))):
            sols.append(tuple(x))
    return set(sols)


def _span_gf2(particular, basis):
    out = set()
    n = len(particular)
    for mask in range(1 << len(basis)):
        v = list(particular)
        for i, k in enumerate(basis):
            if (mask >> i) & 1:
                v = [(v[c] + k[c]) % 2 for c in range(n)]
        out.add(tuple(v))
    return out


def test_gf_solve_against_exhaustive_gf2_enumeration():
    """The full solution set ``particular + span(nullspace)`` equals the
    brute-forced set, on 60 systems up to 10 unknowns (1024 candidates each).

    Both halves matter: when the brute force finds nothing, ``consistent`` must
    be False; when it finds something, the two SETS must be equal — not merely
    the same size, and not merely 'the particular solution checks out'.
    """
    checked = consistent = inconsistent = 0
    for case in range(60):
        n_cols = 2 + case % 9
        n_rows = 2 + (case // 3) % 8
        flat = _bits(b"rc360/gf2/A/%d" % case, n_rows * n_cols)
        A = [flat[r * n_cols:(r + 1) * n_cols] for r in range(n_rows)]
        b = _bits(b"rc360/gf2/b/%d" % case, n_rows)
        truth = _brute_force_gf2(A, b)
        got = gf_solve(A, b, 2)
        assert got["rank"] == gf_rref(A, 2)["rank"]
        assert len(got["nullspace"]) == n_cols - got["rank"]
        if not truth:
            assert got["consistent"] is False and got["particular"] is None
            inconsistent += 1
        else:
            assert got["consistent"] is True
            assert _span_gf2(got["particular"], got["nullspace"]) == truth
            consistent += 1
        checked += 1
    assert checked == 60
    assert consistent and inconsistent, (
        f"the fixture must exercise BOTH branches; got {consistent} consistent "
        f"and {inconsistent} inconsistent")


@pytest.mark.parametrize("p", (2, 3, 7, 101, 2147483629))
def test_gf_nullspace_against_the_exact_rational_kernel(p: int):
    """``QMat.nullspace`` builds the SAME classical free-variable basis over
    exact ℚ. Reduced mod p it must be the GF(p) kernel — a different field and
    a different implementation reaching the same vectors.

    The check is that each exact-ℚ kernel vector, cleared of denominators and
    reduced, lies in the GF(p) kernel; the reverse inclusion is the rank
    identity ``nullity = n_cols − rank``, asserted alongside.
    """
    mats = ([[1, 2, 3], [2, 4, 6], [1, 1, 1]],
            [[2, -1, 0], [-1, 2, -1], [0, -1, 2]],
            [[1, 0, 1, 0], [0, 1, 0, 1], [1, 1, 1, 1]])
    for M in mats:
        n_cols = len(M[0])
        basis = gf_nullspace(M, p)
        assert len(basis) == n_cols - gf_rref(M, p)["rank"]
        for vec in basis:
            for row in M:
                assert sum(row[i] * vec[i] for i in range(n_cols)) % p == 0
            assert all(0 <= v < p for v in vec)
        for col in QMat.from_rows(M).nullspace():
            qs = [q for row in col.to_lists() for q in row]
            den = 1
            for q in qs:
                den = den * q.denominator // _gcd_int(den, q.denominator)
            if den % p == 0:
                continue          # the denominator-clearing factor dies mod p
            cleared = [(q.numerator * (den // q.denominator)) % p for q in qs]
            assert any(v for v in cleared), (
                "the cleared exact-ℚ kernel vector vanished mod p — the "
                "differential would be vacuous")
            for row in M:
                assert sum(row[i] * cleared[i] for i in range(n_cols)) % p == 0


def _gcd_int(a: int, b: int) -> int:
    while b:
        a, b = b, a % b
    return a


def _cocycle_system(dim: int, drop_e0_column: bool = True):
    """``δt = ε`` over GF(2): is the Cayley–Dickson sign cocycle a coboundary?

    ``(δt)(i, j) = t(i) + t(j) + t(i⊕j)`` must equal ``ε(i, j)``, where
    ``e_i·e_j = (−1)**ε(i,j) e_{i⊕j}``.

    ⚠️ THE MATRIX ENCODING — NOT A GAUGE. ``drop_e0_column`` substitutes
    ``t(e₀) = 0`` and drops column 0. That is legitimate because ``t(e₀) = 0``
    is a THEOREM of this system, not a convention: ``e₀·e₀ = +e₀``, so the
    ``(i, j) = (0, 0)`` row IS literally ``t(e₀) = 0``. Eliminating the variable
    removes that redundant row along with the column, which is why BOTH ranks
    sit one below the keep-the-column encoding. Quoting a rank without saying
    which encoding produced it is not reproducible; the CONCLUSION and the
    nullity are invariant under both.
    """
    off = 1 if drop_e0_column else 0
    A, b = [], []
    for i in range(dim):
        for j in range(dim):
            idx, sign = cd_basis_product(dim, i, j)
            row = [0] * (dim - off)
            for u in (i, j, idx):
                if u >= off:
                    row[u - off] ^= 1
            A.append(row)
            b.append(0 if sign == 1 else 1)
    return A, b


def test_cd_sign_cocycle_is_not_a_coboundary_at_any_rung():
    """The regression fixture, WITH ITS MATRIX ENCODING STATED.

    ``rank([A|b]) == rank(A) + 1`` at every rung is the whole content: the CD
    sign is COHOMOLOGICAL, not a relabelling — no choice of ``t`` turns the
    signs into a coboundary. The nullity is ``log2(dim)``, the GF(2)-linear
    functionals, and it is ENCODING-invariant while the ranks are not.

    Also pinned in closed form: ``rank(A) == dim - log2(dim)`` in the
    keep-the-column encoding, which is the identity rc359 published and the
    reason the rank pair is only a frame-relative shadow of the nullity.
    """
    dropped = {2: 0, 4: 1, 8: 4, 16: 11, 32: 26, 64: 57}
    for dim, rank_a in dropped.items():
        lg = dim.bit_length() - 1
        A, b = _cocycle_system(dim, drop_e0_column=True)
        got = gf_solve(A, b, 2)
        assert got["consistent"] is False, f"dim {dim} became consistent"
        assert got["particular"] is None
        assert got["rank"] == rank_a, f"dim {dim} drop-column rank"
        assert len(got["nullspace"]) == lg

        kept_A, kept_b = _cocycle_system(dim, drop_e0_column=False)
        kept = gf_solve(kept_A, kept_b, 2)
        assert kept["consistent"] is False
        assert kept["rank"] == rank_a + 1, (
            f"dim {dim}: keeping the t(e0) column must raise the rank by "
            f"exactly one — that shift is why the ENCODING has to be stated, "
            f"and it is not a gauge choice (t(e0) = 0 is a theorem here)")
        # The closed form rc359 published, in the encoding it was quoted for.
        assert kept["rank"] == dim - lg
        # The nullity is the encoding-INVARIANT number.
        assert len(kept["nullspace"]) == len(got["nullspace"]) == lg


def test_gf_solve_edge_shapes():
    """Zero rows, zero columns, and the inconsistent 0 = 1 they can carry."""
    assert gf_solve([], [], 5) == {"consistent": True, "particular": [],
                                   "nullspace": [], "rank": 0}
    assert gf_solve([[], []], [0, 0], 5)["consistent"] is True
    bad = gf_solve([[], []], [0, 1], 5)
    assert bad["consistent"] is False and bad["particular"] is None
    assert gf_nullspace([], 5) == [] and gf_nullspace([[], []], 5) == []
    full = gf_solve([[1, 0], [0, 1]], [3, 4], 7)
    assert full == {"consistent": True, "particular": [3, 4],
                    "nullspace": [], "rank": 2}


def test_gf_solve_and_nullspace_reject_bad_input():
    with pytest.raises(ValueError, match="gf_solve: p must be a prime"):
        gf_solve([[1]], [1], 1)
    with pytest.raises(ValueError, match="gf_nullspace: p must be a prime"):
        gf_nullspace([[1]], 0)
    with pytest.raises(TypeError, match="gf_solve: p must be int"):
        gf_solve([[1]], [1], 2.0)
    with pytest.raises(ValueError, match="one entry per row"):
        gf_solve([[1, 1], [0, 1]], [1], 2)
    with pytest.raises(ValueError, match="equal length"):
        gf_solve([[1, 1], [0]], [1, 0], 2)
    with pytest.raises(TypeError, match="entry of b must be int"):
        gf_solve([[1]], [1.0], 2)


def test_gf_solve_is_exported_and_classified():
    """A new public name in a module WITH ``__all__`` is invisible to the
    ledger walk unless it is listed — the trap this module's ``__all__`` sets.
    """
    import srmech.amsc.modular_linalg as ml
    assert "gf_solve" in ml.__all__ and "gf_nullspace" in ml.__all__
    ledger = (Path(__file__).resolve().parent
              / "rosetta_classification.ndjson").read_text(encoding="utf-8")
    for name in ("srmech.amsc.modular_linalg.gf_solve",
                 "srmech.amsc.modular_linalg.gf_nullspace",
                 "srmech.amsc.cascade.cayley_dickson.associator",
                 "srmech.amsc.cascade.cayley_dickson.random_anticommutative_table"):
        assert f'"{name}"' in ledger, f"{name} has no Rosetta bucket"
