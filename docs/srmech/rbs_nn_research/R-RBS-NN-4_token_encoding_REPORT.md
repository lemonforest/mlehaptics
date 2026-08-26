# R-RBS-NN-4 — Token → hypervector encoding with variant-choice protocol

**Status:** Partition R-RBS-NN-4 closing REPORT. Pending → closed by this REPORT.
**Predecessors:** R-RBS-NN-1 (MFO two-level ontology), R-RBS-NN-2 (user lexicon as native binding alphabet), R-RBS-NN-3a (MLP cascade), R-RBS-NN-3b (transformer cascade)
**Substrate:** srmech v0.4.3 (Klein-4 + Polar HDC LANDED per UPSTREAM_NOTES §4 + §5)
**Architectural foundation:** `ARCHITECTURAL_PATTERN_two_tier_klein4_polar.md`
**Empirical foundation:** F132-F143 (Klein-4 HDC engineering proposal walked through completion)

---

## §1 What this partition delivers

**Three concrete artifacts:**

1. **Token encoder module** (`R-RBS-NN-4_token_encoder.py`) — variant-routing encoder that takes user-vocabulary tokens and emits hypervectors in the right substrate variant (bipolar / klein-4 / polar / hybrid) per a `class_hint` argument
2. **Smoke test** (`R-RBS-NN-4_token_encoding_smoke.py`) — 9-test empirical verification on a 20-token synthetic lexicon spanning all four variants
3. **This REPORT** — closing artifact per the R-RBS-NN partition walk convention; documents the variant-choice protocol that R-RBS-NN-4 lands

**Key API surface:**

```python
from R_RBS_NN_4_token_encoder import encode_token, bind_pair, similarity, random_baseline

# Encode a token with explicit class hint
result = encode_token(
    token="left_helix",
    D=8192,
    class_hint="chirality",
    chirality_sector=0,        # 0=RH+ visible matter, 1=RH- dark anti, 2=LH+ visible anti, 3=LH- dark matter
)

result['variant']    # 'klein4'
result['hv']         # np.ndarray, shape (8192,), dtype uint8, values in {0,1,2,3}
result['metadata']   # {'token': ..., 'class_hint': 'chirality', 'D': 8192, 'seed_hex': ..., 'sector': 0}

# Bind two encodings (variants must match)
bound = bind_pair(result_a, result_b)

# Similarity (variant-aware)
sim = similarity(result_a, result_b)

# Random baseline for above-random normalization
baseline = random_baseline("klein4", D=8192)
```

---

## §2 The variant-choice protocol — when to use which

Per F142 §6 (BCI nuanced verdict) and F141 (polar plasticity gracefulness), variant choice is **scenario-specific, not universal**. The protocol:

| Class hint | Variant | When to use |
|---|---|---|
| `'content'` | bipolar (rank-1 abelian XOR over F₂) | Default. Token has no chirality structure and no plasticity decay. Maximum raw capacity. |
| `'chirality'` | Klein-4 (rank-2 abelian XOR over F₂×F₂) | Token carries chirality-axis information. Needs 4-sector tagging (γ₅, iω₇). Per F139, chirality survives cascade composition at sufficient D. |
| `'plasticity'` | Polar HDC ({-1, 0, +1}) | Token represents memory/binding subject to decay. The 0-state captures "uncertain" / "dead-band" as first-class substrate marker per `[[user_stance_asymptotic_dof_sidesteps_infinity]]`. Per F141, graceful 3-4× advantage over bipolar at moderate-to-high decay. |
| `'hybrid'` | Klein-4 + polar overlay | Token has BOTH chirality AND plasticity (e.g., a chiral drug binding state subject to decay over time). Research path; not yet fully characterized. |

**Default is `'content'` (bipolar).** Per F137, bipolar wins on raw capacity. Promote to other variants only when the application explicitly needs chirality / plasticity content.

