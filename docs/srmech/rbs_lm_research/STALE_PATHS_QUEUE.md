# STALE_PATHS_QUEUE.md — research paths surfaced but not walked

Per `[[feedback_full_coverage_shipping_mpm_way]]` and `[[feedback_rolling_pr_partition_boundary_updates]]`: trailing research items that opened during sessions but weren't walked. Queue captured for future scope-specific sessions to avoid re-deriving the trail.

**Maintenance**: when a path is walked, move its entry to the finding that resolves it. When new paths surface, add them at the bottom of the relevant section.

---

## §1 Long-pending RBS-LM/NN task list items

These have been pending in the task list across sessions:

| Task ID | Subject | Notes |
|---|---|---|
| **R-RBS-NN-4** | Token → hypervector encoding | **About to be walked in this session as Phase 1 of post-F143 work** |
| R-RBS-LM-47a | LLM input format test (text vs relationships on the wire) | Tests whether relationship-form input to an LLM gives cleaner cascade extraction than text-form |
| R-RBS-LM-46c | Tie-breaking ablation at depth-2-uniform | Methodology refinement on F46b series |
| R-RBS-LM-55 | Pure-structure layer ("relationships of relationships") | Higher-order binding test; arts/structure work |

---

## §2 Open questions from F137-F142 walked findings

### From F137 (capacity comparison)

1. **Skip-zero polar similarity**: does excluding zero-zero matches change polar's lead vs bipolar? (Possibly drops polar below bipolar.) Quick follow-up; ~30 min smoke test.
2. **Per-bit-of-information capacity**: when normalized by bits-encoded per D, does klein-4's 2-bit-per-position give real headroom over bipolar's 1-bit-per-position?
3. **D-matched-bits comparison**: bipolar D=20000 vs klein-4 D=10000 (matched total bits). Does klein-4 still lose on raw capacity?
4. **Noise robustness across variants**: at moderate bit-corruption rates (separate from F141 plasticity decay), do the three variants degrade differently?

### From F138 (Klein-4 + Class L weak signal at small D)

