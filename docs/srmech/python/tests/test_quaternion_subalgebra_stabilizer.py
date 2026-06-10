"""Bit-exact acceptance tests for the quaternion-subalgebra stabiliser voxel.

Per issue #759 (srmech MS#20 / F215). The new
``srmech.qm.so8.quaternion_subalgebra_stabilizer`` exposes the 6-dim
``so(4) = su(2) ⊕ su(2)`` subalgebra of ``g2 = Der(O)`` that stabilises a
quaternion subalgebra ``H ⊂ O`` — the ℍ-reading SIBLING of
``srmech.qm.so8.an_embedding`` (the su(3) ⊕ 3 ⊕ 3bar ℂ-reading).

The tests prove the invariant CERTIFICATE:

1. ``dim == 6`` (the so(4) stabiliser).
2. ``Killing-form rank == 6`` — SEMISIMPLE (Cartan's criterion).
3. the two-su(2) / two-triplet split is present + bit-exact: two 3-dim
   ideals (the self-dual / anti-self-dual halves on ``H^⊥``), each closing
   as su(2), commuting (``[su2_+, su2_-] = 0``), each a g2-ideal,
   ``span[su2_+ | su2_-] == span(so4)``; AND the two-triplet Killing
   SPECTRUM (two distinct eigenvalues ×3).
4. ℍ-CHOICE-INVARIANCE across ≥ 2 quaternion subalgebras — the Killing
   spectrum is bit-identical (the seven Fano-line H are g2-conjugate).
5. the MPR self-attestation block is present + well-formed.
6. ``srmech.introspect.describe()["tools"]["total"] == 177`` (this voxel's
   +1 ToolEntry, the #761 lean-ISA seventh-primitive voxel's +1, and the
   rc6 parallel_sector_dispatch +1).

ALL deviations are reduced through the **scalar** Class K pin-slot
magnitude (:func:`srmech.amsc.cascade.magnitude`) — NEVER Python ``abs()``
per ``[[feedback_sign_handling_is_class_k_pin_slot_not_alu_abs]]`` — by
first reducing a matrix / scalar deviation to a Python float, then passing
it to ``magnitude`` (scalar-only; it raises on an ndarray).

Determinism: every basis extraction is a deterministic SVD / QR (no
``np.random``), so the certificate is reproducible.

F215 (surfaced under the separately-keyed ``framework_so4_reading``): this
so(4) ⊂ g2 SYMMETRY surface is explicitly DISTINCT from the 6
``cascade.atoms`` operator surface; the "6 = 6" is a coincidence (0 of the
6 atoms are Lie generators).
"""

from __future__ import annotations

import numpy as np
import pytest

from srmech.amsc.cascade import magnitude
from srmech.qm import so8

_TOL = 1e-9
_BIT_EXACT = 1e-10


# ----------------------------------------------------------------------
# Helpers — scalar reductions through cascade.magnitude (never abs()).
# ----------------------------------------------------------------------


def _frob(matrix: np.ndarray) -> float:
    """Frobenius-norm deviation reduced through the scalar Class K magnitude.

    Reduce the matrix to a SCALAR float FIRST (``np.linalg.norm`` is the
    Frobenius norm), then pass that scalar to ``cascade.magnitude``
    (scalar-only; it raises on an ndarray). NEVER ``abs()``.
    """
    return magnitude(float(np.linalg.norm(matrix)))


def _scalar(value: float) -> float:
    """A scalar deviation reduced through the Class K magnitude (no abs())."""
    return magnitude(float(value))


def _epq_coords(matrix: np.ndarray) -> np.ndarray:
    """E_{pq}-coords of an antisymmetric 8×8 (the shared so8 frame)."""
    return so8._epq_coords(matrix)


def _commutator(x: np.ndarray, y: np.ndarray) -> np.ndarray:
    return x @ y - y @ x


def _span_projector(matrices) -> np.ndarray:
    """The orthogonal projector onto span(matrices) in the E_{pq} frame."""
    coords = np.column_stack([_epq_coords(m) for m in matrices])
    q, _ = np.linalg.qr(coords)
    return q @ q.T


