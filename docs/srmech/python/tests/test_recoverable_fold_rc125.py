"""rc125 (task #723) — the RECOVERABLE FOLD as a HarmonicMaass-style PAIR
carrier: ``coupling.RecoverableFold`` + ``coupling.fold_encode_recoverable`` +
``coupling.fold_identity`` + ``op_provenance.lossy_projection_record``.

rc124 shipped ``fold_encode`` (EXACT) + ``fold_spectrum`` (a similarity/cleanup
read, exact WHEN the fold has capacity, honest-``unrecovered`` below the
``dim >= 4·n_pairs`` floor). rc125 makes recovery EXACT at ANY dim by ATTACHING
the exact complement (the generating decimation ``R``) — the field–excitation
recoverability principle: a lossy projection is recoverable iff you attach the
exact complement it dropped. The pair MIRRORS
``srmech.amsc.harmonic_maass.HarmonicMaass(hol, shadow)`` (rc71):
``lossy_bundle ↔ hol``, ``exact_seed_R ↔ shadow`` — "storing R IS storing the
recovery" (as "storing the shadow IS storing the completion").

numpy-FREE and math-FREE (the module under test is numpy-free, so this test is
too — ``[[feedback_test_for_numpy_free_module_must_itself_be_numpy_free]]``): no
``abs()``.

Coverage:
  (a) THE HEADLINE — exact recovery at ANY dim via the carried seed: at
      ``dim=8`` (< the 4·n_pairs=16 gasket floor, where the rc124 BARE read
      returns honest-``unrecovered``) the pair recovers R EXACTLY, ==
      ``fractal_spectrum(R)`` bit-for-bit; verdict 'recovered', EQUAL,
      recovery 'exact-seed', fold_consistency == 1;
  (b) the fold-IDENTITY verdict — EQUAL (same R, different dim) / NOT_EQUAL
      (different R) / UNKNOWN (a bare seed-less fold on either side; never a
      false verdict from a lossy bundle);
  (c) the rc124 BARE fallback — a seed-less RecoverableFold reads via the
      rc124 similarity path (recovered at high dim, honest-``unrecovered`` at
      low dim), UNCHANGED;
  (d) the HarmonicMaass-shape mirror — the (lossy_bundle, exact_seed_R) pair,
      .has_seed, .complement() ↔ xi(), immutability;
  (e) determinism — same (R, branches, dim, seed) → identical pair + identity;
  (f) the op_provenance registration — lossy_projection_record: family=None,
      rung={}, projection_kind='hdc', leaves_exact True; scope-widened;
  (g) registration + counts — tools.total == 394, the two ToolEntries present,
      fold_identity is NOT a ToolEntry (carrier-param exempt), both rosetta
      rows non_compute, param types coercible;
  (h) discipline — the coupling / op_provenance sources stay abs()-free.
"""

import os
import re
import tokenize

import pytest

from srmech.amsc import coupling
from srmech.amsc import op_provenance
from srmech.amsc.coupling import (
    RecoverableFold,
    fold_encode,
    fold_encode_recoverable,
    fold_identity,
    fold_spectrum,
    fractal_spectrum,
)
from srmech.amsc.poly import Poly
from srmech.amsc.q import Q

# The Sierpinski gasket decimation R(z)=z(5−4z): 4 bound pairs → capacity floor
# 4·4 = 16, so dim=8 is BELOW it (the rc124 bare read fails there).
_GASKET = [0, 5, -4]          # 5z − 4z² ; scale R'(0)=5, branches 3
_OTHER = [0, 3, -2]           # 3z − 2z² ; a DIFFERENT decimation
_LO_DIM = 8                   # < 4·n_pairs = 16 → bare rc124 fails here
_HI_DIM = 1024                # comfortably above the floor

# The full fractal_spectrum key-set the exact recovery must reproduce.
_FS_KEYS = ("decimation_map", "scale", "branches", "self_similarity_dim",
            "q_octaves_per_level", "rung_class", "log_period_over_2pi",
            "spectrum_open")


def _fs_equal(a, b) -> bool:
    """Bit-for-bit equality of two fractal_spectrum dicts over the FS keys (the
    decimation_map is a Poly compared by its exact coeffs)."""
    for k in _FS_KEYS:
        if k == "decimation_map":
            if a[k].coeffs != b[k].coeffs:
                return False
        elif a[k] != b[k]:
            return False
    return True


