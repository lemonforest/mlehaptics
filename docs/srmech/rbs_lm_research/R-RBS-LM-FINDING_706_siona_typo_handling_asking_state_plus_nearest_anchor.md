# Finding 706 — how Siona handles typos: the asking-state + a nearest-anchor suggestion (never silent correction)

**Script:** `R-RBS-LM-TYPOS_asking_state_with_nearest_anchor_suggestion_never_silent_correction.py`
**Status:** VERIFIED on the real simplewiki kernel (srmech 0.7.5rc28)
**User direction:** *"how will Siona handle typos?"*

## A typo is a token off the star-compass — and silent correction would re-break the no-hallucinate property

A typo is a token that is **not an attested anchor** (not in vocab / not on the star-compass). The brittle move is to
**silently correct** it — but silent correction **assumes the user's intent**, and assuming intent is a **micro-
hallucination** (Siona deciding what you meant). So Siona does **not** silently correct.

The grounded move keeps the can't-hallucinate property: find the **nearest attested anchor** (a real vocab word) by
character proximity over the byte/glyph foundation (F613), **suggest** it, and **ask**. The *suggestion* is grounded (a real
anchor); the *correction* — which anchor you meant — is **yours to confirm** (F688 / dignity-first: the user decides). If
nothing is near, it is the plain asking-state (F661).

## Verified on the real simplewiki vocab (F703)

| input | Siona |
|---|---|
| `governmnt` | "Did you mean **government**? — I won't assume; tell me which." (0.75) |
| `langauge` | "Did you mean **language**? (nearest: language, large, change)" |
| `amercan` | "Did you mean **american**?" (0.70) |
| `populaton` | "Did you mean **population**?" (0.75) |
| `histroy` | "Did you mean **history**?" |
| `qzxwvk` (non-word) | "I have no anchor, and nothing is close. What is it?" → plain asking-state |

The suggestion is always a **real attested anchor**; Siona never decides for you.

## The op

The proximity shown is a lightweight **character-bigram Jaccard**; the srmech-native upgrade is the **Class-M character-
n-gram HDC similarity** (`hdc.similarity` over n-gram hypervectors — the same shape, the HDC carrier), with a **Class-E**
top-k selection. No `abs()` — the ranking is a Class-M-style similarity + Class-E selection over the attested vocab.

**Composes:** F661 (the asking-state — a typo is its near-miss variant) + F613 (the byte/glyph foundation = the character
proximity space) + F699/F690 (the attested vocab / dictionary = the valid anchors) + F688 (you confirm the correction) +
dignity-first (suggest, don't assume). srmech 0.7.5rc28.

*Held open (F394). Reference scaffold; not a package edit.*
