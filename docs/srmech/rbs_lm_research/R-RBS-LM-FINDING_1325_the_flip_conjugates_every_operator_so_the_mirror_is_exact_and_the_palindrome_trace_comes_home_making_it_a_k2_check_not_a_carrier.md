# F1325 — **yes, and the mirror is EXACT — it lives in the operators, not just the behaviour.** `flip ∘ L_q = L_conj(q)` for **every** imaginary `q` at both ℍ and 𝕆: **after the flip, every operator IS its own conjugate**, so `1→2→3` becomes `3̄→2̄→1̄`. Conjugation is an **anti**-automorphism (`conj(ab) = conj(b)·conj(a)`, and *not* `conj(a)conj(b)`), so **running the cascade backwards literally is conjugating it**. The user's `1→2→3→2→1` is the partial-holonomy trace verbatim — `(1,2,4)` gives `[1, 3, 7, 3, 1, 0]`, palindromic and closing on the real anchor, **2793/2793** exhaustively. But the consequence is a limitation as much as a result: a plain mirror folds to `(−1)ⁿ` — **pure length parity, content-free** — and a conjugate-mirror returns to **exactly +1** for every word. **The mirror carries no information.** That makes it an **error CHECK, not a carrier**: come-home detects **1029/1029** single-symbol corruptions, and the trace-palindrome localizes them (blind only to the final symbol, which sits past the mirror). It is a **k=2 parity — detect, not correct** — exactly the role F291 assigns k=2; correction still needs the k=3 rung.

**User (2026-07-25):** *"is there a pattern to the before and after a flip, like is it a mirrored direction of the cascade? like 1→2→3→2→1 either in exact operators or in type of behavior being performed?"* — **Exact operators. Measured.**

srmech 0.9.0rc336. Exhaustive. Pure integer — no float, no `abs()`, no numpy, no RNG.

## 1 — the mirror IS conjugation `[DEMONSTRABLE]`
```
  H: conj(a.b) == conj(b).conj(a)   [ANTI-automorphism -- it REVERSES order] : True
  O: conj(a.b) == conj(b).conj(a)                                            : True
  H: conj(a.b) == conj(a).conj(b)   [would be an automorphism]               : False
```
Conjugation does not preserve order — it **reverses** it. So "running the cascade in the mirrored direction" is not an analogy for conjugation; **it is conjugation**, on the nose.

