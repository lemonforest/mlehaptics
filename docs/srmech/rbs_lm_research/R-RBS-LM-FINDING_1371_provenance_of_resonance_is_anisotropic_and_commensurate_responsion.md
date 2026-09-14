# F1371 — **provenance: "resonance is anisotropic" came from the maintainer on 2026-09-07, was endorsed twice by the main assistant within 12 minutes, withdrawn 47 minutes after the first endorsement, and fenced that evening without the endorsement recorded; an assistant had labelled a different maintainer object "anisotropic" on 2026-05-23; "responsion is commensurate / incommensurate" first appears in F1308 (2026-07-23); "a measure of commensurateness" is the maintainer's 2026-09-14 wording**

**User (2026-09-14T17:21Z), as quoted verbatim in the Fable report:** *"it's in my notes from research that the asymmetric asymptotic resonator description … in some earlier research you'd help us decide that what I was describing was a thing that is anisotropic"*

Session research, 2026-09-14, landed from the session scratchpad. Two independent investigators, Fable (high) and Opus (xhigh), worked read-only over the repository (all refs), the memory directory, PR comments and the session transcripts. Both reports are in `F1371_supporting/` verbatim, except the disclosed code spans below, with their scripts. Labels are the reports': MEASURED / DERIVED / CANDIDATE.

**Instrument limit, stated first by both (MEASURED).** Exactly one top-level session transcript exists on this machine, spanning **2026-08-08T23:09Z → 2026-09-14**. Before that date the only witnesses are committed text, memory files and PR comments. "No earlier endorsement" is therefore bounded to 2026-08-08 onward, plus those witnesses.

## 1 — "anisotropic": the dated record

