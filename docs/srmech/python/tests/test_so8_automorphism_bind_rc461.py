"""rc461 (`#T1181`) — the AUTOMORPHISM-side triality contract + the frame bind.

WHAT WAS UNBOUND, AND WHAT IT COST
==================================
``triality_automorphism()`` returns the 28×28 ``τ = S_B·S_C`` **in the E_pq
frame**; ``triality_swap()`` returns ``S_B`` in the same frame.
``so8_adjoint_basis()`` orders the SAME 28 so(8) directions differently
(``14 g2 + 7 L + 7 R``). Through rc460 **nothing bound them**, and the gap is
not theoretical. MEASURED, with ``P`` the change of basis between the two:

* ``τ`` read in the adjoint frame fails the bracket test **378 of 378** and
  fixes **0 of the 14** dimensions of ``g2`` — while the mathematics is fine
  and only the frames disagree;
* for a genuine monomial G2 element whose E_pq commutator is EXACTLY ZERO,
  ``[τ, P⁻¹ Ad P]`` carries **176 of 784** nonzero entries.

Well-formed, plausible, wrong; no exception, no warning, no gate. Same class as
rc460 B1 (42 silent wrong answers from an unbound frame), which shipped a
content-address bind as its fix. So does this.

THE NAME IS THE RESULT OF A MEASUREMENT
=======================================
The obvious name for the new predicate — ``is_triality_fixed``, over the two
commutators alone — would be a LIE, and this file executes the counterexample.
``Ad(−I) = I₂₈`` exactly, so ``−I`` commutes with everything; yet ``−I`` fails
octonion multiplicativity on **64 of 64** basis pairs. It is not one
counterexample either: over the monomial ``±G2`` set, EVERY ``−g`` passes both
commutators and fails multiplicativity 64/64. The commutators see
``PSO(8) = SO(8)/{±I}`` and cannot separate ``g`` from ``−g``, so the commutator
verdict ships as ``fixed_mod_center`` and ``in_g2`` is decided by
multiplicativity — which IS the definition of ``Aut(O) = G2``.

⚠️ ``determinant`` does not rescue the commutator reading: ``det(−g) =
(−1)⁸ det(g) = det(g)``, executed ``+1`` for all 32 monomial G2 elements AND
all 32 of their negatives. That is checked below so nobody re-invents it.

EVERY PREDICATE HERE CARRIES A CONTROL THAT COMES BACK NEGATIVE
===============================================================
``[[feedback_an_instrument_that_cannot_return_otherwise_is_not_a_measurement]]``.
The certificate returns 0/378 on both shipped generators AND 168/378 on
``2·S_B``, 161/378 on ``P⁻¹ S_B P``, 214/378 on ``P⁻¹ τ P``. ``g2_membership``
returns ``in_g2`` True on 32 elements and False on 32 negatives plus two RED
controls with distinct nonzero residuals. The dissonance guard is proved firable
by FAULT INJECTION, because a guard never observed to fire is not an instrument.

⚠️ These are HAND-WRITTEN execution gates on purpose.
``tests/test_preserves_taxonomy_rc423.py`` declares eight of ten property kinds
EXECUTABLE and at :371-377 executes NONE of them, so a declared property can be
classified machine-checkable and never run. Nothing here leans on that taxonomy.

NO NUMPY. Exact ``Q`` / ``int`` only; float appears nowhere in a decision path.
"""

from __future__ import annotations

import itertools

import pytest

from srmech.math.q import Q, to_q
from srmech.physics.qm.octonion import octonion_mult_table, octonion_table_attestation
from srmech.physics.qm.so8 import (
    _DIM_SO8,
    _epq_pairs,
    epq_frame_address,
    g2_membership,
    so8_adjoint_basis,
    so8_bracket_certificate,
)
from srmech.physics.qm.triality import (
    triality_automorphism,
    triality_frame_action,
    triality_swap,
)

N = _DIM_SO8
PAIRS = _epq_pairs()
LABELS = ("v", "s", "c")


# ── exact-ℚ helpers (test-local; no numpy, no float) ──────────────────────

def _rows(mat):
    return [[to_q(x) for x in row] for row in mat.tolist()]


