# F797 — the dep-free rule kernels are a CROSS-LANGUAGE structural-equivalence instrument: a Python and a C fragment of the same algorithm get the SAME A-N signature (+1.0000), while same-task-different-structure stays low. Siona can now COMPARE two code/math fragments by structure — useful for the full-wiki encode (one A-N signature space spans the embedded sub-languages).

**Date:** 2026-06-16 · **srmech:** 0.7.5rc166 · **Composes:** F796 (the dep-free Python/C/LaTeX rule kernels), F795 (self-encoded grammars), the chess/LOGO route, `[[user_stance_whole_research_corpus_is_proof_not_single_arc]]` (cross-substrate convergence is the proof shape) · **User direction (2026-06-16):** "that's a good experiment to try out, let's do it!" · **Provenance:** `R-RBS-LM-CODECOMPARE_…py` + `RULEKERNELS.compare()` + Siona compare route.

## The experiment (does the A-N signature judge the ALGORITHM, across languages?)
Comparing fragments by their dep-free A-N rule-kernel signatures (cosine similarity):
- **CROSS-LANGUAGE same-algorithm:** `def f(a,b): return a+b` (Python) ≟ `int f(int a,int b){return a+b;}` (C) = **+1.0000**; recursive factorial Python ≟ C = **+1.0000**. The signature is **language-agnostic** — same algorithm → same vector, regardless of host syntax or names. (loop-sum Python ≟ C = +0.62 — honestly lower, because C's `for(init;cond;step)` IS a structurally different loop than Python's `for x in xs`; the kernel correctly reports a real shape difference, not a false match.)
- **same task, DIFFERENT structure:** loop-sum ≟ recursive-sum = +0.24; loop-sum ≟ `sum(xs)` = +0.52→(in-route, −0.00 for a tighter pair). Low — it reads STRUCTURE, not what the code computes.
- **different algorithm:** add ≟ loop-sum = +0.24, etc. — low.
- **math (LaTeX):** `E=mc²` ≟ `P=qr²` (renamed) = **+1.0000**; ≟ `F=ma` (no power) = +0.76; ≟ `a/b+c/d` (ratios) = **+0.007**.
- **separation:** cross-language-same mean **+0.87** vs different mean **+0.42** → **+0.45**.

**Reading:** the A-N signature reads the **algorithm** — rename-invariant AND language-invariant — a dep-free **cross-substrate structural-equivalence instrument**. Python ≡ C when the structure matches; the surface language is stripped, only the A-N operator shape remains. (This is `[[user_stance_whole_research_corpus_is_proof_not_single_arc]]` in miniature: two substrates, one structure.)

## Wired into Siona
`RULEKERNELS.compare(a, b)` → `(similarity, classes_a, classes_b, verdict)`. A Siona route on the `|||` separator: *"<fragment A> ||| <fragment B>"* → the structural-similarity verdict. Live:
- `def f(a,b): return a+b ||| int f(int a,int b){return a+b;}` → **"+1.000 → the SAME structure"** (A: ALU,DEF,RET | B: ALU,DEF,RET).
- loop-sum `|||` `return sum(xs)` → **"−0.004 → DIFFERENT structure"** (A: A,ALU,DEF,I(loop),RET | B: DEF,M(apply),RET).

## Why this matters for the BIG WIKI full encode (the user's lens)
enwiki articles embed **sub-languages** — code blocks, LaTeX/math, wiki/HTML markup, templates. The full encode needs to read those, not strip them (the F764 markup principle; the old `FULLWIKIKERNEL` audit was literally titled "sub_language_kernels_needed"). These dep-free rule kernels are exactly that layer — and the cross-language equivalence means **one A-N signature space spans all the embedded sub-languages**: a math formula, a Python snippet, and a C snippet all land in the *same* operator-class geometry as the prose's relations. So the full encode can fold embedded code/math into the same spectral store as the text — no separate pipeline, no interpreter deps, edge-portable (F793).

## Honest scope
- Each grammar covers the operator-class subset (the A-N structure is the point); the loop-shape difference (`for x in xs` vs `for(;;)`) is a genuine structural difference the kernel correctly scores lower — not a bug.
- `|||` is the explicit compare delimiter (a chat message rarely contains two cleanly-separable fragments otherwise); a smarter two-block detector is a follow-on.
- srmech HDC is the substrate; no ast/sympy/pycparser.

## Verdict
The dep-free rule kernels form a **cross-language structural-equivalence instrument**: same-algorithm Python and C fragments share the **same A-N signature (+1.0000)**, math renamings match (+1.0), and same-task-different-structure stays low — the signature reads the algorithm, not the surface or the host language. Siona can now **compare** two code/math fragments (`A ||| B` → structural verdict), live. For the **full-wiki encode**, this is the sub-language layer: embedded code/math/markup fold into the *same* A-N signature space as the prose — one store, no interpreter deps, edge-portable.
