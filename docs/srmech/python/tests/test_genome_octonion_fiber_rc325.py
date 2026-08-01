"""rc325 PROVE-GATES — the genome OCTONION TOPOLOGY / FIBER channel (§𝕆-FIBER).

The 𝕆 analog of rc322's ℍ (Q₈) fiber channel, ONE Cayley–Dickson rung up. The
fibration has TWO sides; the register holds BOTH and reconstructs the fiber:

  BASE  (sequence)  — the per-turn coupled octonion store (:func:`_oct_couple`,
      `stored[i] = oct_mult(turn[i], one[i])`) re-stamps a function of turn i + the
      shared `one` ALONE, so a reorder is a PURE positional permutation. KEPT
      byte-identical.
  FIBER (topology) — :func:`genome_octonion_holonomy` folds the ORDERED octonion
      product along the strand. 𝕆 is non-commutative AND non-associative, so REORDER
      CHANGES it. The NON-ASSOCIATIVITY the Q₈ (associative) fiber cannot express is
      read by :func:`genome_octonion_associator` — the per-slot defect bit between the
      LEFT- and RIGHT-associated folds.

The four ship claims (numpy-free — a test for a numpy-free surface is itself numpy-free):

  F1  ORDER CARRIED IN THE FIBER: reorder a strand -> the accumulated octonion holonomy
      CHANGES; the base stored turns are a pure PERMUTATION (unchanged multiset), and the
      octonion index read is permutation-invariant as a multiset.
  F2  NON-ASSOCIATIVITY CAPTURED: a genuinely non-associative octonion triple (DERIVED by
      searching basis indices with the exact-rational cd_mult) has the associator defect
      BIT SET, matching the cd_mult-derived associator sign; any quaternionic triple
      (indices ⊆ {0,1,2,3}) yields defect CLEAR.
  F2b GAUGE RECONSTRUCTS: genome_read_octonion_fiber reports consistent, holonomy ==
      recomputed, and associator_defect one bit per slot.
  F3  BASE UNTOUCHED: the sequence channel + codon read are byte-identical with/without the
      𝕆 cap; the base is a strict prefix + exactly one 0x4F cap; format version is 18; a
      strand carrying BOTH a 0x46 (ℍ) and a 0x4F (𝕆) cap round-trips both independently; a
      pre-rc325 (fmt-17) body still opens.
  F4  NATIVE == PURE for the octonion fold (byte-identical; the exact-integer octonion fold).
"""
from __future__ import annotations

import json
import random
import tempfile
from pathlib import Path

import pytest

from srmech.amsc import genome as G
from srmech.amsc import _native
from srmech.amsc.cascade.cayley_dickson import cd_mult
from srmech.amsc.genome import (
    ELEMENT_TYPE_KLEIN4, ELEMENT_TYPE_OCTONION, OCTONION_SECTORS, QUAD,
    FIBER_CAP_MARKER, OCT_FIBER_CAP_MARKER, GENOME_FORMAT_VERSION,
    genome_octonion_holonomy, genome_octonion_associator,
    genome_add_octonion_fiber, genome_read_octonion_fiber,
    genome_add_fiber, genome_read_fiber,
    chromosome, recall, telomere, codon_read, _cap_kind, _hv_bytes,
)
from srmech.math.octonion import oct_bind, oct_mult
from srmech.amsc.hv import HV


# leaf_dim ≥ 24 so the default "octonion" (8-char) label + 4-bit-packed holonomy fits
# one leaf: 1 (marker) + 8 (label) + 1 (NUL) + 2 (n_holo) + ceil(D/2) ≤ D.
_LD = 32


def _oct_one(D=_LD):
    return HV.from_sequence(bytes((1 + i) % 16 for i in range(D)), sectors=OCTONION_SECTORS)


def _oct_leaf(seq):
    return HV.from_sequence(bytes(seq), sectors=OCTONION_SECTORS)


def _oct_strand(order, D=_LD, label="chrO"):
    """An octonion chromosome over three distinct leaves picked by `order`."""
    base = {
        "A": _oct_leaf([(1 + i) % 16 for i in range(D)]),
        "B": _oct_leaf([(3 + 2 * i) % 16 for i in range(D)]),
        "C": _oct_leaf([(5 + 3 * i) % 16 for i in range(D)]),
    }
    leaves = [base[c] for c in order]
    return chromosome(leaves, _oct_one(D), label=label, element_type=ELEMENT_TYPE_OCTONION)


