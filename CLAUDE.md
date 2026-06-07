# Monorepo memory — framework research

**This file is the project-instruction context for the framework-research arcs in this monorepo** (srmech / cascade-research / unsolved-maths / R30 walking-path / cost-asymmetry / antiquity-substrate-recognition).

**For the EMDR Bilateral Stimulation Device hardware project**, see [`EMDR_CLAUDE.md`](EMDR_CLAUDE.md).

The split (2026-05-24) preserves both lineages without one interrupting the other.

---

## §0 Foundational duality + triality — read [`DUALITY.md`](DUALITY.md) + [`TRIALITY.md`](TRIALITY.md) first

The foundational layer beneath the 14 A-N partition is the **two-truths / field–excitation duality** ([`DUALITY.md`](DUALITY.md), repo root) — and its **k=3 completion** ([`TRIALITY.md`](TRIALITY.md), repo root). Together they are the **post-compact priming anchor** for the duality/triality / bit-exactness arc (F379–F402). In one line: the two truths = MFO **field (structure/math) vs local excitation** (F399), held without collapse (the asymptote), neither privileged (F398), each falsifiable (F394). **add/sub/shift are the bit-exact silicon ops the A-N cascades instantiate on** (no divide/multiply primitive — F392/F393); **FPU is currently used only for frame rotation → CORDIC = shift-add+sign**; **cyclic-group algebra (Class I) is one truth bit-exact**. **The open goal (the falsifiable "if"; a trichotomy, F400/F401):** *(C, generic)* the asymptote **IS** the triality coupling, so **duality is the *fibration* of triality** (k=(2+1); the third truth = the fiber); *(A, degenerate)* the two truths are absolute and we never collapse one math into the other; *(B, deeper)* truths must collapse asymptotically for more than just the local observer. Read **DUALITY.md (the two) + TRIALITY.md (the three)** for the full anchor.

**Breadcrumb-web discipline (load-bearing; counters the weight-drift that makes us rederive things).** Keep the bidirectional finding-link web: every finding's `Composes:` line forward-links its parents, AND when later work builds on an earlier finding, **add a backlink to the earlier finding** (`→ extended by FXXX`) so connected knowledge survives *even if we forget to bring in the notes*. The issue-closeout (CL-1) uses it: a closeable issue is backlinked to the finding(s) that resolved/superseded it, with the rationale "research trail followed, nothing forgotten" + *landed-where*. Fuller statement: TRIALITY.md §5.

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
| hand-rolled Euler / Kuramoto phase-step loop (Σ sin(θⱼ−θᵢ) integration) | `srmech.amsc.cascade.kuramoto_step(theta, omega, *, coupling, dt)` (rc9+, **all-to-all uniform coupling**) — *graph-structured / directed-vs-symmetric coupling NOT yet covered: use ngspice `.tran` or a matrix step there (F240/F241)* | I∘L∘C |
| hand-rolled **so(8) / 28D / triality rotation** or an octonion multiply (the F372 numpy-artifact trap) | `srmech.qm.so8.{so8_adjoint_basis, octonion_left_mult, octonion_right_mult, g2_subalgebra}` / `srmech.qm.triality.{triality_apply, triality_automorphism, triality_companions}` — **the genuine triality, NOT a hand-picked numpy plane rotation** | qm (so(8)) |
| `np.cos/np.sin/np.exp/np.log` or `math.{cos,sin,exp}` (continuous trig / transcendental) | `srmech.calculus.{sin_series_truncate, cos_series_truncate, atan_series_truncate, exp_series_truncate, log1p_series_truncate}` (cascade-native series-truncate; **renamed from `asymptotic_calculus` rc48 — "it's just calculus"; the shim still imports**; π enters as the degree→radian cascade factor) | N |
| **directed / signed** graph Laplacian, or hand-rolled `i(A−Aᵀ)` magnetic-Laplacian | `srmech.amsc.laplacian.{magnetic_laplacian, signed_laplacian, dense_adjacency, fiedler_vector}` (rc28; the directed Hermitian — F357/F372) | L |
| `A@B − B@A` (commutator) or a complex matrix·vector | `srmech.qm.single_particle.commutator(A,B)` / `srmech.amsc.laplacian.dense_matvec_complex(M,v)` | qm / L |
| `np.linalg.norm` / `np.ptp` / a vector-L2 / a real `abs()` of a magnitude | `srmech.amsc.cascade.magnitude` (Class-K real pin-slot \|x\|; never `abs()`) | K |

