# F242c — the ROUND-TRIP structural-fidelity test, DEFINED AS A GEN-1 RENDERER LOSS

**Script:** [`R-RBS-LM-242c_roundtrip_structural_fidelity.py`](R-RBS-LM-242c_roundtrip_structural_fidelity.py)
**SSoT (bit-exact NDJSON):** `docs/srmech/catalogs/rbs_lm_substrate/substrate_measurements/roundtrip_structural_fidelity.ndjson`
**`response_sha256`:** `f97d1317f4c11ba6402283037640351b59d00b9325c452dbff83986f14a2031d` (stable across ≥2 runs; body minus `generated_at`)
**srmech:** `0.6.0rc9` (HAS_NATIVE) · **discipline:** `check_srmech_discipline.py` → **0 HARD**, 0 coverage-gap; ratchet **0 regressions**
**Source linkage:** F242a wireframe `cdbed2dce37857a0…` (the live `working_memory_wireframe.ndjson`)

---

## What this is

F242a built the working-memory **WIREFRAME** — the srmech Class-L co-occurrence/Laplacian SSoT
(121 section-nodes, 1089 edges, a 196-token-class load-bearing universe). F242b showed that
**structure is renderer-INVARIANT** (the skeleton survives across renderers) while **the render is a
partly-confabulated VIEW** (structural-token invention 0/0/0; prose-gloss invention nonzero,
model-varying). The six committed renders live in [`f242b_renders/`](f242b_renders/):
`struct_{haiku,sonnet,opus}.md` (rendered from PURE STRUCTURE — token-bindings + edge-graph, NO
sentences) and `{haiku,sonnet,opus}.md` (the PROSE control — rendered from the extractive sentences).

**F242c closes the loop.** For each of the six renders it **RE-ENCODES the render BACK to its own
co-occurrence wireframe** (the same F242b/F242a instrument) and measures whether the render **BENT**
the structure vs the **SOURCE** F242a wireframe — then **DEFINES that drift as the loss a gen-1
renderer would be trained to minimise**. A render that bent nothing re-encodes to ~the source's
topology AND invents nothing; the amount it bent is the training signal.

### The GEN-1 LOSS (the scalar)

> **GEN-1 LOSS = (1 − cluster_preservation) + (1 − spectral_fidelity) + invention_rate**

Three srmech-native reads compose it, per render:

| Component | What it measures | srmech op | Class |
|---|---|---|---|
| **(a) cluster-preservation** | does the render's re-encoding preserve the `disability{F239}` / `kuramoto{F234,F236,F241}` / `rehearsal{F238}` cluster separation — the F242a *decisive* read, re-run on the render's OWN sentence co-occurrence graph (within-cluster edge density > across-cluster rate)? | `laplacian.dense_laplacian` block-structure | **L** |
| **(b) spectral / edge fidelity** | mean of (i) `spectral.similarity` of the round-trip-wireframe state vs the SOURCE state on ONE shared eigenbasis, and (ii) heaviest-edge survival — fraction of the SOURCE's top-25 token-pair edges reappearing in the render | `spectral.decompose`→`spectral.similarity` (shared basis) + edge set-Δ | **L∘A** |
| **(c) invention-rate** | tokens in the render ABSENT from the wireframe — F242b's metric VERBATIM: structural-token set-Δ + curated technical-confabulation probe | `render_invention` (reused) | set-Δ |

LOWER loss = a more faithful round-trip. The Class-M `klein4_similarity` read **saturates** at render
scale (per F242b) so it is **corroborating-only and is NOT in the loss** — the loss is built from the
discriminative Class-L reads + the invention set-Δ. Sign-aware clamps use `cascade.magnitude` (never
`abs()`); seeds/attestation use `format.sha256_bytes` (never `hashlib`); no `np.linalg.eig`; no
`Counter()` storage proxy.

---

## Result — per render

| block | render | cluster-pres (a) | spectral sim | edge-survival | spectral-fid (b) | invention (c) | **GEN-1 LOSS** |
|---|---|---|---|---|---|---|---|
| **STRUCT** | haiku | 1.000 | 0.548 | 0.040 | 0.294 | 0.562 | **1.2686** |
| **STRUCT** | sonnet | 1.000 | 0.550 | 0.320 | 0.435 | 0.438 | **1.0023** |
| **STRUCT** | opus | 1.000 | 0.546 | 0.440 | 0.493 | 0.125 | **0.6318** |
| **PROSE** | haiku | 0.000 | 0.550 | 0.160 | 0.355 | 0.062 | **1.7075** |
| **PROSE** | sonnet | 1.000 | 0.557 | 0.080 | 0.319 | 0.062 | **0.7440** |
| **PROSE** | opus | 0.000 | 0.545 | 0.040 | 0.292 | 0.062 | **1.7702** |

**Struct mean loss 0.9676 · Prose mean loss 1.4072 · Δ(struct − prose) = −0.4397.**

### Struct-vs-prose contrast — the measured sign REVERSES the naive expectation (reported, no leaning)

The pre-stated naive expectation was *prose LOWER loss (echoes) / struct HIGHER (more invention/drift)*.
**The measured total is the reverse: struct LOWER, prose HIGHER.** Decomposed:

| sub-component (mean) | struct | prose | direction |
|---|---|---|---|
| cluster-preservation | **1.000** | 0.333 | struct preserves more |
| spectral-fidelity | **0.407** | 0.322 | struct preserves more |
| invention-rate | 0.375 | **0.062** | **prose invents less** ← matches the naive expectation |