# ─────────────────────────────────────────────────────────────────────
# (a) THE HEADLINE — exact recovery at ANY dim (dim=8) via the carried seed
# ─────────────────────────────────────────────────────────────────────
def test_exact_recovery_at_dim8_where_bare_fails():
    """At dim=8 (< the 16 capacity floor) the rc124 BARE read fails, but the
    RecoverableFold recovers R EXACTLY from the carried seed == fractal_spectrum(R)."""
    # BARE rc124 at dim=8 → honest unrecovered.
    bare = fold_encode(Poly.from_coeffs(_GASKET), 3, dim=_LO_DIM)
    bare_read = fold_spectrum(bare)
    assert bare_read["verdict"] == "unrecovered"
    assert bare_read["op_provenance"] == "UNKNOWN"
    assert "decimation_map" not in bare_read       # no wrong Poly

    # RECOVERABLE at the SAME dim=8 → exact.
    rf = fold_encode_recoverable(_GASKET, 3, dim=_LO_DIM)
    rec = fold_spectrum(rf)
    assert rec["verdict"] == "recovered"
    assert rec["op_provenance"] == "EQUAL"
    assert rec["recovery"] == "exact-seed"

    direct = fractal_spectrum(Poly.from_coeffs(_GASKET), 3)
    assert _fs_equal(rec, direct)                  # == fractal_spectrum(R) bit-for-bit
    assert rec["decimation_map"].coeffs == tuple(Poly.from_coeffs(_GASKET).coeffs)
    # the carried seed genuinely GENERATED the stored bundle (integrity check)
    assert rec["fold_consistency"] == Q(1, 1)
    assert rec["similarity"] == Q(1, 1)
    assert rec["confidence"] == Q(1, 1)


def test_exact_recovery_across_dims_and_degrees():
    """Exact recovery holds at a spread of dims (incl. sub-floor) and for a
    higher-degree decimation — always == the direct fractal_spectrum call."""
    for coeffs, br in ((_GASKET, 3), (_OTHER, 2), ([0, 6, -5, 2], 4)):
        direct = fractal_spectrum(Poly.from_coeffs(coeffs), br)
        for dim in (1, 4, _LO_DIM, 64, _HI_DIM):
            rf = fold_encode_recoverable(coeffs, br, dim=dim)
            rec = fold_spectrum(rf)
            assert rec["verdict"] == "recovered", (coeffs, dim)
            assert _fs_equal(rec, direct), (coeffs, dim)


def test_recover_method_matches_fold_spectrum():
    """The ``.recover()`` shortcut == ``fold_spectrum(pair)``."""
    rf = fold_encode_recoverable(_GASKET, 3, dim=_LO_DIM)
    a, b = rf.recover(), fold_spectrum(rf)
    assert a["verdict"] == b["verdict"] == "recovered"
    assert _fs_equal(a, b)


# ─────────────────────────────────────────────────────────────────────
# (b) the fold-IDENTITY verdict — EQUAL / NOT_EQUAL / UNKNOWN
# ─────────────────────────────────────────────────────────────────────
def test_fold_identity_equal_same_R_different_dim():
    """Same (R, branches) at DIFFERENT dims → EQUAL (identity is dim/seed-
    independent: both recover the same object)."""
    a = fold_encode_recoverable(_GASKET, 3, dim=_HI_DIM)
    b = fold_encode_recoverable(_GASKET, 3, dim=_LO_DIM, seed=7)
    assert fold_identity(a, b) == "EQUAL"
    assert a.identity() == b.identity()
    assert a.identity() is not None


def test_fold_identity_not_equal_different_R_or_branches():
    """Different R → NOT_EQUAL; same R different branches → NOT_EQUAL (branches
    is part of the recovered identity)."""
    a = fold_encode_recoverable(_GASKET, 3, dim=_HI_DIM)
    diff_R = fold_encode_recoverable(_OTHER, 3, dim=_HI_DIM)
    diff_br = fold_encode_recoverable(_GASKET, 2, dim=_HI_DIM)
    assert fold_identity(a, diff_R) == "NOT_EQUAL"
    assert fold_identity(a, diff_br) == "NOT_EQUAL"


def test_fold_identity_unknown_when_a_bare_fold_is_involved():
    """A bare (seed-less) fold on EITHER side → UNKNOWN — identity is decidable
    only when you hold the complement; NEVER a false EQUAL/NOT_EQUAL from a
    lossy bundle."""
    seeded = fold_encode_recoverable(_GASKET, 3, dim=_HI_DIM)
    bare = RecoverableFold(fold_encode(Poly.from_coeffs(_GASKET), 3, dim=_HI_DIM), None)
    assert bare.identity() is None
    assert fold_identity(seeded, bare) == "UNKNOWN"
    assert fold_identity(bare, seeded) == "UNKNOWN"
    assert fold_identity(bare, bare) == "UNKNOWN"


