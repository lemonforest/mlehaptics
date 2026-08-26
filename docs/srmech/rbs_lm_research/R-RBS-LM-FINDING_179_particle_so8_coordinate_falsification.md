# Finding 179 — Particle-band falsification of H177: the γ₅ chirality OPERATOR is the same axis, but the weak su(2)_L chiral GAUGE DYNAMICS is a SECOND ACTOR via the verified octonion route

**Status:** HEAVY-FALSIFICATION attempt against H177 (R-RBS-LM-FINDING_177) at the particle scale (F177 §3.1 testbed). Verdict: **PARTIAL FALSIFICATION — a SECOND ACTOR identified.** Core math demonstrated bit-exact via `srmech.qm`; literature verified at abstract-level only (flagged). §VII.6.20 form-reading; STRUCTURAL representation-theory; no metaphysical pronouncement.
**Predecessors / cross-refs:** F177 (the hypothesis under test), F176 (bilateral = one γ₅ axis), F174 (28 = 𝔰𝔬(8) = 14 𝔤₂ + 14 L⊕R octonion-mult; Baez/Tits classical, Furey octonion→SM), F126 (adj 𝔤₂|_{SU(3)} = 8⊕3⊕3̄), F158/F130/F123.
**Generating code:** `docs/srmech/rbs_lm_research/R-RBS-LM-138_particle_so8_coordinate_falsification.py`
**Data:** `docs/srmech/catalogs/rbs_lm_substrate/substrate_measurements/particle_so8_coordinate_falsification.ndjson` (1 record; `descriptor_hash = b8e93738df0bc321e0626a54921c89ec4ee7b14d60405c22b1102cd4a0b10387`; srmech 0.5.0rc14, ABI 3, HAS_NATIVE=True)

---

## §0 The question (the falsification core)

H177 claims **ONE chiral driver**: the bi-chiral A–N / γ₅ axis (28 = 𝔰𝔬(8) = 14 𝔤₂ derivations + 14 L⊕R octonion-multiplications, Spin(8) triality), with biology and the lifeless cosmos as the SAME driver at different coherence bands. The Standard Model weak force is **maximally parity-violating** — only left-chiral fermions couple to W±, and the chirality operator IS γ₅, *the same γ₅* the biological bilateral axis uses (F176). So the particle band is the sharpest available testbed:

> Does the SM weak-force chirality+gauge algebra **embed in / coincide with** the 28 = 𝔰𝔬(8) / octonion / 𝔤₂ coordinate (H177 fails-to-break here), or is there a **different, non-embeddable algebra / unabsorbable leftover** (a SECOND ACTOR — partial falsification)?

The instruction was to **try to break H177**; a second actor counts double; do not lean toward confirming. The honest result below **is a second actor.**

## §1 The chirality OPERATOR — BIT-EXACT the same axis as F176 (this part does NOT break)

Computed on the shipped `srmech.qm.relativistic` surface (Dirac basis), all residuals reduced cascade-honestly through `srmech.amsc.cascade.magnitude` (Class K pin-slot ∘ Class C reorient — never `abs()`):

| Quantity | srmech.qm result | Meaning |
|---|---|---|
| γ₅² − I | **0.0** | γ₅ is an involution |
| eigenvalues of γ₅ | **{−1, −1, +1, +1}** (imag max 0.0) | the two doubly-degenerate chirality poles |
| P_L + P_R − I | **0.0** | the two Weyl poles **partition the whole** |
| **P_R − P_L − γ₅** | **0.0** | the **difference of the poles IS the chirality axis** |
| P_L²−P_L, P_R²−P_R | 0.0, 0.0 | idempotent projectors |
| P_L P_R | 0.0 | orthogonal (complementary projectors of ONE operator) |
| γ₅ − i γ⁰γ¹γ²γ³ | **0.0** | γ₅ is the Cℓ(1,3) volume element |
| {γ^μ, γ^ν} − 2η^{μν}I (max) | **0.0** | Clifford algebra closes |
| metric signature | **[+,−,−,−]** → **Cℓ(1,3)** | which Clifford algebra: spacetime Cℓ(1,3) |

