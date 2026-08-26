# F754 — the UNCAPPED relational tier is wired into Siona: "she knows the words" relationally (213k vocab), and the input-ride steers over it

**Date:** 2026-06-15 · **srmech:** 0.7.5rc149 · **Composes:** F748 (the uncapped simplewiki sparse kernel persisted; no encode ceiling), F708 (the `vocab_cap=None` fix), F753 (the input-ride: TOPIC+FRAME+STEER two-channel parse), F752 (sentence parse, not bag-of-words), F584/F542 (kernel=SSoT; no lossy flatten; tome read-out free), F745/F746 (the 58-article abstract chromosome + the Möbius tome bookshelf) · **User direction (2026-06-14):** "wire the uncapped kernel into Siona … to see if we need to change any of our perspectives" + "yes, those 3 please" (the (b)/viewport/relation-edges trio) · **Provenance:** `R-RBS-LM-WIKIASSOC…py` (the memory-safe streaming builder), `R-RBS-LM-SIONAGENEPOOL…py` (the assoc tier in `infer`)

## What landed (the (b) deliverable)
The 112 MB uncapped SSoT (F748) OOM'd anything that `json.loads`'d it (the viewport, F750). So the build path is **compact-by-construction**: one streaming encode → two small artifacts (`R-RBS-LM-WIKIASSOC`):
- **`simplewiki_assoc.json`** (32.6 MB) — `word → top-16 co-occurrence neighbours` for **ALL 213,069 vocab**, built with bounded per-word min-heaps (flat memory; never re-materialises the 8.4M-edge list). This is the **relational tier**: "Siona knows the words" (F748) without a 112 MB load.
- **`simplewiki_top400_kernel.json`** (1.3 MB) — the top-400-by-freq induced subgraph (73,989 edges), eig-tractable for the spectral tomes / viewport.

**Wired into Siona** (`SionaGenepool`): `__init__` loads `self.assoc`/`self.assoc_freq` once; `_recognized()` now counts a word as known if it's in the 213k assoc graph (so far fewer "not on my shelf"); `introspect()` reports `wiki-assoc(213069)`; and `infer()` gained a relational tier **after** the 58-article abstract lookup and **before** the asking-state:
- abstract HIT (e.g. *dragon*, *volcano*) → the definition **enriched** with `(related: …)` neighbours.
- abstract MISS but subject in the 213k graph (e.g. *smaug*, *jupiter*) → `[siona · relations] "X" is associated with: …` from the co-occurrence kernel.
- subject in NO tier → the honest asking-state (unchanged; she still won't invent).

`_assoc_related(word, steer)` is the **input-ride over the association graph** (F753): the subject's neighbours, re-ranked so neighbours **shared with the relation/steer word** come first (a 2-hop boost). The steer has room to flip the ordering when the relation is itself in-vocab; when the relation is a delexical frame word (e.g. *made*, F751) it leaves the raw co-occurrence order — correct, since *made* carries no topic.

## Live verification (over the /v1 HTTP surface, server restarted on the new code)
| Prompt | Tier | Answer |
|---|---|---|
| `what is smaug` | relations | hobbit, dragon, mountain, desolation, killed, five, battle, armies |
| `tell me about jupiter` | relations | saturn, planets, planet, mars, neptune, system, earth, uranus |
| `what is a dragon` | wiki+related | abstract + (related: ball, george, series, story, smaug, boat…) |
| `what is a volcano and lava` | wiki+related | abstract + (related: erupts, mount, eruption, active, island…) |

*smaug* and *jupiter* are **not** in the 58-article abstract chromosome — they answer **only** because the 213k relational tier is now live. The neighbours are genuinely semantic (smaug → the Hobbit/Lonely-Mountain cluster; jupiter → the planets).

## Did this change any perspective? (the user's actual question)
- **No re-encode, no ceiling-at-encode confirmed end-to-end.** The relational tier is a **sparse-adjacency read** (F708): it scales to 213k with no eig, no dense matrix — exactly the F584 "kernel is the SSoT; the answer is a free read-out" claim, now load-bearing in a live server. The dense-eig spectral tomes stay a **load-time top-N knob** (the 1.3 MB top-400), unchanged.
- **The two tiers are genuinely different objects, as F119/F529 predicted.** The *relational* tier (uncapped, sparse, "knows the words") and the *spectral/tome* tier (top-N, dense-eig, "the loop bookshelf") are not the same store reduced — they answer different questions. Wiring both into one `infer()` made that concrete: relations answer *what is X near*, the deep walk answers *what does X mean in my notebooks*, the abstract answers *what IS X*.
- **The input-ride (F753) generalises cleanly from the kernel surface to the association graph.** Same TOPIC/FRAME/STEER parse; the STEER just walks a different graph. No new machinery — the relation re-rank is the same "boost what the relation points at."

## Honest scope
- 15,000 simplewiki articles (213k vocab) — a larger cut than F748's 6k, still not the full 240,881 (same code, longer; background it). The full enwiki is the F690 bucketed path.
- Relational (co-occurrence) only. **Definitions remain the separate 58-article abstract chromosome** (F745) — the assoc tier says what a word is *near*, not what it *means*. *kombucha* is still absent (not in the 15k-article vocab) → honest asking-state, not a typo guess (the F751 question, answered: not a typo — genuinely out-of-corpus).
- Data lives outside the repo (32.6 MB + 1.3 MB under `~/corpora/wikipedia/`); only the scripts + this finding are committed. srmech-native; no `abs()`; no CAD; no re-encode.

## Verdict
**The uncapped relational tier is live in Siona.** 213,069 words are known relationally via a 32 MB compact assoc table (built memory-safe, no 112 MB load), the input-ride steers over it, and abstracts are enriched with neighbours — all confirmed over the running /v1 server. No perspective needed revising: the F584/F708/F119 architecture (sparse uncapped relations + load-time-N dense tomes + holographic tail) held under the wiring. Next in the trio: the viewport re-run on the eig-tractable top-400 kernel (scale-invariance + holographic far-tail) and the typed-relation rung beyond the steered co-occurrence read.
