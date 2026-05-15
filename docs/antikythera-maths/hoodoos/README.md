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
