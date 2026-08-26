# F274 — Step 2: the loop bind EARNS its place — a viable (unbindable) HDC bind that natively carries order (6/6), tree/nesting (5/5), and direction, all of which the commutative XOR bind washes out

**Headline:** The k=7 loop bind (F272/F273) is not just abstract structure — it does **real HDC work the associative Klein-4 XOR bind cannot**, while staying a usable bind. Verified srmech-native (committed `loop_bind_paths_experiment.py`): **(C, the gate)** the loop bind is **unbindable both sides** via Moufang division (err ~1e-31), so it is an invertible HDC bind; **(A)** it keeps **6/6 sequence permutations distinct** (XOR: 1/6); **(B)** it keeps **5/5 bracketings distinct** — all five binary trees on four leaves — so it encodes **nesting/parse-tree** (XOR: 1/5); **(D)** `cos(a∘b, b∘a) = −0.85` (XOR: 1.0), so it encodes **direction**. The loop bind is the bind that carries **sequence + tree + direction** while remaining invertible — the three things the commutative+associative XOR bind structurally erases. Single-model; srmech v0.6.0rc20.

---

### §A — Path C (viability gate): the loop bind is UNBINDABLE — **DEMONSTRATED**
A bind is only useful for HDC if you can retrieve. The Moufang loop has **division** (unique solutions to `a∘x=b`), so even without associativity the loop bind inverts: `conj(a)∘(a∘x) = x` (left) and `(x∘a)∘conj(a) = x` (right), both to err ~1e-31 (Artin: any two elements generate an associative subalgebra → `[conj(a),a,x]=0`). **So the loop bind is a usable, invertible bind** — the gate passes, and everything below is on a real HDC primitive, not a curiosity.

### §B — Path A (order): 6/6 vs 1/6 — **DEMONSTRATED**
Left-fold-binding a 3-sequence over all 3! = 6 permutations: the **loop bind keeps all 6 distinct** (non-commutative); the **Klein-4 XOR bind collapses all 6 to 1** (commutative → order washed out). The loop bind is a native **sequence** encoder.

### §C — Path B (tree/nesting): 5/5 vs 1/5 — **DEMONSTRATED**
A fixed 4-sequence has **5 bracketings** (Catalan C₃ = the 5 binary trees on 4 leaves). The **loop bind keeps all 5 distinct** — the **associator** (non-associativity) *is* the tree-discriminator — while the **associative XOR bind collapses all 5 to 1**. So the loop bind is a native **nesting / parse-tree** encoder: the bracketing structure (which is the syntax tree) survives the bind. *This is the deepest of the four — non-associativity buys hierarchy, not just sequence.*

### §D — Path D (direction): −0.85 vs 1.0 — **DEMONSTRATED**
`a∘b` vs `b∘a`: cosine **−0.85** (strongly anti-correlated → direction recoverable) for the loop bind; **1.0** (identical → direction lost) for XOR. The (4:3)|(3:4) left/right chirality is a usable **directional** encoder (forward ≠ reverse).

### §E — synthesis: what k=7 buys, concretely
| property the bind carries | loop bind (k=7) | Klein-4 XOR bind |
|---|---|---|
| invertible / unbindable | ✅ (Moufang division) | ✅ (self-inverse) |
| **sequence / order** | ✅ 6/6 | ❌ 1/6 |
| **tree / nesting** | ✅ 5/5 | ❌ 1/5 |
| **direction** | ✅ (−0.85) | ❌ (1.0) |

The loop bind is the bind that **adds order, tree, and direction to an HDC store without losing invertibility.** That is k=7 earning its place: it is the natural primitive for **sequence, hierarchy, and directionality** — exactly where the commutative XOR bind has always had to bolt on position-roles/permutations. Ties **R-RBS-LM-75** (order-invariance falsification — the loop bind is the order-*sensitive* resolution) and **F270 §C** (order-dependent 3-domain-expert routing — the experts compose non-commutatively).

### New Moufang-loop-bind paths — status (per user "follow all new paths")
- **DONE:** C (viability/unbind), A (order), B (tree/bracketing), D (direction).
- **QUEUED:** (i) capacity — how many bound pairs a loop-bind bundle holds vs a Klein-4 bundle (does non-associativity cost capacity?); (ii) the **G₂ calibration φ/\*φ as a 3|4 sector-router** (the geometric leg — route content by associative-3-plane vs coassociative-4-complement); (iii) drop the loop bind into a real **RBS-NN/LM cascade** (e.g. the F166 autoregressive loop) and measure whether order/tree retention improves emission; (iv) left-vs-right division as **two readout heads** (store with L, read with R).

### Status / discipline
FRAMEWORK + DEMONSTRATED (all four paths verified srmech-native; results reproducible via committed `loop_bind_paths_experiment.py`, seed attested-B). Baseline = srmech `klein4_bind` (commutative + associative + self-inverse). Class-K (cosine via inner products; no `abs()`/sign-fold). No-magic (6=3!, 5=Catalan C₃, the unbind identities are attested-to-structure A; the −0.85 is measured B). CAD-ban. Single-model / no-twin. The loop bind is the F272 helper (`loop_bind_moufang.py`), hand-rolled (srmech has the triality *symmetry* but not this *product* — F271 §C capability target). Builds on F271/F272/F273 (the loop bind, its DoF), F270 §C (order-dependent routing), R-RBS-LM-75 (order-invariance). Verified srmech v0.6.0rc20, `/tmp/srmech_rc20_venv`. `[[user_stance_cross_substrate_cascade_matching_as_research_method]]`.
