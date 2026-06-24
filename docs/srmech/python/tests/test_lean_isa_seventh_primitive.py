"""Bit-exact acceptance tests for the lean-ISA seventh-primitive voxel.

Per issue #761 (srmech MS#20 / F220 / R-RBS-LM-FINDING_220). The new
``srmech.qm.triality.lean_isa_seventh_primitive`` presents the order-3
**triality** operator as the 7th lean-ISA primitive — making the
chirality-complete A-N core explicit: **6 order-2 cascade.atoms + 1 order-3
triality = 7**, the only access to the 3rd chiral axis.

The tests prove the certificate:

1. the 6 order-2 atoms are named + reference ``srmech.amsc.cascade.atoms``.
2. the order-3 7th primitive is the triality automorphism, with the order
   of ``τ`` EXACTLY 3 BIT-EXACT (``‖τ³ − I‖ ≈ 0``, ``τ ≠ I``, ``τ² ≠ I``).
3. the F220 ``|G| = 8`` / no-order-3 / Lagrange (``3 ∤ 8``) certificate +
   the chirality-complete-7.
4. the MPR self-attestation block is present + well-formed.
5. the separately-keyed ``framework_chirality_complete_reading`` is present,
   tagged "framework-reading, not derived", and is NOT in any load-bearing
   certificate key.
6. ``srmech.introspect.describe()["tools"]["total"] == 177`` (the running
   total after the rc6 parallel_sector_dispatch +1 ToolEntry).

ALL deviations are reduced through the **scalar** Class K pin-slot magnitude
(:func:`srmech.amsc.cascade.magnitude`) — NEVER Python ``abs()`` per
``[[feedback_sign_handling_is_class_k_pin_slot_not_alu_abs]]``.

HONESTY SPLIT (mirrors the so8 ``an_embedding`` discipline): the order of
``τ`` (= 3) and the Lagrange arithmetic (``3 ∤ 8``) are BIT-EXACT
self-computed; that the 6 atoms generate EXACTLY ``Z2 × Z2 × Z2`` of order 8
is a documented framework-reading (surfaced only under the framework field),
NOT labelled bit-exact derived.

rc123 (numpy-free, #564): this test is itself numpy-FREE —
``lean_isa_seventh_primitive``'s ``triality`` is a :class:`srmech.amsc.mat.Mat`;
matmuls / norms route through ``mat_matmul`` / ``mat_norm`` with no numpy
oracle and no ``.to_numpy()`` (per
``[[feedback_test_for_numpy_free_module_must_itself_be_numpy_free]]``).
"""

from __future__ import annotations

from srmech.amsc.cascade import magnitude
from srmech.amsc.laplacian import mat_matmul, mat_norm
from srmech.amsc.mat import Mat
from srmech.qm import triality
from srmech.qm.triality import lean_isa_seventh_primitive

_TOL = 1e-9
_BIT_EXACT = 1e-10

#: The 6 order-2 lean-ISA atoms (the cascade.atoms intrinsics).
_EXPECTED_ATOMS = (
    "pin_slot_at_zero",
    "reorient",
    "magnitude",
    "chiral_flip",
    "chiral_dual",
    "net_chirality",
)


def _eye(n: int) -> Mat:
    return Mat.from_rows([[1.0 if i == j else 0.0 for j in range(n)]
                          for i in range(n)])


def _sub(a: Mat, b: Mat) -> Mat:
    ar, br = a.tolist(), b.tolist()
    return Mat.from_rows([[ar[i][j] - br[i][j] for j in range(len(ar[0]))]
                          for i in range(len(ar))])


def _frob(matrix: Mat) -> float:
    """Frobenius-norm deviation reduced through the scalar Class K magnitude.

    Reduce to a SCALAR float FIRST (the numpy-free Class-N ``mat_norm`` is the
    Frobenius norm), then pass that scalar to ``cascade.magnitude``
    (scalar-only; it raises on an array). NEVER ``abs()``.
    """
    return magnitude(mat_norm(matrix))


# ----------------------------------------------------------------------
# TEST 1 — the 6 order-2 atoms (names; reference cascade.atoms).
# ----------------------------------------------------------------------


def test_six_order_two_atoms_are_named():
    """The 6 order-2 atoms are named, in the canonical lean-ISA order."""
    result = lean_isa_seventh_primitive()
    atoms = result["order_two_atoms"]
    assert tuple(atoms) == _EXPECTED_ATOMS
    assert len(atoms) == 6
    assert result["certificate"]["n_order_two_atoms"] == 6


