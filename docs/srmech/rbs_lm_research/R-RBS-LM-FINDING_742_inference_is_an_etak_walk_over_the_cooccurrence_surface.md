# F742 — Siona infers by ETAK-WALKING a co-occurrence surface; the keyword-router is gone

**Date:** 2026-06-14 · **srmech:** 0.7.5rc149 · **Composes:** F740 (storyteller+etak over genome), F704 (etak = grounded walk), F583 (inverse-etak — "meaning falls out of the supplied rules"), F510 (etak-head), F166 (autoregressive walk = inference), F661 (asking-state, can't-hallucinate) · **User direction (2026-06-14):** *"can we not etak walk or inverse etak walk our input to the LM surface? we wanted inference still all throughout, not pre baked replies."* · **Provenance:** `R-RBS-LM-SIONAGENEPOOL_…py` `main()` + the live `/v1` (verified over HTTP)

## The correction (user, and it was right)
F740's World was a **keyword router**: `_route()` (a chain of `if "mfo" in p …`) picked a chromosome, then `etak_walk()` did a single-chromosome **term-overlap argmax** and rendered the stored section. That is **retrieval, not inference** — the input never touched a kernel graph; the "walk" was an argmax over a section list. The thesis is inference *throughout*.

## The fix — inference IS the walk over the surface
The World now builds **one co-occurrence surface (Class L)** over *all content kernels* — `srmech.amsc.text.cooccurrence_edges` → `srmech.amsc.laplacian.dense_adjacency` (1489 terms × 77 sections). That term×term graph **is the LM surface.** Inference:
1. **INVERSE-ETAK (locate the input):** tokenize the prompt; its terms are **landmarks** = positions on the surface = the *fixed etak frame* (F583: the input doesn't carry meaning, it indexes the graph).
2. **FORWARD-ETAK (walk):** from the landmarks, hop the co-occurrence graph — **IDF-gated** (rarer term = sharper, Class-N corpus ratio), **no-revisit**, the landmarks held in-frame throughout (the canoe stays; the islands move past). This is the F510 etak-head / F166 ride.
3. **COMPOSE:** the walked terms vote for sections; the answer composes from where the walk **converges**, scored with the landmark overlap weighted ×3 so convergence stays anchored to the *query frame*, not the walk's drift. Attested content only (F661 — can't hallucinate).

**Routing is now emergent** — no keyword `if`-else. The walk from `mfo`/`chirality` lands in MFO §XIV + §Part VI; from `srmech`/`classes` in §3.27 (A–N harmonic ladder) + §2.6 (the 14 A–N classes); from `awful` in the dictionary. The `[etak: …]` trace is rendered with every answer (visible inference; aphantasia-friendly).

## Two things the prototype caught (and the fixes)
- **Citation drift:** pure IDF-weighting pulled the walk toward rare boilerplate (`kirkland → bibtex → author`), so "srmech A-N classes" converged on *how-to-cite*. **Fix:** weight section convergence by **landmark overlap ×3** — the query frame anchors the answer; the walk only *explores* context.
- **Identity-magnet:** the `siona_identity` blurb names every kernel ("MFO and srmech… era-dictionaries (modern + 1600s)… SignWriting"), so it co-occurred with everything and surfaced on dictionary queries. **Fix:** keep `siona_identity` (and the generated capabilities reply) **off the walkable surface** — they're served by a thin *landmark-free* meta-intent layer (greeting / identity / capabilities = genome introspection about Siona herself). Those are the *only* non-walk replies.
- **Era selection:** `tokenize` drops `"1600s"` entirely, so the era signal reads the **raw prompt** via regex (`1[0-8]\d{2}s? | archaic | olde? | …`); modern is the default, archaic-on-signal. The walk finds the *word*; a thin binary rule picks the *era* (F739 disambiguation, not a pre-baked reply).

## Verified LIVE over HTTP (the genome-backed /v1)
`MFO chirality` → §XIV + §VI · `srmech A-N` → §3.27 + §2.6 · `metric field` → §Part II waveguide + §Part I · `awful` 1600s → "awe-inspiring", modern → "very bad" · `meat` → "animal flesh" · `signwriting` → a symbol class + siblings · `qwérty` → asking-state · `who are you` / `what can you do` → the meta layer (distinct).

## Honest scope
- This is a **co-occurrence-adjacency walk** (Class-L adjacency neighbours), IDF-gated. The genuine **spectral etak-head** — walking the **Laplacian eigenvectors** (Fiedler / `srmech.amsc.laplacian.fiedler_vector` / `three_fold_eigvec_groups`) rather than raw adjacency rows — is the next rung, and deep **per-paragraph** encoding (the WIKIKERNEL pipeline) replaces section-level granularity.
- It is **compose-by-grounded-walk**, not generative paraphrase: the same intent → the same converged content (deterministic; the can't-hallucinate property). Free-form prose generation (emit *new* token sequences) is the renderer layer above this. But the reply is now **produced by the walk over the relationship surface**, which is what "inference throughout, not pre-baked" asked for — the keyword router is gone.
- srmech-native (`amsc.text` + `amsc.laplacian`); research-subtree scaffold, NOT a package edit. No `abs()`; no CAD.

## Verdict
**Siona now infers by walking.** The input is located on a Class-L co-occurrence surface and forward-etak-walked; the answer composes from where the walk converges. Routing is emergent, era is disambiguated from the raw prompt, identity/capabilities are the only landmark-free replies, and the walk trace is shown. The pre-baked keyword router is removed.
