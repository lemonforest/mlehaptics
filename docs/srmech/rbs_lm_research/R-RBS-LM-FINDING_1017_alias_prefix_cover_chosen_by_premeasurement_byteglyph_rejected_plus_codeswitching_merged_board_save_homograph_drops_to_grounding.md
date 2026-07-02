# F1017 (PKG-2 gate item + user question / #230) — **(1) alias/morphology SOLVED by pre-measurement: PREFIX-COVER promotion wins (index Gram unchanged at 0.271, eval kept 15/18, alias 3/5 gained) and the byteglyph-vector alternative is REJECTED read-independently (+0.130 index-wide cross-talk AND worse alias 1/5) — the structure check killed the attractive option a THIRD time; (2) CODE-SWITCHING measured (user: "do bilingual people mix languages… what happens with mixed Bislama+English inputs"): the MERGED bilingual board routes mixed input 5/5 and runs a flawless mixed dialogue (`mekem the gcd blong 48 and 36` → 12; `wanem is the fiedler vector` → the definition), the attested `save` HOMOGRAPH (eng→remember vs bis→recall) auto-drops from deterministic dispatch to grounding — operators declared, when declarations COLLIDE operands decide — and resolves correctly with content ("save the note that chess is a game" → remember) while failing honestly without it ("save wota" → noise, which is human-like: a bilingual can't disambiguate that cold either); (3) the honest boundary: cross-language CONTENT recall (`luksave water` vs the stored `wota`) FAILS as predicted — token-exact vectors are orthogonal; the spelling bridge lives at byteglyph, whose index-wide cost was just measured — the targeted memory-note byteglyph augmentation is the scoped next question. Bonus catch: the merged strip was DOCTORING stored notes (F982) — notes now store undoctored (strip = address + dispatching verb only).**

