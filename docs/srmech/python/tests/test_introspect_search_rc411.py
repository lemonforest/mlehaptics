"""rc411 (`#T1086`) — the introspect INDEX acceptance gate.

WHAT THIS GATES
===============
The introspect layer's authored half is at 100% and, before this rc, its derived
half was at 0%. ``ToolEntry.explanation`` and ``ToolEntry.example`` are both
floor-enforced at 100% by ``test_tool_docs_coverage_rc240.py:52,:62`` — and no
accessor read either one. ``ToolSchema.resolve`` reads ``name``, and only whole
dotted segments of it.

So the registry could answer *"what is the op called X"* and could not answer
*"what do you have for X"*. This file pins the second question.

**At rc410 every test below fails with ``ModuleNotFoundError`` — there is no
such surface.** That is the non-vacuity argument, and it is structural rather
than asserted: the module did not exist.

WHY THE CORPUS ASSERTION IS "IN THE RETURNED SET", NOT "AT RANK 1"
==================================================================
Two of these needs are answered by a POINTER inside a neighbouring op's prose
rather than by their own registry row, and that is a property of the corpus, not
a weakness of the query:

* **matrix rank** — ``0`` registered op NAMES contain ``rank``, because
  ``QMat.rank`` is a carrier METHOD and the registry indexes module-level ops
  only (``describe()['tools']['covers']`` says so deliberately). The answer is
  nevertheless written down, with its file and line, inside other ops'
  explanations. Measured on this tree: ``qmat.rank`` appears in **7 of 585**
  frames, and a ``k=25`` search for *"rank of a matrix"* returns **6 of those
  7**.
* **the exact rational type** — the caller's error is a MODULE PATH
  (``srmech.math.rational.Q`` for ``srmech.math.q.Q``), and the correction ships
  inside ``example.worked`` import lines.

Asserting rank 1 for those would be asserting a property of one authored
paragraph. Asserting *the answer-bearing row is returned* is the retrieval claim
actually being made, and it is the one that survives a prose edit.

⚠️ EVERY RANK IN THIS FILE IS IN-SAMPLE. The scorer (df gate as ``Q(N-df, df)``,
a 4x name-leaf boost) was measured against these same queries. The defensible
claim is *"the mechanism composes from shipped ops and returns the target at
all"*, NOT the exact ordinal. A HELD-OUT query set is required before any rank
number here is defended as a quality measurement — see the follow-on in
CHANGELOG rc411.
"""
from __future__ import annotations

import pytest

from srmech.introspect.search import search
from srmech.introspect.search import _build_frames
from srmech.introspect.tool_schema import get_tool_schema, warmup_all
from srmech.math.q import Q

warmup_all()


#: (need as felt, the answer token, where it is allowed to be found).
#:
#: ``"record"`` — the token must appear in a returned record's own
#: name / why / reach, i.e. the row IS the answer.
#: ``"frame"``  — the token must appear in a returned row's indexed text, i.e.
#: the answer is a pointer the caller can read off the hit.
CORPUS = (
    ("log base 2 of 3/2 exactly", "srmech.math.rational.log", "record"),
    ("greatest common divisor", "srmech.math.cyclic.gcd", "record"),
    ("find zero divisors", "cd_zero_divisor_witness", "record"),
    ("get the tool registry", "get_tool_schema", "record"),
    ("which surface lists ops", "srmech.introspect.describe", "record"),
    ("rank of a matrix", "qmat.rank", "frame"),
    ("the exact rational type", "srmech.math.q", "frame"),
)

_K = 25


def _frames_by_name():
    frames, _witness = _build_frames("all")
    return {f.name: f for f in frames}


