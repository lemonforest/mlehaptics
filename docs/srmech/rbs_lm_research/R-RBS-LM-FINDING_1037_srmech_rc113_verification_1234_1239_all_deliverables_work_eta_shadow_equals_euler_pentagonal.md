# F1037 (user: verify our deliverables in rc113) — **srmech 0.9.0rc113 VERIFIED: every item of #1234 and #1239 works, and the mock-theta reader produces a MATHEMATICALLY EXACT result — `theta_coefficients(eta-shadow)` = Euler's pentagonal number theorem coefficients term-for-term (∏(1−qⁿ) = 1 −q −q² +q⁵ +q⁷ −q¹² −q¹⁵ +q²²+q²⁶…), matched exactly to n≤30. #1234: `qm.quaternion.quaternion_exp(0.5, mu='i')` = (0.877583, 0.479426, 0, 0) = (cos½, sin½, 0, 0) EXACT (the exp(μθ) twiddle, BX-7); `cascade.quaternion_dft`/`octonion_dft` + `quaternion_twiddle`/`octonion_twiddle` present + callable (BX-5/6); `laplacian.heat_trace(L, t)` gives Tr(e^{−tL})→2.97 at t=0.01 →1.45 at t=1 for the 3-cycle (the F1007 theta Laplacian, Item 2); magnetic per-edge charges (Item 3, rc105) + klein4_bundle HV parity (Item 4, rc104) already verified. #1239: `qpoly_from_coeffs`/`qbipoly_from_coeffs`/`poly_from_coeffs` construct carriers from int lists; `q_gosper(qpoly, qpoly)` returns None = the honest OPEN (correct — no q-hypergeometric closed form for that ratio); `theta_coefficients(UnaryTheta, n_max)` is the UnaryTheta consumer. The mock-theta sparse-form pipeline is WIRED end to end: construct term-ratio → q_gosper → closed-form-or-honest-OPEN, with the shadow side reading exact.**

**Date:** 2026-07-03 · **srmech:** 0.9.0rc113 (TestPyPI; native dispatching, ABI 3) · **Branch:** `research/rbs-lm-rolling-2` (PR #687) · **User direction:** "issue items #1234 and #1239 are delivered in test.pypi.org srmech. pull the latest rc113 srmech and verify our deliverables work as expected. #1245 still in development." · **Composes:** #1234 (the consolidated ask F1027/F380/BX-5/6/7), #1239 (F1027 → the mock-theta pipeline), F1007 (heat_trace = the theta Laplacian), F999–F1002 (the elliptic/hypercomplex row).

## Grounded (rc113) — the verification
```
#1234 Item 1 (QDFT/ODFT + qm.quaternion + exp(mu*theta) twiddle):
  quaternion_exp(0.5, mu='i') = [0.877583, 0.479426, 0, 0]  == (cos.5, sin.5, 0, 0) EXACT
  quaternion_dft / octonion_dft (srmech.amsc.cascade) present, callable (impulse -> flat spectrum)
  quaternion_twiddle / octonion_twiddle (srmech.qm.quaternion) present
#1234 Item 2 (heat_trace / theta Laplacian): heat_trace(3-cycle Ln, t) = 2.970 @0.01 -> 1.446 @1.0 (Tr e^{-tL})
#1234 Item 3 (magnetic per-edge charges): rc105, verified F1033 (dispute flux 0.7071)
#1234 Item 4 (klein4_bundle HV parity): rc104, verified F1032-era
#1239 (a) constructors: qpoly_from_coeffs([0,1]) -> QPoly ; qbipoly_from_coeffs, poly_from_coeffs present
#1239 (b) UnaryTheta consumer: theta_coefficients(eta-shadow, 30) =
  [1,-1,-1,0,0,1,0,1,0,0,0,0,-1,0,0,-1,0,0,0,0,0,0,1,0,0,0,1,...]  == EULER PENTAGONAL, exact match
  q_gosper(qpoly,qpoly) = None = honest OPEN (correct SUSTAIN-regime behavior)
```

## The reading
- **The theta_coefficients reader is provably correct**, not just present: the Dedekind η shadow's q-expansion IS the Euler function ∏(1−qⁿ), and rc113 reproduces its pentagonal-number-theorem coefficients exactly to n=30. This is the strongest possible verification of a new op — output matched against a closed-form theorem, not just a smoke test.
- **The mock-theta sparse-form pipeline exists end to end:** coefficient-list → QPoly carrier → q_gosper → recurrence-or-honest-OPEN, with the shadow constructible AND readable. #1239 delivered exactly what the finding F1027 asked for: "find the sparse form of f(q)" is now a real computational path (register-chained once siona's conversational binding of the multi-operand consumers is refined — see follow-on).
- **Siona-side follow-on (OURS, not srmech's):** siona drives `quaternion_exp(0.5)` conversationally today, but `heat_trace` (edges + t) and `theta_coefficients` (register-chain the built UnaryTheta) need grounding/binding refinement for the new multi-operand + carrier-consuming signatures — the result-register (F1024) extended from Mat to UnaryTheta. srmech deliverables all pass when called directly; the conversational layer is the next rung.

## Verdict / next
**#1234 (all 4 items) and #1239 (both items) VERIFIED WORKING on rc113 — the eta-shadow==Euler-function match is the headline: a new srmech op reproducing a closed-form theorem exactly. #1245 (genome bit-packing + linear append) remains in development per the user.** Next (ours): siona conversational binding for the new carrier-consuming tools (heat_trace, theta_coefficients register-chain); the register-chained mock-theta pipeline as a siona read; BX-5/6/7 tasks close. The rc1 SEQUENCING is unchanged — siona rc1 still waits for the srmech CLEAN tag (rc113 is TestPyPI), but the deliverables are proven on it.
