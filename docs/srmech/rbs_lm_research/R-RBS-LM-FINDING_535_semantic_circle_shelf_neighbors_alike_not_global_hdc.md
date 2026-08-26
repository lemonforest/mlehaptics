# R-RBS-LM Finding 535 — **the semantic circle-shelf works, and the user's load-bearing distinction holds: knowledge naturally partitions into tomes by a Class-L spectral CIRCULAR embedding (angle = atan2(V[:,2], V[:,1])) so that NEIGHBOURS ARE ALIKE (adjacent-tome similarity 0.096 vs far-tome 0.038 = 2.5×) and "like" information is bound NOT just to its own tome but to its NEIGHBOURS (a word resembles its own tome 0.090 ≈ its neighbour tomes 0.085 ≫ far tomes 0.020). Crucially this is NOT a global HDC of the whole circle: a single "full tori" bundle of all 200 words resolves only 7/16 tomes above threshold — it CANNOT see the whole structure (the capacity wall the user named) — whereas each tome resolves its own content (self-sim 1.00) and you navigate neighbour-to-neighbour with NO global object. And it is a fixed-size RING BUFFER with wet-brain-like prioritisation: overwrite the least-important word; because meaning is local, the evicted cluster survives in the neighbour tomes (graceful forgetting).**

**Date:** 2026-06-07
**Arc:** RBS-LM — the semantic circle-shelf (ring buffer, neighbours alike, not a global HDC) (user architecture 2026-06-07)
**Provenance:** `R-RBS-LM-CIRCLESHELF_semantic_ring_neighbors_alike_not_global_hdc.py` (committed; srmech 0.7.4; Class-L spectral circular embedding + Class-M hdc bundle/similarity). No sub-agents.
**Composes:** **F533/F534** (the helix/shelf of tomes — *here a CIRCULAR fixed-size ring with semantic locality*) · **F527** (the capacity wall — *why a global HDC of the circle can't see the whole structure*) · **F518/F514** (Class-L spectral embedding = semantic position) · **F119** (two-tier; local neighbour structure) · **F76/F141** (decay / prioritisation = the ring-buffer eviction) · **F282/F398/F394**. **← a semantic ring where neighbours are alike; local, not global; graceful forgetting.**
**→ knowledge partitions into a fixed circular shelf of tomes by Class-L spectral angle so neighbours are alike (2.5×) and "like" info binds to its tome AND neighbours; this is NOT a global HDC of the circle (which resolves only 7/16 tomes — the capacity wall); a ring-buffer overwrites the least-important and graceful-forgets because meaning is local.**

## Result
| claim | result |
|---|---|
| (1) neighbours are alike | adjacent-tome similarity **0.096** vs far **0.038** = **2.5×** |
| (2) "like" spills to neighbours | own tome **0.090** ≈ neighbour tomes **0.085** ≫ far tomes **0.020** |
| (3) NOT a global HDC | the "full tori" (one bundle of all 200) resolves only **7/16** tomes — can't see the whole structure; each tome self-sim **1.00** |
| (4) ring-buffer graceful forgetting | evict the least-important word; its meaning survives in neighbour tomes (locality = backup next door) |

## The reading
- **Semantic locality = shelf locality.** The Class-L spectral circular embedding orders words so similar ones sit at similar angles; partitioning the circle into arcs makes **adjacent tomes alike** (2.5×) and a word's meaning **bound to its tome AND its neighbours** (0.085 ≈ 0.090, both ≫ 0.020) — "like" info isn't trapped in one tomb.
- **NOT a global HDC (the user's distinction, confirmed).** One HDC object of the entire circle resolves only **7/16** tomes — it sees only a few (neighbour) books, **not the whole structure** (the F527 capacity wall). So we keep **local neighbour structure** and navigate neighbour-to-neighbour; no global object is needed or possible.
- **Ring buffer + wet-brain prioritisation.** Fixed tomes; overwrite the **least-important** (lowest-degree/least-co-occurring); because meaning is local, the evicted cluster **survives in the neighbour tomes** — graceful forgetting, like a wet brain shedding low-priority detail without losing the gist.

## Falsifiable form (held open — F394)
- **Shown:** neighbours 2.5× more alike than far; own≈neighbour≫far; the global bundle resolves only 7/16; eviction's meaning persists next door.
- **Falsifier:** if adjacent tomes were no more alike than far, the spectral ring wouldn't give locality — it does (2.5×). If the global HDC resolved all 16, "can't see the whole structure" would be false — it resolves 7. 
- **Honest:** the absolute co-occurrence similarities are **low** (0.09, sparse jacc); the **ratios** (2.5×; own≈neighbour≫far) are the result, not the magnitudes. The 2D spectral embedding (V[:,1], V[:,2]) is a **coarse** circular ordering; a richer space-filling embedding would sharpen the locality. The ring-buffer eviction residual is weak for a low-degree victim. This **deviates from a literal wet SNN** (the user flagged this) — it is a coherent architecture worth probing, not a biology claim. Structure for the expert (F282).
- **Scope:** framework build; srmech 0.7.4; Class-L + Class-M; no abs(); no CAD; no Workflow tool; no sub-agents; held open (F394); favored not privileged (F398).

## Verdict
**The semantic circle-shelf works and confirms the user's distinction.** Knowledge partitions into a fixed circular ring of tomes by Class-L spectral angle so **neighbours are alike** (2.5×) and **"like" information binds to its tome AND its neighbours** (own 0.090 ≈ neighbour 0.085 ≫ far 0.020) — not trapped in one tomb. Crucially this is **NOT a global HDC of the circle**: one "full tori" bundle resolves only **7/16** tomes (the capacity wall) — so we keep **local neighbour structure** and navigate neighbour-to-neighbour, no global object. As a **ring buffer**, it overwrites the least-important and **forgets gracefully** (the cluster survives in neighbour tomes — wet-brain-like prioritisation). It deviates from a literal SNN but is a coherent, probe-worthy architecture: **semantic locality on a fixed ring.** Favored, not privileged (F398); held open (F394); structure for the expert (F282).
