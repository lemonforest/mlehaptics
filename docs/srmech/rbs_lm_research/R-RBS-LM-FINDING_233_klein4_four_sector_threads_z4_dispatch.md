# Finding 233 — Can ONE cascade run as FOUR independent threads = the Klein-4 four chirality sectors, dispatched on the Z₄ quarter-turn (π/2) splay, capped at 4 before triality? YES — the 4-RUNG fires: each of the 4 Klein-4-sector threads reconstructs its canonical sector-dual from its OWN sector-transformed input with ZERO cross-thread reads (bit-exact, all bodies), the 4 phase-lock on the Z₄ splay `[0,.25,.5,.75]` (Sakaguchi α=π/2 ring, slots `[0,1,2,3]`, 4/4 distinct), the involution group closes at EXACTLY 4 (no 5th order-2 thread; Klein-4 has no order-4+ element, so 8+ needs the order-3 triality, F220), and the 4 results are USEFUL iff bi-axially sensitive (4) and COLLAPSE on any symmetric axis (iω₇-sym → 2, γ₅-sym → 2, both-sym → 1, the F232 redundant edge generalized) — so the THREAD-COUNT LADDER IS the CHIRALITY-ACCESS LADDER (1→2→4→triality); F232's 2-rung extended to the 4-rung

