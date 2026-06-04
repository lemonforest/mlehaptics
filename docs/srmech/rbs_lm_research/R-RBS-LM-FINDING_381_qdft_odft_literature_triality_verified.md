# R-RBS-LM Finding 381 — QDFT/ODFT literature: triality-verified attested bibliography (discharges the F378 verify-PDF debt)

**Date:** 2026-06-04
**Arc:** RBS-LM · FFT-ladder thread (F377 → F378 → F379 → F380 → **F381**); discharges the verify-PDF debt flagged in F378 and carried into #863's DoD
**Engine:** `research-triality` (first live run — k=3 haiku∥sonnet∥opus, per-claim 2-of-3 majority + spot-verify merge); run `wf_a5500bbd-5c6`, 5 agents, ~12 min
**Provenance:** `R-RBS-LM-R23_triality_qdft_odft_litverify_results.json` (full surveys + triangulation + merged result)
**Discipline:** MPM citation discipline + `[[feedback_paywalled_doi_cannot_be_attested]]` — bibliographic identity verified via independent OA indices (Crossref / PubMed / IEEE Xplore / Semantic Scholar); every **load-bearing claim** anchored to an **OA full-text** source (no load-bearing claim rests on a paywalled PDF).

---

## Outcome

The literature **independently confirms the structural claims** the QDFT/ODFT draft descriptors were built on — non-commutativity → left/right/two-sided forms; non-associativity → a **declared multiplication convention** + real-valued restriction; Q₈/{±1}≅Klein-4 as a standard fact. The verify-PDF debt is **discharged**: the bibliography below is attested (verified) or honestly held (minority/single-tier).

### LODGED — verified (unanimous / majority across the 3 tiers)

**Quaternion FT lineage** (the corrected quartet — the loose "Sangwine-Ell 2000s discrete-QFT-with-fast-algorithms" framing does NOT map to one paper):
| # | citation | DOI / OA | consensus |
|---|---|---|---|
| 1 | Ell, T.A. (1993), "Quaternion-Fourier transforms for analysis of two-dimensional linear time-invariant partial differential systems", *Proc. 32nd IEEE CDC* | DOI 10.1109/CDC.1993.325510 (IEEE Xplore doc 325510; **paywalled full-text**, bibliographic verified) | unanimous |
| 2 | Sangwine, S.J. (**sole author** — NOT Sangwine-and-Ell), "Fourier transforms of colour images using quaternion, or hypercomplex, numbers", *Electronics Letters* 32(21):1979-1980 (1996) | DOI 10.1049/el:19961331 (IET; **paywalled**, bibliographic verified) | unanimous |
| 3 | Bülow, T. (1999), "Hypercomplex Spectral Signal Representations for the Processing and Analysis of Images", PhD thesis, Christian-Albrechts-Universität zu Kiel | **OA** — Kiel repo `macau_mods_00001940` | unanimous |
| 4 | Ell, T.A. & Sangwine, S.J. (**Ell-first**), "Hypercomplex Fourier Transforms of Color Images", *IEEE Trans. Image Processing* 16(1):22-35 (2007) | DOI 10.1109/TIP.2006.884955; **PMID 17283762** (PubMed OA metadata); paywalled full-text | majority (sonnet+opus; haiku missed) |
| 5 | Ell, T.A., Le Bihan, N. & Sangwine, S.J. (2014), *Quaternion Fourier Transforms for Signal and Image Processing*, ISTE/Wiley (comprehensive monograph) | ISBN 9781848214781; DOI 10.1002/9781118930908; **OA bibliographic** HAL `hal-00987367` | majority |

**Left / right / two-sided QFT distinction** (non-commutativity):
| 6 | Because quaternion multiplication is non-commutative, the QFT kernel can sit LEFT, RIGHT, or BOTH (two-sided). Source-for-fact: **Hitzer, E., "Quaternion Fourier Transform on Quaternion Fields and Generalizations", arXiv:1306.1023** (**OA full-text** — the right-sided QFTr definition + non-commutativity rationale extracted verbatim) | unanimous |

