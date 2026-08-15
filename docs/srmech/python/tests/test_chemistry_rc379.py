"""rc379 (`#T1050`) — the ``srmech.chemistry`` domain.

Reaction networks as exact-integer linear algebra: ``balance_reaction`` (the
integer nullspace of the element×species matrix), ``conservation_laws`` (the
integer left-nullspace of the species×reaction stoichiometric matrix),
``deficiency`` (the Feinberg ``δ = n − ℓ − s``), and ``parse_formula`` (the
formula tokenizer with a C twin). This module pins the correctness against
TEXTBOOK oracle values, the element×species vs species×reaction convention (the
#1 correctness trap — both are exercised), the sign convention, the
unbalanceable / underdetermined / GCD-reduction edges, the formula-string vs
dict vs QMat input parity, and the C↔Python byte-parity of parse_formula
(native forced ON then OFF).

Numpy-ABSENT + fractions-free by construction: every carrier is ``Q`` / ``QMat``
/ plain ``int`` — no numpy, no stdlib ``fractions`` import anywhere.
"""
from __future__ import annotations

import pytest

from srmech import _native
from srmech.chemistry import (
    balance_reaction,
    conservation_laws,
    deficiency,
    parse_formula,
)
from srmech.chemistry import formula as _formula_mod
from srmech.math.q import Q
from srmech.math.qmat import QMat

from tests._native_gate import require_native


# ──────────────────────────────────────────────────────────────────────
# parse_formula — tokenizer semantics
# ──────────────────────────────────────────────────────────────────────

def test_parse_simple_and_implicit_counts():
    assert parse_formula("H2O") == {"H": 2, "O": 1}
    assert parse_formula("O2") == {"O": 2}
    assert parse_formula("NaCl") == {"Na": 1, "Cl": 1}


def test_parse_multi_letter_symbols():
    assert parse_formula("CaCO3") == {"Ca": 1, "C": 1, "O": 3}
    assert parse_formula("C12H22O11") == {"C": 12, "H": 22, "O": 11}


def test_parse_nested_parens_with_multipliers():
    assert parse_formula("Ca3(PO4)2") == {"Ca": 3, "P": 2, "O": 8}
    assert parse_formula("(OH)2") == {"O": 2, "H": 2}
    assert parse_formula("K4(ON(SO3)2)2") == {"K": 4, "O": 14, "N": 2, "S": 4}


def test_parse_repeated_element_accumulates():
    assert parse_formula("CH3CH2OH") == {"C": 2, "H": 6, "O": 1}


def test_parse_malformed_raises():
    with pytest.raises(ValueError):
        parse_formula("h2o")                 # lowercase start
    with pytest.raises(ValueError):
        parse_formula("Ca(PO4")              # unbalanced '('
    with pytest.raises(ValueError):
        parse_formula("PO4)2")               # unbalanced ')'
    with pytest.raises(ValueError):
        parse_formula("")                    # empty
    with pytest.raises(TypeError):
        parse_formula(123)                   # not a str


def test_parse_deferred_syntax_raises():
    for bad in ("CuSO4·5H2O", "Ca^2+", "Na+", "[13C]O2"):
        with pytest.raises(ValueError):
            parse_formula(bad)


# ──────────────────────────────────────────────────────────────────────
# parse_formula — C ↔ Python byte-parity (native forced ON, then OFF)
# ──────────────────────────────────────────────────────────────────────

def test_parse_native_is_actually_exercised():
    require_native("srmech_parse_formula")
    assert _native.has_native_parse_formula(), "C peer not bound"
    assert _formula_mod._parse_formula_c("Ca3(PO4)2") == {"Ca": 3, "P": 2, "O": 8}


def test_parse_native_matches_pure():
    require_native("srmech_parse_formula")
    cases = [
        "H2O", "O2", "NaCl", "CaCO3", "C12H22O11", "Ca3(PO4)2", "(OH)2",
        "K4(ON(SO3)2)2", "CH3CH2OH", "Fe2O3", "C6H12O6", "Mg", "Uuo",
    ]
    saved = _native.HAS_NATIVE
    try:
        for f in cases:
            _native.HAS_NATIVE = True
            native = parse_formula(f)
            _native.HAS_NATIVE = False
            pure = parse_formula(f)
            assert native == pure == _formula_mod._parse_formula_pure(f), f
    finally:
        _native.HAS_NATIVE = saved


