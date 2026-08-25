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

**The `+` on the fourth row is load-bearing — that block is not the same KIND as the other three** (clarified 2026-07-29, `#T1017`; nothing above is retracted). The first three rows are the **imaginaries**: `1 + 3 + 7 = 11 = dim Im ℂ / ℍ / 𝕆`, shipped as `one.py`'s `AN_IMAG_SLOTS = (("A",), ("I","C","J"), ("D","E","F","G","K","L","M"))`. B/H/N are **not a fourth imaginary block** — they are the three **`ℝ·1` reals**, shipped as a *separate* constant `GRAMMAR_SLOTS = ("B","H","N")` and bound **one per Hurwitz rung** rather than listed as a block (`one.py` enforces `len(GRAMMAR_SLOTS) == len(BLOCK_DIMS)`, i.e. "one `ℝ·1` anchor per block", and `_the_one_anchor` indexes them by rung `n`). So the same fourteen directions carry two co-valid groupings — by **role**, `1+3+7+3` (the table above); by **algebra**, `BLOCK_DIMS = (2,4,8)`, since `2+4+8 = 14` too. `2+4+8` is **not** a rival count. This is the "14 = 3 anchors + 11 imaginaries" decomposition the R30 note below already states, made explicit at the table so the four rows are not read as four peers.

### Per R30 (structurally closed 2026-05-24; MS #18 R30/R31/R32; PR #680)

R30 **final-refined** (substrate notebook §5): 11D-quantum-language and 14 = 1+3+7+3 cyclic-algebra-language are **two co-equal substrate-native mathematical languages for the same substrate**, both bit-exact — NOT substrate-vs-projection. The original inversion-hypothesis ("11D is a projection-artifact of the 14-substrate") was **structurally falsified** (substrate §3.2: *"no projection-residue at 14→11D"*), even though the 1:3:7:3 = 14 antiquity-convergence is real. Accordingly the +3 meta-cascade triad (B/H/N) are **substrate-native language-translation operators** between the continuous-Hopf-quantum and discrete-cyclic-cascade languages — **NOT "projection-enablers"** (that earlier wording is retracted; §4.2/§5). R31 Antikythera SURVIVES: the back-panel metacycle dials (Saros + Metonic + Callippic) ARE the three B/H/N language-translation anchors. The universal +3 = B/H/N is the source of the **k=3 cross-substrate signature** (every catalogued k=3 is a B/H/N instantiation event; substrate §5–§6). The 14 = 3 anchors + 11 imaginaries decomposition and the "11D observer frame" *label* survive the refinement; only the projection/inversion *direction* was retracted. (CLAUDE.md kept the stale "projection-enabler / inversion" wording until 2026-07-24; corrected then.)

### Class O dissolution note (vocabulary discipline; 2026-05-16)

**Class O is NOT a separate class.** The signed-metric / Wick-rotation operation initially located by Spike #24 bonus 8 was dissolved into **Class L as a signed-Laplacian-variant sub-operation** per `[[feedback_no_privileged_primitive_classes]]`. Vocabulary stays at **14 classes A–N** (no Class O). **The signed-Laplacian op SHIPPED** (`srmech/amsc/laplacian.py:3279` `signed_laplacian`, plus `magnetic_laplacian` at `:3458` — the Hermitian directed/chiral peer); this line previously read "future Class L rcs will add it" and was stale per `[[feedback_claude_md_orientation_can_lag_notebook_ssot]]` (corrected 2026-07-25).

---

## §2 Use srmech for all maths + spectral-encoding tasks

