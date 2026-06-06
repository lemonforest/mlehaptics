# R-RBS-LM Finding 463 — **v4 canonical A-N IR**: the STRUCTURAL commensurability route (F455 Route-1), built and verified. v3 showed cross-LANGUAGE operator-signatures are orthogonal (F457) because the *concrete* syntax trees differ (for-of vs for-range vs for-each, decl-vs-assign, wrapper nodes). v4 normalizes every grammar into ONE shared canonical A-N operator **inventory** (one `I(loop)` for every loop form, one `A(assign)` for decl+assign, canonical `ALU/M/N` arithmetic). Result: the **same algorithm in 5 different languages becomes commensurate** — pairwise sim **+0.86** (vs v3's ~0), and the **F462 coupler coherence rises from the ~1.1 floor to 3.23×** (toward k=5). Cross-PARADIGM reps (the LaTeX declarative Σ, the natural-language word problem) stay **at the floor (−0.01)** — structure alone cannot bridge paradigms, so that is precisely where the **F458 semantic anchor (Route-2)** is required. The two commensurability routes are now both demonstrated.

**Date:** 2026-06-06
**Arc:** RBS-LM · the grammar-kernel capstone — v4 canonical IR (user direction 2026-06-06: "latex v3 then c and python … v4 canonical A-N IR"; the structural route F462 located as the missing piece)
**Provenance:** `R-RBS-LM-CANON_ir_v4_canonical_an_inventory.py` (committed; srmech 0.7.3rc1; sympy/ast/pycparser/tree-sitter; `hypercomplex_couple` per-dimension). Clean venv `/tmp/verify_srmech_073rc1_sci`.
**Composes:** **F462** (located the missing piece: k=7 binds, commensurability is the precondition — *v4 supplies the structural half*) · **F457** (the cross-grammar NULL — *v4 resolves it WITHIN a paradigm*) · **F458** (the word-problem semantic anchor — *the cross-PARADIGM half v4 cannot reach, confirmed empirically here*) · **F455** (the two routes encode/structural vs learn/semantic — *both now demonstrated*) · **F459** (the k coupler — *the binder v4 feeds*) · **F317/F426** (operator-signature addressing) · the v1/v2/v3 grammar engine (`R-RBS-LM-GRAMMAR_signature_engine_v3.py`, whose closing lines named this exact next rung). **← resolves the F462/F457 cross-language null via structural normalization; the cross-paradigm residue is handed to F458.**
**→ Route-1 (v4, structural) supplies commensurability WITHIN a paradigm; Route-2 (F458, semantic) across paradigms. The k coupler (F459) is the binder; v4 + F458 are its two commensurability feeds.**

## What was built
The v4 IR walks each grammar's parse tree and emits a **canonical A-N operator inventory** — a count of the framework's own primitive classes, *dropping* grammar-specific wrapper/leaf noise and *unifying* every loop form to `I(loop)`, every decl-or-assign to `A(assign)`, and every `+/−/*/÷/%` to the canonical `ALU(add)/ALU(sub)/M(product)/N(ratio)/I(mod)`. The inventory is encoded as a count-weighted bundle of canonical-class hypervectors. Adapters: Python `ast`, C `pycparser`, sympy LaTeX, and tree-sitter (JS/Go/Rust) with the binary operator read from the anonymous operator child's `.kind`.

The seven representations of **Σaᵢ** yield these canonical inventories:

| rep | canonical A-N inventory |
|---|---|
| Python | `A(assign)×2, ALU(add), DEF, I(loop), RET` |
| JavaScript | `A(assign)×2, ALU(add), DEF, I(loop), RET` |
| Rust | `A(assign)×2, ALU(add), DEF, I(loop), RET` |
| C | `A(assign)×3, ALU(add), DEF, I(loop), K(compare), RET` |
| Go | `A(assign)×3, ALU(add), DEF, I(loop), RET` |
| LaTeX Σ | `AGG` (declarative aggregate) |
| word problem | `{}` (natural language — no grammar tree) |

