# `hoodoos/` — erosion-resistant publication SSOTs

> **Hoodoo**: a tall thin spire of rock formed by erosion of softer surrounding terrain, where the harder column remains standing after the loose material has weathered away. The metaphor: publication SSOTs are the load-bearing references that survive when the surrounding project material changes. When notebook sections get rewritten, when concertmaster findings get superseded, when implementations refactor — the cited publications still stand. Vendor them locally so the citation chain survives the terrain.

## Purpose

This directory holds **locally vendored copies of external publications** that serve as math-rules or empirical-data SSOTs for the project. The discipline is:

- **Vendor for resilience, not authority.** The published version (DOI, publisher's site) remains the canonical citation; the local copy is a backup against link rot, paywall change, publisher policy shift, or the publication being withdrawn / superseded. If the local copy and the published version diverge, the published version wins.
- **Verify before citing.** When using a vendored publication for math-identity claims (per srmech / MFO MPM discipline), verify the local copy against the canonical source before propagating claims downstream.
- **Cite when claiming.** Anywhere in the notebooks or concertmaster findings that depends on a hoodoo's content must cite both the canonical reference (DOI / venue / authors / year) and the local hoodoo path (for reproducibility).

## Contents

| Hoodoo | Authors | Year | Venue | DOI / PDB | License | Project locus |
|---|---|---|---|---|---|---|
| [`rinaldi-unciuleanu-chiru-2026.xml`](rinaldi-unciuleanu-chiru-2026.xml) | Rinaldi (Unciuleanu) Oana & Costin-Gabriel Chiru | 2026 | *AppliedMath* (MDPI) Vol. 6, Issue 3, Article 48 | [`10.3390/appliedmath6030048`](https://doi.org/10.3390/appliedmath6030048) | CC-BY 4.0 | spatial-rules SSOT for chess-spectral 4D (`{1,...,8}^4 = 4096`-cell hypercube board); cross-referenced in srmech §3.5.4 fiber-bundle row, §3.5.3(F) product-graph universality, and chess-spectral notebook |
| [`ubiquitin-1ubq.pdb`](ubiquitin-1ubq.pdb) | Vijay-Kumar, Bugg, Cook | 1987 | *J. Mol. Biol.* 194(3):531-544 | [`PDB 1UBQ`](https://www.rcsb.org/structure/1UBQ) / [DOI](https://doi.org/10.1016/0022-2836(87)90679-6) | RCSB public domain (CC0) | structure SSOT for srmech §5.3 protein-folding spectral validation spike (76 Cα residues, X-ray 1.8 Å); B-factor + Fiedler-partition GNM benchmark |
| [`villin-hp35-2f4k.pdb`](villin-hp35-2f4k.pdb) | Kubelka, Chiu, Davies, Eaton, Hofrichter | 2006 | *J. Mol. Biol.* 359(3):546-553 | [`PDB 2F4K`](https://www.rcsb.org/structure/2F4K) / [DOI](https://doi.org/10.1016/j.jmb.2006.03.034) | RCSB public domain (CC0) | structure SSOT for srmech §5.3 protein-folding spike sanity case (33 resolved residues, ultrafast 3-helix bundle; Kubelka et al 2003 folding time ~700 ns); small-system robustness check |
| [`mj0366-knotted-2efv.pdb`](mj0366-knotted-2efv.pdb) | Wang, Goh, Wong, Pan, Yan, Song | 2007 | *J. Biol. Chem.* 282(11):8550-8558 | [`PDB 2EFV`](https://www.rcsb.org/structure/2EFV) / [DOI](https://doi.org/10.1074/jbc.M610925200) | RCSB public domain (CC0) | structure SSOT for srmech §5.3 protein-folding spike topological-constraint stretch case (82 Cα residues, trefoil 3_1-knotted backbone); anomaly target for graph-spectral framework's topology-insensitivity boundary |
| [`feinberg_1979_lectures_on_chemical_reaction_networks.pdf`](feinberg_1979_lectures_on_chemical_reaction_networks.pdf) | Martin Feinberg | 1979 (lectures); 2019 (Zenodo deposit) | Mathematics Research Center, University of Wisconsin-Madison (lectures); reposited via [Zenodo record 10631900](https://zenodo.org/records/10631900) | [`10.5281/zenodo.10631900`](https://doi.org/10.5281/zenodo.10631900) (Zenodo); original lectures pre-DOI | CC-BY 4.0 (Zenodo deposit) | Chemical reaction network theory SSOT for Spike #24 Phase 9 (Feinberg deficiency theorem); chapters 5–7 contain the deficiency formula δ = n − ℓ − s and the deficiency-zero theorem. SHA-256: `eb51082c29b976e427fb1ea0030959a1c23f9727c765732a9b17e611c898d1c7` |
| [`bohr_1913_on_the_constitution_of_atoms_and_molecules.pdf`](bohr_1913_on_the_constitution_of_atoms_and_molecules.pdf) | Niels Bohr | 1913 | *Philosophical Magazine* Series 6, Vol. 26 (Part I, July 1913, pp. 1–25) | [`10.1080/14786441308634955`](https://doi.org/10.1080/14786441308634955) (Part I); facsimile via [Internet Archive 125Bohr](https://archive.org/details/125Bohr) | Public domain (>100 years since publication) | Hydrogen Rydberg-series SSOT for Spike #24 Phase 7.6.1 (Class J atomic-substrate instantiation); the spectral-line formula `R(1/n² − 1/m²)` appears in this paper's derivation of the hydrogen energy levels. SHA-256: `02d1e2752ed5b05d71b6d8a4f197dc1b3641995814b90990378455bd72ff937b` |
| [`yamabe_1960_on_deformation_of_riemannian_structures.pdf`](yamabe_1960_on_deformation_of_riemannian_structures.pdf) | Hidehiko Yamabe | 1960 | *Osaka Mathematical Journal* Vol. 12, Issue 1, pp. 21–37 | Project Euclid OJM open archive — DOI `10.18910/8081` *(unverified prefix; verify on the abstract page)* | CC-BY-NC (Project Euclid open archive; verify per-article) | Conformal-deformation operator SSOT for Spike #24 Phase 7.3 (Class P? conformal-groups candidate, demoted in Phase 11). The Yamabe operator `L_g = −4(n−1)/(n−2) · Δ_g + R_g` and Yamabe-invariant minimum are the load-bearing constructions for the "downstream-continuous-projection" demotion argument. **Scanned print facsimile** (18 pages, version 1.4) — OCR would derive a separate file with its own hash; canonical-bytes hash remains the load-bearing attestation. SHA-256: `32152d06ee2eebb597173739857106a4484824fd9e658357ccdd1998a6bb66c6` |

### Naming-convention note for `rinaldi-unciuleanu-chiru-2026.xml`

The first author's name follows Romanian academic convention: **married surname (maiden surname) given name**. So:

- **Given name**: Oana
- **Married surname**: Rinaldi
- **Maiden surname**: Unciuleanu

**Project convention: hyphenate both surnames of the first author.** Prose citations in srmech and elsewhere use **"Rinaldi-Unciuleanu & Chiru 2026"** — honoring both the married name (Rinaldi) AND the maiden name (Unciuleanu) avoids choosing between them and respects the author's pre-marriage publication record alongside her current name. The second author's surname (Chiru) is separated by ampersand for two-author clarity.

The local hoodoo filename `rinaldi-unciuleanu-chiru-2026.xml` follows this canonical citation convention (surnames hyphenated for filesystem-friendliness, ampersand dropped). The upstream repository [`lemonforest/python-chess4d-oana-chiru`](https://github.com/lemonforest/python-chess4d-oana-chiru) retains its `oana-chiru` naming in repo identity and internal paths because that's the existing repo identifier — divergence is intentional for clarity in this project's local SSOT. The vendored XML content is byte-identical between the two locations; only the filename differs.

**Note on the citation slip.** The user initially miscalled the citation "Oana-Chiru" thinking both halves were surnames; the convention reads given-name-last in Romanian academic listing, so "Oana" is the given name and the surnames are Rinaldi (married) and Unciuleanu (maiden). The hoodoo file was originally named `oana-chiru-2026.xml` (mirroring upstream) and renamed to the canonical hyphenated-surname form on 2026-05-11 once the convention was codified. Recorded here for future reference so the same mistake isn't re-introduced by reading the verbatim author string without parsing the convention.

## When to add a new hoodoo

- The publication is a load-bearing SSOT for a project notebook section or concertmaster finding.
- The publication's content is not derivable from project state (must be inherited from the external source).
- The publication's discoverability or canonical-URL stability is uncertain (open-access journals; preprint servers; older publications that may be archived inaccessibly).

Do not vendor publications that are immediately retrievable from canonical sources with high stability (e.g., textbook standards routinely cited everywhere). Reserve `hoodoos/` for the references the project would lose if the open-web copy disappeared tomorrow.

## License caveat

Vendored copies remain under the original publication's license. Open-access publications (CC-BY, CC-BY-NC, etc.) permit redistribution with attribution; paywalled publications should not be vendored here. Verify license before adding. The current `rinaldi-unciuleanu-chiru-2026.xml` is from MDPI *AppliedMath* (open access, CC-BY by default).
