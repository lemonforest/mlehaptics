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

---

## RENDER-SETS #2 + #3 — cross-corpus ACQUIRED + triality-cross-checked (2026-06-03)
Substitute-verifier triality (haiku∥sonnet∥opus). **It earned its keep again:** opus caught a **P-number error** (the search-suggested CDLI `P461271` is NOT the Hammurabi stele — it is a 1st-millennium commentary "Fs Finet I 098"; the stele composite is likely `Q007317`, unfetchable this pass) and surfaced a **CDLI/ORACC reachability disagreement** (sonnet quoted ATF from `P464358`; opus found `cdli.earth` composite routes 500/404 + ORACC HTTPS unresolved) → **CDLI/ORACC native-ATF = flagged-residue** (disputed reachability + unresolved P-number → Assyriologist + working CDLI). opus also secured a **German render** — independence *beyond English* (honors the F49 "English-only collapses independence" lesson).

### Render-set #2 — Thucydides, *History of the Peloponnesian War* (Greek ↔ Latin ↔ English TRIPLE)
A genuine **3-render cross-language triple**, all **CC-BY-SA 4.0**, same CTS work `tlg0003.tlg001`, opening sentences quoted verbatim (content-identity confirmed). Primary-verified from the canonical-greekLit XML `<teiHeader>`:
- **Greek** `tlg0003.tlg001.perseus-grc2` — Henry Stuart Jones, OUP 1910/1942 — `Θουκυδίδης Ἀθηναῖος ξυνέγραψε…`
- **Latin** `tlg0003.tlg001.1st1K-lat2` — Friedrich Haase, Didot 1869 (First1KGreek) — `Thucydides Atheniensis conscripsit…`
- **English** `tlg0003.tlg001.perseus-eng6` — Richard Crawley 1914 — `Thucydides, an Athenian, wrote…`
Hosted: `github.com/PerseusDL/canonical-greekLit`; Scaife Viewer (`scaife.perseus.org`). Independence: 3 translators / 3 eras (1869 / 1914 / 1942). **Flagged residue:** OCR fidelity (Latin Haase = "quickly corrected OCR output"; Greek Kurzweil-scanned) → classicist; ancient-script content fidelity unverified-by-us. (Corroboration: opus confirmed the NT/Perseus has Greek+English but **no co-hosted Latin** — most Perseus texts lack a Latin render, so Thucydides is a deliberately-good pick.)

### Render-set #3 — Code of Hammurabi (Akkadian transliteration + English ×2 + German)
Clean PD set with a **non-English** render (the independence we wanted):
- **Akkadian transliteration + German** — Hugo Winckler, *Die Gesetze Hammurabis in Umschrift und Übersetzung* (Leipzig: Hinrichs, 1904), archive.org `diegesetzehamm1904hamm` — **PD**; Umschrift (transliteration) + German in one volume. (opus-grounded)
- **English (King 1910)** — Avalon Project (Yale) / Wikisource `Codex_Hammurabi_(King_translation)` — **PD** (King d. 1919).
- **English (Harper 1904)** — Wikisource `The_Code_of_Hammurabi_(Harper_translation)` — **PD**.
§1 + prologue quoted across renders (content-identity: King "If any one ensnare another…"; Harper "When the lofty Anu…"). **Flagged residue:** the **CDLI/ORACC native ATF + stele P-number** (`P461271` WRONG → likely composite `Q007317`; reachability disputed) → Assyriologist + working CDLI; **eHammurabi** = "© OMNIKA, Some rights reserved" → reference-only, NOT redistributable; Winckler 1904 OCR (Fraktur) is messy → Assyriologist; ancient-script fidelity unverified-by-us.

### Cross-corpus independence achieved
- #1 Rosetta = cross-**script** within one artifact (hiero/Demotic/Greek).
- #2 Thucydides = cross-**language** (Greek/Latin/English, 3 eras), uniform CC-BY-SA-4.0.
- #3 Hammurabi = cross-**language incl. non-English** (English ×2 + German) + a native transliteration.
Together = the maximally-independent multi-language render-base the F335/F337 truth-filter wants. **Next:** a Hebrew (Sefaria) and/or Sanskrit (GRETIL) set to widen beyond the European/Mesopotamian axis; the CDLI/ORACC native-ATF upgrade (when access works); and #847 (native-language peer-review) as the methodology sibling.

