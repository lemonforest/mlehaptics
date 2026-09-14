# F1370 — **the textbook's module paths audited (34 printed locations never existed; about 20 moved under ADR-0010; two arithmetic errors in the book), and the unboundedness duality read through distributional ⊗ relational ⊗ responsion: "exact finite-stage correspondence iff commensurate" is refuted with both off-diagonal corners, Kepler's lattice factorises over a non-commuting pair, a fourth convergence radius 2/ℯ appears, and `jacobi_eigvals(exact=True)` returns conjugate eigenvalues that compare equal**

**User (2026-09-14T14:45Z), as quoted verbatim in both F1371 provenance reports:** *"other shape for seach would be distributional(x)relatinal(x)resposion and that resonance is anisotropic, and that responsion is a measure of commensurateness"*

Session research, 2026-09-14, landed from the session scratchpad. This is the follow-up to F1369, worked by two independent researchers, Fable (high) and Opus (xhigh). Both reports are in `F1370_supporting/` verbatim, with scripts and small outputs. Instrument, as both state: srmech 0.9.0rc472 on `main` at `b398b8c46`, pure cell, numpy absent. Labels are the reports' own: MEASURED / DERIVED / CANDIDATE / CITED-NOT-FETCHED / DOES-NOT-MAP.

## A — every module path the textbook tells the reader to run

The book's appendix (p.181) pins it to srmech 0.4.2. Both reports find the `srmech.amsc.<module>` spellings were real when written and have since moved under ADR-0010: `amsc.kepler` → `math.kepler` (rc372); `amsc.{cyclic, dispatch, hdc, laplacian, primes, rational, …}` → `math.*` (rc373); `amsc.naming` → `introspect.naming` (rc367); `amsc.{tool_schema, _native, compose}` → `introspect.tool_schema` / `_native` / `cascade.compose` (rc376); `qm.*` → `physics.qm.*` (rc381, alias removed rc382).

| | Fable | Opus |
|---|---|---|
| audited | 70 = 64 `srmech.*` paths + 6 sister-package names | 69 = 63 path rows + 6 sister-package references |
| EXISTS | 11 | 9 |
| MOVED | 19 | 20 |
| printed location never existed | 34 of the 64 `srmech.*` paths (sister 2, functional equivalent 9, spike-script-only 9, nothing under any name 14) | **34 rows** (sister 1, functional equivalent 8, spike-script-only 7, never shipped 18), MEASURED by an all-history path list and a `-G` pickaxe with a passing positive control |

- **Still verifiable through shipped ops (examples both ran):** Thm 7.2's T = 999 and 999999/2 by exact closed form; ISCO 1 − √(8/9) = 0.0571909584…; Ω_sub ≈ 1.8127e-18 rad/s; `chsh_operator_norm()` = 2.8284271247461907; the shifted-circle eigenvalues on |λ − 1| = 1.
- **Unverifiable today, per Fable:** 7 rows (121/121 double-Hopf, octopus, Ramachandran density, class frequency, coupling intensity, QFT T-count, shadows). **The reports disagree on one:** Fable finds no script computing the 121-count; Opus classes that row SPIKE-SCRIPT-ONLY at `notes/spike216_compute.py:248` (`m2_m5_bipartite_test`). Not resolved here.

**Defects in the book that running the paths exposed** (Opus §A.4, MEASURED; the notebooks do not carry them):

1. **Ex. 8.4, p.69 (Newton–Raphson, e = 0.3, M = π/4).** The book's E2 = 0.99622 is wrong. Newton steps give E1 = 1.054646, **E2 = 1.044868**, E3 = 1.044853; `kepler_solve` gives E = 1.0448534569212085; the residual at 0.99622 is −0.0410.
2. **p.154 (Hubble tension).** t₀ = 13.787 gives ΔH₀/H₀ = 0.0767456 (**7.67%**), not the printed 7.69%. The notebooks' t₀ = **13.797** (`sr:1284`, `mfo:2143`) gives 0.076856 (**7.69%**) — three instruments agree. The notebooks are right.
3. p.33 prints 196 sign flips at depth 2 against its own spike's 98; p.24's "octonionic" Hopf example is quaternionic; pp.69/110 attribute the Antikythera recovery to Spike #127, which is the Physarum spike; the pp.183–184 quick start needs numpy and a removed `dense_laplacian` signature; Table 1 disagrees with pp.168–170 on Class C and Class J paths; p.170's "asymptotic-DoF modulation routine" never existed.

## B — the duality through distributional ⊗ relational ⊗ responsion

