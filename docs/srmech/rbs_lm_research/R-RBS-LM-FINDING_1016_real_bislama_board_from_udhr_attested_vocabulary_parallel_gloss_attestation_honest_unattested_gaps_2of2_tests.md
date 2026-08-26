# F1016 (PKG-2 gate item / #230) — **the REAL Bislama board, authored ONLY from UDHR-attested vocabulary with the parallel English articles as the gloss source (the Rosetta method attesting its own board): `wanem`=what (arts 16/23), `soem`=show/manifest (art 18), `luksave`=recognition→recall (art 6), `talem`=expression (art 19), `save`=know→recall (docf 16 — the cross-board homograph: the same string English maps to *remember*), `mekem`/`jusum` imperatives (arts 8/23), and the strip set MEASURED as doc-freq function-ness over the 31 UDHR-bis sections (i:31 blong:29 mo:27 …). The honest gaps stay honest: no remember-verb (tingbaot is NOT attested in the UDHR) → the slot is EMPTY, and arithmetic kernel words are an explicitly-marked unattested carryover. 2/2 tests pass: routing parity, luksave/soem dispatch, and a real srmech drive under a Bislama utterance (`mekem gcd blong 48 mo 36` → 12).**

**Date:** 2026-07-02 · **srmech:** 0.9.0rc97 · **Branch:** `research/rbs-lm-rolling-2` (PR #687) · **Milestone:** PKG-2 gate item (#230) — the "Bislama board from UDHR-attested vocab" checklist line, DONE · **Files:** `siona/descriptors/bislama_udhr.toml` (per-token attestation comments), `siona/tests/test_bislama_board.py` (2/2), `PUBLISH_GATE.md` (six items checked off) · **Attestation source:** UDHR-bis "Deklereisen Blong Raet Blong Evri Man Mo Woman Raon Wol" (eric-muller/udhr, public domain; local at `~/corpora/udhr/`), parallel-glossed against UDHR-eng per article · **Grounds / composes:** F1015 (the synthetic swap test this converts to a real language), F1013/F649 (dignity-first: a PUBLIC text, not kastom content; the board honors the lineage without touching the tradition), `[[feedback_pdf_extraction_citation_discipline]]` applied to vocabulary (NO token from training data — every operator word verified in the local text, with its article + parallel gloss recorded in the descriptor), F768/F984 (the strip set is MEASURED function-ness, not hand-picked). · **User direction (2026-07-02):** "continue with the Bislama board from UDHR-attested vocab."

## Grounded — the attestation table (all verified in the local text this session)
```
operator     role          attestation (bis)                              parallel gloss (eng, same article)
wanem        interrogative art16 'nomata wanem reis'                      'without any... race'
                           art23 'jusum wanem wok hemi wantem'            'free choice of employment'
soem         show          art18 'blong soem rilijen blong hem'           'freedom to manifest his religion'
luksave      recall        art6  'narafala man i luksave hem'             'right to recognition'
talem        show (alias)  art19 'talem tingting blong hem'               'freedom of opinion and expression'
save         recall        docf16 (e.g. art2)                             know/can  [HOMOGRAPH: eng-board save->remember]
mekem        imperative    art8  'Konstitusen o loa givim, oli mekem'     remedy/acts (do/make)
jusum        imperative    art23 'jusum wanem wok'                        'free choice'
strip        (measured)    doc-freq over 31 sections: i:31 blong:29 mo:27 long:27 we:25 ol:19 o:19 hemi:16 oli:13 se:11 olsem:12
UNATTESTED   remember      tingbaot ABSENT from UDHR-bis -> verb_tools has NO remember mapping (slot empty, documented)
UNATTESTED   kernel arith  times/over/plus absent (a rights declaration) -> English carryover, explicitly marked
TESTS (2/2): board loads with disjoint attested classes + no remember mapping; 'wanem raet blong evriwan'->define;
  'ol man mo woman i gat'->continue; 'siona luksave wota'->recall (retrieves the seeded note); 'siona soem'->show;
  'mekem gcd blong 48 mo 36'->tool-call-> gcd(48,36)=12 (a real srmech drive under a Bislama utterance)
```

## The reading
- **The citation discipline extended to vocabulary, and it held.** Every operator token was verified in the local corpus with its article and parallel gloss recorded in the descriptor — the same verify-the-PDF rule, applied to words. Where the corpus could not attest (remember-verb, arithmetic words), the slot stays **empty or explicitly carried over** — never filled from training data. The board is exactly as capable as its attestation allows, and says so.
- **The parallel corpus is the gloss source — the Rosetta method attesting its own board.** `luksave`'s role comes from art 6's English "right to recognition", not from my priors. One interpretive step (recognition→recall = retrieval-of-the-known) is documented as such in the descriptor.
- **The `save` homograph is the boards-architecture earning its keep:** the identical string maps to *remember* on the English board and *recall* (know) on the Bislama board — per-board operator roles over one substrate, exactly what the profile design exists for.
- **A real srmech computation ran under a Bislama utterance** (`mekem gcd blong 48 mo 36` → 12): tool names stay the srmech surface (correct — they're the tool layer, not the language layer), operands are language-independent evidence, and the board carries the rest.

## Honest scope
The board is UDHR-bounded: ~8 attested operator words + a measured strip set — enough for define/recall/show/imperative routing, NOT a full conversational Bislama profile (no remember-verb; kernel arithmetic carried over; test memory seeded directly where the missing verb would have been used). Frames are single-token (`wanem` — multi-token frames aren't attestable from a declaration's register). The interpretive gloss steps (recognition→recall; know→recall) are documented in the descriptor for a Bislama speaker to correct — the board is a **pointer for the community to improve**, not a claim of fluency. Speaker review would be the genuine validation; everything here is structural + attested.

## Verdict / next
**The gate item is done: siona ships a REAL second-language board authored entirely from attested public-domain vocabulary with recorded per-token provenance, honest unattested gaps, and 2/2 passing tests including a real srmech drive under a Bislama utterance.** Six gate checklist items are now checked off (bag fixtures, recovery, re-rank, UDHR run, egyptian_tla, board-swap→real-board). **Remaining before the rc1 tag:** alias/morphology in grounding (with the cross-talk pre-measurement), paraphrase frames, Mat/Vec/HV operands, version SSOT pass, clean-venv verify — then the publisher move to `lemonforest/siona` (MIT) and the own-PR release cut. #230 stays in_progress.
