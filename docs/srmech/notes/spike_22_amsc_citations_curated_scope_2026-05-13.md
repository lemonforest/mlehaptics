# Spike #22 — AMSC `citations_curated` catalog scope: descriptor + schema + backfill protocol

**Branch:** `research/spike-22-amsc-citations-curated-scope` (from `main` at `a39a28a`)
**Date:** 2026-05-13
**Predecessors:**
- PR #366 (merged): [`citation_hygiene_paywall_policy_2026-05-13.md`](./citation_hygiene_paywall_policy_2026-05-13.md) — the Tier A/B/C/D policy this catalog operationalizes.
- May 2026 spike series #14–#21C plus refined structural law consolidation — the backfill corpus.
- `memory/feedback_pdf_extraction_citation_discipline.md` — the underlying discipline.
- `memory/reference_amsc_catalog_full_ship_procedure.md` — the standard AMSC ship procedure.
- `memory/reference_autonomous_validation_tos_landscape.md` — permitted vs. prohibited sources.
- `memory/project_amsc_handcurated_consumption_channel.md` — `literature_curated` as the universal hand-curated channel.
**Status:** SCOPE-ONLY. Architectural design + descriptor template + schema sketch + backfill protocol + ship sequence + gotchas. No SSOT row added; no codegen mirror; no test ratchet. Implementation is a follow-up ship.
**Tabular sidecar:** None for this spike — design discussion only.

---

## §0. The question and the architectural commitment

User's 2026-05-13 directive (verbatim):

> *"In order to help with the incorrect DOI training data, the new plan should maybe be that even if we can't download from a place, we catalog the open access parts, even if all that is DOI and authors. establish the SSoT into AMSC where a link can always let the user get it themselves... it's a hole we've identified that needs repaired, like a falsified."*

The directive identifies an architectural hole: **citation metadata is currently scattered across spike notes as freeform prose, with no SSoT that records what was verified, by what method, at what tier.** The PR #366 policy specifies *how* to verify; the missing piece is *where to record the verifications* such that:

1. Future spikes can cite a previously-verified paper without re-doing the verification work.
2. A citation correction (e.g., the four catches from the May 2026 arc) updates one place, not N spike notes.
3. The user can dereference any catalog entry to a fetch link — even when the AI agent can't fetch the body of the paper, the user can (Tier C / paywalled cases).
4. The catalog itself is auditable: every entry has attestation (response_sha256 + retrieved_at) per AMSC standard, so the catalog's own metadata is verifiable.

The architectural commitment of this spike: **the catalog lives as an AMSC `literature_curated` sibling, not as a new top-level system.** Per `project_amsc_handcurated_consumption_channel.md`, AMSC already absorbs hand-curated knowledge with citations as its native shape. Citations themselves — title, authors, DOI, arXiv ID, OA status, verification tier — are exactly hand-curated knowledge with citations, recursively. The descriptor + schema + NDJSON triad is the right shape; no new machinery is needed.

This spike scopes:
- §1 (**Q1**) Where the catalog lives — discovered: srmech has no AMSC subtree, so the catalog lands in ephemerides AMSC; honest-negative implication discussed.
- §2 (**Q2**) `descriptor.toml` complete template — implementation-ready.
- §3 (**Q3**) `citation.schema.json` JSON Schema (draft 2020-12) — implementation-ready.
- §4 (**Q4**) Backfill protocol — algorithm sketch, corpus estimate, edge cases.
- §5 (**Q5**) Tier mapping to PR #366 — descriptor-side gate logic.
- §6 (**Q6**) Ship sequence — standard AMSC procedure with srmech-specific deviations called out.
- §7 (**Q7**) Gotchas + honest-negative on a real ambiguity.

The spike is scope-only. Recommendation surface at the end of §7.

---

## §1. Q1 — Where does the catalog live? (srmech AMSC layout discovery)

### §1.1 Discovery result

The srmech project at `docs/srmech/` has the following structure as of `a39a28a`:

```
docs/srmech/
├── .pages
├── srmech_research_notebook.md
├── hoodoos/                       # holdout testcases (PDB / XML)
└── notes/                         # ~186 files: .md spikes, .ndjson sidecars, .py scripts, .png plots
```

**There is no `docs/srmech/research/attested/` subtree.** A `Glob` for `docs/srmech/**/attested/**` and `**/srmech/**/research/**` returns zero matches.

AMSC machinery is currently localized to ephemerides at `docs/antikythera-maths/research/attested/<key>/`, with the codegen mirror at `docs/antikythera-maths/ephemerides-spectral/python/ephemerides_spectral/_research/attested/<key>/` and the test surface at `docs/antikythera-maths/ephemerides-spectral/python/tests/test_attested_collector.py`.

There are 19 existing AMSC catalogs as of `a39a28a` (axial_seamount, cmb_anomalies, cmb_power_spectrum, dynamical_regime, dynamical_regime_probes, earthref_sc, gmrt, hawaii_chain, loki_patera, luna_dynamical_spectrum, mars_dynamical_spectrum, mars_tharsis, mercury_dynamical_spectrum, petdb_v4, pluto_charon_dynamical_spectrum, saturn_rings, sun_dynamical_spectrum, toroidal_residual, yarkovsky_yorp). 16 of those 19 use `adapter = "literature_curated"`.

### §1.2 Path decision

There are three plausible homes for the new catalog. I work through each.

**Option A — Land it in ephemerides AMSC at `docs/antikythera-maths/research/attested/citations_curated/`.**

- Pro: Reuses all existing AMSC machinery (collector, adapter registry, bridge, test ratchet). Zero new infrastructure.
- Pro: The codegen mirror, manifest, and `initial_phases.json` synchronization work without modification.
- Pro: The bridge surface (`list_attested_sources`, `get_attested_descriptor`, `get_attested_dataset`) accessors immediately work for the new catalog.
- Pro: Matches the existing pattern — `dynamical_regime` is a meta-consumer (catalog of catalog rows) already.
- Pro: One project, one AMSC instance is a simpler mental model.
- Con: The catalog's primary consumers are srmech spike notes (not ephemerides ships), so the catalog lives in a directory whose conceptual ownership is ephemerides. This is a *cosmetic* mismatch, not a functional one.
- Con: srmech-side tooling (if any future srmech bridge / CLI exists) would have to reach across into the ephemerides AMSC instance.

**Option B — Build a new srmech AMSC instance at `docs/srmech/research/attested/citations_curated/`.**

- Pro: Conceptually clean — srmech catalogs live in srmech.
- Pro: Future srmech-side tooling has a natural home.
- Con: **Significant infrastructure work.** Would require porting `attested_collector_catalog`, the adapter registry, the descriptor/schema validators, the bridge surface, the test machinery — essentially duplicating ephemerides-spectral's AMSC pillar inside a new srmech-spectral package. Per the `feedback_no_mvp_framing` discipline, this can't be scoped as "minimal port"; it would need to be a full-coverage parallel instance.
- Con: No srmech Python package exists today. There is `docs/antikythera-maths/antikythera-spectral/python/antikythera_spectral/` and `docs/antikythera-maths/ephemerides-spectral/python/ephemerides_spectral/` and `docs/chess-maths/chess-spectral/python/chess_spectral_4d/`, but no `docs/srmech/srmech-spectral/python/srmech_spectral/`. Creating one to host the catalog is a much larger architectural commitment than this spike scopes.

**Option C — Land the SSoT files under srmech notes (`docs/srmech/notes/citations_curated/`) without AMSC integration.**

