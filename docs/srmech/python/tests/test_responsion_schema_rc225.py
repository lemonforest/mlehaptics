"""rc225 (user design 2026-07-12) — responsion_schema: the RESPONSION
(stored-relationship) introspection surface, the k=3 completion of the
introspection triad.

tool_schema introspects the OPS (verbs); carrier_schema (rc205) the OPERANDS
(nouns) — the k=2 pair of NODES. responsion_schema is the EDGE face binding
them: "this op, on this operand, answers THIS way" (op⊗operand⊗responsion;
srmech = Stored-RELATIONSHIP Mechanism). Pins:

  1. **The edge shape (the key IS the edge).** Every entry is keyed by the
     ``"<operator>|<carrier>"`` pair with both refs first-class in every
     responsion — never a bare-name flat registry (the rc224 flatten-trap,
     one algebra up).
  2. **No dangling refs (the k=3 binds the k=2).** Every ``operator`` is a
     registered tool_schema key AND every ``carrier`` is a real
     carrier_schema() key.
  3. **Two regimes of ONE responsion.** Both ``discrete_algebraic`` (the
     F929 reduce-back rows) and ``continuous_spectral`` (the
     response-function ops) are present; the propagator ⊗ resolvent
     LAPLACE-DUAL pair rides the ONE ``laplacian.responsion|Mat`` edge.
  4. **The honest OPEN (F934 sustain).** The open entries are the F929 rows'
     residues on the ``infer`` router, ``answers_with`` VERBATIM from
     ``dispatch._OPEN_HINTS`` — surfaced, never hidden.
  5. **The hash-ratchet (THE gate).** The C ``srmech_responsion_schema``
     assembler over the compiled-in ``srmech_responsion_registry`` const
     table emits bytes BYTE-IDENTICAL to the Python SSoT pre-image
     ``json.dumps(_pure_responsion_schema(), sort_keys=True,
     separators=(",", ":"))`` — same sha256. If an edge / a hint changes
     Python-side without regenerating the C table, this fails.
  6. **Codegen idempotence + purity.** Re-running gen_responsion_registry.py
     reproduces the checked-in .c exactly; the generated file is pure ASCII
     (MSVC-safe).
  7. **Registration.** The ToolEntry exists; tools.total == 418; the Rosetta
     row is composes_c.

The native-requiring assertions ``skipif`` cleanly when the rc225 C peer is
absent (pure / stale-lib host). numpy-free (imports only srmech + stdlib).
"""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

from srmech import _native
from srmech.introspect.carrier_schema import _CARRIERS
from srmech.math.dispatch import _OPEN_HINTS
from srmech.introspect.responsion_schema import (
    _CONTINUOUS_VERIFIED,
    _DISCRETE_VERIFIED,
    _INFER_OP,
    _ROW_OPEN_CARRIER,
    _pure_responsion_schema,
    responsion_schema,
)
from srmech.introspect.tool_schema import get_tool_schema, warmup_all

warmup_all()

_HERE = Path(__file__).resolve().parent
_C_SRC = _HERE.parent.parent / "c" / "src" / "srmech_responsion_registry.c"
_CODEGEN = _HERE.parent.parent / "c" / "tools" / "gen_responsion_registry.py"

_needs_native = pytest.mark.skipif(
    not _native.has_native_responsion_schema(),
    reason="rc225 responsion-registry C peer not loaded (pure / stale host)",
)

# rc237 (F3): the curvature FLAT/CURVED frame-independence class is now a
# first-class per-responsion field (the schema lift of rc236's is_flat).
_FIELDS = ("operator", "carrier", "kind", "regime", "answers_with", "status",
           "curvature")
_REGIMES = ("continuous_spectral", "discrete_algebraic")
_STATUSES = ("verified", "open")
_CURVATURES = ("flat", "curved")


def _canonical_payload() -> bytes:
    """The Python SSoT canonical pre-image (compact, sorted keys, default
    ensure_ascii=True) the C table is hash-ratcheted against."""
    return json.dumps(
        _pure_responsion_schema(), sort_keys=True, separators=(",", ":")
    ).encode("utf-8")


# ── 1. the edge shape (the key IS the edge) ───────────────────────────────────

