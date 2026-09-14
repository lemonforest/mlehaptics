# F1358 — **preserved: the rc426 notation-carrier research (`#T1124`) — the carrier is a torsor, the clef is an origin the page cannot hold, the KEY is not torsorial, and two of its own sourced rows were retracted after reading the PDFs**

Consolidation record (2026-09-14). Source: local branch `research-rc426-notation-torsor`, five commits on no remote (2026-08-11). All 14 touched paths were absent here, so all five commits were cherry-picked with `-x`, in order.

## What the commits found (their own words and labels)

**Setup, as stated in the first commit:** *"READ-ONLY research spike. No package change, no version bump, no PR."* Generating scripts and NDJSON artifacts under `docs/srmech/notes/`; *"All measurements run on 0.9.0rc424 under WSL2 with numpy ABSENT."* Headed *"MEASURED, not asserted"*:

- **P1** — *"0 of 29 carriers and 0 of 612 ops name a notation object. The notation layer is EMPTY."* Of rc424's 6 relational music ops, 3 are frame-parametric / frame-free and 3 hard-wire ℤ/12, reaching it through private helpers (the first version of the script under-reported this; the correction is left visible).
- **P2** — the GIS axioms executed: ℤ/n is a torsor at every n in {5,7,12,17,19,22,24,31,53}, *"12 is not special"*. The 24 consonant triads under T/I (non-abelian, 360/576 non-commuting pairs) are a torsor 13824/13824 + 576/576. Reversing the composition order breaks axiom A (5184/13824) while simple transitivity survives both ways. 4 negative controls, 0 wrongly blessed.
- **P3** — `octonion_frame_read` satisfies the clef shape on all 28 frames: *"something moves (11 of 12 fields), something survives (`norm_sq`, 1/28)"*, and no frame-free quantity singles out the default frame. The frame set is not one torsor. `oct_torsor_*`'s group measures as **Q8**, and *"0 of 7 candidate pitch-interval groups can be hosted"*.
- **P4** — *"octave equivalence IS the shipped central extension"*: `center_lift`'s shadow is bit-identical to the `cyclic_mod_add` chain at 10/10 moduli, and the origin torsor's group is ℤ, not ℤ/n (0/25 vs 25/25). An executable three-bucket leak test catches the three shipped ℤ/12 ops.
- **P5** — the carrier+chart prototype *"falsified its own first atlas test"*: checking compatibility through the carrier blessed a deliberately corrupted chart 1225/1225. Under the corrected condition that chart fails (30/35), and the derived transition for an origin shift produced the key-signature shape unprompted (rotate by 3; one degree of seven needs a flat).

**Second commit**, after a citation round. Lewin: *"GIS-is-a-torsor CONFIRMED-BY-SOURCE"*, with an independent cross-check (k = 9 conjugacy classes gives 24·9 = 216 commuting pairs, measured 216, and 24·216 = 5184, measured 5184). Mazzola: *"'clef as a chart' REFUTED from his own text"*. P6: the origin freedom (clef) is a free action at all 10 moduli, so it is a torsor. The renaming freedom (Syn / automorphism) is free at no modulus. The full chart-freedom group ℤ/n ⋊ Aut(ℤ/n) is transitive but not free (multiplicity 4 at n=12), so it is not a torsor. φ(12)=4 ranks last of the 10 moduli.

**Third commit** adds a positive control to P3's across-line null (`u = 0` returns 7/7) and reclassifies it *"BOUNDED, not REFUTED"*: `octonion_frame_read` presents the 28 frames *"as a FIBRED SET — 7 bases, each carrying a 4-element torsor"*, and only the within-line level is certified torsorial by a shipped op.

**Fourth commit** finds five attested chart families (10 instances: 9 VERIFIED-OA, 1 EXPERT-WEB). Three chart the interval carrier; two do not (instrument-action notations, Western tablature alongside jianzipu). The action→pitch map is total but not injective backwards (preimage histogram {1:10, 2:13, 3:14}). F24: one 6-symbol sequence yields 12 distinct readings across 12 start states — *"this is a TRANSDUCER"*. The Seeger prescriptive/descriptive axis is *"ABANDONED, not used"*. The F24-to-F9 resemblance stays an OPEN QUESTION.

**Fifth commit.** A second sourcing pass disagreed, so the contested PDFs were extracted and grepped directly. The Tse & Wong citation is real. **Gongche → UNSOURCED** (kept as an explicit gap). **F24's anchor → UNSOURCED, claim RETRACTED**: 0 hits for the position-inheritance rule across 417 KB of extracted text, and F24 is reframed as a CONDITIONAL structural result. Pitch-as-output becomes the best-attested row (new tier VERIFIED-SELF). Final tiers: *"6 VERIFIED-OA, 1 VERIFIED-SELF, 1 EXPERT-WEB, 1 CONTESTED, 1 UNSOURCED — and zero unsourced claims stated as fact."*

## Where it lives on PR #687

- Cherry-picked with `-x` (all five commits): `docs/srmech/notes/_p1_notation_carrier_census_rc426.{py,ndjson}` through `_p7_chart_families_sourced_rc426.{py,ndjson}`, 14 files. P2, P3 and P7 were revised by the later commits, which are included.
- Each script's only `import numpy` sits inside an absence probe that prints *"!! numpy PRESENT — environment wrong"*. The scripts carry no numpy dependency.
- Archive: `preserved_branches/research-rc426-notation-torsor/`.

## DIFFERS

None.

Branch safe to delete once this commit is on origin: yes
