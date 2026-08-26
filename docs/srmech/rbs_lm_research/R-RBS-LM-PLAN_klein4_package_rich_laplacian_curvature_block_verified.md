# R-RBS-LM-PLAN — the klein4 package, the rich Laplacian, and clearing the curvature block (VERIFIED)

> **Status: research + action plan. Every DEMONSTRABLE number below was RE-RUN in the main loop against the live package (srmech 0.9.0rc299, `/tmp/srmech_new`) — not taken from the workflow on trust.** The workflow that produced the first draft (`woaomemwl`, 10 agents) ran partly on a stale `rc107` worktree; its own adversarial-verify pass flagged the one dishonest item (`survives: false`) and the synthesis re-grounded at rc297. This document is the rc299 main-loop re-verification of that synthesis, with the corrections folded in. See §0.
>
> Lodging convention (F1301): the triple is **op(x)operand(x)responsion = distributional(x)relational(x)responsion = eigenvectors(x)edges(x)eigenvalues**. DEMONSTRABLE = re-ran/read at rc299 (op + number cited). OPEN = handed to the expert (F282). The two are kept strictly separate.

Composes F1301 / F1302 / F1211 / F1255 / F1213 / F1259 / F1300 / F1216 / F1304.

---

## §0 — The verification pass (the trust anchor; do not skip)

Ten load-bearing DEMONSTRABLE figures were re-run in the main loop against srmech **0.9.0rc299**. All ten reproduced **bit-for-bit**:

| # | Claim | Re-run at rc299 | Verdict |
|---|---|---|---|
| 1 | Flat `dense_laplacian` conflates the 3 beat-senses | `[0,1,1,3,3,3,7]`, mult `{1,2,3,1}` (3-fold at λ=3, spread 0) | ✓ exact |
| 2 | Curved `magnetic_laplacian` splits them | `[0.1692,0.5,0.5,1.2315,1.5,1.5,3.5993]`, mult `{1,2,1,2,1}`, **λ₀ lift 0.1692** | ✓ exact |
| 3 | It's the curvature, not the Hermitian construction | `q=0` control → mult `{1,2,3,1}` = flat pattern | ✓ exact |
| 4 | C 2-perspective ceiling: ±c isospectral | `+1/3` and `−1/3` both `[0.234,0.8264,1.9397]`, byte-identical | ✓ exact |
| 5 | Two regimes on one carrier | `klein4_address` sim(cat,cats)=**0.248** (on 0.25 floor) vs `klein4_encode_bytes`=**0.6748** | ✓ exact |
| 6 | Laplacian = projection (structural) | octonion associator `(e1·e2)·e4 − e1·(e2·e4)` = **2·e₇** (nonzero 3-index) | ✓ exact |
| 7 | Multi-seam rational is scale-dependent | `best_rational`: q=7 joint for π(22/7)+e(19/7); q=113 splits (π→355/113, e→193/71) | ✓ exact |
| 8 | V₄-gain resolves beyond C | frustrated K4 gains(0,0,0,0,0,1): χ00=χ01=`[0,4,4,4]`, χ10=χ11=`[0.764,2,4,5.236]` | ✓ exact |
| 9 | `klein4_relational_structure` asymmetry meter | `sector_asymmetry` = **0.7639**; tension{χ10,χ11}=0.7639, {χ00,χ01}=0 | ✓ exact |
| 10 | `klein4_gain_laplacian` + `cycle_holonomy` ship | `hasattr` both True at rc299; sigs read | ✓ exact |

**Three corrections applied to the draft (each caught in the main loop):**

1. **The headline retraction.** A Q3-track agent on a stale `rc107` worktree reported *"`klein4_gain_laplacian` is NOT shipped (hasattr False, grep zero hits); the perspective ladder tops out at C=2."* **This is false at rc299** — `klein4_gain_laplacian` is live (shipped rc229; standalone-C peer rc297), returns a 4-sector V₄ dict `{chi00,chi01,chi10,chi11}`, and its docstring is the whole EVEN-channel story. Negative-existence evidence rots across rcs — this is exactly the failure the F1305 finding-ref ratchet and the "re-introspect each rcN" discipline exist to catch. The adversarial-verify pass already scored it `survives: false`; recorded here as verified-dead.