def test_every_entry_is_an_edge_keyed_by_operator_carrier() -> None:
    schema = _pure_responsion_schema()
    assert schema, "the relation must be non-empty"
    for key, responsions in schema.items():
        assert isinstance(responsions, list) and responsions
        for r in responsions:
            assert tuple(sorted(r)) == tuple(sorted(_FIELDS)), (
                f"{key}: entry fields {sorted(r)} != {sorted(_FIELDS)}"
            )
            # The key references the EDGE — never a bare name.
            assert key == f"{r['operator']}|{r['carrier']}", (
                f"key {key!r} does not encode its (operator, carrier) edge"
            )
            assert r["regime"] in _REGIMES
            assert r["status"] in _STATUSES
            assert r["curvature"] in _CURVATURES
            assert isinstance(r["answers_with"], str) and r["answers_with"]
        # Every responsion on one edge shares the SAME two refs.
        assert len({(r["operator"], r["carrier"]) for r in responsions}) == 1


def test_key_is_never_a_bare_name() -> None:
    """A flat noun-registry key (no '|', or a bare carrier/op name) would
    flatten the relation — the rc224 flatten-trap, one algebra up."""
    for key in _pure_responsion_schema():
        assert "|" in key
        op, carrier = key.split("|", 1)
        assert "." in op, f"operator side of {key!r} is not a dotted tool key"
        assert carrier and "." not in carrier


# ── 2. no dangling refs — the k=3 binds the k=2 ──────────────────────────────

def test_operator_refs_resolve_in_tool_schema() -> None:
    registered = {t.name for t in get_tool_schema().tools}
    for key, responsions in _pure_responsion_schema().items():
        for r in responsions:
            assert r["operator"] in registered, (
                f"{key}: operator {r['operator']!r} is not a tool_schema key"
            )


def test_carrier_refs_resolve_in_carrier_schema() -> None:
    from srmech.introspect.carrier_schema import carrier_schema

    carriers = set(carrier_schema())
    assert carriers == set(_CARRIERS)
    for key, responsions in _pure_responsion_schema().items():
        for r in responsions:
            assert r["carrier"] in carriers, (
                f"{key}: carrier {r['carrier']!r} is not a carrier_schema key"
            )


def test_dangling_ref_raises_at_derivation() -> None:
    """A dangling ref is a BUG, not a payload: the derivation itself raises."""
    from srmech.introspect import responsion_schema as rs

    bogus = (("cyclic", "srmech.amsc.no_such.op", "One", "x"),)
    real = rs._DISCRETE_VERIFIED
    rs._DISCRETE_VERIFIED = bogus
    try:
        with pytest.raises(RuntimeError, match="unregistered operator"):
            rs._pure_responsion_schema()
    finally:
        rs._DISCRETE_VERIFIED = real


# ── 3. two regimes of ONE responsion ─────────────────────────────────────────

def test_both_regimes_present() -> None:
    schema = _pure_responsion_schema()
    regimes = {r["regime"] for v in schema.values() for r in v}
    assert regimes == set(_REGIMES)


def test_propagator_resolvent_laplace_dual_pair_on_one_edge() -> None:
    """The two canonical continuous members are LAPLACE-TRANSFORM DUALS and
    ride the SAME (laplacian.responsion, Mat) edge — the unity held, not
    split into two flat rows."""
    schema = _pure_responsion_schema()
    edge = schema["srmech.math.laplacian.responsion|Mat"]
    kinds = {r["kind"]: r for r in edge}
    assert set(kinds) == {"propagator", "resolvent"}
    for r in kinds.values():
        assert r["regime"] == "continuous_spectral"
        assert r["status"] == "verified"
    assert "e^{−zL}·u0" in kinds["propagator"]["answers_with"]
    assert "(zI−L)^{-1}·u0" in kinds["resolvent"]["answers_with"]
    assert "Laplace".lower() in kinds["resolvent"]["answers_with"].lower()


def test_continuous_response_family_edges_present() -> None:
    schema = _pure_responsion_schema()
    assert ("srmech.math.laplacian.propagate|Mat" in schema)
    trace = schema["srmech.math.laplacian.heat_trace|Mat"][0]
    assert trace["kind"] == "trace"
    assert "Tr" in trace["answers_with"]
    flux = schema["srmech.math.laplacian.ground_state_flux_response|Mat"][0]
    assert flux["kind"] == "response_curve"


