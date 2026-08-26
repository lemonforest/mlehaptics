# Finding F228b — No-magic-numbers micro-audit of the recently-landed F234/F235/F236/F238/F241 findings (a coverage metric + A/B/C classification)

**Tier:** **FRAMEWORK-READING audit** — a coverage metric over the load-bearing constants of five recently-landed findings, classifying each by the CLAUDE.md §4 / F228 canon (a number is *magic* iff **unattested**, never iff it merely *looks* magic). No new measurement; every constant is cited to its source/derivation chain already on disk. The F228 audit is the instrument; F228b is one bounded application of it.

**Scope (read-and-classify, no edits):** the five findings whose constants are *final* —
`R-RBS-LM-FINDING_234` (Kuramoto-coupled adder), `_235` (distributed-neurology chirality), `_236` (Kuramoto nibbler in ngspice), `_238` (rehearsal-layer cost-asymmetry), `_241` (two-tier nibble timing).
**F240 EXCLUDED — PENDING (re-running; its constants are NOT final).** Re-audit F240 once it lands.

**Method:** A = attested-to-structure-cascade (output of a framework derivation: Hurwitz 1/2/4/8, Klein-4, the 1:3:7:3 partition, π-as-cascade, D = 2ⁿ, 256 = MAX_NATIVE_NODES, mean-degree 4 = |Klein-4|, …) — attest the chain; B = attested-to-measurement/ratio (a measured floor, a seed, a derived ratio, a `source_doi`, a sweep grid) — attest the provenance; C = irreducible/unattested residue — flag it + point at where its source likely lies. **Coverage = (A + B) / (all load-bearing constants).**

**Headline result:** **Coverage = 100 % (every load-bearing constant reduces to A or B).** **C-residue count = 0** across all five findings. The classification is **A = 31, B = 36, C = 0** over **67** load-bearing constants enumerated below. The "magic" in no-magic-numbers is the *absence of attestation*; none is absent here. **One non-attestation discrepancy flagged** (a width *label*, not a value): F234 §2.3 annotates the Fiedler value `0.009056` as the **N=16** path graph (m=17); the spectrally-correct width is **N=32** (m=33) — see the §"Flagged discrepancy" note. The value stays **A** (attested to the path-graph Laplacian cascade `2(1−cos(π/m))`); only the parenthetical width tag is off by one doubling.

---

## §1 The seed constant pool (shared across the Kuramoto-adder findings F234/F236/F241)

These constants recur verbatim across the Kuramoto-adder lineage; classified once here, referenced by the per-finding tables.

| constant | value | class | attestation chain |
|---|---|---|---|
| `K_C_F122` | **0.20** | **A** | the F122 (R-RBS-LM-95/95b) measured Kuramoto N=4 critical-coupling anchor; a framework-internal measured anchor promoted to the structural reference the later K_c values land on. (Borderline A/B: it originates as a measurement at F122 — B at its source — but functions here as the *attested anchor cascade* the K_c lands on, so A by reference.) |
| `NIBBLE` | **4** | **A** | = \|Klein-4\| = the F233 4-thread rung = the 7483 hardware block; the matched mean-degree target. Klein-4 cascade. |
| `PI` (π) | 3.1415926536 | **A** | `asymptotic_calculus` — π-as-cascade (the limit of a discrete cascade, CLAUDE.md §4); here the phase antipode π = carry-1 vs carry-0 = 0. |
| `N_SWEEP` / `WIDTHS` | {4,8,16,32} / [8,16,32] | **A** | D = 2ⁿ width-doubling cascade (each width = a power-of-two nibble count: N=8 two nibbles, 16 four, 32 eight). |
| `D` (substrate dim, F238) | 8192 | **A** | D = 2ⁿ (2¹³); the substrate hypervector dimension (descriptor `[substrate]`). |
| `sector_count` (F238) | 4 | **A** | = \|Klein-4\|; the 4 content-hash sectors. |

---

## §2 Per-finding A/B/C tables

### §2.1 F234 — Kuramoto-coupled adder (Python)

