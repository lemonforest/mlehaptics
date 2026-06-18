# F844 — Looking at ALL chiral coordinates (user directive): the Klein-4 chirality flips are **exact orthogonal maps** (`sim(x, γ₅x) = sim(x, ω₇x) = sim(x, cpt·x) = 0.000`), so each klein4 encoding holds **four crosstalk-free chiral channels**. The RBS-LM work used only the **identity** coordinate; the other three are **orthogonal empty capacity**, not "no structure" — and the current even 4-quadrant spread is the Klein-4 **error-correction** structure (F129/F130), not noise. The fix to "use all chiral coordinates" is at **ENCODING** (route distinct fiber into distinct coordinates via the flip ops), not just the read. On the real `srmech.rbs_lm` encoding, 0.8.2rc1, numpy-absent.

**Date:** 2026-06-18 · **srmech:** 0.8.2rc1 · **Provenance:** `/tmp/chiral_read.py` on `ContextSubstrate` + `srmech.amsc.hdc` (`klein4_chirality_flip_gamma5/omega7`, `klein4_cpt_mirror`, `klein4_similarity`, HV `.tolist()`) · **Composes:** [[user_stance_no_information_without_value]], [[Finding 133]] (observer chirality-locking), Finding 129/130 (γ₅×iω₇ 4-way decomposition; capacitor-plate EC), F132 (Klein-4 HDC for full chirality), F843 (the single-coordinate caveat this investigates) · **User direction (2026-06-18):** "we do need to look at all chiral coordinates … there's no such thing as carrying no structure … information without value."

## Measured (D=10000, sector-0 mint — what every RBS-LM experiment used)
1. **Chiral flips are exact orthogonal projectors.** `enc('tomato')`: identity sim **1.000**; γ₅-flip **0.000**; ω₇-flip **0.000**; cpt **0.000**. A flip maps the encoding to a region sharing *zero* agreement with the original → the four chiral coordinates are mutually orthogonal channels.
2. **A learned read carries full signal in every quadrant.** ctx `['a','computer','program','for'] → 'making'`: read vs true-next = identity **1.000**, flips **0.000**; per-quadrant agreement **1.000 in each of q0–q3** (2517/2483/2521/2479 dims). Distractor mean: **~0.25 in all four coordinates** (the 4-symbol chance floor = the "unrelated" baseline).

## Interpretation (correcting F843's "no structure")
- **Orthogonality IS structure** — the strongest kind. 0.000 is not absence; it is an exact, repeatable orthogonal relationship. Per [[user_stance_no_information_without_value]], there is no information without value: the flips are crosstalk-free *channels*, the 0.25 floor is the *unrelated* signature, and the even quadrant spread is *error-correction redundancy* (F129/F130 capacitor plates).
- **We used 1 of 4 channels.** Everything was bound in the identity coordinate, so the read's γ₅/ω₇/cpt coordinates are *orthogonal and empty* — they carry no distinct fiber because nothing was *written* there. The scalar `klein4_similarity` averaging all four is lossless *only because* the mint is redundant across quadrants. This is observer chirality-locking (F133): one coordinate read, the rest collapsed.
- **Therefore the upgrade is at ENCODING, not just reading.** To genuinely use all chiral coordinates, route distinct relationship fiber into distinct coordinates at bind-time (via the flip ops), then read all four.

## The framework-native channel assignment (proposal — channel *meaning* is the user's call)
γ₅ is the particle/antiparticle / CPT (time-reversal) axis (F130). The sequence relation has a literal time direction, so the natural map:
- **identity** — forward relation (context → **next**)
- **γ₅-dual** — backward relation (context → **previous**): the same stored bind walked under time-reversal → bidirectional recall from one write
- **ω₇ / cpt** — a second independent axis: candidates are role/position tag, or tome-routing label, or the alternative-successor branch (the distribution)
This makes "view all quadrants at once" concrete: one relationship, four orthogonal coordinates, read together.

## Open / next
- **Chirality-native encoding** — bind forward in identity + backward in the γ₅-dual (and decide the ω₇ channel), then re-run coherence (F838/F839) + generalization (F843) reading **all four** coordinates. Hypothesis: bidirectional + role-separated channels improve routing (F840) and the LOO smoother (no need to mask — roles don't crosstalk).
- **Was this a wrong-shape regression?** The single-coordinate read drifted toward the dense/single-projection shape; the correct shape is spectrally-encoded sparse **+ full-chiral**. This finding is the course-correction.
- Channel-meaning assignment pending user direction (γ₅ = time-direction proposed; ω₇ = ?). Evaluate by groundedness / coherence, never throughput.