def _matmul(a, b):
    n = len(a)
    return [[sum((a[i][k] * b[k][j] for k in range(n)), Q(0))
             for j in range(n)] for i in range(n)]


def _eye(n):
    return [[Q(1) if i == j else Q(0) for j in range(n)] for i in range(n)]


def _inverse(a):
    n = len(a)
    m = [list(a[i]) + [Q(1) if i == j else Q(0) for j in range(n)]
         for i in range(n)]
    for c in range(n):
        piv = next((r for r in range(c, n) if m[r][c] != 0), None)
        assert piv is not None, "singular matrix in test helper"
        m[c], m[piv] = m[piv], m[c]
        inv = Q(1) / m[c][c]
        m[c] = [x * inv for x in m[c]]
        for r in range(n):
            if r != c and m[r][c] != 0:
                f = m[r][c]
                m[r] = [m[r][j] - f * m[c][j] for j in range(2 * n)]
    return [row[n:] for row in m]


def _rank(rows):
    m = [list(r) for r in rows]
    nr, nc = len(m), len(m[0])
    rank = 0
    for c in range(nc):
        piv = next((r for r in range(rank, nr) if m[r][c] != 0), None)
        if piv is None:
            continue
        m[rank], m[piv] = m[piv], m[rank]
        inv = Q(1) / m[rank][c]
        m[rank] = [x * inv for x in m[rank]]
        for r in range(nr):
            if r != rank and m[r][c] != 0:
                f = m[r][c]
                m[r] = [m[r][j] - f * m[rank][j] for j in range(nc)]
        rank += 1
    return rank


@pytest.fixture(scope="module")
def tau():
    return _rows(triality_automorphism())


@pytest.fixture(scope="module")
def swap():
    return _rows(triality_swap())


@pytest.fixture(scope="module")
def change_of_basis():
    """``P`` — the so8_adjoint_basis generators as E_pq columns, and ``P⁻¹``.

    This IS the frame mismatch, written down: column ``c`` of ``P`` is the
    E_pq coordinate vector of ``so8_adjoint_basis()[c]``, so ``P⁻¹ M P``
    re-expresses an E_pq-frame map in the adjoint ordering.
    """
    adj = so8_adjoint_basis()
    p = [[to_q(int(adj[c].tolist()[a][b])) for c in range(N)]
         for (a, b) in PAIRS]
    return p, _inverse(p)


# ── G1 — the shipped generators' exact invariants ─────────────────────────

def test_g1_tau_and_swap_are_exact_half_integer(tau, swap):
    """Entries in ``{0, ±1/2}``, max denominator 2 — the fact that puts the
    whole certificate on the INTEGER ALU."""
    for name, m in (("tau", tau), ("S_B", swap)):
        entries = {x for row in m for x in row}
        assert entries == {Q(-1, 2), Q(0), Q(1, 2)}, (name, sorted(entries))
        assert max(x.denominator for row in m for x in row) == 2, name
        doubled = [[2 * x for x in row] for row in m]
        assert all(x.denominator == 1 for row in doubled for x in row), name


def test_g1_traces_orders_and_fixed_dimensions(tau, swap):
    """Tr(τ) = 7, dim Fix(τ) = 14 = dim g2; Tr(S_B) = 14, dim Fix(S_B) = 21
    = dim so(7). Spin(7): 28 = 21 + 7."""
    assert sum((tau[i][i] for i in range(N)), Q(0)) == 7
    assert sum((swap[i][i] for i in range(N)), Q(0)) == 14

    identity = _eye(N)
    assert _matmul(_matmul(tau, tau), tau) == identity          # τ³ = I
    assert _matmul(tau, tau) != identity                        # τ ≠ order 2
    assert _matmul(swap, swap) == identity                      # S_B² = I

    for name, m, want in (("tau", tau, 14), ("S_B", swap, 21)):
        minus_i = [[m[i][j] - identity[i][j] for j in range(N)]
                   for i in range(N)]
        assert N - _rank(minus_i) == want, name


# ── G2 — the bracket certificate, with controls that come back RED ────────

