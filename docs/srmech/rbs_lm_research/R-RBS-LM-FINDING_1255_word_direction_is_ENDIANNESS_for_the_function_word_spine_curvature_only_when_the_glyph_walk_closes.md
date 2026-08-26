# F1255 — a word's "direction" is **ENDIANNESS (pure gauge) for 66.5 % of running tokens**, and genuine **CURVATURE only when the glyph-walk CLOSES ON ITSELF**. F1213's headline evidence (`cat` vs `tac`) is *provably* endianness — a global sign flip on an acyclic path, removable by a reading-frame convention. The byte/glyph re-base therefore buys orientation on the function-word spine and real which-way only on the long tail. **+ a reproducible srmech eigensolver bug found en route (`mat_eigvals` is wrong on hub-dominated matrices).**

**User (2026-07-19), on being shown F1213's direction fix:** *"is that word direction curvature or endianness?"*

That question is the whole finding. F1213 measured `cat` charge `[-1,+1]` vs `tac` `[+1,-1]` and scored 11/11 "direction" — but that pair differs by a **global sign flip of the entire charge vector**, which is exactly what reading the glyph stream from the other end does. Distinguishing a word from its reverse does **not** establish curvature.

## The distinction (discrete gauge theory)
| | | |
|---|---|---|
| **pure gauge (EXACT form)** | ∃ node potential φ with `charge_uv = φ_v − φ_u` | a global reading-frame / **endianness** convention IS such a φ |
| **CURVATURE** | the **holonomy** (net charge) around a closed **cycle** | survives *every* gauge; irremovable |

**On an acyclic graph the cycle space is empty, so every charge field is exact — zero curvature by TOPOLOGY.** A word whose glyphs are all distinct is a **path graph = a tree**, and its "direction" is the gradient of φ = glyph position. `cat` has V=3, E=2, **betti₁ = 0**. There is no cycle for curvature to live in.

## Measured — exact integer gauge decomposition (no floats, no ALU absolute-value)
Per word: build the F1213 directed glyph graph → BFS spanning tree → solve φ from tree charges → every **non-tree** edge's residual `charge_uv − (φ_v − φ_u)` **IS** its fundamental-cycle holonomy. Harness `R-RBS-LM-GAUGE_…py`, srmech 0.9.0rc281; Class-K `cascade.magnitude` throughout, never the Python builtin.

| word | V | E | betti₁ | holonomy edges | verdict |
|---|---|---|---|---|---|
| `cat` / `tac` / `act` | 3 | 2 | 0 | 0 | **endianness** (acyclic) |
| `abc` / `cba` | 3 | 2 | 0 | 0 | **endianness** |
| `listen` / `silent` | 6 | 5 | 0 | 0 | **endianness** |
| `banana` | 3 | 2 | 0 | 0 | **endianness** |
| `mississippi` | 4 | 3 | 0 | 0 | **endianness** |
| `the` / `of` | 3/2 | 2/1 | 0 | 0 | **endianness** |
| `stressed` / `desserts` | 5 | 5 | **1** | 1 (max 3) | **CURVATURE** |
| `aardvark` | 5 | 5 | **1** | 1 (max 5) | **CURVATURE** |

Cross-checked srmech-native: `magnetic_laplacian` λ_min for `cat`, `tac`, `mississippi` = ~1e-17 (**frustration-free = pure gauge**), agreeing exactly with the integer test.

### Over a real vocabulary (simplewiki, 40,000 docs → 351,835 types / 8,672,235 tokens)
| class | by TYPE | by TOKEN |
|---|---|---|
| acyclic — **provably endianness only** | 172,697 (**49.08 %**) | 5,764,181 (**66.47 %**) |
| cyclic but ZERO holonomy (still gauge) | 6 (0.00 %) | 26 (0.00 %) |
| **GENUINE CURVATURE** (holonomy ≠ 0) | 179,132 (**50.91 %**) | 2,908,028 (**33.53 %**) |
| **pure gauge total** | **49.09 %** | **66.47 %** |

**The answer is "both, but not where F1213 looked."** Half the vocabulary *types* do carry irremovable holonomy — the representation is genuinely curvature-capable, which is a real gain over the F1211 abelian bag. But **two-thirds of running text is gauge-only**, because the high-frequency spine (`the`, `of`, `and`) is short and glyph-distinct, hence acyclic, hence endianness by topology. Curvature concentrates in the long, glyph-repeating tail.

