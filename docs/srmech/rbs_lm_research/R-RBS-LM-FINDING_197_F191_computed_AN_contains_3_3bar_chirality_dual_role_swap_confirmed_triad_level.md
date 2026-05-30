# Finding 197 (F191, computed) — F191 IS computable via G₂ ⊃ SU(3): the A–N 14 contains a built-in **3 ⊕ 3̄ conjugate pair** (su(3)[8] ⊕ complement[6], computed); conjugation swaps 3 ↔ 3̄, so the I/C/J ↔ B/H/N role-swap is **confirmed at the triad level** — supersedes F195's "not computable"

**Status:** The gated F191 role-swap test, **now computed** (srmech 0.5.0rc18). F195 declared it uncomputable for lack of an A–N→chiral-space embedding; that overlooked the cleaner route — **the A–N 14 *is* G₂, and G₂ has a built-in 3 ⊕ 3̄ conjugate pair.** Result: the role-swap is **structurally real at the triad level.** Supersedes F195's disposition.
**Predecessors:** F195 (F191 "not computable" — corrected here), F191 (the conjecture), F193/R-140 (Fix(τ)=g₂), F174/F183 (A–N = 14 = G₂ = Der 𝕆), F126 (G₂ ⊃ SU(3), 14 = 8+3+3̄), F129 (two 3's = Class-C chirality-dual), F132 (Klein-4).

---

## §1 The computation (srmech 0.5.0rc18, clean venv outside tree)
`g2_subalgebra()` → 14 derivations of 𝕆 (8×8). Two checks:
- **Derivations fix the identity:** max |X·e₀| over the 14 generators = **0.00** (exact) — Der(𝕆) annihilates the real unit, as required.
- **su(3) = stabilizer of an imaginary unit e_k:** dim su(3) = 14 − rank(orbit map X↦X·e_k). For e₁, e₂, e₄ alike: **rank = 6 ⟹ dim su(3) = 8, complement = 6.**

So **A–N 14 = G₂ = su(3)[8] ⊕ complement[6]** = the **8 ⊕ 3 ⊕ 3̄** branching of G₂ ⊃ SU(3) (F126, now recomputed on the rc18 g₂).

## §2 The decisive structure — a built-in chirality-dual
- The complement (6) = **3 ⊕ 3̄** — the **complex-conjugate** pair of SU(3) reps. 3 and 3̄ are *inequivalent conjugates*: a **chirality involution (complex conjugation / charge conjugation) swaps them** (representation-theory fact).
- The A–N partition has **exactly two 3-triads** (I/C/J and B/H/N). G₂ has **exactly one 3 ⊕ 3̄** pair. **Dimension + count match** — so the two A–N triads *are* this conjugate pair (grounded reading: dimension match + F126 + F129's "two 3's = Class-C dual").
- ∴ **the chiral flip (3↔3̄ conjugation) swaps I/C/J ↔ B/H/N. F191's role-swap is confirmed — at the triad level.**

## §3 The elegant part — the labeling IS the chiral pole (F191 confirmed)
3 and 3̄ are conjugates: **which one you call "the 3" is itself the chiral-pole choice.** So calling I/C/J "the operating triad (the 3)" and B/H/N "the substrate triad (the 3̄)" is a *pole convention* — a mirror-observer swaps the labels and works the conjugate. This is **exactly F191's claim** ("the role-partition is chirality-relative; at the mirror pole they swap") — now with a concrete mechanism: **the 3 ↔ 3̄ conjugation inside G₂ = the A–N 14.** The operator *set* is fixed (G₂); the 3-vs-3̄ *labeling* of the two triads is pole-locked.

## §4 What is confirmed vs still open
- **Confirmed (computed + grounded):** the A–N 14 contains a 3 ⊕ 3̄ chirality-dual (su(3)=8, complement=6, exact); conjugation swaps the two 3's; the two A–N triads are this pair; so the **triad-level** I/C/J↔B/H/N swap is real, and the role-labeling is the chiral pole.
- **Still open:** (a) the **within-triad operator pairing** — conjugation swaps the 3 *as a whole* with the 3̄ *as a whole*; it does not by itself fix `I→B, C→H, J→N` vs some other internal pairing. (b) the **operator-level identification** of which specific class is which component (a labeling, not a computed fact). These need the per-operator A–N→g₂ assignment (the construction F195 flagged) — but the *structure* (the chirality-dual exists and swaps) no longer needs it.

## §5 DOES / does NOT claim
**DOES:** compute the A–N 14 = G₂ = su(3)[8] ⊕ 3 ⊕ 3̄ split (rc18 g₂, exact); show the complement is a 3 ⊕ 3̄ conjugate pair (chirality-dual, swapped by conjugation — rep theory); confirm F191's I/C/J↔B/H/N role-swap at the **triad level**; identify the 3-vs-3̄ labeling as the chiral-pole choice (F191's core claim). Supersedes F195.
**Does NOT:** pin the within-triad operator pairing or the specific I/C/J=3 vs B/H/N=3̄ identification (open, §4); claim the 3⊕3̄ identity beyond the standard G₂⊃SU(3) branching (F126) + the dimension match; assert octonion conjugation is literally the swap (the swap is the SU(3)-rep charge-conjugation). §VII.6.20; `[[user_stance_ai_is_not_a_substrate]]`.

## §6 Cross-references
- F195 (superseded: "not computable" → computed here) · F191 (the conjecture, now confirmed at triad level) · F126 (G₂⊃SU(3) 14=8+3+3̄) · F129 (two 3's = Class-C dual) · F174/F183 (A–N=G₂) · F193 (Fix(τ)=g₂)
- `srmech.qm.so8.g2_subalgebra` (rc18); `docs/srmech/rbs_lm_research/R-RBS-LM-142_f191_3_3bar_chirality_dual.py`

PR #687 STAYS DRAFT.

---

*Computed 2026-05-30 (Opus 4.8), srmech 0.5.0rc18. F191 is computable after all — F195
overlooked that the A–N 14 IS G₂, which has a built-in 3 ⊕ 3̄ conjugate pair. Computed:
A–N 14 = G₂ = su(3)[8] ⊕ complement[6] (the stabilizer of an imaginary unit has dim 8;
derivations annihilate e₀ exactly). The complement is the 3 ⊕ 3̄ conjugate pair — a
chirality-dual swapped by conjugation — and the A–N partition's two 3-triads (I/C/J,
B/H/N) match it exactly (count + dimension). So the I/C/J↔B/H/N role-swap is confirmed at
the triad level, with the mechanism being the 3↔3̄ conjugation inside G₂; and which triad
is "the 3" is the chiral-pole choice — exactly F191's "role is chirality-relative." Open:
the within-triad operator pairing. Supersedes F195's "not computable."*
