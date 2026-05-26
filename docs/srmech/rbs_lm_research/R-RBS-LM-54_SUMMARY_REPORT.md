# R-RBS-LM-54 SUMMARY REPORT — Rosetta Stone Layer (Golden Path)

**Status:** CLOSED (54a-e shipped; Golden Path roadmap established)
**Branch:** `research/rbs-lm-rolling-2`
**Date:** 2026-05-26
**Arc partition:** 54a → 54b → 54c → 54d → 54e

---

## §1 What we set out to ask

After R-RBS-LM-53 established that **all 14 corpora across religious /
secular sub-genres / multiple translations share a single form-category**
(coherence ratio 1.57), the natural next question:

> **Can we build a single shared translation layer ("Rosetta Stone")
> with multiple domain-specific kernels bound to it?**

Per user direction (verbatim):

> "we can also try to learn if cross domain knowledge finding will mean
> that all we need to do is bind two different domain translation
> kernels to the same translation layer. This looks like the Golden
> path."

And the architectural clarification that came mid-arc (also verbatim):

> "This reminds me exactly of our ephemerides-spectral ITN tube tool.
> it's one operation to find ITN, and a totally different cascade to
> ride the itn highway."

Two cascades, not one:
- **Find-cascade** — locate the form-correspondence between domains
- **Ride-cascade** — actually translate (or compute) along that
  correspondence once located

Plus the disambiguator: a **DOMAIN anchor** to pick the correct
ride-kernel when find-cascade lands in a form-family with multiple
substrate-distinct members.

---

## §2 What each partition tested + found

### R-RBS-LM-54a — Rosetta Stone *precondition*

**Question:** Is there a vocab-independent structural form that
can be compared across corpora at all?

**Method:** Compare eigenvalue spectra (no vocabulary at all —
pure spectrum shape) across 6 corpora in 4 families.

**Result:** KS-distance coherence ratio **1.40** — same-family
spectra cluster; cross-family widens. Precondition
**WEAKLY-TO-MODERATELY SUPPORTED** — vocab-independent form
exists and is measurable.

**Verdict:** A Rosetta Stone is at least worth trying to build.

---

### R-RBS-LM-54b — Rank-matching attempt (honest negative)

**Question:** If eigenvalue spectra are similar, can we just match
eigenvectors by rank? (rank-1 ↔ rank-1, rank-2 ↔ rank-2, …)

**Method:** For each rank, intersect top-21 tokens between anchor
corpus and each other corpus.

**Result:** Same-family token overlap **2.3/21**; cross-family
**1.9/21** — ratio **1.21**. Honest negative: rank-matching is
NOT the right alignment operation. The eigenvalues' *ordering*
is not preserved across corpora because lexical density varies.

**Verdict (user-supplied reframe):** "It's one operation to find
ITN, and a totally different cascade to ride." 54b conflated find
and ride. The premise was wrong, not just the result.

---

### R-RBS-LM-54c — Find-cascade by content similarity

**Question:** Drop the rank assumption. For each anchor eigvec,
*search* across the target corpus for the best content-similarity
match. Does THAT work?

**Method:** Find-cascade alignment via cosine over content-vectors
(token-frequency-weighted top-K eigenvector tokens).

**Result:** Same-family alignment-sim **+0.107**; cross-family
**+0.094** — ratio **1.14**. Find-cascade works, but
**weakly** in raw magnitude. Critically: rank-correlation between
matched ranks is only **0.42** — confirming 54b's rank-matching
premise was incorrect; the *best* matches don't preserve rank
order.

**Top aligned pairs were semantically real:**
- KJV-NT rank-3 (god/jesus/man) ↔ Quran rank-3 (god/lord/unto) sim=+0.33
- KJV-NT ↔ Tanakh-proxy: spirit/holy/heaven word-cluster
- Plato ↔ Origin: science/structure/forms vs philosophy/state/man

**Verdict:** Find-cascade is a real operation; alignment is by
**semantic content**, not by rank.

---

### R-RBS-LM-54d — Ride-cascade with explicit alignment

**Question:** Once find-cascade has located the alignment, does
the *ride* (actual cross-domain translation) work?

**Method:** Build ride-cascade using the 54c alignment table.
For each test-token in anchor corpus, traverse its top eigvec,
find aligned eigvec in target corpus, predict tokens. Compare to
rank-based naive baseline.

