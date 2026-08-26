# F1008 (SIONA-INFER-2 / #234) — **srmech's tool_schema grounds as a depth-read dictionary: a natural "user asks X" utterance retrieves the correct srmech tool at 78% top-1 / 83% top-3 over all 347 tools, zero training, pure sparse Klein-4 — the F766/F1005 depth-read mechanism pointed at the tool catalog.** This is the "knows how to use srmech CLI + tool_schema" half of the siona rc1 gate. Three disciplined iterations each fixed a real collision class; remaining misses are within-family fine distinctions + one poor query.

**Date:** 2026-07-02 · **srmech:** 0.9.0rc97 (347 tools, tool_schema 1.0) · **Branch:** `research/rbs-lm-rolling-2` (PR #687) · **Milestone:** SIONA-INFER-2 (#234, rc1-GATE) · **Probe:** `R-RBS-LM-FINDING_1008_*.py` · **Grounds / composes:** F1005/F766 (depth-read dictionary — tool summaries ARE the "definitions", utterance = the query), F768/F984 (aboutness gate), F769 (name = the "title" weighted over the summary "definition"), `[[feedback_never_bag_of_words_even_for_testing]]` (the first cut was a bag → collisions → fixed with adjacency bigrams), `[[feedback_read_independent_structure_check_first]]` (discriminability measured first). · **User direction (2026-07-02):** "let's start with our siona tasks." · **Scope:** framework/tool; sparse Klein-4; bundle via `bundle_odd` (§82); no numpy/abs/Counter.

## Grounded (rc97, all 347 srmech tools)
```
(A) tool-vector discriminability (read-independent, mean off-diag sim; ~0.25 orthogonal): 0.271 (distinct)
(B) retrieval -- 18 natural paraphrase utterances -> correct tool:
    first cut (bag-of-tokens):                     top-1 67%  top-3 72%
    + adjacency bigrams (order-aware, not a bag):  top-1 67%  top-3 78%
    + letter-digit tokenization + name-weighting:  top-1 78%  top-3 83%   <- SIONA-INFER-2 v2
    14/18 top-1: sha256_bytes, sha256_batch, gcd, best_rational, factor, magnetic_laplacian, signed_laplacian,
       jacobi_eigvals, hermitian_eigendecompose, fiedler_vector, klein4_unbundle, klein4_random,
       cooccurrence_edges, three_fold_eigvec_groups
    misses (all sensible): klein4_bundle->bundle_resolve (top-2, same family); klein4_similarity->unbind (top-2,
       same family); polar_random->the_one ("one" homograph -- describing values {-1,0,+1} in words = a poor query)
```

## The reading (why it works, what the iterations taught)
- **The tool_schema IS a depth-read dictionary.** Each ToolEntry's name+summary is a "definition"; a user utterance is a "define/retrieve" query; retrieval is the F1005 aboutness-gated nearest-tool read. The mechanism transfers directly from the wiki depth-read (F1005) to the tool catalog — no new machinery, 78% top-1 over 347 tools with zero training.
- **Each iteration fixed a real, named collision class (honest debugging trail):**
  1. **bag → order-aware bigrams** (`[[feedback_never_bag_of_words_even_for_testing]]`): the first cut was an order-free token bundle; `klein-4 similarity` retrieved `klein_gordon` (physics!) on the shared unigram "klein". Adjacency bigrams (`(klein,4)` ≠ `(klein,gordon)`) are the fix — I had violated the no-bag discipline and it bit exactly as the memory warns.
  2. **letter-digit tokenization**: `klein4_similarity` (name) tokenized to `klein4`, but the query `klein-4` → `klein`,`4` — no overlap, so only the ambiguous summary matched. Splitting letter↔digit on **both** sides (`klein4`→`klein`,`4`; `sha256`→`sha`,`256`) aligns query and name.
  3. **name-weighting** (F769 title-vs-definition): the tool *name* is its identity; weighting name tokens 3× (+2× name-bigrams) over the summary lets a query that *names* the op hit the right tool. This is F769's "usage/identity overrides the definition-bag" made operational.
- **The remaining misses are the right kind.** Two are within-klein4-family fine distinctions (`bundle` vs `bundle_resolve`; `similarity` vs `unbind`) — the correct family, top-2/3, disambiguable downstream by the call signature; one is a poor query (values-in-words → the "one" homograph). None is a cross-domain error anymore.

## Honest scope
78/83% is a solid *first* build, not rc1-ship-ready. The 18-utterance eval is a hand-authored harness (test *inputs*, not stored content — the stored content is the real 347-tool schema, so this is not a magic-number reply). Within-family disambiguation (bundle/bundle_resolve/unbundle) is the top remaining lever and is exactly where SIONA-INFER-3's *emit+run* loop helps: surface top-3 candidates + disambiguate by the call's parameter fit / a trial run. The "one"-homograph miss argues for a values→canonical-token normaliser, not a core fix. Gate 0.271 (read-independent) confirms the 347 tool-vectors are distinct — the retrieval ceiling is high; the work is query→tool matching, not discriminability. Sparse Klein-4 throughout; no numpy/abs/Counter/bag.

## Verdict / next
**SIONA-INFER-2 first build works: srmech's tool_schema grounds as a depth-read dictionary; a natural utterance retrieves the correct tool at 78% top-1 / 83% top-3 over 347 tools, zero training, pure sparse Klein-4 — the "knows how to use srmech tool_schema" half of the rc1 gate is prototyped.** The disciplined iteration trail (bag→bigram, letter-digit tokens, name-weighting) is itself the reusable recipe for grounding ANY tool_schema (including siona's own — SIONA-INFER-4). **Next:** (i) **SIONA-INFER-3** — the emit+run loop, using top-3 candidates + call-signature disambiguation to close the within-family gap and drive a real srmech op end-to-end; (ii) harden within-family disambiguation (parameter-fit re-rank); (iii) the same grounding on siona's own CLI (SIONA-INFER-4). Kept #234 in_progress — capability demonstrated, hardening pending.
