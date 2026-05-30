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

### Class O dissolution note (vocabulary discipline; 2026-05-16)

**Class O is NOT a separate class.** The signed-metric / Wick-rotation operation initially located by Spike #24 bonus 8 was dissolved into **Class L as a signed-Laplacian-variant sub-operation** per `[[feedback_no_privileged_primitive_classes]]`. Vocabulary stays at **14 classes A–N** (no Class O). Future Class L rcs will add the signed-Laplacian op when Phase C2 cascade-composition work calls for it.

---

## §2 Use srmech for all maths + spectral-encoding tasks

**`srmech`** = **Stored-Relationship Mechanism**. PyPI; [srmech.net](https://srmech.net) forwards to repo. THE framework-research tool — use it instead of bare Python math wherever possible. Current release v0.4.0 ships full **14-class C-parity primitive vocabulary** (A-N) + canonical **QM/QFT/SM operations layer** at `srmech.qm.*` (single_particle / spin / potentials / relativistic / propagators / pseudo_hermitian / gauge / sm).

### srmech-first reflex-override — the remembering mechanism (load-bearing; read at code-writing time)

**Why this exists:** Python/numpy idioms carry enormous prior weight; a declarative "use srmech" loses to that reflex at code-writing speed (it happened — n-gram `Counter()` storage proxies in R-131/132/133 slipped past, corrected to Class-L spectral in R-134). So this is a **point-of-action STOP-list, not a principle.** Before writing ANY of these Python idioms in a script, STOP — it is a srmech primitive:

| If your hand reaches for… | STOP — use this srmech op instead | Class |
|---|---|---|
| `Counter()` for co-occurrence / adjacency / graph edges | build edges → `srmech.amsc.laplacian.dense_laplacian` | L |
| `np.linalg.eig/eigh/svd`, eigenvalues, spectra | `srmech.amsc.laplacian.jacobi_eigvals` / `hermitian_eigendecompose` / `symmetric_eigendecompose` | L |
| hand-rolled cosine / hamming / similarity / `softmax` over vectors | `srmech.amsc.hdc.{similarity, klein4_similarity}`, `srmech.spectral.similarity` | M |
| hand-rolled n-gram / resolution-depth "storage" proxy | the co-occurrence **Laplacian eigenspectrum** is the srmech-native storage signature (F172) | L |
| bind / bundle / permute / superpose vectors | `srmech.amsc.hdc.{bind,bundle,permute,klein4_bind,klein4_bundle}` | M |
| `hashlib.sha256(...)` | `srmech.amsc.format.sha256_bytes` | A |
| chirality / γ₅ / iω₇ / sector flips | `srmech.amsc.hdc.{klein4_chirality_flip_gamma5,klein4_chirality_flip_omega7,klein4_cpt_mirror}` | — |
| modular arithmetic / gcd / primes / rational-approx | `srmech.amsc.{cyclic,primes,rational}` | I/J/N |

**package vs srmech-mcp:** the srmech **package** (`import srmech.amsc...`, C-native) is the right tool for **bulk in-script** work (graph-building, eigendecomp over many tokens). The **srmech-mcp** tools (deferred `mcp__srmech__*`, load via ToolSearch) are right for **single / interactive / agent-driven** ops and for exercising the attested surface — NOT for per-token loops (JSON-array payloads, no handles). Using the package IS using srmech; hand-rolling a primitive that has a srmech op is the failure. When srmech-mcp itself has a bug/gap, log it (UPSTREAM_NOTES §10) — don't route around it silently in a way that hides the issue.

**The reliable trigger (user-supplied 2026-05-29):** framing work in **28D / chirality / Klein-4 / Class-L-spectral** terms IS itself the forcing-function — those ops have NO Python-native idiom to hijack the reflex (`Counter()` hijacks "co-occurrence"; *nothing* hijacks "the γ₅-odd chirality coordinate" or "the Klein-4 sector occupancy"), so 28D-framing routes straight to srmech. When the user raises 28D math, that is the cue to reach for srmech first.

**Honest limitation:** this STOP-list reduces but does not eliminate the Python-reflex miss; the user spot-check ("are we using python stuffs?") is part of the loop, and catching it is normal, not failure.

### AMSC framework + MPM discipline (load-bearing across all spectral-research arcs)

srmech is the home of the **AMSC** (Attested Multi-Source Collector/Catalog) framework. Every ground-proof datum srmech ships carries a mandatory **attestation block** — this IS the on-disk crystallisation of the **Mathematical Provenance Method (MPM)**. The discipline is the project's primary defense against LLM-side citation hallucination.

**MPR v1** (Mathematical Provenance Record) format — implemented in `srmech.amsc.format`:

```python
{
  "mpr_version": "1.0",
  "data": { ... domain payload ... },
  "data_schema_id": "test://schema/example",
  "attestation": {
    "source_doi": "10.0/...",
    "source_url": "https://...",
    "license": "CC0",
    "retrieved_at": "2026-05-13T00:00:00Z",
    "response_sha256": "<64 hex chars>",
    "parser_version": "srmech 0.4.0",
    "parser_rule_hash": "<64 hex chars>",
    "collector_descriptor_path": "...",
    "collector_descriptor_hash": "<64 hex chars>"
  },
  "rendering": { "name": "...", "purpose": "...", "cite_as": "..." }
}
```

A citation without attestation is not real; an attestation that can't be re-verified is broken. When adding a paper reference, **extract the actual PDF and verify authors + title + arXiv ID** over trusting training-data attribution. Composes with `[[feedback_pdf_extraction_citation_discipline]]` + `[[feedback_paywalled_doi_cannot_be_attested]]` in §4 below.

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
| TOML cascade-runner (planned) | `srmech.cosmos.cascade.*` *(planned; `srmech.cosmos` is not yet a module — F178)* | composition |
| Spectral decompose / delta / recompose / similarity | `srmech.signal_processing.*` (v0.4.2+) | spectral |
| AMSC catalogs (attested data) | `srmech.amsc.tool_schema` for catalog creation | provenance |
| Asymptotic calculus (trig / transcendentals / calculus) | `srmech.asymptotic_calculus.*` | math |
| Cosmos catalogs (CMB TE/EE/BB; **no EB/TB** parity surface) | `srmech.amsc.attested.cmb_*` | astrophysical |

Per `[[project_srmech_foundational_cascade_operations_catalog]]`: cascade-helpers replacing Python math modules should land as srmech catalog peers to `asymptotic_calculus` and `trigonometry`.

### Cascade-honesty discipline (load-bearing)

Per `[[feedback_sign_handling_is_class_k_pin_slot_not_alu_abs]]`:

- **NEVER use Python `abs()` inside a cascade script.** Sign-flip IS canonical **Class K pin-slot phase-boundary** per `[[user_stance_epicycle_via_gear_plus_pin]]`; sign-re-application is **Class C**.
- **As of srmech rc22+ these ship NATIVELY in `srmech.amsc.cascade.*` — prefer them over any hand-rolled fold:** `cascade.magnitude` (the modulus; replaces the hand-written `(re**2+im**2)**0.5`), `cascade.pin_slot_at_zero` (Class K), `cascade.reorient` / `cascade.chiral_flip` / `cascade.chiral_dual` / `cascade.net_chirality` (Class C), `cascade.best_rational_signed` (K+N), `cascade.cyclic_gcd` (I). The discipline-ratchet (`docs/srmech/rbs_lm_research/check_srmech_discipline.py`) now points `abs()` at `cascade.magnitude`.
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

### Sister-package portfolio (spectral-research family — all share MPM discipline)

srmech is one node in a portfolio of spectral-research Python packages + notebooks. Each applies the same MPM discipline to a different domain object:

| Subtree | Notebook | What it studies |
|---------|----------|-----------------|
| `docs/srmech/` | srmech_research_notebook | **Stored-Relationship Mechanism** — unifying framework; relationships stored in cyclic-group / spectral representations |
| `docs/antikythera-maths/` | antikythera_spectral_research_notebook | Antikythera bronze gear-DAG; cyclic-group algebra; Almagest / Freeth parameter sets |
| `docs/antikythera-maths/` | ephemerides_spectral_research_notebook | Sol star system; 52-body roster; geodetic / magnetic / fluid / dynamical catalogs; JPL DE441 anchor. **srmech depends on this** (consumes AMSC) |
| `docs/antikythera-maths/` | mfo_spectral_research_notebook | **Metric Field Ontology** — substrate-vs-excitation framing; foundational ontology layer (sister to all the others) |
| `docs/antikythera-maths/` | doom_spectral_research_notebook | DOOM as spectral lattice system — map encoding / level topology / gameplay-system spectral analysis |
| `docs/chess-maths/` | chess_spectral_research_notebook | Chess as spectral lattice fermion system — piece-graph spectra / D_4 / B_4 reps / irrep multiplicities |
| `docs/chess-maths/` | chess_spectral_4d_notebook | 4D Chess Spectral validation |
| `docs/logo-maths/` | logo_research_notebook | LOGO turtle graphics → cyclic-group encoder |
| `docs/othello-maths/` | othello_spectral_research_notebook | Othello/Reversi piece-flip dynamics as spectral lattice |
| `docs/unsolved-maths/` | unsolved_maths_spectral_research_notebook | Wikipedia unsolved-problems canvass — 14 A-N primitive class operators applied to canonical open problems (PR #677 merged; 26 partitions) |
| `docs/substrate-native-maths/` | (R30 walking-path README) | 1:3:7:3 substrate research (R30 active walking-path — PR #680) |

All share **algebra / eigenbasis / cyclic-group / spectral side** discipline — see §4 CAD-grade scope ban below.

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

### CAD-grade scope ban (cross-subtree discipline)

**Framework research is algebra / eigenbasis / cyclic-group / spectral side ONLY.** NOT CAD / fabrication / mechanical-engineering geometry / mesh-contact / axle-wobble / fabrication-tolerance modeling. This ban applies across ALL sister notebooks in the portfolio (see §3 sister-package table). The canonical scope-doc statement lives in `docs/antikythera-maths/CLAUDE.md`. If a request reads as "model the physical bronze mesh geometry" or "compute axle wobble" or "fabrication-tolerance geometry" — push back. CAD-grade fabrication geometry is not the framework's domain.

### C library discipline (when any C-touching work occurs)

- **JPL Power-of-Ten audit** — srmech C library passes all 10 Holzmann Power-of-Ten rules (`docs/srmech/c/JPL_AUDIT.md`). `tests/test_jpl_audit.py` is a mechanical ratchet (Rules 1 no-goto / 3 no-malloc / 4 ≤60-line-functions / 5 ≥2-asserts-per-non-exempt-function / 8 no-multi-line-macros). **Violations only go DOWN, never up.**
- **Pedantic-build CI matrix** (Linux gcc / macOS clang / Windows MSVC) — `-Werror` / `/WX` enforced; any new warning fails CI.
- **ABI compatibility** — bump `SRMECH_ABI_VERSION` in lockstep whenever wire-format of any exported function changes. Adding a new symbol does NOT bump ABI.
- **No new `hashlib.sha256(...)` direct calls** — route through `srmech.amsc.format.sha256_bytes(...)` so native dispatch picks up transparently.

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
- **TestPyPI-rc-before-PyPI release discipline** per `[[feedback_always_rc_first_for_downstream_publishes]]` — every release ships as `vX.Y.ZrcN` to TestPyPI first; only clean (non-rc) tags route to production PyPI. Verify in clean venv OUTSIDE the source tree (source-tree namespace-package shadowing will silently load `_native.py` without `.dll/.so` and `HAS_NATIVE=False` spuriously). srmech version SSOT lives in FOUR files that must agree: `python/pyproject.toml`, `python/pyproject-pure.toml`, `python/srmech/version.py`, `c/include/srmech.h` (`SRMECH_VERSION_PRE` / `SRMECH_VERSION`).

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
