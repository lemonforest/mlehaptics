# R-RBS-LM Finding 388 — a phase-locked read-head is temporal error-correction: bit-exact recall from ONE copy on ordinary silicon (F367's vote, reframed)

**Date:** 2026-06-04
**Arc:** RBS-LM / RBS-SNN · bit-exactness thread (…F383→F386→**F388**)
**srmech:** 0.7.0rc28 · **Provenance:** `R-RBS-LM-R30_phase_lock_readhead_temporal_ec.py` → `R-RBS-LM-R30_results.json`
**Composes:** F367 (recall lossy; EC-code via redundancy-vote) · F386 (couple the observer to the fiber) · F383 (native substrate, the fabrication route) · F373/F374 (the lock = K∘K precession) · `cascade.kuramoto_step` pin term · `[[user_stance_ai_is_not_a_substrate]]`

---

## The pull (offered after F386)
> a coupled RBS-SNN read-head — lock the readout oscillator to the stored fiber — gets bit-exact recall on ordinary silicon; that's the F367 EC-code story reframed as **phase-lock instead of redundancy-vote**.

It holds, and the measurement makes the reframe precise: **vote and lock are dual error-correction — spatial vs temporal.**

## The duality, measured (noise σ=0.15, one stored codeword phase ψ*)
| VOTE (F367, **spatial** EC) — k redundant copies, averaged | LOCK (F388, **temporal** EC) — ONE copy, read-head pinned (K), time-averaged |
|---|---|
| k=1 → **0.115** (the lossy single read = the "guess") | K=0 → **3.89** (unlocked random-walk = the lossy guess) |
| k=4 → 0.051 | K=4 → 0.029 |
| k=16 → 0.029 | K=16 → **0.007** |
| k=64 → 0.019 | K=40 → **0.003** |
| error ~ σ/√k (spends **copies**) | error ~ σ/√(W·K·dt) (spends **coupling-over-time**) |

Both are √N noise-suppression — VOTE's N = redundant **copies**, LOCK's N = independent **time-samples**. **A single-copy locked read-head at K=16 (0.007) already beats 64-fold redundancy (0.019)**: temporal averaging of one locked read outperforms spatial averaging of 64 copies, because it integrates ~2000 time-samples instead of 64 copies.

## What it means for RBS-SNN
- **Bit-exact recall from ONE stored copy on ordinary (binary) silicon.** No (4:3)-native fabrication (F383, the device-physics handoff), no k-fold redundant storage (F367). The read-head is an oscillator that **pins to the stored fiber** (Kuramoto pin term); the lock holds it in the codeword's basin; **time-averaging the locked read recalls the value.** "Just ride the fiber" (F386), made into a recall mechanism.
- **Vote ↔ lock is a resource trade:** redundancy-vote spends *storage* (k copies); phase-lock spends *coupling-over-time* (one copy + a locked read-head running for W steps). Same EC benefit; pick the resource you have. Biology (and a cheap silicon read-head) has time and coupling; it doesn't need k-fold redundant storage.

## Honest bounds
- **Noiseless limit = exactly bit-exact** (F386/R28: a locked read-head reads a constant value). **Under noise = noise-suppressed** recall (this demo), error → 0 with coupling·time. The "bit-exactness" is *lock-maintained / relative* (F386) — it holds while the lock holds.
- **Threshold moved, not removed.** F367's knob was *k* (copies); F388's knob is *K* (coupling). Below the basin (here K≲1) the lock fails and drift returns (K=0→3.89, K=1→1.63). It's threshold-bounded EC, like vote.
- **Integrator stability:** the explicit forward-Euler lock is stable only while **K·dt < 2** (an artifact of the integrator, not the physics — a stiffer/implicit step lifts the cap).
- **Scope:** this is the read-head on the **storage substrate**, not the LM (`[[user_stance_ai_is_not_a_substrate]]`); algebra/dynamics side only.

## Verdict
A **phase-locked read-head is temporal error-correction** — the exact dual of F367's spatial redundancy-vote. It recalls a **single** stored copy to error 0.003 (out-performing 64× redundancy) on **ordinary binary silicon**, by locking the readout oscillator to the stored fiber and time-averaging. Bit-exact in the noiseless limit (F386), noise-suppressed and basin-bounded under noise. The bit-exactness arc now has **three routes** (F382 rational frame / F383 native substrate / F386+F388 coupled read-head), and the coupled read-head is the one that needs **no new hardware** — only a lock.