**What the record says, source-read by both.** The triple is D1's second naming (srmech notebook §3.59.1 / §3.59.3), not a seventh dictionary: slot 1 op / distributional / eigenvectors is **invariant** under Lⁿ; slot 2 operand / relational / edges goes **1-hop → n-hop**; slot 3 responsion / eigenvalues goes **λ → λⁿ**. "Resonance is anisotropic" is fenced by MFO §VIII.31.20 item 5. The record predicates commensurate / incommensurate **of the responsion's values** (§3.59.12); it never says the responsion "is a measure of" commensurateness.

### B1 — "exact finite-stage correspondence iff commensurate" is refuted, with both off-diagonal corners

- **Fable** (definitions fixed in the script docstring before any run): the hypothesis fails on **2 of 8 pairs**, and both failures have one shape — an exact finite-stage correspondence with incommensurate responsion values. **P3**, Heron against the continued fraction of √2: an exact subsequence (Heron n = convergent 2ⁿ − 1, via the shipped `best_rational` path length), but order-2 against order-1 rates. **P7**, the Class-L C₇ with Lⁿv against its eigen-expansion: exact, while `commensurability_verdict` on the exact `Qalg` ladder returns `inharmonic`, rational_rank 1. *"They vary independently."*
- **Opus** (pre-registered; sha256 `0e198576df7b22001ff7885adb9e9a55b7c7d4401054e6b6d9647dcfd0ca97dd`): *"H is REFUTED as stated, in every cell, and in both directions."* **Correspondence without commensurateness — P1**, Kepler depth ↔ e-order: an exact projection at every stage (L2), with rates e and e/r_L that are irrationally related at every rational e < r_L (DERIVED, resting on Lindemann–Weierstrass, CITED-NOT-FETCHED). **Commensurateness without correspondence — P7**, Pfaff two-mean ↔ Euler 4(atan ½ + atan ⅓): the identical rate 1/4, while no stage of one is ever a stage, projection or intrinsic jet of the other. *"Both off-diagonal corners are measured (P1; P7)."*
- Both relate the result to MFO §VIII.31.21's asymmetric-versus-inharmonic independence (Opus: CANDIDATE link).
- **Opus: "commensurate" is two words for a pair of frames.** In the value-ratio sense, `commensurability_verdict([Q(1,1), Q(4,25)])` → `harmonic`, rational_rank 2. In the step-count sense the same pair is incommensurate (log 2 / log 5). Any sentence using the word for frames must say which sense it means.

### B2 — Kepler's lattice factorises into the three slots, over a pair that does not commute

**Opus, MEASURED, exact, 272 cells (1 ≤ p ≤ 16, 0 ≤ k ≤ 16), 0 mismatches:**

```
c(p,k) = [H^p]_(k,0) · k^(p-1) / ( 2^(p-1) · p! )
```

- H = S − S⁻¹ is the chiral hop on the harmonic lattice ℤ, and D = diag(harmonic index).
- The support of [A^p]_(k,0), with A = S + S⁻¹, equals the cone {k ≤ p, k ≡ p mod 2}, with 0 disagreements.
- The lattice itself is re-validated against `bessel_j_fixed` at e = 3/5 to ≤ 3.5e-77.
- **The coordinator re-ran it: 272 cells, 0 mismatches.**
- **Fence, MEASURED: `[D, H] = A`.** The eigenbasis factor comes from D and the walk factor from H, and they do not commute, so these are not three reads of one Class-L object. Status: a **CANDIDATE** reading ("D1 shape over a non-commuting pair"), not D1, and not lodged as a seventh dictionary.
- Reading: depth and e-order index the same slot (relational reach), while modes index a different slot (the distributional window). None of the three Kepler rates is a responsion value of H or D (CANDIDATE); Heron / CF differs exactly there, since its rate is the eigenvalue ratio.

### B3 — direction dependence in the index lattice, and a fourth convergence radius

