# #846 + #847 — Antiquity render-set acquisition + native-language peer-review widening: PROTOCOL, source landscape, first candidates (begun 2026-06-03)

Working note (not a finding) — the careful scaffold for GH **#846** (acquire MPM-attested antiquity texts, native + translated, multi-language) and **#847** (widen peer-review to native-language scholarship). Both are **render-independence widening for the many-to-many truth-filter** (F334/F335/F337): more *independent* renders of one source → the cross-render majority resolves the truth-invariant and rejects correlated (English-only) false shapes.

## The multilingual-verification discipline (LOAD-BEARING — the user is not multilingual)
The user cannot independently verify non-English / native-script content → **I am the only frame on it → that is the F335 self-correlation ceiling**, live. My errors there would be invariant to the user. So, baked in from the first text:
1. **Primary-source only.** Fetch the actual attestable edition (the archive / critical edition / digital corpus), never a training-data memory of a text. The attestation block points at the fetched source.
2. **Independent cross-check (the substitute verifier).** Native-script content is verified through a **triality** (independent models cross-reading the *same fetched source*) — because when the user can't be the second frame, the independent-model majority is. This is the truth-filter applied to our own acquisition.
3. **Flag-what-I-can't-verify.** Every render carries a **verification_level**: `primary-verified` (grounded + cross-checked) / `cross-checked` (triality-agreed) / `flagged-residue` (I cannot ground it → handed to a domain expert, never asserted). The philologist owns the decipherment (`framework_hands_the_next_question_to_the_expert`).

## Attestation schema (per render — MPR-style, MPM discipline)
`{ source_url, edition_or_editor, translator (if translation), script, language, render_role (native | translation:<lang>), license, retrieved_at, response_sha256, verification_level }`. Paywalled-only DOI REJECTED → OA / archive / canonical-edition chain (`feedback_paywalled_doi_cannot_be_attested`).

## Attestable-OA source landscape (grounded survey, 2026-06-03)
| corpus | source | native | translations | license | note |
|---|---|---|---|---|---|
| **Greek / Latin** | Perseus / Open Greek & Latin / Scaife Viewer | TEI-XML, public-domain primary | yes | primary PD + CC BY-NC-SA 3.0 US; modern CC BY-SA 4.0 | 2,699 works / 3,860 editions+translations |
| **Cuneiform (Sumerian / Akkadian)** | CDLI + ORACC (SumTablets = CC BY 4.0) | transliteration (ATF) | English | CDLI license **to verify**; SumTablets CC BY 4.0 clean | 320k+ artifacts |
| **Egyptian trilingual** | Rosetta Stone Online (Topoi / Humboldt-Univ. Berlin) + attalus.org | hieroglyphic + Demotic + Greek | translations | **per-source, to verify** | the 3-script anchor |
| *(future)* Hebrew | Sefaria | yes | yes | CC (verify) | — |
| *(future)* Sanskrit | GRETIL | yes | partial | verify | — |
| *(future)* Classical Chinese | ctext.org | yes | some | verify | — |