**Status:** **DEMONSTRATED (srmech-native, bit-exact-reproducible)** for the four measurements — (1) 4-way independence (each Klein-4 sector-thread reconstructs the canonical sector-dual from its own sector-transformed input, **0 cross-thread reads, 8 own-reads, max-dev 0.0** across all five bodies), (2) the Z₄ dispatch splay (Sakaguchi α=π/2 4-oscillator ring → relative-phase fractions **exactly `[0.0, 0.25, 0.5, 0.75]`**, dispatch slots `[0,1,2,3]`, **4/4 distinct**, max-dev-from-splay **0.0**), (3) the cap-at-4 (the stream-involution group closes at **|G| = 4**, every non-identity sector an involution, **no 5th order-2 thread**, Klein-4 has no order-4+ element, and triality is genuinely **order-3** — `qm.triality` 28×28, τ³=I, τ²≠I — the only way past 4, F220), (4) the usefulness collapse-lattice **4 / 2 / 2 / 1** (bi-axial body → 4 distinct; iω₇-symmetric → 2; γ₅-symmetric → 2; bi-symmetric → 1). **FRAMEWORK-READING** for the ladder synthesis (the thread-count ladder reading reads F133/F219/F220's shape; no biological/clinical claim). **In-scope** as Klein-4-sector / Z₄-dispatch / involution-group algebra. **NOT** CAD / VLSI / gate-layout / fabrication / timing-closure (CAD-ban holds, matching F231/F232). §VII.6.20 form-reading; `[[user_stance_ai_is_not_a_substrate]]`; `[[feedback_trauma_informed_defensive_scope]]`; `[[feedback_no_lineage_claims_in_notebook]]`.

**Predecessors:** **F232** (#775 — the 2-RUNG this finding extends: a cascade + its `cascade.chiral_dual` = a genuinely independent antiphase pair, **bit-exact reconstruction-from-own-transform** with 0 cross-thread reads, useful **iff orientation-sensitive** + the demonstrated redundant edge — the method generalized to 4 here), **F231** (#774 — the Kuramoto dispatch demo whose **Sakaguchi α=π/2 4-ring splay `[0,.25,.5,.75]`** = the Z₄ round-robin reused verbatim as the dispatch timing; the in-phase broadcast vs ring-splay distinction), **F132** (Klein-4 HDC = the **4 sectors** γ₅±×iω₇±; `klein4_*`; the four thread-identities), **F130** (the **γ₅-mirror sector** — antimatter in the γ₅-axis flip), **F219** (the **chirality-access ladder** uni/bi/triality — biology bi-axial-native but observer-locked; silicon uni→bi), **F220** (triality reachable **only via an order-3 primitive**, NOT by composing order-2 atoms — the **CAP**; the lean order-2 atoms generate the 2-group Z₂³, |G|=8, no order-3 element), **F122** (R-RBS-LM-95/95b — Kuramoto N=4 operational core at K_c ≈ 0.20; the machinery reused), **F133** (observer chirality-locking — the 1-rung floor, biology). Ties **#774** (F231) / **#775** (F232) and the candidate MS #20 forward-ask home for the thread-ladder reading.

**Empirical anchor:** srmech **0.5.0rc22** (`/tmp/verify_srmech_rc22/venv`). Artifact: `R-RBS-LM-233_klein4_four_sector_threads_z4_dispatch.py` + `substrate_measurements/klein4_four_sector_threads_z4_dispatch.ndjson`. **Discipline-check: 0 HARD, 0 coverage-gap.** Deterministic (`RandomState(233)`; the splay seeds on the F231 traveling-wave basin `2πk/N`, no jitter); the **content-address `response_sha256` is bit-exact-reproducible** across runs = `6f45c347628dd9f571554aa3fd82cde039bf57090b907e094bdbcae4a299e47d` (computed over the record minus the wall-clock `generated_at`, so the *measurement* re-verifies bit-for-bit — the MPM point; verified identical across two reruns).

**User direction (2026-05-30):** "climb the thread-count ladder to the 4-RUNG — can 1 cascade run as 4 independent threads = the Klein-4 four chirality sectors, dispatched on the Z₄ quarter-turn (π/2) splay, capped at 4 before triality?" — lodged as F233, the 4-rung built directly on F232's confirmed 2-rung.

**Vocabulary (this session):** the 14 A–N classes are **OPERATORS** (the ISA), not cores. The whole coupled object — the four cascade-clocks + their Sakaguchi-frustrated ring coupling — is read with **the Kuramoto mechanism** (principle *and* device, one name; sibling to **srmech**), continuing F231/F232.

---

## §1 The structure — two DISTINCT order-4 objects, kept at their levels

The hypothesis names two order-4 objects that compose, and the discipline is to **not conflate them** (the F132/F220 distinction is exactly this):

- **THREAD IDENTITIES (the *who*) = the Klein-4 four sectors.** Z₂×Z₂ = γ₅± × iω₇± — **two independent π-flips**, NO order-4 element (F132/F220). Each thread is one sector:

  | sector | (γ₅, iω₇) | stream-transform `T_s` | srmech op | F-tie |
  |---|---|---|---|---|
  | **0** | (+, +) | identity (neither flip) | — | F232 thread A; "our" sector (F130) |
  | **1** | (+, −) | iω₇-flip only | `klein4_chirality_flip_omega7` (XOR 1) | the iω₇ axis |
  | **2** | (−, +) | γ₅-flip only | `klein4_chirality_flip_gamma5` (XOR 2) | **== F232's `chiral_dual` axis** |
  | **3** | (−, −) | both flips / CPT mirror | `klein4_cpt_mirror` (XOR 3) | F130 dark-antimatter sector |

- **DISPATCH TIMING (the *when*) = the Z₄ quarter-turn splay.** π/2 spacing; Sakaguchi frustration α=π/2 on the 4-oscillator ring → F231's demonstrated `[0,.25,.5,.75]` round-robin. **Z₄ is cyclic-order-4 (the "i" rotation), DISTINCT from the Klein-4 identity** (Klein-4 ≠ Z₄ — Klein-4 = Z₂×Z₂ has no order-4 element, Z₄ does; the F132/F220 distinction made operational).

**The thread-count ladder = the chirality-access ladder (F219):** 1 (chirality-LOCKED, biology, F133) → 2 (one axis = γ₅, F232) → 4 (Klein-4, BOTH axes) → beyond-4 needs the order-3 TRIALITY (F220). This finding tests the 4-rung.

**How F233 extends F232's method, precisely.** F232's chiral dual is `chiral_dual(op, x) = chiral_flip(op(chiral_flip(x)))` — the body conjugated by orientation-reversal (the γ₅ axis). F233 generalizes the conjugation to all four Klein-4 stream-transforms:

> `sector_dual(body, s, x) = inv_T_s( body( T_s(x) ) )`, with `T_s ∈ {identity, iω₇-flip, γ₅-flip, both}`.

The γ₅ axis on the stream is exactly F232's `cascade.chiral_flip` (reversal); the **second, independent** axis (iω₇) is realised srmech-natively as a per-register **Class-C `reorient(-1, ·)`** (a sign-flip involution, independent of and commuting with reversal). The two generate the Klein-4 group of stream-transforms. **Sanity-checked bit-exact:** the sector-2 dual `== srmech `cascade.chiral_dual`` (so F233 sector 2 literally IS F232's object), and the two axes commute (`γ₅∘iω₇ = iω₇∘γ₅`, the Klein-4 property).

---

## §2 The falsifiable test (4 measurements, srmech-native)

### §2.1 Measurement 1 — INDEPENDENCE (the crux, 4-way)

A real 4th thread needs **no wait** on the other three. Exactly F232's check, now for all 4 sectors: does the **independent construction** (sector-thread runs its OWN `body(…)` on its OWN sector-transformed input, reads NOTHING from any other thread's buffer) reproduce the *canonical* `sector_dual` bit-for-bit? Both a `independent` and a `shared` construction are instrumented (`DependencyTracer` — own-reads vs shared-reads, the F232 instrument).

