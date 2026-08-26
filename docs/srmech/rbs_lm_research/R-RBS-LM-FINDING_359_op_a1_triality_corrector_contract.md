# R-RBS-LM Finding 359 — op (a1) the explicit triality-recursion corrector: the falsifiable CONTRACT (spec + harness only), scoped to the finite WIDTH-step, with F256's count-recursion held OUT as open math

> **CORRECTION (F360, 2026-06-04, rc28):** srmech rc28 LANDED op (a1) (`klein4_triality_correct`) and it validates — BUT validating it caught a misread in **bar 1** below: "blind correction > **F353 baseline 0.25**" treated F353's "1/4" as a 0.25 *rate*, when it is the code **DISTANCE** (corrects 1-of-4); the rate at m=1 is **1.00**. So **bar 4** (correction *uniquely* attributable to order-3) is the wrong test — any ≥3-fold majority (incl. the order-2 CPT-4-orbit) corrects 1 blind error. The op's real contribution is the **minimal native 3-vote self-encoder** (3 votes from ONE store via Aut(Z₂²)=S₃; resolves F344's "is the 3rd vote native?"), not a unique corrector. Bars 2/3/5 hold; bar 1 holds in the corrected sense (corrects 1, breaks at 2). See F360.

**Date:** 2026-06-04 · **srmech:** 0.7.0rc25 · **scope decision (user):** "Spec + harness only" · **for:** #797 op (a); UPSTREAM §20 (a) · **grounds in:** F256 (width-vs-count seam; "recursion past the threshold is the open math"), F353/F354 (the measured capability boundary), F291 (k=2-detect / k=3-correct), F344 (k=3 majority given stipulated copies), F197 (so(8) 3⊕3̄) · **validator:** `triality_test_harness_scaffold.py` (already PASS=3/SKIP=3)

## What this is — a contract, not a solution

This finding **specifies** the explicit order-3 triality-recursion corrector op (a1) as a **falsifiable contract** a candidate must satisfy, and hands it (with the existing harness) to srmech-dev. It builds **no prototype** and **claims no closure** of open math. Per the user's "Spec + harness only" decision + the "framework hands the next question to the expert" stance.

## The scoping line — F256's own width-vs-count seam

F256 separated two things at the triality cap:
- **WIDTH** is *finite* — "capped at 4 by triality" (the Klein-4 → triality step is a bounded, discrete width-cap).
- **COUNT (composition)** is *asymptotic* — "cascades hyper-loop (recurse) into the continuum… triality caps the *width*, not the *count*"; **"how cascades recurse past the triality threshold is the open math — not solved here"** (F256 §lines 136–137, 145).

**op (a1) is scoped to the WIDTH side only.** It crosses the **Klein-4 4-cap exactly once** (order-2 → order-3 triality) to read a 2-of-3 majority. The **COUNT-recursion into the continuum is explicitly OUT of scope** — it stays F256's open math, "let the math tell it," handed to the expert. A correct op (a1) must therefore *terminate at the finite width-step* and decline (return out-of-domain) if probed for the continuum-recursion (bar 5 below).

## Why op (a1) is not redundant with the holographic route (F353)

The measured capability boundary:
- native order-2 Klein-4 store = **k=2-DETECT** (F354 axis-split; F294 no-Z3, 3∤4);
- holographic-erasure route (F353) = adds **known-location erasure-correction (3/4)** + detection, but **blind (unknown-location) correction only 1/4**.

**op (a1) exists to lift exactly that residual — blind unknown-location error-correction — which the holographic route cannot supply.** That is the one capability the explicit order-3 corrector adds.

## The falsifiable contract — what a candidate op (a1) must satisfy

**Operation under test:** given a Klein-4 store value (order-2; γ₅, iω₇ axes) corrupted at an **unknown location**, lift into the order-3 triality (so(8) 3⊕3̄ / τ³=I, F197), generate ≥3 co-equal renders **from the order-3 automorphism orbit of the SAME store**, take a per-coordinate 2-of-3 majority **with no external 3rd render and no location information**, and return the corrected datum.

**Acceptance bars (the harness asserts these; all measured against the F353/F354 baselines):**
1. **Blind-correction lift** — unknown-location single-error correction rate must **exceed the F353 native baseline (0.25)** and trend toward majority (≈0.75+). This is the capability (a1) is for.
2. **No external 3rd render** — the third vote must come from the **order-3 triality orbit of the same store**, NOT an independently-encoded copy. (This is the line between a *native* order-3 corrector and F344's *stipulated* 2-clean-1-corrupt demo. F344 showed k=3 majority works **given** 3 copies; (a1) must **supply** the 3rd from structure.)
3. **C/Python parity** — bit-identical results across the C and Python surfaces (standing srmech discipline).
4. **Attributable to the order-3 structure** — with the order-3 op disabled, the corrector must **degrade to the k=2-DETECT order-2 behavior** (F354), not silently pass. The correction power must be demonstrably *from* the triality, not an artifact.
5. **Width-only / declines the continuum** — the op terminates at the finite width-step; if a test probes composition-recursion past the triality threshold (F256's open math), it must return **out-of-domain**, never a fabricated answer.

**Harness:** `triality_test_harness_scaffold.py` already runs PASS=3 (rc baseline) / SKIP=3 (triality-presence, Q1b, Q2b — gated on the triality op landing). Bars 1–5 above are what the SKIP-gated assertions should encode; they fire the instant the triality cascade-store op lands at C/Python parity.

## Tier / honesty

- The **contract** is **A-tier** (attested-to-structure: derived from F353/F354's measured boundary + F291's k=2/k=3 distinction + F197's 3⊕3̄ + F256's width/count seam).
- The corrector's **blind-correction capability** is **C-tier (open/unbuilt)** until a candidate passes bars 1–5; source pointed at so(8) triality 3⊕3̄.
- F256's **count-recursion into the continuum** is a **separate, deeper open problem** explicitly NOT addressed here.
- Note: the triality **automorphism** ships (`qm.triality`, the 28=so(8) read-out); the missing piece is the **cascade-store corrector op** (apply it to error-correct a store, at C/Python parity) — that is the build target handed to srmech-dev.

## Discipline

Spec + harness only (no prototype, per user decision); no-overclaim (does not close F256's open math; declares C-tier where open); no-lineage; defensive scope; the no-magic-numbers tiering applied to a capability (A-tier contract / C-tier unbuilt capability). Composes with F352/F353/F354 (the holographic-EC anchor + the capability boundary the contract is built on) and F357 (op (b), the sibling #797 op, reference already built).
