# R-RBS-LM-70 Test A — CORRECTION to Finding 70 framing

**Status:** CORRECTION committed (no code change; framing fix)
**Predecessor commit:** `aa007d7a` (Test A — "HDC is decorative")
**Date:** 2026-05-26
**Correction trigger:** User pointed out that I conflated *generic Kanerva-style HDC*
with *RBS-HDC instrument shape*. The two are not the same.

---

## §1 The conflation

In the Test A commit message and follow-up summary, I wrote:

> "HDC layer is architecturally decorative" / "the cascade is classical NLP
> cooccurrence-eigvec methodology + multi-stage compositional pipeline, not
> hyperdimensional"

This is overreach. The user correctly flagged it:

> "How can HDC be decorative? our RBS-HDC instrument is supposed to be the
> shape of A-N operators I thought, no? what am I not understanding. I know
> that HDC the way the rest of the world does it is the reason we have crappy
> noise in the data, but the shape of the NN is RBS-HDC, right?"

---

## §2 What Test A actually measured

The narrow, specific claim that Test A *did* support:

> The operation `bundle(mint_vector(t) for t in top_K_tokens)` — namely,
> Kanerva-style HDC: random bipolar D-dimensional vector per token, summed
> for set-membership encoding — produces routing decisions and per-pair
> similarity scores indistinguishable from set-cosine over the top-K token
> sets directly. Routing accuracy 29/30 in both; Pearson r > 0.99 between
> similarity scores.

This is a finding about **random-bipolar-projection-for-set-membership**, which is
generic Kanerva-style HDC. The user explicitly noted this is "HDC the way the rest
of the world does it" and "the reason we have crappy noise in the data."

The finding is: **for set-membership encoding, random bipolar projection is
equivalent to set-membership similarity.** This is actually expected — projecting
a set into a random vector space and then measuring cosine recovers set-overlap
modulo SNR noise. Test A confirmed this empirically.

---

## §3 What Test A did NOT measure

The overreached extrapolation:

> ❌ "HDC is decorative"
> ❌ "RBS-HDC instrument is decorative"
> ❌ "The cascade SHAPE is classical NLP, not hyperdimensional"

None of these are supported by Test A. Specifically NOT measured:

1. **Class M as a class.** Class M includes bind, bundle, permute, similarity. We
   tested ONE op (bundle for set-membership). We didn't test bind. We didn't test
   permute. We didn't test similarity under associative composition.

2. **Class L (Laplacian eigendecomp).** This is the *load-bearing* part of the
   cascade. Strip Class L and there's no eigvec table to even ask similarity
   questions about. Class L is what produces the structural content in the first
   place.

3. **Other A-N classes used in the broader RBS-LM arc.** Class K (sign-flip
   thresholds in 49 Method B) and Class C (chirality preservation in 49 Method C)
   are load-bearing in their partitions. Test A's domain (DOMAIN routing) doesn't
   exercise them.

4. **The A-N cascade SHAPE.** The multi-class composition (Class L → Class M
   fingerprint → find-cascade → DOMAIN anchor → ride → G4 gating) is the actual
   RBS-HDC instrument. Test A swapped ONE step (Class M bundle) and showed it
   reduces to set-overlap. The COMPOSITION is unchanged. The SHAPE is unchanged.

---

## §4 The corrected Finding 70

**Finding 70 (corrected):**

