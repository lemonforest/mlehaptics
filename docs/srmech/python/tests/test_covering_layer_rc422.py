"""rc422 (`#T1123`) — the CENTRE / COVERING layer + the Z(Spin(8)) anchor.

WHAT THIS GATE IS FOR
=====================
rc421 measured the V₄ ↔ so(8) bridge **NOT canonical as shipped**, residual
ambiguity **3**, and named the blocker precisely: no shipped op carried the
rep-LABELING, so `center_or_kernel_ops` was `[]`. rc422 builds that anchor. The
assertions below are the ones that would go red if the dictionary had been
CHOSEN rather than DERIVED, which is the whole content of the standing
falsifier — *a bridge requiring an arbitrary choice is an isomorphism, not a
link*.

THE TRAP, GATED SO NOBODY RE-WALKS IT
=====================================
"Compute the centre of so(8)" returns the ZERO object and that is CORRECT: so(8)
is semisimple. The Klein four-group is Z(Spin(8)), a property of the
simply-connected GROUP — global (π₁) data where an algebra carries local data.
`test_the_algebra_centre_is_zero_and_that_is_the_setup_not_a_refutation` pins
that zero as an EXPECTED value so a future reader meeting it does not read a
refutation into it.

THE ANTI-PICK CONTROL IS THE LOAD-BEARING TEST
==============================================
`test_the_label_action_is_read_off_the_matrices_not_asserted` recomputes the
label actions of the shipped 28×28 τ and S_B by **exact characteristic
polynomial**, WITHOUT using how those matrices were constructed. The shipped
`_TAU_LABEL_ACTION` / `_SWAP_LABEL_ACTION` are stated definitionally (S_B is by
construction the map to the 8s companion); this test is the independent second
construction that turns a definitional statement into a checked one — a
consistency oracle, so a DISAGREEMENT would be the finding
(``[[user_stance_co_equal_dual_construction_is_a_consistency_oracle]]``). It is
the slowest test here (~45 s: it forces the cached 28-generator companion
solve) and it is the one worth keeping.

numpy-free; no stdlib math / fractions / decimal; no ``abs()``.
"""
from __future__ import annotations

import pytest

from srmech.introspect.tool_schema import get_tool_schema
from srmech.math.covering import (
    UNIVERSAL,
    center_lift,
    center_parity,
    covering_catalog,
    lift_fibre,
    linking_number_cwf,
)
from srmech.math.q import Q
from srmech.physics.qm.triality import (
    _SWAP_LABEL_ACTION,
    _TAU_LABEL_ACTION,
    spin8_center,
    triality_rep_dictionary,
)

_FRAMES = ("v", "s", "c")


# ══════════════════════════════════════════════════════════════════════
# 1. Z(Spin(8)) — the anchor rc421 measured absent
# ══════════════════════════════════════════════════════════════════════

def test_the_centre_is_a_klein_four_group_solved_not_asserted() -> None:
    """Four scalar triples, closed, all involutions — SOLVED off the table."""
    c = spin8_center()
    assert c["order"] == 4, c["elements"]
    assert c["is_klein_four"], c
    assert c["basis_pairs_checked"] == 64
    assert sorted(c["elements"]) == sorted(
        [(-1, -1, 1), (-1, 1, -1), (1, -1, -1), (1, 1, 1)]), c["elements"]


def test_the_algebra_centre_is_zero_and_that_is_the_setup_not_a_refutation() -> None:
    """so(8) is semisimple, so its LIE-ALGEBRA centre is 0.

    Pinned as an EXPECTED value. The Klein four-group belongs to the
    simply-connected GROUP; the same algebra is shared by Spin(8), SO(8) and
    PSO(8) and structurally cannot distinguish them, because a centre is global
    (π₁) data. A run reporting zero here has confirmed the setup.
    """
    assert spin8_center()["algebra_centre_dim"] == 0


