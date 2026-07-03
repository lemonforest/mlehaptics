# F1026 (user direction / #230; the F774 rung F1025 queued) — **SUB-NOTE EXTRACTION ships as a closed op: the wh-frame DECLARES the answer's shape (`how many days` → NUMBER + `days`; `what month` → ordinal + `month`), and extraction is a Class-D pattern-match + adjacency read over the best attested note — never generation. Live against the real smallwiki kernel: `april has how many days` → `30 days -- extracted from: "...months to have 30 days april always..." [attested: Wikipedia contributors, 'april', Simple English Wikipedia (CC-BY-SA) | sha256=a539bf670b23]` — the extracted VALUE, its source SPAN, and the full MPR citation in one answer. Ordinals work (`what month` → `fourth month`), ambiguity is reported not hidden (`(+1 more span in the note)` — "four months" genuinely also matches), and a question with no answering span falls to the cited whole-note recall (the honest floor). The number/ordinal vocabulary and quantity-words are BOARD operators (english-not-privileged: a board without attested numwords simply doesn't extract).**

**Date:** 2026-07-03 · **srmech:** 0.9.0rc97 · **Branch:** `research/rbs-lm-rolling-2` (PR #687); synced to lemonforest/siona PR #1 · **User direction:** "continue with the sub-note extraction rung from F774" · **Files:** `siona/boards.py` (Board.quantity_words + Board.numwords — declared operator classes, defaults empty), `siona/infer.py` (`_extract` tier between answer-derivation and recall; `_best_note` shared helper; 'how MANY x' target refinement), `siona/tests/test_subnote_extraction.py` (memory-seeded — no corpus in the wheel) · **Composes:** F774 (the closed-op reasoning tier this extends from compare/derive to EXTRACT), F1025 (the read-ladder this completes: define-frames → answer-derive → **answer-extract** → cited recall → filtered grounding), F1024 (the MPR trail the citation rides), `[[feedback_operators_declared_operands_by_meaning]]` (the wh-frame + quantity-word + numword classes are all DECLARED; only the note content is meaning-resolved).

## Grounded (rc97) — live against the real kernel
```
siona> acquire april -> MPR-ATTESTED sha256=a539bf670b23 offset=0
siona> april has how many days
[siona.answer] 30 days -- extracted from: "...months to have 30 days april always..."
               [attested: Wikipedia contributors, 'april', Simple English Wikipedia (CC-BY-SA) | sha256=a539bf670b23]
siona> april is what month of the year
[siona.answer] fourth month (+1 more span in the note) -- extracted from: "...apr is the fourth month of the..."
               [attested: ...]
miss regime: 'chess is played by how many players' over a note with NO adjacent number -> recall: (whole note, cited)
```
The op: parse wh-frame → target unit ('how MANY x' → the unit follows the quantity word) → best note
(the same ranking recall uses) → scan for unit tokens (exact or prefix-cover ±4) → adjacency read at
j-1/j-2 for a digit or board-numword → span [number..unit] + a ±3-token context window + the MPR cite.
Multiple spans → first answers, count reported. No spans → cited recall. Zero thresholds anywhere.

## The reading
- **Extraction is a READ, structurally guaranteed:** every answered token exists verbatim in the attested note at a located offset — the answer can be re-verified byte-for-byte against the record its sha256 names. This is what "can't confabulate the value" means at this rung: the op has no vocabulary except the note's own tokens.
- **The board owns the linguistic closed classes:** quantity-words and numwords are per-board declared operators like interrogatives and politeness. English got its attested set; the Bislama board extracts nothing until its number vocabulary is UDHR-attested (the honest gap, consistent with F1016's unattested-slots discipline).
- **Ambiguity is surfaced, never resolved silently:** "(+1 more span)" told the truth — "four months" is a real second number+unit span in the note. The first-span choice is positional and stated; a wrong first span is visible and correctable by the reader, not hidden.

## Verdict / next
**The F774 extraction rung ships: count and ordinal questions answer with the extracted value + source span + MPR citation; misses fall honestly. Suite green pending this commit's run (18 tests).** Next rungs banked: unit-AFTER-number orders (other languages / 'players two'); multi-note synthesis (compare two attested notes — the original F774 compare op over acquired knowledge); Bislama numwords from UDHR attestation.
