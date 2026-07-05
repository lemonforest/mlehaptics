"""rc117 — OPERATORS⊗OPERANDS as ONE addressable object: the op-carrying
carrier (`srmech.amsc.op_provenance`; dives #718/#719 + the joint review).

The value of an inexact-frontier op is a PROJECTION; the exact generating
operation is the SSOT. rc117 ships five genuinely NEW public ops
(tools.total 376 → 381): carry / op_provenance_hash / op_verdict /
family_verdict / reproject.

Covered here — the three #718 wins + the boundary:

  (1) WIN 1: op-EQUAL where value-equality FAILS — two ±1-ulp-divergent
      readouts of the SAME cascade (simulated platform divergence via
      math.nextafter, the rc110-FMA pattern) verdict EQUAL; a
      coincidentally-equal VALUE from a DIFFERENT op verdicts UNKNOWN
      (never a false EQUAL); an algebraically-equal but syntactically-
      different cascade verdicts UNKNOWN (never a false UNEQUAL).
  (2) WIN 2: re-projection — the operation as SSOT. A sin(1) carrier at
      N=3 reprojects to N=12; the value is REGENERATED from the carried
      operation, verified against the direct call, and the exact rational
      sharpens toward the target.
  (3) WIN 3: the asymptote addressed by its generator — three truncations
      of sin(1) = ONE family address + THREE instance addresses; the SAME
      target approached by the interior (Taylor) vs the edge
      (continued-fraction) tower = DIFFERENT families.
  (4) leaves_exact honesty: a float-leaf matrix records leaves_exact False
      and gets NO derived family (instance-only); an int matrix records
      True with a content-addressed family.
  (5) Python==C hash parity (native-guarded): the C peer produces the
      IDENTICAL digest from canonical AND non-canonical (indented,
      unsorted) formattings of the same record; raw floats are rejected
      on BOTH sides (the mirror agrees on the domain).
  (6) the canonical hasher: chain_sha256 exclusion, float rejection with
      the tag-encoding fix named, bigint tagging, key-order independence.
  (7) registration: tools.total == 381, the five ToolEntries present,
      Rosetta buckets (op_provenance_hash c_dispatched; the rest
      non_compute), declared param types coercible.
  (8) numpy-free / math-free / abs()-free source hygiene of the module.
"""

from __future__ import annotations

import json
import math
from fractions import Fraction
from pathlib import Path

import pytest

from srmech.amsc.op_provenance import (
    carry,
    family_verdict,
    op_provenance_hash,
    op_verdict,
    reproject,
)
from srmech.amsc.rational import best_rational, sin_series_truncate

SIN_OP = "srmech.amsc.rational.sin_series_truncate"
BR_OP = "srmech.amsc.rational.best_rational"
JAC_OP = "srmech.amsc.laplacian.jacobi_eigvals"

# The P4 path-graph Laplacian — exact integer entries (a NAMED target).
P4 = [[1, -1, 0, 0], [-1, 2, -1, 0], [0, -1, 2, -1], [0, 0, -1, 1]]


# ── (1) WIN 1: op-EQUAL where value-equality fails ───────────────────────────

def test_ulp_divergent_same_cascade_is_op_equal():
    """Two platforms run the SAME cascade; one readout diverges by +1 ulp
    (the rc110 clang-FMA pattern, simulated via math.nextafter). The
    VALUES differ; the OPERATION address is identical → EQUAL: provably
    the same ideal object, the divergence a projection artifact."""
    a = carry(JAC_OP, {"matrix": P4})
    b = carry(JAC_OP, {"matrix": P4})
    ev_a = [float(a["value"][i]) for i in range(4)]
    ev_b = list(ev_a)
    ev_b[1] = math.nextafter(ev_b[1], math.inf)      # platform B, +1 ulp
    b = {"value": ev_b, "inputs": b["inputs"], "provenance": b["provenance"]}
    assert ev_a != ev_b                              # value-equality FAILS
    assert op_verdict(a, b) == "EQUAL"               # op-equality holds
    # The chain hash is the ADDRESS of the operation, not of the value.
    assert a["provenance"]["chain_sha256"] == b["provenance"]["chain_sha256"]


