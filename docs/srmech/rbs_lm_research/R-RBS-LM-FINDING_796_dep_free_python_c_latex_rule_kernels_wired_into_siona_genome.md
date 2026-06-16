# F796 — the Python / C / LaTeX rule kernels, rebuilt dep-FREE (our own grammars, no ast/sympy/pycparser) as genuine RBS-HDC instruments, and WIRED into Siona's genome: she now holds the construct→A-N vocabulary AND structurally reads pasted code/math

**Date:** 2026-06-16 · **srmech:** 0.7.5rc166 · **Composes:** F795 (the dep-free Python kernel + the rule: a rule kernel self-encodes its grammar, no interpreter), the LOGO/chess spectral kernels (the exemplars), F764 (the markup grammar — the sibling genome language-layer component), F793 (portable/edge-ready — no host runtime) · **User direction (2026-06-16):** "we should not be sneaking in deps when they aren't asked for — this is what srmech and our research notebooks are for. I don't understand how the other deliverable was an RBS-HDC instrument. let's fix it now."

## The fix (the user's point, applied)
The earlier CODE (`ast`) and LaTeX (`sympy`) kernels weren't truly **RBS-HDC instruments** — they borrowed a host interpreter to parse, then bound the result with srmech HDC. A genuine instrument is **self-encoded end-to-end**: *our* grammar + the srmech HDC substrate, no external parser. Built that:
- **`R-RBS-LM-RULEKERNELS_…py`** — one shared module, three dep-FREE grammars (our own tokenizer + recursive-descent each): **Python** (indentation blocks), **C** (brace/semicolon blocks), **LaTeX-math** (command/brace/`^`/`_`). Each emits the **same A-N operator signature** (`bind(op-class, bundle(child-sigs))`) over srmech HDC. **No `ast`, no `sympy`, no `pycparser`.**
- Verified — genuine instruments: symbol/rename-invariance **+1.0000** for all three; and **cross-language structural equivalence** — `def f(a,b): return a+b` (Python) and `int f(int a,int b){return a+b;}` (C) **both** read as `{ALU(add), DEF, RET}`; `E = m c^2` → `{Jpow(power), K(equation), M(product)}`. The closed grammar is ENCODED (chess/LOGO/F455), not borrowed.

## Wired into Siona (both senses of "understand")
1. **She HOLDS the vocabulary** — a new **`code-grammar` chromosome** in the genome carries the construct→A-N map (`if→C`, `for/while→I`, `=→A`, `compare→K`, `+-→ALU`, `*→M`, `/,\frac→N`, `**,^→Jpow`, `&&/||→B`, `call→M`, `def→DEF`, `return→RET`). `GENEPOOL_SCHEMA_VERSION` bumped → forces a genome rebuild so the new chromosome lands.
2. **She READS code/math** — a runtime **rule-kernel route**: a pasted Python/C/LaTeX fragment (detected) is parsed by the dep-free grammar → its A-N construct classes + a one-line structural read. Live (fresh instance):
   - `def f(a,b): return a+b` → *"a python fragment built from: ALU(add), DEF, RET"*
   - a C loop-sum → *"a c fragment built from: A(assign), ALU(add), DEF, I(loop), K(compare), RET"*
   - `E = m c^2` → *"a latex fragment built from: Jpow(power), K(equation), M(product)"*
   - plain English ("what is tomato") → unaffected (definition tier; the code detector is conservative).

## Honest scope
- Each grammar covers the **operator-class-bearing subset** (the A-N structure is the point — exactly as LOGO covers turtle commands), not the full language. More productions = more coverage, same method, still dep-free.
- The C kernel was **specified-not-built** before (F790 noted "C is the same via pycparser, flagged"); it is now **actually built** — dep-free, no pycparser.
- The standalone `ast` CODE kernel + `sympy` LaTeX kernels remain as historical artifacts (superseded by this dep-free module).
- `detect_language` is a conservative heuristic; the rule-kernel route only fires on clear code/math markers (`def …(`, `{…;`, `\frac`, `$…$`, `x^n`).
- srmech HDC (`bind/bundle/permute/mint_vector`) is the substrate, not a parser dep.

## Verdict
The rule kernels are now **genuine RBS-HDC instruments**: Python, C, and LaTeX grammars **encoded by us** (no `ast`/`sympy`/`pycparser`), each symbol-invariant + structurally clustering, on the srmech substrate — the chess/LOGO route the user has always meant. Wired into Siona two ways: a **`code-grammar` chromosome** (she holds the construct→A-N vocabulary) and a **runtime rule-kernel route** (she structurally reads pasted Python/C/LaTeX). No deps sneaked in; portable/edge-ready (F793). Deployed to the live server.
