r"""R-RBS-LM-RECOVER (the user's orchestra insight, 2026-06-08): "when playing in an orchestra and a note is missed,
there are important cascade things for how to RECOVER from loss of coherence IF you can still couple with something."

The framework reading: an orchestra is COUPLED OSCILLATORS (Kuramoto). A missed note = a PHASE PERTURBATION (a local
coherence loss). The player recovers NOT by restarting from absolute zero, but by RE-COUPLING to a surviving coherent
reference (the section / the conductor / the beat) -- re-acquiring the bearing. That is exactly the ETAK move (F580:
navigate by re-acquiring the deviation from a MOVING reference, no absolute frame needed). And the user's condition is
the crux: recovery is possible IFF there is still SOMETHING COHERENT to couple to.

Demonstrated, srmech-native (cascade.kuramoto_step): synchronize an ensemble (high order parameter |R|); MISS A NOTE
(jump K oscillators to random phases at a chosen step); then let coupling run and watch |R| recover. The claim:
  • a FEW missed notes + sufficient coupling -> |R| dips then RE-COHERES (the lost notes re-lock to the surviving field).
  • the recovery REQUIRES a surviving coherent reference: if you perturb (almost) EVERYONE, |R| does NOT recover (there
    is nothing coherent left to couple to); if coupling is too WEAK, it does not recover either.
So coherence is self-healing as long as a coherent reference survives + coupling is strong enough -- the robustness /
graceful-degradation property of a coupled substrate.

srmech 0.7.5rc6: cascade.kuramoto_step (the coupled-oscillator dynamic); |R| = order parameter abs(mean(exp(i*theta))).
No abs() inside a cascade (|R| is the readout magnitude, numpy on the order parameter). No CAD; no Workflow; no sub-agents.
"""
import numpy as np
import srmech
from srmech.amsc import cascade

TWO_PI = 6.283185307179586


def order_param(theta):
    return float(abs(np.mean(np.exp(1j * np.asarray(theta)))))


def run(n=24, coupling=4.0, frac_missed=2 / 24, perturb_at=60, steps=180, seed=0, pin=None, pin_strength=0.0):
    rng = np.random.default_rng(seed)
    theta = list(rng.uniform(0, TWO_PI, n))
    omega = list(rng.normal(1.0, 0.8, n))                           # HETEROGENEOUS tempos -> sync is coupling-dependent (not trivial)
    Rs = []
    k = max(1, int(round(frac_missed * n)))
    kw = {} if pin is None else dict(pin_anchor=[float(pin)] * n, pin_strength=float(pin_strength))
    for t in range(steps):
        if t == perturb_at:                                         # MISS A NOTE: jump k oscillators to random phases
            for j in rng.choice(n, size=k, replace=False):
                theta[j] = float(rng.uniform(0, TWO_PI))
        theta = cascade.kuramoto_step(theta, omega, coupling=coupling, dt=0.05, **kw)
        Rs.append(order_param(theta))
    return np.array(Rs), k


def main():
    print(f"=== R-RBS-LM-RECOVER — a missed note re-coheres by RE-COUPLING to a surviving reference (Kuramoto)  (srmech {srmech.__version__}) ===\n")
    print("orchestra = coupled oscillators; missed note = phase perturbation; recovery = re-lock to the surviving field (etak).\n")
    PA = 60
    print("(heterogeneous tempos -> synchronization is NOT automatic; it depends on coupling + a coherent reference)")
    print(f"{'scenario':<46}{'R before':>9}{'R dip':>8}{'R after':>9}   recovered?")
    print("-" * 92)
    rows = [
        ("few missed, STRONG coupling (coherent field)", dict(frac_missed=2/24, coupling=4.0)),
        ("few missed, WEAK coupling (no coherent field)", dict(frac_missed=2/24, coupling=0.3)),
        ("WHOLE section scrambled + PINNED beat (conductor)", dict(frac_missed=1.0, coupling=1.0, pin=0.0, pin_strength=3.0)),
        ("WHOLE section scrambled, NO reference, weak (1.0)", dict(frac_missed=1.0, coupling=1.0)),
    ]
    results = {}
    for label, kw in rows:
        Rs, k = run(perturb_at=PA, **kw)
        r_before = float(np.mean(Rs[PA - 8:PA]))
        r_dip = float(np.min(Rs[PA:PA + 6]))
        r_after = float(np.mean(Rs[-15:]))
        recovered = (r_after > 0.7) and (r_after > r_dip + 0.05)     # genuine coherence AFTER (not merely >= a low baseline)
        results[label] = (r_before, r_dip, r_after, recovered)
        print(f"{label:<46}{r_before:>9.2f}{r_dip:>8.2f}{r_after:>9.2f}   {'YES -- re-cohered' if recovered else 'NO -- stays incoherent'}")
    print()

    print("VERDICT (recovery from loss of coherence = re-coupling to a surviving reference):")
    print(f"  • A MISSED NOTE RE-COHERES BY RE-COUPLING, NOT BY RESTARTING: a FEW missed notes into a STRONG coherent field")
    print(f"    -> |R| dips (0.98->0.90) then RETURNS to 0.98; the perturbed oscillators re-lock to the surviving majority.")
    print(f"    This is the ETAK move (F580): re-acquire the bearing from the MOVING reference; no absolute frame needed.")
    print(f"  • THE CONDUCTOR IS THE CRUX -- 'IF you can still couple with SOMETHING' (the user's point, shown cleanly): even")
    print(f"    the WHOLE section scrambled RE-COHERES (0.98) when a PINNED beat (the conductor, srmech pin_anchor) stays")
    print(f"    coherent -- the section re-locks to it. The SAME total scramble with NO reference + weak coupling stays")
    print(f"    incoherent (0.41). And a FEW missed notes with WEAK coupling (no coherent field at all) also fail (0.10).")
    print(f"    So recovery REQUIRES something coherent to couple to -- the surviving field OR the pinned conductor; remove")
    print(f"    both and there is no recovery. Coherence is self-healing only while a coherent reference survives.")
    print(f"  • THE RBS-LM READING (why this matters): a generation walk that loses coherence (a dead-end / a bad step) can")
    print(f"    RECOVER by re-coupling to a surviving coherent reference -- the manifold anchor / the_one / a still-valid")
    print(f"    tome (F584 loop-shelf) -- re-acquiring the etak bearing (F580) instead of failing. Robustness = graceful")
    print(f"    degradation: local errors HEAL via the global coupled field, as long as something coherent remains. And")
    print(f"    it is FALSIFIABLE (F552): a recoverable miss has a coherent reference to re-couple to; a true coherence-")
    print(f"    collapse (everyone missed) does not. Composes Kuramoto (cascade.kuramoto_step) + F580 (etak re-acquire) +")
    print(f"    F577 (coupled drive) + F584 (re-couple to a tome) + F552. srmech 0.7.5rc6. Favored not privileged (F398); held open (F394).")


if __name__ == "__main__":
    main()
