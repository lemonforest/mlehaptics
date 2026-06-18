"""v0.7.0rc2 — the 7-D cross product + G₂ associative 3-form (MS #21 / #813).

Bit-exact ground-truth from F281 (commit 4e8c5184), all COMPUTED FROM the
shipped ``loop_bind`` so cross7/g2_three_form agree with the rc1 bind by
construction:

  - cross7(x,y) = Im(loop_bind(x,y)); the full antisymmetric 7×7 basis table
  - the identities ‖x×y‖² = ‖x‖²‖y‖² − ⟨x,y⟩² and Re(x·y) = −⟨x,y⟩ (imaginaries)
  - g2_three_form = ⟨x, cross7(y,z)⟩; the 7 Fano triples + signs (the two − are
    (1,6,7) and (3,5,6)); the other 28 of C(7,3)=35 are exactly 0
  - the TRIALITY VERDICT (F281, owned): dim Der(loop_bind) = 14 = G₂, and a
    generic O(8) rotation BREAKS the bind ⟹ triality does NOT preserve the
    bind; the 14-dim G₂ does.

numpy-FREE (#564): numpy is GONE from srmech, so this test runs with numpy NOT
installed. ``cross7`` / ``g2_three_form`` / ``loop_bind`` take plain lists and
return lists / floats; the 7-D cross product IS the explicit Fano-plane formula
and the 3-form IS φ(x,y,z) = ⟨x, x×y⟩, so the oracles are the hand-derived F281
basis tables + plain-list dot/cross. The derivation-algebra rank is the EXACT
RREF rank (``so8._rank_exact``, numpy-free); the generic O(8) rotation is built
numpy-free via the cascade ``matrix_cascades.qr`` (orthonormal Q).

Class-K clean throughout: zero/identity tests via the inner-product norm² ⟨v,v⟩,
never abs() (``[[feedback_sign_handling_is_class_k_pin_slot_not_alu_abs]]``).
"""
import itertools
import random

from srmech.amsc.cascade import matrix_cascades as mc
from srmech.amsc.hdc import (
    LOOP_DIM,
    cross7,
    g2_three_form,
    loop_bind,
)
from srmech.qm.so8 import _rank_exact

DIM = 8
SEED = 12345


def _e(i, dim=DIM):
    v = [0.0] * dim
    v[i] = 1.0
    return v


def _dot(a, b):
    return sum(float(x) * float(y) for x, y in zip(a, b))


def _normsq(v):
    return _dot(v, v)


def _scaled_e(scale, i, dim=DIM):
    """scale · e_i as a plain list."""
    v = [0.0] * dim
    v[i] = float(scale)
    return v


def _allclose(a, b, tol=1e-9):
    """Element-wise closeness over plain lists (abs() for a test tolerance is
    fine; the SUBSTRATE sign-handling stays Class-K, this is just the gate)."""
    return all(abs(float(x) - float(y)) < tol for x, y in zip(a, b))


def _rand_vec(rng, dim=DIM):
    return [rng.gauss(0.0, 1.0) for _ in range(dim)]


def _matmul(a, b):
    n, k, m = len(a), len(b), len(b[0])
    return [
        [sum(a[i][p] * b[p][j] for p in range(k)) for j in range(m)]
        for i in range(n)
    ]


def _transpose(a):
    return [[a[i][j] for i in range(len(a))] for j in range(len(a[0]))]


def _matvec(a, x):
    return [sum(a[i][p] * x[p] for p in range(len(x))) for i in range(len(a))]


# The bit-exact cross7 basis table (F281), upper triangle (i<j); cross7(e_i,e_j)
# = sign·e_k. Antisymmetry gives the lower triangle; the diagonal is 0.
CROSS7_UPPER = {
    (1, 2): (+1, 3), (1, 3): (-1, 2), (1, 4): (+1, 5), (1, 5): (-1, 4),
    (1, 6): (-1, 7), (1, 7): (+1, 6),
    (2, 3): (+1, 1), (2, 4): (+1, 6), (2, 5): (+1, 7), (2, 6): (-1, 4),
    (2, 7): (-1, 5),
    (3, 4): (+1, 7), (3, 5): (-1, 6), (3, 6): (+1, 5), (3, 7): (-1, 4),
    (4, 5): (+1, 1), (4, 6): (+1, 2), (4, 7): (+1, 3),
    (5, 6): (-1, 3), (5, 7): (+1, 2),
    (6, 7): (-1, 1),
}

# The 7 nonzero (Fano) g2_three_form triples + signs (F281).
G2_FANO = {
    (1, 2, 3): +1, (1, 4, 5): +1, (1, 6, 7): -1, (3, 5, 6): -1,
    (2, 4, 6): +1, (2, 5, 7): +1, (3, 4, 7): +1,
}


def test_loop_dim_is_octonion():
    assert LOOP_DIM == 8


def test_cross7_basis_table_bit_exact():
    # [1] every basis product matches the F281 table; antisymmetric; 0 on diag.
    for i in range(1, DIM):
        assert _normsq(cross7(_e(i), _e(i))) < 1e-18  # diagonal zero
    for (i, j), (sign, k) in CROSS7_UPPER.items():
        assert _allclose(cross7(_e(i), _e(j)), _scaled_e(sign, k))
        assert _allclose(cross7(_e(j), _e(i)), _scaled_e(-sign, k))  # antisymmetry


def test_cross7_is_imaginary_part_of_bind():
    # cross7 = Im(loop_bind): the e₀ component is always dropped.
    rng = random.Random(SEED)
    for _ in range(20):
        x, y = _rand_vec(rng), _rand_vec(rng)
        c = cross7(x, y)
        assert abs(c[0]) < 1e-18
        assert _allclose(c[1:], loop_bind(x, y)[1:])


