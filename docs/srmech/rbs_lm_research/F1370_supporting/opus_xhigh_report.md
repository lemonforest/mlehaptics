# Follow-up: the textbook's module paths, and the unboundedness duality read through distributional ⊗ relational ⊗ responsion

Researcher: Opus (xhigh). One of two independent researchers on this brief. I read no file under `followup/` other than my own.
Date: 2026-09-14. srmech 0.9.0rc472, main checkout `b398b8c46`, pure cell. Every script printed `HAS_NATIVE False`, and numpy was absent.
I made no edits to the repository or to memory. Scratch: `followup/opus_xhigh_scratch/`.

**Labels.**
- **MEASURED**: a command in §0 printed it.
- **DERIVED**: algebra done here that you can check by hand.
- **CANDIDATE**: a reading that was not measured.
- **CITED-NOT-FETCHED**: an external result I did not fetch. Where a verdict leans on one, I say so.

**Sources.**
- The notebooks are the source of truth. They are cited as `sr:LINE` (srmech notebook) and `mfo:LINE` (MFO notebook).
- The PDF (`docs/srmech/metric-field-and-its-primitives.pdf`, 245 pages) counts only as evidence of what the 2026-05-22 snapshot promised. It is cited as "p.N" (printed page = PDF page index). No edit to it is proposed.

---

## §0 Figures ledger

Commands run from `…/followup/opus_xhigh_scratch/` as `PYTHONIOENCODING=utf-8 python <script>`. Outputs are saved as `<script>.out.txt` unless noted. Every script does `sys.path.insert(0, "D:/GitHub/mlehaptics/docs/srmech/python")`.

| id | command | what it measures | hand-rolled part (disclosed) |
|---|---|---|---|
| A0 | `extract.py` → `book.txt`; `paths.py` → `paths_raw.txt`, `paths_ctx.txt`, `book_ctx_wide.txt` | PDF text (pypdf); every `srmech.*` dotted name with its pages and context. Table 1 (p.183), the quick start (pp.183-184), the plugin section (p.186) and the profiles section (p.187) were also read by eye | regex; line-break joining |
| A1 | `a1_resolve.py` | importlib + getattr walk over 128 names: **25 importable, 103 not** | none |
| A2 | `a2_index.py` | AST index of every def/class/top-level assignment in **2570** tracked `.py` files under `docs/` (srmech, sister packages, notes) | the indexer |
| A3 | `git log --all --name-only --format= \| sort -u` → `all_history_paths.txt` (9217 paths), then grep | whether any printed module file ever existed on any ref | — |
| A3p | `git log --all -G "(def\|class) (cauchy_kernel\|toy_modulation_time\|cycle_derivative\|fft_decomposition\|recursive_hopf_signs\|ring_equilibrium_attractor\|shifted_circle_eigenvalues\|class_frequency\|proof_check_cascade\|dark_ratio_trajectory\|hubble_tension\|coupling_intensity\|complex_project\|octonionic_project\|omega_sub\|bipartite_modes\|band_membership\|smica_nilc_compare\|lunar_dial\|ramachandran\|verify_attestation\|schwarzschild_isco_efficiency\|isco_efficiency)\b" -- "*.py"` → `a3_pickaxe.txt` | definitions of 23 printed leaf names anywhere in history: **empty**. Positive control on the same instrument, `-G "def (pin_slot\|kepler_solve\|chsh_operator_norm)\b"`, returns `c44b50325`, `81dc43ee2`, `412a1eed6`, `a909c193e`, so the null is a real null | — |
| A3m | `git log --diff-filter=D --name-only -- "docs/srmech/python/srmech/amsc/*.py" "docs/srmech/python/srmech/qm/*.py"` and `git log --diff-filter=A` per module | the move commits, and whether each module existed when the book was written (v0.4.2 graduated `235293896`, 2026-05-19) | — |
| A4 | `a4_equivalents.py` (stopped at the shifted-circle step with a `Mat` constructor error; that step was re-run in A4b) | shipped equivalents run on the book's own examples | float Newton steps using srmech sin/cos |
| A4b | `a4b_equivalents.py` | shifted circle, fft, both Hopf examples, the Hubble figure under 3 instruments | quaternion product for the fibre check; a 30-term Fraction cos series as a second instrument |
| B0 | `b0_preregistration.txt`, sha256 **`0e198576df7b22001ff7885adb9e9a55b7c7d4401054e6b6d9647dcfd0ca97dd`** (via `srmech.amsc.format.sha256_bytes`, printed first by B1) | the definitions, hypothesis and pairs, written before any B run | — |
| B1 | `b1_kepler_triple.py` | the Kepler lattice checked against the harmonic-graph walk counts; the commutator; per-direction rates at six eccentricities; the Laplace limit | Kapteyn lattice in Fraction (re-validated against `bessel_j_fixed`, part 0); 64-point sup-norm grid; bisection; ratio estimators |
| B2 | `b2_heron_cf.py` | Heron vs CF as powers of one matrix; rates; Pell signs; irreversibility | Fraction bookkeeping |
| B3 | `b3_pi_pairs.py` | Pfaff two-mean vs Machin vs Euler arctan; shipped commensurability instrument | Pfaff recurrence copied from the `pi_cascade_digits` docstring, carried in exact Q using srmech sqrt at 3000 bits so stages are readable |
| B4 | `b4_classL.py` | C₅ trace identity (float side); P₅ power iteration vs Jacobi sweeps | Rayleigh-quotient bookkeeping |
| B5 | `b5_register_and_exact.py` | register constant vs Machin (P10); exact Qalg power sums on C₅; Table-1 existence checks | none |
| B6 | `b6_exact_eig_check.py`, plus an inline follow-up (heredoc printing `a == b`, `vars(a)`, `vars(b)` for the two returned eigenvalues) | whether `jacobi_eigvals(exact=True)` returns distinguishable eigenvalues | none |
| G | `git grep -n -i -E "resonan.{0,80}anisotrop\|anisotrop.{0,80}resonan" -- docs ':!*.pdf'`; the same grep over the memory directory; `grep -a -i anisotrop book.txt` | is "resonance is anisotropic" tree / memory / book text? | — |

---

## (A) Every module path the textbook tells the reader to run

### A.1 What was audited, and the class counts

- **63 path rows.** Each row is one `srmech.*` module path printed in the PDF. Named functions go inside their module's row.
  - Artifacts of line-final periods are merged: `…lunar_dial.Example`, `…ring_equilibrium_attractor.What`, `…shifted_circle_eig envalues`.
  - The book's Table 1 (p.183) writes `amsc.X` under the caption "mapped to their srmech.amsc module", so those rows are included.
  - `srmech.net` (a URL) is excluded.
  - Counting the named functions, the rows cover **110 dotted names**.
- **6 sister-package references.** The book prints no dotted path under any sister package, only package names (§A.3).
- **Total: 69.**

**Classes, exclusive, assigned in this order.**
1. **EXISTS**: importable at the printed path today (A1).
2. **MOVED**: the path existed in some commit and the object now lives elsewhere (A3m).
3. **SISTER**: lives in a sister package.
4. **FUNCTIONAL EQUIVALENT**: never existed at that path, but a shipped op computes the claim.
5. **SPIKE-SCRIPT-ONLY**: never shipped, but a notes or research script does the job.
6. **NEVER SHIPPED**: none of the above.

| class | rows | count |
|---|---|---|
| EXISTS | 1, 2, 7, 14, 15, 50, 51, 62, 63 | **9** |
| MOVED | 3, 6, 10, 11, 16, 18, 19, 22, 26, 28, 29, 30, 31, 32, 53, 54, 55, 57, 59, 60 | **20** |
| SISTER | 5 | **1** |
| FUNCTIONAL EQUIVALENT (never at the printed path) | 13, 17, 23, 36, 40, 46, 47, 49 | **8** |
| SPIKE-SCRIPT-ONLY | 9, 12, 20, 21, 38, 44, 56 | **7** |
| NEVER SHIPPED (no shipped equivalent, no script doing the job) | 4, 8, 24, 25, 27, 33, 34, 35, 37, 39, 41, 42, 43, 45, 48, 52, 58, 61 | **18** |

