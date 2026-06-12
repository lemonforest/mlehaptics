"""v0.7.0rc1 — the Moufang loop-bind (k=7 gauge arithmetic; MS #21 / #814).

Ports the F271/F272 reference self-tests (the `loop_bind_moufang.py` oracle)
against the PRODUCTION `srmech.amsc.hdc` loop-bind family:

  - exactly 7 associator-zero basis triples = the associative 3-planes (Fano lines)
  - L_a != R_a != R_aᵀ, and [L_a, R_b]·x == -loop_associator(a, x, b)
  - the three Moufang identities hold (the loop is Moufang)
  - the tangent algebra is Mal'cev, NOT Lie (Jacobi fails, Mal'cev holds)
  - the inverse unbinds: loop_bind(x, loop_inv(x)) == e0 (Moufang division)
  - associativity on a two-generator subalgebra (Artin's theorem)

Class-K clean throughout: zero-tests via the inner-product norm² ⟨v,v⟩, never
abs() (`[[feedback_sign_handling_is_class_k_pin_slot_not_alu_abs]]`).

rc125 (numpy-free, #564): this test is itself numpy-FREE — the loop family
returns ``list[float]`` (single-element) / :class:`srmech.amsc.mat.Mat` (the
L/R operators); operator products / matvecs route through ``mat_matmul``,
norms through ``mat_norm``, and the random vectors come from stdlib
``random.Random`` (no numpy oracle, per
`[[feedback_test_for_numpy_free_module_must_itself_be_numpy_free]]`).
"""
import itertools
import random

from srmech.amsc.laplacian import mat_matmul, mat_norm
from srmech.amsc.mat import Mat
from srmech.amsc.hdc import (
    LOOP_DIM,
    loop_associator,
    loop_bind,
    loop_conj,
    loop_inv,
    loop_left_op,
    loop_right_op,
)

DIM = 8
SEED = 12345  # attested-B reproducibility seed (matches the reference oracle)


def _e(i, dim=DIM):
    v = [0.0] * dim
    v[i] = 1.0
    return v


def _vsub(u, v):
    return [u[i] - v[i] for i in range(len(u))]


def _normsq(v):
    return float(sum(x * x for x in v))


def _matvec(m, v):
    rows = m.tolist()
    return [sum(rows[i][j] * v[j] for j in range(len(v))) for i in range(len(rows))]


def _commutator(a, b):
    return _vsub(loop_bind(a, b), loop_bind(b, a))


def _standard_normal(rng, n):
    return [rng.gauss(0.0, 1.0) for _ in range(n)]


def _fano_lines():
    return [
        t
        for t in itertools.combinations(range(1, DIM), 3)
        if _normsq(loop_associator(_e(t[0]), _e(t[1]), _e(t[2]))) < 1e-9
    ]


def test_loop_dim_is_octonion():
    assert LOOP_DIM == 8


def test_seven_associative_fano_lines():
    # [1] exactly 7 associator-zero triples = the associative 3-planes
    assert len(_fano_lines()) == 7


def test_left_right_distinct_and_residue_identity():
    # [2] L != R != Rᵀ ; and [L_a, R_b]·x == -associator(a, x, b)
    a, b, x = _e(1), _e(2), _e(4)
    La, Ra = loop_left_op(a), loop_right_op(a)
    assert mat_norm(_mat_sub(La, Ra)) > 1e-9          # L != R
    assert mat_norm(_mat_sub(La, Ra.T)) > 1e-9        # L != Rᵀ
    # [L_a, R_b] = L_a·R_b − R_b·L_a (operator commutator over Mats).
    lb, rb = loop_left_op(a), loop_right_op(b)
    lr = _mat_sub(mat_matmul(lb, rb), mat_matmul(rb, lb))
    lhs = _matvec(lr, x)
    rhs = [-v for v in loop_associator(a, x, b)]
    assert mat_norm(_vsub(lhs, rhs)) < 1e-9


def test_three_moufang_identities():
    # [3] all three Moufang identities hold (the loop is Moufang)
    rng = random.Random(SEED)
    worst = 0.0
    for _ in range(50):
        z, u, w = (_standard_normal(rng, DIM) for _ in range(3))
        m1 = _vsub(loop_bind(z, loop_bind(u, loop_bind(z, w))),
                   loop_bind(loop_bind(loop_bind(z, u), z), w))
        m2 = _vsub(loop_bind(u, loop_bind(z, loop_bind(w, z))),
                   loop_bind(loop_bind(loop_bind(u, z), w), z))
        m3 = _vsub(loop_bind(loop_bind(u, w), loop_bind(z, u)),
                   loop_bind(u, loop_bind(loop_bind(w, z), u)))
        worst = max(worst, _normsq(m1), _normsq(m2), _normsq(m3))
    assert worst < 1e-18


def test_jacobi_fails_malcev_holds():
    # [4] tangent algebra is Mal'cev, NOT Lie
    rng = random.Random(SEED)

    def jac(p, q, r):
        return _vadd3(
            _commutator(_commutator(p, q), r),
            _commutator(_commutator(q, r), p),
            _commutator(_commutator(r, p), q),
        )

    assert _normsq(jac(_e(1), _e(2), _e(4))) > 1e-6  # nonzero => not Lie
    xs, ys, zs = (_standard_normal(rng, DIM) for _ in range(3))
    mal = _vsub(jac(xs, ys, loop_bind(xs, zs)),
                loop_bind(jac(xs, ys, zs), xs))
    assert _normsq(mal) < 1e-18


def test_inverse_unbinds_moufang_division():
    # loop_inv is the unbind key: x · x⁻¹ == x⁻¹ · x == e0 ; unit inv == conj
    rng = random.Random(SEED)
    x = _standard_normal(rng, DIM)
    assert mat_norm(_vsub(loop_bind(x, loop_inv(x)), _e(0))) < 1e-9
    assert mat_norm(_vsub(loop_bind(loop_inv(x), x), _e(0))) < 1e-9
    inv_norm = 1.0 / _normsq(x) ** 0.5
    u = [v * inv_norm for v in x]
    assert mat_norm(_vsub(loop_inv(u), loop_conj(u))) < 1e-9


def test_associator_zero_on_two_generator_subalgebra():
    # Artin: any two octonions generate an associative subalgebra, so the
    # associator of a, b, and their product vanishes.
    a, b = _e(1), _e(2)
    c = loop_bind(a, b)
    assert _normsq(loop_associator(a, b, c)) < 1e-12


def test_real_anchor_is_identity():
    # e0 is the loop identity (the real anchor binds as 1).
    rng = random.Random(SEED)
    x = _standard_normal(rng, DIM)
    assert mat_norm(_vsub(loop_bind(_e(0), x), x)) < 1e-9
    assert mat_norm(_vsub(loop_bind(x, _e(0)), x)) < 1e-9


def _mat_sub(a: Mat, b: Mat) -> Mat:
    ar, br = a.tolist(), b.tolist()
    return Mat.from_rows([[ar[i][j] - br[i][j] for j in range(len(ar[0]))]
                          for i in range(len(ar))])


def _vadd3(a, b, c):
    return [a[i] + b[i] + c[i] for i in range(len(a))]