JS/Python/Rust are **identical**; C/Go differ only by the extra `A(assign)` from their explicit loop-counter / short-var declarations (and C's bound `K(compare)`). The LaTeX Σ is a single declarative `AGG`; the word problem has *no* parse tree at all.

## Results
**[1] cross-LANGUAGE commensurability (the v4 win):** pairwise sim over the 5 imperative loop-sums = **+0.86 mean** (min +0.75, max +1.00; JS=Python=Rust = +1.00). v3's raw cross-grammar signatures were ~0 (the F457 null). The canonical IR makes the same algorithm in different languages *the same object*.

**[2] cross-PARADIGM (the honest boundary):** LaTeX Σ vs the imperative cluster = **−0.012**; word problem vs the cluster = **−0.007**. Structure alone cannot bridge an imperative loop to a declarative aggregate or to natural language — they live in different paradigms. This is **exactly** the F458 frontier: the semantic anchor (Route-2) is the only bridge across paradigms.

**[3] F462 coupler RE-RUN on v4 signatures (the decisive fusion):**
| condition | per-dim coupler coherence | vs |
|---|---|---|
| MATCHED cross-language (5 imperative, v4 canonical) | **3.23** | F462 raw floor ~1.1 → **lifted toward k=5** |
| MISMATCHED (5 different algorithms) | 2.04 | the shared `DEF/RET` function-scaffold floor |
| (F462 raw cross-grammar, no v4) | ~1.12 | the F457 null |

v4 nearly **triples** the cross-language coupler coherence (1.1 → 3.23) by supplying the commensurability the k binder (F459) needs — confirming v4 IS the structural commensurality layer F462 located.

## Falsifiable form (pre-stated; not leaning — F394)
- **The win is real and bounded:** cross-language same-algorithm coherence rises 1.1 → 3.23 (mean sim +0.86) — *not* to a perfect 5.0, because the canonical inventories are *near*-identical, not identical (C/Go carry one extra `A(assign)`); 3.23/5 ≈ 0.65 tracks the +0.86 alignment honestly.
- **MISMATCHED sits at 2.04, not 1.0 — and that is honest, not a flaw:** the canonical IR gives *every* function a shared `DEF/RET` scaffold (it really is true that all five are functions that return), so different algorithms are not maximally independent; the discrimination lives in the body (`I(loop)+ALU(add)` for a sum vs `C(branch)+M(apply)+M(product)` for a recursion). Matched (3.23) > mismatched (2.04) > F457 floor (1.1).
- **The inventory is a MULTISET, not a tree** — v4 deliberately discards tree *shape* (the grammar-specific noise that caused F457). It distinguishes loop-sum from loop-product (add vs product) and from recursion (loop vs branch+apply), but it does NOT distinguish two programs with the same operator inventory and different wiring. A canonical-*tree* IR (normalized shape) is the sharper, harder follow-up — flagged, not built.
- **Cross-paradigm is a true NULL, by design** — LaTeX/NL at −0.01 is the honest demonstration that Route-1 has a boundary; F458 (Route-2) owns the cross-paradigm bridge. The two routes are complementary, not redundant.
- **Scope:** algebra/HDC/grammar/eigenbasis side; defensive / no-lineage; srmech 0.7.3rc1; no CAD; no Workflow tool (inline run).

## Verdict
**v4 canonical A-N IR is built and it works as the structural commensurability route.** Normalizing every grammar into one shared canonical operator inventory makes the *same algorithm in five different languages* commensurate (+0.86 sim vs ~0 raw), and feeding those v4 signatures into the F462/F459 coupler **lifts cross-language coherence from the ~1.1 floor to 3.23×** — the canonical IR supplies the commensurability the k binder needs. Its boundary is honest and exactly where the framework predicted: **cross-paradigm** reps (declarative LaTeX Σ, natural-language word problem) stay at the floor (−0.01), so the **F458 semantic anchor (Route-2)** is the only bridge there. The grammar-kernel arc now closes with both commensurability routes demonstrated: **Route-1 (v4, structural) within a paradigm, Route-2 (F458, semantic) across paradigms — the k coupler (F459) the binder over both.** Favored, not privileged (F398); the win is bounded and stated as such; the canonical-tree IR and the F458 anchor build are the flagged next rungs.