def test_each_central_involution_kills_exactly_one_rep() -> None:
    """The kernels ARE the dictionary — forced, not chosen.

    Each non-identity element has exactly one ``+1`` coordinate, so the map
    {3 involutions} → {3 reps} is a bijection by structure.
    """
    k = spin8_center()["rep_kernels"]
    assert set(k) == set(_FRAMES), k
    assert len({tuple(v) for v in k.values()}) == 3, k
    for frame, triple in k.items():
        trivial = [f for f, eps in zip(_FRAMES, triple) if eps == 1]
        assert trivial == [frame], (frame, triple)


def test_the_triality_fixed_subgroup_of_the_centre_is_trivial() -> None:
    """The MEASURED basis for the ``g2_der_octonions`` rejection row.

    τ permutes the three non-identity central elements exactly as it permutes
    the three reps, so nothing but the identity survives — g₂ = Fix(τ) inherits
    no centre to carry. This is the rejection that shows the covering
    predicate discriminates rather than accepting whatever it is handed.
    """
    fixed = spin8_center()["triality_fixed_subgroup"]
    assert fixed == [(1, 1, 1)], fixed


# ══════════════════════════════════════════════════════════════════════
# 2. The dictionary — 3 → 1, and the controls that make the 1 mean something
# ══════════════════════════════════════════════════════════════════════

def test_the_residual_ambiguity_went_three_to_one() -> None:
    d = triality_rep_dictionary()
    assert d["prior_ambiguity"] == 3
    assert len(d["order3_only_survivors"]) == 3, d["order3_only_survivors"]
    assert d["residual_ambiguity"] == 1, d["order3_plus_order2_survivors"] \
        if "order3_plus_order2_survivors" in d else d
    assert d["dictionary"] == {"iomega7": "s", "gamma5": "c", "cpt": "v"}, \
        d["dictionary"]


def test_the_derived_dictionary_intertwines_BOTH_shipped_generators() -> None:
    """The property that makes it an intertwiner rather than a table.

    Checked directly against both generator pairs rather than trusting the
    census that produced it.
    """
    d = triality_rep_dictionary()
    dic = d["dictionary"]
    v4_cycle, v4_rung = d["v4_cycle"], d["v4_rung_transposition"]
    for k in ("iomega7", "gamma5", "cpt"):
        assert dic[v4_cycle[k]] == _TAU_LABEL_ACTION[dic[k]], (k, dic)
        assert dic[v4_rung[k]] == _SWAP_LABEL_ACTION[dic[k]], (k, dic)


def test_the_negative_controls_behave() -> None:
    """§3.29.3's named 'single most common triality error' must return 0.

    Using an order-2 object where the order-3 element is meant must admit NO
    bijection, from either side; and a vacuous (identity) constraint must leave
    all 6, which is what proves the order-3 cut to 3 was a real cut and not an
    artefact of how the census enumerates.
    """
    ctl = triality_rep_dictionary()["controls"]
    assert ctl["order2_for_order3_v4_side"] == 0, ctl
    assert ctl["order2_for_order3_so8_side"] == 0, ctl
    assert ctl["identity_for_cycle"] == 6, ctl
    assert ctl["behave"] is True, ctl


def test_the_swap_fixes_exactly_one_rep_and_tau_fixes_none() -> None:
    assert [k for k, v in _SWAP_LABEL_ACTION.items() if k == v] == ["c"]
    assert not [k for k, v in _TAU_LABEL_ACTION.items() if k == v]
    # order: τ³ = id, S_B² = id, as label permutations.
    tau2 = {k: _TAU_LABEL_ACTION[_TAU_LABEL_ACTION[k]] for k in _FRAMES}
    assert {k: _TAU_LABEL_ACTION[tau2[k]] for k in _FRAMES} == \
        {k: k for k in _FRAMES}
    assert {k: _SWAP_LABEL_ACTION[_SWAP_LABEL_ACTION[k]] for k in _FRAMES} == \
        {k: k for k in _FRAMES}