def test_g2_shipped_generators_are_bracket_automorphisms():
    for mat in (triality_automorphism(), triality_swap()):
        cert = so8_bracket_certificate(mat)
        assert cert["is_bracket_automorphism"] is True
        assert cert["failures"] == 0
        assert cert["pairs_checked"] == 378 == N * (N - 1) // 2
        assert cert["first_failure"] is None
        assert cert["denominator"] == 2
        assert cert["frame_sha256"] == epq_frame_address()


def test_g2_control_scaling_breaks_the_bracket(swap):
    """NEGATIVE CONTROL. ``2·S_B`` is a perfectly good 28×28 integer matrix and
    is NOT a bracket automorphism — the bracket is quadratic in φ on one side
    and linear on the other, so a scale factor cannot survive it."""
    doubled = [[2 * x for x in row] for row in swap]
    cert = so8_bracket_certificate(doubled)
    assert cert["is_bracket_automorphism"] is False
    assert cert["failures"] == 168
    assert cert["first_failure"] == (0, 1)
    assert cert["denominator"] == 1


def test_g2_control_wrong_frame_is_detected(tau, swap, change_of_basis):
    """NEGATIVE CONTROL, and the whole point of the rc: the SAME two maps,
    re-expressed in the so8_adjoint_basis ordering, are refused."""
    p, p_inv = change_of_basis
    assert _rank(p) == N                      # the two orderings really are bases

    swap_adj = _matmul(p_inv, _matmul(swap, p))
    tau_adj = _matmul(p_inv, _matmul(tau, p))
    assert so8_bracket_certificate(swap_adj)["failures"] == 161
    assert so8_bracket_certificate(tau_adj)["failures"] == 214


# ── G3 — BOTH SIDES of the silent wrong answer, pinned ────────────────────

def test_g3_frame_action_answers_the_wrong_frame_map_wrongly(swap,
                                                             change_of_basis):
    """The defect, pinned from both ends so it cannot drift silently.

    ``triality_frame_action`` is CORRECT within its declared scope — it is a
    reader of the induced action on ``h``, and its docstring says in terms
    that a pass is not a certificate of automorphy. What this test pins is
    that the wrong-frame map is INVISIBLE to every invariant that op inspects,
    and that the shipped certificate SEES it. Deliberately NOT fixed by making
    ``triality_frame_action`` raise: that would delete a documented scope
    boundary and its own rank-≤4 witness in ``test_frame_action_rc461.py``.
    """
    p, p_inv = change_of_basis
    swap_adj = _matmul(p_inv, _matmul(swap, p))

    # RIGHT frame, right answer.
    assert triality_frame_action(triality_swap())["frame_action"] == {
        "v": "s", "s": "v", "c": "c"}
    assert triality_frame_action(triality_swap())["order"] == 2

    # WRONG frame, plausible wrong answer, no exception.
    wrong = triality_frame_action(swap_adj)
    assert wrong["frame_action"] == {"v": "v", "s": "s", "c": "c"}
    assert wrong["order"] == 1
    assert wrong["is_identity"] is True

    # WHY it walks through: every invariant the op inspects still checks out.
    assert _matmul(swap_adj, swap_adj) == _eye(N)                # involution
    assert sum((swap_adj[i][i] for i in range(N)), Q(0)) == 14   # same trace

    # And the shipped instrument that SEES it.
    cert = so8_bracket_certificate(swap_adj)
    assert cert["is_bracket_automorphism"] is False
    assert cert["failures"] == 161


def test_g3_frame_action_emits_the_frame_address():
    """The bind: the op that reads the E_pq frame now says which frame it read
    in. A label, not a check — the docstring says so in those words."""
    payload = triality_frame_action(triality_swap())
    assert payload["frame_sha256"] == epq_frame_address()


# ── the monomial G2 locus, built exactly ──────────────────────────────────

@pytest.fixture(scope="module")
def structure_constants():
    """``{(i, j): (k, c)}`` with ``e_i·e_j = c·e_k`` for ``i ≠ j`` in 1..7."""
    table = octonion_mult_table()
    out = {}
    for i in range(1, 8):
        for j in range(1, 8):
            if i == j:
                continue
            v = table[i][j]
            nz = [t for t in range(8) if v[t] != 0]
            assert len(nz) == 1, (i, j, v)
            out[(i, j)] = (nz[0], v[nz[0]])
    return out