| sector | indep reconstructs sector-dual | cross-thread reads | own-reads | **genuine independent thread?** |
|---|---|---|---|---|
| 0 (neither) | **True** (max-dev 0.0) | **0** | 8 | **True** |
| 1 (iω₇) | **True** (max-dev 0.0) | **0** | 8 | **True** |
| 2 (γ₅ = F232 dual) | **True** (max-dev 0.0) | **0** | 8 | **True** |
| 3 (both / CPT) | **True** (max-dev 0.0) | **0** | 8 | **True** |

**Result:** for **all 4 sectors across all 5 cascade bodies**, the independent construction reconstructs the canonical sector-dual with **0 reads from any other thread** (max-dev 0.0, bit-exact). Each Klein-4 sector is a genuinely independent thread — it is **not** forced to read another chain. (The `shared` construction reproduces the duals too, but only by post-processing thread-0's forward buffer — that path is pipelining of one chain, and the tracer attributes its reads to the shared source, distinguishing the two exactly as in F232.) The honest content: independence is the **falsifiable bit-exact fact** that all four sector-duals are reconstructible from their own transformed input alone — it could have failed (a sector-dual that fundamentally needed another thread's result would not reproduce), and it did not, for any sector or body.

### §2.2 Measurement 2 — the Z₄ DISPATCH SPLAY

