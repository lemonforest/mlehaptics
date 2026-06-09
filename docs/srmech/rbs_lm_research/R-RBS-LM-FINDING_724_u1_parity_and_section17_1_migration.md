# Finding 724 — §17.1 migration: the wiki kernel now runs on the shipped `srmech.amsc.text` ops (parity-verified, output-preserving)

**Scripts:** `R-RBS-LM-U1PARITY_wiki_kernel_vs_shipped_text_ops.py` (the gate) + the migrated
`R-RBS-LM-WIKIKERNEL_…py`
**Status:** VERIFIED (srmech 0.7.5rc50, numpy-free) — full parity, output-preserving migration
**User direction:** *"run that parity check (and, if it matches, do the migration)."*

## The gate: full parity (the migration is safe)

Compared our hand-rolled `content_words` + `build_edges_topk` against the shipped `srmech.amsc.text.{tokenize,
cooccurrence_edges}` (rc50, F723) on a clean multi-article sample with aligned params (same stoplist, window,
vocab):

- **(A) Tokenization:** **4/4 articles identical** — including the `café`/`naïve` accented cases and a CJK-glued
  `day每` edge case. `tokenize(a, stoplist=DEFAULT_STOPLIST)` == `[w for w in content_words(a) if w not in
  DEFAULT_STOPLIST]`.
- **(B) Edges:** identical **edge-pair set** and identical **weights** on the shared vocab (27 edges each).

## The migration (the §17.1 ours-side item — done)

`R-RBS-LM-WIKIKERNEL` now uses the shipped ops, with our corpus-specific markup-strip kept in the adapter:

- **`stream_articles`:** `strip_wiki_markup_hardened` (F700, ours) → **`text_ops.tokenize(cleaned,
  stoplist=DEFAULT_STOPLIST)`** (was `content_words` + stoplist filter).
- **`build_edges_topk` PASS-2:** the hand-rolled windowed co-occurrence loop → **`text_ops.cooccurrence_edges(docs,
  window, vocab)`**, pre-filtering to `keep` so out-of-vocab words compact exactly as before. PASS-1 (freq rank +
  `vocab_cap` + `dropped`) and the return contract are unchanged.
- **Graceful fallback:** a `_HAS_TEXT` flag keeps the hand-rolled path for srmech < rc50, so the reference still
  runs everywhere.

**Output-preserving — verified:** the shipped path and the hand-rolled fallback produce **byte-identical**
`(vocab, idx, edges, weights, freq, dropped)` on the sample, **and** on the `vocab_cap=6` out-of-vocab-compaction
case. So the migration changes the *engine*, not the *output* (no re-encode needed, no drift).

## What this closes

- **The Counter() idiom is genuinely retired** in the wiki kernel — it now builds edges via the shipped Class-L
  precursor straight into `dense_laplacian`. The §40 boundary holds: markup-strip stays ours (corpus-specific),
  tokenize+edges are the shipped ops.
- **#855 R3 §17.1** (migrate the ours-side build onto the upstreamed surface, where parity holds) is **done** for
  the wiki kernel. (Other ours-side kernels can migrate the same way when touched.)
- The **multilingual path is now open**: because the shipped `tokenize` is Unicode-aware (F723), the kernel can
  ingest non-English corpora (R6 / #846/#847) that the old ASCII-era assumptions couldn't — the markup-strip is the
  only English-agnostic-but-wiki-specific piece left, and it's correctly isolated.

**Honest scope:** parity was demonstrated on a small aligned sample; it is *output-preserving by construction* (the
fallback path IS the old code, and the toggle-comparison shows identical output), so the migration is safe without
a full re-encode. A full-wiki re-encode would still be the separate scale run (the parse cost, unchanged). The
migration touches only the tokenize + edge-build stages (both verified); the kernel `__main__`'s later
`fiedler_clusters` demo step calls `laplacian.fiedler_vector`, which requires **numpy** (the scientific tier) and so
does not run in the numpy-free venv — a **pre-existing** dependency, unrelated to U1/this migration.

**Composes:** F723 (rc50 ops that meet the bar) · §40 (the spec) · F722 (the rc49 fail that gated this) · F698/F700/
F714 (the tokenization lessons) · F708 (no-cap) · F690 (one-article-one-window-reset) · #855 R3 §17.1. srmech
0.7.5rc50. Held open (F394).
