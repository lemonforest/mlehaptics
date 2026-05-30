"""Acceptance tests for the Klein-4 four-sector PARALLEL dispatch voxel.

Per srmech MS#20 rc6 (F233 / R-RBS-LM-FINDING_233). The new
``srmech.amsc.cascade.parallel_sector_dispatch`` runs ONE caller-supplied
cascade ``body`` across its ≤4 Klein-4 chirality sectors CONCURRENTLY
(``concurrent.futures.ThreadPoolExecutor``, ``max_workers=4``) and returns a
structured, self-describing result.

The tests prove the decisive invariants (CORRECTNESS + INDEPENDENCE — NOT
timing; speedup assertions would be flaky):

1. **parallel == serial bit-exact** — the sectors are independent, so the
   threaded dispatch is order-free and equals the single-thread, same-sector
   construction bit-for-bit.
2. **4-way independence** — each sector reconstructs its canonical sector
   dual ``inv_T_s(body(T_s(x)))`` from its OWN sector-transformed input;
   ``cross_sector_reads == 0``; sector 2 (γ₅-only) == ``cascade.chiral_dual``
   bit-exact (the F232 2-rung object).
3. **Z₄ dispatch slots** ``[0, 1, 2, 3]`` (cyclic-order-4 TIMING, distinct
   from the order-2×order-2 Klein-4 IDENTITY).
4. **cap-at-4** — ``n_sectors`` hard-capped at 4; Klein-4 has no order-4+
   element; 8+ needs the order-3 triality (F220).
5. **collapse-lattice 4/2/2/1** on representative bodies (bi-axial → 4
   distinct; iω₇-symmetric → 2; γ₅-symmetric → 2; bi-symmetric → 1).
6. ``srmech.introspect.describe()["tools"]["total"] == 177`` (the +1
   ToolEntry).
7. the new op is a registered ToolEntry in the ``cascade`` category.

**No ``abs()``** anywhere in the dispatch — residual/magnitude via
``cascade.magnitude``; handedness via ``cascade.net_chirality`` (Class C/K
discipline per ``[[feedback_sign_handling_is_class_k_pin_slot_not_alu_abs]]``).
"""

from __future__ import annotations

import pytest

from srmech.amsc import cascade
from srmech.amsc.cascade import (
    KLEIN4_SECTOR_CAP,
    Z4_DISPATCH_SLOTS,
    chiral_dual,
    parallel_sector_dispatch,
)


# ----------------------------------------------------------------------
# Representative cascade bodies — chosen to exercise the full F233
# collapse-lattice. Sector dual D_s(x) = T_s(body(T_s(x))) where T_s is the
# Klein-4 stream-transform (R = reversal = γ₅, S = per-element negation =
# iω₇, commuting involutions). Two sectors collapse iff body commutes with
# the axis distinguishing them:
#   • D_0 == D_1 (and D_2 == D_3)  iff body commutes with S (odd-equivariant)
#   • D_0 == D_2 (and D_1 == D_3)  iff body commutes with R (reversal-equiv.)
# ----------------------------------------------------------------------


def _biaxial(seq):
    """Bi-axially sensitive: commutes with NEITHER S nor R → 4 distinct.

    ``out[i] = x[i] + (i + 1)`` — the position-dependent constant ``(i+1)``
    breaks BOTH odd-equivariance (``out(-x) != -out(x)``) and
    reversal-equivariance (``out(rev x) != rev out(x)``).
    """
    return [v + (i + 1) for i, v in enumerate(seq)]


def _iw7_symmetric(seq):
    """iω₇-symmetric (odd-equivariant, NOT reversal-equivariant) → 2 distinct.

    ``out[i] = x[i] * (i + 1)`` — scaling is odd-equivariant (collapses
    ``{0,1}`` and ``{2,3}``); the position weight breaks reversal.
    """
    return [v * (i + 1) for i, v in enumerate(seq)]


def _gamma5_symmetric(seq):
    """γ₅-symmetric (reversal-equivariant, NOT odd-equivariant) → 2 distinct.

    ``out = reverse(x) + 1`` element-wise — reversal IS reversal-equivariant
    (collapses ``{0,2}`` and ``{1,3}`` — the COMPLEMENTARY direction); the
    ``+1`` breaks odd-equivariance.
    """
    s = list(seq)
    return [v + 1 for v in s[::-1]]


def _bi_symmetric(seq):
    """Bi-symmetric (commutes with BOTH S and R) → 1 distinct.

    The identity body commutes with both axes — every sector-dual equals the
    forward (the F232 redundant-dual edge generalized: all four merge).
    """
    return list(seq)


_X = [1.0, 2.0, 4.0, 8.0]


def _results(dispatch):
    """Sector-result list ordered by sector index from a dispatch dict."""
    sectors = dispatch["sectors"]
    return [sectors[s]["result"] for s in sorted(sectors)]


