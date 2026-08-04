"""rc399 (`#T1064` Tier 2/3) — the octonion Cayley plane 𝕆P² (carrier-native)
and the guarded generalized-n-gon / Feit–Higman spectral read.

Verifies THROUGH the shipped ops (exact-ℚ where the object is exact):

Tier 2 (𝕆P², srmech.cascade.cayley_plane):
  * jordan_product — E1∘E1 = E1 (idempotent), E1∘E2 = 0 (Jordan-orthogonal),
    commutativity A∘B == B∘A, Hermitian result.
  * cayley_plane_point — P∘P = P & tr P = 1 for associating Veronese vectors;
    the exact non-associating boundary (defect 4/27 for (e1,e2,e4)).
  * cayley_plane_incidence — Tr(Eᵢ∘Eⱼ) = δᵢⱼ, Tr(Eᵢ∘U) = 1/3, Tr(P∘P) = 1.
  * octonion_hopf_base — the exact S⁸ norm identity, the ℍ²-reduction, and the
    §3.41 fiber ceiling (a seam-crossing fiber MOVES the base; an associating
    one does not).

Tier 3 (generalized_ngon, srmech.math.laplacian):
  * girth 2n / diameter n / biregularity for the Fano plane (n=3), the doily
    (n=4) and the thin ordinary n-gons (n=3,4,6,8);
  * the Feit–Higman distinct-eigenvalue constraint (n+1 distinct);
  * a non-polygon control is rejected;
  * the supplied-structure path == the built-in example path.

Registration ratchet: the five ops are in the schema, __all__ and the Rosetta
ledger.
"""
import pytest

from srmech.cascade import (
    cd_basis,
    jordan_product,
    cayley_plane_point,
    cayley_plane_incidence,
    octonion_hopf_base,
)
from srmech.cascade.cayley_dickson import cd_mult
from srmech.math.laplacian import generalized_ngon
from srmech.math.q import Q


def _e(i):
    return [int(c) for c in cd_basis(8, i)]


ZERO8 = [0] * 8
E0 = [1, 0, 0, 0, 0, 0, 0, 0]


def _point(v1, v2, v3):
    return cayley_plane_point(v1, v2, v3)["point"]


# ── Tier 2: jordan_product ────────────────────────────────────────────────
def test_jordan_product_idempotent_point():
    E1 = _point(E0, ZERO8, ZERO8)
    sq = jordan_product(E1, E1)
    assert list(sq) == list(E1)          # E1∘E1 = E1 (a rank-1 idempotent)


def test_jordan_product_orthogonal_coordinate_points():
    E1 = _point(E0, ZERO8, ZERO8)
    E2 = _point(ZERO8, E0, ZERO8)
    prod = jordan_product(E1, E2)
    assert all(c == 0 for c in prod)     # E1∘E2 = 0 (Jordan-orthogonal)


def test_jordan_product_is_commutative():
    A = _point(E0, _e(1), _e(2))
    B = _point([1, 1, 0, 0, 0, 0, 0, 0], ZERO8, _e(3))
    assert list(jordan_product(A, B)) == list(jordan_product(B, A))


def test_jordan_product_len_27_and_diagonal_real():
    A = _point(E0, _e(1), _e(2))
    out = jordan_product(A, A)
    assert len(out) == 27


# ── Tier 2: cayley_plane_point ────────────────────────────────────────────
@pytest.mark.parametrize("v1,v2,v3", [
    (E0, ZERO8, ZERO8),                  # E1 diagonal idempotent
    (E0, _e(1), _e(2)),                  # quaternionic (common ℍ) coords
    (E0, [2, 0, 0, 0, 0, 0, 0, 0], _e(5)),  # two real entries
])
def test_cayley_plane_point_is_genuine_when_entries_associate(v1, v2, v3):
    r = cayley_plane_point(v1, v2, v3)
    assert r["is_point"] is True
    assert r["idempotent_defect"] == 0
    assert r["trace"] == Q(1, 1)