@pytest.fixture(scope="module")
def cycling_automorphisms(structure_constants):
    """The 32 monomial octonion automorphisms with index action e₁→e₂→e₃→e₁.

    Built from the Fano/sign conditions directly, so the 32 is DERIVED here
    rather than pinned: an index permutation must preserve the Fano lines, and
    the signs must satisfy ``c·s[k] = s[i]·s[j]·c'``.
    """
    struct = structure_constants
    out = []
    for perm in itertools.permutations(range(1, 8)):
        p = {i + 1: perm[i] for i in range(7)}
        if p[1] != 2 or p[2] != 3 or p[3] != 1:
            continue
        if any(p[k] != struct[(p[i], p[j])][0]
               for (i, j), (k, _c) in struct.items()):
            continue
        for bits in range(128):
            s = {i + 1: (1 if not (bits >> i) & 1 else -1) for i in range(7)}
            if all(c * s[k] == s[i] * s[j] * struct[(p[i], p[j])][1]
                   for (i, j), (k, c) in struct.items()):
                g = [[0] * 8 for _ in range(8)]
                g[0][0] = 1
                for i in range(1, 8):
                    g[p[i]][i] = s[i]
                out.append((tuple(perm), g))
    return out


def test_g4_the_cycling_locus_is_four_index_perms_by_eight_signs(
        cycling_automorphisms):
    """RECONCILIATION (a), EXECUTED. The 32 factor as 4 index permutations ×
    8 sign patterns — a coset of the pointwise line-stabiliser times the
    diagonal sign group — NOT one index permutation with 32 signs.

    ⚠️ This 32 is unrelated to ``triality_frame_action``'s ``32`` weight-table
    entries (8 weights × 4 Cartan coordinates). They share a numeral and no
    structure; neither reconciles the other.
    """
    assert len(cycling_automorphisms) == 32
    by_perm = {}
    for perm, _g in cycling_automorphisms:
        by_perm[perm] = by_perm.get(perm, 0) + 1
    assert len(by_perm) == 4, sorted(by_perm)
    assert set(by_perm.values()) == {8}
    assert sorted(by_perm) == [
        (2, 3, 1, 4, 6, 7, 5), (2, 3, 1, 5, 7, 6, 4),
        (2, 3, 1, 6, 4, 5, 7), (2, 3, 1, 7, 5, 4, 6)]


def test_g4_cycling_elements_are_in_g2_and_inner(cycling_automorphisms):
    """All 32 are genuine automorphisms, centralise BOTH generators, and are
    INNER — the prediction the contract exists to be able to answer."""
    for perm, g in cycling_automorphisms:
        r = g2_membership(g)
        assert r["in_g2"] is True, perm
        assert r["multiplicativity_failures"] == 0, perm
        assert r["centralizes_tau"] is True, perm
        assert r["centralizes_swap"] is True, perm
        assert r["tau_residual"] == 0 and r["swap_residual"] == 0, perm
        assert r["fixed_mod_center"] is True, perm
        assert r["center_coset"] == "G2", perm
        assert r["induced_outer_class"] == "inner", perm
        assert r["determinant"] == 1, perm


def test_g4_control_negatives_pass_the_commutators_and_are_not_in_g2(
        cycling_automorphisms):
    """THE CONTROL THAT MAKES THE NAME NECESSARY. Each ``−g`` passes BOTH
    commutators — ``fixed_mod_center`` is True — and is not an automorphism at
    all. 32 counterexamples to ``is_triality_fixed`` in this fixture alone.

    ``determinant`` cannot separate them either: ``(−1)⁸ = 1``.
    """
    for perm, g in cycling_automorphisms:
        neg = [[-x for x in row] for row in g]
        r = g2_membership(neg)
        assert r["centralizes_tau"] is True, perm
        assert r["centralizes_swap"] is True, perm
        assert r["fixed_mod_center"] is True, perm      # ← "fixed" would lie
        assert r["in_g2"] is False, perm
        assert r["multiplicativity_failures"] == 64, perm
        assert r["center_coset"] == "minus_G2", perm
        assert r["determinant"] == 1, perm              # NOT a discriminator