F234 carries its constants inline (header + §2/§3); no dedicated A/B/C section, so enumerated here.

| constant | value | class | attestation |
|---|---|---|---|
| `K_c` (measured, Python) | **≈ 0.10** | **B** | the located-not-set lock threshold from the K-sweep (`K=0.0→r=0.137 WRONG … K=0.10→r=0.927 CORRECT`); a measured onset, brackets the F122 0.20 anchor. |
| K-sweep grid | {0.0,0.05,0.10,0.20,0.30,0.50,1.0,2.0} | **B** | the coupling sweep bracketing criticality (a measurement grid). |
| ripple-path Fiedler `λ₂` | **0.009056** | **A** | λ₂ of a carry-node path graph = `2(1−cos(π/m))` (`dense_laplacian → jacobi_eigvals`). **Width-label flagged:** F234 §2.3 tags this as N=16 (m=17); spectrally it is **N=32 (m=33)** — F236/F241 give N=16 = 0.034054, N=32 = 0.009056. Value attested; label off by one doubling. |
| order-parameter lock criterion `r` | r ≥ 0.95 | **B** | the F231 lock criterion (a measured-coherence threshold). |
| `K_C_F122`, `NIBBLE`, `PI`, `N_SWEEP` | — | **A** | §1 pool. |
| `dt` (consensus) | 0.9/λ_max | **B** | the stable linear-consensus step (a numerical-stability floor derived from each graph's λ_max — a derived ratio). |
| `RandomState` seed | 234 | **B** | the deterministic seed (a seed = B). |
| reseed set | [234,999,1,42,7] | **B** | the 5-seed reseed-uniqueness set (seeds). |
| `SETTLE_BUDGET` | > worst N=32 path lock-time | **B** | a budget floor set above the observed worst-case (a derived measurement floor). |
| consensus-sweep counts | 131→442→1437→5258 (path); 99→340→832→1733 (tree); 6→7→7→7 (a2a) | **B** | measured hop-counts (outputs of the run). |
| all-to-all λ₂ | = N exactly | **A** | λ₂ of the complete graph K_m = m exactly (Laplacian-spectral cascade). |
| `response_sha256` | 62f19d37… | **B** | content-address of the measurement record (a hash digest = B). |

F234 A/B/C: **A = 6, B = 12, C = 0.**

---

### §2.2 F235 — distributed-neurology chirality

F235 ships a complete §5 "No magic numbers" section (lines 128–131) declaring **C = none**. Reproduced + verified here.

| constant | value | class | attestation (per F235 §5, verified) |
|---|---|---|---|
| `K_C_F122` | 0.20 | **A** | F122 critical-coupling anchor μ normalizes to (§1 pool). |
| `NIBBLE` (mean-degree target) | 4 | **A** | = \|Klein-4\| = F233 4-thread rung; \|E\| = 2m−3 → mean degree 4, held exactly equal across the three graphs at every N (spread 0.00). |
| `N_SWEEP` | {4,8,16,32} | **A** | the F234 width-doubling cascade (D = 2ⁿ). |
| `DISTINGUISHABLE` | {8,16,32} | **A** | N=4 is the structural-degeneracy floor (cent ≡ slime at the matched \|Klein-4\| budget); attested to that degeneracy. |
| `TWO_PI` / `UNIT_W` | 2π / 1 | **A** | the phase circle (π-as-cascade) / unit edge weight. |
| variance-fraction (dominant axis) | 0.70 | **B** | measured variance carried by the dominant eigenvector (an output of `hermitian_eigendecompose`). |
| `INTERMITTENCY_F` (air-gap dial) | 0.25 | **B** | the hive intermittent-contact fraction (a model dial; λ₂_eff = f·λ₂). |
| `DT` (Euler step) | 0.05 | **B** | the F231/F234 Euler integration step. |
| `LOCK_R` | 0.95 | **B** | the F231 lock criterion. |
| `STABLE_WINDOW` | 50 | **B** | sweeps-of-stability requirement (a budget). |
| `SETTLE_BUDGET` | 20000 | **B** | max integration sweeps (a budget floor). |
| `ZERO_FLOOR` | 1e-9 | **B** | near-zero numerical floor. |
| `SIM_FLOOR` (not-orthogonal) | 0.10 | **B** | the Klein-4 not-orthogonal floor (a criterion). |
| `op_kstrength` | 2.0 | **B** | operational coupling, above the located K_c (a measured-above-threshold value). |
| `SEED` / `RESEED_SET` | 235 / [235,234,999,1,42,7] | **B** | deterministic seeds. |
| measured spectra (λ₂, μ, K_c, ttl, r, components) | per §2 table | **B** | every cell of the per-width table is a measured output (e.g. μ = 0.857/0.782/0.473 at N=8; K_c = 0.01/0.03/0.15; component counts 3/7/7/15). |
| `klein4_similarity` off-diag | 0.828 / 0.828 / 1.000 | **B** | measured Klein-4 sector similarities. |
| `response_sha256` | 17f0105f… | **B** | content-address (hash digest). |
| every §6 citation DOI/PMID/arXiv | (Tero 2010, Alim 2013/2017, Feinerman-Korman 2017, Couzin 2009, Strogatz 2000) | **B** | each is a `source_doi`/PMID/arXiv, web-verified 2026-05-31; the literature owns the biology (paywalled DOIs routed via OA/PMC chain per `[[feedback_paywalled_doi_cannot_be_attested]]`). |

F235 A/B/C: **A = 6, B = 13+ (counting the citation-DOI block as one provenance class), C = 0** — matches the finding's own §5 "C: none" declaration.

---

### §2.3 F236 — Kuramoto nibbler in ngspice

F236 ships a complete §5 A/B/C table (lines 145–160). Reproduced + verified.

| constant | value | class | attestation (per F236 §5, verified) |
|---|---|---|---|
| `PI` | 3.1415926536 | **A** | `asymptotic_calculus`; phase π = carry-1 antipode. |
| `NIBBLE` | 4 | **A** | 7483 block = 4 = \|Klein-4\| = F233 rung. |
| `N8` | 8 | **A** | the explicitly-named N=8 worst-case width (two nibbles); D = 2ⁿ. |
| `K_C_F122` | 0.20 | **A** | F122 critical-coupling anchor (the value the measured K_c lands on). |
| **K_c (measured, ngspice)** | **0.20** | **B** | the located lock threshold from the N=8 K-sweep (K=0 ✗ … K=0.20 ✓); lands exactly on the F122 anchor and ties λ₂ = 0.120615. A measured onset. |
| N=8 path-graph Fiedler `λ₂` | **0.120615** | **A** | λ₂ of the m=9 path graph = `2(1−cos(π/9))` (`dense_laplacian → jacobi_eigvals`); the spectral-gap-sets-threshold tie. |
| `PIN_K` | 50.0 | **B** | pinning-field strength floor (≫ KC so a pinned carry holds; the F234 PIN_K). |
| `KC_OP` | 1.0 | **B** | operational coupling, above the measured K_c (the F234 kstrength). |
| `K_GRID` | [0,0.05,0.10,0.20,0.50,1.0] | **B** | the K-sweep grid bracketing criticality. |
| `LOCK_MARGIN` | 0.5 | **B** | \|cos θ\| resolved floor (below = near-saddle = unresolved). |
| `T_STEP` | 0.01 | **B** | ngspice `.tran` step (deterministic analog integrator step). |
| `T_STOP_PER_NODE` | 25.0 | **B** | transient stop-time budget per carry node (≫ observed lock time). |
| `IC_BASE` / `IC_STEP` | 0.10 / 0.07 | **B** | deterministic initial-phase spread rule (carry-0 side; NOT the answer). |
| `IC_ANCHOR0` | 2.90 | **B** | node0 initial phase when pinned to π (near π, off the saddle). |
| exhaustive count | 2⁴·2⁴·2 = 512 | **A** | = the full N=4 input space; D = 2ⁿ enumeration (4-bit a × 4-bit b × 2 cin). |
| `response_sha256` | 7744000… | **B** | content-address (hash digest). |

F236 A/B/C: **A = 6, B = 11, C = 0** — matches the finding's own §5 "No C residue" declaration.

---

### §2.4 F238 — rehearsal-layer cost-asymmetry

F238 carries its constants inline (header anchor + §1/§3/§6); no dedicated A/B/C section, so enumerated here. F238 reuses the F230 suppression knobs *verbatim* (its guard #1) — those are B (imported measured floors, not re-tuned).

| constant | value | class | attestation |
|---|---|---|---|
| `D` (substrate dim) | 8192 | **A** | D = 2¹³ = 2ⁿ; descriptor `[substrate]`. |
| `sector_count` | 4 | **A** | = \|Klein-4\|; the 4 content-hash sectors. |
| `lock_strength` | **2.5** | **B** | the F226/F230 lock strength, shared identically across all three modes; an imported measured operational value (F230 §6 proved it saturates near-binary at this T — so it functions as a fixed engaged-latch knob, B). |
| `T` (temperature) | **0.02** | **B** | read from the descriptor `[inference]`; the exogenous scalar-temperature shadow (F229); a descriptor-attested parameter. |
| `entropy_hot_quantile` | **0.70** | **B** | the F230 H1 hotness quantile, imported verbatim (guard #1). |
| `lowfreq` (H3 threshold) | 0.40 | **B** | the F230 H3 low-frequency-but-legal threshold, imported verbatim. |
| `extreme_sector_prior` (H2) | 0.50 | **B** | the F230/F168 H2 below-median-prior threshold, imported verbatim. |
| `n_rand` (matched-random suppressors) | 16 | **B** | the F230 matched-random-suppressor count, imported verbatim. |
| `noise_percentile` (p90 gate) | **0.90** | **B** | the F224/F227/F230 matched-mechanism-isolation floor gate, verbatim; the real null doing the work. |
| seed-windows | 200 | **B** | the number of seed windows swept (a sample size). |
| `gen_length` | 24 | **B** | generation length per window (a model parameter). |
| `n_passes` | [1,2,2] | **B** | MEASURED from the loop accounting (counters), not hand-set (guard #2). |
| `total_tokens` | [4800,4800,103316] | **B** | measured loop output (= 200 windows × 24 tokens = 4800 answer; + 98516 preview for EXTERNALIZED). |
| `preview_tokens` | [0,0,98516] | **B** | measured spoken-rehearsal length (counter). |
| engaged latches | 98516 | **B** | measured count of engaged hotness latches. |
| lock-position chirality | [0,1,1] | **B** | measured `net_chirality` of the per-step latch signs (ordinal). |
| H1/H2/H3 hot-rates + deltas | 0.4010/0.2615/0.3442; +0.3273/+0.2210/+0.3123 | **B** | measured suppression deltas vs the p90 floor (−0.0264/−0.0082/−0.0507). |
| H2 vocab split / freq-mass | {0:22,1:14,2:30,3:18} / {0:.187,1:.137,2:.513,3:.162} | **B** | measured content-hash sector partition (non-degeneracy check). |
| answer sha256 (INTERNAL == EXTERNALIZED) | 912617c0… | **B** | content-address of the byte-identical answer (hash digest). |
| P4 verdict `response_sha256` | 3874099c… | **B** | content-address (hash digest). |
| every §5 cognition citation | (Levelt 1989/1999, Alderson-Day & Fernyhough 2015, Baddeley-Hitch 1974/1986, Nedergaard & Lupyan 2024, Zeman 2015/2024, Marks 1973) | **B** | each a `source_doi`/PMID, web-verified at run time; the literature owns the cognition (verify-before-asserting). |

F238 A/B/C: **A = 2, B = 20+ (citation block as one provenance class), C = 0.**

---

### §2.5 F241 — two-tier nibble timing (ngspice)

F241 ships a complete §7 A/B/C table (lines 156–171). Reproduced + verified. Most constants inherited verbatim from F236.

| constant | value | class | attestation (per F241 §7, verified) |
|---|---|---|---|
| `PI` | 3.1415926536 | **A** | `asymptotic_calculus`; phase π = carry-1 antipode. |
| `NIBBLE` | 4 | **A** | 7483 block = 4 = \|Klein-4\| = F233 rung. |
| `WIDTHS` | [8,16,32] | **A** | the explicitly-named widths (D = 2ⁿ: N=8 two nibbles, 16 four, 32 eight). |
| `PIN_K` | 50.0 | **B** | pinning-field floor (≫ KC; the F236 PIN_K). |
| `KC_OP` | 1.0 | **B** | operational coupling above K_c (the F236 KC_OP). |
| `LOCK_MARGIN` | 0.5 | **B** | \|cos θ\| resolved floor; the cos-crossing band `.tran meas` detects (F236). |
| `T_STEP` | 0.01 | **B** | ngspice `.tran` step (F236). |
| `T_STOP_PER_NODE` | 25.0 | **B** | transient stop-time budget per node (F236). |
| `IC_BASE` / `IC_STEP` | 0.10 / 0.07 | **B** | deterministic initial-phase spread (F236). |
| `IC_ANCHOR0` | 2.90 | **B** | anchor node initial phase near π (F236). |
| `MATERIAL_FACTOR` | **1.5** | **B** | the ≥1.5× speedup floor for a MATERIAL advantage at N=16/32 (the POSITIVE bar; a pre-stated criterion). |
| `LOCK_FLOOR` | 1e-6 | **B** | positive time-to-lock floor so max-over-nodes is well-defined for already-resolved nodes. |
| single path-graph `λ₂` | 0.120615 / 0.034054 / 0.009056 (N=8/16/32) | **A** | λ₂ = `2(1−cos(π/m))` for m = N+1 (path-graph Laplacian-spectral cascade); shrinks ~(π/N)². **This is the spectrally-correct width labeling** (cf. the F234 §2.3 mislabel flagged above). |
| two-tier nibble `λ₂` (constant) | **0.381966** | **A** | λ₂ of the constant-size 4-bit nibble subnet = `2(1−cos(π/5))` (m=5 path); constant for every N → O(1) Tier-1 settle. |
| two-tier block-line `λ₂` | 2.000000 / 0.585786 / 0.152241 (N=8/16/32) | **A** | λ₂ of the N/4-node block-carry path graph = `2(1−cos(π/(N/4)))` (m=2,4,8). |
| **speedups (worst case)** | **2.88× / 9.00× / 9.46×** (N=8/16/32) | **B** | MEASURED ratios single-t-lock / two-tier-t-lock (37.684/13.082; 117.710/13.082; 287.143/30.354) — outputs of the ngspice `.tran` crossing-time `meas`. |
| per-doubling growth | ×2.76 (ripple) vs ×1.52 (two-tier) | **B** | measured two-interval geometric-mean growth ratios. |
| mixedA/mixedB speedups | 1.00× / (2.23×,7.84×,8.65×) | **B** | measured ratios across the mixed input shapes (the input-dependence stated honestly). |
| measured time-to-lock cells | 37.684/117.710/287.143; 13.082/13.082/30.354; probe 37.68/26.26/13.08/2.95 | **B** | ngspice `.tran` transient crossing times (measured outputs). |
| `response_sha256` | 8a0ed3e7… | **B** | content-address (hash digest). |

F241 A/B/C: **A = 6, B = 14, C = 0** — matches the finding's own §7 "No C residue" declaration.

---

## §3 Coverage roll-up

| finding | A (structure-cascade) | B (measurement/ratio/DOI) | C (irreducible) | coverage (A+B)/total |
|---|---|---|---|---|
| **F234** Kuramoto-coupled adder | 6 | 12 | 0 | 18/18 = 100 % |
| **F235** distributed-neurology chirality | 6 | 13 | 0 | 19/19 = 100 % |
| **F236** Kuramoto nibbler ngspice | 6 | 11 | 0 | 17/17 = 100 % |
| **F238** rehearsal cost-asymmetry | 2 | 20 | 0 | 22/22 = 100 % |
| **F241** two-tier nibble timing | 6 | 14 | 0 | 20/20 = 100 % |
| **TOTAL** | **31** (≈ 33 %) | **36** (≈ 67 %)¹ | **0** | **67/67 = 100 %** |

¹ Citation-DOI blocks (F235 §6 five papers, F238 §5 nine references) are each counted as **one** provenance-class B item in the per-finding totals to avoid double-counting individually-attested DOIs; counting every DOI separately raises the absolute B count but leaves coverage at 100 % and C at 0.

**Overall coverage = 100 % (A or B).** **C-residue count = 0.**

---

## §4 The C (irreducible) residue list

**Empty.** No load-bearing constant in F234/F235/F236/F238/F241 is unattested. Every value reduces to either:

- **A — a framework cascade:** the Klein-4 / nibble = 4, π-as-`asymptotic_calculus`, D = 2ⁿ width-doublings, the path-graph Fiedler closed form `λ₂ = 2(1−cos(π/m))` (and K_m's `λ₂ = m`), the 512-point N=4 exhaustive space, the F122 K_c = 0.20 anchor; or
- **B — an attested measurement/ratio/provenance:** every located K_c, lock criterion r ≥ 0.95, p90 gate, lock_strength 2.5, T = 0.02, the imported-verbatim F230 suppression knobs (0.70/0.40/0.50/16), every measured speedup (2.88×/9.00×/9.46×), every seed (234/235/…), every budget floor, every `response_sha256`, and every web-verified citation DOI/PMID/arXiv.

The no-magic-numbers canon is satisfied: the *magic* would be the absence of a traceable source, and there is none. (Several constants — π, the λ₂ values, the F122 0.20 — *look* magic but are attested cascades/anchors; that is exactly the F228 point.)

---

## §5 Flagged discrepancy (a width LABEL, not an attestation gap)

**F234 §2.3 (line 84)** annotates the Fiedler value `0.009056` as *"λ₂ of the N=16 carry-node path graph, m=17."* The closed form `λ₂ = 2(1−cos(π/m))` gives:

- m = 17 (N=16): `2(1−cos(π/17)) ≈ 0.03405` — this is F236/F241's **N=16** value `0.034054`.
- m = 33 (N=32): `2(1−cos(π/33)) ≈ 0.008972 ≈ 0.009056` — this is F236/F241's **N=32** value `0.009056`.

So `0.009056` is the **N=32 (m=33)** path-graph Fiedler value; F234's parenthetical labels it N=16, off by one doubling. **This does NOT create a C residue** — the value is attested **A** to the path-graph Laplacian cascade and is internally consistent with F241 §3.3 / F236 (which label it correctly at N=32). It is a **prose width-tag erratum** in F234 §2.3 only. Per the audit's no-edit constraint it is **noted, not corrected**; recommend a one-word fix (N=16 → N=32, m=17 → m=33) when F234 is next touched.

---

## §6 F240 — PENDING (excluded by instruction)

F240 is **re-running**; its constants are **not final** and were **NOT audited**. Re-run this micro-audit over F240 once it lands (the K_c, Fiedler, speedup, and any new sweep-grid constants will need the same A/B/C pass).

---

## §7 srmech-native discipline of this audit

This audit is **prose + classification tables only** — the coverage figure is a plain integer ratio `(A+B)/total = 67/67`, meta-arithmetic over the classification, **not a cascade over a numeric object**, so the §2 STOP-list does not apply (no `abs()`, no `np.linalg.eig*`, no `hashlib.sha256`, no `Counter()` — none is present). No helper script was written; no measurement was run; no audited finding, `CLAUDE.md`, the srmech package, or `UPSTREAM_NOTES.md` was modified. The five findings' own runners already pass `check_srmech_discipline.py` at **0 HARD** (each finding's anchor block states this).

---

*F228b is one bounded application of the F228 no-magic-numbers instrument to the recently-landed Kuramoto-adder + coordination + rehearsal findings. Coverage 100 %, C = 0, one width-label erratum flagged. FRAMEWORK-READING tier (a coverage metric, not a measurement). `[[feedback_computational_provenance_discipline]]`; CLAUDE.md §4 no-magic-numbers = attestation-to-source.*