# ──────────────────────────────────────────────────────────────────────
# balance_reaction — textbook oracles + sign convention
# ──────────────────────────────────────────────────────────────────────

def test_balance_water_synthesis():
    # 2 H2 + O2 -> 2 H2O ; H2O carries the opposite sign (product)
    assert balance_reaction(["H2", "O2", "H2O"]) == [2, 1, -2]


def test_balance_propane_combustion():
    # C3H8 + 5 O2 -> 3 CO2 + 4 H2O
    assert balance_reaction(["C3H8", "O2", "CO2", "H2O"]) == [1, 5, -3, -4]


def test_balance_ethane_combustion_needs_gcd_reduction():
    # 2 C2H6 + 7 O2 -> 4 CO2 + 6 H2O — the raw kernel column is halved to primitive
    assert balance_reaction(["C2H6", "O2", "CO2", "H2O"]) == [2, 7, -4, -6]


def test_balance_iron_oxide_redox():
    # 4 Fe + 3 O2 -> 2 Fe2O3
    assert balance_reaction(["Fe", "O2", "Fe2O3"]) == [4, 3, -2]


def test_balance_input_parity_string_dict_qmat():
    expect = [2, 1, -2]
    from_strings = balance_reaction(["H2", "O2", "H2O"])
    from_dicts = balance_reaction([{"H": 2}, {"O": 2}, {"H": 2, "O": 1}])
    # element×species QMat: rows = elements (H, O), cols = species (H2, O2, H2O)
    A = QMat([[Q(2), Q(0), Q(2)], [Q(0), Q(2), Q(1)]])
    from_qmat = balance_reaction(A)
    assert from_strings == from_dicts == from_qmat == expect


def test_balance_unbalanceable_raises():
    # a single species has full column rank -> trivial kernel -> unbalanceable
    with pytest.raises(ValueError):
        balance_reaction(["H2O"])
    with pytest.raises(ValueError):
        balance_reaction(["H2", "O2"])       # no shared way to cancel


def test_balance_underdetermined_returns_all_with_flag():
    # 5 species over 3 elements -> nullity >= 2 (multiple independent balances)
    species = ["CO", "CO2", "H2", "H2O", "CH4"]
    with pytest.raises(ValueError):
        balance_reaction(species)            # ambiguous by default
    all_b = balance_reaction(species, all_balances=True)
    assert len(all_b) >= 2
    # every returned balance actually conserves every element (A·v == 0)
    A = balance_reaction  # alias to keep the closure readable
    from srmech.chemistry.reactions import _element_species_matrix
    M = _element_species_matrix(species)
    for v in all_b:
        acc = [sum(int(M[i, j]) * v[j] for j in range(M.n_cols))
               for i in range(M.n_rows)]
        assert acc == [0] * M.n_rows


# ──────────────────────────────────────────────────────────────────────
# conservation_laws — species×reaction left-nullspace (NOT element×species!)
# ──────────────────────────────────────────────────────────────────────

def test_conservation_michaelis_menten():
    # E + S <-> ES -> E + P ; species rows E, S, ES, P ; reaction cols R1,R2,R3
    N = [[-1, 1, 1],
         [-1, 1, 0],
         [1, -1, -1],
         [0, 0, 1]]
    laws = conservation_laws(N)
    assert len(laws) == 2                     # two conserved moieties
    # each law satisfies gamma^T N == 0
    for g in laws:
        for j in range(3):
            assert sum(g[i] * N[i][j] for i in range(4)) == 0


def test_conservation_qmat_input_matches_list():
    N = [[-1, 1], [1, -1]]
    as_list = conservation_laws(N)
    as_qmat = conservation_laws(QMat([[Q(-1), Q(1)], [Q(1), Q(-1)]]))
    assert as_list == as_qmat
    # A ⇌ B conserves the total A + B
    assert as_list == [[1, 1]]


def test_conservation_full_rank_has_no_law():
    # a species×reaction matrix with full ROW rank has no conserved moiety
    N = [[1, 0], [0, 1]]
    assert conservation_laws(N) == []


