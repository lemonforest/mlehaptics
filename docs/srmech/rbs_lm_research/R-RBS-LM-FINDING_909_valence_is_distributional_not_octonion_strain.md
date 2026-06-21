# F909 (T7) — word VALENCE ("solid only when bonded" vs "gas when loose") is DISTRIBUTIONAL, NOT octonion bond-strain. The F908 octonion affinity does NOT distinguish bound morphemes (`-ing`, `un-`) from free ones (`cat`, `run`) — HOST-STRAIN bound 1.473 ≈ free 1.403; DIR-ASYM 0.000 both (the strain is byte/spelling-derived: `ing` 1.87 ≈ `sun` 1.92). But the distributional free-occurrence rate separates them cleanly — true bound affixes occur free at 0.0/M, free words at mean 374.5/M. So valence lives at the morpheme-distribution scale, with the octonion affinity as the sub-byte bond force underneath — a DIFFERENT scale of coherence (the user's "other scales").

**Date:** 2026-06-21 · **srmech:** 0.9.0rc13 · **Branch:** `research/rbs-lm-rolling-2` (PR #687) · **Probe:** `R-RBS-LM-FINDING_909_valence_is_distributional_not_octonion_strain.py` · **Composes:** F908 (the octonion bond-affinity mechanism), F906 (octonion content-dependent force), F905 (C1 content-blind), F902 (form-coherence = the adjacency/distribution manifold), F552 (the noise/honesty rule) · **User direction (2026-06-21):** "run T7 with that mechanism" + the affinity reframe (coherence phases are affinity classes from a fundamental force; "other scales of coherence").

## The test
F908 gave the affinity mechanism (octonion `cd_mult` bond-strain). T7's hypothesis: **bound morphemes** are high-strain ("solid only when bonded" — must discharge strain into a host) and **free morphemes** low-strain ("gas when loose"). Tested on KNOWN bound affixes vs free words with two octonion-affinity probes (host-context strain; directional asymmetry — since suffix/prefix *direction* is what the octonion non-commutativity could capture), plus the distributional ground-truth.

## Measured (srmech rc13, exact `Fraction`; corpus = 201,389 simplewiki tokens)

**Octonion affinity — does NOT distinguish bound from free:**
| measure | BOUND mean | FREE mean | separates? |
|---|---|---|---|
| HOST-STRAIN (assoc. of `[root, m, root2]`) | 1.473 | 1.403 | **no/weak** |
| DIR-ASYM (`|strain(end) − strain(start)|`) | 0.000 | 0.000 | **no/weak** |

Per-morpheme overlap is total: `ing` 1.87 ≈ `sun` 1.92; `un` 1.10 ≈ `run` 1.05. The octonion strain is **byte/spelling-derived**, so it tracks the bytes, not the morphological role. (DIR-ASYM = 0 ⇒ the associator carries no suffix/prefix directionality either — that is positional, not in the bond-strain.)

**Distributional valence — DOES separate cleanly** (free-token rate, per million):
| bound | rate | free | rate |
|---|---|---|---|
| ing / ness / tion / ly / dis / ment | **0.0** each | cat / run / water / sun | 99 / 104 / 1549 / 660 |
| (contamination: `less` 348, `able` 189, `re` 89, `ed` 84) | — | book / light / big / red | 268 / 402 / 641 / 333 |

Bound mean **53.9/M** vs free mean **374.5/M** (~7×); the *true* affixes that are not also free words are exactly **0.0** (never occur unbonded). The non-zero bound entries are honest contamination — `less`/`able`/`er`/`re`/`ed` double as free words.

## The answer (honest null + the right scale)
**The "valence = octonion bond-strain" hypothesis is FALSIFIED.** The octonion affinity (F908) does not distinguish bound from free morphemes (both probes null). **Valence is DISTRIBUTIONAL** — "solid only when bonded" = free-occurrence ≈ 0; "gas when loose" = free-occurrence > 0 — i.e. it lives in the morpheme's *distribution* (free-occurrence + adjacency obligatoriness, the F902 manifold scale), **not** in the octonion bond-strain.

This is exactly the user's "**other scales of coherence**": there are at least three distinct scales, and they do **not** collapse into one —
- **byte-bond affinity** (octonion `cd_mult` strain, F908) — the sub-byte *fundamental force*: which atoms bond cleanly (content-dependent, the "water-loving/hating");
- **form coherence** (C1 manifold, F902) — are the words/adjacencies on the real manifold;
- **morphological valence** (distribution, F909) — does the morpheme occur free (bound/free).

Valence sits at the distribution scale; the octonion affinity is the force *underneath*. They are not the same coherence — the build (F908) gives the force, but the morpheme's "solid vs gas" is an *emergent distributional* property, not a direct read of the force. (Consistent with F903/F905: emergence is a higher-scale phenomenon, not a direct substrate read.)

## Verdict / next
**Found (honest):** word valence is **distributional**, not octonion bond-strain — the F908 affinity is the byte-level force; "solid only when bonded / gas when loose" is the morpheme's free-occurrence (true affixes 0.0/M, free words ~375/M). The user's "different scales of coherence" is confirmed: byte-bond affinity (F908) ≠ form coherence (F902) ≠ morphological valence (F909). **Next candidates:** (a) measure valence the *right* way at scale — the adjacency-obligatoriness on the F902 sequential manifold (a bound morpheme's neighbours are obligatory; a free morpheme's are optional) — and see if it predicts bound/free across the full lexicon; (b) test whether the octonion affinity (F908) predicts a *different* linguistic axis it is suited to (e.g. which roots+affixes form *stable* derived words vs nonce — the actual byte-bond compatibility); (c) T9 ni-Vanuatu/Bislama agnosticism. The honest lesson: don't collapse the scales — the fundamental force (octonion) and the distributional valence are different rungs of coherence.