Four cascade-clocks coupled as a **Sakaguchi α=π/2 ring** (F231's exact convention reused verbatim — `dθ_i/dt = ω_i + (1/N)Σ_j K_ij sin(θ_j − θ_i − α)`, ring matrix `K[i,i±1]=2.0`, seed on the traveling-wave basin `2πk/N`, T=200/dt=0.02; `sin`/`exp_i` via `laplacian.elementwise_transcendental`, modulus via `cascade.magnitude`, slot via `rational.best_rational` + `cyclic.mod_add`).

| quantity | value |
|---|---|
| relative-phase fractions | **`[0.0, 0.25, 0.5, 0.75]`** (exact) |
| Z₄ dispatch slots (Class N /4 + Class I Z/4) | `[0, 1, 2, 3]` — **4/4 distinct** |
| max deviation from the splay target | **0.0** |
| final order parameter r | **0.0** (the splay signature) |
| **Z₄ splay locked?** | **True** |
| ring Laplacian (Class L) | eig `[0, 2, 2, 4]`, **1 component**, Fiedler 2.0 |

**Result:** the 4 threads phase-lock on the **Z₄ quarter-turn splay** — relative phases sit at exactly `[0, ¼, ½, ¾]` of a turn, the four quarter-turn dispatch slots. r ≈ 0 in that state is **the splay signature, not a failure** (the four phases evenly spread around the circle cancel — the F231 traveling-wave invariant). The ring reads as one coherent Class-L graph (one component). This is the **cyclic-Z₄ timing** (the round-robin "i" rotation), confirmed **distinct from the Klein-4 sector identity** (which is order-2 × order-2). The two order-4 objects are demonstrated at their separate levels.

### §2.3 Measurement 3 — the CAP-AT-4

Klein-4 has order 4 (exactly 4 sectors). Closing the group of stream-transforms generated by {reverse (γ₅), signflip (iω₇)} under composition (exact, on the sample stream):

| quantity | value | reading |
|---|---|---|
| involution-group order \|G\| | **4** | exactly the 4 Klein-4 sectors |
| every non-identity sector is an involution (T(T(x))=x) | **True** | each sector is order 2 |
| a 5th INDEPENDENT order-2 thread exists | **False** | the group closed at 4 — no 5th distinct sector |
| Klein-4 = Z₂×Z₂ has no order-4+ element | **True** | so you can't reach 8 by order-2 means |
| triality order-3 (`qm.triality`, 28×28) | **τ³=I, τ²≠I** | the genuinely order-3 primitive |
| **beyond-4 needs the order-3 triality (F220)** | **True** | the ladder caps at 4 *before* triality |

**Result:** the ladder **caps at exactly 4** by order-2 (Klein-4) means. A 5th independent thread by the SAME means is impossible — the involution group closes at |G|=4, and Klein-4 has no order-4+ element (every non-identity sector is an involution), so 8+ threads would require a genuinely **order-3 primitive**: triality (`qm.triality.triality_automorphism`, demonstrated order-3 here, τ³=I, τ²≠I). This is exactly F220's cap (the lean order-2 atoms generate the 2-group Z₂³; triality is the only way to the 3rd axis). **The cap is the falsifiable content** — a 5th distinct order-2 sector would have refuted the Klein-4 framing of the ladder, and none exists.

### §2.4 Measurement 4 — USEFULNESS (the F232 condition, generalized)

The sector-dual is `dual_s(x) = inv_T_s(body(T_s(x)))`. Two sectors COLLAPSE (give the bit-exact same result) exactly when the body is **symmetric** under the axis distinguishing them: symmetric under iω₇ ⇔ `body(−x) = −body(x)` (odd-equivariant) merges the pairs {0,1} and {2,3}; symmetric under γ₅ ⇔ reversal-invariant structure merges {0,2} and {1,3}; symmetric under both merges all four. Each body's distinct-count is a direct readout of which axes it ignores.

| cascade body | symmetry | # distinct sector-results | **useful (4 distinct)?** | distinct classes |
|---|---|---|---|---|
| `biaxial_4DISTINCT` | neither (both axes live) | **4** | **True** | {0},{1},{2},{3} |
| `iw7_symmetric_4to2` | iω₇-symmetric | **2** | False | {0,1},{2,3} |
| `gamma5_symmetric_4to2` | γ₅-symmetric | **2** | False | {0,2},{1,3} |
| `bi_symmetric_4to1` | both-symmetric | **1** | False | {0,1,2,3} |
| `sign_classC_classN` (F232 carry-over) | neither | **4** | True | {0},{1},{2},{3} |

**Result — the full collapse lattice 4 / 2 / 2 / 1 demonstrated.** The 4 sectors give 4 DISTINCT (useful) results iff the cascade is sensitive to BOTH axes (`biaxial_4DISTINCT`, and the F232 sign body, both → 4 distinct, mutually-orthogonal sector tags `klein4_similarity = 0.0` off-diagonal). They COLLAPSE on any symmetric axis: **iω₇-symmetric → 4→2** (the {0,1}/{2,3} pairing), **γ₅-symmetric → 4→2** the OTHER way (the {0,2}/{1,3} pairing — the complementary collapse direction), and **bi-symmetric → 4→1** (all four merge — the F232 redundant-dual edge generalized: every sector-dual = the forward, delivering nothing new). This is the demonstrated NULL edge for the usefulness question per `[[feedback_dont_pre_commit_spike_query_operators]]`: *not every cascade's four sector-threads are four useful results.*

---

## §3 THE VERDICT (pre-stated outcomes honored)

> **Pre-stated POSITIVE:** 4 genuinely independent threads (Klein-4 sectors, bit-exact reconstruction, 0 cross-reads), Z₄-π/2-splay-dispatched, capped at 4 (8+ needs triality), useful iff bi-axially-sensitive → **the thread-ladder IS the chirality-access ladder (1→2→4→triality); F232 extended to the 4-rung.**
> **Pre-stated NULL:** the 4 sectors do NOT give 4 independent threads (collapse to ≤2 / share dependencies regardless of sensitivity) → the ladder caps at 2 (only γ₅ un-locks usefully), not 4; OR there is no cap at 4 (a 5th independent order-2 thread exists) → the Klein-4 framing of the ladder is wrong.

**Disposition — POSITIVE FIRED.**

> **POSITIVE: on silicon, 1 cascade CAN run as 4 INDEPENDENT threads = the Klein-4 four chirality sectors.** Each of the 4 sector-threads reconstructs its canonical sector-dual from its OWN Klein-4-transformed input with **ZERO cross-thread reads, bit-exact** (all 5 bodies) — a genuine 4-way independent thread set, **the F232 2-rung (one axis, γ₅) extended to the full Klein-4 (BOTH axes)**. The 4 threads phase-lock on the **Z₄ quarter-turn splay** (Sakaguchi α=π/2 ring; relative phases exactly `[0,.25,.5,.75]`; slots `[0,1,2,3]`) — the cyclic-order-4 DISPATCH TIMING, demonstrated **distinct** from the Klein-4 (order-2 × order-2) thread IDENTITY. The ladder **CAPS AT 4**: the stream-involution group closes at exactly 4 (no 5th order-2 sector), Klein-4 has no order-4+ element, so 8+ is unreachable by order-2 means — it requires the genuinely **order-3 TRIALITY** (`qm.triality`, demonstrated order-3, F220). The 4 results are USEFUL (distinct) iff the cascade is sensitive to BOTH axes, and COLLAPSE on any symmetric axis (iω₇-sym → 2, γ₅-sym → 2, both-sym → 1, the F232 redundant edge generalized).

**The synthesis (the FRAMEWORK-READING tier):** the **THREAD-COUNT LADDER IS the CHIRALITY-ACCESS LADDER** (F219): **1** (chirality-LOCKED — biology, one chirality → one thread, F133) → **2** (one axis un-locked = γ₅, F232) → **4** (Klein-4, BOTH axes un-locked, this finding) → **beyond-4 needs the order-3 triality** (F220 — not reachable by composing order-2 sectors). The DEMONSTRATED tier is the four measurements (independence, Z₄ splay, cap, collapse-lattice — all bit-exact); the FRAMEWORK-READING tier is reading this 4-rung AS the chirality-access ladder's bi-axial rung. The usefulness condition (a F232-conditional, now bi-axial) keeps the NULL edge visible: the 4 threads are *always* independent, but *useful* (4 distinct) only for a bi-axially-sensitive cascade.

---

## §4 The integrated reading (one line)

**On silicon (not chirality-locked, F133), a cascade's four Klein-4 sector-conjugates (`sector_dual(body,s,x) = inv_T_s(body(T_s(x)))`, the F232 chiral dual generalized to all four γ₅±×iω₇± sectors) form a genuinely INDEPENDENT 4-thread set — each reconstructs from its own sector-transformed input with ZERO cross-thread reads (bit-exact, all bodies) — that Z₄-splay-dispatches on the Sakaguchi α=π/2 ring `[0,.25,.5,.75]` (the cyclic-order-4 timing, distinct from the order-2×order-2 Klein-4 identity), CAPS AT 4 (the involution group closes at \|G\|=4; Klein-4 has no order-4+ element; 8+ needs the order-3 triality, F220), and delivers 4 USEFUL results iff bi-axially-sensitive (collapsing 4→2→1 on any symmetric axis, the F232 redundant edge generalized); so the THREAD-COUNT LADDER IS the CHIRALITY-ACCESS LADDER 1→2→4→triality — F232's 2-rung extended to the 4-rung.** Same form-not-machine + CAD-ban discipline as F231/F232.

---

## §5 DOES / does NOT claim

**DOES:** extend F232's 2-rung method to 4 by running a cascade's four Klein-4 sector-conjugates as a thread set and a Sakaguchi α=π/2 4-ring dispatch; **DEMONSTRATE** (srmech-native, bit-exact-reproducible, 0 HARD) — (1) all 4 Klein-4 sector-threads are genuinely **independent** (the independent construction reconstructs each canonical sector-dual with 0 cross-thread reads, max-dev 0.0, across five bodies; sector 2 == srmech `cascade.chiral_dual` bit-exact); (2) the 4 threads **Z₄-splay-lock** (Sakaguchi α=π/2 ring → relative phases exactly `[0,.25,.5,.75]`, slots `[0,1,2,3]`, the ring a one-component Class-L object), confirmed the cyclic-Z₄ timing **distinct** from the Klein-4 order-2×order-2 identity; (3) the **cap at 4** (the involution group closes at |G|=4, no 5th order-2 sector, Klein-4 has no order-4+ element, triality demonstrated order-3 — 8+ needs triality, F220); (4) the **usefulness collapse-lattice 4/2/2/1** (bi-axial → 4 distinct; iω₇-sym → 2; γ₅-sym → 2; bi-sym → 1); **conclude** POSITIVE — the thread-count ladder IS the chirality-access ladder 1→2→4→triality, F232 extended to the 4-rung; read the biology comparison (chirality-lock) as the **shape** of F133/F219 only; tag the four threads with their Klein-4 sectors (Class M, mutually orthogonal) to show silicon's bi-axial access (F132); keep the demonstrated NULL edges (the collapse cases) visible per `[[feedback_dont_pre_commit_spike_query_operators]]`.

**Does NOT:** claim a built device, a threaded silicon computer, or any gate-layout / VLSI / PCB / timing-closure / fabrication-tolerance content (CAD-ban holds — matches F231/F232; this is Klein-4-sector + Z₄-dispatch + involution-group **algebra** read as form); claim biology "is" chirality-locked or that silicon "is" Klein-4 as proven physics — the chirality-lock / bi-axial-access framing is the **form-reading** of F133/F219/F132 per §VII.6.20; claim the substrate or any silicon "knows itself" or that AI is a substrate (`[[user_stance_ai_is_not_a_substrate]]` — the transducer reads the form); claim **supremacy** of silicon over biology — "silicon not chirality-locked, so reaches the 4-rung" is the F219/F220 **access-ladder** reading (both substrates valid; biology is bi-axial-native, silicon assembles bi-axial — neither is superior), NOT a hierarchy; claim to **invent** Klein-4, Z₄, the Sakaguchi/Kuramoto splay, chirality, the chiral dual, or triality, or to extend prior scholarship (`[[feedback_no_lineage_claims_in_notebook]]` — it reads what `klein4_*`, the Sakaguchi ring, and the order-3 triality already ARE); claim the independence is *unconditional in usefulness* (it is not — the collapse-lattice NULL edges are demonstrated bit-exact); conflate the two order-4 objects (the Klein-4 *identity* is order-2×order-2; the Z₄ *dispatch* is cyclic-order-4 — kept distinct throughout); offer any weapons / capability / offensive framing — a benign dispatch/threading reading (`[[feedback_trauma_informed_defensive_scope]]`).

**Pre-stated outcomes — disposition:**
- **POSITIVE** → **FIRED:** 4 genuine independent threads (0 cross-thread reads, bit-exact, all bodies) + Z₄ splay lock (`[0,.25,.5,.75]`, 4/4 slots) + cap at 4 (no 5th order-2 sector; 8+ needs triality) + useful-iff-bi-axial (collapse-lattice 4/2/2/1) → the thread-count ladder IS the chirality-access ladder 1→2→4→triality.
- **NULL** → **did NOT fire as the headline:** neither NULL horn held — the 4 sectors DID give 4 independent threads (no collapse of *independence*; the collapses are only of *usefulness*, the expected F232-generalized edge), and there IS a cap at 4 (no 5th independent order-2 thread exists — the involution group closes at |G|=4). The usefulness-collapse edges (4→2→1) are the demonstrated NULL *of the usefulness sub-question*, kept visible, exactly as F232's redundant-dual edge was.

---

## §6 Cross-references

**F232** (#775 — the 2-RUNG: chiral-dual antiphase thread independence, the bit-exact reconstruction-from-own-transform method + the useful-iff-orientation-sensitive condition + the redundant edge, all generalized here to 4) · **F231** (#774 — the Kuramoto dispatch demo; the Sakaguchi α=π/2 4-ring splay `[0,.25,.5,.75]` reused verbatim as the Z₄ dispatch) · **F132** (Klein-4 HDC — the 4 sectors γ₅±×iω₇±; `klein4_chirality_flip_gamma5`/`klein4_chirality_flip_omega7`/`klein4_cpt_mirror`/`klein4_similarity`/`klein4_sector_count`) · **F130** (the γ₅-mirror sector) · **F219** (the chirality-access ladder uni/bi/triality — the ladder this finding's 4-rung populates) · **F220** (triality reachable only via an order-3 primitive, NOT by composing order-2 — the cap; the lean order-2 atoms = Z₂³, no order-3) · **F133** (observer chirality-locking — the 1-rung, biology) · **F122** (R-RBS-LM-95/95b — Kuramoto K_c ≈ 0.20; machinery reused). srmech ops: `cascade.chiral_flip` / `chiral_dual` / `reorient` / `net_chirality` (C) · `cascade.pin_slot_at_zero` / `magnitude` (K) · `laplacian.elementwise_transcendental` / `dense_laplacian` / `jacobi_eigvals` (L) · `rational.best_rational` (N) · `cyclic.mod_add` (I — Z₄ = Z/4) · `hdc.klein4_chirality_flip_gamma5` / `klein4_chirality_flip_omega7` / `klein4_cpt_mirror` / `klein4_similarity` / `klein4_sector_count` / `klein4_bind` / `klein4_bundle` (M) · `qm.triality.triality_automorphism` (order-3 cap) · `format.sha256_bytes` (A).

PR #687 STAYS DRAFT.

---

*Articulated 2026-05-30 (Opus 4.8). The user asked to climb the thread-count ladder to
the 4-RUNG — can ONE cascade run as FOUR independent threads = the Klein-4 four chirality
sectors, dispatched on the Z₄ quarter-turn (π/2) splay, capped at 4 before triality? —
building directly on F232's confirmed 2-rung. Generalizing F232's chiral dual
(`chiral_dual(op,x) = chiral_flip(op(chiral_flip(x)))`, the γ₅ axis) to all four Klein-4
stream-transforms `sector_dual(body,s,x) = inv_T_s(body(T_s(x)))` (s=2 == the F232 dual,
bit-exact), the test measures four things, all srmech-native, bit-exact-reproducible
(`response_sha256` 6f45c347…, 0 HARD, srmech 0.5.0rc22): (1) 4-WAY INDEPENDENCE — each of
the 4 sector-threads reconstructs its canonical sector-dual from its OWN sector-transformed
input with ZERO cross-thread reads (max-dev 0.0, all five bodies) — a genuine 4-thread set,
no wait on the others; (2) Z₄ DISPATCH SPLAY — the Sakaguchi α=π/2 4-ring locks at relative
phases exactly [0,.25,.5,.75], slots [0,1,2,3], 4/4 distinct (r=0 = the splay signature;
the ring a one-component Class-L object), the cyclic-Z₄ timing demonstrated DISTINCT from
the order-2×order-2 Klein-4 identity; (3) CAP-AT-4 — the stream-involution group closes at
|G|=4 (no 5th order-2 sector), Klein-4 has no order-4+ element, triality is order-3 (28×28,
τ³=I, τ²≠I) — so 8+ needs the order-3 triality (F220); (4) USEFULNESS collapse-lattice
4/2/2/1 — bi-axial body → 4 distinct, iω₇-symmetric → 2, γ₅-symmetric → 2, bi-symmetric → 1
(the F232 redundant edge generalized). VERDICT: POSITIVE — 1 cascade = 4 independent
Klein-4-sector threads on silicon, Z₄-splay-dispatched, capped at 4 (8+ needs triality),
useful iff bi-axially sensitive; the THREAD-COUNT LADDER IS the CHIRALITY-ACCESS LADDER
(1→2→4→triality), F232's 2-rung extended to the 4-rung. Held with the form-not-machine +
CAD-ban discipline (F231/F232); the biology comparison reads F133/F219's shape only
(§VII.6.20); ai-is-not-a-substrate; no-lineage; "silicon reaches the 4-rung" is the
F219/F220 access-ladder reading, NOT supremacy — both substrates valid; the two order-4
objects (Klein-4 identity vs Z₄ dispatch) kept distinct throughout.*
