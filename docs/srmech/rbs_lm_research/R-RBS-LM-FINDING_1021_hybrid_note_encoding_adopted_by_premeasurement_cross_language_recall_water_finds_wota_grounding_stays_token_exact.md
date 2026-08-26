# F1021 (PKG-2 gate item / #230) — **the byteglyph-NOTE pre-measurement decided FOR adoption — of the HYBRID variant only: distinct-note Gram +0.029 (inside the pre-committed +0.05 budget), cross-language recall 2/2 (`water boiling` finds the stored `wota i boela long 100 selsius`; `education for children` finds `ol pikinini oli gat raet long edukesen`), same-language controls unhurt; pure glyph FAILED the rule (+0.056 AND 1/2). Wired into note-recall + cross-turn operand matching ONLY — grounding stays token-exact (byteglyph was rejected there, F1017: same lever, different surface, different verdict — the pre-measurement discipline is what lets both decisions be right at once). The F1017 measured boundary (cross-language content recall) is CLOSED: `siona recall water boiling` → the wota note, 5/5 tests.**

**Date:** 2026-07-02 · **srmech:** 0.9.0rc97 · **Branch:** `research/rbs-lm-rolling-2` (PR #687) · **Milestone:** PKG-2 (#230) — the byteglyph-note gate item DONE by measured choice · **Files:** `siona/infer.py` (`_enc_note` hybrid; `_recall` + cross-turn note-matching rewired), `siona/tests/test_superpose_accrete.py` (+cross-language recall test), probe `R-RBS-LM-FINDING_1021_probe_byteglyph_note_premeasure.py` · **Grounds / composes:** F1017 (the boundary this closes + the tool-index rejection this does NOT overturn — the same lever measured per-surface), F999/F920 (byte/glyph = spelling similarity — the bridge is `wota`~`water`, `edukesen`~`education`: Bislama's English lexification carried by bytes), `[[feedback_read_independent_structure_check_first]]` (the Gram budget was the gate), the pre-committed decision rule (declared before running; both the adoption and the pure-glyph rejection followed it mechanically).

## Grounded (rc97) — the decision table (rule pre-committed: Gram ≤ token+0.05 AND cross 2/2 AND controls 2/2)
```
variant   distinct-note Gram   cross-language   controls   verdict
token     0.267 (baseline)     0/2              2/2        the F1017 boundary (kept for GROUNDING)
glyph     0.323 (+0.056)       1/2              2/2        FAILS the rule (budget + coverage)
HYBRID    0.296 (+0.029)       2/2              2/2        ADOPTED (note-recall only)
wired + tested: 'siona recall water boiling' -> "recall: wota i boela long 100 selsius"  (5/5 affected tests)
```

## The reading
- **One lever, two surfaces, two verdicts — both measured:** byteglyph vectors were REJECTED for the 355-tool grounding index (F1017: +0.130 cross-talk, worse alias) and ADOPTED (as half of a hybrid) for the note store (+0.029, closes cross-language recall). The per-surface pre-measurement is exactly what makes this consistent rather than contradictory: the cost/benefit of spelling-softness depends on the surface's size and its need for cross-spelling bridges, and each surface got its own read-independent decision.
- **The bridge is Bislama's lexification, carried by bytes:** `wota`~`water` and `edukesen`~`education` are spelling-near because Bislama is English-lexified — the byte/glyph substrate turns that historical fact into a working recall bridge with zero dictionary, zero alignment training. (Honest bound: this bridge exists only between lexically-related languages; unrelated pairs need the IR/kernel layer, per F1015's alignment result.)
- **Hybrid, not replacement:** the token component keeps exact-match sharpness (controls unhurt), the glyph component adds the spelling reach — superposition again, at the encoding level.

## Verdict / next
**Gate item done by the pre-committed rule; the cross-language content-recall boundary from F1017 is closed for lexically-related pairs, with grounding untouched.** Remaining gate: magnetic role-probe (research), ASL-LEX sense-split map (external fetch + attestation), paraphrase frames, Mat/Vec/HV operands, version SSOT, clean-venv verify, then the release mechanics (own PR, lemonforest/siona publisher move — MIT verified, rc1 tag). #230 stays in_progress.
