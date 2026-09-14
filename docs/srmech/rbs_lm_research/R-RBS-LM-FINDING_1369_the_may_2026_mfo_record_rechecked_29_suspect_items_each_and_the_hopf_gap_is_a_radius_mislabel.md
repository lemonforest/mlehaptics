# F1369 — **the May-2026 MFO record rechecked by two independent researchers: 29 suspect items each; the Kepler-form defect is one mislabel carried through the record; the Hopf per-mode gap is ruled a radius mislabel**

Session research, 2026-09-14, landed from the session scratchpad. Two researchers (Fable, Opus) worked the same brief without reading each other's files; both reports are in `F1369_supporting/` verbatim, with their scripts and small outputs. This finding states only what the reports state, with their labels: **MEASURED** (a command in the report printed it), **DERIVED**, **CANDIDATE**, **CITED-NOT-FETCHED**, plus the status words each report used.

**Shared setup, as both reports state it.** Early-era source of truth: `docs/antikythera-maths/mfo_spectral_research_notebook.md` at commit `7b6faa27a` (2026-05-22, the last commit touching it before 2026-05-23). The textbook PDF `docs/srmech/metric-field-and-its-primitives.pdf` (`9dd3f27fc`) is treated as a derived rendering and not proposed for editing. Instrument: srmech 0.9.0rc472, pure cell, numpy absent. The companion *Inners Guide to the Hyper Loop* is not in the repository.

## 1 — counts and families

| | Fable | Opus |
|---|---|---|
| suspect items (status other than STANDS) | **29**: rows 2, 3, 5, 8, 10, 11, 14a, 14c, 15, 16, 19, 20, 21, 22, 23, 25, 26, 27, 28, 29, 30, 32, 33 (evidence), 35, 36, 37, 38, 39, 41 | **29**: A1–A6, A7b, A8, A9, A12–A17 (15); B1, B2 (2); C1–C12 (12) |
| how the report groups them | *"the Kepler-form family (5, 14a, 14c, 20, 21, 22, 25, 27, 28, 29, 35, 36, 37, 38, 39) is one defect propagated fifteen ways; the frame-privileging family (2, 8, 10, 15, 26, 30) is one tension repeated six ways; row 19 is one tautology; rows 23 and 41 stand alone"* | A = infinity / unboundedness / bounded grammar / hidden fibre; B = the "generator" framing; C = the Kepler-shape family and everything downstream |

## 2 — what both measured the same

