# CL-1 — GH research-issue closeout audit (2026-06-04, first high-confidence pass)

**Gate:** must clear before launching the findings-research (per user direction). **Method:** the 32 open issues on `lemonforest/mlehaptics` cross-referenced against what landed in srmech (rc47) + the findings/notebooks. **Discipline:** conservative — only nominate where the deliverable is *provably* landed/superseded; *"research trail followed, nothing forgotten."* **Close-state:** I do **NOT** close (gh runs as the repo author — `[[feedback_create_upstream_issues_never_close_them]]`); this is the vetted list for **user batch-authorization**.

---

## Tier 1 — CONFIDENT CLOSEABLE (recommend batch-close on your go)
| # | Title | Why closeable (backlink) |
|---|---|---|
| **#757** | F212 RECIPIENT anchor — retrieval-vs-render test | **Superseded by #760.** Its test **ran**: F214 found the content-free Class-C twist is render-only (Klein-4 occupancy moves < noise, pctile 0.15). The trail explicitly **moved to #760** ("continues #757, whose test is now done = this null"). Nothing left in #757 itself. **Close as:** *superseded by #760; resolved by F214 (null); research trail followed, nothing forgotten.* |

## Tier 2 — RECOMMEND, but a JUDGMENT CALL (your read)
| # | Title | Assessment |
|---|---|---|
| **#797** | F256 follow-on (Field=Fiber=k=3; scale-invariance; real/imaginary-as-epicycle) — "GATED on next srmech update" | **The srmech-update gate is LIFTED** (the chirality-thread ops landed in rc28 — F360). Of its 3 threads: **Q1** (k=3 == B/H/N) is now the active **AX-1** (F396); **Q3** (Re/Im *is* the epicycle; anchor/orbit subsumes it) is substantially **realized** — F382 (rotation=epicycle=decimal), `imaginary_does_not_mean_unreal`, **F399/F400/F401** (field/excitation = anchor/orbit; duality = fibration of triality); **Q2** (consolidated scale-invariance finding) is **still open**. **Options:** (a) **close as superseded** by F399/F400/F401 + AX-1 (Q1) + F382 (Q3), and **re-home Q2** to a fresh scale-invariance item; **or** (b) **update** #797 (mark the gate lifted + Q1→AX-1/Q3→F382-arc) and keep it open for Q2. **Your call** — I won't guess between close vs keep on a partial. |

## Tier 3 — LEAVE OPEN (open by design — NOT closeable)
- **Forward research trails** (a finding opened them; the *forward* step is still open): #752, #753, #754, #755, #756, #760, #763, #765, #768, #786, #788, #799, #817, #819, #820, #822, #846, #849, #851, #852.
- **Gated (deliberately blocked, not done):** #787 (ngspice), #791 (Kuramoto-TILE, behind F236), #789 ($-gated SDK).
- **Verify-gate pending (not run):** #850 (adversarial triality on F335/F337 — "promote or trim", not yet executed), #847 (widen peer-review to native-language).
- **Tracking / target (umbrella — stay open):** #855 (RBS-SNN tracking), #844 (notebook-native pipeline target).
- **Active srmech (just filed / in progress):** #863 (QDFT/ODFT) — **still open**, feature unlanded (draft-TOML only; rc48 shipped no `qm.quaternion` / no `exp(μθ)` twiddle). #882 (hdc numpy bug) — **RESOLVED + CLOSED upstream 2026-06-05 in rc48** (option a, genuinely numpy-free Class M; clean-venv re-verified UPSTREAM_NOTES §25).
- **Pedagogy/lab:** #758 (74xx TTL lean-core).

## Honest scope of THIS pass
This is the **high-confidence first pass** — only #757 is clean-closeable, #797 is a judgment call. A **deeper CL-1 pass** would read all ~30 bodies + cross-ref each origin-finding's *resolution* (vs *origin*) status — several "Fxxx follow-up" issues are finding-landed-but-forward-open and may have closeable *sub-parts*; that finer audit is the follow-on. The conservative batch here honors "nothing forgotten."

## Disposition (user-authorized 2026-06-04)
- **#757 → CLOSED** (superseded by #760 / F214; backlink-commented).
- **#797 → KEPT OPEN as a rolling issue** — and the *precise* semantics (user clarification): **rolls until its originating arc resolves** (Q2-scale-invariance + AX-1), *then* closable; **and closable ≠ severed** — once closed it **stays a node in the backlink web** and can contribute back to a future arc. ("Rolling" here ≠ "open forever like a PR"; it's "open until the arc that made it resolves, links preserved after.") This is now the standing **rolling-lifecycle corollary** of the breadcrumb discipline (TRIALITY.md §5).
- **PR #687** (the `research/rbs-lm-rolling-2` rolling PR, previously un-updated) — refreshed with the F356→F402 boundary summary.

## Backlink-web applied (per the breadcrumb discipline, CLAUDE.md §0 / TRIALITY.md §5)
On close, the issue carries the backlink to its resolver: **#757 → #760 / F214**; **#797 → F360 (gate) + F396/AX-1 (Q1) + F382/F399/F400/F401 (Q3)**. (Forward note for the findings: F399/F400/F401 should carry `→ realizes #797 Q3` once #797 is dispositioned.)