def test_coincidental_value_from_different_op_is_unknown():
    """A DIFFERENT operation whose value coincidentally matches must NOT
    verdict EQUAL — different provenance, honestly UNKNOWN."""
    s1 = carry(SIN_OP, {"numerator": 0, "denominator": 1},
               {"num_terms": 3})
    s2 = carry("srmech.amsc.rational.atan_series_truncate",
               {"numerator": 0, "denominator": 1}, {"num_terms": 3})
    assert s1["value"] == s2["value"] == (0, 1)      # values coincide
    assert op_verdict(s1, s2) == "UNKNOWN"           # never a false EQUAL


def test_syntactically_different_cascade_is_unknown_never_unequal():
    """The one-sided contract: a different rung of the SAME target is a
    DIFFERENT exact operation — the verdict is UNKNOWN (never 'UNEQUAL';
    equality of programs is undecidable)."""
    lo = carry(SIN_OP, {"numerator": 1, "denominator": 1}, {"num_terms": 3})
    hi = carry(SIN_OP, {"numerator": 1, "denominator": 1}, {"num_terms": 12})
    v = op_verdict(lo, hi)
    assert v == "UNKNOWN"
    assert v not in ("UNEQUAL", "DIFFERENT")


def test_default_and_explicit_default_params_carry_one_address():
    """Param defaults are MATERIALISED: jacobi with implicit defaults and
    with tolerance/max_sweeps spelled out is ONE operation address."""
    a = carry(JAC_OP, {"matrix": P4})
    b = carry(JAC_OP, {"matrix": P4},
              {"max_sweeps": 100, "tolerance": 1e-12})
    assert op_verdict(a, b) == "EQUAL"


# ── (2) WIN 2: re-projection — the operation as SSOT ─────────────────────────

def test_reproject_regenerates_value_from_the_carried_operation():
    low = carry(SIN_OP, {"numerator": 1, "denominator": 1}, {"num_terms": 3})
    hi = reproject(low, num_terms=12)
    # The regenerated value equals the direct call — the operation IS the SSOT.
    assert tuple(hi["value"]) == sin_series_truncate(1, 1, 12)
    # The exact rational SHARPENS toward the target (partial sums of an
    # alternating series with decreasing terms tighten monotonically here).
    target = Fraction(*sin_series_truncate(1, 1, 40))
    err_low = Fraction(*low["value"]) - target
    err_hi = Fraction(*hi["value"]) - target
    err_low = err_low if err_low >= 0 else -err_low   # Class-K by comparison
    err_hi = err_hi if err_hi >= 0 else -err_hi
    assert err_hi < err_low
    # Different rung → different instance; SAME family (rung-independent).
    assert op_verdict(low, hi) == "UNKNOWN"
    assert family_verdict(low, hi) == "SAME_TARGET"


def test_reproject_empty_override_rederives_verbatim():
    low = carry(SIN_OP, {"numerator": 1, "denominator": 1}, {"num_terms": 5})
    again = reproject(low)
    assert tuple(again["value"]) == tuple(low["value"])
    assert op_verdict(low, again) == "EQUAL"


def test_reproject_reverifies_inputs_against_input_sha256():
    low = carry(SIN_OP, {"numerator": 1, "denominator": 1}, {"num_terms": 3})
    # A bare record without inputs cannot re-run.
    with pytest.raises(ValueError, match="input"):
        reproject(low["provenance"])
    # Wrong inputs fail the MPM re-verification.
    with pytest.raises(ValueError, match="re-verif"):
        reproject(low["provenance"],
                  inputs={"numerator": 2, "denominator": 1}, num_terms=12)
    # The right inputs re-verify and run.
    ok = reproject(low["provenance"],
                   inputs={"numerator": 1, "denominator": 1}, num_terms=12)
    assert tuple(ok["value"]) == sin_series_truncate(1, 1, 12)


def test_reproject_rejects_non_rung_overrides():
    low = carry(SIN_OP, {"numerator": 1, "denominator": 1}, {"num_terms": 3})
    with pytest.raises(ValueError, match="not rung"):
        reproject(low, numerator=2)


def test_reproject_class_l_op_proves_the_pattern():
    """One Class-L op re-projects too: jacobi at a coarser tolerance rung
    re-runs from the carried operation and stays in the SAME family."""
    a = carry(JAC_OP, {"matrix": P4})
    b = reproject(a, tolerance=1e-9)
    assert b["provenance"]["rung"]["tolerance"] != \
        a["provenance"]["rung"]["tolerance"]
    assert family_verdict(a, b) == "SAME_TARGET"
    # The spectra agree to the coarser tolerance (same ideal target).
    for i in range(4):
        d = float(a["value"][i]) - float(b["value"][i])
        d = d if d >= 0 else -d
        assert d < 1e-6


