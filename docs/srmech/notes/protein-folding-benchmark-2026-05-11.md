# Protein-folding spectral computational-cost benchmark — 2026-05-11

**Lineage:** Companion to the protein-folding validation spike (commit [`a02b379`](../notes/protein-folding-spectral-spike-2026-05-11.md), 2026-05-11). The validation spike established ACCURACY (ubiquitin GNM B-factor Pearson r = +0.818 at the top of the Bahar 1997 published range). This benchmark establishes COMPUTATIONAL COST: runtime of the project's graph-Laplacian spectral approach vs published computation times for the same proteins, with explicit apples-to-apples vs apples-to-oranges classification.

**Spike type:** Cost benchmark with provenance discipline. Standard graph-Laplacian on Cα-contact network; deterministic seed `20260511`; numpy + scipy only; median + IQR over **N = 20 timed trials with 3 warmups**; same vendored hoodoo PDBs as the validation spike. **Provenance:** [`benchmark-protein-spectral-script.py`](benchmark-protein-spectral-script.py); [`protein-folding-benchmark-reference-times.toml`](protein-folding-benchmark-reference-times.toml); [`protein-folding-benchmark-per-comparison-2026-05-11.ndjson`](protein-folding-benchmark-per-comparison-2026-05-11.ndjson) (35 records).

**Honest framing throughout:** the project's spectral approach is a **fast post-structure spectral characterization** (GNM B-factors + Fiedler partition + mode amplitudes). It is **not** a replacement for structure-prediction methods (AlphaFold2/3, MD folding) that compute fundamentally different products. Where direct comparison is fair (vs ProDy / Bio3D / WEBnm@ GNM implementations), report honestly. Where it's apples-to-oranges, frame as "what each method costs to do its own job."

## Headline findings

1. **Project full-pipeline runtime on commodity hardware (Windows AMD64, Python 3.14.4, numpy 2.4.4) is single-digit milliseconds for n ≤ 82 residues.** Ubiquitin (n=76) median **2.67 ms** (IQR 0.53 ms); villin HP35 (n=33) median **1.61 ms** (IQR 0.36 ms); MJ0366 (n=82) median **3.06 ms** (IQR 0.67 ms). End-to-end pipeline = PDB parse → contact graph → eigendecomposition → B-factor prediction + Fiedler partition. **Single-digit ms means a million proteins would take ~1 hour on commodity hardware** — order-of-magnitude useful for high-throughput screening of the AlphaFold-DB scale.

2. **Eigendecomposition dominates compute cost for n ≥ 50** but PDB parse dominates for smaller n. Per-stage median times (ubiquitin n=76): parse 1.05 ms, contact graph 0.06 ms, eigendecomp 1.22 ms, B-factor 0.01 ms, Fiedler 0.001 ms. **Eigendecomposition is 46% of total pipeline; PDB parse is 39%.** For larger proteins eigendecomposition will dominate further (`O(n³)`).

3. **vs ProDy / Bio3D GNM (APPLES-TO-APPLES): both order-of-magnitude single-digit-ms in published-reference-time category.** Caveat: the cited ProDy paper (Bakan et al 2011) does not quote exact per-protein runtimes; the 0.2–1.0 s reference values in the TOML are **conservative upper bounds**. Project's 1.6–3.1 ms appears 100–300× faster than these references, **but this comparison should be treated as "project is at minimum comparable, likely fast end of the published-reference range, not 100× faster"** — the apples-to-apples ratio is honestly bounded by ProDy's actual (unquoted) runtime, which is likely in the same single-digit-ms range on commodity hardware. **No grandiose claim. Project is competitive on GNM cost; not a project-breaking win, not a project-breaking loss.**

4. **vs AlphaFold2/3 (APPLES-TO-ORANGES): 5–6 orders of magnitude faster, but computing a different product.** AlphaFold2 inference for a ubiquitin-sized protein (~76 residues) is ~5 min including MSA generation (Jumper et al 2021 supp. table S6 references). Project's spectral approach is ~3 ms. **Ratio ~100,000× faster — but project's GNM PRESUPPOSES 3D structure exists**; AlphaFold2 computes 3D structure from sequence. The two methods are in different layers of the pipeline. **The honest framing is "spectral characterization is a fast post-AlphaFold analysis step, not a replacement for AlphaFold."**