def test_the_label_action_is_read_off_the_matrices_not_asserted() -> None:
    """THE ANTI-PICK CONTROL — the co-equal second construction.

    Recompute the label actions of the shipped 28×28 ``τ`` and ``S_B`` by exact
    characteristic polynomial over three Cartan probes, using ONLY the matrices'
    values and never their construction. The shipped constants are stated
    definitionally; if the two routes disagreed, the DISAGREEMENT would be the
    finding, not a tolerance to widen.

    ~45 s — it forces the cached 28-generator companion solve.
    """
    from srmech.physics.qm.so8 import _epq_basis, _epq_pairs
    from srmech.physics.qm.triality import (
        triality_automorphism,
        triality_companions,
        triality_swap,
    )

    pairs = _epq_pairs()
    scale = 2

    def to_int(rows):
        out = []
        for r in rows:
            row = []
            for x in r:
                v = float(x) * scale
                iv = int(round(v))
                assert v - iv == 0.0, (x, "non-integral at scale 2")
                row.append(iv)
            out.append(row)
        return out

    basis = [to_int(m) for m in _epq_basis()]
    rho = {"v": [], "s": [], "c": []}
    for m in _epq_basis():
        gs, gc = triality_companions(m)
        rho["v"].append(to_int(m))
        rho["s"].append(to_int(gs.tolist()))
        rho["c"].append(to_int(gc.tolist()))

    def lincomb(coeffs, mats):
        n = len(mats[0])
        out = [[0] * n for _ in range(n)]
        for c, mm in zip(coeffs, mats):
            if not c:
                continue
            for i in range(n):
                ri, mi = out[i], mm[i]
                for j in range(n):
                    if mi[j]:
                        ri[j] += c * mi[j]
        return out

    def charpoly(m, denom):
        """Faddeev–LeVerrier over exact ℚ — a conjugation invariant."""
        n = len(m)
        a = [[Q(m[i][j], denom) for j in range(n)] for i in range(n)]
        zero, one = Q(0), Q(1)
        acc = [[zero] * n for _ in range(n)]
        coeffs = [one]
        for k in range(1, n + 1):
            acc = [[sum((a[i][t] * acc[t][j] for t in range(n)), zero)
                    for j in range(n)] for i in range(n)]
            for i in range(n):
                acc[i][i] = acc[i][i] + coeffs[-1]
            tr = zero
            for i in range(n):
                tr = tr + sum((a[i][t] * acc[t][i] for t in range(n)), zero)
            coeffs.append(zero - tr / Q(k))
        return tuple(str(c) for c in coeffs)

    def probe(terms):
        out = [0] * 28
        for (p, q), val in terms:
            out[pairs.index((p, q))] = val
        return out

    probes = [probe([((0, 1), 1), ((2, 3), 2), ((4, 5), 4), ((6, 7), 8)]),
              probe([((0, 1), 3), ((2, 3), 5), ((4, 5), 7), ((6, 7), 11)]),
              probe([((0, 1), 1), ((2, 3), -2), ((4, 5), 5), ((6, 7), 9)])]

    # The three reps must be pairwise INEQUIVALENT, else "which rep" is empty.
    base = {f: [charpoly(lincomb(pr, rho[f]), scale) for pr in probes]
            for f in _FRAMES}
    assert len({tuple(base[f]) for f in _FRAMES}) == 3, \
        "the three 8-dim reps are not separated by the probes"

    def read(phi28):
        perm = {}
        for f in _FRAMES:
            hits = None
            for i, pr in enumerate(probes):
                moved = [sum(phi28[r][j] * pr[j] for j in range(28))
                         for r in range(28)]
                got = charpoly(lincomb(moved, rho[f]), scale * scale)
                match = {g for g in _FRAMES if base[g][i] == got}
                hits = match if hits is None else (hits & match)
            assert len(hits) == 1, (f, sorted(hits))
            perm[f] = hits.pop()
        return perm

    assert read(to_int(triality_automorphism().tolist())) == _TAU_LABEL_ACTION
    assert read(to_int(triality_swap().tolist())) == _SWAP_LABEL_ACTION


