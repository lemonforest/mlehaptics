"""rc322 PROVE-GATES — the genome TOPOLOGY / FIBER channel (§Q8-FIBER, F-HOLO-MISLOCATED).

The fibration has TWO sides; the register must hold BOTH and reconstruct the gauge:

  BASE  (sequence)  — the per-turn coupled store (quad_turn, element_type=q8) RE-STAMPS
      stored[i]=q8_mult(turn[i], one[i]) — a function of turn i + the shared `one` ALONE,
      never of prior turns — so it is winding-INVARIANT: a reorder is a PURE positional
      permutation (the #T914 order-discard). KEPT byte-identical.
  FIBER (topology) — genome_fiber_holonomy folds the ORDERED non-abelian Q8 product along
      the strand. Q8 is non-abelian (i.j=+k, j.i=-k), so REORDER CHANGES it — the
      accumulated holonomy = the gauge = the accumulated Lk (Lk=Tw+Wr).

The four ship claims (numpy-free — a test for a numpy-free surface is itself numpy-free):

  F1  ORDER CARRIED IN THE FIBER: reorder a strand -> the accumulated fiber holonomy
      CHANGES; the base sequence bytes are a pure PERMUTATION (unchanged). And the base
      per-turn store re-stamps identically regardless of position (F-HOLO-MISLOCATED).
  F2  GAUGE RECONSTRUCTS: the accumulated Lk (the fiber-fold center-sign) == Tw + Wr
      (cwf_consistency_mod2 consistency, in ACCUMULATED form).
  F3  BASE UNTOUCHED: the sequence channel + codon read are BYTE-IDENTICAL with/without
      the fiber, and a default save's turns.bin is byte-identical to a pre-fiber save
      (backward-compat); a fiber body is the base bytes + exactly one 0x46 cap.
  F4  NATIVE == PURE for the fiber op (byte-identical; the exact-integer Q8 fold).
"""
from __future__ import annotations

import random
import tempfile
from pathlib import Path

import pytest

from srmech.biology import genome as G
from srmech import _native
from srmech.biology.genome import (
    ELEMENT_TYPE_Q8, FIBER_CAP_MARKER, GENOME_FORMAT_VERSION,
    genome_fiber_holonomy, genome_add_fiber, genome_read_fiber,
    quad_turn, chromosome, codon_read, cwf_consistency_mod2, _cap_kind, _hv_bytes,
)
from srmech.biology.q8 import q8_from_one, q8_bind, q8_project_v4
from srmech.cascade.one import the_one
from srmech.math.hv import HV


_LD = 16


def _one(D=_LD):
    return q8_from_one(the_one(1, 1, 3, 6), D)


def _leaf(seq):
    return HV.from_sequence(bytes(seq), sectors=8)


def _q8_strand(order, D=_LD, label="chrF"):
    """A Q8 chromosome over three distinct leaves picked by `order` ('ABC'/'CAB'/...)."""
    base = {
        "A": _leaf([(1 + i) % 8 for i in range(D)]),
        "B": _leaf([(3 + 2 * i) % 8 for i in range(D)]),
        "C": _leaf([(5 + 3 * i) % 8 for i in range(D)]),
    }
    leaves = [base[c] for c in order]
    return chromosome(leaves, _one(D), label=label, element_type=ELEMENT_TYPE_Q8)


def _pure_fiber(turns, D):
    """The forced-pure ordered Q8 fold — the parity oracle."""
    acc = bytes(D)
    for t in turns:
        acc = q8_bind(acc, t)
    return acc


def _data_turns(strand):
    return [_hv_bytes(hv) for hv in strand if _cap_kind(hv) is None]


# ── F1 — order carried in the fiber; base is a pure permutation ──────────────
def test_f1_fiber_holonomy_changes_under_reorder():
    s_abc = _q8_strand("ABC")
    s_cab = _q8_strand("CAB")
    h_abc = genome_fiber_holonomy(_data_turns(s_abc), _LD)
    h_cab = genome_fiber_holonomy(_data_turns(s_cab), _LD)
    assert h_abc != h_cab, "fiber holonomy MUST change under reorder (order carried)"


def test_f1_base_sequence_is_a_pure_permutation_under_reorder():
    s_abc = _data_turns(_q8_strand("ABC"))
    s_cab = _data_turns(_q8_strand("CAB"))
    # the stored blocks are the SAME multiset (a pure positional permutation)
    assert sorted(s_abc) == sorted(s_cab)
    # and the V4 / Watson-Crick sequence read is permutation-invariant as a multiset
    assert (sorted(bytes(q8_project_v4(t)) for t in s_abc)
            == sorted(bytes(q8_project_v4(t)) for t in s_cab))