**Result:** Find→ride ride-quality **+52% over rank-baseline**.
The find/ride architectural split delivers real signal.

**But also:** Cross-family ride-quality is **as good as
same-family**. (KJV anchor rides about as well into Plato or
Frankenstein as into Quran.) Find-cascade locates the
form-family but does NOT discriminate further within it.

**Verdict:** Find→ride architecture WORKS structurally;
**DOMAIN anchor empirically required** to disambiguate the
ride-kernel within a form-family.

---

### R-RBS-LM-54e — Cross-substrate-family boundary test

**Question:** Does find-cascade respect substrate-family
boundaries at all? Does it ever say "this corpus is in a
different family, don't ride it"?

**Method:** KJV-NT as anchor; align to Quran (same family),
Bhagavad (eastern religious), Origin/Plato/Frankenstein
(secular sub-genres).

**Result:**
| comparison | avg sim |
|---|---|
| same-family (Quran) | +0.1055 |
| cross-family avg | +0.0836 |
| religious super-family | +0.0990 |
| secular super-family | +0.0806 |

Ratios: same/cross **1.26**; religious/secular **1.23**.

**Top aligned pairs (cross-family but real):**
- KJV ↔ Plato rank-9↔1: "one/another/man/come" vs "one/state/man" sim=+0.29
- KJV ↔ Frankenstein rank-3↔2: "god/jesus/man" vs "him/one/his/man" sim=+0.29

**Verdict:** WEAK substrate-family boundary at the find-cascade
level. Find-cascade alone is **not sufficient** to refuse a wrong
ride-kernel. DOMAIN anchor (or some other gating signal) **is the
selection mechanism**, not the find-cascade's intrinsic strength.

---

## §3 Golden Path architecture (now empirically grounded)

```
                  ┌──────────────────────────────┐
                  │   SHARED TRANSLATION LAYER   │
                  │  (universal form-skeleton —  │
                  │   eigvec content, no vocab)  │
                  └──────────────┬───────────────┘
                                 │
        ┌────────────────────────┼───────────────────────┐
        │                        │                       │
        ▼                        ▼                       ▼
   FIND-CASCADE            DOMAIN ANCHOR            RIDE-CASCADE
  (content-sim         (external substrate-          (project anchor
   alignment over       content selector;             form along
   target eigvec        chooses WHICH                 aligned eigvec
   table — locates      domain kernel to             into target
   form-family)         load)                         vocabulary)
        │                        │                       │
        └────────────────────────┼───────────────────────┘
                                 │
                                 ▼
                       BOUND DOMAIN KERNEL k_i
                       (one per substrate-family;
                       carries vocabulary + ride
                       parameters for that domain)
```

**Three operations, distinct:**
1. **Find** — content-similarity alignment (54c); locates form-family
2. **Disambiguate** — DOMAIN anchor (external signal — 54d/e)
3. **Ride** — project along aligned eigvecs into target vocabulary (54d)

**Bound kernel = thin object:** vocabulary + ride parameters for a
substrate-family. Multiple kernels bind to ONE translation layer.

---

## §4 The two epistemic findings worth shipping

### Finding 51: Find-cascade by content similarity ≠ rank-matching

Eigenvalue rank-ordering is NOT preserved across corpora because
lexical density varies. The right alignment operation is
**content-similarity search** over the target's full eigvec table,
NOT positional rank-matching. (54b → 54c reframe.)

### Finding 52: Find-cascade locates form-family; DOMAIN anchor selects kernel

Find-cascade alone has only **modest** substrate-family
discrimination (same/cross ratios 1.14-1.26). It can put you in the
right *neighbourhood* of form-families but cannot distinguish
KJV-style religious from Plato-style philosophy strongly enough
to refuse the wrong kernel. The architectural disambiguator is an
**external DOMAIN anchor** that selects which bound kernel to load.

This is consistent with the ITN-tube architecture: finding the tube
(find-cascade) is geometric / topological; choosing which highway
to actually drive on (ride-cascade) is an additional signal that
sits outside the geometry itself.

---

## §5 What we did NOT settle (honest scope)

- **Closed-loop ride.** 54d ride-cascade measures structural
  alignment quality, not literal translation correctness. Whether
  the ride actually produces *meaningful tokens* in target
  vocabulary is still an open test (queued: 54f).