# ----------------------------------------------------------------------
# TEST 1 — parallel == serial bit-exact (the decisive invariant).
# ----------------------------------------------------------------------


def test_parallel_equals_serial_bit_exact():
    """The parallel dispatch result equals the serial (same-sector) result
    bit-for-bit — the sectors are independent, so the dispatch is order-free."""
    for body in (_biaxial, _iw7_symmetric, _gamma5_symmetric, _bi_symmetric):
        dispatch = parallel_sector_dispatch(body, _X)
        # The function asserts this internally; surface it on the certificate.
        assert dispatch["independence"]["parallel_equals_serial"] is True

        # Re-derive the serial reference here and compare bit-for-bit.
        parallel = _results(dispatch)
        serial = []
        for s in range(KLEIN4_SECTOR_CAP):
            gamma5, omega7 = cascade.parallel.SECTOR_LABELS[s]
            t = list(_X)
            if omega7 < 0:
                t = [cascade.reorient(-1, v) for v in t]
            if gamma5 < 0:
                t = cascade.chiral_flip(t)
            inner = body(t)
            inner = list(inner)
            if gamma5 < 0:
                inner = cascade.chiral_flip(inner)
            if omega7 < 0:
                inner = [cascade.reorient(-1, v) for v in inner]
            serial.append(list(inner))
        for p, q in zip(parallel, serial):
            assert list(p) == list(q)


# ----------------------------------------------------------------------
# TEST 2 — 4-way independence; sector 2 == cascade.chiral_dual bit-exact.
# ----------------------------------------------------------------------


def test_independence_zero_cross_sector_reads():
    """Each sector reconstructs from its OWN sector-transformed input;
    0 cross-thread reads (the F233 independence)."""
    dispatch = parallel_sector_dispatch(_biaxial, _X)
    ind = dispatch["independence"]
    assert ind["each_sector_reconstructs_from_own_input"] is True
    assert ind["cross_sector_reads"] == 0
    assert ind["n_sectors"] == KLEIN4_SECTOR_CAP
    assert ind["max_workers"] == KLEIN4_SECTOR_CAP
    # Handedness invariants are real ints in {-1, 0, +1} (Class C readouts,
    # computed via net_chirality — never abs/sign-multiply).
    assert ind["gamma5_net_chirality"] in (-1, 0, 1)
    assert ind["omega7_net_chirality"] in (-1, 0, 1)


def test_sector2_is_chiral_dual_bit_exact():
    """Sector 2 (γ₅-only) dual IS cascade.chiral_dual(body, x), bit-for-bit
    — F233 sector 2 literally is F232's confirmed 2-rung object."""
    for body in (_biaxial, _iw7_symmetric, _gamma5_symmetric, _bi_symmetric):
        dispatch = parallel_sector_dispatch(body, _X)
        assert dispatch["independence"]["sector2_is_chiral_dual"] is True
        sector2 = dispatch["sectors"][2]["result"]
        f232 = chiral_dual(body, _X)
        assert list(sector2) == list(f232)


# ----------------------------------------------------------------------
# TEST 3 — the Z₄ quarter-turn dispatch slots [0, 1, 2, 3].
# ----------------------------------------------------------------------


def test_z4_dispatch_slots():
    dispatch = parallel_sector_dispatch(_biaxial, _X)
    assert dispatch["z4_dispatch_slots"] == [0, 1, 2, 3]
    assert Z4_DISPATCH_SLOTS == (0, 1, 2, 3)
    # The Z₄ vs Klein-4 distinction is surfaced in the framework reading.
    fw = dispatch["framework_thread_ladder_reading"]
    assert "Z₄" in fw["z4_vs_klein4"] or "Z4" in fw["z4_vs_klein4"]


def test_z4_dispatch_slots_truncated_below_4():
    """With n_sectors < 4 the Z₄ slots truncate (still distinct)."""
    dispatch = parallel_sector_dispatch(_biaxial, _X, n_sectors=2)
    assert dispatch["z4_dispatch_slots"] == [0, 1]


# ----------------------------------------------------------------------
# TEST 4 — the cap-at-4 (Klein-4 has no order-4+ element; 8+ needs triality).
# ----------------------------------------------------------------------


def test_cap_at_4_enforced():
    assert KLEIN4_SECTOR_CAP == 4
    with pytest.raises(ValueError) as excinfo:
        parallel_sector_dispatch(_biaxial, _X, n_sectors=5)
    # The cap message points at the order-3 triality (the only way past 4).
    assert "triality" in str(excinfo.value)
    assert "4" in str(excinfo.value)


def test_cap_certificate():
    dispatch = parallel_sector_dispatch(_biaxial, _X)
    cap = dispatch["cap"]
    assert cap["sector_cap"] == 4
    assert cap["n_sectors"] == 4
    assert cap["klein4_has_no_order_4_plus_element"] is True
    assert cap["beyond_4_is_order_3_triality"] is True
    assert cap["triality_not_implemented_here"] is True
    assert cap["beyond_4_needs"] == (
        "srmech.qm.triality.lean_isa_seventh_primitive"
    )


