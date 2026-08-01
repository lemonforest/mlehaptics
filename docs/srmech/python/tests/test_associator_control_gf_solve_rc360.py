"""rc360 (`#T1032` + `#T1024`) — the three exact ops, and their differentials.

WHAT LANDED
===========
* ``cascade.associator(x, y, z, table=None)`` — the associativity defect.
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

THE CONTROL MUST BREAK SOMETHING — AND IT MUST BE STRUCTURED
============================================================
A negative control that satisfies every law the subject satisfies is not a
control. FLEXIBILITY is the law that separates: every Cayley–Dickson algebra is
flexible, and MEASURED here so is every γ-twist AND every group ring — so
neither of those controls a flexibility claim at all. ONE NAMED SIGN FLIP does,
at 4 violations per rung, with no random draw anywhere. The control-section
comment below records why the DRAWN control this file first shipped was the
wrong shape, and what replaced it.

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
                                 left_mult_kernel, table_product)
from srmech.amsc.format import sha256_bytes
from srmech.math.modular_linalg import gf_nullspace, gf_rref, gf_solve
from srmech.math.qmat import QMat

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
    text = (_SRMECH / "introspect/carrier_schema.py").read_text(encoding="utf-8")
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
# The STRUCTURED negative controls
#
# rc360 first shipped a `random_anticommutative_table(dim, key)` op that drew
# its sign cocycle from SHA-256. IT WAS DROPPED BEFORE RELEASE, and the reason
# is worth keeping next to the tests that replaced it: a control drawn from a
# structureless hash tests GENERICITY, not structure — it answers "is the
# ladder unlike a random algebra", which nothing needed asking. It was also
# spelled in the wrong alphabet. srmech's resonant alphabet is TERNARY
# {−1, 0, +1} (`hdc.polar_random` draws `_randbelow(3)`, not `_randbelow(2)`)
# because the 0 is the rest / non-ringing value; an earlier ±1-only design that
# encoded "only what changes" was superseded once the 0 was recognised as
# necessary. A uniform ±1 sign draw is that abandoned alphabet, and the absent
# ±1 C stream was never a gap to fill.
#
# So every control below is STRUCTURED: a single named perturbation of the
# ladder, reproducible from its own description, with no stream to agree about
# across implementations. MEASURED at dim 4 / 8 / 16 — and the three are
# COMPLEMENTARY, each biting exactly one axis, which is what lets a measured
# difference be attributed to something:
#
#   control                       flexibility bite    inertia bite
#   ---------------------------   -----------------   ----------------------
#   algebra_table(gammas=)        0  (all 8 flex)     YES (5,3,0) vs (1,7,0)
#   ONE named sign flip           4  at EVERY rung    none (signature intact)
#   R[Z/dim] wrong quotient       0  (associative)    YES (5,3,0) vs (1,7,0)
#
# ⚠️ THE NAMED FLIP IS THE ONLY ONE OF THE THREE THAT BREAKS FLEXIBILITY, and
# it beats the dropped random op on every axis: no draw at all, a CONSTANT 4
# per rung rather than a key-dependent 12–28 range, and it works at dim 4 —
# where the drawn control silently failed (key `control-01` was flexible there,
# which is to say it was not a control). Promoting it to a named op is filed:
# hand-rolling a control beside a test is the exact defect `#T1032` was opened
# for, and this file is currently committing it on purpose, in the open.
# ══════════════════════════════════════════════════════════════════════

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


def _nonassoc(dim: int, table) -> int:
    """Ordered basis triples with a NONZERO associator — the complement of the
    census :func:`test_associator_reproduces_the_published_census` pins."""
    basis = [cd_basis(dim, i) for i in range(dim)]
    return sum(1 for i in range(dim) for j in range(dim) for k in range(dim)
               if any(v != 0 for v in associator(basis[i], basis[j], basis[k],
                                                 table=table)))


def _flip_pair(dim: int, i: int, j: int):
    """The FLIP CONTROL — negate ``e_i·e_j`` and ``e_j·e_i`` on the ladder,
    keeping anticommutativity. ONE named bit away from the definite table.

    No key, no hash, no RNG: the control is named by the pair ``(i, j)`` and any
    implementation with :func:`algebra_table` rebuilds it identically. The
    diagonal (``e_i² = −e₀``) is untouched, so the trace form — and therefore
    the inertia signature — is unchanged BY CONSTRUCTION; whatever it perturbs,
    it perturbs in the off-diagonal cocycle and nowhere else.
    """
    table = [[list(row) for row in plane] for plane in algebra_table(dim)]
    lane = i ^ j
    table[i][j][lane] = -table[i][j][lane]
    table[j][i][lane] = -table[j][i][lane]
    return table


def _group_ring(dim: int):
    """The WRONG-QUOTIENT control — ``ℝ[ℤ/dim]``, the cyclic group ring, whose
    lane is ``(i + j) mod dim`` instead of the CD ``i ⊕ j`` and whose signs are
    all ``+1``. Structured, and wrong in a NAMED way: it replaces the sign
    cocycle with the trivial one over a different group."""
    table = [[[0] * dim for _ in range(dim)] for _ in range(dim)]
    for i in range(dim):
        for j in range(dim):
            table[i][j][(i + j) % dim] = 1
    return table


def test_gamma_family_controls_the_metric_not_the_laws():
    """⚠️ THE γ-FAMILY HAS ZERO BITE ON THE ASSOCIATIVITY LAWS — measured, and
    it is the reason a second control is needed at all.

    All eight dim-8 γ-twists are flexible (0/512) AND carry the identical
    non-associating count (168/512). What the γ parameter moves is the METRIC:
    seven twists sit at signature (5,3,0) and only γ = (−1,−1,−1) — which IS
    ``algebra_table(8)``'s default, the definite ladder — sits at (1,7,0).

    So a claim resting on flexibility or on the associativity census cannot be
    controlled with a γ-twist. Quoting one as "the negative control" for such a
    claim would be an instrument that could not have returned otherwise.
    """
    import itertools
    rows = {}
    for gammas in itertools.product((1, -1), repeat=3):
        table = algebra_table(8, list(gammas))
        rows[gammas] = (_flex_violations(8, table), _nonassoc(8, table),
                        inertia_signature(table)["signature"])

    assert all(flex == 0 for flex, _, _ in rows.values()), rows
    assert {na for _, na, _ in rows.values()} == {168}, rows

    definite = [g for g, (_, _, sig) in rows.items() if sig == (1, 7, 0)]
    split = [g for g, (_, _, sig) in rows.items() if sig == (5, 3, 0)]
    assert definite == [(-1, -1, -1)], definite
    assert len(split) == 7, split
    assert (inertia_signature(algebra_table(8))["signature"]
            == inertia_signature(algebra_table(8, [-1, -1, -1]))["signature"]
            == (1, 7, 0))


def test_one_named_sign_flip_is_the_flexibility_control():
    """⚠️ THE LOAD-BEARING CONTROL. A single named bit breaks flexibility at
    every rung, and the count is a CONSTANT 4 — not a range.

    Every Cayley–Dickson algebra is flexible, so any nonzero count is decisive.
    Flipping one imaginary pair's sign gives exactly 4 violations at dim 4, 8
    and 16 alike, and it does so for EVERY pair — uniformly, with no key to
    choose and no draw to reproduce. The inertia signature is unchanged, which
    is the attribution: the perturbation is in the cocycle and nowhere else.
    """
    # The subject is flexible at every rung — the baseline the control breaks.
    for dim in (4, 8, 16):
        assert _flex_violations(dim, algebra_table(dim)) == 0

    # dim 4: all three imaginary pairs. The DRAWN control failed here.
    d4 = {(i, j): (_flex_violations(4, _flip_pair(4, i, j)),
                   _nonassoc(4, _flip_pair(4, i, j)),
                   inertia_signature(_flip_pair(4, i, j))["signature"])
          for i in range(1, 4) for j in range(i + 1, 4)}
    assert set(d4.values()) == {(4, 12, (1, 3, 0))}, d4

    # dim 8: all twenty-one pairs, and the result is uniform over them.
    d8 = {(i, j): (_flex_violations(8, _flip_pair(8, i, j)),
                   _nonassoc(8, _flip_pair(8, i, j)),
                   inertia_signature(_flip_pair(8, i, j))["signature"])
          for i in range(1, 8) for j in range(i + 1, 8)}
    assert len(d8) == 21
    assert set(d8.values()) == {(4, 148, (1, 7, 0))}, d8

    # dim 16: one representative pair — 4096 triples × two exact-ℚ products is
    # seconds per pair, so the rung is covered without the full 120-pair sweep.
    flip16 = _flip_pair(16, 1, 2)
    assert _flex_violations(16, flip16) == 4
    assert _nonassoc(16, flip16) == 1828
    assert inertia_signature(flip16)["signature"] == (1, 15, 0)
    assert (inertia_signature(algebra_table(16))["signature"] == (1, 15, 0))


def test_wrong_quotient_group_ring_bites_the_metric_and_its_diff_is_a_tautology():
    """The ℝ[ℤ/dim] control, and ⚠️ A NUMBER THAT LOOKS LIKE EVIDENCE AND IS NOT.

    The group ring is ASSOCIATIVE and commutative, so it has 0 non-associating
    triples and 0 flexibility violations at every rung — no bite on either law.
    Its real bite is the metric: the trace form is far more positive than the
    ladder's, separating them at every rung.

    ⚠️ The tempting statistic — "the control's associator differs from the
    ladder's on 168 of 512 triples at dim 8, 1848 of 4096 at dim 16" — is a
    FORCED IDENTITY, not a measurement. The group ring's defect is identically
    zero, so it differs from the ladder EXACTLY where the ladder is nonzero:
    the number is the ladder's own non-associating census wearing a disguise
    (512 − 344 = 168, 4096 − 2248 = 1848). It is asserted here as an identity,
    in the one place it cannot be mistaken for a differential.
    """
    expected_sig = {2: (2, 0, 0), 4: (3, 1, 0), 8: (5, 3, 0), 16: (9, 7, 0)}
    for dim in (2, 4, 8, 16):
        ring = _group_ring(dim)
        assert _nonassoc(dim, ring) == 0, dim
        assert _flex_violations(dim, ring) == 0, dim
        assert inertia_signature(ring)["signature"] == expected_sig[dim], dim
        # ... and it does separate from the ladder on the metric.
        assert (inertia_signature(ring)["signature"]
                != inertia_signature(algebra_table(dim))["signature"]), dim

    # The tautology, stated as one. differs == the ladder's own nonassoc count.
    for dim, published_nonassoc in ((8, 168), (16, 1848)):
        basis = [cd_basis(dim, i) for i in range(dim)]
        ring, ladder = _group_ring(dim), algebra_table(dim)
        differs = sum(
            1 for i in range(dim) for j in range(dim) for k in range(dim)
            if associator(basis[i], basis[j], basis[k], table=ladder)
            != associator(basis[i], basis[j], basis[k], table=ring))
        assert differs == published_nonassoc == _nonassoc(dim, ladder), dim


def test_structured_controls_drop_into_the_table_consumers_unchanged():
    """Both controls are the same rank-3 shape ``algebra_table`` returns, so
    every table-taking op accepts them with no adapter — which is what makes
    them usable as controls rather than second objects needing their own
    plumbing."""
    e0, x, y = cd_basis(8, 0), cd_basis(8, 1), cd_basis(8, 2)
    for label, table in (("flip", _flip_pair(8, 1, 2)),
                         ("group-ring", _group_ring(8))):
        # table_product: e0 is still the two-sided unit on both.
        assert table_product(table, e0, x) == x, label
        assert table_product(table, x, e0) == x, label
        # associator: any triple containing the unit still associates.
        assert all(v == 0 for v in associator(x, y, e0, table=table)), label
        # inertia_signature + left_mult_kernel read them without complaint.
        sig = inertia_signature(table)
        assert sig["n_plus"] + sig["n_minus"] + sig["n_zero"] == 8, label
        assert left_mult_kernel(x, table=table) == [], label


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
    import srmech.math.modular_linalg as ml
    assert "gf_solve" in ml.__all__ and "gf_nullspace" in ml.__all__
    ledger = (Path(__file__).resolve().parent
              / "rosetta_classification.ndjson").read_text(encoding="utf-8")
    for name in ("srmech.math.modular_linalg.gf_solve",
                 "srmech.math.modular_linalg.gf_nullspace",
                 "srmech.amsc.cascade.cayley_dickson.associator"):
        assert f'"{name}"' in ledger, f"{name} has no Rosetta bucket"