- **Fable, MEASURED with DERIVED limits.** Five directions through one lattice, each with its own per-step ratio. Along the diagonal (the leading e-order of each harmonic) the ratio tends to e·ℯ/2, so that direction converges only for **e < 2/ℯ ≈ 0.7358** (ℯ is Euler's number; measured ratio 0.3926 / 0.9160 / 0.9814 at e = 0.3 / 0.7 / 0.75). This is distinct from the rows (Laplace, 0.6627), the columns and the iteration (1), and each column's own tower (entire): *"Four directions, four radii."* At equal index n = K, depth error / mode error = 0.619, 0.249, 0.026 at n = 5, 10, 20 (e = 0.3).
- **Fable's verdict on the word:** DOES-NOT-MAP to "resonance is anisotropic" (the fence stands); it MAPS to *"frame-relative rate; the pair is asymmetric"*, which the record already states.
- **Opus** measures four index-space dependences and says none is spatial anisotropy or the Sakaguchi arrow: (a) a reach cone; (b) per-direction rate ratios log(depth)/log(mode) = 1.152 … 3.371 across e = 0.1 … 0.9; (c) a sign bit the CF frame carries (Pell norm alternating −1, +1) and Heron collapses (always +1); (d) irreversible against reversible stage maps.

### B4 — a defect in the exact eigen route

- **Opus B6, MEASURED:** `jacobi_eigvals(..., exact=True)` on `[[2,1],[1,0]]` returns two `Qalg` eigenvalues with identical `_m = (−1,−2,1)` and `_coords = (0, 1)`. They compare **`a == b` → True** and differ only in a float `_root` (−0.41421356237309503 against 2.414213562373095). Their field sum is 2α and their product α², not trace 2 and det −1. Opus files it as a CANDIDATE silent-wrong-answer class for the maintainer's ruling.
- **From the consolidation brief:** the coordinator records `a == b` True also for `[[1,1],[1,0]]`, and the maintainer slated the defect into the ALU arc's rc-F on 2026-09-14. Neither report measures the second matrix.

### B5 — what the triple adds to the F1369 draft amendments (Opus B.4, Fable B.4)

- **"Share only the limit" is too strong.** At stage n with K ≥ n, depth and modes are both exact on the whole e-order ≤ n jet (L1); depth ↔ e-order is a projection (L2).
- **Name the slot.** A finite-stage correspondence is a slot-2 fact; a rate is a slot-3 value. They vary independently (B1).
- **Say the tier** — Tier 3 / 2 / 1 for the Kepler / CF / Fibonacci responsions — and write "commensurate", not "harmonic".
- **An open contradiction on the "generator" word** (Fable C-B4, recorded, not decided): `mfo:6664` places `the_one` in the resonance slot, while the maintainer's 2026-09 direction says the object does not create, project or resonate.

## C — corrections owed (listed by the reports, not applied here)

Fable C-A1–C-A5 and C-B1–C-B5; Opus (C) 1–8. Among them:

- a textbook path-audit append to the MFO notebook;
- an errata append to `docs/srmech/notes/spike129_octopus_distributed_cognition_cascade_match.md:170` (`srmech.amsc.asymptotic_dof` never shipped);
- a new srmech notebook §3.59.x for B1 and B2;
- `docs/antikythera-maths/CLAUDE.md:9`, which says four dictionaries where the census has six;
- a tracker item for B4.

These belong to a later corrections step.

## D — not measured / not fetched (as the reports list)

- Lindemann–Weierstrass, the closed form of ρ(e), the Laplace-limit location and the Stirling limit are CITED-NOT-FETCHED. Opus's P1/P2 verdicts rest on them, but the refutation of H does not: P7 alone refutes it.
- Measured rates approach their limits from below without converging. Opus's e-order rates at e = 0.1 and 0.3 hit the float floor and print nan.
- The sister-package scripts and several numpy/healpy spike scripts were located, not run. The Bell "171/171" test count was not recounted.
- Opus clarified its L1 definition after measuring and reports P6/P7 under both readings. Fable's rate-commensurateness definition is a threshold instrument, disclosed as such.

## Supporting files

`F1370_supporting/` holds `fable_high_report.md` and `opus_xhigh_report.md` plus scripts and small outputs:

- `fable_high_scratch/`: `a_runs`, `b2_commensurate`, `b3_anisotropy`, `probe_paths` (`.py` + `.out`), and `gitlogS.txt`
- `opus_xhigh_scratch/`: `a1_resolve`, `a2_index`, `a4_equivalents`, `a4b_equivalents`, `b1_kepler_triple`, `b2_heron_cf`, `b3_pi_pairs`, `b4_classL`, `b5_register_and_exact`, `b6_exact_eig_check` (`.py` + outputs); `a1_resolve.json`; `a3_pickaxe.txt` (the empty null); `b0_preregistration.txt`; `extract.py`; `paths.py`

A `.gitattributes` (`* -text`) keeps the bytes exact, so the pre-registration sha256 can be re-checked. The only change to the reports is disclosed: in `fable_high_report.md`, two report-item references (opus §5b `#14`, opus `#16`) gained code-span backticks so they cannot autolink; the digits are unchanged.

- **Skipped for size (over 1 MB):** `opus_xhigh_scratch/a2_index.json` (4,058,326 bytes; the AST index `a2_index.py` rebuilds).
- **Not copied (repository- and PDF-derived text extractions, re-derivable by the command each report names):** `fable_high_scratch/{appendix_ascii.txt, appendix_pages.txt, path_context.txt, pdf_text.txt, srmech_modules.txt}`; `opus_xhigh_scratch/{all_history_paths.txt, book.txt, book_ctx_wide.txt, paths_ctx.txt, paths_raw.txt}`.

**Composes:** F1368, F1369, F1371.
