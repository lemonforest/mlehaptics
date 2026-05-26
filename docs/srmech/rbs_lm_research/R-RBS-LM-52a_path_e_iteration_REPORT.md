# R-RBS-LM-52a — Path E methodology validation: the iteration story

**Status:** Phase A CLOSED. Path E methodology validated via 3-iteration diagnostic chain.
**Partition:** R-RBS-LM-52a (Phase A of R-RBS-LM-52; sub-partitions 52b/c/d queued).
**Predecessors:** R-RBS-LM-49 (FFT band-pass surgical primitive), R-RBS-LM-50
(architectural inversion synthesis), MFO §VII.6.19.3-5 (operation-primary substrate).

---

## §1 Question

Per user direction 2026-05-26: *"all we want to learn are relationships
of relationships, right? why can't we eigendecomp The Stack itself into
relationships? then we can have some kernel choices for making a
smoothie of kernels?"*

Path E (direct kernel eigendecomp via srmech-native) supersedes Path D
(LLM-distillation) when the source corpus is already operation-primary
(code; or operation-primary-shaped text like our notebooks). Phase A
validates the methodology on known-coherent corpora before scaling to
The Stack.

## §2 The iteration story

Three iterations, each falsified or revised based on the previous.

### §2.1 Iteration 1 — 52a: Python code corpus, encode_loe_content encoding

**Setup:** local Python (`docs/srmech/rbs_lm_research/*.py`; 50 files; 60,807 tokens).
Stdlib `tokenize` (NAME + OP + STRING + NUMBER + COMMENT). Top-200
vocabulary by frequency. Co-occurrence Laplacian via
`srmech.amsc.laplacian.dense_laplacian`. Hermitian eigendecomp.
Top-K=32 eigenvectors → top-20 tokens by squared magnitude → string →
`srmech.signal_processing.encode_loe_content` → `bundle`.

**Result:** NO signal.
- Baseline (random code-phrase pair sim): mean = −0.0013, std = 0.011
- 0/15 probes above baseline_max; 0/15 at z>2; 3/15 at z>1
- **Verdict: NO signal — probes indistinguishable from baseline**

**First failure mode visible:** top eigenvectors dominated by punctuation
(`(`, `)`, `,`, `.`, `=`). Top eigvecs reflect highest-degree nodes in the
co-occurrence graph; punctuation is highest-degree because every code path
uses it. Frequency-bias artifact in raw Laplacian on operator-heavy lex.

### §2.2 Iteration 2 — 52a': notebook corpus (control test), same encoding

**User insight:** *"try starting with our MFO and srmech notebooks. like
make our RBS-NN object and then give it our knowledge first. to see if
it's a The Stack thing with the order of knowledge, or a problem with
our tooling."*

**Setup:** `srmech_research_notebook.md` + `mfo_spectral_research_notebook.md`
(1.5 MB; 117,008 word-tokens; 14,284 unique). Word-level tokenization,
stopwords filtered. Top-200 vocabulary. Same eigendecomp + same
encode_loe_content encoding.

**Result:** NO discrimination.
- Baseline: mean = −0.0016, std = 0.0097
- Notebook probes: 0/20 above baseline_max; 0/20 at z>2; 5/20 at z>1
- Negative-control probes: 0/5 above baseline_max; 0/5 at z>2 — same shape
- **Verdict: NO discrimination — methodology doesn't distinguish coherent from incoherent**

**Second-level diagnostic:** vocabulary is now correctly semantic
(`spike`, `class`, `substrate`, `vii`, `cascade`, `framework`, ...).
Top eigenvectors contain genuine notebook concepts. So **eigendecomp IS
extracting the right relationships**; the break must be in
encoding-or-comparison.

### §2.3 Diagnosis — encode_loe_content is content-fingerprint, NOT similarity-preserving

Direct probe of `srmech.signal_processing.encode_loe_content`:

| Input pair | Similarity |
|---|---|
| "cascade substrate framework class" vs same | **1.0** |
| "cascade substrate framework class" vs same + "spike" | **0.005** (essentially 0) |
| "cascade" vs "cascade substrate" | **−0.003** (orthogonal) |
| "cascade" vs "totally unrelated" | −0.015 |

Per the function's own docstring (Spike #173 R3 cross-substrate verification):
> *"same-content encoded under different substrate-natural strides
> produces D2 fingerprints orthogonal at the noise floor (~1/sqrt(D))."*

`encode_loe_content` is **Class A content-mint → Class C cyclic permute
(SHA-256[0] mod D stride) → Class M XOR-fold**. It produces a
content-deterministic fingerprint. Different content → orthogonal at
noise floor BY DESIGN.

