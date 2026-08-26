# F795 — a rule kernel must SELF-ENCODE the closed grammar (our own tokenizer + parser), NOT import the language's interpreter: the CODE kernel's `ast` and the LaTeX kernel's `sympy` were shortcuts that violate the chess/LOGO thesis and break edge/PAL portability. Dep-free Python rule kernel built — same rename-invariance + structure-clustering, zero deps.

**Date:** 2026-06-16 · **srmech:** 0.7.5rc166 · **Composes / corrects:** the chess + LOGO spectral kernels (the exemplars — `docs/logo-maths/logo_parser.py` is hand-written), F455 (a programming language is a CLOSED FINITE GRAMMAR → encode it, no training), F793 (edge/PAL portability — a dep-free grammar runs anywhere), `[[user_stance_learning_without_gpu_compute]]` (encode, don't borrow a runtime) · **User correction (2026-06-16):** "why do rule kernels have dependencies? our LOGO spectral notebook didn't need some other interpreter dep — we built it." · **Provenance:** `R-RBS-LM-CODEKERNEL_dep_free_self_encoded_python_grammar_logo_route.py`.

## The error the user caught
The chess/LOGO route is: **encode the closed finite grammar ourselves** — no training data, **no external interpreter.** LOGO did this right (`logo_parser.py` + `logo_ast.py` — hand-written; the only import is numpy for the HDC). But the later kernels cut a corner:
- `R-RBS-LM-CODE_aware_kernel.py` → **`import ast`** (Python's *own* parser).
- `R-RBS-LM-LATEX_aware_kernel_v2.py` → **`from sympy.parsing.latex import parse_latex`** (a heavy external lib).

That dependency was **never necessary** — and it's a real violation, not just inelegant:
1. **It contradicts the thesis.** "We encode the grammar (no training, no external interpreter)" — then importing the language's own parser is a hidden dependency on the very thing we claim to encode. The grammar wasn't encoded; it was borrowed.
2. **It breaks portability.** `ast` couples the kernel to a specific Python runtime/version; `sympy`/`pycparser` are large libs. None of that runs on the edge / PAL target (F793) where the kernel should live as a tiny portable artifact. LOGO's hand-written parser runs anywhere.
3. **"C needs pycparser" was wrong by our own logic.** C, like LOGO, is a closed finite grammar we *encode ourselves* (tokenizer + the constructs that carry A-N classes) — no pycparser.

## Done right (dep-free Python rule kernel, the LOGO way)
`R-RBS-LM-CODEKERNEL_…py` replaces `ast` with **our own tokenizer (INDENT/DEDENT, operators, keywords) + recursive-descent parser** over the operator-class-bearing subset (def/return/for/while/if/assign/augassign/compare/and-or/binop/call/name/const), feeding the **same** A-N signature engine (`bind(op-class, bundle(child-sigs))`). srmech HDC ops are the *substrate*, not a parser dep. Verified — same behaviour as the `ast` version:
- rename-invariance **+1.0000** (`f(a,b)=a+b` ≡ `g(x,y)=x+y`);
- our parser's A-N classes: `DEF · I(loop) · C(branch) · A(assign) · K(compare) · ALU(add) · M(product) · RET`;
- structure-clustering within **+1.00** / cross **+0.42** / separation **+0.58**;
- structure-not-intent (loop-sum vs `sum(xs)`) **+0.52** (below within-1.0).

So the rule kernel runs with **zero external dependency** — exactly like LOGO/chess. (Supersedes the `ast`-based CODE kernel for the Python rule kernel; the old script stays as the historical artifact.)

## The general rule (the correction, stated)
**A rule kernel ENCODES its grammar — a hand-written tokenizer + parser — and imports NO language interpreter.** This is the chess/LOGO discipline; the `ast`/`sympy`/`pycparser` shortcuts are the failure mode (borrow-the-runtime instead of encode-the-grammar). It also makes the kernel **portable / edge-ready** (F793): a self-encoded grammar is a tiny artifact that runs on any substrate, no host runtime.
- **C kernel:** the same — write a C tokenizer + the constructs that map to A-N (`if→C`, `for/while→I`, `=→A`, `==/<→K`, `+/-→ALU`, `*→M`, `/→N`, call/`def`), **no pycparser.**
- **LaTeX kernel:** the same — write a `\cmd{}` / `$…$` / `_^` tokenizer + a small math grammar, **no sympy.**

## Honest scope
- The dep-free Python kernel covers the **operator-class subset** (the A-N structure is the point), not all of Python's grammar — exactly as LOGO covers turtle commands, not all of a general language. Full-grammar coverage is more productions, same method.
- `[4]` structure-not-intent reads +0.52 (vs the ast version's lower value) — both tiny functions share the def/group/return scaffolding; still clearly below within-group 1.0. A larger corpus sharpens it.
- srmech HDC (`bind/bundle/permute/mint_vector`) is the framework substrate, not a parser dependency.

## Verdict
The user is right: **rule kernels should have no dependency** — we encode the closed grammar ourselves (the LOGO route, `logo_parser.py`). The CODE (`ast`) and LaTeX (`sympy`) kernels took a borrow-the-interpreter shortcut that violates the chess/LOGO/F455 thesis and breaks edge/PAL portability. Fixed: a **dep-free Python rule kernel** (our own tokenizer + recursive-descent) reproduces rename-invariance + structure-clustering with **zero external deps** — portable, edge-ready, and wireable into Siona without dragging in a host runtime. C and LaTeX are the same: write the grammar, no pycparser/sympy.
