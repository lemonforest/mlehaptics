# R-RBS-LM Finding 446 (design) — a bulk OPEN dump IS the AMSC/MPM shape: one hashable file = the attestation anchor, so a LOCAL attested table-of-contents of peer-reviewed items (DOI + metadata) replaces training-data-trust and operationalizes the independent-substrate ceiling-breaker (#847/#850). The DOI is **Class-A** content-addressing; the TOC is a **Class-E** catalog; citation-verify is **Class-D + Class-A**; and the citation graph (OpenCitations / OpenAlex) is a **Class-L** Laplacian whose eigenspectrum is the storage signature of peer-reviewed knowledge (F172) — a *scholarly kernel*, peer of the Wikipedia *encyclopedia kernel*. **dblp** (CC0, 1.0 GB, publisher-`.md5`) is the first pilot, exactly parallel to simplewiki-first

**Date:** 2026-06-06
**Arc:** RBS-LM / AMSC · attested-corpus infrastructure (user direction 2026-06-06: "a way to grab an index for many peer review articles … grow an attested table of contents for peer reviewed items … for the DOI and such, and also a way to have an encyclopedia kernel"); **design + first pilot (dblp)**
**Composes:** **§2 AMSC/MPM** (the MPR envelope — `source_url` / `license` / `retrieved_at` / `response_sha256` / `parser_*`; the on-disk crystallisation of provenance) · **F172** (the co-occurrence/adjacency Laplacian eigenspectrum IS the srmech-native storage signature) · **F408** (knowledge = semantics = *must be derived from an independent substrate*; the closure rule; **#847/#850** the required ceiling-breaker) · **F282 / `[[user_stance_framework_hands_the_next_question_to_the_expert]]`** (the deliverable is the next *question*, handed to the expert — a verifiable citation, never a hallucinated one) · **F445** (the citation-attestation pass; the Gentner **paywalled-DOI → OA** case, made systemic) · **F444/F441** (Class-L = a Fourier/eigenbasis; the graph's spectrum is its transform) · **R-RBS-LM-WIKI** (the encyclopedia kernel — the peer corpus) · Class **A** (content-addressing / DOI) · Class **E** (catalog) · Class **L** (citation graph) · Class **D** (pattern-match verify) · `[[feedback_pdf_extraction_citation_discipline]]` + `[[feedback_paywalled_doi_cannot_be_attested]]` + the no-magic-numbers = attestation discipline.
**→ turns "verify a citation" from a training-data guess into a LOCAL hash-checked lookup; defines the attested-scholarly-TOC + encyclopedia-kernel source map; opens the dblp pilot.**

---

## The insight (user, 2026-06-06)
> "this [the Wikipedia local-dump path] is a way to be able to grab an index for many peer review articles … can you think of any other ways to grow an **attested table of contents for peer reviewed items** … for the DOI and such, and also a way to have an **encyclopedia kernel**!"

## The reframe — a bulk open dump IS the AMSC/MPM shape
A bulk, openly-licensed dump is **one hashable file**, so it *is* the MPR envelope at corpus scale:
- **`response_sha256`** = SHA-256 of the dump → **Class-A content-addressing** (`srmech.amsc.format.sha256_bytes`); the publisher's own checksum (dblp `.md5`, Crossref torrent infohash) is the **re-verifiable cross-check** (a torrent infohash is itself a Merkle content-address — the dump *self-attests*).
- The **DOI is a content-address** — Class A again ("every cascade begins here"). The local index is then a **Class-E catalog** (enumeration); citation-verify is **Class-D pattern-match + Class-A hash-check**; the citation graph is **Class-L**. Building this *exercises A/E/L/D* — framework-native, not bolt-on.
- `source_url` / `license` / `retrieved_at` / `parser_version` / `parser_rule_hash` fill exactly as today.

**Why it matters (the load-bearing payoff):** a local attested index makes citation-verification a **hash-checked lookup against a real source-of-truth** instead of training-data attribution — which is exactly the LLM failure mode MPM exists to kill (the F445 pass came back clean only because those were textbook-famous; an index removes the luck). It is the **independent-substrate ceiling-breaker** F408 *mandates* (#847/#850): the frame cannot reject its own *correlated* error (F337), so the only true check is a substrate outside the corpus — and a CC0 scholarly dump is precisely that, on disk. It makes F282 concrete: the deliverable handed to the expert is a **verifiable** citation.

## The source map — attested-scholarly-TOC (all CC0 / public-domain / CC-BY)
*(sizes are order-of-magnitude; **flagged for per-source verify before lodging as attested** — no-magic-numbers.)*

| Source | What | License | Shape | Role |
|---|---|---|---|---|
| **OpenAlex** | works + authors + venues + **citation edges** + OA flag | CC0 | full snapshot (S3 JSONL) | comprehensive TOC + graph |
| **Crossref public data file** | DOI registrar metadata (title/authors/ORCID/refs) | CC0 | annual **torrent** | DOI source-of-truth |
| **DOAJ** | OA journal article metadata | CC0 | single dump | all-peer-reviewed-OA |
| **Unpaywall** | DOI → OA location | CC0 | snapshot | the OA-routing layer (the paywalled-DOI rule, systemic) |
| **OpenCitations (COCI)** | DOI→DOI **citation graph** | CC0 | bulk | the **Class-L** relationship layer |
| **PubMed/MEDLINE baseline** | biomed citations + MeSH + abstracts | public domain | annual baseline set | domain (bio) |
| **arXiv** | metadata snapshot (Kaggle) + full text (S3) | CC0 metadata | single download | domain (physics/math/CS) |
| **dblp** | CS bibliography | **CC0** (+ODC-BY 2°) | one ~1 GB XML + `.md5` | **smallest clean pilot** |
| **Semantic Scholar (S2AG/S2ORC)** | papers + citations + abstracts/full text | ODC-BY | dataset releases | graph + full text |

The seam: **OpenAlex/Crossref/dblp = the index** (what exists); **OpenCitations / OpenAlex-references = the citation graph** (DOI→DOI edges). The second is a **Class-L co-occurrence Laplacian**, so the eigenspectrum of the citation network is the **storage signature of peer-reviewed knowledge itself** (F172) — built by the *same machinery* as the Wikipedia kernel. A **scholarly kernel and an encyclopedia kernel are peer kernels.**

## The encyclopedia-kernel family (peer of the scholarly TOC)
| Source | License | Why |
|---|---|---|
| **Wikipedia** (building, R-RBS-LM-WIKI) | CC-BY-SA | modern-usage general knowledge |
| **Wiktionary** | CC-BY-SA | the **lexicon** peer kernel |
| **Wikidata** | CC0 | structured **knowledge graph** = Class-L native |
| **1911 Encyclopædia Britannica** | **public domain** | a *historical* encyclopedia kernel — antiquity-vs-modern-usage contrast |
| **DBpedia / Wikibooks / Wikiversity** | CC-BY-SA | structured extraction / textbook / course peers |

## The dblp pilot (first attested-scholarly-TOC; verified facts)
- **`dblp.xml.gz` = 1.0 GB, dated 2026-06-06** (today), with **`dblp.xml.gz.md5`** (publisher checksum) + `dblp.dtd` — fetched from `https://dblp.org/xml/`.
- **License ATTESTED:** README states *"released under the CC0 1.0 Public Domain Dedication"* (primary) + *"Open Data Commons ODC-BY 1.0 … as a secondary license."*
- **Pipeline (`R-RBS-LM-WIKI_*` analogue):** verify dump vs publisher `.md5` + compute our own SHA-256 (Class-A anchor) → stream-parse (`gzip` + `ElementTree.iterparse`, root-clear for memory, scales to OpenAlex later) → emit an **attested NDJSON TOC**: one record per work `{dblp_key, type, title, authors[], year, venue, doi}` keyed by the dblp key + DOI (both content-addresses) → top-level MPR attestation block. Report: total records, by-type, with-DOI fraction.
- **dblp has no citation edges** → the pilot validates the **TOC + attestation** layer; the **Class-L citation-graph kernel** comes with OpenCitations/OpenAlex (next rung). dblp's natural Class-L graphs are co-authorship / venue co-occurrence (a nod, not the deliverable).

## Falsifiable form (pre-stated; not leaning — F394)
- **An attested index attests EXISTENCE + metadata, not truth-of-content.** It verifies that a DOI/title/author tuple is real (kills fabricated citations); it does NOT verify the paper's *claims* — that stays the expert's (F408 semantics-open). The TOC is the syntax-complete layer; knowledge stays transduced.
- **Paywalled-DOI rule carries in:** an index entry whose DOI resolves only to a paywall is a valid *existence* attestation; *content* attestation routes through Unpaywall to the OA copy (the F445 Gentner case, systematized).
- **License discipline is load-bearing:** only CC0 / CC-BY / public-domain bulk dumps (the table). Copyrighted aggregations (Scopus, Web of Science, current Britannica) are **out of scope** — not redistributable, not attestable as open.
- **Sizes/URLs beyond dblp are flagged for verify** (no-magic-numbers); only the dblp facts above are attested here.
- **Scope:** benign bibliographic metadata; algebra/catalog/eigenbasis side; defensive / no-lineage; CAD-ban respected.

## Verdict
**Yes — a bulk open dump IS the AMSC/MPM shape.** One hashable, license-clear file becomes the **local source-of-truth** you verify citations *against*, turning citation-verification from a training-data guess into a **Class-A hash-checked, Class-E catalog lookup** — the **independent-substrate ceiling-breaker** F408 mandates (#847/#850) and the systematized form of F445's paywalled-DOI→OA rule. The **DOI is Class-A**, the **TOC is Class-E**, **verify is Class-D+A**, and the **citation graph is Class-L** whose eigenspectrum is the storage signature of peer-reviewed knowledge (F172) — a **scholarly kernel peer to the Wikipedia encyclopedia kernel** (R-RBS-LM-WIKI). The source map (OpenAlex / Crossref / DOAJ / Unpaywall / OpenCitations / PubMed / arXiv / dblp / Semantic Scholar) is all CC0/PD/CC-BY; **dblp** (CC0, 1.0 GB, publisher-`.md5`) is the first pilot, exactly parallel to simplewiki-first, scaling to OpenAlex/Crossref. Favored, not privileged (F398); attests existence+metadata, never truth-of-content; sizes-beyond-dblp flagged for verify.
