# Monorepo memory — framework research

**This file is the project-instruction context for the framework-research arcs in this monorepo** (srmech / cascade-research / unsolved-maths / R30 walking-path / cost-asymmetry / antiquity-substrate-recognition).

**For the EMDR Bilateral Stimulation Device hardware project**, see [`EMDR_CLAUDE.md`](EMDR_CLAUDE.md).

The split (2026-05-24) preserves both lineages without one interrupting the other.

---

## §0 Foundational duality + triality — read [`DUALITY.md`](DUALITY.md) + [`TRIALITY.md`](TRIALITY.md) first

The foundational layer beneath the 14 A-N partition is the **two-truths / field–excitation duality** ([`DUALITY.md`](DUALITY.md), repo root) — and its **k=3 completion** ([`TRIALITY.md`](TRIALITY.md), repo root). Together they are the **post-compact priming anchor** for the duality/triality / bit-exactness arc (F379–F402). In one line: the two truths = MFO **field (structure/math) vs local excitation** (F399), held without collapse (the asymptote), neither privileged (F398), each falsifiable (F394). **add/sub/shift are the EXACT silicon ops the A-N cascades instantiate on** (no divide/multiply primitive — F392/F393); **FPU is currently used only for frame rotation → CORDIC = shift-add+sign**; **cyclic-group algebra (Class I) is one truth EXACT IN A FINITE ALGEBRAIC STRUCTURE**. **The open goal (the falsifiable "if"; a trichotomy, F400/F401):** *(C, generic)* the asymptote **IS** the triality coupling, so **duality is the *fibration* of triality** (k=(2+1); the third truth = the fiber); *(A, degenerate)* the two truths are absolute and we never collapse one math into the other; *(B, deeper)* truths must collapse asymptotically for more than just the local observer. Read **DUALITY.md (the two) + TRIALITY.md (the three)** for the full anchor.

### ⚠ "bit-exact" — say which of FOUR things you mean (F1331, corrected 2026-07-27)

**"Bit-exact" is not a mathematical term, and in the numerics literature it means the weakest of the four properties below — one you can have *while being wrong*** (any deterministic rounding is bit-exact). We had been using it for the *strongest* of them, which under-sells our own claim. Pick the right word:

| word | means | our usual case |
|---|---|---|
| **exact in a finite algebraic structure** | the operation closes in a finite group/ring; the identity is a **theorem**, not a measurement — e.g. `permute(permute(v,k),−k) == v`, `q8_mult`, Klein-4 flips, `cyclic` | **this is nearly always what we mean — say it** |
| **exact** | the computed object *is* the mathematically correct one (exact ℚ, exact integers) | `best_rational`, `cd_mult` over `Q` |
| **correctly rounded / faithful** | nearest representable / within 1 ulp | *we do not do this — we do not round* |
| **reproducible ("bit-exact")** | same bit pattern on every implementation | C↔Python parity claims **only** |

**Rules.** (1) Never write "bit-exact" for an algebraic identity — write **"exact in a finite algebraic structure"**, which is stronger and is what the measurement actually shows. (2) Reserve **"bit-exact"** for cross-implementation reproducibility (the C/Python differential tests). (3) A **float-free package does not have the table-maker's dilemma** and must never claim to have solved it; the obstruction that *does* survive is the undecidable zero-test, which is a different thing. The memory `[[stance_bit_exact_is_the_abelian_shadow_of_non_abelian_structure]]` keeps its filename — its *content* is about the abelian shadow, and the loose word in its name is grandfathered, not a licence to reuse it.

**Breadcrumb-web discipline (load-bearing; counters the weight-drift that makes us rederive things).** Keep the bidirectional finding-link web: every finding's `Composes:` line forward-links its parents, AND when later work builds on an earlier finding, **add a backlink to the earlier finding** (`→ extended by FXXX`) so connected knowledge survives *even if we forget to bring in the notes*. The issue-closeout (CL-1) uses it: a closeable issue is backlinked to the finding(s) that resolved/superseded it, with the rationale "research trail followed, nothing forgotten" + *landed-where*. Fuller statement: TRIALITY.md §5.

