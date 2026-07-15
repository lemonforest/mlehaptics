# F1235 — corpus_store switched to DEMAND-LOAD (gene_express / EPH): the server opens in ~1 s instead of ~21 min, and each query gene-expresses only its token's neighbourhood. The genome is the DNA (store); reads/ is the expression index.

**User (2026-07-15):** *"what does corpus loading in the background mean? it's re-encoding smallwiki?"* → No — it was READING (inflating) the already-built genome. *"switch corpus_store to demand-load. I thought this was the EPH pattern — epigenetics — gene_express."* Correct, and done.

## The reframe (the user's, confirmed)
The genome is the **DNA (the store** — the directed Laplacian, F1216/F1221). Reading it is **gene expression** (EPH / gene_express, F1095/F1112): a query should EXPRESS only the queried token's neighbourhood, not inflate all 39M edges into RAM at startup. The old `corpus_store` full-materialized everything (`kernel_to_graph` of 39M edges + a 78M-entry dict) — ~21 min **per server start**, ~GB RAM. That is not expression; that is transcribing the whole genome every boot.

## The fix (`corpus_store` demand-load)
- **reads/ = the expression index**, built ONCE under the genome dir: `adj.bin` (per-token neighbour records, sorted by metric, **mmap'd**) + `adj.idx` (token → byte-offset, count) + `vocab.txt`. Recomputable from the genome (or the source); the store stays the genome. Top-K is a query read, never a storage cut (F708/F748).
- **`prepare()` opens INSTANTLY** when reads/ exists (mmap, no decode); **`read(token)` pages in only that token's bytes**. Falls back to full in-RAM for small corpora (same `read()` API). RAM-path == mmap-path read parity verified.

## Measured (real simplewiki, 831,139 vocab / 39M edges)
| | before (full-materialize) | after (demand-load) |
|---|---|---|
| build reads/ (one-time, from source) | — | **124 s** (2 min; no 39M-edge re-decode) |
| **server open** | **~21 min** every start | **1.1 s** (mmap) |
| per-query read | (already in RAM) | **~0.1 ms** (mmap page-in) |
| RAM at open | ~several GB (all edges + index) | ~idx+vocab only; slices page in on demand |
| reads/ on disk | — | 955 MB (adj.bin 937 + adj.idx 10 + vocab.txt 8) |

Live over HTTP: `what is water` → `water — seen with: ← area, → sq, ← mi, ← land, ← km, → polo` (identical to the full-load demo), served in ms, server up in ~1 s. The `reads/` step is now in Siona's `build_wiki_corpus_genome` recipe (step 5), so any future wiki gets the fast-serving expression layer too.

## Honest note
The one-time reads/ build still decodes the corpus once (here ~2 min from the source, since the genome round-trips the source byte-exact). But it's ONE-TIME + cached; every server start after is ~1 s. True per-token expression from the packed genome (no reads/ sidecar) would need a token-sharded genome (a chromosome per token-block) — a bigger re-encode, deferred; the mmap'd reads/ index is the pragmatic gene_express that gives instant-open now.

Composes **F1233** (the read-path wiring this accelerates), **F1234** (the HTTP server, now instant-open), **F1216/F1221** (the genome IS the store; reads/ is a derived read accelerator), **F1095/F1112** (gene_express / demand-load — the pattern the user named), **F1208** (the byte-offset-seek read, here mmap), #231/PKG-3, [[feedback_siona_working_memory_never_compacted]] (mmap pages, no truncation), [[feedback_store_sparse_complete_never_top_k_truncation_at_storage]] (the genome stays uncapped; reads/ is a read).