**The printed location never existed in any commit for 34 rows** (SISTER + FUNCTIONAL EQUIVALENT + SPIKE-SCRIPT-ONLY + NEVER SHIPPED). MEASURED by A3 + A3p.
- **13 rows carry a claim you can still check with shipped ops:** 13, 17, 23, 34, 36, 40, 46, 47, 48, 49, 52, 58, and the arithmetic of 44.
- **Rows with no computation to run:** 35 and 39 are readings of classical facts; 8, 24, 25, 27, 41, 42, 43, 45, 61 name no data or no computation.
- **The refetch half of 33 has no op.**
- **Six spike scripts were not run:** 9, 12, 20, 21, 38, 56 (they need numpy, scipy, healpy or external data).
- **Row 5** is checkable only through a private sister-package module.

**Book-time fact that matters for reading the MOVED rows** (A3m, MEASURED): every `srmech.amsc.{kepler, hdc, laplacian, cyclic, dispatch, primes, rational, search, template, tlv, naming, _native, tool_schema, catalog, format, gap_suggester}` and `srmech.qm.{bell, propagators, relativistic, single_particle, spin}` module existed by 2026-05-18. The book was right when written, and ADR-0010 moved them. The top-level `srmech.cascade` (created `686a4329a`, 2026-07-30), `srmech.calculus` (`a3aa1ca31`, 2026-06-04) and `srmech.introspect` (`a6c074523`, 2026-05-28) did **not** exist when the book was written.

### A.2 The full path table

"Verifiable?" asks whether the claim the path is offered for can be checked with shipped ops today.

