# Round 41.A — ℓ=7 future-data test: turnkey pre-registration (PARKED, no result)

**Dispatched** 2026-05-26 on the rolling draft PR #690 (open-queue item: "ℓ=7 future-data test"). This item explicitly *names a resolving event* and is **not dispatchable today** — the data does not exist. The honest closing is a **turnkey, tamper-proof pre-registration**: fix the test in advance so it runs the moment CMB-S4 / LiteBIRD per-ℓ data lands. **No result is computed; the verdict is PARKED.** Generating code: [`verify_round41_ell7_preregistration_parked.py`](verify_round41_ell7_preregistration_parked.py) (emits the pre-registration record only).

## Background (Round 10.A / §11.9.6a)
The framework's `{1+3+7}` Hurwitz **algebra identity is preserved**, but its *projection* onto CMB TT low-ℓ multipoles **lost ℓ=7**: Round 10.A tested ℓ=7 on Spike #190's attested SMICA per-ℓ data and found ℓ=7 ranks **#5/7** in ℓ=2–8 (outranked by non-Mersenne ℓ=5/4/2) — no ℓ=7-specific signature. The per-ℓ projection claim was **withdrawn**. This pre-registration names the resolving event and fixes the re-test in advance (no post-hoc tuning).

## Pre-registered protocol (fixed in advance)
- **Data:** future per-ℓ TT `C_ℓ` from a higher-precision / independent map — **CMB-S4** (forecast 2030s) and/or **LiteBIRD** (~2028); FITS → HEALPix `anafast`, the **same pipeline as Spike #190 (SMICA) / #192 (NILC)**.
- **Range:** ℓ = 2–8 (7 multipoles; the Round 10.A comparison set).
- **Statistic:** the Round 10.A per-ℓ concentration metric (`C_ℓ` vs smooth ΛCDM expectation), ranked over ℓ=2–8.
- **Null:** no ℓ=7 preference (rank ~ uniform `U{1..7}`).
- **Decision rule (all three required to *re-open* the withdrawn claim):** (a) ℓ=7 ranks **#1** of 7; (b) exceeds significance after **Bonferroni / look-elsewhere** over `n_tested=7` (`α_corr = 0.05/7 ≈ 0.00714`); (c) cross-confirms across **≥2 independent component-separation methods** (Spike #190/#192 discipline).
- **Outcome if not met:** the per-ℓ ℓ=7 claim **remains withdrawn**; the `{1+3+7}` algebra identity is unaffected either way (only its multipole projection is at stake).

## Verdict
🅿️ **PARKED — pre-registered, no result.** The honest closing of a not-dispatchable-today item: the future test is now turnkey and tamper-proof (statistic / null / threshold / cross-confirmation fixed in advance), without fabricating a finding. The Round 10.A withdrawal stands. **HONEST SCOPE:** this is a *pre-registration*, not a result; no bit-exact claim beyond the fixed protocol parameters; no new stance (nothing to bless); framework reading only.

Lands on rolling **PR #690** (Round 41.A); unsolved-maths §11.9.34. CMB-S4 science book (arXiv:1610.02743); LiteBIRD (arXiv:2202.02773).