def test_atom_names_reference_cascade_atoms_module():
    """Each named atom is a real callable in srmech.amsc.cascade.atoms."""
    from srmech.amsc.cascade import atoms as cascade_atoms

    for name in lean_isa_seventh_primitive()["order_two_atoms"]:
        assert hasattr(cascade_atoms, name)
        assert callable(getattr(cascade_atoms, name))
    # The framework reading points at the atoms module by name.
    reading = lean_isa_seventh_primitive()["framework_chirality_complete_reading"]
    assert reading["atoms_module"] == "srmech.amsc.cascade.atoms"


# ----------------------------------------------------------------------
# TEST 2 — the order-3 7th primitive: τ³ = I bit-exact, τ ≠ I, τ² ≠ I.
# ----------------------------------------------------------------------


def test_seventh_primitive_is_triality_automorphism():
    """The 7th primitive is the triality automorphism τ (the order-3 axis)."""
    result = lean_isa_seventh_primitive()
    assert (
        result["order_three_primitive"]
        == "srmech.qm.triality.triality_automorphism"
    )
    tau = result["triality"]
    assert tau.shape == (28, 28)
    # The returned τ matches the engine's τ bit-exactly.
    assert _frob(_sub(tau, triality.triality_automorphism())) < _BIT_EXACT


def test_triality_order_is_exactly_three_bit_exact():
    """The order of τ is EXACTLY 3 — ‖τ³ − I‖ ≈ 0, τ ≠ I, τ² ≠ I (BIT-EXACT).

    This is the bit-exact self-computed half of the honesty split: the
    genuine order-3 element of S3 = Out(Spin(8)), verified via the existing
    engine (residual ~4e-14), reduced through the Class K magnitude.
    """
    cert = lean_isa_seventh_primitive()["certificate"]
    assert cert["triality_order"] == 3
    # τ³ = I bit-exact (the order divides 3).
    assert cert["triality_order_residual"] < _TOL
    # τ ≠ I and τ² ≠ I (the order is exactly 3, not 1).
    assert cert["triality_not_identity"] > 1.0
    assert cert["triality_squared_not_identity"] > 1.0

    # Independent re-derivation from the returned τ (no abs()).
    tau = lean_isa_seventh_primitive()["triality"]
    identity = _eye(28)
    tau2 = mat_matmul(tau, tau)
    tau3 = mat_matmul(tau2, tau)
    assert _frob(_sub(tau3, identity)) < _TOL
    assert _frob(_sub(tau, identity)) > 1.0
    assert _frob(_sub(tau2, identity)) > 1.0


# ----------------------------------------------------------------------
# TEST 3 — F220: |G| = 8 / no-order-3 / Lagrange (3 ∤ 8) / 6 + 1 = 7.
# ----------------------------------------------------------------------


def test_f220_lagrange_obstruction_and_chirality_complete_seven():
    """|G| = 8, 3 ∤ 8 ⇒ no order-3 element; 3 ∣ 3; the core is 6 + 1 = 7.

    The Lagrange arithmetic (3 ∤ 8 for the order-2 atoms' abelian group; 3 ∣ 3
    for the triality element) is bit-exact; the |G| = 8 / Z2^3 structure is the
    documented framework finding combined with that arithmetic.
    """
    cert = lean_isa_seventh_primitive()["certificate"]
    assert cert["abelian_group_order"] == 8
    # 3 ∤ 8 (no order-3 element among the order-2 atoms) ...
    assert cert["three_divides_group_order"] is False
    # ... but 3 ∣ 3 (the genuine triality element has order 3).
    assert cert["three_divides_triality_order"] is True
    # The Lagrange obstruction holds: an order-3 element needs 3 | |G|.
    assert cert["lagrange_obstruction"] is True
    # The chirality-complete core: 6 order-2 atoms + 1 order-3 triality = 7.
    assert cert["chirality_complete_core"] == 7
    assert cert["n_order_two_atoms"] + 1 == cert["chirality_complete_core"]


# ----------------------------------------------------------------------
# TEST 4 — the MPR self-attestation block is present + well-formed.
# ----------------------------------------------------------------------


