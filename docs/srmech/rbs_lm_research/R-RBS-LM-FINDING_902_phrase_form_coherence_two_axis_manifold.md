# F902 — hardens F901(i): phrase-level FORM coherence detected by the C1 scale-invariance manifold, on TWO axes. The fractal principle "a coherent whole is made of on-manifold parts" is measurable one rung up: LEXICAL (are the words on the real-word manifold?) catches gibberish; SEQUENTIAL (are the adjacencies on the real-adjacency manifold?) monotonically orders coherent > scrambled > random-word > gibberish. A graded similarity-density signal, not a binary classifier — which is the honest shape of an on-manifold measure.

**Date:** 2026-06-21 · **srmech:** 0.9.0rc13 · **Branch:** `research/rbs-lm-rolling-2` (PR #687) · **Probe:** `R-RBS-LM-FINDING_902_phrase_form_coherence_two_axis_manifold.py` · **Composes / extends:** F901 (the recursive C1 ladder + scale_signature — this is its "(i) push coherence up to the phrase level" next-step), F900 (the C1 reframe), F761/F737 (the ni-Vanuatu glyph base = C1), F552 (the noise rule — a deviation can be a substrate feature) · **User direction (2026-06-21):** "harden first with (i) phrase-level coherence detection."

## The method — coherence by recursion (the fractal introspection)
A phrase is coherent iff its **sub-units are themselves on-manifold**, checked one rung down:
- **LEXICAL axis** — each word's neighbor-density (max-similarity) to a real-word manifold (`word_C1` of the corpus vocab). Detects whether the *atoms* (words) are real.
- **SEQUENTIAL axis** — each adjacent pair's neighbor-density to a real-**adjacency** manifold (`bigram_C1` of the corpus's real adjacencies). Detects whether the *bonds* (word-order) are real.

Both axes are the SAME C1 scale-invariance from F901, applied at the rung below the phrase. Native `sim_k4_batch` for the neighbor-density. (The lost first run died at the storm power-cut; this is the re-run, sped up with batch similarity.)

## Measured (srmech rc13, D=8192, |adjacency manifold|=700, |word ref|=500, 24 phrases/type; chance ≈ 0.25)

| phrase type | LEXICAL (words real?) | SEQUENTIAL (adjacencies real?) |
|---|---|---|
| **coherent** (real corpus phrase) | 0.723 | **0.744** |
| **scrambled** (real words, shuffled order) | 0.723 | 0.643 |
| **random-word** (random real words) | 0.749 | 0.568 |
| **gibberish** (random byte-strings) | **0.425** | 0.485 |

## Reading (honest)
- **LEXICAL cleanly flags gibberish** (0.425 vs ~0.72–0.75 for all real-word phrases). Real words sit on the word manifold; random byte-strings fall off it. (Gibberish stays above chance 0.25 because random byte-strings still share *some* bytes with real words — the byte/glyph core is graceful, not all-or-nothing.)
- **SEQUENTIAL monotonically orders by word-order coherence**: coherent **0.744** > scrambled **0.643** > random-word **0.568** > gibberish **0.485**. The adjacency manifold detects *real word-order*: a coherent phrase has real adjacencies; shuffling real words lowers it; random words lower it more; gibberish lowest. ~0.10 steps — a **graded** signal.
- **Two orthogonal axes:** LEXICAL = "are the atoms real" (catches gibberish); SEQUENTIAL = "are the bonds real" (catches scrambles + random). Together they place each phrase type on a coherence grid. This is the F901 `scale_signature`(4b) lifted to the phrase rung, on two axes.
- **It is graded, not binary** — an on-manifold *density*, inherently soft. The detector orders/ranks coherence; it does not hard-classify. That is the correct, honest shape (and it is what a similarity manifold yields).

## Scope / boundary (getting the piece correct)
This is a **FORM** coherence detector (spelling + adjacency), built purely from the byte/glyph C1 manifold. It does **not** reach **semantic** coherence: an idiom ("kick the bucket") is *form*-coherent (real words, common adjacencies) yet *meaning*-non-compositional — that emergence lives at the **meaning** layer (the resonator/usage model), a separate axis, NOT this manifold. Stating that boundary is part of getting the piece right (F901→F903 arc).

## Verdict / next
**Done (F901 hardening i):** phrase-level FORM coherence is detectable on two axes from the C1 scale-invariance manifold — LEXICAL flags gibberish, SEQUENTIAL orders coherent > scrambled > random > gibberish, graded. Composes the ni-Vanuatu glyph base (F761) — the same machinery is language-agnostic by construction (the Bislama agnosticism test is the next piece). Strictly sparse (Klein-4, bounded byte codebook, numpy-free, no bag). **Next on this arc:** (a) the ni-Vanuatu (Bislama) agnosticism run — same machinery on real ni-Vanuatu text; (b) the semantic/emergence layer (idioms) — the meaning axis this form detector explicitly does not reach; (c) the `sim_k4_batch` hot-path (2k sims/sec — a C-acceleration / upstream-batch candidate). **Hot-path note:** `sim_k4_batch` returns `Q` objects in a Python loop; a native float-returning batch would remove the bottleneck — logged for srmech + a research-local C option.
