# Spike #12C — Virasoro Casimir from Liouville–Nekrasov representation of Λ_ℓm(aω): SCOPE

**Date:** 2026-05-13
**Status:** SCOPING PROPOSAL — NOT YET RUN. Awaiting user review.
**Branch:** `research/spike-12c-virasoro-liouville-nekrasov`
**Lineage:** Follow-up to Spike #11 (PR #359, abelian KY tower negative) and Spike #12A (PR #361, KY ⊕ photon-ring SL(2,R) interpolation negative). Spike #12A's own `rec_2` (Phase 6 next-step record, NDJSON of PR #361) explicitly named this spike.
**Discipline:** PDF-verification per `feedback_pdf_extraction_citation_discipline.md`; no manufactured closed-form; honest negative is a valid outcome.

---

## 0. Two attribution corrections caught *during scoping*

Per the running tally — Spike #11 caught one, Spike #12A caught two more. **This scoping run caught two further:**

1. **`arXiv:2105.04122` is NOT the BLLT Kerr/CFT² paper.** The user-supplied scoping prompt named `arXiv:2105.04122` as a candidate BLLT 2022 ID. PDF-verification on 2026-05-13 returns Gaoqing Cao, "Macroscopic transports in a rotational system with an electromagnetic field," Phys. Rev. D 104, 031901 (2021) — unrelated nuclear-theory paper. The correct BLLT 2022 paper is **`arXiv:2105.04483`** (already correctly cited in the 2026-05-12 KY literature review, table row 10). PDF-retrieved + `pdftotext`-extracted 2026-05-13; title, authors, section structure, eq. (39), eq. (95), eq. (24) verified.

2. **`arXiv:1811.11912` is NOT Aminov–Grassi–Hatsuda 2019.** The 2026-05-12 KY literature review (table row 9) listed `arXiv:1811.11912` as "Aminov, Grassi, Hatsuda 2019, 'Black Hole Quasinormal Modes and Seiberg-Witten Theory' / 'Kerr-de Sitter QNMs via accessory parameter expansion'." PDF-verification on 2026-05-13 returns Novaes–Marinho–Lencsés–Casals, "Kerr–de Sitter Quasinormal Modes via Accessory Parameter Expansion," JHEP 05 (2019) 033. The actual Aminov–Grassi–Hatsuda paper "Black Hole Quasinormal Modes and Seiberg-Witten Theory" is **`arXiv:2006.06111`** (RUP-20-18, 2020 — not 2019), abstract verified to claim closed-form NS-limit expressions for spin-weighted spheroidal eigenvalues. This is a second misattribution in the same KY-Kerr review.

**Running tally — 5 misattributions caught by PDF-verify discipline across this arc:**

| # | Caught by | Original (wrong) | Correct |
|---|---|---|---|
| 1 | Spike #11 | Houri-Tanahashi-Yasui 2024 | Gray-Kubizňák 2024 (arXiv:2401.03553) |
| 2 | Spike #12A | HKLS arXiv:2207.06435 | HKLS arXiv:2205.05064 |
| 3 | Spike #12A | "Hadar-Lupsasca-Strominger 2023" for arXiv:2309.02262 | Xue-Jiang-Zhang 2023 |
| 4 | Spike #12C scope | BLLT arXiv:2105.04122 | BLLT arXiv:2105.04483 |
| 5 | Spike #12C scope | AGH arXiv:1811.11912 (2019) | AGH arXiv:2006.06111 (2020); 1811.11912 is Novaes–Marinho–Lencsés–Casals 2019 |

The discipline is load-bearing. Per `feedback_pdf_extraction_citation_discipline.md`: when citing post-2020 papers, retrieve the PDF and verify title + authors + arXiv ID.

---

## 1. The BLLT 2022 dictionary — PDF-verified

**Paper:** Bonelli, Iossa, Lichtig, Tanzini, "Exact solution of Kerr black hole perturbations via CFT² and instanton counting. Greybody factor, Quasinormal modes and Love numbers," `arXiv:2105.04483`, Phys. Rev. D **105**, 044047 (2022). PDF retrieved + extracted 2026-05-13; sections §3.4 ("The angular dictionary") and §5.3 ("Angular quantization") are load-bearing here.

### 1.1 The Teukolsky angular equation, Schrödinger form