- Pro: srmech-native; no cross-project reach.
- Con: **Loses every benefit of AMSC.** No attestation (response_sha256), no collector enumeration, no bridge accessors, no test ratchet, no codegen mirror. The catalog becomes a freeform NDJSON file. This is functionally what `unverified.ndjson` in PR #366 §5 already does for Tier D entries — a flat file, not a catalog.

**Decision: Option A.** Land the catalog at `docs/antikythera-maths/research/attested/citations_curated/` and accept the cosmetic ownership mismatch. The functional benefits of reusing AMSC machinery are decisive, and the existing `dynamical_regime` catalog already sets the precedent that an AMSC catalog can be a meta-consumer (a catalog of citations-of-other-rows) rather than a domain-instrument catalog. The catalog's `purpose` field can explicitly identify it as the cross-project citation SSoT.

If a separate srmech-spectral package is created in some future ship (e.g., to host srmech-side bridge / CLI surfaces), this catalog can be moved or mirrored at that time. For the current scope, Option A is the correct choice and the rest of this spike assumes it.

### §1.3 Honest-negative on Option A

The Option A decision has a real cost: it embeds a srmech-primary asset inside the ephemerides directory tree. Future readers may be confused: "why is there a citations catalog under ephemerides when the citations come from srmech spike notes?" The mitigation is explicit framing in the descriptor `purpose` field, in the `[source]` block's `human_readable_name`, and in a top-of-file comment.

A second cost: the catalog will be the largest non-instrument literature_curated entry, with high cardinality of free-text fields (titles, author lists, framing notes). This stresses the AMSC infrastructure in ways the existing instrument-data catalogs don't — particularly around row deduplication and the `data_schema_id` semantic for "the row IS a citation, not a citation OF a row." The schema design in §3 addresses this directly.

A third cost: per `reference_amsc_catalog_full_ship_procedure.md`, the test ratchet hits four tests with hardcoded counts. Adding citations_curated bumps `n_sources` from 19 → 20 across all four. This is mechanical but not zero-cost.

---

## §2. Q2 — `descriptor.toml` complete template

### §2.1 Design considerations

The descriptor must encode:

1. **Source identity** — single catalog with multi-source-fanout enrichment (arXiv first, then Crossref / OpenAlex / Semantic Scholar fallback, leave Tier C/D entries with only the user_fetch_link).
2. **Adapter selection** — `literature_curated`, per the precedent. The catalog is hand-curated; fetch is not a remote API call to a citation index, it is a curated NDJSON written by the spike-author + verification process.
3. **Per-row verification provenance** — every row records *how* and *when* it was verified, against *which* upstream source, and at *which* tier. This is the load-bearing distinction from a normal AMSC catalog: each row is not just a data point but a verification record.
4. **Rendering templates** — cite_as / purpose / user_fetch_link rendering that produces a usable citation block from the catalog row, including the explicit tier flag from PR #366.
5. **Attestation** — standard AMSC fields (response_sha256, retrieved_at, parser_version, parser_rule_hash, collector_descriptor_path, collector_descriptor_hash). The attestation envelope wraps the catalog row; per-row verification metadata is separate.
6. **Gap targeting** — for citations_curated, gap_targeting doesn't map naturally to regime_labels the way instrument catalogs do. Instead, it can declare tier-gating rules ("entries below Tier B are quarantined").

### §2.2 Complete descriptor template

The following is an implementation-ready `descriptor.toml`. Comments are extensive because the catalog is the SSoT for citation hygiene across the project and future readers / future spike authors must be able to read the descriptor and understand exactly what the catalog is for.

```toml
# Citations Curated — SSoT for citation metadata across srmech / ephemerides
# spike notes.
#
# This catalog is the operational artifact of the Tier A/B/C/D citation-
# hygiene policy established in PR #366
# (docs/srmech/notes/citation_hygiene_paywall_policy_2026-05-13.md).
# Per-row verification metadata records:
#   - The bibliographic record (title, authors, year, venue, DOI, arXiv ID).
#   - The verification method (PDF-extracted, abstract-via-DOI, etc).
#   - The verification tier (A / B / C / D per PR #366).
#   - The verification date (when the verification was performed; later
#     re-verifications append a new row, not update in-place — see §7
#     of the source-spike note for the revision-discipline rationale).
#   - The first spike note that cited the paper (for traceability).
#   - The user_fetch_link (a URL the user can paste in a browser; for
#     paywalled-to-AI-agent papers, this is what makes the catalog
#     useful — the user gets it themselves).
#
# The catalog is the cross-project citation SSoT despite living under
# the ephemerides AMSC tree, because (i) AMSC machinery is currently
# only instantiated there, (ii) the literature_curated adapter already
# absorbs hand-curated-knowledge-with-citations as its native shape,
# and (iii) creating a parallel srmech AMSC instance to house this
# single catalog would be disproportionate infrastructure work. See
# Spike #22 scope note (docs/srmech/notes/spike_22_amsc_citations_curated_scope_2026-05-13.md)
# for the path-decision discussion.
#
# Multi-source verification path (per row, recorded in `verification_method`):
#   1. arXiv (preferred for 1991+ physics / math / CS preprints):
#      https://arxiv.org/abs/<arxiv_id> — abstract page is PDF-grade
#      metadata source (title, authors, date, abstract). Tier A.
#   2. Crossref REST (preferred for DOI metadata):
#      https://api.crossref.org/works/<doi> — clean JSON, title +
#      author list + year + venue. Tier B.
#   3. OpenAlex (broad coverage):
#      https://api.openalex.org/works/doi:<doi> — title + authors +
#      OA status + concepts. Tier B.
#   4. Semantic Scholar Graph API (corroboration + abstract):
#      https://api.semanticscholar.org/graph/v1/paper/DOI:<doi>?fields=title,authors,year,journal,abstract,openAccessPdf
#      — Tier B, often elevates to Tier A via openAccessPdf URL.
#   5. Publisher landing page via DOI redirect:
#      https://doi.org/<doi> — Tier B *only when accessible*; Wiley /
#      Elsevier / Springer / Nature / APS / IEEE return 402/403 to
#      AI agents and the verification must use indexes 1-4 instead.
#   6. ResearchGate / preprint mirror — Tier C, never relied on alone
#      (see PR #366 §3 worked example).
#
# Catalog rows are added (not updated in-place) when:
#   - A new citation appears in a srmech / ephemerides spike note.
#   - A previously-cited paper undergoes re-verification at a higher
#     tier (Tier C → Tier B; Tier B → Tier A).
#   - A previously-cited paper's framing_note is refined by a later
#     spike (the new row supersedes the older one via the
#     `supersedes` field; both rows are retained for audit).
#
# Catalog rows are NEVER modified in-place. The append-only discipline
# protects historical audit trails against silent rewrites (which is
# exactly the failure mode that "training-data DOI corruption" produces
# in upstream LLMs — the corrected version of a fact replaces the
# original without trace, and we lose the ability to see which version
# of the fact a given spike was built against).

[source]
key = "citations_curated"
human_readable_name = "Citations Curated — Cross-Project Citation SSoT"
purpose = "operational SSoT for the Tier A/B/C/D citation-hygiene policy (PR #366); each row records one verified citation with method + tier + date + user_fetch_link, supporting cross-spike citation reuse and audit"
license = "literature-curated metadata only (titles, authors, DOIs, arXiv IDs, OA status); no body text or full abstracts stored — the catalog respects publisher copyright by storing only the metadata layer that the citation indexes themselves freely expose"
homepage = "https://github.com/lemonforest/mlehaptics/blob/main/docs/srmech/notes/citation_hygiene_paywall_policy_2026-05-13.md"
canonical_doi = ""
# canonical_doi is intentionally empty: this catalog has no single canonical
# upstream paper. Each row carries its own source_doi / arxiv_id; the
# catalog as a whole is a project artifact, not a published-paper-derived
# dataset.

[fetch]
adapter = "literature_curated"
ndjson_path = "row.ndjson"

[parse]
# Each row must carry at least one of (source_doi, arxiv_id, user_fetch_link)
# per the schema's anyOf constraint (see citation.schema.json §3.3).
# require_per_row_source_doi is intentionally false here because Tier C/D
# entries may have only a user_fetch_link with no resolvable DOI.
require_per_row_source_doi = false

[schema]
data_schema_id = "citations_curated.row.v1"
data_schema_path = "row.schema.json"

[rendering]
# cite_as_template produces a citation string suitable for inclusion in a
# spike note's source list. The tier flag is appended in square brackets
# per PR #366 §2 notation.
cite_as_template = "{schema.authors_compact} ({schema.year}). \"{schema.title}\". {schema.venue}, doi:{schema.doi} [Tier {schema.verification_tier} — {schema.verification_method}, verified {schema.verification_date}]."
# purpose_template renders a one-line description of why this citation is
# in the catalog.
purpose_template = "verified citation for {schema.key}: {schema.title}; first cited in {schema.first_cited_in}; tier {schema.verification_tier}"
# user_fetch_link_template constructs a click-through URL the user can
# paste in a browser. Preference: arXiv > DOI > literal user_fetch_link
# field. (The template uses {schema.user_fetch_link} which the row's
# parser will populate via the priority above; raw arxiv_id and doi
# remain as separate fields for index lookup.)
user_fetch_link_template = "{schema.user_fetch_link}"

[attestation]
hash_response = true
hash_algorithm = "sha256"
required_fields = [
    "source_doi",
    "source_url",
    "license",
    "retrieved_at",
    "response_sha256",
    "parser_version",
    "parser_rule_hash",
    "collector_descriptor_path",
    "collector_descriptor_hash",
]
# Note on attestation semantics for this catalog:
#   - The response_sha256 attests the NDJSON file's row, not an external
#     API response (which the catalog does not store — only metadata
#     fields are extracted into per-row verification_evidence).
#   - retrieved_at is the catalog-row's first-write date, NOT the
#     paper's publication date (that lives in `year` and
#     `source_published_date`).
#   - parser_version increments when the per-row data_schema or
#     verification-method enum changes.

[gap_targeting]
# citations_curated does not target gaps in dynamical-regime classifier
# space (it is not an instrument catalog). Instead it targets gaps in
# verification-tier coverage: which papers are quarantined (Tier C/D),
# which are pending re-verification, which have multiple competing
# attributions.
#
# A future srmech gap-suggester (analogous to the ephemerides
# attested_collector_gap_suggester) could read this catalog and flag:
#   - Citations at Tier C/D that are load-bearing in some spike.
#   - Citations whose user_fetch_link returns 404 on user-side check.
#   - Citations with `supersedes` chains indicating prior errors.
#
# For now, gap_targeting carries only the tier-quarantine flag; no
# regime_labels are declared (the catalog is not a regime-classifier row
# set).
tier_quarantine_threshold = "C"
# Entries at Tier C or D are flagged as quarantined in the catalog's
# rendered output (the cite_as_template appends the Tier flag verbatim,
# so Tier C/D entries are visually distinguishable). The threshold is
# documented here for downstream tooling.
regime_labels = []
```