---

## KERNEL ROSTER — per-locale native-instruction kernels + build catalogs (user direction, 2026-06-03)
**Principle — each its own kernel, no cross-pollution.** Locale / language / script each get an **independent native-instruction kernel**, built from *"how to speak/write THIS variety"* (grammar/usage, open-access), NOT from translations or cross-variety content — the **F49 / R-RBS-LM-73** discipline applied at the locale level. **en-US ≠ en-GB ≠ en-AU** structurally; collapsing them = **locale-pollution**.

**The kernels NEST — three layers; the truth-filter recurses at each:**
| layer | examples | render-set role |
|---|---|---|
| **script** | Latin · Cyrillic · Greek · hieroglyphic · Demotic | symbolic render-surface; shared across languages (Latin → En/Fr/It/De/Es; Cyrillic → Ru/Uk/Bg/Sr) |
| **language** | English · French · Italian · German · Russian · Spanish | grammatical/lexical structure, rendered in a script |
| **locale** | en-US · en-GB · en-AU ; es-ES · es-MX | locale conventions (spelling / idiom / usage) |

**cross-locale (en-US/GB/AU) ⊂ cross-language (En/Fr/It/De/Es) ⊂ cross-script (Latin/Cyrillic/Greek)** — each level is a ≥3-independent-render set ⇒ **nested truth-filter** (F334/F335 recurses per layer).

**Roster (user-specified) + build plan:**
| kernel | layer | native-instruction corpus (target) | availability | status |
|---|---|---|---|---|
| **en-US** | locale | McGuffey (R-RBS-LM-73) + US grammar/usage | rich | partial-self-checkable (English) |
| **en-GB** | locale | UK grammar/usage (PD grammars) | rich | — |
| **en-AU** | locale | AU usage/style | **thinner** — source carefully | — |
| **French** | language | OA French grammar/usage (Gutenberg/OER) | moderate | triality |
| **Italian** | language | OA Italian grammar/usage | moderate | triality |
| **German** | language | OA German grammar/usage | moderate | triality |
| **Spanish es-ES** | locale | RAE / Peninsular grammar/usage | moderate | triality |
| **Spanish es-MX** | locale | Mexican-Spanish usage | **thinner** — source carefully | triality |
| **Russian** | language (Cyrillic) | OA Russian grammar/usage | moderate (richest Slavic OA) | triality |
| **Ukrainian** | language (Cyrillic) | OA Ukrainian grammar/usage | **thinner** — source carefully | triality |
| **Bulgarian** | language (Cyrillic) | OA Bulgarian grammar/usage | **thinner** — source carefully | triality |
| **Serbian** | language (**Cyrillic + Latin**, digraphic) | OA Serbian grammar/usage | **thinner** — source carefully | triality; **digraphia = built-in script-control** |

**Build-catalog per kernel (AMSC):** native-instruction corpus + `descriptor.toml` + MPM attestation (source / license / `response_sha256`). **Substitute-verifier triality for every non-English kernel** (the user is not multilingual). **Phased:** English locales first (most available + partial self-check) → Latin-script Romance/Germanic via triality → Cyrillic/Russian once the layer is resolved.

**Purpose:** this roster IS the kernel-set for the **cross-coupling / structure-universality experiment** (the prior-turn research direction): build independent native kernels → test cross-coupling at 0 anchors → add #846 Rosetta anchors → measure **anchor-count vs translation-fidelity** = the operational, falsifiable test of "is structure universal." Defensive / MPM / no-lineage; not srmech-gated.

**Controlled-design bonus (Cyrillic-Slavic family; user resolution 2026-06-03):** Russian + Ukrainian + Bulgarian + Serbian = 4 LANGUAGE kernels sharing ONE script (Cyrillic) → the cleanest cross-coupling testbed. **Hold script, vary language** → isolates the *language-layer* coupling from the script confound; **distance-graded** (Ru+Uk = East Slavic, close vs Bg+Sr = South Slavic, further → a coupling-vs-distance *curve*). **Serbian is digraphic (Cyrillic + Latin)** → a same-language-two-script render-set = a **built-in script-layer control** (hold language, vary script). So the Slavic-Cyrillic set supplies *both* experiment controls — scientifically richer than the near-identical English locales (low variation). Tradeoff: all non-English (every kernel needs the substitute-verifier triality) + Uk/Bg/Sr corpora thinner than Russian.