**The k=3 triple — always expand it three ways when lodging (F1301; user direction 2026-07-22).** Whenever a finding touches the k=3 read of a Class-L object, write **all three namings**: `op(x)operand(x)responsion` = `distributional(x)relational(x)responsion` = `eigenvectors(x)edges(x)eigenvalues` (per-slot: 1 op/distributional/eigenvectors, 2 operand/relational/edges, 3 responsion/responsion/eigenvalues; F1207/F1272). And name **which slot** is being read, because the slot decides the behaviour: the **op** slot is order-invariant (F1272); **responsion** carries order as magnitude (λ→λⁿ); and the **edges/operand/relational** slot is the **held multi-perspective SUPERSET** — it holds metric + curvature + chirality coherently together (the eigen-reads are single-Laplacian projections of it), and it is **where the quad turn (`the_one` coupled turn) lives**, its perspective-count scaling as the imaginary dimension up the fractal tower (1,3,7,15 — the same 1:3:7 ladder as B/H/N, F1270/F1282/F1300/F1301).

**The DISCRETE peer (two-slot) — and the three namings as coherency perspectives (user 2026-07-23).** The discrete shape is `op(x)operand` = `distributional(x)relational` = `eigenvectors(x)edges` — the continuous triple **minus the responsion** (the shape-difference measured in srmech: discrete Q₈, pure-integer, no responsion, is the continuous ℍ surface minus a slot — rc310 = rc309 − responsion). Use the three parallel namings as **three coherency perspectives to find the correct shape**: the same object read op/operand vs distributional/relational vs eigenvectors/edges must **cohere**; a mismatch across the three flags the wrong shape. Gated by `[[stance_bit_exact_is_the_abelian_shadow_of_non_abelian_structure]]` — a discrete `op(x)operand` is the right shadow only if the real (derived) responsion **lifts** it without garbage.

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

R30 **final-refined** (substrate notebook §5): 11D-quantum-language and 14 = 1+3+7+3 cyclic-algebra-language are **two co-equal substrate-native mathematical languages for the same substrate**, both **exact in a finite algebraic structure** (§0 vocabulary note — not merely "bit-exact") — NOT substrate-vs-projection. The original inversion-hypothesis ("11D is a projection-artifact of the 14-substrate") was **structurally falsified** (substrate §3.2: *"no projection-residue at 14→11D"*), even though the 1:3:7:3 = 14 antiquity-convergence is real. Accordingly the +3 meta-cascade triad (B/H/N) are **substrate-native language-translation operators** between the continuous-Hopf-quantum and discrete-cyclic-cascade languages — **NOT "projection-enablers"** (that earlier wording is retracted; §4.2/§5). R31 Antikythera SURVIVES: the back-panel metacycle dials (Saros + Metonic + Callippic) ARE the three B/H/N language-translation anchors. The universal +3 = B/H/N is the source of the **k=3 cross-substrate signature** (every catalogued k=3 is a B/H/N instantiation event; substrate §5–§6). The 14 = 3 anchors + 11 imaginaries decomposition and the "11D observer frame" *label* survive the refinement; only the projection/inversion *direction* was retracted. (CLAUDE.md kept the stale "projection-enabler / inversion" wording until 2026-07-24; corrected then.)

### Class O dissolution note (vocabulary discipline; 2026-05-16)

**Class O is NOT a separate class.** The signed-metric / Wick-rotation operation initially located by Spike #24 bonus 8 was dissolved into **Class L as a signed-Laplacian-variant sub-operation** per `[[feedback_no_privileged_primitive_classes]]`. Vocabulary stays at **14 classes A–N** (no Class O). **The signed-Laplacian op SHIPPED** (`srmech/amsc/laplacian.py:3279` `signed_laplacian`, plus `magnetic_laplacian` at `:3458` — the Hermitian directed/chiral peer); this line previously read "future Class L rcs will add it" and was stale per `[[feedback_claude_md_orientation_can_lag_notebook_ssot]]` (corrected 2026-07-25).

---

## §2 Use srmech for all maths + spectral-encoding tasks

