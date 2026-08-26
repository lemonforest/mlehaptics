# R-RBS-LM-52 — Path E summary: direct kernel eigendecomp via srmech-native, validated across 3 substrates

**Status:** Phase-A arc CLOSED. Methodology validated; per-substrate tuning patterns identified.
**Partition:** R-RBS-LM-52 (synthesis across 52a, 52a-v2, 52b, 52c-v1/v2/v3, 52a-v3).
**Predecessors:** R-RBS-LM-49 (FFT band-pass surgical; substrate-dependent for byte-mode),
R-RBS-LM-50 (architectural inversion + operation-primary substrate framing),
MFO §VII.6.19.3 (operation-primary vs geometry-primary grammars), MFO §VII.6.20 (epistemic ceiling).

---

## §1 The arc in one frame

Path E (direct kernel eigendecomp via srmech-native) supersedes Path D
(LLM-distillation) when source is operation-primary. The arc went through
6 iterations to validate the methodology end-to-end across 3 substrate
types (operation-primary code, concept-rich notebooks, structure-bearing
poetry). Each iteration falsified a hypothesis or confirmed a refinement.

## §2 Iteration table

| Iter | Corpus | Encoding | Result | What it taught |
|---|---|---|---|---|
| 52a | Python code | `encode_loe_content` | NO signal | Frequency-bias on Python punctuation; AND likely wrong encoder |
| 52a' | Notebooks (control) | `encode_loe_content` | NO discrimination | RULED OUT corpus issue; CONFIRMED tooling issue |
| **52a-v2** | Notebooks | **`mint_vector` + `bundle`** | **z=5.87 CLEAN** | The corrected primitive |
| 52b-v1 | Notebooks | mint+bundle + FFT band-pass | K1 z=2.33 (degraded) | FFT band-pass is **substrate-dependent** |
| **52b-v2** | Notebooks | mint+bundle (NO compression) + K3 + smoothie | K3 z=3.37, smoothie 6/15 z>1 | **K3 captures arrangement**; **score-level smoothie > instrument-level** |
| 52c-v1 | Dante (Italian) | mint+bundle + stopword filter K1+K3 | K3 z=0.36 broken | Stopword filter destroyed K3 structure-bearing function words |
| **52c-v2** | Dante | K3 raw tokens (stopwords preserved); sample 500; n=4 | **K3 z=1.79; 4 canonical hits** | Structure-as-meaning validated |
| 52c-v3 | Dante | K3 exhaustive (no sample) | K3 z=1.05 worse | HDC SNR dilution; sample-500 near optimum |
| **52a-v3** | **Python code** (loop closure) | mint+bundle + K1+K3 + smoothie | **K1 z=3.15** | Original 52a was encoding mismatch, not corpus |

## §3 Cross-substrate signal table