BLLT eq. (9), angular part, with `x = cos θ`, `c = aω`:

```
∂_x[(1 − x²) ∂_x S] + [(cx)² + λ + s − (m + sx)²/(1 − x²) − 2csx] S = 0
```

where `λ = Λ_ℓm(aω) + a²ω² − 2amω` (BLLT eq. (10), `_λ_,s := λ + a²ω² − 2amω`, but they then drop the `,s` subscript). After change of variables `z = (1+x)/2`, `y = √((1−x²)/2) · S`, this becomes a confluent Heun equation in Schrödinger form (BLLT eq. (15)).

### 1.2 The angular dictionary (BLLT eq. (39))

The confluent Heun equation in Liouville-CFT semi-classical form maps to gauge-theory parameters via:

| Black-hole parameter | Liouville/CFT parameter | Role |
|---|---|---|
| `c = aω` (dimensionless spin) | `Λ_inst = 4c = 4aω` | Instanton counting parameter (NS Ω-background) |
| `s` (spin weight) | `m₃ = −s` | Adjoint mass in N=2 SU(2) Nf=3 |
| `m` (azimuthal index) | `a₁ + a₂ = −m` | Liouville momenta combination |
| `s` (spin weight) | `a₂ − a₁ = −s` | Liouville momenta combination |
| **`Λ_ℓm(aω)`** (sep. constant) | **`E = 1/4 + c² + s(s+1) − 2cs + λ` so `E = a² − F_inst + …`** | **Schrödinger-energy parameter ↔ Casimir-like role** |

Explicitly: `a₁ = (m − s)/2`, `a₂ = (m + s)/2`, `m₃ = −s`, `Λ_inst = 4aω`, and the "Liouville accessory parameter" / Schrödinger energy `E` is

```
E = 1/4 + c² + s(s+1) − 2cs + λ
```

so the **angular separation constant is recovered as** `λ = E − 1/4 − c² − s(s+1) + 2cs`.

### 1.3 Where Λ_ℓm(aω) actually lives in the CFT (BLLT eq. (95))

The angular quantization condition (BLLT eq. (95), §5.3, p. 20):

```
λ − λ₀ = 2cs − c² − F_inst(1/2 + ℓ, −m, −s, −s; Λ_inst = 4c)
```

where `λ₀ = ℓ(ℓ+1) − s(s+1)` is the small-aω limit (BLLT eq. (94)) and `F_inst(a; m₁, m₂, m₃; Λ_inst)` is the Nekrasov–Shatashvili instanton free energy of N=2 SU(2) with Nf=3 fundamental hypermultiplets.

**This is the load-bearing equation.** It expresses `Λ_ℓm(aω)` as `ℓ(ℓ+1) − s(s+1) + 2caω⋅s − a²ω² − F_inst(series in aω)`. The "exact" closed form *is* the F_inst — a convergent power series in `Λ_inst = 4aω`, summed over Young-tableau instanton sectors per the Nekrasov combinatorial formula.

### 1.4 Status of the dictionary

✅ **PDF-verified 2026-05-13.** All four anchor equations (BLLT (9), (10), (39), (95)) extracted and cross-checked. Sections §3.4 + §5.3 are the canonical reference for this scope.

---

## 2. Virasoro Casimir on the BLLT-identified module

### 2.1 The Virasoro Casimir question, precisely

The Virasoro algebra has commutation relations

```
[L_n, L_m] = (n − m) L_{n+m} + (c/12)(n³ − n) δ_{n+m, 0}.
```

It is an *infinite-dimensional* Lie algebra. **Virasoro has no quadratic Casimir in the usual sense** — there is no central element of `U(Vir)` quadratic in the generators that commutes with everything. (The center is generated by `c` itself; quadratic combinations like `Σ L_{−n} L_n` are *not* central — they have nontrivial commutators with `L_m` for `m ≠ 0`. The only honest Casimir-like quantity on a *Verma module* is `L₀`, the energy.)

On a Verma module `V(c, Δ)` built on a highest-weight state `|Δ⟩` with `L₀|Δ⟩ = Δ|Δ⟩`, `L_n|Δ⟩ = 0` for `n > 0`, the operator `L₀` has eigenvalue spectrum `{Δ, Δ+1, Δ+2, ...}` on the descendants `L_{−1}|Δ⟩, L_{−2}|Δ⟩, ...`. So **on the highest-weight state `L₀` IS the "Casimir" and its eigenvalue is the conformal weight Δ**.