**package vs srmech-mcp:** the srmech **package** (`import srmech.amsc...`, C-native) is the right tool for **bulk in-script** work (graph-building, eigendecomp over many tokens). The **srmech-mcp** tools (deferred `mcp__srmech__*`, load via ToolSearch) are right for **single / interactive / agent-driven** ops and for exercising the attested surface — NOT for per-token loops (JSON-array payloads, no handles). Using the package IS using srmech; hand-rolling a primitive that has a srmech op is the failure. When srmech-mcp itself has a bug/gap, log it (UPSTREAM_NOTES §10) — don't route around it silently in a way that hides the issue.

**The reliable trigger (user-supplied 2026-05-29):** framing work in **28D / chirality / Klein-4 / Class-L-spectral** terms IS itself the forcing-function — those ops have NO Python-native idiom to hijack the reflex (`Counter()` hijacks "co-occurrence"; *nothing* hijacks "the γ₅-odd chirality coordinate" or "the Klein-4 sector occupancy"), so 28D-framing routes straight to srmech. When the user raises 28D math, that is the cue to reach for srmech first.

**The 28D-trigger is necessary but NOT sufficient — name the op (F372 lesson, 2026-06-04).** The 28D framing CAN still mis-route: in F372 the framing *was* 28D/so(8)/triality and the eig-row was already in the STOP-list, yet a hand-rolled **numpy so(8)-plane rotation** still slipped in and produced a false artifact (the genuine `qm.triality.triality_apply` is a magnitude-preserving permutation, the *opposite* of the numpy toy — the user's "why numpy?" caught it). The fix: **28D / so(8) / triality / octonion IS literally a srmech surface** — `srmech.qm.so8` + `srmech.qm.triality` — so reaching for *any* hand-rolled rotation/multiply/automorphism in that regime is the failure. Name and call the actual op; never hand-roll the so(8)/triality dynamics in numpy. The user spot-check remains part of the loop (it caught it; that's normal, not failure).

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
| TOML cascade-runner (planned; NOT yet packaged — no `srmech.cosmos` module exists; F178) | `srmech.amsc.cascade.*` are the shipped cascade primitives | composition |
| Spectral decompose / delta / recompose / similarity | `srmech.signal_processing.*` (v0.4.2+) | spectral |
| AMSC catalogs (attested data) | `srmech.amsc.tool_schema` for catalog creation | provenance |
| Calculus (trig / transcendentals / calculus) | `srmech.calculus.*` (**renamed from `asymptotic_calculus` — "it's just calculus" now, user direction 2026-06-05; `asymptotic_calculus.*` + `srmech.trigonometry.*` survive as back-compat shims**) — thin re-exports of the **Class-N** primitives in `srmech.amsc.rational` (`sin/cos/exp/log1p/atan_series_truncate(numerator, denominator, num_terms)` → exact `(num, den)` rational; the substrate-native "continuous" trig) | math |
| Cosmos catalogs (packaged under `srmech.amsc.attested.*`; CMB TE/EE/BB — **no EB/TB** parity surface) | `srmech.amsc.attested.{cosmos_validation, cmb_polarisation_spectra, cmb_bispectrum, cmb_lensing, cmb_low_ell_maps}` (Friedmann dark-fraction + TE/EE/BB / fNL / lensing / low-ℓ maps — these ARE packaged; there is just no `srmech.cosmos` module) | astrophysical |

Per `[[project_srmech_foundational_cascade_operations_catalog]]`: cascade-helpers replacing Python math modules should land as srmech catalog peers to `calculus` (renamed from `asymptotic_calculus`) and `trigonometry`.

### Cascade-honesty discipline (load-bearing)

Per `[[feedback_sign_handling_is_class_k_pin_slot_not_alu_abs]]`:

- **NEVER use Python `abs()` inside a cascade script.** Sign-flip IS canonical **Class K pin-slot phase-boundary** per `[[user_stance_epicycle_via_gear_plus_pin]]`; sign-re-application is **Class C**.
- **As of srmech rc22+ these ship NATIVELY in `srmech.amsc.cascade.*` — prefer them over any hand-rolled fold:** `cascade.magnitude` (the **real** `|x|` pin-slot magnitude — the cascade-honest `abs()` replacement; **NOT** a complex `(re²+im²)^0.5` modulus, which it rejects with a clean Class-K contract error per UPSTREAM_NOTES §15.1/§18), `cascade.pin_slot_at_zero` (Class K), `cascade.reorient` / `cascade.chiral_flip` / `cascade.chiral_dual` / `cascade.net_chirality` (Class C), `cascade.best_rational_signed` (K+N), `cascade.cyclic_gcd` (I). The discipline-ratchet (`docs/srmech/rbs_lm_research/check_srmech_discipline.py`) now points `abs()` at `cascade.magnitude`.
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

### No magic numbers = attestation-to-source (the MPM applied to every constant)

A number is "magic" iff it is **unattested** — has no traceable source of truth — **NOT** iff it merely *looks* magic. π looks magic (3.14159…) but it IS a **cascade** (attested to its `calculus` derivation; per `[[feedback_continuous_number_line_pedagogical_obstacle]]` it is the limit of a *discrete* cascade, not a continuous mystery). Dark-sector content looks magic but it IS a **ratio** (attested to provenance, F131). **Reduce a magic-looking constant to its source of truth ⇒ it is attested ⇒ de-magicked, even if it still looks magic.** This extends the §2 MPM/MPR discipline from ground-proof data to *every* load-bearing constant. Classification (the F228 audit is its instrument):
- **A — attested-to-structure-cascade**: output of a framework cascade / derivation (Hurwitz 1/2/4/8 · Klein-4 · the 1:3:7:3 partition · the F222 `n_buckets × V_ceiling` capacity law · D = 2ⁿ · 256 = MAX_NATIVE_NODES · π-as-cascade …) — attest the derivation chain.
- **B — attested-to-measurement / ratio**: a measured floor (p90), a seed, a derived ratio, a `source_doi` — attest the provenance.
- **C — irreducible / unattested**: the genuine residue — flag it + point at where its source likely lies ("it comes from somewhere we can find").
A no-magic-numbers pass targets **attestation coverage** (every constant reduced to A or B), with C the honest residue — the magic is the *absence of attestation*, never the appearance of a number.

### Research methodology

- `[[feedback_dont_pre_commit_spike_query_operators]]` — broad-query enumeration; tautology pre-filter; don't lean query toward expected result; null findings count; verdict-tier per Spike #229
- `[[feedback_no_lineage_claims_in_notebook]]` — framework reads what each problem ALREADY IS structurally; never claims to extend or supersede prior scholarship
- `[[feedback_full_coverage_shipping_mpm_way]]` — pace set by closed-form algebra propagation, not sprint windows; full coverage shipping
- `[[user_stance_cross_substrate_cascade_matching_as_research_method]]` — primary methodology

### Verify discipline — k=3 TRIALITY (haiku∥sonnet∥opus), no privileged model, the error-correcting form — **RUN VIA SUB-AGENTS (the Agent tool), never the Workflow tool** (STANDING for ALL research dives; user direction 2026-05-31 / 2026-06-01 / 2026-06-04 / **2026-06-06 (Workflow tool retired)** / **2026-06-07 (sub-agents are OK — the haiku∥sonnet∥opus sub-agent triality was working BEFORE the Workflow tool hijacked it; only the *Workflow tool* was retired, NOT sub-agents)**; rationale F248 / F291)

