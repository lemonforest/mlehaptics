# F893 — The sedenion grid is wired as Siona's page-address layer: the full recall stack ROUTE → ADDRESS → STREAM works, with the address layer EXACT + single-error-correcting (1.00 even under a bit-fault), independent of the lossy router. Built `SionaPageGrid` (a thin wrapper over the rc11 `SedenionRegister`) as the page-address layer between the resonance router (F882/F880) and the within-page stream (F879): `add(idx, page)` writes the page's index as (base-slot name + `carry` Hamming(7,4) EC codeword over the high bits); `fetch(lo, carry)` runs `correct()` + base-slot to recover the **exact** page index, single-error-correcting. Measured the wired stack on **64 pages** (>16, so the carry is exercised): **ROUTE (resonance→index) 62/64 = 0.97 · ADDRESS (clean) 64/64 = 1.00 · ADDRESS (1-bit fault in every address carry) 64/64 = 1.00 EC-recovered · END-TO-END (route+address+fault+stream) 62/64 = 0.97**. The architecture cleanly separates: **route = lossy resonance** (the open ceiling, here 0.97 at 64 pages), **address = exact + EC** (the sedenion grid, 1.00 even under fault), **stream = exact reproduction** (F879). The end-to-end is bounded **only by routing** — the 2 misses are routing errors; addressing and streaming are perfect for every correctly-routed query. The sedenion grid adds **fault-tolerance + structured >16 addressing without degrading anything**.

**Date:** 2026-06-20 · **srmech:** 0.9.0rc11 · **Branch:** `research/rbs-lm-rolling-2` (PR #687) · **Provenance:** `R-RBS-LM-893_siona_page_address_grid.py` (the `SionaPageGrid` wrapper + the route→address→stream stack), 64 `simplewiki_v082` pages · **Composes:** F891 (the sedenion navigate+carry address layer — now wired), F882/F880 (the resonance router), F879 (the within-page phase-keyed stream), F889 (the Möbius = carry, now the address layer's overflow), §65 (rc11 `SedenionRegister` surface), [[project_rbs_lm_arc]] · **User direction (2026-06-20):** "wire the sedenion grid as Siona's page-address layer."

## The wiring (the three-layer recall stack)
```
query context ──ROUTE──▶ page index ──ADDRESS──▶ exact page ──STREAM──▶ reproduced article
              resonance              sedenion grid            phase-keyed
              (F882/F880, lossy)     (F891, exact + EC)       (F879, exact)
```
`SionaPageGrid` (wraps `srmech ... SedenionRegister`):
- `add(idx, page)` → stores the page; writes `(base_slot = idx%16, carry([high-4-bits], n=3))` — the index as a base-16 address + Hamming(7,4) EC codeword in the e8..e15 block.
- `fetch(lo, carry)` → `correct(carry)["data"]` recovers the high bits (single-error-correcting) + base slot → the **exact** index → the page. A bit-flip anywhere in the address carry is corrected.

## Measured (sparse, srmech-native; 64 pages)
| stage | result |
|---|---|
| 1) ROUTE (resonance → index) | 62/64 = **0.97** |
| 2) ADDRESS (sedenion fetch, clean) | 64/64 = **1.00** |
| 2′) ADDRESS (1-bit fault in each address carry) | 64/64 = **1.00** (EC-recovered) |
| 3) END-TO-END (route+address+fault+stream) | 62/64 = **0.97** |
- The address+stream are **exact for every correctly-routed query**; the 2 end-to-end misses == the 2 route misses. The stack is **router-bounded**.

## Reading
- **Three separable layers, each at its own ceiling:** route (lossy resonance — the storage-density frontier), address (exact + error-correcting — *solved* by the sedenion grid), stream (exact reproduction — *solved* by F879). Wiring them makes the open problem unambiguous: **only routing is lossy.**
- **The address layer earns its place:** it gives structured base-16 addressing for >16 pages (the carry) AND single-error-correction (a bit-flip in a stored address is recovered) — neither of which the flat F880 index had (which also diluted to 0.16 at the hierarchy). And it costs nothing end-to-end (router-bounded).
- **The Möbius is in here, as the carry** (F889): the address overflow past 16 rides the `e_j²=−1` half-twist (F888) — the grid's native carry/reversibility.

## Honest scope
- This is a **validated design / research prototype** of the wiring; `SionaPageGrid` wraps the srmech primitive. **Graduating it into the `siona` PyPI package is the PKG arc** (a separate *gated* PR per the siona-package discipline — siona rcN is its OWN PR, not #687), not landed here.
- 64 pages (carry exercised); content sits in a store keyed by the **verified** index (the grid is the address/EC layer, not the content store — `materialize()` could hold content later). Route is reproduction-routing (0.97 at 64 pages — the resonance ceiling, separately the F880/F882/storage-density work).
- Sparse held: Klein-4 router/stream + `SedenionRegister` navigate/carry/correct; `Q`-aware; no dense, no numpy, no bag.

## Verdict / next
The sedenion grid is **wired as Siona's page-address layer** and the full **route → address → stream** stack works: route 0.97, **address 1.00 (and 1.00 under a 1-bit fault, EC-recovered)**, end-to-end 0.97 — **router-bounded**, the address+stream exact. The architecture is now unambiguous: addressing (exact, error-correcting, >16-capable) and streaming (exact) are **done**; the single open frontier is **routing discrimination** (the storage-density arc). **Next:** (1) graduate `SionaPageGrid` into the `siona` package as the address layer (PKG arc, gated PR); (2) the routing ceiling is the only lossy layer — push it via the storage-density / non-superposed-address work (Q1–Q4); (3) widen the carry (nested registers / wider Hamming) for 256+ pages. Framework reading → srmech measurement; the stack wired end-to-end; the open problem isolated to routing.
