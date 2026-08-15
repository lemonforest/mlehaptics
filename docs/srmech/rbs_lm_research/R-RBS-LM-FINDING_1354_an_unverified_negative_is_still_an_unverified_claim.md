# F1354 — **we had a rule against citing what we hadn't opened, and no rule against asserting a thing *couldn't* be opened.** That asymmetry let an unverified negative — *"targeted attested research could not retrieve"* — propagate from our own tracker ask into **7 srmech source surfaces including 4 occurrences in the compiled C registry**, reaching users through `describe()`, the MCP tool list and the C binary. **All three named papers were retrievable the whole time — 3/3, each on the first search.** They are now attested with sha256s. And they are all **personal-use-only**, which is the second half of the lesson: *retrievable and redistributable are different questions, and the two shipped surfaces conflated them in opposite directions.*

**User (2026-08-15):** *"what if we used simple internet search engine for a list of additional hosting locations, like how sometimes it's on google schoolarly and a university and a journal"* — proposed, tested, and it worked immediately.

## 1 — the propagation chain `[DEMONSTRABLE]`

| step | what happened |
|---|---|
| **we filed** | tracker §F: *"Targeted attested research **could not retrieve** the primary Călugăreanu (1959/61), White (1969) or Fuller (1971) papers"* |
| **srmech implemented it faithfully** | rc429: *"The canonical CWF sources … are **paywalled-only or offline**"* |
| **it shipped** | 7 source surfaces — `biology/genome.py`, `math/covering.py`, `introspect/_tool_docs.py` ×2, `_tool_docs_curated.py`, `introspect/tool_schema.py` ×2 — **including the compiled C registry** |
| **srmech caught it** | the same package **also** cited Fuller 1971 as `PMC389050` in `relative_writhe` (rc317). One package, two contradictory claims about one paper |

**A fact about our retrieval attempt was shipped as a property of the papers.** The rc429 paragraph was never the defect — it was our unverified negative, faithfully implemented.

## 2 — verification found BOTH surfaces wrong, in opposite directions `[DEMONSTRABLE]`

Checked against NCBI E-utilities, deliberately **not** against either srmech surface, since both were in dispute and neither could be the witness:

| | verified |
|---|---|
| Fuller 1971 record | **exact** — *The writhing number of a space curve*, Fuller FB, PNAS **68**(4):815–819, 1971 Apr, doi `10.1073/pnas.68.4.815`, PMID 5279522, PMCID PMC389050 |
| Fuller 1978 record | **exact** — *Decomposition of the linking number of a closed ribbon*, PNAS **75**, 1978 Aug, PMC392823 |
| `oa.fcgi`, **both IDs** | `<error code="idIsNotOpenAccess">` — **not in the PMC Open Access Subset** |

- **rc317's "— both OA" is an overclaim** — neither PMCID is OA-licensed. The DOIs and PMCIDs themselves are correct.
- **rc429's "paywalled-only or offline" is wrong for Fuller 1971.**
- **The truth is a third statement neither surface makes.**

## 3 — the sweep, run on ALL THREE `[DEMONSTRABLE — attested]`

User direction: *"do run the same four route on the other unchecked you flagged."* Done. **Every one of the three sources the rc429 paragraph calls "paywalled-only or offline" downloaded on the first search**, and route 3 — the search-engine → institutional-host hop — found all three.