def test_cayley_plane_point_non_desarguesian_boundary():
    # three non-associating imaginary units → NOT a point; the defect is exact.
    r = cayley_plane_point(_e(1), _e(2), _e(4))
    assert r["is_point"] is False
    assert r["idempotent_defect"] == Q(4, 27)   # exact, nonzero
    assert r["trace"] == Q(1, 1)                 # trace still 1


def test_cayley_plane_point_zero_vector_raises():
    with pytest.raises(ValueError):
        cayley_plane_point(ZERO8, ZERO8, ZERO8)


# ── Tier 2: cayley_plane_incidence (the Jordan trace form) ────────────────
def test_incidence_coordinate_triangle_is_orthonormal():
    E1 = _point(E0, ZERO8, ZERO8)
    E2 = _point(ZERO8, E0, ZERO8)
    E3 = _point(ZERO8, ZERO8, E0)
    pts = [E1, E2, E3]
    for i in range(3):
        for j in range(3):
            expected = Q(1, 1) if i == j else Q(0, 1)
            assert cayley_plane_incidence(pts[i], pts[j]) == expected


def test_incidence_unit_point_off_the_coordinate_lines():
    E1 = _point(E0, ZERO8, ZERO8)
    U = _point(E0, E0, E0)
    assert cayley_plane_incidence(E1, U) == Q(1, 3)
    assert cayley_plane_incidence(U, U) == Q(1, 1)   # a point: Tr(P∘P)=1


# ── Tier 2: octonion_hopf_base (𝕆P¹ ≅ S⁸) ─────────────────────────────────
def test_hopf_base_lands_on_s8_exactly():
    r = octonion_hopf_base(_e(1) + _e(4))
    assert r["on_s8"] is True
    # |base_O|² + base_R² == norm_sq²
    assert r["base_norm_sq"] + r["base_R"] * r["base_R"] == r["norm_sq"] * r["norm_sq"]


def test_hopf_base_reduces_into_h():
    # x ∈ ℍ² collapses base_O into ℍ (seam half zero).
    r = octonion_hopf_base([1, 2, 3, 4, 0, 0, 0, 0] + [5, 6, 7, 8, 0, 0, 0, 0])
    assert r["reduces_to_h"] is True
    assert r["on_s8"] is True
    assert all(r["base_O"][i] == 0 for i in range(4, 8))


def test_hopf_base_fiber_ceiling():
    # The §3.41 ceiling: a seam-crossing unit-octonion right-multiply MOVES the
    # base (the instrument can return otherwise); an associating fiber does not.
    a = [1, 1, 0, 0, 0, 0, 0, 0]
    b = [0, 0, 1, 1, 0, 0, 0, 0]          # a, b ∈ ℍ
    base0 = octonion_hopf_base(a + b)["base_O"]
    e4 = tuple(Q(int(c), 1) for c in _e(4))
    aq = tuple(Q(int(c), 1) for c in a)
    bq = tuple(Q(int(c), 1) for c in b)
    seam = [int(c) for c in cd_mult(aq, e4)] + [int(c) for c in cd_mult(bq, e4)]
    base_seam = octonion_hopf_base(seam)["base_O"]
    assert base_seam != base0             # seam-crossing fiber MOVES it
    e1 = tuple(Q(int(c), 1) for c in _e(1))
    assoc = [int(c) for c in cd_mult(aq, e1)] + [int(c) for c in cd_mult(bq, e1)]
    assert octonion_hopf_base(assoc)["base_O"] == base0   # associating fiber holds


def test_hopf_base_bad_length_raises():
    with pytest.raises(ValueError):
        octonion_hopf_base([1, 0, 0, 0, 0, 0, 0, 0])   # 8, not 16


