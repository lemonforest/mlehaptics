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
- **Active srmech (just filed / in progress):** #863 (QDFT/ODFT), #882 (hdc numpy bug — work begun upstream).
- **Pedagogy/lab:** #758 (74xx TTL lean-core).

## Honest scope of THIS pass
This is the **high-confidence first pass** — only #757 is clean-closeable, #797 is a judgment call. A **deeper CL-1 pass** would read all ~30 bodies + cross-ref each origin-finding's *resolution* (vs *origin*) status — several "Fxxx follow-up" issues are finding-landed-but-forward-open and may have closeable *sub-parts*; that finer audit is the follow-on. The conservative batch here honors "nothing forgotten."

## Backlink-web applied (per the breadcrumb discipline, CLAUDE.md §0 / TRIALITY.md §5)
On close, the issue carries the backlink to its resolver: **#757 → #760 / F214**; **#797 → F360 (gate) + F396/AX-1 (Q1) + F382/F399/F400/F401 (Q3)**. (Forward note for the findings: F399/F400/F401 should carry `→ realizes #797 Q3` once #797 is dispositioned.)