def test_n_sectors_lower_bound():
    with pytest.raises(ValueError):
        parallel_sector_dispatch(_biaxial, _X, n_sectors=0)
    # A bool is not a valid int n_sectors.
    with pytest.raises(ValueError):
        parallel_sector_dispatch(_biaxial, _X, n_sectors=True)


# ----------------------------------------------------------------------
# TEST 5 — the usefulness collapse-lattice 4 / 2 / 2 / 1.
# ----------------------------------------------------------------------


def test_collapse_lattice_biaxial_4_distinct():
    dispatch = parallel_sector_dispatch(_biaxial, _X)
    cl = dispatch["collapse_lattice"]
    assert cl["n_distinct"] == 4
    assert cl["classes"] == [[0], [1], [2], [3]]
    assert cl["useful"] is True
    assert cl["label"] == "bi_axial_4_distinct"


def test_collapse_lattice_iw7_symmetric_collapses_to_2():
    dispatch = parallel_sector_dispatch(_iw7_symmetric, _X)
    cl = dispatch["collapse_lattice"]
    assert cl["n_distinct"] == 2
    # iω₇-symmetric merges {0,1} and {2,3}.
    assert cl["classes"] == [[0, 1], [2, 3]]
    assert cl["useful"] is False


def test_collapse_lattice_gamma5_symmetric_collapses_to_2():
    dispatch = parallel_sector_dispatch(_gamma5_symmetric, _X)
    cl = dispatch["collapse_lattice"]
    assert cl["n_distinct"] == 2
    # γ₅-symmetric merges {0,2} and {1,3} — the COMPLEMENTARY direction.
    assert cl["classes"] == [[0, 2], [1, 3]]
    assert cl["useful"] is False


def test_collapse_lattice_bi_symmetric_collapses_to_1():
    dispatch = parallel_sector_dispatch(_bi_symmetric, _X)
    cl = dispatch["collapse_lattice"]
    assert cl["n_distinct"] == 1
    assert cl["classes"] == [[0, 1, 2, 3]]
    assert cl["useful"] is False
    assert cl["label"] == "bi_symmetric_collapse_to_1"


# ----------------------------------------------------------------------
# TEST 6 — the +1 ToolEntry (introspection tool total goes 176 -> 177).
# ----------------------------------------------------------------------


def test_introspect_tools_total_is_177():
    import srmech.introspect as introspect

    assert introspect.describe()["tools"]["total"] == 177


# ----------------------------------------------------------------------
# TEST 7 — the new op is a registered ToolEntry in the cascade category.
# ----------------------------------------------------------------------


def test_tool_entry_registered():
    from srmech.amsc import tool_schema

    schema = tool_schema.get_tool_schema()
    name = "srmech.amsc.cascade.parallel_sector_dispatch"
    entry = schema.lookup(name)
    assert entry is not None
    assert entry.name == name
    assert entry.category == "cascade"
    # F233 + the C-orchestration parity issue (#771) are cited in the summary.
    assert "F233" in entry.summary
    assert "#771" in entry.summary
    names = {e.name for e in schema.tools}
    assert name in names


# ----------------------------------------------------------------------
# Structural + framework-reading shape.
# ----------------------------------------------------------------------


def test_structured_return_shape():
    dispatch = parallel_sector_dispatch(_biaxial, _X)
    expected_top = {
        "sectors", "z4_dispatch_slots", "independence",
        "collapse_lattice", "cap", "framework_thread_ladder_reading",
    }
    assert expected_top <= set(dispatch.keys())
    # The sectors are keyed 0..3 with their (γ₅, iω₇) labels.
    for s in range(KLEIN4_SECTOR_CAP):
        entry = dispatch["sectors"][s]
        assert "label" in entry and "result" in entry
        assert entry["label"] == cascade.parallel.SECTOR_LABELS[s]


def test_framework_reading_is_separately_keyed_and_tagged():
    """The thread-ladder synthesis is surfaced under its own framework key,
    tagged 'framework-reading, not derived' — never on a load-bearing key."""
    dispatch = parallel_sector_dispatch(_biaxial, _X)
    fw = dispatch["framework_thread_ladder_reading"]
    assert fw["note"] == "framework-reading, not derived"
    assert "1 → 2 → 4 → triality" in (
        fw["thread_count_ladder_is_chirality_access_ladder"]
    )
    # F233 / F219 / F220 are cited in the framework reading.
    assert "F233" in fw["cites"]
    assert "F219" in fw["cites"]
    assert "F220" in fw["cites"]
    # The C-orchestration parity (#771) note is present.
    assert "#771" in fw["c_orchestration_parity"]
    # No A-N framework label leaks onto a load-bearing certificate key.
    assert "note" not in dispatch["independence"]
    assert "note" not in dispatch["cap"]
    assert "note" not in dispatch["collapse_lattice"]