def test_mpr_attestation_present_and_well_formed():
    """The MPR v1 self-attestation content-addresses the computed τ.

    ``response_sha256`` is ``sha256_bytes`` over the float64 bytes of the
    28×28 τ (the build output); the attestation cites Baez (arXiv OA) for the
    PARENT facts only (Out(Spin(8)) = S3 / g2 = Der(O)), NOT the F220
    chirality-complete-7 reading (the framework finding). parser_version is
    the 0.6.0 release line.
    """
    from srmech.amsc.format import sha256_bytes

    result = lean_isa_seventh_primitive()
    att = result["attestation"]

    # MPR v1 shape.
    assert att["mpr_version"] == "1.0"
    assert set(att.keys()) >= {
        "mpr_version", "data", "data_schema_id", "attestation", "rendering",
    }

    block = att["attestation"]
    # 64-hex SHA-256 digests, routed through sha256_bytes (no hashlib).
    assert len(block["response_sha256"]) == 64
    assert len(block["parser_rule_hash"]) == 64
    assert len(block["collector_descriptor_hash"]) == 64
    # Paywalled DOI rejected; arXiv OA cited for the parent fact only.
    assert block["source_doi"] is None
    assert block["source_url"] == "https://arxiv.org/abs/math/0105155"
    assert block["license"] == "CC0"
    assert block["parser_version"] == "srmech 0.6.0"

    # response_sha256 == sha256_bytes over the 28×28 τ float64 bytes.
    # Mat.tobytes() is the row-major float64 buffer — byte-identical to the
    # prior ``ascontiguousarray(τ, float64).tobytes()``. Numpy-free.
    tau = triality.triality_automorphism().tobytes()
    assert block["response_sha256"] == sha256_bytes(tau)

    # The data payload records the chirality-complete 6 + 1 core + the atoms.
    assert att["data"]["structure"] == "chirality_complete_an_core_6_plus_1"
    assert att["data"]["order_two_atoms"] == list(_EXPECTED_ATOMS)
    assert att["data"]["order_three_primitive"] == "triality_automorphism"
    assert att["data"]["triality_order"] == 3
    assert att["data"]["chirality_complete_core"] == 7


# ----------------------------------------------------------------------
# TEST 5 — the framework reading is distinct + tagged framework-reading.
# ----------------------------------------------------------------------


def test_framework_reading_is_distinct_and_not_load_bearing():
    """The framework reading is tagged + the scope hierarchy is present.

    F220: the Z2 × Z2 × Z2 / chirality-complete-7 reading + the scope
    hierarchy (endianness ⊂ Class C ⊂ Klein-4 ⊂ Spin(8) triality) live ONLY
    under the separately-keyed framework field, tagged
    "framework-reading, not derived". No framework claim appears in any
    load-bearing certificate key.
    """
    result = lean_isa_seventh_primitive()
    reading = result["framework_chirality_complete_reading"]
    assert reading["note"] == "framework-reading, not derived"
    assert reading["atom_chirality_group"] == "Z2 × Z2 × Z2"
    assert reading["atom_chirality_group_order"] == 8
    assert reading["atoms_commute_abelian"] is True
    assert reading["no_order_three_element_in_atoms"] is True
    assert reading["order_three_axis_unreachable_from_atoms"] is True
    assert reading["chirality_complete_core_6_plus_1"] == 7
    # The scope hierarchy: endianness ⊂ Class C ⊂ Klein-4 ⊂ Spin(8) triality.
    hierarchy = reading["scope_hierarchy"]
    for piece in ("endianness", "Class C", "Klein-4", "triality"):
        assert piece in hierarchy

    # The load-bearing certificate carries NO framework note/hierarchy keys.
    cert = result["certificate"]
    assert "note" not in cert
    assert "scope_hierarchy" not in cert
    assert "atom_chirality_group" not in cert
    # The load-bearing top-level keys are present.
    load_bearing = {
        "order_two_atoms", "order_three_primitive", "triality",
        "certificate", "attestation",
    }
    assert load_bearing <= set(result.keys())


# ----------------------------------------------------------------------
# TEST 6 — the introspection tool total (this voxel's +1 took it to 176;
# the rc6 parallel_sector_dispatch +1 then took it to 177).
# ----------------------------------------------------------------------


def test_introspect_tools_total_is_210():
    import srmech.introspect as introspect

    assert introspect.describe()["tools"]["total"] == 331


def test_tool_entry_registered():
    """The new op is a registered ToolEntry in the qm.triality category."""
    from srmech.amsc import tool_schema

    schema = tool_schema.get_tool_schema()
    name = "srmech.qm.triality.lean_isa_seventh_primitive"
    entry = schema.lookup(name)
    assert entry is not None
    assert entry.name == name
    assert entry.category == "qm.triality"
    names = {e.name for e in schema.tools}
    assert name in names
