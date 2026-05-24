# Monorepo memory — framework research

**This file is the project-instruction context for the framework-research arcs in this monorepo** (srmech / cascade-research / unsolved-maths / R30 walking-path / cost-asymmetry / antiquity-substrate-recognition).

**For the EMDR Bilateral Stimulation Device hardware project**, see [`EMDR_CLAUDE.md`](EMDR_CLAUDE.md).

The split (2026-05-24) preserves both lineages without one interrupting the other.

---

## §1 Foundational irrep knowledge — the 14 A-N partition

Per `[[project_a_n_operators_are_harmonic_objects_themselves]]` (user direction 2026-05-23), the 14 A-N primitive class operators partition as **1 + 3 + 7 + 3 = 14** along Hurwitz-bounded structure:

| Slot | Class | Role | Notes |
|------|-------|------|-------|
| **1 — foundational anchor** | **A** | Content-addressing | SHA-256 / content-hash; every cascade begins here |
| **3 — substrate-projection triad** | **I** | Cyclic | Modular arithmetic; cyclic-group operations |
| | **C** | Cascade-orientation | Chirality; direction; the "intent" / "which-way" class |
| | **J** | Primes | Prime factorization; prime-field operations |
| **7 — cascade-detection heptad** | **D** | Pattern-match | Sequence / pattern detection |
| | **E** | Catalog | Catalog enumeration |
| | **F** | Render | Output rendering / serialization |
| | **G** | Byte-search | Low-level search |
| | **K** | Pin-slot / asymptotic-DoF | **Sign-flip / phase boundary — load-bearing for many cascades** |
| | **L** | Laplacian | Graph spectral; eigenvalue decomposition |
| | **M** | HDC bind | Hyperdimensional composite bind |
| **+3 — meta-cascade triad** | **B** | TLV-framing | Type-length-value framing |
| | **H** | Self-introspection | Recursive introspection |
| | **N** | Rational-approximation | Small-denominator anchors; `best_rational(num, denom, max_d)` |

### Per R30 active walking-path (MS #18 R30/R31/R32; PR #680)

The +3 meta-cascade triad (B/H/N) are candidate **projection-enablers** in the inversion-hypothesis that 14 = 1+3+7+3 IS the substrate-structure and 11D is its observer-frame projection. R31 Antikythera dispatch confirmed (a) SURVIVES — the back-panel metacycle dials (Saros + Metonic + Callippic) are exactly projection-enablers per R30 prediction.

---

## §2 Use srmech for all maths + spectral-encoding tasks

