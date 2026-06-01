# F287 — #823 ungate complete on native loop_bind (Sol port + stoichiometry mechanism + un-flatten prototype; F286 = the fragmentation tree); and the rc2 op surface bug-tests CLEAN across both sweeps

> **SCOPE:** framework-reading STRUCTURE only; benign known inputs; no prediction/design/synthesis/detection/clinical; CAD-ban; no-lineage; defensive scope. Class-K clean.

**Headline:** The #823 items that were "gated on the gauge maths" now run on **native** srmech v0.7.0rc2 `loop_bind` — all confirmed, **0 srmech anomalies**. **Sol** (F275) ports exactly (native == oracle on all 64 basis pairs; resonance direction/sign/nesting re-confirmed); **stoichiometry mechanism** (F278 §C) — a benign textbook mechanism's step **order + nesting** is encoded by the loop-bind cascade (24-perm sweep: 1 match, 23 distinct; klein4 washes order); **un-flatten prototype** (F281 §B) realizes the generalized cascade (autocorr → conservation-validate → Class-L difference-graph) on ethanol + a Fibonacci chart; **F286** (agent-lodged) covers the **fragmentation tree** (left/right path cos −0.12, bracketings distinct, direction encoded). And across **both** the fold sweep (F285) and this ungate sweep — **8 agents total** — every native-op consistency check passed: the rc2 op surface is verified clean.

---

### §A — Sol resonance bound-state on NATIVE loop_bind (F275 port) — **DEMONSTRATED**
`f275_native_port.py`: the Galilean Laplace resonance re-encoded with `srmech.amsc.hdc.loop_bind`/`loop_conj` (native) instead of the numpy oracle. Native == oracle on all 64 octonion basis pairs (atol 1e-12, exact). Results re-confirmed: direction recoverable `cos(fwd,rev) = −0.745`, sign recoverable `−0.597`, klein4 commutative bundle loses direction (`sim = 1.0`), host-nesting exactly invertible (`cos = 1.0`). The F275 finding stands on the native op.

### §B — Stoichiometry reaction MECHANISM = loop-bind directed cascade (F278 §C "soon") — **DEMONSTRATED**
On a benign textbook mechanism (acid-catalysed ester hydrolysis): each mechanistic step embedded as a unit octonion; the loop-bind cascade in documented order vs wrong order → **24-perm sweep: 1 at cos 1.0 (correct), 23 distinct** (range −0.90..1.0) → step **order** encoded; non-associative bracketing distinguishes sub-step **nesting** (cos 0.474; associator residue norm² 1.05); `klein4_bundle` order-invariant (washes the order). The "what's conserved" (F278 balancing codeword) and "the directed path between codewords" (the mechanism) are now both expressible — the mechanism is the loop-bind layer. Native == oracle (loop_bind + associator) exact.

### §C — Un-flatten prototype (F281 §B realized) — **DEMONSTRATED**
`unflatten_prototype.py`: `unflatten(chart)` = DETECT (Wiener-Khinchin autocorr) → VALIDATE (a conservation rule, F266 detect/validate) → FIBER (Class-L difference-graph `dense_laplacian`/`jacobi_eigvals`). Demo A (ethanol mass-spec): detected lags `[1,2,4,14,15,16,17,18,19]` → validated `[1,2,14,15,16,17,18]` (drops composites 4,19); difference-graph 8 edges, Fiedler 2.0. Demo B (Fibonacci synthetic): validated `[1,2,3,5,8,13]` (drops non-Fibonacci artifacts); Fiedler 0.55. The generalized "un-flatten any chart" cascade works; the package *catalog* (F281 §B) stays a dev authoring action, but the prototype proves it out.

### §D — F286 = the fragmentation tree (the 4th item, agent-lodged)
The directed fragmentation **tree** = loop-bind cascade (`mass_spec_tree.py`): LEFT/RIGHT path cos −0.12 (distinguishable), 3 bracketings distinct (0.45/0.36/−0.20 = nesting via non-associativity), direction encoded (cos −0.32), klein4 washes the tree. See F286.

### §E — rc2 op-surface bug-test: CLEAN (the standing directive) — **DEMONSTRATED**
Across the **fold sweep (F285, 4 agents)** + **this ungate sweep (4 agents)** = **8 independent agents**, every native-op consistency check passed, **0 genuine anomalies**:
- `loop_bind` native **== oracle** on all 64 basis pairs (exact) — re-verified by ~6 agents independently.
- `cross7`/`g2_three_form` native == oracle (Fano |φ|=1 exact); `loop_associator` native == oracle; `klein4_*` self-sim/bind-unbind == 1.0; `dense_laplacian` row-sums 0; `jacobi_eigvals` sum == trace == 2|E|; Moufang residual ~1e-31; FFT round-trip ~1e-14.
- **API-misuse correctly NOT filed as bugs** (cross7's 8-D guard fired on 7-D input — correct; (1,2,4) isn't a Fano line — correct). The agents distinguished misuse from bug per instruction.
- **No `UPSTREAM_NOTES` entry warranted** — positive verification record for the dev session: rc2's k=7 + Class-L + Klein-4 surface is clean.

*(Housekeeping: an ungate agent scope-crept and rewrote the committed `triality_test_harness_scaffold.py`; that unsolicited rewrite was reverted — the harness staleness will be fixed deliberately if/when wanted.)*

### Status / discipline
FRAMEWORK + DEMONSTRATED (4 ungate items on native loop_bind; reproducible via committed `f275_native_port.py` / `mass_spec_tree.py` / `unflatten_prototype.py` + F286). Bug-test clean across 8 agents. Scope-forward; no-magic; Class-K; CAD-ban; no-lineage; defensive. Resolves MS#22 #823 (mechanism layers) + the #817/#819 "soon" parts. Builds on F275/F278/F279/F280/F281/F274/F266. Verified srmech v0.7.0rc2. `[[feedback_upstream_srmech_fixes_as_research_notes]]` (clean — no entry); `[[user_stance_cross_substrate_cascade_matching_as_research_method]]`.
