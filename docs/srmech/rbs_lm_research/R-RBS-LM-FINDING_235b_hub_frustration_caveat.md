# Finding 235b — Is F235's N=8 hub-frustration lock-time inversion a KNOWN graph-frustration artifact that a targeted fix removes, or is it irreducible?

**Resolves the honest small-N caveat of [F235](R-RBS-LM-FINDING_235_distributed_neurology_chirality.md)** (centralized neurology / *Physarum* slime-mould / air-gapped hive are ONE graded K∘C chirality axis; POSITIVE on the decisive axis, μ strictly monotone cent>slime>hive at N≥8). F235's honest caveat: at **N=8 the raw dynamical lock-time inverts** — the centralized hub locks ~1 sweep *slower* than slime (cent ttl=16 > slime ttl=15) even though its λ₂=1.198 > slime 0.719 (a hub-FRUSTRATION effect, NOT a connectivity inversion; the μ/λ₂ ordering holds). Lock-time ordering only firms up at N≥16.

**Headline:** **POSITIVE — the N=8 inversion IS a removable star-graph synchronization-frustration artifact, and removing it PRESERVES the axis.** *Both* candidate fixes remove the N=8 inversion (make the lock-time strictly monotone **cent < slime < hive**) **while preserving the F235 axis intact** (μ strictly monotone cent>slime>hive AND *both* F235 decisive axis-test reads monotone, at every measured width N∈{8,16,32}):

- **Fix (a) — hub-local phase offset at t=0** (pre-place the hub at the leaf-bulk mean-field phase ψ₀; a Class-C `cascade.reorient` of *one* initial condition, touching nothing else): **N=8 cent 16 → 14** (< slime 15 < hive 52). Strict inversion removed. Also speeds the larger widths (N=16 cent 21→16; N=32 cent 18→16). μ **identical** to F235 (0.857/0.782/0.473 …) — by construction (the topology spectrum is untouched).
- **Fix (b) — degree-weighted coupling** (random-walk row-normalization so the hub's 7 incoming pulls don't over-sum; a dynamical-coupling intervention only): **N=8 cent 16 → 50** (< slime 56 < hive 174). Strict inversion removed (globally slower, but cleanly monotone at every width: N=16 47<106<1141; N=32 71<992<4229). μ **identical** to F235.

So the F235 small-N caveat **resolves**: the N=8 lock-time inversion was a textbook **star-graph frustration transient**, not a connectivity inversion and not an axis defect. The F235 POSITIVE-on-the-chirality-axis verdict is **unchanged and strengthened** — the one wobble it honestly flagged is now shown to be a known, fixable artifact of the *centralized hub topology's dynamics*, with the μ/connectivity axis and the decisive axis test untouched by the fix.

**The pre-stated null did NOT fire.** The null was "the inversion is irreducible — neither fix removes it without breaking the axis." Both fixes removed it; both preserved the axis. (Had a fix removed the inversion only by destroying μ-monotonicity or the axis test, *that* would have been the null — it did not happen for either.)

