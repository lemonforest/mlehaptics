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
#:
#: **RE-PINNED AGAIN at v0.9.0rc420 (`#T1114`).** rc419's value was
#: ``cc1d93e6bb901ef5d52d28a895771b502ec5b32b1888b14e7e381f472262d7fa``. Two
#: prose edits in the same rc moved it, both inside the corpus by
#: construction: rc420 registered **29** new ops for the executable cascade
#: catalog (569 -> 598, and the frame set is 627 = 598 ops + 29 carriers), and
#: the rc420 CI-red fix corrected three shipped docstring falsehoods in the
#: curated tool docs (``list_ops``'s ``returns`` shape, one additive key
#: behind after ``list_catalog_ops`` gained ``status``). Both are the "re-pin"
#: branch of this constant's own failure message, not the drift branch.
#:
#: Determinism re-established independently at this value: the identical
#: digest came from all four native CI cells, the pure shards, the
#: fork-isolated asserts-live cell, AND a local WSL2 re-derivation on the
#: branch. **Seven independent builds, one hash.**
#:
#: **RE-PINNED AGAIN at v0.9.0rc421 (`#T1122`).** rc420's value was
#: ``4200c5fbf84bb2b2d6d57816fa7f77abfeed23a4c9e50645c3cffb714d9e525f``. rc421
#: registers NO new op (the frame set is unchanged at 627 = 598 ops + 29
#: carriers, and ``describe()['tools']['total']`` is untouched) — this move is
#: PURE PROSE: `octonion_frame_read`'s ToolEntry summary + its ``frame``
#: parameter text, which said "frame defaults to 4 and any other value
#: raises" and is now false, plus the paired curated explanation/example.
#: Same "re-pin" branch of this constant's own failure message.
#:
#: ⚠️ **This is the FOURTH consecutive re-pin (rc416 → rc419 → rc420 → rc421),
#: and rc421 is the first where `tools/ripple_check.py` was RUN and went GREEN
#: anyway** (388 passed) while CI went red on these three tests — because this
#: file was not in `tools/ripple_gates.txt`. ToolEntry prose IS a dispatch
#: surface and the corpus is BUILT FROM IT, so any rc that edits a ToolEntry
#: moves this digest by construction. rc421 adds this file to the manifest and
#: freezes it in `FROZEN_KNOWN_GATES`, so the next prose rc learns it in ~13 s
#: instead of after a ~25 min full-suite round.
#:
#: Determinism re-established independently at this value BEFORE re-pinning:
#: five successive local `_build_frames('all')` builds produced one hash, and
#: all four native CI cells plus pure shard 6 reported this identical digest in
#: their failure output. The drift branch is ruled out by measurement, again.
#:
#: **RE-PINNED AGAIN at v0.9.0rc422 (`#T1123`).** rc421's value was
#: ``4200c5fbf84bb2b2d6d57816fa7f77abfeed23a4c9e50645c3cffb714d9e525f``. This
#: is the FIFTH consecutive re-pin, and the first of the two kinds this
#: constant distinguishes that is NOT pure prose: rc422 registers **seven new
#: ops** — the five ``srmech.math.covering`` centre/covering ops and the two
#: ``Z(Spin(8))`` rep-kernel anchor ops — so the frame set moves
#: **627 -> 634 = 605 ops + 29 carriers** and
#: ``describe()['tools']['total']`` moves 598 -> 605. Seven new ToolEntry
#: summaries plus seven new curated explanation/example/worked blocks all land
#: in the corpus by construction. Still the "re-pin" branch of this constant's
#: own failure message, but for the population reason rather than the prose
#: one — and rc421's manifest entry did its job: `tools/ripple_check.py`
#: surfaced this locally instead of a CI round.
#:
#: Determinism re-established independently at this value BEFORE re-pinning:
#: five successive local `_build_frames('all')` builds on WSL2 (numpy-absent)
#: produced one hash, with `len(frames) == 634` each time.
#:
#: **RE-PINNED AGAIN at v0.9.0rc423 (`#T1113`).** rc422's value was
#: ``989dd20b28080ea9af75b9e142053f30c1f614e90751fbdd728eab93b4714056``. This
#: is the SIXTH consecutive re-pin, and it is a THIRD kind — neither new prose
#: nor new ops, but new **structured metadata on existing rows**. rc423's
#: composes POPULATION pass takes ``composes`` from 16/605 to 164/605, and
#: ``search.py::_op_fields`` has indexed that field since rc412, so 148 rows
#: that previously contributed no ``composes`` frame-field now contribute one.
#: The frame COUNT is unchanged at **634 = 605 ops + 29 carriers** — no op was
#: registered — and ``describe()['tools']['total']`` stays **605**. Only the
#: frame CONTENTS moved. That is worth naming: a witness move with a flat
#: frame count is the signature of a metadata rc, and reading it as prose
#: drift or as a registration would send the next author looking in the wrong
#: place.
#:
#: Determinism re-established independently at this value BEFORE re-pinning:
#: EIGHT builds on WSL2 (numpy-absent) — five successive
#: `_build_frames('all')` calls inside one process, plus three FRESH
#: interpreters — all produced this one hash. The cross-process half matters
#: here because the new frame content is derived from a dict populated at
#: import through the curated-docs merge, which is exactly the shape that
#: could have carried iteration-order nondeterminism between runs. It does
#: not.
#:
#: **RE-PINNED AGAIN at v0.9.0rc424 (`#T1113`).** rc423's value was
#: ``376cdbf03d83a47d2a032589128cc805dd5877ee7cfe7744f677181db8551dac``. This
#: is the SEVENTH consecutive re-pin, and it is back to the **population**
#: kind: rc424 registers **seven new ops** — the six ``srmech.music``
#: relational ops (``just_limit`` / ``comma_of_chain`` / ``tempers_out`` /
#: ``interval_vector`` / ``normal_order`` / ``prime_form``) and
#: ``srmech.signal_processing.music_doa`` — so the frame set moves
#: **634 -> 641 = 612 ops + 29 carriers** and
#: ``describe()['tools']['total']`` moves 605 -> 612. Seven new ToolEntry
#: summaries, seven new curated explanation/example/worked blocks, and seven
#: new ``composes`` tuples all land in the corpus by construction.
#:
#: One entry deserves naming because it would otherwise be mis-read as a
#: rename: ``music_doa`` had **no ToolEntry at all** through rc423, so it
#: contributed **no frame** and was ABSENT from the corpus rather than
#: out-ranked within it. Its arrival is a genuine +1 to the frame count, not a
#: relabelling of an existing frame — which is why the count moves by seven
#: and not by six.
#:
#: Determinism re-established independently at this value BEFORE re-pinning:
#: EIGHT builds on WSL2 (numpy-absent) — five successive
#: `_build_frames('all')` calls inside one process, plus three FRESH
#: interpreters — all produced this one hash, with `len(frames) == 641` every
#: time.
#:
#: **RE-PINNED AGAIN at v0.9.0rc425 (`#T1112`).** rc424's value was
#: ``ad80c34e0c5fb6e03b76dee9d2511050791f726a8a5a8c049d116837439fca09``. This
#: is the EIGHTH consecutive re-pin and the largest population move so far:
#: rc425 registers **37 new ops** — the remaining Path-A ``closed_form_ops``
#: — so the frame set moves **641 -> 678 = 649 ops + 29 carriers** and
#: ``describe()['tools']['total']`` moves 612 -> 649. Thirty-seven new
#: ToolEntry summaries, thirty-seven new curated explanation / example /
#: worked blocks, and twenty-six new ``composes`` tuples all land in the
#: corpus by construction.
#:
#: The move is **+37 with ZERO renames** — every one of the 612 rc424 frame
#: names survives verbatim (``test_op_name_set_witness_rc361`` pins the SET
#: alongside this hash, and it reports no removals). That is worth stating
#: because a bulk registration is exactly the change under which a quiet
#: rename would hide: the count moves so much that a single relabelled frame
#: would not be visible in the cardinal alone.
#:
#: Three modules were deliberately NOT registered and so contribute no frame:
#: ``closed_form_ops`` also ships ``fft`` / ``ifft`` / ``pi_cascade``, each of
#: which was executed against the op it shadows and agreed BIT-EXACTLY, so a
#: frame for it would be a duplicate of one already in the corpus rather than
#: new content. 40 unregistered modules, 37 frames.
#:
#: Determinism re-established independently at this value BEFORE re-pinning:
#: FIFTEEN builds on WSL2 (numpy-absent) — five successive
#: `_build_frames('all')` calls inside each of THREE fresh interpreters — all
#: produced this one hash, with `len(frames) == 678` every time, and the
#: ops/carriers sub-corpora summing to it on every build.
#:
#: **RE-PINNED AGAIN at v0.9.0rc427 (`#T1130`).** rc425's value was
#: ``e40ec9963b134cdb096c3465bae3ba992a753fbecbd7255f11191fa1e1cee072``. This
#: is the NINTH consecutive re-pin. rc427 registers **6 new ops** — the
#: closed-form directional generator ``math.cyclic.mod_mul_arrow``, its
#: tabulated peer ``cascade.finite_semiflow``, and the four table-eating
#: carriers/censuses ``conjugacy_census`` / ``reversal_law_census`` /
#: ``anti_automorphism_witnesses`` / ``dihedral_group`` — so the frame set
#: moves **678 -> 684 = 655 ops + 29 carriers** and
#: ``describe()['tools']['total']`` moves 649 -> 655.
#:
#: TWO further corpus movers in the same rc carry NO frame of their own, and
#: naming them is the point of this note: (a) ``unit_loop`` and
#: ``loop_invariants`` each gained a ``table=`` parameter, so their existing
#: frames' TEXT changed while the frame COUNT did not; and (b) an attestation
#: fix rewrote the citation prose on ``moufang_residue`` / ``is_moufang`` /
#: ``malcev_defect`` / ``unit_loop`` (Baez arXiv:math/0105155 §2 was cited for
#: the Moufang identities and does not state them). So this hash would have
#: moved this rc even with zero new ops — which is exactly why the witness is
#: a hash over content and not a count.
#:
#: The move is **+6 with ZERO renames** — ``test_op_name_set_witness_rc361``
#: pins the SET alongside this hash and reports no removals.
#:
#: Determinism re-established independently at this value BEFORE re-pinning:
#: FIFTEEN builds on WSL2 (numpy-absent) — five successive
#: ``_build_frames('all')`` calls inside each of THREE fresh interpreters —
#: all produced this one hash, with ``len(frames) == 684`` every time and the
#: ops/carriers sub-corpora measuring 655 + 29 = 684 on every build.
#:
#: MOVED AGAIN in the rc427 repair pass, with **zero op-count change**
#: (684 = 655 + 29 both before and after) — the corpus is a hash over ToolEntry
#: PROSE, and the repair rewrote prose on five entries: the ``dihedral_group``
#: summary + curated explanation (the shipped "unit_loop yields orders
#: {4, 8, 16, 32} only" was false — the ladder runs to order 512), three
#: Schafer ``§III.1`` citations (that book has no sections at all; the
#: associator is ch. II eqn (11)), and the Baez positive-control count
#: (7× → 22×). That a +0-op rc moves this hash is the property the witness
#: exists for. Re-measured the same way: FIFTEEN builds, three fresh
#: interpreters, one hash, ``len(frames) == 684`` every time.
#:
#: MOVED AGAIN at rc428 (`#T1126`), again with **zero op-count change**
#: (684 = 655 + 29 before and after; the citation rc registers no op, so the
#: registry stays 655 and ABI stays 14). Exactly ONE ToolEntry's prose moved:
#: ``srmech.cascade.octonion_hopf_base``, whose SSoT read
#: "arXiv:math/0105155 §4.1–§4.2 (the octonionic Hopf fibration S⁷↪S¹⁵↠S⁸,
#: 𝕆P¹≅S⁸)" through rc427 and was FALSE at both endpoints — §4.1 is G₂, §4.2 is
#: F₄, and "Hopf" occurs 0 times in either; the fibration is set out in §3.1
#: "Projective Lines". The entry now cites §3.1 and records the correction
#: inline, so the prose grew and the corpus hash moved with it.
#:
#: The two burdens this re-pin discharges, per the pin discipline:
#:   1. **the op set did not move** — 655 ops + 29 carriers = 684 frames, the
#:      same decomposition as rc427, so nothing was added, renamed or dropped;
#:   2. **the move has a named cause** — a single ToolEntry's SSoT string,
#:      changed because ``tests/test_citation_manifest_rc428.py`` measured it
#:      false against the attested source. The hash moving on a +0-op rc whose
#:      only edit is a corrected citation is precisely the property the witness
#:      exists for: prose that reaches users through ``describe()``, the MCP
#:      tool list and the compiled-in C registry is content, not commentary.
#: Re-measured the same way: FIFTEEN builds, three fresh interpreters, one
#: hash, ``len(frames) == 684`` and ``(655, 29)`` every time.
#: **RE-PINNED AGAIN at v0.9.0rc429 (`#T1128`).** rc428's value was
#: ``91fb1c351e5bb855d338271b5a50cf6e50a5c38f18287de999e934e0f5e16f53``. This
#: is the ELEVENTH consecutive re-pin and the THIRD in a row with **zero
#: op-count change** — 684 = 655 ops + 29 carriers before and after, registry
#: 655, ABI 14. rc429 is a PROVENANCE rc and registers no op.
#:
#: The two burdens this re-pin discharges:
#:   1. **the op set did not move** — the decomposition is identical to rc427
#:      and rc428, so nothing was added, renamed or dropped;
#:   2. **the move has a named cause** — rc429 carried a provenance VERDICT into
#:      the emitted prose fields that were shipping the claim without one. Four
#:      ToolEntries moved: ``malcev_defect`` and ``moufang_residue``
#:      (explanation, plus the latter's ``example['why']``),
#:      ``genome.cwf_consistency_mod2`` (summary + explanation) and
#:      ``covering.linking_number_cwf`` (summary + explanation). Two of those
#:      edits also NARROWED prose that appealed to a named theorem as its own
#:      warrant — "the theorem's content is" became "the asymmetry this op
#:      measures is" — which is a content change by exactly the standard this
#:      witness exists to enforce.
#:
#: That a +0-op rc moves this hash is the property the witness exists for:
#: ToolEntry prose reaches users through ``describe()``, the MCP tool list and
#: the compiled-in C registry, so a provenance verdict added there is content.
#: Re-measured the same way BEFORE re-pinning: FIFTEEN builds on WSL2
#: (numpy-absent) — five successive ``_build_frames('all')`` calls inside each
#: of THREE fresh interpreters — one hash every time, ``len(frames) == 684``
#: every time, and the ops/carriers sub-corpora summing to it on every build.
#: RE-PINNED at the rc430 repair (`#T1127`), and the mover is NOT where a
#: reader would look first. That repair edited ``returns.type`` on seven ops —
#: and ``returns`` is not in the corpus at all (the fields are name / category /
#: summary / explanation / example.* / composes / preserves). The corpus moved
#: through its CARRIER half instead: ``kuramoto_sin_term`` and
#: ``kuramoto_gen_term`` were declared ``float`` and actually return ``Q``, so
#: correcting them moved both ops out of the **float** carrier's ``produces``
#: list and into **Q**'s — and the carrier frames embed those op lists. Measured
#: rather than reasoned: the two ops appear in exactly THREE carrier frames
#: (``Q``, ``float``, ``int``), and ``len(frames)`` stays 684, so no frame was
#: added or dropped — two frames changed content.
#:
#: That is the witness doing its job on the second-order effect of a
#: declaration fix, which is precisely the drift it exists to catch: a consumer
#: reading the carrier index was being told float produces something it does not.
#:
#: Re-measured the documented way BEFORE re-pinning: FIFTEEN builds on WSL2
#: (numpy-absent) — five successive ``_build_frames('all')`` calls inside each of
#: THREE fresh interpreters — ONE hash every time, ``len(frames) == 684`` every
#: time, and ops (655) + carriers (29) summing to 684 on every build.
#:
#: **RE-PINNED AGAIN at v0.9.0rc434 (`#T1130`).** rc430's value was
#: ``50ee7c0d5aedf0865cbe902f87949048a6c38872f6a2fabf4ac67f972827c476``. This is
#: the TWELFTH consecutive re-pin and the FOURTH in a row with **zero op-count
#: change** — 684 = 655 ops + 29 carriers before and after, registry 655, ABI 14.
#: rc434 registers no op.
#:
#: The two burdens this re-pin discharges:
#:   1. **the op set did not move** — the decomposition is identical to rc427
#:      through rc430, so nothing was added, renamed or dropped;
#:   2. **the move has a named cause, MEASURED not reasoned** — exactly TWO
#:      ToolEntry ``explanation`` fields changed, ``srmech.cascade.cyclic_gcd``
#:      and ``srmech.math.cyclic.gcd``, both of which claimed a ``ValueError``
#:      for arguments past ``2**64``. rc167 (gh #765) removed that cap and the
#:      registry never followed; ``cyclic_gcd(2**64, 5)`` returns ``1``,
#:      confirmed at three magnitudes to ``2**200``. Located by probing the
#:      built corpus rather than by inference — the frames are LOWER-CASED, so
#:      a case-sensitive search for the new prose finds nothing and would have
#:      supported a confident wrong cause. Searching the blobs as they are
#:      actually stored gives: ``"uncapped big-int euclid"`` in 1 frame
#:      (``cascade.cyclic_gcd``), ``"no upper cap"`` and ``"gh #765"`` in 1
#:      frame (``math.cyclic.gcd``), and ``"0.9.0rc433"`` in exactly those 2.
#:
#: This rc also added ``Raises:`` blocks to eleven docstrings, and those did
#: NOT move the hash — worth recording, because it is the same structural fact
#: rc433 measured from the other side: the corpus carries ToolEntry prose, the
#: tool-docs generator seeds ``explanation`` from a docstring's FIRST paragraph
#: only, and curated text wins the merge. Contract documentation appended below
#: the opening paragraph reaches neither surface.
#: **RE-PINNED AGAIN at v0.9.0rc436 (local task T1141).** rc435's value was
#: ``af759315d6043541938bfc9618635bf959d059f3d79928957b753946a96e44d7``. This is
#: the POPULATION kind rather than the pure-prose kind: rc436 registers ONE new
#: op, ``srmech.cascade.octonion_associator_support``, so the frame set moves
#: **684 -> 685 = 656 ops + 29 carriers** and ``describe()['tools']['total']``
#: moves 655 -> 656. Its ToolEntry summary and its curated
#: explanation/why/worked blocks all land in the corpus by construction. The rc
#: ALSO edits ToolEntry and docstring prose on four existing surfaces (the
#: Fuller-1971 retrievability repair), which is the prose kind arriving in the
#: same commit -- both branches of this constant's own failure message at once.
#:
#: Determinism re-established independently at this value BEFORE re-pinning:
#: FIVE successive ``_build_frames('all')`` builds in FIVE FRESH interpreters on
#: WSL2 (numpy-absent) produced this one digest, with the frame counts
#: 685 / 656 / 29 identical on every build. The drift branch is ruled out by
#: measurement, again.
#:
WITNESS_RC416 = (
    "fb949e35ff814848739ce32c25bfdde5a32ff47539ffb5ae6011a78c22110f37")

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