### 2.2 The Liouville conformal weight Δ

For Liouville CFT with `c = 1 + 6Q²`, `Q = b + 1/b`, primary `V_α = e^{2αφ}` has conformal weight

```
Δ_α = α(Q − α) = (c − 1)/24 + ((Q/2) − α)² · (something)
```

More usefully parametrized: write `α = Q/2 + a`, then `Δ_α = Q²/4 − a²`. In the BLLT angular dictionary (§1.2), the Liouville momenta `a₁ = (m − s)/2`, `a₂ = (m + s)/2` are these `a`-parameters, so their conformal weights are

```
Δ_{α₁} = Q²/4 − a₁² = Q²/4 − (m − s)²/4
Δ_{α₂} = Q²/4 − a₂² = Q²/4 − (m + s)²/4.
```

In the semi-classical limit `b → 0` (`c → ∞`) used by BLLT, `Q ≈ 1/b → ∞`, and conformal weights are rescaled to keep the Schrödinger picture finite. The standard Nekrasov–Shatashvili rescaling sets `Δ_i = δ_i / b²` with `δ_i` finite, and the rescaled weight `δ` becomes the Seiberg–Witten "gauge-theory mass" parameter.

### 2.3 The intermediate-channel `a` parameter — where Λ_ℓm hides

The 4-point Liouville correlator on the sphere has an intermediate-channel weight `Δ_α = α(Q − α)` for some `α = Q/2 + a` with `a` *the* intermediate-channel momentum. Per BLLT §5.3, **`a` is determined by the regularity condition (BLLT eq. (92)): `a = 1/2 + ℓ`** (with `ℓ ≥ max(|m|, |s|)`). Then

```
E = a² − F_inst(a; m₁, m₂, m₃; Λ_inst)         (BLLT, semi-classical Liouville)
```

The angular separation constant `λ = Λ_ℓm(aω) − a²ω² + 2amω` (eq. (10) sign convention) is then `λ = E − 1/4 − c² − s(s+1) + 2cs`, giving eq. (95).

So in Virasoro-Casimir language:

> **On the intermediate-channel Verma module `V(c, Δ_α)` with `α = Q/2 + (ℓ + 1/2)`, the eigenvalue of `L₀` is**
> ```
> Δ_α = Q²/4 − (ℓ + 1/2)²
> ```
> **and the angular separation constant `Λ_ℓm(aω)` is obtained from this by adding (i) the Liouville Schrödinger-frame shift `1/4 + c² + s(s+1) − 2cs`, AND (ii) the Nekrasov instanton free energy `F_inst(1/2 + ℓ, −m, −s, −s; Λ_inst = 4aω)` summed over all instanton sectors.**

### 2.4 The compression verdict (the load-bearing question)

**`L₀` alone — i.e. the "true" Virasoro Casimir — gives ONLY the `aω = 0` limit `Λ₀ = ℓ(ℓ+1) − s(s+1)`.** The full `Λ_ℓm(aω)` requires `L₀ + F_inst`, where `F_inst` is an infinite series in `Λ_inst = 4aω` summed over instanton-Young-tableau sectors:

```
F_inst(a; m_i; Λ) = Σ_{n=1}^{∞} F_n(a; m_i) Λ^n,   F_n = sum over partitions of |Y| = n
```

The series converges (BLLT §4.3 demonstrates convergence numerically) but is not a finite expression in elementary functions. **In Virasoro-Casimir language: `Λ_ℓm` is the eigenvalue of `L₀` PLUS a generating function of higher-mode Virasoro descendants — not the eigenvalue of any single Casimir.**

This is the *honest-negative possibility* the user's scoping prompt explicitly flagged (§6 of the brief). **It is the most likely outcome.**

---

## 3. The generic-aω regime — does Liouville close the Spike #11 gap?

### 3.1 What Spike #11 actually ruled out

Spike #11 (PR #359) proved the KY 4-operator algebra `{□, K, L_ξ, L_η}` is **abelian** on joint eigenstates `|μ², Λ, ω, m⟩`. Therefore every polynomial in those eigenvalues is "central" but informationally equivalent to the joint tuple — no compression.