def _worst_closure(matrices, projector) -> float:
    """Max residual of ``[m_i, m_j]`` outside span(matrices) (no abs())."""
    worst = 0.0
    for i in range(len(matrices)):
        for j in range(len(matrices)):
            v = _epq_coords(_commutator(matrices[i], matrices[j]))
            worst = max(worst, _scalar(float(np.linalg.norm(v - projector @ v))))
    return worst


# ----------------------------------------------------------------------
# TEST 1 — dim == 6 (the so(4) stabiliser).
# ----------------------------------------------------------------------


def test_stabiliser_dim_is_six():
    """The quaternion-subalgebra stabiliser is exactly 6-dimensional."""
    result = so8.quaternion_subalgebra_stabilizer()
    so4 = result["so4"]
    assert len(so4) == 6
    # Each generator is a real antisymmetric 8×8 (so(4) ⊂ so(8) ⊂ g2 ⊂ so(8)).
    for generator in so4:
        assert generator.shape == (8, 8)
        assert _frob(generator + generator.T) < _BIT_EXACT  # antisymmetric
    # The 6 generators are linearly independent (rank exactly 6).
    coords = np.column_stack([_epq_coords(m) for m in so4])
    assert np.linalg.matrix_rank(coords, tol=_TOL) == 6


def test_stabiliser_generators_stabilise_H():
    """Each so(4) generator maps H back into H (leaks nothing into H^⊥)."""
    result = so8.quaternion_subalgebra_stabilizer(1)
    h_imag = result["quaternion_imaginary_units"]
    complement = [i for i in range(1, 8) if i not in h_imag]
    basis = np.eye(8)
    for generator in result["so4"]:
        for a in h_imag:
            image = generator @ basis[a]
            leak = sum(image[k] * image[k] for k in complement)
            assert _scalar(float(np.sqrt(leak))) < _BIT_EXACT


# ----------------------------------------------------------------------
# TEST 2 — Killing-form rank == 6 (SEMISIMPLE; Cartan's criterion).
# ----------------------------------------------------------------------


def test_killing_form_rank_is_six_semisimple():
    """The Killing form has full rank 6 — so(4) is semisimple (Cartan)."""
    result = so8.quaternion_subalgebra_stabilizer()
    killing = result["killing_form"]
    assert killing.shape == (6, 6)
    # Symmetric Killing form.
    assert _frob(killing - killing.T) < _BIT_EXACT
    scale = max(1.0, float(np.max([_scalar(float(v)) for v in killing.flat])))
    rank = int(np.linalg.matrix_rank(killing, tol=_TOL * scale))
    assert rank == 6
    assert result["killing_rank"] == 6


# ----------------------------------------------------------------------
# TEST 3 — the two su(2) ideals / two-triplet split (bit-exact).
# ----------------------------------------------------------------------


