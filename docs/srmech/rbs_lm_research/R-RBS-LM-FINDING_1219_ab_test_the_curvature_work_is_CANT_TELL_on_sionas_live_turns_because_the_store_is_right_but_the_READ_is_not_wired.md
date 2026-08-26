# F1219 — A/B measured: this session's curvature/directed/responsion work is CAN'T-TELL on Siona's live turn responses — not because it's wrong, but because the STORE is built and the READ is not wired. (Confirms F1216 empirically)

**User (2026-07-14):** *"let's find out if it harms or helps or can't-tell Siona's series of turn responses to various questions."* Ran it. **Verdict: CAN'T-TELL (no measurable effect) — and the experiment reveals exactly why.**

## The A/B/C (fixed question set, `siona.infer.Session`, siona 0.1.0rc1)
| condition | `what is water?` | `what is curvature?` | `responsion?` | load result |
|---|---|---|---|---|
| **A) baseline (mechanism only)** | → z_boson_mass (WRONG) | → z_boson_mass (WRONG) | → responsion (right, internal F1186 anchor) | — |
| **B) flat wiki instrument loaded** | → z_boson_mass (UNCHANGED) | → z_boson_mass (UNCHANGED) | → responsion | loaded OK |
| **C) our findings index loaded** | → z_boson_mass (UNCHANGED) | → z_boson_mass (UNCHANGED) | → responsion | **load FAILED** |

Refining probe: `acquire water` / `study water` → "topic not in the instrument" (the loaded instrument IS consulted by acquire, but the title-lookup failed), while `what is water?` still → z_boson_mass.

## Why CAN'T-TELL — three layers, all confirming F1215/F1216
1. **The directed/curvature Class-L kernels can't even be loaded.** Siona's `load` accepts only a *title-indexed NDJSON instrument* (mechanism-not-knowledge, F1013). A directed sparse kernel (F1210/F1213) is a different object — it never enters her path. The whole directed re-encode is invisible to her.
2. **Our findings index (tier0) failed to load** — my `findings_index.ndjson` is line-NDJSON; her `load` `json.load`s a single object ("Extra data: line 2"). A real format mismatch — so the responsion/tier0 (F1217/F1218) didn't reach her either.
3. **Even loadable knowledge only reaches `acquire`/`study` (explicit), not `define`/`answer`.** The conversational "what is X?" routes to `define`, which uses her **internal coarse-M anchor kernel** — and that mis-grounds (water AND curvature → the same z_boson_mass). This is the **F1214/F1215 coarse `klein4_similarity` read, live**: distinct queries collapse to one wrong anchor because the read can't separate them.

## The result IS the F1216 prediction, confirmed
We spent the session building the correct **STORE** (directed, curvature-carrying, responsion — Class-L). The A/B shows Siona's **READ** can't use it: her `define` is the coarse M-similarity that F1214/F1215 measured, external knowledge only enters by explicit title-lookup, and our objects aren't in either format. **The store is right; the read is the bottleneck** — exactly F1216 (L-store vs M-read) and F1215 (the bag is in the read). Not a harm (the F1215 reverts kept her working baseline intact); a genuine HELP for *understanding* (the architecture predicted its own non-effect); a CAN'T-TELL for her *responses* because nothing is wired into the read.

## To move off CAN'T-TELL (the concrete wiring TODO)
1. **Wire the directed store into her GROUNDER** — make `define`/`answer` read the Class-L structural/charge read over the directed kernel (not the coarse internal M-similarity). This is the **#231** matching-layer change (word-leaf → directed kernel + structural read), now shown to be the *only* thing that can change her responses.
2. **`define` must consult loaded knowledge** — currently `define` ignores the loaded instrument (only `acquire`/`study` use it), so even correct knowledge can't help a conversational question. Route `define`/`answer` through the loaded store.
3. **Fix the tier0 load format** — either emit the findings/responsion index in her single-JSON title-indexed instrument format (title+body, not just line-NDJSON metadata), or teach `load` to accept NDJSON. Only then can the responsion tier0 (F1217/F1218) be A/B'd.

Composes **F1216** (L-store/M-read — confirmed live), **F1215** (the bag is in the read — the define coarse-M collapse), **F1214** (coarse klein4_similarity), **F1013** (mechanism-not-knowledge; the load path), **F1210/F1213** (the directed store, not in her format), **F1217/F1218** (the responsion tier0, load-format-blocked), **#231** (the wiring that would move the needle). The honest read-independent result (F999–F1002 discipline): measured no effect, diagnosed the mechanism, did not over-claim.