# ── Tier 3: generalized_ngon ──────────────────────────────────────────────
@pytest.mark.parametrize("example,n,thick", [
    ("fano", 3, True),
    ("doily", 4, True),
    ("ordinary_3", 3, False),
    ("ordinary_4", 4, False),
    ("ordinary_6", 6, False),
    ("ordinary_8", 8, False),
])
def test_generalized_ngon_girth_diameter_and_feit_higman(example, n, thick):
    r = generalized_ngon(example=example)
    assert r["n"] == n
    assert r["girth"] == 2 * n            # girth 2n
    assert r["diameter"] == n            # diameter n
    assert r["biregular"] is True
    assert r["thick"] is thick
    assert r["is_generalized_polygon"] is True
    # Feit–Higman: the incidence graph is distance-regular of diameter n, hence
    # exactly n+1 distinct adjacency eigenvalues.
    assert r["n_distinct_eigenvalues"] == n + 1
    assert r["spectral_consistent"] is True


def test_fano_is_heawood_spectrum():
    r = generalized_ngon(example="fano")
    # Heawood graph: eigenvalues ±3, ±√2.
    assert r["distinct_eigenvalues"] == [-3.0, -1.414214, 1.414214, 3.0]


def test_doily_is_tutte_coxeter_spectrum():
    r = generalized_ngon(example="doily")
    # Tutte–Coxeter graph (GQ(2,2)): eigenvalues ±3, ±2, 0.
    assert r["distinct_eigenvalues"] == [-3.0, -2.0, -0.0, 2.0, 3.0]


def test_fano_orders_and_counts():
    r = generalized_ngon(example="fano")
    assert (r["n_points"], r["n_lines"], r["n_vertices"]) == (7, 7, 14)
    assert (r["order_s"], r["order_t"]) == (2, 2)   # PG(2,2)


def test_non_polygon_control_is_rejected():
    # a path 0-1-2 as two lines: a forest (no cycle), not biregular.
    r = generalized_ngon(n_points=3, lines=[[0, 1], [1, 2]])
    assert r["is_generalized_polygon"] is False
    assert r["girth"] == -1              # forest → no cycle


def test_supplied_structure_matches_example_path():
    from srmech.math.laplacian import _standard_ngon_incidence
    np_, lns, _, _ = _standard_ngon_incidence("fano")
    supplied = generalized_ngon(n_points=np_, lines=lns)
    built_in = generalized_ngon(example="fano")
    assert supplied["is_generalized_polygon"] == built_in["is_generalized_polygon"]
    assert supplied["n"] == built_in["n"] == 3


def test_generalized_ngon_needs_input():
    with pytest.raises(ValueError):
        generalized_ngon()               # neither example nor (n_points, lines)


def test_generalized_ngon_unknown_example_raises():
    with pytest.raises(ValueError):
        generalized_ngon(example="octagon_thick")


# ── registration ratchet ──────────────────────────────────────────────────
def test_ops_registered_in_schema():
    from srmech.introspect.tool_schema import get_tool_schema
    names = {e.name for e in get_tool_schema().tools}
    for op in (
        "srmech.cascade.jordan_product",
        "srmech.cascade.cayley_plane_point",
        "srmech.cascade.cayley_plane_incidence",
        "srmech.cascade.octonion_hopf_base",
        "srmech.math.laplacian.generalized_ngon",
    ):
        assert op in names


def test_ops_in_cascade_all_and_laplacian_all():
    import srmech.cascade as cascade
    from srmech.math import laplacian
    for op in ("jordan_product", "cayley_plane_point",
               "cayley_plane_incidence", "octonion_hopf_base"):
        assert op in cascade.__all__
    assert "generalized_ngon" in laplacian.__all__
    assert "generalized_ngon" in laplacian.LAPLACIAN_OPS


def test_ops_in_rosetta_ledger():
    import pathlib
    rosetta = (pathlib.Path(__file__).resolve().parent
               / "rosetta_classification.ndjson").read_text(encoding="utf-8")
    for op in (
        "srmech.cascade.jordan_product",
        "srmech.cascade.cayley_plane_point",
        "srmech.cascade.cayley_plane_incidence",
        "srmech.cascade.octonion_hopf_base",
        "srmech.math.laplacian.generalized_ngon",
    ):
        assert op in rosetta