def test_fold_identity_rejects_non_recoverable_operands():
    with pytest.raises(ValueError, match="RecoverableFold"):
        fold_identity(fold_encode_recoverable(_GASKET, 3, dim=64), {"not": "a fold"})


# ─────────────────────────────────────────────────────────────────────
# (c) the rc124 BARE fallback — UNCHANGED
# ─────────────────────────────────────────────────────────────────────
def test_bare_fold_falls_back_to_rc124_read():
    """A seed-less RecoverableFold reads via the rc124 similarity path: recovered
    at high dim, honest-``unrecovered`` at low dim — bit-identical to calling
    fold_spectrum on the underlying bundle directly."""
    hi = fold_encode(Poly.from_coeffs(_GASKET), 3, dim=_HI_DIM)
    lo = fold_encode(Poly.from_coeffs(_GASKET), 3, dim=_LO_DIM)

    bare_hi = RecoverableFold(hi, None)
    bare_lo = RecoverableFold(lo, None)
    assert bare_hi.has_seed is False

    r_hi, r_lo = fold_spectrum(bare_hi), fold_spectrum(bare_lo)
    assert r_hi["verdict"] == "recovered"
    assert r_hi["op_provenance"] == "EQUAL"
    assert r_lo["verdict"] == "unrecovered"
    assert r_lo["op_provenance"] == "UNKNOWN"
    # bit-identical to the rc124 read on the raw bundle
    direct_hi = fold_spectrum(hi)
    assert _fs_equal(r_hi, direct_hi)
    # bare read carries NO 'recovery: exact-seed' marker (that is the seed path)
    assert "recovery" not in r_hi


# ─────────────────────────────────────────────────────────────────────
# (d) the HarmonicMaass-shape mirror
# ─────────────────────────────────────────────────────────────────────
def test_harmonic_maass_shape_mirror():
    """RecoverableFold(lossy_bundle ↔ hol, exact_seed_R ↔ shadow) mirrors
    HarmonicMaass(hol, shadow): the pair, .has_seed, .complement() ↔ .xi()."""
    rf = fold_encode_recoverable(_GASKET, 3, dim=_HI_DIM)
    # the PAIR: lossy_bundle is the rc124 store; exact_seed_R is the decimation
    assert isinstance(rf.lossy_bundle, dict)
    assert "fold" in rf.lossy_bundle and "codes" in rf.lossy_bundle
    assert isinstance(rf.exact_seed_R, Poly)
    assert rf.exact_seed_R.coeffs == tuple(Poly.from_coeffs(_GASKET).coeffs)
    assert rf.has_seed is True
    assert rf.branches == 3
    assert rf.dim == _HI_DIM
    # .complement() ↔ HarmonicMaass.xi(): returns the exact complement (the seed)
    assert rf.complement() is rf.exact_seed_R

    # the direct constructor mirrors HarmonicMaass(hol, shadow) — a bundle + a seed
    rf2 = RecoverableFold(rf.lossy_bundle, _GASKET, branches=3)
    assert rf2.has_seed is True
    assert fold_identity(rf, rf2) == "EQUAL"

    # bare pair: exact_seed_R is None (a real-corpus 'found' fold)
    bare = RecoverableFold(rf.lossy_bundle, None)
    assert bare.has_seed is False
    assert bare.exact_seed_R is None
    assert bare.complement() is None

    # immutability (a __slots__ carrier, like HarmonicMaass)
    with pytest.raises(AttributeError):
        rf.newattr = 1


def test_recoverable_fold_requires_branches_with_seed_and_validates():
    with pytest.raises(ValueError, match="branches is required"):
        RecoverableFold(fold_encode(Poly.from_coeffs(_GASKET), 3, dim=64), _GASKET)
    with pytest.raises(TypeError, match="fold-store dict"):
        RecoverableFold("not a dict", None)


# ─────────────────────────────────────────────────────────────────────
# (e) determinism
# ─────────────────────────────────────────────────────────────────────
def test_encode_recoverable_is_deterministic():
    a = fold_encode_recoverable(_GASKET, 3, dim=256, seed=5)
    b = fold_encode_recoverable(_GASKET, 3, dim=256, seed=5)
    assert a.lossy_bundle["fold"].tolist() == b.lossy_bundle["fold"].tolist()
    assert a.identity() == b.identity()
    # a different seed changes the LOSSY bundle but NOT the identity (dim/seed-free)
    c = fold_encode_recoverable(_GASKET, 3, dim=256, seed=6)
    assert c.lossy_bundle["fold"].tolist() != a.lossy_bundle["fold"].tolist()
    assert c.identity() == a.identity()


