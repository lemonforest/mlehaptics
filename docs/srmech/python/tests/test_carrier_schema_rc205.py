"""rc205 (gh #1293) — carrier_schema: the CARRIER (operand) introspection
surface, the noun-side DUAL of tool_schema.

Pins:

  1. **Shape + authored metadata.** Every carrier entry carries the gh #1293
     fields (name / one-line description / ladder / rung / variables / ops);
     the descriptions genuinely DIFFERENTIATE carriers that differ only by a
     rung number (the Siona finding: Poly vs BiPoly vs TriPoly).
  2. **Descriptor consistency.** ladder/rung agree with the rc116/rc120
     carrier_ladder_descriptor() (the thin surface this enriches), including
     the Cayley-Dickson R/C/H/O/S dims surfacing as float/complex/quaternion/
     octonion/sedenion.
  3. **The DERIVED ops back-index.** Known consume/produce relations hold
     (gosper consumes Poly; apagodu_zeilberger consumes TriPoly; the qm
     octonion family + cd_* index under octonion via the rc120 contract);
     every back-index name resolves in the live tool schema.
  4. **The hash-ratchet (THE gate).** The C `srmech_carrier_schema` assembler
     over the compiled-in `srmech_carrier_registry` const table emits bytes
     BYTE-IDENTICAL to the Python SSoT pre-image
     ``json.dumps(_pure_carrier_schema(), sort_keys=True,
     separators=(",", ":"))`` — same sha256. If a carrier / description / a
     new op joins Python-side without regenerating the C table, this fails.
  5. **Codegen idempotence + purity.** Re-running gen_carrier_registry.py
     reproduces the checked-in .c exactly (drift catcher); the generated
     file is pure ASCII (MSVC-safe).
  6. **Registration.** The ToolEntry exists; tools.total == 418; the Rosetta
     row is composes_c (CEIL_NON_COMPUTE_OWED untouched at 0).
  7. **The carrier-coverage drift ratchet.** Every srmech carrier-class token
     appearing in a ToolEntry type string is either IN the registry or on the
     explicit non-carrier infra allowlist — a future carrier cannot ship
     un-introspectable.

The native-requiring assertions ``skipif`` cleanly when the rc205 C peer is
absent (pure / stale-lib host). numpy-free (imports only srmech + stdlib).
"""

from __future__ import annotations

import importlib.util
import json
import re
from pathlib import Path

import pytest

from srmech.amsc import _native
from srmech.amsc.carrier_ladder import carrier_ladder_descriptor
from srmech.amsc.carrier_schema import (
    _CARRIERS,
    _LADDER_RUNG_CARRIERS,
    _pure_carrier_schema,
    carrier_schema,
)
from srmech.amsc.tool_schema import get_tool_schema, warmup_all

warmup_all()

_HERE = Path(__file__).resolve().parent
_C_SRC = _HERE.parent.parent / "c" / "src" / "srmech_carrier_registry.c"
_CODEGEN = _HERE.parent.parent / "c" / "tools" / "gen_carrier_registry.py"

_needs_native = pytest.mark.skipif(
    not _native.has_native_carrier_schema(),
    reason="rc205 carrier-registry C peer not loaded (pure / stale host)",
)

# Non-carrier identifiers that legitimately appear in ToolEntry type strings
# (typing / infra / handle types — NOT operand carriers). The drift ratchet
# below allows exactly these; anything else capitalized that names a srmech
# class must join the carrier registry.
_NON_CARRIER_TYPE_TOKENS = frozenset({
    "Any", "Callable", "Iterator", "Mapping", "None", "Optional", "Path",
    "Sequence",
    "I",                 # array('I') typecode, not a type name
    "ChainSpec",         # compose chain-spec IR (orchestration, not operand)
    "Endpoint",          # bus endpoint handle
    "MPRRecord",         # provenance record envelope
    "RecoverableFold",   # coupling pair-carrier handle (in-process only)
    "Run",               # typing artifact of "Runnable"-style summaries
    "SpectralHandle",    # by-reference spectral handle (rc16 envelope)
})


def _canonical_payload() -> bytes:
    """The Python SSoT canonical pre-image (compact, sorted keys, default
    ensure_ascii=True) the C table is hash-ratcheted against."""
    return json.dumps(
        _pure_carrier_schema(), sort_keys=True, separators=(",", ":")
    ).encode("utf-8")


# ── 1. shape + authored metadata ──────────────────────────────────────────────

def test_every_entry_has_the_gh1293_fields() -> None:
    schema = _pure_carrier_schema()
    assert len(schema) == len(_CARRIERS)
    for name, entry in schema.items():
        assert entry["name"] == name
        assert isinstance(entry["description"], str) and entry["description"]
        assert entry["ladder"] is None or isinstance(entry["ladder"], str)
        assert entry["rung"] is None or isinstance(entry["rung"], int)
        assert (entry["ladder"] is None) == (entry["rung"] is None)
        assert isinstance(entry["variables"], list)
        ops = entry["ops"]
        assert set(ops) == {"consumes", "produces"}
        assert ops["consumes"] == sorted(set(ops["consumes"]))
        assert ops["produces"] == sorted(set(ops["produces"]))


