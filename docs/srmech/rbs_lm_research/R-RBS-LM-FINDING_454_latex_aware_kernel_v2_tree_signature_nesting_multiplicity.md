# R-RBS-LM Finding 454 — the LaTeX-aware kernel **v2** (real sympy parse-**tree** → recursive A-N operator-signature) strictly dominates v1: it adds **NESTING** sensitivity (∑-inside-ratio vs ratio-inside-∑ — same operator *set*, so v1 conflates at +1.0; v2 **separates at +0.003**) and **MULTIPLICITY/arity** sensitivity (`x+y` vs `x+y+z` — v1 +1.0, v2 **+0.51**), while keeping **symbol-invariance** (+1.0) and *sharpening* structure-clustering (within +0.70 ≫ cross +0.003). The signature is `sig(node) = bind(OP-class(node), bundle(permute(sig(childᵢ), i)))` with symbol-free leaves — the **grammar** alphabet of F406 realized: math addressed by its operator **tree**, not its operator **bag**

**Date:** 2026-06-06
**Arc:** RBS-LM · LaTeX-aware kernel research path, v1 (F452) → **v2** (user direction: "follow latex aware kernel research paths" → "v2: sympy parse-tree, nesting/multiplicity-aware")
**Provenance:** `R-RBS-LM-LATEX_aware_kernel_v2.py` (committed; srmech 0.7.1 + sympy 1.14 Lark backend, antlr-free). srmech-native: `mint_vector` (A) + `bind`/`bundle`/`permute`/`similarity` (M).
**Composes:** **F452** (v1 presence-set — *this extends it, fixing the conflation it flagged*) · **F406** (the three alphabets: operator/operand/**GRAMMAR** — the parse-tree IS the grammar) · **F317/F426** (operator-signature addressing — index by the structural invariant) · **F445** (the cross-domain invariant) · **F75** (order/structure sensitivity — v2 adds the structural axis v1's bag lacked) · the unsolved-maths arc (14 A-N applied to math) · **F398**. **← extends F452.**
**→ math expressions get a nesting+multiplicity-aware, symbol-free operator-signature address — the structure-kernel that distinguishes what the bag-kernel conflates.**

## What v2 does (vs v1)
v1 (F452) was a **presence-set** signature — *which* operators are present, symbol- and count-free. It proved symbol-invariance + structure-clustering but **conflated nesting and multiplicity** (two expressions with the same operator *set* got the same signature). v2 parses the expression into a **real sympy tree** (`parse_latex`, Lark backend — antlr-free) and builds a **recursive** signature:

```
sig(node) = bind( mint("OP:" + Aclass(node)),  bundle( permute(sig(childᵢ), (i+1)·stride) ) )
leaf (Symbol/Number) → mint("LEAF:OPERAND" | "LEAF:CONST")     # symbol-free
```

Each node binds its **A-N operator class** to the **position-permuted bundle of its children's signatures** — so nesting (operator-of-operator) and child arity/multiplicity both enter the signature; symbols never do (leaves are generic). **sympy node → A-N map** (a reading, F398): `Add→ALU(add)` · `Mul→M(product)` (or **N(ratio)** if it has a negative-exponent `Pow` factor — sympy renders `a/b` as `Mul(a, Pow(b,-1))`) · `Pow→Jpow(power)` / **N(root)** (exp ½) / N(recip) (exp<0) · `Sum/Integral/Product→M(aggregate)` · `Derivative→K(diff)` · `Symbol→OPERAND` · `Number→CONST`.

## Results
| test | result | reading |
|---|---|---|
| **[1] symbol-invariance** `\frac{a}{b}` vs `\frac{m}{n}` | **+1.0000** | same tree, symbol-free leaves — retained from v1 |
| **[2] NESTING** `\frac{\sum a_i}{x}` vs `\sum \frac{a_i}{x}` | v1 **+1.0** (conflates) → **v2 +0.003** | same operator *set* {ratio, aggregate, recip, group}; v2 separates by root/nesting (Mul-root vs Sum-root) — **the headline v2 win** |
| **[3] MULTIPLICITY/arity** `x+y` vs `x+y+z` | v1 **+1.0** (conflates) → **v2 +0.51** | Add/2 vs Add/3 — v2 separates by arity, v1 cannot |
| **[4] cross-domain ratio** `\frac{a}{b}` vs `\frac{f+1}{g}` | **+0.26** | shared `N(ratio)` root, different subtree (one has a nested Add) — proportional |
| **[5] derivative** `df/dx` vs `dg/dy` (constructed `Derivative`) | **+0.50** | same `K(diff)` structure, symbol-free |
| **[6] structure-clustering** (ratio/sum/power groups) | within **+0.70** ≫ cross **+0.003** (sep **+0.70**) | sharper than v1's +0.64 |

## Falsifiable form (pre-stated; not leaning — F394)
- **v2 strictly adds structure v1 lacked** (nesting + multiplicity), demonstrated by the same-pair v1-vs-v2 comparison ([2],[3]): where v1 = +1.0 (blind), v2 separates. It does **not** discard v1's wins (symbol-invariance, clustering both retained/improved).
- **Parser-grammar gaps are real and bounded:** sympy's Lark backend does **not** parse `\partial` (used a constructed `sympy.Derivative` for [5]) and requires explicit `\sum` limits (`\sum_{k=1}^{m}`, not bare `\sum_{k}`) — unparseable expressions are **skip-guarded + logged**, not silently dropped. A fuller parser (antlr backend with pinned runtime, or a custom grammar) is the v3 lever.
- **The sympy-node → A-N map is a READING (F398),** not a theorem (e.g. `Sum`/`Integral`→M(aggregate), `Derivative`→K(diff) are framework interpretations; sympy's normalization — `\frac`→`Mul(·,Pow(-1))`, `\sqrt`→`Pow(·,½)` — is what's detected). The *demonstrated* claim is the structural one: a symbol-free **tree** signature distinguishes nesting/multiplicity and clusters by structure.
- **Scope:** algebra/notation/grammar/eigenbasis side; defensive / no-lineage; standard sympy + standard HDC; no CAD; no Workflow tool (inline run, parse-gaps skip-guarded).

## Verdict
**v2 of the LaTeX-aware kernel works and strictly dominates v1.** Parsing math into a real **sympy tree** and binding a **recursive operator-signature** (`bind(class, bundle(permuted child-sigs))`, symbol-free leaves) adds the two axes v1's presence-set conflated — **nesting** (∑-in-ratio vs ratio-in-∑: v1 +1.0 → v2 +0.003) and **multiplicity/arity** (`x+y` vs `x+y+z`: v1 +1.0 → v2 +0.51) — while keeping symbol-invariance (+1.0) and sharpening structure-clustering (within +0.70 ≫ cross +0.003). This realizes the **grammar** alphabet of F406 (the parse-tree *is* the grammar) and gives equations a nesting-aware operator-signature address (F317/F426) — the structure-kernel that tells apart what the bag-kernel could not. Honest fences: Lark grammar gaps (skip-guarded), the node→A-N map is a reading (F398), v3 = fuller parser. Favored, not privileged.
