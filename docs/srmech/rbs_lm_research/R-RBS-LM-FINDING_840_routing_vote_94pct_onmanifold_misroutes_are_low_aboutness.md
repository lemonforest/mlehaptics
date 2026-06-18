# F840 — The per-tome ROUTING VOTE is **94.3% accurate on-manifold** across a 6-tome store, and its misroutes are **low-aboutness generic contexts** (shared phrases like "is a type of") that don't disambiguate the tome — NOT a flaw in the resonance vote itself. Content-bearing contexts (incl. each article's name-carrying seed) route home reliably, so **sticky-route-at-the-seed is reliable**; **per-step re-routing needs an aboutness-weighted vote** (composes F768 / task #221) — which is also the gate for cross-tome composition (generalization). Closes the consolidate+route loop with an honest residual. On the real `srmech.rbs_lm` encoding, 0.8.2rc1, numpy-absent, no gen-1 code.

**Date:** 2026-06-18 · **srmech:** 0.8.2rc1 (TestPyPI dev substrate) · **Provenance:** `/tmp/route_vote.py` on `srmech.rbs_lm.substrate.ContextSubstrate` + `srmech.amsc.hdc`, D=10000, 6 per-article tomes (tagged chunks, C=8 sweet-spot), simplewiki raw-body instrument · **Composes:** F839 + its §CORRECTION (consolidate+route; sweet-spot C=8), [[F778]] (etak clump-routing), F768 / task #221 (aboutness-gate; low-aboutness contexts route poorly), [[feedback_relationship_lm_ideas_not_code_from_gen1]] · **User direction:** "keep continuing" (the per-tome/routing walk).

## The measurement (6-tome store, per-article tagged chunks, C=8; ~5 real contexts/article)
The vote: for a context, score every tome by `max`-resonance (`klein4_bind(M_chunk, encode_context(ctx))` → `sim_k4_batch` against that tome's own vocab, max over its chunks), route to the argmax tome.

| article | k\* | routed home |
|---|---|---|
| Adobe Illustrator | 4 | 100.0% (6/6) |
| Andouille | 4 | 80.0% (4/5) |
| Abrahamic religions | 6 | 83.3% (5/6) |
| Application | 6 | 100.0% (6/6) |
| Beard | 4 | 100.0% (6/6) |
| Creator | 4 | 100.0% (6/6) |
| **overall** | | **94.3% (33/35)** |

## What the 2 misroutes are (diagnostic, not noise)
Both misroutes are **generic, low-information contexts** — k\*-grams dominated by function/common words ("is a type of", short connective spans) that legitimately occur across multiple articles, so the home tome has no resonance advantage. This is **exactly the F768 aboutness phenomenon** (task #221: replace routing-stoplist extremes with *measured* function-ness): a context's routing reliability tracks its **aboutness** (content-word density), not a defect in the resonance math. Content-bearing contexts — crucially each article's **name-carrying seed** ("andouille is a type", "the abrahamic religions are a group") — route home 100%.

## What this establishes (relationship-native, no gen-1 code)
- **Sticky routing is reliable.** Seed the route from the article's content-bearing opening (high aboutness) → correct tome → generate within it. The 94.3% includes generic mid-article contexts that sticky routing never re-queries; the seed itself routes home for all 6. So the F839 "consolidate + sticky-route + sweet-C + k\*" recipe is **automatic** (the vote picks the tome; no hand-scoping), with the residual confined to per-step re-voting.
- **Per-step re-routing needs an aboutness-weighted confidence vote.** Naive per-step re-voting wanders (F839 §CORRECTION: 11–80% stayed-home) partly because it re-votes on every context including the low-aboutness ones. The fix is to **gate/weight the vote by aboutness** (F768's measured function-ness) — only re-route when a content-bearing context gives a confident margin; otherwise hold the current tome (hysteresis). This is the same gate that **cross-tome composition (generalization)** needs: switch tomes only on a confident, content-bearing cue.
- **Boundary unchanged.** The vote is `klein4_bind` + `sim_k4_batch` over the chunk-set (the §58 srmech candidate). The aboutness-weighting + hysteresis is recall-shaping → siona (composing the F768 aboutness work already there).

## Verdict / next
The consolidate+route loop is closed: many articles share one store (F839 read rank-1 100%), the routing vote picks the home tome 94.3% on-manifold (100% on content-bearing seeds), and per-article generation is ≥97.7% at the sweet-spot C (F839 §CORRECTION). The honest residual — generic-context misroutes — is the F768 aboutness gate, and resolving it (aboutness-weighted confidence vote + hysteresis) is the **gate to cross-tome composition / generalization** (the real LM test, vs. reproduction-via-inference). **Next:** (a) aboutness-weighted per-step routing (compose F768 measured function-ness) → re-measure stayed-home + generation; (b) the first **generalization** probe — a novel prompt whose continuation must compose across two routed tomes. Evaluate by groundedness / coherence, never throughput.
