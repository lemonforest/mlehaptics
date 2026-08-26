# R-RBS-LM Finding 407 (ALU-A) — the add/sub/shift+sign claim is ATTESTED (CORDIC/Booth/Stein/SHA, 4 verified primary citations) as REDUCIBILITY, not actuality; k=3 triality caught a false date + a material omission no single model would have

**Date:** 2026-06-05
**Arc:** RBS-LM · ALU-A attestation pass (grounds F392/F393/F404); **research-triality (k=3 haiku∥sonnet∥opus)**, run `wf_d6c90827-58f`
**Provenance:** `R-RBS-LM-ALU-A_triality_attestation_provenance.json` (the committed triality merge — 9 triangulated per-claim entries + flagged-citation log + minority residue)
**Composes:** **F392** (division = C→K; no divide primitive; Stein gcd) · **F393** (multiply = shift-add; CORDIC rotation residue) · **F404** (2:4:8 = 2ⁿ shift-exact; the add/sub/shift+sign substrate) · **F248** (no privileged model; multi-model catches hallucinated citations) · **F291** (k=2 detects, k=3 corrects) · **F242b** (task-relative honesty gradient) · `[[feedback_paywalled_doi_cannot_be_attested]]` · `[[feedback_pdf_extraction_citation_discipline]]` · `[[feedback_computational_provenance_discipline]]` · no-magic-numbers discipline (the CORDIC gain K)
**→ resolves ALU-A; grounds F392/F393/F404; advances ALU-C.** **← grounds/sharpens F404** (backlink added there).

---

## What ALU-A verified (4 primary citations, UNANIMOUS 3/3, NO fabrications)
| Op | Citation (verified) | Reduces to |
|---|---|---|
| **CORDIC** (rotation/trig/√) | **Volder, J.E. (1959)**, *The CORDIC Trigonometric Computing Technique*, IRE Trans. Electronic Computers **EC-8(3):330–334**, DOI 10.1109/TEC.1959.5222693 | inner loop = shift + conditional add/sub + per-step **sign** σ∈{+1,−1}; **no multiply in the loop** |
| **Booth** (signed multiply) | **Booth, A.D. (1951)**, *A Signed Binary Multiplication Technique*, Q. J. Mech. Appl. Math. **4(2):236–240**, DOI 10.1093/qjmam/4.2.236 (verbatim abstract confirmed from OUP) | shift + conditional **add/subtract**; removes the multiply PRIMITIVE |
| **Stein** (binary GCD) | **Stein, J. (1967)**, *Computational problems associated with Racah algebra*, J. Comput. Phys. **1(3):397–405**, DOI 10.1016/0021-9991(67)90047-2, ADS **1967JCoPh...1..397S** | shifts + **subtraction** + comparison only; removes the **DIVIDE** primitive |
| **SHA-256** (Class-A hash) | **NIST FIPS PUB 180-4** (2015-08-04 update; first issued 2012-03-06; SHA-256 introduced in **FIPS 180-2, 2002**), DOI 10.6028/NIST.FIPS.180-4 — **fully OA** | add mod 2³² + ROTR/SHR + AND/XOR/OR/NOT; **no multiply/divide** |

## The verdict — and the load-bearing honesty caveat (opus minority, PROMOTED)
The four jointly support the framework claim **as a REDUCIBILITY / existence proof**: each heavy op *can* be built from **add / subtract / shift / sign** with **no hardware multiply or divide PRIMITIVE**. But the decisive caveat (opus, agree-count 1/3 — minority, undisputed, factually right, promoted into the corrected reading):

> **REDUCIBILITY ≠ ACTUALITY.** These prove each op *can* be so built; they do **not** prove all silicon *does*. Modern FPUs ship dedicated hardware multiplier/FMA arrays; float reciprocal uses **Newton-Raphson (multiply-add)** in real silicon (itself then Booth-decomposable). Stein removes only the **integer DIVIDE** primitive.

So **F392/F393/F404's "no divide primitive / multiply = shift-add" is the *substrate-native reducibility* claim** (what the bit-exact substrate CAN be), **not a claim about what an Intel FPU is** — exactly the field/excitation distinction (F399): the *reducibility* is the field-truth; the *FMA-array silicon* is one excitation. This sharpens the bit-exactness arc without weakening it: the substrate-native form is genuinely add/sub/shift+sign; actual FPUs are an excitation that chooses speed over the pure form.