| # | printed path (functions named under it) | pages | offered as verification for | class | evidence: current path / commit / script (file:line) | verifiable? |
|---|---|---|---|---|---|---|
| 1 | `srmech.__version__` | 181 | import sanity ("0.4.2") | EXISTS | A1; now `0.9.0rc472` | yes |
| 2 | `srmech.amsc` | 74, 146-147, 181-183, 186, 241, 245 | fibre-content catalogue entries (p.74); MPR machinery; the plugin bridge | EXISTS | A1. Drained by ADR-0010 to `catalog`, `descriptor`, `format`, `gap_suggester`, `adapters/`, `attested/` | the MPR / catalogue half yes; "fibre-content entries per substrate" (p.74) names no data |
| 3 | `srmech.amsc._native` (`HAS_NATIVE`; Table 1 row H `srmech_version()`) | 181, 183 | native-load check; Class H | MOVED | → `srmech._native` (`fa967cbb8`, rc376). `HAS_NATIVE`, `NATIVE_VERSION`, `NATIVE_ABI_VERSION` present; no Python attribute `srmech_version` (B5) | yes, at the new path |
| 4 | `srmech.amsc.antikythera` | 110, 176 | gear-train decomposition catalogue; "2k/223" projection | NEVER SHIPPED | no module in history (A3) | not checked here |
| 5 | `srmech.amsc.antikythera.lunar_dial` | 69 | pin-slot eccentric-cog geometry; "5 of 5 historical-period recovery … Spike #127" | SISTER | `antikythera_spectral/_research/pin_and_slot.py` (packaged copy of `docs/antikythera-maths/research/pin_and_slot.py`, `f64ab84f7`, 2026-04-24; the D-H1 lunar pin-and-slot). **Mis-cited spike:** `notes/spike127_physarum_cascade_match.md` is the *Physarum* spike; Antikythera appears there only in canon lists (`:32`, `:68`) (MEASURED source-read) | the geometry partly (private module); the 5/5 claim not re-run |
| 6 | `srmech.amsc.cascade` | 168 | the runtime cascade-orientation primitive | MOVED | did not exist at book time (created `9542bcd07`, 2026-05-30); → `srmech.cascade` (`539b50fea`, rc377) | module yes; no op named for Class C orientation |
| 7 | `srmech.amsc.catalog` (`register_attested_root`, `list_attested_sources`, `get_attested_dataset`) | 147, 169, 186 | Class E; the downstream plugin pattern | EXISTS | A1 | yes |
| 8 | `srmech.amsc.class` | 167 | "code reference for the runtime implementation" of every class | NEVER SHIPPED | none in history. **And it cannot exist under that name:** `class` is a Python keyword, so `import srmech.amsc.class` is a SyntaxError (DERIVED) | no |
| 9 | `srmech.amsc.cmb_residual.smica_nilc_compare` | 103 | SMICA 6.18σ vs NILC 6.14σ residual consistency | SPIKE-SCRIPT-ONLY | `notes/spike190_healpix_anafast_planck_tt.py`, `notes/spike192_nilc_cross_method_verification.py` (+ findings ndjson) | not with shipped ops (needs maps) |
| 10 | `srmech.amsc.cyclic` (`mod_add`, `mod_mul`, `mod_pow`, `mod_inv`, `gcd`, `lcm`) | 170, 183 | Class I | MOVED | → `srmech.math.cyclic` (`ea79fc895`, rc373); defs at `math/cyclic.py:116, 172, 236, 257, 278, 301` (A2) | yes |
| 11 | `srmech.amsc.dispatch` (`match`) | 168, 183 | Class D | MOVED | → `srmech.math.dispatch` (rc373); `match` at `:69` | yes |
| 12 | `srmech.amsc.dna` | 42 | DNA 14-class scoring ("12/14 attested") | SPIKE-SCRIPT-ONLY | `notes/spike182_dna_is_cascade_of_loe_operators_prototype.py` + findings md/ndjson | not with shipped ops |
| 13 | `srmech.amsc.factorise` | 170 | Class J code reference | FUNCTIONAL EQUIVALENT | never a file; `srmech.math.primes.factor` (`:84`). The book's own Table 1 (p.183) says `amsc.primes`: internal inconsistency | yes |
| 14 | `srmech.amsc.format` (`sha256_bytes`, `read_ndjson`) | 146, 167, 183 | Class A; MPR v1; Class C streaming | EXISTS | A1 | yes |
| 15 | `srmech.amsc.gap_suggester` | 169 | catalogue completeness via Class G | EXISTS | A1 | yes |
| 16 | `srmech.amsc.hdc` (`bind`, `bundle`, `permute`, `similarity`) | 171, 183, 185 | Class M; the cross-substrate workflow | MOVED | → `srmech.math.hdc` (rc373); all four present (B5) | yes |
| 17 | `srmech.amsc.introspect` | 169 | Class H code reference | FUNCTIONAL EQUIVALENT | never a file; `srmech.introspect` package (created after the book, `a6c074523`) | yes |
| 18 | `srmech.amsc.kepler` (`kepler_solve`, `equation_of_centre`, `pin_slot`; p.170 adds "the asymptotic-DoF modulation routine") | 170, 183 | Class K | MOVED | → `srmech.math.kepler` (`d7e21fb41`, rc372). The three functions exist; **no asymptotic-DoF modulation routine exists there** (A2) | the three functions yes; the routine no |
| 19 | `srmech.amsc.laplacian` (`dense_laplacian`, `hermitian_eigendecompose`, `jacobi_eigvals`) | 171, 183, 185 | Class L; quick start | MOVED | → `srmech.math.laplacian` (rc373). **The signature changed** to `dense_laplacian(n, edges, weights=None, *, exact=False)`, so the quick start's `dense_laplacian(A.astype(np.complex128))` no longer runs, and numpy is gone (B5) | functions yes; the printed example no |
| 20 | `srmech.amsc.mtheory.bipartite_modes` | 138 | 121/121 double-Hopf mode match; M2+M5 = 7 | SPIKE-SCRIPT-ONLY | `notes/spike216_compute.py:248` `m2_m5_bipartite_test`; `notes/spike208_compute.py:402`; "121/121" in `notes/spike216_m_theory_geometric_bridge.md` | not run |
| 21 | `srmech.amsc.mycorrhizal.band_membership` | 118 | β-band membership held across four orders of magnitude | SPIKE-SCRIPT-ONLY | `notes/spike130_1_mycorrhizal_spectral.py:18-22, 57-59` (Spike #117 band (0.25, 0.6]); scipy.sparse | not run |
| 22 | `srmech.amsc.naming` (`lookup`) | 183 (Table 1 row E) | catalogue lookup | MOVED | → `srmech.introspect.naming` (`b5aecd66f`, rc367); `lookup(key, pairs)` is a sorted-catalogue binary search | yes |
| 23 | `srmech.amsc.ndjson` | 168 | Class C code reference | FUNCTIONAL EQUIVALENT | never a file; `srmech.amsc.format.read_ndjson`. Table 1 row C itself says `format.read_ndjson`: internal inconsistency | yes |
| 24 | `srmech.amsc.octopus` | 153 | L+I+M+C+A attestation chain | NEVER SHIPPED | `notes/spike129_octopus_distributed_cognition_cascade_match.md` + findings ndjson; `spike129_1_decoder_sketch.py` is a BCI decoder sketch, not a scoring script. **Planned-path note:** `spike129…md:170` names "`srmech.amsc.asymptotic_dof` (Class K, shipped 0.4.0rcN+2 pending)", never shipped | no |
| 25 | `srmech.amsc.physarum` | 55 | slime-mould cascade identity "at machine precision" | NEVER SHIPPED | `notes/spike127_*.md` + ndjson only; **no generating script** (a computational-provenance gap) | no |
| 26 | `srmech.amsc.primes` (`is_prime`, `factor`, `cyclic_period`) | 183 | Class J | MOVED | → `srmech.math.primes` (rc373) | yes |
| 27 | `srmech.amsc.protein.ramachandran` | 69 | "the Ramachandran-plot canonical density data is shipped" | NEVER SHIPPED | no data catalogue; "ramachandran" appears only in PDB fixtures (`hoodoos/mj0366-knotted-2efv.pdb`, `notes/1BPI.pdb`) and two scoping notes | no |
| 28 | `srmech.amsc.rational` (`continued_fraction`, `best_rational`) | 172, 183 | Class N | MOVED | → `srmech.math.rational` (rc373) | yes |
| 29 | `srmech.amsc.search` (`byte_search`) | 169, 183 | Class G | MOVED | → `srmech.math.search` (rc373) | yes |
| 30 | `srmech.amsc.template` (`render`) | 169, 183 | Class F | MOVED | → `srmech.math.template` (rc373) | yes |
| 31 | `srmech.amsc.tlv` (`tlv_pack`) | 168, 183 | Class B | MOVED | → `srmech.math.tlv` (rc373) | yes |
| 32 | `srmech.amsc.tool_schema` (`get_tool_schema`, `tool_schema_view`) | 185 | LLM tool-schema introspection | MOVED | → `srmech.introspect.tool_schema` (`fa967cbb8`, rc376) | yes |
| 33 | `srmech.amsc.verify_attestation` (`.bytes` p.149; `(record)` p.229) | 149, 150, 229 | end-to-end refetch + SHA-256 re-verification | NEVER SHIPPED | nearest: `srmech.amsc.catalog.attestation_audit(source_key)`, which returns the eight attestation fields per row and **does not refetch or hash** (docstring source-read) | offline hash half via `sha256_bytes` on a local copy; refetch half no |
| 34 | `srmech.asymptotic_dof.toy_modulation_time(alpha, c, eps, gap)` | 60, 200 | T(ε) for dξ/dt = c(ξ*−ξ)^α; T = 999 (α=2), 499999.5 (α=3) | NEVER SHIPPED | no module or def ever (A3, A3p). Planned under `srmech.amsc.asymptotic_dof` (row 24's note) | **yes, as DERIVED closed form**: exact Q gives **999** and **999999/2** (A4) |
| 35 | `srmech.calculus.cycle_derivative` | 178 | substrate reading of (sin x)′ = cos x | NEVER SHIPPED | `srmech.calculus` exists (after the book); no such attribute (A1) | the identity is classical; the "reading" is not a computation |
| 36 | `srmech.cascade.cauchy_kernel` (`K_k`, `eps`) | 87, 178, 218 | f_RE(ε) = Σ K_k ε^k: e^ε for K_k = 1/k!; f(ε)f(−ε) = 1; geometric K_k = 1 converges iff \|x\| < 1; e^0.5 ≈ 1.6487 | FUNCTIONAL EQUIVALENT | `srmech.math.rational.exp_series_truncate`, exact Q. MEASURED (A4): f(1/2) = 1.648721270700 at N=16; f(1/2)·f(−1/2) = 1.000000000000000. Geometric sums exact Q: → 2 at x = 1/2; 1, 3, 7, …, 4095 at x = 2. There is **no general-kernel op** for the printed call `cauchy_kernel(K_k=lambda k: …, eps=0.5)`. `notes/spike103_concertmaster_cmb_cauchy.py:169` is a different construction (residues on a circle) | yes, per kernel |
| 37 | `srmech.cascade.fft_decomposition(N=8)` | 49, 197 | "the cascade-class trace" (L / I / M per recursion level) of an N-point FFT | NEVER SHIPPED | shipped: `srmech.cascade.spectral_cascades.fft` (value; A4b `fft([0..7])` = 28, −4+9.656854249i, …); `exact_dft._radix2_ring_op_count(8)` = **(64, 64, 3)** (op counts). **No class-trace op** | the value yes; the trace no |
| 38 | `srmech.cascade.recursive_hopf_signs` | 33 | sign flips {14, 196, 686} with "14·14 = 196", "196·3.5 = 686" | SPIKE-SCRIPT-ONLY | `notes/spike212_compute.py:53`, `spike213_compute.py:48`, `spike214_compute.py:58`, `spike215_compute.py:72` (`count_sign_flips`). **The book's 196 contradicts its own spike:** `spike213_compute.py:11, :170, :324` give depth-2 = **98** (98/14 = 7); 196 is the *short-axis* count (`:252`) (MEASURED source-read). The counts are 2∏r by construction (prior Opus report S5, DERIVED) | counts yes (DERIVED); "Hopf" content no |
| 39 | `srmech.cascade.ring_equilibrium_attractor` | 180 | max of x·e^−x at x = 1 read as the attractor's projection peak | NEVER SHIPPED | none | the calculus fact yes; the reading no |
| 40 | `srmech.cascade.shifted_circle_eigenvalues(n)` | 48, 184, 195 | eigenvalues 1 + e^{2πik/n} lie on \|λ−1\| = 1 (n = 4, 6) | FUNCTIONAL EQUIVALENT | never (`srmech.cascade` did not exist at book time). `srmech.math.laplacian.mat_eigvals(Mat.from_rows(I + P_n))`, MEASURED (A4b): n=4 {2, 1±i, 0}; n=6 {2, 1.5±0.866i, 0.5±0.866i, 0}; max \|\|λ−1\|−1\| = **1.3e-15 / 7.8e-16**. (`cyclic_laplacian_spectrum` is a different circle: 2 − ζ^k − ζ^−k) | yes |
| 41 | `srmech.catalogue.class_frequency` | 125 | per-class occurrence counts across the substrate catalogue | NEVER SHIPPED | none by name (content search not exhaustive) | no |
| 42 | `srmech.cognition.proof_check_cascade` | 164 | proof checking as an L+I+M+C+A cascade | NEVER SHIPPED | none | no |
| 43 | `srmech.cosmology.dark_ratio_trajectory` | 210 | bounded oscillation 95:5 ↔ 30:70 | NEVER SHIPPED | related, not the trajectory: `notes/spike109_concertmaster_hubble_tension.py:177`, `notes/spike188_universal_tick_crosssub.py:137` | no |
| 44 | `srmech.cosmology.hubble_tension` | 154 | ΔH₀/H₀ = 1 − cos(π t₀/T_sub) = 7.69% with **t₀ = 13.787** | SPIKE-SCRIPT-ONLY | `notes/spike109_concertmaster_hubble_tension.py`. Arithmetic MEASURED (A4b, three instruments agree): t₀ = 13.787 gives **0.0767456 (7.67%)**; t₀ = **13.797** (the value at `sr:1284` and `mfo:2143`) gives **0.076856 (7.69%)**. The notebooks are right; the book's p.154 t₀ does not produce its own 7.69% | arithmetic yes; the prediction is a reading |
| 45 | `srmech.dark_sector.coupling_intensity` | 18 | the (4+3)D_g phase-boundary coupling | NEVER SHIPPED | mentioned only in `notes/spike218_findings_2026-05-20.ndjson` | no |
| 46 | `srmech.geometry.hopf.complex_project` | 23 | z₁/z₂ at (1/√2, 1/√2) = 1 ∈ S², fibre S¹ | FUNCTIONAL EQUIVALENT | `srmech.cascade.cayley_plane.octonion_hopf_base` with a = b = (1/√2, 0, …). A4b gives base_O = (1 + 1.4e-16, 0, …), base_R = 0, `on_s8 True`, `reduces_to_h True`. That is the point "1" on the ℂ-restricted base under the standard (2a·b̄, \|a\|²−\|b\|²) chart (DERIVED). Spike scripts: `notes/hopf_fibration_explorations_script.py:116` (numpy) | yes |
| 47 | `srmech.geometry.hopf.octonionic_project` | 24 | q₁q₂⁻¹ = 1 on "𝕆P¹ = S⁴", fibre S³ = SU(2) | FUNCTIONAL EQUIVALENT | the example is the **quaternionic** fibration S³ → S⁷ → S⁴; "S⁷ ⊂ 𝕆²" is dimensionally the unit sphere of ℍ² (DERIVED; memory `reference_hopf_fibration_names_quaternionic_not_octonionic`). Equivalent: `srmech.cascade.cayley_dickson.octonion_frame_read`. MEASURED (A4b): `base_H`, `base_R`, `norm_sq` are unchanged when both halves are right-multiplied by the unit quaternion (½, ½, ½, ½), while q0/q1 change; this is the S³ fibre | yes (as quaternionic) |
| 48 | `srmech.gr.isco.efficiency(spin=0)` | 152 | η = 1 − √(8/9) = 0.0571909584 | NEVER SHIPPED | none in history; `notes/spike124…py:144` and `notes/spike154_saturation_threshold_calc.py:38, :112` mention it | arithmetic yes: `1 − calculus.sqrt(Q(8,9), precision=200)` = **0.057190958417936644**; Kerr 1 − 1/√3 = **0.42264973081037416** (A4) |
| 49 | `srmech.kepler.solve` | 69 | Newton–Raphson trace for e = 0.3, M = π/4, "E ≈ 0.99622" | FUNCTIONAL EQUIVALENT | `srmech.math.kepler.kepler_solve(M_rad, e, tolerance, max_iter)`, no trace. MEASURED (A4): E = **1.0448534569212085**. Newton steps E1 = 1.054646, **E2 = 1.044868**, E3 = 1.044853. The residual at 0.99622 is −0.0410. **The book's E2 is an arithmetic error**; no notebook carries 0.99622 (grep) | yes, with the corrected value |
| 50 | `srmech.list_profiles` | 187 | enumerate installed profiles | EXISTS | `srmech.profile_loader` | yes |
| 51 | `srmech.profile("ephemerides")` / entry-point group `srmech.profiles` | 187 | profile activation | EXISTS | ephemerides-spectral registers `ephemerides = "ephemerides_spectral"` (`pyproject.toml:86-87`); chess-spectral also registers (`pyproject-pure.toml:94`) | yes, with the sister package installed |
| 52 | `srmech.precession.omega_sub(T_yr=109.84e9)` | 94, 211 | Ω_sub ≈ 1.813e-18 rad/s | NEVER SHIPPED | constant carried in `notes/spike163_cross_substrate_scale_test.py:175` | arithmetic yes: **1.8126903981893924e-18** (π from `pi_chudnovsky_digits`, exact Fraction; A4) |
| 53 | `srmech.qm` | 9, 132, 182 | the QM / QFT / SM layer | MOVED | → `srmech.physics.qm` (`2dd1d1906`, rc381); alias removed `bc975fb53` (rc382) | yes, new path |
| 54 | `srmech.qm.bell` (`chsh_operator_norm`) | 129, 132, 184, 223 | Tsirelson 2√2; "171/171 unit tests" | MOVED | → `srmech.physics.qm.bell`. MEASURED (A4): `chsh_operator_norm()` = **2.8284271247461907**; `verify_chsh()` = (True, 4.4e-16, 4.4e-16). The 171 test count was not recounted | yes |
| 55 | `srmech.qm.propagators` | 133 | Feynman propagators | MOVED | → `srmech.physics.qm.propagators` | yes |
| 56 | `srmech.qm.qft.decompose(2)` | 131 | explicit Clifford gate list with empty T set | SPIKE-SCRIPT-ONLY (partial) | no `qm/qft` ever; `notes/spike136_quantum_computing_via_cascade_without_brute_force.py:483` `qft_t_gate_count(n)` returns **counts**, not a gate list | not with shipped ops |
| 57 | `srmech.qm.relativistic` | 133, 184 | Dirac / Weyl / Klein–Gordon | MOVED | → `srmech.physics.qm.relativistic` | yes |
| 58 | `srmech.qm.relativistic.schwarzschild_isco_efficiency` | 184 | 0.0571909584 | NEVER SHIPPED | absent from `__all__` (`charge_conjugation_matrix … weyl_right_projector`); A3p null | arithmetic yes (row 48) |
| 59 | `srmech.qm.single_particle` | 133 | TDSE / TISE / … | MOVED | → `srmech.physics.qm.single_particle` | yes |
| 60 | `srmech.qm.spin` | 132 | Pauli / Clifford | MOVED | → `srmech.physics.qm.spin` | yes |
| 61 | `srmech.shadows` | 81 | the five shadow-stance entries | NEVER SHIPPED | none | no |
| 62 | `srmech.signal_processing` (`fft`, `ifft`, `sign_quantise`, `matched_filter`, `wiener`, `hdc_truncation`) | 182 | the dual-path surface | EXISTS | created `d2d6291b5` (2026-05-19). Four ops at top level; `fft` / `ifft` are registry modules `closed_form_ops.fft` / `path_b_ops.fft` (each exports `op`), not top-level attributes (A1, A2) | yes |
| 63 | `srmech.spectral` (`decompose`, `delta`, `predict`, `recompose`, `truncate_sparse`) | 171, 182, 185 | quick start; the cross-substrate workflow | EXISTS | A1; `decompose(state, laplacian, *, encoder_tag)`. The printed quick start does not run (row 19) | functions yes; example no |

### A.3 Sister-package references (no dotted paths printed)

| reference | pages | claim | finding |
|---|---|---|---|
| ephemerides-spectral (v0.24.x, v0.24.5, v0.24.7, v0.24.12) | 52, 109-110, 121-122, 186-187, 237, 241, 245 | celestial mechanics; Hawaiian-Emperor / Tharsis / Loki Patera Laplacian catalogues; the plugin exemplar | **EXISTS**: `docs/antikythera-maths/ephemerides-spectral/python`, version 0.32.0. The three cited versions match their topics at `ROADMAP.md:37` (v0.24.5 Hawaiian-Emperor), `:35` (v0.24.7 Tharsis), `:30` (v0.24.12 Loki Patera) (MEASURED) |
| chess-spectral §5b | 121 | "spectral game-state via piece-adjacency Laplacian … capture algebra" | **EXISTS** (1.19.1rc1). `chess_spectral_research_notebook.md:661` §5b is "Capture as Global Field Perturbation", which is topical only to the capture half |
| antikythera-spectral | 67, 110, 176 | Antikythera literature; lunar dial | **EXISTS** (0.3.0); see row 5 |
| othello-spectral | 122 | L+I piece-flip dynamics | **EXISTS** as a package (`docs/othello-maths/research/othello_spectral/pyproject.toml:30`); no publish workflow under `.github/workflows` |
| doom-spectral | 122 | L+C room adjacency | **NO Python package.** `docs/antikythera-maths/doom-spectral/source/` is DOOM C source; the notebook exists |
| logo-spectral | 122 | C+I turn-vector path decomposition | **NO package of that name.** `docs/logo-maths/` holds scripts + `logo_hdc/`; the name is a project label (`docs/index.md:16`) |

PyPI presence of any sister package is CITED-NOT-FETCHED (no network).

### A.4 Defects in the book that running the paths exposed

PDF only. Grep finds none of them in the current notebooks unless stated.
1. **Ex. 8.4, p.69.** E2 = 0.99622 is wrong; E = 1.044853 (row 49).
2. **p.154.** t₀ = 13.787 does not give the printed 7.69%; the notebooks' t₀ = 13.797 does (row 44).
3. **p.33.** "196 sign flips at depth 2" and "14·14 = 196" contradict `spike213_compute.py`'s own 98 (row 38).
4. **p.24.** The "octonionic" Hopf example is quaternionic (row 47).
5. **p.69 and p.110.** The Antikythera lunar-dial recovery is attributed to Spike #127, which is the Physarum spike (row 5).
6. **pp.183-184.** The quick start needs numpy and a removed `dense_laplacian` signature (row 19).
7. **Table 1 vs pp.168-170.** Class C is `format.read_ndjson` vs `amsc.ndjson`; Class J is `amsc.primes` vs `amsc.factorise`.
8. **p.170.** `amsc.kepler` is said to hold "the asymptotic-DoF modulation routine"; it never did.

---

## (B) The unboundedness duality read through distributional ⊗ relational ⊗ responsion

### B.0 What the record actually says (source-read), and which dictionary this triple is

- **`sr:8363-8413` §3.59.1.**
  - The k=3 lodging convention is quoted from the branch. Per slot: **1 op / distributional / eigenvectors**, **2 operand / relational / edges**, **3 responsion / responsion / eigenvalues**.
  - Its authority table under repeated application `Lⁿ` reads: slot 1 **INVARIANT**; slot 2 **1-hop → n-hop reach**; slot 3 **λ → λⁿ**.
  - Its scope sentence: *"whenever a finding touches the k=3 read of a **Class-L object**"*.
- **`sr:8430-8477` §3.59.3.** Six dictionaries D1–D6. **The brief's triple is D1's name-2 column, not a seventh dictionary.** It becomes a new usage only when applied to something that is not one Class-L object; B.1 measures exactly where that happens.
- **`sr:9048-9111` §3.59.11.**
  - `responsion` names the **slot**, `resonance` its **function**, and harmonic / subharmonic / inharmonic its **values**.
  - "harmonic" is two words: a multiple of an angle vs a commensurate eigenvalue ratio.
- **`sr:9113-9217` §3.59.12.**
  - The generic word for a responsion is **commensurate / incommensurate**.
  - The harmonic family presupposes a declared fundamental, and `commensurability_verdict` makes the caller supply it.
  - `λ → λⁿ` is not an octave.
- **`mfo:6727-6778` §VIII.31.20.**
  - Item 4 settles responsion (slot) vs resonance (function) and calls `distributional ⊗ relational ⊗ resonant` the function-name spelling, *correct as written*.
  - **Item 5 (`mfo:6754-6756`) says "resonance is anisotropic" appears nowhere under `docs/` and "must never be quoted as a framework convention"**, because anisotropy is spatial direction-dependence and the measured asymmetry is the temporal/causal arrow.
  - **Correction to the brief:** §VIII.31.20 does *not* state "resonance is anisotropic"; it fences that phrase. "Commensurate / incommensurate as a property of responsion values" is stated at `sr:9113ff` and in §VIII.31.21's table (`mfo:6788-6791`); §VIII.31.20 only cross-refers to it.
- **`mfo:6780-6859` §VIII.31.21.**
  - inharmonic / subharmonic = **VALUES of the responsion** (instrument: `commensurability_verdict`).
  - asymmetric = **DYNAMICS / coupling** (Sakaguchi α).
  - These are **two independent facts, with both off-diagonal corners measured**. B.2 finds the same shape one level over.
- **Brief reading 2, "responsion is a measure of commensurateness".** This inverts the record's wording. The record makes commensurateness a *property of responsion values*. The brief applies it to *pairs of frames*, which is a new use and must name its sense (B.2.4).
- **G checks (MEASURED).**
  - The co-occurrence grep over `docs/` returns only `mfo:6754` and `mfo:6756`, both stating the absence.
  - Memory: zero co-occurrences. The one memory file with "anisotropic" in its name (`user_stance_finite_fractal_stacked_minima_anisotropic_expansion_cascade.md:28`) uses it for a one-stack-axis Koch-spiral expansion, never with resonance.
  - The book: zero hits for "anisotrop".

### B.1 Item 1: placing the two measured two-frame instances in the triple

#### B.1.1 Heron / continued fraction for √2: a genuine D1 object, measured in all three columns

One symmetric integer matrix `A = [[2,1],[1,0]]`. As a graph: two vertices, a loop of weight 2, an edge of weight 1. So the "is there a graph?" test passes.
- Strictly, A is an adjacency with a loop, not `L = D − A`. The three authority-table columns hold for any fixed symmetric matrix under powers (DERIVED), and srmech's Class-L `jacobi_eigvals` reads it (B2).
- Convergents: `P₀ @ A^k` with `P₀ = [[1,1],[1,0]]`. They agree with `best_rational` at every denominator for k < 100 (B2, MEASURED).

| | **distributional** (op, eigenvectors) | **relational** (operand, edges) | **responsion** (eigenvalues) |
|---|---|---|---|
| the object | invariant eigenvector: `A·(1+√2, 1) = (1+√2)·(1+√2, 1)`, printed (2.414213562373095, 1.0) after dividing; `P₀` maps it to the ratio **1.4142135623730951**. **The LIMIT lives here** | edge weights 2, 1, 1; `A^k` entries are weighted walk counts, e.g. `A⁸ = [[985,408],[408,169]]` | `1 ± √2` (jacobi float: −0.41421356237309515, 2.414213562373096) |
| **CF frame**, index k | fixed | **reach k** (one more hop per step) | error ratio **−0.171572875** at k = 20, 40, 80 = λ₋/λ₊ = −(3−2√2). The sign of λ₋ is **kept**: the Pell norm alternates −1, +1, … |
| **Heron frame**, index n | fixed | **reach 2ⁿ** (squaring): Heron n = convergent **2ⁿ − 1** for n = 1…6 (exact equality of stage objects) | same base 3−2√2 on schedule 2ⁿ; order log ε(n+1)/log ε(n) = 2.447, 2.173, 2.080, 2.038, 2.019, **2.009**. The sign is **collapsed**: Pell norm **+1** at every n |

All MEASURED in B2.

**Result.** For this instance the three slots separate the duality cleanly:
- the limit is the slot-1 invariant;
- both unbounded indices are slot-2 reach schedules (k vs 2ⁿ) of one edge set;
- the approach rate is a slot-3 quantity, the ratio of the two responsion values.

The two frames share slots 1 and 3 exactly and differ only in the slot-2 schedule. MEASURED.

#### B.1.2 Kepler E(M): the lattice factorises into the three slots, but over two operators that do not commute

**MEASURED (B1 part 1), exact, 272 cells (1 ≤ p ≤ 16, 0 ≤ k ≤ 16), 0 mismatches:**

```
c(p,k)  =  [H^p]_(k,0)  ·  k^(p-1)  /  ( 2^(p-1) · p! )
           signed walk        eigenvalue k of D,
           count on ℤ         raised to p-1
```

- `H = S − S⁻¹` is the chiral hop on the harmonic lattice ℤ. It is the pin's `sin` acting on harmonic indices.
- `A = S + S⁻¹`. The support of `[A^p]_(k,0)` equals the cone `{k ≤ p, k ≡ p mod 2}`, with **0 disagreements**.
- `D = diag(harmonic index)`, which is −i·d/dM on `e^{ikM}`.
- The lattice itself is re-validated against `srmech.music.bessel_j_fixed` at e = 3/5: column sums differ by ≤ **3.5e-77** (B1 part 0).
- The k = 0 column has nonzero walk counts for even p, but the factor `0^(p−1)` removes it. The eigenvalue-0 mode is annihilated by the responsion power (MEASURED).
- DERIVED origin: the Lagrange inversion `E = M + Σ_p (e^p/p!) d^{p−1}/dM^{p−1} sin^p M`, with `sin^p M` expanded binomially. The *formula* is standard and CITED-NOT-FETCHED as a named theorem. The equality above was measured independently of it.

**Fence, MEASURED:** `[D, H] = A` (True, B1). The eigenbasis factor comes from D and the walk factor from H, and they do not commute. So these are **not three reads of one Class-L object**, and the k=3 convention's own scope sentence is not met.
- Status: a **CANDIDATE reading ("D1 shape over a non-commuting pair")**, not D1.
- It should not be lodged as a D7 until someone either finds a single linear object whose three reads give this factorisation, or rules that a non-commuting pair qualifies.

Figure: the (p, k) lattice, and where each Kepler frame cuts it. Support is from B1 part 1; exactness per frame is from the coordinator-confirmed S1 and the construction.

```
 k (harmonic = distributional index)
 7 |  .   .   .   .   .   .   x
 6 |  .   .   .   .   .   x   .
 5 |  .   .   .   .   x   .   x
 4 |  .   .   .   x   .   x   .
 3 |  .   .   x   .   x   .   x
 2 |  .   x   .   x   .   x   .
 1 |  x   .   x   .   x   .   x
   +--1---2---3---4---5---6---7---> p (e-order = walk length = relational reach)
   x = nonzero cell (k <= p, k = p mod 2: the walk cone of H on Z)

 depth n    : exact on every cell with p <= n (a vertical cut; finitely many cells: 6, 20, 72 at n = 4, 8, 16)
 e-order p  : the partial sum IS the jet p' <= p
 modes K    : exact on every cell with k <= K (a horizontal cut; infinitely many cells)
```

| frame | its index lives in | distributional | relational | responsion | status |
|---|---|---|---|---|---|
| **depth n** | **relational reach**: exact for walk length ≤ n | the harmonic basis is *not* invariant under the pin map (all harmonics appear at orders > n from depth 2, S1) | the chiral hop H; n applications resolve reach n | per-cell `k^(p−1)` exact only inside p ≤ n. **Rate e** (sup of the contraction \|e·cos E*\|, DERIVED): measured step ratio **0.0888, 0.2892, 0.4916, 0.5904, 0.6941, 0.8981** at e = 0.1, 0.3, 0.5, 0.6, 0.7, 0.9 (B1) | factorisation / reach MEASURED; rate DERIVED + MEASURED. **The rate is not an eigenvalue of H or D: DOES-NOT-MAP as a responsion value** |
| **e-order p** | **relational reach**: walk length p | cone window k ≤ p | signed walk count `[H^p]_(k,0)` | `k^(p−1)`, the (p−1)-th power of D's eigenvalue. **Rate e/r_L**, with Laplace limit r_L = **0.662743419349** (B1 bisection; the minimum-radius location M = π/2 is CITED-NOT-FETCHED). Measured per-order ratio at M = π/2: **0.7346** (e = 0.5, DERIVED 0.7544); **0.8814** (0.6, DERIVED 0.9053); **1.0282, divergent** (0.7, 1.0562); **1.3219, divergent** (0.9, 1.3580). Root test \|a_p\|^{1/p} = 1.2006, 1.3381, 1.4058, 1.4334, **1.4487** at p = 21…201, rising toward 1/r_L = 1.508880 (not converged) | MEASURED / DERIVED. At e = 0.1 and 0.3 the error hit the float floor inside the window, so those rates were **not measured** (B1 prints nan) |
| **modes K** | **distributional window** k ≤ K | sin kM, eigenvectors of D | inside each mode, every walk length (the whole e-tower) | exact per cell. **Rate ρ(e) = e·exp(√(1−e²))/(1+√(1−e²))** (CITED-NOT-FETCHED closed form). Measured r(k+1)/r(k) at k = 60: **0.1323, 0.3888, 0.6215, 0.7237, 0.8137, 0.9459** vs ρ = 0.1356, 0.3986, 0.6370, 0.7418, 0.8341, 0.9692, approaching from below (B1) | MEASURED ratios; closed form CITED |

**Reading.**
- Depth and e-order index the **same slot** (relational reach).
- Modes index a **different slot** (the distributional window).
- The "e-order tower hidden inside a mode" is that mode's walk-length decomposition: signed walk count × eigenvalue power (MEASURED).
- None of the three Kepler rates is a responsion *value* of H or D; they are asymptotic balances of walk count, `k^(p−1)` and `1/p!` (CANDIDATE).
- Heron / CF differs on exactly this point: there the rate *is* the eigenvalue ratio.

### B.2 Item 2: responsion as commensurateness

#### B.2.1 Pre-registration (B0; summary)

The definitions below were fixed before any B run (sha256 above).

**Correspondence levels between stages:**
- **L3 equality:** A(n) = B(f(n)).
- **L2 projection:** A(n) = π_n(B(f(n))).
- **L1 jet:** exact agreement on a growing common graded coordinate set, with neither frame a projection of the other.
- **L0 limit only.**
- ESC-weak = L ≥ 1; ESC-strong = L ≥ 2.

**Commensurateness, two definitions:**
- **Def R (per-step rate).** Classify each frame as LINEAR (root rate r), SUPERLINEAR (order q), TERMINATING or DIVERGENT. A pair is commensurate iff it is in the same class with log-ratio in ℚ; cross-class pairs are incommensurate; a terminating or divergent member makes the pair UNDEFINED.
- **Def B (shared base).** ε = C·β^{s(n)}; a pair is commensurate iff log β_A / log β_B ∈ ℚ, whatever the schedules.
- Irrationality is decided only from closed forms. A float ratio is UNDECIDED.

**H (CANDIDATE):** ESC ⟺ commensurate. It is tested in all four cells of (Def R, Def B) × (weak, strong).

**One clarification made after measuring, disclosed.** "Common graded coordinate system" could be read to admit positional digit expansions. Under that reading *every* pair of convergent frames is L1 (leading digits agree), which makes ESC-weak vacuous. I therefore read L1 as a grading intrinsic to the constructions (e-order, harmonic index, walk length), and I report P6 / P7 under both readings. The strong-ESC cells, and P1's refutation, do not depend on this choice.

#### B.2.2 The pairs

| pair | L level (evidence) | Def R | Def B | H: R-weak / R-strong / B-weak / B-strong |
|---|---|---|---|---|
| **P1** Kepler depth ↔ e-order | **L2**: S_n = J_n(E_n), the coordinator-confirmed S1 ("depth n exact for every p ≤ n through depth 7") | LINEAR e vs LINEAR e/r_L → **incommensurate at every rational e < r_L** (DERIVED, below). At e ≥ r_L e-order diverges → UNDEFINED | same bases → **incommensurate** | **REFUTED / REFUTED / REFUTED / REFUTED** |
| **P2** Kepler depth ↔ modes | **L1**: at stage n with K ≥ n both are exact on the whole jet p ≤ n (S1 + lattice support), and neither is a projection of the other (S1: depth-m cells at p = m+1 differ from the lattice, e.g. depth 2 (3,1): −3/8 vs −1/8) | e vs ρ(e) → **incommensurate at every rational e ∈ (0,1)** (DERIVED) | **incommensurate** | REFUTED / consistent / REFUTED / consistent |
| **P3** Kepler e-order ↔ modes | **L2**: S_p = J_p(T_K) for K ≥ p (DERIVED: every cell with p′ ≤ p has k ≤ p ≤ K) | e/r_L vs ρ(e): **UNDECIDED** (two transcendental quantities; Lindemann–Weierstrass alone does not decide) | UNDECIDED | not testable |
| **P4** Heron ↔ CF (√2) | **L3** (B2) | SUPERLINEAR (order → 2.009) vs LINEAR (0.171572875) → **incommensurate** (cross-class) | both base 3−2√2 → **commensurate** | REFUTED / REFUTED / consistent / consistent |
| **P5** CF ↔ every second convergent (control) | **L3** (construction) | 0.171572875 vs **0.029437252** = (3−2√2)²; log-ratio 2 → commensurate | commensurate | consistent ×4 |
| **P6** Pfaff two-mean ↔ Machin | **L0**: Pfaff stages for n ≥ 1 are irrational (√ each step), Machin partial sums rational; b₀ = 3 equals no Machin or Euler partial sum for N ≤ 40 (B3). [L1 under the digit reading] | **0.25000000** (B3) vs Machin −0.0368, −0.0382, **−0.0388** at N = 10, 20, 30 (→ −1/25 with the (2N−1)/(2N+1) factor, DERIVED); log(1/4)/log(1/25) = **log 2/log 5 ∉ ℚ** (2^a = 5^b has no positive solution) → **incommensurate** | incommensurate | consistent ×4 [digit reading: REFUTED in the weak cells] |
| **P7** Pfaff two-mean ↔ Euler 4(atan ½ + atan ⅓) | **L0** (same argument). [L1 under the digit reading] | 1/4 vs Euler −0.2297, −0.2388, **−0.2423** (→ −1/4, dominated by atan ½) → log-ratio 1 → **commensurate** | commensurate | **REFUTED ×4** [digit reading: consistent in the weak cells, REFUTED in the strong cells] |
| **P8** C₅: tr Lʲ ↔ Σλᵢʲ | **L3**: `QMat` traces 10, 30, 100, 350, 1250, 4500, 16250, 58750, 212500, 768750 equal the exact `Qalg` power sums for j ≤ 10 (B5); float side diff ≤ 1.2e-10 (B4) | divergent sequences → UNDEFINED | UNDEFINED | not testable (DOES-NOT-MAP: these are identities, not approximations) |
| **P9** P₅: power iteration ↔ Jacobi sweeps | **L0** (different iterated objects: powers of L vs plane rotations) | LINEAR **0.523607** = (λ₃/λ₄)² = 0.5236067977 (B4) vs SUPERLINEAR (sweep errors 1.6e-1, 6.6e-3, 2.3e-6, 6.2e-15 floor; log-ratios 2.7, 2.6) → incommensurate | Jacobi has no base form → UNDEFINED | consistent (R cells); B not testable |
| **P10** winding_fold pure register ↔ Machin | a bounded register has no unbounded index, so it is not a frame | — | — | not applicable. MEASURED (B5): `_EPH_TWO_PI` = 7595904947272677161575987 / 2⁸⁰, \|… − 2π\| = 6.58e-26. It equals no 2·Machin_N for N < 80. 2·Machin_N enters and stays in its 2⁻⁴⁴ fold cell from **N = 9** (checked 5 further stages); \|diff\| saturates at 6.58e-26 from N ≈ 20. Correspondence exists only at the register's resolution: a coarse-graining, not ESC |

**DERIVED irrationality arguments** (Lindemann–Weierstrass is CITED-NOT-FETCHED; e rational):
- **r_L is transcendental.** If r_L were algebraic, √(1+r_L²) would be algebraic and nonzero, so exp(√(1+r_L²)) = (1+√(1+r_L²))/r_L would be algebraic. Lindemann–Weierstrass forbids that.
- **P1.** Suppose log e / log(e/r_L) = a/b. Then a·log r_L = (a−b)·log e, so r_L = e^{(a−b)/a} would be algebraic. Contradiction. (a = 0 forces b = 0.)
- **P2.** Put s = √(1−e²), algebraic and nonzero. Suppose log e / log ρ = a/b. Then exp(a·s) = e^{b−a}·(1+s)^a would be algebraic with a ≠ 0. Contradiction.
- **Contingency.** Both arguments assume the sup-norm root rates are exactly e, e/r_L and ρ(e). Those are DERIVED; B1's measured ratios approach them from below and have not converged.

#### B.2.3 Verdict on H

**H is REFUTED as stated, in every cell, and in both directions.**
- **ESC without commensurateness.** P1 is an exact projection at every stage between two frames with irrationally related rates. P4 does the same under Def R, and P2 under ESC-weak.
- **Commensurateness without ESC.** In P7 two frames approach π at the identical rate 1/4 while no stage of one is ever a stage, projection or intrinsic jet of the other.

Where H held (P5, P6, P9, and P4 under Def B), it held alongside the refuting pairs, so it does not survive as a law.

**The shape matches §VIII.31.21 one level over** (CANDIDATE link; `mfo:6793` measures the same pattern for "asymmetric" vs "inharmonic"):
- exact finite-stage correspondence and rate commensurateness **vary independently**;
- **both off-diagonal corners are measured** (P1; P7).

#### B.2.4 "Commensurate" is two words for a pair of frames

MEASURED (B3). The shipped instrument, applied to the step rates *as values*:
- `commensurability_verdict([Q(1,1), Q(4,25)])` (Pfaff 1/4 vs Machin 1/25) → `verdict = harmonic`, `integer_series = False`, `rational_rank = 2`.
- `commensurability_verdict([Q(1,1), Q(1,1)])` (Pfaff vs Euler) → `harmonic`, `integer_series = True`.

In the **step-count sense** ("how many steps of A buy one step of B"), P6 is **incommensurate** (log 2/log 5). The two senses come apart on the first example, exactly as `sr:9092-9094` records for "harmonic".
- The shipped op answers the **value-ratio** question.
- The step-count question is a log question that the op cannot be asked: its inputs must be exact Q / Qalg, and the logs of rationals are transcendental.

So "responsion is a measure of commensurateness" is true in the value-ratio sense only, and any sentence using it for frames must say which sense it means.

#### B.2.5 What does predict ESC (post-hoc, CANDIDATE, not tested by the pre-registration)

Across all ten pairs, the L level tracks whether both indices are **reach schedules of one shared iterated object**:
- **P1, P4, P5, P8** (same edge set, same slot) → L2 / L3;
- **P3** (reach vs a window whose cone makes the jet exact) → L2;
- **P2** (reach vs window) → L1;
- **P6, P7, P9** (no shared iterated object) → L0.

Commensurateness tracks the **responsion** side: where one linear operator is shared, the rate is an eigenvalue ratio (P4 / P5: 0.171572875 = \|λ₋/λ₊\|; P9: 0.523607 = (λ₃/λ₄)²).

The pattern was read off after the measurements. It needs a fresh pre-registered set, e.g. Halley vs Newton for √2 (reach 3ⁿ vs 2ⁿ of one unit), Lucas vs Fibonacci ratios, or a relaxed-pin Kepler depth vs e-order.

### B.3 Item 3: anisotropic resonance

**What the record's word means.** `mfo:6756`: anisotropy is **spatial direction-dependence**. The record's measured asymmetry is the **temporal / causal arrow**, the sign of the Sakaguchi α (`mfo:6791`, `mfo:7257`). The record also notes the comb comes from nonlinearity, not spatial asymmetry (`mfo:7251`). The brief's reading is **not tree text and is fenced** (B.0). **DOES-NOT-MAP.**

**What is measurable in these instances is direction dependence in *index space*.** Four kinds were pre-declared and measured. None of them is the record's spatial anisotropy, none is the Sakaguchi arrow, and none is §IV.5's degeneracy-lifting residual:
- **(a) A reach cone, not an axis symmetry.**
  - The Kepler lattice support is exactly the walk support of the hop on ℤ (0 disagreements, B1).
  - A budget B spent along the reach direction makes finitely many cells exact (6, 20, 72 at B = 4, 8, 16). The same budget along the harmonic direction makes infinitely many exact.
  - The two index directions of one lattice are not interchangeable. The cone is symmetric under k → −k, so it carries no sign.
- **(b) The rate depends on the index direction, and the dependence varies with the object's parameter.**
  - log(depth rate)/log(mode rate) = **1.152, 1.309, 1.537, 1.711, 1.966, 3.371** at e = 0.1, 0.3, 0.5, 0.6, 0.7, 0.9 (B1; float, UNDECIDED as verdicts, DERIVED irrational at every rational e).
  - The e-order direction is slowest and diverges beyond r_L while the other two converge.
- **(c) A sign bit that one frame carries and the other collapses.**
  - CF alternates the Pell norm −1, +1, −1, … and alternates sides of √2 (−, +, −, +, …).
  - Heron has Pell norm **+1** at every n and stays above √2, because 2ⁿ − 1 is always odd (B2).
  - The bit is the Galois norm of the unit 1+√2, i.e. the conjugation 1+√2 ↔ 1−√2 (DERIVED).
  - **The exact carrier cannot see it (MEASURED, B6).** `jacobi_eigvals(exact=True)` on A returns two `Qalg` eigenvalues with identical `_m = (−1,−2,1)` and `_coords = (0, 1)`, and they compare **`a == b` → True**. They differ only in a float `_root` (−0.41421356237309503 vs 2.414213562373095). Their field sum is 2α and their product is α², not trace 2 and det −1.
  - So the sign separating the two frames lives in the real embedding, which the exact carrier's equality ignores.
  - Closest record sense: §3.59.11's "subharmonic" sense 3, a Class-K chirality / sign bit (`sr:9105`). CANDIDATE; not merged.
- **(d) Irreversible vs reversible stage maps.**
  - Heron is 2-to-1: h(3/2) = h(4/3), True (B2).
  - The CF step matrix is unimodular (det A = det P₀ = −1), so the step is invertible over ℤ (B2).
  - The Kepler depth map E ↦ M + e·sin E is many-to-one (its range is bounded; DERIVED).
  - The modes frame has no stage map at all.
  - This is irreversibility, which is **not** the record's arrow (a coupling phase lag). The two must not be merged.

### B.4 Item 4: what the triple adds to or corrects in the draft amendments (Fable §5.1, Opus §5a)

1. **"Share only the limit" is too strong.**
   - Fable §5.1 says the depth and mode truncations "are different objects at every finite stage and coincide only at the limit; what they share is the invariant". Opus §5a says "or the shared limit only (Kepler depth ↔ modes)".
   - Corrected: at stage n (K ≥ n) both are **exact on the whole e-order ≤ n jet** (L1). What they lack is projection (L2) or equality (L3).
   - Opus §5a's "exact jet agreement (Kepler depth ↔ e-order)" understates that pair: it is a **projection** (L2).
2. **Replace "each frame's unbounded index is the other's hidden fibre"** (Opus §5a, CANDIDATE) with a slot statement. Depth and e-order index the **same relational reach**; modes index the **distributional window**. The e-order tower inside a mode is its walk-length decomposition, `c = [H^p]_(k,0)·k^(p−1)/(2^(p−1)p!)` (MEASURED). Avoid "fibre": it has three senses on main (`mfo:6774`).
3. **Keep "rates belong to constructions" (both drafts) and add two sentences.**
   - A rate does **not** predict exact correspondence, and nothing in either direction supports that it does (P1, P7).
   - Where one linear operator is shared, the rate is an eigenvalue ratio, and two constructions sharing the operator share the base while differing in schedule (Heron 2ⁿ vs CF k).
4. **Any use of "commensurate" for frames must say value-ratio sense or step-count sense** (B.2.4).
5. **Do not write "resonance is anisotropic"** (`mfo:6754`). Name the direction dependence instead: reach cone, per-direction rate, sign collapse, or irreversibility.
6. **The replacement word for "generator".** Under D1's authority table, as measured on Heron / CF, an unbounded construction has **its index in slot 2** (the repeated edge rule), **its limit in slot 1** (the invariant) and **its rate in slot 3** (the eigenvalue ratio). A generator of a construction is therefore the slot-2 edge rule: A, or H for Kepler. Against that:
   - **"form / reference form" (Opus).**
     - "form" fits D1 slot 1 (the invariant).
     - "reference" is D3 slot 2: `mfo:6663` "real = the *operand*", and the three reals *are* the fixed references (`mfo:6691`, measured).
     - The compound phrase joins two dictionaries, which is the cross-dictionary transport `sr:8430-8477` exists to stop. **It survives only if split and dictionary-named.**
   - **"register / carrier" with "translate" as the process verb (Fable).**
     - "register" is a D2 noun (slot 2) and shipped vocabulary (`CDRegister`). It **survives in D2.**
     - "translate" is a D2 verb, fitting B/H/N as A–N operator classes. It **survives as the verb for B/H/N, not as a description of the_one.**
   - **Neither word addresses the record's own candidate.** D3 places the_one in **slot 3**: *"resonance … it **is** `the_one`"* (`mfo:6664`, candidate, held lightly). A replacement must say whether it keeps or withdraws that identification.
   - **"generator" in the D1 slot-2 sense is not supported for the_one** (CANDIDATE reading of a measured fact). Its frame is block-diagonal **by construction** and couples nothing across rungs (`mfo:6701`, FORCED), so it has no cross-rung reach to repeat.

---

## (C) Corrections owed

Dated appends to current notebooks or memory, and one tracker item. Nothing is proposed for the PDF.

1. **srmech notebook, new §3.59.15** (next open number after `sr:9337` §3.59.14).
   - Title: *"Two constructions of one limit: exact finite-stage correspondence and commensurateness vary independently; both off-diagonal corners measured (2026-09-14; MEASURED at 0.9.0rc472)"*.
   - Carry:
     - the pre-registration hash;
     - P1 and P7 as the two corners;
     - Heron / CF as a measured instance of all three columns of §3.59.1's authority table;
     - the two senses of "commensurate" for frames, with the `commensurability_verdict` output;
     - the Kepler factorisation `c = [H^p]_(k,0)·k^(p−1)/(2^(p−1)p!)` with the `[D,H] = A` fence (not one Class-L object, so not D1 and not lodged as D7);
     - the post-hoc reach-schedule pattern as CANDIDATE with its proposed test.
2. **MFO notebook, dated append after §VIII.31.20 item 5** (or §VIII.31.24).
   - The phrase "resonance is anisotropic" re-circulated in a research brief on 2026-09-14.
   - Record the four index-space direction dependences measured here: cone, per-direction rate, Galois sign collapse, irreversibility. None is spatial anisotropy or the Sakaguchi arrow. The sign-collapse bit is only a CANDIDATE link to `sr:9105`'s third "subharmonic" sense.
3. **Memory `user_stance_infinity_approximates_asymptote.md` and `user_stance_asymptotic_dof_sidesteps_infinity.md`.** When the Fable §5.1 / Opus §5a amendment is appended, fold in B.4 points 1–5 (L1 / L2 wording; the slot statement; rate ≠ correspondence; the sense of "commensurate"; no "anisotropic").
4. **Memory `user_stance_resonate_dont_brute_force_asymmetric_resonator.md`: one dated fence line.**
   - "anisotropic" is not this stance's word (`mfo:6754-6756`); "asymmetric" carries two readings on main (`mfo:6830-6836`).
   - `mfo:6754` records the phrase as a paraphrase of this stance, and it has now reappeared, so the fence should travel with the stance.
5. **`docs/srmech/notes/spike129_octopus_distributed_cognition_cascade_match.md:170`: dated errata append.** The named primitive `srmech.amsc.asymptotic_dof` ("shipped 0.4.0rcN+2 pending") never shipped. No module or def exists in any commit (A3, A3p). The book's `srmech.asymptotic_dof.toy_modulation_time` is the same unshipped surface.
6. **MFO notebook (the book's source of truth), dated "textbook path audit" append.**
   - Carry the 34 printed paths whose location never existed, and for each still-verifiable claim the shipped op that verifies it (§A.2), plus the printed-example defects of §A.4 (E2 = 1.044853; t₀ 13.787 vs 13.797; 98 vs 196; quaternionic label; Spike #127 misattribution; the dead quick start).
   - The notebooks themselves were checked and do not carry the E2 or t₀ errors (`sr:1284` and `mfo:2143` use 13.797 and are correct).
7. **For the maintainer's ruling (tracker item, not a notebook edit): a CANDIDATE silent-wrong-answer class in the exact eigen route.**
   - `jacobi_eigvals(..., exact=True)` on `[[2,1],[1,0]]` returns two eigenvalues that compare **equal** under `Qalg.__eq__` and differ only in a float `_root` (B6).
   - If field-element equality is intended, the docstring's "list of n ascending … eigenvalues with multiplicity" needs a sentence saying that `==` does not distinguish conjugate eigenvalues and that sums or products of the list are not trace or det.
   - If it is not intended, a caller counting distinct eigenvalues with `==` gets a wrong answer and no error.
8. **Confirmed, not new: `docs/antikythera-maths/CLAUDE.md:9`** still reads "§3.59.3 names the four different dictionaries" against the six at `sr:8432-8439` (already owed by the prior Opus report). It is an orientation file; fix in place.

---

## (D) What I could not measure, and what would change the conclusions

- **Lindemann–Weierstrass is CITED-NOT-FETCHED.**
  - The P1 and P2 "incommensurate" verdicts rest on it, and on the asymptotic rates being exactly e, e/r_L and ρ(e). Those are DERIVED; measured ratios approach from below but have not converged (e-order 0.8814 vs 0.9053 at e = 3/5; modes 0.7237 vs 0.7418 at k = 60).
  - If a true sup-norm rate differed, P1 / P2 would need rederiving.
  - The refutation of H does **not** depend on this: P7 (equal rates 1/4 by unique factorisation and measurement, no ESC) refutes H in the strong cells under either reading, and P4 refutes it under Def R.
- **e-order rates at e = 1/10 and 3/10 were not measured.** The float truth floor was reached inside the estimation window, so B1 printed nan.
- **The root test is not converged:** \|a_p\|^{1/p} = 1.4487 at p = 201 vs 1/r_L = 1.5089. The ρ(e) closed form and the M = π/2 location of the Laplace limit are CITED-NOT-FETCHED.
- **The L levels for P1 / P2 use the coordinator-confirmed S1 depth jets.** I did not re-run the depth series.
- **The L1 definition's admissible coordinates were clarified after measuring** (digit expansions excluded). P6 / P7 are reported under both readings. A cleaner pre-registration would have named the admissible gradings.
- **The reach-schedule pattern (B.2.5) is post-hoc.** A fresh pre-registered pair set could refute it.
- **The Kepler three-slot factorisation uses two non-commuting operators.** If a single linear object is found whose eigenvectors / edges / eigenvalues give it (for example a Weyl-algebra representation), the fence in B.1.2 lifts and the Kepler reading becomes D1 proper.
- **Task A limits.**
  - PDF extraction can miss names inside figures or split across pages; Table 1 and the code blocks were read by eye.
  - Definition search covers every tracked `.py` under `docs/` on the current tree, a full all-refs history path list, and a `-G` pickaxe for 23 leaf names with a passing positive control.
  - Content-based search for "some dataset that does this job" (class_frequency, Ramachandran density, octopus / Physarum scoring) was not exhaustive.
  - The spike scripts for rows 9, 12, 20, 21, 56 were not run (numpy / scipy / healpy / external data).
  - The "171/171" Bell test count was not recounted, and PyPI was not queried.
- **Worktree hit disclosure.** One read-only `git grep` listed file names under `docs/srmech/.claude/worktrees/`. Those hits were excluded from every finding, and nothing there was opened or changed.
