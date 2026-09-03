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
#: ⚠️ **The value moved a SECOND time inside rc436**, and saying why matters:
#: the first rc436 value was
#: ``fb949e35ff814848739ce32c25bfdde5a32ff47539ffb5ae6011a78c22110f37``, taken
#: before the item-1 rework. That rework rewrote the Fuller-1971 provenance
#: prose on four ToolEntry surfaces — twice, once when NCBI ``oa.fcgi`` showed
#: "OA" was a false LICENCE claim, and again when a four-route sweep showed the
#: not-retrievable list was empty. The corpus is BUILT FROM ToolEntry prose, so
#: each rewrite moved the digest by construction. This is the pure-prose branch
#: of this constant's own failure message arriving three times in one rc, which
#: is exactly why the re-pin is done LAST, after the prose has settled.
#:
#: Determinism re-established independently at this value BEFORE re-pinning:
#: FIVE successive ``_build_frames('all')`` builds in FIVE FRESH interpreters on
#: WSL2 (numpy-absent) produced this one digest, with the frame counts
#: 685 / 656 / 29 identical on every build. The drift branch is ruled out by
#: measurement, again.
#:
#: rc437 (local task T1142) re-pins it AGAIN, and again after re-establishing
#: determinism rather than assuming it: FIVE fresh numpy-absent interpreters
#: agreed on this digest with the frame counts 690 / 661 / 29 identical on every
#: build. The corpus is BUILT FROM ToolEntry prose, so five registrations plus
#: five curated explanations move it by construction; 690 = 661 ops + 29
#: carriers, and the ops half is exactly the live registry total.
#:
#: ⚠️ AND THE FIRST rc437 VALUE WAS WRONG, which is this constant's own advice
#: arriving a fourth time. It was pinned while the argument harvester still had
#: two findings outstanding; fixing them rewrote four curated snippets, the
#: corpus moved again, and the full sweep went red on exactly these three tests
#: and nothing else. RE-PIN LAST — after regen_all --check is clean AND both
#: example ledgers are final — or the pin is a snapshot of prose still in
#: flight. Determinism re-verified at THIS value across five fresh
#: interpreters, same 690 / 661 / 29.
#:
#: rc438 (local task T1140) re-pins it again, and this time the FRAME COUNTS DO
#: NOT MOVE: 690 / 661 / 29, identical to rc437. That is the informative part.
#: rc438 registers NOTHING — the registry stays at 661 — and the digest moved
#: anyway, because the corpus is built from ToolEntry PROSE and rc438 rewrote
#: the ``klein4_from_one`` and ``q8_from_one`` summaries to state the winding
#: they now read. So a moved witness with UNCHANGED counts is the signature of
#: a pure-prose edit, and a moved witness with changed counts is a
#: registration; reading which one you have is the first thing to do when this
#: constant goes red. Determinism re-established BEFORE re-pinning, as every
#: prior entry here insisted: FIVE fresh numpy-absent WSL2 interpreters agreed
#: on this digest with 690 / 661 / 29 on every build. Re-pinned LAST — after
#: ``regen_all.py --check`` reported all six generated files up to date and
#: both example ledgers were final.
#:
#: ⚠️ AND rc438 PINNED IT TWICE, which is this constant's own advice landing a
#: FIFTH time and is worth reading before the sixth. The first rc438 value was
#: taken after the op fix and before CI — and CI then went red on the
#: cascade-catalog COUNT (a 21st descriptor), whose repair rewrote the
#: LLM-facing ``list_catalog_ops`` summary in ``tool_schema`` to enumerate the
#: new op by name and cite ``21 ops`` twice. That is ToolEntry prose, so the
#: corpus moved again and this constant went red a second time in one rc. The
#: lesson is not "re-pin twice"; it is that "the prose has settled" means AFTER
#: the gates that can force more prose have run, and a local sweep that does
#: not cover the changed count is not those gates. Determinism re-established
#: a second time across FIVE fresh numpy-absent interpreters at this value,
#: same 690 / 661 / 29 — still unchanged, because rc438 registers nothing.
#:
#: rc439 (`#T1140`) moved it again, and this one is the CLEAN case the block
#: above describes: counts UNCHANGED at 690 / 661 / 29, so a pure-prose edit
#: and not a registration. Two prose sources moved — ``centromere_of``'s
#: docstring gained its dicentric SCOPE paragraph, and the curated
#: ``genome.mint`` / ``genome.genome`` entries stopped presenting a
#: cross-chromosome centromere blend as a real reading. Determinism
#: re-established BEFORE re-pinning across FIVE fresh numpy-absent WSL2
#: interpreters, and measured on a COMPLETE tree copy rather than the session
#: worktree: ``citation_corpus`` excludes any path containing ``.claude`` or
#: ``worktrees``, so in-worktree the corpus is EMPTY and a witness taken there
#: would be a digest of nothing. Re-pinned LAST — after ``regen_all.py
#: --check`` reported all six generated files up to date and both example
#: ledgers were final.
#: rc440 (`#T1147`) moved it again, and it is the CLEAN case as well: counts
#: UNCHANGED at 690 / 661 / 29, so pure prose and no registration. Two curated
#: entries moved — ``klein4_from_one``'s explanation stopped claiming the
#: coupling is a function of "three canonical constructor integers" (rc438 made
#: the winding a fourth, conditionally, and the promise was left behind), and
#: ``q8_from_one``'s stopped enumerating the One's inputs flatly. Determinism
#: re-established BEFORE re-pinning across FIVE fresh numpy-absent WSL2
#: interpreters on a COMPLETE tree copy, and cross-checked against three more
#: in the session worktree — the two agree here, because unlike
#: ``citation_corpus`` this corpus is built from in-package ``ToolEntry`` prose
#: and carries no path-based exclusion. Re-pinned LAST, after
#: ``regen_all.py --check`` reported all six generated files up to date.
#:
#: rc441 (`#T1148`) moves it again, and it is the CLEAN case a third time
#: running: counts UNCHANGED at **690 / 661 / 29**, so pure prose and no
#: registration — measured on both sides, rc440 and rc441 each build 690
#: frames, and 690 = 661 ops + 29 carriers with the ops half still exactly the
#: live registry total. Two curated entries moved, both Class-B TLV:
#: ``tlv_pack``'s explanation stopped citing its C peer by LINE number
#: (``c/include/srmech.h:2707`` had drifted onto unrelated prose — stale before
#: this rc touched the header, and a symbol name cannot go stale where a line
#: offset does) and now records that ``tlv_unpack`` has a C peer of its own;
#: ``tlv_unpack``'s gained that peer's contract, because rc441 is the rc that
#: SHIPPED it — through rc440 Class B had a writer in C and a reader in Python
#: only, so the registry's own "the ONLY correct way to read these frames back"
#: was advice no C caller could take.
#:
#: Determinism re-established BEFORE re-pinning, and more widely than usual
#: because this rc changes a dispatch path: **eleven** builds agreed on this
#: one digest — FIVE fresh numpy-absent WSL2 interpreters on a COMPLETE tree
#: copy with NO ``.so`` (the pure projection, which is the cell that went red),
#: THREE more on the same copy WITH ``libsrmech.so`` loaded (``HAS_NATIVE``
#: True), and THREE in the session worktree. Pure and native agree, which is
#: the check that matters here: a witness that differed between projections
#: could not be pinned by a single constant at all. The rc440 note above is
#: confirmed — this corpus is built from in-package ``ToolEntry`` prose and
#: carries no path-based exclusion, so unlike ``citation_corpus`` the worktree
#: reading is trustworthy.
#:
#: The value was ALSO cross-checked against CI rather than only against itself:
#: the ``fallback (pure-Python, no native) • shard 6/6`` job of run
#: 31981627025 reported exactly this digest on all three of these tests before
#: the re-pin, so the local measurement and the authoritative cell agree.
#: Re-pinned LAST, after ``regen_all.py --check`` reported all six generated
#: files up to date.
#:
#: rc442 (`#T1150`) re-pins it again, and for the reason this note says is the
#: legitimate one: a PROSE EDIT moved it. The corpus is built from in-package
#: ``ToolEntry`` prose, and rc442 registers two new entries (the §GROUP/v20
#: ``genome_groups`` / ``genome_group`` pair), so the digest MUST move — a
#: witness that did not move here would mean the new prose never reached the
#: corpus. Measured in the same order the note prescribes: ``regen_all.py
#: --check`` reported all six generated files up to date FIRST, then the
#: witness was read off ``search("rank", k=1).witness``. The corpus carries no
#: path-based exclusion, so unlike ``citation_corpus`` the worktree reading is
#: trustworthy here.
#: rc444 (`#T1152`) re-pins it again, for the same legitimate reason as rc442: a
#: PROSE EDIT moved it. rc444 edits in-package ``ToolEntry`` prose at six sites
#: — ``triality_companions`` gains an ``exact`` parameter and a reworded summary,
#: and the stale "exact-rational **Fraction** solve" / "force the exact
#: **Fraction** solve" claim is corrected to ``Q`` on ``dense_solve`` /
#: ``schur_complement`` / ``dirichlet_to_neumann`` (measured false: the leaves
#: are ``srmech.math.q.Q``). The corpus is built from that prose, so the digest
#: MUST move — a witness that did NOT move here would mean the corrected prose
#: never reached the corpus, i.e. the shipped falsehood was still live.
#:
#: Measured in the order this note prescribes: ``regen_all.py --check`` reported
#: all six generated files up to date FIRST, then the witness was read off
#: ``search("rank", k=1).witness``. CROSS-CHECKED AGAINST CI rather than only
#: against itself, exactly as the rc440 note requires: the ``fallback
#: (pure-Python, no native) • shard 6/6`` job of run 32032764725 reported this
#: digest (prefix ``91501f9106d6``, suffix ``31f0d8a163781``) on all three of
#: these tests before the re-pin, and the local reading matches on both ends.
#:
#: rc445 (`#T1153`) MOVES IT AGAIN, for the same reason and on a wider surface.
#: The FALSE-tier prose pass rewrote **25 ToolEntry ``summary=`` fields** and
#: **6 curated ``explanation`` blocks** — the false ``n <= 256`` native cap
#: (measured: ``_can_dispatch_native`` never reads its ``n``; ``srmech.h:1536``
#: says "No N cap"), the false "NumPy eigh fallback" on
#: ``hermitian_eigendecompose`` and "via NumPy eigh" on
#: ``symmetric_eigendecompose`` (both measured to run with numpy absent from
#: ``sys.modules``), "numpy as CONTAINER only" on the four
#: ``matrix_cascades`` factorisations, and the remaining ``Fraction`` -> ``Q``
#: mechanism claims. The corpus is BUILT from that prose, so this digest MUST
#: move; a witness that did not move would mean the corrected summaries never
#: reached the corpus and the shipped falsehoods were still being served.
#:
#: Same order as above: ``regen_all.py --check`` reported all six generated
#: files up to date FIRST (so the digest is taken against a regenerated tree,
#: not a half-regenerated one), then the witness was read off
#: ``search("rank", k=1).witness`` and independently re-derived as
#: ``sha256_bytes(b"".join(f.blob for f in _build_frames("all")[0]))`` over
#: 692 frames (663 ops + 29 carriers) — the two agree, which is the same
#: cross-check ``test_scope_witnesses_agree_with_the_union`` performs.
#: rc446 (`#T1154`) MOVES IT AGAIN — the RESIDUE/ORIENTATION half of the same
#: campaign, and a WIDER prose surface than rc445's. 130 ToolEntry ``summary=``
#: fields were edited (the numpy/ndarray population there falls 175 -> 49), 13
#: ``returns.shape`` strings were rewritten to name the carrier positively
#: (``Mat``, ``array('d')`` row-major, interleaved ``(re, im)``), and 229
#: docstrings across 81 files were triaged clause-by-clause. The corpus is BUILT
#: from that prose, so this digest MUST move; a witness that did NOT move would
#: mean the edited summaries never reached the corpus.
#:
#: Same order as the rc440/rc445 notes prescribe, and for the same reason:
#: ``regen_all.py --check`` reported all six generated files up to date FIRST
#: (71.6s, "all 6 generated files are up to date"), so the digest is taken
#: against a fully regenerated tree rather than a half-regenerated one. THEN the
#: witness was read off ``search("rank", k=1).witness`` and independently
#: re-derived as ``sha256_bytes(b"".join(f.blob for f in _build_frames("all")[0]))``
#: over 692 frames (663 ops + 29 carriers) — the two agree, which is the same
#: cross-check :func:`test_scope_witnesses_agree_with_the_union` performs.
#:
#: The 663/29 split is unchanged from rc445: this rc registers and removes no
#: op, so a moved FRAME COUNT (rather than a moved digest) would have been the
#: signal that something other than prose had changed.
#: rc452 (`#T1166`) - RE-PINNED, and the determinism question was SETTLED BY
#: EXECUTION BEFORE the digit moved, because this gate's own message offers two
#: readings ("if a prose edit caused it, re-pin; if nothing was edited, the frame
#: build is non-deterministic") and re-pinning the second one would convert a real
#: ADR-0011 contract break into a silent one. Both halves were measured:
#:
#:   DETERMINISM - `_build_frames("all")` was run in FOUR separate processes under
#:   PYTHONHASHSEED 0 / 13 / 271 / 9999. All four returned the SAME digest, and all
#:   three derivation paths agree inside each run (the witness `_build_frames`
#:   returns, `sha256_bytes` recomputed over the joined blobs, and the live
#:   `search("rank", k=1).witness`). It also matches what CI measured on its own
#:   runners. The build is deterministic; the ADR-0011 witness contract HOLDS.
#:
#:   CAUSATION - the tree at the merge-base was materialised read-only and its
#:   corpus built: it reproduces `eb9f7dd1...` EXACTLY, i.e. the OLD pin was correct
#:   for the OLD prose. Diffing the two frame sets positionally shows the same 692
#:   names in the same order and exactly TWO of 692 frame blobs moved - the `Q` and
#:   `int` CARRIER frames. `int.produces` lost the nine Class-N ops rc452 flipped to
#:   returning `Q`; `Q.produces` gained those same nine and `Q.consumes` gained the
#:   four that now accept a `Q` operand. No op frame moved at all.
#:
#: The 663/29 split is UNCHANGED, which is the signal the rc445 note prescribes: a
#: moved FRAME COUNT would have meant something other than prose changed. It did not.
#: rc452 (gh #1653, the registry-ripple phase) - RE-PINNED AGAIN, and this time the
#: FRAME COUNT ITSELF moves: 692 -> 695 (666 ops + 29 carriers). That is the reading
#: the rc445 note reserves for "something other than prose changed", and here it is
#: the DECLARED change - three ops were registered, so a frame count that had NOT
#: moved would have been the failure. Both halves were measured BEFORE the digit
#: moved, in the order the rc452 exact-Q note above prescribes:
#:
#:   DETERMINISM - `_build_frames("all")` run in FOUR separate processes under
#:   PYTHONHASHSEED 0 / 13 / 271 / 9999 returned the SAME digest and 695 frames
#:   each, and inside every run all three derivation paths agree (the witness
#:   `_build_frames` returns, `sha256_bytes` recomputed over the joined blobs, and
#:   the live `search(...).witness`). The ADR-0011 witness contract HOLDS.
#:
#:   CAUSATION - the op-frame NAME set was diffed against the pre-registration
#:   population, `tests/registered_op_names.txt` at the branch head (663 names):
#:   ADDED = exactly `srmech.amsc.descriptor.render_template`,
#:   `srmech.amsc.format.sha256_raw`, `srmech.signal_processing.mint_vector`;
#:   REMOVED = none. Carriers stay 29, and exactly ONE carrier frame's blob can
#:   mention a new op - `int`, whose `consumes` gains `mint_vector` (its `D` is an
#:   int). The digest move is therefore fully attributed to the three registrations.
#:
#: This gate was RED in the handed-over working tree: the registration slice bumped
#: every `describe()["tools"]["total"]` pin (74 lines across 67 files against
#: the RIPPLE_GATES.md predicate, plus the one `EXPECTED_N` assignment that
#: predicate cannot match) but not this witness, so three tests
#: in this file failed on the stale digest. It is exactly the "invisible class" the
#: RIPPLE_GATES.md count-pin note names - a pin that is a DIGEST rather than a
#: comparison against the count, which no `== 663` predicate can find.
#:
#: rc454 (`#T1168`) — RE-PINNED, and this is the NARROWEST move the constant has
#: recorded: exactly ONE frame of 695 changed.
#:
#: ⚠️ IT WAS RE-PINNED TWICE, and the first value was WRONG BY THE TIME IT SHIPPED.
#: That is worth recording, because the failure is not arithmetic — it is temporal,
#: and it is the exact shape this release is otherwise about. The first pin
#: (`6e607fc2...`) was measured correctly, against the tree as it stood at that
#: moment: the `(17 executable / 3 leaf)` de-literalization had landed and nothing
#: else had. The release then CONTINUED, and de-literalized a SECOND cardinal —
#: `98 proof cases` — in the SAME `run_cascade_chain` explanation, one field away.
#: One more regen, one more blob, and a digest measured an hour earlier described a
#: tree that no longer existed. CI caught it in the pure shard; three tests in this
#: file went red on a digest nobody had re-measured.
#:
#: THE RULE THE NEXT RE-PIN NEEDS: a content-address is only valid against the tree
#: state AT SHIP TIME. Measure it LAST — after the final regen, not after the edit
#: that prompted it — or it dates itself the way every stale cardinal in this
#: release dated itself. A pin taken mid-release is a measurement of a draft.
#:
#:   DETERMINISM (re-measured at the rc454 ship head) — `regen_all.py --check`
#:   reported "all 6 generated files are up to date" FIRST (11.1s, no `REFUSED:`),
#:   so the digest is taken against a fully regenerated tree rather than a
#:   half-regenerated one. Then `_build_frames("all")` was run in THREE separate
#:   numpy-absent processes in the MAIN checkout. All three returned the SAME digest
#:   and 695 frames (666 ops + 29 carriers), and inside every run all three
#:   derivation paths agree (the witness `_build_frames` returns, `sha256_bytes`
#:   recomputed over the joined blobs — srmech's OWN Class-A op, not `hashlib` —
#:   and the live `search("rank", k=1).witness`). The ADR-0011 contract HOLDS.
#:
#:   ⚠️ ON THE HASH SEED, stated precisely because the earlier note overstated it.
#:   The intent was fixed seeds 0 / 13 / 271. MEASURED: `PYTHONHASHSEED` does NOT
#:   reach the interpreter through the invocation path used here — `os.environ.get`
#:   returns None in the child — so the three runs used CPython's DEFAULT hash
#:   randomization, verified live by `hash("abc")` returning three different values
#:   across the same three invocations. That is a STRONGER result than the one
#:   intended, not a weaker one: three INDEPENDENT random seeds agreed, rather than
#:   three chosen ones. Do not "restore" the fixed seeds without first checking they
#:   arrive; an env var that is silently dropped is an instrument that cannot fail.
#:
#:   CAUSATION — the tree at the pre-rc454 head (`a15bfd4f0`, rc453) was
#:   materialised read-only with `git archive` and its corpus built: it reproduces
#:   `7cb11ffb...` EXACTLY, i.e. the OLD pin was correct for the OLD prose.
#:   Diffing the two frame sets positionally gives the same 695 names in the same
#:   order, ZERO added, ZERO removed, and exactly ONE moved blob —
#:   `srmech.dsl.run_cascade_chain`.
#:
#: That ONE frame is the entire rc454 corpus delta, and the reason the rest of the
#: release is invisible here is worth stating rather than leaving to be
#: rediscovered: rc454 is a prose-currency release that also edited README,
#: CHANGELOG, ADR-0012 and the research notebook, and NONE of those feed this
#: corpus. It is built from ToolEntry prose and the carrier registry — see
#: `_build_frames` — not from repository documents, so a reader who expects a
#: four-document prose sweep to move this digest is reading the wrong corpus.
#:
#: The frame that DID move is `run_cascade_chain`, whose `explanation` carried a
#: hard `(17 executable / 3 leaf)` against a live 18 / 3 while its OWN `example`,
#: one field away in the same entry, already said `18 executable descriptors`.
#: rc447 bumped one of those two literals and left the other, so the entry shipped
#: self-contradictory for six rcs. rc454 DE-LITERALIZES both halves rather than
#: bumping them — the explanation now names the `executable` / `leaf` split and the
#: example defers to `describe()['cascade_catalog']['status']`.
#:
#: THAT ENTRY HELD A THIRD CARDINAL, and draining it is why this digest moved twice.
#: The same `explanation` also carried `98 proof cases`, which would have been left
#: behind in exactly the rc447 shape — one literal fixed, its neighbour stranded for
#: the next rc to rediscover. It is now a pointer form too ("one proof case per
#: boundary case each descriptor documents"). So the honest statement is: no cardinal
#: remains in that entry AT ALL, and the ONE frame that moved absorbed all three
#: de-literalizations, not the two the first pin was measured against.
#:
#: The 666/29 split is UNCHANGED from rc452, which is the signal the rc445 note
#: prescribes: this rc registers and removes no op, so a moved FRAME COUNT would
#: have meant something other than prose changed. It did not move.
#:
#: rc456 (the representation stratum) — RE-PINNED, and the FRAME COUNT moves:
#: 695 -> 705 (676 ops + 29 carriers). That is the rc452 reading again — the
#: DECLARED change is ten registrations (nine srmech.math.groups ops +
#: srmech.math.poly.cyclotomic_polynomial), so a frame count that had NOT
#: moved would have been the failure. Measured LAST, after the final regen,
#: per the rc454 rule above ("a pin taken mid-release is a measurement of a
#: draft") — and this release DID have a mid-release draft moment of exactly
#: the rc454 shape: a first regen was followed by a curated-row repair (a
#: cayley_graph SIBLINGS citation naming the dead srmech.amsc.laplacian path
#: where the live ops are srmech.math.laplacian.*), a second regen, and only
#: then this measurement.
#:
#:   DETERMINISM — `regen_all.py --check` reported "all 6 generated files are
#:   up to date" FIRST (58.8s, no `REFUSED:`), then `_build_frames("all")`
#:   ran in THREE separate numpy-absent WSL2 processes. All three returned
#:   the SAME digest and 705 frames each. The ADR-0011 witness contract
#:   HOLDS.
#:
#:   CAUSATION — the op-frame population delta against
#:   `tests/registered_op_names.txt` at the rc455 head (666 names) is exactly
#:   the ten rc456 registrations; REMOVED = none; carriers stay 29. The
#:   as-text prose delta beyond the ten new frames is the two rc452-drain
#:   `composes` declarations (sha256_raw, mint_vector) riding their existing
#:   frames.
#: rc457 re-pin — the corpus witness moved because the registry PROSE moved,
#: which is the sanctioned cause: three new ToolEntry registrations (the
#: representation-stratum tier-3 triple under srmech.math.groups) plus their
#: curated example/explanation rows. Frame count 705 -> 708, exactly the
#: three new op frames; REMOVED = none; carriers unmoved. Measured LAST,
#: after the final regen (`regen_all.py --check` reported "all 6 generated
#: files are up to date" FIRST, no `REFUSED:`), per the rc454 rule ("a pin
#: taken mid-release is a measurement of a draft").
#:
#:   DETERMINISM — `_build_frames("all")` ran in THREE separate numpy-absent
#:   WSL2 processes; all three returned the SAME digest and 708 frames each.
#:   The ADR-0011 witness contract HOLDS.
#: rc460 re-pin — the corpus witness moved because the registry PROSE moved,
#: the sanctioned cause again: three new ToolEntry registrations (the exact
#: A2 weight-lattice triple, in the NEW module srmech.math.weight_lattice)
#: plus their curated example/explanation rows.
#:
#:   MEASURED: `len(frames) == 719`. The DELTA is exactly the three new op
#:   frames, and that is derived rather than eyeballed: the registry moved
#:   687 -> 690 (measured live), REMOVED = none (the rosetta-completeness
#:   gate reported exactly three unclassified ADDITIONS and no deletions,
#:   and the composes-population gate reported "Deleted: []" — two
#:   independent instruments agreeing that nothing left the surface), and
#:   carriers are unmoved (the carrier-schema gate is green). The op-name
#:   SET witness next door passed on a freshly rewritten manifest, which is
#:   the assertion that no RENAME hid inside the same count.
#:
#:   Measured LAST, after the final regen (`regen_all.py --check` reported
#:   "all 6 generated files are up to date", no `REFUSED:`), per the rc454
#:   rule that a pin taken mid-release is a measurement of a draft.
#:
#:   DETERMINISM — `_build_frames("all")` ran in THREE separate numpy-absent
#:   WSL2 processes; all three returned the SAME digest and 719 frames each,
#:   and `search("rank", k=1).witness` agreed with the direct build in every
#:   one. The ADR-0011 witness contract HOLDS.
#: rc461 re-pin — the corpus witness moved because the registry PROSE moved,
#: the sanctioned cause a fifth release running: two new ToolEntry
#: registrations (`triality_frame_action`, `cyclic_laplacian_spectrum`) plus
#: their curated example / explanation rows.
#:
#:   MEASURED: `len(frames) == 721`, and the split is 692 ops + 29 carriers.
#:   The DELTA is exactly the two new op frames, DERIVED and not eyeballed:
#:   the registry moved 690 -> 692 (measured live), REMOVED = none (the
#:   rosetta-completeness gate reported exactly two unclassified ADDITIONS and
#:   no deletions, and the composes-population gate reported "Deleted: []" —
#:   two independent instruments agreeing that nothing left the surface), and
#:   carriers are UNMOVED at 29 (neither op mints a carrier TYPE; exact ℚ
#:   leaves both as `int` pairs, which is the whole reason this rc adds no C
#:   symbol and no ABI bump). The op-name SET witness next door passed on a
#:   freshly rewritten manifest, which is the assertion that no RENAME hid
#:   inside the same count.
#:
#:   Measured LAST, after the final regen (`regen_all.py --check` reported all
#:   six generated files up to date), per the rc454 rule that a pin taken
#:   mid-release is a measurement of a draft.
#:
#:   DETERMINISM — `_build_frames` ran in THREE separate numpy-absent WSL2
#:   processes; all three returned the SAME digest and 721 / 692 / 29, and
#:   `search("rank", k=1).witness` agreed with the direct build in every one.
#:   The ADR-0011 witness contract HOLDS.
#: rc461 PART 2 re-pin (`#T1181`) — the corpus witness moved again, and again
#: for the sanctioned reason: the registry PROSE moved, three new ToolEntry
#: registrations plus their curated example / explanation rows.
#:
#:   MEASURED: `len(frames) == 724`, and the split is 695 ops + 29 carriers,
#:   read straight off the build as `{'op': 695, 'carrier': 29}` rather than
#:   inferred. The DELTA is exactly the three new op frames, DERIVED and not
#:   eyeballed: the registry moved 692 -> 695 (measured live), REMOVED = none
#:   (the rosetta-completeness gate reported exactly three unclassified
#:   ADDITIONS and no deletions), and carriers are UNMOVED at 29 — none of the
#:   three mints a carrier TYPE (ℚ leaves as `int` pairs and a `str` leaves
#:   `epq_frame_address`), which is the whole reason this part adds no C symbol
#:   and no ABI bump. The op-name SET witness next door passed on a freshly
#:   rewritten 695-row manifest, which is the assertion that no RENAME hid
#:   inside the same count.
#:
#:   Measured LAST, after the final regen (`regen_all.py --check` reported all
#:   six generated files up to date), per the rc454 rule that a pin taken
#:   mid-release is a measurement of a draft.
#:
#:   DETERMINISM — three successive `_build_frames('all')` calls inside each of
#:   THREE fresh numpy-absent WSL2 interpreters: all nine returned the SAME
#:   digest, and `search("rank", k=1).witness` agreed with the direct build in
#:   every one. The ADR-0011 witness contract HOLDS.
#: rc461 PART 3 re-pin (`#T1183`) — moved again, same sanctioned reason: the
#: registry PROSE moved, five new ToolEntry registrations plus their curated
#: example / explanation rows (the AFFINE / KAC-WALTON layer).
#:
#:   MEASURED: `len(frames) == 729`, split 700 ops + 29 carriers, read off the
#:   build as `len(_build_frames('ops')[0])` / `len(_build_frames('carriers')[0])`
#:   rather than inferred, with the sum checked against the union. The DELTA is
#:   exactly the five new op frames, DERIVED not eyeballed: the registry moved
#:   695 -> 700 (measured live), REMOVED = none (the rosetta-completeness gate
#:   named exactly five unclassified ADDITIONS and no deletions), and carriers
#:   are UNMOVED at 29 — none of the five mints a carrier TYPE. The zeta values
#:   ride the INTEGER coordinate vectors `character_table` already mints and
#:   `zeta_mul` already reads, and ℚ leaves as `int` pairs, which is exactly
#:   why this part adds no C symbol and no ABI bump. The op-name SET witness
#:   next door passed on a freshly rewritten 700-row manifest, which is the
#:   assertion that no RENAME hid inside the same count.
#:
#:   Measured LAST, after the final regen (`regen_all.py` reported all six
#:   generated files current and idempotent across two passes), per the rc454
#:   rule that a pin taken mid-release is a measurement of a draft.
#:
#:   DETERMINISM — three successive `_build_frames('all')` calls inside each of
#:   THREE fresh numpy-absent WSL2 interpreters: all nine returned the SAME
#:   digest, `len(frames)` was 729 and the split 700/29 in every one, and
#:   `search("rank", k=1).witness` agreed with the direct build every time. The
#:   ADR-0011 witness contract HOLDS.
#: rc461 PART 3 re-pin (`#T1181`/`#T1183`) — moved again, and this time for the
#: NARROWEST sanctioned reason: PROSE ONLY. No op was added, none renamed, none
#: removed.
#:
#:   MEASURED, and the measurement is the whole argument: `len(frames)` is
#:   UNMOVED at **729**, split 700 ops + 29 carriers, read off
#:   `len(_build_frames('ops')[0])` / `len(_build_frames('carriers')[0])` rather
#:   than inferred, with the sum checked against the union. An unmoved count
#:   with a moved digest is exactly the signature of a text-only edit — and it
#:   is what separates this re-pin from one that would be hiding a rename. The
#:   op-name SET witness next door is UNTOUCHED on the same 700-row manifest,
#:   which is the independent assertion that the NAMES did not move.
#:
#:   WHAT moved the text: `alcove_fold`'s ToolEntry summary (the corrected
#:   termination measurement, 962 -> 901), `so8_bracket_certificate`'s summary
#:   and `returns` (the homomorphism/automorphism split and its three new
#:   payload fields), the module docstrings those two ops carry, and the SIX
#:   corrected `composes` declarations (the runtime-traced call orders, plus
#:   the two edges the trace REMOVED as unverifiable and the two it added).
#:
#:   Measured LAST, after `regen_all.py --check` reported all six generated
#:   files up to date, per the rc454 rule that a pin taken mid-release is a
#:   measurement of a draft.
#:
#:   DETERMINISM — three successive `_build_frames('all')` calls inside each of
#:   THREE fresh numpy-absent WSL2 interpreters: all nine returned the SAME
#:   digest, `len(frames)` was 729 and the split 700/29 in every one, the
#:   recomputed blob hash agreed with the returned witness in every one, and
#:   `search("rank", k=1).witness` agreed with the direct build every time.
#: rc463 (`#T1188`) re-pin — TWO moves, both ATTRIBUTED rather than assumed.
#:
#:   The re-pin rule this file states is "if a prose edit caused it, re-pin; if
#:   nothing was edited, the frame build is non-deterministic". rc463 moved the
#:   witness twice, so both halves were measured before either was accepted.
#:
#:   COUNTS (as measured at rc463; see the rc464 block below for the current
#:   split): `len(frames)` was **749**, split **720 ops + 29 carriers**, read off
#:   `len(_build_frames('ops')[0])` / `len(_build_frames('carriers')[0])` and
#:   checked against the union. 720 is `EXPECTED_N` — the eighteen registrations
#:   rc463 added (702 -> 720). Carriers UNMOVED at 29: this rc mints no carrier
#:   TYPE.
#:
#:   MOVE 1 (rc463 proper) `c34e8e85…` -> `17a43674…`: the +18 registrations plus
#:   this rc's prose. Reproduced from the committed rc463 sources during the fix
#:   pass, which is what makes it a MEASUREMENT and not an inference.
#:
#:   MOVE 2 (the rc463 fix pass) `17a43674…` -> `24a0858e…`. ATTRIBUTED FRAME BY
#:   FRAME rather than assumed: a pristine copy of `srmech/` with every
#:   fix-pass-modified module restored from `HEAD` was built alongside the live
#:   tree and the per-frame digests differenced. **0 frames added, 0 removed, 8
#:   changed**, and every one is a direct consequence of a text/declaration edit
#:   already in this rc's diff:
#:     * `lstsq_exact`, `singular_values_exact`, `jordan_form_exact` — the three
#:       ToolEntry SUMMARIES the fix pass rewrote (the lstsq two-engine
#:       projection, the mixed-σ absent-not-refused wording, and the
#:       integer-valued operand correction);
#:     * `Mat`, `QMat`, `Q`, `Vec`, `int` — five CARRIER frames, whose consumer /
#:       producer lists are DERIVED from the declared parameter type tokens, and
#:       the fix pass replaced the dishonest `Mat` tokens on `lstsq_exact`,
#:       `singular_values_exact` and `separate_frame_curvature` with the exact
#:       ones the ops actually accept. `lstsq_exact` and `singular_values_exact`
#:       correctly LEAVE the `Mat` consumer list and JOIN `QMat`'s;
#:       `separate_frame_curvature` is on both, which is what a two-rung op is.
#:   Ops whose only edit was a parameter description or type did NOT move their
#:   own op frame — the blob carries the summary and the worked EXAMPLE, not the
#:   per-parameter prose — which is itself a check that the diff is the one
#:   described.
#:
#:   MOVE 3 `24a0858e…` -> the value below, and it is one frame: `lstsq_exact`
#:   again. `tests/test_frame_scope_rc430.py` had `NO_ARG` at 281 over a
#:   down-only ceiling of 280, and the marginal op was `lstsq_exact`, harvested
#:   as `no_jsonable_arg` with `unserializable: ["a", "b"]`. The cause was
#:   ORDER, not thinness: `example_args.harvest_op` keeps the FIRST returning
#:   call, and this op's worked snippet led with the `Fraction` witness, which
#:   JSON cannot carry — while the snippet's own all-integer call two lines
#:   below binds cleanly. Moving that call to the front DRAINS the census
#:   (`NO_ARG` 281 -> 280, `ok` 437 -> 438) with the ceiling untouched, which is
#:   the gate's own stated remedy and is why this is not the fourth structural
#:   raise. Differenced the same way: **0 added, 0 removed, 1 changed**.
#:
#:   DETERMINISM, measured before each re-pin was accepted: six fresh
#:   numpy-absent WSL2 interpreters — three plain and three under distinct
#:   `PYTHONHASHSEED` values — all returned the SAME digest with the same
#:   749 = 720 + 29 split. The value is also identical on the NATIVE and PURE
#:   projections (measured with the freshly built `libsrmech.so` present and
#:   with it absent), so the corpus is a function of the committed sources and
#:   not of a build artifact. The ADR-0011 witness contract HOLDS.
#:
#:   Measured LAST, after `regen_all.py` reported all six generated files
#:   written and idempotent across two passes, per the rc454 rule that a pin
#:   taken mid-release is a measurement of a draft.
#: was: c34e8e854128a6266ad57e428cf5295c3ae6d2eec75fe52d0984daf8bfca31a6 (rc462)
#:
#: rc464 (`#T1188`) re-pin — ATTRIBUTED FRAME BY FRAME, per this file's own rule,
#: and the attribution caught a MISS as well as confirming the expected move.
#:
#:   COUNTS: `len(frames)` is **763**, split **734 ops + 29 carriers**, read off
#:   `len(_build_frames('ops')[0])` / `len(_build_frames('carriers')[0])` and
#:   checked against the union. 734 is `EXPECTED_N` — the fourteen cdr_*
#:   registrations rc464 added (720 -> 734). Carriers UNMOVED at 29: this rc
#:   mints no carrier TYPE.
#:
#:   METHOD: a pristine `docs/srmech` was extracted with `git archive` at TWO
#:   refs — `05202a8aa` (rc463 tip) and `54d2dbf21` (this rc's first commit) —
#:   and the per-frame digests differenced against the live tree, rather than
#:   the move being assumed from the diff. NOTE FOR THE NEXT RE-PIN: extracting
#:   only `docs/srmech/python` is NOT enough to reproduce a witness. Measured:
#:   a python-only extraction of rc463 tip returned `04bc0852…`, not the pinned
#:   `f1f521af…`, because the corpus reads generated C-side material too. Archive
#:   `docs/srmech` whole.
#:
#:   MOVE 1 `f1f521af…` -> `5bf91348…`, and it is ONE frame: `cd_register`,
#:   changed. rc464's first commit repointed sixteen shipped `[1, 64]` sites to
#:   the real `CD_MAX_DIM` of 256, four of them inside `cd_*` ToolEntry summaries
#:   and parameter descriptions, and the `cd_register` blob carries its summary.
#:   That commit did NOT re-pin this witness — the miss was found by running this
#:   gate here rather than in CI, which is the whole reason a corpus digest is
#:   cheaper than a review.
#:
#:   MOVE 2 `5bf91348…` -> `e728909c…`: **+14 added, 0 removed, 2 changed**.
#:   The fourteen added are exactly the `srmech.cascade.cdr_*` adapters the
#:   packaged `cd_register.toml` [class] descriptor binds its methods to. The two
#:   CHANGED are the `float` and `int` CARRIER frames, and that is a consequence
#:   rather than a coincidence: a carrier frame's consumer / producer lists are
#:   DERIVED from declared parameter type tokens, and the new entries declare
#:   `int` (dim / slot / j / n) and `list[float]` (the coupler's streams), so both
#:   carriers legitimately gain consumers. Nothing else moved — in particular the
#:   `cd_*` free-function frames are untouched, which is the check that the +14
#:   are additions and not a rename of the family they sit beside.
#:
#:   MOVE 3 `e728909c…` -> the value below, and it is the rc454 rule earning its
#:   keep INSIDE one rc rather than across two. `e728909c` was measured after a
#:   clean `regen_all.py`, and it was still a measurement of a draft: the
#:   fourteen ops then gained their WORKED snippets, and a frame blob carries
#:   the worked example, so all fourteen op frames moved again. Differenced the
#:   same way against `05202a8aa`: **+14 added, 0 removed, 3 changed** — the
#:   `float` and `int` carrier frames and `cd_register`, i.e. the union of what
#:   moves 1 and 2 each did, with the fourteen additions in their final form.
#:   The lesson is narrower than "re-measure last": a pin whose corpus includes
#:   EXAMPLES cannot be taken until the examples are final, and a worked snippet
#:   is authored after the entry it documents.
#:
#:   Measured LAST, after `regen_all.py` reported all six generated files written
#:   and idempotent across two passes, per the rc454 rule that a pin taken
#:   mid-release is a measurement of a draft.
#:
#:   MOVE 4 `dfa8cfa9…` -> `b213cf4f…`: **0 added, 0 removed, 4 changed**,
#:   and the four are the whole of rc464's preferred-shape rewording — the
#:   `srmech.cascade.cd_register` and `srmech.cascade.sedenion_register` OP
#:   frames (ToolEntry summary + curated explanation) and the `CDRegister` /
#:   `SedenionRegister` CARRIER frames (their `carrier_schema` descriptions).
#:   Counts UNMOVED at 763 = 734 ops + 29 carriers: this move registers nothing
#:   and mints no carrier, so a count change here would have meant something
#:   other than a reword happened. Differenced the same way as moves 1-3, by
#:   `git archive`-ing `docs/srmech` WHOLE at `eaee799a7` and building both
#:   corpora — and the extracted rc464-stage-1 tree reproduced `dfa8cfa9…`
#:   exactly, which is what makes the four-frame attribution a measurement
#:   rather than a reading of the diff.
#:
#:   MOVE 5 `b213cf4f…` -> the value below, the rc464 REMOVAL half: **0 added,
#:   2 removed, 12 changed**, counts 763 -> 761 (733 ops + 28 carriers).
#:   Attributed frame by frame against a `git archive` of `3d404205d`, which
#:   reproduced `b213cf4f…` exactly.
#:
#:     REMOVED (2) — `op:srmech.cascade.sedenion_register` and
#:     `carrier:SedenionRegister`, the 16-slot register's whole searchable
#:     presence. This is the FIRST move on this pin with a removal in it, which
#:     is why the counts move at all.
#:
#:     CHANGED (12), and none of them is a reword for its own sake:
#:       * `carrier:CDRegister`, `carrier:sedenion` — descriptions that named
#:         the removed class.
#:       * `carrier:int` — DERIVED, and the one worth reading twice: a carrier
#:         frame carries the back-index of ops that consume or produce it, and
#:         the removed factory declared an `int` `D` parameter. Nothing about
#:         `int` was edited; its frame moved because an op left. A frame set
#:         that did NOT move here would have meant the back-index is not
#:         actually derived.
#:       * `op:srmech.cascade.cd_navmap` / `cd_navigate` / `cd_couple_working` /
#:         `cd_register` — summaries that pointed at the 16-slot peer.
#:       * `op:srmech.cascade.left_mult_is_invertible` — its curated SIBLINGS
#:         line named `SedenionRegister.is_navigable`.
#:       * `op:srmech.dsl.describe_class` / `list_class_surface` /
#:         `srmech.introspect.carrier_schema.carrier_schema` /
#:         `srmech.introspect.describe` — the four curated example TRANSCRIPTS
#:         that printed the removed class. Re-EXECUTED rather than hand-edited.
#:
#:   Measured LAST, after `regen_all.py` reported all six generated files
#:   idempotent across two passes, per the rc454 rule that a pin taken mid-rc is
#:   a measurement of a draft.
#: was: f1f521af99cbcf3a3b404a11e521052e08d26577ccf0cc04c5f356816138f5cd (rc463)
#: was: dfa8cfa99710c81f1be406d32e0ec42a15dcfb8c699d893e3c02f302540236f1 (rc464 stage 1)
#: was: b213cf4fc311e5ae06beee96061d9b919653e921bcf749a5312765b1053e341d (rc464 stage 2)
#:
#: rc464 CLOSING PASS — re-pinned a FOURTH time inside this one rc, and the
#: attribution is why that is acceptable rather than a habit. CI (not the local
#: subsets) reported `cdr_element_of` accepting a `CDRegister`, naming it in its
#: own coercion raise text, and DECLARING `int` —
#: `test_declared_type_honesty_rc363.py`'s C2 clause, strict-zero. The parameter
#: type was corrected from `object` to `CDRegister | CatalogClass | dict`, which
#: is a CORPUS edit: the carrier frame aggregates the ops that declare it.
#:
#:   MEASURED, frame by frame, against a `git archive 195c2c4f0` extraction of
#:   the whole docs/srmech subtree: frames 761 -> 761, **0 added, 0 removed,
#:   exactly 1 CHANGED — `CDRegister`**, the carrier whose declaration was
#:   fixed. A witness re-pin is only honest when the delta is attributable to
#:   the edit that caused it; this one is, to a single frame.
#:
#:   Taken AFTER `regen_all.py` reported all six generated files idempotent
#:   across two passes, per the rc454 rule that a pin taken mid-rc measures a
#:   draft — and after the last corpus-touching edit of this rc, per the stage-2
#:   lesson that a pin whose corpus includes examples cannot be taken until the
#:   examples are final.
#: was: 9add5607e7cd594594f14f8767543fe25f75a807c04a9d4a8135c3ac8c0f579c (rc464 stage 3)
WITNESS_RC416 = (
    "54fd35fa99df3812ceea67c54c039201c5f92fe284a523cb462bc1923de3e809")
#: rc462 (`#T1179`): re-pinned. The corpus witness is a digest over the SEARCHABLE
#: op corpus, so registering induced_representation + zeta_conjugate moves it by
#: construction. Registry 700 -> 702; no tokenizer or search behaviour changed.
#: was: 401c0fdec037ce544dfe17381d64394aaedb99cda1205dad32c092bb835e1624

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