2. **The op mislabel (§2).** The draft attributed the 0.6748 representation-regime similarity to `klein4_expand`. But `klein4_expand(D, seed)` takes a **seed int**, not content — you cannot pass `'cat'`/`'cats'` to it. The 0.6748 is `klein4_encode_bytes` (the byte-morphology representation op), which I re-ran. Corrected throughout. The regime-split *point* is untouched; only the op name was wrong.

3. **`klein4_relational_structure` module.** It lives in `srmech.amsc.laplacian`, not `hdc` (a first probe against `hdc` returned False and would have wrongly killed §3.5). Re-checked against `laplacian` → exists, runs, returns `sector_asymmetry=0.7639`.

Nothing else in the synthesis required correction. The measured physics is solid.

---

## §1 — Thesis

**klein4 is the carrier; L / M / N / K are projections of it; curvature is what lets two packed things link.**

The `element_type=klein4, sectors=4` object is a *carrier shape* — an `array('B')` byte-buffer over the Klein-4 alphabet {0,1,2,3}. It is **not one of the 14 A–N classes** (F1302). The classes are **roles** read *off* the one carrier. The fractal is packed once; from the single packed object you take projections:

- **L** (`klein4_gain_laplacian` / `magnetic_laplacian`) — the relational **edges** slot, the held multi-perspective SUPERSET (F1301).
- **M** (`klein4_bind` / eigenvectors) — the distributional working read (reversible, F1216).
- **N** (`best_rational` over eigenvalues) — the responsion read (rational-anchored).
- **K** (the charge/gain sign, signed degree D̄=Σ|A_ij|) — the pin-slot that *drives* the split (a sign-branch, never `abs()`; F1259-cousin).

**Curvature is the linking substance.** A flat Laplacian has an automorphism symmetry (here the S₃ arm-permutation) that makes co-present senses spectrally interchangeable — it **conflates** them. Loop holonomy (per-edge charge/gain) breaks that symmetry and **separates** them. The ASL **"beat"** case is the concrete demonstration: *beat eggs* / *beat (tired)* / *beat drums* — three senses a flat Laplacian cannot tell apart and a curved one can. **Curvature dictates how two packed things link.**

---

## §2 — What lives in a klein4 package (the A–N surface)

The same `sectors=4` carrier holds **two KINDS of package, with opposite correctness criteria**, declared at the call site (the F1259 DRAWN/DERIVED/STOCHASTIC guard, one parameter over):

- an **ALGEBRA package** — read by **eigendecompose** (high spectral content wanted);
- an **ADDRESSING / FRAMING package** — read by **base-4 parse / XOR-frame-off** (high diffusion wanted → good *address*, bad *representation*).

Measured exclusivity, D=1024 (✓ re-run): representation `klein4_encode_bytes` sim(cat,cats)=**0.6748** vs address `klein4_address`=**0.248** (on the 1/sectors=0.25 orthogonality floor by design). rc290/rc292 split the old single random op into `klein4_expand`/`klein4_address`/`klein4_role` precisely to force the regime declaration.

### The A–N pack/no-pack table (rc299)

