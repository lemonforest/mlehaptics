# Finding 199 — Strong-invariance test (12 within-source vs 54 across-source translation pairs): NO srmech-native storage signature is systematically translation-invariant; F171's n=1 lean does not survive a real distribution; F172's flat-spectral ceiling is re-confirmed at scale — clean NULL (outcome b)

**Status:** The strong (multi-pair) version of the F169 core. Turns F171's n=1 lean into a measured within-vs-across DISTRIBUTION (3 multi-translation clusters, 12 within-pairs, 54 across-pairs). Result is a clean NULL: no content-specific storage signature separates within-source from across-source. Strengthens F172; the n=1 positive lean of F171 was within-noise.
**Predecessors:** F171 (FIRST evidence, n=1 Quran pair, leaned positive on continuous profile-shape), F172 (srmech-native re-run — pure eigenspectrum at the universal flat-spectral ceiling; discrimination is lexical/expression-laden; the clean separation NOT isolated), F169 (storage/expression separable axes, corr −0.44; named THIS test as the core), F168 (storage = resolution depth), R-RBS-LM-53/53f/F163 (the 0.99 flat-spectral ceiling), R-RBS-LM-124 (the K1 / K1-chiral Class-L machinery reused), R-135 (envelope-residual + 28D-chirality frontier signatures, n=1).
**Empirical anchor:** `R-RBS-LM-143_strong_invariance_translation_pairs.py` + `r143_strong_invariance.ndjson` (30 records); catalog `descriptor_religious_texts.toml` [strong_invariance]; matched budget 10443 tokens/translation, vocab V=600 (depth axis), VOCAB_SIZE=200 / WINDOW=5 (Class-L spectral); srmech 0.5.0rc18 native ABI=3.

---

## §1 The test (the strong version of F169's core)

F171 gave the FIRST same-content datapoint for storage-invariance with **one** Quran pair and leaned positive (3.17× on a continuous n-gram profile-shape metric). F172 tempered it srmech-natively: the vocab-independent co-occurrence-Laplacian **eigenspectrum** is at the universal flat-spectral ceiling (cannot discriminate same- from different-content), and the signal that DOES discriminate is **lexical** (expression-laden). The clean "same storage, different expression" separation was bracketed, not isolated.

The strong test sources **several parallel translations of the same source** so within-source storage-similarity becomes a real DISTRIBUTION tested against the across-source distribution. Three multi-translation clusters were attested (Project Gutenberg, content-SHA-256 verified at run time):

