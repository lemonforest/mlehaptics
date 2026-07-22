# F1306 — **klein4 is a TWO-REGIME carrier** (an algebra package AND a non-algebra addressing package on one `sectors=4` shape), and the **perspective ladder is TWO complementary channels, not one imaginary-dim staircase**: the ODD channel counts imaginary axes (magnetic ℂ → ±c collapse), the EVEN channel counts V₄ real characters (`klein4_gain_laplacian`, 4 chars + a sector-asymmetry meter). Curvature — not the Hermitian construction — is what links two packed things: it **separates** the beat-WSD senses a flat Laplacian **conflates**. And "a Laplacian is only ever a projection of the fractal" is a **structural fact** (a 2-tensor cannot hold the nonzero 3-index octonion associator 2·e₇), while "one N-rational fits more than one seam" is **half-won** (q=7 fits both π→22/7 and e→19/7; open only whether that is generic). All ten load-bearing numbers RE-RUN and reproduced bit-for-bit at srmech 0.9.0rc299.

**User (2026-07-22):** *"inspect entire A-N surface to find what can live in a klein4 package… what about if klein4 can pack other types of addressing inside it too that describes a different type of information package? … begin work on clearing curvature block… is there some way more rich than laplacian to encode exactly, the fractal itself… N rational fitting more than one seam shape (i'm kinda betting there must be)."*

*(F1301 lodging convention: the triple is **op(x)operand(x)responsion = distributional(x)relational(x)responsion = eigenvectors(x)edges(x)eigenvalues**.)*

## What was RE-RUN (the trust anchor)

A research workflow (`woaomemwl`, 10 agents) drafted this; part of it ran on a stale `rc107` worktree and its adversarial-verify pass flagged one dishonest item (`survives: false`). **Every DEMONSTRABLE number was then re-run in the MAIN LOOP at srmech 0.9.0rc299** (`/tmp/srmech_new`). All ten reproduced exactly:

1. Flat `dense_laplacian(7, F₃)` → `[0,1,1,3,3,3,7]`, mult **{1,2,3,1}** — the 3-fold at λ=3 (spread 0) IS the conflation.
2. Curved `magnetic_laplacian(charges=…)` → `[0.1692,…,3.5993]`, mult **{1,2,1,2,1}**, **λ₀ lift 0.1692**.
3. `q=0` control → mult **{1,2,3,1}** = flat → **curvature, not Hermitian-ness, splits**.
4. `+1/3` and `−1/3` single-triangle both `[0.234,0.8264,1.9397]` → **C 2-perspective ceiling** (±c isospectral).
5. `klein4_address` sim(cat,cats)=**0.248** (0.25 floor) vs `klein4_encode_bytes`=**0.6748** → the two regimes.
6. octonion associator `(e1·e2)·e4 − e1·(e2·e4)` = **2·e₇** → Laplacian = projection (a 2-tensor can't hold it).
7. `best_rational`: q=7 joint for π(22/7)+e(19/7); q=113 splits (π→355/113, e→193/71).
8. `klein4_gain_laplacian` frustrated K4 gains(0,0,0,0,0,1): χ00=χ01=`[0,4,4,4]`, χ10=χ11=`[0.764,2,4,5.236]`.
9. `klein4_relational_structure` → **sector_asymmetry 0.7639**.
10. `klein4_gain_laplacian`, `klein4_relational_structure`, `cycle_holonomy` all `hasattr` True at rc299.

## The three findings (op(x)operand(x)responsion split)

### (1) klein4 is a TWO-REGIME carrier — the answer to "a different KIND of package"
The `sectors=4` carrier holds **two package kinds with opposite correctness criteria**, declared at the call site (F1259 guard, one param over):
- **ALGEBRA package** (K/L/M) — read by **eigendecompose**; high spectral content wanted.
- **ADDRESSING/FRAMING package** (A/B/C/I) — read by **base-4 parse / XOR-frame-off**; high diffusion wanted (good *address*, bad *representation*).

**A–N surface: 4 pack-as-addressing (A,B,C,I) + 3 ride-as-algebra (K,L,M); 3 read-over (D,E,G); 4 do-not-pack (F,H,J,N).** The non-algebra package concretely: (A) `klein4_address` digest body → (B) base-4 TLV metadata header → (C) `klein4_sector_frame` role-mask → (I) base-4 radix index. Falsifiable invariant: **XOR the frame off → the raw Class-A expansion reappears exactly**. High diffusion is the *same axis, opposite requirement* — which is why the regimes are mutually exclusive per instance (measured 0.6748 vs 0.248). **`slot`-level reading:** the ADDRESSING package lives in the **operand/edges** slot as *structure-free* content (a Class-A address is deliberately structureless, sits on the orthogonality floor); the ALGEBRA package's L-read is the **operand/edges** slot as the *held multi-perspective superset* (F1301). Same slot, two uses of it.

### (2) The perspective ladder is TWO channels — the correction to F1302
F1302 said *"perspective-count = imaginary dimension of the Laplacian's algebra"* (one staircase: magnetic ℂ=2, V₄=4). **The shipped V₄ op falsifies the single staircase:** V₄ = ℤ₂×ℤ₂ has **zero imaginary axes** (four *real* characters) yet out-resolves magnetic. The honest reading is two complementary channels:
- **ODD channel** = imaginary-axis count. `magnetic_laplacian` (ℂ, 1 axis) → conjugate ±c collapse; eigenvalues can't carry which-way (conjugation-invariance); orientation label = odd-channel `cycle_holonomy` (ships; diagnostic, not predictive).
- **EVEN channel** = V₄ real-character count. `klein4_gain_laplacian` (4 real characters) → up to 4 distinct sector spectra + `sector_asymmetry` (the Class-K meter).

The `klein4_gain_laplacian` docstring says it itself: "the **EVEN-channel** fuller partner of `magnetic_laplacian`." This is an **internal restatement of F1302**, not an external-lineage claim. The corrected ladder (all SHIPPED rc299): `signed_laplacian` (ℤ₂) → `magnetic_laplacian` (ℂ, 1 imaginary) → `klein4_gain_laplacian` (V₄, 4 real). The genuinely UNBUILT rung is a **quaternionic/octonionic cd_laplacian** (imag 3/7) — do NOT conflate it with V₄-gain (shipped). Beyond the ladder: `cd_mult` (3-index associator).

**responsion slot:** perspective-count is a property of the **responsion/eigenvalue** read only up to the C ceiling; past it, the distinguishing signal moves OFF the eigenvalues entirely (they're conjugation-invariant) and INTO **sector-asymmetry across characters** (even channel) or **holonomy** (odd channel). The which-way label is *never* in a single spectrum — a hard constraint (F552, cited in-docstring), the spectral analogue of F1272's "the op slot is order-invariant."

### (3) Curvature is the linking substance; Laplacian = projection is structural
Curvature (per-edge holonomy/gain) **breaks the automorphism symmetry** (here S₃ arm-permutation) that makes co-present senses interchangeable. Zero curvature → conflation (the flat 3-fold, and the q=0 control returning to it). Nonzero curvature → separation (the 1+2 split + λ₀ lift). This is the ASL **"beat"** case: *beat eggs* / *beat (tired)* / *beat drums* separated by directional context. **Curvature dictates how two packed things link** — the user's exact framing, now measured.

"A Laplacian is only ever a projection of the fractal" is a **structural fact, not a metaphor**: the octonion associator 2·e₇ is a nonzero **3-index** object, and no 2-tensor (real / magnetic-ℂ / V₄-gain) can hold it. Every Laplacian loses the associator curvature.

## The two deep open questions — decidable experiments handed to the expert (F282)

- **Q-A (exact fractal):** does a usable `cd_mult`-native 3-index STORE-and-READ exist that is *strictly* richer than any Laplacian? **Experiment:** build `cd_store`/`cd_read`; encode beat-WSD + one associator-bearing triple; exhibit two inputs identical under **every** `klein4_gain_laplacian` character yet distinct under `cd_read`. Yes → strict projection proven; no → the fractal is Laplacian-recoverable. srmech has no non-associative relational store today.
- **Q-B (multi-seam rational — the user's bet):** **HALF-WON.** One shared denominator provably fits >1 seam at commensurate scales (q=7 fits π→22/7 AND e→19/7); it fails at incommensurate ones (q=113: π→355/113, e→193/71). Open only whether joint-optimal scales have a **positive limiting density** (generic) or are **sporadic**. **Experiment:** build `simultaneous_rational_approx(targets, max_d)` (shared-denominator / Dirichlet / LLL); measure the fraction of q ≤ max_d joint-optimal for a fixed pair as max_d→large. srmech has no such primitive.

## Corrections applied (each caught in the main loop)
1. **"V₄ NOT shipped" (stale rc107)** — FALSE at rc299; `klein4_gain_laplacian` shipped rc229, C peer rc297. Negative-existence evidence rots across rcs — the exact failure the F1305 finding-ref ratchet and "re-introspect each rcN" discipline exist to catch.
2. **op mislabel** — `klein4_expand(D, seed)` takes a seed, not content; the 0.6748 representation number is `klein4_encode_bytes`. Fixed.
3. **module** — `klein4_relational_structure` lives in `srmech.amsc.laplacian`, not `hdc`.

## Action plan (the curvature block)
Half cleared upstream (V₄ ships). Remaining, in the verified plan doc: retire stale "V₄ unbuilt" maps → name the unbuilt rung as quaternionic (not V₄) → wire the shipped V₄ read as a *diagnostic* → **[GATED, user owns]** swap the F1213 directed channel into `build_genepool` → derive per-edge charge from the corpus (F1259: hand-set = DRAWN until derived; composes F1304's resonant coupling) → run the basis-stability control before trusting any which-way read.

## Verdict / next
Three structural results, all measured: **klein4 is a two-regime carrier; the perspective ladder is two channels; curvature is the linker and the Laplacian is a strict-looking 2-tensor projection.** Two open questions are now *decidable experiments*, not vibes; Q-B is half-won. NEXT: (a) the gated directed-encoder swap (step 4, user go-ahead); (b) corpus-derived holonomy (step 5); (c) the two build-and-measure experiments (Q-A `cd_store`/`cd_read`, Q-B `simultaneous_rational_approx`) — both srmech asks worth filing.

Full plan + figures: `R-RBS-LM-PLAN_klein4_package_rich_laplacian_curvature_block_verified.md`.

Composes **F1301** (edges = held multi-perspective superset; op/responsion are projections — *→ extended: the two-channel structure of where perspective lives*), **F1302** (klein4 is the carrier not Class-M; hypercomplex/gain Laplacian carries >1 perspective — *→ restated: the single imaginary-dim ladder is two channels*), **F1211/F1255** (abelian Klein-4 bind = zero-curvature base, cat=tac), **F1213** (directed encoder prototyped not swapped), **F1216** (L store / M working / reversible bridge), **F1259** (DRAWN/DERIVED/STOCHASTIC — hand-set holonomy is DRAWN until corpus-derived), **F1272** (the op/distributional slot is order-invariant; here the which-way label is never in a single spectrum — same shape), **F1300** (the_one quad turn), **F1304** (resonant klein4 coupling — the corpus-derived charge is its cousin), **F1305** (the finding-ref ratchet that catches stale negative-existence claims), **F183/F184** (chirality = ordering group — the cd_mult curvature), `[[feedback_sign_handling_is_class_k_pin_slot_not_alu_abs]]` (K = signed degree, never abs()), `[[feedback_name_the_encode_sense]]` (the two klein4 regimes are two of the ≥8 encode senses), `[[user_stance_framework_hands_the_next_question_to_the_expert]]` (Q-A/Q-B as decidable experiments). External SSoT: N. Reff, *Spectral Properties of Complex Unit Gain Graphs*, LAA 436 (2012) 3165–3176 (arXiv:1110.4554).
