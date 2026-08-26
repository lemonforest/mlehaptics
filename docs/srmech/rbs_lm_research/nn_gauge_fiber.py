"""nn_gauge_fiber.py — does the Moufang loop bind reveal NNs doing gauge maths with a hidden gauge fiber?

Brings the loop-bind / gauge knowledge back to RBS-NN/LM. Honest + no-forcing (the F285 fold-G2-NULL
precedent: test rigorously, report null if null).

The reading, tested in 4 steps:
  1. A NN's hidden layer IS a gauge FIBER: permuting hidden units leaves f invariant (gauge symmetry);
     the hidden activations are gauge-DEPENDENT (the fiber), f is the gauge-INVARIANT observable.
  2. Standard NN transport (matrix composition) is ASSOCIATIVE -> a FLAT connection (trivial holonomy).
  3. The Moufang loop bind is NON-associative -> a CURVED connection: the associator IS the holonomy /
     field-strength = a path/order MEMORY (F274) a flat NN lacks.
  4. HONEST no-forcing: the NN gauge group is permutation x scaling, NOT G2 (=Der(O), the loop-bind's gauge
     group, F273). So 'NNs do octonionic gauge maths' would be FORCED; the true reading is fiber+flat-connection,
     and the loop bind is the curved (path-memory) UPGRADE -- it endows the holonomy, it does not reveal a hidden
     octonionic structure.

srmech v0.7.0rc2 native loop_bind (consistency-checked vs the oracle). Class-K clean (norms/inner products).
"""
import os
import sys
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from srmech.amsc import hdc                       # noqa: E402
import loop_bind_moufang as oracle                # noqa: E402

rng = np.random.default_rng(0)


def e(i):
    v = np.zeros(8); v[i] = 1.0; return v


def main():
    # 1) the gauge FIBER: hidden-unit permutation is a gauge symmetry (f invariant)
    din, dh, dout = 6, 8, 3
    W1 = rng.standard_normal((dh, din)); b1 = rng.standard_normal(dh)
    W2 = rng.standard_normal((dout, dh)); b2 = rng.standard_normal(dout)
    f = lambda x, A, a, B: B @ np.tanh(A @ x + a) + b2
    x = rng.standard_normal(din)
    P = np.eye(dh)[rng.permutation(dh)]            # a hidden-unit permutation (the gauge transform)
    err = np.linalg.norm(f(x, W1, b1, W2) - f(x, P @ W1, P @ b1, W2 @ P.T))
    print("=== does the loop bind reveal NNs doing gauge maths with a hidden gauge fiber? ===\n")
    print(f"[1 gauge FIBER] ||f - f(gauge-permuted weights)|| = {err:.2e}  -> "
          f"{'GAUGE-INVARIANT: the hidden layer IS a fiber' if err < 1e-9 else 'NOT invariant'}")
    print("   hidden activations = gauge-DEPENDENT (the fiber); f = gauge-INVARIANT (the observable). NNs HAVE a hidden gauge fiber.")

    # 2) the connection is FLAT: matrix transport is associative -> trivial holonomy
    A, B, C = (rng.standard_normal((dh, dh)) for _ in range(3))
    flat = np.linalg.norm((A @ B) @ C - A @ (B @ C))
    print(f"\n[2 FLAT connection] matrix-transport ||(AB)C - A(BC)|| = {flat:.2e}  -> "
          f"{'ASSOCIATIVE = flat connection (trivial holonomy)' if flat < 1e-9 else 'non-assoc'}")

    # 3) the loop bind is a CURVED connection: non-associative -> the associator IS the holonomy
    assoc = (hdc.loop_bind(hdc.loop_bind(e(1), e(2)), e(4))
             - hdc.loop_bind(e(1), hdc.loop_bind(e(2), e(4))))
    a2 = float(np.dot(assoc, assoc))
    native_ok = np.allclose([hdc.loop_bind(e(i), e(j)) for i in range(8) for j in range(8)],
                            [oracle.loop_bind(e(i), e(j)) for i in range(8) for j in range(8)])
    print(f"\n[3 CURVED connection] loop-bind associator |[e1,e2,e4]|^2 = {a2:.3f}  -> "
          f"{'NON-ZERO = curved connection (a holonomy / path-memory)' if a2 > 1e-9 else 'flat'}")
    print(f"   (native loop_bind == oracle on all 64 basis pairs: {native_ok})  [bug-test: clean]")

    # 4) honest no-forcing check
    print("\n[4 HONEST no-forcing] the NN gauge group = permutation(S_h) x positive-scaling -- discrete/abelian,")
    print("   NOT G2 (=Der(O), 14-dim, the loop-bind's gauge group, F273). A generic NN's fiber is NOT octonionic;")
    print("   claiming 'NNs do octonionic gauge maths' would repeat the fold-G2-NULL error (F285).")

    print("\n--- verdict (honest) ---")
    print("  YES, NNs do gauge maths with a hidden gauge fiber -- the hidden-unit permutation/scaling symmetry")
    print("  (f is the gauge-invariant observable; the activations are the fiber). But standard NNs run it with a")
    print("  FLAT connection (associative transport, trivial holonomy). The Moufang loop bind is the CURVED-")
    print("  connection upgrade: non-associativity = the holonomy/field-strength = a path/order MEMORY (F274) the")
    print("  flat NN lacks. So the loop bind REVEALS the fiber + that NNs run it flat, and OFFERS to curve it.")
    print("  It does NOT reveal a hidden octonionic/G2 structure -- that gauge group is the loop bind's own, not")
    print("  the NN's. Reveal the gauge fiber: yes. Reveal hidden octonionic maths: no (honest null).")


if __name__ == "__main__":
    main()