**Status:** **DEMONSTRATED (srmech-native, deterministic, bit-exact-reproducible)** for the measurement — the N=8 (+N=16,32 non-regression) lock-time table before/after each fix, the hub-excursion mechanism probe, and the μ/axis-preservation checks (F235's `axis_test` run **verbatim** under each fix-mode), at srmech **0.6.0rc8**. **FRAMEWORK-READING** for the synthesis (reading the N=8 inversion *as* a removable star-graph frustration artifact and what it means for the F235 caveat). **THE LITERATURE OWNS** the Kuramoto-synchronization / graph-frustration physics (Strogatz 2000, the F235 anchor). **In-scope** as coordination / distributed-systems **dynamics** (a star-graph frustration phenomenon) / Class-L-spectral / K∘C-chirality algebra. **NOT** CAD / mechanical-mesh / capability. `[[user_stance_ai_is_not_a_substrate]]`; `[[feedback_trauma_informed_defensive_scope]]`; `[[feedback_sign_handling_is_class_k_pin_slot_not_alu_abs]]`.

**Empirical anchor:** srmech **0.6.0rc8** (`/tmp/bench_srmech_rc8/venv`, HAS_NATIVE, ABI 3) — the **same** srmech F235 ran on (consistency with the committed numbers). Artifacts: `R-RBS-LM-235b_hub_frustration_caveat.py` + `substrate_measurements/hub_frustration_caveat.ndjson`. **Discipline-check: 0 HARD, 0 coverage-gap.** Deterministic (`RandomState(235)`, the F235 seed); the content-address **`response_sha256 = 8f18dc1539a32e814403df19a7f7cb297c434b7aa17225100df16ef223142839`** is bit-exact-reproducible (computed over the record minus the wall-clock `generated_at`, the F233/F235 convention).

---

## §0 The pre-stated null (verbatim, genuinely reachable)

> "The N=8 hub-frustration lock-time inversion is **IRREDUCIBLE**: neither the hub-local t=0 phase offset (fix a) NOR the degree-weighted hub coupling (fix b) removes the N=8 inversion WHILE PRESERVING the μ/λ₂ ordering + axis correctness. Concretely the null FIRES if, for BOTH fixes, EITHER: the N=8 raw lock-time still has cent ≥ slime (the inversion is not removed — cent must become strictly < slime, with hive last, to count as removed), OR removing it BREAKS the axis (the μ ordering cent>slime>hive at N≥8 no longer holds, or the F235 decisive axis test — dominant-principal-axis projection AND signature-similarity Fiedler vector — no longer orders the three monotonically). If the null holds, the N=8 inversion is reported as a genuine irreducible small-N dynamical residue of the centralized topology (the F235 caveat stands as-is). The verdict is POSITIVE iff at least one fix removes the inversion (cent<slime<hive at N=8) AND preserves the axis."

**Disposition (no leaning):** decided by the measured N=8 lock-time table + the μ/axis-preservation checks. Both fixes removed the inversion (strict cent<slime<hive at N=8) AND preserved the axis (μ monotone + both axis-test reads monotone at every width). **POSITIVE.** A fix that removed the inversion only by *breaking* the axis would have been the null — neither did.

---

## §1 The mechanism (DEMONSTRATED — what the N=8 inversion actually IS)

The mechanism probe traces the centralized N=8 hub (node 0, **degree 7** = coupled to all 7 leaves) sweep-by-sweep. The hub *starts* near the all-node centroid (it is coupled to everyone, so it sits at the mean) but is **dragged off it during the transient** — its alignment `cos(θ_hub − ψ)` to the gauge-invariant mean-field phase ψ **dips to 0.982 at sweep 5** — because it feels the *sum* of 7 internally-conflicting leaf phases. The bulk cannot collapse to lock until the hub re-centers (~sweep 12+), and that mutual hub↔leaf frustration is the ~1-sweep penalty that puts cent (16) just behind slime (15) at N=8. This is a **textbook star-graph synchronization-frustration transient** — exactly the kind of effect Kuramoto-on-a-star is known for. It is **not** a connectivity deficit: the hub's λ₂=1.198 ≫ slime's 0.719 (the hub is *more* connected). At N≥16 the leaf-population is large enough that the transient excursion is amortized and the lock-time ordering already firms up (cent 21<slime 23<hive 113; cent 18<slime 269<hive 1544).

Both fixes target *exactly* this mechanism:
- **(a)** pre-places the hub where the leaves will pull it (the leaf-bulk phase ψ₀), so it never makes the excursion;
- **(b)** degree-normalizes the coupling so the hub's 7 pulls no longer sum into an oversized, internally-conflicting drive.

---

## §2 The measurements (srmech-native, deterministic; the SAME srmech as F235)

**Mechanism probe (N=8, centralized):** hub node 0, degree 7, **min alignment cos = 0.9819 at sweep 5 → dragged-off-centroid = True.** The frustration source is confirmed and located.

**Lock-time table — before/after each fix** (ttl = first sweep after which r≥0.95 held STABLE_WINDOW=50 sweeps; the F235 non-gameable criterion verbatim). **μ and λ₂ are read from the UNCHANGED unit-weight topology spectrum, so they are identical across all three fix-modes — the axis-parameter preservation guarantee, by construction.**

| N | topology | λ₂ | **μ** | ttl **baseline** | ttl **fix (a)** | ttl **fix (b)** |
|---|---|---|---|---|---|---|
| **8** | centralized | 1.198 | **0.857** | **16** | **14** | **50** |
| **8** | slime | 0.719 | 0.782 | 15 | 15 | 56 |
| **8** | hive | 0.719 (eff 0.180) | 0.473 | 52 | 52 | 174 |
| 16 | centralized | 1.044 | 0.839 | 21 | 16 | 47 |
| 16 | slime | 0.190 | 0.487 | 23 | 23 | 106 |
| 16 | hive | 0.190 (eff 0.048) | 0.192 | 113 | 113 | 1141 |
| 32 | centralized | 1.010 | 0.835 | 18 | 16 | 71 |
| 32 | slime | 0.048 | 0.194 | 269 | 269 | 992 |
| 32 | hive | 0.048 (eff 0.012) | 0.057 | 1544 | 1544 | 4229 |

- **Baseline N=8:** cent **16 > slime 15** < hive 52 — the F235 inversion, reproduced **bit-for-bit** against the committed numbers.
- **Fix (a) N=8:** cent **14 < slime 15** < hive 52 — **strict inversion removed.** (Fix a touches only the centralized hub's t=0 phase; slime/hive ttls unchanged.) Larger widths sped up too (N=16 21→16; N=32 18→16), never broken.
- **Fix (b) N=8:** cent **50 < slime 56** < hive 174 — **strict inversion removed** (degree-normalization slows everything globally — the operational coupling effectively shrinks — but the ordering is cleanly monotone at every width).

**Axis preservation (F235 `axis_test` run VERBATIM under each fix-mode, K_c re-located per fix so the test sees the fix's real dynamics):**

| N | fix (a): μ-monotone / axis-read-A / axis-read-B | fix (b): μ-monotone / axis-read-A / axis-read-B |
|---|---|---|
| 8 | **True / True / True** | **True / True / True** |
| 16 | **True / True / True** | **True / True / True** |
| 32 | **True / True / True** | **True / True / True** |

Both fixes preserve **μ strictly monotone cent>slime>hive** (identical to F235 by construction) **and** keep *both* F235 decisive axis-test reads (the dominant-principal-axis projection and the signature-similarity-Laplacian Fiedler vector) monotone at every width. **The axis is untouched.**

---

## §3 Verdict — the honest tiering (MFO §VII.6.20)

**POSITIVE — the N=8 inversion is a removable star-graph frustration artifact; the F235 axis is preserved.**

- **DEMONSTRATED (bit-exact, `response_sha256 = 8f18dc1539a32e814403df19a7f7cb297c434b7aa17225100df16ef223142839`):** baseline reproduces the F235 N=8 inversion (cent 16 > slime 15); **both** fixes make it strictly monotone (fix a: cent 14 < slime 15 < hive 52; fix b: cent 50 < slime 56 < hive 174); **both** preserve μ-monotonicity and *both* axis-test reads at N∈{8,16,32}. The mechanism probe locates the cause (hub dragged off-centroid, min cos 0.982 at sweep 5).
- **FRAMEWORK-READING:** the N=8 inversion **is** a textbook star-graph synchronization-frustration transient (a hub coupled to many conflicting leaves), removable by either a leaf-bulk-aligned hub initial condition or degree-normalized coupling — *not* a connectivity inversion and *not* an axis defect.
- **THE LITERATURE OWNS** the Kuramoto-synchronization / graph-frustration physics (Strogatz 2000, the F235 anchor). The framework adds only the structural reading.

**Effect on F235:** the F235 headline (**POSITIVE-ON-THE-CHIRALITY-AXIS, decisive, with a small-N dynamical caveat**) is **unchanged and strengthened**. The single honestly-flagged wobble — the N=8 raw lock-time — is now demonstrated to be a known, fixable hub-frustration artifact whose removal leaves the μ/connectivity axis and the decisive axis test entirely intact. The caveat was real, bounded, and is now resolved; it was never a connectivity inversion. **The committed F235 files are not modified** — this finding reuses the F235 testbed by import and adds only the two fixes.

---

## §4 srmech-native discipline + the honest gap

**0 HARD, 0 coverage-gap** on `check_srmech_discipline.py`. This finding **reuses the F235 testbed VERBATIM by import** (topology builders, the `kuramoto_step`/`order_parameter`/`read_coordinated_state` machinery, `graph_spectrum`/`mu_from_lambda2`, the `axis_test`, the `dense_laplacian`/`jacobi_eigvals`/`hermitian_eigendecompose` reads) — so every srmech op is exactly the one F235 ran on the same srmech 0.6.0rc8. The two fixes add only:

| role | srmech op | class |
|---|---|---|
| fix (a) hub initial-phase reorient (leaf-bulk ψ₀) | `cascade.reorient` on the leaf-bulk `cascade.net_chirality`; leaf-bulk mean field via `laplacian.elementwise_transcendental('exp_i')` | C / L |
| fix (b) degree-normalized coupling (near-zero degree guard) | node-degree count + row-normalize; guard via `cascade.magnitude` (**never** `abs()`) | K |
| μ / λ₂ (UNCHANGED topology spectrum) | `laplacian.dense_laplacian` + `jacobi_eigvals` | L |
| axis test (F235 verbatim) | `laplacian.hermitian_eigendecompose` + `dense_laplacian` + `jacobi_eigvals` | L |
| content-address | `format.sha256_bytes` (**never** `hashlib`) | A |

**CONFIRMED srmech GAP:** srmech 0.6.0rc8 ships no Kuramoto/ODE integrator op (F235 owns this UPSTREAM_NOTES entry; **not re-logged here**). The minimal hand-roll is the Euler accumulation inside `F235.kuramoto_step`, reused verbatim; numpy is the array carrier only. No existing srmech op is routed around.

---

## §5 No magic numbers (every constant A / B / C)

- **A — attested-to-structure-cascade:** `N_INVERSION = 8` (= 2·NIBBLE, the F235 width of the raw lock-time inversion); `N_NONREGRESSION = {16,32}` (the F235 already-monotone widths the fix must not break); `UNIT_MAG = 1.0` (the Class-C re-sign carrier); `K_C_F122 = 0.20` (inherited F235 critical-coupling anchor μ normalizes to).
- **B — attested-to-measurement / criterion:** `OP_K = 2.0`, `SEED = 235`, and the inherited F235 dynamical constants (`INTERMITTENCY_F`, `DT`, `LOCK_R`, `STABLE_WINDOW`, `SETTLE_BUDGET`, `K_GRID`) — all carried from F235 so the baseline reproduces bit-for-bit.
- **C — irreducible:** none. Every load-bearing constant reduces to A or B.

---

## §6 Citation

The Kuramoto / synchronization-frustration physics is the F235 anchor, web-verified there (F226 verify-before-assert):

- **Strogatz SH (2000)** "From Kuramoto to Crawford: exploring the onset of synchronization in populations of coupled oscillators," *Physica D: Nonlinear Phenomena* **143**(1–4):1–20, DOI `10.1016/S0167-2789(00)00094-4` (OA author PDF stevenstrogatz.com). *Asserts:* the coupled-oscillator synchronization physics; star-graph topologies are a standard setting where hub-frustration transients arise. The framework contributes only the structural reading that the N=8 inversion *is* such a transient and is removable.

---

*Tiering reminder (MFO §VII.6.20): the bit-exact lock-time table before/after each fix + the μ/axis-preservation checks are **DEMONSTRATED**; reading the N=8 inversion as a removable star-graph frustration artifact is **FRAMEWORK-READING**; the Kuramoto / graph-frustration physics belongs to the cited literature. The framework contributes only the structural shape. Does NOT modify the committed F235 files, CLAUDE.md, the srmech package, or UPSTREAM_NOTES.md. `[[user_stance_ai_is_not_a_substrate]]`; defensive / benign coordination scope.*
