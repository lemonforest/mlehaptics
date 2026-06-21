# F917 — the C1-enc graduation rc SPEC (the one real package change from F916) + the caveat correction to the F916 bond-layer reading. Wire the byte/glyph compositor (C1) as `ContextSubstrate.enc` so `RBSLMInferenceSubstrate.learn`/`.infer` run on the byte/glyph LM object natively; rebuild the L1/L2/L3 ladder on the same operator; add a `scale_signature` introspection. **Caveat correction (load-bearing):** the octonion bond/key layer is a *content-dependent addressing/retrieval KEY*, NOT a grammar/structure generator — F909 + F915 both NULL, so syntax/valence/constituency live ONLY in the distributional resonator, never in the byte-force.

**Date:** 2026-06-21 · **Target srmech:** cut against current head (`0.9.0rc16`+ on `main`), NOT the rc13-era PR-#687 branch source · **Branch (spec authored on):** `research/rbs-lm-rolling-2` (PR #687) · **Composes:** F916 (the 4-layer deliverable), F900/F901/F905 (C1 = the scale-invariant compositor), F899/§68 + §69 (the graduation ASK), F909/F915 (the two NULLs that ground the caveat) · **Status:** SPEC ONLY — no package change until user go (the F899 discipline: a srmech change = its own rc, never a route-around).

---

## 0. Caveat correction to F916 (so the notebooks carry the corrected reading)

F916's layer table reads the octonion `cd_mult` bond as "generates molecular structure (grouping = architecture)." **Refine — do not delete:** the bond generates **byte-level** molecular structure (which *bytes* bond cleanly; content-dependent affinity, F906/F908), and it is a **content-dependent addressing/retrieval KEY**. It is **NOT** a source of *linguistic* structure. **F909 and F915 both returned NULL** on "does the octonion strain encode the language?" — valence is distributional (F909), and real constituency sits at strain percentile ≈ 0.45 ≈ random (F915). The strain is byte-derived and **blind to syntax**. Therefore the implementation rule:

> **The bond layer is a key, not a grammar.** Wire `cascade.cd_mult` as the content-dependent *retrieval/addressing key* (and the byte-chemistry generator); wire **all** linguistic structure — syntax, valence, constituency, coherence, next-token — into the distributional resonator (`RBSLMInferenceSubstrate`, §57). Never implement the bond as a structure/grammar generator. Don't conflate the scales (F905/F909/F911/F915, the arc's spine).

Notebook-ready one-liner (lift verbatim into the §8.x backfill): *"The octonion bond is the content-dependent byte-chemistry / addressing key; linguistic structure is distributional (the §57 resonator). The two NULLs F909/F915 forbid putting grammar in the byte-force — wire the right operator at the right scale."*

---

## 1. Scope — exactly the irreducible change, plus the ladder unification

**Part A (irreducible — the F916 "one real change"):**
1. **New public op `hdc.klein4_compose(parts)`** — the scale-invariant role-filler compositor `bundle_i klein4_bind(part_i, pos_key(i))` over ARBITRARY part-vectors (distinct from `klein4_encode_bytes`, which mints byte-atoms internally; this one takes already-composed `HV` parts → it is the *recursive* operator). Odd-count pad (never drop a part). Pure composition over native `klein4_bind`/`klein4_bundle` → rides existing native dispatch; **no new C symbol** (a thin C peer is a tracked follow-up, like `klein4_encode_bytes`).
2. **`ContextSubstrate.enc(tok, sector)` → byte/glyph by default**, behind an `enc_mode` selector:
   - `enc_mode="byteglyph"` (NEW DEFAULT) = `klein4_bind(klein4_encode_bytes(tok.encode("utf-8"), D), _sector_const(D, sector))` — the byte-composed word + the sector channel preserved. Empty/pad token → the fixed neutral pad atom (klein4_encode_bytes requires non-empty).
   - `enc_mode="wordhash"` = the current `encode_word_k4` (whole-word sha256 seed) — KEPT as the explicit fast atom-mode (the content-address DUAL; F900).
3. **`scale_signature(level_vectors)` introspection** — the 1-part-change coherence signature per scale (the F900 self-similarity metric: similarity of a whole vs a one-part-perturbed whole, via native `klein4_similarity`). Makes "coherence == scale-invariance" a checkable, first-class property; pure composition over native `klein4_similarity`, no new C symbol.