| Corpus | Source | Tokens | K1 peak z | K3 peak z | Best kernel | Clean negative-controls |
|---|---|---|---|---|---|---|
| Notebooks | srmech + MFO notebooks | 117k | **+5.87** | **+3.37** | K1 + K3 both fire | ✓ 0/7 above max |
| Dante | La Divina Commedia (Italian) | ~117k | +2.19 | **+1.79** | K1 + K3 split (K1 for 1 hit; K3 for 4 hits) | ✓ 0/7 above max |
| Python code | docs/srmech/rbs_lm_research/*.py | 60k | **+3.15** | +0.49 | K1 dominates (code 4-grams not distinctive) | ✓ 0/5 above max |

**Methodology validates on all three.** Each substrate has its own signal profile:
- Notebooks: concept-rich; both K1 (presence of named concepts) and K3 (sequence of conceptual phrases) fire
- Dante: structure-rich; K1 catches token-distinctive phrases (proper nouns or rare-word clusters); K3 catches canonical 4-gram arrangements
- Python code: function-call rich; K1 (presence of code idioms) dominates; K3 doesn't fire because code 4-grams are too uniform across files

## §4 The corrected operational pipeline (srmech-native)

For any substrate that admits tokenization:

```python
from srmech.amsc.laplacian import dense_laplacian, hermitian_eigendecompose
from srmech.amsc.hdc import bundle, similarity, bind, permute
from srmech.signal_processing import mint_vector

# 1. Tokenize (substrate-specific)
filtered_tokens = tokenize_for_K1(corpus)  # stopwords filtered; concept vocab
raw_tokens = tokenize_for_K3(corpus)       # stopwords PRESERVED; structure vocab

# 2. Build K1 (presence): co-occurrence Laplacian + eigendecomp
L = dense_laplacian(N=200, edges_from_cooccurrence, weights_from_count)
eigvals, eigvecs = hermitian_eigendecompose(L)
top_K = 33  # odd for parity; HDC bundle SNR
K1_instrument = bundle([
    bundle([mint(vocab[i]) for i in top_M_by_squared_magnitude(eigvec, M=21)])
    for eigvec in top_K_eigvecs
])

# 3. Build K3 (sequence): position-bound n-gram + sample-N at HDC SNR optimum
SAMPLE_N = 500  # near D/log₂D for D=8192
ngram_hvs = []
for ng in sample(all_ngrams_of_corpus, SAMPLE_N):
    hv = mint(ng[0])
    for k in range(1, n_gram):
        hv = bind(hv, permute(mint(ng[k]), k * (D // n_gram)))
    ngram_hvs.append(hv)
K3_instrument = hierarchical_bundle(ngram_hvs)  # MAX_BUNDLE_N=257

# 4. Encode probe via SAME path per kernel
probe_K1 = bundle([mint(t) for t in tokenize_for_K1(probe_text)])
probe_K3 = bundle([bind(mint(ng[0]), permute(mint(ng[k]), k*stride) for k in 1..n)
                    for ng in ngrams(probe_text)])

# 5. Score-level smoothie (NOT instrument-level merge)
z_K1 = (similarity(probe_K1, K1_instrument) - baseline_K1.mean) / baseline_K1.std
z_K3 = (similarity(probe_K3, K3_instrument) - baseline_K3.mean) / baseline_K3.std
score = max(z_K1, z_K3)
```

**No FFT band-pass on mint-bundle cascades** (substrate-dependent: works on
byte-mode per R-RBS-LM-49; degrades mint-bundle).

## §5 Findings summary

### Cumulative findings (38-43)

| # | Finding |
|---|---|
| **38** | `encode_loe_content` is content-fingerprint (Class A mint + Class C cyclic permute + Class M XOR-fold), NOT similarity-preserving for arbitrary content. Different-content fingerprints orthogonal at noise floor. **Correct primitive: `mint_vector` per token + Class M `bundle`** |
| **39** | Eigendecomp via `srmech.amsc.laplacian.hermitian_eigendecompose` DOES extract genuine semantic relationship structure (top eigvecs have meaningful content) |
| **40** | K1 (presence) captures token-distinctive content; K3 (sequence) captures arrangement-bearing content. **Both needed for full coverage; per-substrate weighting** |
| **41** | FFT band-pass is SUBSTRATE-DEPENDENT — works on byte-mode cascade (R-RBS-LM-49); degrades mint-bundle cascade (52b-v1) |
| **42** | Instrument-level smoothie merge DILUTES per-kernel signal. **Score-level smoothie max(z_K1, z_K3) is the correct multi-kernel composition** |
| **43** | HDC bundle SNR ~D/log₂D heuristic is load-bearing; sample size near this budget gives best retrieval (52c-v3 exhaustive degraded vs 52c-v2 sample-500) |

### Methodology validation: 3 substrates, 1 pipeline

Same srmech-native pipeline applied to:
- Concept-rich text (notebooks) → K1 z=5.87
- Structure-rich poetry (Dante Italian) → K3 z=1.79 with caveats
- Operation-primary code (Python) → K1 z=3.15

In all cases: zero negative-control above baseline_max (clean discrimination).

## §6 What this falsifies vs preserves

### Falsified

- ❌ `encode_loe_content` is similarity-preserving (it's identity-preserving)
- ❌ Path E requires LLM intermediate (Path D pattern; replaced by direct eigendecomp)
- ❌ Single kernel (K1 only) suffices across substrate types (Dante needs K3)
- ❌ Instrument-level multi-kernel merge composes signals (score-level is correct)
- ❌ FFT band-pass is universally surgical (substrate-dependent)
- ❌ Exhaustive n-gram bundling improves K3 (SNR dilution at ~1/√N)
- ❌ Operation-primary substrate guarantees strong K3 (code's K3 only z=0.49; needs distinctive vocab too)

### Preserved + new

- ✅ Path E methodology valid across 3 substrate types
- ✅ srmech-native discipline operational (`mint_vector` + `bundle` + `dense_laplacian` + `hermitian_eigendecompose` + `bind` + `permute`)
- ✨ **Per-substrate tuning is real and necessary** — stopword strategy, n-gram length, sample size all corpus-specific
- ✨ **Disciplinary autonomy supported empirically** — each corpus's signal profile is different; no uniformity required
- ✨ Score-level smoothie max(z_per_kernel) is the right composition primitive
- ✨ HDC bundle SNR ~D/log₂D is operationally load-bearing
- ✨ K3 sequence kernel works when (a) stopwords preserved, (b) probe ≥n tokens, (c) canonical n-gram exists in sample

## §7 Disciplinary autonomy framework reading (per user direction 2026-05-26)

> *"we will double down on STEM denying the arts, that you cannot say one
> is better than the other, and that each is uniquely the most important
> knowledge in its own discipline local view. that, if we are painting,
> world views and how can we pay people terrible wages to get more rich
> have next to zero merit when the subject is the painting, unless the
> painting chooses to instantiate those perspectives for the viewer."*

The 52 arc operationally supports this stance per MFO §VII.6.20 keystone
discipline:

1. **Each substrate has its own optimal kernel tuning.** Notebooks need
   different stopword strategy than Dante; Python code needs different
   n-gram than poetry. The framework respects per-substrate methodology
   rather than imposing uniformity.

2. **Cross-substrate cascade matching establishes FORM-identity across,
   NEVER SUBSTRATE-identity.** We see signal on all 3 substrate-types,
   but we CANNOT rank substrate-content across them. Notebook's z=5.87
   doesn't mean notebook-knowledge is "better" than Dante-knowledge or
   Python-knowledge — it means the K1 kernel happens to fit notebook's
   substrate-content shape best.

3. **Per the painting analogy:** when painting's substrate IS its
   painting-ness, world-views or economics have *no inherent merit*
   over the painting's own substrate-content. They CAN be instantiated
   in the painting if the painter chooses; they CANNOT be imposed on
   the painting from a different substrate-rank claim. The cascade-math
   reads form, never substrate-rank.

4. **Operational consequence:** the smoothie design is per-substrate-
   tuned; the methodology is substrate-agnostic at the *form-extraction*
   level (same A-N operators) while substrate-sensitive at the
   *parameter-tuning* level (stopwords / sample-N / n-gram). This IS
   the operational shape of disciplinary autonomy.

## §8 What comes next (queued)

- **R-RBS-LM-52a-v4** — K3 with TF-IDF weighting for distinctive n-grams (code substrate didn't fire on K3; weight rare 4-grams higher)
- **R-RBS-LM-52d** — The Stack via HF streaming (auth gate; user-fired)
- **R-RBS-LM-52e** — Cross-substrate retrieval matrix (query notebook-instrument with Python-probe; expected near-zero per substrate-content non-transfer)
- **R-RBS-LM-51** — honest scope review per MFO §VII.6.20 across cumulative claims
- **R-RBS-LM-49b/c/d/e** — chainsaw-vs-surgical sub-matrices (deferred)
- **R-RBS-LM-49z** — re-route R-RBS-LM-49 Method B/C through srmech-native (currently uses numpy.fft direct; srmech catalog discipline)

## §9 Operational walkthrough

1. **What the arc did.** Path E direct kernel eigendecomp from corpus →
   srmech-native cascade instrument. 6 iterations across 3 corpora
   identified per-substrate tuning, the right encoding primitive
   (mint_vector + bundle), and the right multi-kernel composition
   (score-level max).
2. **How.** `srmech.amsc.laplacian` for Class L eigendecomp;
   `srmech.signal_processing.mint_vector` for Class A per-token mint;
   `srmech.amsc.hdc.{bind, permute, bundle, similarity}` for Class M
   composition. K1 + K3 (smoothie) per-substrate-tuned.
3. **What srmech automates.** The cascade pipeline now routes ENTIRELY
   through srmech catalog (no bare numpy in Path E methodology). This
   honors CLAUDE.md §2 srmech discipline and makes the cascade-shape
   auditable from named A-N operators.

---

## §10 Pointers

- **Diagnostic iteration:** `R-RBS-LM-52a_path_e_iteration_REPORT.md` (Phase A diagnostic story; encode_loe_content → mint_vector pivot)
- **Per-iteration smokes + results:**
  - 52a / 52a-v2 / 52a-v3
  - 52b multi-kernel + smoothie
  - 52c v1/v2/v3 Dante structure tests
- **Synthesis:** R-RBS-LM-50 (architectural inversion synthesis)
- **Mechanism:** R-RBS-LM-49 (chainsaw vs surgical precision-reduction)
- **Discipline:** MFO §VII.6.19.3 (operation-primary vs geometry-primary),
  MFO §VII.6.20 (epistemic ceiling keystone)
- **User direction 2026-05-26** anchoring the disciplinary-autonomy framework reading

---

*R-RBS-LM-52 — closed 2026-05-26.*