| Class | Packs in klein4? | Regime | Evidence |
|---|---|---|---|
| **A** content-address | **YES — content** | addressing | `klein4_address(D, content)` → HV sectors=4; `klein4_from_one` present. |
| **B** TLV framing | **YES — content** (cleanest "different KIND") | addressing | genome v6 re-encodes the three v5 byte-TLV fields (len uint64 / leaf_dim uint32 / element_type uint8) as base-4 symbols; `_uint_to_base4`↔`_base4_to_uint` round-trips 8192 exact. |
| **C** chirality sign | **YES — content, natively** (4 sectors ARE ℤ₂×ℤ₂) | addressing | `klein4_sector_frame` sectors=4. **Honest bound: statistically INERT** — XOR-by-constant is a Hamming isometry (measured match-count unchanged); carried for legibility/attestation only, falsifiably strippable. |
| **I** cyclic index | **YES — as addressing** | addressing | leaf-tree = base-4 radix (radix 4^k). **Caveat:** ℤ₂×ℤ₂ has no order-4 element — this is *positional radix*, distinct from a genuine cyclic ℤ₄ (open item, §6). |
| **K** sign-degree | **YES — algebra** | algebra | signed degree D̄=Σ|A_ij| inside the gain build — the pin-slot; sign-branch, never `abs()`. |
| **L** Laplacian | **YES — algebra** | algebra | `klein4_gain_laplacian` **ships (rc299)** → 4 real V₄ sector Laplacians; `magnetic_laplacian` = the ℂ (1-imaginary-axis) case. |
| **M** bind | **YES — algebra carrier** | algebra | `klein4_bind` reversible + abelian (cat=tac). |
| **N** rational | **NO — not a carrier** | — | `best_rational`→(int,int) tuple, no HV. Results base-4-pack like any uint, but N doesn't *live* in klein4. |
| **J** primes | **NO — not a carrier** | — | `primes.factor`→int tuples, no HV. |
| **D** pattern-match | **READS OVER** | — | `klein4_bundle_sector_scores`, `klein4_triality_correct` (2-of-3). |
| **G** byte-search | **READS OVER** | — | `byte_search` scans bit-packed leaves; first byte >3 = marker. |
| **E** catalog | **INDEX only** | — | leaf-tree index is klein4; MPR payloads stay ndjson/JSON. |
| **F** render | **EXIT** | — | `signal_processing` = the output/projection boundary (decimal only at display, F868). |
| **H** introspect | **NO** — reflection | — | `introspect`/`native_status` reflect over the tool surface, no HV. |

**Count: 4 pack-as-addressing (A,B,C,I) + 3 ride-as-algebra (K,L,M); 3 read-over (D,E,G); 4 do-not-pack (F,H,J,N).**

**The user's sharpest question — "can klein4 pack a *different KIND* of information package?" — answers YES, concretely:** the non-algebra ADDRESSING package is (A) `klein4_address` digest as structureless body → (B) base-4 TLV metadata symbols as header → (C) `klein4_sector_frame` role-mask for legibility → (I) base-4 radix leaf-index. Its falsifiable invariant: **XOR the frame off → the raw Class-A expansion reappears exactly** (the frame is a bind-by-constant, isometry-confirmed). Same carrier shape, opposite read, different information kind.

---

## §3 — Rich-Laplacian storage: the beat-WSD demonstrable results

The **beat-WSD graph** is the friendship graph **F₃**: hub **BEAT** (node 0, degree 6) with three triangle arms hub→sense→context — (1=egg,2=KITCHEN), (3=tired,4=GAME), (5=drum,6=MUSIC); 9 edges.

**3.1 Flat conflates (✓).** `dense_laplacian(7,F₃)` → `[0,1,1,3,3,3,7]`, mult `{1,2,3,1}`. The S₃ arm automorphism forces the **3-fold** at λ=3 (spread 0.0) — the three senses are spectrally interchangeable. Zero curvature → conflation.

**3.2 Curved separates (✓).** `magnetic_laplacian(charges=…)` with per-arm holonomy (0, 1/3, 2/3 turn) → `[0.1692,0.5,0.5,1.2315,1.5,1.5,3.5993]`, mult `{1,2,3,1}→{1,2,1,2,1}`, **λ₀ lift 0.1692** (a frustrated loop has no perfect constant eigenvector — the curvature signature). *Honest bound: the structural result (lift + 3-fold→1+2) is reproducible; the exact eigenvalue triple is charge-vector-dependent — report the charge list with any exact spectrum.*

