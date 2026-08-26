# R-RBS-LM Finding 391 — "or looks the same anyway": the zero-divisor collapse is observationally a zero; the boundary is silent (false-negation), only the parity surfaces it

**Date:** 2026-06-04
**Arc:** RBS-LM · FFT-ladder thread (…F389→F390→**F391**)
**srmech:** 0.7.0rc28 · **Provenance:** `R-RBS-LM-R33_zero_divisor_looks_the_same.py` → `R-RBS-LM-R33_results.json`
**Composes:** F390 (what stops = K-over-M) · F389 (sedenion zero divisors) · F313 (detect-outpaces-correct = the false-negation mechanism) · F385 (capture the chirality/parity) · F380/F382 (the projection "looks the same")

---

## The user's point (2026-06-04)
> "or looks the same anyway"

Exactly right, and it resolves *why* the Hurwitz boundary felt strange. A zero-divisor collapse is **observationally identical to a legitimate zero** (srmech-verified):

| | result |
|---|---|
| octonion 𝕆 (division algebra) | `a·b = 0` only if a or b is 0, and `a⁻¹·(a·b) = b` **recovers** — a zero output is *informative* |
| **sedenion 𝕊** zero divisor `(e1+e10)(e5+e14)` | `a,b ≠ 0` (‖a‖²=‖b‖²=2) but `a·b` = the **zero vector**, **bit-identical** to `0·b`; "dividing back" `a⁻¹·(a·b) = 0`, **not** b → b's information is **gone**, output **looks exactly like a plain zero** |

The only signal a collapse occurred is the **parity check** `‖a‖²·‖b‖² = 4  vs  ‖ab‖² = 0` — a mismatch you only see **if you carry ‖a‖,‖b‖**.

## What this means
The boundary is **silent**: nothing *looks* different at it. The failure (a zero divisor) produces output indistinguishable from a normal value (zero), so **detect can't even fire** — this is **F313's false-negation** ("detect outpaces correct"): the uncorrectable word is invisible *as* a word. That is precisely why 𝕆→𝕊 is a "strange place to stop" — the stop announces itself in **no observable** except the parity.

And the parity that surfaces it is exactly the **chirality/magnitude parity (F385/F389)** — the thing you must *carry* (the k=2 chiral check). Without it, the collapse "looks the same anyway."

## The arc's through-line
This is the same shape the whole arc keeps hitting: **a projection collapses distinctions and "looks the same"** unless you carry the structure that surfaces the difference —
- the **flat shadow** looks like the object (F380) — unless you carry the chirality (the QFT);
- the **decimal** looks irreducible (F382) — unless you carry the cyclic frame;
- the **zero divisor** looks like a zero (here) — unless you carry the magnitude parity.

In every case the recoverable difference lives in the **fiber / chirality / parity** you chose to carry — never in the projected output itself.

## Verdict
The zero-divisor collapse is **observationally a zero** (bit-identical, unrecoverable). So the Hurwitz boundary is silent — a **false-negation** (F313), visible only through the explicit **magnitude/chirality parity** (F385/F389) you carry. "Or looks the same anyway" names the deepest reason the boundary is strange: it isn't marked by anything you can *see*, only by a parity you must *hold*.