# ══════════════════════════════════════════════════════════════════════
# 3. The general covering layer
# ══════════════════════════════════════════════════════════════════════

def test_center_parity_is_the_double_cover_bit() -> None:
    assert center_parity(0) == 1
    assert center_parity(1) == -1
    assert center_parity(2) == 1
    # orientation-blind: (-1)^w == (-1)^(-w), so no special case is needed.
    for w in range(-25, 26):
        assert center_parity(w) == center_parity(-w)
        assert center_parity(w) == (1 if w % 2 == 0 else -1)


def test_center_lift_keeps_the_integer_the_shadow_reduces_away() -> None:
    """The `#T1005` property: the cover datum survives the projection."""
    steps = [1, 1, 1, -3, 5]   # sums to 5 in the cover
    for order in (UNIVERSAL, 2, 3, 7):
        r = center_lift(steps, order)
        assert r["cover_lift"] == 5, r
        assert r["center_order"] == order
        assert r["shadow_determines_lift"] is (order == UNIVERSAL)
    assert center_lift(steps, 2)["center_shadow"] == 1
    assert center_lift(steps, 3)["center_shadow"] == 2
    assert center_lift(steps, UNIVERSAL)["center_shadow"] == 5


def test_the_signed_reduction_matches_the_mathematical_residue() -> None:
    """The Class-K/Class-C composition must agree with the true residue.

    ``mod_add`` serves the unsigned domain, so a negative lift routes through
    a pin-slot magnitude plus an orientation re-application on the cyclic
    carrier. That composition is only honest if it lands on the right value.
    """
    for order in (2, 3, 4, 5, 7, 12):
        for k in range(-40, 41):
            got = center_lift([k], order)["center_shadow"]
            assert got == k % order, (k, order, got)


def test_lift_fibre_can_report_BOTH_ways() -> None:
    """An instrument that could only ever report loss would not measure it."""
    lost = lift_fibre(1, 2, 4)
    assert lost["fibre"] == [-3, -1, 1, 3]
    assert lost["determined"] is False
    kept = lift_fibre(3, UNIVERSAL, 5)
    assert kept["fibre"] == [3]
    assert kept["determined"] is True
    # every enumerated lift really does carry the shadow
    for order in (2, 3, 5):
        for shadow in range(order):
            f = lift_fibre(shadow, order, 12)
            assert f["fibre"], (order, shadow)
            assert all(k % order == shadow for k in f["fibre"]), f


def test_linking_number_cwf_certifies_integrality_rather_than_rounding() -> None:
    r = linking_number_cwf((3, 2), (5, 2))
    assert r["lk"] == (4, 1) and r["is_integer"] is True
    assert r["linking_number"] == 4 and r["center_parity"] == 1
    bad = linking_number_cwf((7, 3), (1, 3))
    assert bad["lk"] == (8, 3) and bad["is_integer"] is False
    assert bad["linking_number"] is None and bad["center_parity"] is None
    # the frame-relative halves are preserved verbatim; only the sum is claimed
    assert bad["twist"] == (7, 3) and bad["writhe"] == (1, 3)


@pytest.mark.parametrize("bad", [((1, 0), (1, 1)), ((1.5, 1), (1, 1)),
                                 ((1,), (1, 1)), ((1, 1), "nope")])
def test_linking_number_cwf_rejects_a_non_class_n_input(bad) -> None:
    with pytest.raises(ValueError):
        linking_number_cwf(*bad)


@pytest.mark.parametrize("bad", [-1, -7])
def test_a_negative_center_order_is_rejected(bad) -> None:
    with pytest.raises(ValueError):
        center_lift([1], bad)
    with pytest.raises(ValueError):
        lift_fibre(0, bad, 3)


# ══════════════════════════════════════════════════════════════════════
# 4. The census — the rows cannot outlive the ops they name
# ══════════════════════════════════════════════════════════════════════