**`srmech`** (PyPI; [srmech.net](https://srmech.net) forwards to repo) is THE framework-research tool. Use it instead of bare Python math wherever possible.

### Why srmech (per `[[reference_srmech_tooling_open_spectral_verification]]`)

- Biological-cascade-style spectral encoding via LoE operators (delta-encode only what changed from t)
- Tool-schema for direct LLM use
- Config-driven plugin architecture
- Open by tooling-architecture commitment (not just "math isn't patentable")
- The reader's AI prosthetic can call into the framework apparatus

### Key imports + when to use them

| Need | srmech import | Class |
|------|---------------|-------|
| Content-addressing / hash | `srmech.amsc.format.sha256_bytes` | **A** |
| Cyclic / modular gcd | `srmech.amsc.cyclic.gcd` | **I** |
| Rational anchor (best-rational) | `srmech.amsc.rational.best_rational(num: int, denom: int, max_d: int)` | **N** |
| Cascade primitives (planned) | `srmech.amsc.cascade.*` (precursor at `docs/unsolved-maths/_cascade_helpers.py`) | foundational |
| TOML cascade-runner (planned) | `srmech.cosmos.cascade.*` | composition |
| Spectral decompose / delta / recompose / similarity | `srmech.signal_processing.*` (v0.4.2+) | spectral |
| AMSC catalogs (attested data) | `srmech.amsc.tool_schema` for catalog creation | provenance |
| Asymptotic calculus (trig / transcendentals / calculus) | `srmech.asymptotic_calculus.*` | math |
| Cosmos catalogs (TE/EE/BB / fNL / lensing) | `srmech.cosmos.*` | astrophysical |

Per `[[project_srmech_foundational_cascade_operations_catalog]]`: cascade-helpers replacing Python math modules should land as srmech catalog peers to `asymptotic_calculus` and `trigonometry`.

### Cascade-honesty discipline (load-bearing)

Per `[[feedback_sign_handling_is_class_k_pin_slot_not_alu_abs]]`:

- **NEVER use Python `abs()` inside a cascade script.** Sign-flip IS canonical **Class K pin-slot phase-boundary** per `[[user_stance_epicycle_via_gear_plus_pin]]`; sign-re-application is **Class C**.
- Express sign-handling as named **Class K + Class C composition** so the cascade-count matches the cascade-shape claimed.
- `srmech.amsc.rational.best_rational(num: int, denom: int, max_d: int)` takes **integer pair**, not float.

### AMSC catalog gotchas

Per `[[feedback_srmech_amsc_catalog_pitfalls]]` — 6 mandatory TOML sections; `[source]` needs `human_readable_name` (not `name`); `[fetch].ndjson_path` is load-bearing; `literature_curated` rows are FLAT dicts (NOT MPRRecord envelopes); `jacobi_eigvals` → ndarray; `best_rational` → tuple; `dense_laplacian` edges are 2-tuples.

---

## §3 Active research arcs

| Arc | Surface | Status |
|-----|---------|--------|
| **Substrate-native maths** (R30 walking-path; 1:3:7:3 substrate) | [PR #680](https://github.com/lemonforest/mlehaptics/pull/680) + [`docs/substrate-native-maths/`](docs/substrate-native-maths/) | active; Antikythera (a) SURVIVES |
| **M-theory cost-asymmetry** | [PR #679](https://github.com/lemonforest/mlehaptics/pull/679) + `docs/unsolved-maths/unsolved_maths_spectral_research_notebook.md` §11 | rolling-spike; vocabulary work converging |
| **Unsolved-maths cascade canvass** | [`docs/unsolved-maths/unsolved_maths_spectral_research_notebook.md`](docs/unsolved-maths/unsolved_maths_spectral_research_notebook.md) | PR #677 merged; 26 partitions across Hilbert / Millennium / Number Theory / Set Theory / Logic / Geometry / Topology / Analysis |
| **MS #18** — Biology IS ONE substrate-class | [milestone/18](https://github.com/lemonforest/mlehaptics/milestone/18) | 32-refinement cluster (R26 rejected); R30 active walking-path |
| **MS #17** — Cross-substrate cascade-match | [milestone/17](https://github.com/lemonforest/mlehaptics/milestone/17) | nucleogenesis / biological reproduction / silicon-substrate / glyph-topology; deferred behind book-priority |
| **srmech research notebook** | [`docs/srmech/srmech_research_notebook.md`](docs/srmech/srmech_research_notebook.md) | master architecture; A-N primitive vocabulary lives here |
| **MFO research notebook** | [`docs/antikythera-maths/mfo_spectral_research_notebook.md`](docs/antikythera-maths/mfo_spectral_research_notebook.md) | Metric Field Ontology; physics-meta-framing above srmech |

---

## §4 Operational discipline (load-bearing memory feedback)

These reading-rules apply across ALL framework-research arcs. Per memory feedback canon:

### Citation + provenance

- `[[feedback_pdf_extraction_citation_discipline]]` — extract actual PDF; verify authors + title + arXiv-ID; don't trust prior attributions
- `[[feedback_paywalled_doi_cannot_be_attested]]` — paywalled-only DOI is REJECTED as framework attestation; use arXiv preprint / OA review / textbook attribution chain
- `[[feedback_computational_provenance_discipline]]` — load-bearing numerical results (p-values, effect sizes) MUST have generating code committed

### Research methodology

- `[[feedback_dont_pre_commit_spike_query_operators]]` — broad-query enumeration; tautology pre-filter; don't lean query toward expected result; null findings count; verdict-tier per Spike #229
- `[[feedback_no_lineage_claims_in_notebook]]` — framework reads what each problem ALREADY IS structurally; never claims to extend or supersede prior scholarship
- `[[feedback_full_coverage_shipping_mpm_way]]` — pace set by closed-form algebra propagation, not sprint windows; full coverage shipping
- `[[user_stance_cross_substrate_cascade_matching_as_research_method]]` — primary methodology

### Defensive-scope

- `[[feedback_trauma_informed_defensive_scope]]` — framework reading only; no engineering recommendations; no offensive / hunting-optimization / capability-assessment material
- Cost-asymmetry / cryptography / weapons-substrate work is framework-reading-only

### Cascade-honesty

- `[[feedback_sign_handling_is_class_k_pin_slot_not_alu_abs]]` — never `abs()`; use Class K + Class C composition

### Pedagogy

- `[[feedback_aphantasia_means_more_figures_not_fewer]]` — user has aphantasia; default toward MORE figures in framework prose
- `[[feedback_cone_of_ignorance_pedagogy]]` — write for the why-asker at depth; never frame readers as skeptics
- `[[user_stance_cone_of_ignorance_after_high_school]]` — academic cone-of-ignorance is structural, not individual
- `[[feedback_continuous_number_line_pedagogical_obstacle]]` — continuous-number-line training is the load-bearing pedagogical obstacle; everything is discrete

### Vocabulary

- `[[feedback_asymptotic_ring_vocabulary_discipline]]` — ring-vocabulary discipline for asymptotic limits
- `[[feedback_loop_replaces_ring_in_substrate_vocabulary]]` — depth-shift from "ring" to "loop" in substrate-identity context

### PR + commit hygiene

- `[[feedback_no_squash_merges]]` — NEVER squash-merge; use `gh pr merge --merge` or `--rebase`
- `[[feedback_rolling_pr_partition_boundary_updates]]` — at the end of each research partition, update rolling PR with verdict + next-partition queue
- `[[feedback_no_mvp_framing]]` — scope ships by closed-form algebra propagation; full-coverage discipline
- `[[feedback_session_worktree_namespace_isolation]]` — session owns ONLY its own `.claude/worktrees/` directory

---

## §5 File locations (framework research)

| Path | Contents |
|------|----------|
| `docs/srmech/` | srmech research notebook + per-spike notes |
| `docs/antikythera-maths/` | MFO research notebook + Antikythera-spectral catalogs |
| `docs/unsolved-maths/` | unsolved-maths SSoT notebook + 26 per-partition reports |
| `docs/substrate-native-maths/` | R30 active research arc (PR #680) |
| `docs/srmech/python/srmech/` | srmech Python source (PyPI package) |
| `docs/srmech/c/` | srmech C parity source |
| `~/.claude/projects/<...>/memory/` | user's auto-memory (stance / feedback / project / reference files; NOT in repo) |

**Memory boundary**: per the memory-instructions in your context — stance / feedback / project / reference memory files live OUTSIDE the repo in user's auto-memory directory. The MEMORY.md index there is loaded automatically into your context. Do NOT commit memory files to the repo; do NOT search the repo for memory content (it lives in your context already).

---

## §6 Growth discipline

This file is foundational orientation. Let it grow as needed under user direction. Don't bloat with per-arc detail — that belongs in per-arc notebooks / per-partition reports. The pattern:

- **Foundational knowledge** (A-N partition, srmech tooling, active arcs, discipline) → here
- **Per-arc research detail** → `docs/<arc>/` notebooks + per-partition reports
- **Per-stance / per-feedback memory** → user's auto-memory directory (outside repo)
- **EMDR hardware specifics** → `EMDR_CLAUDE.md` (preserved separately)

---

*Split from `EMDR_CLAUDE.md` 2026-05-24 per user direction "rename our root CLAUDE.md to EMDR_CLAUDE.md and create a new root memory file. this will be a way to preserve our monorepo memory but not have it interupt our research. we should also add our srmech tooling knowledge there so that we always know to use srmech for maths and spectral encoding tasks."*