def test_descriptions_differentiate_the_poly_ladder() -> None:
    """The Siona finding: Poly / BiPoly / TriPoly must be distinguishable by
    more than a rung number — distinct descriptions, each naming its
    variables and its consuming engine."""
    schema = _pure_carrier_schema()
    descs = {n: schema[n]["description"] for n in ("Poly", "BiPoly", "TriPoly")}
    assert len(set(descs.values())) == 3
    assert "gosper" in descs["Poly"]
    assert "zeilberger" in descs["BiPoly"]
    assert "apagodu_zeilberger" in descs["TriPoly"]
    assert schema["Poly"]["variables"] == ["k"]
    assert schema["BiPoly"]["variables"] == ["n", "k"]
    assert schema["TriPoly"]["variables"] == ["n", "j", "k"]


def test_spot_check_carrier_entries() -> None:
    schema = _pure_carrier_schema()
    assert schema["TriPoly"]["ladder"] == "variable"
    assert schema["TriPoly"]["rung"] == 3
    assert schema["octonion"]["ladder"] == "cayley_dickson"
    assert schema["octonion"]["rung"] == 8
    assert "Hurwitz" in schema["octonion"]["description"]
    assert schema["Mat"]["ladder"] is None
    assert schema["Mat"]["rung"] is None
    assert "matrix" in schema["Mat"]["description"]
    assert schema["QBiPoly"]["variables"] == ["X=qⁿ", "Y=qᵏ"]


# ── 2. descriptor consistency (the surface this enriches) ────────────────────

def test_ladder_rungs_agree_with_carrier_ladder_descriptor() -> None:
    desc = carrier_ladder_descriptor()
    # The 5 variable-ladder carriers appear by NAME in the descriptor.
    for name, spec in desc["carriers"].items():
        entry = _pure_carrier_schema()[name]
        assert entry["ladder"] == spec["ladder"], name
        assert entry["rung"] == spec["rung"], name
    # Every ladder rung the descriptor declares has a carrier entry at the
    # SAME rung value (cayley_dickson dims surface under the value-carrier
    # names float/complex/quaternion/octonion/sedenion).
    schema = _pure_carrier_schema()
    for ladder, rung_map in _LADDER_RUNG_CARRIERS.items():
        declared = desc["ladders"][ladder]["rungs"]
        assert sorted(declared.values()) == sorted(rung_map), ladder
        for rung, carrier in rung_map.items():
            assert schema[carrier]["ladder"] == ladder
            assert schema[carrier]["rung"] == rung


# ── 3. the DERIVED ops back-index ─────────────────────────────────────────────

def test_ops_back_index_known_relations() -> None:
    schema = _pure_carrier_schema()
    assert "srmech.amsc.gosper.gosper" in schema["Poly"]["ops"]["consumes"]
    assert ("srmech.amsc.apagodu_zeilberger.apagodu_zeilberger"
            in schema["TriPoly"]["ops"]["consumes"])
    assert ("srmech.amsc.tripoly.tripoly_from_coeffs"
            in schema["TriPoly"]["ops"]["produces"])
    # The rc120 contract union: the CD ops' ToolEntry types say list[float] /
    # HV, but the contract indexes them under the rung carriers.
    assert ("srmech.qm.octonion.octonion_conjugate"
            in schema["octonion"]["ops"]["consumes"])
    assert ("srmech.qm.quaternion.quaternion_twiddle"
            in schema["quaternion"]["ops"]["produces"])
    assert ("srmech.amsc.cascade.cd_mult"
            in schema["sedenion"]["ops"]["consumes"])
    # Token derivation: Mat flows through the dense-LA surface.
    assert "srmech.amsc.laplacian.mat_matmul" in schema["Mat"]["ops"]["consumes"]
    assert "srmech.amsc.laplacian.mat_matmul" in schema["Mat"]["ops"]["produces"]
    # Word-boundary discipline: gosper takes Poly, NOT QPoly.
    assert ("srmech.amsc.gosper.gosper"
            not in schema["QPoly"]["ops"]["consumes"])


def test_ops_back_index_names_resolve_in_tool_schema() -> None:
    schema = _pure_carrier_schema()
    registered = {t.name for t in get_tool_schema().tools}
    for name, entry in schema.items():
        for side in ("consumes", "produces"):
            unknown = set(entry["ops"][side]) - registered
            assert not unknown, (
                f"{name}.ops.{side} names unregistered tools: {sorted(unknown)}"
            )


# ── 4. the hash-ratchet (native == pure, byte-identical) ─────────────────────

@_needs_native
def test_c_json_byte_identical_to_python_ssot() -> None:
    c_payload = _native.carrier_schema_json_c()
    assert c_payload is not None
    assert c_payload == _canonical_payload(), (
        "srmech_carrier_schema bytes differ from the Python SSoT — "
        "regenerate c/src/srmech_carrier_registry.c with "
        "c/tools/gen_carrier_registry.py"
    )


