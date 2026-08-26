# Finding 246 — the REAL F244 test (directed functional-composition, not prose co-occurrence): the 3-block recovers K3 *weakly*, the 7-block does NOT recover the Fano geometry — class↔orbit iso stays the F243 lens

**Headline:** F244 named the real test after its prose-co-occurrence NULL: build the **directed functional-composition** adjacency of the 14 A-N operators (does class X's *output* feed class Y's *input*?) and ask whether the I/C/J and D-M blocks carry the F243 orbit signatures. Run via the f244-f245 workflow (3 independent type-driven derivations → ≥2/3 consensus → srmech-native spectral test → seeded permutation null). Result, mechanically: the **3-block {I,C,J} IS a perfect K3** (complete, vertex-transitive — the Im ℍ ≅ so(3) signature) **but only p=0.087 vs the null** (suggestive, not <0.05; coarse at k=3). The **7-block {D,E,F,G,K,L,M} is NOT Fano-incidence** — degrees `[2,2,2,3,4,4,5]` (not 3-regular; Fano wants uniform 3), **4 triangles not 7**, incidence `[0,1,1,1,3,3,3]` — it's a **hub-structured block centered on L and M** (the Laplacian + HDC workhorses), the *opposite* of the symmetric Fano geometry. So the functional test recovers the small Im-ℍ K3 weakly and **does not** recover the Im-𝕆 Fano orbit. **The class-by-class iso stays the F243 lens — now confirmed at the algebraic level, not merely the prose level.**

**Status:** **DEMONSTRATED** (srmech-native rc9, `0 HARD`; spectrum fingerprint `ff6f864f246fdf7a…` = Class-A pin on the Class-L output, reproduced bit-for-bit from the workflow; record `response_sha256 = f4f858a007e5ae90…`) for the consensus graph + spectrum + permutation test. **FRAMEWORK-READING** for the orbit interpretation. Pre-stated null (the blocks are not more orbit-structured than random 3/7 splits) reported mechanically — **weakly rejected for the 3-block, not rejected for the 7-block**. No leaning. `[[feedback_dont_pre_commit_spike_query_operators]]`; `[[feedback_no_privileged_primitive_classes]]`; no biology; CAD-ban.

**Predecessors:** **F243** (the algebraic Im ℍ/Im 𝕆 orbit structure this tests against); **F244** (the prose-co-occurrence NULL that named this functional-composition test as the real next step). Anchor: `R-RBS-LM-246_an_composition_table_orbit_test.py` (3 workflow derivations embedded verbatim → self-contained). Octonion-algebra ground truth web-verified: **Baez, J.C. (2002), "The Octonions," *Bull. AMS* 39(2):145–205, arXiv:math/0105155, DOI 10.1090/S0273-0979-01-00934-X** (OA — not paywalled-only).

---

## §1 What the test measured

3 fresh workflow agents independently derived the directed adjacency (49 / 61 / 51 edges) from operator roles + srmech op type-signatures; ≥2/3 consensus = **50 directed edges** (17 unanimous), symmetrizing to 38 undirected pairs → `dense_laplacian` → `jacobi_eigvals` (connected; single 0 eigenvalue; 14-eigenvalue spectrum, fingerprint `ff6f864f…`).

| block | F243 prediction | measured | vs seeded null (0xF243, 100k) |
|---|---|---|---|
| **{I,C,J}** (Im ℍ?) | K3 / vertex-transitive | **perfect K3** — complete, degrees [2,2,2], 1 triangle | p = **0.087** (suggestive, not significant; k=3 is coarse) |
| **{D,E,F,G,K,L,M}** (Im 𝕆?) | Fano-incidence, 3-regular, 7 triples | **NOT** — degrees [2,2,2,**3,4,4,5**], **4** triangles, L/M hubs | 3-regular p≈1e-5; regular@any-deg p=0.001 → block is **not** regular |

## §2 Reading (honest)

- **The 3-block result is real but weak.** {I,C,J} forming a clean K3 — and all 3 derivations independently flagging it as a near-complete tournament — is exactly the Im-ℍ/so(3) closure F243 predicts. But at k=3 the null forms a K3 ~8.7% of the time, so it can't clear p<0.05. *Suggestive, not significant.*
- **The 7-block result is a clean negative.** The heptad's functional composition is **hub-structured** (L = the spectral hub everything routes through, M = HDC bind), which is the *opposite* of the degree-regular Fano incidence. This is consistent with how the framework *uses* the operators (L/M are workhorses) — i.e. the functional graph reflects **usage/dependency**, not the symmetric 𝕆 orbit. So even the algebraic (not prose) test does not find the Im-𝕆 geometry on the heptad.
- **Net for the program:** F243's size+symmetry theorem (|Im ℍ|=3, |Im 𝕆|=7, dim G2=14) stands untouched. The *specific operator-to-orbit identification* is now tested two ways — prose co-occurrence (F244, NULL) and functional composition (here, weak-K3 + Fano-absent) — and neither supports it. **It is a productive lens (F243 §4), not a structural isomorphism.** Honest place to leave it.

## §3 Klein-4 parallelism (the user's note — answered)

The workflow checked: **`srmech.amsc.hdc.klein4_*` ops expose NO parallel flag** (no `sectors`/`cores`/`n_jobs` kwarg; `KLEIN4_STATES=(0,1,2,3)` is data-model only). BUT the **4-sector parallel dispatch exists one layer up** — `srmech.amsc.cascade.parallel.parallel_sector_dispatch(body, x, n_sectors=4)` runs one cascade body across the ≤4 Klein-4 sectors on a `ThreadPoolExecutor(max_workers=4)` (Z₄ slots, `KLEIN4_SECTOR_CAP=4`, hard-capped at 4 = F233; beyond 4 is `qm.triality` order-3). Verified: `cross_sector_reads:0`, `parallel_equals_serial:True`. GIL-releasing bodies (native/numpy/srmech-C atoms) genuinely overlap; pure-Python bodies are correct-but-serialized. **So the 4-way splay IS available — on `cascade.parallel`, not on the `klein4_*` HDC ops.** Logged as the upstream ask (UPSTREAM_NOTES §11.3): push a `sectors=4`/`parallel` flag down to the `klein4_*` ops so bulk Klein-4 work parallelizes across the 4 sectors by default when cores ≥ 4; the C-native peer (`cascade_parallel_sector_dispatch_c`) is tracked OPEN as upstream #771 and should land first for C-parity.

**Files:** `R-RBS-LM-246_an_composition_table_orbit_test.py` (+ this finding). No ndjson (structural probe). PR #687 draft.