def test_discrete_verified_rows_cover_the_f929_reducers() -> None:
    schema = _pure_responsion_schema()
    expected = {
        "srmech.cascade.the_one|One",
        "srmech.biology.coupling.resonant_spectrum|Mat",
        "srmech.apokatastasis.gosper.gosper|Poly",
        "srmech.apokatastasis.zeilberger.zeilberger|BiPoly",
        "srmech.apokatastasis.wz_certificate.wz_certificate|BiPoly",
        "srmech.apokatastasis.apagodu_zeilberger.apagodu_zeilberger|TriPoly",
        "srmech.apokatastasis.q_gosper.q_gosper|QPoly",
        "srmech.apokatastasis.q_zeilberger.q_zeilberger|QBiPoly",
        "srmech.apokatastasis.q_wz_certificate.q_wz_certificate|QBiPoly",
        "srmech.apokatastasis.elliptic_wz_certificate.elliptic_wz_certificate"
        "|EllRatio",
        "srmech.apokatastasis.elliptic_jackson.multivariate_elliptic_jackson"
        "|EllMonomial",
    }
    assert expected <= set(schema)
    for key in expected:
        for r in schema[key]:
            assert r["regime"] == "discrete_algebraic"
            assert r["kind"] == "closed_form"
            assert r["status"] == "verified"


def test_every_discrete_row_names_an_f929_dispatch_row() -> None:
    """The discrete side derives FROM the dispatch SSoT: every authored row
    tag (verified and open alike) is a real _OPEN_HINTS key."""
    for row, _op, _carrier, _answers in _DISCRETE_VERIFIED:
        assert row in _OPEN_HINTS
    for row, _carrier in _ROW_OPEN_CARRIER:
        assert row in _OPEN_HINTS


# ── 4. the honest OPEN (F934 sustain) ────────────────────────────────────────

def test_at_least_one_open_entry_and_all_verbatim_from_open_hints() -> None:
    schema = _pure_responsion_schema()
    opens = [r for v in schema.values() for r in v if r["status"] == "open"]
    assert opens, "the schema must surface the OPEN relationships honestly"
    hint_texts = {v for k, v in _OPEN_HINTS.items() if k is not None}
    for r in opens:
        assert r["kind"] == "open_sustain"
        assert r["regime"] == "discrete_algebraic"
        assert r["operator"] == _INFER_OP
        assert r["answers_with"] in hint_texts, (
            "an OPEN responsion's answers_with must be the dispatch "
            "_OPEN_HINTS text VERBATIM (the router's own honest hint)"
        )


def test_open_residue_rides_the_row_operand_carrier() -> None:
    schema = _pure_responsion_schema()
    edge = schema[f"{_INFER_OP}|EllRatio"]
    assert len(edge) == 1
    assert edge[0]["answers_with"] == _OPEN_HINTS["sigma_elliptic"]
    edge = schema[f"{_INFER_OP}|Mat"]
    assert edge[0]["answers_with"] == _OPEN_HINTS["spectral"]


# ── 5. the hash-ratchet (native == pure, byte-identical) ─────────────────────

@_needs_native
def test_c_json_byte_identical_to_python_ssot() -> None:
    c_payload = _native.responsion_schema_json_c()
    assert c_payload is not None
    assert c_payload == _canonical_payload(), (
        "srmech_responsion_schema bytes differ from the Python SSoT — "
        "regenerate c/src/srmech_responsion_registry.c with "
        "c/tools/gen_responsion_registry.py"
    )


@_needs_native
def test_hash_ratchet_sha256_locks_c_to_python() -> None:
    from srmech.amsc.format import sha256_bytes

    c_payload = _native.responsion_schema_json_c()
    assert c_payload is not None
    assert sha256_bytes(c_payload) == sha256_bytes(_canonical_payload())


@_needs_native
def test_registry_count_and_keys_round_trip() -> None:
    schema = _pure_responsion_schema()
    assert _native.responsion_registry_count_c() == len(schema)
    keys = _native.responsion_registry_keys_c()
    assert keys == sorted(schema, key=lambda k: k.encode("utf-8"))