1. **Kepler's E(M) − M harmonics are (2/k)J_k(ke)** — MEASURED by both. Fable: the ratio to `bessel_j_fixed` is 1.000000000 at every (e, k) tested, while ε^k/k misses by 12–100% by k = 3–6. Opus: the Kapteyn lattice agrees with `bessel_j_fixed` to ≤ 4.2e-77.
2. **ε^k/k is exactly the pin-slot's own series.** Fable measures the ratio at 1.000000000 for k = 1..5 and DERIVES `atan2(sin M, cos M − ε) = M + Im log(1 − εe^{−iM})`, the Hipparchan eccentric-circle equation of centre. Opus marks the series itself STANDS (DERIVED) and MEASURES its exact home in Kepler motion: (ν − E) has harmonics 2β^k/k with β = e/(1 + √(1 − e²)), agreeing to 8 digits.
3. **The record's identities were self-comparisons** — TAUTOLOGICAL in both. Spike #29's *"ratio 1.0000 across 7+ harmonics"* checked the atan2 series against its own expansion. Spike #41's *"max diff 0.00e+00"* compared ε^k/k with ε^k/k (Opus quotes `spike_41_fibonacci_unity.py:117-119`).
4. **Spike #30B's and the AoE section's numbers are the true-anomaly equation of centre**, 2e, (5/4)e², (13/12)e³, not ε^k/k. Both measure 3.339884e-2, 3.485769e-4, 5.044712e-6 at e = 0.0167. Fable: *"Spike #30B's data were right … the 'ε^k/k' verdict wrapped around them is wrong by the factor (5/4)/2 at k=2."*
5. **The strict-K test cannot tell the series apart.** Fable: on the true Kepler coefficients it scores r² = 0.99991 / 0.99877 / 0.99308 at e = 0.0167 / 0.3 / 0.618. Opus: the instrument *"cannot return otherwise"*.
6. **The Fibonacci identity fails.** Fable: |ψ|^k/k against Kepler at e = 0.618 gives ratios 1.0494, 1.1383, 1.1075, 1.0267, 0.9260, 0.8204. Opus: the Fibonacci ratio converges at ψ² = 0.381966, not |ψ| = 0.618034.
7. **"Depth-3 confirmed unbounded" is a construction count** — TAUTOLOGICAL. Sign flips are 2∏r by construction; Opus measures 14, 98, 686, 42, 286 for the stacks tested.
8. **The shipped `pin_slot` docstring** (`srmech/math/kepler.py:62-64`, *"IS the Kepler equation of centre to second order"*) is wrong as written. Fable measures pin_slot(θ, 2e, 1) against ν − M at e = 0.0167: k = 1 ratio +1.000, k = 2 −1.600, k = 3 +2.462, so agreement is first-order only. Opus calls it MIS-CITED under the module's own definition of equation of centre (c₁ = 2e, where pin_slot's c₁ is ε). It is live in rc472.
9. **"Generator" is not May-era vocabulary.** Fable dates it to 2026-06-05 (`a48c7d4f5`; `one.py` `457dc9c7d`). Opus finds an IFS sense from 2026-05-26 (`9ef5d4829`), the One from 2026-06-05, and the addressing bump from 2026-07-24. Both rate the word OVERSTATED by the record's own evidence.
10. **The frame-privileging direction** ("asymptote = substrate, infinity = tool"; "polygon actual, circle shadow"; "integer-cyclic upstream") sits against R30 (2026-05-24: *"NEITHER is downstream-projection of the other"*). Fable rates it STANDS-W/TENSION; Opus rates it OVERSTATED.

## 3 — where they differed, and the ruling

