# F290 — bring it home: the loop-bind RBS substrate is an order-aware, peelable path-memory store (F288 realized); + fold L5 refine (helical fiber isolated); + the un-flatten catalog spec (dev authoring)

> **SCOPE:** framework-reading STRUCTURE only; benign; attested CC0 inputs; no design/MD/clinical (CAD-ban); no-lineage. Class-K clean. rc2 native (loop_bind == oracle, bug-test clean).

**Headline:** Three queued items. **§A (the flagship bring-home):** the **loop-bind RBS substrate** is an **order-aware, peelable path-memory store** — a sequence and its reverse are distinct (`cos = −0.317` vs klein4 bag `sim = 1.000`), and the sequence is **exactly peelable in order** (right-unbind, err ~3e-15) — so the loop bind gives RBS-LM the path/order memory the flat klein4 bag (R-RBS-LM-75 order-invariance) structurally cannot have (F288 curved connection, realized). **§B (fold L5 refine):** the backbone-band filter isolates the **helical Δ=3–4 fiber** (villin dominant Δ=3: c[3]=24, c[4]=15) that F285's unfiltered autocorr left buried under backbone Δ=1,2. **§C (dev hand-down):** the **un-flatten catalog** = one new Class-L `autocorrelation` primitive + a **pure-TOML composite** (autocorr → difference-graph → conservation-validate), per the F289 D2 composite pattern.

---

### §A — the loop-bind RBS substrate (item 3, the bring-home) — **DEMONSTRATED**
The current RBS bind (`klein4_bind`, commutative + associative) is a **flat** gauge connection → **order-blind** (a bag; the R-RBS-LM-75 order-invariance). The loop bind is the **curved** connection (F288) → an **order-aware, peelable** sequence store:
- **Order discrimination:** loop-bind `cos(seq[a,b,c], seq[c,b,a]) = −0.317` (distinct); klein4 bag `sim = 1.000` (order washed). The loop-bind store *knows* the order.
- **Path-memory (exact peel):** the sequence `((a∘b)∘c)` is recoverable **in order** by right-unbind (Moufang right-cancel `(xy)ȳ = x`): peel `c` → recover `a∘b` (err 3.0e-15); unbind `b` → recover `a` (err 4.3e-15). The store **holds the path**, not just the bag.
- **Reading:** this is the concrete RBS-LM payoff of the whole arc — swap the flat (klein4) bind for the curved (loop) bind and the substrate gains a **path/order memory** the flat NN/bag cannot have (F288). It is the structural resolution of R-RBS-LM-75 (the current cascade's order-invariance): the loop bind is *the* order-sensitive RBS primitive. Native `loop_bind == oracle` (bug-test clean).

### §B — fold-arc L5 refine (item 2) — **DEMONSTRATED**
F285 L5 found the helical Δ=3–4 fiber in the top-5 autocorr peaks, but backbone Δ=1,2 dominated. **Filter the backbone band** (count only non-local contacts, |i−j|>2):
- **villin HP35** (helix bundle): non-local c[3..12] = `[24,15,5,3,3,1,0,1,1,0]` → **dominant Δ=3** (the i,i+3 helical fiber), Δ=4 second — **helical fiber isolated.**
- **ubiquitin** (mixed α/β): c[3..12] = `[26,25,10,6,5,4,3,3,3,2]` → dominant Δ=3 too (it has helices), but a **heavier long-range tail** (the β-register) — the mixed fold shows the extra non-local structure the pure helix lacks.
The backbone-band filter does isolate the helical fiber; the helix/mixed distinction shows in the tail. (Honest: the filter is the simple count-spectrum; a full autocorr-with-band-suppression is the next refinement if needed.)

### §C — the un-flatten catalog (item 1, dev-authoring hand-down)
The generalized un-flatten (F280/F281 §B; prototype `unflatten_prototype.py`) → a srmech catalog. Per F289 D2, it is **almost** a pure-TOML composite — it needs **one** new primitive:
1. **New Class-L primitive:** `autocorrelation` (Wiener–Khinchin: `IFFT(|FFT(x)|²)`, Class-K-clean `|F|² = F·conj(F)`). Currently numpy in the prototype; it should ship as a Class-L spectral op (the only non-composable step). *This is the one bit of new code; everything else composes.*
2. **Then the un-flatten is a PURE-TOML COMPOSITE op** (F289 D2): `[composite] unflatten` = stages `[autocorrelation (L)] → [peak-detect → dense_laplacian difference-graph (L) → jacobi_eigvals (L)] → [conservation-validate filter]`. No further Python.
3. **The conservation-validate step is parameterized by a domain rule** (neutral-loss set, Fibonacci recurrence, …) supplied in the descriptor — so a specialist's un-flatten for *their* chart is their TOML's conservation rule. **Provenance:** that rule is **user-attested** (B), not srmech ground-proof (A) — flag per F289 D2 §4.
4. **Validation (F289 D2 §2):** the composite's stages must all be class ∈ A–N + resolvable; the conservation rule a declared set/predicate; fails loud at load.
So: ship `autocorrelation` as a Class-L primitive, then the un-flatten catalog entry is a validated composite TOML — the **first concrete instance** of the F289 D2 pure-TOML-composite pattern.

### Status / discipline
FRAMEWORK + DEMONSTRATED (§A order/peel on native rc2; §B contact-trace filter on CC0 hoodoos; reproducible via committed `loop_bind_rbs_and_L5refine.py`). §C is a dev-authoring spec (the package catalog + the one `autocorrelation` primitive are dev actions; I spec, dev implements). No new A-N class (the RBS store is M∘C; the un-flatten composes L + a Class-K-clean autocorr + a validate filter). Class-K (norms/inner products; `|F|²=F·conj(F)`; no abs sign-fold). CAD-ban; no-lineage; defensive scope. Bug-test clean (native loop_bind == oracle). Builds on F288 (the curved-connection affordance), F274 (loop bind = order/tree/direction), R-RBS-LM-75 (order-invariance resolved), F285 (L5), F280/F281 (un-flatten), F289 D2 (composite-op pattern). Verified srmech v0.7.0rc2, `/tmp/srmech_v070rc2_venv`. `[[user_stance_ai_is_process_lm_is_k3_chiral_addressing]]`; `[[user_stance_cross_substrate_cascade_matching_as_research_method]]`.