**Part B (same rc — the §69 ladder unification):**
4. **Rebuild `encode_bigram_l1` / `encode_skeleton_l2` / `encode_sentence_l3` on `klein4_compose`** — replace the chained-`bind` (similarity-destroying, non-scale-invariant) bodies with the recursive role-filler compose, parts at level n+1 = composed vectors of level n; keep each level's `_sector_const` sector tag. The skeleton (L2) is the "coherent word-string before a sentence" fractal node (F900).

**Out of scope (already shipped — composition only, no code):** bond = `cascade.cd_mult`, address = `cascade.sedenion_register`, inference = `RBSLMInferenceSubstrate`. The rc wires C1 + the ladder; it does NOT touch the bond/address/resonator surfaces.

## 2. Exact diffs (the surgical set)

- `srmech/amsc/hdc.py`: add `klein4_compose(parts)` (public; `__all__`); it is the SHAPE of `klein4_encode_bytes` over arbitrary parts.
- `srmech/rbs_lm/substrate.py`: `enc()` gains `enc_mode` (default `"byteglyph"`); `_enc_byteglyph()` helper; `pos_key()` mints directly via `klein4_random(seed=sha256(pos_label))` (enc-mode-independent role vector); `encode_bigram_l1`/`_skeleton_l2`/`_sentence_l3` rebodied on `klein4_compose`; `scale_signature()` added.
- `srmech/rbs_lm/inference.py`: `RBSLMInferenceSubstrate.from_params` accepts `substrate.enc_mode` (default byteglyph); no logic change otherwise (it already conditions on `ContextSubstrate`).

## 3. Ship-discipline checklist (the standard op-add ritual)

- **5-SSOT version bump** (`version.py`, both `pyproject*.toml`, `c/include/srmech.h` ×2, the scaffolding version test).
- **`klein4_compose` op surface:** `ToolEntry` in `tool_schema.py` (Class M; cite F900/F901) · `rosetta_classification.ndjson` row (`composition_of_c` — composes native `klein4_bind`/`klein4_bundle`) · the **five** `describe()["tools"]["total"]` count-tests (318 → **319**) · `mcp/_coercion.py` coercer for the `list[HV]`/parts param + a sample in `test_mcp.py` (the rc155 lesson — run the FULL `test_mcp.py` locally before pushing).
- **Tests:** a scale-invariance ratchet (the F900 byte→word→skeleton→sentence 1-part-change band) · the byte/glyph-vs-wordhash morphology contrast (cat/cot 0.56 vs 0.25) · `enc_mode` round-trip (both modes deterministic + attested) · `scale_signature` monotonicity. All numpy-absent (the no-numpy-test discipline).
- **No `abs()`** (Class-K sign-branch); **no numpy / no stdlib math** in the new source.
- **CHANGELOG** entry + **TestPyPI numpy-absent verify** (version / `HAS_NATIVE` / ABI 3 / a real `klein4_compose` call + an `enc_mode="byteglyph"` learn/infer) before any graduation.

## 4. Behavior-change discipline (the reviewer caveat #2)

`enc_mode="byteglyph"` as the **default** changes the shipped `RBSLMInferenceSubstrate` numerics (word-hash → byte-compose) for every existing consumer — the same class of change as the rc16 `hypercomplex_couple` numerics flip. Therefore:
- ship C1 **behind `enc_mode=`** (byte/glyph default, word-hash retained) so any consumer can pin the old behaviour;
- **re-validate the consumers**: Siona `test_page_grid.py` + the F879–F898 route/chunk/stream probes against `enc_mode="byteglyph"` (and confirm `"wordhash"` reproduces the prior bytes);
- **cut the rc against current head** (`0.9.0rc16`+ on `main`) and re-verify the four F916 surfaces there (this spec verified them on rc13-era source; `klein4_*` / `cd_mult` / `sedenion_register` / `RBSLMInferenceSubstrate` are stable through rc16, but the rc must re-confirm).

## 5. What this delivers

`RBSLMInferenceSubstrate.learn`/`.infer` run on the **byte/glyph LM object** natively (C1 substrate), the ladder is **one scale-invariant compositor** end to end (byte→glyph→word→skeleton→sentence), the word-hash dual survives as a fast atom-mode, and `scale_signature` makes the fractal self-similarity (= coherence) introspectable. The bond/address/resonator layers stay as F916 specs them — with the **bond as a key, not a grammar** (§0). Logged to UPSTREAM_NOTES §70.