def test_f1_base_restamps_identically_regardless_of_position():
    # F-HOLO-MISLOCATED: a Q8-coupled turn stamps byte-identically wherever it sits.
    one = _one()
    A = _leaf([(1 + i) % 8 for i in range(_LD)])
    B = _leaf([(2 + i) % 8 for i in range(_LD)])

    def couple(t):
        return bytes(quad_turn(t, one, element_type=ELEMENT_TYPE_Q8).tobytes())
    first = couple(A)
    # A after some other turn — the store is a function of (A, one) alone
    _ = couple(B)
    last = couple(A)
    assert first == last


# ── F2 — the gauge reconstructs: accumulated Lk == Tw + Wr ───────────────────
_I = [0.0, 1.0, 0.0, 0.0]
_NEG_I = [0.0, -1.0, 0.0, 0.0]
_ONE = [1.0, 0.0, 0.0, 0.0]
_EDGES = [(0, 1), (1, 2), (2, 3), (3, 0)]
_SKEW = [(0, 0, 0), (2, 2, 0), (2, 0, 10), (0, 2, 10)]  # +1 crossing


def _vec_to_q8(v):
    for i, c in enumerate(v):
        if c > 0.5:
            return i
        if c < -0.5:
            return (1 << 2) | i
    return 0


@pytest.mark.parametrize("gains, expect_lk", [
    ([_I, _I, _ONE, _ONE], 1),      # i.i.1.1 = -1  -> Lk 1 ; Tw 0 + Wr 1
    ([_NEG_I, _I, _ONE, _ONE], 0),  # (-i).i.1.1 = +1 -> Lk 0 ; Tw 1 + Wr 1
])
def test_f2_accumulated_lk_reconstructs_tw_plus_wr(gains, expect_lk):
    # accumulated form: the fiber fold of the per-turn Q8 gains, one slot each
    turns = [bytes([_vec_to_q8(v)]) for v in gains]
    holo = genome_fiber_holonomy(turns, 1)
    accumulated_lk = holo[0] >> 2                 # the center-sign IS Lk mod 2
    res = cwf_consistency_mod2(_EDGES, gains, embedding=_SKEW, closed=True)
    assert accumulated_lk == expect_lk
    assert accumulated_lk == res["lk_mod2"]       # fiber == the intrinsic Lk
    assert res["consistent"] is True              # cwf: (Tw + Wr) % 2 == Lk


def test_f2_read_fiber_reports_consistent_gauge():
    strand = _q8_strand("ABC")
    fib = genome_add_fiber(strand)
    r = genome_read_fiber(fib)
    assert r["consistent"] is True                # stored gauge == re-derived from base
    assert r["holonomy"] == r["recomputed"]
    assert len(r["lk_mod2"]) == _LD               # one accumulated-Lk bit per slot
    assert all(b in (0, 1) for b in r["lk_mod2"])


# ── F3 — base untouched (backward-compat) ────────────────────────────────────
def test_f3_codon_and_sequence_read_identical_with_without_fiber():
    strand = _q8_strand("ABC")
    fib = genome_add_fiber(strand)
    base_syms = b"".join(bytes(q8_project_v4(t)) for t in _data_turns(strand))
    fib_syms = b"".join(bytes(q8_project_v4(t)) for t in _data_turns(fib))
    assert base_syms == fib_syms                  # sequence channel byte-identical
    assert codon_read(base_syms) == codon_read(fib_syms)
    # the fiber cap is skipped by the data-turn walk (same number of data turns)
    assert len(_data_turns(strand)) == len(_data_turns(fib))


def test_f3_turns_bin_base_identical_and_fiber_appends_one_cap():
    one = _one()
    strand = _q8_strand("ABC")
    fib = genome_add_fiber(strand)

    def _save_body(strd):
        d = tempfile.mkdtemp()
        data = G.genome_save(strd, d, one, element_type=ELEMENT_TYPE_Q8)
        return data, Path(d, "turns.bin").read_bytes()

    data0, body0 = _save_body(strand)
    data1, body1 = _save_body(fib)
    # format bumped, but the BASE bytes are byte-identical: body0 is a strict prefix
    assert data0["format_version"] == 20 and data1["format_version"] == 20
    assert body1.startswith(body0)                # base sequence bytes untouched
    appended = body1[len(body0):]
    assert len(appended) == _LD and appended[0] == FIBER_CAP_MARKER