def test_cross7_norm_identity_on_imaginaries():
    # ‖x×y‖² = ‖x‖²‖y‖² − ⟨x,y⟩²  and  Re(x·y) = −⟨x,y⟩  (imaginary x,y)
    rng = random.Random(SEED)
    for _ in range(50):
        x, y = _rand_vec(rng), _rand_vec(rng)
        x[0] = 0.0
        y[0] = 0.0
        lhs = _normsq(cross7(x, y))
        rhs = _normsq(x) * _normsq(y) - _dot(x, y) ** 2
        assert abs(lhs - rhs) < 1e-9
        assert abs(loop_bind(x, y)[0] + _dot(x, y)) < 1e-9  # Re = −⟨x,y⟩


def test_g2_three_form_fano_triples_bit_exact():
    # [2] exactly the 7 Fano triples are ±1; all other 28 basis triples are 0.
    for trip in itertools.combinations(range(1, DIM), 3):
        want = G2_FANO.get(trip, 0)
        got = g2_three_form(_e(trip[0]), _e(trip[1]), _e(trip[2]))
        assert abs(got - want) < 1e-9, f"{trip}: got {got}, want {want}"
    nonzero = sum(
        1
        for t in itertools.combinations(range(1, DIM), 3)
        if abs(g2_three_form(_e(t[0]), _e(t[1]), _e(t[2]))) > 1e-9
    )
    assert nonzero == 7


def test_g2_three_form_consistency_and_antisymmetry():
    # φ(x,y,z) == ⟨x, cross7(y,z)⟩ by definition (all inputs); fully antisymmetric
    # (swap → −) on the IMAGINARY octonions ℝ⁷ where the G₂ 3-form lives — for
    # general 8-D vectors cross7 carries a symmetric real-part term (Im(y·z)
    # includes y₀·Im(z)+z₀·Im(y)), so antisymmetry is an Im(𝕆)=ℝ⁷ statement.
    rng = random.Random(SEED)
    for _ in range(30):
        x, y, z = _rand_vec(rng), _rand_vec(rng), _rand_vec(rng)
        assert abs(g2_three_form(x, y, z) - _dot(x, cross7(y, z))) < 1e-12
        xi, yi, zi = list(x), list(y), list(z)
        xi[0] = yi[0] = zi[0] = 0.0   # restrict to Im(𝕆) = ℝ⁷
        phi = g2_three_form(xi, yi, zi)
        assert abs(phi + g2_three_form(yi, xi, zi)) < 1e-9   # swap x,y
        assert abs(phi + g2_three_form(xi, zi, yi)) < 1e-9   # swap y,z


# ── triality verdict (F281, owned): Aut(loop_bind) = the 14-dim G₂, not τ ──

def _derivation_nullity():
    """dim of the Leibniz/derivation algebra of loop_bind: D with
    D(xy) = (Dx)y + x(Dy) for all basis pairs. = dim Der(𝕆) = 14 = G₂.

    Numpy-free: the constraint matrix's rank is the EXACT RREF rank
    (``so8._rank_exact``, rational Gaussian elimination — exact on the
    ``{-1, 0, +1}`` octonion structure constants), and nullity = (DIM·DIM) −
    rank. (``_rank_exact`` is transpose-invariant, so passing the constraint
    ROWS as its column stack yields the matrix rank.)"""
    e = [_e(i) for i in range(DIM)]
    m = [[loop_bind(e[i], e[j]) for j in range(DIM)] for i in range(DIM)]
    rows = []
    for i in range(DIM):
        for j in range(DIM):
            for c in range(DIM):
                row = [0.0] * (DIM * DIM)
                for b in range(DIM):          # +(D @ m_ij)[c]
                    row[c * DIM + b] += m[i][j][b]
                for a in range(DIM):          # −(Σ_a D[a,i] m_aj)[c]
                    row[a * DIM + i] -= m[a][j][c]
                for b in range(DIM):          # −(Σ_b D[b,j] m_ib)[c]
                    row[b * DIM + j] -= m[i][b][c]
                rows.append(row)
    return DIM * DIM - _rank_exact(rows)


def test_derivation_algebra_is_g2_dim_14():
    # Aut(loop_bind) has Lie algebra Der = G₂ = 14 (≠ so(8) = 28). F273/F281.
    assert _derivation_nullity() == 14


def test_generic_o8_rotation_breaks_the_bind():
    # A generic O(8) rotation is NOT a bind-automorphism ⟹ triality (which lives
    # in so(8)=28, not the fixed 14) does NOT preserve loop_bind; G₂ does. F281.
    # Numpy-free: a generic orthonormal Q is the cascade QR factor of a random
    # 8×8 matrix (matrix_cascades.qr), and the action is plain-list matvec.
    rng = random.Random(SEED)
    a = [[rng.gauss(0.0, 1.0) for _ in range(DIM)] for _ in range(DIM)]
    Q, _ = mc.qr(a)  # generic orthogonal (reduced QR of a full-rank square)
    # Q is genuinely orthonormal (Qᵀ·Q = I) — the property under test relies on it.
    gram = _matmul(_transpose(Q), Q)
    assert all(
        abs(gram[i][j] - (1.0 if i == j else 0.0)) < 1e-9
        for i in range(DIM)
        for j in range(DIM)
    )
    worst = 0.0
    for _ in range(20):
        x, y = _rand_vec(rng), _rand_vec(rng)
        qx, qy = _matvec(Q, x), _matvec(Q, y)
        diff = [
            _matvec(Q, loop_bind(x, y))[t] - loop_bind(qx, qy)[t]
            for t in range(DIM)
        ]
        worst = max(worst, _normsq(diff))   # norm², never abs()
    assert worst > 1e-3  # breaks (residual ≫ 0) — not an automorphism