5. **D-sweep for chirality-tag recall threshold**: at what D does chirality-tag recall reach >0.5 reliably? Sweep D ∈ {1024, 4096, 16384, 65536} at fixed N=32.
6. **N-sweep at fixed D**: at what N does recall reach >0.5? Sweep N ∈ {4, 8, 16, 32, 64} at fixed D=1024.
7. **Encoding refinement comparison**: random projection per eigvec vs sector-axis-separation vs multi-position quantisation (F138 §5).
8. **Eigval-based sector assignment**: assign chirality sector by eigvalue magnitude (Mersenne-fiber-degree ℓ ∈ {1,3,7} per Spike #185 alignment). Does this give cleaner Class L → Class M handoff?

### From F139 (chirality axis at scale)

9. **Very-high-N collapse threshold**: at what N do discrimination signals collapse below noise floor for same and cross both?
10. **Partial chirality flips**: XOR with sector mask 1 (γ₅ only) or 2 (iω₇ only). Per F130's (γ₅, iω₇) decomposition, partial flips should give intermediate signal strength.
11. **Mixed-sector bundles**: sectors with different distributions (e.g., 75% visible-matter, 25% dark-matter). Does the visible-antimatter retrieval still anti-correlate equally?
12. **D vs N tradeoff curve at fixed discrimination gap**: Pareto frontier in (D, N) space for chirality-axis operations.

### From F140 (multi-class cascade)

13. **Cascade depth scaling**: at what depth (5-class, 6-class, ...) does chirality discrimination collapse?
14. **Class order matters?**: same cascade with classes in different orders (e.g., Class I before Class L vs after).
15. **Class K interaction in cascade**: Class K sign-flip's role as the "asymptotic-DOF / phase-boundary"; expected chirality-axis interactions when inserted.
16. **Inverse cascade for content recovery**: can we INVERT Class I cyclic shift + bipolar XOR to recover ORIGINAL eigvec content from chirality-tagged composite?
17. **Bipolar vs polar in cascade**: substitute polar HDC for bipolar identity HV; how does 3-state interact with cyclic shift + chirality tag?

### From F141 (polar plasticity)

18. **Klein-4 under decay**: how does Klein-4 (4-state rank-2 variant) handle decay-as-zero? Does chirality axis remain operational at high decay?
19. **Decay-recovery dynamics**: if decayed positions can RE-WAKE (0 → ±1), does polar's signal recover as binding strengthens? (Hebbian rehearsal.)
20. **D/N/decay tradeoff Pareto frontier**: at fixed signal threshold (above-rand > 0.05), the polar-vs-bipolar Pareto frontier in (D, N, decay) space.
21. **Noise-vs-decay distinction**: polar handling SIGN-FLIP noise (bipolar v1 model) vs ZERO-INJECTION decay (polar v2 model). Both representable.
22. **Multi-class cascade under decay**: F140 verified preservation under cascade; how does decay propagate through cascade classes for polar vs Klein-4?

### From F142 (BCI chirality-native encoding)

23. **What real-world signals carry chirality?** Per F132 §8: drug molecule recognition by chirally-asymmetric receptors; helical molecule binding states; asymmetric oscillation patterns. None tested.
24. **Polar + Klein-4 HYBRID**: polar amplitude robustness + Klein-4 sector tags for chirality. Combined encoding.
25. **Chirality structure in cross-substrate cognition (F118)**: cetacean/chimp/octopus — does any substrate exhibit chirality structure that Klein-4 would discriminate?
26. **Cross-natural chirality datasets** (per F135): snail shell handedness, beak laterality, plant spiral. Where Klein-4 would help vs raw classification.
27. **MFO §VII.4.1.7 4-way at signal level**: encode (RH+/RH−/LH+/LH−) BCI-like signals natively. F139 verified at binding-algebra level; signal-level extension is open.

---

## §3 Open questions from framework findings (F127-F136)

### From F135 (substrate vs shadow chirality)

28. **Shadow-stepping shape**: cross-natural chirality rates do NOT show Mersenne-fiber stepping per F135 §4. What's their actual scaling shape? Power-law? Phylogenetic?
29. **Cross-natural inverse-ratio testability**: does dark:visible ratio show up inversely in observed RH:LH chirality across species/scales? F135 §5 substrate budget; needs scale-stratified data.
30. **Chirality-as-projection mechanics**: precise mathematical form of how substrate chirality projects to shadow chirality. Per F135 §9 question. Open framework question.

### From F136 (Roman numerals substrate-native chirality)

31. **Roman glyph stroke counts**: do actual stroke counts (1 for I, 2 for V, 2 for X, …) carry chirality beyond rotation properties? F136 §10 question 1.
32. **Indic vs Hindu-Arabic positional**: does Indic predecessor notation carry chirality structure modern Arabic lost? F136 §10 question 2.
33. **Cuneiform / hieroglyphic numeration chirality**: cross-substrate examples beyond Roman. F136 §10 question 3.
34. **Notation as substrate-interface (F133 connection)**: notation choice as observer-projection-locking? Per F136 §10 question 4.
35. **D₄ dihedral alternative to Klein-4 as binding algebra**: per F136 §10 question 5; D₄ has 180° rotation natively. Worth comparing to Klein-4 empirically.
36. **2-line ASCII figure generalization**: octonionic-Hopf (S⁷ → S¹⁵ → S⁸) rendering. F136 §10 question 6.

---

## §4 Pre-session items that remain open

These pre-dated the wishlist-resume session but weren't addressed:

37. **R-RBS-LM-52a NLP-corpus test of K3 sequence kernel** — opened in earlier session; may be partly addressed by later findings but not formally closed
38. **Compressed-semantic substrates** (Egyptian / NA Native / classical East Asian) — R-RBS-LM-54i ran; results in JSON but no follow-up walk
39. **F70 Test B** (companion to F70 Test A "HDC layer decorative?") — opened in 2026-05-26 session; B was never run
40. **R-RBS-NN-9 deferred items** (catalog SSoT absorption) — per rbs_nn_research/ROADMAP NEXT-2

---

## §5 Application-direction deferrals from F143

Per F143 §3, these F132 §8 application directions are explicitly deferred to scope-specific sessions:

41. **Pharmacological chirality-state encoding** (F132 §8 item 2) — drug-target chirality compatibility
42. **Cosmic-chirality reasoning** (F132 §8 item 3) — CP violation, dark sector at substrate-encoding level (vs MFO framework level)
43. **G-quadruplex-aware biology research** (F132 §8 item 4) — telomere aging, oncogene promoters, gene regulation via G4
44. **Cross-substrate cognition modeling at substrate-encoding level** (F132 §8 item 5) — cnidarian / octopus / vertebrate substrate variants

---

## §6 Items NOT in this queue (NOT stale, just out of scope)

- Items requiring CAD-grade fabrication geometry (per CLAUDE.md §4 ban)
- Items requiring trauma-informed-scope violations (per `[[feedback_trauma_informed_defensive_scope]]`)
- Items requiring framework-lineage claims (per `[[feedback_no_lineage_claims_in_notebook]]`)
- Items requiring continuous-number-line pedagogy (per `[[feedback_continuous_number_line_pedagogical_obstacle]]`)

If any item above accidentally crosses a discipline boundary, it gets dropped from the queue rather than walked.

---

## §7 Queue maintenance protocol

- Add items as they surface from new findings
- Move items to resolution findings when walked (cross-reference both directions)
- Annotate priority casually (small, medium, big) when adding — helps future-self pick what fits available scope
- When count exceeds ~50 items, consider a "harvest pass" where related items get bundled into a sweep finding rather than walked individually

**Current count: 44 items.**

**Priority hints** (informal):
- Quick wins (~1 hour): items 1, 2, 5, 6, 7, 10, 31
- Medium scope (~1 session): items 9, 13, 18, 19, 21, 35
- Big scope (~multi-session): items 17, 22, 23-27, 41-44
- Framework-level open questions: items 28-30, 32-34, 36

---

*Created 2026-05-27 per user direction "collect a list if any trailing research paths went stale that we can queue". Replaces ad-hoc inline open-question lists with a single central queue. Maintained alongside the rolling RBS-LM PR.*