# ── G5 — the −I name defect, exactly ──────────────────────────────────────

def test_g5_minus_identity_is_the_name_defect():
    """``Ad(−I) = I₂₈`` so both commutators vanish, and ``−I`` fails octonion
    multiplicativity 64/64. A predicate over the commutators ALONE, named
    "fixed", returns True here."""
    minus_i = [[-1 if i == j else 0 for j in range(8)] for i in range(8)]
    r = g2_membership(minus_i)
    assert r["tau_residual"] == 0 and r["swap_residual"] == 0
    assert r["fixed_mod_center"] is True
    assert r["in_g2"] is False
    assert r["multiplicativity_failures"] == r["octonion_pairs"] == 64
    assert r["negated_multiplicativity_failures"] == 0
    assert r["center_coset"] == "minus_G2"
    assert r["determinant"] == 1
    assert r["commutator_entries"] == 784 == N * N


def test_g5_identity_is_the_positive_control():
    """POSITIVE CONTROL for the same fields: ``I`` IS in G2."""
    ident = [[1 if i == j else 0 for j in range(8)] for i in range(8)]
    r = g2_membership(ident)
    assert r["in_g2"] is True
    assert r["multiplicativity_failures"] == 0
    assert r["negated_multiplicativity_failures"] == 64
    assert r["center_coset"] == "G2"
    assert r["induced_outer_class"] == "inner"


# ── G6 — the two RED controls, executed ───────────────────────────────────

def test_g6_swap_control_fails_both_commutators_and_multiplicativity():
    """``e₁ ↔ e₂``, ``e₃ ↦ −e₃``: det +1, in SO(8), and NOT in ±G2."""
    g = [[0] * 8 for _ in range(8)]
    g[0][0] = 1
    g[2][1] = 1
    g[1][2] = 1
    g[3][3] = -1
    for k in (4, 5, 6, 7):
        g[k][k] = 1
    r = g2_membership(g)
    assert r["determinant"] == 1
    assert r["tau_residual"] == 120
    assert r["swap_residual"] == 120
    assert r["centralizes_tau"] is False and r["centralizes_swap"] is False
    assert r["fixed_mod_center"] is False
    assert r["multiplicativity_failures"] == 36
    assert r["in_g2"] is False
    assert r["center_coset"] is None
    assert r["induced_outer_class"] is None


def test_g6_det_minus_one_control_cannot_centralize_the_three_cycle():
    """``diag(−1, 1, …, 1)``: its induced outer part is a TRANSPOSITION, and
    two distinct transpositions in ``S₃`` never commute — so it fails the τ
    commutator for a stated reason, and the reason is executed here via the
    shipped ``triality_frame_action``."""
    g = [[0] * 8 for _ in range(8)]
    g[0][0] = -1
    for k in range(1, 8):
        g[k][k] = 1
    r = g2_membership(g)
    assert r["determinant"] == -1
    assert r["tau_residual"] == 42
    assert r["swap_residual"] == 42
    assert r["fixed_mod_center"] is False
    assert r["in_g2"] is False
    assert r["multiplicativity_failures"] == 22
    assert r["center_coset"] is None

    # THE MECHANISM, measured: Ad(g) induces the (s c) transposition, and S_B
    # induces (v s). Distinct transpositions in S₃ do not commute.
    cols = [[Q(g[a][p] * g[b][q] - g[a][q] * g[b][p]) for (a, b) in PAIRS]
            for (p, q) in PAIRS]
    ad = [[cols[c][r] for c in range(N)] for r in range(N)]
    assert triality_frame_action(ad)["frame_action"] == {
        "v": "v", "s": "c", "c": "s"}


# ── G7 — the dissonance instrument, PROVED FIRABLE by fault injection ─────