### §2.3 Notes on the descriptor design

The descriptor is implementation-ready as written. Three design choices deserve explicit justification.

**Design choice 1: `require_per_row_source_doi = false`.** This is the explicit difference from instrument catalogs like cmb_power_spectrum where every row has a DOI (the cited paper of record). Citation catalog rows may legitimately lack a DOI — pre-DOI era papers (Hawking 1975 *Comm. Math. Phys.* has no DOI per CrossRef as of catalog scope; the standard practice is to cite the journal+volume+page directly), conference proceedings, textbook references, and any Tier D snippet-only citation. The schema's `anyOf` (see §3) requires at least one of doi / arxiv_id / user_fetch_link, which is the right looser constraint.

**Design choice 2: `canonical_doi = ""` (empty).** Existing literature_curated catalogs all have a canonical_doi pointing at the upstream paper that defines the dataset. citations_curated has no upstream paper — it is a project artifact, not a published dataset. Empty-string is the cleanest representation; the schema validators in `attested_collector_catalog._descriptor` should already permit this (the field is typed as a Crossref-shaped DOI string and empty is the unset value), but the ship will need to verify this against the actual validator.

**Design choice 3: `[gap_targeting]` carries `tier_quarantine_threshold`, not `regime_labels`.** Per the existing gap-suggester architecture, `regime_labels` are how an instrument catalog declares the dynamical-regime types its rows represent. citations_curated doesn't declare regime labels (it is meta-consumer-shaped); instead it declares a tier threshold for downstream gap-targeting. This is the load-bearing innovation in the descriptor design and may require a small extension to the descriptor-parsing code to recognize `tier_quarantine_threshold` as a valid gap_targeting key. Alternative: collapse the field into a free-text comment in `[gap_targeting]` and let downstream tooling read it as a documentation artifact rather than a structured field — this is the safer path for an initial ship.

---

## §3. Q3 — `citation.schema.json` JSON Schema

### §3.1 Design considerations

The schema must:

1. Accept the citation record shape proposed in the conductor's brief (key, doi, arxiv_id, title, authors, year, venue, user_fetch_link, oa_status, verification_tier, verification_method, verification_date, first_cited_in, framing_note).
2. Require at least one of (doi, arxiv_id, user_fetch_link) — `anyOf` on those three.
3. Forbid full text body (only metadata).
4. Cap free-text fields at sensible limits (titles ≤ 500 chars, framing_note ≤ 2000 chars) to enforce that the catalog stores metadata, not content.
5. Use enums for tier, oa_status, verification_method to enforce vocabulary discipline.
6. Support the supersedes / also_cited_in / cross_references chain for the append-only revision model.
7. Match existing AMSC schema conventions (draft 2020-12, `$id` matching `data_schema_id` from the descriptor, `entered_locally_at` field for AMSC-side attestation date, free `additionalProperties: true` for forward-compatibility).

