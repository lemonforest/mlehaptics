# F748 — the UNCAPPED simplewiki sparse kernel is now PERSISTED (the F708 fix carried over); the ceiling is a LOAD-TIME knob, not an encode cap

**Date:** 2026-06-14 · **srmech:** 0.7.5rc149 · **Composes:** F708 (uncapped the pre-encode top-256 quantization bug; never persisted), F584/F542 (kernel = SSoT; shelf latent + no re-encode), F640 (the stale capped kernel), F746/F747 (the tome bookshelf + 256-cap audit), the user's load-time-N + holographic design (2026-06-14) · **User direction (2026-06-14):** "simplewiki where we do not have an artificial ceiling … when loaded into RAM, load with a top-words-rank-of-N selection vs all encoded words — is this not holographic substrate reduction?" · **Provenance:** `R-RBS-LM-WIKIFULL…py` (reuses F708 `build_edges_topk`; simplewiki_extracted/articles.jsonl)

## The gap, closed
F708 fixed the pre-encode top-256 quantization bug (`build_edges_topk`, `vocab_cap=None` → ALL words) but **never persisted** the uncapped kernel — so the only file on disk stayed the stale capped one (loaded wrongly in F746). **F748 persists it.** And it lands the user's architecture: **no ceiling at ENCODE; the ceiling is a RAM knob at LOAD.**

## Result — the uncapped kernel (6000 simplewiki articles, first cut)
- **145,127 vocab · 5,140,599 edges · 77.4s · dropped 0** (no pre-encode quantization — the whole-thesis point).
- **Persisted** the full sparse SSoT → `simplewiki_full_sparse_kernel.json` (112.5 MB, outside the repo), CC-BY-SA attested.
- **Direct associations are UNCAPPED and genuinely semantic** (the words the 256-cap threw away, now present *with real neighbours*):
  - `science` → fiction, computer, writer, technology · `planet` → earth, solar, system, sun, **neptune, dwarf**
  - `earth` → sun, water, moon, planets · `computer` → scientist, software, program · `music` → rock, pop, british
  - `dragon` → chinese, festival, saint, boat *(dragon-boat festival; Saint George)*
  This is night-and-day better than the census-skewed enwiki top-256 (F640/F747).

## The architecture (user's design, F708-verified, now persisted)
- **Direct associations = a SPARSE-ADJACENCY query** — no eig, no dense matrix → works at ANY vocab size, uncapped. This is the full-vocab "Siona knows the words relationally" tier.
- **The spectral tome bookshelf = a LOAD-TIME top-N rank cut** → the N-word induced subgraph → dense-eig only that → the N-tome bookshelf. **N is a RAM knob on the one full SSoT, EXACT for the loaded words.** Verified: load top-256 → 29,898-edge subgraph → 12/14 tomes; load top-1024 → 310,334-edge subgraph → 12/14 tomes.
- **Holographic reduction (F390) is the graceful-LONG-TAIL tool, not the whole** — F584 warns that flattening everything into one substrate capacity-walls. So: exact top-N working tier **+** holographic tail = the F119/F529 two-tier (the user's "holographic substrate reduction," correctly scoped).

## Honest scope
- **6000 articles = a first cut** (145k vocab already); the full 240,881 simplewiki articles is the same code, longer (the 15k run needed >280s — background it, no timeout). Full enwiki = the F690 bucketed path.
- This is the **relational** layer (co-occurrence). **Definitions are a separate dictionary kernel** (Wiktionary, CC) — F747's vocab-vs-dictionary distinction.
- Data lives outside the repo (112 MB); the script + findings are committed. srmech-native; no `abs()`; no CAD; no re-encode for the tomes (V from the persisted edges).

## Verdict
**The uncapped simplewiki kernel is persisted — the F708 fix finally carried over.** No ceiling at encode (145k vocab, 0 dropped); the ceiling is a **load-time top-N RAM knob** on the one full SSoT, exact for the loaded words, with direct associations available uncapped and the spectral tomes built per load-N. The user's "no artificial ceiling; choose top-words-rank at load" is realized; holographic reduction is correctly scoped to the graceful tail. Next: the NT=11/14/16 near:far re-check on a load-time top-N from THIS richer kernel, then (b) wire into Siona / the full 240k run / the dictionary kernel.