def test_every_reached_row_names_live_registered_ops() -> None:
    """A catalog row that outlived its op would be a silent falsehood.

    Resolved against the live registry, with ``One.spinor_sign`` handled as the
    method it is (it is a carrier method, not a registry row) — named
    explicitly rather than filtered by a pattern, so a typo cannot slip through
    as an exemption.
    """
    registered = {e.name for e in get_tool_schema().tools}
    method_rows = {"srmech.cascade.one.One.spinor_sign"}
    missing = []
    for row in covering_catalog()["reached"]:
        for op in row["shipped_ops"]:
            if op in method_rows:
                from srmech.cascade.one import One
                assert hasattr(One, "spinor_sign"), op
                continue
            if op not in registered:
                missing.append((row["name"], op))
    assert not missing, missing


def test_the_census_rejects_as_well_as_accepts() -> None:
    """A census that accepts everything is not a census."""
    cat = covering_catalog()
    assert cat["n_reached"] == 4, [r["name"] for r in cat["reached"]]
    assert cat["n_rejected"] == 5, [r["name"] for r in cat["rejected"]]
    assert cat["n_rejected"] >= cat["n_reached"]
    for row in cat["rejected"]:
        assert row["fails_clause"] in ("(i)", "(ii)", "(iii)"), row
        assert len(row["reason"]) > 80, row["name"]


def test_the_catalog_is_a_computation_not_a_table() -> None:
    """The two most-disbelievable fields are recomputed per call.

    If these were literals the row could drift from the op it describes; they
    are read from :func:`spin8_center` on every call instead.
    """
    cat = covering_catalog()
    centre = spin8_center()
    spin8 = next(r for r in cat["reached"] if r["name"] == "spin8")
    assert spin8["center_order"] == centre["order"] == 4
    assert spin8["rep_kernels"] == centre["rep_kernels"]
    g2 = next(r for r in cat["rejected"] if r["name"] == "g2_der_octonions")
    assert g2["measured_fixed_subgroup"] == [(1, 1, 1)]
    assert g2["measured_center_is_trivial"] is True


def test_the_universal_cover_row_is_the_only_infinite_centre() -> None:
    """``center_order == 0`` is the ℤ sentinel, and only ``circle_z`` carries
    an integer invariant — the row where the lost datum was never a bit."""
    rows = {r["name"]: r for r in covering_catalog()["reached"]}
    assert rows["circle_z"]["center_order"] == UNIVERSAL
    assert rows["circle_z"]["integer_invariant"] is not None
    for name in ("spin8", "spin3", "q8_v4"):
        assert rows[name]["center_order"] > 0, name
        assert rows[name]["integer_invariant"] is None, name


# ══════════════════════════════════════════════════════════════════════
# 5. Part 3 — the shipped-prose correctness fix
# ══════════════════════════════════════════════════════════════════════

def test_the_klein4_docstring_no_longer_asserts_the_wrong_dictionary() -> None:
    """`klein4_triality_cycle` used to open with a sentence that reads as
    ``iω₇↔8v, γ₅↔8s, CPT↔8c`` — a specific correspondence, asserted while none
    was pinned, and NOT the one that holds. The fix must name the derived
    dictionary and point at the op that derives it.
    """
    from srmech.math.hdc import klein4_triality_cycle
    doc = klein4_triality_cycle.__doc__ or ""
    assert "triality_rep_dictionary" in doc, \
        "the corrected docstring must cite the deriving op"
    assert "iω₇ ↔ 8s" in doc and "γ₅ ↔ 8c" in doc and "CPT ↔ 8v" in doc, \
        "the corrected docstring must state the DERIVED dictionary"
    assert not doc.lstrip().startswith(
        "Cycle the three Klein-4 chirality involutions — the order-3 S₃ "
        "generator.\n\n    The V₄-carrier image"), \
        "the retracted opening sentence is back"