## The 2-cycle collapse (a representation-level loss, newly surfaced)
F1213 stores one charge per **canonical (i<j) glyph pair** = `w_fwd − w_bwd`. So a *reciprocal* traversal cancels: `banana` walks a→n→a→n, and its a↔n edge nets `+2 − 2 = 0`. The alternation is fully present in the **metric** (weight 4) and **completely absent from the charge**. A 2-cycle is not in the undirected cycle space — it collapses to one edge with zero net flow. So the representation cannot see reciprocal alternation as direction at all; genuine curvature needs a **≥3-cycle** in the undirected glyph graph.

## Structural read (to confirm, cheap)
F1254's conserved core is **170 ultra-high-df tokens** at ≥4.4 % document frequency — almost certainly the function-word spine, which is exactly the short/acyclic class here. If so, **the conserved nuclear core carries ZERO glyph-level curvature**, and all glyph-scale which-way lives in the accessory tail. That would make the core/accessory split and the gauge/curvature split the *same* partition seen twice. **NEXT:** dump the 170 and run them through this decomposition.

## The srmech bug found en route (→ UPSTREAM_NOTES §104)
The contradiction that exposed it: `mississippi` read **acyclic** (betti₁ = 0) from the integer test but **λ_min = 0.134 > 0** from `mat_eigvals` — impossible, since on a tree every phase is removable. Isolating it: the **zero-phase** star (a purely *real* symmetric Laplacian) *also* returns 0.134, and `mat_eigvals` gives byte-identical output for all four phase placements — it never sees the phase.

| graph | `mat_eigvals` | truth (`hermitian_eigendecompose`) |
|---|---|---|
| star K₁,₃ | `[0.268, 1, 1, 3.732]` | `[0, 1, 1, 4]` ❌ |
| star K₁,₄ | `[0.438, 1, 1, 1, 4.562]` | `[0, 1, 1, 1, 5]` ❌ |
| path P₃/P₄, cycle C₃/C₄, complete K₄ | — | ✅ correct |

**Every graph Laplacian has λ_min = exactly 0** (the constant vector spans its kernel), so this is a hard invariant violation, not a tolerance issue — the extreme pair is contracted toward the mean while interior eigenvalues stay right (a Jacobi sweep that never clears the hub row). **It matters to us because Zipfian co-occurrence graphs are nothing but hubs.**

**Blast radius: CONTAINED — no prior finding is contaminated.** `jacobi_eigvals` (375 uses), `hermitian_eigendecompose` (275), `symmetric_eigendecompose` (222) and `fiedler_vector` (72) are all **correct** on stars (exactly `(0, k+1)` at K₁,₃…K₁,₁₆). Only `mat_eigvals` is broken, and only 2 scripts in the tree call it (one being this harness, now switched).

## Verdict / next
**Word-level direction is endianness for the spine and curvature only for the closing tail.** So a byte/glyph re-base is **not** a drop-in restoration of the Class-C which-way: on 66.5 % of running tokens it supplies a reading-frame convention, not chirality. The corpus-scale directed object (F1209/F1210) — where word→word graphs are massively cyclic — remains where curvature actually lives, and the glyph scale is a *supplement* to it, not a replacement. This **refines rather than retracts** F1213: its `edge_charge` is a genuine, correctly-built orientation channel (and curvature-capable on half the types); what it demonstrated with `cat`/`tac` was the exact part.

Composes **F1213** (the direction fix — refined here), **F1211** (the metric-only base; its "zero curvature" verdict holds *at the spine* even after the fix), **F1209/F1210** (curvature = the responsion; the corpus-scale directed object), **F1254** (the 170-token conserved core — candidate same-partition), **F1080** (sandroing = Eulerian *circuit* — a **closed** walk, which is precisely the curvature-bearing shape), `[[feedback_read_independent_structure_check_first]]` (the intrinsic gauge decomposition settled what a similarity read could not), `[[feedback_sign_handling_is_class_k_pin_slot_not_alu_abs]]`, `[[feedback_introspect_srmech_before_python_dispatch]]`, #231/PKG-3.