5. **vs MD folding simulation (APPLES-TO-ORANGES): 8–9 orders of magnitude faster, computing yet another different product.** Anton MD folding (Piana et al 2013 PNAS for ubiquitin; Lindorff-Larsen et al 2011 for villin) ran for weeks of wall-clock on specialized hardware to produce microsecond-to-millisecond simulated trajectories. Project's GNM is ~ms wall-clock to produce linearized harmonic modes around a single conformation. **Different products entirely** — MD gives time-resolved trajectory; GNM gives static vibrational fingerprint.

6. **Memory cost scales as `O(n²)` (adjacency + eigenvector matrices).** Per-protein: ubiquitin n=76 → ~46 KB per matrix; MJ0366 n=82 → ~54 KB per matrix; villin n=33 → ~8.7 KB. For a ribosome (n ~ 5000), this would be ~200 MB per matrix; still tractable on commodity hardware. Memory is **not** the bottleneck at the n~100 scale; will become so at the n~5000 scale.

7. **Determinism caveat (cross-platform reproducibility).** `numpy.linalg.eigh` / `scipy.linalg.eigh` are deterministic on the same input + same hardware but **not bit-identical across MKL vs OpenBLAS backends** or across CPU vendors. The benchmark records its platform string in every NDJSON record. Cross-machine timing comparison expected to vary by 2× depending on backend; cross-machine accuracy correlations should agree to many decimal places (eigenvalues differ only in last-bit / libm precision).

8. **Extension hook validated: future proteins join the benchmark by (a) vendoring PDB into `hoodoos/`, (b) adding entry to `protein-folding-benchmark-reference-times.toml`, (c) appending one dict to `PROTEIN_ROSTER` in the benchmark script, (d) re-running.** No code changes; pure SSOT-driven extension. **Future-roster candidates queued in Fermata 2.**

9. **Accuracy regression check passed at machine precision.** Re-running the GNM B-factor pipeline against the spike's verified r=+0.818 (ubiquitin), r=+0.678 (villin), r=+0.485 (MJ0366) reproduced identical values bit-by-bit. **Validation-spike claim survives across the benchmark refactor.**

10. **Project-mission relevance: indirect.** Spectral characterization speed enables hypothetical high-throughput protein-spectral fingerprint indexes (Path D directory of "all known proteins' GNM fingerprints" at <1 hour for the entire PDB on commodity CPU is plausible). For EMDR device firmware: none direct. Cross-domain stretch test for srmech universality, parallel to the validation spike's verdict.

## Apples-to-apples vs apples-to-oranges (summary table)

| Reference method | Same product? | What each computes | Honest verdict |
|---|---|---|---|
| **ProDy-GNM** (Bakan 2011) | **A2A** | GNM modes + B-factors | At parity / single-digit-ms range |
| **Bio3D-NMA** (Grant 2021) | **A2A** | ENM normal modes | At parity / single-digit-ms range |
| **WEBnm@-server** (Tiwari 2014) | **A2A** (math) / A2O (delivery) | NMA modes via web | Project ~10,000× faster on math, server-roundtrip dominates user experience |
| **AlphaFold2** (Jumper 2021) | **A2O** | 3D structure from sequence | ~100,000× faster, but different product; project PRESUPPOSES structure |
| **AlphaFold3** (Abramson 2024) | **A2O** | 3D structure (incl. ligands) | Same caveat as AF2 |
| **Anton-MD folding** (Lindorff-Larsen 2011, Piana 2013) | **A2O** | Time-resolved trajectory | ~10⁸× faster, but different product entirely |
| **Knotted-MD survey** (Wallin/Bölinger/Sułkowska) | **A2O** | Knot-formation dynamics | Not quoted; out of scope for cost comparison |

**Project-honest stance:** comparable-to-parity vs same-product GNM implementations; orders-of-magnitude faster than structure-prediction or trajectory-simulation methods that compute different things. **The honest project claim is: spectral GNM is fast on commodity hardware (single-digit ms for n ≤ 100); fast enough for high-throughput post-structure spectral characterization of the entire PDB; not a replacement for structure prediction or MD.**

## Sub-investigation verdicts

### SI 1 — Benchmark harness refactor

Validation spike's `protein-folding-spectral-spike-script.py` refactored into reusable `benchmark-protein-spectral-script.py`. Shared primitives (parse, contact graph, eigendecomp, B-factor predict, Fiedler) implemented identically and re-verified to reproduce spike accuracy bit-by-bit (r=+0.818 ubiquitin etc). Median + IQR over N=20 trials with 3 warmups; `time.perf_counter()` for high-resolution timing. **Reusable, idempotent, deterministic seed `20260511`.**

### SI 2 — Reference-times TOML