---

## STREAM B — kernel-catalog build BEGUN (2026-06-03): English locales first
**Per-kernel build recipe (AMSC):** (1) source an **open-access native-instruction corpus** ("how to speak/write THIS variety" — grammar / usage / readers, NOT translations); (2) write `descriptor.toml` (the `compute_from_source`/`literature_curated` schema, per R-RBS-LM-13); (3) MPM attestation per source (`source_url` / `license` / `retrieved_at` / `response_sha256`); (4) verify — English locales are **user-sanity-checkable**; every non-English kernel goes through the substitute-verifier triality. Phase order: **en-US → en-GB → en-AU** (then Latin-script Romance/Germanic, then the Cyrillic-Slavic testbed).

### Stream-B set #1 — English locales: native-instruction corpora sourced + attested (2026-06-03)
All English → **user-sanity-checkable** (no triality needed). PD/OA sources, via Project Gutenberg / OA:

**en-US** (rich; R-RBS-LM-73 head-start):
- **McGuffey Eclectic Readers** — Project Gutenberg, **PD**: Primer #14642, First #14640, Third #14766, Fourth #14880 (New-Fourth #1490), Fifth #15040 — *this is the R-RBS-LM-73 grammar-substrate corpus already in-tree.*
- **American grammars** (PD): Kittredge & Farley, *An Advanced English Grammar* (#45814, Harvard); Baskervill & Sewell, *An English Grammar* (#14006, Vanderbilt); Goold Brown, *The Grammar of English Grammars* (#11615).

**en-GB** (clean anchor):
- **Fowler & Fowler, *The King's English* (1906)** — Project Gutenberg **#75439, PD** — the canonical British usage guide (precursor to *Modern English Usage*).

**en-AU** (THINNEST — flagged):
- No comprehensive **PD** Australian grammar. Cleanest OA: **Australian Government Style Manual** (free online since 2020; **license to VERIFY** — likely Crown CC-BY) + **WSU Library Open Textbook Style Guide** (Western Sydney Univ. Pressbooks, **CC** — verify). These are **style/usage** guides, not full grammars — *appropriate*, since en-AU's locale-distinctiveness IS usage/spelling/vocabulary (it shares English grammar with US/GB). **Macquarie Dictionary + Cambridge Guide to Australian English Usage = copyrighted, NOT usable.**

**Honest caveats:**
1. **Register-date** — PD grammars are historical (McGuffey 1836 / Fowler 1906 / Goold Brown ~1850s); a *contemporary*-locale kernel would need modern OA supplements (Wikibooks / OER). Flag each kernel's register; structure-universality should hold across registers, so historical is acceptable for the first cross-coupling test.
2. **en-AU licenses to VERIFY** (Gov Style Manual / WSU) before ingest; paywalled-only → rejected per MPM.
3. **The English locales are usage-level-distinct only** (they share grammar) → cross-coupling among en-US/GB/AU will be **HIGH/near-identical** — which is *exactly why* the Slavic-Cyrillic family is the scientifically richer cross-coupling test (real language-distance). The English locales are the **verifiable warm-up**, not the informative test.

**Next:** write `descriptor.toml` per locale (can-do-now, R-RBS-LM-13 `compute_from_source` schema) + the MPM attestation blocks; the srmech **ENCODE** (kernel-build from corpus) is **srmech-gated** (bugfix-wait). Then Latin-script Romance/Germanic (Fr/It/De) via triality.

### Stream-B sets #2 (Romance/Germanic) + #3 (Slavic-Cyrillic) — triality-cross-checked (2026-06-03)
Substitute-verifier triality (haiku∥sonnet∥opus); all non-English. **It earned its keep — corrected 2 false-negatives + caught 3 pollution sources:** (i) haiku concluded Italian native-instruction was weak / only translation-polluted → **opus found Fornaciari 1882, a clean PD native Italian grammar** (corrected); (ii) sonnet/haiku said Ukrainian was thin/primer-only → **opus found Smal-Stotsky & Gartner 1914, a full PD Ukrainian grammar** (corrected); (iii) **rejected as polluted per F49:** Vittorini (Italian — an EN→IT *translation* for English learners), Belinsky & Grech (Russian — *reviews* of grammars, not grammars), Tsertelyev (Ukrainian — a review).

**Set #2 — Latin-script:**
| lang | primary native-instruction corpus | secondary | license | verify |
|---|---|---|---|---|
| **French** | Bescherelle, *Grammaire nationale* (1850), fr.wikisource | fr.wikibooks (native FR) | PD + CC-BY-SA | primary-verified (verbatim body; 2/3) |
| **Italian** | **Fornaciari, *Grammatica italiana dell'uso moderno* (1882), it.wikisource** | it.wikibooks (native IT) | PD + CC-BY-SA | primary-verified (verbatim, opus); **Vittorini REJECTED (translation)** |
| **German** | de.wikibooks *Deutsche Grammatik* (modern, native) + Wustmann *Allerhand Sprachdummheiten* (1912, Gutenberg) | Grimm *Deutsche Grammatik* Bd.1 (1822) = foundational-historical anchor | CC-BY-SA + PD | primary-verified (verbatim); **Grimm flagged: historical-comparative + Fraktur OCR, NOT modern-learner** |

**Set #3 — Cyrillic-script:**
| lang | primary native-instruction corpus | secondary | license | verify |
|---|---|---|---|---|
| **Russian** | Grot, *Русское правописание* (1885), ru.wikisource | Lomonosov *Российская грамматика* (1757, ur-text); ru.wikibooks | PD + CC | primary-verified (verbatim, opus); **Belinsky/Grech reviews REJECTED** |
| **Ukrainian** | **Smal-Stotsky & Gartner, *Граматика руської мови* (1914)** — uk.wikisource / archive.org / Diasporiana (3 OA homes) | Derkachov 1861; Simovych 1919 | PD | primary-verified (verbatim, opus); **THINNER — under-catalogued** (Bruce-modern + Tsertelyev-review rejected) |
| **Bulgarian** | Neofit Rilski, *Болгарска грамматика* (1835) — zografnasledstvo / strumski / Wikimedia Commons | — | PD | **3/3 on source; THINNEST — image-scan only (no OCR text-layer → transcription needed); 1835 transitional register** |
| **Serbian** | Novaković, *Српска граматика* (1894), sr.wikisource | Vuk Karadžić *Писменица* (1814) | PD + CC-BY-SA | primary-verified (verbatim Cyrillic; 2/3); **SCRIPT-CONTROL DISPUTED** |

**Flagged residue (honest non-multilingual limits → native-speaker / linguist):**
- **Script-content fidelity** unverified-by-us across all (we verified provenance/license/native-not-translation, not the grammatical *content*).
- **Wikibooks EN-mediation:** prefer **native-script wikibooks** (fr/it/de/ru.wikibooks) — the en.wikibooks frame carries EN render-fiber.
- **Register-date:** PD grammars span 1755–1914 (historical registers); contemporary-locale kernels need modern OA supplements (the native-script wikibooks).
- **Bulgarian = image-scan only** (Rilski 1835) → an OCR/transcription pass is required before ingest.
- **Serbian script-control DISPUTE:** sonnet — the sr.wikisource Novaković page has a Cyrillic↔Latin toggle = the hold-language-vary-script control; opus — that toggle may be a Wikisource *transliteration-render*, and no clean PD *digraphic* source exists (Vuk 1814 predates the reform; modern dual-script grammars are in-copyright). **Resolve whether the toggle is a genuine dual-script edition before using Serbian as the script-control.**
- **Ukrainian under-catalogued:** Smal-Stotsky 1914 is NOT linked from the author's Wikisource page — a naive search misses it (found via archive.org/Diasporiana).

**Availability verdict (as predicted):** FR/IT/DE/RU = rich, clean, text-layer PD. UK/BG/SR = thinner (UK under-catalogued; BG image-scan-only; SR script-control-disputed). None invented; all reached by fetch.

**Status:** Stream B corpora SOURCED + ATTESTED for all 7 + the 3 English locales = **10 kernels' corpora identified.** **Next (can-do-now):** `descriptor.toml` + MPM blocks per kernel; resolve the BG-OCR + SR-script-control residues. **srmech ENCODE = bugfix-gated.** The Cyrillic-Slavic set is ready as the cross-coupling testbed (Ru/Uk/Bg/Sr; Serbian script-control pending resolution).