- **The Hopf per-mode gap, MFO §VII.4.1.1** (`l(l+2) − l(l+1) = l`, read as the S¹ fibre's extra spectral degree of freedom over each S² mode). Fable row 7: **STANDS** (textbook identity; the discrete test relayed from PR #331). Opus A12: **FIT-REPORTED-AS-IDENTITY** — the arithmetic pairs unit-S³ degree l with unit-S² degree l, but the Hopf base is S² of radius ½, where the U(1)-invariant S³ modes (l = 2j) have eigenvalue 4j(j+1) = l(l+2) exactly, with no gap. MEASURED as integer arithmetic for l = 0..8 (0, 8, 24, 48, 80 on both sides); the radius-½ base is CITED-NOT-FETCHED as a textbook fact.
  **Coordinator ruling (2026-09-14):** the gap is a radius mislabel — the U(1)-invariant S³ modes on the radius-1/2 base have no gap. The ruling adopts the Opus reading; the MFO text is not corrected in this commit.
- **Opus only.** A5, the Kerr extremal gap sequence {2.000, 1.485, 0.282, 0.089}, is TAUTOLOGICAL: 2√(1 − x²) sampled at a/M = 0, 0.66985, 0.99001, 0.99901. A9, the closure conjecture's *"four independent positive verifications"*, is OVERSTATED: verification #2 was closed by broadening Class L's scope. B2 is CURIOUS: 𝕊 names both the One (dim 14) and the sedenions (dim 16). A16, Heron: error squares each step, and depth n equals continued-fraction convergent 2ⁿ − 1 (MEASURED).
- **Fable only.** Row 23: the book's Thm 7.2 says "super-logarithmic", but its proof gives logarithmic (α = 1) or power-law (α > 1) time-to-gap; and `srmech.asymptotic_dof.toy_modulation_time` and `srmech.cascade.cauchy_kernel` do not exist at rc472 (MEASURED absence). Row 32: a memory file still says "Class O".
- **Replacement word for "generator"** — CANDIDATE vocabulary in both reports. Fable: *register* / *carrier*, with *translate* as the verb. Opus: *form* / *reference form*.

## 4 — the measured two-frame instance: Kepler's E(M)

- **Fable F1 (MEASURED):** depth-n error scales as a power of e whose floor is n + 1. Exponents at depth 1: 3.00, 1.99, 2.98, 3.97, 4.95, 5.94; at depth 4: 5.01, 5.98, 4.95, 5.94, 5.00, 5.95. So depth n agrees with Kepler through O(eⁿ) in every harmonic. **F2:** from depth 2 the depth frame has infinite harmonic support, while the mode frame has exactly K harmonics — *"Neither truncation lattice contains the other."* **F4:** winding number 1.000000 at every truncation in both frames.
- **Opus S1 (MEASURED, exact `Fraction` to e⁹):** depth n reproduces every lattice cell with p ≤ n and none reliably at p = n + 1. The depth and mode truncations are *"row and column projections of one triangular lattice"* {(p, k): 1 ≤ k ≤ p, p ≡ k mod 2}, with *"No bijection"* between them. **S2:** per-step depth ratio tends to e (0.0928–0.0990 at e = 0.1; 0.2871–0.2940 at 0.3; 0.6908–0.6927 at 0.7), per-mode ratio tends to ρ(e) (closed form CITED-NOT-FETCHED; 0.1356 / 0.3986 / 0.8341). **Third frame:** the Lagrange e-power series at M = π/2 converges at e = 0.60 and 0.65 and **diverges at 0.70** (error +2.34e-01 at P = 121), while depth and modes both converge. *"An exact finite-stage correspondence does not carry convergence."*
- **CANDIDATE, not measured beyond Kepler and Heron:** two constructions of one limit are two summation orders of one multi-graded object, and each frame's unbounded index is the other's hidden fibre (Opus CAND-1). Fable's form: *"at least two frames per asymptotic object"*.
- F1370's follow-up refines one sentence here: at stage n with K ≥ n, depth and modes are both exact on the whole e-order ≤ n jet, so "share only the limit" is too strong.

## 5 — drafted, not applied

Both reports draft an amendment to the infinity stance and a table of corrections owed (Fable §5.1 with C1–C12; Opus §5a with 1–22). Both withdraw the direction "asymptote upstream, infinity downstream" and the 2026-05-17 sharpening (ε^k/k as the Kepler kernel; the Fibonacci identity), and both keep the vocabulary and Spike #28's finite-N validations. Applying any of it is a later corrections step, not this commit.

## 6 — not measured / not fetched (as the reports list)

Brouwer & Clemence 1961 §3.2 (opened by neither; each verdict that touches it rests on the record contradicting itself or on a measurement); the Laplace limit 0.6627434; the closed form of ρ(e); the Hopf base radius ½; Hurwitz/Adams; Hardy & Wright. Spikes #154 (the s* threshold), #45, #42/#43 and #212–#215 were not re-run. The PDF was read only at keyword-located pages.

## Supporting files

`F1369_supporting/` holds `fable_report.md` and `opus_report.md` (verbatim) and, from the two scratch folders, every script with its small outputs:

- `fable_scratch/`: `kepler_recheck.py`, `kepler_recheck.out`, `laplacian_frames.py`
- `opus_scratch/`: `s1_lattice.py` … `s5_kerr_sampling.py` with their `.out.txt`, `rerun_*.txt`, `bookgrep.py`, `mfo_may22.commit`

A `.gitattributes` there (`* -text`) keeps the bytes exact. The scripts are the researchers' own. Several use `abs()` and float `math` on the instrument side, which the reports disclose, and the numpy lines are absence probes.

**Not copied (all under 1 MB; none skipped for size):** the repository- and PDF-derived text extractions, each re-derivable by the command the report names — `fable_scratch/{book_text.txt, mfo_snapshot_2026-05-22.md, srmech_snapshot_2026-05-22.md}` and `opus_scratch/{mfo_may22.md, mfp.txt, may22_headings.txt, may22_terms.txt, a.txt, b.txt, g1.txt, g2.txt, sec_769_may.txt, sec_769_now.txt, sec_889_may.txt, sec_889_now.txt}`.

**Composes:** F1368, F1370, F1356 (Spike #28, rated STANDS by both).