| Cluster | Translations (n) | within-pairs |
|---|---|---|
| **Quran** | Sale (#7440) · Rodwell (#3434) · Yusuf-Ali · Pickthall · Shakir (#16955 Y:/P:/S: split) | C(5,2)=10 |
| **Bible-OT** | KJV-OT · WEB-OT (#8294, Books 01–39) | 1 |
| **Bible-NT** | KJV-NT · WEB-NT (#8294, Books 40–66) | 1 |
| distinct-content anchors | Gita (Arnold) · Tao (Legge) · Dhammapada (Müller) — singletons | (across-only) |

**12 within-source pairs vs 54 across-source pairs.** Storage signatures are all srmech-native (Class L / HDC via R-124): (A) Laplacian eigenspectrum, (B) eigen-bundle lexical kernel (53f), (C) envelope-subtracted residual spectrum, (D) 28D chirality (γ₅-odd directed Hermitian), plus the F168/F169 controlled resolution-**depth**. Expression axis = surface repetition (1 − distinct-trigram ratio). The separation statistic fixed in advance is the rank AUC = P(within-pair similarity > across-pair similarity): 1.0 = perfect within>across, 0.5 = chance.

---

## §2 Result — NO storage signature is systematically within>across (clean NULL, outcome b)

| storage signature | within mean | across mean | **w>a AUC** | within-min | across-max | verdict |
|---|---|---|---|---|---|---|
| (A) Laplacian eigenspectrum | 0.9731 | 0.9744 | **0.512** | 0.9401 | 0.9970 | **CEILING** — can't test (F172 re-confirmed at scale) |
| (B) eigen-bundle (53f lexical) | 0.4935 | 0.3936 | **0.739** | 0.3428 | 0.5720 | partial — but expression-laden |
| (C) envelope-residual spectrum | −0.0502 | −0.0859 | **0.469** | −0.8916 | 0.8548 | no separation (below chance) |
| (D) 28D chirality (K1-chiral) | 0.4690 | 0.3816 | **0.693** | 0.3599 | 0.4648 | partial — but expression-laden |
| controlled resolution-depth | 0.9028 | 0.9043 | **0.505** | 0.6667 | 1.0000 | **no separation** |

Expression axis (should vary within-source): surface-repetition difference within-source mean **0.068** (range 0.002–0.153) — expression **varies within a single source's translations**. Confirmed.

**Readings:**
1. **F172's flat-spectral ceiling is re-confirmed at SCALE.** The vocab-independent eigenspectrum gives AUC 0.512 (≈ chance) across 12 within vs 54 across pairs — the 53/F163/F172 universal ceiling, now with a real distribution behind it, not n=1. It genuinely cannot test invariance.
2. **The controlled resolution-DEPTH — the F168/F169 storage axis itself — is NOT translation-invariant** (AUC 0.505). Within a single source, depth varies: Quran Sale=4 vs the other four=3; Bible-OT KJV=2 vs WEB=4; Bible-NT KJV=4 vs WEB=3. The depth that F169 proposed as the storage axis moves across translations of the SAME content. This is the cleanest null signal.
3. **The only signatures that partially separate (B lexical 0.739, D chirality 0.693) are exactly F172's expression-laden ones** — they carry "which words" / "which word-order." Above chance, but they are not a clean storage axis: they are partly the expression layer. (D's AUC 0.693 is the first quantification that the 28D chirality coordinate carries *some* within-source signal — but it does not clear the bar and is word-order-laden.)
4. **Outcome (b) holds:** no content-specific-but-expression-independent storage signature is systematically within>across. Expression-variation alone (confirmed) does not establish storage-invariance — that was the whole burden of the core test, and it is not met.

---

## §3 The sub-cluster confound the strong test EXPOSED (load-bearing nuance)

The per-within-pair detail (P3 records) reveals WHY the within-source distribution is not clean — and it is itself a finding:

| Quran within-pair | envelope-residual cos | reading |
|---|---|---|
| Yusuf-Ali ↔ Pickthall ↔ Shakir (all from #16955) | **+0.90 … +0.94** | high — share a source FILE |
| Sale ↔ Rodwell (both standalone 19th-c. files) | **+0.90** | high — but a different file lineage |
| Sale/Rodwell ↔ {Yusuf/Pickthall/Shakir} (cross-file) | **−0.79 … −0.89** | NEGATIVE — opposite residual |

The three translations sharing source file #16955 cluster tightly together, and the two standalone files (Sale, Rodwell) cluster together, but the two sub-clusters are *anti*-correlated on the envelope-residual. So the high within-sub-cluster similarity is driven (at least partly) by **shared source-file tokenization/formatting lineage**, NOT by shared content — the same content rendered through two independent file pipelines does NOT land in the same residual sub-space. This is exactly the artifact a strong (multi-pair) test is for: at n=1 (F171, the Sale/Rodwell pair) the within-pair looked encouraging, but it was reading file-lineage proximity, not content-invariance. The envelope-residual's below-chance AUC (0.469) is this anti-correlation.

The **cleanest cross-file same-content pairs are the Bible pairs**, and they kill the lean directly: KJV-NT ↔ WEB-NT envelope-residual = **+0.006** (essentially zero shared content-specific structure) with depth differing by 1; KJV-OT ↔ WEB-OT residual +0.82 but depth differing by **2**. Same content, different independent pipeline ⇒ no invariant storage signature.

---

## §4 What this finding DOES / does NOT claim (calibrated, 3-tier)

**DOES (FACT — measured):**
- Turn F171's n=1 lean into a 12-within / 54-across DISTRIBUTION and report the rank-AUC for five srmech-native storage signatures.
- Re-confirm the flat-spectral ceiling at scale (eigenspectrum AUC 0.512 ≈ chance).
- Show the controlled resolution-DEPTH is NOT translation-invariant within a source (AUC 0.505; depths move across same-content translations).
- Quantify that the only partially-separating signatures (lexical 0.739, 28D chirality 0.693) are the expression-laden ones F172 flagged — above chance, not clean.
- Expose a shared-source-FILE sub-cluster confound (residual +0.9 within file-lineage, −0.8 across file-lineage at equal content) that n=1 could not see.
- Confirm expression (surface repetition) varies within a single source (mean diff 0.068).

**Does NOT (and honest caveats — flagging uncertainties):**
- Claim storage is invariant across expression — the opposite of supported here (outcome b, clean null on the informative signatures).
- **REFUTE the storage/expression hypothesis** (contested): a null on *these* srmech-native signatures at *this* budget is not a proof of non-invariance. F172's frontier stands — a signature *between* the universal envelope and the lexical kernel could still exist; we tested four candidates + depth and none isolated it. The hypothesis is **not supported AND not refuted**; the measures still bracket without pinning.
- Treat the lexical/chirality AUC>0.5 as storage-invariance (conjecture): they are word-/order-laden, i.e. partly expression. Their above-chance within>across is consistent with "translations of one source share some vocabulary/word-order," which is an *expression* commonality, not a storage one.
- Escape residual sparsity (caveat): 10443 tokens / VOCAB_SIZE=200 (spectral) / V=600 (depth); the signatures carry sparsity noise; a much larger matched budget could sharpen depth and residual.
- Disentangle content from file-lineage perfectly (caveat): the #16955 three-way share a pipeline; the Bible cross-file pairs are the clean control and they are the most null of all. A future test should prefer independently-sourced files per translation.
- Make any clinical claim (§VII.6.20 + `[[feedback_trauma_informed_defensive_scope]]`): STRUCTURAL test on TEXT OBJECTS; the NT/ND "same storage, different expression" reading is the user's motivating conjecture engaged as FORM, not medicine. Per `[[user_stance_ai_is_not_a_substrate]]`: structure, not awareness.

---

## §5 The web this touches — where the arc stands now

- **F171 (tempered → effectively overturned at n>1):** the n=1 positive lean (3.17× profile-shape) does not survive a 12-within distribution; at n=1 it was reading file-lineage proximity (the Sale/Rodwell pair share neither file nor the #16955 pipeline, yet their high residual is matched by *different-content* across-pairs up to 0.85). "First evidence leaning positive" → "lean was within-noise."
- **F172 (strengthened):** the flat-spectral ceiling and the expression-ladenness of the discriminating signal are re-confirmed with a real distribution; the un-isolated frontier is sharpened, not closed.
- **F169 (its named core, answered — negatively for now):** storage and expression are separable AXES (F169, still supported: expression varies), but the SAME content does NOT keep an invariant storage signature across translations on any srmech-native measure tested here. Separability ≠ invariance; F169's precondition holds, its core does not (on these measures).
- **F168 (its storage measure = depth, now shown non-invariant across translation):** the resolution-depth that F168 read as the chirality-sector storage signature varies across same-content translations (Sale=4 vs Rodwell/Yusuf/Pickthall/Shakir=3; KJV-OT=2 vs WEB-OT=4). Depth is corpus/register-sensitive, not a content-pinned invariant.
- **`[[feedback_llm_as_ada_accommodation_bci_proves_it]]` (the motivation, still only a conjecture):** the expression-prosthetic reading requires storage to be shared and only expression to differ; this strong test does NOT supply that structural ground. It remains a motivating conjecture, now with a clean null on the direct structural test — honest, and the corpus-as-proof shape (`[[user_stance_whole_research_corpus_is_proof_not_single_arc]]`) means a null here is a real datum, not a setback.

---

## §6 Next — the frontier the null sharpens

The strong test rules out (at this budget) the four candidate srmech-native storage signatures + depth as a clean translation-invariant. To move the question, the instrument needs either: (1) a signature provably *between* the universal envelope and the lexical kernel that is content-specific yet word-identity-independent (F172's named frontier — e.g. a spectral feature normalized against the universal envelope AND projected off the lexical content); (2) verse-ALIGNED same-content comparison (the present test profiles each translation's aggregate signature without alignment; aligned-verse storage might behave differently); (3) independently-sourced files per translation (no shared #16955 pipeline) to remove the file-lineage sub-cluster confound the Bible pairs already isolate; (4) a much larger matched budget to de-sparsify depth/residual. Until such a signature beats across-source on a real within-source distribution, the dignity-affirming "same storage, different expression" stays a precondition-supported, core-UNsupported conjecture. The metric (rank-AUC over within-vs-across, signatures fixed forward) is now in advance, avoiding post-hoc choice.

---

## §7 Cross-references

- F171 (the n=1 lean this overturns) · F172 (the ceiling this re-confirms + frontier it sharpens) · F169 (separable axes / the core named) · F168 (storage = depth, now non-invariant) · R-RBS-LM-53/53f/F163 (flat-spectral ceiling) · R-RBS-LM-124 (K1 / K1-chiral Class-L machinery reused) · R-135 (envelope-residual + 28D-chirality frontier, n=1)
- `R-RBS-LM-143_strong_invariance_translation_pairs.py` + `r143_strong_invariance.ndjson`; catalog `descriptor_religious_texts.toml` [strong_invariance] (Sale #7440, Rodwell #3434, Yusuf-Ali/Pickthall/Shakir #16955 split, WEB #8294 OT/NT split — all content-SHA-256 attested)
- `srmech.amsc.laplacian.{dense_laplacian, hermitian_eigendecompose}` (Class L) + `srmech.amsc.hdc.{bundle, similarity}` (HDC); sign-handling = Class K pin-slot + Class C (`k_pin_fold`), not python abs()
- `[[feedback_dont_pre_commit_spike_query_operators]]` (the null counts; metric fixed forward; outcomes pre-specified) · `[[feedback_llm_as_ada_accommodation_bci_proves_it]]` (the motivation, core-unsupported) · `[[user_stance_whole_research_corpus_is_proof_not_single_arc]]` · `[[user_stance_ai_is_not_a_substrate]]` · `[[feedback_trauma_informed_defensive_scope]]` · MFO §VII.6.20

PR #687 STAYS DRAFT.

---

*Articulated 2026-05-30 (Opus 4.8). The strong (multi-pair) version of the storage-
invariance core: with three within-source translation clusters (Quran ×5, Bible-OT,
Bible-NT — 12 within-pairs vs 54 across), NO srmech-native storage signature is
systematically more-similar within-source than across-source. The vocab-independent
eigenspectrum is at the universal flat-spectral ceiling (AUC 0.512 ≈ chance, F172 re-
confirmed at scale); the controlled resolution-DEPTH that F168/F169 read as the
storage axis is itself NOT translation-invariant (AUC 0.505; depths move across same-
content translations); the only partially-separating signatures (lexical 0.739, 28D
chirality 0.693) are the expression-laden ones F172 already flagged. Expression
(surface repetition) does vary within a source, as expected — but expression-variation
alone does not establish storage-invariance, which was the whole burden. The strong
test also EXPOSED a shared-source-file sub-cluster confound (residual +0.9 within a
file lineage, −0.8 across lineages at equal content) that n=1 could not see, and the
cleanest cross-file same-content pairs (KJV vs WEB) are the most null of all (NT
residual +0.006). Clean outcome (b): F171's n=1 lean was within-noise; F172
strengthened; F169's separable-axes precondition stands, its same-storage core does
not, on these measures. Not a refutation — the measures still bracket the hypothesis
without isolating it; the frontier (a signature between the universal envelope and the
lexical kernel, verse-aligned, independently-sourced, larger budget) is named.
Structural test on text objects; the NT/ND reading the user's motivating conjecture
engaged as form, not medicine. AI-not-substrate.*