def test_f3_native_save_load_roundtrips_the_fiber():
    one = _one()
    fib = genome_add_fiber(_q8_strand("ABC"))
    d = tempfile.mkdtemp()
    G.genome_save(fib, d, one, element_type=ELEMENT_TYPE_Q8)
    loaded, _cpl, _lbls = G.genome_load(d, coupling=one)
    r_loaded = genome_read_fiber(loaded)
    r_orig = genome_read_fiber(fib)
    assert r_loaded["consistent"] is True
    assert r_loaded["holonomy"] == r_orig["holonomy"]   # survives save/load + the walker


def test_f3_format_version_is_pinned():
    # NAME CARRIES NO NUMBER ON PURPOSE. This pin tracks a value that MOVES;
    # a name that spells the value is falsified by the next bump and was —
    # 16 such tests were found tree-wide, one named for 367 asserting 663.
    # See test_pinned_names_carry_no_value_rc447.py.
    assert GENOME_FORMAT_VERSION == 20


# ── F4 — native == pure ──────────────────────────────────────────────────────
# rc351 (task `#T1004`): a native-vs-pure differential has nothing to compare when there is
# no native lib, so it SKIPS rather than asserting the lib into existence. Before this, the
# no-native run of the suite was red on these two rows for a reason that had nothing to do
# with the code under test — which is part of why nobody ran it (see the new
# `fallback (pure-Python, no native)` CI cell in .github/workflows/srmech-ci.yml).
@pytest.mark.skipif(not _native.has_native_genome_fiber_holonomy(),
                    reason="native fiber-holonomy symbol required for the differential")
def test_f4_native_equals_pure_random_strands():
    assert _native.has_native_genome_fiber_holonomy()
    rng = random.Random(1234)
    for _ in range(200):
        ld = rng.randint(1, 12)
        n = rng.randint(0, 15)
        turns = [bytes(rng.randint(0, 7) for _ in range(ld)) for _ in range(n)]
        native = genome_fiber_holonomy(turns, ld)
        assert native == _pure_fiber(turns, ld)


def test_f4_native_matches_forced_pure_via_monkeypatch(monkeypatch):
    rng = random.Random(99)
    ld = 8
    turns = [bytes(rng.randint(0, 7) for _ in range(ld)) for _ in range(9)]
    native = genome_fiber_holonomy(turns, ld)
    monkeypatch.setattr(_native, "genome_fiber_holonomy_c", lambda *a, **k: None)
    pure = genome_fiber_holonomy(turns, ld)
    assert native == pure == _pure_fiber(turns, ld)


# ── edges + surface ──────────────────────────────────────────────────────────
def test_fiber_cap_round_trip():
    holo = bytes((i * 5 + 1) % 8 for i in range(_LD))
    cap = G._pack_fiber_cap(holo, "gauge", _LD)
    assert len(cap) == _LD
    assert _cap_kind(cap) == FIBER_CAP_MARKER
    label, got = G._unpack_fiber_cap(cap)
    assert label == "gauge" and bytes(got) == holo


def test_fiber_holonomy_of_empty_and_flat_forms_agree():
    assert genome_fiber_holonomy([], _LD) == bytes(_LD)         # identity
    turns = [bytes([1, 2, 3, 0]), bytes([4, 5, 6, 7])]
    flat = b"".join(turns)
    assert genome_fiber_holonomy(turns) == genome_fiber_holonomy(flat, 4)


def test_fiber_rejects_non_q8_byte():
    with pytest.raises(ValueError):
        genome_fiber_holonomy([bytes([1, 8, 2, 3])], 4)         # 8 is not a Q8 element


def test_add_fiber_rejects_double_fiber():
    fib = genome_add_fiber(_q8_strand("ABC"))
    with pytest.raises(ValueError):
        genome_add_fiber(fib)


def test_read_fiber_rejects_base_only_strand():
    with pytest.raises(ValueError):
        genome_read_fiber(_q8_strand("ABC"))


def test_fiber_ops_are_public_and_registered():
    for name in ("genome_fiber_holonomy", "genome_add_fiber", "genome_read_fiber",
                 "FIBER_CAP_MARKER"):
        assert name in G.__all__
    from srmech.introspect import tool_schema
    tools = {t.name for t in tool_schema.get_tool_schema().tools}
    for op in ("genome_fiber_holonomy", "genome_add_fiber", "genome_read_fiber"):
        assert f"srmech.biology.genome.{op}" in tools