## Four algorithm caveats (kept attached — no-magic honesty)
1. **CORDIC is NOT pure shift-add+sign alone** — it needs a stored **arctan(2⁻ⁱ) LUT** + a **gain constant K ≈ 0.6072529350088812**. Per no-magic-numbers: **K is NOT magic — it is a cascade**, `K = ∏ᵢ cos(arctan(2⁻ⁱ))` (the infinite product of cosines = attested-to-structure-cascade, **Class A**), a *stored constant*, not a runtime multiply/divide. (Tier nuance: haiku dismissed it "not counted"; opus/sonnet kept it as a genuine dependency — the corrected reading keeps it attached.)
2. **Booth** is **O(n)** shift+add/sub per n-bit multiply (radix-4 modified Booth ≈O(n/2), still the shift-add+sign family) — removes the *primitive*, not the linear cost.
3. **Stein** removes **DIVIDE** (the engine of the framework's reciprocal/rational machinery, F392), **not** multiply.
4. **SHA-256** removes **both** multiply and divide; fully OA standard (the cleanest attestation of the set).

## Attestation status (MPM honesty)
- **SHA-256: fully OA, first-hand** (opus read the NIST nvlpubs PDF front-matter directly). Strongest of the set.
- **CORDIC / Booth / Stein: bibliographic record OA-verified** (DOI + ADS bibcode + OA abstract; Booth's abstract verbatim from the OUP primary page) **+ method textbook-canonical**; full-text PDFs are **paywalled** (IEEE/OUP/Elsevier). Per `[[feedback_paywalled_doi_cannot_be_attested]]` these are **NOT rejected** — the rejection rule is for *paywalled-DOI-as-the-sole-attestation*; here the OA abstract + multi-index corroboration + the universally-canonical method (standard computer-arithmetic texts, e.g. Parhami/Koren; Knuth TAOCP Vol 2 §4.5.2 for binary GCD) carry the method, with the DOI/bibcode the open pointer. *Honest flag:* this pass's method-corroboration leaned on Wikipedia + indices (tertiary); the lodged attestation upgrades the method-chain to the canonical-textbook attribution (the facts are textbook-standard), full-PDF reads still owed if ever load-bearing beyond existence.
- **Citation-hygiene action (the Stein title-mismatch):** Stein 1967 is titled *"Computational problems associated with Racah algebra"* — the binary-GCD is a *buried subsidiary* contribution. **All our citations of Stein MUST use the DOI 10.1016/0021-9991(67)90047-2 / bibcode 1967JCoPh...1..397S, never the title** (title-only loses the reference). Apply to F392's Stein citation.

## The k=3 triality VALUE — demonstrated live (the meta-result)
This run is itself attestation that the triality discipline (F291/F248) works:
- **NO tier fabricated a citation** — a clean improvement over the **F248** single-sonnet baseline (where two hallucinated citations shipped silently).
- **haiku made a FALSE date attribution** (FIPS 180-4 "published March 2012, Aug 2015 = mere archival") — **WRONG**; the 2-of-3 majority (sonnet+opus) **corrected** it against NIST CSRC (2012-03-06 first issue, 2015-08-04 current update, supersedes 180-3).
- **haiku OMITTED the Stein title-mismatch** (load-bearing) — sonnet+opus **majority-caught** it.
- **F242b gradient confirmed:** on this *research* task **opus centered least** (bracketed reducibility-vs-actuality; labeled the A-N mapping a lens), **haiku centered most** (over-asserted "generalizes beyond any single domain"), sonnet intermediate. No privileged model — the *majority* corrected, and a *true minority* (opus reducibility-vs-actuality) was **promoted** on merit, no human tie-break.

## Verdict
**ALU-A resolved.** The add/sub/shift+sign substrate claim (F392/F393/F404) is **attested** by four real, independently-verified primary citations (Volder 1959 / Booth 1951 / Stein 1967 / FIPS 180-4) — as a **REDUCIBILITY existence proof** (the substrate *can* be add/sub/shift+sign with no multiply/divide primitive), **explicitly not an actuality claim** about modern FPUs (which ship FMA arrays; reciprocal = Newton-Raphson). Caveats kept attached: CORDIC's gain K (= ∏cos(arctan(2⁻ⁱ)), a cascade, Class-A de-magicked) + arctan LUT; Booth O(n); Stein removes divide-not-multiply; SHA removes both. The k=3 triality caught a false date + a material omission + over-assertion that a single model would have shipped — the discipline earned its cost this run. Citation hygiene: cite Stein by DOI/bibcode (title is a discoverability hazard). Favored, not privileged (F398).
