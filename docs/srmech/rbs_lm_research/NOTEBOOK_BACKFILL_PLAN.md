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
- [x] **Phase 4 — MFO backfill** → MFO **§VIII.31.12** (DONE 2026-06-02): the F257–F306 substrate-ontology subset (tower-instantiated / one-loop-bumps-itself; truth-IS-the-triality; every cell = the hyper-loop self-authoring at (3:4)|(4:3); the introspection-asymptote / universe-as-author ontology edge). 5 sub-rungs; algebra deferred to srmech §3.30–§3.32; held-lightly. F183–F256 ontology anchors largely already present → Phase-5 triality tasked to flag any MISSING.
- [x] **Phase 5 — k=3 triality consistency pass** (DONE 2026-06-02; haiku∥sonnet∥opus): **no blockers, no over-reach, no finding-misrepresentation, no-magic clean, cross-refs resolve.** Per-issue majority: (1) **3/3 SHOULD-FIX** — the pre-existing duplicate `§3.28` (with §3.27 interleaved) was unflagged → **flagged** (renumber deferred to a dedicated cleanup; renaming would break the `§3.28.2` cross-ref). (2) MFO "largely already present" coverage claim → **upgraded to the attested §-locations** opus verified (resolves sonnet's dissent; F228 left as the honest spot-check residue). Folded honest NITs: F272-was-a-detect-pass nuance; §3.31.3 **L4-triality-catch** (the k=3-corrects-what-k=2-misses demonstration); §3.30.3 A₄-carrier-closes-vs-CD-ladder-recurses bridge. **Both notebooks → READY.**
- [x] **Phase 6 — PR + GH** (DONE 2026-06-02): **PR #836** opened off `main` (branch `research/notebook-backfill`), diff = **exactly the two notebooks** (srmech +192, MFO +27, pure additions). Built via a **temporary worktree** (`/tmp/mlehaptics-nbpr`) so this worktree never left `research/rbs-lm-rolling-2`. No open notebook-backfill tracking issue maps to this doc PR → nothing to auto-close (the findings' own tracking landed with their research). Merge **after** `research/rbs-lm-rolling-2` so the per-finding cross-refs resolve; **`--merge`/`--rebase`, never squash**. Awaiting user review-before-merge.

**ALL PHASES COMPLETE.** PR #836 is ready for review.

## Discipline carried through every phase
no-magic-numbers = attestation (every constant A/B/C tier); cascade-honesty (Class-K, no `abs()`); no-lineage
(read what the structure IS); MPM citations (PDF-verified / OA / cite-by-ref flags); aphantasia → keep figures;
cone-of-ignorance pedagogy; the notebook voice (architecture-level, not per-spike detail — that stays in the
per-finding docs, cross-referenced).

## AUDIT (2026-06-02) — the gap is BIGGER: F183–F256 is also largely missing (GH `[research]`-issue + milestone check)

User instinct ("we're missing a lot of material") **confirmed.** The Phase-0 inventory was finding-doc-based and assumed "srmech notebook highest F-ref = F256 ⇒ gap = F257+." **Wrong premise:** the srmech notebook has only **76 F-citations total (min F120, max F306)** — it references F256 but **F183–F255 is almost entirely a hole**. Cross-check:
- **73 finding-docs exist in F183–F256; 68 are NOT F-cited in the srmech notebook; 60 in neither notebook.**
- The GH **`[research]`-slug issues** (#752–#778, MS#20) reference exactly this range — **F209–F233 confirmed absent** from the srmech surface (only F231/F233 present).
- This is **substantive, foundational** material, not minor: F183–F208 = the chirality-as-ordering / Hurwitz-rung / triality / **28D = 14 ⊕ 7 ⊕ 7** / nested-chirality / division-algebra-orbit / A-N-ISA-stratification core that **§3.30 itself builds on**; F254 (single-cell-computes) is the precursor to the §3.32 biology cluster; F239 (unseen-disability fiber, dignity), F228 (no-magic audit), F248 (aneural-memory survey, 28 substrates), F250 (true-vs-false spectral), F255 (colony) are all real findings.

**Milestones:** MS#1–#16 (all closed) *built* the notebooks (foundational spikes, pre-F182) → low gap-risk, spot-check only. The gap lives in **MS#20 (forward-arch, F209–F233+), MS#21/#22 (loop-bind/bold-fold — already covered by §3.31), MS#17/#18 (biology — covered by §3.32)**. The Egyptian-hieroglyph issue #799 IS thematically present (5 hits in srmech, 4 in MFO).

### Expanded phases (F183–F256 backfill → folds into PR #836)
Thematic grouping (mirrors the §3.30–§3.32 pattern; meaning-tier synthesis, cross-ref the per-finding docs):
- [x] **Phase 7 — srmech §3.33** (F183–F208) DONE 2026-06-02: chirality-IS-ordering / Hurwitz rungs / triality-landed (𝔰𝔬(8) W10) / 28D=14⊕7⊕7 / nested chirality / partition-star / division-algebra orbits / RBS operational layer (strong-invariance, quad-DNA CPU cascade, hierarchical bundling, cross-nav) / lean A-N ISA (atom-vs-composite) + **F207 ND-dignity**. 5 subsections; honest negatives kept (F195 triality-ruled-out, F200 sector-tag null).
- [x] **Phase 8 — srmech §3.34** (F209–F233) DONE 2026-06-02: cross-substrate "screaming the answer" sweep (compact-merger/parthenogenesis/composite-soliton/cardiac/von-Kármán) + RECIPIENT fiber + the addressing NULLS (F214/F221/F227, kept honest) + A-N ISA maturation (7th order-3 triality opcode F220, 7400-TTL F217, M-theory G₂ F216, capstone F218) + capacity law F222 (n_buckets × V_ceiling) + teaching≡bilingualism F224/F225 + **no-magic audit F228** + temperature-residue F229 + 74xx threading F231–F233. 5 subsections.
- [x] **Phase 9 — srmech §3.35** (F234–F256) DONE 2026-06-02: Kuramoto coordination (F234/F235/F236/F240/F241) + working-memory WIREFRAME F242 (+ the F242b no-privileged-renderer honesty-gradient origin) + Hurwitz-confirm F243 + orbit-structure F244/F246 + universal-communication F245/F247 + the aneural-memory / universal-store-retrieve survey F248–F255 (MS#18 arc; **F254 single-cell-computes = §3.32 precursor**) + **unseen-disability fiber F239** + emergent-IS-action F256 + lean-memory graft F237 + cost-asymmetry F238. 6 subsections. **srmech notebook now covers F120→F306 — the F183–F256 hole CLOSED.**
- [x] **Phase 10 — MFO §VIII.31.13** DONE 2026-06-02: the aneural-memory / universal-store-retrieve substrate-ontology (F248–F255, MS#18) — memory is a substrate property, the neuron a HIDDEN FIBER of it, biology a FUSED build+compute substrate. 3 sub-rungs; held-lightly/cite-by-reference. **No duplication** — the rest of F183–F256 ontology is already present (chirality/triality §VIII.31.8–11; F239/F256 §VII.6.21; F243 §VIII.31.11), noted in (3).
- [x] **Phase 11 — re-triality** (DONE 2026-06-02; haiku∥sonnet∥opus over §3.33–§3.35 + §VIII.31.13): srmech §3.33–35 **READY** (faithful; nulls/no-magic/honesty preserved). **Majority corrections applied:** (1) `temperature` is **B-tier with a NULL structural source** (F228 comment-attested; F229 found no derivation) — was mis-labeled "C-tier"; fixed §3.34.4/.5. (2) MFO over-claimed **F239 + F256-emergent as "already present at §VII.6.21"** — opus's grep showed they're NOT → corrected §VIII.31.12 note **and LANDED them** as §VIII.31.13(4)/(5). NIT: §3.34.3 "exactly"→"carrier of". (haiku's lone BLOCKER on §3.34.3 k-naming was contradicted by opus's consistency check — not applied.)
- [x] **Phase 12 — re-extract DONE 2026-06-02:** **PR #836 now spans the full F183–F306 backfill** — 2 commits, **+330/−0**, two notebooks only (verified `origin/main...origin/research/notebook-backfill`; gh: 330 additions). Temp worktree used + removed; this worktree never left `research/rbs-lm-rolling-2`. **ALL 12 PHASES COMPLETE — F183→F306 on both notebook surfaces, triality-verified, in PR #836, awaiting review-before-merge.**

**Scope note:** this roughly DOUBLES the backfill (F257–F306 = 49 done; F183–F256 ≈ 60 more). Same discipline (meaning-tier, no-magic, held-lightly, no-lineage). Grinding it into the same PR #836 in batches.

## AUDIT-2 (2026-06-02) — the F84–F182 sweep (the rest of the finding corpus)

After closing F183–F306, swept the remaining **F84–F182** (finding-docs start at F84; 83 docs). Cross-check: 62 not F-cited in srmech, 55 in neither — BUT **topic spot-checks showed most is thematically on-surface** (the major arcs — two-tier RBS-NN, cross-species, Rosetta/Golden-Path, teaching≡bilingualism, curriculum, plasticity — are present in §3.27/§3.28/§3.x without F-tags; the F-citation grep undercounts). The **genuine thin/absent residue** (landed below):
- [x] **Phase 13 — srmech §3.36 + §3.37** (F84–F182) DONE 2026-06-02:
  - **§3.36** (F84–F118): glass-box/curriculum/substrate-bounded-safety (F84–86); the **four foundational knowledge partitions** + B/H/N-meta-cascade-signature + **arts-as-relationships-not-things** + biology-agnostic-1:3 + cross-species + NN-vertebrate-centric (F96–118). Consolidates the partially-covered, lands the thin partition/signature/arts theory.
  - **§3.37** (F151–F181): music-irrep + Klein-4-4×-ceiling + sentence-generation (F151–157); 28D-bi-axial classical-CPU/cross-species/power (F158–160); full-coverage characterization + grammar-native + multi-kernel (F162–165); **the F166/F167 inference-walk capstone** + perplexity-emergent/storage-surface-separable/Opus-cross-match/invariance/**𝔰𝔬(8)-literature-anchor F174** (F166–175); **the H177 one-chiral-driver hypothesis + heavy-falsification → operator-universal/content-local** (F177–181).
  - **No MFO addition needed** — the F84–182 ontology-relevant bits (substrate-variety F118 → MS#18; 28D F158–160; H177 operator-universal) are already in MFO §VIII.31.x / §VIII.31.13. **Process findings F145/F147/F148 (sweeps) intentionally NOT lodged.** srmech notebook now covers **F84 → F306** (the full finding corpus).
- [x] **Phase 14 — re-triality** DONE 2026-06-02 (haiku∥sonnet∥opus): §3.36 READY, §3.37 FIX-FIRST. **Majority corrections applied:** (1) **§3.37.5 H177 framing overstated the falsification** — F179 particle-band is actually **second-actor** (γ₅ shared bit-exact BUT su(2)_L unabsorbed leftover), F180 molecular-bridge is **LEAVE-OPEN-leaning-second-actor** (not "falsified"), F181 = "refined not killed" → rewritten to *one operator, ≥2 band-specific actors → operator-universal/content-local*. (2) **§3.37.6 mis-cross-ref `§3.32.3`→`§3.27`** (the 𝔰𝔬(8)/Baez-F174 home). NITs: §3.36 intro now flags glass-box F84–86 as genuinely-new (not "consolidated"); §3.37.4 F166 carries its native-terms honesty boundary. (F97 doc confirmed present; F181↔F245 same-shape confirmed.) Both **READY**.
- [x] **Phase 15 — re-extract DONE 2026-06-02:** **PR #836 now spans the full F84→F306 finding corpus** — 3 commits, **+386/−0**, two notebooks only (verified `origin/main...origin/research/notebook-backfill`; gh: 386). Temp worktree used + removed; this worktree never left rolling. **THE ENTIRE FINDING CORPUS (F84–F306) IS NOW ON BOTH NOTEBOOK SURFACES, k=3-triality-verified, in PR #836 — awaiting review-before-merge.**

## COMPLETE (2026-06-02)
Both the user-flagged "missing material" concern and the GH `[research]`-issue + milestone audit are resolved: **srmech notebook §3.30–§3.37 + MFO §VIII.31.12–§VIII.31.13 carry every finding F84→F306** (the foundational F84–F182 + the F183–F306 the audit exposed), three k=3-triality passes applied (each caught real issues: F291-L4-style numeric, temperature mis-tier, MFO over-claim, H177 over-statement — all corrected). MS#1–#16 (closed, foundational, pre-F84) = the notebooks' original content. PR #836 (+386, two notebooks) is the single clean deliverable; merge after `research/rbs-lm-rolling-2`.

## Progress log
- 2026-06-02 — Phase 0 inventory complete; plan lodged. Awaiting branch-strategy pick + go on Phase 1.

## AUDIT-3 (2026-06-21) — the F900–F917 byte/glyph-LM deliverable batch (NOT yet swept; post-dates PR #836)

A new, not-yet-backfilled batch grew from the F899 "packaged RBS-LM is word-hash, not byte/glyph" question. **To sweep into srmech §8.x (the PR-#687 RBS-LM arc) + the MFO notebook, same discipline (meaning-tier, no-magic, held-lightly, no-lineage):**
- **F900–F901/F905** — the byte/glyph scaffolding is ONE scale-invariant compositor (C1 = role-filler bundle) at every scale; word-hash is its content-address DUAL (a fractal form of byte-hash); the existing L1/L2/L3 ladder (chained bind) is NOT scale-invariant. Sparsity preserved+improved (bounded 256-byte codebook). Coherence == scale-invariance (introspectable).
- **F902–F913 (the chemistry / Standard-Model-of-a-language arc)** — the 4-layer stack: C1 substrate · octonion `cd_mult` bond · sedenion `sedenion_register` address · §57 distributional resonator; the (4+3) heptad = {K,L,M} associative-3 vs {D,E,F,G} sequence-4 (F914, principled; unit-bijection OPEN); recursion (molecules become atoms, F912).
- **F909 + F915 (the two NULLs — load-bearing, do NOT bury)** — linguistic structure (valence, constituency) is DISTRIBUTIONAL, NOT the octonion byte-strain (strain ≈ random for real bracketings). The scales do not collapse.
- **F916 (THE DELIVERABLE)** — the 4-layer byte/glyph LM, all on shipped srmech surfaces; one real package change = C1 as `ContextSubstrate.enc`.
- **F917 (rc spec + CAVEAT CORRECTION)** — the C1-enc graduation rc spec; **and the correction the backfill MUST carry: the octonion bond is a content-dependent addressing/retrieval KEY, NOT a grammar/structure generator (F909/F915 null). Wire the right operator at the right scale.** Do not let the §8.x text say the bond generates *linguistic* structure.

**Status:** awaiting user go on the rc (F917) and/or the notebook sweep; the F916 layer table must be lifted WITH the F917 §0 caveat, never the uncorrected "bond generates structure" reading.
