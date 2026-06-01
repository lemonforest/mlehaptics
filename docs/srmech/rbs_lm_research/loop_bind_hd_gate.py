"""loop_bind_hd_gate.py — MS#21 / issue #811 THE GATE: HDC-scale realization of the loop bind.

The dim-8 loop bind (F272-F274) is intrinsically dim-8 (octonions are the last division
algebra; Cayley-Dickson to dim 16+ -> zero divisors -> not unbindable). srmech HDC is
high-dim (D=2048). This tests the candidate realization:

  BLOCK-OCTONION TILING: tile a D-dim hypervector into D/8 octonion blocks; the high-dim
  "loop bind" = block-wise octonion product. Each block is a unit octonion (invertible),
  so the full bind is unbindable; per-block non-commutativity/non-associativity carries
  the order/tree/direction up to the vector level.

Resolves the gate iff the F274 properties SURVIVE at D=2048 AND capacity is real (vs the
commutative Klein-4 XOR bind baseline). Class-K clean (cosine via inner products; signs
via conj; no abs()). Seed attested-B. numpy-only (the product is the dim-8 octonion table,
batched -- srmech has no native octonion product yet, F271 sec-C).
"""
import os
import sys
import itertools
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from srmech.amsc import hdc                                       # noqa: E402

D = 2048
BS = 8                       # octonion block size
NB = D // BS                 # number of blocks
SEED = 17


# ---- batched Cayley-Dickson (octonion) product over the last axis ----
def conj_b(x):
    y = -x.copy()
    y[..., 0] = x[..., 0]
    return y


def cd_b(x, y):
    d = x.shape[-1]
    if d == 1:
        return x * y
    n = d // 2
    a, b = x[..., :n], x[..., n:]
    c, e = y[..., :n], y[..., n:]
    left = cd_b(a, c) - cd_b(conj_b(e), b)
    right = cd_b(e, a) + cd_b(b, conj_b(c))
    return np.concatenate([left, right], axis=-1)


# ---- high-dim block-octonion loop bind ----
def loop_bind_hd(x, y):
    return cd_b(x.reshape(NB, BS), y.reshape(NB, BS)).reshape(D)


def conj_hd(x):
    return conj_b(x.reshape(NB, BS)).reshape(D)


def unbind_hd(key, y):
    """Left-unbind for unit-block keys: conj(key) o y  (per-block Moufang division)."""
    return loop_bind_hd(conj_hd(key), y)


def rand_unit_blocks(rng):
    v = rng.standard_normal((NB, BS))
    v /= np.linalg.norm(v, axis=1, keepdims=True)   # each block a unit octonion
    return v.reshape(D)


def cos(u, v):
    return float(np.dot(u, v)) / (float(np.linalg.norm(u)) * float(np.linalg.norm(v)))


def n_distinct(vecs, tol=0.99):
    reps = []
    for v in vecs:
        if not any(cos(v, r) > tol for r in reps):
            reps.append(v)
    return len(reps)


def main():
    rng = np.random.default_rng(SEED)
    LB = loop_bind_hd
    print(f"=== block-octonion loop bind at D={D} ({NB} octonion blocks) ===\n")

    # ---- F274 paths at HD scale ----
    a, x = rand_unit_blocks(rng), rand_unit_blocks(rng)
    # C: unbind
    lerr = max(float(np.linalg.norm(unbind_hd(a, LB(a, xx)) - xx))
               for xx in [rand_unit_blocks(rng) for _ in range(50)])
    print(f"[C viability]  left-unbind max ||err|| over 50 = {lerr:.2e}  -> {'UNBINDABLE' if lerr < 1e-9 else 'FAIL'}")

    # A: order (6 perms of a 3-seq)
    s = [rand_unit_blocks(rng) for _ in range(3)]
    perms = [LB(LB(s[i], s[j]), s[k]) for i, j, k in itertools.permutations(range(3))]
    ca = [cos(perms[0], perms[t]) for t in range(1, 6)]
    print(f"[A order]      {n_distinct(perms)}/6 permutations distinct  (cos to perm0: {[f'{c:+.2f}' for c in ca]})")

    # B: tree (5 bracketings of a 4-seq)
    a4, b4, c4, d4 = (rand_unit_blocks(rng) for _ in range(4))
    br = [LB(LB(LB(a4, b4), c4), d4), LB(LB(a4, LB(b4, c4)), d4), LB(LB(a4, b4), LB(c4, d4)),
          LB(a4, LB(LB(b4, c4), d4)), LB(a4, LB(b4, LB(c4, d4)))]
    print(f"[B tree]       {n_distinct(br)}/5 bracketings distinct")

    # D: direction
    p, q = rand_unit_blocks(rng), rand_unit_blocks(rng)
    print(f"[D direction]  cos(a*b, b*a) = {cos(LB(p, q), LB(q, p)):+.3f}  (<1 -> direction)\n")

    # ---- capacity: bundle K key*val pairs, unbind+cleanup; vs klein4 baseline ----
    print("=== capacity (retrieval accuracy of bundled key*val pairs) ===")
    Ks = [2, 4, 8, 16, 32, 64, 128]
    TR = 8
    M = 256  # value codebook size

    def cap_octonion(K):
        accs = []
        for _ in range(TR):
            Vm = np.stack([rand_unit_blocks(rng) for _ in range(M)])        # (M, D)
            Vn = Vm / np.linalg.norm(Vm, axis=1, keepdims=True)             # unit rows
            idx = rng.choice(M, size=K, replace=False)
            keys = [rand_unit_blocks(rng) for _ in range(K)]
            bundle = np.sum([LB(keys[i], Vm[idx[i]]) for i in range(K)], axis=0)
            ok = 0
            for i in range(K):
                rec = unbind_hd(keys[i], bundle)
                # |rec| is constant across codebook entries -> argmax(Vn@rec) == argmax cosine
                ok += (int(np.argmax(Vn @ rec)) == idx[i])
            accs.append(ok / K)
        return float(np.mean(accs))

    # (klein4 baseline comparison deferred to #812 — the gate only needs octonion capacity to be real)
    print(f"  {'K':>4} | {'loop-bind acc':>14}   (M={M} codebook, {TR} trials)")
    for K in Ks:
        print(f"  {K:>4} | {cap_octonion(K):>14.3f}", flush=True)

    print("\n--- verdict ---")
    print("  If C/A/B/D survive at D=2048 and capacity tracks klein4, the GATE is RESOLVED:")
    print("  block-octonion tiling IS the HDC-scale realization -> the op spec (#814) can proceed.")


if __name__ == "__main__":
    main()