# ──────────────────────────────────────────────────────────────────────
# deficiency — Feinberg δ = n − ℓ − s (documented δ=0 and δ=1 networks)
# ──────────────────────────────────────────────────────────────────────

def test_deficiency_isomerization_is_zero():
    # A ⇌ B : n=2 complexes, ℓ=1 linkage class, s=1 -> δ=0
    d = deficiency([({"A": 1}, {"B": 1})], with_components=True)
    assert d == {"deficiency": 0, "n_complexes": 2,
                 "n_linkage_classes": 1, "rank_stoichiometric": 1}


def test_deficiency_classic_delta_one():
    # 2A -> A+B -> 2B -> 2A : n=3, ℓ=1, s=1 -> δ=1 (a documented Feinberg δ=1)
    net = [({"A": 2}, {"A": 1, "B": 1}),
           ({"A": 1, "B": 1}, {"B": 2}),
           ({"B": 2}, {"A": 2})]
    assert deficiency(net) == 1
    comps = deficiency(net, with_components=True)
    assert comps == {"deficiency": 1, "n_complexes": 3,
                     "n_linkage_classes": 1, "rank_stoichiometric": 1}


def test_deficiency_zero_complex_birth_death():
    # ∅ -> A , A -> ∅ : complexes {∅, A}, n=2, ℓ=1, s=1 -> δ=0
    net = [("0", {"A": 1}), ({"A": 1}, "0")]
    assert deficiency(net) == 0


def test_deficiency_two_separate_isomerizations():
    # A⇌B and C⇌D : n=4 complexes, ℓ=2 linkage classes, s=2 -> δ=0
    net = [({"A": 1}, {"B": 1}), ({"C": 1}, {"D": 1})]
    comps = deficiency(net, with_components=True)
    assert comps["n_complexes"] == 4
    assert comps["n_linkage_classes"] == 2
    assert comps["rank_stoichiometric"] == 2
    assert comps["deficiency"] == 0


def test_deficiency_empty_raises():
    with pytest.raises(ValueError):
        deficiency([])


# ──────────────────────────────────────────────────────────────────────
# registration + describe count
# ──────────────────────────────────────────────────────────────────────

def test_ops_registered_in_tool_schema():
    from srmech.introspect.tool_schema import get_tool_schema
    names = {e.name for e in get_tool_schema().tools}
    for op in ("srmech.chemistry.balance_reaction",
               "srmech.chemistry.conservation_laws",
               "srmech.chemistry.deficiency",
               "srmech.chemistry.parse_formula"):
        assert op in names, op


def test_describe_total_is_535():
    import srmech
    assert srmech.describe()["tools"]["total"] == 656


# ──────────────────────────────────────────────────────────────────────
# MCP param-coercion round-trip (JSON example -> coercer -> op)
# ──────────────────────────────────────────────────────────────────────

def test_mcp_coercers_roundtrip_into_each_op():
    """The three math ops must be genuinely MCP/Anthropic-callable: a
    JSON-serializable payload for each param type coerces into the exact Python
    the op expects. Pins the coercer keys AND that the coerced value runs."""
    from srmech.mcp._coercion import coerce_param

    # balance_reaction `species`: a JSON list of formula strings
    sp = coerce_param(["H2", "O2", "H2O"], "Sequence[str | dict[str,int]] | QMat")
    assert balance_reaction(sp) == [2, 1, -2]

    # conservation_laws `N`: JSON nested ints, and [num, den] exact-Q pairs
    N = coerce_param([[-1, 1, 1], [-1, 1, 0], [1, -1, -1], [0, 0, 1]],
                     "QMat | Sequence[Sequence[int | Q]]")
    assert len(conservation_laws(N)) == 2
    Nq = coerce_param([[[1, 1], [-1, 1]], [[-1, 1], [1, 1]]],
                      "QMat | Sequence[Sequence[int | Q]]")
    assert conservation_laws(Nq) == [[1, 1]]

    # deficiency `reactions`: JSON [reactant, product] complex-dict pairs
    rx = coerce_param([[{"A": 2}, {"A": 1, "B": 1}],
                       [{"A": 1, "B": 1}, {"B": 2}],
                       [{"B": 2}, {"A": 2}]],
                      "Sequence[tuple[dict[str,int], dict[str,int]]]")
    assert deficiency(rx) == 1
