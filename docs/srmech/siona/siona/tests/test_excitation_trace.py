"""Excitation trail (F1206 melange signature) — opt-in, off by default.

A traced turn records which genome pieces lit up: the intent route, the reply mode expressed from the
context genome, the per-owner ground-hits (which anchors/tools the query excited + similarity), and the
attestation sources the reply points at. OFF by default = identical behavior + zero overhead. numpy-free;
no abs builtin; no Counter. One module-scoped Session (construction is ~expensive; toggle trace per test)."""
import json

import pytest

from siona.infer import Session


@pytest.fixture(scope="module")
def sess():
    return Session()


def test_trace_off_by_default_is_unchanged(sess):
    sess.disable_trace()
    assert sess.trace is None                     # off
    out = sess.turn("define cascade")
    assert isinstance(out, tuple) and len(out) == 3   # turn still returns (intent, tag, output)
    assert sess.trace is None                     # nothing collected when off


def test_enable_trace_records_one_per_turn_with_all_fields(sess):
    sess.enable_trace()                           # resets sess.trace = []
    utts = ["define cascade", "define resonator", "define chirality"]
    for u in utts:
        sess.turn(u)
    assert len(sess.trace) == len(utts)           # one record per turn
    need = {"utterance", "intent", "tag", "mode", "excited", "sources", "reply"}
    for rec in sess.trace:
        assert need <= set(rec)
        assert isinstance(rec["excited"], list)
        assert isinstance(rec["mode"], list)


def test_trace_captures_ground_excitation(sess):
    sess.enable_trace()
    sess.turn("define cascade")
    lit = [rec for rec in sess.trace if rec["excited"]]
    assert lit, "a define turn grounds the term -> ground-hits must be recorded"
    hit = lit[0]["excited"][0]
    assert "owner" in hit and "hits" in hit
    assert hit["hits"] and len(hit["hits"][0]) == 2   # [similarity, tool/anchor name]


def test_ndjson_sink(sess, tmp_path):
    p = tmp_path / "trace.ndjson"
    sess.enable_trace(path=str(p))
    for u in ("define cascade", "define resonator"):
        sess.turn(u)
    lines = [json.loads(ln) for ln in p.read_text(encoding="utf-8").splitlines() if ln.strip()]
    assert len(lines) == 2
    assert lines[0]["utterance"] == "define cascade"


def test_disable_trace_detaches(sess):
    sess.enable_trace()
    sess.turn("define cascade")
    sess.disable_trace()
    assert sess.trace is None and sess.g._hits is None
    sess.turn("define cascade")                   # still works with tracing off