Sources surveyed: Perseus/OGL (<https://www.perseus.tufts.edu/hopper/>, <https://www.opengreekandlatin.org/>, <https://scaife.perseus.org/>); CDLI (<https://cdli.mpiwg-berlin.mpg.de/> via MPIWG) + ORACC/SumTablets (arXiv 2602.22200, CC BY 4.0); Rosetta Stone Online (<http://rosettastone.hieroglyphic-texts.net/>) + attalus.org (<https://www.attalus.org/egypt/rosettastone.html>).

## FIRST candidate (#846) — the Rosetta Stone (the k=3 anchor incarnate)
**Why first:** 3 co-equal scripts of one decree (Ptolemy V, 196 BC) = a real-world **≥3-independent-render truth-filter** on a single source content — *and* the namesake of the whole `rosetta_table_of_truth` stance. It is the cleanest possible first many-to-many anchor.
**Render-set (target):** ① hieroglyphic ② Demotic ③ Greek (the three native scripts) + ④ modern translations (≥2 independent, ideally different languages, per the F49 "English-only collapses independence" lesson).
**Verification plan (honest):** the **Greek** I can ground + cross-check well; the **hieroglyphic + Demotic** are `flagged-residue` pending the triality cross-check + a domain-expert pass — I will NOT assert their content as verified. The decree's *near-identical-across-scripts* property (well-attested) is itself the k=3 demonstration: agreement across the 3 = the invariant; the minor per-script differences = the render-fiber.

## #847 — native-language peer-review widening: protocol
- **Where it lives:** non-English journals + original-language editions of foundational works (de Gruyter/German, Persée/French, J-STAGE/Japanese, CNKI/Chinese, eLIBRARY/Russian, etc.). Many results were published natively before/without English translation.
- **How to verify (the hard part, given the user can't):** primary-source fetch of the native-language record; verify authors + title + ID **in the native language**; OA where possible; **triality cross-check** of the native-language attribution (the substitute verifier); `flagged-residue` for anything ungroundable.
- **Pairs with #846:** both widen render-independence; together they push the truth-filter past the English-correlated ceiling (F335/F337).

## Scope / discipline
Defensive / no-lineage / structure-reading only; MPM attestation on every render; expert-owns-the-decipherment; **the triality cross-check is the standing substitute for the user's non-multilingual verification.** Not srmech-op-gated — can proceed now while srmech bug-fixes land. The first acquired render-set (Rosetta Stone) doubles as the **first ingest-gate / many-to-many test** for the F336/F337 honesty-store.

### Next concrete step
Fetch + attest the Rosetta Stone render-set (Greek `primary-verified`; hieroglyphic/Demotic `flagged-residue` → triality cross-check), build the MPR blocks, and run it as the first ≥3-render anchor. Then extend to a Greek/Latin pair (Perseus) and a cuneiform pair (CDLI/ORACC) to get cross-*corpus* independence, not just cross-script-within-one-artifact.

---

## RENDER-SET #1 ACQUIRED + triality-cross-checked (2026-06-03) — the Rosetta Stone
**Method:** my primary fetch (attalus Greek) + a **k=3 substitute-verifier triality** (haiku∥sonnet∥opus each independently fetched the primary sources, quote-or-flag).

**The triality earned its keep (the substitute verifier worked):** haiku + sonnet hit `ECONNREFUSED` on the *best* source — **Rosetta Stone Online (Topoi / Humboldt-Univ. Berlin)** — because WebFetch force-upgrades to HTTPS and that site is **HTTP-only**. **Opus diagnosed it** (`curl http://… → 200 OK`, Apache/WordPress) and recovered the source. 2-of-3 would have wrongly reported "Topoi unreachable"; **k=3 corrected the false-negative.** *Protocol note added: the antiquity-fetch path must allow plain-HTTP — many scholarly sites are HTTP-only.*

**Cross-checked (k=3 + my fetch agree):**
- **k=3 anchor CONFIRMED** — one decree (Ptolemy V, 27 March 196 BC) in three scripts (hieroglyphic / Demotic / Greek), **"only minor differences across the three versions"** (the redundant ≥3-render property); the decree *self-mandates* its trilingual inscription. `primary-verified` across all tiers + Wikipedia.
- **Cleanest open-licensed render-set → Rosetta Stone Online (Topoi/Humboldt):** TEI/EpiDoc XML `Rosetta_Stone-v1.1-04012019.epidoc.tei.xml`, **CC BY-SA**, per-script layers (traditional + modern transliteration, interlinear morphemic glossing, EN+DE word-by-word + sentence translations). Coordinators: Lincke / Werning / Georgakopoulos. Stone photo © British Museum CC-BY-NC-SA. **← the render-set to ingest.**
- **attalus.org** — English **translations only**, **no license stated** → scholarly provenance, NOT redistributable (Greek = Carol Andrews, BM 1985, citing **OGIS 90 / PackHum 219002**; Demotic = Quirke & Andrews, BM 1988 + Simpson, Griffith 1996).
- **Greek original** via **OGIS 90 / PackHum** (`epigraphy.packhum.org/text/219002`).

**FLAGGED RESIDUE (honest non-multilingual limits — the substitute-verifier cannot close these; → domain expert):**
- the **ancient-script → transliteration/translation fidelity** is unverified-by-us (rests on the BM / Griffith / Topoi scholarship);
- the **hieroglyphic first half is physically lost** (stone damage; attalus: *"almost all of the first half of the hieroglyphic version has been lost"*);
- the **"minor differences"** across renders are asserted but **not enumerated** → the *degree* of render-independence-vs-redundancy is uncollated;
- the **exact scope of the Topoi CC BY-SA** (XML file vs whole annotation layer) — confirm on the OSF landing page before redistribution.

**Status:** render-set #1 attested at the **metadata/provenance + k=3-property** level (cross-checked); ancient-script *content* is `flagged-residue`. **Ingest target = the Topoi CC-BY-SA TEI/EpiDoc XML.** Doubles as the first ingest-gate / many-to-many test (#849) once the build lands. **Next:** cross-*corpus* independence — a Perseus Greek↔Latin↔English set + a CDLI/ORACC cuneiform set — so independence is cross-corpus, not just cross-script-within-one-artifact.
