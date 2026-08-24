"""rc404 (`#T1069`) — the down-only ratchet on the OVERFLOW/LIMIT conflation.

WHAT IS BEING RATCHETED. Through rc403 the C tree used ``SRMECH_ERR_OVERFLOW``
for two conditions a caller must tell apart: "the buffer YOU supplied was too
small" (grow and retry) and "this bound is structural — an unrepresentable
value, a compiled-in cap, a non-convergent iteration" (retrying is futile).
rc404 adds ``SRMECH_ERR_LIMIT = 8`` for the second and migrates ONE MEASURED
SLICE — ``srmech_json.c`` and ``srmech_toml.c`` — where a live cost defect was
measured. The rest of the tree still conflates them. This file makes that
residue VISIBLE and MONOTONE so it drains instead of drifting.

WHY THE CEILING IS ON LINES AND NOT ON FILES
--------------------------------------------
A file-level ceiling was the obvious first design and it is **arithmetically
impossible**. Measured across the rc404 migration:

======================================================  ======  ======
metric                                                   rc403   rc404
======================================================  ======  ======
``.c`` files MENTIONING ``SRMECH_ERR_OVERFLOW``             98      98
``.c`` files with a ``return SRMECH_ERR_OVERFLOW``          95      95
``return SRMECH_ERR_OVERFLOW`` LINES                       720     706
``srmech_json.c`` returns                                   15      10
``srmech_toml.c`` returns                                   10       1
======================================================  ======  ======

The file count **cannot move**, because both migrated files deliberately RETAIN
their buffer-class returns — 10 and 1, which is exactly ``DRAINED_EXACT`` below.
A file with even one remaining return is still counted by any file-level grep,
so a file-level pin would either sit forever at 98/95 (measuring nothing) or be
set to a number the tree can never reach (reddening rc404 itself).

The alternative reading — "files still returning OVERFLOW for a NON-BUFFER
reason" — is not mechanically decidable. Classifying a given return line as
buffer-class or structural is precisely the human judgement this rc performs by
hand, one site at a time. No grep computes it. Note also that 98 and 95 are
different populations: 98 files MENTION the token, 95 RETURN it. Conflating
"mention" with "return" is its own measurement error.

So the ceiling counts LINES, which do move, monotonically, and are decidable.

WHAT EACH HALF CATCHES
----------------------
* ``DRAINED_EXACT`` is an EXACT pin, both directions. Adding an eleventh bare
  ``return SRMECH_ERR_OVERFLOW`` to ``srmech_json.c`` reds it — which is the
  point: these two files have been adjudicated line by line, so a NEW status-4
  return in them is a claim that needs its own justification, not a default.
* ``CEIL_CONFLATING_RETURN_LINES`` is DOWN-ONLY. It reds if the tree-wide count
  grows, and it reds with a "lower the ratchet" message if it shrinks — so a
  future slice cannot land without recording its own progress.

WHAT THE CEILING ACTUALLY COUNTS — a VOLUME PROXY, named as such (rc420)
------------------------------------------------------------------------
The ceiling counts EVERY live ``return SRMECH_ERR_OVERFLOW`` line, correct and
conflating alike — because (per the paragraph above) "is this line buffer-class
or structural" is not mechanically decidable; that classification is a human
adjudication, one site at a time, and no grep computes it. Two consequences,
both deliberate:

* a CORRECT new buffer-class return still trips the ceiling. That is the
  instrument being honest about its own resolution, not a defect: the trip
  forces the adjudication to happen ON THE RECORD. rc420 is the precedent —
  see the ceiling's own comment below.
* the sanctioned move when the trip is a verified buffer-class addition is an
  EXPLICIT raise with a written adjudication naming each line and why growing
  the caller's arena is the fix — the same discipline ``DRAINED_EXACT``'s
  failure message has always named ("raise the number here and say why").
  A silent bump is never sanctioned; neither is re-labelling a correct
  OVERFLOW as LIMIT just to keep a number flat, which would break every
  caller grow-loop keyed on status 4.

Could the instrument be sharpened to "count only returns NOT shown retryable"?
Only by maintaining a per-site adjudicated allowlist — which is exactly what
``DRAINED_EXACT`` is, extended file by file as sites are hand-audited. Until a
file's every site is adjudicated, the volume proxy over the residue is the
strongest decidable instrument available, and this section is the written
reason why.

COUNTING RULE. Block comments are stripped before counting, because a
``return SRMECH_ERR_OVERFLOW`` inside a ``/* ... */`` narration is prose, not a
producer site. Measured at rc404: **2** such lines (``srmech_ndjson.c`` and
``srmech_rational.c``), neither in the migrated slice. A raw grep therefore
reads 2 high; this file's counter strips them and pins the stripped number.

KNOWN REMAINING CONFLATION, named so it is not mistaken for done: ``srmech.h``
documents ``SRMECH_ERR_OVERFLOW`` as a "bounded buffer overflow guard", and
that is still FALSE for the ~700 unmigrated sites — for instance
``srmech_ndjson.c`` returns it for a line exceeding
``SRMECH_NDJSON_MAX_LINE_BYTES``, a compiled-in structural cap that is
LIMIT-class by rc404's own rule. The comment becomes true when the ratchet
reaches the buffer-only floor, not at rc404.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

#: ``docs/srmech/c/src``. ``parents[2]`` is ``docs/srmech``, which reaches ABOVE
#: ``docs/srmech/python`` — hence the mandatory SCAN_ROOTS declaration in
#: tests/test_ref_notation_emitted_rc348.py (``("docs/srmech/c",)``).
_C_SRC_DIR = Path(__file__).resolve().parents[2] / "c" / "src"

#: EXACT pin: the buffer-class returns that SURVIVE in the migrated slice.
#: These two files were adjudicated site by site in rc404, so both a new
#: status-4 return and the loss of a legitimate one must be deliberate.
DRAINED_EXACT = {
    # json: the arena / output-buffer returns. The structural six (the
    # tmp[64] staging bound, strtoll ERANGE, the >int64 guard, uint32
    # child-count saturation, and both depth caps) moved to LIMIT.
    "srmech_json.c": 10,
    # toml: exactly ONE survivor — genuine arena exhaustion in
    # toml_arena_alloc. Its compound partner (a saturated toml_align_up,
    # which no arena satisfies) split off to LIMIT, as did the other nine.
    "srmech_toml.c": 1,
}

#: DOWN-ONLY CEIL on tree-wide ``return SRMECH_ERR_OVERFLOW`` LINES, comments
#: stripped. rc403 measured 718 (720 raw, less 2 inside block comments);
#: rc404 migrates 14 of them, landing at 704.
#:
#: rc420 (`#T1114`) ADJUDICATED RAISE, 704 -> 706 — never a silent bump. The
#: sixth combinator (``dsl_run_map_indexed`` in ``srmech_dsl_chain_run.c``)
#: added exactly two returns, both verified buffer-class at the source:
#:
#:   * ``if (res == NULL)   { return SRMECH_ERR_OVERFLOW; }`` — ``dv_new``'s
#:     only NULL path is its ``dcr_carve`` of ``sizeof(dv_value_t)`` failing;
#:   * ``if (items == NULL) { return SRMECH_ERR_OVERFLOW; }`` — the item
#:     pointer-array carve failing;
#:
#: and ``dcr_carve`` returns NULL on exactly one condition: the requested
#: bytes do not fit the remaining bump arena, which is built directly on the
#: CALLER-SUPPLIED ``ws``/``ws_len``. Grow the arena and retry, and the call
#: may succeed — the rc404 definition of status 4. The structural bounds in
#: the same function (``n > DCR_MAX_SEQ`` compiled cap, non-LIST input,
#: unknown map body) all return ``SRMECH_ERR_NOT_IMPL`` (defer to pure)
#: BEFORE either carve, so neither line is reachable through a condition no
#: arena can relieve; and ``DCR_MAX_SEQ = 1<<24`` bounds the carve request
#: (``n * sizeof(void *) + 1``) far below any size_t wrap. No conflation —
#: the ceiling moved because the instrument counts volume, not because the
#: residue grew (see "WHAT THE CEILING ACTUALLY COUNTS" above).
#: rc442 (`#T1150`) ADJUDICATED RAISE, 706 -> 712 — again never a silent bump.
#: The §GROUP/v20 nesting work adds exactly SIX returns to
#: ``c/src/srmech_genome.c``, and every one was read at its source against the
#: rc404 definition. Named individually, because "six new lines in one file" is
#: exactly the shape a silent bump would hide:
#:
#:   * ``srmech_genome_group_wrap``: ``out_cap < (n_blocks + 2u) * dim`` — the
#:     CALLER's output buffer cannot hold the wrapped strand. Textbook status 4:
#:     the required size is stated in the header, and growing ``out`` to it makes
#:     the same call succeed.
#:   * ``genome_strings_alloc``: the NULL check over the nine
#:     ``genome_arena_alloc`` carves (three of them new: ``region_sha`` resized to
#:     ``n_regions``, plus ``reg_offset`` / ``reg_len``). ``genome_arena_alloc``
#:     returns NULL on exactly one condition — the request does not fit the
#:     remaining bump arena, which is built on the caller-supplied ``ws``/``ws_len``.
#:   * ``genome_build_manifest``'s ``region_items`` carve — the same arena, now
#:     sized to ``n_regions`` rather than ``n_chroms`` because a frame block earns
#:     its own region.
#:   * ``genome_scan_frame_block``: ``s->n_regions >= s->cap_regions``, and
#:     ``cap_regions`` is what ``genome_strings_alloc`` carved OFF THE CALLER ARENA.
#:     A bigger ``ws`` carves more regions and the scan completes.
#:   * ``genome_scan_open_chrom``: ``s->n_regions >= s->cap_regions``, the same
#:     bound reached from the chromosome branch. (Its sibling ``n_chroms >=
#:     cap_chroms`` on the line above is the pre-rc442 line, MOVED by the JPL
#:     Rule-4 extraction, not a new one — the extraction is why this file's diff
#:     looks larger than six.)
#:
#: TWO are counter-saturation guards rather than buffer failures, and they are
#: called out rather than glossed: ``genome_count_chroms``'s ``groups ==
#: 0xFFFFFFFFu`` and ``genome_fill_strings``'s ``n_chroms > 0xFFFFFFFFu -
#: n_groups``. Under rc404's rule a compiled-in cap is ``SRMECH_ERR_LIMIT``, so
#: the question is real. They stay status 4 because they are neither compiled-in
#: nor structural: they guard the SAME uint32 count table the two lines beside
#: them already guard (``n == 0xFFFFFFFFu``, ``blocks == 0xFFFFFFFFu``, both
#: pre-existing status-4 in this ratchet's own baseline), the count is bounded by
#: how many blocks the caller's body holds, and a caller with 2^32 frame blocks in
#: one body has a size problem, not a policy one. Splitting a three-line guard
#: family across two statuses would make the surrounding code lie about itself.
#:
#: No conflation: the ceiling moved because the instrument counts VOLUME, and this
#: rc added volume to a file that already holds the largest share of it.
#:
#: ── rc447 (gh #1653): 712 -> 721. NINE new lines, ALL in srmech_compose_run.c,
#: ALL verified caller-arena failures. Named individually per this ratchet's own
#: rule, with the NULL provenance for each:
#:
#:   cr_op_cyclic          ov->num == NULL          <- cr_new_bigint -> cr_carve
#:   cr_op_cyclic_inv      ov == NULL               <- cr_new_value  -> cr_carve
#:   cr_op_dseq            res == NULL              <- cr_carve (result vector)
#:   cr_op_pin_slot        lst == NULL              <- cr_new_value  -> cr_carve
#:   cr_op_pin_slot        items == NULL            <- cr_carve (2-slot item array)
#:   cr_op_pin_slot        items[0]/items[1] == NULL <- cr_int_i64 / cr_dbl -> cr_carve
#:   cr_run_fold           acc == NULL              <- cr_int_i64   -> cr_carve
#:   cr_op_dseq            *out == NULL             <- cr_dvec_value -> cr_carve
#:   cr_op_reorient        *out == NULL             <- cr_dbl       -> cr_carve
#:
#: EVERY ONE is `X == NULL` where X came from cr_carve, the chain runner's bump
#: allocator over the CALLER-SUPPLIED workspace. cr_carve returns NULL for
#: exactly one reason — the remaining arena is smaller than the request — so
#: status 4 is the correct status under rc404's rule and a caller's grow-loop
#: terminates: srmech_chain_run_arena_bytes reports a larger figure and the call
#: succeeds. None of the nine is a value outside a representable range, a
#: compiled-in cap, or a non-convergent iteration, so none of them is LIMIT.
#:
#: ⚠️ THE CONTRAST IS LIVE IN THE SAME rc, which is why this is not a rubber
#: stamp: rc447 ALSO added a genuine SRMECH_ERR_LIMIT path — an out-of-int64
#: integer LITERAL declines at srmech_json_parse, and no arena relieves it. That
#: value rides the rc176 decimal-STRING transport instead. So this rc placed
#: lines on BOTH sides of the rc404 distinction, deliberately.
#:
#: No conflation: the ceiling moved because the instrument counts VOLUME, and
#: this rc added a real-sequence arm, a fold arm and a Class-K/C pair to the file
#: that already holds the largest share of it.
#:
#: ── rc451 (`#T1164`, gh #1653 item 4): 721 -> 724. THREE new lines, ALL in
#: srmech_compose_run.c, ALL verified caller-arena failures. Named individually
#: per this ratchet's own rule, with the NULL provenance for each:
#:
#:   cr_op_pair           lst == NULL || items == NULL  <- cr_new_value / cr_carve
#:   cr_op_best_rational  lst == NULL || items == NULL  <- cr_new_value / cr_carve
#:   cr_op_best_rational  items[0]/items[1] == NULL     <- cr_int_u64 -> cr_carve
#:
#: MEASURED, PREDICATE STATED, so the number is reproducible rather than
#: asserted: this file's own `_count_returns` over `sorted(_C_SRC_DIR.glob(
#: "*.c"))` reads 724 at HEAD and 721 at b9a5bc330 (the rc450 merge-base), and
#: the whole delta is one file — srmech_compose_run.c 25 -> 28. The multiset of
#: its stripped return lines has THREE additions and an EMPTY removal set, so
#: nothing was re-statused to make room. Both ops are new in this rc; the base
#: commit contains neither symbol.
#:
#: Provenance traced to the leaf, because "it came from a carve" is the claim
#: being made and a carve is not the only way these helpers answer NULL:
#:   * cr_new_value's ONLY NULL path is cr_carve(b, sizeof(cr_value_t));
#:   * the item array is a direct cr_carve(b, 2u * sizeof(void *));
#:   * cr_int_u64 answers NULL from cr_new_value or cr_new_bigint(b, 3u), and
#:     cr_new_bigint's two NULL paths are both cr_carve. It has NO value-range
#:     NULL — the uint64 is written straight into two of the three carved limbs
#:     with no set/fit call that can fail — so no OPERAND can drive this line,
#:     only an exhausted arena. (Its sibling cr_int_i64 does carry a third,
#:     defensive srmech_bigint_set_i64 check; that line is rc447's, already
#:     adjudicated above, and cap=3 limbs cannot be overrun by an int64.)
#: cr_carve returns NULL for exactly one condition — the request does not fit
#: the remaining bump arena, which is built on the CALLER-SUPPLIED ws/ws_len —
#: so status 4 is correct under rc404's rule and a caller's grow-loop
#: terminates: srmech_chain_run_arena_bytes reports a larger figure and the same
#: call succeeds. None of the three is an unrepresentable value, a compiled-in
#: cap, or a non-convergent iteration, so none of them is LIMIT.
#:
#: ⚠️ THE CONTRAST IS LIVE INSIDE THE SAME FUNCTIONS, which is why this is not a
#: rubber stamp. cr_op_best_rational's other two early exits are deliberate
#: NOT_IMPL declines rather than status 4: an out-of-uint64 or negative operand
#: (cr_as_u64 refusing to narrow silently) and a `with_path=True` request whose
#: third element the wire has no shape for. Those DEFER to the pure projection,
#: and reading either as a buffer failure would have put a fourth line under
#: this ceiling wrongly. rc451's sibling cr_op_dead_band declines a non-double
#: operand for the same reason. So this rc placed exits on BOTH sides of the
#: rc404 distinction, deliberately — and on a third side the ratchet does not
#: count at all.
#:
#: No conflation: the ceiling moved because the instrument counts VOLUME, and
#: this rc added four step arms to srmech_compose_run.c.
#:
#: ── rc452 (`#T1171`): 724 -> 725. The same rc's map-form refactor, adjudicated
#: after it tripped this ratchet in CI. NET +1, and the net is the whole story:
#: TWO lines added, ONE removed, all three in srmech_compose_run.c (28 -> 29).
#:
#:   REMOVED  cr_chain_run_json  c.step_out == NULL   <- cr_carve (flat array)
#:   ADDED    cr_step_map        f->outs == NULL || f->acc == NULL
#:                                                    <- cr_carve / cr_list_of
#:   ADDED    cr_chain_run_json  frames[0].outs == NULL  <- cr_carve
#:
#: MEASURED, PREDICATE STATED: this file's own `_count_returns` over
#: `sorted(_C_SRC_DIR.glob("*.c"))` reads 725 at HEAD and 724 at c8d8c26d4 (the
#: commit that set the current ceiling). Bisected to ONE commit — 2e8e45256,
#: srmech_compose_run.c 28 -> 29; every other commit in the rc reads 28.
#:
#: WHY IT IS +1 AND NOT +2. rc452 replaced the chain runner's single flat
#: `step_out` array with a FRAME spine, so the one carve that used to serve the
#: whole chain became two: one for frame 0 (the chain body, run once) and one
#: per map frame (its per-iteration outputs plus the accumulator). The removal
#: is not a re-statusing to make room — the symbol `c.step_out` does not exist
#: at HEAD.
#:
#: Provenance traced to the leaf, per this ratchet's own rule:
#:   * f->outs and frames[0].outs are direct `cr_carve` calls;
#:   * f->acc comes from cr_list_of, whose ONLY two NULL paths are cr_new_value
#:     -> cr_carve and a direct cr_carve of the item array. It has no
#:     value-range NULL: `n` is copied from the already-resolved sequence's own
#:     length, so no OPERAND can drive it, only an exhausted arena.
#: cr_carve returns NULL for exactly one condition — the request does not fit
#: the remaining bump arena, built on the CALLER-SUPPLIED ws/ws_len — so status
#: 4 is correct under rc404's rule and a caller's grow-loop terminates:
#: srmech_chain_run_arena_bytes reports a larger figure and the same call
#: succeeds. Neither is an unrepresentable value, a compiled-in cap, or a
#: non-convergent iteration, so neither is LIMIT.
#:
#: ⚠️ THE CONTRAST IS LIVE THREE LINES AWAY, which is why this is not a rubber
#: stamp. cr_step_map's own earlier exits are NOT status 4: a non-list
#: `map_over` is SRMECH_ERR_NOT_IMPL (it defers to compose.py's ChainSpecError),
#: and a missing/!ARRAY body or a non-STRING index name is
#: SRMECH_ERR_BAD_INPUT. Reading any of those as a buffer failure would have put
#: extra lines under this ceiling wrongly.
#:
#: ⚠️ AND THE DRAIN WAS CONSIDERED AND REJECTED ON THE MERITS. The alternative to
#: raising was to re-status an existing site so the total stayed flat. Every one
#: of srmech_compose_run.c's 29 status-4 returns was read for this: ALL 29 are
#: `X == NULL` where X came from cr_carve. There is no mislabelled structural
#: site in the file to drain honestly, and draining a CORRECT one is precisely
#: what this ratchet's failure message forbids — "never re-label a correct
#: status-4 return as LIMIT to keep the number flat — grow-loops key on 4". A
#: flat number bought that way would have broken a caller's retry loop to
#: protect a statistic.
#:
#: No conflation: the ceiling moved because the instrument counts VOLUME, and
#: this rc turned one chain-wide carve into a per-frame one.
#:
#: ── rc452 (`#T1166`, gh #1662): 725 -> 739. NET +14, and the net is the whole
#: story: FIFTEEN lines added, ONE removed, every one of them in
#: srmech_compose_run.c (29 -> 43). No other .c file moved at all.
#:
#: MEASURED, PREDICATE STATED, so the figure is reproducible rather than
#: asserted: this file's own `_count_returns` over `sorted(_C_SRC_DIR.glob(
#: "*.c"))` reads 739 at HEAD and 725 at 5b66e46c8 (the commit that set the
#: previous ceiling). ⚠️ A raw `grep -c` reads 744 — five high, because it
#: counts the block-comment narrations this file's counter strips. 744 is the
#: WRONG INSTRUMENT for this ceiling and must never be quoted as the
#: population. Bisected across the rc: 725 (5b66e46c8) -> 734 (6f2eabe99,
#: +9) -> 739 (bc2cccd11, +5) -> 739 (d89d50157, +0).
#:
#: THE ADDED FIFTEEN, by file:line and enclosing function, each with the NULL
#: provenance traced to its leaf — named individually because "fifteen new
#: lines in one file" is exactly the shape a silent bump would hide:
#:
#:   2001  cr_q_apply           *on == NULL || *od == NULL   <- cr_new_bigint -> cr_carve
#:   2002  cr_q_apply           !cr_qctx_init(b,&q,lim)      <- qctx limb carve
#:   2130  cr_op_kur_gen_term   qs == NULL || ov == NULL     <- cr_carve / cr_new_value
#:   2241  cr_op_kur_gen_out    qterm == NULL                <- cr_carve
#:   2579  cr_op_vec_scale      r == NULL                    <- cr_dvec_value -> cr_carve
#:   2647  cr_op_sha256_bytes   hex == NULL                  <- cr_carve (65-byte hex buf)
#:   2668  cr_op_str_concat     buf == NULL                  <- cr_carve (joined text)
#:   2719  cr_op_int_parse_le   ov == NULL                   <- cr_new_value -> cr_carve
#:   2722  cr_op_int_parse_le   ov->num == NULL              <- cr_new_bigint -> cr_carve
#:   2890  cr_op_render_template buf == NULL                 <- cr_carve (render buf)
#:   2953  cr_b_f64_add         ov == NULL                   <- cr_new_value -> cr_carve
#:   2962  cr_b_f64_add         ov == NULL                   <- cr_new_value -> cr_carve
#:   2964  cr_b_f64_add         ov->num == NULL              <- cr_new_bigint -> cr_carve
#:   2994  cr_b_vec_add         ov == NULL                   <- cr_new_value -> cr_carve
#:   3004  cr_b_vec_add         ov->items[i] == NULL         <- cr_dbl -> cr_carve
#:
#: THE ONE REMOVED, so the net is auditable rather than a subtraction nobody
#: sees: `acc == NULL` in cr_run_fold — rc447's line. It is NOT a re-statusing
#: to make room: the fold accumulator moved into the frame spine, and its
#: successor is the already-adjudicated `f->acc` arm of cr_map_enter (3780).
#: The symbol `acc` no longer exists as a cr_run_fold local at HEAD.
#:
#: EVERY ONE of the fifteen is `X == NULL` (or the boolean form of the same
#: check) where X came from the cr_carve family — the chain runner's bump
#: allocator over the CALLER-SUPPLIED ws/ws_len. cr_carve returns NULL for
#: exactly one condition: the request does not fit the remaining arena. So
#: status 4 is CORRECT under rc404's rule and a caller's grow-loop terminates
#: — srmech_chain_run_arena_bytes reports a larger figure and the same call
#: succeeds. NONE of the fifteen is an unrepresentable value, a compiled-in
#: cap, or a non-convergent iteration, so NONE of them is LIMIT-class and
#: there is no structural site here to root-fix. Relabelling any of them would
#: break the grow-loops this ratchet's own failure message protects.
#:
#: The two `cr_*ctx_init` lines are called out rather than glossed, because
#: they are the only two that are not a bare pointer test. cr_qctx_init
#: returns false on exactly one condition — its limb carves off `b` fail —
#: so the boolean is a carve failure wearing a different type, not a
#: value-range refusal.
#:
#: ⚠️ THE CONTRAST IS LIVE IN THE SAME FILE, which is why this is not a rubber
#: stamp: cr_op_reorient's exact-ℚ arm (this rc's own ABI-21 driver) DECLINES
#: with SRMECH_ERR_NOT_IMPL where it cannot answer, and cr_op_best_rational
#: still declines an out-of-uint64 operand the same way. Those defer to the
#: pure projection and are deliberately NOT status 4 — reading either as a
#: buffer failure would have put extra lines under this ceiling wrongly.
#: ── rc452 Phase 2 (`#T1166`, the K1 slice): 739 -> 743. NET +4, all four in
#: srmech_compose_run.c (43 -> 47). No other .c file moved.
#:
#: MEASURED with THIS FILE'S OWN `_count_returns` over `sorted(_C_SRC_DIR.glob(
#: "*.c"))` — 743 — not with grep, for the reason the rc452 block above already
#: records: a raw `grep -c` over-counts by five because it reads the
#: block-comment narrations this counter strips.
#:
#: THE ADDED FOUR, by enclosing function, each with the NULL provenance traced
#: to its leaf. Line numbers are deliberately omitted where the block above
#: gives them, because the additions shift them; the FUNCTION survives an edit:
#:
#:   cr_op_sha256_raw    raw == NULL   <- cr_carve (33-byte raw-digest buffer)
#:   cr_op_mint_vector   buf == NULL   <- cr_carve (D/8-byte hypervector)
#:   cr_op_hdc_permute   buf == NULL   <- cr_carve (n-byte rotated vector)
#:   cr_op_hdc_bind      buf == NULL   <- cr_carve (n-byte XOR result)
#:
#: ALL FOUR are `X == NULL` where X came from cr_carve — the chain runner's
#: bump allocator over the CALLER-SUPPLIED ws/ws_len. cr_carve returns NULL for
#: exactly one condition: the request does not fit the remaining arena. So
#: status 4 is CORRECT under rc404's rule, srmech.h:555's forced direction
#: holds (status 4 keeps the retryable/grow meaning), and a caller's grow-loop
#: terminates — srmech_chain_run_arena_bytes reports a larger figure and the
#: same call succeeds. NONE is an unrepresentable value, a compiled-in cap or a
#: non-convergent iteration, so NONE is LIMIT-class and there is no structural
#: site to root-fix. This is an ADJUDICATED raise with per-line provenance, not
#: a silent bump.
#:
#: ⚠️ THE CONTRAST IS LIVE INSIDE THE SAME FOUR FUNCTIONS, which is what makes
#: this an adjudication rather than a rubber stamp. Each of them ALSO returns
#: SRMECH_ERR_NOT_IMPL (a wrong-typed operand, a D outside [256, 65536] or not
#: a multiple of 8, a length mismatch, an empty vector) and SRMECH_ERR_BAD_INPUT
#: (the delegated primitive refusing). Three statuses, three meanings, chosen
#: per condition — the OVERFLOW arm is the arena one and only the arena one.
#: ── rc452 Phase 2, the K3 slice: 743 -> 745. NET +2, both in
#: srmech_compose_run.c (47 -> 49), both inside cr_op_schur, both measured
#: with THIS FILE'S counter and not with grep:
#:
#:   cr_op_schur   bi == NULL   <- cr_carve (the 2n boundary/interior index pair)
#:   cr_op_schur   s  == NULL   <- cr_carve (the |d|x|d| result block)
#:
#: Same adjudication as the four above and the fifteen above those: cr_carve
#: returns NULL for exactly one condition — the request does not fit the
#: remaining caller arena — so status 4 keeps the retryable/grow meaning
#: srmech.h:555 states is FORCED, and none of them is LIMIT-class.
#:
#: ⚠️ THE FUNCTION'S OTHER FOUR CARVE SITES ARE **NOT** UNDER THIS CEILING, and
#: that is the adjudication, not an omission. cr_schur_mat, cr_schur_idx and
#: cr_schur_solve return NULL rather than a status, and cr_op_schur maps that
#: NULL to SRMECH_ERR_NOT_IMPL — because for those three a NULL means EITHER an
#: arena failure OR a genuine refusal (a ragged L, a duplicate boundary index,
#: a SINGULAR interior block, which is Python's ZeroDivisionError). A capability
#: refusal must defer to the pure projection, which computes the complete
#: answer or raises the documented exception; calling it status 4 would send a
#: caller into a grow-loop that can never succeed. The two lines above are the
#: only two in the arm whose NULL has exactly one cause.
CEIL_CONFLATING_RETURN_LINES = 745

_RETURN_OVERFLOW = re.compile(r"return\s+SRMECH_ERR_OVERFLOW\s*;")


def _strip_comments(text: str) -> str:
    """Blank out C comments, PRESERVING newlines so line counts stay honest.

    STRING- AND CHAR-LITERAL AWARE, and that is not pedantry — a regex-only
    stripper measures this tree WRONG. ``srmech_platform.c`` builds the Windows
    FindFirstFile glob with::

        int w = snprintf(pattern, sizeof(pattern), "%s/*", path);
        if (w < 0 || (size_t)w >= sizeof(pattern)) { return SRMECH_ERR_OVERFLOW; }

    The ``/*`` there is inside a STRING LITERAL. A naive ``/\\*.*?\\*/`` with
    DOTALL treats it as a comment opener, runs to the next ``*/`` somewhere
    below, and blanks the live ``return`` on the following line — silently
    under-counting by one and leaving a real conflating site unprotected by the
    ceiling. The scan below tracks literal state, so that line is counted.
    """
    out = []
    i, n = 0, len(text)
    while i < n:
        c = text[i]
        nxt = text[i + 1] if i + 1 < n else ""
        if c == "/" and nxt == "*":                      # block comment
            j = text.find("*/", i + 2)
            j = n if j < 0 else j + 2
            out.append("".join(ch if ch == "\n" else " " for ch in text[i:j]))
            i = j
        elif c == "/" and nxt == "/":                    # line comment
            j = text.find("\n", i)
            j = n if j < 0 else j
            out.append(" " * (j - i))
            i = j
        elif c in ('"', "'"):                            # literal: copy verbatim
            j = i + 1
            while j < n and text[j] != c:
                j += 2 if text[j] == "\\" else 1
            j = min(j + 1, n)
            out.append(text[i:j])
            i = j
        else:
            out.append(c)
            i += 1
    return "".join(out)


def _count_returns(path: Path) -> int:
    text = _strip_comments(path.read_text(encoding="utf-8", errors="replace"))
    return len(_RETURN_OVERFLOW.findall(text))


pytestmark = pytest.mark.skipif(
    not _C_SRC_DIR.exists(),
    reason=f"C sources not present at {_C_SRC_DIR} (pure-wheel checkout)",
)


def test_migrated_slice_holds_exactly_its_buffer_returns() -> None:
    """The two rc404-migrated files keep EXACTLY their buffer-class returns."""
    for name, expected in sorted(DRAINED_EXACT.items()):
        path = _C_SRC_DIR / name
        assert path.exists(), f"{name} is missing from {_C_SRC_DIR}"
        actual = _count_returns(path)
        assert actual == expected, (
            f"{name}: expected exactly {expected} `return SRMECH_ERR_OVERFLOW` "
            f"(the buffer-class survivors adjudicated in rc404), found {actual}.\n"
            f"  MORE than {expected}: a new status-4 return landed in a file "
            f"whose sites were classified one by one. If the new return really "
            f"is a caller-supplied-buffer failure, raise the number here and say "
            f"why. If growing the caller's arena cannot fix it, it is "
            f"SRMECH_ERR_LIMIT.\n"
            f"  FEWER than {expected}: a legitimate retryable return was "
            f"removed or re-statused; every caller grow-loop keys on status 4, "
            f"so lower this number only with the loop audited."
        )


def test_conflating_return_lines_ratchet_down_only() -> None:
    """Tree-wide status-4 returns may only DECREASE."""
    per_file = {
        path.name: _count_returns(path)
        for path in sorted(_C_SRC_DIR.glob("*.c"))
    }
    total = sum(per_file.values())
    worst = sorted(per_file.items(), key=lambda kv: (-kv[1], kv[0]))[:5]
    worst_text = ", ".join(f"{n}={c}" for n, c in worst if c)

    assert total <= CEIL_CONFLATING_RETURN_LINES, (
        f"`return SRMECH_ERR_OVERFLOW` lines rose to {total}, above the "
        f"down-only ceiling {CEIL_CONFLATING_RETURN_LINES}.\n"
        f"Heaviest files: {worst_text}.\n"
        f"Status 4 means ONE thing as of rc404: a caller-supplied buffer was "
        f"too small and GROWING IT IS THE FIX. If the new site is a value "
        f"outside a representable range, a compiled-in cap, or a "
        f"non-convergent iteration, it is SRMECH_ERR_LIMIT — returning 4 there "
        f"makes a caller's grow-loop allocate its way to a verdict that was "
        f"fixed before it started.\n"
        f"If the new site IS a verified caller-arena failure, the sanctioned "
        f"move is an EXPLICIT raise of CEIL_CONFLATING_RETURN_LINES with a "
        f"written adjudication naming each line and its NULL provenance (the "
        f"rc420 note above the constant is the template). Never bump "
        f"silently, and never re-label a correct status-4 return as LIMIT to "
        f"keep the number flat — grow-loops key on 4."
    )

    assert total == CEIL_CONFLATING_RETURN_LINES, (
        f"GOOD NEWS — status-4 returns fell to {total}, below the ceiling "
        f"{CEIL_CONFLATING_RETURN_LINES}. Lower CEIL_CONFLATING_RETURN_LINES "
        f"to {total} so the progress is locked in and cannot silently reverse."
    )


def test_the_counter_ignores_commented_out_returns() -> None:
    """The instrument must not count prose — proven, not asserted.

    Without this, a docs-only edit could move the ceiling, and the ratchet
    would be measuring narration rather than producer sites.
    """
    sample = (
        "int f(void) {\n"
        "    /* historical: this used to `return SRMECH_ERR_OVERFLOW;` here */\n"
        "    // return SRMECH_ERR_OVERFLOW;\n"
        "    return SRMECH_ERR_OVERFLOW;\n"
        "}\n"
    )
    stripped = _strip_comments(sample)
    assert len(_RETURN_OVERFLOW.findall(stripped)) == 1, (
        "the comment-stripping counter is broken: it must count the ONE live "
        "return and neither of the two commented ones"
    )
    # Line-count preservation matters for any future line-number reporting.
    assert stripped.count("\n") == sample.count("\n")

    # And it must still SEE a live return — an instrument that counts zero
    # everywhere would satisfy the ceiling vacuously.
    assert _count_returns(_C_SRC_DIR / "srmech_json.c") > 0


def test_counter_is_string_literal_aware() -> None:
    """A ``/*`` inside a STRING LITERAL must not open a comment.

    This is a REGRESSION GUARD on the instrument, not on the library. The
    obvious ``/\\*.*?\\*/`` stripper gets this wrong on real srmech source:
    ``srmech_platform.c`` writes ``snprintf(pattern, ..., "%s/*", path)`` for
    the Windows FindFirstFile glob, and a regex stripper swallows from that
    literal to the next ``*/``, blanking the live ``return
    SRMECH_ERR_OVERFLOW;`` on the very next line. The ceiling would then be set
    one too low and one genuine conflating site would sit outside it.
    """
    sample = (
        'int w = snprintf(pattern, sizeof(pattern), "%s/*", path);\n'
        "if (w < 0) { return SRMECH_ERR_OVERFLOW; }\n"
        "/* a genuine comment */\n"
        "int later = 1;\n"
    )
    stripped = _strip_comments(sample)
    assert len(_RETURN_OVERFLOW.findall(stripped)) == 1, (
        "a `/*` inside a string literal was treated as a comment opener, "
        "blanking the live return on the following line"
    )
    assert "int later = 1;" in stripped, (
        "code after the literal was swallowed by a phantom comment"
    )

    # The real file this guard is derived from must still contribute its site.
    platform = _C_SRC_DIR / "srmech_platform.c"
    if platform.exists():
        assert _count_returns(platform) >= 1, (
            "srmech_platform.c's live status-4 return vanished from the count "
            "— the literal-aware scan has regressed"
        )
