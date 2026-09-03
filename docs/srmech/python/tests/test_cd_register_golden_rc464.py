"""rc464 (`#T1188`) — the faithfulness gate, against a RECORD rather than a peer.

``CDRegister`` is the register shape srmech ships. The 16-slot ``SedenionRegister``
it subsumes was, until this rc, both the thing being subsumed AND the oracle the
subsumption was measured against — and ``test_cd_register_rc297.py`` carried a
test whose whole job was to forbid the subsumption, by asserting through
``inspect.getsource`` that the oracle does not mention the subject.

That test was right. An oracle that delegates to its subject shares the subject's
failure modes, and a gate against it proves nothing. So the guarantee is not
deleted here; it MOVES, from code independence to data provenance:

    tests/sedenion_register_golden_rc464.ndjson

is 1157 records of what the shipped class actually did, recorded before its
removal by ``docs/srmech/notes/_golden_sedenion_register_rc464.py`` at commit
eaee799a7 from a source file whose SHA-256 is in the fixture header, with the
fixture's own bytes pinned in ``tests/_golden_sedenion.py``. Recorded output
cannot acquire the subject's failure modes for a reason stronger than "different
lines": it is not running. Nothing in this suite can re-record it.

WHAT IS GATED HERE, and it is more than the class ever gated:

* THE NINE-D BIT-EXACT GATE, verbatim — ``CDRegister(16, namespace="SEDENION")``
  must reproduce the recorded (key, sign) on all 120 probes at each of nine D,
  INCLUDING the capacity-starved regime where the register itself only scores
  116/120. Matching only where capacity hides the difference would leave the
  minting unverified exactly where it is exposed.
* The per-D hit counts as numbers (116 at D=256 ... 120 at D>=1024), so a
  regression that keeps the shape and loses a read is a failure, not a shrug.
* BYTE level, which the live oracle never gated: the materialised bundle's
  SHA-256, every slot's unbound vector digest, and the codebook digests. The
  old gate compared what came back out of ``read``; this compares the bytes in
  between.
* The C address peers at dim 16 against the recorded navigation, replacing a
  test that compared two C symbols to each other — one of which this arc
  removes.
* The recorded value-ops (coupler words as ``float.hex()``, every single-bit
  Hamming correction) and the rc330 signed-slot reads.

THE SUBSUMING FORM is ``CDRegister(16, namespace="SEDENION", coupling=True,
error_correction=True)``. The namespace is load-bearing (it IS the address mint
name) and both flags are, because the 16-slot register's coupling and EC layers
were UNGATED while CDRegister gates them. ``test_a_different_namespace_does_not
_reproduce_the_record`` proves the first is not decoration.

numpy-free; no ``abs()``; digests route through ``srmech.amsc.format``.
"""

from __future__ import annotations

import pytest

from srmech import cascade
from srmech import _native
from srmech.amsc.format import sha256_bytes
from srmech.math.hdc import bind

from tests._golden_sedenion import (
    EXPECTED_RECORD_COUNTS,
    GOLDEN_D_VALUES,
    GOLDEN_KEYS,
    GOLDEN_SHA256,
    golden_bytes,
    golden_header,
    int_keyed,
    load_golden,
    probes_for,
)


def _subsuming(D=8192, namespace="SEDENION"):
    """The CDRegister spelling that IS the recorded register."""
    return cascade.cd_register(16, D=D, namespace=namespace,
                               coupling=True, error_correction=True)


def _replay_probes(D, namespace="SEDENION"):
    """The recorded probe protocol, run live: a fresh register per direction,
    eight keys written, each read back at its navmap-predicted destination.
    Returns one dict per probe, in the recorded order."""
    out = []
    for j in range(1, 16):
        r = _subsuming(D=D, namespace=namespace)
        for i, k in enumerate(GOLDEN_KEYS):
            r.write(i, k)
        nav = r.navmap(j)
        moved = r.navigate(j)
        for i, k in enumerate(GOLDEN_KEYS):
            dest, sign = nav[i]
            got_key, got_sign = moved.read(dest)
            out.append({"j": j, "i": i, "key": k, "dest": dest,
                        "sign_expected": sign, "got_key": got_key,
                        "got_sign": got_sign,
                        "hit": bool(got_key == k and got_sign == sign)})
    return out