@_needs_native
def test_registry_find_first_class_fields() -> None:
    schema = _pure_responsion_schema()
    for probe in ("srmech.math.laplacian.responsion|Mat",
                  "srmech.apokatastasis.gosper.gosper|Poly",
                  f"{_INFER_OP}|EllRatio"):
        found = _native.responsion_registry_find_c(probe)
        assert found is not None
        assert found["key"] == probe
        assert found["operator"] == schema[probe][0]["operator"]
        assert found["carrier"] == schema[probe][0]["carrier"]
        assert found["n_responsions"] == len(schema[probe])
    assert _native.responsion_registry_find_c("not|AnEdge") is None


@_needs_native
def test_dispatching_wrapper_equals_pure() -> None:
    """responsion_schema() (which routes native when available) is
    VALUE-identical to the pure derivation."""
    assert responsion_schema() == _pure_responsion_schema()


def test_wrapper_equals_pure_on_any_host() -> None:
    """On a pure host the wrapper IS the pure path; on a native host the
    ratchet above makes them equal — either way, value-identical."""
    assert responsion_schema() == _pure_responsion_schema()


# ── 6. codegen idempotence + purity (pure Python, always runs) ───────────────

def _load_codegen():
    spec = importlib.util.spec_from_file_location(
        "gen_responsion_registry_rc225", _CODEGEN)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_codegen_is_idempotent() -> None:
    """Re-running the generator reproduces the checked-in table exactly
    (line-ending normalised). If this fails, srmech_responsion_registry.c is
    stale — an edge / a hint / a response form changed Python-side."""
    assert _C_SRC.exists(), f"missing generated table {_C_SRC}"
    assert _CODEGEN.exists(), f"missing codegen {_CODEGEN}"
    mod = _load_codegen()
    regenerated = mod.generate().replace("\r\n", "\n")
    on_disk = _C_SRC.read_text(encoding="utf-8").replace("\r\n", "\n")
    assert regenerated == on_disk, (
        "c/src/srmech_responsion_registry.c is out of date — regenerate with "
        "c/tools/gen_responsion_registry.py > "
        "c/src/srmech_responsion_registry.c"
    )


def test_generated_table_is_pure_ascii() -> None:
    data = _C_SRC.read_bytes()
    non_ascii = [i for i, b in enumerate(data) if b > 0x7F]
    assert not non_ascii, (
        f"srmech_responsion_registry.c has {len(non_ascii)} non-ASCII "
        f"byte(s) — the codegen must emit ASCII-only source (MSVC-safe)"
    )


def test_generated_table_holds_every_edge() -> None:
    text = _C_SRC.read_text(encoding="utf-8")
    for key in _pure_responsion_schema():
        assert f'"{key}"' in text, (
            f"edge {key!r} is missing from srmech_responsion_registry.c — "
            f"regenerate"
        )


# ── 7. registration ───────────────────────────────────────────────────────────

def test_tool_entry_registered_and_total_matches_live() -> None:
    schema = get_tool_schema()
    entry = schema.lookup("srmech.introspect.responsion_schema.responsion_schema")
    assert entry is not None
    assert entry.category == "responsion_schema"
    assert "k=3" in entry.summary
    assert "EDGE" in entry.summary
    assert len(schema.tools) == 687


def test_rosetta_row_is_composes_c() -> None:
    fixture = _HERE / "rosetta_classification.ndjson"
    rows = [json.loads(l) for l in
            fixture.read_text(encoding="utf-8").splitlines() if l.strip()]
    row = [r for r in rows
           if r["defined_at"]
           == "srmech.introspect.responsion_schema.responsion_schema"]
    assert len(row) == 1
    assert row[0]["bucket"] == "non_compute"
    assert row[0]["non_compute_kind"] == "composes_c"


def test_describe_total_matches_live() -> None:
    from srmech import introspect

    assert introspect.describe()["tools"]["total"] == 687


def test_within_edge_order_is_deterministic() -> None:
    """The within-edge list order is (kind, status, answers_with) — the
    canonical payload never depends on authored-tuple ordering."""
    for responsions in _pure_responsion_schema().values():
        keyed = [(r["kind"], r["status"], r["answers_with"])
                 for r in responsions]
        assert keyed == sorted(keyed)


def test_continuous_edges_are_authored_consistently() -> None:
    """Belt-and-braces: the authored continuous tuples all target the Mat
    generator today (the response family acts on L; the excitation u0 is the
    query, per the module docstring)."""
    for _op, carrier, kind, _answers in _CONTINUOUS_VERIFIED:
        assert carrier == "Mat"
        assert kind in ("propagator", "resolvent", "trace", "response_curve")