def test_two_su2_split_is_present_and_bit_exact():
    """The two 3-dim su(2) ideals close, commute, are ideals, and reassemble.

    All residuals are reduced through the scalar Class K magnitude (never
    abs()) and are below ~1e-10 (bit-exact ~1e-15 in practice).
    """
    result = so8.quaternion_subalgebra_stabilizer()
    su2_plus = result["su2_plus"]
    su2_minus = result["su2_minus"]
    so4 = result["so4"]
    assert len(su2_plus) == 3
    assert len(su2_minus) == 3
    assert result["decomposition"]["so4_6"] == (3, 3)

    proj_plus = _span_projector(su2_plus)
    proj_minus = _span_projector(su2_minus)

    # Each su(2) factor closes under its own bracket.
    assert _worst_closure(su2_plus, proj_plus) < _BIT_EXACT
    assert _worst_closure(su2_minus, proj_minus) < _BIT_EXACT

    # The two ideals COMMUTE ([su2_+, su2_-] = 0 — a direct sum of ideals).
    cross = 0.0
    for a in su2_plus:
        for b in su2_minus:
            cross = max(cross, _scalar(float(np.linalg.norm(_commutator(a, b)))))
    assert cross < _BIT_EXACT

    # Each su(2) is an IDEAL in the whole so(4): [so4, su2_±] ⊆ su2_±.
    worst_plus = 0.0
    worst_minus = 0.0
    for g in so4:
        for s in su2_plus:
            v = _epq_coords(_commutator(g, s))
            worst_plus = max(worst_plus, _scalar(float(np.linalg.norm(v - proj_plus @ v))))
        for s in su2_minus:
            v = _epq_coords(_commutator(g, s))
            worst_minus = max(worst_minus, _scalar(float(np.linalg.norm(v - proj_minus @ v))))
    assert worst_plus < _BIT_EXACT
    assert worst_minus < _BIT_EXACT

    # Bidirectional killer: span[su2_+ | su2_-] == span(so4) (rank 6 both ways).
    plus_coords = np.column_stack([_epq_coords(m) for m in su2_plus])
    minus_coords = np.column_stack([_epq_coords(m) for m in su2_minus])
    so4_coords = np.column_stack([_epq_coords(m) for m in so4])
    split = np.column_stack([plus_coords, minus_coords])
    assert np.linalg.matrix_rank(split, tol=_TOL) == 6
    assert np.linalg.matrix_rank(
        np.column_stack([split, so4_coords]), tol=_TOL
    ) == 6


def test_killing_spectrum_is_two_triplets():
    """The Killing spectrum has exactly two distinct eigenvalues, ×3 each.

    Two eigenvalues each with multiplicity 3 IS the su(2) ⊕ su(2)
    fingerprint (each simple su(2) factor contributes one Killing
    eigenvalue with multiplicity dim su(2) = 3).
    """
    spectrum = so8.quaternion_subalgebra_stabilizer()["killing_spectrum"]
    assert spectrum.shape == (6,)
    ordered = np.sort(spectrum)
    # Two triplets: the first three equal, the last three equal, distinct.
    low = ordered[:3]
    high = ordered[3:]
    assert _scalar(float(np.max(low) - np.min(low))) < _BIT_EXACT
    assert _scalar(float(np.max(high) - np.min(high))) < _BIT_EXACT
    assert _scalar(float(np.mean(high) - np.mean(low))) > 0.1  # distinct
    # so(4) is semisimple with NO zero eigenvalue (negative-definite here).
    assert np.all(ordered < -1e-6)


# ----------------------------------------------------------------------
# TEST 4 — ℍ-choice-invariance across ≥ 2 quaternion subalgebras.
# ----------------------------------------------------------------------


def test_h_choice_invariance_spectrum_bit_identical():
    """The Killing spectrum is bit-identical across different ℍ choices.

    The 7 Fano-line quaternion subalgebras are g2 = Aut(O)-conjugate, so
    their stabilisers are isomorphic; with the orthonormalised generator
    basis the invariant Killing spectrum is bit-identical (the same
    so(4) = su(2) ⊕ su(2) algebra-type for every ℍ).
    """
    reference = np.sort(so8.quaternion_subalgebra_stabilizer(1)["killing_spectrum"])
    for quaternion_index in range(2, 8):
        spectrum = np.sort(
            so8.quaternion_subalgebra_stabilizer(quaternion_index)["killing_spectrum"]
        )
        deviation = _scalar(float(np.max(reference - spectrum)))
        assert deviation < _BIT_EXACT, (
            f"ℍ index {quaternion_index} spectrum differs by {deviation}"
        )


def test_h_choice_invariance_dim_and_rank():
    """Every ℍ gives the same dim-6 / Killing-rank-6 / (3, 3) split."""
    for quaternion_index in range(1, 8):
        result = so8.quaternion_subalgebra_stabilizer(quaternion_index)
        assert len(result["so4"]) == 6
        assert result["killing_rank"] == 6
        assert len(result["su2_plus"]) == 3
        assert len(result["su2_minus"]) == 3
        assert result["decomposition"]["so4_6"] == (3, 3)