# ──────────────────────────────────────────────────────────────────────
# The fixture itself — pinned, complete, and provenance-bearing
# ──────────────────────────────────────────────────────────────────────

def test_the_fixture_is_pinned_complete_and_carries_its_provenance():
    """A golden fixture with no digest is a file anyone can regenerate from the
    thing it is supposed to gate. The digest is checked by the loader; this
    pins the CENSUS too, because a truncated read passes a digest check on the
    part it read and silently gates less than it claims."""
    by_kind = load_golden()
    assert {k: len(v) for k, v in by_kind.items()} == EXPECTED_RECORD_COUNTS
    assert sha256_bytes(golden_bytes()) == GOLDEN_SHA256

    h = golden_header()
    assert h["oracle"] == "srmech.cascade.sedenion_register.SedenionRegister"
    assert len(h["oracle_source_sha256"]) == 64
    assert h["source_commit"] and h["srmech_version"].startswith("0.9.0")
    # The laws a reader needs to reconstruct any record without the class.
    assert h["laws"]["address_mint_name"] == "SEDENION:e{slot}"
    assert h["laws"]["value_mint_name"] == "VAL:{key}"
    assert h["laws"]["num_slots"] == 16
    assert h["laws"]["working_word_cap"] == 7
    assert "coupling=True" in h["subsuming_form"]


# ──────────────────────────────────────────────────────────────────────
# THE NINE-D BIT-EXACT GATE
# ──────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("D", GOLDEN_D_VALUES)
def test_the_nine_d_bit_exact_gate_against_the_record(D):
    """``CDRegister(16, namespace="SEDENION")`` reproduces the recorded register
    byte-for-byte — same recovered key AND same Class-C sign on all 120 probes —
    at EVERY D, including the starved regime where both fall short of 120/120.

    Deliberately stronger than "agrees at adequate D". This is the rc297 gate
    with the oracle replaced by its own recorded output, and it additionally
    checks the navmap-predicted DESTINATION and expected sign per probe, which
    the live comparison never did (it compared only what came back)."""
    recorded = probes_for(D)
    live = _replay_probes(D)
    assert len(recorded) == 120 and len(live) == 120
    for want, got in zip(recorded, live):
        assert (got["j"], got["i"], got["key"]) == (want["j"], want["i"], want["key"])
        assert (got["dest"], got["sign_expected"]) == (want["dest"], want["sign_expected"]), (
            f"the address routing diverges from the record at D={D}, "
            f"j={want['j']}, slot {want['i']}")
        assert (got["got_key"], got["got_sign"]) == (want["got_key"], want["got_sign"]), (
            f"the general register diverges from the recorded oracle at D={D}, "
            f"j={want['j']}, key {want['key']!r} -> slot {want['dest']} — "
            f"faithfulness is NOT established")


def test_the_recorded_hit_counts_are_reproduced_as_numbers():
    """The shape agreeing is not the same as the SCORE agreeing. 116/120 at
    D=256 is a documented number about this register at a starved capacity; if
    it silently became 115 the probe lists would still be "some list"."""
    by_D = {r["D"]: r for r in load_golden()["probe_hits"]}
    assert sorted(by_D) == sorted(GOLDEN_D_VALUES)
    assert by_D[256]["hits"] == 116, "the documented starved-capacity score moved"
    for D in (1024, 4096):
        assert by_D[D]["hits"] == 120, f"the brief's stated gate fails at D={D}"
    for D in GOLDEN_D_VALUES:
        live = sum(1 for p in _replay_probes(D) if p["hit"])
        assert live == by_D[D]["hits"], (
            f"hit count at D={D}: live {live} vs recorded {by_D[D]['hits']}")


def test_a_different_namespace_does_not_reproduce_the_record():
    """The negative control on the gate above. ``namespace`` IS the address mint
    name, so if the gate could not tell ``SEDENION`` from ``CD16`` it would be
    passing on something other than what it claims. At the starved D=256 the two
    namespaces genuinely disagree — and at adequate capacity both reach 120/120,
    which is why the gate is run at starved D and not only at 4096."""
    recorded = [(p["got_key"], p["got_sign"]) for p in probes_for(256)]
    other = [(p["got_key"], p["got_sign"]) for p in _replay_probes(256, namespace="CD16")]
    assert other != recorded, (
        "a different address-mint namespace reproduced the record exactly — the "
        "gate is not sensitive to the one variable the faithfulness claim rests on")
    assert sum(1 for p in _replay_probes(4096, namespace="CD16") if p["hit"]) == 120