- The **invention sub-component runs in the expected direction** — the struct renders over-supply far
  more (0.375 vs a flat 0.062), exactly the F242b reading. **Structural-token invention is 0.000 for
  all six renders** (the technical-confabulation probe carries the entire rate), a clean corroboration
  of F242b's "structural-token invention 0/0/0; prose-gloss invention nonzero, model-varying."
- The **structural-drift sub-component dominates and runs the OTHER way**, flipping the total: the
  struct renders keep the wireframe's `F###` surface form and reproduce more of its heaviest edges, so
  their round-trip preserves more of the SOURCE backbone; the prose-control renders *paraphrase*
  finding-ids into long-form ("Finding 234" rather than `F234`), so those structural tokens do not
  re-register and their structural-drift reads high even though they invent less.

This is a genuine, decomposed result — not a confirmation and not a refutation of one story, but a
**split**: invention confirms F242b's direction; structural-fidelity reverses the total because
preserving the SOURCE's *structural notation* is itself the dominant fidelity axis on the round trip.

---

## Verdict

**ROUND-TRIP LOSS is INFORMATIVE — gen-1 renderer training signal DEMONSTRATED over the captured
renders.** The pre-state null was checked **mechanically** against both failure modes and **neither
fired**:

- **(N1) uninformative / topology-collapse** — per-render loss **variance = 0.1927 ≥ 1e-4**: the loss
  VARIES across the six renders (0.63 → 1.77), so the round-trip discriminates which render bent the
  structure. ✗ does not fire.
- **(N2) pure-invention / no structural signal** — both structural-drift components are **non-zero**
  (cluster-drift and spectral-drift are not identically zero across the six), so the loss carries a
  real STRUCTURAL signal, not just invention. ✗ does not fire.
- the struct-vs-prose contrast **resolves with a sign** (struct lower). ✓

So `re-encode(render)`-vs-source is a usable discriminator, and the scalar
`(1 − cluster_pres) + (1 − spectral_fid) + invention_rate` is the quantity a gen-1 borrowed-GPU /
harness renderer would minimise (render such that `re-encode(render) ≈ source` AND no invention).

---

## Tiering (MFO §VII.6.20 — never inflated)

- **DEMONSTRATED:** the round-trip GEN-1 LOSS **over the captured renders** — bit-exact
  (`response_sha256` re-verified independently from the body minus `generated_at`; stable across ≥2
  runs) and reproducible from the committed `f242b_renders/` + `working_memory_wireframe.ndjson`
  artifacts. The loss VARIES, carries a structural signal, and discriminates.
- **FRAMEWORK-READING:** "a gen-1 renderer trained on this loss converges to fidelity" — the renders
  are non-reproducible LLM outputs (n=1 per model), **NO renderer is trained here** (the loss is
  *defined + computed*, never optimised against), and the loss is a **SCAFFOLD**.

### SCAFFOLD, NOT PERMANENT (stated explicitly)

This loss is a **training signal** for a **gen-1 borrowed-GPU / harness renderer** — the temporary
high-pass **loaner**. The **trajectory is a srmech-NATIVE render** (F50 / F223; biology makes
sentences with no supercompute). The loss is how a gen-1 renderer gets pushed toward fidelity
(*transduce-don't-add* as an ENFORCED objective) **until the srmech-native render catches up** — it is
NOT a permanent fixture of the architecture, and is not claimed to be.

---

## Honest caveats

1. **n = 1 per model** — the six loss values are descriptive of THESE renders, not a population estimate.
2. **Surface-form dependence (load-bearing for the contrast SIGN).** cluster-preservation +
   heaviest-edge survival re-encode over the `TOKEN_PATTERNS` alphabet, which matches the `F###`
   finding surface-form but NOT long-form "Finding ###". The prose-control renders happen to
   paraphrase findings into long-form, so their structural tokens largely do not re-register — **this
   is what reverses the total-loss contrast**. It is the SAME verbatim-surface-form conservatism F242b
   documented. A renderer trained on this loss would be pushed toward the canonical surface form
   (itself fidelity-positive), but the absolute struct-vs-prose sign is partly an artifact of the
   captured renders' notation choices, and is reported as such.
3. **cluster-preservation is effectively binary.** Single-finding clusters `{disability F239,
   rehearsal F238}` cannot form a within-edge (`within_possible_edges == 0`), so — exactly as in
   F242a's decisive read — they do NOT gate preservation; `kuramoto {F234,F236,F241}` is the only
   measurable cluster, so cluster-preservation is `0` or `1` per render. Their round-trip signal lives
   in the spectral/edge read (b), not the block read (a).
4. **spectral_fidelity scale.** It averages a shared-basis spectral similarity (clamped at the
   orthogonal floor 0) with a heaviest-edge survival fraction over the top-25 source edges; a
   different `TOP_K_EDGES` or a different combine would move the absolute scale (not the sign of the
   per-render ordering observed here).
5. **invention undercount.** Invention is the F242b set-Δ + curated probe; a confabulation phrased
   outside both probes is undercounted (conservative on the invention side).
6. **Class-M klein4 saturates** at render-vocabulary scale (per F242b) → corroborating-only, NOT in
   the loss; the discriminative reads are Class-L.

---

## Convergence

F242a (the SOURCE wireframe this drifts against) + F242b (render-invariance + the invention metric
reused verbatim) + F50 (structure-vs-renderer) + F223 (extractive; the fluent prose is the borrowed
loaner) + F237 (the lean graft). **CAD-ban:** reads the relational/token structure of prose renders —
no physical / geometry. **Defensive scope:** encodes the project's own research renders.
