"""The search tokenizer segments GLYPHS, not ASCII runs (`#T1102`, rc416).

THE DEFECT, AND WHY IT WAS WORSE THAN A DROP
============================================
``srmech/introspect/search.py`` accumulated ``ch.isalnum() and ch.isascii()``
until rc416. Three of the four Latin-shaped assumptions that got
``srmech.math.text.tokenize`` DELETED at rc287 had reassembled inside the one
runtime-reachable discovery surface: a length floor of 2 CODEPOINTS, a
universal ``lower()``, and an ``isascii()`` gate harder than anything the
retired tokenizer carried.

Measured at rc415, and each of these is a test below:

* ``_tokenize('中 国')``  → ``()`` — the exact content deletion ``README:311``
  names as the reason ``tokenize`` was removed;
* ``search('ℚ')``        → 0 rows, in a corpus holding ``ℚ`` in 51 frames;
* ``search('groß')``     → ``group_algebra_table``, confidently.

The last one is the whole point and is why this shipped rather than waiting.
``'groß'`` truncated to the needle ``b'gro'``, which is a perfectly valid
needle, so the caller received three real rows about group algebra with real
scores. Not a decline — a **confident wrong answer**. ``'élevée'`` did the
same via ``b'lev'`` and landed on ``gene_express_levels``.

It also broke two contracts the module states about itself:

* :func:`~srmech.introspect.search.search` documents that an EMPTY result
  means *"we have nothing for this."* For a non-ASCII query it meant *"this
  instrument cannot express your query"* — UNSUPPORTED reported as EMPTY,
  which a caller cannot recover
  (``[[feedback_an_instrument_that_cannot_return_otherwise_is_not_a_measurement]]``).
* ``_as_text`` refuses ``json.dumps`` explicitly so the corpus keeps ``ℚ``,
  ``𝕆``, ``Σ`` and ``→`` searchable. That care was 100% cancelled two
  functions above it.

WHAT IS ASSERTED HERE
=====================
The four acceptance criteria, plus the properties the fix must not break:

1. ``search('ℚ')`` returns rows;
2. the ASCII benchmark (``grapheme`` / ``okina`` / ``virama`` / ``GB9c``)
   keeps its top-k — the fix must not buy recall with regression;
3. the corpus witness is re-pinned HERE, so the next edit that moves it is a
   deliberate act;
4. **the truncation witness** — ``search('groß')`` must not confidently return
   ``group_algebra_table``.

Plus the alignment property that makes folding safe (BOTH sides fold, so a
folded query token is findable in folded corpus bytes) and the ASCII
short-circuit's correctness proof (``fold_marks`` is the identity over the
whole ASCII domain, so skipping it there is value-preserving by construction
rather than an optimisation guess).
"""
from __future__ import annotations

import pytest

from srmech.introspect import search as S
from srmech.introspect.search import _index_fold, _tokenize, search
from srmech.math.text import fold_marks, glyph_stream

#: The corpus content-address at rc416. Order-dependent by construction: any
#: add, removal, reorder or prose edit moves it. rc415's was
#: ``298e2939ca1156b9f2f4a75f4e64a0b9fc537ad4c14ecd127449fd31ce99004b``; rc416
#: moves it because BOTH sides of the index now fold, and that IS the edit.
#:
#: **RE-PINNED at v0.9.0rc419 (`#T1110`).** rc416's value was
#: ``cd067fe2f4d4e9bb2dbae1838b853273d0d70b79795858135849c2b40d5874df``. It
#: moved because rc419 registered NINE ``srmech.signal_processing`` rows
#: (560 -> 569 ops is the visible part; the corpus is built from ToolEntry
#: prose, so nine new frames plus the README / docstring edits in the same rc
#: are all inside the digest) — a PROSE edit, which is the branch this
#: constant's own failure message names as "re-pin".
#:
#: The other branch — non-determinism, which WOULD break the ADR-0011 witness
#: contract — was ruled out by measurement, not by assumption: the identical
#: digest was produced by all four native CI cells (ubuntu py3.10, ubuntu
#: py3.12, macos-14 py3.12, windows py3.12), the pure shards, and a local
#: WSL2 re-derivation. Five independent builds, one hash. The contract holds;
#: only the corpus moved.
WITNESS_RC416 = (
    "86689a98927ca61774d63dc4677fd11591007da072a88fa344950c3aeef251dd")

