"""rc443 (`#T1151`) — ``triality_companions`` must not ROUND the caller's operator.

``_solve_companions`` built its normal equations with
``rhs_m = int(round(target[m]))``. ``target = operator·(e_i * e_j)`` is CALLER
data, so through rc442 the op returned the companions of the caller's operator
**with every entry rounded half-to-even to an integer** — silently, with no
exception and a well-formed real ``8×8`` :class:`Mat`, inside a routine whose
docstring claims *"exact-ℚ, native-independent … NO float ``mat_solve``, NO
Tikhonov ridge … BIT-IDENTICAL on every platform"*.

MEASURED RED at rc442 (this file's five legs, run against ``origin/main``):

* **Linearity.** Cartan's relation ``A(x*y) = B(x)*y + x*C(y)`` is LINEAR in
  ``(A, B, C)``, so ``companions(k·A)`` must equal ``k·companions(A)`` for every
  real ``k``. Over 20 coefficients: the 5 integer ones gave residual ``0.0``;
  **all 15 fractional ones violated the relation** (residuals ``1.6 … 8.0``),
  7 of them by returning the all-zero matrix.
* **Composition.** The op's own output is fractional — ``8 of 64`` entries of
  ``companions(E_pq)`` are ``±0.5`` — so feeding it back in is ordinary API
  composition, and it broke:
  ``residual(companions(companions(A))) = 32.0``.
* **The law.** ``companions(X) == companions(round_half_even(X))``, measured
  9/9: ``companions(1.5·A)`` was BIT-IDENTICAL to ``companions(2.0·A)``,
  ``companions(0.5·A)`` to ``companions(0.0·A)`` (all-zero).

Why it survived since rc33: every in-tree caller passes an INTEGER operator.
:func:`~srmech.physics.qm.triality._companion_maps` iterates the ``±1``
``E_pq`` generators, so ``tau`` / ``S_B`` / ``S_C`` / ``Fix(tau) = g2`` are
unaffected and the shipped theorems are correct. Only the public entry point on
non-integer input was wrong, and nothing exercised it. Leg 5 pins those
untouched values as literals **captured from ``origin/main`` at rc442**, so this
gate cannot go green by breaking the theorems it is meant to leave alone.

THE FIX. ``_octonion_mul(e_i, e_j)`` is a ``±1`` unit vector, so ``_matvec``
performs one ``±1`` multiply and adds zeros: ``target[m]`` is exactly ``±`` an
operator entry, already bit-exact as a float. The Class-N
:func:`srmech.math.q.to_q` promotion is therefore LOSSLESS — the rounding was
the only lossy step. The structure constants at the other two ``round`` sites
genuinely ARE integers (leg 6 measures it rather than asserting it), and they
now coerce through :func:`~srmech.physics.qm.triality._exact_int`, which RAISES
on a non-integer instead of absorbing it.

Discipline: numpy-free (a test for a numpy-free module must itself be
numpy-free); the Class-K pin-slot :func:`srmech.cascade.magnitude` everywhere a
deviation is measured, **never** ``abs()``
(``[[feedback_sign_handling_is_class_k_pin_slot_not_alu_abs]]``); no stdlib
``fractions`` / ``math`` / ``decimal``.
"""
from __future__ import annotations

import pytest

from srmech.amsc.format import sha256_bytes
from srmech.cascade import magnitude
from srmech.math.mat import Mat
from srmech.math.q import Q, to_q
from srmech.math.qmat import QMat
from srmech.physics.qm import so8, triality


_DIM = 8
_NVAR = 128

