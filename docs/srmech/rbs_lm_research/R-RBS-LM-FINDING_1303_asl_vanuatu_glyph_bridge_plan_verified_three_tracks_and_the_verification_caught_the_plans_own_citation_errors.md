# F1303 — **the ASL / ni-Vanuatu glyph-bridge research + action plan, produced by two ultracode workflows (design: 11 agents; verify: 9 agents) and main-loop-checked, is LODGED** (`R-RBS-LM-PLAN_asl_vanuatu_glyph_bridge_verified.md`). The structural thesis survives verification; the three code defects it names are all real; and the verification pass **caught the plan's OWN citation errors** — its headline "citation-fix" was itself wrong. **Safe to lodge; NOT safe to build from as written** — three hard blockers gate any build.

**User (2026-07-21 → 2026-07-22):** *"check if our ni-vanuatu glyph primitive also has ASL to bridge missing glyphs and/or glyph-sequence to english with escapable names that could be glyph form and standardized. we likely don't have this yet, so let's make the research and action plan in ultracode."* → *"proceed with ASL/ni-Vanuatu."*

## What was built
Two workflows, then a main-loop check:
1. **Design** (understand→design→verify→synthesize, 11 agents): mapped the ni-Vanuatu base, the ASL/SignWriting work, the glyph→concept gap, and the escapable-name discipline; designed three tracks; adversarially verified each.
2. **Verify** (9 agents): every **code** claim grep-checked against the repo, every **citation** web-verified per MPM, the **structural** claims run, and an adversarial break — folded into a **§7 Verification Pass**.
3. **Main-loop check**: caught one verification overstatement (below).

## The thesis (survives verification), with the directionality corrected
The bridge **reads** three things already in one stack, and wires the read-out the genome only *represents* today:
- **ni-Vanuatu byte/glyph = the order-native base** — a word is a directed **unicursal walk** (sandroing = an Eulerian circuit; UNESCO ICH 00073, attested).
- **ASL = a PEER glyph→concept system at the same level as the base** (F761), on the 2D-spatial "draw-it" pole with SignWriting.
- **English = a lossy projection of the ORDER-NATIVE BASE** — *corrected* from the plan's "lossy projection of ASL specifically," which the verification refuted against F761 (ASL is a peer, not above English).