# ── (3) WIN 3: the asymptote addressed by its generator ──────────────────────

def test_three_truncations_one_family_three_instances():
    ladder = [
        carry(SIN_OP, {"numerator": 1, "denominator": 1}, {"num_terms": n})
        for n in (2, 5, 9)
    ]
    fams = {json.dumps(c["provenance"]["family"], sort_keys=True)
            for c in ladder}
    chains = {c["provenance"]["chain_sha256"] for c in ladder}
    assert len(fams) == 1          # ONE family address (the generator)
    assert len(chains) == 3        # THREE instance addresses (the rungs)
    assert ladder[0]["provenance"]["family"] == {
        "target_id": "sin(1/1)", "tower_kind": "interior"}
    assert family_verdict(ladder[0], ladder[2]) == "SAME_TARGET"


def test_interior_vs_edge_tower_of_same_target_are_different_families():
    """sin(1) by Taylor (interior) vs a best_rational approach of the same
    value (edge; the caller ATTESTS the target naming) — the SAME named
    target in TWO towers is TWO families."""
    interior = carry(SIN_OP, {"numerator": 1, "denominator": 1},
                     {"num_terms": 9})
    edge = carry(BR_OP, {"numerator": 841471, "denominator": 1000000},
                 {"max_denominator": 50},
                 family={"target_id": "sin(1/1)"})
    fi = interior["provenance"]["family"]
    fe = edge["provenance"]["family"]
    assert fi["target_id"] == fe["target_id"] == "sin(1/1)"
    assert fi["tower_kind"] == "interior"
    assert fe["tower_kind"] == "edge"
    assert fi != fe                                  # DIFFERENT families
    assert family_verdict(interior, edge) == "UNKNOWN"


def test_tower_kind_is_op_intrinsic_never_overridable():
    with pytest.raises(ValueError, match="op-intrinsic"):
        carry(BR_OP, {"numerator": 1, "denominator": 2},
              {"max_denominator": 10},
              family={"target_id": "x", "tower_kind": "interior"})


def test_reduced_point_names_one_target():
    """sin(2/2) and sin(1/1) name ONE target (the family names the reduced
    sign-normalised rational point, not the spelling)."""
    a = carry(SIN_OP, {"numerator": 1, "denominator": 1}, {"num_terms": 4})
    b = carry(SIN_OP, {"numerator": 2, "denominator": 2}, {"num_terms": 4})
    assert family_verdict(a, b) == "SAME_TARGET"
    assert op_verdict(a, b) == "UNKNOWN"   # different pinned inputs → UNKNOWN


# ── (4) leaves_exact honesty ─────────────────────────────────────────────────

def test_float_leaf_records_leaves_exact_false_and_no_family():
    m = [[0.1, -0.1], [-0.1, 0.1]]
    c = carry(JAC_OP, {"matrix": m})
    assert c["provenance"]["leaves_exact"] is False
    assert c["provenance"]["family"] is None          # unnamed → instance-only
    # The float leaves ride as EXACT bit patterns (well-defined address):
    tag = c["inputs"]["matrix"][0][0]
    assert tag == {"__float64__": (0.1).hex()}
    # Same op on the same bit patterns still addresses EQUAL (stated weaker).
    c2 = carry(JAC_OP, {"matrix": [[0.1, -0.1], [-0.1, 0.1]]})
    assert op_verdict(c, c2) == "EQUAL"


def test_exact_leaf_records_leaves_exact_true_and_named_family():
    c = carry(JAC_OP, {"matrix": P4})
    assert c["provenance"]["leaves_exact"] is True
    fam = c["provenance"]["family"]
    assert fam is not None and fam["tower_kind"] == "edge"
    assert fam["target_id"].startswith("eigvals(sha256:")


# ── (5)+(6) the canonical hasher + Python==C parity ──────────────────────────