def test_the_retrieval_corpus_is_answered() -> None:
    """Every corpus need returns its answer within k=25. STRICT ZERO."""
    by_name = _frames_by_name()
    unanswered = []
    for need, answer, where in CORPUS:
        hits = search(need, k=_K)
        if where == "record":
            ok = any(answer in (h["name"] + h["why"] + h["reach"]).lower()
                     for h in hits)
        else:
            ok = any(answer.encode("utf-8") in by_name[h["name"]].blob
                     for h in hits)
        if not ok:
            unanswered.append(f"{need!r} -> {answer!r} ({where})")
    assert not unanswered, (
        f"{len(unanswered)} of {len(CORPUS)} corpus needs are unanswered at "
        f"k={_K}:\n  " + "\n  ".join(unanswered))


def test_the_control_that_motivated_the_arc() -> None:
    """``resolve`` is CORRECT AS IS — this is not a bug report against it.

    ``resolve('winding')`` returning ``None`` is the documented whole-segment
    contract, and the index does not change it. The point is that the same felt
    word now reaches the op through a different accessor.
    """
    assert get_tool_schema().resolve("winding") is None
    hits = search("winding number", k=10)
    assert any("winding" in h["name"] for h in hits), (
        "the felt word 'winding' reaches no op through the index either")


def test_the_registry_contains_its_own_front_door() -> None:
    """Need 6, closed BY CONSTRUCTION rather than by ranking.

    Before rc411 the name ``get_tool_schema`` matched 0 registered entries: the
    function that RETURNS the registry was not IN it.
    """
    schema = get_tool_schema()
    for name in ("srmech.introspect.search.search",
                 "srmech.introspect.tool_schema.get_tool_schema",
                 "srmech.introspect.tool_schema.tool_schema_view"):
        assert schema.resolve(name) is not None, f"{name} is not registered"
    assert schema.resolve("get_tool_schema") is not None
    assert schema.resolve("tool_schema_view") is not None
    assert schema.resolve("search") is not None


def test_every_record_carries_why_and_reach() -> None:
    """ADR-0012 — the answer must be actionable without a second call.

    A record with an empty ``why`` or ``reach`` fails the autonomous-composition
    standard even though it names the right op, so both are asserted non-empty
    rather than merely present as keys.
    """
    bad = []
    for need, _answer, _where in CORPUS:
        for h in search(need, k=5):
            if not h["why"].strip():
                bad.append(f"{need!r} -> {h['name']}: empty why")
            if not h["reach"].strip():
                bad.append(f"{need!r} -> {h['name']}: empty reach")
    assert not bad, "\n  ".join([f"{len(bad)} record(s) are not actionable:"] + bad)


def test_why_names_a_field_and_carries_the_excerpt() -> None:
    """``why`` is ``"<field>: <matched excerpt>"``. The excerpt half is the
    load-bearing one — a bare field label still forces the second call."""
    for h in search("greatest common divisor", k=5):
        assert ": " in h["why"], f"why has no excerpt: {h['why']!r}"
        field = h["why"].split(":", 1)[0]
        assert field in ("name", "category", "summary", "explanation") or (
            field.startswith("example.") or field.startswith("carrier.")), (
            f"why names an unknown field: {field!r}")


def test_reach_is_an_importable_call_form() -> None:
    """``reach`` must actually import. A paste-ready string that does not run is
    worse than no string, because it costs the caller a debugging round."""
    for need in ("greatest common divisor", "winding number"):
        for h in search(need, k=5):
            if h["kind"] != "op":
                continue
            assert h["reach"].startswith("from "), h["reach"]
            module, _, leaf = h["reach"][len("from "):].partition(" import ")
            mod = __import__(module, fromlist=[leaf])
            assert hasattr(mod, leaf), f"{h['reach']} does not resolve"


def test_scores_are_exact_rationals_never_floats() -> None:
    """Cascade-honesty: the idf is ``Q(N-df, df)`` and ``top_k_by_score`` takes
    the exact ``Q`` directly, so no float enters the chain."""
    for h in search("greatest common divisor", k=10):
        assert isinstance(h["score"], Q), (
            f"score is {type(h['score']).__name__}, expected exact Q")
        assert not isinstance(h["score"], float)