- **DOMAIN anchor mechanism.** "Anchor required" is shown; the
  *form* of the anchor (small classifier? external metadata?
  hand-picked? cascade off the input itself?) is not yet built.
- **Translator-stability vs substrate-family confound.** 53f
  showed translator contributes ~50% of form-signature; 54e shows
  weak substrate-family signal. These two findings interact and
  the partition isn't fully untangled.
- **Closed-form math substrate (open).** "FFTing relationships of
  relationships that are not also relationships of words" remains
  unbuilt — this is the asymptotic-math-knowledge / pure-structure
  test the user queued and asked NOT to auto-start.

---

## §6 Roadmap (next partitions, in priority order)

| ID | Description | Premise |
|---|---|---|
| R-RBS-LM-54f | DOMAIN-anchor implementation: thin classifier on top of find-cascade output; binds to correct kernel | 54e proves it's needed |
| R-RBS-LM-54g | Closed-loop ride: emit real target-vocabulary tokens via aligned eigvec projection; measure faithfulness against held-out target | 54d only measured structural alignment |
| R-RBS-LM-55 | "Relationships of relationships" pure-structure layer (no vocab); test whether eigvec *table shape itself* (not tokens) is portable across corpora | Direct follow-up to 53h's "form is shared" finding |
| R-RBS-LM-51 | Honest scope review per MFO §VII.6.20 — form-identity provable; substrate-identity not. Captures what we can/cannot claim from this arc | Was queued before 54; now informed by 54's results |
| R-RBS-LM-49z | Rebuild Method B/C cascade primitives via srmech-native; drop bare numpy where avoidable | Catalog discipline; queued earlier |

---

## §7 Operational walkthrough (per `[[feedback_human_coherent_steps_in_reports]]`)

What you'd do, today, with the 54 finding to translate from anchor to target:

1. **Build kernels (offline).** For each substrate-family (KJV-style
   religious, Plato-style philosophy, Origin-style science, …) run
   the 54a eigvec table — Laplacian of co-occurrence graph → top-200
   eigvecs with their token-projection. Persist as bound kernel
   `k_{family}`. srmech handles via `srmech.amsc.laplacian` (Class L)
   eigvals + the cooccurrence build is plain counting (Class I + Class A).

2. **Pick anchor.** User points at corpus / prompt / fragment in
   anchor language (or substrate). Build its eigvec table the same
   way. (This is "fingerprint the form" — Class L on the input.)

3. **Find-cascade.** For each anchor eigvec, search all candidate
   kernel eigvec tables for best content-similarity match.
   Per 54c: cosine over top-K token-weighted content-vectors;
   keep best-match in each candidate kernel. (Class M HDC-similarity
   over the content vector.) srmech-native: `srmech.amsc.hdc.bundle`
   + cosine; no bare-numpy needed.

4. **DOMAIN-anchor disambiguate.** External signal (user-supplied
   genre tag, classifier output, parent-document metadata) picks
   `k_target` from the candidates. This step is what 54e shows is
   load-bearing — find-cascade alone is not sharp enough.

5. **Ride-cascade.** Project anchor eigvec onto matched eigvec in
   `k_target`; pull out token-projection in target vocabulary.
   (Class L recompose + Class M unbind.) Output: translated /
   projected token sequence.

What srmech automates: kernel build (eigvec extraction), find-cascade
(content-vector similarity), ride-cascade (projection). What stays
external: the DOMAIN anchor (intentional — the framework reading is
that this is a substrate-content selection step, not a structural
operation).

---

## §8 PR-status note

This summary closes the 54 arc. PR #687 STAYS DRAFT (per
`[[feedback_no_squash_merges]]` + project discipline). The Golden
Path is empirically mapped; specific next-partition entries (54f,
54g, 55) are queued. User has explicit veto on whether to walk the
54f → 54g path now or pause for asymptotic-math-substrate
brainstorming first.

---

*Synthesized 2026-05-26 across 54a (precondition) → 54b (honest
negative; ITN reframe) → 54c (find-cascade) → 54d (find→ride) →
54e (cross-substrate-family). All partition smokes + result JSONs
committed; commit chain `58613bc0 → fe51e85d → cc6ed5f8 → cd8f68a1
→ c550b350`.*