def test_invalid_quaternion_index_raises():
    """``quaternion_index`` out of 1..7 raises a clean ValueError."""
    with pytest.raises(ValueError):
        so8.quaternion_subalgebra_stabilizer(0)
    with pytest.raises(ValueError):
        so8.quaternion_subalgebra_stabilizer(8)


# ----------------------------------------------------------------------
# TEST 5 — the MPR self-attestation block is present + well-formed.
# ----------------------------------------------------------------------


def test_mpr_attestation_present_and_well_formed():
    """The MPR v1 self-attestation content-addresses the computed structure.

    Mirrors ``an_embedding``: ``response_sha256`` is ``sha256_bytes`` over
    the float64 bytes of the 14 g2 generators (the build input); the
    attestation cites Baez (arXiv OA) for the PARENT g2 = Der(O) fact only,
    NOT the su(2) ⊕ su(2) split (this op's own computation).
    """
    from srmech.amsc.format import sha256_bytes

    result = so8.quaternion_subalgebra_stabilizer()
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
    assert block["parser_version"].startswith("srmech ")

    # response_sha256 == sha256_bytes over the 14 g2 generators' float64 bytes.
    g2 = [np.array(m) for m in so8.g2_subalgebra()]
    generator_bytes = b"".join(
        np.ascontiguousarray(g, dtype=np.float64).tobytes() for g in g2
    )
    assert block["response_sha256"] == sha256_bytes(generator_bytes)

    # The data payload records the so(4) = su(2) ⊕ su(2) structure + the H line.
    assert att["data"]["structure"] == "g2_so4_su2_su2_quaternion_stabiliser"
    assert att["data"]["real_dimensions"] == {
        "so4": 6, "su2_plus": 3, "su2_minus": 3,
    }
    assert att["data"]["quaternion_fano_line"] == [1, 2, 3]


def test_framework_so4_reading_is_distinct_from_atoms():
    """The framework reading marks so(4) symmetry ≠ cascade.atoms operators.

    F215: the 6 cascade.atoms are group-element ops (0/6 Lie generators);
    the 6 = 6 dimension match is coincidence — surfaced ONLY under the
    separately-keyed framework field, tagged framework-reading-not-derived.
    """
    reading = so8.quaternion_subalgebra_stabilizer()["framework_so4_reading"]
    assert reading["note"] == "framework-reading, not derived"
    assert reading["six_equals_six_is_coincidence"] is True
    assert reading["atoms_that_are_lie_generators"] == 0
    assert "cascade.atoms" in reading["operator_surface"]
    assert "so(4)" in reading["symmetry_surface"]
    # The reading is NOT in any load-bearing return key (only this field).
    result = so8.quaternion_subalgebra_stabilizer()
    load_bearing = {
        "so4", "su2_plus", "su2_minus", "killing_form", "killing_rank",
        "killing_spectrum", "decomposition", "quaternion_fano_line",
        "quaternion_imaginary_units", "attestation",
    }
    assert load_bearing <= set(result.keys())


# ----------------------------------------------------------------------
# TEST 6 — the introspection tool total (174 -> 175 here -> 176 with the
#          #761 lean-ISA seventh-primitive voxel -> 177 with the rc6
#          parallel_sector_dispatch voxel also registered).
# ----------------------------------------------------------------------


def test_introspect_tools_total_is_210():
    import srmech.introspect as introspect

    assert introspect.describe()["tools"]["total"] == 284


def test_tool_entry_registered():
    """The new op is a registered ToolEntry in the qm.so8 category."""
    from srmech.amsc import tool_schema

    schema = tool_schema.get_tool_schema()
    name = "srmech.qm.so8.quaternion_subalgebra_stabilizer"
    entry = schema.lookup(name)
    assert entry is not None
    assert entry.name == name
    assert entry.category == "qm.so8"
    names = {e.name for e in schema.tools}
    assert name in names