def test_g7_dissonance_guard_fires_on_an_injected_tau_swap_split(monkeypatch):
    """``[τ,Ad(g)] = 0`` with ``[S_B,Ad(g)] ≠ 0`` is IMPOSSIBLE for orthogonal
    ``g`` — measured 0 across the whole ±G2 monomial set. So the guard is NOT
    input validation; it is a theorem check on our OWN shipped τ / S_B, and it
    fires only if the companion solve regenerates one of them wrongly.

    An instrument that cannot return otherwise is not a measurement, so the
    fault is INJECTED at the private residual seam and the raise is executed.
    """
    import srmech.physics.qm.so8 as so8

    monkeypatch.setattr(so8, "_ad_center_residuals", lambda cols: (0, 7))
    ident = [[1 if i == j else 0 for j in range(8)] for i in range(8)]
    with pytest.raises(ValueError, match="DISSONANCE"):
        so8.g2_membership(ident)


def test_g7_dissonance_guard_fires_on_an_injected_in_g2_without_tau(monkeypatch):
    """The second impossible cell: ``g ∈ G2`` but ``[τ, Ad(g)] ≠ 0``. ``G2 =
    Fix(τ)`` at the group level, so this cannot happen either."""
    import srmech.physics.qm.so8 as so8

    monkeypatch.setattr(so8, "_ad_center_residuals", lambda cols: (5, 5))
    ident = [[1 if i == j else 0 for j in range(8)] for i in range(8)]
    with pytest.raises(ValueError, match="DISSONANCE"):
        so8.g2_membership(ident)


def test_g7_control_no_injection_no_raise():
    """CONTROL for the two above: without the injected fault the same input
    returns cleanly, so the raises are caused by the fault and not by the
    fixture."""
    ident = [[1 if i == j else 0 for j in range(8)] for i in range(8)]
    assert g2_membership(ident)["in_g2"] is True


# ── G8 — induced_outer_class is FORCED, not asserted ──────────────────────

def test_g8_centralizing_both_generators_forces_the_identity_permutation():
    """The derivation behind ``induced_outer_class == 'inner'``, EXECUTED in
    ``Sym(3)`` rather than asserted in prose.

    The two frame actions come from the shipped ``triality_frame_action``; the
    centralisers and their intersection are computed over the six elements.
    ``|C(τ)| = 3`` (the 3-cycle's centraliser is ``A₃``), ``|C(S_B)| = 2``, and
    the intersection is exactly the identity — so an ``Ad(g)`` commuting with
    both can only induce the trivial permutation of ``{8v, 8s, 8c}``.
    """
    tau_p = triality_frame_action(triality_automorphism())["frame_action"]
    sb_p = triality_frame_action(triality_swap())["frame_action"]
    assert tau_p == {"v": "s", "s": "c", "c": "v"}      # OUTER, order 3
    assert sb_p == {"v": "s", "s": "v", "c": "c"}       # OUTER, order 2

    sym3 = [dict(zip(LABELS, p)) for p in itertools.permutations(LABELS)]
    assert len(sym3) == 6

    def compose(a, b):
        return {f: a[b[f]] for f in LABELS}

    c_tau = [g for g in sym3 if compose(g, tau_p) == compose(tau_p, g)]
    c_sb = [g for g in sym3 if compose(g, sb_p) == compose(sb_p, g)]
    assert len(c_tau) == 3            # A₃
    assert len(c_sb) == 2
    intersection = [g for g in c_tau if g in c_sb]
    assert intersection == [{f: f for f in LABELS}]

    # CONTROL: neither centraliser is trivial on its own, so the intersection
    # being trivial is a real conclusion and not a vacuous one.
    assert len(c_tau) > 1 and len(c_sb) > 1