**`srmech`** = **Stored-Relationship Mechanism**. PyPI; [srmech.net](https://srmech.net) forwards to repo. THE framework-research tool — use it instead of bare Python math wherever possible. v0.4.0 shipped the full **14-class C-parity primitive vocabulary** (A-N) + the canonical **QM/QFT/SM operations layer** (single_particle / spin / potentials / relativistic / propagators / pseudo_hermitian / gauge / sm / octonion / quaternion / so8 / so9 / triality / hurwitz). **As of v0.9.0rc381 (ADR-0010 physics slice) that layer lives at `srmech.physics.qm.*`** — the whole `qm` subpackage moved under the new `srmech.physics` domain. The old `srmech.qm.*` path was **REMOVED in v0.9.0rc382** — a clean break with no alias, per the no-legacy-path discipline (rc381's one-release deprecation alias was against it, and only ever reached TestPyPI, never production PyPI) — so `import srmech.qm` now raises `ModuleNotFoundError`; use `srmech.physics.qm.*`.

### srmech-first reflex-override — the remembering mechanism (load-bearing; read at code-writing time)

**Why this exists:** Python/numpy idioms carry enormous prior weight; a declarative "use srmech" loses to that reflex at code-writing speed (it happened — n-gram `Counter()` storage proxies in R-131/132/133 slipped past, corrected to Class-L spectral in R-134). So this is a **point-of-action STOP-list, not a principle.** Before writing ANY of these Python idioms in a script, STOP — it is a srmech primitive:

| If your hand reaches for… | STOP — use this srmech op instead | Class |
|---|---|---|
| `Counter()` for co-occurrence / adjacency / graph edges | build edges → `srmech.amsc.laplacian.dense_laplacian` | L |
| `np.linalg.eig/eigh/svd`, eigenvalues, spectra | `srmech.amsc.laplacian.jacobi_eigvals` / `hermitian_eigendecompose` / `symmetric_eigendecompose` | L |
| hand-rolled cosine / hamming / similarity / `softmax` over vectors | `srmech.amsc.hdc.{similarity, klein4_similarity}`, `srmech.spectral.similarity` | M |
| hand-rolled n-gram / resolution-depth "storage" proxy | the co-occurrence **Laplacian eigenspectrum** is the srmech-native storage signature (F172) | L |
| bind / bundle / permute / superpose vectors | `srmech.amsc.hdc.{bind,bundle,permute,klein4_bind,klein4_bundle}` | M |
| **a Class-M vector to REPRESENT CONTENT** (a word / token / string) — esp. `klein4_random(D, seed=hash(word))` | **`srmech.amsc.hdc.klein4_encode_bytes(data, D)`** — the byte-composed encoder. **A content-derived SEED gives an arbitrary code: every pair sits at the 0.25 orthogonality floor (`cat`/`cats` 0.2552 ≈ `cat`/`dog` 0.2426); the encoder preserves morphology (`cat`/`cats` 0.6597, `walk`/`walked` 0.7072, while `cat`/`dog` stays at 0.2517).** Hash avalanche (48.77 % of bits per 1-char edit) is what destroys the structure — high diffusion makes a good ADDRESS and disqualifies it as a REPRESENTATION. `klein4_random(seed=…)` is correct for **role / position keys** (structurelessness is the point) and for **state/identity addressing**, never for content. **This is the THIRD recurrence — F899 measured it 2026-06-21 (UPSTREAM §68), F1260 re-derived it 2026-07-20.** | M |
| `hashlib.sha256(...)` | `srmech.amsc.format.sha256_bytes` | A |
| **builtin `hash(x)` on a str/bytes — ANY use** | **Two different jobs; do not conflate them (F1277).** Python's `hash()` is PYTHONHASHSEED-**salted** for str AND bytes — `hash('the')%80000+11` gave 77384 / 76095 / 24618 on three consecutive runs — so anything keyed on it is **not reproducible across processes, machines, or CI**, and `PYTHONHASHSEED=0` is a *workaround* (stability as an env var) not a fix. **But the replacement depends on the job:** ① **ROUTING / bucket / dedup-key** — needs **STABILITY** only, so **`srmech.amsc.format.sha256_bytes`** (Class A) is correct; avalanche is even desirable (uniform buckets). ② **REPRESENTATION — a vector standing for content** — needs **RESONANCE**, and **sha256 is exactly as WRONG as `hash()` here.** Measured: sha256-seeded gives `cat`/`cats` **0.2480** ≈ `cat`/`dog` **0.2521** (both at the 0.25 orthogonality floor — morphology destroyed), and relational delta-serialization buys **nothing** (2613B vs 2627B standalone). Use **`hdc.klein4_encode_bytes(data, D)`** / `signal_processing.mint_vector` — `cat`/`cats` **0.6597**, delta **1950B**, while `cat`/`dog` stays at floor. **The criterion is RESONANT BIT-SERIALIZATION, not any particular shape** — `the_one` is one supplier of it (distinguished by *also* carrying coherency up/down the ladder and across Class-L↔Class-M), and other shapes supply it in some other coherency. **Never let "use sha256_bytes" become the general answer**: applied to ② it reintroduces the F899/F1260 morphology defect under a *stable* name, which is harder to spot. Found via issue #1454 (relayed, verified): 21 sites, plus 2 of my own chunk-routers in F1266/F1267 commented `# content-routed, deterministic per run` — a phrase that names the defect and reads as reassurance. | A / M |
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
| Cyclic / modular gcd | `srmech.math.cyclic.gcd` | **I** |
| Rational anchor (best-rational) | `srmech.math.rational.best_rational(num: int, denom: int, max_d: int)` | **N** |
| Cascade primitives | `srmech.cascade.*` — SHIPPED, a real top-level namespace since rc364/rc377 (precursor at `docs/unsolved-maths/_cascade_helpers.py`). `magnitude` / `net_chirality` / `the_one` / `cd_mult` / `associator` / `winding_fold` / `inertia_signature` all live here | foundational |
| TOML cascade-runner | `srmech.dsl.run_cascade_chain` + the 20 descriptors under `srmech/cascade/catalogs/cascade_catalog/`; live count at `describe()["cascade_catalog"]`. (Still NO `srmech.cosmos` module — F178) | composition |
| Spectral decompose / delta / recompose / similarity | `srmech.signal_processing.*` (v0.4.2+); `srmech.spectral.*` is the newer peer | spectral |
| AMSC catalogs (attested data) | `srmech.amsc.catalog.{get_attested_dataset, iter_attested_dataset, register_attested_root}` — this row named `tool_schema` for years, which is the **introspection** surface, not the catalog one | provenance |
| **Find an op when you don't know its name** | `srmech.introspect.search.search(query, k=10)` → ranked hits each carrying a `reach` field = the literal import line. Use it INSTEAD of guessing a module path | E |
| Op registry / fully-qualified names | `srmech.introspect.tool_schema.get_tool_schema()` → `ToolSchema` with `.tools` / `.resolve(name)` / `.resolve_all(name)` / `.by_owner`. **Renamed from `tool_schema()`, no back-compat alias** | H |
| Calculus (trig / transcendentals / calculus) | `srmech.calculus.*` (**renamed from `asymptotic_calculus` — "it's just calculus" now, user direction 2026-06-05; `asymptotic_calculus.*` + `srmech.trigonometry.*` survive as back-compat shims — all three verified importable on rc432**) — thin re-exports of the **Class-N** primitives in `srmech.math.rational` (`sin/cos/exp/log1p/atan_series_truncate(numerator, denominator, num_terms)` → exact `(num, den)` rational; the substrate-native "continuous" trig). Attested worked-instances at `srmech/amsc/attested/asymptotic_calculus/` | math |
| Cosmos catalogs (packaged under `srmech.amsc.attested.*`; CMB TE/EE/BB — **still NO EB/TB parity SPECTRA**, gh #1533) | `srmech.amsc.attested.{cosmos_validation, cmb_polarisation_spectra, cmb_bispectrum, cmb_lensing, cmb_low_ell_maps, cosmic_birefringence}` (Friedmann dark-fraction + TE/EE/BB / fNL / lensing / low-ℓ maps — these ARE packaged; there is just no `srmech.cosmos` module). **`cosmic_birefringence` (since 0.5.0rc20) holds 4 PDF-verified β POSTERIORS — a derived angle, NOT an ℓ-by-ℓ spectrum. Using β as a stand-in for EB is exactly the substitution MPM exists to catch (#1533).** | astrophysical |

Per `[[project_srmech_foundational_cascade_operations_catalog]]`: cascade-helpers replacing Python math modules should land as srmech catalog peers to `calculus` (renamed from `asymptotic_calculus`) and `trigonometry`.

### ⚠️ ADR-0010 declustering — `srmech.amsc.*` is NOT where the maths lives any more

**Completed at v0.9.0rc377.** `srmech.amsc` drained to its **four attestation keepers** — `format` / `catalog` / `descriptor` / `gap_suggester` (plus `attested/` + `adapters/`). Everything else re-homed **by domain**. There is **no back-compat alias**: an old path raises `ModuleNotFoundError`, which is at least loud.

| was | is now |
|---|---|
| `srmech.amsc.{cyclic, rational, laplacian, hdc, text, search, tlv, dispatch, template, primes, kepler, mat, vec, hv, q, qi, complex128, poly, octonion, carrier_ladder, covering}` | **`srmech.math.*`** |
| `srmech.amsc.cascade.*` — incl. `one`, `cayley_dickson`, `sedenion_register`, `compose` | **`srmech.cascade.*`** (top-level) |
| `srmech.amsc.{tool_schema, naming, responsion_schema, op_provenance, carrier_schema, _carrier_examples}` | **`srmech.introspect.*`** |
| `srmech.amsc.{genome, q8, plasmid}` | **`srmech.biology.*`** |
| `srmech.amsc.harmonics` | **`srmech.music.harmonics`** |
| `srmech.amsc.elliptic_partial_fraction` | **`srmech.apokatastasis.*`** |
| `srmech.amsc._native` | **`srmech._native`** (a package now) |
| `srmech.qm.*` | **`srmech.physics.qm.*`** — old spelling REMOVED at rc382, clean break |

**Do not reconstruct this table from memory or from the changelog.** Resolve the actual name: `get_tool_schema().resolve_all("<op>")` returns the fully-qualified path, or `srmech.introspect.search.search("<what you want>")` returns a `reach` line you can paste. Schema names are **fully qualified** — a bare-name lookup returns nothing and looks like a coverage gap that isn't one.

**Ops that exist but are NOT registered** (so `resolve` returns nothing and they are invisible to search) — verified rc432: `srmech.cascade.cayley_dickson.cd_add`, `srmech.cascade.one.separate_winding_curvature`, `srmech.rbs_lm.substrate.sim_k4_batch`. Import them directly; they work. Tracked on gh #1530.

### The 4D irrep is ADOPTED — as a `(frame, lane)` PERSPECTIVE, never as the carrier (F1338, 2026-08-14)

Per user direction *"adopt the 4D irrep now that the lane surface answers it, **but only as a perspective**"*. A carrier declares a **pair**, not a basis:

| field | range | what it selects |
|---|---|---|
| **frame** | 1..**28** = 7 Fano lines × 4 splitting units | which ℍ-in-𝕆 perspective the read is taken from (`octonion_frame_read(x, frame=(i,j,k,ℓ))`) |
| **lane** | `index` / `sign` / `both` | which half is read (`describe()["lanes"]`) |

Five measured consequences, all through shipped rc432 ops:

1. **The 4-cube is a READ-OUT, never the storage.** 28 frames give **28 distinct reads of the same octonion** and **one** invariant norm. Storing one frame's coordinates stores 1 of 28 equally valid answers.
2. **Only invariants carry a cross-perspective claim.** `cd_norm_sq` and φ survive a frame change; a base does not. "This strand *is* X" must be phrased in an invariant, or it is a claim about the frame.
3. **`ab:bc:ca || c:a:b` is an IDENTITY, not an analogy.** On **7/7** Fano lines the pair-product IS the complementary single up to a Class-K sign. **Naming any two names the third** — the third is implied, not stored. Storing all three of a Fano triple stores a redundancy.
4. **Index lane = unbounded shadow; sign lane = where every ceiling lives** (F1337). A carrier that stores only the index lane has stored the shadow — cheap, useful, and it must be **labelled as such**.
5. **An address is basepoint-relative.** In the seam torsor the label **SET** is invariant (always the whole group) but the **ASSIGNMENT** is a choice — every basepoint labels *itself* `0`. Two carriers may disagree on every label and be the same object; **test agreement on the invariant, never on the labels.**

**We never leave a tower rung, we nest it.** `Der(𝕊) = Der(𝕆) = g₂ = 14` — the 𝕊 rung adds no new symmetry; measured, `𝕊` is one 𝕆 that closes (49/49) plus one 𝕆-shaped coset that does not (64/64). srmech's own tier text: *"both are 𝕆 ⊕ 𝕆"*. ⚠️ The tie to a **triality generator** is **[SPECULATIVE]** and stays FORM-only — `triality_automorphism` is `τ³=I` on 𝔰𝔬(8), not a permutation of an octonion triple (notebook §3.46.11).

### Cascade-honesty discipline (load-bearing)

Per `[[feedback_sign_handling_is_class_k_pin_slot_not_alu_abs]]`:

- **NEVER use Python `abs()` inside a cascade script.** Sign-flip IS canonical **Class K pin-slot phase-boundary** per `[[user_stance_epicycle_via_gear_plus_pin]]`; sign-re-application is **Class C**.
- **As of srmech rc22+ these ship NATIVELY in `srmech.amsc.cascade.*` — prefer them over any hand-rolled fold:** `cascade.magnitude` (the **real** `|x|` pin-slot magnitude — the cascade-honest `abs()` replacement; **NOT** a complex `(re²+im²)^0.5` modulus, which it rejects with a clean Class-K contract error per UPSTREAM_NOTES §15.1/§18), `cascade.pin_slot_at_zero` (Class K), `cascade.reorient` / `cascade.chiral_flip` / `cascade.chiral_dual` / `cascade.net_chirality` (Class C), `cascade.best_rational_signed` (K+N), `cascade.cyclic_gcd` (I). The discipline-ratchet (`docs/srmech/rbs_lm_research/check_srmech_discipline.py`) now points `abs()` at `cascade.magnitude`.
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
- `[[feedback_paywalled_doi_cannot_be_attested]]` — paywalled-only DOI is REJECTED as framework attestation; use arXiv preprint / OA review / textbook attribution chain. **"Paywalled-only" is now a CLAIM THAT MUST BE EARNED — see the four-route sweep immediately below.**
- `[[feedback_computational_provenance_discipline]]` — load-bearing numerical results (p-values, effect sizes) MUST have generating code committed

### An unverified NEGATIVE is still an unverified claim — the four-route retrievability sweep (F1354; user direction 2026-08-15)

**The gap this closes.** The rules above govern *positive* claims about content ("this paper says X" — open it first) and said **nothing about negative claims about access** ("this paper cannot be opened"). That asymmetry is not theoretical: our own tracker ask said *"targeted attested research could not retrieve"* three CWF papers, srmech implemented it faithfully as *"paywalled-only or offline"*, and it shipped to **7 source surfaces including 4 occurrences in the compiled C registry** — reaching users through `describe()`, the MCP tool list and the C binary. **All three were retrievable; a sweep found every one on the first search.**

**Before writing that a source is unretrievable, run all four routes:**

| # | route | note |
|---|---|---|
| 1 | **publisher DOI** | a **403 here is bot-blocking, NOT evidence** — an automated client is not a reader |
| 2 | **PMC / PubMed Central** | free-to-read and OA-subset are **different questions**; `oa.fcgi?id=PMCxxxxx` answers the second |
| 3 | **search engine → the AUTHOR'S INSTITUTIONAL REPOSITORY** | **highest yield, and the one that worked 4/4. A HIT LIST IS NOT A SEARCH — OPEN the author/institution page, don't just note that one exists** (the 4th paper sat on a page that was already the top hit of an earlier query, unopened, while "unverified" was written beside it).** Pre-internet papers have no arXiv and a hostile publisher, **but the author had an employer, and employers retro-deposit faculty work** (Fuller→Caltech, White→Edinburgh archive, Călugăreanu→DML-CZ) |
| 4 | **Google Scholar / preprint servers / OA aggregators / national digital maths libraries** | DML-CZ, EuDML, EMIS and similar cover most pre-1990 European mathematics |

**Only after all four fail may a source be called unretrievable — and the claim must NAME WHICH ROUTES WERE TRIED.** "We couldn't get it" is a fact about the attempt, never about the source; write it that way or don't write it. **And never leave an unswept item sitting in a list beside confirmed ones** — placed there it reads as "unfindable", which is the same conflation one level down.

**⚠ RETRIEVABLE and REDISTRIBUTABLE are two questions — answer them separately.** Our attestation bar keys on **retrievability**, so a personal-use-only scan is perfectly attestable (URL + `response_sha256` + `retrieved_at` is the MPR record, and it is *stronger* than a secondary-review chain). But it is **not** an OA licence: **never write "OA" without checking, and never commit a retrieved PDF to the repo.** The original defect was exactly this conflation, made twice in opposite directions — one surface claimed "OA" (a false *licence* claim), another claimed "paywalled-only" (a false *retrievability* claim), about the same paper, in the same package.

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
- `[[feedback_read_independent_structure_check_first]]` (STANDARD FIRST TEST; user direction 2026-07-02) — when asking *"does operator/code/structure X have a genuine advantage?"*, run the **read-INDEPENDENT structural measurement FIRST** (X's intrinsic signature — cross-correlation/Gram + sidelobe, Laplacian eigenspectrum, orthogonality, circulant/Toeplitz check) *before* trusting a read-dependent recall/accuracy number. A recall metric is one projection through one read and *fluctuates*; F999–F1002 = 3 recall reads of the elliptic `−z⁻¹` code gave +0/+6/−2pp (noise), while the cross-correlation matrix settled it definitively (perfectly circulant = structure real; equal orthogonality = NO advantage; F1000's +6pp was noise; elliptic value is *generative* not recall). If the intrinsic measure shows no difference, don't ship the recall delta as an advantage. Composes `[[user_stance_no_information_without_value]]` (read ALL of X's coordinates, not one recall projection) + `[[feedback_dont_pre_commit_spike_query_operators]]`.
- **Noise rule / epistemic ceiling (F552; user direction 2026-06-07):** we will NEVER find "error of biology" in our model, and a person's mind is likely never exactly modelable — we can't control substrate chirality nor know the universe's unseen, always-asymptotic collapse drivers. **Our cascade models the EXACT IDEAL in FULL chirality; biology runs a chirality-COLLAPSED projection (fibrations down) — so the simulated story never matches the universe exactly, and that gap is NOT model-error and NOT random.** Therefore: **when a model↔biology deviation looks like "random noise", FIRST ask whether it is a biology SUBSTRATE FEATURE — the (4:3)|(3:4) chirality-dual.** It is testable (a chirality-collapse deviation carries a (4:3)|(3:4) sector-occupancy asymmetry random noise lacks — Class-K sector-count + the γ₅ chiral-dual check) and **diagnostic, not predictive** (recognise the feature; never claim to reproduce which-way/when it collapses → hand it to the expert, F282). Composes F526/F528 / F129/F130 / F51.

### Verify discipline — k=3 TRIALITY (haiku∥sonnet∥opus), no privileged model, the error-correcting form — **RUN VIA SUB-AGENTS (the Agent tool), never the Workflow tool** (STANDING for ALL research dives; user direction 2026-05-31 / 2026-06-01 / 2026-06-04 / **2026-06-06 (Workflow tool retired)** / **2026-06-07 (sub-agents are OK — the haiku∥sonnet∥opus sub-agent triality was working BEFORE the Workflow tool hijacked it; only the *Workflow tool* was retired, NOT sub-agents)**; rationale F248 / F291)

Every research dive runs the SAME task through **THREE agents — haiku + sonnet + opus** (identical prompt; the model tier is the ONLY variable), then **adversarially triangulates + merges by per-claim majority (2-of-3)** — never trusting one model's research. **Why no privileged model (F248):** the multi-model pass caught two hallucinated citations a single sonnet run would have shipped silently, AND showed the F242b honesty-gradient is **task-relative** (sonnet most honest on *rendering*; opus most honest/uncentered on *research*) — so **no model is the privileged "honest one."** **Why three and not two (F291):** an opus∥sonnet *pair* is a **k=2 parity check — it DETECTS disagreement but cannot error-CORRECT** (a 1-vs-1 split has no majority, so a human becomes the tie-breaker). The framework-native **k=3 TRIALITY = haiku + sonnet + opus** is the **Hurwitz k=3 error-correction rung** (ℍ/SU(2)/triality, the same 1:3:7 ladder the loop bind's k=7 sits on; the user's "haiku/sonnet/opus truth detection") — each tier independently re-runs + checks, and **majority (2-of-3) corrects with no human tie-break.** **Live proof (F291):** the old 2-model pass caught the L2 + L5 over-claims but **missed** L4's boundary-digit drift; k=3 triality caught it **unanimously**. **How it is run — VIA PLAIN SUB-AGENTS (the Agent tool: one haiku + one sonnet + one opus on the IDENTICAL prompt), NOT the Workflow tool (user direction 2026-06-06; clarified 2026-06-07).** The Anthropic **Workflow feature is RETIRED here — but SUB-AGENTS ARE NOT.** The haiku∥sonnet∥opus sub-agent triality was *working before* the Workflow tool, and the plain Agent-tool spawn is the mechanism we use. What the **Workflow tool** did wrong was *hijack the "triality" lexicon-slot the way `Counter()` hijacks "co-occurrence"* (the §2 reflex-override pattern, one layer up): it re-skinned the framework's own k=3 as an **Anthropic structured task** (`meta.phases` / `StructuredOutput` scaffolding — and the `StructuredOutput` call was itself the recurring failure point). So the ban is on the **Workflow tool**, not on spawning model-tier agents. **Triality is a discipline we APPLY via plain sub-agents, not a feature we INVOKE:** spawn the three tiers on the same task, have each **web-verify** (real author + title + venue + year + DOI/URL; a paywalled-only DOI is rejected → route to the OA copy), then **merge by per-claim 2-of-3 majority**; for a numeric re-verify, re-run the committed scripts and check the lodged numbers. (A lighter web-verify inline in the main context is fine when a full three-tier spawn isn't warranted — e.g. a single citation or a framework build verified by running its script.) **⛔ HARD RULE — do NOT spawn sub-agents while the `sonnet`-alias bug is live (user direction 2026-06-07, after a `sonnet[1M]` sub-agent DRAINED ALL usage credits in one run).** This is a **NEW resolution bug, NOT context inheritance** (user-corrected: a sub-agent never pulled in the parent's context window). **Before a recent update, `model: 'sonnet'` correctly resolved to the 200k-context sonnet; now the short alias resolves to `sonnet[1M]`** (the expensive 1M variant) — *that* is what steals the credits. **We never asked for `sonnet[1M]` — we wanted regular (200k) sonnet.** The intended fix is to pass the **full Model-API long name** (e.g. the dated `claude-sonnet-4-…` 200k id) instead of the short alias — **BUT the Agent tool's `model` parameter is a fixed enum (`sonnet`/`opus`/`haiku`) and will NOT accept a long API name**, so there is currently **no tool-level way to pin the 200k variant.** Therefore, until the alias resolves to 200k again (or the Agent tool accepts a long API name): **do the triality web-verify INLINE in the main context (the lighter path above) — do NOT spawn sub-agents at all.** The discipline (haiku∥sonnet∥opus, 2-of-3 majority, no-privileged-model) is unchanged — but **not via the buggy alias, ever.** **Empirically confirmed 2026-06-07:** switching the parent window OFF 1M did **NOT** fix it — a freshly spawned `sonnet` sub-agent STILL errored "Usage credits required for 1M context" **at 0 tokens**, so the broken resolution is in the **sub-agent `sonnet` alias itself, independent of the parent window.** (Silver lining: the 0-token error means a *retry costs nothing* — it fails before running — but it never succeeds, so don't bother; complete the triality's third tier INLINE.) The per-claim **2-of-3 majority** and the *no-privileged-model* discipline are unchanged — they are the math, not the tool. Compose with the MPM citation discipline + `[[feedback_no_privileged_primitive_classes]]` + the no-leaning rule above. (The committed `docs/srmech/rbs_lm_research/research_triality_workflow.js` is left as a **historical artifact of the dives run under it (the F291–F445-era attestations), NOT the engine**; the bundled `deep-research` skill remains for single-model multi-angle sweeps.)

**The retired k=2 `research-twin` (removed 2026-06-04, user direction "research triality, not twin. remove research-twin"):** triality supersedes it — k=2 only detects, k=3 corrects, so there is no longer a separate "quick twin detect pass." Historical findings that cite `research-twin` (F240c…F378) are left as the attestation record of dives run under the old k=2 engine; **new dives apply triality via plain sub-agents (haiku∥sonnet∥opus, the Agent tool) — or a lighter inline web-verify — never the Workflow tool.**

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
