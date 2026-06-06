# R-RBS-LM Finding 457 — the unified **grammar-signature engine** (v3): ONE grammar-agnostic operator-signature core + a pluggable adapter per closed grammar reads **nine closed grammars training-data-free** — math (sympy), Python (ast), C (pycparser), LOGO (hand-parser), and the **still-used languages** JavaScript / Go / Rust / Java / TypeScript (tree-sitter). **WITHIN each grammar: perfect symbol/rename/shape-invariance (+1.000 for all nine).** **CROSS-language** (same loop-sum in JS/Go/Rust/Java): **~0.000** — comparable *within* a grammar but **not across** without a shared **canonical normalization** (Go-`for-range` = JS-`for-of` = Java-`for-each` → one `I(loop)`); that's the next rung (a canonical A-N IR every adapter normalizes *into*), not a failure. Realizes F455 (encode the closed grammar) + F456 (programming languages) as one engine; LOGO recognized as an early instance

**Date:** 2026-06-06
**Arc:** RBS-LM · the unified encode-the-grammar engine (user direction 2026-06-06: "latex v3 then c and python and we already did logo" + "a programming language kernel for still-used languages now as well")
**Provenance:** `R-RBS-LM-GRAMMAR_signature_engine_v3.py` (committed; srmech 0.7.1 + sympy/lark, stdlib `ast`, pycparser, `tree_sitter_language_pack`; NO corpus, NO model, NO training).
**Composes:** **F455** (the two routes; F408 discriminator; closed grammar → ENCODE — *this is the universal encoder*) · **F456** (the Python code-aware kernel — *generalized to an engine + adapters*) · **F452/F454** (the v1/v2 operator-signature — *now the grammar-agnostic core*) · **F406** (operator/operand/grammar — the closed grammars) · **F317/F426** (operator-signature addressing) · **F445** (cross-domain invariant — *the cross-language null + the normalization next-rung*) · chess-spectral (the encode-the-rules route) · the **logo-maths** arc (LOGO — the early instance the user recalled) · **F398**. **← extends F455, F456.**
**→ one engine encodes any closed grammar (math + 4 programming languages + LOGO + Python/C) training-data-free; per-still-used-language kernels work; cross-language matching needs a canonical A-N IR (next).**

## The engine
```
operator_signature(root, node_class, children):
    sig(n) = bind( mint("OP:"+node_class(n)),  bundle( permute(sig(child_i), i) ) )   # leaves symbol-free
```
Grammar-agnostic: feed it a parse tree + a `node_class(n)->str` adapter + a `children(n)->list` adapter. **The same 6-line core** handles every grammar; only the adapter changes. Adapters built + verified:
- **math** — sympy `parse_latex` (Lark) tree; sympy node → A-N (F454).
- **Python** — stdlib `ast` (zero deps); ast node → A-N (F456).
- **C** — `pycparser` AST; c_ast node → A-N.
- **LOGO** — a ~30-line hand-parser (`REPEAT n [...]`, `TO…END`, `FD/RT`); turn → C(chirality), repeat → I(loop).
- **still-used languages** — `tree_sitter_language_pack` (one library, grammars for ~all current languages); generic `node.kind` → A-N. JS / Go / Rust / Java / TypeScript verified.

## Results
| grammar | within-grammar invariance | note |
|---|---|---|
| math (sympy) | **+1.000** | `\frac{a}{b}` ≡ `\frac{m}{n}` |
| Python (ast) | **+1.000** | rename-invariant |
| C (pycparser) | **+1.000** | rename-invariant |
| LOGO (hand) | **+1.000** | shape-invariant (`REPEAT 4` ≡ `REPEAT 360` — count is symbol-free) |
| JavaScript / Go / Rust / Java / TypeScript (tree-sitter) | **+1.000 each** | rename-invariant — *a kernel per still-used language* |
| **cross-language** (loop-sum: JS/Go/Rust/Java) | **~0.000** (−0.02..+0.01) | NULL with the coarse generic map — see below |

## The cross-language null (the honest, load-bearing part)
The operator-signature is **comparable within a grammar but not across** without normalization. Each language's *concrete* syntax tree (CST from tree-sitter) has **language-specific node kinds + nesting** — Go's `for_range_clause`, JS's `for_in_statement`/`for_of`, Java's `enhanced_for_statement`, Rust's `for_expression` — so the *same algorithm* produces *different trees*, hence orthogonal signatures. **Cross-language (and cross-grammar) matching requires a shared CANONICAL A-N intermediate representation** that every adapter normalizes *into* (every for-each-flavour → one `I(loop)`; every binary `+` → one `ALU(add)`), so a Go loop-sum, a JS loop-sum, and a math `∑` all land on the same canonical operator-tree. **That is the next rung ("v4 — canonical A-N IR"), and it is exactly where the F445 cross-domain invariant becomes operational for code.** Not a failure — a precisely-located next step.

## Falsifiable form (pre-stated; not leaning — F394)
- **WITHIN-grammar invariance is proven (+1.0 × 9); CROSS-grammar/language matching is NOT yet achieved** (null) — it needs the canonical-IR normalization layer. Do not over-read the 9× +1.0 as cross-language matching; it is per-grammar.
- **The node→A-N maps are readings (F398),** per-grammar; the tree-sitter generic map is *coarse* (by `node.kind` keyword) — deliberately, since cross-language alignment is deferred to the canonical IR, not the coarse map.
- **"Still-used languages" demonstrated on 5** (JS/Go/Rust/Java/TS) via one library; tree-sitter has grammars for ~all current languages, so coverage is a config list, not new engineering — flagged (not all run).
- **GRAMMAR layer only** (F455/F456): this encodes code/notation STRUCTURE; SEMANTICS ("what it computes," the stories) stays Route-2/learn (F408).
- **Scope:** algebra/grammar/eigenbasis side; defensive / no-lineage; stdlib + standard parsers + standard HDC; no CAD; no Workflow tool; **no training data** (the point).

## Verdict
**One grammar-agnostic engine encodes nine closed grammars training-data-free** — math, Python, C, LOGO, and the still-used languages JS/Go/Rust/Java/TS — with **perfect within-grammar symbol/rename/shape-invariance (+1.0 across all nine)**. A **kernel per still-used language works** (parser swap only, no corpus), realizing F455 (encode the closed grammar) + F456 (programming languages) as a single `operator_signature` core + per-grammar adapters; LOGO is recognized as the early instance (with chess). The **cross-language null (~0)** precisely locates the next rung: a **canonical A-N intermediate representation** all adapters normalize into, so the same algorithm aligns across languages and the F445 cross-domain invariant becomes operational for code. Favored, not privileged (F398); within-grammar proven, cross-grammar needs the canonical IR, semantics stays Route-2.