### §3.2 Schema (JSON Schema draft 2020-12)

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "citations_curated.row.v1",
  "title": "Citation record",
  "description": "One verified citation entry. Records the bibliographic identity (title, authors, year, venue, doi, arxiv_id), the verification provenance (tier, method, date), the project context (first_cited_in, also_cited_in, framing_note), and the user-side fetch path (user_fetch_link, oa_status). Append-only: corrections create new rows with `supersedes` chains, never modify existing rows.",
  "type": "object",
  "required": [
    "key",
    "row_type",
    "title",
    "authors",
    "authors_compact",
    "year",
    "verification_tier",
    "verification_method",
    "verification_date",
    "first_cited_in",
    "entered_locally_at"
  ],
  "anyOf": [
    {"required": ["doi"]},
    {"required": ["arxiv_id"]},
    {"required": ["user_fetch_link"]}
  ],
  "additionalProperties": true,
  "properties": {
    "key": {
      "type": "string",
      "pattern": "^[a-z][a-z0-9_]*[a-z0-9]$",
      "minLength": 3,
      "maxLength": 64,
      "description": "Stable identifier for this citation. Convention: lastname-of-first-author + year + short-title-token, e.g. 'verlinde2016emergent' or 'penington2019entanglement'. Used as the citation reference key in spike notes via `[[citation:<key>]]` (see §7.2 of source-spike note for the syntax)."
    },
    "row_type": {
      "type": "string",
      "enum": ["citation"],
      "description": "Single value; reserved for future expansion if the catalog evolves to record other citation-adjacent artifacts (e.g., 'venue' rows recording journal-level metadata)."
    },
    "title": {
      "type": "string",
      "minLength": 1,
      "maxLength": 500,
      "description": "Full title of the paper, exactly as it appears in the verified source (publisher landing page, arXiv abstract page, or PDF first page). No editorial annotations; no truncation."
    },
    "authors": {
      "type": "array",
      "items": {"type": "string", "minLength": 1, "maxLength": 200},
      "minItems": 1,
      "maxItems": 200,
      "description": "Author list in publication order. Each entry is a single author's name in the source's chosen form (e.g., 'Verlinde, Erik P.' or 'Penington, G.'). Compact form is in authors_compact field."
    },
    "authors_compact": {
      "type": "string",
      "minLength": 1,
      "maxLength": 300,
      "description": "Compact rendering of the author list for citation strings: solo paper -> 'Lastname'; two authors -> 'Lastname1 & Lastname2'; 3-5 -> 'Lastname1, Lastname2, ..., LastnameN'; 6+ -> 'Lastname1 et al.'. Stored explicitly (not computed) to preserve any source-specific compact form (e.g., 'AEMM' or 'BPZ')."
    },
    "year": {
      "type": "integer",
      "minimum": 1600,
      "maximum": 2100,
      "description": "Publication year of the cited venue (NOT the arXiv first-upload year if the published paper is later)."
    },
    "venue": {
      "type": ["string", "null"],
      "maxLength": 300,
      "description": "Journal / conference / publisher name as it appears in the canonical citation form (e.g., 'Communications in Mathematical Physics' or 'JHEP 2011(4)' or 'arXiv preprint' for unpublished preprints)."
    },
    "doi": {
      "type": ["string", "null"],
      "pattern": "^10\\.[0-9]{4,}/.+$",
      "description": "Crossref DOI for the published paper, if assigned. Null for pre-DOI papers or unpublished preprints."
    },
    "arxiv_id": {
      "type": ["string", "null"],
      "pattern": "^(([a-z\\-]+/[0-9]{7})|([0-9]{4}\\.[0-9]{4,5}))(v[0-9]+)?$",
      "description": "arXiv identifier in either old-style (e.g., 'gr-qc/9504004') or new-style (e.g., '1611.02269' or '1905.08255v2') form. Null for non-arXiv papers."
    },
    "user_fetch_link": {
      "type": ["string", "null"],
      "format": "uri",
      "maxLength": 500,
      "description": "URL the user can paste in a browser to retrieve the paper. Preference order in the row-author's choice: (1) arXiv abs page, (2) publisher DOI redirect URL, (3) institutional repo / preprint mirror PDF URL. For paywalled-to-AI-agent papers (Wiley, Elsevier, etc.), this is the load-bearing field — the AI agent can't fetch the body, but the user can."
    },
    "oa_status": {
      "type": ["string", "null"],
      "enum": ["green", "gold", "hybrid", "bronze", "closed", null],
      "description": "Open-access status per OpenAlex / Unpaywall conventions. green=author-archived preprint available; gold=publisher-OA on publication; hybrid=OA in subscription journal; bronze=free-to-read without explicit license; closed=paywalled with no OA copy. Null when not determined."
    },
    "verification_tier": {
      "type": "string",
      "enum": ["A", "B", "C", "D"],
      "description": "Tier per PR #366: A=PDF-extracted; B=publisher-DOI-abstract-verified-with-2-index-corroboration; C=ResearchGate/preprint-mirror-only (FLAGGED); D=search-snippet-only (REJECT for primary citations)."
    },
    "verification_method": {
      "type": "string",
      "enum": [
        "pdf_extract_arxiv",
        "pdf_extract_publisher",
        "pdf_extract_institutional_repo",
        "pdf_extract_authorpage",
        "abstract_doi_crossref_corroborated",
        "abstract_doi_openalex_corroborated",
        "abstract_doi_semantic_scholar_corroborated",
        "abstract_doi_pubmed_corroborated",
        "abstract_publisher_landing_two_index_corroborated",
        "researchgate_filename_flagged",
        "researchgate_pdf_extracted_flagged",
        "search_snippet_only_flagged",
        "user_provided_unverified",
        "pre_2010_canonical_no_reverify",
        "secondary_source_reference_list"
      ],
      "description": "How this citation was verified. The enum names encode both the source and the corroboration level. `pre_2010_canonical_no_reverify` covers the discipline counter-clause from `feedback_pdf_extraction_citation_discipline.md`. `user_provided_unverified` is for citations the user supplied that have not yet been verified — these should be re-verified before being relied on."
    },
    "verification_date": {
      "type": "string",
      "format": "date",
      "description": "ISO 8601 date when verification was performed. For pre-2010-canonical entries, this is the date of catalog entry, not the original publication date (which lives in `year`)."
    },
    "verification_evidence": {
      "type": ["string", "null"],
      "maxLength": 1000,
      "description": "Free-text record of what was checked. E.g., 'arXiv abstract page title + author list confirmed; first-page PDF metadata matches'; or 'Crossref API and OpenAlex API both return identical title + author list; publisher landing page returned 402 to AI agent'. Used for audit when a later spike disputes the verification."
    },
    "first_cited_in": {
      "type": "string",
      "minLength": 5,
      "maxLength": 200,
      "description": "Filename of the spike note where this citation first appeared, e.g., 'spike_19_mfo_hawking_radiation_dof_mismatch_2026-05-13.md'."
    },
    "also_cited_in": {
      "type": "array",
      "items": {"type": "string", "minLength": 5, "maxLength": 200},
      "maxItems": 100,
      "description": "Additional spike note filenames that cite this paper. Updated when a later spike note references the same paper. Append-only: a later spike's reference is added; no existing entries are removed."
    },
    "framing_note": {
      "type": ["string", "null"],
      "maxLength": 2000,
      "description": "How this paper is framed in srmech / ephemerides spike notes. Records project-specific interpretation, distinguishing claims that the paper actually makes from claims the project attributes to it. Example: 'predicts emergent dark MATTER (MOND-like), NOT dark energy — caught in Spike #21A'. The framing_note is the load-bearing field for the misattribution-prevention discipline."
    },
    "caveat": {
      "type": ["string", "null"],
      "maxLength": 1000,
      "description": "Free-text caveat about the citation. E.g., 'arXiv ID shares prefix with unrelated paper 1905.08762; ensure 1905.08255 is used for Penington'. Caveats are appended to a row at the time the issue is identified; if the issue is later resolved, a new row supersedes this one (see `supersedes`)."
    },
    "supersedes": {
      "type": ["string", "null"],
      "pattern": "^[a-z][a-z0-9_]*[a-z0-9]$",
      "description": "Key of an earlier catalog row this row supersedes (e.g., an earlier-attributed misattribution that has been corrected). The earlier row is retained; the new row's supersedes field points to it. Read-time consumers should prefer the latest non-superseded row for a given citation-of-record."
    },
    "superseded_by": {
      "type": ["string", "null"],
      "pattern": "^[a-z][a-z0-9_]*[a-z0-9]$",
      "description": "Key of a later catalog row that supersedes this one. Set ONLY when a later row is added; never removed. Read-time consumers see this and follow the chain forward."
    },
    "cross_references": {
      "type": "array",
      "items": {"type": "string", "pattern": "^[a-z][a-z0-9_]*[a-z0-9]$"},
      "maxItems": 100,
      "description": "Keys of other citations in this catalog that are topically related (cited together, foundational predecessors, refinements). Used for downstream gap-targeting and citation-chain visualization."
    },
    "source_doi": {
      "type": "string",
      "minLength": 0,
      "description": "AMSC required field: DOI of the cited reference (mirrors `doi` field above; populated for AMSC attestation compatibility). Empty string when no DOI."
    },
    "source_published_date": {
      "type": ["string", "null"],
      "pattern": "^[0-9]{4}(-[0-9]{2}(-[0-9]{2})?)?$",
      "description": "ISO 8601 partial date for the cited venue's publication date."
    },
    "entered_locally_at": {
      "type": "string",
      "format": "date",
      "description": "ISO 8601 date when this row was first added to the catalog."
    }
  }
}
```

### §3.3 Notes on the schema design

**Note 1: `anyOf` on (doi, arxiv_id, user_fetch_link).** This is the minimal-identification constraint — every citation in the catalog must have at least one machine-resolvable identifier. A Tier D snippet-only citation may have only a user_fetch_link (e.g., a Google Scholar result page); that is permitted (and quarantined per the tier policy) but the row cannot be both DOI-less and arXiv-less and user-fetch-link-less. The constraint is checked at catalog-write time, not catalog-read time.

**Note 2: Forbidden content (full text body, abstracts > 500 chars).** The schema's `framing_note` cap of 2000 chars and the absence of any `abstract` or `body_text` field is the load-bearing copyright respect. The catalog is a metadata SSoT; it stores titles, authors, identifiers, and project-specific framing — not paper content. Future tooling that wants to query abstracts should use the upstream APIs (Semantic Scholar Graph API), not the catalog.

**Note 3: `supersedes` / `superseded_by` chain.** Append-only revision is the right discipline for two reasons:
- Forensic traceability: future readers should be able to see that "in May 2026, AEMM was attributed to arXiv:1905.08762 — *and the catalog says so* — and the same catalog also says this attribution was superseded by a row dated 2026-05-13-after-PDF-verification confirming the same ID."
- LLM-training-data-corruption mitigation: the user's stated motivation ("incorrect DOI training data") implies that some prior LLM may have memorized a wrong DOI. The catalog's append-only history is a counterweight: even if a wrong DOI is asserted somewhere, the catalog records what was verified, by whom, with what method, and what later correction (if any) superseded the original entry.

**Note 4: Enum-controlled `verification_method`.** Fifteen distinct values. This may seem excessive, but the cost of an open string field is exactly the problem the catalog is designed to solve: ambiguous "verified somehow" claims with no enforced vocabulary. The enum codifies what counts as which tier and supports downstream gap-suggesters ("show me all entries with `researchgate_filename_flagged`").

**Note 5: `additionalProperties: true`.** Per existing AMSC catalog conventions, the schema is forward-compatible. Future fields (e.g., `pdftotext_sha256` to attest the PDF extraction itself, or `crossref_response_sha256` to attest the Crossref API response) can be added without invalidating existing rows.

**Note 6: AMSC compatibility fields.** `source_doi`, `source_published_date`, `entered_locally_at` are required by AMSC's row-level attestation. They mirror `doi` / `year` / catalog-entry-date but are duplicated explicitly because AMSC's collector expects them by exact name. The schema enforces this duplication.

---

## §4. Q4 — Backfill protocol

### §4.1 Source corpus

The May 2026 spike series + consolidation note + comparative-ethology scope notes form the backfill corpus:

| File | Citation density (grep -c arXiv\|DOI) |
|------|-------|
| spike_12b_lie_algebroid_ky_bracket_scope_2026-05-13.md | 18 |
| spike_12c_virasoro_liouville_nekrasov_scope_2026-05-13.md | 16 |
| spike_13_candidate_anisotropic_interior_chaos_scope_2026-05-13.md | 15 |
| spike_14_abelian_wall_structural_law_test_2026-05-13.md | 3 |
| spike_15_heun_monodromy_test_2026-05-13.md | 21 |
| spike_16_painleve_algebraic_classification_2026-05-13.md | 19 |
| spike_17_spherical_harmonics_higher_d_2026-05-13.md | 2 |
| spike_18_heisenberg_representations_2026-05-13.md | 0 (no inline citations) |
| spike_19_mfo_hawking_radiation_dof_mismatch_2026-05-13.md | 8 inline arXiv refs + ~12 bibliographic entries |
| refined_structural_law_consolidation_2026-05-13.md | 7 |
| spike_19b / spike_20 / spike_21A,B,C (post-2026-05-13) | ~30 additional |
| Earlier May spikes (#11, #12A on Kerr) | ~20 |

Total raw citation-string count: approximately 150–180. After deduplication (canonical works like Hawking 1975, Bekenstein 1973, Penrose-Floyd 1973, BPZ 1984 are cited in many spikes), the unique-citation count is estimated **60–80**.

### §4.2 Walk algorithm

The backfill operates as a script (run-once, out-of-repo per `reference_autonomous_validation_tos_landscape.md` policy §3 — single-paper-verification CLI tools are OK, but the script itself is not committed to the repo because it is a one-shot data-prep tool, not project machinery).

**Algorithm:**

```
1. For each file in CORPUS:
   a. Read the markdown.
   b. Run regex extraction for citation patterns:
      - arXiv ID: \barXiv:?[/]?([a-z\-]+/[0-9]{7}|[0-9]{4}\.[0-9]{4,5})(v[0-9]+)?\b
      - DOI: \b10\.[0-9]{4,}/[^\s)\]]+\b
      - Author-year inline: \b([A-Z][a-z]+(?:[-A-Z][a-z]+)?)\s+\(?([0-9]{4})\)?\b (high false-positive rate; manual filtering)
      - Bibliographic entries: lines starting with name-Lastname, M. (year) ... pattern
   c. For each extracted candidate, produce a candidate-row record.