#: The ASCII control set. These four queries are the ops the tokenizer work is
#: ABOUT, so a regression on them would be the change eating its own subject.
ASCII_BENCHMARK = {
    "grapheme": ("srmech.math.text.glyph_stream",),
    "okina": ("srmech.math.text.glyph_stream",),
    "virama": ("srmech.math.text.fold_marks", "srmech.math.text.glyph_stream"),
    "GB9c": ("srmech.math.text.glyph_stream",),
}


def _names(result):
    return [row["name"] for row in result]


# ── 1. the tokenizer no longer deletes or truncates ─────────────────────────

def test_the_rc287_deletion_case_is_recovered():
    """``README:311`` names ``tokenize('中 国') == []`` by hand as the content
    deletion that got the word tokenizer removed. It was live again here."""
    assert _tokenize("中 国") == ("中".encode(), "国".encode())


def test_a_single_glyph_query_is_answerable_at_all():
    """``_MIN_GLYPHS`` is 1, and 2 is not available: both halves of ``中 国``
    are one-glyph tokens, so a floor of 2 returns ``()`` and reproduces the
    rc287 deletion exactly. The old floor was buying a SCAN, not an answer —
    a one-glyph token that is in every frame scores ``Q(N-N, N) == 0``
    exactly, so it contributes nothing rather than noise."""
    assert S._MIN_GLYPHS == 1
    for one in ("中", "ℚ", "π", "9"):
        assert _tokenize(one), f"{one!r} tokenizes to nothing"


def test_no_query_is_silently_truncated():
    """THE TRUNCATION WITNESS at token level. A prefix is a valid needle, so a
    truncated token does not decline — it answers, wrongly and confidently."""
    assert _tokenize("groß") == ("groß".encode(),)
    assert _tokenize("groß")[0] != b"gro"
    assert _tokenize("élevée")[0] != b"lev"
    assert _tokenize("élevée") == ("elevee".encode(),), (
        "the mark fold is what makes 'élevée' reach 'elevee'; a TRUNCATION to "
        "'lev' is a different thing entirely")


def test_notation_the_corpus_is_full_of_is_tokenizable():
    """``search.py``'s own ``_as_text`` names these four as the characters the
    corpus preserves on purpose. Three are LETTERS and now tokenize; ``→`` is
    a SYMBOL and deliberately does not — asserted, so the cost is recorded
    rather than discovered.

    Compared against ``_index_fold(glyph)`` and not against the raw glyph,
    because ``Σ`` lowercases to ``σ`` and the corpus side lowercases too — the
    token has to match what the FRAME holds, not what the caller typed.
    """
    for glyph in ("ℚ", "𝕆", "Σ", "δ", "π"):
        assert _tokenize(glyph) == (_index_fold(glyph).encode(),), glyph
    assert _tokenize("→") == (), (
        "Symbol (S*) is a token separator by design — admitting Sm would fuse "
        "'a+b' and 'x=1' into single tokens across the ASCII corpus")


def test_underscores_still_split():
    """The one behaviour the property set is deliberately narrowed to keep.
    UTS #18's word-character class includes Connector_Punctuation; this table
    does not, because ``search`` documents and depends on the query
    ``"top k score"`` reaching ``top_k_by_score``."""
    assert _tokenize("top_k_by_score") == (b"top", b"k", b"by", b"score")


