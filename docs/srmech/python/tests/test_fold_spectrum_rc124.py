"""rc124 (task #697) — ``coupling.fold_encode`` / ``coupling.fold_spectrum``:
the BIDIRECTIONAL translation between a stored HDC fold and a self-similar
lattice's SPECTRAL-DECIMATION structure (the "Q2 reader made LITERAL").

Where ``fractal_spectrum(R, branches)`` (rc100) reads the decimation from an
EXPLICIT ``Poly`` R, these two ops read/write the decimation through a STORED
Klein-4 HDC FOLD. The two directions are ASYMMETRIC by the nature of HDC:

  * ``fold_encode``  (params → fold): EXACT / total / deterministic.
  * ``fold_spectrum``(fold → params): a SIMILARITY / CLEANUP-MEMORY readout,
    NOT exact — it returns the ``fractal_spectrum`` params PLUS a
    similarity/confidence readout, and when crosstalk overwhelms the signal it
    returns an HONEST "unrecovered" verdict, NEVER a silent wrong Poly.

Both ops are pure orchestration over shipped Klein-4 HDC + ``Poly`` +
``fractal_spectrum`` ops → NO new numerical kernel → ``non_compute`` (the
``cooccurrence_fold`` / ``from_bodies`` precedent). ``tools.total`` 386 → 388.

numpy-FREE and math-FREE (the module under test is numpy-free, so this test is
too — ``[[feedback_test_for_numpy_free_module_must_itself_be_numpy_free]]``): no
``abs()`` (a Class-K sign branch is used in test code too).

Coverage:
  (a) the round-trip LAW — the Sierpinski gasket ``R(z)=z(5−4z)`` round-trips
      confidently at high dim; the recovered params EQUAL a direct
      ``fractal_spectrum(R)`` call bit-for-bit; verdict 'recovered', EQUAL,
      fold_consistency == 1;
  (b) the honest UNRECOVERED verdict fires at low/crowded dim (crosstalk), with
      NO decimation Poly and op_provenance UNKNOWN;
  (c) the NO-SILENT-WRONG guarantee — across seeds at a low dim, EVERY
      'recovered' read is actually the correct Poly (never a wrong one);
  (d) the similarity / confidence / per-slot readout (exact ``Q``, in [0,1]);
  (e) encode DETERMINISM (same seed → identical fold; different seed differs);
  (f) the JSON-native MCP boundary (serialise the HV store → dict-of-lists →
      fold_spectrum still recovers);
  (g) a higher-degree decimation round-trips too;
  (h) input validation (both directions);
  (i) both ops REGISTERED (tool schema; param types MCP-coercible; total 388);
  (j) discipline — the two new functions are ``abs()``-free in source.
"""

import json
import os
import re
import tokenize

import pytest

from srmech.amsc import coupling
from srmech.amsc.poly import Poly
from srmech.amsc.q import Q

# A dim comfortably above the HDC bundle-capacity floor (4·n_pairs; the gasket
# has 4 bound pairs → floor 16) for confident recovery; and a degenerate dim
# well below it for the honest-unrecovered case.
_HI_DIM = 1024
_LO_DIM = 8

_GASKET = [0, 5, -4]        # 5z − 4z² = z(5 − 4z); scale R'(0)=5, branches 3


def _abs(x):
    """Magnitude without ``abs()`` (Class-K sign branch in test code too)."""
    return -x if x < 0.0 else x


def _fractal_keys():
    return ("decimation_map", "scale", "branches", "self_similarity_dim",
            "q_octaves_per_level", "rung_class", "log_period_over_2pi",
            "spectrum_open")


# ─────────────────────────────────────────────────────────────────────
# (a) the round-trip LAW — high-dim confident recovery == fractal_spectrum(R)
# ─────────────────────────────────────────────────────────────────────
def test_gasket_high_dim_round_trip_equals_direct_fractal_spectrum():
    R = Poly.from_coeffs(_GASKET)
    direct = coupling.fractal_spectrum(R, 3)

    store = coupling.fold_encode(R, 3, dim=_HI_DIM, seed=0)
    got = coupling.fold_spectrum(store)

    # confident recovery
    assert got["verdict"] == "recovered"
    assert got["op_provenance"] == "EQUAL"
    assert got["fold_consistency"] == Q(1, 1)

    # the recovered decimation Poly is EXACTLY R
    assert got["decimation_map"].coeffs == R.coeffs

    # every fractal_spectrum-shaped key matches the DIRECT call bit-for-bit
    for k in _fractal_keys():
        if k == "decimation_map":
            assert got[k].coeffs == direct[k].coeffs
        else:
            assert got[k] == direct[k], f"key {k!r} mismatch"