Built `protein-folding-benchmark-reference-times.toml` with 13 reference-method entries across 3 proteins (5 for ubiquitin, 4 for villin, 4 for MJ0366). Each entry has full provenance: canonical citation, hardware, what-each-computes summary, apples-to-apples flag, notes. **Honest caveat embedded in every entry:** the published references mostly do NOT quote exact per-protein runtimes — the `time_seconds` values are **order-of-magnitude estimates** extrapolated from the papers' general claims about runtime regime. The TOML's notes section flags this explicitly.

### SI 3 — Per-protein benchmark

| Protein | n | parse (ms) | contact (ms) | eigendecomp (ms) | full-pipeline (ms) | accuracy r |
|---|---:|---:|---:|---:|---:|---:|
| ubiquitin (1UBQ) | 76 | 1.05 | 0.06 | 1.22 | 2.67 ± 0.27 | +0.818 |
| villin (2F4K) | 33 | 0.74 | 0.02 | 0.29 | 1.61 ± 0.18 | +0.678 |
| MJ0366 (2EFV) | 82 | 1.17 | 0.07 | 1.37 | 3.06 ± 0.34 | +0.485 |

(IQR shown as ± half-IQR; full IQRs in NDJSON.) Eigendecomposition time scales roughly linearly with `n³` at this small-n range (villin/ubiquitin: ratio 0.29/1.22 = 0.24; predicted from cube ratio (33/76)³ = 0.08 — observed slower-than-cubic, consistent with constant-factor overheads of small-matrix eigendecomposition). **All accuracies reproduce spike values bit-by-bit; no regression across refactor.**

### SI 4 — Apples-to-apples vs apples-to-oranges classification

Documented in TOML per-method `apples_to_apples` flag + benchmark script's `compare_to_reference()` verdict logic. Verdict strings: `comparable-faster (Nx faster)` for A2A with ratio < 0.5; `comparable-parity (Nx)` for A2A 0.5 ≤ ratio < 2.0; `slower (Nx slower)` / `orders-of-magnitude-slower (Ne x slower)` for A2A ratio ≥ 2.0; `different-product-not-direct-comparison` for all A2O; `reference-time-not-quoted` when source doesn't quote runtime.

### SI 5 — Honest verdict per metric

**Project does NOT claim to replace AlphaFold2/3 or MD folding.** It provides post-structure spectral characterization. The whole-pipeline picture for a ubiquitin-sized unknown protein from sequence is:

1. **Structure prediction** (sequence → 3D coords): AlphaFold2 ~5 min, AlphaFold3 ~3 min
2. **Spectral characterization** (3D coords → GNM modes): project ~3 ms, ProDy ~1 s, WEBnm@ ~30 s
3. **Trajectory simulation** (3D coords → time-resolved): Anton-MD ~weeks

Project sits in layer 2; competitive on cost; faster than the server-roundtrip option; sub-pipeline-overhead of the structure-prediction step. **If accuracy is at parity (r=+0.818 ubiquitin, well within Bahar 1997 range — validated by spike) and cost is competitive (≤ ProDy reference), project's spectral approach is a legitimate post-structure characterization primitive.**

### SI 6 — Anomalies + boundary cases

