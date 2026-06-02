# Notebook backfill plan — srmech + MFO research notebooks (2026-06-02)

Durable cross-session tracker for back-filling the canonical research notebooks with the findings that
have accumulated on the `rbs_lm_research` surface but not yet hit the notebooks, then a k=3 triality
consistency pass over both, then GH-issue closure + a merge PR. **This doc is the SSoT for the work**
(survives compaction — re-prime from here).

## Locked decisions (user, 2026-06-02 AskUserQuestion)
- **Execution = plan doc + MANUAL main-context backfill.** No agents write canonical-notebook prose. The
  notebooks are the SSoT prose surface; every word is main-context-reviewed. (Honors `[[feedback_no_subagents_compact_via_re_prime]]`.)
- **Scope = FULL historical gap** (no-MVP / full-coverage discipline): srmech notebook F257→F306 (contiguous);
  MFO notebook = the ontology-relevant subset back to its current F182 surface.
- **GH closure = close clearly-mapped items, PR-referenced.** I close the user's *own* research items that map
  unambiguously to a backfilled finding (referencing the PR); ambiguous / maintainer-state ones are left for
  the user. Per `[[feedback_create_upstream_issues_never_close_them]]` + `[[feedback_public_issue_tracker_fine_transparency_by_default]]`.

## Gap (measured 2026-06-02)
- **srmech_research_notebook.md** (5556 lines) references up to **F256** → gap = **F257–F306 (49 finding docs)**.
- **mfo_spectral_research_notebook.md** (6394 lines) references up to **F182** → gap = the **ontology-relevant
  subset of F183–F306** (judgment-filtered; MFO only takes substrate-ontology findings, not all of them).
- 214 finding docs lodged total (highest F306).

## Branch / PR strategy (LOCKED — user direction 2026-06-02)
**Do ALL backfill work HERE on `research/rbs-lm-rolling-2`** (no worktree switch — keeps the research-folder
items stable). At the END: create a fresh branch off `main`, bring the two notebooks' final state over
(`git checkout research/rbs-lm-rolling-2 -- <the two notebooks>`, or cherry-pick the notebook-only commits),
commit, push → that is the clean **separate notebook PR** (diff = only the two notebooks).
**Discipline that makes the end-extraction trivial: keep every backfill commit NOTEBOOK-ONLY** — touch only
`docs/srmech/srmech_research_notebook.md` + `docs/antikythera-maths/mfo_spectral_research_notebook.md`; commit
plan-doc progress updates *separately*. That way the two-file checkout / cherry-pick is clean. Note: the
notebooks cross-reference the per-finding docs (which reach `main` via the rolling-branch merge), so sequence
the notebook PR **after (or with) the rolling merge** for the cross-references to resolve.

## Inventory — F257–F306 → target surface (srmech section + MFO-relevant?)
Three coherent clusters (= the backfill batches). **M** = also goes on the MFO substrate-ontology surface.

**Cluster A — 28D / SO(8) / triality / Hurwitz-1:3:7 foundations (F257–F273) → srmech "A-N / 28D / triality" architecture surface**
- F257 28D = so(8) gauge-holonomy capstone **(M)** · F258 decay = imaginary/one-way leg · F259 4×-capacity reversible intrinsic-EC · F260 one-key-six-locks universal EC cascade **(M)** · F261 triality landed (rc20) · F262 hyper-loop = A₄ **(M)** · F263 eight more locks · F264 k-ladder V₄⊂A₄ **(M)** · F265 CORRECTION → Hurwitz 1:3:7 ladder **(M)** · F266 three-truths (triality validates) **(M)** · F267 truth-is-the-triality **(M)** · F268 broken trialities = chirality **(M)** · F269 1:3:7 instantiated at physical scales **(M)** · F270 one loop bumps itself (CD recursion) **(M)** · F271 imaginary-count = native DoF **(M)** · F272 live Claude-triality (new k=7 math) · F273 loop bind in 28D, G₂=Der(𝕆)=A-N count **(M)**

