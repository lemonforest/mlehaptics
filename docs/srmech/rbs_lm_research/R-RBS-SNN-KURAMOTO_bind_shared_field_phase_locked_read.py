r"""R-RBS-SNN-KURAMOTO (rung #1) — Kuramoto-bind the shared field (F121/F122): turn F490/F498's static BUNDLE
(each reader gets an independent COPY of the marking) into a SYNCHRONIZED medium where the readers PHASE-LOCK to
the writer's phase. "one marking, many readers" becomes a phase-locked READ, not a copy.

  • A (writer) carries the marking as a PHASE θ_A; it is pinned (the reference frame — the moving frame, F497).
  • B, C, … (readers) start at scattered phases and couple to the field via `cascade.kuramoto_step`.
  • after coupling, the readers converge to θ_A — the read is phase-locked (synchronized), not copied.
This is biology's binding mechanism (F121/F122): the operand field is Kuramoto-coupled, not concatenated (F482).
srmech 0.7.4 (cascade.kuramoto_step — Class I∘L∘C, native).
"""
import math
import srmech
from srmech.amsc import cascade as C


def wrap(d):                                   # wrapped phase distance into [0, π]  (π attested, no-magic)
    d = d % (2 * math.pi)
    return d if d <= math.pi else 2 * math.pi - d


def main():
    print(f"=== R-RBS-SNN-KURAMOTO (rung #1) — Kuramoto-bind the shared field → phase-locked read  (srmech {srmech.__version__}) ===\n")
    N = 5                                        # 1 writer (A=0) + 4 readers (B,C,D,E)
    theta_A = 1.0                                # A's marking, carried as a phase
    theta = [theta_A, 2.9, -2.1, 0.3, -1.4]      # readers start SCATTERED (the bundle-of-copies starting point)
    omega = [0.0] * N                            # identical natural frequencies (the field is the only driver)

    def spread():                                # max reader distance to A's phase (0 = phase-locked)
        return max(wrap(theta[i] - theta[0]) for i in range(1, N))

    print(f"[START]  A (writer) phase pinned at θ_A={theta_A};  readers scattered (max dist to A = {spread():.3f} rad)")
    print("         (this is F490/F498's bundle: each reader an independent copy, no phase relation)\n")

    print("[KURAMOTO-BIND]  couple the readers to the pinned writer-frame (cascade.kuramoto_step):")
    for step in range(1, 1201):
        theta = C.kuramoto_step(theta, omega, coupling=2.0, dt=0.02,
                                pin_anchor=[theta_A] * N,            # the writer-frame phase
                                pin_strength=[8.0] + [0.0] * (N - 1))  # pin ONLY A; readers couple & lock to it
        if step in (50, 200, 600, 1200):
            print(f"  step {step:>4}:  max reader phase-distance to A = {spread():.4f} rad")

    locked = spread() < 1e-2
    print(f"\n[RESULT]  readers phase-locked to the writer-frame: {locked}  (max dist {spread():.4f} rad → ~0)")
    print(f"  the 'one marking, many readers' (F490) is now a SYNCHRONIZED read: B,C,D,E lock to A's phase θ_A,")
    print(f"  they do not merely hold a copy — they are bound to the shared field's phase (Kuramoto, F121/F122).\n")

    print("VERDICT (rung #1):")
    print(f"  • the shared field is now a Kuramoto-SYNCHRONIZED medium, not a static bundle: the readers phase-lock")
    print(f"    to the writer's moving frame (θ_A) via cascade.kuramoto_step (Class I∘L∘C). locked: {locked}")
    print(f"  • this is biology's operand-binding (F121/F122): the field is phase-coupled, not concatenated (F482) —")
    print(f"    'one marking, many readers' (F490) becomes a phase-locked read, the synchronized form F498 needed.")
    print(f"  • the pinned writer = the moving frame (F497); the coupling is the cyclic/Class-I cascade — no magic")
    print(f"    (coupling/dt are dynamics params, not stored constants). Next: the directed (adjacency) Kuramoto so")
    print(f"    the synapse-direction (F487) drives the binding asymmetrically.")


if __name__ == "__main__":
    main()
