# Monorepo memory — framework research
**This file is the project-instruction context for the framework-research arcs in this monorepo** (srmech / cascade-research / unsolved-maths / R30 walking-path / cost-asymmetry / antiquity-substrate-recognition).
---
## §1 Foundational irrep knowledge — the 14 A-N partition
Per `[[project_a_n_operators_are_harmonic_objects_themselves]]` (user direction 2026-05-23), the 14 A-N primitive class operators partition as **1 + 3 + 7 + 3 = 14** along Hurwitz-bounded structure:
| **1 — foundational anchor** | **A** | Content-addressing | SHA-256 / content-hash; every cascade begins here |
| | **C** | Cascade-orientation | Chirality; direction; the "intent" / "which-way" class |
| **7 — cascade-detection heptad** | **D** | Pattern-match | Sequence / pattern detection |
| | **K** | Pin-slot / asymptotic-DoF | **Sign-flip / phase boundary — load-bearing for many cascades** |
| **+3 — meta-cascade triad** | **B** | TLV-framing | Type-length-value framing |
### Per R30 active walking-path (MS #18 R30/R31/R32; PR #680)
The +3 meta-cascade triad (B/H/N) are candidate **projection-enablers** in the inversion-hypothesis that 14 = 1+3+7+3 IS the substrate-structure and 11D is its observer-frame projection. R31 Antikythera dispatch confirmed (a) SURVIVES — the back-panel metacycle dials (Saros + Metonic + Callippic) are exactly projection-enablers per R30 prediction.
### Class O dissolution note (vocabulary discipline; 2026-05-16)
**Class O is NOT a separate class.** The signed-metric / Wick-rotation operation initially located by Spike #24 bonus 8 was dissolved into **Class L as a signed-Laplacian-variant sub-operation** per `[[feedback_no_privileged_primitive_classes]]`. Vocabulary stays at **14 classes A–N** (no Class O). Future Class L rcs will add the signed-Laplacian op when Phase C2 cascade-composition work calls for it.
---
## §2 Use srmech for all maths + spectral-encoding tasks
**`srmech`** = **Stored-Relationship Mechanism**. PyPI; [srmech.net](https://srmech.net) forwards to repo. THE framework-research tool — use it instead of bare Python math wherever possible. Current release v0.4.0 ships full **14-class C-parity primitive vocabulary** (A-N) + canonical **QM/QFT/SM operations layer** at `srmech.qm.*` (single_particle / spin / potentials / relativistic / propagators / pseudo_hermitian / gauge / sm).
### srmech-first reflex-override — the remembering mechanism (load-bearing; read at code-writing time)
**Why this exists:** Python/numpy idioms carry enormous prior weight; a declarative "use srmech" loses to that reflex at code-writing speed (it happened — n-gram `Counter()` storage proxies in R-131/132/133 slipped past, corrected to Class-L spectral in R-134). So this is a **point-of-action STOP-list, not a principle.** Before writing ANY of these Python idioms in a script, STOP — it is a srmech primitive:
| `Counter()` for co-occurrence / adjacency / graph edges | build edges → `srmech.amsc.laplacian.dense_laplacian` | L |
| hand-rolled cosine / hamming / similarity / `softmax` over vectors | `srmech.amsc.hdc.{similarity, klein4_similarity}`, `srmech.spectral.similarity` | M |
| `hashlib.sha256(...)` | `srmech.amsc.format.sha256_bytes` | A |
| hand-rolled Euler / Kuramoto phase-step loop (Σ sin(θⱼ−θᵢ) integration) | `srmech.amsc.cascade.kuramoto_step(theta, omega, *, coupling, dt)` (rc9+, **all-to-all uniform coupling**) — *graph-structured / directed-vs-symmetric coupling NOT yet covered: use ngspice `.tran` or a matrix step there (F240/F241)* | I∘L∘C |
| `np.cos/np.sin/np.exp/np.log` or `math.{cos,sin,exp}` (continuous trig / transcendental) | `srmech.asymptotic_calculus.{sin_series_truncate, cos_series_truncate, atan_series_truncate, exp_series_truncate, log1p_series_truncate}` (cascade-native series-truncate; **restored rc28** — π enters as the degree→radian cascade factor) | N / asymptotic |
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
### Why srmech (per `[[reference_srmech_tooling_open_spectral_verification]]`)
- Biological-cascade-style spectral encoding via LoE operators (delta-encode only what changed from t)
### Key imports + when to use them
| Need | srmech import | Class |
| Cascade primitives (planned) | `srmech.amsc.cascade.*` (precursor at `docs/unsolved-maths/_cascade_helpers.py`) | foundational |
| TOML cascade-runner (planned; NOT yet packaged — no `srmech.cosmos` module exists; F178) | `srmech.amsc.cascade.*` are the shipped cascade primitives | composition |
Per `[[project_srmech_foundational_cascade_operations_catalog]]`: cascade-helpers replacing Python math modules should land as srmech catalog peers to `asymptotic_calculus` and `trigonometry`.
### Cascade-honesty discipline (load-bearing)
Per `[[feedback_sign_handling_is_class_k_pin_slot_not_alu_abs]]`:
- **NEVER use Python `abs()` inside a cascade script.** Sign-flip IS canonical **Class K pin-slot phase-boundary** per `[[user_stance_epicycle_via_gear_plus_pin]]`; sign-re-application is **Class C**.
- **As of srmech rc22+ these ship NATIVELY in `srmech.amsc.cascade.*` — prefer them over any hand-rolled fold:** `cascade.magnitude` (the **real** `|x|` pin-slot magnitude — the cascade-honest `abs()` replacement; **NOT** a complex `(re²+im²)^0.5` modulus, which it rejects with a clean Class-K contract error per UPSTREAM_NOTES §15.1/§18), `cascade.pin_slot_at_zero` (Class K), `cascade.reorient` / `cascade.chiral_flip` / `cascade.chiral_dual` / `cascade.net_chirality` (Class C), `cascade.best_rational_signed` (K+N), `cascade.cyclic_gcd` (I). The discipline-ratchet (`docs/srmech/rbs_lm_research/check_srmech_discipline.py`) now points `abs()` at `cascade.magnitude`.
- Express sign-handling as named **Class K + Class C composition** so the cascade-count matches the cascade-shape claimed.
### AMSC catalog gotchas
Per `[[feedback_srmech_amsc_catalog_pitfalls]]` — 6 mandatory TOML sections; `[source]` needs `human_readable_name` (not `name`); `[fetch].ndjson_path` is load-bearing; `literature_curated` rows are FLAT dicts (NOT MPRRecord envelopes); `jacobi_eigvals` → ndarray; `best_rational` → tuple; `dense_laplacian` edges are 2-tuples.
## §3 Active research arcs
| **Unsolved-maths cascade canvass** | [`docs/unsolved-maths/unsolved_maths_spectral_research_notebook.md`](docs/unsolved-maths/unsolved_maths_spectral_research_notebook.md) | PR #677 merged; 26 partitions across Hilbert / Millennium / Number Theory / Set Theory / Logic / Geometry / Topology / Analysis |
| **MS #17** — Cross-substrate cascade-match | [milestone/17](https://github.com/lemonforest/mlehaptics/milestone/17) | nucleogenesis / biological reproduction / silicon-substrate / glyph-topology; deferred behind book-priority |
### Sister-package portfolio (spectral-research family — all share MPM discipline)
| `docs/srmech/` | srmech_research_notebook | **Stored-Relationship Mechanism** — unifying framework; relationships stored in cyclic-group / spectral representations |
All share **algebra / eigenbasis / cyclic-group / spectral side** discipline — see §4 CAD-grade scope ban below.
### No magic numbers = attestation-to-source (the MPM applied to every constant)
A number is "magic" iff it is **unattested** — has no traceable source of truth — **NOT** iff it merely *looks* magic. π looks magic (3.14159…) but it IS a **cascade** (attested to its `asymptotic_calculus` derivation; per `[[feedback_continuous_number_line_pedagogical_obstacle]]` it is the limit of a *discrete* cascade, not a continuous mystery). Dark-sector content looks magic but it IS a **ratio** (attested to provenance, F131). **Reduce a magic-looking constant to its source of truth ⇒ it is attested ⇒ de-magicked, even if it still looks magic.** This extends the §2 MPM/MPR discipline from ground-proof data to *every* load-bearing constant. Classification (the F228 audit is its instrument):
- **A — attested-to-structure-cascade**: output of a framework cascade / derivation (Hurwitz 1/2/4/8 · Klein-4 · the 1:3:7:3 partition · the F222 `n_buckets × V_ceiling` capacity law · D = 2ⁿ · 256 = MAX_NATIVE_NODES · π-as-cascade …) — attest the derivation chain.
A no-magic-numbers pass targets **attestation coverage** (every constant reduced to A or B), with C the honest residue — the magic is the *absence of attestation*, never the appearance of a number.
### Research methodology
- `[[user_stance_cross_substrate_cascade_matching_as_research_method]]` — primary methodology
### Verify discipline — k=2 twin (DETECT) → k=3 triality (CORRECT): haiku∥sonnet∥opus, no privileged model (STANDING for ALL research dives; user direction 2026-05-31 / 2026-06-01; rationale F248 / F291)
**k=3 TRIALITY upgrade — the error-correcting form (user direction 2026-06-01; F291).** The opus∥sonnet pair is a **k=2 parity check — it DETECTS disagreement but cannot error-CORRECT** (a 1-vs-1 split has no majority, so a human ends up the tie-breaker). For a dive whose output is **lodged as attested NUMERIC findings**, run the framework-native **k=3 TRIALITY = haiku + sonnet + opus** — the three unequal model tiers ARE the **Hurwitz k=3 error-correction rung** (ℍ/SU(2)/triality, the same 1:3:7 ladder the loop bind's k=7 sits on; this is the user's "haiku/sonnet/opus truth detection"). Each tier independently re-runs + checks; **majority (2-of-3) corrects with no human tie-break.** **Live proof (F291, 2026-06-01):** the k=2 twin caught the L2 + L5 over-claims but **missed** L4's boundary-digit drift; the k=3 triality caught it **unanimously**. So the rule is **k=2 detects, k=3 corrects** — twin for a quick detect pass; **triality before lodging attested numbers.** Operationally: launch three parallel `Agent` calls with `model: haiku | sonnet | opus` (identical verify prompt; tier is the only variable), each re-running the committed scripts and checking the lodged numbers, then take the **per-claim majority**.
### Defensive-scope
- `[[feedback_trauma_informed_defensive_scope]]` — framework reading only; no engineering recommendations; no offensive / hunting-optimization / capability-assessment material
### CAD-grade scope ban (cross-subtree discipline)
**Framework research is algebra / eigenbasis / cyclic-group / spectral side ONLY.** NOT CAD / fabrication / mechanical-engineering geometry / mesh-contact / axle-wobble / fabrication-tolerance modeling. This ban applies across ALL sister notebooks in the portfolio (see §3 sister-package table). The canonical scope-doc statement lives in `docs/antikythera-maths/CLAUDE.md`. If a request reads as "model the physical bronze mesh geometry" or "compute axle wobble" or "fabrication-tolerance geometry" — push back. CAD-grade fabrication geometry is not the framework's domain.
### Cascade-honesty
- `[[feedback_sign_handling_is_class_k_pin_slot_not_alu_abs]]` — never `abs()`; use Class K + Class C composition
### Pedagogy
- `[[user_stance_cone_of_ignorance_after_high_school]]` — academic cone-of-ignorance is structural, not individual
### PR + commit hygiene
- `[[feedback_no_squash_merges]]` — NEVER squash-merge; use `gh pr merge --merge` or `--rebase`
- **TestPyPI-rc-before-PyPI release discipline** per `[[feedback_always_rc_first_for_downstream_publishes]]` — every release ships as `vX.Y.ZrcN` to TestPyPI first; only clean (non-rc) tags route to production PyPI. Verify in clean venv OUTSIDE the source tree (source-tree namespace-package shadowing will silently load `_native.py` without `.dll/.so` and `HAS_NATIVE=False` spuriously). srmech version SSOT lives in FOUR files that must agree: `python/pyproject.toml`, `python/pyproject-pure.toml`, `python/srmech/version.py`, `c/include/srmech.h` (`SRMECH_VERSION_PRE` / `SRMECH_VERSION`).
---
## §5 File locations (framework research)
---