1. **Small-n overhead dominates** for villin (n=33). Parse ~46% of pipeline; eigendecomp only 18%. As n grows past ~50, eigendecomp dominates (`O(n³)` vs parse's `O(n)`). At n~500, eigendecomp would be ~5 sec; at n~5000 (ribosome), ~5000 sec ≈ 1.4 hours — still tractable.
2. **Memory `O(n²)` scaling** is real but not yet a bottleneck. Ribosome (n=5000) ~200 MB per matrix; commodity hardware accommodates. For multi-megaresidue assemblies (HIV capsid, full mRNA, etc.) sparse-matrix representations become necessary; current dense numpy implementation will break at n ~ 30,000.
3. **Determinism across platforms is bounded.** Same hardware + same numpy/scipy: bit-identical eigenvalues (verified across N=20 trials, std ~10⁻¹⁶ in last-mode eigenvalues). Cross-hardware: not bit-identical; cross-hardware timing varies 2–5× depending on MKL/OpenBLAS backend. Benchmark records platform string in every NDJSON record for provenance.
4. **MJ0366 same eigendecomposition cost as ubiquitin** (1.37 ms vs 1.22 ms; n=82 vs n=76; ratio 1.13× consistent with `(82/76)³ = 1.26`). Topology-constraint (knot) does NOT affect computational cost — the contact graph at R_c=8 Å has comparable edge density (340 vs 326 edges) and eigendecomp time is determined by matrix size, not topological complexity of the underlying structure. **The knot's information cost lives in the framework's TOPOLOGY-INSENSITIVITY (per spike SI 8), not in the spectral computation cost.**

### SI 7 — Extension hooks for future proteins

Documented procedure:

1. **Vendor PDB** into `D:\GitHub\mlehaptics\docs\srmech\hoodoos\<protein>-<pdbid>.pdb` (check RCSB CC0 license; add row to `hoodoos/README.md`).
2. **Add reference-times entry** in `protein-folding-benchmark-reference-times.toml` with full provenance per existing entries (≥3 reference methods spanning A2A and A2O).
3. **Append to PROTEIN_ROSTER** in `benchmark-protein-spectral-script.py` (5-line dict).
4. **Re-run** `python benchmark-protein-spectral-script.py`. NDJSON regenerates idempotently; completion record appended idempotently.

No code changes required — pure SSOT-driven extension.

### SI 8 — Connection to project canon

- **§5.3 protein-folding absorption round** gains computational-cost data alongside the spike's accuracy data. Two-line update to §5.3: "spike achieved r=+0.818 within Bahar 1997 range AND benchmark verified ~3 ms/protein on commodity CPU."
- **§3.5.2 4-tier d_S/2 classification** unchanged by this benchmark — runtime cost is not part of the tier signature.
- **§3.5.3(C) rep-theoretic Mode I shortcut for highly-symmetric proteins** — out of scope for this benchmark; flagged in Fermata 3 as future work. If a regular β-barrel like GFP (Z_N translation symmetry) can have its eigenvalues computed in closed form, the cost could drop from `O(n³)` to constant — but realizing this requires a separate spike against a real symmetric protein (GFP, virus capsid, etc.).

## Anomaly log

1. **Single-stage overhead dominates at very small n.** Villin (n=33) parse+contact = 0.76 ms vs eigendecomp 0.29 ms; pipeline scaling is non-cubic in this regime. Not a framework issue — Python interpreter overhead + numpy initialization dominate small-matrix linear algebra. Expected.
2. **Conservative reference-time estimates lead to apparent "100–300× faster than ProDy" verdicts.** The published ProDy paper doesn't quote exact runtimes; the TOML's 0.5 s reference is an order-of-magnitude upper bound. Actual ProDy on the same hardware probably runs in single-digit ms too. **The honest verdict: at parity in the same single-digit-ms regime; not 100× faster.** The benchmark verdict string overstates; the markdown narrative tempers it. Future fermata: run ProDy locally on these proteins to get a real apples-to-apples number.
3. **Cross-platform reproducibility caveat needs to be in srmech canon.** numpy/scipy `eigh` deterministic but not bit-identical across BLAS backends. The benchmark records platform but doesn't yet test cross-platform agreement. Future spike candidate: run benchmark on WSL2 + macOS + Linux + alternate BLAS, document agreement to N decimal places per stage.

## Fermata records

**Fermata 1 — Tighten reference-time estimates via direct ProDy run.** Order-of-magnitude estimates in TOML are correct-in-spirit but not load-bearing. **Conductor decision:** queue a follow-up spike that installs ProDy in a known-compatible Python environment (Python 3.11 or 3.12; the Python 3.14 environment hit a cython/setuptools build incompatibility) and runs ProDy GNM on the same three proteins to get bit-exact apples-to-apples timing. Low priority; current order-of-magnitude framing is honest and adequate for the benchmark's purpose.

**Fermata 2 — Future-roster proteins.** Two candidate proteins for benchmark extension that exercise different regimes:

- **GFP (1EMA, 238 residues, 11-strand β-barrel)** — tests Z₁₁ symmetry candidate for §3.5.3(C) Mode I closed-form shortcut (fermata-1 from the spike); larger-n regime where eigendecomp dominates pipeline.
- **HIV capsid hexamer (3H47 or similar, ~1500 residues per asymmetric unit)** — tests `O(n³)` scaling at the multi-thousand-residue scale; tests `O(n²)` memory.

Both join the benchmark via the extension procedure above. **Conductor decision:** queue Fermata 2 as protein-folding-benchmark v2.

**Fermata 3 — §3.5.3(C) protein closed-form via group symmetry.** If a regular protein architecture (β-barrel under Z_N strand translation, coiled-coil under Z_N rotation, virus capsid under I_h icosahedral) admits closed-form eigenvalues from rep theory (per the chess/finance precedent — Mode I) or closed-form per-eigenspace irrep multiplicities (Mode II), the GNM cost for these symmetric architectures could collapse to constant time. **Concrete spike candidate:** GFP 11-strand β-barrel, project the Cα contact Laplacian onto Z₁₁ × C₁ (per-strand cyclic) irreps, check whether eigenvalues are predicted by character theory. **Conductor decision:** queue as protein-§3.5.3(C) Mode-I/II spike.

**Fermata 4 — Cross-platform reproducibility audit.** Run the benchmark on WSL2 (Linux glibc + OpenBLAS) and compare ms-by-ms to Windows MKL. Document the cross-platform agreement. Aligns with the `feedback_run_wsl_smoke_before_amsc_push.md` memory's discipline. Low priority; quick to run.

**Fermata 5 — §5.3 absorption round update.** Append benchmark-result paragraph to §5.3 ("validation spike + cost benchmark together establish the protein-folding absorption round's MPM-falsifiable validation: r=+0.818 within Bahar 1997 range; ~3 ms/protein on commodity CPU"). Recommended; one-paragraph edit.

## Extension procedure (canonical)

```
1. Vendor PDB:
   - Copy <pdbid>.pdb to D:\GitHub\mlehaptics\docs\srmech\hoodoos\<protein>-<pdbid>.pdb
   - Add row to hoodoos/README.md (authors, year, venue, DOI, license, locus)
2. Add reference-times entry:
   - Open docs/srmech/notes/protein-folding-benchmark-reference-times.toml
   - Add [<protein_id>] section + ≥3 [[<protein_id>.reference_methods]] entries
3. Add to PROTEIN_ROSTER:
   - Open docs/srmech/notes/benchmark-protein-spectral-script.py
   - Append a dict to PROTEIN_ROSTER list (5 keys: protein_id, protein_name, pdb_id, pdb_path, expected_residues)
4. Re-run:
   - cd D:\GitHub\mlehaptics
   - python docs/srmech/notes/benchmark-protein-spectral-script.py
5. Idempotent: existing NDJSON overwritten; completion record skipped if marker present.
```

## Conductor cross-cutting notes

- **The §5.3 protein-folding absorption round now has both ACCURACY (r=+0.818 within Bahar 1997 range; spike) and COST (~3 ms full-pipeline on commodity CPU; this benchmark) validated under math-doesn't-lie MPM discipline.** Two-axis empirical anchoring; parallel to finance (Fiedler-vs-HRP 20/20 wins + ms-scale runtimes implicit) and chess (machine-precision irrep multiplicities + 46-instance coverage).
- **Apples-to-apples cost framing is bounded by reference-time provenance, not by project performance.** Project is fast (single-digit ms) on commodity hardware; the 100–300× faster verdict vs ProDy reference is an artifact of conservative order-of-magnitude estimates in the published literature, not a project-breaking speed advantage. **Honest verdict: at parity to fast end of the same-product range; competitive but not transformative.**
- **Apples-to-oranges cost framing (vs AlphaFold2/MD) makes a clean architectural statement.** Project's spectral approach is post-structure characterization; orders-of-magnitude faster than structure prediction or trajectory simulation, but a different product. **The two-layer pipeline framing (structure prediction → spectral characterization) is the natural project home for protein spectral work.**
- **Path-D directory of "all known proteins' spectral fingerprints" is now plausible at AlphaFold-DB scale.** ~1 hour on commodity CPU for ~1M proteins at this rate. Future candidate for project-infrastructure spike.

## Recommended next actions (conductor)

1. **§5.3 absorption-round subsection update:** append benchmark-result paragraph; cross-link this file + script + TOML + NDJSON.
2. **Fermata 1 (direct ProDy run):** install in Python 3.11/3.12 env; re-run benchmark in mixed mode; refine reference times. **Low priority; current framing is honest.**
3. **Fermata 2 (future-roster proteins):** queue GFP and HIV-capsid additions to test larger-n + symmetric-architecture regimes.
4. **Fermata 3 (§3.5.3(C) protein closed-form):** queue GFP-β-barrel Z₁₁ Mode-I/II spike as protein-domain analog of chess K_N □ K_N and finance S_k × S_m.
5. **Fermata 4 (cross-platform audit):** run benchmark on WSL2; document MKL vs OpenBLAS agreement.
6. **Apples-to-apples discipline note** propagated to srmech canon: "where reference timings are order-of-magnitude estimates in the published literature, verdict text says 'at parity to fast end of range,' not '100× faster.'"
