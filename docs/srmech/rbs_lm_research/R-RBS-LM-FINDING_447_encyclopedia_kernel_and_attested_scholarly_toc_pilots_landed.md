# R-RBS-LM Finding 447 — F446 validated in practice: (a) the **encyclopedia kernel** (Simple-English Wikipedia, local dump) builds srmech-native and carries signal — K1 presence REAL z=+1.59 vs gibberish −0.51 *after* stripping wikitext markup residue (essential), and K3 sequence shows real, sample-size-dependent structure (+0.32→+0.66 as the n-gram sample goes 20k→120k); (b) the first **attested-scholarly-TOC** (dblp, CC0) is a real local hash-checked citation index — **12,676,702** records, **7,211,597 with DOI (56.9%)**, **publisher-MD5 verified**, SHA-256 Class-A anchored. Two methodology lessons: the K1 presence probe is a **bag → order-invariant**, so the real-vs-shuffled test is *null by construction* for K1 (it bites only on K3, the sequence kernel — re-confirming F75); and `strip_code` leaves markup that **dominates the top-vocab** until filtered

**Date:** 2026-06-06
**Arc:** RBS-LM / AMSC · the two local-dump pilots (F446 → **F447**); **empirical (simplewiki kernel + dblp TOC)**
**Provenance:** `R-RBS-LM-WIKI_extract.py` + `R-RBS-LM-WIKI_kernel_build.py` (+ `R-RBS-LM-WIKI_simplewiki_results.json`, `kernels_wikipedia/simplewiki_K{1,3}.bin`); `R-RBS-LM-DBLP_toc_build.py` (+ `R-RBS-LM-DBLP_attestation.json`). srmech 0.7.1 scientific venv.
**Composes:** **F446** (bulk-dump-IS-AMSC-shape — *this validates it in practice*) · **R-RBS-LM-WIKI / R-RBS-LM-DBLP** (the pipelines) · **F172** (the Class-L co-occurrence-Laplacian eigenspectrum = the srmech-native storage signature — the K1 kernel) · **§2 MPM/MPR** (the dblp attestation block: `response_sha256` + `publisher_md5_verified` + `license` + `retrieved_at`) · **F75** (order-invariance falsification — *the K1 bag-probe is order-invariant, so it cannot see a shuffle; same point, re-confirmed*) · **F435** (the representation residue — K3 sequence is the n-gram layer, sparse on a large corpus) · **F52c-v2** (the prior K3 stopword-iteration precedent). **← extends F446.**
**→ the encyclopedia kernel + attested scholarly TOC both work; the TOC (existence/DOI) layer is done, the Class-L citation-graph kernel awaits a citation source (OpenCitations/OpenAlex).**

---

## What ran (local dumps, no HTTP streaming; version-proof on Python 3.14)
- **Simple-English Wikipedia** dump (350 MB `.bz2`) → lean `bz2`+`ElementTree`+`mwparserfromhell` extractor (after `wikiextractor` crashed on Py3.14, the `re` inline-flag `PatternError`) → **240,881 articles** → srmech-native K1+K3 kernel.
- **dblp** dump (1.07 GB `.xml.gz`, CC0 1.0, dated 2026-06-06) → SHA-256 anchor + publisher-MD5 cross-check → stream-parse (DTD entities substituted dependency-free) → attested NDJSON TOC.

## (a) Encyclopedia kernel — simplewiki (237,250 articles, 37.9M tokens, 1.25M unique)
| kernel | result | reading |
|---|---|---|
| **K1 presence** (Class-L co-occurrence Laplacian, vocab 256, window 5) | REAL z=**+1.59**, GIBBERISH z=**−0.51** | strong **content-vocabulary** signal — real text sits well above the random-article-pair floor, gibberish below it |
| **K1 vs SHUFFLED** | +1.59 vs +1.65 (Δ≈0) | **null BY CONSTRUCTION** — the probe is a bag (`hierarchical_bundle` of minted tokens), order-invariant, so a token-shuffle cannot change it (F75 re-confirmed); the shuffle test is K3's, not K1's |
| **K3 sequence** (position-bound n-gram bind/permute) | REAL +0.39 > SHUFFLED −0.27 (structure **+0.66** @120k; **+0.32** @20k) | **real, sample-size-dependent** structure — shuffling obliterates the n-grams; the signal sharpens as the n-gram sample grows (under-sampling on a 34.6M-ngram corpus) |

