# F1025 (user check / #230) — **the user's smallwiki-kernel check caught TWO routing classes and drove the fix: (1) QUESTIONS ARE READS — wh-marked utterances had grounded to write/act tools (`april has how many days` → remember STORED THE QUESTION AS A FACT; `chess … how many players` → knowledge.load); read-filtering alone then mis-picked among reads (define pulled an irrelevant dictionary hit; continue walked the substrate) while recall held the answer; (2) the completing declared rule: a verb-less question whose CONTENT words appear in a memory note is a CONTENT question → recall (exact-token + prefix-cover, integer match, no thresholds); otherwise the read-filtered grounding stands (`siona what can you do` still finds help). And recall now answers WITH its provenance — an attested note carries its MPR citation inline: `[attested: Wikipedia contributors, 'april', Simple English Wikipedia (CC-BY-SA) | sha256=a539bf670b23]`. The full conversational loop verified: instructed load → MPR-attested acquires → both content questions answered from the correct attested notes with citations → introspective question unaffected.**

**Date:** 2026-07-03 · **srmech:** 0.9.0rc97 · **Branch:** `research/rbs-lm-rolling-2` (PR #687); synced to lemonforest/siona PR #1 · **User direction:** "check if siona is able to correctly respond to instructions to load the smallwiki kernel and then ask it a few questions that should be attested from smallwiki sparse kernel" · **Files:** `siona/infer.py` (questions-are-reads filter + content-question→recall rule + attested-citation recall) · **Composes:** F1024 (the knowledge loop this completes), F1023 (wh-in-situ routing — this is its read-side counterpart), F1008 (aboutness — the note-content match IS an aboutness read, integer-count sparse), `[[feedback_operators_declared_operands_by_meaning]]` (the interrogative's ROLE extends: it marks the read-mode, content selects the note), AMSC/MPM (the citation travels with the answer).

## Grounded (rc97) — the check transcript
```
siona> load .../simplewiki_fullbody_instrument.ndjson   -> instrument loaded (+ title index, sha256=f0ffdc211295)
siona> acquire april   -> MPR-ATTESTED sha256=a539bf670b23 offset=0
siona> acquire chess   -> MPR-ATTESTED sha256=d197bbfbe824 offset=3774198
siona> april has how many days
[siona.recall] ... it is one of four months to have 30 days ... [attested: Wikipedia contributors, 'april',
               Simple English Wikipedia (CC-BY-SA) | sha256=a539bf670b23]
siona> chess is a game played by how many players
[siona.recall] ... each player has an equal amount of time for the game ... [attested: ... 'chess' ... | sha256=d197bbfbe824]
siona> siona what can you do -> [siona.help] my commands (12, from my live schema): ...
BEFORE the fixes: q1 -> [siona.remember] noted (the question stored as a fact!); q2 -> [siona.load] error;
after read-filter alone: q1 -> define (irrelevant dictionary hit); q2 -> continue_text ('the').
```

## The reading
- **The user's check did exactly what a check is for** — the capabilities all existed (load, acquire, attest, recall) but the QUESTION path to them mis-routed twice, and only a live conversational session surfaces that. Both fixes are declared structure, not tuning: a wh-mark selects READ-mode; content-word presence in memory selects the CONTENT read. Zero thresholds — the note-match is an integer count over exact tokens with prefix-cover.
- **The attestation now travels with the answer.** The user's phrase "questions that should be attested from smallwiki" is now literal: the answer arrives WITH its MPR citation (source, license, record hash). This is the anti-hallucination claim made visible at the surface where it matters — the reader can trace every recalled fact to the exact record bytes.
- **Honest limit stated:** recall returns the whole acquired note (the answer "30 days" / "each player" is IN it, cited), not an extracted value. Sub-note extraction ("30" as the answer to "how many days") is the next reasoning rung — the F774 closed-op tier direction over attested notes, not a routing fix.

## The third catch (the suite's turn to catch one)
The content-question→recall rule as first written SHADOWED THE ANSWER PATH: the F1012 smoke turned red because
`water boils at what fahrenheit` (a content question — its words match the remembered fact) now recalled the
fact instead of deriving 212. The completing form: **content-question → ANSWER first; each of _answer's four
honest-miss returns falls back to the cited content recall.** The derivation wins when a kernel composes
(`212 fahrenheit (EXACT: (100*9+32*5)/5 …)`), the attested note answers otherwise (April → cited recall).
Both regimes verified in one session. The read-ladder is now: define-frames (route) → answer (derive) →
recall (cited content) → filtered grounding (help/show) — every rung declared, every miss honest.

## Verdict / next
**The check PASSES end-to-end after two caught-and-fixed routing classes: conversational load ✓, MPR-attested acquire ✓, content questions answered from the correct attested notes WITH citations ✓, introspective questions unaffected ✓.** Next rungs banked: sub-note answer extraction (closed-op tier over attested notes); plural/inflection in the cover rule if a real miss shows; multi-note synthesis questions.