### 3.2 What Liouville-Virasoro gives that KY does not

The Virasoro algebra is **non-abelian**, infinite-dimensional, with infinitely many independent `L_n` modes. The intermediate-channel Verma module `V(c, Δ_α)` is therefore a genuine non-trivial irrep, and `L₀` is a genuine Casimir-like quantity (uniquely identifying the irrep label `Δ_α`).

But: **the irrep label `Δ_α = Q²/4 − (ℓ + 1/2)²` reproduces only the `aω = 0` limit of Λ_ℓm.** The `aω`-dependence is *outside* the Casimir — it comes from `F_inst`, which sums Virasoro descendants in the instanton counting.

### 3.3 So does Liouville-Casimir close the gap at generic aω?

**Verdict (predicted, with one caveat below):** ❌ **NO** — the Liouville/Virasoro Casimir `L₀` reproduces only `Λ₀ = ℓ(ℓ+1) − s(s+1)`, the same `aω = 0` limit that the CMS SL(2,R) Casimir already reaches. The generic-`aω` `Λ_ℓm(aω) − Λ₀` is *not* a Casimir eigenvalue — it is an instanton-summed *correlator*. This is structurally the same kind of result as Spike #11: the algebraic Casimir is informationally equivalent to a label, not a generating function.

**Caveat that makes this a real spike not a settled question:** the AGT correspondence relates Virasoro conformal blocks to *Nekrasov partition functions*, and there is a notion of "higher Casimir" / `W_∞`-type / quantum-group Casimir in the Nekrasov–Shatashvili integrable-system reading. Under the **Bethe/Gauge correspondence** (Nekrasov–Shatashvili 2009), the NS limit of N=2 SU(2) Nf=3 maps to an integrable system (deformed XXX spin chain / Gaudin model) whose **Hamiltonians are infinite in number and form a commutative algebra**, with `Λ_ℓm(aω)` realized as a *joint eigenvalue* of this commutative tower. The first Hamiltonian gives `L₀`; the second gives an `a²`-coefficient; the n-th gives the n-th instanton correction.

So there *is* a generalized "Casimir tower" structure — but it is an *abelian tower* of commuting Hamiltonians, structurally analogous to Spike #11's abelian KY tower. The compression problem replicates: an abelian tower's joint eigenvalues are informationally equivalent to the tuple itself.

### 3.4 Comparison summary table

