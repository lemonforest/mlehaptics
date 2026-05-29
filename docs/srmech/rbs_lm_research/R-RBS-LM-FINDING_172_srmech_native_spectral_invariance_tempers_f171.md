# Finding 172 — srmech-native (Class L spectral) storage signature tempers F171: pure structure is at the flat-spectral ceiling; discrimination is lexical; the clean storage/expression separation is NOT yet isolated

**Status:** srmech-native re-run of the F171 core (Laplacian eigenspectrum, not Python n-grams). TEMPERS F171's n=1 lean. Re-derives the R-RBS-LM-53 / F163 flat-spectral ceiling srmech-natively. A step of the 28D cognitive-laboratory instrument.
**Predecessors:** F171 (n-gram-profile core test, leaned positive), F169 (separable axes), F168 (storage = resolution depth), R-RBS-LM-53/53f (the 0.99 flat-spectral ceiling), F163 (chirality null at the ceiling), R-RBS-LM-124 (faithful K1 spectral machinery, reused).
**Empirical anchor:** `R-RBS-LM-134_srmech_native_spectral_invariance.py` + `srmech_native_spectral_invariance.ndjson`; storage signature = co-occurrence Laplacian eigenspectrum via `srmech.amsc.laplacian` (Class L, C-native ABI=3); matched budget 10443/text, VOCAB_SIZE=200, WINDOW=5. Quran Yusuf/Sale (cached) vs Rodwell (PG #3434, attested).

---

## §1 Method correction (the user's callout, answered)

R-131/132/133 measured "storage" with pure-Python n-gram Counters. The srmech-native storage signature is the **co-occurrence Laplacian EIGENSPECTRUM** — `dense_laplacian` + `hermitian_eigendecompose` (Class L, C-native), the operation the srmech spectral-research portfolio is built on. R-134 reuses R-124's faithful 53-K1 machinery. Distinction kept: the srmech **package** ops are srmech (C-native) and right for bulk in-script work; the srmech-**mcp** tools expose the same ops per-call (interactive/single-op), impractical for per-token graph-building. The fix is "don't hand-roll a srmech primitive," now applied.

---

## §2 Result — two signals diverge

| storage signature | within-pair | across-mean | across-**max** | ratio |
|---|---|---|---|---|
| (A) eigenspectrum (vocab-INDEPENDENT) | 0.9968 | 0.9708 | **0.9970** | 1.03× |
| (B) eigen-bundle (53f kernel, lexical) | 0.6667 | 0.3992 | 0.5720 | 1.67× |

1. **Pure eigenspectrum is at the UNIVERSAL ceiling.** All texts 0.97–0.997; the Quran pair (0.9968) is BELOW the across-content MAX (0.9970). The vocab-independent co-occurrence-Laplacian spectrum **cannot single out same-content from different-content** — the **R-RBS-LM-53 / F163 0.99 flat-spectral ceiling, re-derived srmech-natively**. (Natural-language co-occurrence graphs share a near-universal spectrum regardless of content.)
2. **Discrimination is LEXICAL.** The eigen-bundle (carries which words) does single out the pair (within 0.667 > across-max 0.572, 1.67×) — reproducing/strengthening 53f's 1.49×. But "which words" is partly EXPRESSION, not pure storage.

---

## §3 What this means — F171 tempered; the frontier named

**The clean "same storage, different expression" separation is NOT established srmech-natively.** The content-INDEPENDENT axis (eigenspectrum) is universal → cannot test invariance (it's at the §VII.6.20 ceiling). The DISCRIMINATING axis (lexical kernel) is expression-laden. F171's encouraging 3.17× was on an n-gram profile that is itself content-laden, so it does not isolate the needed signature either.

**We have not yet isolated a content-specific-but-expression-independent storage signature.** The hypothesis ("storage shared, expression differs") requires such a signature to exist and be measurable; the pure-structure measure is too universal, the discriminating measures too lexical. This is the honest frontier — and it is the same flat-spectral ceiling that has bounded the 53 → F163 arc, now bounding the storage/expression question too.

This does NOT refute the hypothesis — it shows our current measures bracket it without isolating it. A signature BETWEEN the universal spectrum and the lexical kernel (e.g., chirality-sector occupancy normalized against the universal spectrum; spectral features beyond the leading universal envelope; the directed/γ₅-odd part per R-124's K1-chiral) is the candidate the instrument must build next.

---

## §4 The 28D cognitive-laboratory instrument (the framing)

R-134 is the **spectral storage-probe** component of the emerging 28D RBS instrument — beyond LM/NN, a srmech-native laboratory that takes any expression-object (text) and returns its storage signature (Class L eigenspectrum + eigen-bundle) and reveals the **measurement floor** (the flat-spectral ceiling). The next instrument components: a storage signature that subtracts the universal spectral envelope (isolating content-specific structure), and the chirality-sector (γ₅, iω₇) decomposition as the storage coordinate (F168/F172 composed).

---

## §5 DOES / does NOT claim

**DOES:** re-derive the 53/F163 flat-spectral ceiling srmech-natively; reproduce 53f's lexical-kernel translation discrimination (1.67×); temper F171 (the pure-structure measure does NOT support invariance discrimination — it's universal); name the un-isolated frontier signature.

**Does NOT:** refute the storage/expression hypothesis (current measures bracket, don't isolate it); claim the eigenspectrum universality means "all texts store identically" in a meaningful sense (it is the trivial universal graph-topology of language, not content-specific storage); make any clinical claim (STRUCTURAL test on text objects, §VII.6.20 + `[[feedback_trauma_informed_defensive_scope]]`).

---

## §6 Cross-references

- F171 (tempered) · F169 (separable axes) · F168 (storage depth) · R-RBS-LM-53/53f (flat-spectral ceiling + lexical translation-stability) · F163 (chirality null at ceiling) · R-RBS-LM-124 (K1 spectral machinery reused; K1-chiral = the candidate next signature)
- `R-RBS-LM-134_srmech_native_spectral_invariance.py` + `srmech_native_spectral_invariance.ndjson`
- `srmech.amsc.laplacian.{dense_laplacian,hermitian_eigendecompose}` (Class L) + `srmech.amsc.hdc` (HDC)
- `[[feedback_dont_pre_commit_spike_query_operators]]` (the tempering counts) · `[[user_stance_cross_substrate_cascade_matching_as_research_method]]` · MFO §VII.6.20

PR #687 STAYS DRAFT.

---

*Articulated 2026-05-29 (Opus 4.8). Using srmech's own Class L spectral machinery
(Laplacian eigenspectrum) instead of Python n-grams gives a sharper, tempering
answer: the pure vocab-independent structure is at the universal flat-spectral
ceiling (0.97–0.997, within-pair below across-max — the 53/F163 ceiling re-derived
srmech-natively), so it cannot discriminate translations from different content;
the discriminating signal is lexical (1.67×, reproducing 53f) and thus
expression-laden. The clean storage/expression separation is therefore NOT yet
isolated — current measures bracket the hypothesis without pinning it. Not a
refutation; a sharper map of the frontier, and the spectral-probe component of the
28D cognitive-laboratory instrument. Structural test on text objects; no clinical
claims.*