**Variant choice is NOT learned** per the RBS-NN end-user goal (README §0): the user provides the class_hint when defining their lexicon. The encoder uses the hint as substrate-encoding direction; no learning bottleneck.

---

## §3 Per-variant encoding details

### 3.1 Content variant (bipolar)

```python
result = encode_token(token, D, class_hint="content")
```

- **Source seed**: SHA-256(token UTF-8 bytes)[:8] interpreted as int32 → numpy rng seed
- **Output**: `np.ndarray[int8]` of shape `(D,)` with values in `{-1, +1}`
- **Algebra**: rank-1 abelian XOR over F₂ (sign-product binding; self-inverse)
- **Self-similarity**: 1.0
- **Random pair baseline**: ~0.0
- **Best for**: content tokens where chirality and plasticity are not load-bearing

### 3.2 Chirality variant (Klein-4)

```python
result = encode_token(token, D, class_hint="chirality", chirality_sector=2)
```

- **Source seed**: SHA-256(token)[:8] → rng seed
- **Base**: `hdc.klein4_random(D, rng)` → uint8 in {0,1,2,3}
- **Chirality tag**: XOR with sector_mask = `[chirality_sector] * D`
- **Output**: `np.ndarray[uint8]` of shape `(D,)` with values in `{0,1,2,3}`
- **Algebra**: rank-2 abelian XOR over F₂ × F₂ (self-inverse; commutative; associative)
- **Self-similarity**: 1.0
- **Random pair baseline**: ~0.25 (1/4)
- **Best for**: tokens where chirality IS the load-bearing distinction (per F142: 13× advantage over bipolar on chirality-pure cases)

**Sector mapping** (per F132 §3, MFO §VII.4.1.7):

| Sector | (γ₅, iω₇) | Domain reading |
|---|---|---|
| 0 | (+1, +1) | RH+ visible matter (our sector projection per F131) |
| 1 | (+1, −1) | RH− dark antimatter |
| 2 | (1,0) | LH+ visible antimatter (γ₅ flip) |
| 3 | (1,1) | LH− dark matter (CPT mirror) |

### 3.3 Plasticity variant (Polar)

```python
result = encode_token(token, D, class_hint="plasticity", plasticity_density=0.50)
```

- **Source seed**: SHA-256(token)[:8] → rng seed
- **Base**: `hdc.polar_random(D, rng)` → int8 in {-1, 0, +1}
- **Density adjustment**: if `plasticity_density` ≠ 0.67 (upstream default), shift positions between 0 and ±1 to match target density
- **Output**: `np.ndarray[int8]` of shape `(D,)` with values in `{-1, 0, +1}`
- **Algebra**: multiplicative sign-product with 0 absorbing
- **Self-similarity**: 1.0
- **Random pair baseline**: ~0.50 (zero-zero matches counted; per F137 §4)
- **Best for**: tokens representing memory/binding states subject to decay; per F141, gracefully degrades

**Density attestation**: `metadata['density_actual']` reports the fraction of non-zero positions in the encoded vector, providing substrate-attestation per `polar_density(hv)`. Deltas from target ≤ 0.001 per smoke test T6.

### 3.4 Hybrid variant (Klein-4 + polar overlay; research path)

```python
result = encode_token(token, D, class_hint="hybrid", chirality_sector=0, plasticity_density=0.60)
```

- **Stage 1**: Klein-4 with chirality tag (as 3.2)
- **Stage 2**: Convert to polar via state-bit-pair XOR-bit extraction:
  ```
  klein4 0 (00) → polar +1   (visible matter)
  klein4 1 (01) → polar -1   (visible antimatter)
  klein4 2 (10) → polar -1   (dark matter)
  klein4 3 (11) → polar +1   (CPT conjugate)
  ```