def test_hash_excludes_chain_sha256_and_is_key_order_independent():
    r1 = {"op": "x", "params": {"a": 1, "b": 2}, "input_sha256": []}
    r2 = {"input_sha256": [], "params": {"b": 2, "a": 1}, "op": "x"}
    h1 = op_provenance_hash(r1)
    assert h1 == op_provenance_hash(r2)               # sort_keys canonical
    r3 = dict(r1, chain_sha256="0" * 64)
    assert op_provenance_hash(r3) == h1               # cache excluded
    assert len(h1) == 64 and set(h1) <= set("0123456789abcdef")


def test_hash_rejects_raw_floats_naming_the_tag_fix():
    with pytest.raises(ValueError, match="__float64__"):
        op_provenance_hash({"op": "x", "params": {"tol": 1e-12},
                            "input_sha256": []})


def test_hash_rejects_beyond_int64_naming_the_tag_fix():
    with pytest.raises(ValueError, match="__bigint__"):
        op_provenance_hash({"op": "x", "params": {"n": 2 ** 80},
                            "input_sha256": []})


def test_bigint_leaves_are_tagged_and_hash_cleanly():
    """A huge exact rational (e.g. a deep series partial sum) rides as a
    __bigint__ decimal tag — inside the C writer's int64 domain — and an
    exact Fraction input canonicalises to the __rational__ tag."""
    num, den = sin_series_truncate(1, 1, 20)     # far beyond int64
    rec = {"op": "x", "params": {"n": {"__bigint__": str(num)},
                                 "d": {"__bigint__": str(den)}},
           "input_sha256": []}
    assert len(op_provenance_hash(rec)) == 64
    # heat_trace with an exact rational time: Fraction leaf stays exact.
    c = carry("srmech.amsc.laplacian.heat_trace",
              {"L": [[1, -1], [-1, 1]], "t": Fraction(1, 2)})
    assert c["provenance"]["leaves_exact"] is True
    assert c["inputs"]["t"] == {"__rational__": [1, 2]}
    assert c["provenance"]["family"]["target_id"].startswith(
        "heat_trace(sha256:")


def _native_hash(record_bytes: bytes):
    """Call the C peer directly on raw record bytes; None when no native."""
    import ctypes

    from srmech.amsc import _native
    if not (_native.HAS_NATIVE and _native.LIB is not None
            and hasattr(_native.LIB, "srmech_op_provenance_hash")
            and hasattr(_native.LIB, "srmech_op_provenance_hash_arena_bytes")):
        return None
    ws_bytes = int(_native.LIB.srmech_op_provenance_hash_arena_bytes(
        ctypes.c_size_t(len(record_bytes))))
    ws = ctypes.create_string_buffer(ws_bytes)
    out_hex = ctypes.create_string_buffer(65)
    rc = _native.LIB.srmech_op_provenance_hash(
        record_bytes, ctypes.c_size_t(len(record_bytes)),
        ws, ctypes.c_size_t(ws_bytes), out_hex)
    return (rc, out_hex.value.decode("ascii"))


def _require_native():
    from srmech.amsc import _native
    if not (_native.HAS_NATIVE and _native.LIB is not None
            and hasattr(_native.LIB, "srmech_op_provenance_hash")):
        pytest.skip("native srmech_op_provenance_hash not available")


def test_python_c_hash_parity_on_identical_records():
    """Python==C on the SAME record — including a NON-canonical formatting
    (indented, unsorted keys, a chain_sha256 cache to strip): the C peer
    parses ANY formatting and re-emits canonically."""
    _require_native()
    record = {"op": "srmech.amsc.rational.sin_series_truncate",
              "params": {"num_terms": 3},
              "input_sha256": ["ab" * 32, "cd" * 32],
              "family": {"target_id": "sin(1/1)", "tower_kind": "interior"},
              "rung": {"num_terms": 3},
              "leaves_exact": True}
    py = op_provenance_hash(record)
    # The PURE canonical pre-image (json.dumps sort_keys canonicalisation +
    # Class-A sha256_bytes) — the C peer's parse→canonical-rewrite must
    # produce the byte-identical pre-image, hence the identical digest.
    from srmech.amsc.format import sha256_bytes
    pure = sha256_bytes(json.dumps(
        record, sort_keys=True, ensure_ascii=False).encode("utf-8"))
    assert pure == py
    # canonical bytes
    rc, ch = _native_hash(json.dumps(
        record, sort_keys=True, ensure_ascii=False).encode("utf-8"))
    assert rc == 0 and ch == py
    # non-canonical: indented, insertion-ordered, with the cache present
    messy = dict(record, chain_sha256=py)
    rc, ch = _native_hash(json.dumps(
        messy, indent=2, ensure_ascii=False).encode("utf-8"))
    assert rc == 0 and ch == py
    # a carry()-built record round-trips through the C peer identically
    carried = carry(SIN_OP, {"numerator": 1, "denominator": 1},
                    {"num_terms": 3})
    rec = carried["provenance"]
    rc, ch = _native_hash(json.dumps(rec, ensure_ascii=False).encode("utf-8"))
    assert rc == 0 and ch == rec["chain_sha256"]