# ──────────────────────────────────────────────────────────────────────
# Address algebra — the navmap and the routing
# ──────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("j", list(range(16)))
def test_navmap_at_dim_16_matches_the_record(j):
    """The general layer is a GENERALISATION, not a second algebra: at dim 16 its
    signed permutation is the recorded 16-slot one, in both the free-function and
    the method spelling."""
    rec = {int(i): tuple(v) for i, v in
           next(r for r in load_golden()["navmap"] if r["j"] == j)["map"].items()}
    assert cascade.cd_navmap(16, j) == rec
    assert cascade.cd_register(16, D=256).navmap(j) == rec


@pytest.mark.parametrize("j", list(range(16)))
def test_navigate_routing_matches_the_record(j):
    """Content routing composes the Class-C signs the recorded register composed."""
    rec = next(r for r in load_golden()["navigate"] if r["j"] == j)
    r = _subsuming(D=512)
    for slot, key, sign in rec["occupancy"]:
        r.write(slot, key, sign=sign)
    routed = r.navigate(j).slots()
    assert routed == {int(s): (k, g) for s, (k, g) in rec["routed"].items()}


def test_c_peers_reproduce_the_recorded_navigation_at_dim_16():
    """The dim-16 C address peers against the RECORD.

    This replaces ``test_c_peers_agree_with_the_sedenion_c_peers_at_dim_16``,
    which compared ``srmech_cd_navmap`` to ``srmech_sedenion_navmap`` — two C
    symbols, one of which this arc removes. Comparing the survivor to the
    recorded answer keeps the guarantee (the general symbol did not fork the
    16-slot behaviour) and outlives the peer."""
    if not (_native.has_native_cd_navmap() and _native.has_native_cd_navigate()):
        pytest.skip("no native library loaded")
    for rec in load_golden()["navmap"]:
        j = rec["j"]
        want = {int(i): tuple(v) for i, v in rec["map"].items()}
        assert _native.cd_navmap_c(16, j) == want, f"srmech_cd_navmap forked at j={j}"
    for rec in load_golden()["navigate"]:
        j = rec["j"]
        occ = sorted((s, k, g) for s, k, g in rec["occupancy"])
        slots = [s for s, _k, _g in occ]
        signs = [g for _s, _k, g in occ]
        out_slots, out_signs = _native.cd_navigate_c(16, j, slots, signs)
        keys = [k for _s, k, _g in occ]
        got = {out_slots[m]: (keys[m], out_signs[m]) for m in range(len(occ))}
        assert got == {int(s): (k, g) for s, (k, g) in rec["routed"].items()}, (
            f"srmech_cd_navigate forked from the recorded routing at j={j}")


# ──────────────────────────────────────────────────────────────────────
# Byte level — what the live oracle never gated
# ──────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("idx", list(range(EXPECTED_RECORD_COUNTS["storage"])))
def test_storage_is_byte_identical_to_the_record(idx):
    """The materialised bundle, every slot's unbound vector and every codebook
    entry, as SHA-256 digests.

    The rc297 gate compared what ``read`` returned. Two registers can agree on
    every read while disagreeing on the bytes in between — bundle order, the
    odd-N pad, a sign applied at a different step — and the difference would sit
    there until a capacity-starved D exposed it. This closes that: the
    superposition itself is identical, not merely its decodings."""
    rec = load_golden()["storage"][idx]
    r = _subsuming(D=rec["D"])
    for slot, key, sign in rec["writes"]:
        r.write(slot, key, sign=sign)

    bundle = r.materialize()
    assert len(bundle) == rec["materialize_bytes"]
    assert sha256_bytes(bundle) == rec["materialize_sha256"], (
        f"the materialised bundle differs from the record "
        f"({rec['label']}, D={rec['D']})")
    assert {k: sha256_bytes(v) for k, v in sorted(r.codebook.items())} \
        == rec["codebook_sha256"]
    assert {str(s): sha256_bytes(bind(r._addr(s), bundle)) for s in range(16)} \
        == rec["unbind_sha256"]
    assert {str(s): list(r.read(s)) for s in range(16)} == rec["reads"]
    assert {str(s): [k, g] for s, (k, g) in sorted(r.slots().items())} \
        == rec["slots"]