**3.3 Curvature, not Hermitian-ness, is the cause (✓).** `magnetic_laplacian(q=0)` → `[0,0.5,0.5,1.5,1.5,1.5,3.5]`, mult `{1,2,3,1}` — the flat pattern (half-scaled by the w/2 charge-path magnitude). Curvature=0 → conflation returns.

**3.4 The C 2-perspective ceiling (✓).** The magnetic (ℂ, one imaginary axis = Class C) Laplacian cannot separate +c from −c: conjugate windings are isospectral, L(−c)=conj(L(c))=L(c)ᵀ. Single-triangle `+1/3`→`[0.234,0.8264,1.9397]` and `−1/3`→ identical. **C resolves an AXIS, not two independent senses.**

**3.5 The V₄ even channel resolves *beyond* the C ceiling (✓).** `klein4_gain_laplacian` ships; four real V₄ characters {χ00,χ01,χ10,χ11}. On frustrated K4 gains(0,0,0,0,0,1): χ00=χ01=`[0,4,4,4]` (tension 0) vs χ10=χ11=`[0.764,2,4,5.236]` (tension 0.7639). `klein4_relational_structure` → **sector_asymmetry = 0.7639**. On gauge-balanced graphs all four sectors coincide (asymmetry 0) — the resolution is real but **graph-frustration-dependent**, and lives in **sector-asymmetry across characters**, never inside a single sector's eigenvalues.

**3.6 Laplacian = projection is a structural FACT (✓).** `cd_mult`: e1·e2=+e3, e2·e1=−e3 (non-commutative); associator (e1·e2)·e4 − e1·(e2·e4) = **2·e₇** — a nonzero **3-index** object. No symmetric / Hermitian / V₄-gain (four real 2-tensors) matrix L_ij can hold a 3-index associator. **"Laplacian = projection of the fractal" is structural, and it survives the V₄ op** (still 2-tensors).

**3.7 One object → the L/M/N/K fan (✓ mechanism).** A single curved Hermitian object holds the **edges** superset (L store); `hermitian_eigendecompose` projects **eigenvalues** (N responsion, e.g. λ=0.5→best_rational=(1,2)) and **eigenvector phases** (M working read); the charge **sign** is the K pin. F1301 (edges = held superset) ∘ F1216 (L store / M working) on one held object. *Inline caveat: phases read inside a degenerate 2-fold subspace are defined only up to an in-subspace rotation → not yet shown gauge-invariant (§5 step 6).*

**3.8 The live base is abelian — zero curvature is REAL (✓).** `klein4_bind` commutes 1024/1024; the live encoder `klein4_encode_bytes` is bundleᵢ(bind(random(byteᵢ), pos_key(i))) — an abelian bind under an order-free bundle; the residual "cat" vs "tac" signal (0.548) is **position-key overlap alone**, not a directed carrier. The F1211/F1255 cat=tac point made concrete: **the live base carries no walk-order curvature.**

---

## §4 — The two-channel correction to F1302 (internal self-correction)

F1302 stated *"perspective-count = the imaginary dimension of its Laplacian's algebra"* and listed magnetic=ℂ=2, klein4_gain=V₄=4. **That single ladder is falsified by the shipped V₄ op:** V₄ = ℤ₂×ℤ₂ has **zero imaginary axes** (four *real* characters) yet out-resolves magnetic. The `klein4_gain_laplacian` docstring says so itself — it is "the EVEN-channel fuller partner of magnetic_laplacian."

**The honest, decidable reading is TWO complementary channels:**