def test_a_grapheme_cluster_is_one_decision():
    """A cluster is classified by its BASE and travels whole. The keycap is
    the case a hand-rolled ASCII/non-ASCII split gets wrong: its base is the
    ASCII digit ``1`` while the cluster carries U+FE0F and U+20E3."""
    assert len(glyph_stream("1️⃣")) == 1
    assert _tokenize("1️⃣") == (b"1",)
    assert _tokenize("Hawaiʻi") == ("hawaiʻi".encode(),), (
        "U+02BB MODIFIER LETTER TURNED COMMA is Lm — a LETTER — so the "
        "Hawaiian okina must stay inside its word")
    # ...while U+2019 RIGHT SINGLE QUOTATION MARK is Pf and correctly splits.
    # These are different characters; the README's '’okina' example is the
    # typographic apostrophe, and glyph_stream keeping it is a LOSSLESSNESS
    # guarantee, not a claim that a tokenizer should treat it as a letter.
    assert _tokenize("’okina") == (b"okina",)


# ── 2. the fold is aligned on BOTH sides ────────────────────────────────────

def test_fold_marks_is_the_identity_over_the_whole_ascii_domain():
    """The PROOF the ASCII short-circuit in ``_index_fold`` rests on.

    No codepoint below U+0080 is General_Category Mn/Mc/Me and none carries a
    canonical decomposition containing a mark, so skipping the call for ASCII
    input cannot change a value. Asserted over the whole domain rather than
    sampled — a sampled check could miss exactly the one that moved.
    """
    ascii_all = "".join(chr(c) for c in range(0x80))
    assert fold_marks(ascii_all) == ascii_all
    for c in range(0x80):
        assert _index_fold(chr(c)) == chr(c).lower(), f"U+{c:04X}"


def test_both_sides_of_the_index_pass_through_the_same_fold():
    """The alignment contract. Folding the QUERY only would make the fold a
    mismatch generator: a folded token cannot be found in unfolded bytes."""
    frames, _witness = S._build_frames("ops")
    marked = "क्षि"
    folded = _index_fold(marked)
    assert folded != marked, "the sample must actually move under the fold"
    # the query side folds...
    assert _tokenize(marked)[0] == folded.encode()
    # ...and the corpus side folds to the same bytes, so the needle is found.
    hay = b"".join(f.blob for f in frames)
    assert folded.encode() in hay, (
        "the folded query token is absent from the folded corpus — the two "
        "sides of the index have drifted apart")


def test_the_fold_is_lower_not_casefold():
    """``str.lower()`` is the locale-INDEPENDENT map. ``casefold`` unifies
    pairs some locales hold distinct (Turkish I/ı), which would make the index
    locale-DEPENDENT in the name of being more thorough."""
    assert "I".casefold() == "i" and "ı".casefold() == "ı"
    assert _called_attributes(S.__file__).isdisjoint({"casefold"}), (
        "search.py must not casefold — see _index_fold's docstring")
    # The one case fold_marks-before-lower exists to repair:
    assert _index_fold("İSTANBUL") == _index_fold("istanbul")


def _called_attributes(path):
    """The set of attribute names this module actually CALLS.

    An ``ast`` walk, not a text scan, and that is the point rather than
    fastidiousness: both files below DISCUSS the banned calls at length in
    their docstrings, so a ``grep``-shaped guard would fire on the prose
    explaining why the call is banned. That is the same
    exempt-the-code-span lesson the ref-notation ratchet already carries.
    """
    import ast

    with open(path, encoding="utf-8") as fh:
        tree = ast.parse(fh.read(), path)
    return {node.func.attr for node in ast.walk(tree)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)}


