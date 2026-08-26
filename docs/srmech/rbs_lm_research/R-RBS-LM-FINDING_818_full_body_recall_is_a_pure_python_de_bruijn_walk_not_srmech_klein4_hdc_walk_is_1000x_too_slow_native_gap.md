> **→ §53 RESOLVED by F823 (2026-06-17, rc170):** native klein4 bind/bundle/similarity landed (~10×: bind 0.86 ms, bundle 1.01 ms); the live server moved to rc170 so the genome's per-query klein4 layer is now native. The F808 HDC walk now completes + is exact but at ~12–26 ms/token still isn't the live engine — the dict walk below stays. The wiki encode/decode are still pure-Python *by design* (text/indexing, no srmech-math primitive).

# F818 — the live full-body encode/decode is PURE PYTHON, not srmech: the de Bruijn shape-walk (encode k*-scan + decode walk) calls zero srmech ops, and the srmech-native klein4 HDC content-addressed walk (the F808 "RBS-HDC" recall) is ~1000× too slow to be the live engine because srmech's Class-M klein4 bind/bundle/similarity run pure-Python (~9–14 ms/call at D=10000 → ~45 s/article). The dict de Bruijn walk and the klein4 HDC walk are the SAME context→successor stored-relationship — the dict is the fast/exact realization, klein4 is the noise-tolerant/BCI one. (User caught it: "why is python3 pegged… why aren't we using srmech to encode/decode?")

**Date:** 2026-06-17 · **srmech:** 0.7.5rc166 · **Provenance:** code audit of `R-RBS-LM-RAWENCODE` + the genome `_fullbody`; klein4 primitive timing; `srmech.native_status()` + `_native` symbol scan · **Composes:** F814/F817 (the instrument), F805 (the fiber/de Bruijn shape), F806/F807/F808 (the klein4 context-addressed bundle-record walk — the HDC realization), the §2 srmech-first reflex-override (this IS a Python-reflex miss) · **User direction (2026-06-17):** "I'm looking at top… wondering why python3 is pegged… I thought we would see a native named process if we were doing a C native encode. thanks for checking why we aren't using srmech to encode/decode!" + "should not be a doctored source as fall back."

## What the user observed + the two-part answer
**(1) The process-name premise is a red herring.** srmech's "native" is `libsrmech.so` loaded **via ctypes into the Python process** (`…/srmech/_native/libsrmech.so`) — an in-process shared library, not a separate executable. So even a fully-native srmech encode runs *inside* `python3`; you would **never** see a separate native-named process with this architecture (`srmech.bus`/`srmech-mcp` are the only separate-process surfaces, unused here). Process name cannot tell you whether srmech is doing the work.

**(2) But the real answer is yes — we are NOT using srmech to encode/decode.**
- **Encode** (`R-RBS-LM-RAWENCODE`): the only `srmech.` reference is `srmech.__version__` in a log string. Every operation — `understand_markup` (regex), tokenize (`re.findall`), the k* uniqueness scan (`dict`) — is pure Python. srmech native is loaded + dispatching (`has_native: true`) but never invoked.
- **Decode** (`_fullbody`): a pure-Python `dict` de Bruijn graph + `max()` argmax walk. Zero srmech.
- So the live "RBS-HDC instrument" was, until this finding, a token-shape **index + dict walk** — the HDC (klein4) realization (F808) lived only in research scripts and was never wired into the live path.

## Why it's not wired in (measured — the honest reason, not an oversight)
Timing the Class-M klein4 primitives at D=10000 (rc166):

| op | latency | native? |
|---|---|---|
| `klein4_bind` | 8.74 ms/call | pure-Python (only a partial `has_native_klein4_fold` C symbol exists) |
| `klein4_bundle` | 14.4 ms/call | pure-Python |
| `klein4_similarity` | 4.25 ms/call | pure-Python |

The full-body recall is a **per-token walk**: ~6 klein4 ops × ~770 steps for a 390-token article ≈ **45 s for ONE article** (a 10-article prototype timed out at 200 s before printing). The pure-Python dict walk does the same thing in **µs/step, exact, O(n)**. So the dict walk is **not a shortcut around srmech** — it is the only tractable *exact* realization of the `context→successor` stored-relationship. The klein4 HDC walk (F808, monotone-100% on-path) is the **noise-tolerant / BCI-facing** variant that trades ~1000× speed for similarity-tolerance.

Note: the genome's *other* klein4 usage (the running context bundle, similarity re-ranking, glyph encoding, the structure cards) DOES go through srmech klein4 — and is fine, because those are a **handful of ops per query**, not per-token. The walk is the one place per-token cost is fatal.

## What was done
- **Removed the doctored fallback** (user direction): the genome's `FULLBODY_FILE`/`INDEX` now point ONLY at the F817 raw no-doctoring instrument; if it is absent the full-body tier is simply off — Siona never silently serves a wikiextractor projection.
- **Honest docstring** on `_fullbody`: it is the de Bruijn dict walk (fast/exact), explicitly NOT srmech klein4; the HDC realization awaits native acceleration.
- **Filed the upstream gap (UPSTREAM_NOTES §53):** a **C-native fast path for klein4 bind/bundle/similarity** (Class-M HDC core), dispatched like the sha256/ndjson/laplacian/kuramoto surface. A ~100–1000× speedup would make the F808 HDC content-addressed walk viable as the LIVE encode/decode at interactive latency — i.e. Siona would genuinely encode/decode entire articles through srmech HDC, not a Python dict.

## Honest scope
- This does NOT make the live decode srmech-native — it makes the situation HONEST and routes the genuine blocker upstream (the framework hands the next question to the expert). The dict walk stays as the tractable exact engine until §53 lands.
- The encode's text-parse + k*-scan are sequence/text operations for which srmech has no native primitive (its C surface is spectral/HDC/cyclic/graph math); that part being Python is partly legitimate, but the HDC realization is the part that should — and now is documented to — go native once §53 ships.

## Verdict
"Why is python3 pegged and where's the native process?" — because srmech native is an in-process .so (no separate process), AND because the encode/decode call **no srmech ops at all**: they are pure-Python de Bruijn (regex + dict). The srmech-native klein4 HDC walk (F808) is ~1000× too slow to be live (pure-Python Class-M, ~9–14 ms/call), so it can't yet be the engine. The doctored fallback is removed; the honest gap (C-native klein4) is filed as UPSTREAM §53 — the concrete next question for the framework.
