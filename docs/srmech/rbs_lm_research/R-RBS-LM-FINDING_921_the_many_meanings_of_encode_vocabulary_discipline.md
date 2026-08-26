# F921 — vocabulary discipline: "encode" is overloaded across the project's layers, and conflating its senses is a real hazard (the user took "word encoding" to mean "spectral encoding for relationships-of-relationships" — two *different* operations, F920 just showed them orthogonal). Because the framework simulates BOTH operators and operands across every domain, each layer has its own "encode." Name the sense. The chess-spectral arc is the cautionary tale: it began as **spectral** encoding (eigenvectors/eigenstates = the shape of relationships) and ended at the **cyclic-algebra duality** — a *different* encoding sense was the real substrate.

**Date:** 2026-06-22 · **srmech:** 0.9.0rc28 · **Branch:** `research/rbs-lm-rolling-2` (PR #687) · **Composes:** F920 (spectral vs byte/glyph, shown orthogonal — the concrete instance), F127 (substrate-native naming discipline), the chess-spectral arc (`docs/chess-maths/`), `[[feedback_correct_user_wrong_words_against_record]]` + `[[feedback_operators_declared_operands_by_meaning]]` (precise-operation discipline) · **User direction (2026-06-22):** "how many different meanings of encode there are now … I thought we were doing spectral encoding for relationships of relationships … I neglected how many meanings 'encode' can have with our project that does span every domain."

## The distinct senses of "encode" (all live in this project)
| # | sense of "encode" | operation | where | class |
|---|---|---|---|---|
| 1 | **spectral** | relationships → eigenbasis (eigenvectors/eigenvalues of the relationship operator); the *shape* of relationships; "relationships of relationships" | F172, F920, chess-spectral origin | **L** |
| 2 | **symbol→vector (HDC)** | a token/byte/word → a hypervector (C1 byte/glyph, Klein-4 bind/bundle, role-filler) — *the* "word encoding" | F901/F916, `encode_word_byteglyph` | **M** |
| 3 | **cyclic-group / phase** | a relationship → a cyclic-group / epicycle / `the_one` phase representation (rotation, time-direction) | the cyclic-algebra duality, Antikythera, LOGO | **I/C/K** |
| 4 | **hypercomplex (Cayley-Dickson)** | content+order → octonion `cd_mult`; address → sedenion | F906–F916 | foundational |
| 5 | **content-address / provenance** | bytes → SHA-256 content hash + the attestation block (MPR) | AMSC/MPM | **A** |
| 6 | **channel / wire (serialize)** | a structure → a byte stream (TLV framing; the bit-serialized instrument) | F898, Class-B | **B** |
| 7 | **rational / numeric** | a value → two ints (Fraction) / `best_rational` | asymptotic_calculus | **N** |
| 8 | **source-model translation** | trained-NN float weights → bipolar HDC bindings (cross-substrate) | R-RBS-LM-4/5 | M∘C |

## The discipline + the lesson
**Name the sense.** "Encode" without a qualifier is ambiguous in a project that simulates operators *and* operands across every domain — the same English word names a different A-N operator at each layer. The conflation is not harmless: the user read the byte/glyph **word-encoding** (#2, local form) as the **spectral relationships-of-relationships encoding** (#1, global relationship) — and F920 measured them **orthogonal** (`cat~cot` spelling vs `king~emperor` usage). They are genuinely different operations that happen to share the verb.

**The chess-spectral cautionary arc:** that journey *began* hunting the shape of relationships through **spectral** encoding (#1 — eigenvectors/eigenstates) and *arrived* at the **cyclic-algebra duality** (#3) as the real substrate. So even the framework's own discovery path crossed from one "encode" sense to another. Reading #1 as the answer would have missed that the duality (#3) was the deeper structure — and reading the byte/glyph (#2) as #1 misses that the spectral kernel (#1) is a *separate, complementary* layer (F920). 

**Practice:** when "encode" appears in a finding, prose, or a request, attach the sense (spectral / symbol→vector / cyclic-phase / hypercomplex / content-address / wire / rational / source-translation), or the A-N class. Composes with `[[feedback_correct_user_wrong_words_against_record]]` (correct to the precise operation) and `[[feedback_operators_declared_operands_by_meaning]]` (function words = operators, declared by rule). This is the same naming-discipline as F127's three substrate-native readings — one structure, many names; say which.

## Verdict
"Encode" carries ≥8 distinct operational senses here, one per layer of the operators-and-operands simulation. The hazard is real and just bit (the spectral-vs-word conflation). Discipline: **always name the encode-sense** (or its A-N class). The chess-spectral arc (spectral → cyclic duality) is the standing example that the senses are not interchangeable.