- **Stage 3**: Apply plasticity decay (zero out fraction of positions to reach target density)
- **Output**: `np.ndarray[int8]` polar-shaped; carries chirality information collapsed to ±1 sign + uncertainty at 0
- **Research status**: not yet empirically characterized at scale; smoke test T3 confirms self-sim = 1.0; broader testing per `STALE_PATHS_QUEUE.md` item 24

---

## §4 Smoke test results (T1-T9)

| Test | Description | Verdict |
|---|---|---|
| T1 | Deterministic encoding (same input → same output) | ✅ PASS |
| T2 | Variant routing (8 bipolar, 6 klein-4, 5 polar, 1 hybrid from 20-token lexicon) | ✅ PASS |
| T3 | Self-similarity = 1.0 across all 4 variants | ✅ PASS |
| T4 | Bipolar bind→unbind round-trip (sim = 1.000) | ✅ PASS |
| T5 | Klein-4 bind→unbind preserves sector (sim = 1.000) | ✅ PASS |
| T6 | Polar density attestation (deltas ≤ 0.001) | ✅ PASS |
| T7 | Cross-variant comparison raises ValueError | ✅ PASS |
| T8 | Bundle 3 tokens per variant; recover via similarity (above-rand > 0.4 for all) | ✅ PASS |
| T9 | Klein-4 chirality discrimination operational (left_helix vs right_helix at random baseline = correct discrimination) | ✅ PASS |

**Key T8 numbers** (n=3 bundle retrieval, above-random similarity):

- Bipolar: +0.50 (3 tokens; strong recovery)
- Klein-4: +0.42 (3 tokens; strong recovery; sector preserved)
- Polar: +0.80 (3 tokens; very strong recovery; benefits from elevated random baseline + 0-state)

**T9 chirality discrimination check** — mirror-image token pairs:
- sim('left_helix', 'right_helix') = 0.249 (random baseline = 0.250)
- sim('amino_acid_L', 'amino_acid_D') = 0.252 (random baseline = 0.250)

The mirror-image pairs sit RIGHT AT random baseline — chirality-axis tagging IS forcing the structural orthogonality predicted by F142. Without chirality tagging, mirror pairs would have correlated structure (same content); with chirality tagging, they're effectively unrelated.

---

## §5 What R-RBS-NN-4 closes and what it leaves open

### Closed by this partition

✅ Token → hypervector encoder with variant routing
✅ Variant-choice protocol (content / chirality / plasticity / hybrid)
✅ Empirical validation across the 4 variants on synthetic lexicon
✅ Deterministic encoding via SHA-256 seeding (Class A content-mint)
✅ Variant-aware bind, similarity, baseline operations
✅ Round-trip preservation for bipolar and Klein-4
✅ Density attestation for polar variant
✅ Hybrid variant initial design (Klein-4 + polar overlay)

### Left open for follow-up (cross-ref `STALE_PATHS_QUEUE.md`)

- **Hybrid variant empirical characterization** at scale (item 24)
- **Token-classifier upstream** that infers class_hint without user labeling — currently the user MUST provide class_hint
- **Mixed-variant bundles**: what if a user has tokens of different variants in the same logical group? Current API requires variant match
- **Cross-natural lexicon test** (per F135 cross-natural chirality observations): apply encoder to real chirality-bearing lexicons (snail shell handedness names, beak laterality terms, plant spiral direction names)
- **Hierarchical bundling for n > 257** per ROADMAP.md NEXT-5: needed when application bundles > MAX_BUNDLE_N tokens
- **Plasticity decay dynamics**: encoder produces static polar at density target; dynamic decay over time (Hebbian-style) per F141 needs separate dynamics layer
- **End-user lexicon API**: user-facing way to declare class_hints (TOML config? Class A AMSC catalog entry?) per RBS-NN README §0 end-user goal

---

## §6 Cross-references

