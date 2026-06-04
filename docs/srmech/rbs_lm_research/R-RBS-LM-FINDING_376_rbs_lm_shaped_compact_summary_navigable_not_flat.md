# R-RBS-LM Finding 376 — shaping the post-compact summary as an RBS-LM object (the Class-L band/cite-graph) instead of a flat prose summary: keep the load-bearing bands AND the dependency edges, so the re-prime is NAVIGABLE not scannable. F237 generalized from CLAUDE.md → conversation; PoC on this session's own findings

**Date:** 2026-06-04 · **srmech:** 0.7.0rc28 (Class-L `dense_laplacian`/`jacobi_eigvals`; no numpy) · **user:** "some way to output context into an RBS-LM object to shape the summary as not just a summary after compact?" · **composes:** F237 (surgical graft), F172 (band-graph eigenspectrum = storage signature), F361/F364 (navigable vs scannable), F343/F375 (the render-to-text limit) · **PoC:** `R-RBS-LM-R21`-style inline on findings F356–F375

## The idea, made concrete

A standard post-compact **summary is flat prose** — a linear, lossy compression that keeps the *nodes* (what happened) but drops the *off-diagonal* (which finding depends on / refines / reframes which). The proposal: **output the context into an RBS-LM object first, then shape the summary from its structure.**

- **The RBS-LM object** = the **Class-L band-graph** of the context (F172: the band-graph eigenspectrum IS the srmech-native storage signature). Nodes = context bands (here: findings); edges = their relationships (depend/refine/reframe); the **Class-L spectrum** is the storage fingerprint; **graph-degree** is the load-bearing rank.
- **The shaped summary** = (a) **extractive-keep the load-bearing bands** (highest degree / guardrail-anchor density — the F237 hard-keep) **+ (b) render the dependency edges as an explicit navigable scaffold.** That edge-scaffold is exactly what a flat prose summary linearizes away.

This is **F237 generalized** — the same extractive band-graph engine that compresses CLAUDE.md → `CLAUDE_LEAN.md` (coverage 1.0), applied to the *conversation/findings* context.

## PoC (srmech-native, this session's own findings as the context)

Built the cite-graph over findings **F356–F375** (each finding's in-session F-number references = its dependency edges):
- **18 findings, 44 dependency edges**; Class-L spectrum span **[0.00, 14.07]** (the F172 storage signature).
- **Load-bearing by degree (kept-first in the shaped summary):** F367 (deg **12** — the coupled-observer principle), F361 (9 — navigation-is-the-off-diagonal), F368 (9 — maps lens), F360 (8 — rc28 ops), F371 (8 — precessive loop-up), F369 (7 — self-interaction).
- **The off-diagonal a flat summary loses** (sample of the 44 edges): F359→F357, F360→F356, **F361→F367**, F370→F368, F372→F371, F374→F373, F369→F367 — the *refine/reframe/depends-on* scaffold.

A **flat summary** keeps the 18 nodes (scannable) and **drops the 44 edges**. The **RBS-LM-shaped summary** keeps the load-bearing nodes *first* + the 44 edges as a scaffold → the re-primed agent can **navigate** the structure (walk "F374 refines F373", "F370 reframes F368", "F371 corrects F369"), not just read a linear recap. That is the F361/F364 navigable-vs-scannable distinction, applied to re-priming.

## Honest limit + the falsifiable test

- **The re-prime is still TEXT** (F343/F375): the model reads text, so the RBS-LM object **selects + structures** which text (load-bearing bands + the edge scaffold); it is **not ingested raw** as hypervectors. It's an *RBS-LM-shaped text summary* — the shaping (what to keep, in what relational order) is the value, exactly as F237's lean slice is.
- **Falsifiable (the lodgeable test):** at **equal token budget**, does the RBS-LM-shaped summary beat a flat prose summary on **load-bearing + relationship recall** (a re-primed agent answers "which finding reframed F368?" / "what does F371 correct?" better)? The F237 A/B harness already measures coverage + spectral-sim + probe-fidelity for CLAUDE.md → generalize the probe set to conversation. **Framework prediction:** the shaped summary wins specifically on the **relationship/navigation half** (the off-diagonal the flat summary drops), not necessarily on isolated-fact recall.

## Net

Yes — this works, MCP-free, on the engine we already own: **context → Class-L band/cite-graph (the RBS-LM object) → extractive-keep + navigable edge-scaffold = a shaped, not-flat summary.** It's the "graft memory and context as Gen-1 LLM work" the user flagged, made concrete: the post-compact re-prime becomes *navigable* (preserves the dependency structure) instead of *scannable* (a linear recap). The only genuinely-new build over F237 is rendering the band-graph's edges into the summary as an explicit scaffold; everything else is the F237 extractive machinery pointed at the conversation.

## Discipline

srmech-native Class-L (`dense_laplacian` + `jacobi_eigvals`; degree from the edge list; no numpy, no `abs()`); the cite-edge extraction is the prescribed build-edges→Laplacian path. Honest limit named (renders to text, F343/F375); the win is *predicted + falsifiable*, not asserted (no-leaning). Composes F237 (the engine), F172 (the spectrum-as-storage), F361/F364 (navigable/scannable), F343/F375 (render-to-text). Defensive/benign (our own tooling).