| UTC | speaker | what happened (verbatim where quoted) |
|---|---|---|
| 2026-05-23 | assistant-authored label on a maintainer description (memory `user_stance_finite_fractal_stacked_minima_anisotropic_expansion_cascade.md`; blessed CANONICAL 2026-05-25; on `main` in unsolved-maths §11.8, commit `168402709`) | the maintainer: *"a finite length fractal/(coch spiral structure), where local minimuma could be stacked to create a rapidly expanding structure …"* → the assistant: *"**Anisotropic**: the expansion happens in ONE direction (the stack-axis); perpendicular axes are unaffected by this mode."* A different object from the resonator, labelled in an abstract stack-axis sense |
| 2026-07-03 | maintainer's own edit, `a5b2956ae`, MFO:91 | *"An asymmetric resonator."* — the tree's phrase |
| 2026-09-07T17:38:37Z | **maintainer** | *"… op(x)operand(x)responsion / distributional(x)relational(x)responsion / eigenvectors(x)edges(x)eigenvalues and resonance is anisotropic -- describe both continuous and discrete systems."* |
| 2026-09-07T17:39:39Z | **main assistant — endorsement** | *"And 'resonance is anisotropic' fits cleanly: the spectrum isn't a scalar, each eigenvector carries its own eigenvalue. Direction-dependent in both domains."* |
| 2026-09-07T17:50:07Z | **main assistant — second endorsement** | *"It also sharpens 'resonance is anisotropic': the spectrum is spread rather than scalar …"* |
| 2026-09-07T18:25:24Z | subagent | a zero-hit search: the phrase *"is not tree text"* |
| 2026-09-07T18:26:14Z | **main assistant — withdrawal** | *"Also: 'resonance is anisotropic' is not tree text — zero hits. The tree's phrase is 'an asymmetric resonator' …"* (it does not acknowledge the two endorsements) |
| 2026-09-07T21:54:47Z | commit `98a405be9` → MFO §VIII.31.20 item 5; merged `fc717212d` (gh #1681) 2026-09-08 | the fence: *"'resonance is anisotropic' appears nowhere under docs/ … must never be quoted as a framework convention"*; it cites F1209 and does not record the 17:39Z / 17:50Z endorsements or the 2026-05-23 label |
| 2026-09-14T14:45Z, 17:21Z | maintainer | the phrase re-raised; the recollection of an earlier "anisotropic" judgement |

**Other senses of "anisotropic" on `main` (Opus, MEASURED).** Beyond the geometric sense, `main` carries the abstract stack-axis sense (unsolved-maths §11.8; `cost_asymmetry/round1_entry_C…:650`) and the algebraic quadratic-form sense in shipped code (`srmech/cascade/cayley_dickson.py:3536`, `CHANGELOG.md:9822`: *"composition AND AN ANISOTROPIC NORM ⟹ no zero divisors"*). So the fence's sentence *"Every `anisotropic` on `main` is the ordinary geometric sense"* is false as written.

## 2 — was the 2026-09-07 endorsement sound? (MEASURED at srmech 0.9.0rc472, pure cell)

- **Fable.** `cyclic_laplacian_spectrum(7)` has multiplicities (1, 2, 2, 2) with `chirality_paired True`: the k and −k eigen-directions share one eigenvalue. Q₃ gives `[0, 2, 2, 2, 4, 4, 4, 6]`, degenerate eigenspaces with no distinguished direction. A directed C₄ under `magnetic_laplacian` gives the identical spectrum `[0.292893, 0.292893, 1.707107, 1.707107]` for q = +1/8 and q = −1/8; the reversal shows only in `cycle_holonomy` (1/8 → 7/8). DERIVED verdict: in the sense used, the statement is a tautology for any non-scalar operator and false on degenerate eigenspaces, and the resonator's asymmetry lives in the holonomy channel. *"The 18:26Z withdrawal was correct; the endorsement was not sound. The 05-23 use was sound for its object."*
- **Opus.** S1: the Rayleigh quotient on C₅ over four exact directions gives four distinct values — true, but generic to any non-scalar operator. S2: `onesᵀ L ones = 0` for a nonzero vector, so the Laplacian's form is **isotropic** in the algebraic sense. S3: the definite octonion norm is anisotropic (2 for every e₀ + eᵢ), while split twists are isotropic. Verdict: *"vacuous in sense S1, contradicted in sense S2."* The 2026-05-23 label is *"sound as a definitional label and unmeasured as a property"*.
- **From the consolidation brief (coordinator summary):** the endorsement was measured unsound as stated — K₄ is isotropic, and eigen-direction anisotropy and the tree's "asymmetric" vary independently. The K₄ figure is the coordinator's; neither report prints it.

## 3 — "responsion is commensurate / incommensurate"

| date | where | what (verbatim) |
|---|---|---|
| 2026-07-05 | F1065 (`ea676bef3`, this branch) | precursor, about a spectrum: *"Resonance closes the form iff the spectrum is commensurate."* |
| 2026-07-09 | F1179 / F1180 | the word "responsion" enters |
| **2026-07-23** | **F1308 (`92752b935`, this branch), answering the maintainer's e4 question** | **earliest statement:** *"inharmonic = the responsion in its INCOMMENSURATE value"*; *"harmonic = the responsion's HIGH / short-period end … the commensurate/consonant case"* |
| 2026-07-23 | srmech notebook `:6390` §3.42.5 (`72d5e8aec`) | *"harmonic / inharmonic / subharmonic are all values of the responsion"* |
| 2026-09-08 | srmech §3.59.12 (`4b70cc06d`) | the rule: *"the responsion is commensurate / incommensurate (Tier 1/2/3, rational rank `r` of `n`)"* |
| 2026-09-14T14:45Z | maintainer | *"responsion is a measure of commensurateness"* — the first and only occurrence of that wording |

Both reports (MEASURED): no record says the responsion **is a measure of** commensurateness. Every sentence predicates commensurateness of the responsion's **values**. The maintainer's recollection that an assistant said the responsion is commensurate / incommensurate is accurate (F1308).

## 4 — what both recommend (a later corrections step, not this commit)

**Keep the fence's ruling; amend its provenance and its definitions; do not retire it.**

- Record the dated path: maintainer 17:38Z → assistant endorsement 17:39Z and 17:50Z → withdrawal 18:26Z → fence 21:54Z.
- Record the 2026-05-23 label as the one earlier assistant use of "anisotropic", scoped to the stacked-minima expansion mode, not the resonator.
- Widen *"anisotropy is spatial direction-dependence"*: Fable proposes "direction-dependence (spatial, or along a preferred axis of an abstract space)"; Opus proposes the three senses that `main` actually carries.
- Add the measured sense checks (§2).
- Note the transcript scope limit (before 2026-08-08, not on disk).

For §3.59.12: keep it, and say explicitly that it rules on the responsion's values, and that "a measure of commensurateness" is the maintainer's paraphrase. Fable also notes that the memory references `#717` / `#719` are local task IDs that should read `#T717` / `#T719`.

## Supporting files

`F1371_supporting/` holds `fable_high_report.md` and `opus_xhigh_report.md`, plus the scripts `fable_high_scratch/{measure_aniso.py, tx_grep.py}` and `opus_xhigh_scratch/{measure_aniso.py, measure_aniso.out.json, scan.py, subscan.py, lines.py, genuine.py}`. A `.gitattributes` (`* -text`) keeps the bytes exact.

**Changes to the reports, disclosed:** three bare local-task references inside quoted memory text (`#717`, `#719` in the Fable report; `#719` in the Opus report) gained code-span backticks so they cannot autolink. The digits are unchanged, and the Fable report's own sentence naming GitHub `#717` / `#719` as unrelated PRs is left as written.

**Not copied, deliberately:** the transcript-derived extracts. They are raw excerpts of the session conversation and of subagent transcripts, which the reports quote only where load-bearing. Left in the volatile session scratchpad and **not preserved** by this commit:

- `fable_high_scratch/{main_addl.txt, main_aniso.txt, main_commens.txt, main_resonator.txt, sub_aniso.txt, sub_files.txt, sub_ria.txt, sub_ria2.txt, sub_ria_hits.txt, branch_add_dates.txt, date_map.tsv}`
- `opus_xhigh_scratch/{key2.txt, key_lines.txt, main_aniso.txt, main_asymres.txt, main_comm.txt, main_newterms.txt, newterm_lines.txt, sub_pre.txt, user_asym.txt, pr679_aniso.txt, findings.txt}`

None was over 1 MB. The scripts that produced them are included.

**Composes:** F1370, F1308, F1065, F1209.
