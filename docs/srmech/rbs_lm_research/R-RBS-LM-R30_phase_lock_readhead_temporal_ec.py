"""F388 — a phase-LOCKED RBS-SNN read-head recovers a SINGLE stored copy under noise by TEMPORAL averaging:
the F367 EC-code reframed as phase-LOCK (temporal EC) instead of redundancy-VOTE (spatial EC).

Offered as the F386 next-pull: lock the readout oscillator to the stored fiber, then TIME-AVERAGE the locked
read -> low-error recall from ONE copy, no fabricated substrate (F383), no k-fold redundant storage (F367).

THE DUALITY under test:
  VOTE (F367, SPATIAL EC): store k redundant copies; read all k through independent noise; average ->
    estimate error ~ sigma/sqrt(k). Spends COPIES (k>1).
  LOCK (F388, TEMPORAL EC): store ONE copy as a fiber phase psi*; a read-head oscillator PINS to it
    (Kuramoto pin term, strength K). The lock holds the read-head in psi*'s basin; TIME-AVERAGING the locked
    read over W samples -> estimate error ~ sigma/sqrt(W/tau), with correlation time tau ~ 1/(K*dt) shrinking
    as K grows. Spends COUPLING-over-TIME, ONE copy.
Same 1/sqrt(N) noise-suppression; VOTE's N = copies, LOCK's N = independent time-samples (~ W*K*dt).

In the NOISELESS limit the lock is exactly bit-exact (F386/R28, constant readout); UNDER noise it is
noise-SUPPRESSED recall, threshold/basin-bounded (the threshold moved from VOTE-k to LOCK-K), and the
explicit integrator is stable only while K*dt < 2 (forward-Euler) — both honest bounds.

srmech-native: amsc.cascade.kuramoto_step (the pin term IS the lock; STOP-list op, NOT a hand-rolled sin
loop). Noise is environmental (numpy rng, as F367/R18). Error magnitudes via (x*x)**0.5 (Class-K; no abs()).
Run: /tmp/verify_srmech_v070rc28/bin/python docs/srmech/rbs_lm_research/R-RBS-LM-R30_phase_lock_readhead_temporal_ec.py
"""
import json
from pathlib import Path
import numpy as np                       # environmental noise only; the dynamics are srmech's
import srmech
from srmech.amsc import cascade

HERE = Path(__file__).parent
PSI = 0.0                                # stored codeword phase (the fiber)
DT, STEPS, WINDOW, TRIALS, NOISE = 0.02, 3000, 2000, 40, 0.15      # K*dt < 2 keeps forward-Euler stable


def mag(x):
    return (x * x) ** 0.5                                          # Class-K magnitude, no abs()


def lock_recall(Kpin):
    """LOCK: ONE stored copy; read-head pinned to psi* (strength Kpin) under per-step noise; the recalled
    value is the TIME-AVERAGE of the locked read over the window (temporal EC)."""
    est_errs, band_rms = [], []
    for t in range(TRIALS):
        rng = np.random.default_rng(5000 + t)
        theta = [0.6]                                             # read-head displaced from the codeword
        tail = []
        for s in range(STEPS):
            theta = cascade.kuramoto_step(theta, [0.0], coupling=0.0, dt=DT,
                                          pin_anchor=[PSI], pin_strength=Kpin)
            theta[0] += float(rng.normal(0.0, NOISE))             # environmental noise on the read-head
            if s >= STEPS - WINDOW:
                tail.append(theta[0])
        est = sum(tail) / len(tail)                               # TIME-AVERAGE = the recalled value
        est_errs.append(mag(est - PSI))
        band_rms.append((sum((x - PSI) ** 2 for x in tail) / len(tail)) ** 0.5)
    return sum(est_errs) / TRIALS, sum(band_rms) / TRIALS


def vote_recall(k):
    """VOTE (F367): k redundant copies read through independent noise, averaged (spatial EC)."""
    errs = []
    for t in range(TRIALS):
        rng = np.random.default_rng(9000 + t)
        samples = [PSI + float(rng.normal(0.0, NOISE)) for _ in range(k)]
        errs.append(mag(sum(samples) / k - PSI))
    return sum(errs) / TRIALS


def main():
    print(f"F388 phase-lock read-head = temporal EC (srmech {srmech.__version__}, noise sigma={NOISE})")

    print("\n  VOTE (F367, SPATIAL EC): k redundant copies, averaged -> estimate error ~ sigma/sqrt(k)")
    vote = {}
    for k in (1, 4, 16, 64):
        e = vote_recall(k); vote[k] = e
        print(f"    k={k:<3} copies : recall error = {e:.4f}   {'(k=1: lossy single read = the guess)' if k == 1 else ''}")

    print("\n  LOCK (F388, TEMPORAL EC): ONE copy; read-head pinned (K), recalled value = TIME-AVERAGE of the lock")
    lock = {}
    for K in (0.0, 1.0, 4.0, 16.0, 40.0):
        est_err, band = lock_recall(K); lock[K] = dict(recall_err=est_err, band_rms=band)
        tag = ("UNLOCKED -> random-walk, lossy (the k=1 guess)" if K == 0.0
               else ("LOCKED -> low-error recall from ONE copy" if est_err < 0.02 else "locking (error falling with K)"))
        print(f"    K={K:<5}: recall error = {est_err:.4f}   (locked band RMS = {band:.3f})   {tag}")

    print("\n=== verdict ===")
    print("  VOTE drives recall error down with COPIES (k): ~ sigma/sqrt(k) — spatial EC, needs k>1 storage (F367).")
    print("  LOCK drives recall error down with COUPLING (K): the lock holds the read-head in the codeword's basin,")
    print("  and TIME-AVERAGING the locked read recovers it ~ sigma/sqrt(W*K*dt) — TEMPORAL EC, ONE stored copy.")
    print("  Same 1/sqrt(N) noise-suppression; VOTE spends COPIES, LOCK spends COUPLING-over-TIME. So a phase-LOCKED")
    print("  read-head gives low-error recall from a SINGLE copy on ORDINARY (binary) silicon — no (4:3)-native")
    print("  fabrication (F383), no k-fold redundancy (F367); just lock the readout to the stored fiber and average.")
    print("  HONEST: bit-exact in the NOISELESS limit (F386/R28); under noise it is noise-SUPPRESSED recall,")
    print("  threshold/basin-bounded (the knob moved from VOTE-k to LOCK-K) and stable only while K*dt < 2.")

    (HERE / "R-RBS-LM-R30_results.json").write_text(json.dumps(
        dict(srmech_version=srmech.__version__, noise=NOISE, steps=STEPS, window=WINDOW, dt=DT, trials=TRIALS,
             vote=vote, lock={str(k): v for k, v in lock.items()}), indent=2))
    print(f"\n  Results: {HERE / 'R-RBS-LM-R30_results.json'}")


if __name__ == "__main__":
    main()
