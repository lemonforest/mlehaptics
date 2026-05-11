# `hoodoos/` — erosion-resistant publication SSOTs

> **Hoodoo**: a tall thin spire of rock formed by erosion of softer surrounding terrain, where the harder column remains standing after the loose material has weathered away. The metaphor: publication SSOTs are the load-bearing references that survive when the surrounding project material changes. When notebook sections get rewritten, when concertmaster findings get superseded, when implementations refactor — the cited publications still stand. Vendor them locally so the citation chain survives the terrain.

## Purpose

This directory holds **locally vendored copies of external publications** that serve as math-rules or empirical-data SSOTs for the project. The discipline is:

- **Vendor for resilience, not authority.** The published version (DOI, publisher's site) remains the canonical citation; the local copy is a backup against link rot, paywall change, publisher policy shift, or the publication being withdrawn / superseded. If the local copy and the published version diverge, the published version wins.
- **Verify before citing.** When using a vendored publication for math-identity claims (per srmech / MFO MPM discipline), verify the local copy against the canonical source before propagating claims downstream.
- **Cite when claiming.** Anywhere in the notebooks or concertmaster findings that depends on a hoodoo's content must cite both the canonical reference (DOI / venue / authors / year) and the local hoodoo path (for reproducibility).

## Contents

| Hoodoo | Authors | Year | Venue | DOI | Project locus |
|---|---|---|---|---|---|
| [`oana-chiru-2026.xml`](oana-chiru-2026.xml) | Rinaldi (Unciuleanu) Oana & Costin-Gabriel Chiru | 2026 | *AppliedMath* (MDPI) Vol. 6, Issue 3, Article 48 | [`10.3390/appliedmath6030048`](https://doi.org/10.3390/appliedmath6030048) | spatial-rules SSOT for chess-spectral 4D (`{1,...,8}^4 = 4096`-cell hypercube board); cross-referenced in srmech §3.5.4 fiber-bundle row, §3.5.3(F) product-graph universality, and chess-spectral notebook |

### Naming-convention note for `oana-chiru-2026.xml`

The first author's name follows Romanian academic convention: **married surname (maiden surname) given name**. So:

- **Given name**: Oana
- **Married surname**: Rinaldi
- **Maiden surname**: Unciuleanu

**Project convention: hyphenate both surnames of the first author.** Prose citations in srmech and elsewhere use **"Rinaldi-Unciuleanu & Chiru 2026"** — honoring both the married name (Rinaldi) AND the maiden name (Unciuleanu) avoids choosing between them and respects the author's pre-marriage publication record alongside her current name. The second author's surname (Chiru) is separated by ampersand for two-author clarity.

The filename `oana-chiru-2026.xml` mixes the first author's given name with the second author's surname — kept for upstream consistency with the [`lemonforest/python-chess4d-oana-chiru`](https://github.com/lemonforest/python-chess4d-oana-chiru) repository where the paper XML originates. Filename ≠ canonical citation; prose citations use the hyphenated-surname form.

**Note on the citation slip.** The user initially miscalled the citation "Oana-Chiru" thinking both halves were surnames; the convention reads given-name-last in Romanian academic listing, so "Oana" is the given name and the surnames are Rinaldi (married) and Unciuleanu (maiden). Recorded here for future reference so the same mistake isn't re-introduced by reading the verbatim author string without parsing the convention.

## When to add a new hoodoo

- The publication is a load-bearing SSOT for a project notebook section or concertmaster finding.
- The publication's content is not derivable from project state (must be inherited from the external source).
- The publication's discoverability or canonical-URL stability is uncertain (open-access journals; preprint servers; older publications that may be archived inaccessibly).

Do not vendor publications that are immediately retrievable from canonical sources with high stability (e.g., textbook standards routinely cited everywhere). Reserve `hoodoos/` for the references the project would lose if the open-web copy disappeared tomorrow.

## License caveat

Vendored copies remain under the original publication's license. Open-access publications (CC-BY, CC-BY-NC, etc.) permit redistribution with attribution; paywalled publications should not be vendored here. Verify license before adding. The current `oana-chiru-2026.xml` is from MDPI *AppliedMath* (open access, CC-BY by default).