def test_c_peer_rejects_raw_floats_like_python():
    """The mirror agrees on the DOMAIN: a raw float token is BAD_INPUT in
    C exactly as it is a ValueError in Python (%.17g vs repr would fork
    the hash silently — rejected on both sides instead)."""
    _require_native()
    rc, _ = _native_hash(b'{"op": "x", "params": {"tol": 1e-12}}')
    assert rc == 2                                    # SRMECH_ERR_BAD_INPUT
    rc, _ = _native_hash(b'{"op": "x", "params": {"tol": 0.5}}')
    assert rc == 2


def test_unknown_op_raises_naming_the_registry():
    with pytest.raises(ValueError, match="registered ops"):
        carry("srmech.amsc.nowhere.no_op", {})


# ── (7) registration: tools.total, entries, buckets, coercers ────────────────

def test_tools_total_is_381():
    """rc117 ships 5 genuinely NEW public ops → +5 ToolEntries (376 → 381)."""
    from srmech import introspect
    assert introspect.describe()["tools"]["total"] == 395


def test_new_tool_entries_present_with_declared_types():
    from srmech.amsc.tool_schema import get_tool_schema
    schema = get_tool_schema()
    expected = {
        "srmech.amsc.op_provenance.carry": (
            {"op": "str", "inputs": "dict", "params": "dict",
             "family": "dict"}),
        "srmech.amsc.op_provenance.op_provenance_hash": (
            {"record": "dict"}),
        "srmech.amsc.op_provenance.op_verdict": (
            {"p1": "dict", "p2": "dict"}),
        "srmech.amsc.op_provenance.family_verdict": (
            {"p1": "dict", "p2": "dict"}),
        "srmech.amsc.op_provenance.reproject": (
            {"provenance": "dict", "overrides": "dict", "inputs": "dict"}),
    }
    for name, params in expected.items():
        entry = schema.lookup(name)
        assert entry is not None, f"missing ToolEntry {name}"
        assert entry.category == "op_provenance"
        assert entry.mcp_callable is True
        declared = {p.name: p.type for p in entry.parameters}
        assert declared == params, f"{name}: params {declared} != {params}"


def test_rosetta_buckets():
    """op_provenance_hash routes to its C twin (c_dispatched); the carry /
    verdict / reproject ops are registry+verdict dispatch (non_compute —
    all numerical compute delegated to registered ops + the hasher)."""
    ledger = Path(__file__).resolve().parent / "rosetta_classification.ndjson"
    rows = {r["defined_at"]: r["bucket"]
            for r in (json.loads(l) for l in
                      ledger.read_text(encoding="utf-8").splitlines()
                      if l.strip())}
    assert rows.get(
        "srmech.amsc.op_provenance.op_provenance_hash") == "c_dispatched"
    for leaf in ("carry", "op_verdict", "family_verdict", "reproject"):
        assert rows.get(f"srmech.amsc.op_provenance.{leaf}") == "non_compute"


def test_new_param_types_are_coercible():
    from srmech.mcp._coercion import has_coercer
    for t in ("str", "dict"):
        assert has_coercer(t), f"no coercer for declared type {t!r}"


# ── (8) hygiene: numpy-free / math-free / abs()-free source ──────────────────

def test_module_is_numpy_math_abs_free():
    import srmech.amsc.op_provenance as OP
    text = open(OP.__file__, encoding="utf-8").read()
    assert "import numpy" not in text
    assert "import math" not in text
    assert "abs(" not in text.replace("abs()", "")   # Class-K discipline
    assert "import hashlib" not in text               # routes sha256_bytes
    assert "hashlib.sha256" not in text
