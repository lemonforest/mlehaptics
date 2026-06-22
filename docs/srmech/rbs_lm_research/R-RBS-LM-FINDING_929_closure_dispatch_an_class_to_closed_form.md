# F929 — the **closure dispatch**: "cascade → equality" is the classical problem of **closed-form reduction**, and *which* reduction collapses a given cascade is fixed by its algebraic structure — which is exactly what an A–N class names. So the 14 A–N classes are a **dispatch table over the established closed-form theories** (spectral, cyclic, generating-function, Galois, …): the class tells you which ordered language turns the cascade into an equation — or marks it **open** (no closing symmetry → it must be *inferred/walked*, not solved). `the_one` and `resonant_spectrum` are not new tricks; they are the framework's instances of two rows of this table (cyclic + spectral).

**Date:** 2026-06-22 · **srmech:** 0.9.0rc33 · **Branch:** `research/rbs-lm-rolling-2` (PR #687) · **Composes:** F928/§75 (`resonant_spectrum` = the spectral row), `the_one` (the cyclic row), F920/F781 (spectral instances), F901/F912 (the construction/recursion rows), `[[feedback_correct_user_wrong_words_against_record]]` (solve-for/derive = closed vs infer = open) · **User direction (2026-06-22):** "is there already ordered math language that tells us how to make a cascade into an equality equation or formula?"

## The dispatch (cascade structure → the established ordered language → framework instance)
| cascade structure (the A–N class) | the classical "ordered language" (turns the cascade into an equality) | framework instance |
|---|---|---|
| iterate one linear map `Lⁿ` (**L**) | **spectral theorem / diagonalization** → `V Λⁿ Vᵀ` | **`resonant_spectrum`** (§75), F920/F781 |
| rotate / cycle / epicycle (**I, C, K**) | **cyclic groups, roots of unity, `e^{iθ}`** | **`the_one`** `S(σ,θ)` |
| linear recurrence `aₙ=…aₙ₋₁…` (**I**) | **characteristic equation** (Fibonacci → Binet) | cyclic / `cyclic_period` |
| build-from-parts: seq/set/cycle of (**M, B**) | **generating functions + the symbolic method** (Analytic Combinatorics — a literal grammar: construction → GF equation) | the C1 compose ladder (F901/F912) |
| discrete-time filter / LTI cascade | **Z-transform → transfer function `H(z)`** | `srmech.signal_processing` |
| differential cascade (ODE) | **Laplace transform / operational calculus** → algebra in `s` | `asymptotic_calculus` |
| recursive program (fold over structure) (**H**) | **catamorphisms / recursion schemes** (Bird–Meertens "algebra of programs") | the recursive C1 fold (F912) |
| parametrized sum `Σ` (**J, N**) | **creative telescoping / the WZ method** (Zeilberger) — *algorithmically* emits the closed identity **and proves the equality** | **— not yet in srmech (the open row)** |
| multiplicative / factor / period (**J**) | **prime factorisation / p-adic / order** | `Qprime` (F923) |
| *any* composition, reasoned by equality | **monoidal categories / string diagrams / PROPs** — the formal grammar of composition | the A–N operator algebra itself |
| **does it close at all?** | **Galois theory** — closes by radicals ⇔ the symmetry group is solvable | **solve-for/derive (closed) vs infer (open)** |

## The two boundaries that matter
1. **Closed vs open = solvable vs not (Galois) = solve-for/derive vs infer.** A cascade collapses to an equality *iff* it has the closing symmetry (a group, a ring, an eigenbasis). Those that do → an equation (solve-for / derive). Those that don't → Siona must **walk** them (infer) — not a failure, the genuine open/closed line. This is the framework's own lexicon (the user's solve/derive/infer distinction) and Galois's at once.
2. **The framework-native part is the *typing*, not the theories.** Each classical theory handles **one** structure; the **A–N partition is the dispatch over all of them** — the class of the cascade *selects* the reduction (L → diagonalize, I/C/K → cyclic, J → number-theoretic/period, M/B → generating-function, H → recursion-scheme, …). That dispatch is what's new; the rows are textbook.

## Implications
- **Sharpens §75:** `resonant_spectrum` is precisely the **spectral row** of a known table — which makes the srmech ask more legible (it's "ship the diagonalization closure," not a bespoke gadget).
- **The one missing row:** the `Σ` row — **creative telescoping / WZ** — is the only listed ordered-language the framework has no instance of, and it is *algorithmic* (it auto-derives + proves closed identities for holonomic sums). A candidate to add (it would give Class J/N a closed-form *prover*, not just a carrier).

## Verdict / next
Yes — "cascade → equation" is a central, well-mapped project of mathematics; `the_one`/`resonant_spectrum` are the cyclic/spectral rows, and the **A–N class is the dispatch** that picks the row (or declares the cascade open = infer, the Galois/solve-vs-infer line). **Next candidates:** (i) the creative-telescoping/WZ row as a srmech ask (the missing algorithmic closer for Σ-cascades); (ii) tag each existing finding's cascade with its closing row, surfacing which arcs are closed-solvable vs open-infer.