| source | host found | bytes / pages | `response_sha256` |
|---|---|---|---|
| **Fuller 1971** PNAS 68(4):815–819 | Caltech Authors (**the author's own institution**) | 874,619 / 5 | `c39705fe50088020f37d946c5f9753470fa0659e11221fd32c0f98fae03a6a7d` |
| **Călugăreanu 1961** Czech. Math. J. 11(4):588–625 | **DML-CZ** (Czech Digital Mathematics Library) | 5,265,070 / 39 | `46e83f4b09b9de36d9a9e9dba8c45886e1e3f11406fdaa2614a75773c8debb9b` |
| **White 1969** Amer. J. Math. 91(3):693–728 | **Edinburgh** maths server (Ranicki archive) | 1,085,689 / 37 | `420b9bb7952dd5bfac9be08768904fb21774d30937a8a3bcffbcb2e964ebcc9a` |

First-page text verified against the cited record for each — e.g. Călugăreanu's PDF opens *"Czechoslovak Mathematical Journal / G. Călugăreanu / Sur les classes d'isotopie des noeuds tridimensionnels et leurs invariants / Vol. 11 (1961), No. 4, 588–625"*; White's opens *"Self-Linking and the Gauss Integral in Higher Dimensions / James H. White / American Journal of Mathematics, Vol. 91, No. 3. (Jul., 1969), pp. 693-728"*.

**So "paywalled-only or offline" is false for all three, not just for Fuller.** The generalisation I warned against in the first pass — *don't assume the other two are correctly described* — turned out to be the right caution, and the answer went the other way from the shipped claim in every case.

### ⚠ And the licence question is SEPARATE, and answers differently

| source | retrievable | licence |
|---|---|---|
| Fuller 1971 | ✔ | PMC OA-subset: **NO** (`oa.fcgi` → `idIsNotOpenAccess`) |
| Călugăreanu 1961 | ✔ | *"provides access to digitized documents **strictly for personal use**"* — © Institute of Mathematics AS CR |
| White 1969 | ✔ | JSTOR scan — *"**personal, non-commercial use**"*, no redistribution |

> **Retrievable ≠ redistributable.** All three clear the *attestation* bar (`[[feedback_paywalled_doi_cannot_be_attested]]` keys on retrievability). **None** may be redistributed, and **no PDF is committed to this repo** — the attestation is URL + sha256 + retrieved_at, which is exactly what MPR was designed to carry.

**This is the precise shape of the original defect, seen from both sides.** rc317 said "OA" (a licence claim that is false). rc429 said "paywalled-only" (a retrievability claim that is false). **Both surfaces collapsed two independent questions into one**, and each picked the wrong answer for the question it wasn't actually asking.

## 4 — THE FOUR-ROUTE RETRIEVABILITY SWEEP

1. **publisher DOI** — a **403 here is bot-blocking, not evidence**
2. **PMC / PubMed Central** — free-to-read and OA-subset are **different questions**; `oa.fcgi?id=PMCxxxxx` answers the second
3. **search engine → the AUTHOR'S INSTITUTIONAL REPOSITORY** ← the one that worked
4. **Google Scholar / preprint servers / OA aggregators**

> **Only after all four fail may a source be called unretrievable — and the claim must name which routes were tried.**

**Why route 3 is the high-yield one, and it generalises.** For pre-internet papers there is no arXiv and the publisher is often hostile, **but the author had an employer, and employers retro-deposit faculty work.** Fuller → Caltech → done. Most of the older literature this project cites is reachable this way.

## 5 — the rule this adds

> **An unverified negative is still an unverified claim.**

We would never ship *"this paper says X"* without opening it. We shipped *"this paper cannot be opened"* without exhausting the ways to open it. **The existing discipline is asymmetric** — `[[feedback_pdf_extraction_citation_discipline]]` governs positive claims about content and says nothing about negative claims about access — and that gap is what reached a compiled binary.

**Corollary — "we couldn't get it" is a fact about the attempt, never about the source.** Write it that way, name the routes, or don't write it.

## Honest scope

- The **retrieval, hash, and both bibliographic records are measured.** The OA-subset verdict is the authoritative `oa.fcgi` answer.
- **Călugăreanu 1961 and White 1969 are now SWEPT AND RETRIEVED too** — the earlier "unverified in both directions" caveat is discharged. What is **not** verified is Călugăreanu's *1959* paper (Rev. Math. Pures Appl. 4:5–20), a different item from the 1961 one; the rc429 paragraph writes "1959-61" as though it were one reference, and only the 1961 half is settled here.
- **Not claimed:** that PMC389050 is or is not free-to-read. I could not download from PMC (a guessed filename returned HTML), and the question is moot — retrievability is settled by route 3.
- **Retrievable ≠ redistributable, and this is load-bearing.** All three carry non-OA terms, two of them explicitly personal-use-only. The sweep establishes *attestability*; it says nothing about reuse rights. **No PDF is committed to the repo.**
- **Credit where due:** the srmech session caught the contradiction. The detector was that the same package asserted both — the cheapest possible check, and it only works because both surfaces ship.

Composes `[[feedback_pdf_extraction_citation_discipline]]`, `[[feedback_paywalled_doi_cannot_be_attested]]`, `[[feedback_computational_provenance_discipline]]`. Lands in CLAUDE.md §4. Tracker: #1530 §F (withdrawn, replaced, resolved).