def test_rc330_signed_slot_reads_match_the_record():
    """The rc330 record: five signed slots at D=512, every slot read, plus the
    slot map. The carrier surface (element / norm) reads that SAME slot map, so
    the equivalence the rc330 suite asserted against the live class is preserved
    here against its record."""
    rec = load_golden()["reads"][0]
    r = _subsuming(D=rec["D"])
    for s, sign in int_keyed(rec["occupancy"]).items():
        r.write(s, f"v{s}", sign=sign)
    assert {str(s): list(r.read(s)) for s in range(16)} == rec["reads"]
    assert {str(s): [k, g] for s, (k, g) in sorted(r.slots().items())} == rec["slots"]
    assert r.norm() == len(rec["occupancy"])       # each coefficient is +-1


# ──────────────────────────────────────────────────────────────────────
# The value operations — the two OPT layers, recorded
# ──────────────────────────────────────────────────────────────────────

def test_coupler_words_are_bit_exact_with_the_record():
    """Recorded as ``float.hex()`` strings, so this is bit-identity and not a
    tolerance. The recorded register's coupler was UNGATED; CDRegister gates it,
    which is why the subsuming form opts in."""
    r = _subsuming()
    for rec in load_golden()["couple"]:
        vals = [float.fromhex(v) for v in rec["vals"]]
        word = r.couple_working(vals)
        assert [float(v).hex() for v in word] == rec["word"], (
            f"the coupled working word diverged on {vals}")
        assert [float(v).hex() for v in r.uncouple_working(word)] == rec["uncoupled"]


def test_hamming_carry_and_every_single_bit_correction_match_the_record():
    """Each recorded codeword, and the decode of EVERY single-bit corruption of
    it — the located position and the recovered payload, not just the verdict."""
    r = _subsuming()
    for rec in load_golden()["carry"]:
        assert r.carry(rec["data"], n=rec["n"]) == rec["codeword"]
    for rec in load_golden()["correct"]:
        assert r.correct(rec["codeword"]) == rec["result"], (
            f"correction diverged at n={rec['n']}, flipped bit {rec['pos']}")


def test_the_subsuming_form_needs_both_opt_layers_and_says_so():
    """The one behavioural difference between the recorded class and the register
    that subsumes it: the 16-slot register's coupling and EC layers were always
    on, CDRegister gates them. A bare register RAISES where the record returned,
    which is why the fixture header states the subsuming spelling."""
    bare = cascade.cd_register(16, D=256, namespace="SEDENION")
    rec = load_golden()["couple"][0]
    with pytest.raises(ValueError, match="coupling=True"):
        bare.couple_working([float.fromhex(v) for v in rec["vals"]])
    with pytest.raises(ValueError, match="error_correction=True"):
        bare.carry([1, 0, 1, 1], n=3)
    # ... and the addressing CORE is answerable either way — the gates are on the
    # value layers only, so the nine-D probe gate above never needed them.
    assert bare.navmap(1) == cascade.cd_navmap(16, 1)


def test_the_record_comparison_actually_fires():
    """A guard that cannot fail is not a guard. Perturb one field of one recorded
    probe and prove the comparison the gate uses reports it — the fixture is
    read-only on disk, so the perturbation is in memory."""
    recorded = [dict(p) for p in probes_for(1024)]
    live = _replay_probes(1024)
    assert [(p["got_key"], p["got_sign"]) for p in live] \
        == [(p["got_key"], p["got_sign"]) for p in recorded]
    recorded[57]["got_sign"] = -recorded[57]["got_sign"]
    assert [(p["got_key"], p["got_sign"]) for p in live] \
        != [(p["got_key"], p["got_sign"]) for p in recorded], (
        "flipping a recorded Class-C sign did not change the comparison — the "
        "nine-D gate would pass against a corrupted record")
