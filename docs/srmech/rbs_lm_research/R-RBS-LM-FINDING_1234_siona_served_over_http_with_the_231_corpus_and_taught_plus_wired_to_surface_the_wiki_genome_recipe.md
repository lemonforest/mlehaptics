# F1234 — Siona served over HTTP (0.0.0.0:3000) with the #231 corpus store, AND taught + wired to SURFACE the wiki-genome build recipe so the next LLM/person can build another wiki by just asking her

**User (2026-07-15):** *"wire up Siona at #231 over HTTP so I can check it out"* + *"check if Siona's own tooling knows how to create the wiki genome, so the next LLM or person knows how to do other wiki by simply asking her."* Both done.

## Serve Siona over HTTP (`R-RBS-LM-SIONAHTTP`)
A dependency-free stdlib server (`http.server`; no fastapi/uvicorn) serving `siona.infer.Session.turn()`:
- `GET /` — a browser chat page · `GET /chat?q=` — JSON reply · `GET /health`,`/status` — engine + corpus-load state · `POST /v1/chat/completions` — **OpenAI-compatible** (the universal connector: CopilotKit / AG2 / openai SDK, per F694/F726).
- The **#231 corpus loads in a BACKGROUND THREAD**, so the server is up INSTANTLY (`up 0.4s`); `/status` shows the load; `define` falls back to the shipped tool-grounding until the 39M-edge simplewiki genome lands (~21 min), then reads the real store (F1233).
- Binds **0.0.0.0:3000** (LAN-accessible, NO auth — trusted-network only). LAN URL this host: **http://192.168.44.147:3000/**. Verified live: `/health` ok, listening on `0.0.0.0:3000`, the recipe surfaces over HTTP.

## Does Siona know how to build the wiki genome? — she did NOT (stale); now she does + surfaces it
- **Checked:** her `encode_corpus_class_l_genome` pattern was **stale** — it described the OLD loose-JSON encode (`build_edges_topk`, `full_sparse_kernel` JSON), not the native rc253 directed-genome pipeline we just built.
- **Taught:** added `PATTERNS['build_wiki_corpus_genome']` (introspect.py) — the concrete native recipe: tokenize → `text.cooccurrence_edges(directed=True)` → `genome.graph_to_kernel` + a vocab chromosome → `recover_check_structural`/`_spectral`; store the directed Laplacian not Klein-4; refs R-RBS-LM-SIMPLEWIKIGENOME/SIONA231. Refreshed the stale pattern to defer to it. It's now in her knowledge genome (verified present).
- **Wired the SURFACING (the real gap):** F1207 built the pattern tier into her kb, but **s.turn never routed to it** (measured: "how do I build a wiki genome" → `help`, not the pattern). Added `_pattern_hit` + a `_dispatch` hook — a tight gate (a build/how word + a genome/corpus/class-l word, best pattern by key-overlap). Now **"how do I build a wiki corpus genome" → `siona.pattern` → the full recipe**, over HTTP too, while content reads ("what is water") are untouched. So the next LLM/person builds another wiki (enwiki, other language) by asking Siona how — she answers with the exact op pipeline.

## How to use it
- Browser: **http://192.168.44.147:3000/** (LAN) or http://localhost:3000/ on this host — type "how do i build a wiki genome" or (once loaded) "what is water".
- curl: `curl 'http://127.0.0.1:3000/chat?q=how+do+i+build+a+wiki+genome'`
- OpenAI clients: `base_url=http://192.168.44.147:3000/v1`, any `model`, `api_key` unused.
- Status: `curl http://127.0.0.1:3000/status` (watch `corpus` go from "loading" → "simplewiki_directed.genome (831,139 vocab)").
- Stop: kill the `R-RBS-LM-SIONAHTTP` python process.

Composes **F1233** (the corpus read-path wiring served here), **F1232** (native rc253 ops), **F1207**/#264 (the pattern tier — now actually routed to), **F694/F726** (the OpenAI-compatible surface / Siona-is-the-interface), #231/PKG-3, [[user_stance_framework_hands_the_next_question_to_the_expert]] (Siona hands the build recipe to whoever asks), [[feedback_public_issue_tracker_fine_transparency_by_default]] (LAN bind at user request; noted no-auth).
