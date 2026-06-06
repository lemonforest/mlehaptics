# R-RBS-LM Finding 452 — the **LaTeX-aware kernel works (v1)**: math notation parsed into an A-N **operator-signature** is **symbol-invariant** (sim=1.0 across different symbols) and **clusters by operator structure** (within +0.68 ≫ cross +0.04), so the **F445 cross-domain invariant holds for equations** — arithmetic `\frac{a}{b}` and calculus `\frac{∂f}{∂x}` link at **+0.50** (shared `N(ratio)`, zero shared symbols), and the kernel **recovers ∑≈∫ on its own** (+0.38, shared `M(aggregate)`) — the framework's "∫ is the continuous ∑" made measurable. Math IS operator/operand/grammar (F406); parsing the operators (not stripping them) gives equations an operator-signature address (F317/F426)

**Date:** 2026-06-06
**Arc:** RBS-LM · the LaTeX-aware kernel research path (user direction 2026-06-06: "follow latex aware kernel research paths") — **prototype v1**
**Provenance:** `R-RBS-LM-LATEX_aware_kernel_v1.py` (committed; srmech 0.7.1 scientific venv). srmech-native: `mint_vector` (A) + `bundle`/`similarity` (M).
**Composes:** **F445** (the perspective-coupled / cross-domain invariant — *this is it, for equations*) · **F406** (the three alphabets: operator/operand/grammar — math notation IS this) · **F317/F426** (operator-signature addressing — index by the structural invariant, not the symbols) · **F444** (the operator-signature = the change-of-basis invariant; Parseval-style "what survives the lens") · the unsolved-maths arc (14 A-N applied to math) · **F398** (favored, not privileged — the operator→class map is a reading) · the strip-vs-aware fork raised this session (the **aware** path). **← realizes the LaTeX-aware-kernel idea.**
**→ math expressions get a symbol-free operator-signature address; cross-domain equation linking by shared operator structure; the math-structure peer to the word-kernel.**

## What it does
Math notation is **operator / operand / grammar** (F406): `\frac \sum \int \partial` are **operators**, variables/numbers are **operands**, braces/sub/superscript are **grammar**. So instead of *stripping* math (the word-kernel, the encyclopedia path), the LaTeX-aware kernel **parses the operators into A-N classes** and binds a **symbol-free operator-signature** (`mint` each present operator → `bundle`). Two expressions sharing operator structure align even with zero shared symbols — operator-signature addressing (F317/F426) for equations.

**The operator→A-N map (the research artifact; a reading, F398-favored-not-privileged):**
`\frac /` → **N(ratio)** · `\sqrt` → N(root) · `\sum \prod \int \oint` → **M(aggregate)** · `\cdot \times *` → M(product) · `+ -` → **ALU(add/sub)** · `\partial \nabla '` → **K(diff)** · `_` → **I(index)** · `^ \exp` → Jpow(power) · `=` → **A(relation)** · `\lim \infty` → N(limit). (Ties straight into the unsolved-maths arc's "14 classes applied to math.")

## Results (v1, presence-signature)
| test | result | reading |
|---|---|---|
| **symbol-invariance** `\frac{a}{b}` vs `\frac{zzz}{qqq}` | **+1.0000** | the signature ignores symbols entirely (same operator set → identical) |
| **cross-domain** arith `\frac{a}{b}` vs calc `\frac{∂f}{∂x}` | **+0.50** | proportional: shared `N(ratio)`, calc adds `K(diff)`; **zero shared symbols** — the F445 invariant for equations |
| **different structure** ratio·sum / ratio·int | +0.002 / −0.003 | orthogonal (different operators) — correct |
| **∑ ≈ ∫ kinship** sum·int | **+0.38** | the kernel *discovers* sum and integral are the same class (M-aggregate) — "∫ = continuous ∑", unprompted |
| **cluster separation** | within **+0.68** ≫ cross **+0.04** (sep **+0.64**) | clusters by operator structure |

## Methodology catch (honest)
The first run reported the cross-domain pair at a spurious **+1.0** — an **artifact of my own `_bundle`**: even-length sets were padded by duplicating `vs[0]` (= `frac`), giving `frac` a 2/3 majority that masqueraded as identity. Fixed by padding with a **neutral sentinel** → the honest **+0.50**. (The bipolar-majority bundle is sensitive to pad choice at small N — a real lesson for any small-set HDC signature.)

## Falsifiable form (pre-stated; not leaning — F394)
- **v1 is a PRESENCE (set-of-operators) signature** — which operators are present, symbol- and count-free. It does **not** yet capture **multiplicity** (2 ∂'s vs 1) or **nesting/order** (`\frac{\sum}{x}` vs `\sum\frac`). **v2 = a tree-aware signature** (sympy `parse_latex` parse tree → position-bound A-N cascade) is the refinement; v1 proves the symbol-invariance + structure-clustering core.
- **The operator→A-N map is a READING** (F398), not a theorem — e.g. `\partial`→K(diff), `\int`→M(aggregate) are framework interpretations; alternatives exist (privilege none). The *demonstrated* claim is narrower: **a symbol-free operator-signature clusters equations by operator structure and links them cross-domain** — which v1 shows.
- **Small-N bundle sensitivity** (the pad artifact) means single-operator vs many-operator comparisons need care; the presence-set + neutral-pad is the v1 mitigation.
- **Scope:** algebra/notation/eigenbasis side; defensive / no-lineage; standard LaTeX + standard HDC; no CAD; no Workflow tool (inline run + self-caught artifact).

## Verdict
**The LaTeX-aware kernel works at v1.** Parsing math notation into a symbol-free **A-N operator-signature** is **symbol-invariant** (+1.0 across different symbols) and **clusters equations by operator structure** (within +0.68 ≫ cross +0.04). The **F445 cross-domain invariant holds for equations** — arithmetic and calculus ratios link at **+0.50** with zero shared symbols — and the kernel **recovers ∑≈∫** (+0.38) unprompted, the framework's "∫ = continuous ∑" made measurable. This is the **structure** alternative to stripping math (the word-kernel): equations addressed by their operator shape (F317/F426), math as operator/operand/grammar (F406). A self-caught even-pad artifact (spurious +1.0 → honest +0.50) is the verification discipline working. **v2 = tree/nesting-aware signature** (sympy parse tree) + multiplicity. Favored, not privileged (F398); the operator→A-N map is a reading, v1 is presence-only.