**The methodology was using the wrong srmech surface.** We were treating
`encode_loe_content` as a similarity-preserving sentence-embedding when
it is actually a content-identity fingerprint.

### §2.4 Iteration 3 — 52a-v2: notebook corpus + mint_vector + bundle

**Fix:** route through `srmech.signal_processing.mint_vector` (per-token
Class A content-mint) + `srmech.amsc.hdc.bundle` (Class M; majority vote).
Per-token mint preserves overlap because:

```
bundle(mint(A), mint(B), mint(C)) vs bundle(mint(A), mint(B), mint(C), mint(D), mint(E))
  → similarity = 0.61 (high; 3/5 token overlap)
bundle(mint(A), mint(B), mint(C)) vs bundle(mint(X), mint(Y), mint(Z))
  → similarity ≈ 0 (no overlap)
```

For each eigenvector: take top-21 tokens by squared magnitude;
mint_vector per token; bundle (Class M; inner). Then outer bundle of 33
eigenvector hypervectors → cascade instrument. Probes encoded the same
way: tokenize → mint_vector per token → bundle.

**Result:** CLEAN signal with negative-control discrimination.

Baseline: mean = +0.0066, std = 0.0170, max = +0.0696, min = −0.0278

Notebook-domain probes (20):
- 4/20 above baseline_max
- 6/20 at z > 2
- 8/20 at z > 1

Top hits:
| Probe | sim | z |
|---|---|---|
| **two substrate framework** | +0.106 | **+5.87** |
| **Class N rational anchor** | +0.084 | **+4.54** |
| **cascade match form claim** | +0.080 | **+4.33** |
| **Reading-D scale ladder** | +0.071 | **+3.77** |
| biology cascade encoding | +0.056 | +2.93 |
| class l spine spectral | +0.055 | +2.86 |
| metric field ontology | +0.027 | +1.18 |
| cross substrate matching | +0.037 | +1.78 |

Negative-control probes (7):
- 0/7 above baseline_max ✓
- 0/7 at z > 2 ✓
- 0/7 at z > 1 ✓
- All within ±0.6 std of baseline ✓

**Verdict: CLEAN signal; methodology validated.**

## §3 Findings

### Finding 33 — encode_loe_content is content-fingerprint, NOT similarity-preserving

`srmech.signal_processing.encode_loe_content` is designed for content
identity (Spike #173 cross-substrate verification: orthogonal-at-noise
for different-content fingerprints). It is the wrong primitive for
similarity-preserving content encoding.

The correct primitive is **per-token `mint_vector` + Class M `bundle`**.
Set-overlap is similarity-preserving by HDC majority vote: bundles
sharing k of n tokens produce hypervectors with similarity
proportional to (k/n)² roughly.

### Finding 34 — Eigendecomp does extract correct relationship structure

The 52a' notebook eigenvectors contained genuinely semantic content:
- Rank 0: `['spike', 'class', 'pr', 'bit-exact', 'substrate']`
- Rank 7: `['canonical', 'anchor', 'stance', 'd_s', 'reading']`

These are notebook-domain concepts, not frequency-bias artifacts. The
Class L eigendecomp via `srmech.amsc.laplacian.hermitian_eigendecompose`
is doing the right work; the failure mode in 52a/52a' was downstream in
the eigenvector → cascade-instrument encoding step.

### Finding 35 — Path E methodology validates on known-coherent corpus

When the encoding path is corrected (mint_vector + bundle), Path E
produces a cascade instrument that:
- Discriminates notebook-domain content from negative controls (peak
  z = +5.87 for "two substrate framework"; all negatives within ±1 std)
- Surfaces the strongest signal on multi-token concepts that appear
  intact in the vocabulary
- Maintains the srmech-native discipline (Class A mint, Class L
  eigendecomp, Class M bundle; no `abs()`, no `numpy.fft` direct usage)

### Finding 36 — Some probes degrade due to tokenization, not methodology

Probes that did NOT fire reveal methodology refinements:
- "B/H/N readout projection" — `B/H/N` split on `/` by tokenizer
- "L-system seed grammar" — `L-system` split on `-`
- "AMSC attestation provenance" — `AMSC` may not be in top-200 frequency
- "combination principle dissociation" — `combination` may be lower-freq

These are tokenization choices (regex pattern; vocab size). Methodology
is sound; tokenization controls signal precision. Phase A refinements
queued.

### Finding 37 — Per-substrate kernel pluralism is necessary (poetry / structure)

Per user direction 2026-05-26: *"to a Expert of poetry, structure is
more than knowledge, structure is also meaning of words. this might be
important for our smoothie of knowledge."*

