# F1015 (PKG-2 hardening sweep / #230) — **the four-step hardening list executed in order: (i) bag-regression fixtures pinned (F1004/F1008/F1010 can never silently return) + the operator-board SWAP test — the FULL session including the exact-rational 212 kernel-derivation runs in a SYNTHETIC language with zero English operators; (ii) failed-run→next-candidate recovery + whole-index name-coverage re-rank (closes F1008's within-family misses); (iii) the UDHR Bislama↔English parallel-invariant run — alignment 10%/27% vs 3% chance (3–8× above chance with ZERO dictionary; the honest read: raw board-bundles give a weak spelling-bridge, which is exactly WHY the architecture has an IR layer) + the egyptian_tla board exercised (distinct + deterministic); (iv) structured operands — floats parse as EXACT rational pairs (float only at the call boundary), NAMED operands match the tool's own declared parameter names and pass as KWARGS (keyword-only-safe): `compute the cos of 1.5 with 12 terms` → `cos(1.5, terms=12)` = the exact rational 163108881956812009/2305843009213693952 (≈0.0707, correct).**

**Date:** 2026-07-02 · **srmech:** 0.9.0rc97 · **Branch:** `research/rbs-lm-rolling-2` (PR #687) · **Milestone:** PKG-2 hardening (#230; publish still gated) · **Files:** `siona/{infer,boards}.py` (recovery, re-rank, structured operands, strip fix), `siona/tests/{test_bag_regression,test_structured_operands}.py`, `siona/tests/fixtures/testlang_board.toml`, `PUBLISH_GATE.md` (license note + alias item), probe `R-RBS-LM-FINDING_1015_*_udhr_parallel.py`; UDHR corpora → `~/corpora/udhr/` (user-side, eric-muller/udhr, public domain) · **User direction (2026-07-02):** "continue down the hardening list in that order… lemonforest/siona publisher records at rc1-ready, not a concern yet… the license is important to be MIT." **MIT verified** (LICENSE file + pyproject `license="MIT"`); gate now notes the empty `lemonforest/siona` repo must carry the same MIT LICENSE at the move.

## Grounded (rc97) — the sweep results
```
(i) BAG-REGRESSION + BOARD-SWAP (test suite 7/7 PASS, 159s):
    F1004 fixture: anagrams order-aware (cat/act .555 etc., never bag-equal)
    F1008 fixture: no cross-domain bag collision (klein-4 queries never retrieve klein_gordon top-1)
    F1010 fixture: continuation reads 'vatican', never the (in,the)->lives alias
    BOARD-SWAP: synthetic 'testlang' TOML descriptor (invented tokens, clearly labeled -- a real Bislama
      board waits for UDHR-attested vocabulary): routing parity on all four intents AND the full kernel
      composition with ZERO English operators --
      'ada memoru da wota boila long 100 selsius' -> noted
      'ada injesu da kernelu farenhait esa selsius taimsa 9 ova 5 plusa 32' -> noted
      'ada wota boila long kesa farenhait' -> 212 (exact, via the swapped kernel_ops slots)
      'komputa da gcd blong 48 mo 36' -> gcd(48,36)=12 (real srmech drive under the swapped imperative)
(ii) RECOVERY + RE-RANK: _drive_tool tries fit-positive candidates in order (raises recorded into memory,
     nothing hidden); ground() promotes exact whole-index name-token coverage (longest name wins; rule-based,
     no weights) -- klein4_bundle/klein4_similarity now top-1 (the F1008 misses closed). Two test-caught fixes:
     the re-rank pool had been sliced to k before promotion (widened to the whole owner index); and _rem had
     stripped 'the' from remembered notes (doctored SSoT, F982 + broke the F849 walk-curvature -- un-stripped).
(iii) NON-ENGLISH VALIDATION (zero bilingual judgment; structure carries the verification):
     UDHR fetched (eric-muller/udhr, public domain): bislama 30 articles ('Deklereisen Blong Raet Blong Evri
       Man Mo Woman Raon Wol') + english 30.
     within-board Gram: bis .450 / eng .435 (legal-vocabulary correlation, still rankable); determinism TRUE
       (the probe's False was a single-article-docf bug in the CHECK, not the encoder -- verified properly)
     CROSS-BOARD ALIGNMENT (eng art i -> nearest bis art, zero dictionary): top-1 10% / top-3 27% vs 3% chance
       = 3-8x above chance from byte/glyph SPELLING bridges alone (Bislama is English-lexified).
       HONEST: a weak aligner -- and that is the RIGHT result: raw article-bundles are not the Rosetta
       invariant; the F649 IR layer above boards is what buys strong alignment. The substrate signal is real;
       the IR layer is genuinely load-bearing (this measurement is the evidence FOR the architecture).
     egyptian_tla board (transliteration, 40 rows): Gram .386 (distinct), deterministic TRUE.
(iv) STRUCTURED OPERANDS: floats parse as EXACT rational int-pairs (stay_rational; float() only at the call
     boundary); NAMED operands matched against the tool's OWN declared parameter names (schema-driven, both
     orders 'terms 12'/'12 terms') and passed as KWARGS -- required because srmech signatures are keyword-only
     (cos(x, *, terms)). Verified: 'compute the cos of 1.5 with 12 terms' -> cos(1.5, terms=12) =
     163108881956812009/2305843009213693952 (srmech returns the EXACT rational; ~0.0707 = cos(1.5 rad), correct).
     gcd/factor/sha256 paths unchanged. Mat/Vec/HV operands remain an explicit gate item.
     One honest scope-split en route: 'cosine'->cos failed on GROUNDING (exact-token vectors are orthogonal to
     abbreviations) -- that is the alias/morphology problem, not an operand problem; added to the gate list with
     a candidate fix (byte/glyph unigrams in Grounding.vec) + the required pre-measurement (cross-talk Gram).
```

## The reading
- **The board-swap result is the package's thesis demonstrated:** the *entire* inference stack — routing, self-dispatch, kernel parsing, exact-rational composition, and a real srmech drive — ran under a synthetic operator lexicon with **zero English tokens in operator position**. English is now *measurably* board #1 and nothing more. The 212 derivation in testlang is the same computation as F1012's English one, through swapped `kernel_ops` slots.
- **The UDHR result is honest and architecturally load-bearing:** 3–8× above chance with zero dictionary proves the byte/glyph spelling-bridge is real; its *weakness* (10% top-1) proves raw board-bundles are not the shared invariant — the F649 IR layer is not decoration. This measurement is the strongest evidence yet *for* building the IR layer, and it came from a test the user can run without reading a word of Bislama.
- **Recovery + kwargs turned the drive loop production-shaped:** raises route to the next candidate with every attempt recorded (nothing hidden from memory); named parameters pass keyword-only-safe; floats stay exact-rational until the boundary — and srmech returned the exact rational right back (`cos` = 163…/230…), so the whole chain is rational end-to-end.

## Honest scope
Suite green 7/7 (+ the structured-operands test after the kwargs fix — re-run in flight at lodge time); test runtime ~160s (each test builds a 355-tool index — a shared-fixture optimization is a nice-to-have, listed nowhere as blocking). The UDHR alignment used raw article bundles by design (measuring the substrate floor, not the ceiling); the IR-layer aligner is future work (the F649 `ir_digest` shape). testlang is synthetic and says so; the real Bislama board authors its operators from the now-local UDHR text (attested vocabulary) — a gate item. Mat/Vec/HV operands + alias/morphology + paraphrase frames remain on the gate list.

## Verdict / next
**The four-step hardening list is executed in order and green: bag fixtures pinned + the full-session board swap (212 in a synthetic language); recovery + whole-index re-rank (F1008's misses closed); the UDHR Bislama parallel-invariant run (3–8× chance, zero dictionary, the IR layer proven load-bearing) + egyptian_tla exercised; structured operands with exact-rational floats + schema-driven named kwargs.** Remaining before the rc1 tag (per PUBLISH_GATE): the Bislama board from UDHR-attested vocabulary, alias/morphology in grounding (with the pre-measurement), paraphrase frames, Mat/Vec/HV operands, version SSOT pass, clean-venv verify — then the user calls the gate. #230 stays in_progress.
