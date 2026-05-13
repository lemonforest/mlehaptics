# Citation-Hygiene-When-Paywalled — Tiered Verification Policy

**Date:** 2026-05-13
**Branch:** `research/comparative-ethology-age-sociality`
**Status:** Policy proposal — apply to srmech / spectral-collection notebooks going forward
**Cross-reference:** [`memory/feedback_pdf_extraction_citation_discipline.md`](../../../memory/feedback_pdf_extraction_citation_discipline.md) (canonical PDF-extract-and-verify discipline; three catches in the May 2026 spike series; this note adds a fourth, see §3).

---

## 1. The problem this policy addresses

The standing discipline is "extract the actual PDF, verify authors + title + arXiv ID before citing." That works when a PDF is reachable. It is silent on the *much more common case* where the PDF is paywalled and the only available verification surfaces are:

- A publisher landing page that shows abstract + metadata behind a paywall.
- A ResearchGate or institutional-repository page (which may or may not show the PDF).
- A Google Scholar snippet, an OpenAlex / Semantic Scholar metadata record, a Wikidata citation, or a PubMed listing.
- A second-hand citation from a verified paper that uses the work as a reference.

Without an explicit policy, two failure modes happen:

1. **Citation gets accepted as "verified" on weak evidence** — the title is what someone *says* the title is, and a later check finds the title is wrong or the author list is incomplete (see §3 worked example).
2. **Citation gets rejected entirely as "unverifiable"** when in fact a strong-but-imperfect verification path exists — the publisher landing page consistently confirms the same authors+title that two independent indexes also confirm. Rejecting these makes the literature pipeline brittle.

A tiered policy splits the difference: declare exactly what *kind* of verification each citation has, and flag the weak tiers honestly in the prose.

---

## 2. The four tiers

### Tier A — PDF-extracted-verified  (current discipline, gold standard)

**Method:** The actual paper PDF was retrieved (via arXiv, preprint server, open-access journal, author repository, or an institution the user has rightful access to). The bibliographic fields cited (authors, title, year, journal, volume, issue, pages, DOI) were read directly from the PDF or its first-page metadata. Where present, the arXiv ID was confirmed in the arXiv metadata page.

**When to use:** Always preferred. If achievable, use this tier.

**Notation in citation:** No flag needed; this is the assumed default.

**Failure-mode protection:** PDF text-extraction can mangle Unicode (diacritics in author names) or split DOIs across lines. After extraction, the human (or the reviewing agent) must visually confirm the bibliographic record matches the rendered PDF.

### Tier B — Publisher-DOI-abstract-verified

**Method:** The publisher's official article landing page (resolved via DOI) is loadable and shows:
- The full title (not a clipped or auto-generated snippet),
- The complete author list (in publication order, including all coauthors),
- The journal, volume/issue, pages, and year.