@_needs_native
def test_registry_count_and_names_round_trip() -> None:
    assert _native.carrier_registry_count_c() == len(_CARRIERS)
    names = _native.carrier_registry_names_c()
    assert names == sorted(_CARRIERS, key=lambda n: n.encode("utf-8"))


@_needs_native
def test_registry_find_first_class_fields() -> None:
    schema = _pure_carrier_schema()
    for probe in ("TriPoly", "octonion", "Mat"):
        found = _native.carrier_registry_find_c(probe)
        assert found is not None
        assert found["name"] == probe
        assert found["description"] == schema[probe]["description"]
        assert found["ladder"] == schema[probe]["ladder"]
        assert found["rung"] == (schema[probe]["rung"] or 0)
    assert _native.carrier_registry_find_c("NotACarrier") is None


@_needs_native
def test_dispatching_wrapper_equals_pure() -> None:
    """carrier_schema() (which routes native when available) is
    VALUE-identical to the pure derivation."""
    assert carrier_schema() == _pure_carrier_schema()


def test_wrapper_equals_pure_on_any_host() -> None:
    """On a pure host the wrapper IS the pure path; on a native host the
    ratchet above makes them equal — either way, value-identical."""
    assert carrier_schema() == _pure_carrier_schema()


# ── 5. codegen idempotence + purity (pure Python, always runs) ───────────────

def _load_codegen():
    spec = importlib.util.spec_from_file_location(
        "gen_carrier_registry_rc205", _CODEGEN)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_codegen_is_idempotent() -> None:
    """Re-running the generator reproduces the checked-in table exactly
    (line-ending normalised). If this fails, srmech_carrier_registry.c is
    stale — a carrier / description / back-index changed Python-side."""
    assert _C_SRC.exists(), f"missing generated table {_C_SRC}"
    assert _CODEGEN.exists(), f"missing codegen {_CODEGEN}"
    mod = _load_codegen()
    regenerated = mod.generate().replace("\r\n", "\n")
    on_disk = _C_SRC.read_text(encoding="utf-8").replace("\r\n", "\n")
    assert regenerated == on_disk, (
        "c/src/srmech_carrier_registry.c is out of date — regenerate with "
        "c/tools/gen_carrier_registry.py > c/src/srmech_carrier_registry.c"
    )


def test_generated_table_is_pure_ascii() -> None:
    data = _C_SRC.read_bytes()
    non_ascii = [i for i, b in enumerate(data) if b > 0x7F]
    assert not non_ascii, (
        f"srmech_carrier_registry.c has {len(non_ascii)} non-ASCII byte(s) — "
        f"the codegen must emit ASCII-only source (MSVC-safe)"
    )


def test_generated_table_holds_every_carrier() -> None:
    text = _C_SRC.read_text(encoding="utf-8")
    for name in _CARRIERS:
        assert f'"{name}"' in text, (
            f"carrier {name!r} is missing from srmech_carrier_registry.c — "
            f"regenerate"
        )


# ── 6. registration ───────────────────────────────────────────────────────────

def test_tool_entry_registered_and_total_matches_live() -> None:
    schema = get_tool_schema()
    entry = schema.lookup("srmech.amsc.carrier_schema.carrier_schema")
    assert entry is not None
    assert entry.category == "carrier_schema"
    assert "DUAL of tool_schema" in entry.summary
    assert len(schema.tools) == 492


def test_rosetta_row_is_composes_c() -> None:
    fixture = _HERE / "rosetta_classification.ndjson"
    rows = [json.loads(l) for l in
            fixture.read_text(encoding="utf-8").splitlines() if l.strip()]
    row = [r for r in rows
           if r["defined_at"] == "srmech.amsc.carrier_schema.carrier_schema"]
    assert len(row) == 1
    assert row[0]["bucket"] == "non_compute"
    assert row[0]["non_compute_kind"] == "composes_c"


# ── 7. the carrier-coverage drift ratchet ─────────────────────────────────────

def test_every_tool_type_carrier_token_is_registered() -> None:
    """Every capitalized srmech-class token in a ToolEntry type string is
    either a registered carrier or an allowlisted non-carrier infra type.
    A NEW carrier type surfacing on the op surface MUST join the carrier
    registry (with a real description) — it cannot ship un-introspectable
    (the gh #1293 regression guard)."""
    tokens: set = set()
    for tool in get_tool_schema().tools:
        types = [p.type for p in tool.parameters]
        if tool.returns is not None:
            types.append(tool.returns.type)
        for ty in types:
            for tok in re.findall(r"[A-Za-z_][A-Za-z0-9_]*", ty):
                if tok[0].isupper():
                    tokens.add(tok)
    unknown = tokens - set(_CARRIERS) - _NON_CARRIER_TYPE_TOKENS
    assert not unknown, (
        f"ToolEntry type strings name types absent from the carrier registry "
        f"and the non-carrier allowlist: {sorted(unknown)} — add each to "
        f"srmech.amsc.carrier_schema._CARRIERS (with a genuine description) "
        f"or, if it is NOT an operand carrier, to "
        f"_NON_CARRIER_TYPE_TOKENS here (with justification)"
    )