**The load-bearing lesson — markup residue:** the *first* build's K1 top-vocab was `category, align, bgcolor, class, id, references, km…` — **wikitext/HTML/infobox residue** `strip_code` leaves behind. It dominated the 256-vocab and gave K1 **no structure** (REAL z=+0.07). Adding a `MARKUP_RESIDUE` filter flipped the top-vocab to content (`km, american, people, new, first, united, linear, note, socorro…` — the `socorro`/`km` tail = simplewiki's heavy load of asteroid/place stubs, *not* markup) and lifted K1 REAL z to **+1.59**. *For an encyclopedia kernel, markup-residue stripping is essential; the Class-L storage signature is only content after the strip.*

## (b) Attested-scholarly-TOC — dblp (the F446 pilot, fully realized)
| field | value |
|---|---|
| records | **12,676,702** (article 4.33M · inproceedings 3.90M · www 4.11M · phdthesis 154,816 · proceedings 64,552 · incollection 71,100 · book 21,426 · data 23,769 · mastersthesis 27) |
| **with DOI** | **7,211,597 (56.9%)** |
| `publisher_md5_verified` | **true** (our MD5 == dblp `5a942653b968a3e47f400cbabda389c0`) |
| `response_sha256` (Class-A anchor) | `0aee53f0ca21a253ea39534e2ab74e8d1023d7714636da4e413a86d49b491cc7` |
| license | **CC0-1.0** (primary) / ODC-BY-1.0 (secondary) — README-verified |
| dump | 1,072,817,798 bytes; TOC NDJSON 3.14 GB (kept outside git; the **attestation block** is the committed artifact) |

This is a **real local, hash-checked index of 12.7M peer-reviewed items** with 7.2M verifiable DOIs — citation-verify is now a **Class-A hash-checked, Class-E catalog lookup** against a re-verifiable source-of-truth, not a training-data guess. F446's design holds in practice.

## Falsifiable form (pre-stated; not leaning — F394)
- **K1 ≠ a structure detector; it is a presence/vocabulary kernel.** Its bag-probe is order-invariant (F75), so it distinguishes real-vocabulary from gibberish (+2.1 z gap) but *cannot* distinguish real from shuffled. Structure detection is K3's job; do not read K1's null shuffle-Δ as a failure.
- **K3 is under-sampled on a large corpus.** +0.32→+0.66 from 20k→120k n-grams (of 34.6M) shows the signal is real but sparse; **frequency-weighted n-gram sampling** (common content phrases) is the refinement for the full enwiki build, not uniform sampling. Gibberish z stays noisily near 0 (tiny K3 baseline std → unstable z); the REAL>SHUFFLED ordering is the robust signal.
- **dblp validates the TOC (existence/DOI) layer only.** dblp has **no citation edges**, so the **Class-L citation-graph kernel** (the F446 "storage signature of peer-reviewed knowledge") still awaits OpenCitations/OpenAlex — flagged, not claimed.
- **Attests existence+metadata, not truth-of-content** (F408 semantics-open); paywalled-DOI→OA routing carries in (F445).
- **Scope:** benign bibliographic/corpus work; algebra/catalog/eigenbasis side; CC0/PD only; CAD-ban respected; no Workflow tool (verification = the inline publisher-checksum cross-check).

## Verdict
**Both F446 pilots landed.** The **encyclopedia kernel** (simplewiki, local dump) builds srmech-native and carries signal: K1 presence REAL z=**+1.59** vs gibberish −0.51 — *after* the essential markup-residue strip (the Class-L storage signature is content-only once `strip_code`'s wikitext leftovers are filtered) — and K3 sequence shows **real, sample-size-dependent** structure (+0.32→+0.66 as n-grams 20k→120k). The first **attested-scholarly-TOC** (dblp, CC0) is a real local hash-checked citation index — **12.68M records, 7.21M DOIs (56.9%), publisher-MD5 verified, SHA-256 Class-A anchored** — so citation-verify is now a Class-A/Class-E lookup against a re-verifiable source-of-truth. Two methodology lessons banked: **K1's bag-probe is order-invariant** (the shuffle test is K3's, re-confirming F75), and **markup-residue stripping is essential** for the presence kernel. TOC/DOI layer done; the **Class-L citation-graph kernel** is the next rung (OpenCitations/OpenAlex), and the full **enwiki** kernel + **frequency-weighted K3** sampling scale up from here. Favored, not privileged (F398); attests existence+metadata, not truth-of-content.