def test_g8_tau_is_outer_while_the_cycling_elements_are_inner(
        cycling_automorphisms):
    """The prediction, both answers returnable from shipped ops.

    ``τ`` moves all three frames (OUTER). The 32 octonion automorphisms
    realising ``e₁ → e₂ → e₃`` are INNER — so the ``S₃`` permuting ``(i, j, k)``
    in ``Q₈`` is NOT the ``S₃`` permuting ``(8v, 8s, 8c)``; it lives INSIDE
    ``Fix(τ) = g2``.

    ⚠️ ``triality_frame_action`` cannot be the route: measured, it REFUSES
    ``Ad(g)`` for 32 of the 32 on a genuine Cartan escape. That refusal is
    executed here so the reason is recorded, not assumed.
    """
    assert triality_frame_action(triality_automorphism())["order"] == 3
    assert triality_frame_action(triality_automorphism())["fixed_frames"] == ()

    refused = 0
    for _perm, g in cycling_automorphisms:
        assert g2_membership(g)["induced_outer_class"] == "inner"
        cols = [[Q(g[a][p] * g[b][q] - g[a][q] * g[b][p]) for (a, b) in PAIRS]
                for (p, q) in PAIRS]
        ad = [[cols[c][r] for c in range(N)] for r in range(N)]
        with pytest.raises(ValueError, match="Cartan"):
            triality_frame_action(ad)
        refused += 1
    assert refused == 32


# ── G9 — the frame address, and the refusals ──────────────────────────────

def test_g9_frame_address_is_deterministic_and_binds_both_halves():
    """The address is a fixed 64-hex function of the pair ORDER and the
    octonion TABLE, and both halves are load-bearing: recomputing it with a
    different pair separator gives a DIFFERENT value, which is the control
    proving the pair order is really in there."""
    addr = epq_frame_address()
    assert len(addr) == 64 and int(addr, 16) >= 0
    assert epq_frame_address() == addr                       # memoised, stable

    from srmech.amsc.format import sha256_bytes

    table_sha = octonion_table_attestation()["attestation"]["response_sha256"]
    pair_bytes = b";".join(b"%d,%d" % (p, q) for (p, q) in PAIRS)
    payload = b"srmech/so8/epq-frame/1\n" + pair_bytes + b"\n" \
        + table_sha.encode("ascii") + b"\n"
    assert sha256_bytes(payload) == addr

    # CONTROL: a different pair order is a different frame, hence a different
    # address. (Reversing the pair list is exactly the "second-frame producer"
    # case the ruling says widens the discriminator set.)
    other = b";".join(b"%d,%d" % (p, q) for (p, q) in reversed(PAIRS))
    assert sha256_bytes(b"srmech/so8/epq-frame/1\n" + other + b"\n"
                        + table_sha.encode("ascii") + b"\n") != addr


def test_g9_non_orthogonal_input_is_refused():
    """``Ad(g): X ↦ g X gᵀ`` preserves antisymmetry only on ``O(8)``, so the
    object this op decides about does not exist off it."""
    with pytest.raises(ValueError, match="not orthogonal"):
        g2_membership([[2 if i == j else 0 for j in range(8)]
                       for i in range(8)])


def test_g9_wrong_shape_is_refused():
    with pytest.raises(ValueError, match="8x8"):
        g2_membership([[1, 0], [0, 1]])
    with pytest.raises(ValueError, match="28x28"):
        so8_bracket_certificate([[1, 0], [0, 1]])


# ── G10 — so8_adjoint_basis: the float carrier, MEASURED not assumed ──────

def test_g10_adjoint_basis_entries_are_integers_carried_as_float():
    """The so(8) structure constants ARE integers, and ``Mat`` is by contract
    the float64 carrier (``QMat`` is the exact one) — so this is not a defect,
    it is the carrier contract. What was never MEASURED is that the values are
    exactly representable in it. They are: every entry is integer-valued with
    magnitude ≤ 4, far inside float64's exact-integer range ``2⁵³``.

    Changing the return type to an exact carrier would widen a discriminator
    set and must close its projection gap in the same change — out of scope
    for this rc, and recorded as such rather than left implied.
    """
    adj = so8_adjoint_basis()
    assert len(adj) == N
    types, non_integer, max_magnitude, total = set(), 0, 0, 0
    for m in adj:
        for row in m.tolist():
            for x in row:
                types.add(type(x).__name__)
                total += 1
                if float(x) != int(float(x)):
                    non_integer += 1
                # Class K pin-slot at the sign boundary, Class C to re-apply.
                magnitude = x if x >= 0 else -x
                if magnitude > max_magnitude:
                    max_magnitude = magnitude
    assert types == {"float"}
    assert total == N * 8 * 8 == 1792
    assert non_integer == 0
    assert max_magnitude == 4.0
    assert max_magnitude < 2 ** 53
