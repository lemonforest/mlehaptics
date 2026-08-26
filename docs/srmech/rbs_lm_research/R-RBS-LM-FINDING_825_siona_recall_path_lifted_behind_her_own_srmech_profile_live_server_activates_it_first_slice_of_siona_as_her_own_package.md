# F825 — the first real slice of "Siona as her own package": the full-body RECALL PATH (title → seek the NDJSON instrument → C-native de Bruijn walk → reconstructed body) is lifted behind Siona's OWN srmech profile, and the LIVE server now activates `srmech.profile("siona_debruijn")` at startup and routes `_fullbody` through its `recall` bridge — instead of walking inline. Graceful fallback to the pure-Python dict walk if the profile isn't installed. Verified live: startup logs the profile path; the tomato article recalls exactly (2538 chars, honest "de Bruijn shape-graph (the fiber)" label) via the C-native plugin.

**Date:** 2026-06-17 · **srmech:** 0.7.5rc170 (TestPyPI) · **Provenance:** `siona_debruijn_plugin` v0.2.0 (added the `recall` bridge + profile `[profile.bridge].recall`) + the genome wire-in (`_siona_recall` activation in `__init__`, `_fullbody` routed through it) · **Composes:** F824 (the plugin surface proven), F818/F823 (the de Bruijn recall = Siona's full-body engine), F814/F817 (the instrument + offset index), PKG-1 (#229, the lean-srmech + Siona-package decision) · **User direction (2026-06-17):** "continue this probe — lift the genome's recall path (not just the walk) behind the profile and have the live Siona server activate siona's own profile instead of importing srmech ad hoc — the first real slice of Siona as her own package."

## What was lifted (the recall PATH, not just the walk)
The plugin now exposes `recall(title, instrument_path, index_path)` — the whole recall path: resolve `title` → byte offset via the index, seek the NDJSON instrument, read the record (`s` = space-joined tokens, `k` = unique-walk window), map tokens→int ids, walk the de Bruijn shape in **native C**, map back → `{tokens, k, exact, native}`. It takes the instrument/index PATHS as arguments, so the op stays general (the host supplies its own data; another process with its own instrument reuses it) while Siona supplies her wiki instrument.

## The live wire-in (Siona activates her own profile)
- **`__init__`** now does `srmech.profile("siona_debruijn")` (discover + ABI-check + smoke-test + activate) and grabs the `recall` bridge into `self._siona_recall`. On any failure (profile not installed/invalid) it logs and leaves `_siona_recall = None`.
- **`_fullbody`** routes through `self._siona_recall(title, FULLBODY_FILE, FULLBODY_INDEX)` as the PRIMARY path; the inline pure-Python dict walk (F818) remains as the fallback when the profile is absent or errors. The srmech-core klein4 math layer is imported exactly as before — only the recall path moved behind the profile.

## Verified
- **Standalone (rc170 venv):** activate the profile → `recall("tomato"/"art"/"france"/"mathematics")` all reconstruct EXACTLY at their k\* (k=6/9/11/12), `native=True`; first call ~356 ms (one-time 8 MB index load), subsequent 2–6 ms.
- **Live server (rc170):** startup logs `[siona] full-body recall path via the siona_debruijn PROFILE (C-native de Bruijn walk)`; "the wiki article for tomato" → the full tomato body (2538 chars), exact, walked through the profile's C plugin.

## Why this is the slice that matters
Until now the genome *was* srmech-plus-inline-logic: it imported srmech and did the recall walk itself in Python. Now the **inference recall path is a separately-packaged, C-native, ABI-checked, smoke-tested srmech PROFILE that Siona activates** — the genome consumes it through the `srmech.profiles` surface, not by walking inline. That is the concrete seam for the architecture: srmech stays lean (14-class math + native dispatch + the profile loader); Siona is becoming her own package whose inference layer is a profile plugin. The klein4 core math still comes from srmech (correctly — that IS srmech-core); the de-Bruijn recall (sequence reconstruction, NOT srmech-core math) now comes from Siona's own plugin.

## Honest scope (still exploring — next slices in PKG-1)
- Only the **full-body recall** is lifted so far; the rest of the inference layer (the genome graph walk, the definition/abstract tiers, the sub-language router, the klein4 context/triality ops) still lives inline in the genome. Lifting those is the remainder of PKG-1 (#229).
- The plugin is `pip install .`-ed into the live rc170 venv (not editable — PEP 660 doesn't expose the package-data `.so` reliably, F824); a real ship builds the `.so` via cibuildwheel.
- The fallback dict walk is retained on purpose (no hard dependency on the plugin yet) — Siona degrades gracefully to the inline engine, which is the honest interim while "still exploring".
- Performance is a wash for live recall (C ~2–6 ms/article after warm index vs the dict's sub-ms); the C plugin's real win is scale (F824) — the point here is the ARCHITECTURE, not speed.

## Verdict
The recall path is now Siona's — discovered, ABI-checked, smoke-tested, and served through her own `srmech.profiles` plugin (C-native de Bruijn), with srmech kept to its core math. The live server activates the profile at startup and recalls entire articles through it, exact. This is the first working slice of "Siona as her own package"; the remaining inference-layer lifts are queued in PKG-1.