#: Regression pins CAPTURED FROM ``origin/main`` (rc442, commit ``a9f3a6aaf``)
#: before the fix, and re-measured identical after it. The canonical bytes are
#: the shortest round-tripping ``repr`` of every entry, row-major — NOT
#: ``Mat.tobytes()``, whose ``array('d')`` memory image is byte-order dependent.
#: ``repr(float)`` is unique per bit pattern, so this is equally BIT-exact and
#: portable across platforms.
_PIN_TAU = "70005c38335203118818ad628b36ef48694294c06ef62515aa639b0bd0579d33"
_PIN_S_B = "25a3e1307c39f30efad291f2b9e325f39be149f4a73c779737da3204b7e1bfbe"
_PIN_S_C = "75c7ec728dde1f9559660ede73b697a53ad0db73b1ba62097415d59033c9a913"
_PIN_COMPANION_B = "e0904af06e0e5c96ce47af48ee9155c78ff20d445ecbd7cb1d7a037ac02f2b9d"
_PIN_COMPANION_C = "ff1ef8fdcc922bc9f3dd5a062243891a85bf862bcabdb6edff13f89f3b9dc1e6"

#: ``Fix(tau) = g2`` (dim 14) — the D4 →(Z3) G2 theorem — and ``Fix(S_B) =
#: so(7)`` (dim 21), the D4 → B3 fold. Both must survive the fix untouched.
_PIN_FIX_TAU = 14
_PIN_FIX_S_B = 21

#: Exact ``0.0`` is the only acceptable residual here: the operators below are
#: float-scalar multiples of an INTEGER generator, so the exact-ℚ solution is a
#: dyadic-times-``k`` rational that is representable in float64 without loss.
_EXACT = 0.0


def _canonical_bytes(m: Mat) -> bytes:
    """Endian-independent canonical serialisation of a real ``Mat``."""
    return "|".join(";".join(repr(x) for x in row)
                    for row in m.tolist()).encode("utf-8")


def _digest(m: Mat) -> str:
    return sha256_bytes(_canonical_bytes(m))


def _scale(rows, k):
    return [[k * x for x in r] for r in rows]


def _max_deviation(got, want) -> float:
    """Largest entrywise deviation, via the Class-K pin-slot magnitude."""
    return max(magnitude(got[i][j] - want[i][j])
               for i in range(_DIM) for j in range(_DIM))


@pytest.fixture(scope="module")
def integer_generator():
    """A ``±1`` integer ``so(8)`` generator — the shape every in-tree caller
    passes, and the baseline the linearity law is measured against."""
    return [list(r) for r in so8._epq_basis()[0]]


@pytest.fixture(scope="module")
def integer_companions(integer_generator):
    """``companions(A)`` for the integer generator (the companion solve is ~1 s,
    so the whole module shares one)."""
    g_s, g_c = triality.triality_companions(integer_generator)
    return g_s.tolist(), g_c.tolist()


# ── LEG 1 — LINEARITY (red at rc442: 15/15 fractional coefficients) ───────────
#: Dyadic AND non-dyadic fractional scalings, plus integers as the control.
_DYADIC = (0.5, 0.25, 0.125, 0.75, 1.5, 2.5, 3.5, -0.5)
_NON_DYADIC = (0.1, 0.2, 0.3, 0.4, 0.6, 0.7, 0.9, 1.2, -0.7)


@pytest.mark.parametrize("k", _DYADIC + _NON_DYADIC)
def test_companions_are_linear_in_the_operator(k, integer_generator,
                                               integer_companions):
    """``companions(k·A) == k·companions(A)`` and the Cartan residual is EXACTLY
    zero — for dyadic and non-dyadic ``k`` alike.

    RED at rc442 on every one of these: the rounded right-hand side returned the
    companions of ``round(k)·A`` instead, so both the equality and the residual
    failed (residuals ``1.6 … 8.0``).
    """
    b_ref, c_ref = integer_companions
    operator = _scale(integer_generator, k)
    g_s, g_c = triality.triality_companions(operator)

    assert _max_deviation(g_s.tolist(), _scale(b_ref, k)) == _EXACT, (
        f"g_s(k·A) != k·g_s(A) at k={k!r}")
    assert _max_deviation(g_c.tolist(), _scale(c_ref, k)) == _EXACT, (
        f"g_c(k·A) != k·g_c(A) at k={k!r}")

    residual = triality.triality_relation_residual(operator, g_s, g_c)
    assert magnitude(residual) == _EXACT, (
        f"Cartan's relation violated at k={k!r}: residual={residual!r}")