The abstract is visible (or the paywalled page reveals the abstract via the journal's standard preview). The *body* of the paper is paywalled.

**When to use:** When Tier A is unreachable. Always check at least one secondary index (PubMed, OpenAlex, the journal's PMC entry, or an institutional repository) and confirm that index agrees on the title and author list. If the secondary index disagrees on author list, this is NOT a Tier B verification — see §3 worked example for what goes wrong otherwise.

**Notation in citation:** "[abstract-verified; body paywalled]" — appended in the source-list, not the inline cite. The prose using the citation should not lean on body-claims; it should lean only on claims confirmable from the abstract or from a separate Tier A source.

**Failure-mode protection:**
- Cross-check the author list at TWO independent indexes (e.g., publisher landing + institutional repository + PubMed). Single-source author-list confirmation is not enough; ResearchGate filenames have been wrong (§3).
- The DOI must resolve to the *same paper*. (Earlier in this series we caught a DOI that resolved to a different paper than the one the prior reviewer thought.)

### Tier C — ResearchGate / preprint-server-verified  (FLAGGED IN PROSE)

**Method:** The PDF or abstract is reachable on a non-publisher platform (ResearchGate, Academia.edu, institutional preprint, OSF, bioRxiv post-publication mirror, etc.). The metadata available there is read and used.

**When to use:** Only when Tiers A and B are unavailable AND the citation is load-bearing. Hostile blockers (HTTP 403 to programmatic clients, anti-AI-scraper proof-of-work systems, login walls) often gate these — see §4 for the Dunbar & Shultz 2021 case.

**Notation in citation:** "[ResearchGate-verified — filename-derived title; not cross-checked against publisher]" — explicit flag, inline visible to readers. The prose must not present this citation as Tier-B confidence.

**Failure-mode protection:** ResearchGate filenames are user-uploaded and can be arbitrary; the displayed title can be *wrong* or contain extra editorial words ("BiolRevs 2021"). When using Tier C, treat the filename and the publisher-DOI metadata as TWO separate facts; if they disagree, prefer the publisher metadata. **A Tier C verification is never a substitute for a Tier B verification of the same paper if Tier B is achievable.**

### Tier D — Search-snippet-only  (REJECT for primary citations; flag if used at all)

**Method:** Only a Google search snippet, a Wikipedia citation, or a citation-graph mention (Semantic Scholar / OpenAlex with no abstract) is available. No publisher page loadable. No PDF reachable.

**When to use:** Almost never for primary citations. Acceptable only for:
- *Tangential* citations that establish context but whose specific content is not relied on (e.g., "the field has discussed this since the 1980s, see e.g. Tier D ref").
- Backfilling a bibliography from a verified secondary source's reference list, where the secondary source is Tier A or B verified AND the prose only relies on the secondary source's framing of the Tier D ref.

**Notation in citation:** "[snippet-only — UNVERIFIED — flagged for later re-check]" in the source list. **Never present as authoritative.** If the citation is load-bearing, prefer to:
- Drop the citation (cite the verified secondary that mentions it instead), or
- Block on retrieving Tier B or higher.

**Failure-mode protection:** Tier D citations should be treated as research debt. A reasonable practice is to keep a running `unverified.ndjson` file listing all Tier D citations with the prose passages that depend on them, so they can be re-verified or dropped before any external publication.

---

## 3. Worked example — Dunbar & Shultz 2021, Biological Reviews (DOI 10.1111/brv.12730)

This is the fourth catch in the May 2026 citation-hygiene spike series. The prior gap-closure scoping note ([`comparative_ethology_gap_closure_scope_2026-05-13.md`](./comparative_ethology_gap_closure_scope_2026-05-13.md), Gap #3 §A.i and §D, citation 3) listed:

> **Dunbar (2021).** "Social complexity and the fractal structure of group size in primate social evolution." *Biol Reviews* 96(5):1889, DOI `10.1111/brv.12730`. **VERIFIED title via Wiley listing; abstract paywalled, citation unverified at full-content level — paywalled.**

The user then pointed at the ResearchGate URL:
`https://www.researchgate.net/publication/371499758_BiolRevs_2021_DunbarShultz_Socio-cognitive_grades_in_primates`

— noting it was the #1 Google hit and asking whether ResearchGate could be the citation-hygiene fallback.

### What the verification attempts revealed

1. **ResearchGate URL (Tier C attempt) — BLOCKED.** WebFetch returns HTTP 403 Forbidden. ResearchGate denies non-logged-in programmatic access entirely. The URL is unreachable without an account; no PDF, no abstract, no metadata via this route. *Verdict: This URL is NOT a usable Tier C path for AI-agent verification.*
2. **The ResearchGate filename is wrong about the title.** "BiolRevs_2021_DunbarShultz_Socio-cognitive_grades_in_primates" implies the article is titled "Socio-cognitive grades in primates." PubMed search for this title yields **zero results.** No paper of that title by these authors exists in PubMed.
3. **The Wiley DOI landing page (Tier B attempt) — paywalled.** WebFetch returns HTTP 402 Payment Required. Direct verification of authors+title from the publisher is not achievable for an AI agent.
4. **Two independent indexes converge on a different title.**
   - Manchester University institutional repository (research.manchester.ac.uk) confirms:
     - Title: **"Social complexity and the fractal structure of group size in primate social evolution"**
     - Authors: **RIM Dunbar AND S Shultz** (two-author, NOT solo Dunbar)
     - Year: 2021, DOI: 10.1111/brv.12730
   - Web search across multiple sources (Wiley journal listing snippet, Researchgate cataloguing, Manchester repo) consistently report this same title.

### Two errors in the prior citation

- **Author list was incomplete.** Prior scope listed "Dunbar (2021)" — but the paper is **Dunbar & Shultz (2021)**, two authors. The Manchester institutional repository (an authoritative-author-affiliated source) confirms Shultz is a coauthor.
- **The ResearchGate filename misled.** If the prior reviewer had taken the ResearchGate filename at face value, they would have cited a paper titled "Socio-cognitive grades in primates" — which is not the real title.

### What Tier B verification produces

After cross-checking Manchester repo + Semantic Scholar Graph API (DOI lookup) + multiple web-search confirmations, the correct citation is:

> **Dunbar & Shultz (2021).** "Social complexity and the fractal structure of group size in primate social evolution." *Biological Reviews* 96(5):1889–1906, DOI `10.1111/brv.12730`. **Open access (CC BY).** [Tier B — abstract-verified via Manchester repository + Semantic Scholar Graph API metadata; PDF retrievable from open-access mirrors.]

This is **Tier B**, with a path to Tier A worth noting. The Semantic Scholar Graph API endpoint
`https://api.semanticscholar.org/graph/v1/paper/DOI:<doi>?fields=title,authors,year,journal,abstract` is reachable to AI agents (returns clean JSON, no anti-scraper challenge) and corroborates the title and author list. It additionally reports the license — in this case **GREEN open access, CC BY** — which means the AI agent's failure to reach the Wiley publisher page is a *publisher-infrastructure* limitation, not a *licensing* one. Any user-mirrored PDF of this paper is legitimately reachable; the corresponding Tier A verification would succeed if a direct CC-BY mirror URL is found.

**Tier-elevation tactic:** When Semantic Scholar reports `open_access.status: "GREEN"`, search for a non-publisher PDF mirror (institutional repo, OSF, etc.) before settling for Tier B. Tier A is achievable here in principle.

### Why ResearchGate is Tier C *at best*

Even when ResearchGate IS reachable (i.e., the user clicks through manually after logging in), the verification gained is at most Tier C. The displayed title on RG can disagree with the publisher metadata, and the only way to resolve that disagreement is to do a Tier B cross-index check anyway. **ResearchGate's value is as a PDF source for human readers, not as a metadata authority for AI-agent verification.**

---

## 4. The "AI agents can't reach the source" subproblem

Both blocking patterns hit this case:

- **Wiley / Elsevier / Springer publisher pages:** Return HTTP 402 / 403 to AI tools (WebFetch and similar). Real human browsers can usually read at least the abstract.
- **ResearchGate, Academia.edu:** Return HTTP 403 to anything that doesn't look like an authenticated session.
- **Anti-AI-scraper proof-of-work (Anubis / Cloudflare):** Increasingly deployed by data repositories (Dryad uses Anubis as of 2026). Legitimate human-browser traffic passes the JS challenge; pure-HTTP clients are blocked. *This is explicitly designed to refuse AI scrapers and is being respected as a policy signal — not a technical inconvenience to route around.*

**Implication for AI-agent citation discipline:**

- An AI agent performing citation verification operates under a *bounded* set of accessible sources. The tier downgrade is real: a paper that a human reader could verify at Tier A or B may only reach Tier C or D for the AI agent.
- This is NOT a license to fabricate or weaken claims. It IS a license to flag honestly: "the highest tier the AI agent reached for this citation is Tier C; user-side Tier A or B verification is recommended before external publication."
- The list `[memory/feedback_pdf_extraction_citation_discipline.md]` captures the gold standard. The present tiered policy captures the realistic fallback structure.

---

## 5. Operational checklist

When citing a 2020+ paper in a srmech / spectral notebook:

1. **Try Tier A.** Look for arXiv ID, bioRxiv DOI, author institutional PDF, PMC full text. If reachable, verify authors + title + DOI from the PDF metadata. **Stop here. Cite normally.**
2. **If Tier A unreachable, try Tier B.** Resolve the DOI to the publisher landing page. If the page returns 402/403 to the AI agent, try at least TWO of: PubMed, **Semantic Scholar Graph API** (the endpoint `api.semanticscholar.org/graph/v1/paper/DOI:<doi>?fields=title,authors,year,journal,abstract` returns clean JSON without anti-scraper gating; also reports `open_access.status` and license, which is load-bearing for elevation to Tier A), OpenAlex, the institutional repository (search "[author lastname] [first significant title word] site:[affiliated university]"), or the journal's editorial listing. Confirm authors + title agree across both indexes. If Semantic Scholar reports `open_access: GREEN`, do one more pass to find a CC-licensed mirror PDF (lift to Tier A).
3. **If Tier B succeeds (two independent indexes agree),** cite with the "[abstract-verified; body paywalled]" flag in the source-list line and proceed.
4. **If Tier B fails because indexes disagree,** STOP and report the disagreement. Do not pick one. Surface the conflict to the user.
5. **If only Tier C reachable (e.g., a non-publisher PDF mirror that the AI agent can read),** cite with the "[ResearchGate-verified — filename may be misleading]" flag. Do not rely on the source's metadata for claims beyond what the abstract or DOI cross-check supports.
6. **If only Tier D reachable,** consider dropping the citation, or write it with the "[snippet-only — UNVERIFIED]" flag and log it in `unverified.ndjson` for later re-check.

---

## 6. Concrete updates to the prior gap-closure scope file

The prior scope file ([`comparative_ethology_gap_closure_scope_2026-05-13.md`](./comparative_ethology_gap_closure_scope_2026-05-13.md)) has:

- Gap #3 §A.i (paragraph 2): mentions "Dunbar (2021)" — should be **Dunbar & Shultz (2021)**.
- Gap #3 §D citation 3: same fix — add Shultz as coauthor.

These are not corrected in this session because the scope file is part of the prior subagent's frozen output, and the user's two tasks (run the spike + write the policy) did not include rewriting earlier scopings. The corrections are recorded HERE for cross-reference and should be applied when the scope file is next revisited (or simply integrated into any external publication that draws from it).

---

## 7. Discipline notes for this policy file

- No emoji.
- No MVP framing.
- Cross-link to memory file is a soft reference; the memory file is NOT edited from this session (per memory hygiene — only the user edits the memory store).
- The Dunbar & Shultz 2021 case is worked through honestly, including the AI-agent's failure to reach the source via either Tier A, B, or C and the resulting Tier-B-by-cross-index-only verification.
- No security-adjacent dimension; this is a documentation-hygiene policy.
- Disability-accommodation dimension is not load-bearing here (the policy is text-based and screen-reader-friendly).
