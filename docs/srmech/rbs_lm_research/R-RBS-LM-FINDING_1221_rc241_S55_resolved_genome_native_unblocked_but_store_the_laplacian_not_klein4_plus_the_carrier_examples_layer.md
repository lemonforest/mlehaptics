**→ extended by F1246** (the consolidated coupled-turns encode contract — metric+charge+fiber, not just Laplacian — lodged srmech-facing at UPSTREAM §98).

# F1221 — rc241: §55 is RESOLVED (4× lane bloat + O(n²) pack both fixed) → genome-native is UNBLOCKED. But store the LAPLACIAN on disk, NOT Klein-4 (it flattens far more). Plus the new `_carrier_examples` construction layer

**User (2026-07-14):** *"pull latest testpypi srmech — we thought the 4× bloat was fixed several rcN ago; introspect our new examples layer"* + mid-turn *"from earlier research we probably don't want Klein-4 on disk, because it flattens much more than Laplacian."* Pulled rc238→**rc241**; re-measured; introspected. All three land.

## §55 is RESOLVED at rc241 — genome-native is UNBLOCKED (corrects F1220)
- **4× lane bloat: FIXED.** Re-measured at N=200,000 symbols: `turns.bin` = **0.265 B/sym** (ideal 2-bit = 0.25). My F1220 "still live at rc238 (0.81 B/sym)" was a **small-N artifact** — the fixed ~2 KB `manifest.json` dominated at N=4096. At scale it's genuinely 2-bit-packed. (The user was right: fixed several rcN ago.)
- **O(n²) `genome_pack`: FIXED (linear).** Per-chromosome pack time is flat — **0.47 ms/chromosome** across 20 / 80 / 320 chromosomes.
So both §55 blockers that kept Siona on the loose NDJSON store (bridge.py note) are gone. **#231/PKG-3 (genome-native corpus store) is no longer upstream-blocked.**

## BUT — the governing constraint: store the LAPLACIAN, not Klein-4, on disk
Being *able* to store a genome ≠ storing the *right* object. Per the session's own findings (F1214/F1215/F1216) and the user's mid-turn recall: **Klein-4 flattens far more than the Laplacian**, because Klein-4 is the *working-memory READ* — the abelian combine + coarse `klein4_similarity` (F1214) that bags order/direction (F1215). The **Laplacian is the STORE** — exact, addressed, directional, curvature-keeping (F1216). So:
- **Do NOT persist Klein-4 HVs on disk** (that stores the flattened M-read form).
- **DO persist the Laplacian** — the relational directed edges (`edge_list + edge_weights[metric] + edge_charge[direction]`) and/or the **fiber** (the ordered sequence / integer ids). Klein-4 HVs are a *deterministic projection* recomputed on demand at inference (`klein4_random(seed=hash(token))`), never stored (F833) — Siona's bridge.py already does this ("the store holds the fiber, never a spatial HV per position").
- The klein4-symbol *packing* is fine as a **byte alphabet** for serializing the Laplacian (as the directed encoders this session do — the CONTENT is relational; klein4 is just the 2-bit on-disk code). What must not be stored is the *bind/bundle HV object* (the flattening).

So the corrected go-forward: genome-native is unblocked, and the genome should carry the **directed Class-L (Laplacian) + the fiber**, not Klein-4 HV bundles. This is F1216 (L-store / M-read) made the *disk* rule: **relational on disk (Laplacian), holographic in RAM (Klein-4, recomputed).**

## The new carrier-examples layer (rc241 #839)
`srmech.amsc._carrier_examples` exposes **`CARRIER_EXAMPLES`** — a per-carrier **CONSTRUCTION example** ("how to build/obtain this carrier"), the carrier-side peer of `_tool_docs.py`, merged into `carrier_schema()`'s per-carrier payload and flowing through the `srmech_carrier_registry` const table with **sha256 attestation**. Use: this is a genuine **Siona self-knowledge tier** — the "how do I *construct* a Mat/Vec/HV/One?" examples belong in her introspection/imitation tier (#250/#251) alongside `tool_schema` (the verbs) + `carrier_schema` (the nouns) + `responsion_schema` (the relationships) + patterns (F1207). It is attested, so it composes with the AMSC/MPM discipline.

## Verdict / next
1. **Update UPSTREAM_NOTES §55 → RESOLVED (rc241)** with the re-measurement (bloat 0.265 B/sym; pack linear); mark the #231/PKG-3 upstream gate cleared.
2. **#231/PKG-3 is now doable** — but store the **directed Laplacian + fiber**, not Klein-4 HVs (this finding). The corpus genome carries the relational structure; klein4 stays a recompute-on-demand projection.
3. **Wire `_carrier_examples` into Siona's introspection/imitation tier** (a construction-example self-knowledge face).

Composes **F1220** (corrected — §55 not-live-anymore; the self-refute is a curvature edge, F1217), **F1216** (L-store/M-read — now the *disk* rule), **F1214/F1215** (Klein-4 flattens: the reason not to store it), **F833** (fiber-not-HV store; Klein-4 as recomputed projection), **F1013/#231** (the genome-native corpus store, now unblocked), [[feedback_persist_genome_native_not_loose_json]] (now actionable for the corpus, storing the Laplacian), [[feedback_relational_not_dense_distributional_not_sparse]] (relational store).
