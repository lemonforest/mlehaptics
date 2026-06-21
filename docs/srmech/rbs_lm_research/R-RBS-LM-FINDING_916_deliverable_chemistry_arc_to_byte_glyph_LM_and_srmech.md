# F916 — THE DELIVERABLE: the chemistry/Standard-Model arc (F902–F915) → the byte/glyph LM architecture + the refined srmech graduation. The arc that began from the F899 question ("the packaged RBS-LM is word-hash, not the byte/glyph LM object") resolves into a **four-layer stack, each at a distinct scale that must NOT be conflated** — and every piece is already in srmech. The graduation ASK (§68) is now a concrete spec, not just "use byte/glyph."

**Date:** 2026-06-21 · **srmech:** 0.9.0rc13 · **Branch:** `research/rbs-lm-rolling-2` (PR #687) · **Composes the whole arc:** F899/§68 (byte/glyph graduation ASK — the thread that started this), F901/F905 (C1 = the content-blind scale-invariant byte/glyph compositor), F906/F908/F910 (octonion = the content-dependent bond/force, molecular generator), F907/F907c/F465 (sedenion = addressing), F902/F909/F915 (linguistic structure is distributional, not the byte-force), F862 (cd_mult order-walk), F166/§57 (the packaged resonator) · **User direction (2026-06-21):** "bring back to our LM project and the pending srmech research arc that started this all — what this research surfaces are related deliverable."

## The four-layer byte/glyph LM (what the arc delivered)

| layer | rung / scale | srmech surface (already shipped) | role | findings |
|---|---|---|---|---|
| **substrate** | Klein-4 / C1 (the role-filler bundle) | `hdc.klein4_*` + the C1 compose `bundle_i bind(part_i, pos_key(i))` | the **content-blind, scale-invariant** byte→word→phrase→sentence compositor — *the byte/glyph LM object* | F901, F905 |
| **bond / force** | octonion, k=7 | `cascade.cd_mult` (+ `cd_conjugate`) | the **content-dependent** affinity/chemistry; the order-carrying key; **generates molecular structure** (grouping = architecture) | F906, F908, F910, F862 |
| **address** | sedenion, k=15 | `cascade.sedenion_register` (carry/correct) | the **navigable 16-slot box** (Siona's page-grid) | F465, F907c, F908, F891–F898 |
| **inference** | distributional | `rbs_lm.RBSLMInferenceSubstrate` (§57 resonator, no count-table) | the **linguistic structure** — syntax / valence / coherence / next-token | F166, F902, F909, F915 |

## The load-bearing lesson (repeated, now decisive): the scales do NOT collapse
- **byte-bond affinity** (octonion strain) = the *fundamental force* — which atoms bond cleanly (content-dependent, F906/F908). Byte-level.
- **form coherence** (C1 manifold) = the *scale-invariant compositor* — on-manifold words/adjacencies (F902).
- **morphological valence + syntactic constituency** = *distributional* — bound/free, bracketing (F909, F915) — NOT the byte-force.

F909 and F915 both came back NULL on "is the linguistic structure the octonion strain?" — and that null is the deliverable's spine: **the octonion gives the byte-chemistry; the resonator gives the language.** Building the LM means wiring the *right operator at the right scale*, not forcing one to do all.

## The refined srmech graduation ASK (sharpens §68 / F899)
The F899 ASK was "graduate the byte/glyph core into the packaged substrate." The arc specs it:
1. **`ContextSubstrate.enc` → the C1 byte-composed word** (F901's `bundle_odd(klein4_bind(byte_k4(b), pos_key(i)))`) — replacing the word-hash `token_seed` default (keep word-hash as an explicit fast atom-mode). *This is the actual byte/glyph LM object.*
2. **content-key / bond** = `cascade.cd_mult` octonion walk (F862/F906) — the content-dependent addressing key (already used in the F879→F898 probes).
3. **address** = `cascade.sedenion_register` (F465/F907c) — the 16-slot page-grid (already graduated as `siona.page_grid`).
4. **inference** = the existing §57 resonator (`RBSLMInferenceSubstrate`, no count-table) — unchanged; it is the distributional layer the NULLs (F909/F915) say the linguistics lives in.
All four are **already in srmech**; the graduation is *wiring C1 as the substrate enc + the layering*, plus the hot-path (`sim_k4_batch` native-float batch, F902/F903 note). Logged to UPSTREAM_NOTES §69.

## Why this is the deliverable (back to the project + the arc)
- **LM project (RBS-LM / Siona):** the byte/glyph LM = this 4-layer stack — the byte/glyph object (C1) the user kept asking for, with the octonion bond, the sedenion address, and the distributional resonator. The chemistry/SM arc *named the layers and proved they're distinct scales*.
- **srmech arc that started this:** §68/F899's "graduate byte/glyph" is now a concrete 4-point spec on shipped surfaces, with the scale-separation as the design rule (don't put syntax in the byte-force).
- **Cross-substrate proof (the methodology):** the same Hurwitz ladder (ℝ/ℂ/ℍ/𝕆/𝕊) and the same `srmech.qm` triality that build the physics Standard Model build the language one — atoms→bonds→molecules→addressing — which is the whole "one math, every substrate, scale-invariant" thesis the user opened with.

## Verdict / next
**Delivered:** the byte/glyph LM is a four-layer stack (C1 substrate · octonion bond · sedenion address · distributional resonator), each a distinct scale, all on shipped srmech surfaces; the §68/F899 graduation is now spec'd (UPSTREAM_NOTES §69). The derivations closed honestly — the heptad (4+3) = {K,L,M}/{D,E,F,G} (F914, principled partition; unit-bijection open), and linguistic structure is distributional not byte-strain (F915, null, = F909). **Next (gated on the user, a srmech rc):** wire C1 as `ContextSubstrate.enc` (point 1) — the one real package change, which makes `RBSLMInferenceSubstrate` run on the byte/glyph object natively; everything else is composition over already-shipped ops.

## Caveat correction (added in review — F917; carries into the notebook backfill)
The layer table above reads the octonion `cd_mult` bond as "generates molecular structure (grouping = architecture)." **Refine — do not delete:** the bond generates **byte-level** molecular structure (which *bytes* bond cleanly) and is a **content-dependent addressing/retrieval KEY** — it is **NOT** a source of *linguistic* structure. The arc's own two NULLs say so: valence is distributional (F909) and real syntactic constituency sits at octonion strain percentile ≈ 0.45 ≈ random (F915), so the strain is byte-derived and **blind to syntax**. **Implementation rule (load-bearing):** the bond is a *key, not a grammar* — wire `cd_mult` as the content-dependent retrieval/addressing key, and put **all** linguistic structure (syntax / valence / constituency / coherence / next-token) in the distributional resonator (`RBSLMInferenceSubstrate`, §57). Don't conflate the scales. *(Notebook-ready: "The octonion bond is the content-dependent byte-chemistry / addressing key; linguistic structure is distributional (the §57 resonator). The two NULLs F909/F915 forbid putting grammar in the byte-force — the right operator at the right scale.")* Full rc spec for the graduation: **F917**.