def _pure_oct_fold(turns, D):
    """The forced-pure ordered octonion LEFT fold — the parity oracle."""
    acc = bytes(D)
    for t in turns:
        acc = oct_bind(acc, t)
    return acc


def _data_turns(strand):
    return [_hv_bytes(hv) for hv in strand if _cap_kind(hv) is None]


# ── exact-rational cd_mult reference at the octonion-byte level ───────────────
def _oct_byte_to_vec(o):
    idx, sign = o & 7, (-1 if (o >> 3) else 1)
    v = [0] * 8
    v[idx] = sign
    return v


def _oct_vec_to_byte(v):
    nz = [(i, int(c)) for i, c in enumerate(v) if int(c) != 0]
    assert len(nz) == 1, f"expected a single nonzero basis component; got {nz}"
    i, c = nz[0]
    assert c in (1, -1), f"basis-unit product must be ±1; got {c}"
    return ((0 if c == 1 else 1) << 3) | i


def _cdmul(a, b):
    """The octonion byte product via the EXACT-RATIONAL full-vector cd_mult."""
    return _oct_vec_to_byte(cd_mult(_oct_byte_to_vec(a), _oct_byte_to_vec(b)))


def _find_nonassoc_triple():
    """Search basis indices i,j,k for a genuinely non-associative octonion triple —
    (e_i·e_j)·e_k != e_i·(e_j·e_k) — using cd_mult, and return (i, j, k, defect_bit)
    where defect_bit is the cd_mult-derived associator sign (never hard-coded)."""
    for i in range(1, 8):
        for j in range(1, 8):
            for k in range(1, 8):
                left = _cdmul(_cdmul(i, j), k)
                right = _cdmul(i, _cdmul(j, k))
                if left != right:
                    assert (left & 7) == (right & 7)     # ⊕ index lane agrees; sign differs
                    return i, j, k, ((left >> 3) ^ (right >> 3))
    raise AssertionError("no non-associative octonion triple found (algebra broken)")


# ── F1 — order carried in the fiber; base is a pure permutation ──────────────
def test_f1_octonion_holonomy_changes_under_reorder():
    h_abc = genome_octonion_holonomy(_data_turns(_oct_strand("ABC")), _LD)
    h_cab = genome_octonion_holonomy(_data_turns(_oct_strand("CAB")), _LD)
    assert h_abc != h_cab, "octonion holonomy MUST change under reorder (order carried)"


def test_f1_base_stored_turns_are_a_pure_permutation_under_reorder():
    s_abc = _data_turns(_oct_strand("ABC"))
    s_cab = _data_turns(_oct_strand("CAB"))
    # the stored blocks are the SAME multiset (a pure positional permutation)
    assert sorted(s_abc) == sorted(s_cab)
    # and the octonion INDEX read (byte & 7) is permutation-invariant as a multiset
    assert (sorted(bytes(b & 7 for b in t) for t in s_abc)
            == sorted(bytes(b & 7 for b in t) for t in s_cab))


# ── F2 — the non-associativity is captured (convention-robust) ───────────────
def test_f2_nonassociativity_defect_matches_cd_mult():
    i, j, k, expected_bit = _find_nonassoc_triple()
    assert expected_bit == 1, "a genuinely non-associative triple must set the defect bit"
    defect = genome_octonion_associator([bytes([i]), bytes([j]), bytes([k])], 1)
    assert defect == bytes([expected_bit])          # pinned to the real algebra (cd_mult)
    # cross-check the byte object against the whole op's own folds
    assert defect[0] in (0, 1)


def test_f2_quaternionic_triple_is_associative():
    # any triple in the associative quaternion sub-block {e1,e2,e3} ⊆ {0..3} → defect CLEAR
    assert genome_octonion_associator([bytes([1]), bytes([2]), bytes([3])], 1) == b"\x00"
    assert genome_octonion_associator([bytes([1]), bytes([2]), bytes([1])], 1) == b"\x00"
    # a purely-quaternionic multi-slot strand (all indices ⊆ {0..3}) is defect-clear too
    q_turns = [bytes([1, 2, 3, 0]), bytes([3, 1, 2, 3]), bytes([2, 3, 1, 1])]
    assert genome_octonion_associator(q_turns) == bytes(4)


