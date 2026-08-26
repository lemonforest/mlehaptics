# F747 — 14 (the_one loop) vs 16 (sedenion register) on the wiki kernel; the §31 register holds the storyteller's tomes; the 256 cap was a srmech bound now lifted

**Date:** 2026-06-14 · **srmech:** 0.7.5rc149 · **Composes:** F746 (the persisted wiki tome bookshelf), F540 (14 vs 16: local vs far chords), F529/F533 (sedenion tomes; helix of registers), §31 SedenionRegister (F465/F468), F584/F542 (kernel SSoT, no re-encode), F527 (the bundle capacity wall), F640 (the top-256 honest scale) · **User direction (2026-06-14):** test both 14 and 16 structures; test the sedenion register with the storyteller now the genome works; clarify whether the full-vocab encode = Siona "knowing the words" or needs a dictionary; and why the top-256 cap (thought uncapped) didn't carry over. · **Provenance:** `R-RBS-LM-TOMECMP…py` (runs on rc149)

## (c1) 14-tome (the_one loop) vs 16-tome (sedenion) — near-tied on this kernel
Both route off the SAME reused kernel (V recomputed; no re-encode). On the enwiki **top-256** vocab:
| structure | tomes filled | local-recall (own+adj) | far-ring chords |
|---|---|---|---|
| **NT=14** (the_one loop) | 11/14 | **80%** | 12% |
| **NT=16** (sedenion) | 12/16 | 78% | **13%** |

F540's sharp "14-local vs 16-far" split is **only marginally** reproduced here (16 surfaces slightly more far chords, 14 slightly more local) — consistent with F540's own "low-statistics, held open, not a law" caveat. On this census-dominated top-256 vocab the two are **near-equivalent**; a real preference needs a richer kernel (→ the uncap below).

## (c2) the §31 SEDENION REGISTER holds the storyteller's tomes (first test — PASSES)
First time the SedenionRegister is exercised with the storyteller's actual data (the wiki tomes), now that the genome works:
- **write/read round-trips exactly:** all **12 written tomes** read back exactly at D=8192 (3/3, 7/7, 10/10, 12/12) — **no capacity wall at this scale**.
- **the ≤7 octonion COUPLER is exactly reversible:** couple 7 tome-summaries → one octonion → uncouple, **max err ~3e-14** (the e1..e7+anchor working block, F529).
- **CD-navigate addresses without crosstalk:** `navigate(j)` returns the addressed register (the §31 homomorphism).
- **CAVEAT learned:** reading an **unwritten** slot returns a **spurious** nearest-match (the bundle always cleans to *something*) — you must track which slots you wrote, or use the carry/EC block (e8..e15). (My first run's "False" was exactly this: I counted spurious reads on empty slots.)
- The **helix of registers** (F533) is for the *recursive* tome-of-tomes / when slot-capacity is eventually exceeded — **not needed at 12 tomes**.

## (audit) the 256 cap: a srmech node bound, now LIFTED; the kernel file is stale
The user recalled uncapping the top-256 — confirmed, and the honest status: **256 was srmech's `MAX_NATIVE_NODES` Class-L bound**, and it is **gone** (a 300-node Laplacian eigendecomposes fine now). Nothing **re-capped** in srmech. What didn't carry over is the **kernel file**: `enwiki_kernel_256.json` is the *stale* top-256 encode from when the bound was live — the bigger encode was simply never re-run. (Dense still has a real ceiling: n≈thousands is fine; the full **1.77M** vocab is a 3×10¹² dense Laplacian = impossible → the F690 **bucketed/sparse** path. So "uncapped" = thousands dense, full-vocab = bucketed.)

## (clarification) does the full-vocab encode = Siona "knowing the words"? — partly
- The **wiki kernel** registers each word as **vocab + its co-occurrence relationships** (Class-L) — Siona knows the word *exists* and *what it relates to* (structural/relational knowing).
- It does **not** carry **definitions** (what a word *means*). That is a **dictionary** (the `dict-en` chromosome). They are complementary layers: the wiki kernel *relates*, the dictionary *defines*, the REST abstracts (F745) *explain at article level*.
- So a full-vocab wiki encode makes Siona know the words *relationally*; a **full-vocabulary dictionary is a separate kernel** (open/CC source = Wiktionary) if you want her to *define* arbitrary words.

## Order (a/b/c) and the fork
**(c) done.** Meaningful order recommendation: because the current 256 kernel is stale + census-skewed, an **(a-lite)** re-encode at a higher (now-uncapped) vocab — top-few-thousand, dense-feasible — makes **(b)** (wiring the bookshelf into Siona) actually worthwhile, before the full F690 bucketed big-wiki. So: **c → a-lite (richer kernel) → b (wire into Siona) → a-full (bucketed) + the dictionary kernel.**

## Honest scope
Top-256 only (the comparison inherits the census skew); the 14-vs-16 verdict is *near-tied here* and should be revisited on a richer kernel. The register test is at 12 tomes / D=8192 (clean); larger scales need the helix-of-registers. srmech-native; no `abs()` (Class-K); no CAD; no re-encode (V recomputed from stored edges).

## Verdict
**(c) is done and informative.** 14 and 16 are near-tied on this top-256 kernel (F540's split needs a richer kernel to show). The **§31 sedenion register works as the storyteller's tome container** — 12/12 exact write/read, an exact ≤7 octonion coupler, CD-navigate addressing, with the unwritten-slot-spurious-read caveat noted. The 256 cap was a srmech bound now lifted (the file is just stale); the full-vocab encode gives Siona *relational* word-knowledge, with a dictionary the separate *definitional* layer. Recommended next: a-lite (richer kernel) → b (wire into Siona).