def test_fractional_companions_are_not_the_zero_matrix(integer_generator):
    """The 7 coefficients that rounded to 0 returned an all-zero ``8×8`` at
    rc442 — a *plausible* answer, which is what made the defect silent."""
    for k in (0.5, 0.25, 0.1, 0.2, 0.4, 0.125, 0.3):
        g_s, g_c = triality.triality_companions(_scale(integer_generator, k))
        for name, m in (("g_s", g_s), ("g_c", g_c)):
            nonzero = sum(1 for row in m.tolist() for x in row
                          if magnitude(x) != 0.0)
            assert nonzero > 0, f"{name}(k={k!r}) is the all-zero matrix"


# ── LEG 2 — COMPOSITION (red at rc442: residual 32.0) ─────────────────────────
def test_companions_of_a_companion_satisfy_cartan(integer_companions):
    """``companions(companions(A))`` obeys Cartan's relation.

    This is pure in-API composition, not an exotic input: ``8 of 64`` entries of
    ``companions(E_pq)`` are ``±0.5``, so the op's OWN output is a fractional
    operator. RED at rc442 with residual ``32.0``.
    """
    b_ref, _ = integer_companions
    fractional = sum(1 for row in b_ref for x in row
                     if magnitude(x - float(int(x))) != 0.0)
    assert fractional == 8, (
        f"expected 8 of 64 companion entries to be fractional; got {fractional}")

    g_s, g_c = triality.triality_companions(b_ref)
    residual = triality.triality_relation_residual(b_ref, g_s, g_c)
    assert magnitude(residual) == _EXACT, (
        f"companions(companions(A)) violates Cartan: residual={residual!r}")


# ── LEG 3 — NON-VACUITY (the integer path was already green; keep it green) ───
@pytest.mark.parametrize("k", (1.0, 2.0, 3.0, -1.0, -4.0))
def test_integer_operator_path_stays_exact(k, integer_generator,
                                           integer_companions):
    """The gate cannot pass by breaking the integer path — it was correct at
    rc442 and must stay correct."""
    b_ref, c_ref = integer_companions
    operator = _scale(integer_generator, k)
    g_s, g_c = triality.triality_companions(operator)
    assert _max_deviation(g_s.tolist(), _scale(b_ref, k)) == _EXACT
    assert magnitude(
        triality.triality_relation_residual(operator, g_s, g_c)) == _EXACT


def test_derivation_companions_are_triality_fixed(integer_generator):
    """A ``g2`` derivation is triality-fixed: ``g_s = g_c = g_v`` (Baez §2.4).
    An independent structural oracle on the integer path."""
    derivation = so8.g2_subalgebra()[0].tolist()
    g_s, g_c = triality.triality_companions(derivation)
    assert _max_deviation(g_s.tolist(), derivation) == _EXACT
    assert _max_deviation(g_c.tolist(), derivation) == _EXACT


# ── LEG 4 — NEGATIVE CONTROL ON THE LAW (proves the MECHANISM is gone) ────────
#: ``(coefficient, what Python's banker's ``round`` sends it to)``. At rc442
#: ``companions`` of the two were BIT-IDENTICAL, 9/9. If any pair still matches,
#: the round-half-to-even mechanism survived — a green leg 1 alone would not
#: prove that (a *different* wrong answer could also be linear-looking on the
#: sampled points).
_ROUNDING_PAIRS = ((0.5, 0.0), (1.5, 2.0), (2.5, 2.0), (3.5, 4.0),
                   (0.25, 0.0), (0.75, 1.0), (1.2, 1.0), (0.9, 1.0), (2.4, 2.0))


@pytest.mark.parametrize("k,rounds_to", _ROUNDING_PAIRS)
def test_companions_do_not_equal_the_rounded_operators(k, rounds_to,
                                                       integer_generator):
    """``companions(k·A) != companions(round(k)·A)`` — the rc442 law must not
    hold for any of the 9 pairs that established it."""
    frac, _ = triality.triality_companions(_scale(integer_generator, k))
    rounded, _ = triality.triality_companions(_scale(integer_generator,
                                                     rounds_to))
    assert _max_deviation(frac.tolist(), rounded.tolist()) != 0.0, (
        f"companions({k!r}·A) is still bit-identical to "
        f"companions({rounds_to!r}·A) — the rounding mechanism survived")