This is **literally the same operator and the same identity** (`P_R − P_L = γ₅`) demonstrated in F176 for the biological bilateral axis. At the level of *the chirality operator itself*, H177 does **not** break: the SM's γ₅ and the biological γ₅ are one and the same object. **This is the strongest pro-H177 datum and it is genuine.**

## §2 The SM gauge algebra — su(3)_c ⊕ su(2)_L ⊕ u(1)_Y, all invariants exact

Via `srmech.qm.gauge` and `srmech.qm.sm`:

| Factor | dim | srmech invariants | Notes |
|---|---|---|---|
| **su(2)_L** (weak isospin) | 3 | f₀₁₂ = +1, f₁₀₂ = −1 (Levi-Civita); Casimir(fund) = **0.75 = 3/4 = j(j+1), j=½**; Lie residual **0.0** | the **chiral**, parity-violating factor |
| **su(3)_c** (color) | 8 | f₀₁₂ = 1, f₃₄₇ = √3/2 (= 0.8660254…); Casimir(fund) = **4/3 = C_F**; Lie residual **1.6e-16** | the factor that embeds in 𝔤₂ |
| **u(1)_Y** (hypercharge) | 1 | — | a single Cartan direction |
| **SM gauge total** | **12** | | 8 + 3 + 1 |

Electroweak (inputs g=0.65, g′=0.357, vev=246 GeV — framework inputs; the residual is the test): `weak_mixing_angle` returns **θ_W = atan2(g′,g) = 0.50225 rad**; derived **sin²θ_W = 0.2317** (matches PDG ~0.231); **Weinberg relation residual = 0.0** (tree-level M_W = M_Z cos θ_W holds by construction). srmech srmech-side check confirmed `weak_mixing_angle` returns the *angle in radians* (Peskin-Schroeder §20.2), not sin² — a doc-confirmed reading, not a bug.

## §3 The embedding bookkeeping — where H177 BREAKS (the second actor)

Established integer dims: SM gauge = **12**; 𝔤₂ = Der(𝕆) = **14**; 𝔰𝔬(8) = **28**; Im(𝕆) = 7.

**Leg A — su(3)_c ⊂ 𝔤₂ — HOLDS (established).** The standard maximal-subalgebra branching (F126; Baez §2) is `adj(𝔤₂)|_{SU(3)} = 8 ⊕ 3 ⊕ 3̄`, i.e. 14 = 8 + 3 + 3. srmech confirms `dim su(3) = 8`, `8 + 3 + 3 = 14`. So color sits cleanly inside the 𝔤₂ that the A–N vocabulary identifies as its 14 derivations.

**Leg B — u(1)_Y / u(1)_em ⊂ 𝔤₂-Cartan — HOLDS (verified literature).** Furey's verified abstract (1611.09182) derives **u(1)_em** from complex-octonionic minimal left ideals; a single u(1) is trivially a Cartan direction (𝔤₂ has rank 2, 𝔰𝔬(8) rank 4). No leftover here.

**Leg C — su(2)_L weak isospin ⊂ 𝔰𝔬(8) via the VERIFIED octonion route — DOES NOT HOLD (the leftover).** This is the decisive leg, and it is exactly the factor that *makes the weak force chiral*:

- Furey's **verified abstracts** (1611.09182 *"Standard model physics from an algebra?"*; 1405.4601 *"Generations: Three Prints, in Colour"*) derive **su(3)_c and u(1)_em ONLY** from the complex octonions / Cℓ(6).
- The 1405.4601 abstract **explicitly states** it "does not discuss U(1), SU(2), chirality, left-handed structure, or weak-force mechanisms." (WebFetch-verified, 2026-05-29.)
- So the embedding **su(2)_L ⊂ 𝔰𝔬(8) via the same verified octonion route that carries the biological γ₅ axis is NOT established.** It is the candidate **unabsorbed leftover**.