**The load-bearing constraint (confirmed):** the *live* base as shipped is the **abelian Klein-4 bind — metric-only, ZERO curvature** (can't tell `cat` from `tac`; F1211/F1255). Direction lives only in the non-abelian channel (magnetic-Laplacian charge / `the_one` winding / `cd_mult`), prototyped in F1213 but **not swapped into the live language layer**. Any bridge that flattens a glyph-sequence to ASCII inherits zero-curvature. This links straight to **F1301/F1302**: the direction/perspective lives in the edges' held superset and the hypercomplex spectral read — not in the flat projection.

## Three tracks
- **A — missing-glyph bridge (fingerspelling-analogue): SURVIVES.** A missing glyph resolves to a standardized ASL-glyph-form composition, *surfaced* (build-the-kernel), never stripped.
- **B — glyph-sequence → English: NEEDS-REWORK / gated.** Three referenced ops don't exist on disk and a covert English-word flatten hides in its concept-resolution step; blocked behind the directed-encoder swap.
- **C — escapable, glyph-form, standardized names: SURVIVES.** The escape stays glyph-form (a standardized composition of base glyphs, like fingerspelling), content-addressed, never raw ASCII — modeled on the `# srmech-allow:` in-band escape.

## The verification caught the plan's OWN errors (the point of the pass)
| the plan said | verification found |
|---|---|
| "the 5-parameter model is **Liddell & Johnson 1989**" (its headline citation-fix) | **WRONG** — L&J 1989 is the *Movement-Hold* model, not a 5-parameter model. The plan shipped a false fact dressed as the authoritative correction. |
| ASL-LEX 2.0 = **2,723 signs** under the 2017 DOI | **MPM violation** — 2,723 is a *separate* 2021 paper (Sehyr et al., *J. Deaf Studies & Deaf Education* 26(2):263–277), not under `10.3758/s13428-016-0742-0`. Split into its own MPR. |
| Devylder 2022 TAJA **33(3)** | **33(2)** (Wiley + Munin agree). |
| ISWA "**652 symbols** in 7 classes" | **652 BASE symbols** (full set 37,811); primary source is the IETF draft, not Wikipedia. |
| in-tree "**2,297 / 2,280** two readings" | the "two readings" framing is **refuted** — 2,280 is an iconicity-rated subset, not a second read of the 2,297 file. |
| "UNESCO ~80 vs ~130 languages — reconcile" | **not a discrepancy** — ~80 = the sand-drawing region; the national figure is **138** (not 130). |
| ATTESTED, correctly | ASL-LEX Caselli 2017 (DOI verified, OA), UNESCO ICH 00073, Stokoe 1960 (3 params), Battison 1978 (4th=orientation), Sutton SignWriting Unicode 8.0/1974, Munn 1973 (*citation* only — the meanings are Warlpiri cultural knowledge, never framework data). |

## The three code defects (all confirmed) + the hard blockers
- `asl.py:167` — `out.append("fs:" + "-".join(w.upper()))` — the **ASCII fingerspell flatten** (no-flatten violation).
- The `1080` coupling seed — a **DRAWN magic number** (F1259), in two files.
- `corpus_store.py:24` — `klein4_random(LEAF, seed=1080)` — a **second** 1080 pin **and** a call to `klein4_random`, **DELETED at rc297** (F1284/F1285). **The store spine is non-runnable.** *(It escaped the F1285 rename — that glob ran under `rbs_lm_research/`, not the sibling `siona/`.)*

**Build blockers (gate any build, §7.4):** (1) the L&J false fact, (2) the 2,723 mis-attribution, (3) the non-runnable `corpus_store.py`. Everything else is a correction-before-build, not a lodge blocker.

## The meta-lesson: the verification itself needed a check
The verify agent wrote that **F735 and F1128 "appear nowhere"** — but both exist as research-tree findings (9 files reference F735). Its *substantive* point holds — these are **session-ledger** findings, not durable srmech-package / auto-memory records, and should be tagged as such — but "appears nowhere" is an overstatement, caught by a main-loop grep. **Even an adversarial verification pass is a read that can over-project; it got its own check.** That is F1301/F1302 one level up: which read you use determines what you can see, and no single read is authoritative.

## Verdict / next
**Lodged with §7 attached as the checked-not-asserted guarantee.** The user's hypothesis was right: we had the pieces (both glyph systems, the gap named in F1140, the sublanguage-kernel escape in F764/F817) but **not the wiring** — no ASL bridge for missing glyphs, no glyph-sequence→English through the ASL spine, no escapable glyph-form standardized naming. The plan supplies the wiring, gated on: the F1213 directed-encoder live-swap (kills the zero-curvature base), the three citation/code blockers, and the de-magick of the `1080` seed to a Class-A content-address. **Next question handed to the expert (F282):** a Deaf / sign-linguistics reviewer on the manual-alphabet correspondence and the classifier routings — which are constructed *illustrative placeholders*, not measured ASL data.

Composes the two workflows, **F1140** (the gap), **F761** (ASL/SignWriting as peers of the base), **F1211/F1255** (the abelian zero-curvature base), **F1213** (the directed encoder), **F735/F1128** (session-ledger, ASL/SignWriting structure), **F1259** (the magic seed), **F1284/F1285** (the deleted `klein4_random`), **F1301/F1302** (direction lives in the edges/hypercomplex read, not the flat projection), **F282** (hand the question to the expert), `[[feedback_pdf_extraction_citation_discipline]]`, `[[feedback_trauma_informed_defensive_scope]]`.