def test_f2_associator_identically_zero_for_n_lt_3():
    assert genome_octonion_associator([bytes([5])], 1) == b"\x00"          # n=1
    assert genome_octonion_associator([bytes([5]), bytes([6])], 1) == b"\x00"  # n=2
    assert genome_octonion_associator([], _LD) == bytes(_LD)               # n=0


# ── F2b — the gauge reconstructs ─────────────────────────────────────────────
def test_f2b_read_octonion_fiber_reconstructs():
    strand = _oct_strand("ABC")
    fib = genome_add_octonion_fiber(strand)
    r = genome_read_octonion_fiber(fib)
    assert r["consistent"] is True                  # stored gauge == re-derived from base
    assert r["holonomy"] == r["recomputed"]
    assert r["label"] == "octonion"
    assert len(r["associator_defect"]) == _LD       # one associator bit per slot
    assert all(b in (0, 1) for b in r["associator_defect"])


# ── F3 — base untouched (backward-compat) ────────────────────────────────────
def test_f3_sequence_and_codon_read_identical_with_without_octonion_fiber():
    strand = _oct_strand("ABC")
    fib = genome_add_octonion_fiber(strand)
    base_syms = b"".join(_data_turns(strand))
    fib_syms = b"".join(_data_turns(fib))
    assert base_syms == fib_syms                     # sequence channel byte-identical
    # the octonion index projection (byte & 7) drives an identical codon read
    base_idx = bytes(b & 7 for b in base_syms)
    fib_idx = bytes(b & 7 for b in fib_syms)
    assert codon_read(base_idx) == codon_read(fib_idx)
    # the fiber cap is skipped by the data-turn walk (same number of data turns)
    assert len(_data_turns(strand)) == len(_data_turns(fib))


def test_f3_base_is_a_strict_prefix_plus_one_oct_cap():
    strand = _oct_strand("ABC")
    fib = genome_add_octonion_fiber(strand)
    blocks = list(strand)
    fblocks = list(fib)
    # the base blocks are a strict prefix (byte-identical, same order)
    assert [_hv_bytes(h) for h in fblocks[:len(blocks)]] == [_hv_bytes(h) for h in blocks]
    appended = fblocks[len(blocks):]
    assert len(appended) == 1 and _cap_kind(appended[0]) == OCT_FIBER_CAP_MARKER


def test_f3_format_version_is_18():
    assert GENOME_FORMAT_VERSION == 19


def test_f3_both_hbar_and_octonion_caps_round_trip_independently():
    """A strand whose data turns are in 0..7 (valid for BOTH the Q8 fold and the octonion
    fold) can carry a 0x46 (ℍ) AND a 0x4F (𝕆) cap; each reads back independently."""
    turns = [HV.from_sequence(bytes((1 + 2 * i + k) % 8 for i in range(_LD)),
                              sectors=OCTONION_SECTORS) for k in range(3)]
    strand = [telomere("both", dim=_LD)] + turns
    fib_q8 = genome_add_fiber(strand)                     # appends the 0x46 ℍ cap
    fib_both = genome_add_octonion_fiber(fib_q8)          # appends the 0x4F 𝕆 cap
    kinds = [_cap_kind(h) for h in fib_both]
    assert FIBER_CAP_MARKER in kinds and OCT_FIBER_CAP_MARKER in kinds
    # each cap reads back independently — the other cap is skipped as an interior cap
    r_q8 = genome_read_fiber(fib_both)
    r_oct = genome_read_octonion_fiber(fib_both)
    assert r_q8["consistent"] is True
    assert r_oct["consistent"] is True
    # adding the 𝕆 cap did not disturb the ℍ cap's stored gauge, and vice-versa: the ℍ read
    # off the two-cap strand equals the ℍ read off the one-cap strand
    assert r_q8["holonomy"] == genome_read_fiber(fib_q8)["holonomy"]


def test_f3_pre_rc325_fmt17_body_still_opens(tmp_path):
    """A klein4 body written then STAMPED back to format_version 17 (a pre-rc325 save) still
    opens under the fmt-18 reader and recalls its exact sequence — the bump is backward-compat."""
    rng = random.Random(32501)
    one = HV.from_sequence(bytes(rng.randrange(QUAD) for _ in range(_LD)), sectors=QUAD)
    leaves = [HV.from_sequence(bytes(rng.randrange(QUAD) for _ in range(_LD)), sectors=QUAD)
              for _ in range(4)]
    strand = chromosome(leaves, one, label="k4", element_type=ELEMENT_TYPE_KLEIN4)
    d = str(tmp_path)
    data = G.genome_save(strand, d, one, element_type=ELEMENT_TYPE_KLEIN4)
    assert data["format_version"] == 19                  # the current (v18) writer stamps 18
    # rewrite the manifest to a pre-rc325 format_version 17 (the body is byte-identical)
    man_path = Path(d, "manifest.json")
    man = json.loads(man_path.read_text(encoding="utf-8"))
    man["data"]["format_version"] = 17
    man_path.write_text(json.dumps(man), encoding="utf-8")
    loaded, _cpl, _lbls = G.genome_load(d, coupling=one)
    assert [h.tolist() for h in recall(loaded, one)] == [h.tolist() for h in leaves]


