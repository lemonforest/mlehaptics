"""rc237 (F3) — the responsion_schema CURVATURE property: per (op, carrier)
responsion, FLAT (curvature PROVABLY vanishes — frame-independent) vs CURVED
(can carry a frame-dependent holonomy). The schema lift of rc236's
``separate_frame_curvature`` ``is_flat``:
``tool_schema : carrier_schema : responsion_schema :: connection : sections :
CURVATURE``.

SOUNDNESS is the whole point: ``"flat"`` ONLY on the two airtight certificates
(a COMMUTATIVE carrier — ``[A,B] ≡ 0`` by the ring axiom; or a ``kind ==
"trace"`` read — ``Tr[A,B] ≡ 0`` by cyclicity), CURVED conservatively
elsewhere — NEVER a false flat on a genuinely-curved pairing. Cross-checked
against the concrete rc236 op. numpy-free.
"""
from __future__ import annotations

from srmech.introspect.responsion_schema import (
    _COMMUTATIVE_CARRIERS,
    _curvature_class,
    _pure_responsion_schema,
    responsion_schema,
)


# ── every responsion carries a well-formed curvature class ───────────────────

def test_every_responsion_has_flat_or_curved():
    for key, responsions in _pure_responsion_schema().items():
        for r in responsions:
            assert r["curvature"] in ("flat", "curved"), key


def test_curvature_is_derived_from_carrier_and_kind():
    """The field is DERIVED (never authored): it always equals
    ``_curvature_class(carrier, kind)``."""
    for responsions in _pure_responsion_schema().values():
        for r in responsions:
            assert r["curvature"] == _curvature_class(r["carrier"], r["kind"])


# ── the two airtight FLAT certificates ───────────────────────────────────────

def test_commutative_carrier_is_flat():
    """A commutative (q-)polynomial / theta carrier → [A,B] ≡ 0 → FLAT, for
    EVERY responsion riding it (verified reducer or honest-OPEN alike)."""
    schema = _pure_responsion_schema()
    for key, responsions in schema.items():
        for r in responsions:
            if r["carrier"] in _COMMUTATIVE_CARRIERS:
                assert r["curvature"] == "flat", key


def test_trace_read_is_flat_even_on_mat():
    """heat_trace ⊗ Mat: the trace annihilates every commutator (Tr[A,B]≡0), so
    the trace responsion is FLAT even on the NON-commutative Mat operator
    carrier — the one Mat edge that is flat."""
    schema = _pure_responsion_schema()
    trace = schema["srmech.math.laplacian.heat_trace|Mat"][0]
    assert trace["kind"] == "trace"
    assert trace["curvature"] == "flat"


def test_heat_trace_is_the_only_flat_mat_edge():
    """SOUNDNESS witness: on the non-commutative Mat carrier, the ONLY flat
    responsion is the trace invariant — every other Mat read is conservatively
    curved (no false flat)."""
    schema = _pure_responsion_schema()
    flat_mat = [(k, r["kind"]) for k, v in schema.items() for r in v
                if r["carrier"] == "Mat" and r["curvature"] == "flat"]
    assert flat_mat == [("srmech.math.laplacian.heat_trace|Mat", "trace")]


# ── the CURVED pairings (frame-dependent holonomy) ───────────────────────────

def test_the_one_on_One_is_curved_the_F2_holonomy():
    """the_one ⊗ One is CURVED — the One carrier holds the winding grading that
    F2 (separate_winding_curvature) decomposes as its curvature. The two faces
    of rc237 agree: the One's responsion is frame-DEPENDENT."""
    schema = _pure_responsion_schema()
    edge = schema["srmech.cascade.the_one|One"][0]
    assert edge["carrier"] == "One"
    assert edge["curvature"] == "curved"


def test_propagator_and_resolvent_are_curved():
    """The Laplace-dual pair e^{−zL}·u0 / (zI−L)^{-1}·u0 carry the coherence-dial
    phase (the frame) → CURVED."""
    schema = _pure_responsion_schema()
    for r in schema["srmech.math.laplacian.responsion|Mat"]:
        assert r["kind"] in ("propagator", "resolvent")
        assert r["curvature"] == "curved"


def test_flux_response_curve_is_curved():
    schema = _pure_responsion_schema()
    flux = schema["srmech.math.laplacian.ground_state_flux_response|Mat"][0]
    assert flux["curvature"] == "curved"        # the flux gauge is the frame


def test_open_sustain_on_operator_carrier_is_curved():
    """The honest-OPEN residues on the non-commutative operator carriers (Mat /
    One) are curved; on the commutative carriers they are flat."""
    schema = _pure_responsion_schema()
    assert schema["srmech.math.dispatch.infer|Mat"][0]["curvature"] == "curved"
    assert schema["srmech.math.dispatch.infer|One"][0]["curvature"] == "curved"
    assert schema["srmech.math.dispatch.infer|EllRatio"][0]["curvature"] == "flat"


# ── the classifier is a pure (carrier, kind) function ────────────────────────

def test_classifier_unit():
    assert _curvature_class("Poly", "closed_form") == "flat"
    assert _curvature_class("BiPoly", "open_sustain") == "flat"
    assert _curvature_class("EllMonomial", "closed_form") == "flat"
    assert _curvature_class("Mat", "trace") == "flat"          # trace exception
    assert _curvature_class("Mat", "propagator") == "curved"
    assert _curvature_class("Mat", "closed_form") == "curved"
    assert _curvature_class("One", "closed_form") == "curved"


# ── ground the schema classification in the CONCRETE rc236 op ────────────────

def test_rc236_grounds_the_flat_vs_curved_split():
    """The schema's flat/curved lift must agree with rc236's concrete is_flat on
    the same distinction: commuting/1×1/symmetric-commuting pairing → flat;
    non-commuting (σx, σz) → curved."""
    from srmech.cascade.matrix_cascades import separate_frame_curvature

    # non-commuting operator pairing → curved (is_flat False)
    sx, sz = [[0, 1], [1, 0]], [[1, 0], [0, -1]]
    assert separate_frame_curvature(sx, sz)["is_flat"] is False
    # a 1x1 (scalar) carrier — everything commutes → flat
    assert separate_frame_curvature([[5]], [[7]])["is_flat"] is True
    # commuting (shared eigenbasis) → flat
    a, b = [[2, 1], [1, 2]], [[3, 1], [1, 3]]
    assert separate_frame_curvature(a, b)["is_flat"] is True


def test_dispatching_wrapper_preserves_curvature():
    """responsion_schema() (native-routed when available) carries the curvature
    field value-identically to the pure derivation."""
    assert responsion_schema() == _pure_responsion_schema()