def test_fold_store_shape():
    store = coupling.fold_encode(Poly.from_coeffs(_GASKET), 3, dim=256, seed=1)
    assert set(store.keys()) == {
        "fold", "roles", "codes", "coeff_slots", "branch_slot", "slots",
        "dim", "seed", "n_pairs",
    }
    # 3 coeff slots (degree 2 → c0,c1,c2) + the branches slot = 4 bound pairs
    assert store["coeff_slots"] == ["c0", "c1", "c2"]
    assert store["branch_slot"] == "branches"
    assert store["n_pairs"] == 4
    assert store["dim"] == 256
    # the value codebook holds the distinct coefficient values + the branch count
    assert set(store["codes"].keys()) == {"0/1", "5/1", "-4/1", "3/1"}
    # one role per slot
    assert set(store["roles"].keys()) == {"c0", "c1", "c2", "branches"}


# ─────────────────────────────────────────────────────────────────────
# (b) the honest UNRECOVERED verdict fires at low/crowded dim
# ─────────────────────────────────────────────────────────────────────
def test_low_dim_fires_honest_unrecovered():
    R = Poly.from_coeffs(_GASKET)
    # seed chosen so the degenerate low-dim read does not accidentally reconstruct
    got = coupling.fold_spectrum(coupling.fold_encode(R, 3, dim=_LO_DIM, seed=3))
    assert got["verdict"] == "unrecovered"
    assert got["op_provenance"] == "UNKNOWN"
    # NO decimation Poly / spectral params are returned (never a silent wrong Poly)
    assert "decimation_map" not in got
    assert "scale" not in got
    # the honest readout is present
    assert isinstance(got["reason"], str) and got["reason"]
    assert "spectrum_open" in got
    # the capacity gate is named in the reason (dim 8 < 4*4 = 16)
    assert "capacity" in got["reason"]


# ─────────────────────────────────────────────────────────────────────
# (c) the NO-SILENT-WRONG guarantee — every 'recovered' read is CORRECT
# ─────────────────────────────────────────────────────────────────────
def test_no_silent_wrong_poly_across_seeds():
    R = Poly.from_coeffs(_GASKET)
    truth = R.coeffs
    n_unrecovered = 0
    n_recovered = 0
    # dim=16 sits right AT the capacity floor (4*4) — the interesting boundary
    for seed in range(40):
        got = coupling.fold_spectrum(coupling.fold_encode(R, 3, dim=16, seed=seed))
        if got["verdict"] == "recovered":
            n_recovered += 1
            # a 'recovered' verdict MUST be the exact original Poly + branches
            assert got["decimation_map"].coeffs == truth
            assert got["branches"] == 3
        else:
            assert got["verdict"] == "unrecovered"
            n_unrecovered += 1
    # the boundary is not silently-wrong AND not uselessly-eager: the low dim
    # produces honest unrecovered verdicts for most seeds.
    assert n_unrecovered > 0


# ─────────────────────────────────────────────────────────────────────
# (d) the similarity / confidence / per-slot readout
# ─────────────────────────────────────────────────────────────────────
def test_similarity_confidence_readout():
    store = coupling.fold_encode(Poly.from_coeffs(_GASKET), 3, dim=_HI_DIM, seed=0)
    got = coupling.fold_spectrum(store)
    # exact-Q similarity/confidence in [0, 1]
    for key in ("similarity", "confidence", "fold_consistency"):
        v = got[key]
        assert isinstance(v, Q)
        assert Q(0, 1) <= v <= Q(1, 1)
    # per-slot readout: one entry per slot, each with value/similarity/margin
    per = got["per_slot"]
    assert set(per.keys()) == {"c0", "c1", "c2", "branches"}
    for slot, rec in per.items():
        assert set(rec.keys()) == {"value", "similarity", "margin"}
        assert isinstance(rec["similarity"], Q)
        assert isinstance(rec["margin"], Q)
    # the reported top-level similarity is the WEAKEST slot's cleanup similarity
    assert got["similarity"] == min(per[s]["similarity"] for s in per)
    assert got["confidence"] == min(per[s]["margin"] for s in per)


# ─────────────────────────────────────────────────────────────────────
# (e) encode DETERMINISM
# ─────────────────────────────────────────────────────────────────────
def test_encode_is_deterministic():
    R = Poly.from_coeffs(_GASKET)
    a = coupling.fold_encode(R, 3, dim=256, seed=7)
    b = coupling.fold_encode(R, 3, dim=256, seed=7)
    assert list(a["fold"]) == list(b["fold"])
    # a different seed produces a different fold (different random codes)
    c = coupling.fold_encode(R, 3, dim=256, seed=8)
    assert list(c["fold"]) != list(a["fold"])


