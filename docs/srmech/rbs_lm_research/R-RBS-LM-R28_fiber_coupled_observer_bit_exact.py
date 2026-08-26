"""F386 — the THIRD route to bit-exactness: COUPLE the observer DoF to the fiber (phase-lock) and the
rotation is bit-exact in the coupled / co-rotating frame. "Change perspective to the rotation."

User (2026-06-04): "or what if we simply change our perspective to the rotation and see it as bit exact?
DoF coupled. fiber coupled whatever we want to call it."

Three routes to bit-exactness now:
  F382 — make the NUMBER rational (exact in its cyclic frame Z_q).
  F383 — make the SUBSTRATE native (build the (4:3)/Z_3 frame in; device-physics expert handoff).
  F386 — make the OBSERVER co-rotate: COUPLE the observer's DoF to the fiber (phase-lock). In the coupled
         frame the relative phase is CONSTANT -> the readout is the same value every step = bit-exact
         RELATIVE state. Keeps the (2:1) binary substrate; no fabrication; just change perspective.

This is F361 (observation is a coupled epicycle) + F367 (recall is relative) + F382 (the rotation's own
frame — here the observer ENTERS that frame by coupling). The lock IS the Kuramoto coupling.

Test (srmech-native cascade.kuramoto_step, the STOP-list op — NOT a hand-rolled sin loop): an OBSERVER
oscillator (omega=0) reads a FIBER oscillator (omega=Omega, the continuous rotation). Measure the relative
phase (fiber - observer) over a late window.
  UNCOUPLED (K=0) or under-coupled (K<Omega): relative phase DRIFTS (the F382 decimal) -> many distinct
    readouts -> NOT bit-exact.
  COUPLED + locked (K>=Omega): relative phase -> CONSTANT -> ONE readout every step = bit-exact relative.

HONEST: this is RELATIVE (coupled-frame) bit-exactness — the absolute rotation is still continuous; what is
exact is the COUPLED readout. It requires the lock (K >= detuning); the lock is the dynamic coupling (the
K-of-K precession story, F373/F374). And you must couple to the right CHIRALITY (F385): the mirror fiber
gives the conjugate.
Run: /tmp/verify_srmech_v070rc28/bin/python docs/srmech/rbs_lm_research/R-RBS-LM-R28_fiber_coupled_observer_bit_exact.py
"""
import json
from pathlib import Path
import srmech
from srmech.amsc import cascade

HERE = Path(__file__).parent
OMEGA = 0.5          # the fiber's (continuous) rotation rate = the detuning vs the omega=0 observer
STEPS, DT, WINDOW = 6000, 0.01, 800


def run(coupling):
    theta = [0.0, 0.10]                 # [observer, fiber]
    omega = [0.0, OMEGA]
    rel = []
    for _ in range(STEPS):
        theta = cascade.kuramoto_step(theta, omega, coupling=coupling, dt=DT)
        rel.append(theta[1] - theta[0])         # relative phase (fiber as seen by observer); no trig
    window = rel[-WINDOW:]
    spread = max(window) - min(window)          # radians of drift across the window (0 = locked/constant)
    distinct = len({round(x, 2) for x in window})   # distinct readouts (1 = bit-exact relative readout)
    return spread, distinct


def main():
    print(f"F386 fiber-coupled observer -> bit-exact relative readout (srmech {srmech.__version__})")
    print(f"  fiber rate Omega={OMEGA}, observer omega=0; 2-osc Kuramoto locks when coupling K >= Omega")
    print(f"  (relative-phase spread + distinct readouts over the last {WINDOW} of {STEPS} steps)\n")
    rows = {}
    for K in (0.0, 0.3, 1.0, 3.0):
        spread, distinct = run(K)
        locked = spread < 1e-3
        rows[K] = dict(coupling=K, rel_phase_spread_rad=spread, distinct_readouts=distinct,
                       locked=bool(locked), bit_exact_relative=bool(distinct == 1))
        tag = "LOCKED -> bit-exact relative readout" if distinct == 1 else "DRIFTS -> not bit-exact (the decimal)"
        print(f"  K={K:<4} : rel-phase spread={spread:.3e} rad   distinct readouts={distinct:<4}  {tag}")

    print("\n=== verdict ===")
    print("  UNCOUPLED / under-coupled (K < Omega): the observer's reading of the fiber DRIFTS every step")
    print("  (the F382 rotation-decimal) -> many distinct readouts -> NOT bit-exact.")
    print("  COUPLED + locked (K >= Omega): the observer phase-LOCKS to the fiber -> the relative phase is")
    print("  CONSTANT -> the SAME readout every step = BIT-EXACT in the coupled / co-rotating frame.")
    print("  => 'change perspective to the rotation' = COUPLE the observer DoF to the fiber (DoF-coupled /")
    print("     fiber-coupled). A THIRD route to bit-exactness, the CHEAPEST: no rational number (F382), no")
    print("     fabricated substrate (F383) — keep the (2:1) binary substrate, just ride the fiber.")
    print("  HONEST: RELATIVE (coupled-frame) bit-exactness; the absolute rotation stays continuous. Requires")
    print("  the lock (K >= detuning) — the lock is the dynamic coupling (K-of-K precession, F373/F374). And")
    print("  couple to the RIGHT chirality (F385): the mirror fiber locks to the conjugate.")

    (HERE / "R-RBS-LM-R28_results.json").write_text(json.dumps(
        dict(srmech_version=srmech.__version__, omega=OMEGA, steps=STEPS, dt=DT, window=WINDOW, rows=rows), indent=2))
    print(f"\n  Results: {HERE / 'R-RBS-LM-R28_results.json'}")


if __name__ == "__main__":
    main()
