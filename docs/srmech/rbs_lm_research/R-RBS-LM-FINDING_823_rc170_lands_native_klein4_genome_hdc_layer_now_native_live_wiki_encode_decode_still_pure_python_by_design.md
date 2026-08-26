# F823 — native-dispatch re-audit on srmech rc170 (the F818 follow-up): the §53 ask LANDED — klein4 bind/bundle/similarity now dispatch to native C (~10× faster), and the live Siona server is moved to the rc170 venv so the genome's per-query klein4 HDC layer runs native. The wiki ENCODE/DECODE themselves still call zero srmech (pure regex + dict) — by design, not a gap. The F808 HDC content-addressed walk now COMPLETES and is EXACT on rc170 (it timed out on rc166) but at ~12–26 ms/token it remains too slow to replace the dict walk as the live recall engine.

**Date:** 2026-06-17 · **srmech:** 0.7.5rc170 (TestPyPI, verified clean: has_native/dispatching True, abi 3, native_version 0.7.5rc170) · **Provenance:** native-symbol enumeration + klein4 timing + the F818 HDC-walk prototype re-run on rc170; live server migrated rc166→rc170 venv · **Composes / supersedes-in-part:** F818 (the pure-Python finding this updates), §53 (the ask, now LANDED), F808 (the HDC walk), F822 (the triality unbundle — its klein4 ops are now native) · **User direction (2026-06-17):** "check now if our encoding operations on small wiki and if srmech is calling the native bound symbols vs pure python now too."

## Two questions, two answers
**(1) Do the small-wiki ENCODE/DECODE call srmech native?** No — and that is BY DESIGN, unchanged from F818. `R-RBS-LM-RAWENCODE` (encode) is regex tokenize + `understand_markup` (regex) + a `dict` k\*-scan; the live `_fullbody` (decode) is a `dict` de Bruijn walk + `max()` argmax. These are text-parse + sequence-indexing operations for which srmech has **no math primitive** (its native C surface is spectral / HDC / cyclic / graph math). So they are plain Python — neither native nor pure-Python-srmech — and that is correct, not a missed dispatch.

**(2) For the srmech ops we DO use, is it native now?** YES — rc170 is the turning point. The §53 ask (native klein4) **landed**:

| native C-bound symbol (rc170 `_native`) | covers |
|---|---|
| `has_native_klein4_bind` ✅ + `has_native_klein4_fold` ✅ | Class-M klein4 bind / bundle (the F818 gap) |
| `sha256_hex_c` / `sha256_batch_c` / `sha256_shani_c` | Class A (content hash) |
| `ndjson_lines_c` | Class C (streaming) |
| `sin_c`/`cos_c`/`atan_c`/`atan2_c`/`exp_c`/`log_c`/`rational_sqrt_c`/`_scalar_trans_c` | Class N (trig / transcendental — now native) |
| `cascade_parallel_sector_dispatch_c` | Klein-4 four-sector dispatch |
| `genome_*_c` (load/save/append/pack/window/…) | genome file I/O |

**klein4 timing, D=10000 (rc166 → rc170):** bind 8.74 → **0.86 ms**; bundle 14.4 → **1.01 ms**; similarity 4.25 → **0.84 ms** (~5–14×). So the genome's per-query klein4 layer — the context bundle (`klein4_bundle_accumulate`), similarity re-ranking, the F822 triality ops, the structure/identity cards — is now native. **The live server was moved rc166 → the rc170 venv** (deps matched: fastapi 0.137.1 / uvicorn 0.49.0); verified live: full-article recall intact, the galaxy/definition path (which exercises klein4) works, `native_status().native_version == 0.7.5rc170`, `dispatching == True`.

## The F808 HDC walk on rc170 (re-measured)
The klein4 content-addressed walk that **timed out >200 s on rc166** now completes and reconstructs **exactly**: tomato (390 tok, k=6) 4.78 s; art (1022 tok, k=9) 16.3 s; april (2686 tok, k=15) 70.4 s — i.e. ~12–26 ms/token (the per-step cost is ~k native binds + a bundle + the D-tuple hash, run 2n times for store-build + walk). That is ~10× better than rc166 but still ~10³–10⁴× the dict walk (µs/token). So:
- **Live recall stays the dict de Bruijn walk** (exact, µs/token) — the honest engine (F818/F813).
- **Native klein4 makes the F808 HDC walk a viable OFFLINE / demonstration path** (it now runs + is exact at corpus scale), and it removes the pure-Python tax from every per-query klein4 op the genome already uses.

## Verdict
rc170 closes the §53 gap: srmech IS now calling native klein4 (bind/bundle/similarity ~10×), plus native sha256 / Class-N transcendentals / genome I/O, and the live Siona server runs on rc170 so the genome's HDC layer is native. The wiki encode/decode remain pure Python — correctly, because they are text/indexing, not srmech-math. The F808 HDC walk is now feasible + exact but still not live-fast, so the dict walk stays the recall engine. F818's diagnosis stands; its blocker (§53) is resolved.