def test_nothing_asks_the_host_to_classify_a_codepoint():
    """``str.isalnum()`` / ``str.isalpha()`` pin the answer to the RUNNING
    interpreter's UCD (13.0.0 here against the vendored tables' 16.0.0) and a
    bare-C host cannot ask them at all — two projections on different data,
    the ADR-0009 forbidden shape.

    ``str.isascii()`` is deliberately NOT in this ban: it is a codepoint-RANGE
    test carrying no Unicode data, so the compiled projection makes the
    identical decision on ``byte < 0x80``.
    """
    import srmech.rbs_lm.grounding as G

    banned = {"isalnum", "isalpha", "isdigit", "isnumeric", "isdecimal",
              "casefold"}
    for module in (S, G):
        called = _called_attributes(module.__file__)
        hits = sorted(called & banned)
        assert not hits, (
            f"{module.__name__} calls {hits} — use the vendored word-kind "
            f"table (srmech.math.text._word_kind_cp)")


# ── 3. the four acceptance criteria ─────────────────────────────────────────

def test_acceptance_search_for_a_non_ascii_glyph_returns_rows():
    result = search("ℚ", k=5)
    assert len(result) > 0, (
        "search('ℚ') returns nothing while the corpus holds ℚ in 51 frames — "
        "the index cannot express a query in the notation it is written in")
    assert result.witness == WITNESS_RC416


def test_acceptance_the_truncation_witness():
    """THE one that matters: ``search('groß')`` must not confidently answer.

    At rc415 it returned ``group_algebra_table`` /
    ``ground_state_flux_response`` / ``cd_three_form`` — three real rows with
    real scores, about group algebra, for a German word. EMPTY here is the
    CORRECT answer and now means what :func:`search` says it means: the corpus
    genuinely holds nothing for ``groß``.
    """
    names = _names(search("groß", k=5))
    assert "srmech.cascade.group_algebra_table" not in names, (
        "search('groß') still reaches group_algebra_table — the query is "
        "being truncated to a prefix and answered confidently")
    assert names == [], (
        f"search('groß') should be EMPTY (nothing in the corpus matches the "
        f"whole token); got {names}")


@pytest.mark.parametrize("query", sorted(ASCII_BENCHMARK))
def test_acceptance_the_ascii_benchmark_keeps_its_top_k(query):
    """Recall must not be bought with regression. These four resolved to the
    text family at rc415 and must still."""
    expected = ASCII_BENCHMARK[query]
    got = _names(search(query, k=5))
    assert tuple(got[:len(expected)]) == expected, (
        f"search({query!r}) top-{len(expected)} moved: {expected} -> {got}")


def test_acceptance_the_corpus_witness_is_repinned():
    """The witness is the Class-A content-address of the frame set. It moves
    when the corpus prose moves — which is the point — so it is pinned here
    rather than left to drift silently."""
    assert search("rank", k=1).witness == WITNESS_RC416, (
        "the corpus witness moved. If a prose edit caused it, re-pin "
        "WITNESS_RC416; if nothing was edited, the frame build is "
        "non-deterministic, which would break the ADR-0011 witness contract.")


def test_scope_witnesses_agree_with_the_union():
    """``scope='ops'`` and ``scope='carriers'`` build sub-corpora; the union
    must be the witness above, or the witness is not a witness."""
    from srmech.amsc.format import sha256_bytes

    ops, _ = S._build_frames("ops")
    carriers, _ = S._build_frames("carriers")
    both, witness = S._build_frames("all")
    assert len(both) == len(ops) + len(carriers)
    assert sha256_bytes(b"".join(f.blob for f in both)) == witness
    assert witness == WITNESS_RC416


# ── 4. an EMPTY result now means what the module says it means ─────────────

def test_empty_now_means_absent_not_inexpressible():
    """rc415 could not tell a caller apart from a corpus. A CJK query returned
    EMPTY because the tokenizer could not express it; now it returns EMPTY
    because the corpus genuinely has no CJK — and the token that proves the
    difference is reachable."""
    tokens = _tokenize("中 国")
    assert tokens, "the query is expressible"
    frames, _ = S._build_frames("all")
    hay = b"".join(f.blob for f in frames)
    for token in tokens:
        assert token not in hay, (
            "the corpus DOES contain this token, so EMPTY would now be wrong "
            "for a different reason — re-derive this test")
    assert _names(search("中 国", k=5)) == []
