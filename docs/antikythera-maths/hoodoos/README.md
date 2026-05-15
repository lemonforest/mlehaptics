# hoodoos/

> *Hoodoos stand when the rest of the ground has eroded.*

This directory is the project's local cache of **published external knowledge** —
papers, articles, archived references that the research lines anchor on but
which the project does not own copyright to. The PDFs themselves are
**`.gitignore`'d** so we don't redistribute copyrighted material; this README
documents what should be in here, where it came from, and how to retrieve it.

## How to use this directory

1. **You (the human researcher)** download the relevant PDFs to this directory.
   The publishers' terms generally permit personal-use downloads.
2. **Claude / agents** can read the PDFs from disk for analysis — that's
   local processing of material you legitimately accessed, not redistribution.
3. **The PDFs do not get committed.** Only this README + the per-paper
   metadata documented below land in git.
4. **If you replace a file**, update its metadata stanza below (especially
   if the version differs — e.g. publisher PDF vs author manuscript).

The discipline mirrors what `[feedback_autonomous_validation_tos_landscape]`
codifies: external scholarly material is read locally for citation work,
never republished, and the metadata-plus-DOI pattern is what survives in
the repo.

## Cached papers

### 1. Freeth et al. 2006 — Nature

| Field | Value |
|-------|-------|
| **File** | `antik2.pdf` |
| **Title** | Decoding the ancient Greek astronomical calculator known as the Antikythera Mechanism |
| **Authors** | T. Freeth, Y. Bitsakis, X. Moussas, J. H. Seiradakis, A. Tselikas, H. Mangou, M. Zafeiropoulou, R. Hadland, D. Bate, A. Ramsey, M. Allen, A. Crawley, P. Hockley, T. Malzbender, D. Gelb, W. Ambrisco, M. G. Edmunds |
| **Journal** | *Nature* **444**, 587–591 (30 November 2006) |
| **DOI** | [10.1038/nature05357](https://doi.org/10.1038/nature05357) |
| **Publisher URL** | <https://www.nature.com/articles/nature05357> |
| **Retrieved from** | ResearchGate (manually downloaded by the human researcher) |
| **Copyright** | © 2006 Nature Publishing Group / Springer Nature. **Not redistributable.** GitHub-excluded via `.gitignore`. |
| **Used for** | Spike F2 (2026-05-14, see [`docs/srmech/notes/spike_pinslot_elevation_and_differential_findings_2026-05-14.md`](../../srmech/notes/spike_pinslot_elevation_and_differential_findings_2026-05-14.md)) — pin-and-slot geometry, eccentricity ε reconstruction, lunar mechanism architecture |

### 2. Freeth 2009 — Scientific American

| Field | Value |
|-------|-------|
| **File** | `Decoding_an_Ancient_Computer.pdf` |
| **Title** | Decoding an Ancient Computer |
| **Authors** | Tony Freeth |
| **Magazine** | *Scientific American* **301**(6), 76–83 (December 2009) |
| **DOI** | [10.1038/scientificamerican1209-76](https://doi.org/10.1038/scientificamerican1209-76) |
| **Publisher URL** | <https://www.scientificamerican.com/article/decoding-an-ancient-computer/> |
| **Retrieved from** | ResearchGate (manually downloaded by the human researcher) |
| **Copyright** | © 2009 Scientific American, Inc. (Nature America / Springer Nature). **Not redistributable.** GitHub-excluded via `.gitignore`. |
| **Used for** | Popular-audience complement to Freeth 2006; cross-reference for spike F2 lunar-mechanism architecture claims |

### 3. Freeth et al. 2021 — Scientific Reports

| Field | Value |
|-------|-------|
| **File** | `s41598-021-84310-w.pdf` |
| **Title** | A Model of the Cosmos in the ancient Greek Antikythera Mechanism |
| **Authors** | Tony Freeth, David Higgon, Aris Dacanalis, Lindsay MacDonald, Myrto Georgakopoulou, Adam Wojcik |
| **Journal** | *Scientific Reports* **11**, 5821 (2021) |
| **DOI** | [10.1038/s41598-021-84310-w](https://doi.org/10.1038/s41598-021-84310-w) |
| **Publisher URL** | <https://www.nature.com/articles/s41598-021-84310-w> |
| **Retrieved from** | Open-access publisher download (`www.nature.com/scientificreports`) |
| **Copyright** | © 2021 The Author(s). **Open access under CC BY 4.0.** This paper *could* legally be hosted on GitHub with attribution, unlike the other two hoodoos. We keep the `.gitignore` discipline uniform for repo-size hygiene and consistency of the hoodoos pattern; the PDF is retrievable from the publisher URL by anyone. |
| **Used for** | Spike F2 / F6 (2026-05-14): Freeth's substantially updated reconstruction, particularly the planetary mechanisms. Major finding: pin-and-slot is the bronze's universal nonlinear primitive for variable motion — applied to **all 5 planets** (Mercury, Venus, Mars, Jupiter, Saturn) per the proposed planetary gear trains, not just the lunar anomaly. Confirms the architectural cascade premise of Open Question 6 in our spike spec, with refinement (single pin-slot per train, not multi-stage). |

> **Note on the OA distinction.** Scientific Reports is fully open-access under CC BY 4.0. This means redistribution with attribution is legally permitted — unlike the Nature 2006 and SciAm 2009 papers above. We keep the uniform `.gitignore` discipline anyway because the hoodoos pattern is about durability of external knowledge via the publisher's canonical URL, not about repo storage. If someone wanted to vendor open-access papers explicitly, that decision is a separate one from the hoodoos cache pattern.

### 4. Freeth et al. 2021 — Author Correction (Scientific Reports)

| Field | Value |
|-------|-------|
| **File** | `s41598-021-96382-9.pdf` |
| **Title** | Author Correction: A Model of the Cosmos in the ancient Greek Antikythera Mechanism |
| **Authors** | Tony Freeth, David Higgon, Aris Dacanalis, Lindsay MacDonald, Myrto Georgakopoulou, Adam Wojcik |
| **Journal** | *Scientific Reports* **11**, 17361 (2021) |
| **DOI** | [10.1038/s41598-021-96382-9](https://doi.org/10.1038/s41598-021-96382-9) |
| **Published** | 24 August 2021 |
| **Publisher URL** | <https://www.nature.com/articles/s41598-021-96382-9> |
| **Copyright** | © The Author(s) 2021. **Open access under CC BY 4.0.** Same OA framing as the original paper (entry 3 above). |
| **Used for** | Spike F2 / F6 verification step (2026-05-14): confirmed the corrections are **purely typographic** — Greek-letter encoding (ΨΞΒ → ϒΞΒ, ΨΜΒ → ϒΜΒ in the inscriptional number-spellings; the *numerical* values 462 and 442 were never wrong) and fraction-formatting fixes (-¹²/₂₂₃ superscript → -12/223 proper fraction). **No impact on the load-bearing pin-and-slot / lunar-anomaly / planetary-mechanism findings.** Cited per `feedback_pdf_extraction_citation_discipline` discipline — the correction-check itself is the load-bearing step, regardless of outcome. |

### 5. Freeth et al. 2021 — Supplementary Information (Scientific Reports)

| Field | Value |
|-------|-------|
| **File** | `41598_2021_84310_MOESM4_ESM.pdf` |
| **Title** | Supplementary Information for "A Model of the Cosmos in the ancient Greek Antikythera Mechanism" |
| **Authors** | Tony Freeth, David Higgon, Aris Dacanalis, Lindsay MacDonald, Myrto Georgakopoulou, Adam Wojcik |
| **Journal** | *Scientific Reports* **11**, 5821 — Supplementary Information 4 (2021) |
| **DOI** | [10.1038/s41598-021-84310-w](https://doi.org/10.1038/s41598-021-84310-w) (same as main paper; supplementary file is MOESM4_ESM) |
| **Publisher URL** | <https://static-content.springer.com/esm/art%3A10.1038%2Fs41598-021-84310-w/MediaObjects/41598_2021_84310_MOESM4_ESM.pdf> |
| **Copyright** | © The Author(s) 2021. **Open access under CC BY 4.0.** |
| **Used for** | Spike F12 / Batch B / Batch C F17 (2026-05-14). **Contents inspected:** 59 pages; sections S1 (Physical Evidence), S2 (Texts & Inscriptions), S3 (Planetary Periods incl. Babylonian period-relation tables S3–S6), S4 (Theoretical Mechanisms — gear-train derivations, Table S8 gear modules, Table S9 geometric parameters for planetary gear trains), S5 (Matching the Evidence — explicit Venus + Mercury gear-train derivations on p.37–38), S6 (Reconstructing the Cosmos — full mechanism layout incl. shared-fixed-gear 56 architecture on p.51–52). **F17 finding (load-bearing):** the document does NOT contain per-planet bronze-measured eccentricity values, because Freeth's planetary mechanism design uses **AU distance** per planet (Table S9), NOT planetary eccentricity. The originally-anticipated BronzeHipparchan encoder mode (B2 spec) is therefore based on a faulty premise; replaced by BronzeGeocentricEpicycle which uses bronze's actual data (Sun-vector + AU-distance epicycle, vector composition). |

## Retrieval notes

ResearchGate hosts both PDFs as publisher Version-of-Record files. The
authors retain the right to self-archive author-manuscript versions but
typically not the publisher VoR. If you re-download these files, use
the publisher URLs above when possible; if the publisher copy is
paywalled and the ResearchGate copy is publisher VoR, treat the ResearchGate
copy as a third-party redistribution (which you can read but not re-publish).

For future spike work that needs primary-PDF citation discipline (per
[`feedback_pdf_extraction_citation_discipline`](../../../C:/Users/sckir/.claude/projects/D--GitHub-mlehaptics/memory/feedback_pdf_extraction_citation_discipline.md)
in the user's memory tree), this directory is where the canonical local
cache lives.

## What does NOT belong in this directory

- **Open-access papers** — those can be cited by URL or hashed-pointer; no
  need to cache locally. The hoodoos pattern is for paywalled / restrictive-
  redistribution material specifically.
- **Project-internal documents** — those live in their own subtrees.
- **Computed artefacts** — those go to `notes/` or the appropriate
  package's `_research/` tree.
