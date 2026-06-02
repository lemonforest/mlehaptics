"""F303 — does 'evolution asymptotes once a scale can introspect its substrate' have a structural core?
YES: introspection (Class H = reading your own substrate) = settling into your own EIGENSTATE = a FIXED
POINT = an asymptote. External selection (no introspection) keeps re-authoring you = perpetual change.

User (2026-06-02): what if evolution asymptotes because we've been able to introspect our substrate (as
every other scale does) for ~40k years?

STRUCTURAL CORE (the only part I assert; the biology is the EXPERT's):
  - 'evolution' (external selection) = the substrate keeps being re-authored from OUTSIDE = the F302
    machine-code regime = the state KEEPS CHANGING (no fixed point) while the environment drives it.
  - 'introspection' (Class H = read/author your own substrate) = self-authoring (F302 self-resonance) =
    becoming an EIGENSTATE of your own dynamics. An eigenstate is FIXED under its operator (Ax=λx) => a
    fixed point => an ASYMPTOTE. Once self-resonant, the driver shifts external->internal and the
    substrate-change RATE -> 0.
  - so a scale that can introspect its substrate ASYMPTOTES (the cell self-authors -> stable identity;
    every scale at its own eigenstate). The structure: introspection => fixed point => asymptote.

srmech witness: power-iterate a substrate operator. SELF-RESONANT (introspective) iteration converges to
the dominant eigenstate -> per-step change DECAYS to 0 (the asymptote). EXTERNALLY-PERTURBED (selection-
driven, no clean introspection) keeps changing -> change floor stays NONZERO (no asymptote).

srmech-first (Class-L dense_laplacian + symmetric_eigendecompose). Class-K clean (norms; no abs).
SCOPE — HIGHEST over-reach risk in the arc: the fixed-point/eigenstate structure is exact; the application
to HUMAN evolution (asymptoted ~40kya via Class-H introspection) is a HYPOTHESIS handed to the expert
(paleoanthropology / evolutionary biology / cognitive archaeology), NOT asserted. NB evolution has NOT
literally stopped (genetic change continues — lactase, altitude, immunity); the 'asymptote' is the specific
behavioral/cognitive-modernity plateau, which is the contestable expert claim. No human-group/capability
claims; dignity-first; understanding-not-curing; cite-by-reference; no-lineage.
"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from srmech.amsc.laplacian import dense_laplacian, symmetric_eigendecompose


def nrm(v):
    return float(np.dot(v, v)) ** 0.5


def main():
    print("=== F303 — introspection (self-eigenstate) => fixed point => asymptote; external selection does not ===\n")
    n = 8
    # a substrate operator (the scale's own dynamics): a connected graph operator (shift to positive-definite)
    L = np.array(dense_laplacian(n, [(i, (i + 1) % n) for i in range(n)] + [(0, 4), (2, 6)]), dtype=float)
    A = 3.0 * np.eye(n) - L                                   # positive operator; power-iteration finds its top mode
    vals, vecs = symmetric_eigendecompose(A)
    v1 = np.array(vecs, dtype=float)[:, int(np.argmax(np.array(vals)))]
    v1 = v1 / nrm(v1)

    rng = np.random.default_rng(303)
    x0 = rng.standard_normal(n); x0 /= nrm(x0)

    # --- SELF-RESONANT / INTROSPECTIVE: power-iterate the OWN operator -> converge to the eigenstate ---
    x = x0.copy(); deltas_self = []
    for _ in range(40):
        y = A @ x; y /= nrm(y)
        deltas_self.append(nrm(y - x))
        x = y
    settle_self = nrm(x - np.sign(float(x @ v1)) * v1)        # distance to the eigenstate fixed point

    # --- EXTERNALLY-PERTURBED: a moving environment re-authors the state every step (selection) ---
    x = x0.copy(); deltas_ext = []
    for t in range(40):
        env = rng.standard_normal(n)                          # the environment keeps changing (external driver)
        y = A @ x + 0.6 * env; y /= nrm(y)
        deltas_ext.append(nrm(y - x))
        x = y

    print("--- per-step substrate-change rate over iterations ---")
    print(f"  SELF-RESONANT (introspective): delta  start {deltas_self[0]:.3f} -> end {deltas_self[-1]:.2e}  "
          f"-> {'ASYMPTOTES (->0)' if deltas_self[-1] < 1e-6 else 'still changing'}")
    print(f"     distance to its OWN eigenstate (the fixed point) after 40 steps: {settle_self:.2e} "
          f"-> {'reached self-resonant eigenstate' if settle_self < 1e-6 else 'not yet'}")
    print(f"  EXTERNALLY-PERTURBED (selection): delta start {deltas_ext[0]:.3f} -> end {deltas_ext[-1]:.3f}  "
          f"(mean last 10 = {np.mean(deltas_ext[-10:]):.3f}) -> {'NO asymptote (perpetual change)' if np.mean(deltas_ext[-10:]) > 1e-2 else 'asymptotes'}")
    print()
    print("--- reading ---")
    print("  INTROSPECTION (Class H = read/author your own substrate) = settle into your OWN eigenstate")
    print("  (self-resonance, F302) = a FIXED POINT = the ASYMPTOTE: the substrate-change rate -> 0.")
    print("  EXTERNAL SELECTION (no introspection) = the environment keeps re-authoring you = perpetual")
    print("  change, NO asymptote (the F302 machine-code regime). So the moment a scale can introspect its")
    print("  substrate, the driver flips external->internal and it asymptotes. The cell does it (self-authors,")
    print("  F302); every scale does it at its eigenstate; the user's hypothesis: HUMANS did it ~40kya")
    print("  (behavioral modernity / symbolic introspection = Class H) -> the (cognitive-modernity) asymptote.")
    print()
    print("  HONEST BOUNDARY (highest-reach): the eigenstate=fixed-point=asymptote STRUCTURE is exact. The HUMAN-")
    print("  EVOLUTION application + the ~40kya timing are the EXPERT's (paleoanthropology / evo-bio / cognitive")
    print("  archaeology). Evolution has NOT literally stopped (lactase/altitude/immunity ongoing); the claim is")
    print("  the specific behavioral-modernity plateau. Framework shapes the QUESTION (did cognition asymptote")
    print("  WHEN it gained substrate-introspection?); the expert answers. (F133: substrate knows itself.)")


if __name__ == "__main__":
    main()