**Octonion FT lineage:**
| 7 | Hahn, S.L. & Snopek, K.M. (2011), "The unified theory of n-dimensional complex and hypercomplex analytic signals", *Bull. Polish Acad. Sci.: Tech. Sci.* 59(2):167-181 — **the ORIGINAL OFT definition** (not Błaszczyk-Snopek) | DOI 10.2478/v10175-011-0021-2 (Crossref-confirmed; **OA journal** journals.pan.pl) | unanimous |
| 8 | Błaszczyk, Ł. & Snopek, K.M. (2017), "Octonion Fourier Transform of real-valued functions of three variables — selected properties and examples", *Signal Processing* 136:29-37 — first dedicated OFT-properties paper | DOI 10.1016/j.sigpro.2016.11.021 (Crossref; PII S0165168416303358; paywalled Elsevier, content corroborated by OA arXiv:1905.12631) | unanimous |
| 9 | Błaszczyk, Ł. (2020), "A generalization of the octonion Fourier transform to 3-D octonion-valued signals…", *Multidim. Syst. Signal Process.* | DOI 10.1007/s11045-020-00706-3; **OA arXiv:1905.12631** | majority |

**Non-associativity handling (the load-bearing answer for the ODFT bracketing field):**
> **Verbatim, arXiv:1905.12631 (Błaszczyk, OA):** *"the octonion algebra is non-associative, so it is necessary to note that the multiplication in the above integrals is done from left to right."*

So the literature's convention is a **fixed left-to-right multiplication order** (+ restriction to real-valued inputs / exploitation of subalgebra associativity / left-linearity). **This externally confirms the `octonion_dft.draft.toml` design** — the OFT is non-unique and MUST declare a bracketing convention; "left-to-right" is the literature's declared choice.

**Group-theory anchor (matches the R21 proof):**
| 10 | Q₈/{±1} ≅ Klein four-group V ≅ Z₂×Z₂ — standard finite-group fact (Z(Q₈)={±1}; the quotient is the unique non-cyclic order-4 group). Home: **Dummit & Foote, *Abstract Algebra* 3rd ed.** (+ Wikipedia "Quaternion group": "factor group Q₈/{e,ē} ≅ Klein four-group V"; Groupprops; Keith Conrad). | unanimous |

### HELD — minority / single-tier (NOT lodged; corroborate before citing)
- **Said, Le Bihan & Sangwine (2008)**, "Fast complexified quaternion Fourier transform", *IEEE TSP* 56(4):1522-1531, DOI 10.1109/TSP.2007.910477, arXiv math/0603578 — **high-value** (this, NOT a "2000 Sangwine-Ell" paper, is the genuine *fast-algorithm* reference); single-tier (sonnet), held.
- Ell (1992) PhD thesis "Hypercomplex Spectral Transforms", Univ. Minnesota, UMI 9231031 — paywalled ProQuest, no OA/DOI; plausibly predates the 1993 CDC paper; uncorroborated.
- Bülow & Sommer (2001), *IEEE TSP* 49(11):2844-2852, DOI 10.1109/78.960432 — the journal publication of the Bülow thesis.
- Bülow, Felsberg & Sommer (2001) book chapter, "Non-commutative hypercomplex Fourier transforms…", *Geometric Computing with Clifford Algebras*, Springer.
- Hitzer (2016/2017), *AACA* 27:381-395, DOI 10.1007/s00006-016-0684-8 — real but a **later convolution** paper, not the source-for-fact for the basic left/right distinction (use arXiv:1306.1023).
- Błaszczyk-Snopek erratum (2018), *Signal Processing* 142:149-151.

## The engine caught real errors (first-run validation of `research-triality`)
1. **opus emitted a WRONG DOI** for Błaszczyk-Snopek 2017 (`10.1016/j.sigpro.2017.01.001` → Crossref resolves an unrelated "Gaussian filtering" paper); the merge corrected it to `10.1016/j.sigpro.2016.11.021`. A plausible-but-wrong citation a single-model run would have shipped silently.
2. **sonnet correctly rejected** a candidate Hahn-Snopek DOI (`10.2478/v10175-011-0019-8`, live 404); the real DOI `10.2478/v10175-011-0021-2` was found.
3. **The triangulation over-corrected** — it labelled "Sangwine & Ell 2000 (Horwood)" *fabricated*; the **spot-verify merge REVERSED** that false-negative (it's a real book chapter, ResearchGate 263579558). **Engine note:** the 3-way vote can over-reject; the spot-verify merge layer is a needed safety net beyond the bare majority (an honest refinement of the k=3 form — the merge is not redundant with the vote).

## Net
The QDFT/ODFT literature is real, attributable, and **structurally aligned with the framework drafts**: non-commutativity↔left/right/two-sided, non-associativity↔declared left-to-right convention, Q₈/{±1}↔Klein-4. The verify-PDF debt (F378/#863 DoD) is discharged for the lodged set; the framework *readings* (Klein-4-object→QDFT native transform, the 1:3:7 Hurwitz ladder, octonion-FT-carries-the-order-content) remain **our lens**, offered, never attributed to these authors.