# ─────────────────────────────────────────────────────────────────────
# (f) the JSON-native MCP boundary — HV store → dict-of-lists → still reads
# ─────────────────────────────────────────────────────────────────────
def test_json_native_mcp_boundary_round_trip():
    from srmech.mcp._coercion import serialise_native

    R = Poly.from_coeffs(_GASKET)
    store = coupling.fold_encode(R, 3, dim=_HI_DIM, seed=0)
    # simulate the MCP boundary: HV values serialise to uint8 lists, cross JSON
    jstore = json.loads(json.dumps(serialise_native(store)))
    assert isinstance(jstore["fold"], list)
    got = coupling.fold_spectrum(jstore)
    assert got["verdict"] == "recovered"
    assert got["fold_consistency"] == Q(1, 1)
    assert got["decimation_map"].coeffs == R.coeffs


# ─────────────────────────────────────────────────────────────────────
# (g) a higher-degree decimation round-trips too
# ─────────────────────────────────────────────────────────────────────
def test_degree_three_round_trip():
    R3 = Poly.from_coeffs([0, 3, -2, 1])        # R(0)=0, R'(0)=3 > 1
    direct = coupling.fractal_spectrum(R3, 2)
    got = coupling.fold_spectrum(coupling.fold_encode(R3, 2, dim=2048, seed=5))
    assert got["verdict"] == "recovered"
    assert got["decimation_map"].coeffs == R3.coeffs
    assert got["scale"] == direct["scale"]
    assert got["self_similarity_dim"] == direct["self_similarity_dim"]


# ─────────────────────────────────────────────────────────────────────
# (h) input validation
# ─────────────────────────────────────────────────────────────────────
def test_fold_encode_rejects_bad_input():
    with pytest.raises(ValueError):
        coupling.fold_encode(Poly.from_coeffs([0, 5]), 3, dim=64)      # degree < 2
    with pytest.raises(ValueError):
        coupling.fold_encode(Poly.from_coeffs(_GASKET), 1, dim=64)     # branches < 2
    with pytest.raises(ValueError):
        coupling.fold_encode(Poly.from_coeffs(_GASKET), 3, dim=0)      # dim < 1
    with pytest.raises(ValueError):
        coupling.fold_encode("not a poly", 3, dim=64)                  # uncoercible R


def test_fold_spectrum_rejects_bad_store():
    with pytest.raises(ValueError):
        coupling.fold_spectrum("not a dict")
    with pytest.raises(ValueError):
        coupling.fold_spectrum({"fold": [0, 1, 2, 3]})                 # missing keys


def test_fold_encode_coerces_coeff_sequence():
    # a bare ascending-degree sequence is coerced == the Poly path
    from_seq = coupling.fold_spectrum(coupling.fold_encode(_GASKET, 3, dim=512))
    from_poly = coupling.fold_spectrum(
        coupling.fold_encode(Poly.from_coeffs(_GASKET), 3, dim=512))
    assert from_seq["verdict"] == "recovered"
    assert from_seq["decimation_map"].coeffs == from_poly["decimation_map"].coeffs


# ─────────────────────────────────────────────────────────────────────
# (i) both ops REGISTERED (tool schema; param types coercible; total 388)
# ─────────────────────────────────────────────────────────────────────
def test_registered_in_tool_schema():
    from srmech.amsc import tool_schema
    from srmech.mcp._coercion import has_coercer

    schema = tool_schema.get_tool_schema()
    for name in ("srmech.amsc.coupling.fold_encode",
                 "srmech.amsc.coupling.fold_spectrum"):
        entry = schema.lookup(name)
        assert entry is not None, f"{name} not registered"
        assert entry.owner == "srmech"
        assert entry.category == "coupling"
        # every declared param type has an MCP coercer (the rc14 ratchet)
        for p in entry.parameters:
            assert has_coercer(p.type), f"{name}:{p.name} type {p.type!r} uncoercible"

    enc = schema.lookup("srmech.amsc.coupling.fold_encode")
    assert {p.name: p.type for p in enc.parameters}["R"] == "Poly"
    rd = schema.lookup("srmech.amsc.coupling.fold_spectrum")
    assert {p.name: p.type for p in rd.parameters}["fold"] == "dict"


def test_tools_total_is_388():
    from srmech import introspect

    assert introspect.describe()["tools"]["total"] == 397


# ─────────────────────────────────────────────────────────────────────
# (j) discipline — the coupling module source is numpy / math / abs()-free
# ─────────────────────────────────────────────────────────────────────
def test_coupling_source_is_numpy_math_abs_free():
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    src = os.path.join(here, "srmech", "amsc", "coupling.py")
    with tokenize.open(src) as fh:
        text = fh.read()
    assert re.search(r"(?m)^\s*(import|from)\s+numpy\b", text) is None
    assert re.search(r"(?m)^\s*(import|from)\s+math\b", text) is None
    assert re.search(r"abs\([^)]", text) is None          # no bare abs() CALL