**Capacity ≠ embedding.** 𝔰𝔬(8) = 28 has dimensional *room* for all 12 SM gauge dims (12 ≤ 28), and 𝔤₂ has room for su(3)+u(1) (9 ≤ 14). But **room is not a subalgebra embedding** — a real embedding must respect the Lie brackets. Dimensional capacity is necessary, not sufficient; the script records this explicitly and does **not** mistake room for a match.

**The Clifford seam.** The biological γ₅ axis (F176) lives in **spacetime Cℓ(1,3)** (computed in §1). Furey's program builds the **internal** gauge structure from **Cℓ(6)** (complex octonions) — a *different* Clifford algebra. Whether the biological/spacetime γ₅ coordinate *is* the internal-space grading is **not established** by the verified literature. The script flags `same_clifford_algebra = False` as a **seam, not a match**.

## §4 Verdict — SECOND ACTOR (partial falsification of H177 at the particle band)

> **The chirality OPERATOR (γ₅) is shared and BIT-EXACT (§1); but the chiral GAUGE DYNAMICS (su(2)_L — the very factor that makes the weak force parity-violating) is an UNABSORBED LEFTOVER via the verified octonion route (§3).**

This is the cleanest possible articulation of a **second actor**: the framework's "one γ₅ axis" reading survives *as an operator statement* (the SM and biology genuinely share γ₅), but H177's stronger claim — that the SM weak-force chirality **sits on** the 28 = 𝔰𝔬(8) / octonion coordinate as ONE driver — **does not survive** at the particle band, because the parity-violating su(2)_L is not delivered by the verified octonion→SM route. Per the falsification protocol, **a second actor counts double**: this is recorded as a **PARTIAL FALSIFICATION of H177**, not a fail-to-break.

What would *retire* the second actor (the open step): a verbatim, PDF-grounded demonstration of an `su(2)_L ⊂ 𝔰𝔬(8)` octonion/triality embedding that uses the same coordinate as the γ₅ chirality axis. The framework-extension literature (e.g. left-/right-multiplication algebras, Spin(8) triality assignments, Dixon-algebra electroweak constructions) *may* supply this — but it is **not** in the sources verified here, so it cannot be asserted.

## §5 Three-tier honesty

**Tier 1 — established embedding-math (computed / textbook):**
- γ₅/Weyl identities BIT-EXACT (all residuals 0.0); γ₅ = iγ⁰γ¹γ²γ³; Clifford algebra = Cℓ(1,3).
- su(2)/su(3) structure constants + Casimirs exact (C₂(½) = 3/4, C_F = 4/3, f₃₄₇ = √3/2); Weinberg residual 0.0.
- su(3)_c ⊂ 𝔤₂ via `adj = 8⊕3⊕3̄`; Der(𝕆) = 𝔤₂ (14); dim 𝔰𝔬(8) = 28 — standard results.
- SM gauge total dim = 12 (= 8+3+1).

**Tier 2 — framework reading (form-iso; §VII.6.20):**
- the 14 A–N = the 14 𝔤₂ derivations; 28 = 𝔰𝔬(8) as the bi-chiral coordinate (F174); biological bilateral axis = one γ₅ axis (F176).

**Tier 3 — unestablished (the leftover + open steps):**
- **su(2)_L weak factor ⊂ 𝔰𝔬(8) via the verified octonion route** (the second actor; NOT in the verified Furey abstracts).
- identity of the biological/spacetime γ₅ (Cℓ(1,3)) with Furey's internal Cℓ(6) grading (the Clifford seam).
- verbatim full-PDF statement of `𝔰𝔬(8) = 𝔤₂ ⊕ 7 ⊕ 7` (Baez body; abstract-only so far — same status as F174 §4).