# ─────────────────────────────────────────────────────────────────────
# (f) the op_provenance registration — lossy_projection_record
# ─────────────────────────────────────────────────────────────────────
def test_lossy_projection_record_shape():
    """family=None (no asymptotic target), rung={} (no precision rung),
    projection_kind='hdc' (the genuine non-asymptotic kind — never a faked
    interior/edge tower), leaves_exact True, a 64-hex chain hash."""
    rec = op_provenance.lossy_projection_record(
        "srmech.amsc.coupling.fold_encode",
        {"R": [Q(0, 1), Q(5, 1), Q(-4, 1)], "branches": 3},
    )
    assert rec["family"] is None
    assert rec["rung"] == {}
    assert rec["projection_kind"] == "hdc"
    assert rec["leaves_exact"] is True
    assert rec["op"] == "srmech.amsc.coupling.fold_encode"
    assert isinstance(rec["chain_sha256"], str) and len(rec["chain_sha256"]) == 64
    # re-verify: the hash is op_provenance_hash of the record (excl. chain field)
    assert op_provenance.op_provenance_hash(rec) == rec["chain_sha256"]


def test_lossy_projection_record_hash_agrees_with_fold_identity():
    """The RecoverableFold.identity() IS the lossy_projection_record chain hash
    over (R.coeffs, branches)."""
    rf = fold_encode_recoverable(_GASKET, 3, dim=64)
    rec = op_provenance.lossy_projection_record(
        "srmech.amsc.coupling.fold_encode",
        {"R": list(Poly.from_coeffs(_GASKET).coeffs), "branches": 3},
    )
    assert rf.identity() == rec["chain_sha256"]


def test_lossy_projection_record_validates():
    with pytest.raises(ValueError, match="non-empty"):
        op_provenance.lossy_projection_record("", {"R": [Q(0, 1)]})
    with pytest.raises(ValueError, match="dict"):
        op_provenance.lossy_projection_record("op", ["not", "a", "dict"])
    with pytest.raises(ValueError, match="projection_kind"):
        op_provenance.lossy_projection_record("op", {}, projection_kind="edge")


# ─────────────────────────────────────────────────────────────────────
# (g) registration + counts
# ─────────────────────────────────────────────────────────────────────
def test_tools_total_is_390():
    from srmech import introspect
    assert introspect.describe()["tools"]["total"] == 394


def test_new_ops_registered_fold_identity_exempt():
    from srmech.amsc import tool_schema
    from srmech.mcp._coercion import has_coercer

    schema = tool_schema.get_tool_schema()
    for name, cat in (
        ("srmech.amsc.coupling.fold_encode_recoverable", "coupling"),
        ("srmech.amsc.op_provenance.lossy_projection_record", "op_provenance"),
    ):
        entry = schema.lookup(name)
        assert entry is not None, f"{name} not registered"
        assert entry.owner == "srmech"
        assert entry.category == cat
        for p in entry.parameters:
            assert has_coercer(p.type), f"{name}:{p.name} type {p.type!r} uncoercible"

    # fold_identity is EXEMPT (its RecoverableFold operands cannot ride JSON) —
    # a public + tested verdict op, NOT an MCP ToolEntry.
    assert schema.lookup("srmech.amsc.coupling.fold_identity") is None
    assert hasattr(coupling, "fold_identity")

    enc = schema.lookup("srmech.amsc.coupling.fold_encode_recoverable")
    assert {p.name: p.type for p in enc.parameters}["R"] == "Poly"


def test_rosetta_rows_are_non_compute():
    import json
    from pathlib import Path
    ledger = Path(__file__).resolve().parent / "rosetta_classification.ndjson"
    rows = {r["defined_at"]: r["bucket"]
            for r in (json.loads(l) for l in
                      ledger.read_text(encoding="utf-8").splitlines() if l.strip())}
    for op in ("srmech.amsc.coupling.fold_encode_recoverable",
               "srmech.amsc.coupling.fold_identity",
               "srmech.amsc.op_provenance.lossy_projection_record"):
        assert rows.get(op) == "non_compute", op


# ─────────────────────────────────────────────────────────────────────
# (h) discipline — the touched sources stay abs()-free
# ─────────────────────────────────────────────────────────────────────
@pytest.mark.parametrize("rel", [
    ("srmech", "amsc", "coupling.py"),
    ("srmech", "amsc", "op_provenance.py"),
])
def test_source_is_numpy_math_abs_free(rel):
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    src = os.path.join(here, *rel)
    with tokenize.open(src) as fh:
        text = fh.read()
    assert re.search(r"(?m)^\s*(import|from)\s+numpy\b", text) is None
    assert re.search(r"(?m)^\s*(import|from)\s+math\b", text) is None
    assert re.search(r"abs\([^)]", text) is None          # no bare abs() CALL
