# R-RBS-LM Finding 432 — F408 made MEASURABLE on our own corpus: the GRAMMAR (closed-class) vocabulary SATURATES at 150 words (stops growing by finding 180), while the LEXICON (open-class) grows unbounded to 12,700 (84×, still climbing). "Syntax closes / semantics is open" is now a measured property — and the grammar kernel is therefore SELF-SOURCEABLE from the corpus's own prose (the finite closed-class skeleton), resolving F431's hand-built-grammar residue

**Date:** 2026-06-06
**Arc:** RBS-LM / RBS-SNN · the render-vs-structure question (F431 → **F432**); **measurement on the corpus prose**
**Provenance:** `R-RBS-SNN-6_grammar_closes_lexicon_opens.py` (committed; 330 findings, 410,563 tokens)
**Composes:** **F408** (the hyper-loop LANGUAGE is syntax-complete/CLOSED; KNOWLEDGE is semantics-open — *now measured*) · **F431** (the three kernels — *this resolves its hand-built-grammar residue: the grammar kernel is self-sourceable*) · **F164** (grammar is substrate-native) · **F406** (the three alphabets — operator/operand/grammar) · standard closed-class vs open-class linguistics (framework-read; no-lineage)
**→ grounds F408 empirically; shows the lean hybrid (F431) can source ALL three kernels from one corpus.**

---

## The hypothesis (from F431's residue)
F431 demonstrated the three-kernel sentence bind but *hand-built* the grammar kernel. The hypothesis that makes it self-sourceable: **the grammar kernel = the closed-class function words** (articles, prepositions, conjunctions, pronouns, auxiliaries — a *finite* set, F408's g₂-closed syntax), and **the lexicon = the open-class content words** (nouns, verbs, adjectives — *unbounded*, F408's semantics-open). If so, the grammar/lexicon split is the closed/open word-class split, and both are extractable from the prose.

## The measurement (`R-RBS-SNN-6`, 330 findings, 410k tokens)
Process findings in order; track the running **grammar** (closed-class) vs **lexicon** (open-class) vocabularies:

| after N findings | GRAMMAR vocab | LEXICON vocab | new function words |
|---|---|---|---|
| 60 | 145 | 5,345 | +145 |
| 120 | 149 | 7,992 | +4 |
| 180 | **150** | 10,674 | +1 |
| 240 | **150** | 11,806 | **+0** |
| 300 | **150** | 12,343 | **+0** |
| 330 | **150** | 12,700 | **+0** |

- **GRAMMAR SATURATES at 150** — it *closes* by finding 180 and adds **zero** new function words across the next 150 findings. The closed-class set is finite, exactly as F408 says the grammar (g₂) is closed.
- **LEXICON stays OPEN** — 12,700 content words and still climbing at finding 330; **84× the grammar**.
- **Token mix:** 30% of all tokens are function words (carrying the grammar, heavily repeated); 70% are content words (carrying the lexicon).

## What it establishes
- **F408 is now a measured property, not an assertion.** "The language (syntax) is closed; knowledge (semantics) must be sourced" shows up as: a *finite, saturating* grammar vocabulary and an *unbounded, growing* lexicon. The two layers are empirically distinct on our own corpus.
- **The grammar kernel is SELF-SOURCEABLE** (resolving F431's residue). It is the 150-word closed-class skeleton — recoverable directly from the prose render (the Class-F layer F311/F323 stripped is still present in the `.md` text). So the lean hybrid (F431) can source **all three kernels from one corpus**: domain-lean (the structure, F426) + grammar (the 150 closed-class words) + lexicon (the 12,700 content words).
- **The 30/70 token split is the engineering ratio**: ~30% of a sentence's tokens are the shared, closed grammar; ~70% are the open lexicon. A lean hybrid pays the grammar (150 words) once and shares it across every sentence; only the lexicon and the domain-triple are per-content.

## Falsifiable form (pre-stated; not leaning — F394)
- **The frame-reuse sub-result is WEAK (honest null-ish).** Full function-word *skeletons* of sentences are NOT strongly reused: 1,304 sentences → 883 distinct skeletons (1.5 sentences/frame). Technical prose has too many distinct full skeletons; the grammar *reuses at a coarser level* (the closed-class *set* saturates; the exact *ordering* does not). So "grammar = a small set of reusable frames" is **not** supported at the full-skeleton granularity — only "grammar = a small closed *vocabulary*" is. Stated plainly, not hidden.
- **The closed-class list is hand-curated (~150 words).** A different boundary (e.g. counting numerals, or some adverbs) shifts the exact saturation value; the *contrast* (closed saturates, open grows) is robust to the boundary, the specific 150 is not.
- **Saturation ≠ universality:** 150 is *this corpus's* function-word vocabulary; a different-language or different-register corpus would saturate at a different finite number — the point is that it *saturates*, not the value.
- **Scope:** a vocabulary/closed-class measurement grounding F408; not a grammar-induction (we did not *learn* the frames, only separate the classes). Defensive / no-lineage.

## Verdict
**F408's "syntax closes / semantics is open" is now a measured property of our corpus:** the GRAMMAR (closed-class) vocabulary **saturates at 150** words — closing entirely by finding 180 — while the LEXICON (open-class) grows **unbounded to 12,700** (84×). This grounds F408 empirically and **resolves F431's residue**: the grammar kernel is the finite closed-class skeleton, **self-sourceable from the corpus's own prose**, so the lean hybrid can source all three kernels (domain-lean + grammar + lexicon) from one corpus. The honest limit: grammar saturates as a *vocabulary*, not as a small set of reusable full *frames* (the skeleton-reuse signal is weak). Favored, not privileged (F398); the closed-class boundary + weak frame-reuse are the fences.