Every research dive runs the SAME task through **THREE agents — haiku + sonnet + opus** (identical prompt; the model tier is the ONLY variable), then **adversarially triangulates + merges by per-claim majority (2-of-3)** — never trusting one model's research. **Why no privileged model (F248):** the multi-model pass caught two hallucinated citations a single sonnet run would have shipped silently, AND showed the F242b honesty-gradient is **task-relative** (sonnet most honest on *rendering*; opus most honest/uncentered on *research*) — so **no model is the privileged "honest one."** **Why three and not two (F291):** an opus∥sonnet *pair* is a **k=2 parity check — it DETECTS disagreement but cannot error-CORRECT** (a 1-vs-1 split has no majority, so a human becomes the tie-breaker). The framework-native **k=3 TRIALITY = haiku + sonnet + opus** is the **Hurwitz k=3 error-correction rung** (ℍ/SU(2)/triality, the same 1:3:7 ladder the loop bind's k=7 sits on; the user's "haiku/sonnet/opus truth detection") — each tier independently re-runs + checks, and **majority (2-of-3) corrects with no human tie-break.** **Live proof (F291):** the old 2-model pass caught the L2 + L5 over-claims but **missed** L4's boundary-digit drift; k=3 triality caught it **unanimously**. **How it is run — VIA PLAIN SUB-AGENTS (the Agent tool: one haiku + one sonnet + one opus on the IDENTICAL prompt), NOT the Workflow tool (user direction 2026-06-06; clarified 2026-06-07).** The Anthropic **Workflow feature is RETIRED here — but SUB-AGENTS ARE NOT.** The haiku∥sonnet∥opus sub-agent triality was *working before* the Workflow tool, and the plain Agent-tool spawn is the mechanism we use. What the **Workflow tool** did wrong was *hijack the "triality" lexicon-slot the way `Counter()` hijacks "co-occurrence"* (the §2 reflex-override pattern, one layer up): it re-skinned the framework's own k=3 as an **Anthropic structured task** (`meta.phases` / `StructuredOutput` scaffolding — and the `StructuredOutput` call was itself the recurring failure point). So the ban is on the **Workflow tool**, not on spawning model-tier agents. **Triality is a discipline we APPLY via plain sub-agents, not a feature we INVOKE:** spawn the three tiers on the same task, have each **web-verify** (real author + title + venue + year + DOI/URL; a paywalled-only DOI is rejected → route to the OA copy), then **merge by per-claim 2-of-3 majority**; for a numeric re-verify, re-run the committed scripts and check the lodged numbers. (A lighter web-verify inline in the main context is fine when a full three-tier spawn isn't warranted — e.g. a single citation or a framework build verified by running its script.) **⛔ HARD RULE — do NOT spawn sub-agents while the `sonnet`-alias bug is live (user direction 2026-06-07, after a `sonnet[1M]` sub-agent DRAINED ALL usage credits in one run).** This is a **NEW resolution bug, NOT context inheritance** (user-corrected: a sub-agent never pulled in the parent's context window). **Before a recent update, `model: 'sonnet'` correctly resolved to the 200k-context sonnet; now the short alias resolves to `sonnet[1M]`** (the expensive 1M variant) — *that* is what steals the credits. **We never asked for `sonnet[1M]` — we wanted regular (200k) sonnet.** The intended fix is to pass the **full Model-API long name** (e.g. the dated `claude-sonnet-4-…` 200k id) instead of the short alias — **BUT the Agent tool's `model` parameter is a fixed enum (`sonnet`/`opus`/`haiku`) and will NOT accept a long API name**, so there is currently **no tool-level way to pin the 200k variant.** Therefore, until the alias resolves to 200k again (or the Agent tool accepts a long API name): **do the triality web-verify INLINE in the main context (the lighter path above) — do NOT spawn sub-agents at all.** The discipline (haiku∥sonnet∥opus, 2-of-3 majority, no-privileged-model) is unchanged — but **not via the buggy alias, ever.** **Empirically confirmed 2026-06-07:** switching the parent window OFF 1M did **NOT** fix it — a freshly spawned `sonnet` sub-agent STILL errored "Usage credits required for 1M context" **at 0 tokens**, so the broken resolution is in the **sub-agent `sonnet` alias itself, independent of the parent window.** (Silver lining: the 0-token error means a *retry costs nothing* — it fails before running — but it never succeeds, so don't bother; complete the triality's third tier INLINE.) The per-claim **2-of-3 majority** and the *no-privileged-model* discipline are unchanged — they are the math, not the tool. Compose with the MPM citation discipline + `[[feedback_no_privileged_primitive_classes]]` + the no-leaning rule above. (The committed `docs/srmech/rbs_lm_research/research_triality_workflow.js` is left as a **historical artifact of the dives run under it (the F291–F445-era attestations), NOT the engine**; the bundled `deep-research` skill remains for single-model multi-angle sweeps.)

**The retired k=2 `research-twin` (removed 2026-06-04, user direction "research triality, not twin. remove research-twin"):** triality supersedes it — k=2 only detects, k=3 corrects, so there is no longer a separate "quick twin detect pass." Historical findings that cite `research-twin` (F240c…F378) are left as the attestation record of dives run under the old k=2 engine; **new dives apply triality via plain sub-agents (haiku∥sonnet∥opus, the Agent tool) — or a lighter inline web-verify — never the Workflow tool.**

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
