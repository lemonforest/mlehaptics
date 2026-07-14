# F1220 — Why Siona loads NDJSON, not a genome: a DELIBERATE rc1 stopgap (F1013), because the native-genome path is blocked at CORPUS SCALE on two upstream srmech bugs (UPSTREAM §55: ~4× lane bloat + O(n²) pack) — re-measured STILL LIVE at rc238

**User (2026-07-14):** *"find out why Siona is using NDJSON as an instrument instead of srmech tooling, like a genome."* Traced to the code + the decision record + a live re-measurement. **It is deliberate and upstream-gated, not an oversight.**

## The answer (grounded)
1. **The native genome is already built and byte-exact.** `siona.genome_store` packs Siona's Klein-4 instrument into a native srmech genome (`_G.genome`/`genome_save`/`genome_load`/`kernel_unpack`, PKG-3/#249); `siona/bridge.py` states the single-file genome "was prototyped and **recalls exactly**." Genome-native is not missing.
2. **rc1 ships the loose NDJSON store because the genome format is blocked at CORPUS SCALE on two upstream srmech bugs** (bridge.py, UPSTREAM_NOTES §55 / F832/F833):
   - **~4× lane bloat** — the genome stores each **2-bit Klein-4 sector as a full byte**. **Re-measured at rc238** (this finding): a 4096-symbol klein4 kernel packs to **0.81 bytes/symbol** (ideal 2-bit-packed = 0.25; 4×-bloat = 1.0) — the bloat is **STILL LIVE**, unfixed since the rc97-era filing.
   - **`genome_pack` is O(n²)** in chromosome count — quadratic; infeasible for a many-chromosome corpus (one chromosome per article/tome).
   bridge.py: *"Native-genome bodies are revisited once those land; rc1 ships on the loose store."*
3. **The NDJSON also fills a role the genome doesn't (yet):** it is the **byte-offset-seekable, attested RAW-TEXT source** — `_k_load` opens `*_instrument.ndjson` + `*_index.json`; `acquire`/`study` seek to a title's byte offset and quote the source text with per-record **sha256 (Class-A provenance)**. Disk-resident streaming: a huge corpus stays on disk, seek only the needed article (the F1208 disk↔RAM read). The genome carries the *relational* structure — a different payload.

## What it reconciles (a correction to my own F1215 stance)
My F1215 "persist genome-native, not loose JSON" ([[feedback_persist_genome_native_not_loose_json]]) is right for **bounded objects** — proved this session: the findings genome + directed word kernel `kernel_pack`+round-trip byte-exact. But for **corpus scale**, genome-native is *genuinely blocked* on §55 (the 4× bloat + O(n²) pack), which is **why the loose NDJSON store persists** — a real srmech-upstream gate, not sloppiness. Honest rule: **genome-native for bounded kernels now; the loose-store stopgap for the corpus until §55 lands upstream** (re-confirmed unfixed at rc238). This also explains the F1219 load-format mismatch (her `load` expects the title-indexed NDJSON instrument, not a genome or a bare index).

## Status / next
- **Re-verify + re-file §55 at rc238** (the two blockers still live: measured 4× lane bloat 0.81 B/sym; O(n²) pack unaddressed). This is the *actual* unblocker for #231/PKG-3 (genome-native corpus store) — an **upstream** ask, not a Siona-side fix.
- Interim: keep the loose NDJSON store for the corpus; use genome-native only where bounded (bounded per-topic kernels, the responsion/findings store).

Composes **F1013** (PKG-1 mechanism-not-knowledge decision; the loose-store-per-bridge.py note), **F1219** (the load-format mismatch — now explained: NDJSON-by-design), **F1215**/[[feedback_persist_genome_native_not_loose_json]] (refined: bounded=genome, corpus=blocked-on-§55), **F832/F833** (the genome prototype + the fiber-not-spatial-HV store), **F1208** (disk↔RAM streaming = the byte-offset seek), #231/PKG-3 (the migration gated on §55).