# ── LEG 5 — REGRESSION PINS (the shipped theorems must not move) ──────────────
def test_tau_swap_and_companion_maps_are_bit_identical_to_rc442():
    """``tau`` / ``S_B`` / ``S_C`` are built from the ``±1`` ``E_pq``
    generators, so the fix must not move a single bit of them."""
    s_b_rows, s_c_rows = triality._companion_maps()
    assert _digest(triality.triality_automorphism()) == _PIN_TAU
    assert _digest(triality.triality_swap()) == _PIN_S_B
    assert _digest(Mat.from_rows([list(r) for r in s_b_rows])) == _PIN_S_B
    assert _digest(Mat.from_rows([list(r) for r in s_c_rows])) == _PIN_S_C


def test_integer_companions_are_bit_identical_to_rc442(integer_companions):
    """The companions of the integer generator likewise do not move."""
    b_ref, c_ref = integer_companions
    assert _digest(Mat.from_rows(b_ref)) == _PIN_COMPANION_B
    assert _digest(Mat.from_rows(c_ref)) == _PIN_COMPANION_C


def _nullspace_dim_exact(m: Mat) -> int:
    """``dim ker(m - I)`` with the rank taken EXACTLY over ℚ (no float
    tolerance) via :func:`srmech.physics.qm.so8._rank_exact`."""
    rows = m.tolist()
    n = len(rows)
    columns = [[rows[r][c] - (1.0 if r == c else 0.0) for r in range(n)]
               for c in range(n)]
    return n - so8._rank_exact(columns)


def test_fixed_subalgebra_dimensions_are_unchanged():
    """``Fix(tau) = g2`` (dim 14) and ``Fix(S_B) = so(7)`` (dim 21) survive."""
    assert _nullspace_dim_exact(triality.triality_automorphism()) == _PIN_FIX_TAU
    assert _nullspace_dim_exact(triality.triality_swap()) == _PIN_FIX_S_B


# ── LEG 6 — the structure-constant claim, MEASURED not asserted ───────────────
def test_octonion_structure_constants_are_exactly_plus_minus_one_or_zero():
    """The ``{-1, 0, +1}`` claim at the other two ``round`` sites, measured.

    Per ``[[feedback_an_asserted_algebraic_property_is_not_a_measured_one]]``:
    the 512 entries of the structure-constant tensor take exactly THREE distinct
    float values — ``-1.0`` (28×), ``0.0`` (448×), ``+1.0`` (36×) — and NONE is
    moved by ``round``. So rounding them was a genuine no-op, and the two sites
    at ``triality.py`` lines 326/330 were never the defect; only the caller-data
    site was. The claim is now enforced by
    :func:`~srmech.physics.qm.triality._exact_int` rather than assumed.
    """
    table = triality._table_float()
    tally = {}
    for i in range(_DIM):
        for j in range(_DIM):
            for k in range(_DIM):
                value = table[i][j][k]
                # Integrality WITHOUT abs(): the Class-K magnitude of the
                # deviation from the truncated value is exactly 0, and the
                # magnitude itself is bounded by 1.
                assert magnitude(value - float(int(value))) == 0.0, (
                    f"structure constant C[{i}][{j}][{k}] = {value!r} "
                    f"is not an integer")
                assert magnitude(value) <= 1.0, (
                    f"structure constant C[{i}][{j}][{k}] = {value!r} "
                    f"is outside {{-1, 0, +1}}")
                tally[repr(value)] = tally.get(repr(value), 0) + 1
    assert tally == {"-1.0": 28, "0.0": 448, "1.0": 36}, tally


def test_exact_int_refuses_a_non_integer_instead_of_absorbing_it():
    """``_exact_int`` is a coercion that RAISES, not a rounding that absorbs —
    the property ``int(round(...))`` lacked."""
    assert triality._exact_int(-1.0, "probe") == -1
    assert triality._exact_int(0.0, "probe") == 0
    assert triality._exact_int(1.0, "probe") == 1
    with pytest.raises(ValueError, match="refusing to round"):
        triality._exact_int(0.5, "probe")
    with pytest.raises(ValueError, match="refusing to round"):
        triality._exact_int(1.5, "probe")


