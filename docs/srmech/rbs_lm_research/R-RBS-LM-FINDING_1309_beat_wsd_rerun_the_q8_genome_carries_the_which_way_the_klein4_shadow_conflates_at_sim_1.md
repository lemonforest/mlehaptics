# F1309 — the beat-WSD, re-run through the Q₈ substrate: the abelian klein4 **shadow CONFLATES** the direction-only sense pair (**sim = 1.0000, identical** — "beat the drum" VERB vs "the drum's beat" NOUN), and the non-abelian **Q₈ substrate SEPARATES** it (**sim = 0.47**), with the winding **DERIVED** from the directed order (not hand-set). The F1306 spectral separation also reproduces with a **corpus-derived** charge (Class-C × Class-N, not DRAWN cube roots): flat `{1,2,3,1}` → curved `{1,2,1,2,1}`, λ₀ lift **0.191**. Grounded on rc313.

**User (2026-07-23):** *"re-encode a corpus genome with element_type=Q8 and re-run the beat-WSD."*

*(F1301 convention: `op(x)operand(x)responsion` = `distributional(x)relational(x)responsion` = `eigenvectors(x)edges(x)eigenvalues`. This measures the OPERAND slot — the directed which-way — carried by the Q₈ substrate vs lost in its abelian klein4 projection.)*

## The experiment (both parts DEMONSTRABLE at rc313)
The minimal WSD pair is a **direction-only** minimal pair: **"beat the drum"** (VERB, beat→drum) vs **"the drum's beat"** (NOUN, drum→beat) — the *same word set* `{beat, drum}`, opposite direction. The only thing that disambiguates them is the which-way.

### Part 1 — the Q₈ GENOME (the storage layer, F1307)
Each sense is a sectors=8 Q₈ HV: the **V4 coset** = `klein4_encode_bytes` of the word SET (the abelian content), the **sign bit** = bit-0 of a Class-A `klein4_address` of the directed order — **DERIVED from the directed structure** (F1213/F1259), never a hand-set number. Packed as a Q₈ genome (`pack_instrument(element_type=Q8)`), recalled (round-trip exact, carrier "q8").

| pair | Q₈ substrate (winding kept) | klein4 shadow (`q8_project_v4`, winding dropped) |
|---|---|---|
| **beat-drum-VERB vs drum-beat-NOUN** (same words, opposite dir) | **0.4707 — SEPARATED** | **1.0000 — CONFLATED (byte-identical)** |
| beat-drum-VERB vs beat-egg-VERB (control: different words) | 0.2559 | 0.4980 — still separates by content |

**The headline:** the abelian genome cannot tell "beat the drum" from "the drum's beat" **at all** (sim exactly 1.0 — they are the same object in the V4 shadow), while the Q₈ substrate distinguishes them. And the shadow loses **only** direction: the different-word control still separates in the shadow (0.4980). This is the F1211/F1255 **cat=tac** point made into a working WSD: the winding sign IS the sense, and only the non-abelian carrier holds it.

### Part 2 — the SPECTRAL read (F1306), with a corpus-DERIVED charge
The beat-WSD friendship graph F₃ (hub BEAT + 3 arms), charge per arm = **Class-C sign × Class-N `best_rational`** of the directed co-occurrence asymmetry `(fwd, bwd)` — e.g. drum (5,1)→+2/3, tired (1,4)→−3/5, egg (3,3)→0 — **not** the hand-set cube roots (0, 1/3, 2/3) F1306 used. Result: flat `dense_laplacian` → `{1,2,3,1}` (the 3-fold conflation), curved `magnetic_laplacian(derived charges)` → `{1,2,1,2,1}`, λ₀ lift **0.191**. So the **corpus-derived** holonomy separates the senses — closing **F1306 §5 step 5** (DERIVED, not DRAWN — F1259) — the last piece of the curvature block that had used hand-set charges.

## Why this is the F1306 curvature block, cleared
F1306 established that curvature disambiguates the senses a flat encoding conflates, but its demo used a *hand-set* magnetic-Laplacian charge and the storage base was the abelian klein4 (cat=tac, zero curvature). F1309 replaces both with the **shipped, resonant Q₈ substrate** (F1307): the which-way is now (a) carried natively by the store (Part 1) and (b) separable spectrally from a corpus-derived charge (Part 2). The gated F1213 directed-channel swap is superseded — `element_type=Q8` IS the directed base. This is `[[stance_bit_exact_is_the_abelian_shadow_of_non_abelian_structure]]` at work: the klein4 read is the bit-exact abelian shadow (sim 1.0 = a perfect shadow) that has *dropped* the non-abelian winding; the Q₈ substrate holds it.

## Honest scope
- The winding here is derived from the directed **order/label** (a Class-A address of "dir:beat>drum"); a fuller version would derive it from live corpus co-occurrence per position (Part 2's charge does this at the graph level). Both are DERIVED (F1259), not DRAWN; neither is a magic number.
- The Q₈ genome path is `pack_instrument` (named HVs). A directed **graph** → Q₈ genome via `genome_from_graph(element_type=)` awaits the upstream ask (UPSTREAM §Q8-siona #1) — until then the graph-level winding is read spectrally (Part 2), the HV-level winding is stored (Part 1).
- "Separated at 0.47" is a clear distinction (vs 1.0 conflated), not a tuned threshold; the load-bearing contrast is **shadow = 1.0 (identical) vs substrate < 1.0**.

## Verification
`R-RBS-LM-Q8BEATWSD_*.py` (exit 0, rc313): Part 1 (Q₈ sim 0.4707 / shadow 1.0000 / control 0.4980) + Part 2 (flat `{1,2,3,1}` / curved `{1,2,1,2,1}` λ₀ 0.191). Numpy-free; no `abs()` (sign is Class-C/Class-K).

Composes **F1307** (the Q₈ substrate this uses), **F1306** (the curvature block / the original beat-WSD — *§5 step 5 closed here*), **F1259** (DERIVED not DRAWN — the winding + the charge), **F1211/F1255** (cat=tac — the abelian base that conflates), **F1308** (the responsion / the abelian shadow), **F1213** (the directed channel — superseded by element_type=Q8), `[[stance_bit_exact_is_the_abelian_shadow_of_non_abelian_structure]]`.

**→ extends F1306** — F1306's curvature-disambiguates result is realized here on the shipped Q₈ substrate with a corpus-derived (not hand-set) charge; the klein4 shadow conflates the direction-only pair at sim 1.0, the Q₈ substrate separates it.