> Our specific implementation of Class M as `bundle(mint_vector(t) for t in
> top_K_tokens)` — random bipolar vectors per token, summed for set-membership
> encoding — produces results equivalent to set-cosine over the top-K token sets
> directly. The random-bipolar-projection layer (generic Kanerva-style HDC) adds
> no measurable signal for set-membership similarity in DOMAIN-routing context.
>
> This does NOT show:
>   - That Class M as a class is decorative (we only tested bundle for set-membership)
>   - That Class L (Laplacian) is decorative (it's load-bearing)
>   - That the RBS-HDC instrument shape (A-N composition) is decorative (we only tested one sub-op)
>   - That the cascade is "classical NLP rather than hyperdimensional" — the
>     RBS-HDC instrument is the A-N cascade shape, which is what we've been
>     building all along
>
> What it DOES show:
>   - Generic-Kanerva-style HDC with random bipolar projection is noisy-redundant
>     for set-membership routing (consistent with user's prior framework reading)
>   - For DOMAIN routing, we could substitute set-cosine for HDC bundle/similarity
>     with no accuracy loss and clearer semantics
>   - The implementation choice for Class M in this sub-cascade is one of several
>     possible implementations; the A-N SHAPE is unchanged regardless of which we
>     pick

---

## §5 Framework correction — RBS-HDC ≠ generic HDC

Per `[[project_a_n_operators_are_harmonic_objects_themselves]]` and the
14-class A-N partition discipline:

- **RBS-HDC** = the A-N operator cascade SHAPE. It is the composition of (at
  minimum) Class L (Laplacian / spectral decomp), Class M (bind/bundle for
  composition), and any other classes the cascade calls for.

- **Generic HDC** (Kanerva-style) = random bipolar vectors + bundle (sum) +
  bind (XOR/multiply) + similarity (cosine). This is one *implementation*
  family; it has well-known noise properties.

- **The cascade SHAPE is RBS-HDC.** The implementation of Class M *as random
  bipolar vectors* is generic-HDC. The two are not the same thing. Test A
  showed the implementation is swappable; the shape is unchanged.

---

## §6 What WOULD test the broader RBS-HDC shape

Tests Test A did *not* perform, but that would diagnose RBS-HDC proper:

1. **Strip Class L** (replace Laplacian eigvecs with random projection of the
   cooccurrence graph): does routing accuracy degrade? *Expected: yes,
   significantly. This would confirm Class L is load-bearing.*

2. **Strip Class M entirely** (no fingerprint; route by raw cooccurrence
   matrix similarity): does routing accuracy degrade? *Expected: yes,
   because we lose the top-K compression and the alignment becomes O(N²)
   slow.*

3. **Replace random `mint_vector` with learned embedding** (word2vec, fasttext,
   or even just embedding from the source LLM): does routing accuracy
   improve? *Expected: maybe — the semantic structure of learned embeddings
   might tighten Class M's content fingerprint beyond what random projection
   captures.*

4. **Test Class M bind (not bundle).** Bundle is set composition; bind is
   associative composition. We never tested bind. For sequence emission (54r,
   54s) we'd plausibly need bind to encode position-content pairs.

These are the actual diagnostics for "is RBS-HDC as the cascade shape doing
real work." Test A only tested one sub-op of one class.

---

## §7 Updated commit-message vocabulary going forward

When discussing the post-Test-A architecture:

- ❌ Don't say "HDC is decorative" or "RBS-HDC is decorative"
- ✅ Say "the random-bipolar-bundle implementation of Class M for set-membership
  is equivalent to set-cosine in routing"
- ❌ Don't say "the cascade is classical NLP"
- ✅ Say "the cascade is the A-N composition shape we've been building (Class L
  Laplacian + Class M fingerprint + multi-stage composition), and the
  implementation of Class M's bundle as random projection is swappable for
  set-cosine in routing"

The shape claim stays; the implementation claim is narrowed.

---

## §8 Net effect

- All empirical findings 38-72 remain valid
- The framing of Finding 70 is tightened from "HDC decorative" to
  "specific bundle-of-random-vectors-for-set-membership-routing is
  equivalent to set-cosine"
- The RBS-HDC instrument shape (A-N cascade composition) is what we've been
  building; that hasn't changed and isn't what Test A measured

Per MFO §VII.6.20 epistemic ceiling: form-iso between RBS-HDC and our
implementation is form-iso. The implementation of one op being swappable for
another with equivalent results doesn't collapse the form-iso to "decorative."

The cathedral's framing was wrong; the cathedral itself is unchanged.

---

*Correction lodged 2026-05-26 per user framework reading. The Test A commit
(`aa007d7a`) stands as historical record; this addendum is the canonical
framing for going-forward references to Finding 70.*