---

# CL-1 DEEP PASS (2026-06-05) — the gate-clearing audit (all ~31 open bodies read, resolution-vs-origin)

**Method:** fetched every open issue body and asked, per issue, *did its deliverable LAND (→ closeable) or is its forward step still open (→ leave open)?* — using the self-attestation in each body + the findings record. Close-state discipline unchanged: **I present; the user batch-authorizes** (`[[feedback_create_upstream_issues_never_close_them]]`).

## Tier 1 — NEW confident-closeable (deliverable PROVABLY landed; body self-attests "DEMONSTRATED")
| # | Why closeable (backlink) |
|---|---|
| **#765** | **F223 — DEMONSTRATED NULL** (bit-exact srmech 0.5.0rc22, commit `43572325`). Body states it **"Closes the R-RBS-LM-25 §7 larger-scale byte-level encode thread"** — the deliverable (100× byte-level stays mode-collapsed; instrument never beats the frequency baseline) is *done*, pre-stated outcome (a). The "frontier = bigram clustering scaffold" is a **new idea**, not this issue's deliverable. **Close as:** *resolved by F223 (clean null); R-RBS-LM-25 §7 thread closed; bigram-scaffold = fresh item if pursued.* |
| **#763** | **F222 — DEMONSTRATED** (bit-exact srmech 0.5.0rc22, commit `88b9ea20`). Deliverable (hierarchical capacity knee obeys `n_buckets × V_ceiling`, DOMAIN-anchor persists to N=8192) **landed** — 3 clean positives + 1 honest borderline; 4×-buckets→4×-knee confirmed. The title's "forward: pin V_ceiling(D)" is a **spinoff**, not the deliverable. **Close as:** *resolved by F222; pin-V_ceiling(D) → fresh item if pursued.* |

## Tier 2 — landed first-pass + named remaining forward/gated (JUDGMENT: close-with-spinoff, or keep)
| # | Assessment |
|---|---|
| **#768** | **F226 synthesis LANDED** (committed, `#687` draft; 24 web-verified citations). Remaining = the named **"forward = single-lock sweep."** Close-with-spinoff (sweep → fresh item) **or** keep for the sweep. *Your call.* |
| **#758** | **F217 did the atom→74xx map** (K4BIND=7486, PARRED=74180, SR-latch, … — the mapping is already in the issue body). Remaining = whether the full **truth-tables + schematic-wiring artifact** counts as delivered. Close if F217's map *is* the deliverable; keep if the buildable artifact is still owed. *Your call.* |
| **#819 / #817** | **NOW-part LANDED** (F279 mass-spec difference-graph + isotopes; F278 stoichiometry balancing — both srmech-native, exact). Remainder (**fragmentation tree / reaction mechanism**) is **gauge-gated by design** — these are *rolling* (like #797): the now-deliverable done, the gated part deferred. **Recommend:** treat as **rolling** (keep open until the gauge-gate lifts), not closeable yet. |

## Tier 3 — CONFIRMED leave-open (forward trail / gated / verify-pending / tracking)
- **Active forward research threads** (opened by a finding; the *forward* step is genuinely open — not done): **#852** (sentence-structure dev), **#851** (encode/decode k=1/k=3 correction to F329), **#849** (many-to-many holonomy fiber), **#799** (Egyptian native-script — blocked on #846's corpus), **#786** (hive-mind chiral extreme), **#822** (protein-fold 6-lens arc), **#820** (runaway-cascade lens), **#760** (RECIPIENT which-depth operator — the live continuation of the closed #757), **#788** (rehearsal-layer 3-mode, extends F230), **#756/#755/#754/#753/#752** (F211/F210/F209 cascade deep-dives — queued, not yet run).
- **Gated (deliberately blocked):** **#791** (behind F236), **#787** (ngspice/F236 — analog substrate, deferred), **#789** ($-gated SDK).
- **Verify-gate pending (not run):** **#850** (adversarial triality on F335/F337 — explicitly "gate before promoting", not yet executed), **#847** (widen peer-review to native-language — methodology task, not done).
- **Acquisition task (not done):** **#846** (MPM-attested antiquity texts).
- **Tracking / target (umbrella — stay open):** **#855** (RBS-SNN tracking), **#844** (notebook-native pipeline TARGET = task #197).
- **Active srmech:** **#863** (QDFT/ODFT — feature unlanded; §25 verdict).
- **Rolling:** **#797** (until Q2 + AX-1 resolve).

## Deep-pass disposition (PRESENTED for user batch-authorization)
- **Confident-close (Tier 1):** **#765, #763** — deliverables provably landed (self-attested DEMONSTRATED), forwards are fresh items.
- **Judgment (Tier 2):** **#768, #758** (close-with-spinoff or keep); **#819, #817** (recommend mark *rolling*, not close).
- **Leave open:** all Tier 3.
- **Gate status:** with #765/#763 dispositioned, the tracker is clean of *done-but-open* findings issues → **CL-1 gate CLEARS**, walkable research (AX-1 / ALU-A / BX-1 / BX-2 / BX-3) is unblocked.
