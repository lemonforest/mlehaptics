"""rc464 (`#T1188`) — the golden fixture IS what the shipped class did.

THIS MODULE IS DELETED WITH THE CLASS. It exists for exactly one window: the
one in which ``CDRegister`` has already taken over as the register shape and is
gated against ``tests/sedenion_register_golden_rc464.ndjson``, while the
``SedenionRegister`` that fixture was recorded from is still importable.

The rest of the arc rests on the fixture being a faithful recording. Everything
downstream compares the SUBJECT to the record; nothing downstream can compare the
record to the ORACLE, because the oracle is going away. So the one measurement
that can only be made now is made now, in CI rather than on the machine that ran
the generator: replay the recorded protocol against the live class and require
the recorded answers.

If this fails, the fault is in the recording — ``docs/srmech/notes/
_golden_sedenion_register_rc464.py`` — and not in ``CDRegister``. That is the
whole reason it is a separate module with a separate name.
"""

from __future__ import annotations

import pytest

from srmech.amsc.format import sha256_bytes
from srmech.cascade.sedenion_register import SedenionRegister, sedenion_register
from srmech.math.hdc import bind

from tests._golden_sedenion import (
    GOLDEN_D_VALUES,
    GOLDEN_KEYS,
    golden_header,
    int_keyed,
    load_golden,
    probes_for,
)


@pytest.mark.parametrize("D", GOLDEN_D_VALUES)
def test_the_live_class_reproduces_its_own_recorded_probes(D):
    """The recorded protocol, replayed against the class it was recorded from."""
    recorded = probes_for(D)
    idx = 0
    for j in range(1, 16):
        r = sedenion_register(D=D)
        for i, k in enumerate(GOLDEN_KEYS):
            r.write(i, k)
        nav = r.navmap(j)
        moved = r.navigate(j)
        for i, k in enumerate(GOLDEN_KEYS):
            want = recorded[idx]
            idx += 1
            dest, sign = nav[i]
            assert (j, i, k, dest, sign) == (
                want["j"], want["i"], want["key"], want["dest"],
                want["sign_expected"]), "the recorded probe ORDER is not the protocol"
            assert list(moved.read(dest)) == [want["got_key"], want["got_sign"]], (
                f"the fixture does not record what the class does at D={D}, j={j}, "
                f"slot {i} — the RECORDING is wrong, not the subject")
    assert idx == 120


def test_the_live_class_reproduces_its_own_recorded_bytes_and_value_ops():
    """Storage digests, navmaps, routing, coupler words and every single-bit
    Hamming correction — the non-probe half of the fixture, in one pass."""
    r16 = SedenionRegister()
    for rec in load_golden()["navmap"]:
        assert r16.navmap(rec["j"]) == {
            int(i): tuple(v) for i, v in rec["map"].items()}

    for rec in load_golden()["navigate"]:
        r = SedenionRegister(D=512)
        for slot, key, sign in rec["occupancy"]:
            r.write(slot, key, sign=sign)
        assert r.navigate(rec["j"]).slots() == {
            int(s): (k, g) for s, (k, g) in rec["routed"].items()}

    for rec in load_golden()["couple"]:
        vals = [float.fromhex(v) for v in rec["vals"]]
        word = r16.couple_working(vals)
        assert [float(v).hex() for v in word] == rec["word"]
        assert [float(v).hex() for v in r16.uncouple_working(word)] == rec["uncoupled"]

    for rec in load_golden()["carry"]:
        assert r16.carry(rec["data"], n=rec["n"]) == rec["codeword"]
    for rec in load_golden()["correct"]:
        assert r16.correct(rec["codeword"]) == rec["result"]

    rec = load_golden()["reads"][0]
    rr = SedenionRegister(D=rec["D"])
    for s, sign in int_keyed(rec["occupancy"]).items():
        rr.write(s, f"v{s}", sign=sign)
    assert {str(s): list(rr.read(s)) for s in range(16)} == rec["reads"]

    for rec in load_golden()["storage"]:
        r = SedenionRegister(D=rec["D"])
        for slot, key, sign in rec["writes"]:
            r.write(slot, key, sign=sign)
        bundle = r.materialize()
        assert sha256_bytes(bundle) == rec["materialize_sha256"]
        assert {str(s): sha256_bytes(bind(r._addr(s), bundle))
                for s in range(16)} == rec["unbind_sha256"]
        assert {str(s): list(r.read(s)) for s in range(16)} == rec["reads"]


def test_the_header_names_the_class_that_is_actually_here():
    """Provenance is only provenance if it points at something. While the class
    exists, the dotted name in the header must resolve to it."""
    import importlib
    mod_name, _, cls_name = golden_header()["oracle"].rpartition(".")
    assert getattr(importlib.import_module(mod_name), cls_name) is SedenionRegister