# ── F4 — native == pure ──────────────────────────────────────────────────────
# rc351 (task `#T1004`): skip rather than assert the native lib into existence — see the
# matching note in test_genome_fiber_channel_rc322.py.
@pytest.mark.skipif(not _native.has_native_genome_octonion_holonomy(),
                    reason="native octonion-holonomy symbol required for the differential")
def test_f4_native_equals_pure_random_strands(monkeypatch):
    assert _native.has_native_genome_octonion_holonomy()
    rng = random.Random(32502)
    trials = 0
    for _ in range(240):
        ld = rng.randint(1, 12)
        n = rng.randint(0, 15)
        turns = [bytes(rng.randint(0, 15) for _ in range(ld)) for _ in range(n)]
        native = genome_octonion_holonomy(turns, ld)     # C whole-op path
        with monkeypatch.context() as m:
            m.setattr(_native, "HAS_NATIVE", False)      # force the pure oct_bind fold
            pure = _pure_oct_fold(turns, ld)
        assert native == pure
        trials += 1
    assert trials == 240


def test_f4_native_matches_forced_pure_via_monkeypatch(monkeypatch):
    rng = random.Random(32503)
    ld = 8
    turns = [bytes(rng.randint(0, 15) for _ in range(ld)) for _ in range(9)]
    native = genome_octonion_holonomy(turns, ld)
    monkeypatch.setattr(_native, "genome_octonion_holonomy_c", lambda *a, **k: None)
    pure = genome_octonion_holonomy(turns, ld)
    assert native == pure == _pure_oct_fold(turns, ld)


# ── edges + surface ──────────────────────────────────────────────────────────
def test_oct_fiber_cap_round_trip():
    holo = bytes((i * 5 + 1) % 16 for i in range(_LD))
    cap = G._pack_oct_fiber_cap(holo, "octonion", _LD)
    assert len(cap) == _LD
    assert _cap_kind(cap) == OCT_FIBER_CAP_MARKER
    label, got = G._unpack_oct_fiber_cap(cap)
    assert label == "octonion" and bytes(got) == holo


def test_octonion_holonomy_empty_and_flat_forms_agree():
    assert genome_octonion_holonomy([], _LD) == bytes(_LD)         # identity
    turns = [bytes([1, 9, 14, 0]), bytes([4, 15, 6, 8])]
    flat = b"".join(turns)
    assert genome_octonion_holonomy(turns) == genome_octonion_holonomy(flat, 4)


def test_octonion_holonomy_rejects_non_octonion_byte():
    with pytest.raises(ValueError):
        genome_octonion_holonomy([bytes([1, 16, 2, 3])], 4)        # 16 is not an octonion byte
    with pytest.raises(ValueError):
        genome_octonion_associator([bytes([1, 16, 2, 3])], 4)


def test_add_octonion_fiber_rejects_double_cap():
    fib = genome_add_octonion_fiber(_oct_strand("ABC"))
    with pytest.raises(ValueError):
        genome_add_octonion_fiber(fib)


def test_read_octonion_fiber_rejects_base_only_strand():
    with pytest.raises(ValueError):
        genome_read_octonion_fiber(_oct_strand("ABC"))


def test_octonion_fiber_ops_are_public_and_registered():
    for name in ("genome_octonion_holonomy", "genome_octonion_associator",
                 "genome_add_octonion_fiber", "genome_read_octonion_fiber",
                 "OCT_FIBER_CAP_MARKER"):
        assert name in G.__all__
    from srmech.amsc import tool_schema
    tools = {t.name for t in tool_schema.get_tool_schema().tools}
    for op in ("genome_octonion_holonomy", "genome_octonion_associator",
               "genome_add_octonion_fiber", "genome_read_octonion_fiber"):
        assert f"srmech.amsc.genome.{op}" in tools
