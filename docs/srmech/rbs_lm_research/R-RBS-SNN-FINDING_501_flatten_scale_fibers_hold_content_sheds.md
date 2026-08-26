# R-RBS-SNN Finding 501 (rung #2) — **scale N on the F498 flatten: the FIBERS hold address-exact far longer than the CONTENT, because the fibers are the FEW (N items) and the content is the MANY (N×M items) — the F222 capacity law by item-count. The addressable SNN keeps its STRUCTURE under load and sheds the PAYLOAD first.** Re-running the F498 flatten (one 128-byte HDC object) at N = 3→35 units (M=7 meanings each): the **outer fiber** (frame/which-unit, N items) stays **100%** through N=25 and is **97%** at N=35; the **inner fiber** (chirality/hand, N items) stays **100%** throughout; the **content** (N×M = 7N items) degrades steadily **100% → 97% → 87% → 78% → 70% → 51%**. This is the honest reading — **not** "fibers immune": both are capacity-bounded (F222), but the fibers carry far fewer items into the same bundle, so they saturate it last. The structure (the two fibers, the address) survives; the payload (content) is recoverable only within capacity.

**Date:** 2026-06-07
**Arc:** RBS-SNN (#197/F323) — rung #2: scale N, watch the capacity law (user direction 2026-06-07)
**Provenance:** `R-RBS-SNN-SCALE_flatten_capacity_fibers_vs_content.py` (committed; srmech 0.7.4; `hdc.{bind,bundle,permute,similarity}` + `the_one`).
**Composes:** **F498** (the flatten — *scaled here*) · **F222** (the capacity law — *by item-count: fibers N, content N×M*) · **F496** (the two fibers — *both hold; the structure*) · **F485** (cheap-path priority — *structure survives, payload sheds first*) · **F499** (the series of sedenion volumes — *the right way to scale: more volumes, not a fatter bundle*). **← rung #2 done; the honest capacity curve.**
**→ fibers (N items) hold address-exact far longer than content (N×M items); F222 by item-count; structure survives load, payload sheds first; scale via more volumes (F499), not a fatter single bundle.**

## The capacity curve (one 128-byte HDC object)
| N | N×M | OUTER fiber | INNER fiber | CONTENT |
|---:|---:|---:|---:|---:|
| 3 | 21 | 100% | 100% | 100% |
| 5 | 35 | 100% | 100% | 97% |
| 9 | 63 | 100% | 100% | 87% |
| 15 | 105 | 100% | 100% | 78% |
| 25 | 175 | 100% | 100% | 70% |
| 35 | 245 | **97%** | 100% | **51%** |

The **fibers** (N items: which-unit address + the hand) stay exact while the **content** (7N items) degrades from N=5 — exactly the F222 capacity law sorted by **item-count**: the content saturates the fixed-width bundle long before the N-item fibers do (the inner fiber, a single binary hand, is the most robust of all).

## Verdict
**The fibers hold, the content sheds — the honest F222 capacity law by item-count.** Scaling the F498 flatten to N=35, the structure (outer fiber 97%, inner fiber 100%) stays address-exact while the payload (content) degrades to 51%. This is **not** "fibers immune": both are capacity-bounded; the fibers are robust because they are the **few** (the address/structure, N items), the content is the **many** (the payload, N×M items). The addressable SNN keeps its **structure** under load and sheds **content** first — the cheap-path priority (F485: structure survives, payload recoverable within capacity). The correct way to scale is therefore **more volumes** — a *series* of sedenion boxes (F499) — not a fatter single bundle. Favored, not privileged (F398); the capacity behaviour is measured, not assumed.