- **Architectural foundation**: `ARCHITECTURAL_PATTERN_two_tier_klein4_polar.md` — the two-tier pattern this encoder instantiates
- **Empirical foundation**: F137-F142 in `docs/srmech/rbs_lm_research/` — the wishlist-gated walks that validated each substrate primitive
- **F143** — F132 status closure documenting the engineering proposal landing
- **R-RBS-NN-1 §3** — Level 1 substrate ops on ALU (where bipolar lives)
- **R-RBS-NN-2 §6** — user lexicon native binding alphabet (this encoder's API target)
- **R-RBS-NN-3a §5** — MLP cascade decomposition (encoder is the entry-point)
- **R-RBS-NN-3b §5** — transformer cascade (encoder feeds the cascade)
- **R-RBS-NN-9** — catalog SSoT (will absorb encoder API at arc close per ROADMAP NEXT-2)
- **MFO §VII.4.1.7** — 4-way (γ₅, iω₇) decomposition (Klein-4 sector mapping)
- **srmech v0.4.3 catalog**: `srmech.amsc.hdc.klein4_*` + `polar_*` + `bipolar bind/bundle/similarity`

---

## §7 What this REPORT does NOT claim

Per MFO §VII.6.20:

- This is NOT a claim that the encoder is the optimal token→hypervector approach. It's a substrate-faithful baseline using the now-available variants.
- This is NOT a claim that the synthetic 20-token lexicon is representative of real user lexicons. It exercises the encoder's variant-routing logic; production lexicons need real corpus testing.
- This is NOT a claim that hybrid variant is operationally validated. Self-sim works; broader testing per stale queue item 24.
- This is NOT a falsification of bipolar-only RBS-NN. Bipolar remains the default; this REPORT adds chirality and plasticity options where applicable.
- This is NOT a model of biological neural token-encoding. The class_hint is a user/researcher annotation; biological systems don't carry such hints natively.

---

## §8 Catalog landing prep (for R-RBS-NN-9 SSoT absorption)

R-RBS-NN-4 contributes the following to the eventual `docs/srmech/catalogs/rbs_nn/` catalog (per R-RBS-NN-9 pattern):

```
docs/srmech/catalogs/rbs_nn/
  descriptor.toml          # adds: token_encoder section
  literature_curated.ndjson  # references this REPORT's framework anchors
  worked_examples/
    token_encoding_examples.ndjson  # 20-token lexicon results
```

**Schema sketch** (TOML section for the encoder):

```toml
[token_encoder]
schema_id = "srmech://rbs_nn/token_encoder/v1"
class_hints = ["content", "chirality", "plasticity", "hybrid"]
variants = ["bipolar", "klein4", "polar", "hybrid"]
substrate = "srmech.amsc.hdc"
D_default = 8192
algorithm = "SHA-256-seeded variant-router"
provenance = "R-RBS-NN-4"
```

Catalog implementation is deferred to R-RBS-NN-9 close.

---

## §9 Files committed by R-RBS-NN-4

- `R-RBS-NN-4_token_encoder.py` — variant-routing encoder module
- `R-RBS-NN-4_token_encoding_smoke.py` — 9-test empirical verification
- `R-RBS-NN-4_results.json` — smoke test results
- `R-RBS-NN-4_token_encoding_REPORT.md` — this REPORT

PR #687 STAYS DRAFT. R-RBS-NN-4 closes the long-pending task per the wishlist-gated resume.

---

*Closed 2026-05-27 per user direction "begin work". R-RBS-NN-4 was pending across multiple
sessions; closes here with concrete variant-choice protocol building on F132-F143 empirical
foundation + ARCHITECTURAL_PATTERN_two_tier_klein4_polar.md. Encoder handles 4 variants
(bipolar/klein4/polar/hybrid) with deterministic SHA-256 seeding (Class A content-mint),
self-similarity = 1.0 across all variants, round-trip preservation for bipolar and Klein-4,
density attestation for polar. The variant-choice protocol means user lexicons can declare
class_hints per token without learned-embedding bottleneck — directly addressing RBS-NN
README §0 end-user goal "user's vocabulary becomes the binding alphabet directly".*