| Algebra | Type | "Casimir" | What it reproduces of Λ_ℓm | Compression? |
|---|---|---|---|---|
| Virasoro `Vir` | infinite non-abelian | `L₀` on Verma | `Λ₀ = ℓ(ℓ+1) − s(s+1)` only | ❌ NO at generic aω |
| Liouville intermediate `V(c, Δ_α)` | non-abelian Verma | `L₀`, eigenvalue `Δ_α` | same: `ℓ(ℓ+1)` part only | ❌ NO at generic aω |
| Nekrasov–Shatashvili commuting tower | infinite abelian (Bethe/Gauge) | full tower `{H_n}` | full Λ_ℓm(aω) via joint eigenvalue | (Same Spike #11 obstruction): joint-tuple, no compression |
| Spike #11 KY tower `{□, K, L_ξ, L_η}` | 4-dim abelian | full tuple | full set `(μ², Λ, ω, m)` | NO (Spike #11 negative) |
| HKLS photon-ring sl(2,ℝ) | 3-dim non-abelian | quadratic Casimir = 3/16 | eikonal QNM frequencies | YES, but only eikonal regime |
| CMS SL(2,ℝ)² | low-Mω hidden conformal | `C_L + C_R = 2λ_S²(ℓ)` | low-Mω scalar QNMs | YES, but only low-Mω regime |

**Prediction:** Spike #12C will reproduce the same structural negative pattern as Spike #11, with the Virasoro Casimir compressing only the `aω = 0` data (same as CMS at low-Mω, modulo conventions).

---

## 4. Is this the same SL(2,ℝ) as Spike #9/#10 (CMS), or different?

The CMS hidden-conformal SL(2,ℝ)_L × SL(2,ℝ)_R is a **finite-dimensional** symmetry of the scalar wave equation in the *low-Mω* regime, derived from the conformal coordinates on the BTZ-like effective 2D geometry. CMS Casimir is the standard `−J₀² + (J₊J₋ + J₋J₊)/2`, with eigenvalue `Δ(Δ−1) = ℓ(ℓ+1)` on the relevant rep — closed-form in ℓ but valid only for `Mω ≪ 1`.

Liouville's Virasoro is **infinite-dimensional**, with SL(2,ℝ) sitting inside as the "wedge subalgebra" `{L₋₁, L₀, L₊₁}`. **The wedge-SL(2,ℝ) Casimir of Virasoro is precisely `L₀(L₀ − 1) − L₋₁L₊₁`, and on a Liouville primary `V_α` its eigenvalue is `Δ_α(Δ_α − 1)`** — exactly the CMS form, but with `Δ_α = (ℓ + 1/2)²` shifted from `Δ_CMS = ℓ` by `+ 1/2`.

So at the *wedge* level, Virasoro-Liouville and CMS are **the same SL(2,ℝ)**, just in different parametrization conventions and operating in different regimes (low-Mω for CMS, vs all-aω-via-instanton-sum for Liouville). They reproduce the same `aω → 0` limit; they diverge at generic aω in *how* they extend (CMS just stops being a symmetry; Liouville extends via the Virasoro `L_{|n|>1}` descendants encoded in F_inst).

**Verdict:** **Same wedge-SL(2,ℝ); different extensions beyond the wedge.** CMS extends through the second SL(2,ℝ) factor (left/right structure); Liouville extends through the full Virasoro algebra encoded in irregular conformal blocks. They are not literally the same Virasoro module, but they share the wedge.

This makes Spike #12C *not* a re-expression of Spike #9/#10 — it is a genuinely different fourth side of the framework reach. (Specifically: CMS-SL(2,ℝ) bounds the framework's *low-Mω* side; HKLS-SL(2,ℝ) bounds the *eikonal* side; KY-abelian (Spike #11) bounds the *generic-aω* side; Virasoro-wedge-SL(2,ℝ) is a potential *fourth side* operating via Nekrasov–Shatashvili integrability across all aω. If positive, it would be a fourth side. If negative (predicted), it is structurally analogous to Spike #11 — algebraic-Casimir compression hits the same abelian-tower wall when extended to all aω.)

---

## 5. Spike protocol — concrete first-spike computation

### 5.1 Test point

**`(ℓ, m, s, aω) = (2, 2, 0, 0.5)`** — mid-spin Kerr scalar, fundamental gravitational-wave-relevant multipole, well outside CMS low-Mω regime, well below eikonal regime. Exactly the "Spike #11 generic-aω gap" zone.

### 5.2 Reference value (target for BLLT to reproduce)

Direct numerical spheroidal harmonic eigenvalue computation via:
- Leaver's continued-fraction method (Leaver 1985)
- Berti–Cardoso–Casals 2006 series expansion to ~10 terms in `c = aω` (gives `Λ_ℓm` to ~10⁻⁸ accuracy at `aω = 0.5`)
- Or `qnm` Python package by Stein 2019 (`pip install qnm`)

Expected reference value: **`Λ_{ℓ=2, m=2, s=0}(aω=0.5) ≈ 5.9` (low-aω series gives 6 − 0.0 + ... at small `c`; precise value computable to 10⁻¹⁰).**

### 5.3 BLLT closed-form (instanton-summed) evaluation

Compute `Λ` from BLLT eq. (95) by summing F_inst up to instanton order n_max ∈ {3, 5, 10}:

```python
def Lambda_BLLT(ell, m, s, c, n_max):
    """BLLT eq. (95) evaluation at instanton truncation n_max."""
    Lambda_inst = 4 * c
    a_int = 0.5 + ell  # intermediate-channel momentum, BLLT eq. (92)
    F = sum(F_n(a_int, m1=-m, m2=-s, m3=-s) * Lambda_inst**n
            for n in range(1, n_max+1))
    Lambda_0 = ell*(ell+1) - s*(s+1)
    return Lambda_0 + 2*c*s - c**2 - F
```

Where `F_n` is the n-th instanton coefficient — a sum over Young-tableau pairs `(Y, W)` with `|Y| + |W| = n`, computable via standard Nekrasov combinatorial formula (BLLT appendix C, or AGT-standard references).

### 5.4 Falsifier (the rate-of-decision test)

**Falsifier condition:** If BLLT eq. (95) at `n_max = 10` does NOT reproduce the direct-numerical `Λ_{2,2,0}(0.5)` to ≥ 6 decimals, the **dictionary has a sign / convention / U(1)-factor issue** (note: BLLT itself flags such a discrepancy with Aminov–Grassi–Hatsuda in their footnote 4, p. 20) and the spike *pauses* for dictionary verification before proceeding to Phase 6.

**Spike #11 / #12A discipline:** A dictionary issue is a real finding worth recording — do not paper over it. If found, the spike emits an NDJSON record `phase: "dictionary_issue", detail: ...` and stops.

### 5.5 Phases of the spike (proposed structure)

| Phase | Goal | Output |
|---|---|---|
| 1 | PDF re-verify BLLT 2105.04483 §3.4 + §5.3 + appendix A | NDJSON paper-retrieval records (`phase: "1_paper_retrieval"`) |
| 2 | Compute `Λ₀` and `Δ_α = Q²/4 − (ℓ+1/2)²` symbolically | NDJSON Casimir-eigenvalue records |
| 3 | Direct-numerical `Λ_{2,2,0}(0.5)` via Leaver / Berti-Cardoso-Casals series / `qnm` package | reference value, ~10⁻¹⁰ accuracy |
| 4 | BLLT instanton sum at `n_max ∈ {1, 3, 5, 10}`; convergence-rate check | reproducibility vs reference; falsifier check |
| 5 | Symbolic identification: is there a `[L_n, L_m]`-quadratic combination on `V(c, Δ_α)` whose eigenvalue is closed-form `Λ_{ℓm}(aω)` *finite* in aω? (Sympy: search for quadratics in `{L₀, L₋₁L₊₁, L₋₂L₊₂, ...}` whose eigenvalue formula has finite aω-dependence.) | Symbolic search outcome — almost certainly negative |
| 6 | Comparison to Spike #11 KY tower + Spike #9/#10 CMS SL(2,ℝ). Honest verdict. | Verdict NDJSON record |

### 5.6 Outcome classes (mirroring Spike #12A's class taxonomy)

- **(a) Full positive:** A finite Virasoro-Casimir-type identity reproduces `Λ_ℓm(aω)` in closed form at generic aω. **Predicted probability: ~5%.** Would be a genuine fourth side of the bounded framework.
- **(b) Partial:** A "Casimir tower" interpretation exists (Nekrasov–Shatashvili integrable Hamiltonians) but is an abelian tower, structurally same as Spike #11 KY. **Predicted probability: ~70%.** This is the expected outcome.
- **(c) Negative — dictionary works numerically but no Casimir compression:** BLLT eq. (95) reproduces the numerics, but no finite Virasoro-Casimir polynomial gives Λ_ℓm in closed form. **Predicted probability: ~20%.** Combined with (b) gives the "structural negative" combined outcome.
- **(d) Inconclusive / dictionary issue:** Falsifier fires; F_inst doesn't reproduce numerics. **Predicted probability: ~5%.** Would require dictionary forensics.

Per Spike #11 / #12A discipline: **(b), (c), and (d) are valid load-bearing outcomes. NO manufactured (a).**

---

## 6. Honest-negative possibility (the user's §6 flag)

The scoping prompt asked: "maybe BLLT's 'closed form' is a Nekrasov instanton sum that converges but isn't actually a finite closed-form expression — i.e., it's an alternative computation of Λ rather than a compression of it."

**This is exactly what the BLLT paper itself says.** BLLT §1, p. 4 final bullet of "open points": *"The results we present are given as a perturbative series in the instanton counting parameter Λ, which, as we show from comparison with the numerical solution in Subsect. 4.3, actually converges very efficiently."* And the introductory remark (p. 1, abstract): *"explicit expressions"* via *"sums over partitions via the AGT correspondence."*

So BLLT's "closed form" is:
- **An exact reformulation** of the connection problem in terms of Liouville/Nekrasov data
- **NOT a finite expression** in elementary or even special functions of `(ℓ, m, s, aω)`
- **An efficiently convergent instanton series** computable to arbitrary order

This is structurally an *alternative computation* of `Λ_ℓm(aω)` — replacing Leaver's continued fraction and BCC's small-`c` series with an instanton sum. It is mathematically equivalent in informational content (all three compute the same `Λ` to arbitrary precision), but **none compresses Λ into a single closed-form expression at generic aω**.

**Honest-negative reformulation of Spike #12C's likely verdict:**

> The Virasoro algebra has only `L₀` as a genuine Casimir-like quantity on a Verma module, and `L₀`'s eigenvalue on the BLLT intermediate-channel Verma is `Δ_α = (ℓ + 1/2)²`, which reproduces only `Λ₀ = ℓ(ℓ+1) − s(s+1)` (the `aω → 0` limit). The full `Λ_ℓm(aω)` at generic aω is the eigenvalue of `L₀` *plus* the Nekrasov–Shatashvili instanton free energy `F_inst` summed over all Virasoro-descendant Young-tableau states. `F_inst` is an *abelian commuting-Hamiltonian tower* (Bethe/Gauge integrable system), and per the Spike #11 abelian-tower-no-compression theorem, no finite combination of its tower-generators gives `Λ_ℓm` in closed form at generic aω. **Honest-negative outcome class (b) + (c) — Liouville/Virasoro provides an exact alternative computation but not a Casimir compression of `Λ_ℓm(aω)`.**

---

## 7. Connection to bounded-framework arc

Spike #11 (PR #359) + Spike #12A (PR #361) established the three-sided algebraic-Casimir bound:

| Regime | Algebra | Casimir | Closed-form |
|---|---|---|---|
| Low-Mω, scalar | CMS SL(2,ℝ)² (Spike #9) | `C_L + C_R = 2λ_S²(ℓ)` | ✅ |
| Low-Mω, spin-weighted | CMS SL(2,ℝ)² extension (Spike #10) | spin-weighted analog | ✅ |
| Eikonal (ℓ ≫ 1) | HKLS sl(2,ℝ)_QN (Spike #12A side B) | `C = 3/16` | ✅ |
| Generic aω, generic ℓ | KY abelian tower (Spike #11) | joint eigenvalue tuple | ❌ |

**Spike #12C's role:** The Virasoro/Liouville/Nekrasov machinery is the most-developed modern framework operating on the *full* `Λ_ℓm(aω)` for generic aω. If even *this* framework cannot compress `Λ` into a closed-form Casimir identity, the structural negative for the generic-aω regime is over-determined — three independent algebraic approaches (KY-tower, photon-ring interpolation, Liouville-Virasoro) all hit the abelian-tower-no-compression wall.

This would establish the *fourth side* of the framework's reach as **provably the right shape**: closed-form Casimir compression exists on three sides (low-Mω, eikonal, scalar/spin-weighted at fixed Mω) but provably does NOT exist at generic aω at the level of finite-dimensional Casimirs. The Spike #11 + Spike #12A + Spike #12C combined narrative would be:

> *"There is no closed-form Killing-Yano Casimir-decomposition QNM identity for generic-spin Kerr because the algebraic frameworks that admit closed-form compression (CMS SL(2,ℝ)², HKLS sl(2,ℝ)) are regime-restricted (low-Mω and eikonal respectively), and the regime-unrestricted frameworks (KY commuting tower, Nekrasov-Shatashvili commuting Hamiltonian tower) are abelian-tower-structured and therefore informationally equivalent to the joint eigenvalue tuple itself — no Casimir compression. The generic-aω Kerr QNM spectrum is computationally tractable (Leaver, BLLT instanton sum, MST series) but algebraically irreducible at the Casimir level."*

This is a clean, three-spike, structurally-overdetermined negative result. Combined with the three positive Casimir identities (Spike #9, #10, low-Mω; Spike #12A side B reproducing HKLS eikonal), the bounded-framework arc becomes well-defined: the framework reaches closed-form compression on exactly the three regime-restricted sides, and provably does not extend to the generic-aω regime.

---

## 8. Discipline + reproducibility

- All citations PDF-verified per `feedback_pdf_extraction_citation_discipline.md`. Two new misattributions caught (§0).
- No lineage claims per `feedback_no_lineage_claims_in_notebook.md` — citations are technical-content only.
- NDJSON output per `feedback_ndjson_over_bloated_json.md` (for the spike when it runs).
- Honest-negative outcome class is valid per Spike #11 + Spike #12A discipline.
- Predicted outcome distribution: 5% positive / 70% structural-negative-class-(b) / 20% negative-class-(c) / 5% dictionary-issue-class-(d). User to confirm before running.

---

## 9. One-sentence verdict on spike-worthiness

> **Spike #12C is worth running:** the dictionary is PDF-verified, the test point is concrete, the falsifier is precise, the predicted outcome (Liouville Virasoro Casimir reproduces only `Λ₀ = ℓ(ℓ+1) − s(s+1)` and Nekrasov–Shatashvili tower is structurally an abelian commuting-Hamiltonian tower per Bethe/Gauge correspondence — same Spike #11 wall) is itself a load-bearing result that closes the bounded-framework arc on the generic-aω side, and the small-probability positive outcome would yield a genuinely new fourth side of the framework reach.

---

## 10. Paper anchors (verified 2026-05-13)

| # | Citation | arXiv | Status |
|---|---|---|---|
| BLLT-2022 | Bonelli, Iossa, Lichtig, Tanzini, "Exact solution of Kerr black hole perturbations via CFT² and instanton counting" | `arXiv:2105.04483` | ✅ PDF retrieved + extracted 2026-05-13; §3.4, §5.3, eqs. (9), (10), (24), (39), (92), (94), (95) load-bearing |
| BLLT-2022b | Bonelli, Iossa, Lichtig, Tanzini, "Irregular Liouville correlators and connection formulae for Heun functions" | `arXiv:2201.04491`, Comm. Math. Phys. 397 (2023) | ✅ PDF abstract+TOC verified 2026-05-13; companion paper on irregular Virasoro blocks, no explicit `Λ_ℓm(aω)` content |
| AGH-2020 | Aminov, Grassi, Hatsuda, "Black Hole Quasinormal Modes and Seiberg-Witten Theory" | `arXiv:2006.06111`, RUP-20-18 | ✅ PDF abstract verified 2026-05-13; abstract explicitly claims *"exact expressions of eigenvalues of spin-weighted spheroidal harmonics"* via Nekrasov-Shatashvili Ω-background |
| NMLC-2019 | Novaes, Marinho, Lencsés, Casals, "Kerr-de Sitter Quasinormal Modes via Accessory Parameter Expansion" | `arXiv:1811.11912`, JHEP 05 (2019) 033 | ✅ PDF abstract verified 2026-05-13; not Aminov-Grassi-Hatsuda as 2026-05-12 KY lit review claimed |
| BBIT-Z-2023 | Bautista, Bonelli, Iossa, Tanzini, Zhou, "Black Hole Perturbation Theory Meets CFT₂: Kerr Compton Amplitudes from Nekrasov-Shatashvili Functions" | `arXiv:2312.05965`, PRD 109, 084071 | Title + authors verified via Google Scholar 2026-05-13; not PDF-retrieved |
| AGT-2010 | Alday, Gaiotto, Tachikawa, "Liouville Correlation Functions from Four-Dimensional Gauge Theories" | `arXiv:0906.3219`, Lett. Math. Phys. 91 (2010), 167 | Standard reference, BLLT cites as ref [3]; not re-verified |
| NS-2009 | Nekrasov, Shatashvili, "Quantization of integrable systems and four dimensional gauge theories" | `arXiv:0908.4052`, ICMP 2009 proc. | Standard reference, BLLT cites as ref [56]; not re-verified |
| Leaver-1985 | Leaver, "An analytic representation for the quasi-normal modes of Kerr black holes" | Proc. Roy. Soc. A 402 (1985), 285 | Standard reference; falsifier-side numerical method |
| BCC-2006 | Berti, Cardoso, Casals, "Eigenvalues and eigenfunctions of spin-weighted spheroidal harmonics in four and higher dimensions" | `arXiv:gr-qc/0511111`, PRD 73, 024013 | Already cited in Spike #11; falsifier-side series-expansion reference |

---

## 11. Open question for user before running

Should the spike attempt outcome class (a) speculatively (i.e., search the symbolic space of quadratic Virasoro combinations exhaustively) even though predicted-probability ≤ 5%, or accept that the abelian-Bethe/Gauge-tower argument already over-determines the negative and treat outcome (b) as the structural conclusion without doing the symbolic search?

Either choice is defensible. The exhaustive symbolic search adds ~30 min computation and 1-2 NDJSON records; the over-determined-negative reading is faster and intellectually equivalent. User to choose.

---

**End of scope. Awaiting review.**