**`srmech`** = **Stored-Relationship Mechanism**. PyPI; [srmech.net](https://srmech.net) forwards to repo. THE framework-research tool — use it instead of bare Python math wherever possible. v0.4.0 shipped the full **14-class C-parity primitive vocabulary** (A-N) + the canonical **QM/QFT/SM operations layer** (single_particle / spin / potentials / relativistic / propagators / pseudo_hermitian / gauge / sm / octonion / quaternion / so8 / so9 / triality / hurwitz). **As of v0.9.0rc381 (ADR-0010 physics slice) that layer lives at `srmech.physics.qm.*`** — the whole `qm` subpackage moved under the new `srmech.physics` domain. The old `srmech.qm.*` path was **REMOVED in v0.9.0rc382** — a clean break with no alias, per the no-legacy-path discipline (rc381's one-release deprecation alias was against it, and only ever reached TestPyPI, never production PyPI) — so `import srmech.qm` now raises `ModuleNotFoundError`; use `srmech.physics.qm.*`.

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
| Cyclic / modular gcd | `srmech.math.cyclic.gcd` | **I** |
| Rational anchor (best-rational) | `srmech.math.rational.best_rational(num: int, denom: int, max_d: int)` | **N** |
| Cascade primitives (planned) | `srmech.amsc.cascade.*` (precursor at `docs/unsolved-maths/_cascade_helpers.py`) | foundational |
| TOML cascade-runner (planned; NOT yet packaged — no `srmech.cosmos` module exists) | `srmech.amsc.cascade.*` are the shipped cascade primitives | composition |
| Spectral decompose / delta / recompose / similarity | `srmech.signal_processing.*` (v0.4.2+) | spectral |
| AMSC catalogs (attested data) | `srmech.amsc.tool_schema` for catalog creation | provenance |
| Asymptotic calculus (trig / transcendentals / calculus) | `srmech.asymptotic_calculus.*` (+ `srmech.trigonometry.*`) — **importable since v0.7.0rc26**; thin re-exports of the **Class-N** primitives in `srmech.math.rational` (`sin/cos/exp/log1p/atan_series_truncate(numerator, denominator, num_terms)` → exact `(num, den)` rational; the substrate-native "continuous" trig). Attested worked-instances at `srmech/amsc/attested/asymptotic_calculus/` | math |
| Cosmos catalogs (packaged under `srmech.amsc.attested.*`) | `srmech.amsc.attested.{cosmos_validation, cmb_polarisation_spectra, cmb_bispectrum, cmb_lensing, cmb_low_ell_maps}` (Friedmann dark-fraction + TE/EE/BB / fNL / lensing / low-ℓ maps — these ARE packaged; there is just no `srmech.cosmos` module) | astrophysical |

Per `[[project_srmech_foundational_cascade_operations_catalog]]`: cascade-helpers replacing Python math modules should land as srmech catalog peers to `asymptotic_calculus` and `trigonometry`.

### Cascade-honesty discipline (load-bearing)

Per `[[feedback_sign_handling_is_class_k_pin_slot_not_alu_abs]]`:

- **NEVER use Python `abs()` inside a cascade script.** Sign-flip IS canonical **Class K pin-slot phase-boundary** per `[[user_stance_epicycle_via_gear_plus_pin]]`; sign-re-application is **Class C**.
- Express sign-handling as named **Class K + Class C composition** so the cascade-count matches the cascade-shape claimed.
- `srmech.math.rational.best_rational(num: int, denom: int, max_d: int)` takes **integer pair**, not float.

### AMSC catalog gotchas

Per `[[feedback_srmech_amsc_catalog_pitfalls]]` — 6 mandatory TOML sections; `[source]` needs `human_readable_name` (not `name`); `[fetch].ndjson_path` is load-bearing; `literature_curated` rows are FLAT dicts (NOT MPRRecord envelopes); `jacobi_eigvals` → ndarray; `best_rational` → tuple; `dense_laplacian` edges are 2-tuples.

### Config-driven TOML class discipline (load-bearing)

Per `[[feedback_prefer_config_driven_toml_classes]]` (user direction 2026-06-13) — **PREFER config-driven `[class]` TOML (`srmech.dsl.make_class`) over hand-coding srmech domain classes.** When a domain object is a cascade-of-the-14 composition (state + cascade-op-chain methods), declare it as a `[class]` TOML descriptor; the qm/hurwitz + genome treatment is the model. Carriers (`Mat`/`Vec`/`HV`), `srmech.bus`, adapters, and the `srmech.physics.qm.*` physics op-families STAY Python. **Verified conversion cost:** follow the genome two-layer pattern (ship each method as a flat cascade op → bind in TOML); the `make_class` contract is one-op-per-method + a single `appends`/`sets` field, so dict/multi-field-state classes need a contract extension first (`SedenionRegister` is HARD, not a freebie; immutable accessor-shaped classes like `One` are cleaner first targets). Prove every conversion with a DSL-class-vs-Python equivalence test.

---

## §3 Active research arcs

| Arc | Surface | Status |
|-----|---------|--------|
| **Substrate-native maths** (R30 walking-path; 1:3:7:3 substrate) | [PR #680](https://github.com/lemonforest/mlehaptics/pull/680) + [`docs/substrate-native-maths/`](docs/substrate-native-maths/) | structurally closed 2026-05-24 (two co-equal substrate-native languages; inversion falsified, B/H/N = language-translation operators); Antikythera (a) SURVIVES |
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

**The deeper line — start from the metric-field carrier, not the spacetime shadow** (`[[feedback_metric_field_native_not_spacetime_shadow]]`, 2026-07-23). "No CAD / mesh / FEA / GPU" is the *symptom*; the real line is a **direction of derivation**. FAVOR carrier-native / metric-field-native ops (the CD / H-genome carrier's own **distributional ⊗ relational ⊗ resonant** triality, closed-form on the ALU); DISFAVOR spacetime-shadow / continuum-projected math (continuum-first — it needs a GPU *because* the shadow has no closed form). The test is **"does the op emerge FROM the carrier (bottom-up), or is it a cascade reverse-engineered to approximate a continuous / spacetime target (top-down)?"** — not "is it GPU". GPU is only the marker. Deepens `[[feedback_cad_ban_is_gpu_numerical_not_closedform_physical]]`; full statement in the canonical scope-doc above.

### C library discipline (when any C-touching work occurs)

- **JPL Power-of-Ten audit** — srmech C library is clean on **eight** of the 10 Holzmann rules; **Rule 1 and Rule 9 are PARTIAL** under seeded down-only ratchets (9 depth-bounded recursion cycles; 10 function-pointer declarator sites, `IV_VTABLE` named as next drain) — see `docs/srmech/c/JPL_AUDIT.md`. *(This line said "passes all 10" until rc452; it had been false since before rc441, surviving because the unmeasured halves of both rules had no detector.)* `tests/test_jpl_audit.py` is a mechanical ratchet (Rules 1 no-goto+no-new-recursion / 3 no-malloc / 4 ≤60-line-functions / 5 ≥2-asserts-per-non-exempt-function / 8 no-multi-line-macros / 9 no-new-function-pointers). **Violations only go DOWN, never up.**
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

### Issue-reference notation (load-bearing — prose in this repo SHIPS)

**The one inviolable rule: a LOCAL TASK ID is never written bare.** Bare `#NNNN` is *reserved for*
real GitHub objects — it autolinks, which is exactly what you want when the target really is a GitHub
issue. The defect is a **task ID** wearing that form, because it then mints a live link to whatever
unrelated issue happens to hold the number. (Canonical statement: `docs/srmech/python/CHANGELOG.md:5`.)

| Form | Means | Note |
|------|-------|------|
| **`#T986`** | a **local task** (session task list; NOT GitHub) | **Mandatory.** Never bare. |
| **`F1252`** | an RBS-LM **finding** | Own namespace, no `#` |
| **`#1293`** | a real GitHub issue/PR — **correct as-is** | Autolinks on purpose |
| **`gh #1293`** | the same, written explicitly | Optional; clearer in new prose |
| **`` `#938` ``** | a bare ref **quoted as a code span** — legitimate when *documenting* a bad ref | A code span does **not** autolink |

**Existence proves nothing; TOPICALITY decides.** Nearly every number resolves to *some* real GitHub
object. The question is never "does #943 exist" but "does the prose around it describe *that* object,
or one of our tasks?" `#943` is simultaneously a real merged PR and a real local task. **Read the
surrounding prose; never batch-convert.** Two cleanups (`#T974`, `#T986`) each found legitimate bare
refs a mechanical sweep would have broken, including block-quoted external material. **When unsure,
leave it and say so** — a wrongly-converted working link is worse than an unconverted one, because it
looks deliberate.

**Why it is load-bearing: this prose SHIPS.** Docstrings and `ToolEntry` text are emitted into
generated files and travel inside the wheel. Measured 2026-07-27: **15 false links were live in
published artifacts** (`_tool_docs.py`, `_c_claims.py`, `srmech_tool_registry.c`), reaching users via
`describe()`, the MCP tool list and the compiled-in C registry — `#938` as a task ID renders as
*"srmech v0.7.5rc13: numpy-math ratchet"*, an unrelated PR. It applies to **four** surfaces, and the
fourth is the one people miss: file content · commit messages · PR body · **the PR TITLE, which
becomes the merge-commit subject**.

⚠️ **Any mechanical check MUST exempt code spans, and MUST bound the digit range.** A naive `grep`
over rc348's diff flagged 10 "violations" that were all backticked and all correct (0 genuinely
bare); an unbounded digit pattern also swallows `UAX #29`, `MS #20`, `Spike #24`, `graft #1`.
The shipped guard (`tests/test_ref_notation_emitted_rc348.py`) is therefore **strict-zero on the
decidable class** — a number the tree spells `#TNNN` *somewhere*, written bare — and a **down-only
CEIL** on the pre-convention residual, which it drains over time. **Four** bad ref-patterns were
written in a single session; treat this as harder than it looks and do not "simplify" the exemptions.

**Why this is not a style preference.** A bare `#NNN` in prose becomes a live hyperlink to whatever
GitHub object happens to hold that number. Local task IDs and GitHub issue numbers occupy the same
numeric range, so the collision is routine, not rare — `#938` as a local task renders as *"srmech
v0.7.5rc13: numpy-math ratchet + lmmse → cascade"*, an unrelated PR. Measured 2026-07-27: **15 such
false links had shipped inside published wheels** (`_tool_docs.py`, `_c_claims.py`,
`srmech_tool_registry.c`), reaching users through `describe()`, the MCP tool list and the compiled-in
C registry.

**It applies to FOUR surfaces**, and the fourth is the one people miss:
1. file content (including docstrings and `ToolEntry` prose — **these are emitted into generated
   files and ship in the wheel**)
2. commit messages
3. PR body
4. **the PR TITLE — it becomes the merge-commit subject**

**Existence proves nothing; TOPICALITY decides.** Every ref will usually resolve to *some* real
GitHub object. The question is never "does #943 exist" but "does the prose around it describe *that*
object, or one of our tasks?" `#943` is simultaneously a real merged PR and a real local task. **Read
the surrounding prose; never batch-convert.** Two cleanups (`#T974`, `#T986`) both found legitimate
bare refs that a mechanical sweep would have broken — including block-quoted external material.

**When in doubt, leave it and say so.** A wrongly-converted working link is worse than an unconverted
one, because it looks deliberate.

### PR + commit hygiene

- `[[feedback_no_squash_merges]]` — NEVER squash-merge; use `gh pr merge --merge` or `--rebase`
- `[[feedback_rolling_pr_partition_boundary_updates]]` — at the end of each research partition, update rolling PR with verdict + next-partition queue
- `[[feedback_no_mvp_framing]]` — scope ships by closed-form algebra propagation; full-coverage discipline
- `[[feedback_session_worktree_namespace_isolation]]` — session owns ONLY its own `.claude/worktrees/` directory
- **TestPyPI-rc-before-PyPI release discipline** per `[[feedback_always_rc_first_for_downstream_publishes]]` — every release ships as `vX.Y.ZrcN` to TestPyPI first; only clean (non-rc) tags route to production PyPI. Verify in clean venv OUTSIDE the source tree (source-tree namespace-package shadowing will silently load `_native.py` without `.dll/.so` and `HAS_NATIVE=False` spuriously). srmech version SSOT lives in FIVE files that must agree: `python/pyproject.toml`, `python/pyproject-pure.toml`, `python/srmech/version.py`, `c/include/srmech.h` (`SRMECH_VERSION_PRE` / `SRMECH_VERSION`), and the deliberate hard version-pin in `python/tests/test_signal_processing_scaffolding.py` (the single literal gate — its siblings only check the sources AGREE). This line said FOUR until rc358; ADR-0007 §2.1 has said FIVE all along, and that ADR is the SSOT for release mechanics.

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
