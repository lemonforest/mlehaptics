# F1210 — Our genome kernels are FLAT BAGS: the responsion/curvature is provably absent and needs a DIRECTED re-encode; store the ONE directed (magnetic) object → metric + curvature both read out

**User (2026-07-13), on the F1209 follow-up "let's do both":** *"pretty sure … we're going to need to re-encode all genome kernels if edges ended up bags. I'm not sure we'll get anything better than approx curvature from flattened but it's still worth looking at."* Measured — and the instinct is right, and stronger than "approx": the flattened bag carries **exactly zero** curvature. Confirmation script: `R-RBS-LM-CURVATURE_PROBE_frame_vs_curvature_and_genome_order_holonomy.py` (srmech 0.9.0rc238).

## PART A — the operator ops are exactly the field/excitation/curvature split (rc236/rc237)
`separate_frame_curvature(A,B)` → fixed_frame `½{A,B}` (metric) ⊕ curvature `½[A,B]` (responsion). Commuting pair → curvature **0.000** (flat); non-commuting → curvature **0.707** (curved). `separate_winding_curvature(the_one S(σ,θ,w))`: w=(0,0,0) `is_flat=True` holonomy 0; w=(1,0,0) `is_flat=False` holonomy 1 and **spinor_sign flips +1→−1** (the double-cover/odd channel), while the adjoint fixed frame is **byte-identical across windings** (the metric is provably w-blind). The op's own docstring cites *"op / operand / responsion ≅ field / excitation / CURVATURE"* + user directive #834.

## PART B — the stored simplewiki kernel is a symmetric bag with zero curvature
Real kernel: **831,139 vocab, 39,048,148 edges**.
- **B0 (symmetric bag confirmed):** 0 non-canonical edges (a>b), 0 reverse-duplicates. `build_edges_topk` line `a,b=sorted((i,j))` folds "a-before-b" and "b-before-a" into one summed weight. **Order is gone at persist.** Every kernel through this path is flat.
- **B1 (metric read is flat):** a real triangle with no directed charge → `cycle_holonomy` holonomy `0`, `balanced=True`.
- **B2 (bag curvature is EXACTLY zero, not approx — a proof):** the only antisymmetric edge-charge a symmetric graph can synthesize is a **node-potential difference** (degree/IDF/freq): `q(u→v)=φ(v)−φ(u)`. Around any closed loop this **telescopes to 0** (a gradient is curl-free). Measured: max |loop-sum| over 1500 triangles = **0.000e+00**. The bag cannot even *approximate* the fiber — it destroyed it.

## PART B3 — the DIRECTED re-encode recovers real order-curvature (1500 well-observed triangles, ≥10 directed obs/edge)
Re-streamed 120,000 simplewiki articles keeping `dir[u,v] ≠ dir[v,u]`; per-edge asymmetry `(f−r)/(f+r) ∈ [−1,1]`:

| measure | value |
|---|---|
| mean \|loop-holonomy\| | **0.526** |
| mean per-edge \|asym\| | 0.323 |
| rotational-ratio (loop / max-possible) | **0.543** |
| coherence-flat loops (\|loop\|<0.1, F1146) | 12.2% |

**mean |loop| (0.526) > mean |edge| (0.323)** is the clincher: a gradient telescopes to loop ≡ 0, so if word-order were a global potential/ranking the loops would vanish; instead the circulation is *larger than* a single edge — the field is **rotational / non-gradient**, i.e. genuine holonomy. Example `aaron→actor→actress`: asym `(+0.12,+0.06,+0.82)` sums to **exactly +1.00** → `cycle_holonomy` mod-1 ≈ 0, `balanced` — a live F1146 coherence-flattening (strong local order netting to one coherent turn). The symmetric bag has **0** of any of this.

## Verdict + architecture (the re-encode is mandatory for the responsion read — and it's a SUPERSET, not a second object)
Word order carries substantial genuine curvature (≈54% rotational; loop > edge ⇒ non-gradient), and the flattened kernel captures **none** of it (metric-only). To read op/operand/**responsion** at all, kernels must keep **directed** edges. **Do NOT store a second object** — store the ONE directed (magnetic) Laplacian per F1207's "one Class-L object → many read-outs":
- **metric / field** = the Hermitian/symmetric part = `w_fwd + w_bwd` (exactly today's symmetric weight — a free read-out, nothing lost);
- **curvature / responsion** = the antisymmetric part = `w_fwd − w_bwd` = the per-edge charge for `magnetic_laplacian(charges=…)` → `cycle_holonomy`.
The current symmetric kernels are a **derivable subset** of the directed one (sum the two columns). So the re-encode is a one-time cost that never needs redoing, and it *supersets* all existing symmetric work. Encoder change is small: keep the ordered pair instead of `sorted((i,j))`, accumulate two weight columns; the forward window already carries the direction. Update the recover-ratchet to also assert curvature-recoverability (a nonzero holonomy survives on a directed triangle).

**Storage:** ~2× the `edge_weights` array (two columns per pair; `edge_list` pairs unchanged), well within the disk↔RAM external-merge architecture (F1208). This is the F1207 sparse-and-complete discipline applied to the *directional* axis: the symmetric fold was a truncation of the odd/curvature half, exactly as top-16 was a truncation of the weight half.

Composes **F1209** (curvature = the responsion = the F401 fiber; k=2 flat / k≥3 curved), **F1207** (one Class-L object → many read-outs; never truncate at storage), **F1208** (hold it all disk↔RAM), **F552** (the odd channel the Hermitian spectrum can't carry), **F1146** (coherence flattens; the aaron→actor→actress net-1-turn loop), the **never-bag-of-words** discipline (order = the octonion coupling-walk, not a symmetric bundle — now *measured*: 54% of order is irreducibly rotational). Bears on TRIALITY.md §1 / F400/F401 (the fiber, measured on a real corpus).