**Date:** 2026-07-02 · **srmech:** 0.9.0rc97 · **Branch:** `research/rbs-lm-rolling-2` (PR #687) · **Milestone:** PKG-2 (#230) — the alias gate item DONE (measured choice); the code-switching question ANSWERED · **Files:** `siona/infer.py` (prefix-cover in `ground()`; undoctored note storage), `siona/boards.py` (`merge_boards` + the conflict rule), `siona/tests/test_alias_and_codeswitch.py`, probes `R-RBS-LM-FINDING_1017_probe_{alias_premeasure,codeswitch_merged_board}.py` · **Grounds / composes:** `[[feedback_read_independent_structure_check_first]]` (the pre-measurement WAS the decision: byteglyph rejected on intrinsic cross-talk before any retrieval argument could tempt), F1016 (the attested `save` homograph — now the measured conflict case), `[[feedback_operators_declared_operands_by_meaning]]` (extended: when two boards' declarations collide, the operator is no longer deterministic and MEANING decides), F982 (notes undoctored), F1015 (the byteglyph content-bridge cost measured there for tools; here its absence measured for cross-language recall). · **User directions (2026-07-02):** "keep going down the list" + "we're also curious if bilingual people mix their languages when they think and talk. what happens if we try testing inputs that mix bislama and english."

## Grounded (rc97)
```
(1) ALIAS PRE-MEASUREMENT (the decision table):
                      Gram(read-indep)   eval        alias
    baseline          0.271              15/18       0/5
    PREFIX-COVER      0.271 (no re-enc)  15/18       3/5   <- CHOSEN (cos/sin/tan; misses: len-cap 'exponential', multi-token 'laplacians')
    byteglyph vecs    0.401 (+0.130!)    15/18       1/5   <- REJECTED read-independently
(2) CODE-SWITCHING:
    merged board 'english+bislama-udhr': 9 self-verbs, 16 imperatives; CONFLICT detected: save->(remember|recall) -> DROPPED to grounding
    routing mixed input: ENGLISH 4/5 (wanem unknown) | BISLAMA 5/5 | MERGED 5/5
    the mixed dialogue (merged board):
      'siona remember that wota i boela long 100 selsius' -> noted  (eng verb + bis content; stored UNDOCTORED after the fix)
      'mekem the gcd blong 48 and 36'                     -> gcd(48,36)=12   (bis imperative drives srmech)
      'wanem is the fiedler vector'                       -> the fiedler definition  (bis interrogative + eng content)
      'siona soem the working memory'                     -> both items listed
    the save HOMOGRAPH (conflict -> grounding; operands decide):
      'siona save the note that chess is a game' -> remember  (content decided correctly)
      'siona save wota'                          -> noise     (near-zero content: honest failure -- a bilingual can't
                                                               disambiguate 'save wota' cold either; fallback policy = gate item)
(3) the honest boundary: 'siona luksave water' does NOT retrieve the stored 'wota' note -- token-exact vectors are
    orthogonal across spellings; the water~wota bridge exists only at byteglyph (whose index-wide cost = +0.130 was
    just measured). Targeted BYTEGLYPH NOTE-ENCODING for memory recall (a much smaller surface than the tool index)
    = the scoped next question, with its own pre-measurement required.
BONUS CATCH: the merged strip doctored stored notes ('wota i boela long...' -> 'wota boela...'); notes now store
    with strip = address + dispatching verb ONLY (F982; query-stripping unchanged -- queries de-noise, notes never).
```

## The reading (the user's question, answered)
- **Yes — mixed input works, and the architecture says why.** Code-switching decomposes into three layers: (a) **operator mixing** — the union of two declared closed classes is still a declared closed class, so the merged board routes 5/5 by construction; (b) **the homograph** — where the two declarations *collide* (`save`), no closed-class rule can decide, and the merge rule does exactly what a bilingual does: hand it to *context* (grounding by meaning). With content it resolves correctly; with none it fails like a human would; (c) **content mixing** — free at the byte/glyph substrate but NOT yet bridged in recall's token-exact vectors — the measured boundary, with the scoped fix identified and its cost-model already half-measured.
- **The pre-measurement discipline made the alias decision for us — against the attractive option, again.** Byteglyph vectors *sound* right for aliases (spelling-soft matching) and would also have "solved" water~wota — but the read-independent Gram showed +0.130 index-wide cross-talk AND it was *worse* on the alias cases themselves (1/5 vs 3/5). Third time this session the structure check rejected a plausible-but-wrong option before a read-dependent number could sell it (F1002 elliptic, F1010 threshold, now this).
- **The `save` homograph is the linguistically honest detail:** the same attested string carrying different operator roles per language is exactly what bilingual code-switching research deals in, and the conflict rule — *declared operators; colliding declarations fall to meaning* — is the framework's own principle producing human-like behavior (context resolves; no context, no resolution) without any special-case code.

## Honest scope
Prefix-cover's 2/5 alias misses are structural (len-cap +4 guards `sin`⊄`single`; multi-token names need every token covered) — documented, not hidden; a fuller morphology layer is a different mechanism (F769 edit-distance family) if ever needed. The 5-utterance mixed eval is small (hand-authored); the merged board inherits ENGLISH kernel slots (documented choice). Cross-language content recall REMAINS OPEN — measured, not fixed (the fix has a required pre-measurement). 'save wota' noise suggests a conflict-fallback policy (clarify/ask or configurable default) — gate item. Real Bislama speaker review remains the genuine validation for the board itself (F1016).

## Verdict / next
**The alias gate item is done by measured choice (prefix-cover; byteglyph rejected read-independently), and the user's code-switching question is answered with measurements: mixed Bislama+English input runs correctly on the merged bilingual board — including real srmech drives under mixed utterances — the attested homograph resolves by context exactly as the operators-declared principle predicts, and the honest boundary (cross-language content recall) is located with its scoped fix identified.** Gate remaining: paraphrase frames, Mat/Vec/HV operands, conflict-fallback policy, byteglyph-note pre-measurement, version SSOT, clean-venv verify. #230 stays in_progress.