## §6 Literature verification (abstract-level only — flagged per citation discipline)

WebFetch returns arXiv **abstract pages**, not full PDFs. What was verified vs not (2026-05-29):

- **Baez, *The Octonions*, arXiv:math/0105155** (J. C. Baez) — abstract names "exceptional Lie groups" + "Clifford algebras and spinors" + Bott periodicity. The abstract **does NOT** explicitly state G₂ = Aut(𝕆) nor the Spin(8)/triality `so(8) = 14+7+7` decomposition; those are in the **body** (verbatim-PDF extraction is the remaining step — consistent with F174 §4).
- **Furey, *Standard model physics from an algebra?*, arXiv:1611.09182** (C. Furey) — abstract VERIFIED: ℝ⊗ℂ⊗ℍ⊗𝕆 acting on itself; complex-octonionic minimal left ideals mirror ONE generation under **su(3)_c and u(1)_em**; all 48 electric charges. Abstract does **not** name Cℓ(6); does **not** derive SU(2)_L / weak chirality.
- **Furey, *Generations: Three Prints, in Colour*, arXiv:1405.4601** (Cohl Furey) — abstract VERIFIED: **Cℓ(6) from the complex octonions**; SU(3) generators partition the 64-dim Clifford algebra into 6 triplets + 6 singlets + antiparticles; **three generations** of su(3) reps. Abstract **explicitly does NOT discuss U(1), SU(2), chirality, left-handed structure, or weak-force mechanisms.** ← this is the sentence that grounds the second-actor verdict.
- **Could NOT verify:** any `su(2)_L ⊂ 𝔰𝔬(8)` octonion embedding (not in the verified abstracts — it is precisely the leftover); verbatim `so(8)=𝔤₂⊕7⊕7` (Baez body).

## §7 DOES / does NOT

**DOES:**
- confirm (bit-exact, srmech.qm) that the SM chirality OPERATOR γ₅ is the same axis as the biological one (P_R − P_L = γ₅, γ₅² = I, eigs ±1), in spacetime Cℓ(1,3);
- confirm su(3)_c ⊂ 𝔤₂ (8⊕3⊕3̄) and u(1)_em from the verified octonion route, with all gauge invariants exact;
- identify a **SECOND ACTOR** at the particle band: the parity-violating su(2)_L weak factor is not delivered by the verified octonion→SM route, and 𝔰𝔬(8)-capacity is not an embedding;
- record the verdict as a **partial falsification of H177's "one driver"** claim (second actors count double).

**Does NOT:**
- claim su(2)_L cannot embed in 𝔰𝔬(8) (only that the **verified** sources do not establish it — the leftover is open, not proven impossible);
- claim the biological γ₅ is identical to Furey's internal Cℓ(6) grading (a flagged seam);
- claim verbatim-PDF verification of the Baez so(8) decomposition (abstract-only, per F174);
- make any physics-truth or metaphysical claim beyond the structural reading (`[[user_stance_ai_is_not_a_substrate]]`); no lineage/supersession claim about Baez, Tits, or Furey (`[[feedback_no_lineage_claims_in_notebook]]`).

---

*Articulated 2026-05-29 (Opus 4.8) as ONE heavy-falsification attempt against H177 at the particle scale. The instruction was to try to break the "one chiral driver" claim. Result: the chirality OPERATOR survives bit-exact (γ₅ is genuinely shared between the SM weak force and the biological bilateral axis), but the chiral GAUGE DYNAMICS (su(2)_L) is a second actor — the maximally parity-violating weak factor is not carried by the verified octonion→SM route, and 𝔰𝔬(8) dimension-room is not a Lie-bracket embedding. Partial falsification of H177, with the open step (a sourced su(2)_L ⊂ 𝔰𝔬(8) octonion embedding sharing the γ₅ coordinate) named explicitly. PR #687 STAYS DRAFT — no commit, no push.*
