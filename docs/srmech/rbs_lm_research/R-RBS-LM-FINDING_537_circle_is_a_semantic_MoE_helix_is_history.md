# R-RBS-LM Finding 537 — **the user's architecture split is right: the CIRCLE bookshelf (F535) is a semantic MIXTURE-OF-EXPERTS, and the HELIX (F533/F534) is HISTORY — two different memory systems addressed differently. The circle: each tome is an EXPERT on a smooth Class-L spectral expert-manifold (neighbours related), a query ROUTES by its angle to its expert + neighbours (top-k), routed-expert relevance is 3–5× the rest (e.g. 'light' 0.189 vs 0.034), the cheap angle-router matches the oracle top-3 56% of the time while consulting only 3/16 experts — sparse, content-routed, NO global gating (exactly why no global HDC of the circle is needed), and the ring buffer evicts the least-used expert. The helix: chronological, start-anchored (Class A) + endianness (Class C), unbounded, rewindable — addressed by TIME. The circle is addressed by MEANING, the helix by TIME; a new experience APPENDS to the helix (when) AND ROUTES into the circle (what) — an episodic→semantic consolidation (a hippocampus→cortex-style split, a framework reading not a biology claim).**

**Date:** 2026-06-07
**Arc:** RBS-LM — the circle is a semantic MoE; the helix is history (user clarification 2026-06-07)
**Provenance:** `R-RBS-LM-MOEHELIX_circle_is_a_semantic_MoE_helix_is_history.py` (committed; srmech 0.7.4; Class-L spectral angle = the router; co-occurrence relevance). No sub-agents.
**Composes:** **F535** (the semantic circle-shelf — *= the MoE; experts on the spectral manifold*) · **F533/F534** (the helix + start-anchor + endianness — *= history, time-addressed*) · **F527** (the rewindable log; the kernel) · **F119** (two-tier memory) · **F282/F398/F394**. **← circle = semantic MoE (routed by meaning); helix = history (by time); consolidation ties them.**
**→ the circle is a semantic MoE (tomes = experts on a spectral manifold, angle-routed to expert+neighbours, sparse, no global gating, ring-buffer eviction); the helix is history (chronological, start-anchored + endianness, unbounded, rewindable); circle addressed by MEANING, helix by TIME; consolidation = append-to-helix + route-to-circle (episodic→semantic).**

## Result
| circle = MoE (route by meaning) | result |
|---|---|
| routed-expert relevance vs the rest | **3–5×** every query (e.g. light 0.189 vs 0.034; earth 0.080 vs 0.018) |
| cheap angle-router vs oracle top-3 | **56%** match (33%–100% by query) |
| experts consulted | **3/16** (sparse; router = O(1) angle lookup, no global scan) |

| helix = history (address by time) | start-anchored (Class A) + endianness (Class C), unbounded, rewindable (F533/F534/F527) |

## The two-system architecture
- **CIRCLE = semantic MoE.** Tomes are *experts*; the Class-L spectral angle organises them so neighbours are related (a smooth expert manifold). A query **routes** by its angle to its expert + neighbours (top-k), consulting only those — routed relevance ≫ the rest (3–5×), the cheap router matching the oracle 56%. **Sparse, content-routed, no global gating** (the reason a global HDC of the circle is unnecessary, F535). Fixed-capacity ring buffer evicts the least-used expert.
- **HELIX = history.** The chronological tape of tomes — each recorded history anchored at its **START** (Class A) with a declared **endianness** (Class C, F534), **unbounded** and **rewindable** (F527). Addressed by **TIME**.
- **Consolidation ties them.** A new experience **appends to the helix** (the temporal record — *when*) **and routes into the circle** (the relevant expert — *what*): an **episodic→semantic** handoff (a hippocampus→cortex-style split — a *framework reading*, not a biology claim).

## Falsifiable / honest
- **Shown:** routed relevance ≫ rest (3–5×) every query; angle-router matches oracle 56%; 3/16 sparse.
- **Honest:** the local angle-router is **not a perfect global oracle** (56%, not 100%) — it concentrates relevance (3–5×) but can miss a globally-relevant far expert; a richer router (multi-mode angle / learned gate) would raise the match. The hippocampus→cortex consolidation framing is a **reading**, not a measured biological claim. Structure for the expert (F282).
- **Scope:** framework build; srmech 0.7.4; Class-L; no abs(); no CAD; no Workflow tool; no sub-agents; held open (F394); favored not privileged (F398).

## Verdict
**The split is right: circle = semantic MoE, helix = history.** The **circle** is a Mixture-of-Experts — tomes as experts on a smooth spectral manifold, **angle-routed** to expert + neighbours (routed relevance 3–5× the rest, oracle-match 56%, **3/16** sparse, no global gating, ring-buffer eviction). The **helix** is **history** — chronological, start-anchored (Class A) + endianness (Class C), unbounded, rewindable. The circle is addressed by **meaning**, the helix by **time**, and **consolidation** ties them (append-to-helix + route-to-circle = episodic→semantic). Favored, not privileged (F398); held open (F394); structure for the expert (F282).