# ── LEG 7 — the standalone-C srmech_qmat_rref mirror, RE-VERIFIED over ℚ ──────
def _normal_equations(op_rows):
    """The rc443 accumulation: INTEGER Gram ``G``, exact-ℚ right-hand side ``c``
    — the same construction :func:`triality._solve_companions` performs."""
    table = triality._table_float()
    basis = triality._eye(_DIM)
    g = [[0] * _NVAR for _ in range(_NVAR)]
    c = [Q(0)] * _NVAR
    for i in range(_DIM):
        for j in range(_DIM):
            target = triality._matvec(
                op_rows, triality._octonion_mul(basis[i], basis[j]))
            for m in range(_DIM):
                entries = []
                for k in range(_DIM):
                    bval = table[k][j][m]
                    if bval != 0.0:
                        entries.append((k * _DIM + i,
                                        triality._exact_int(bval, "C[k][j][m]")))
                    cval = table[i][k][m]
                    if cval != 0.0:
                        entries.append((_DIM * _DIM + k * _DIM + j,
                                        triality._exact_int(cval, "C[i][k][m]")))
                rhs_m = to_q(target[m])
                for col_a, val_a in entries:
                    c[col_a] = c[col_a] + rhs_m * val_a
                    row_a = g[col_a]
                    for col_b, val_b in entries:
                        row_a[col_b] += val_a * val_b
    return g, c


def _qmat_rref_solution(g, c):
    """The bare-C-host mirror: RREF the augmented ``[G | c]`` through
    :meth:`srmech.math.qmat.QMat.rref` (the ``c_dispatched`` ``srmech_qmat_rref``
    when native is present), then pin the free columns to 0."""
    augmented = QMat.from_rows(
        [[to_q(g[r][col]) for col in range(_NVAR)] + [to_q(c[r])]
         for r in range(_NVAR)])
    reduced = augmented.rref()
    solution = [Q(0)] * _NVAR
    used = set()
    for r in range(_NVAR):
        pivot = None
        for col in range(_NVAR):
            if reduced[r, col] != 0:
                pivot = col
                break
        if pivot is not None and pivot not in used:
            used.add(pivot)
            solution[pivot] = reduced[r, _NVAR]
    return solution


@pytest.mark.parametrize("k", (1.0, 1.5))
def test_qmat_rref_mirror_survives_the_rational_right_hand_side(
        k, integer_generator):
    """``_exact_solve_normal_equations``'s docstring claims the whole solve is
    standalone-reproducible in a bare-C host by ``srmech_qmat_rref`` over the
    same augmented ``[G | c]``, BYTE-IDENTICALLY. rc443 changes that augmented
    column's type from ``int`` to exact ℚ, so the claim is re-verified rather
    than left standing — on an integer operator (``k=1.0``) AND a fractional one
    (``k=1.5``), which the rc442 spelling could not have reached at all.
    """
    operator = _scale(integer_generator, k)
    g, c = _normal_equations(operator)
    sparse = triality._exact_solve_normal_equations(g, c, _NVAR)
    mirror = _qmat_rref_solution(g, c)
    mismatches = [i for i in range(_NVAR) if sparse[i] != mirror[i]]
    assert not mismatches, (
        f"srmech_qmat_rref mirror diverged from the sparse solve at k={k!r} "
        f"in {len(mismatches)} of {_NVAR} unknowns")

    # …and the sparse solve is genuinely what the shipped op returns.
    shipped, _ = triality.triality_companions(operator)
    from_solve = [[float(sparse[i * _DIM + j]) for j in range(_DIM)]
                  for i in range(_DIM)]
    assert shipped.tolist() == from_solve


def test_numpy_is_absent():
    """A test for a numpy-free module must itself be numpy-free
    (``[[feedback_test_for_numpy_free_module_must_itself_be_numpy_free]]``)."""
    import sys
    assert "numpy" not in sys.modules