def test_scores_are_monotone_non_increasing() -> None:
    """The records are RANKED. Exact-Q comparison, no tolerance needed."""
    hits = search("exact rational matrix", k=20)
    assert len(hits) >= 2, "need at least two records to check ordering"
    for a, b in zip(hits, hits[1:]):
        assert a["score"] >= b["score"], (
            f"ranking is not monotone: {a['name']} {a['score']} then "
            f"{b['name']} {b['score']}")


def test_a_no_match_query_returns_empty_not_padding() -> None:
    """The distinction between "we have nothing" and "here is some noise" is
    not recoverable by the caller from a padded list, so it is preserved.

    The control tokens are DERIVED from the corpus, not hard-coded, and the two
    failures that forced that are both worth recording because they are the same
    mistake from opposite directions:

    1. The first draft used the word "token", which occurs in 19 frames. The
       test "failed" against entirely correct behaviour.
    2. The second draft hard-coded nonsense tokens AND demonstrated the miss
       with those literals in the op's own worked example. **This file's corpus
       contains that example**, so the tokens became real, the absence guard
       fired, and the documented ``-> ()`` in the shipped example was false.

    That second one is the interesting failure mode: an index whose own
    documentation is inside the corpus it searches cannot use a literal
    never-matches token anywhere it publishes. Deriving the token at run time is
    the only form that stays true, because it is chosen AFTER the corpus exists.
    """
    frames, _witness = _build_frames("all")
    blobs = [f.blob for f in frames]
    absent = []
    for i in range(64):
        candidate = f"zq{i}wvx{i}kj".encode("ascii")
        if not any(candidate in b for b in blobs):
            absent.append(candidate)
        if len(absent) == 3:
            break
    assert len(absent) == 3, (
        "could not derive three corpus-absent control tokens — either the "
        "corpus is pathological or the generator needs widening")
    hits = search(" ".join(t.decode() for t in absent), k=10)
    assert hits == (), f"expected an empty result, got {len(hits)} records"


def test_the_witness_is_stable_across_rebuilds() -> None:
    """ADR-0011's cache-vs-witness admissibility condition: the derived view
    carries a content-address of the source, so disagreement is loud.

    Nothing is persisted — the second build is a genuinely independent rebuild,
    which is what makes agreement meaningful.
    """
    _f1, w1 = _build_frames("all")
    _f2, w2 = _build_frames("all")
    assert w1 == w2, "the frame witness is not reproducible"
    assert len(w1) == 64, f"expected a sha256 hex digest, got {len(w1)} chars"
    assert search("gcd", k=1).witness == w1


def test_the_witness_moves_when_the_corpus_moves() -> None:
    """⚠️ NON-VACUITY. A witness that cannot disagree is not a witness.

    Scoping to ``ops`` drops the carrier frames, so a witness that did not move
    would prove it was not reading the corpus at all.
    """
    _f_all, w_all = _build_frames("all")
    _f_ops, w_ops = _build_frames("ops")
    assert w_all != w_ops, (
        "the witness is identical across two different corpora — it is not "
        "content-addressing anything")


@pytest.mark.parametrize("scope,kinds", [
    ("ops", {"op"}),
    ("carriers", {"carrier"}),
])
def test_scope_selects_the_registry(scope, kinds) -> None:
    hits = search("exact rational matrix", k=10, scope=scope)
    assert hits, f"scope={scope!r} returned nothing"
    assert {h["kind"] for h in hits} <= kinds


def test_rejects_bad_arguments() -> None:
    """A clean typed decline, per ADR-0003 §2.1 / ADR-0006 §2.6."""
    with pytest.raises(TypeError):
        search(None)
    with pytest.raises(ValueError):
        search("gcd", scope="nonsense")
    with pytest.raises(ValueError):
        search("gcd", k=0)


def test_the_index_is_a_fixed_point_over_itself() -> None:
    """Self-reference is precedent, not a problem: ``describe`` is already a
    registered row. State it as a fixed point — the total includes the index,
    and a query for the index returns the index."""
    hits = search("need-shaped index over the registries", k=10)
    assert any(h["name"] == "srmech.introspect.search.search" for h in hits), (
        "the index does not return itself")