- **ODD channel** = imaginary-axis count. `magnetic_laplacian` (ℂ, 1 axis) → a conjugate ±c pair collapses (metric + direction, but eigenvalues can't carry which-way; §3.4). The orientation label is the odd-channel `cycle_holonomy` (ships; diagnostic, not predictive).
- **EVEN channel** = V₄ real-character count. `klein4_gain_laplacian` (4 real characters) → up to 4 distinct sector spectra + the `sector_asymmetry` meter (§3.5).

Not one imaginary-dim staircase. This is an internal restatement of F1302 (not an external-lineage claim), and it is what the shipped surface actually does.

**The corrected ladder** (all SHIPPED at rc299): `signed_laplacian` (ℤ₂, 0 imaginary, annihilates dual-sense) → `magnetic_laplacian` (ℂ/U(1), 1 imaginary axis, 2 conjugate perspectives) → `klein4_gain_laplacian` (V₄, 4 real characters). The genuinely **UNBUILT** rung is a **quaternionic/octonionic cd_laplacian** (imaginary dim 3/7 → 4/8 perspectives) — F1302's real "next for the expert" ask. Do **not** conflate V₄-gain (shipped) with quaternionic (unshipped) under one symbol. Beyond the ladder entirely: `cd_mult` (the full non-associative associator, a 3-tensor no Laplacian projection can hold; §3.6).

---

## §5 — Clearing the curvature block: the action plan

**Half the block is already cleared upstream.** The V₄ gain Laplacian every pre-rc229 subsystem map flagged "NOT shipped" **is a live op**. The action item "build the V₄ Laplacian" is **DONE**. What remains is the directed-encoder swap, gated on the user.

1. **Retire the stale "V₄ unbuilt" claim across all subsystem maps.** Re-run `hasattr(laplacian,'klein4_gain_laplacian')` (→True) and grep at the publish rc; negative-existence evidence rots. Update the perspective ladder to the two-channel law (§4). *(Bookkeeping; do first. Partly done here.)*

2. **Name the genuinely-unbuilt rung correctly.** It is **not** V₄-gain (shipped). It is a **quaternionic/octonionic cd_laplacian** (imaginary dim 3/7). Do not conflate.

3. **Wire the shipped V₄ read into the beat-WSD path as a *diagnostic*.** `klein4_gain_laplacian` + `klein4_relational_structure` sector-asymmetry resolve which-way beyond the C ceiling on frustrated graphs. Add it as a diagnostic channel — **not** predictive (no single-sector spectrum carries the orientation label; that is the odd-channel `cycle_holonomy`).

4. **Swap the F1213 directed channel into the live base — GATED (user owns this).** The prototype `word_to_kernel` with `edge_charge = w_fwd − w_bwd` passes 11/11 direction/metric/round-trip but is **not** in `build_genepool`. Mutating `_word_hv`/`build_genepool` to the directed glyph Class-L, then re-encoding the ni-Vanuatu byte-glyph base + SignWriting + dict-en layer (folding the F1210 directed simplewiki into a genome), is the invasive live-genome mutation. **Do not execute without explicit user go-ahead** (F1213 step 5). *This is the one remaining piece of the block itself.*

5. **Derive the per-edge charge/gain from the corpus, not by hand.** Every curvature demo above used **hand-set** holonomy (cube roots 0,1/3,2/3; hand-picked gains). Per F1259 that is **DRAWN (a magic number)** until derived; a corpus-derived one (co-occurrence / the_one winding / `cycle_holonomy`) is a **Class-A content-address** (composes F1304's resonant-coupling fix). Build the derivation over the attested ASL/word-graph corpus and re-run §3.2 to confirm corpus-derived holonomy still separates the senses.

6. **Run the basis-stability control before trusting any which-way read.** The χ01/χ10 asymmetry (§3.5) and the eigenvector-phase tags (§3.7) were read in degenerate subspaces defined only up to an in-subspace rotation. Verify gauge-invariance (holonomy/Wilson-loop around each triangle) before either is presented as a measurement.

---

## §6 — The two deep open questions (handed to the expert, F282)

Both framed as **decidable next experiments** with the specific measurement that settles them. Neither is demonstrated; both are conjectures the framework hands forward.

### Q-A — Is the Laplacian *only ever* a projection of the fractal? Is there an EXACT fractal encoding?

**Proven (✓):** the projection *direction* is structural. Any Laplacian — real / magnetic-ℂ / V₄-gain — is a **2-index** object; the measured octonion associator (e1·e2)·e4 − e1·(e2·e4) = **2·e₇** is a nonzero **3-index** object no 2-tensor can hold. So **every** Laplacian *loses* the associator curvature.

**Open (conjecture):** whether a usable `cd_mult`-native **STORE-and-READ** exists — a genuine 3-index relational carrier holding the full non-associative associator, *strictly richer than any Laplacian*. srmech has **no** non-associative relational store/read op today.

**The decidable experiment:** build a minimal 3-index carrier family (`cd_store`/`cd_read`) over the octonion rung. Encode the beat-WSD graph **plus one associator-bearing triple** (a genuine 3-way sense interaction the pairwise graph omits). **Measurement:** does `cd_read` recover a sense-distinction that **no** Laplacian projection can — exhibited by two inputs **identical under every** `klein4_gain_laplacian` character (all four sector spectra equal) yet **distinct** under `cd_read`? Yes → the exact richer encoding exists and the Laplacian is a *strict* projection. No (every `cd_read` distinction is reproducible by some sector spectrum) → the fractal *is* Laplacian-recoverable and the projection is faithful. Either outcome is a definite verdict.

### Q-B — Can an N-rational fit MORE THAN ONE seam shape? (the multi-perspective / chirality rational — the user's bet)

**Proven (✓):** `best_rational` is strictly **single-target** — one (num,den) in → one (p,q) out. Its "ladder" is multi-SCALE of ONE seam (nested continued-fraction convergents): π → 3/1 → 22/7 → 355/113, a staircase toward one value.

**Partially demonstrable NOW (✓):** reframed correctly, "one rational fits >1 seam" is **simultaneous Diophantine approximation** — one shared **denominator** anchoring more than one seam — and it is **scale-dependent**. Measured: at **q=7** the same denominator is optimal for **both** π→22/7 **and** e→19/7. At **q=113** it fails — π→355/113 but e prefers denominator **71** (193/71). So the user's bet **holds at commensurate scales, fails at incommensurate ones.**

**Open (conjecture — the user's bet at scale):** whether a **single** N-rational output can be a genuine **superposition** of multiple chirality/multi-perspective seams *at scale*, via a `simultaneous_rational_approx` op (shared-denominator / Dirichlet / LLL / geometry-of-numbers). srmech has **no** such primitive.

**The decidable experiment:** build `simultaneous_rational_approx(targets, max_d)` returning the shared q minimizing joint error over a target set. **Measurement:** across max_d, is there a **non-trivial limiting density** of scales at which one shared q is jointly optimal for ≥2 seams (as q=7 already is for {π,e})? Quantify the fraction of q ≤ max_d that are joint-optimal for a fixed target pair as max_d→large. A positive limiting density → the multi-seam rational is real and constructible; density→0 → the q=7 coincidence is sporadic and no single rational carries multiple perspectives at scale. Decidable per (targets, max_d); only the general density answer needs the unbuilt op.

**Answering the user directly: "I'm kinda betting there must be" — the bet is HALF-WON already.** A single denominator provably *does* fit more than one seam at commensurate scales (q=7 fits π and e). What is open is only whether that is *generic* (a positive density of scales) or *sporadic* — and that is one buildable op away from a definite answer.

---

## §7 — Figures (aphantasia — one per mechanism)

1. **The beat-WSD graph** — F₃: hub BEAT (deg 6) + three triangle arms, each closing edge annotated with holonomy 0 / 1/3 / 2/3 turn.
2. **The measured separation (headline)** — two stem plots: FLAT `[0,1,1,3,3,3,7]` with the 3-fold at λ=3 highlighted as CONFLATED (spread 0); CURVED `[0.169,0.5,0.5,1.231,1.5,1.5,3.599]` with an up-arrow on the lifted zero-mode (0→0.169) and a fan showing 3-fold→1+2.
3. **Curvature is the cause** — three multiplicity bars: FLAT `{1,2,3,1}`; q=0 magnetic `{1,2,3,1}` ("= flat"); CURVED `{1,2,1,2,1}` ("split").
4. **The C 2-perspective ceiling** — one number line; "+1/3" and "−1/3" arrows both landing on `[0.234,0.826,1.940]`. C resolves an AXIS, not two senses.
5. **The two-channel structure (replaces the single-imaginary-dim ladder)** — LEFT ODD channel (magnetic/ℂ, 1 imaginary axis, ±c collapse); RIGHT EVEN channel (V₄, four real characters + asymmetry meter). Under K4 gains(0,0,0,0,0,1): χ01=`[0,4,4,4]` beside χ10=`[0.764,2,4,5.236]`, |Δtension|=0.7639.
6. **One object, four projections (L/M/N/K fan)** — center box = one curved Hermitian H (L edge-superset store); arrows to eigenVALUES (N, best_rational=(1,2)), eigenVECTOR phases (M, "gauge-check pending"), charge SIGN (K pin), klein4 carrier (M bind).
7. **The corrected curvature/perspective ladder** — signed (ℤ₂) → magnetic (ℂ, 1 imaginary) → klein4_gain (V₄, 4 real characters), all stamped "rc299 SHIPPED"; dashed above = quaternionic/octonionic cd_laplacian (imag 3/7, UNBUILT); beyond = `cd_mult` (3-tensor associator).
8. **The two-regime carrier** — one klein4 box, two exits: LEFT ALGEBRA (M-bind / L-gain-eigenread / K-sign-degree → eigendecompose); RIGHT ADDRESSING (A-digest / B-base4-TLV / C-sector-frame / I-radix → base-4 parse + XOR-frame-off). Regime bars: encode_bytes 0.6748 (tall) vs address 0.248 (on the 0.25 floor).
9. **Laplacian = projection** — a 3-index cube (e1,e2,e4)→2·e₇ next to a greyed 2-index grid "no Laplacian (real/magnetic/V₄-gain) can hold this."
10. **Single-seam vs multi-seam rational** — LEFT nested convergents 3/1→22/7→355/113 climbing toward ONE π seam; RIGHT a shared-denominator lattice where q=7 lands on BOTH π(22/7) and e(19/7), but q=113 splits (π keeps 113, e drops to 71).
11. **The directed-channel swap (gated)** — abelian `klein4_encode_bytes` (cat==tac) → F1213 `word_to_kernel` directed glyph Class-L (edge_charge = w_fwd − w_bwd, 11/11) → live `build_genepool` re-encode, with a **USER-GATE** on the final arrow.

---

### Provenance / honesty ledger

- **rc299 main-loop re-verification:** all 10 DEMONSTRABLE figures re-run; §0 table. `__version__ = 0.9.0rc299`; `klein4_gain_laplacian` at `laplacian.py`; `klein4_relational_structure` at `laplacian.py`; `cycle_holonomy` present.
- **Corrected vs the draft:** the "V₄ NOT shipped" claim (stale rc107) is retired; the `klein4_expand`→`klein4_encode_bytes` op mislabel is fixed; `klein4_relational_structure` located in `laplacian` not `hdc`.
- **F1302 restated, not extended:** the single-imaginary-dim form is falsified by the shipped V₄ op; the honest reading is the two-channel law (§4). Internal self-correction, no external-lineage claim.
- **External citation (MPM):** the V₄ gain-graph construction is N. Reff, *Spectral Properties of Complex Unit Gain Graphs*, Linear Algebra Appl. 436 (2012) 3165–3176 (arXiv:1110.4554) — carried in srmech's own attested registry and in the `klein4_gain_laplacian` docstring; not recalled.
- **DRAWN/DERIVED guard (F1259):** every hand-set holonomy above is a DRAWN magic number until §5 step 5 derives it from the corpus.
- No lineage claims about external work; the framework reads what the structure already is.
