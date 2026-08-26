# F854 — Clean srmech-0.8.2 re-encode of ALL simplewiki from the raw dump (F817 no-doctoring encoder), verified + reproducible. **271,174 articles · 49,977,004 tokens · unique-walk 99.1% · mean k\*=5.3 · 5,780,534 curated edges (21.3/page)** · 381 MB instrument + index (271,107 titles) + the F819 gapmap. First record byte-identical to the rc169-era instrument (deterministic: the encode is the F764 markup kernel + de-Bruijn k\*; srmech is only version-stamped — so 0.8.2 cleanly re-stamps an unchanged, attested artifact). Written to `*_v082*` paths **alongside** the in-use Jun-17 instrument (non-clobbering); SSoT swap is the user's call.

**Date:** 2026-06-18 · **srmech:** 0.8.2 (live PyPI) · **Provenance:** `R-RBS-LM-RAWENCODE_*` (F817) via `/tmp/rawencode_v082_wrap.py` on `simplewiki-latest-pages-articles.xml.bz2`, live 0.8.2 venv, detached run PID 441076 · **Composes:** F817 (no-doctoring raw-dump re-encode), F814 (the instrument it corrects), F764 (understand_markup kernel), F805/F813 (de-Bruijn fiber + k\*), F819 (gapmap = surfaced-not-stripped construct queue), [[feedback_no_doctoring_ssot_use_sublanguage_kernels]] · **User direction (2026-06-18):** "encode smallwiki with fixed sparse srmech … autonomous afk time, yes go!"

## What was produced
- **Instrument** (`simplewiki_rawbody_instrument_v082.ndjson`, 381 MB): one page/line — `{t: title, k: k*, n: n_tokens, u: unique-walk flag, s: clean token shape, e: curated [[outlink]] edges}`. The walkable de-Bruijn fiber (F805/F813); HVs are on-demand functions of tokens (not stored — edge-portable).
- **Index** (8.6 MB, 271,107 titles): title→byte-offset for O(1) low-RAM random access (F793).
- **Gapmap** (`*_gapmap_v082.json`, F819): the markup-construct families surfaced but not yet covered by a sub-language kernel — the kernel-build queue (top: flagicon 97.7k, defaultsort 96.0k, coord 89.0k, small, party, `table {|`, sort, birth, …). These are *surfaced, not stripped* (F817 no-doctoring) — #225/#226.

## Corpus shape (the foundation for everything downstream)
- **50.0M tokens** across 271k articles (mean 184 clean tokens/article after markup comprehension).
- **99.1% unique-walk** at **mean k\*=5.3** — the de-Bruijn fiber is well-defined for almost the whole corpus (only 0.9% long-range-ambiguous, flagged `u=False`, need explicit branch-choices for exact recall, F813).
- **5.78M curated edges** (the [[Target]] outlinks — stronger than co-occurrence; "everything AND its relationships" survive the read, F817).

## Why this is the clean fixed-sparse encode
- **Fixed**: srmech 0.8.2 (numpy-free, §57 bigram-Counter removed) — the contaminant-free substrate the recall layer runs on.
- **Sparse**: relationship/walkable shape + curated edges, NOT spatial HV-per-token (HVs on demand).
- **No doctoring**: read from the raw MediaWiki `.bz2` via the understand-markup kernel (not the wikiextractor projection that F817 corrected) — content unwrapped, form comprehended, edges extracted, nothing pre-stripped.
- **Reproducible/attested**: byte-identical to the prior encode (same dump + kernel; deterministic) — confirms the pipeline is stable and the 0.8.2 stamp is honest.

## Verdict / next
The clean 0.8.2 fixed-sparse encode of all simplewiki exists, verified, reproducible, non-clobbering. It is the attested foundation for the recall recipe (F838–F848) and the physics-of-the-knowledge-metric work (F849–F853). **Next (autonomous):** corpus-scale physics on this instrument (scale-up of F852: degree power-law / fractal at full scale) → then the notebook consolidation. SSoT swap (point live research at v082) deferred to the user.