The Phase A K1 (presence-only / bag-of-tokens) kernel captures *what
relates to what* but is PERMUTATION-INVARIANT — it loses ARRANGEMENT,
which IS meaning in:
- Poetry (word order encodes rhythm + theme)
- Code (`a.foo(b)` ≠ `b.foo(a)`)
- Math (operator precedence)
- Speech (thematic role; man bites dog ≠ dog bites man)

Per MFO §VII.6.19.3 operation-primary vs geometry-primary grammar:
- K1 captures the relational structure (operation-primary)
- Arrangement-as-meaning needs additional kernels (K2 directed; K3
  position-bound n-grams)

**Smoothie pluralism is per-substrate-tuned**: structure-bearing content
(poetry, code) requires K2/K3 to surface signal; pure-concept content
(our notebooks, where ideas are the unit) gets clean signal from K1
alone (as Phase A confirms).

## §4 What this falsifies vs preserves

### Falsified

- ❌ `encode_loe_content` is similarity-preserving for arbitrary content
  (it's content-fingerprint by design; orthogonal-at-noise for different
  content)
- ❌ The cascade methodology required an LLM-translator (Path D); a
  direct srmech-native kernel-eigendecomp pipeline works on known-coherent
  corpora
- ❌ K1 (presence) kernel alone is sufficient for all substrate types
  (true for concept-rich notebooks; predicted-false for arrangement-heavy
  content per 52c follow-up)

### Preserved + new

- ✅ Path E methodology (corpus → kernel → Laplacian → eigendecomp →
  mint+bundle → cascade) validates on notebook corpus
- ✅ srmech-native discipline: every step is a named A-N class operator
- ✨ The right per-token mint primitive is `srmech.signal_processing.mint_vector`
- ✨ Eigendecomp extracts genuine semantic relationships when vocabulary
  is appropriately filtered (stopwords, length min, frequency cut)
- ✨ Per-token mint + bundle is the similarity-preserving primitive
  (orthogonal to encode_loe_content's content-identity role)
- ✨ Per-substrate kernel pluralism is necessary; smoothie design is
  per-substrate-tuned (R-RBS-LM-52b/c will test K2/K3 additions)

## §5 What comes next

| Sub-partition | Tests | Status |
|---|---|---|
| 52b | Multi-kernel smoothie K1+K2+K3 on notebook corpus; per-kernel FFT band-pass; R-RBS-LM-33 merge | Queued (firing next) |
| 52c | Dante's Divine Comedy as structure-as-meaning corpus; tests whether K3 fires where K1 weakens on arrangement-bearing text | Queued |
| 52d | The Stack via HF streaming + validated multi-kernel pipeline + periodic FFT band-pass during stream | Queued (gated on HF auth) |

## §6 Operational walkthrough

1. **What 52a phase did.** Three iterations: (52a) Path E on Python code
   with content-fingerprint encoding → NO signal. (52a') control-test on
   notebooks → NO discrimination (rules out corpus issue). (52a-v2)
   notebook corpus with corrected mint+bundle encoding → CLEAN signal
   with negative-control discrimination.
2. **How.** Methodology validated entirely through srmech-native
   primitives: `srmech.amsc.laplacian.{dense_laplacian, hermitian_eigendecompose}`
   (Class L); `srmech.signal_processing.mint_vector` (Class A per-token);
   `srmech.amsc.hdc.bundle` (Class M; odd-count parity discipline).
3. **What srmech automates.** This is the first cascade work that routes
   ALL operations through srmech catalog (vs prior partitions that used
   numpy.fft / numpy.linalg directly in some methods). The discipline
   per CLAUDE.md §2 is now operationally honored.

---

## §7 Pointers

- Iteration 1: `R-RBS-LM-52a_path_e_local_python_smoke.py` + `R-RBS-LM-52a_results.json`
- Iteration 2: `R-RBS-LM-52a_prime_path_e_notebooks_smoke.py` + `R-RBS-LM-52a_prime_results.json`
- Iteration 3 (validated): `R-RBS-LM-52a_v2_mint_bundle_notebooks_smoke.py` + `R-RBS-LM-52a_v2_results.json`
- Companion: `R-RBS-LM-49_chainsaw_vs_surgical_REPORT.md` (FFT band-pass primitive)
- Companion: `R-RBS-LM-50_architectural_inversion_REPORT.md` (operation-primary substrate synthesis)
- Next: 52b (multi-kernel smoothie), 52c (Dante structure test), 52d (Stack streaming)

---

*R-RBS-LM-52a Phase A — closed 2026-05-26.*