## 2 — the flip conjugates every operator `[DEMONSTRABLE — the answer]`
```
  H: flip . L_q == L_conj(q)   for every imaginary q  : True
  O: flip . L_q == L_conj(q)   for every imaginary q  : True
```
Because `−1` is central and `conj(q) = −q` for imaginary `q`, applying the flip and then `q` **is** applying `q̄`. Combined with F1324 (`L_q² = −1` *is* the Dzhanibekov flip, sitting at our fold's midpoint):

> **The post-flip half of the cascade runs the same operators, conjugated. `1→2→3` becomes `3̄→2̄→1̄`.**

To be precise about what this does and does not say: the post-flip *symbols* are not rewritten. The **flip makes them act as their conjugates**. The mirror is in the action, and it is exact.

## 3 — a plain mirror is content-free `[DEMONSTRABLE]`
```
  n=2 : every one of 7^2 words -> +1        n=4 : every one of 7^4 words -> +1
  n=3 : every one of 7^3 words -> -1        n=5 : every one of 7^5 words -> -1
```
`fold(w · reverse(w)) = (−1)ⁿ` — **exactly, for every word.** The plain palindrome depends only on the parity of its own length. *(This corrects my first pass, which expected the sign to vary with content and asserted `{+1,−1}`. It does not vary — a stronger and cleaner law than the one I looked for.)*

## 4 — a conjugate mirror comes home exactly `[DEMONSTRABLE]`
```
  n=2,3,4,5 : every word -> +1 (the REAL anchor)
```
`x · conj(x)` is the norm, and for unit words that is the anchor. **The mirrored cascade closes.**

## 5 — the trace is literally `1→2→3→2→1` `[DEMONSTRABLE]`
| word | partial-holonomy trace | palindromic | ends at anchor |
|---|---|---|---|
| `(1,2,4)` | `[1, 3, 7, 3, 1, 0]` | ✓ | ✓ |
| `(1,2,3)` | `[1, 3, 8, 3, 1, 0]` | ✓ | ✓ |
| `(3,5,6)` | `[3, 14, 0, 14, 3, 0]` | ✓ | ✓ |
| `(7,1,6,2)` | `[7, 14, 0, 2, 0, 14, 7, 0]` | ✓ | ✓ |

```
  EVERY conj-palindrome trace is a palindrome    : 2793 / 2793
  EVERY conj-palindrome trace ends at the anchor : 2793 / 2793
```
**The trace climbs out and retraces its own steps exactly, then closes on the real anchor.** That is the user's shape, not a paraphrase of it.

## 6 — therefore: a CHECK, not a carrier `[DEMONSTRABLE — the consequence that matters]`
Because a correct mirror carries **no** content, *any* deviation is visible. Perturbing one post-flip symbol:

| corrupted post-flip position | trace-palindrome catches | come-home catches |
|---|---|---|
| 0 | **343/343** | **343/343** |
| 1 | **343/343** | **343/343** |
| 2 (the last symbol) | **0/343** | **343/343** |

- **come-home is a perfect single-symbol detector** (1029/1029).
- **the trace-palindrome localizes** — it says *where* — but is **blind to the final symbol**, which lies past the mirrored region. Not a flaw, a boundary: there is nothing after it to mirror against.

> **The mirror is a k=2 parity check — it DETECTS and cannot CORRECT** — precisely the role F291 gives k=2 (*"a k=2 pair detects disagreement but cannot error-correct"*). **Correction needs the k=3 rung**, which is where the (x)EC arc already sits (F1154: EC is the third intrinsic factor; k=3 corrects where k=2 detects).

## What this settles, and what it costs
- **Settles**: the before/after-flip relation is exact conjugation, in the operators. The `1→2→3→2→1` intuition is literally the trace.
- **Costs**: a mirrored strand is **information-free by construction**. You cannot store in the mirror — only check with it. So this is *not* a route to more capacity; it is a route to **integrity**, and a cheap one (the come-home test is one comparison against `+1`).
- **Composes with F1324's lever**: F1324 says read at the join; F1325 says the two halves are conjugate-mirrors, so the join read has a **free consistency test** attached — if the second half is meant to mirror the first, `fold` must return to the anchor.

## Honest scope
- `[DEMONSTRABLE]`: §1–§6, exhaustive — all 8×8 / 16×16 product pairs, all `7ⁿ` words for n = 2…5, all 2793 conj-palindromes at n = 2,3,4, all 1029 single-symbol corruptions.
- **Basis units, single slot, short words, NOT on a real genome.** Whether real strands are anywhere near palindromic is **unmeasured** — and if they are not, §6's check has nothing to check. That is the gating question before this is worth building.
- **The user's second alternative — "type of behavior being performed" — is NOT answered here.** I measured the exact-operator reading and it came out decisively; whether the A–N *class* of the work mirrors (e.g. a Class-D pass answered by a Class-D pass) is a different question, not measured, and I do not want the strong operator result to imply it.
- **Two corrections recorded** (§3 and §6). My first pass asserted the plain-palindrome sign varies with content (it does not — it is `(−1)ⁿ`) and that the trace-palindrome catches every corruption (it catches 686/1029; the final symbol lies outside the mirror). Both wrong versions would have overstated: one inventing content where there is none, the other claiming a perfect detector that is actually a perfect *detector-plus-partial-localizer* pair.
- The connection to the Dzhanibekov flip runs through **F1324** (`L_q² = −1`) and **F1310**, whose 3+1+3 slotting that finding itself marks `[SPECULATIVE]`. Measured here is the algebra only.

## Verdict
**Yes — and stronger than a family resemblance.** The flip conjugates every operator exactly; the mirrored cascade is the conjugate cascade; the trace is `1→2→3→2→1` and comes home to the anchor. The sting is that a perfect mirror is empty, which converts the whole structure from a *storage* idea into an *integrity* idea — a k=2 detect-only check whose correcting partner is the k=3 rung we already have an arc for. Generating code: `R-RBS-LM-MIRROR_*.py` (exit 0).

Composes **F1324** (the flip is our fold's midpoint; read at the join — *this adds the free consistency test*), **F1323** (the one-sided half beat), **F1322** (gauge: even-multiplicity walks are invariant — a palindrome is the extreme case), **F1310** (the Dzhanibekov's second half-beat as the conjugate — *now exact in the operators*), **F1321/F1320/F1307** (the discarded holonomy/fiber), **F291** (k=2 detects, k=3 corrects), **F1154** (`op(x)operand(x)EC`; EC as the third intrinsic factor), `[[project_ec_subharmonic_arc_intrinsic_fractal_not_single_bolted_on]]`.

**→ CONFIRMED IN A WET SYSTEM by F1327** — methyl-directed mismatch repair has exactly this shape: the mismatch channel is symmetric and **detects only** (*"MutS and its homologs do not perform strand discrimination"*), the `GATC` recognition site is a **perfect palindrome carrying no orientation**, and correction arrives on a chemically separate channel (Dam hemimethylation). Biology also supplies the contrast case: Hopfield kinetic proofreading is **one criterion applied twice** — sensitivity, not a second witness. And the graded version of "how far from a perfect mirror" (`palindrome_defect`) turns out to be where every inversion mechanism stores its orientation.