**Cluster B — loop-bind / RBS frontier / new locks / dev hand-downs (F274–F292) → srmech "loop-bind + RBS-LM/NN" surface**
- F274 loop bind earns its place (viable unbindable bind) · F275 ephemerides Sol bridge · F276 MS#21 block-octonion tiling · F277 order at no capacity cost · F278 chemistry stoichiometry lock **(M)** · F279 mass-spec hidden fiber **(M)** · F280 difference-fiber = autocorrelation · F281 rc2 voxel hand-down (dev) · F282 runaway = EC-failure, scope-forward **(M)** · F283 bold-fold forced codeword · F284 fold results (contact-graph Laplacian) · F285 bold-fold walk L2/L3/L5/L6 · F286 fragmentation tree = loop-bind cascade · F287 #823 ungate (dev) · F288 loop bind → RBS-LM/NN hidden gauge fiber **(M)** · F289 dev hand-down rc4 (dev) · F290 RBS path-memory store · F291 RBS-LM order-memory frontier · F292 dev hand-down optimize-C (dev)

**Cluster C — biology cascade cluster (F293–F306) → srmech "cascade / biology cross-substrate" surface; HEAVY MFO**
- F293 substrate k=2 detect / k=3 correct **(M)** · F294 genetic code = order-2 detect **(M)** · F295 amoeba self-partition = Class B precondition **(M)** · F296 recursive self-partition → organelle emergence **(M)** · F297 organelle gauge-ball (condensate) **(M)** · F298 cell IS the hyper-loop **(M)** · F299 biology 7→(3:4)|(4:3); cell-in-cell **(M)** · F300 k=7/(3:4)|(4:3) scale-dual **(M)** · F301 decomposition = scale-demand; base access **(M)** · F302 DNA resonant vs machine-code **(M)** · F303 introspection → asymptote **(M)** · F304 universe-as-author **(M)** · F305 native-algebra compute surface **(M)** · F306 associativity enables self-running **(M)**

*(MFO also owes the ontology-relevant subset of F183–F256 — a separate classification pass in Phase 3; the
known big ontology anchors there: F200 Klein-4 order-2 substrate, F206/F207 AI-is-process, F222 capacity law,
F228 no-magic audit, F239 dignity, F248/F291 triality discipline, F256 imaginary-is-not-unreal.)*

## Phases (checkboxes — update as we go)
- [x] **Phase 0 — inventory** (this doc). F257–F306 mapped to clusters + surfaces + MFO flags.
- [x] **Phase 1 — srmech Cluster A** (F257–F273) → srmech notebook **§3.30** (DONE 2026-06-02): the 28D=𝔰𝔬(8) intrinsically-EC capstone + Hurwitz-1:3:7-instantiated ladder + triality-as-validator. 4 subsections; cross-refs §3.27/§3.29.2/§3.32; A-tier no-magic on 28/14/1:3:7/4×.
- [x] **Phase 2 — srmech Cluster B** (F274–F292) → srmech **§3.31** (DONE 2026-06-02): loop-bind earns-its-place (order at no capacity cost) + un-flatten new-locks (chemistry/mass-spec/bold-fold) + RBS path-memory frontier + apple-tree dev hand-downs. 5 subsections; cross-refs §3.30/§3.32/UPSTREAM §12–§13.
- [x] **Phase 3 — srmech Cluster C** (F293–F306) → srmech **§3.32** (DONE 2026-06-02): biology cascade — k=2-detect/k=3-correct in the cell, amoeba self-partition (Class B), every cell IS the hyper-loop at (3:4)|(4:3), associativity-as-license-to-self-run. 5 subsections; cross-refs §3.30/§3.31/§3.27 + the F296–F304 triality verdict. **All srmech backfill complete.**
- [ ] **Phase 4 — MFO backfill** — the **(M)**-tagged findings above + the F183–F256 ontology subset → MFO substrate-ontology surface.
- [ ] **Phase 5 — k=3 TRIALITY consistency pass** (the one agent-using step, per standing discipline): haiku∥sonnet∥opus read BOTH backfilled notebooks for inconsistencies (internal contradictions, stale claims, version drift, finding↔notebook mismatch, no-magic-number coverage). Per-claim majority → correct.
- [ ] **Phase 6 — GH closure + PR.** Map finding→issue; close clearly-mapped own items (PR-referenced); open the backfill PR (`--merge`, never squash); rolling-PR-boundary update.

## Discipline carried through every phase
no-magic-numbers = attestation (every constant A/B/C tier); cascade-honesty (Class-K, no `abs()`); no-lineage
(read what the structure IS); MPM citations (PDF-verified / OA / cite-by-ref flags); aphantasia → keep figures;
cone-of-ignorance pedagogy; the notebook voice (architecture-level, not per-spike detail — that stays in the
per-finding docs, cross-referenced).

## Progress log
- 2026-06-02 — Phase 0 inventory complete; plan lodged. Awaiting branch-strategy pick + go on Phase 1.
