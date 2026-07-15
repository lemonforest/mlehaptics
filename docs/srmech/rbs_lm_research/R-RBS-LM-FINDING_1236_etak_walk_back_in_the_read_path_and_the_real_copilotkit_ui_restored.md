# F1236 — two regressions in the #231 demo, both fixed: (1) the ETAK WALK is back in the read path — `define` now NAVIGATES the directed store (move-the-reference-frame, follow the charge) instead of a flat 1-hop lookup; (2) the real CopilotKit UI is restored — the `siona-chat` React chat on :3000 over a STREAMING /v1 backend on :8000, not a 20-line stdlib page.

**User (2026-07-15):** *"this doesn't have any of our etak walk and the http interface looks nothing like it had before."* Both correct. The demand-load switch (F1235) had quietly degraded two things.

## Regression 1 — the read was a 1-hop lookup, not the etak walk
`corpus_store.read()` returned only a token's immediate neighbours (`water -- seen with: <- area, -> sq, ...`). That is a **dictionary**, not a navigation. The store's REASON FOR BEING is the directed edge = **metric + CHARGE** (the chirality / which-way, F1228); a 1-hop read throws the charge axis away after a single step. The etak move (F786/F791 — navigate by MOVING THE REFERENCE FRAME) was absent.

**Fix — `corpus_store.etak_walk(h, token, steps, sense)`** (+ a bounded `_records` helper): from the token, hop to the strongest chirality-consistent neighbour, `steps` times, riding the directed coupling. `sense='fwd'` follows the forward charge (`c>=0`: what this token LEADS TO); `'bwd'` the backward charge (`c<0`: what LEADS HERE) — the two chiral fronts (F990, overtone/undertone). A visited-set halts the co-occurrence loop; metric-desc records mean the first admissible hop is the strongest coupling; the per-hop read window is bounded (`_SCAN=48`) so a hub token never pages its whole degree (a read, never a storage cut — F708/F748). The charge sign is the **Class-C which-way** (never the ALU magnitude-builtin). `infer._define` now leads with the ride, keeps the 1-hop "local star" underneath, falls back to `read()` then tool-grounding.

Live over the real simplewiki store (831,139 vocab, demand-loaded 0.6 s):
- `planet` → **planet -> earth -> sun -> moon** -> km -> socorro -> linear   (leads here: conductor -> symphony -> major -> minor -> planet)
- `music`  → **music -> video -> game -> released -> single -> album -> song**   (leads here: life -> born -> american -> rock -> music)
- `science`→ **science -> fiction -> movie -> directed -> starring -> john** -> american

It is genuinely navigating the directed store. (Some rides pick up simplewiki infobox markup — `sq -> mi -> area`, `subdivision -> name -> type -> string` — the known de-lensing / markup-FORM issue F782/F819/F983, separate from the walk mechanism, which is correct.) The fuller tome-TREE find→ride→web-hop (Fiedler, ETAKNAV) stays the heavier OFFLINE extension over a clustered store; the greedy directed RIDE is the scale-appropriate etak at demand-load.

## Regression 2 — the UI was a stdlib page, not the CopilotKit app
The "before" was a **two-process** setup: the CopilotKit React chat `~/general/siona-chat` (Next.js, **:3000**, `<CopilotChat>`) whose `/api/copilotkit` route (OpenAIAdapter, **streaming**) proxies to **`SIONA_BASE_URL=…:8000/v1`**. F1234 had replaced the whole thing with a 20-line stdlib HTML box squatting :3000 — so it both looked nothing like before AND (single-endpoint, non-stream) couldn't drive the CopilotKit adapter.

**Fix — restore the pair.** `R-RBS-LM-SIONAHTTP` is now the **/v1 BACKEND on :8000**: OpenAI-compatible `/v1/chat/completions` **STREAMING** (word-by-word SSE chunks → `finish_reason:stop` → `[DONE]`, the OpenAIAdapter path) + non-stream, plus `/v1/responses` (typed SSE), `/v1/models`, `/health`, a `/chat?q=` curl surface, and a stdlib fallback page. `ThreadingHTTPServer` so a held SSE stream never blocks; the corpus is loaded synchronously (~1 s demand-load, no startup race); `Session.turn` guarded by a lock (released before streaming). The CopilotKit UI runs unchanged on :3000. Verified end-to-end with the **actual `openai` node SDK** (the exact client the adapter uses): streaming round-trip returns the etak walk.

## Run it
```
# backend:
SIONA_CORPUS=~/corpora/wikipedia/simplewiki_directed.genome SIONA_PORT=8000 \
  /tmp/srmech_v/venv/bin/python3 docs/srmech/rbs_lm_research/R-RBS-LM-SIONAHTTP_...py
# UI:
cd ~/general/siona-chat && npm run dev          # -> http://<host>:3000/
```

Composes **F1235** (the demand-load this restores the walk on top of), **F1233/F1234** (the read-path wiring + the HTTP serve this corrects), **F786/F791** (etak navigation — find/ride/web-hop), **F1228** (directed charge = chirality/which-way, the axis the ride uses), **F990** (the two chiral fronts, overtone/undertone = fwd/bwd ride), **F694** (the OpenAI-compatible endpoint = the universal connector for CopilotKit/AG2), [[feedback_reach_for_the_one_for_phase_crank_navigation]] (navigate, don't divide), [[feedback_store_sparse_complete_never_top_k_truncation_at_storage]] (the ride reads the top edges; the store stays uncapped). #231/PKG-3.