2. Deduplicate by (doi, arxiv_id) pair across all files.
   - Two candidates are the same paper if they share a DOI or share an arXiv ID.
   - Conflicts (same DOI, different titles) flag a manual-review row.

3. For each unique candidate, verify via the multi-source path:
   a. If arxiv_id is present, fetch https://arxiv.org/abs/<arxiv_id>.
      - On success: extract title, authors, year, abstract from arXiv page metadata.
      - Tier A if PDF is retrievable; Tier B if only abstract page.
   b. If doi is present, query Crossref REST:
      https://api.crossref.org/works/<doi>?
      - On success: extract title, authors, year, venue.
      - Tier B (Crossref-corroborated).
   c. Query OpenAlex:
      https://api.openalex.org/works/doi:<doi>?
      - On success: extract OA status + abstract + concepts (no body).
   d. Query Semantic Scholar Graph API:
      https://api.semanticscholar.org/graph/v1/paper/DOI:<doi>?fields=title,authors,year,journal,abstract,openAccessPdf
      - On success: corroborate title + author list + retrieve openAccessPdf URL if exists.
      - If openAccessPdf is non-null: elevate to Tier A by fetching the PDF.
   e. If all of (a)-(d) fail:
      - Try publisher DOI redirect (https://doi.org/<doi>).
        - 200 OK: Tier B publisher-page-verified.
        - 402/403: Tier C/D fallback.
      - Try ResearchGate / institutional repo search.
        - Per `reference_autonomous_validation_tos_landscape.md`, ResearchGate is
          TOS-prohibited for automation; the script does NOT attempt this. The row
          is flagged for user-side completion.
      - If nothing succeeds, row stays as Tier D with verification_method =
        search_snippet_only_flagged.

4. For pre-2010 canonical works (Hawking 1975, Bekenstein 1973, etc.):
   - Detect by year < 2010 AND venue ∈ {Comm. Math. Phys., Phys. Rev., Phys. Rev. D, Phys. Rev. Lett., Nature, J. Math. Phys., Rev. Mod. Phys., ...}.
   - Skip the full multi-source verification.
   - Set verification_method = pre_2010_canonical_no_reverify per discipline counter-clause.
   - Tier B by default (the catalog records the citation as verified-by-canonical-status).

5. For each verified candidate, construct a citation row:
   - key = lastname-firstauthor + year + first-significant-title-token
     (Verlinde 2011 "On the origin..." -> verlinde2011origin)
   - All schema-required fields populated.
   - framing_note left empty initially (later spike-author fills in
     project-specific framing as needed).
   - first_cited_in = filename where the citation first appeared
     (determined by file-modification-date sort).
   - also_cited_in = list of other filenames where the citation appears.

6. Manual review pass:
   - Resolve all conflict-flag rows.
   - Spot-check 20-30 random rows against the upstream source.
   - Cross-check the four known May-2026 catches (the three from
     `feedback_pdf_extraction_citation_discipline.md` + Dunbar & Shultz
     from PR #366) — confirm the correct attribution is in the catalog
     and that any earlier wrong attribution (if it appeared in a spike
     note) is recorded with `supersedes` pointing to the correction.

7. Write the initial row.ndjson with all verified rows.
   - Approximately 60-80 rows for the May 2026 arc.
   - Each row gets entered_locally_at = "2026-05-13".
```

### §4.3 Edge cases

**Edge case 1: Pre-2010 canonical with no arXiv (Hawking 1975).** Per discipline counter-clause, no PDF re-verification needed. Catalog entry: `verification_method = "pre_2010_canonical_no_reverify"`, `verification_tier = "B"`, `arxiv_id = null`, `doi = null` (1975 papers may have backfilled DOIs via Crossref; check per case), `user_fetch_link = "https://doi.org/10.1007/BF02345020"` (if a backfilled DOI exists) or empty.

**Edge case 2: Paywalled-only with no OA copy (e.g., a Wiley journal article).** AI agent cannot reach the body. Tier B via two-index cross-corroboration (Crossref + OpenAlex). user_fetch_link = `https://doi.org/<doi>` for user-side access. oa_status = "closed".

**Edge case 3: Tool-flagged-in-doc citations.** The May 2026 arc includes citations the spike-author already PDF-extracted and verified within the doc (e.g., Spike #19 explicitly notes "I have not freshly PDF-verified Verlinde 2011 in this session"). For these, the catalog records the in-doc state — Tier B with verification_method = `abstract_doi_crossref_corroborated` and a caveat noting the in-doc context. A future spike can elevate to Tier A by performing the PDF extraction.

**Edge case 4: The AEMM ID confusion (Spike #19 §2.9).** Both Penington 2019 and AEMM 2019 were tentatively listed as `arXiv:1905.08762`, which is wrong for one of them. The correct attribution per the post-spike correction commit `eab2ce0` is:
- Penington 2019 → `arXiv:1905.08255`
- AEMM 2019 → `arXiv:1905.08762`

Backfill must encode both correctly as separate rows. The wrong-attribution episode itself can optionally be encoded in the `caveat` field of the AEMM row ("arXiv ID 1905.08762 was tentatively conflated with Penington's 1905.08255 in spike_19's first draft; correction committed in eab2ce0").

**Edge case 5: The Dunbar & Shultz 2021 case (PR #366 §3).** Catalog should encode Dunbar & Shultz with the corrected author list, verification_tier = "B" via Manchester institutional repo + Semantic Scholar Graph API. A `caveat` field can note: "earlier scope file `comparative_ethology_gap_closure_scope_2026-05-13.md` cited as 'Dunbar (2021)' — missing Shultz as coauthor; correction tracked in PR #366 §6". This is the worked-example case for the catalog's audit-trail value.

**Edge case 6: Verlinde 2011 vs Verlinde 2016 (Spike #21A correction).** The Spike #21A finding refuted a previously-asserted "emergent dark energy" attribution for Verlinde 2016, correcting it to "emergent dark matter (MOND-like)". Catalog should have two rows:
- `verlinde2011origin` for arXiv:1001.0785 (the 2011 entropic-gravity paper).
- `verlinde2016emergent` for arXiv:1611.02269 (the 2016 emergent-gravity-dark-universe paper, with framing_note explicitly stating "predicts emergent dark MATTER (MOND-like), NOT dark energy — caught in Spike #21A; matter-vs-energy distinction is load-bearing per the consolidation row").

This is the canonical user-visible value of the catalog: a future spike author writing about Verlinde 2016 will see the framing_note and not repeat the dark-energy misattribution.

### §4.4 Estimated corpus size and ship sizing

| Quantity | Estimate |
|---|---|
| Unique citations across May 2026 arc | 60-80 |
| Pre-2010 canonical (Hawking, Bekenstein, BPZ, Penrose, Wald, Carter, etc.) | 25-35 |
| 2010-2019 (Verlinde, Padmanabhan, Mathur, etc.) | 10-15 |
| 2020+ requiring full verification | 20-35 |
| Tier A achievable (arXiv + PDF extraction works) | 35-50 |
| Tier B (publisher-paywalled or arXiv-only-abstract) | 15-25 |
| Tier C (only ResearchGate / preprint mirror reachable) | 0-5 |
| Tier D (search-snippet-only, REJECT or quarantine) | 0-3 |

NDJSON file size estimate: 60-80 rows × ~1.5 KB/row = approximately 100-120 KB. This is well within existing catalog sizes (cmb_power_spectrum is 111 rows at similar density).

Backfill effort estimate: 4-6 hours of focused work for the script + manual review pass. The script can be run iteratively (one spike-file at a time) to permit early-error detection.

---

## §5. Q5 — Tier mapping to PR #366 four-tier policy

The PR #366 policy specifies four tiers. The catalog operationalizes them as follows.

**Tier A — PDF-extracted-verified.** Catalog entry has `verification_tier = "A"` and `verification_method ∈ {pdf_extract_arxiv, pdf_extract_publisher, pdf_extract_institutional_repo, pdf_extract_authorpage}`. The user_fetch_link points to a PDF; oa_status is one of {green, gold, bronze} (closed → can't be Tier A by definition; pre_2010_canonical → Tier B per the counter-clause). Tier A entries are the most reliable and are NOT quarantined.

**Tier B — Publisher-DOI-abstract-verified.** Catalog entry has `verification_tier = "B"` and `verification_method` ∈ {abstract_doi_crossref_corroborated, abstract_doi_openalex_corroborated, abstract_doi_semantic_scholar_corroborated, abstract_doi_pubmed_corroborated, abstract_publisher_landing_two_index_corroborated, pre_2010_canonical_no_reverify}. The catalog enforces (via the verification_method enum and the require_per_row_source_doi or anyOf constraint) that EITHER a DOI OR a clearly-canonical pre-2010 paper-of-record is present. Tier B entries are NOT quarantined.

**Tier C — ResearchGate / preprint-server-verified (FLAGGED).** Catalog entry has `verification_tier = "C"` and `verification_method ∈ {researchgate_filename_flagged, researchgate_pdf_extracted_flagged}`. The descriptor's `tier_quarantine_threshold = "C"` declares that Tier C entries are quarantined. The cite_as_template renders the explicit "[Tier C — ...]" flag inline so downstream consumers see it.

**Tier D — Search-snippet-only (REJECT for primary citations).** Catalog entry has `verification_tier = "D"` and `verification_method ∈ {search_snippet_only_flagged, user_provided_unverified, secondary_source_reference_list}`. Quarantined per the threshold. The catalog explicitly records these (rather than excluding them) because the user's "even if all that is DOI and authors" directive applies — *some* metadata is better than no record, as long as the tier flag is honest.

The descriptor-side gate (`[gap_targeting] tier_quarantine_threshold = "C"`) is the load-bearing operationalization: downstream tooling that reads the catalog should treat Tier C/D entries as flagged and surface them for re-verification before any external publication.

---

## §6. Q6 — Ship sequence

Following the standard procedure from `reference_amsc_catalog_full_ship_procedure.md`, with srmech-specific deviations called out.

### §6.1 Standard 4-commit sequence

**Commit 1 — SSOT files** (3 files):

```
docs/antikythera-maths/research/attested/citations_curated/descriptor.toml
docs/antikythera-maths/research/attested/citations_curated/row.schema.json
docs/antikythera-maths/research/attested/citations_curated/row.ndjson
```

Message: `ship(amsc): citations_curated — descriptor + schema + initial backfill of May 2026 spike arc`.

**Commit 2 — Codegen mirror + manifest**:

```
docs/antikythera-maths/ephemerides-spectral/python/ephemerides_spectral/_research/attested/citations_curated/descriptor.toml
docs/antikythera-maths/ephemerides-spectral/python/ephemerides_spectral/_research/attested/citations_curated/row.schema.json
docs/antikythera-maths/ephemerides-spectral/python/ephemerides_spectral/_research/attested/citations_curated/row.ndjson
docs/antikythera-maths/ephemerides-spectral/python/ephemerides_spectral/_data/manifest.json
docs/antikythera-maths/ephemerides-spectral/python/ephemerides_spectral/_data/initial_phases.json
```

Message: `chore(amsc): regenerate _research mirror + manifest for citations_curated`.

Per the procedure's non-obvious gotcha: `initial_phases.json` MUST be committed alongside the regenerated manifest even though codegen-reproducibility CI excludes it. (The procedure memory documents the two distinct CI gates with different exclusion sets.)

**Commit 3 — initial_phases.json sync** (if it diverges in re-run):

```
docs/antikythera-maths/ephemerides-spectral/python/ephemerides_spectral/_data/initial_phases.json
```

Message: `chore(amsc): sync initial_phases.json with manifest`.

**Commit 4 — Test ratchet** (1 file, 4 tests):

```
docs/antikythera-maths/ephemerides-spectral/python/tests/test_attested_collector.py
```

- `test_discover_descriptors_finds_committed_pilots`: add `"citations_curated"` to sorted list (between `cmb_power_spectrum` and `dynamical_regime`); add `assert found["citations_curated"].adapter_name == "literature_curated"`.
- `test_bridge_list_attested_sources_returns_committed_pilots`: bump `n_sources` from 19 → 20; add `"citations_curated"` to expected sorted list.
- `test_bridge_list_attested_sources_curated_class_filter`: bump n_sources by 1; add to expected keys.
- `test_bridge_list_attested_sources_specific_adapter_filter`: bump n_sources by 1 (for the literature_curated adapter filter).

Message: `test(amsc): update test_attested_collector hardcoded counts + lists for citations_curated`.

### §6.2 Pre-push verification

Per the procedure: `python -m pytest tests/test_attested_collector.py -k "discover_descriptors or list_attested_sources" --tb=short`.

Per `feedback_run_wsl_smoke_before_amsc_push.md`: `wsl bash scripts/smoke_local.sh` before push, to catch libm last-bit divergence between Windows-local pytest and Linux glibc.

### §6.3 Srmech-specific deviations

There are NO srmech-side bridge, CLI, or test surfaces today (per §1.1 discovery). The standard 4-commit sequence is sufficient. **No deviations from the ephemerides procedure apply.**

If a future ship creates a srmech-spectral Python package, this catalog can be mirrored into it via the same codegen pattern. The current scope does not require that.

### §6.4 Optional bridge accessor extension

After the standard ship, consider adding a thin bridge wrapper specific to citations_curated to expose convenience accessors:

```python
def get_citation(key: str) -> Dict[str, Any]:
    """Return the citation row for a given key (e.g., 'verlinde2016emergent').
    Follows superseded_by chains to return the latest non-superseded row."""
    ...

def list_citations(
    tier: Optional[str] = None,
    cited_in: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Enumerate citations, optionally filtered by tier or by which spike note
    cites the paper."""
    ...
```

These wrap `get_attested_dataset("citations_curated")` and `get_attested_descriptor("citations_curated")` with the citation-specific filtering. Optional — the ship works without them; the standard AMSC bridge accessors are sufficient for the initial catalog use.

---

## §7. Q7 — Gotchas, recommendations, honest-negative

### §7.1 Gotcha — srmech has no AMSC instance; catalog lands in ephemerides directory

This is the primary architectural compromise (§1.2). The catalog's *content* is srmech-primary (cross-spike citation hygiene); its *location* is ephemerides AMSC. The mitigation is explicit framing in the descriptor's `human_readable_name` and `purpose` fields, plus the top-of-file comment. The compromise is *functional* — building a parallel srmech-spectral AMSC instance to host one catalog is disproportionate, per §1.2 Option B's cost analysis.

If this becomes uncomfortable over time, the right resolution is the future srmech-spectral package ship, which is its own scoping spike, not part of this one.

### §7.2 Cross-reference syntax from spike notes to catalog entries

Proposed syntax: `[[citation:verlinde2016emergent]]` inline in spike notes. The spike author writes `[[citation:verlinde2016emergent]]`; a future tooling pass (markdown preprocessor, or a custom mkdocs plugin) renders it as the full citation string via the cite_as_template.

For the initial ship, the `[[citation:<key>]]` syntax is *documented but not auto-rendered*. Spike authors can write the citation manually + add the catalog reference inline as commentary: `Verlinde 2016 (arXiv:1611.02269; [[citation:verlinde2016emergent]] for catalog entry)`. Auto-rendering is a follow-up tooling ship.

This is intentionally a low-friction first deployment. The catalog is the SSoT; the inline-rendering tooling is the convenience layer that can be added incrementally. Per `feedback_no_mvp_framing`, this is *not* an MVP framing — the catalog ships full-coverage on its primary commitment (record all citations with verification metadata). The inline-rendering is a *separate* full-coverage scope (auto-render every `[[citation:<key>]]` in every spike note), not a partial-coverage shortcut on the catalog itself.

### §7.3 Citation-revision discipline (append-only vs update-in-place)

Established in §3.3 Note 3 and the descriptor preamble: **append-only**. The reasons:

- Forensic traceability — historical state is preserved.
- Audit against silent LLM-training-data overwrites — the catalog's history is a counterweight to the failure mode the user identified.
- AMSC attestation envelope — response_sha256 attests the row's bytes at write time; updating in place would invalidate the attestation chain.

The cost: catalog grows over time even as the same paper is repeatedly re-verified. This is acceptable; the catalog is a metadata record, not a hot path.

The `supersedes` / `superseded_by` fields handle the read-time consumer's need to find the latest authoritative entry for a given paper-of-record. Tooling can chase the chain.

### §7.4 Interaction with brief-writing layer (conductor-brief topic-only-discipline)

The conductor-briefs deliberately omit specific arXiv IDs to prevent training-memory contamination (per the present brief's "Topic-only briefing — I describe topics, you build the citation chain"). The catalog is *downstream* of the spike, not upstream of the brief: when a spike subagent extracts the citation chain from primary sources, the result lands in both the spike note's prose AND a catalog entry.

The catalog therefore complements but does not replace the topic-only briefing discipline. A future brief might say "see [[citation:verlinde2016emergent]] for the prior catalog entry" — this is *user-supplied* context to the subagent, not a brief-level smuggling of details. The subagent still does its own PDF verification and either confirms or supersedes the catalog entry.

This is the right relationship: the catalog records the verification history; the brief delegates the verification work to the subagent in each fresh session.

### §7.5 Honest-negative — the `tier_quarantine_threshold` descriptor field is non-standard

I propose `[gap_targeting] tier_quarantine_threshold = "C"` in §2.2. The existing descriptor-validation code in `attested_collector_catalog._descriptor` may not recognize this field; it expects `regime_labels` and any other `[gap_targeting]` keys may be ignored or may cause validation failures.

Two paths forward:
- **Safer (recommended for initial ship):** drop `tier_quarantine_threshold` from the descriptor and capture the threshold *only* in the descriptor's top-of-file comment block. Downstream tooling (the optional bridge wrapper in §6.4 + any future srmech gap-suggester) reads the catalog rows directly and applies tier-based filtering in code, not in declarative metadata.
- **Cleaner (requires small descriptor-parser extension):** add `tier_quarantine_threshold` as an accepted optional key in the descriptor parser, recognized but unused by ephemerides instrument catalogs and used by citations_curated only. This is a one-line change in the parser but is a real scope expansion of the AMSC framework.

The initial ship should take the safer path: comment-only documentation of the threshold; defer the parser extension to a follow-up ship that adds explicit tooling consuming the field. This keeps the citations_curated ship contained.

### §7.6 Honest-negative — the schema's `verification_method` enum has 15 values; real usage will probably want more

The fifteen enum values cover the May 2026 corpus comfortably. Future cases (e.g., a paper verified via author email correspondence, or verified via a Wikidata cross-reference, or verified by re-reading a verified secondary's reference list with a chain-back-to-primary check) will need new enum values. The schema's `additionalProperties: true` does not extend to enum-controlled fields — adding a new value requires bumping `data_schema_id` from `v1` to `v2`.

This is OK; schema version bumps are a normal AMSC pattern. The May 2026 arc fits cleanly in `v1`; the next version bump is a future ship's concern.

### §7.7 Honest-negative — the catalog does not solve LLM-side training data corruption

The user's stated motivation is "incorrect DOI training data." The catalog mitigates this at the *project* layer — within srmech / ephemerides, the catalog is the SSoT and a wrong DOI cited in some upstream LLM training set does not propagate into the project (because new citations are verified before being added). But the catalog does *not* fix the upstream training data; future LLMs may continue to misattribute. The catalog is a defensive moat around the project's claims, not a corrective signal flowing back to the upstream.

This is the right scope: the project owns its own citation integrity; it does not own upstream LLM training. Anything beyond is out of scope and would be over-claim.

### §7.8 Recommendation

**Ship-now: NO. Scope-only.** The spike establishes the catalog's design as implementation-ready, but does not perform the backfill or commit the SSoT files. The reasons to defer to a follow-up ship:

1. The backfill itself is 4-6 hours of focused work + manual review (§4.4), which is its own dedicated ship.
2. The four-commit AMSC ship procedure (§6.1) has known non-obvious gotchas (manifest + initial_phases.json sync) that benefit from focused attention.
3. The two honest-negatives in §7.5 (descriptor field) and §7.6 (enum coverage) should be re-confirmed against the descriptor parser before the ship.
4. The user's review of this scoping spike provides a natural decision-point for committing to the full ship vs. iterating on the descriptor / schema first.

**Follow-up ship candidates:**

- **Spike #23 (proposed):** Run the §4.2 walk algorithm on the corpus; produce the initial row.ndjson; commit the 4-commit ship sequence; verify CI passes.
- **Spike #24 (proposed, optional):** Add the bridge accessors in §6.4 (`get_citation`, `list_citations`); add tests; commit.
- **Spike #25 (proposed, far-future):** Add the `[[citation:<key>]]` inline-rendering tooling.

### §7.9 Disability-accommodation dimension

Per `feedback_disability_accommodation_dimension`: the catalog is text-based metadata, screen-reader-friendly, no visual / spatial encoding. No specific accommodation dimension is load-bearing here. The append-only revision discipline (§7.3) is incidentally helpful for executive-function differences (no silent rewrites = no surprises when re-reading), but that is not the primary motivation.

### §7.10 No security-adjacent dimension

Per `feedback_trauma_informed_defensive_scope`: this is a documentation-hygiene scope; no defensive-preparedness dimension applies.

### §7.11 No lineage claims

Per `feedback_no_lineage_claims_in_notebook`: the catalog does not claim that any cited paper is "a natural extension of" or "the predecessor of" any project framework. Each citation is grounded technical reference: this paper's framing_note (project-side) might say "predicts X mechanism" or "introduced Y bound"; that is technical citation, not lineage-claiming.

---

## §8. Summary

Spike #22 scopes the architectural design of `citations_curated`, an AMSC `literature_curated` catalog that serves as the cross-project citation SSoT operationalizing the Tier A/B/C/D policy from PR #366.

The catalog lives at `docs/antikythera-maths/research/attested/citations_curated/` because srmech has no AMSC instance and creating one is disproportionate. The descriptor uses the standard literature_curated adapter; the schema (`citations_curated.row.v1`, draft 2020-12) records bibliographic identity (title, authors, year, DOI, arXiv ID), verification provenance (tier, method, date, evidence), project context (first_cited_in, also_cited_in, framing_note), the load-bearing user_fetch_link for paywalled-to-AI-agent papers, and append-only revision metadata (supersedes / superseded_by) for forensic auditability against LLM training-data corruption.

The backfill corpus is the May 2026 spike series #11–#21C + consolidation note + comparative-ethology scopes, estimated at 60-80 unique citations. The backfill protocol uses an out-of-repo script (per `reference_autonomous_validation_tos_landscape.md`) that walks the markdown, deduplicates by (DOI, arXiv ID), and verifies via the multi-source path (arXiv → Crossref → OpenAlex → Semantic Scholar → publisher landing → ResearchGate fallback flagged).

The ship sequence follows the standard AMSC 4-commit procedure (SSOT files + codegen mirror + initial_phases.json sync + test ratchet from 19 → 20 sources). No srmech-specific deviations apply.

The primary gotchas: (i) the cosmetic ownership mismatch (srmech-content in ephemerides directory); (ii) the non-standard `tier_quarantine_threshold` descriptor field (recommended to defer to a comment-only treatment initially); (iii) the schema's enum coverage may grow in future versions (acceptable; bump `data_schema_id` to `v2` when needed).

Recommendation: **scope-only**. The backfill + ship is a separate follow-up (Spike #23). The design above is implementation-ready for that follow-up.
