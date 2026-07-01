# F970 — **the srmech shadow/ξ operator IS the grounded "does it close" detector, and the recall trichotomy (F945) is isomorphic to the modular / mock / zero trichotomy** — but the recall→q-series *bridge* is the honest open piece (not fabricated, per F969). Testing F968's claim ("is the phrase-that-won't-stop a mock theta?"): srmech's `harmonic_maass` decomposes a harmonic Maass form `f = f⁺ (mock/holomorphic) + f⁻ (non-holomorphic)`, and the **shadow** = `ξ(f)` is **zero iff the form is modular (closes)** and **nonzero iff it is genuinely mock (does not close — needs the shadow completion)** (Bruinier–Funke). Grounded: Ramanujan's mock `f(q)` is **weight-½, `is_exact=False`, shadow g₃ nonzero** (5 coefficients) → does not close alone. So there IS a real "does it close" detector, and the F945 collapse-margin trichotomy is **the same three-way shape**.

**Date:** 2026-06-29 · **srmech:** 0.9.0rc97 · **Branch:** `research/rbs-lm-rolling-2` (PR #687) · **Probe:** `R-RBS-LM-FINDING_970_*.py` · **Composes:** F968 (mock=fractal-that-doesn't-close, shadow=forcing), F969 (the null + the no-spurious-bridge discipline), F945 (the coherence trichotomy), F934 (dispatch closed-vs-OPEN), `[[feedback_dont_pre_commit_spike_query_operators]]`, `[[user_stance_framework_hands_the_next_question_to_the_expert]]` · **User direction (2026-06-29):** "let's test it next" (F968's real claim: is the phrase-that-won't-stop a mock theta uncompleted by its shadow?).

## Grounded (rc97, exact-rational)
```
mock f = MockQSeries.eulerian_f(): kind=eulerian_f, is_exact=False, weight 1/2
harmonic_maass(f, shadow=g3): shadow_q_series nonzero count = 5  -> shadow NONZERO
   => the mock form does NOT close alone; it needs the shadow completion (= a harmonic Maass form, which closes)
detector: shadow = xi(f); shadow == 0 <=> modular (closes); shadow != 0 <=> mock (does not close)
```

## The isomorphism (the reading)
| recall (F945) | modular-forms (F968/F970) | ξ-shadow |
|---|---|---|
| **COHERENT** — the now collapses to one next | **modular** — the form transforms cleanly (closes) | shadow **= 0** |
| **BRANCH** — the now won't collapse without more forcing | **mock** — almost modular, needs a completion (doesn't close alone) | shadow **≠ 0** |
| **STOP** — nothing above the floor | **zero / no form** — no structure | (trivial) |
The three verdicts are the three modular states. **BRANCH ↔ mock is the load-bearing match:** a mock modular form is *almost* self-similar (the fractal, F962/F963) but carries an anomaly that prevents clean closure — precisely a "now" that is poised between valid continuations and cannot resolve without the shadow (more forcing / more context). The shadow is what would complete it (close the beat).

## Why this is a real result — and where the discipline draws the line
- **Real:** srmech genuinely *has* the "does it close" detector (the ξ-shadow), and it separates mock (doesn't close, shadow≠0) from modular (closes, shadow=0), grounded on Ramanujan's f. So F968's structure is not just analogy — the closure/anomaly is a computable srmech quantity.
- **The line (F969 lesson):** to *measure a correlation* "BRANCH-contexts have larger mock-anomaly than COHERENT-contexts," one must map a recall context to a specific q-series and take its shadow. **That bridge is not fabricated here** — inventing it is exactly the spurious operationalization F969 caught (the key-flip). Building a *principled* recall→q-series bridge (one that isn't an arbitrary encoding) is the genuine open question, handed to the expert / a future build.
- **Adjacent grounded structure:** this is the same shape as F934's `dispatch.infer` **closed-form vs honest-OPEN** (reducible = closes = COHERENT; OPEN = the sustained/unresolved regime = BRANCH). Two srmech detectors (the ξ-shadow and the dispatch verdict) carry the same closes/doesn't-close/empty trichotomy.

## Honest scope
Grounded: the ξ-shadow detector separates mock (Ramanujan f, shadow≠0, doesn't close) from modular (shadow=0, closes), exact-rational in srmech. The **isomorphism** (COHERENT/BRANCH/STOP ↔ modular/mock/zero) is a **reading** — a structural match of two three-way "does-it-close" shapes, not a measured recall correlation. The recall→q-series **bridge is deliberately not fabricated** (F969); the falsifiable correlation awaits a principled bridge. The modular-forms claims (ξ, Bruinier–Funke) are standard and cited in the srmech docstring — verify with a modular-forms source (MPM).

## Verdict / next
**Grounded + read:** srmech's ξ-shadow is the real "does it close" detector (mock = shadow≠0 = doesn't close; modular = shadow=0 = closes), and the F945 recall trichotomy is isomorphic to the modular/mock/zero shape — BRANCH ↔ mock (the fractal that needs a shadow to close) is the load-bearing match. **The honest open question (handed forward):** a *principled* recall-context → q-series bridge, so "does BRANCH-wander carry a larger mock-anomaly than COHERENT" becomes a *measured* correlation rather than an invented mapping. Until then the mock/shadow reading is a validated structural lens (F968) with a grounded detector (F970), not a fabricated recall metric (F969).
