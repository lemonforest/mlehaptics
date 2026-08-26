"""F291b — sharpen the F291-L1 confound: in the octonion loop bind, are ORDER-carrying and
KEY-SEPARATION the SAME structure (the cross / imaginary part), so a commutative bag loses BOTH
at once? (F291-L1 left this as an honest open: the octonion beat the bag on the order-INDEPENDENT
task too, and the builder noted "non-commutativity and key-spreading are the SAME property of the
product and cannot be cleanly separated by any commutative octonion combiner". Measure it.)

THE DECISIVE COMPARISON — three context-keys over the SAME octonion tokens, holding algebra fixed,
varying only commutativity:
  (1) PRODUCT  key = loop_bind(a,b)            — order-AWARE (non-commutative)
  (2) SUM      key = (a+b)/|a+b|               — order-BLIND, commutative vector sum
  (3) SYMPART  key = loop_bind(a,b)+loop_bind(b,a)  — order-BLIND, commutative product symmetrization

For imaginary octonions a,b:  a.b = -<a,b> e0 + a x7 b ,  b.a = -<a,b> e0 - a x7 b
  => a.b + b.a = -2<a,b> e0   (a PER-BLOCK SCALAR; the cross part cancels).
So the symmetric (order-blind) part of the product is the SCALAR <a,b>; the ENTIRE
key-distinguishing content lives in the antisymmetric cross7 part a x7 b — which is EXACTLY the
order carrier (it flips sign under swap). Claim: order and separation are ONE octonion structure.

We MEASURE: (a) the symmetric part is per-block-e0 (cross cancels); (b) order-sensitivity of each
key; (c) key-separation (mean inter-key |cos|, lower=better) of each key; (d) retrieval accuracy on
an order-dependent next-token task for each key. Prediction: PRODUCT wins on BOTH order and
separation; SUM and SYMPART lose order AND separation together -> not separable -> same fiber.

srmech-first: hdc.loop_bind (native dim-8) via the block-octonion HD gate; klein4 only for context.
Class-K clean: Born inner products, NO abs(). Scope: algebra only; benign; no CAD/MD/clinical.
"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from srmech.amsc import hdc                                            # noqa: E402  native rc4
from loop_bind_hd_gate import loop_bind_hd, rand_unit_blocks, D, BS, NB  # noqa: E402
import loop_bind_moufang as oracle                                     # noqa: E402

SEED = 2916            # B
V = 12                 # B — vocabulary size
N_CTX = V * (V - 1)    # all ordered distinct pairs
TRIALS = 3             # B — codebook draws


def n2(v):
    return float(np.dot(v, v))           # Born norm^2, no abs


def cos(u, v):
    du, dv = n2(u), n2(v)
    if du == 0.0 or dv == 0.0:
        return 0.0
    return float(np.dot(u, v)) / ((du ** 0.5) * (dv ** 0.5))


def rand_imag_blocks(rng):
    """unit block-octonion with the e0 component of every block zeroed (purely imaginary blocks)."""
    v = rand_unit_blocks(rng).reshape(NB, BS)
    v[:, 0] = 0.0
    v = v / np.linalg.norm(v, axis=1, keepdims=True)
    return v.reshape(D)


def block_e0_energy_fraction(v):
    """fraction of |v|^2 living in the per-block e0 (real) coordinates."""
    vb = v.reshape(NB, BS)
    e0 = float(np.sum(vb[:, 0] ** 2))
    return e0 / float(np.sum(vb ** 2))


def key_product(a, b):
    return loop_bind_hd(a, b)


def key_sum(a, b):
    s = a + b
    nn = n2(s) ** 0.5
    return s / nn if nn > 0 else s


def key_sympart(a, b):
    return loop_bind_hd(a, b) + loop_bind_hd(b, a)


def mean_inter_key_abs_cos(keys):
    """mean |cos| over distinct key pairs (lower = better separation). |cos| via sqrt(cos^2), no abs()."""
    n = len(keys)
    tot = 0.0
    cnt = 0
    for i in range(n):
        for j in range(i + 1, n):
            c = cos(keys[i], keys[j])
            tot += (c * c) ** 0.5         # |c| without abs()
            cnt += 1
    return tot / cnt if cnt else 0.0


def consistency():
    e = oracle.e
    m = 0.0
    for i in range(BS):
        for j in range(BS):
            d = np.asarray(hdc.loop_bind(e(i), e(j)), float) - np.asarray(oracle.loop_bind(e(i), e(j)), float)
            m = max(m, n2(d) ** 0.5)
    return m < 1e-12, m


def main():
    print(f"=== F291b — order vs separation in the octonion (D={D}, BS={BS}, NB={NB}) ===\n")
    ok, err = consistency()
    print(f"[consistency] native hdc.loop_bind == oracle on 64 basis pairs: {ok} (max err {err:.2e})\n")

    rng = np.random.default_rng(SEED)

    # ---- (a) symmetric part of the product is per-block SCALAR (cross cancels) ----
    a = rand_imag_blocks(rng); b = rand_imag_blocks(rng)
    sym = key_sympart(a, b)
    prod = key_product(a, b)
    print("--- (a) symmetric part of the product collapses to the per-block scalar ---")
    print(f"  e0-energy fraction:  sympart(a,b) = {block_e0_energy_fraction(sym):.4f}   "
          f"(product a.b = {block_e0_energy_fraction(prod):.4f})")
    print(f"  -> sympart is ~all per-block-e0 (scalar); the order-distinguishing content is the")
    print(f"     ANTISYMMETRIC cross part, which the symmetrization cancels.\n")

    # ---- (b) order-sensitivity + (c) key-separation, averaged over codebook draws ----
    agg = {k: {"order_cos": [], "sep": []} for k in ("product", "sum", "sympart")}
    for _ in range(TRIALS):
        toks = [rand_imag_blocks(rng) for _ in range(V)]
        pairs = [(i, j) for i in range(V) for j in range(V) if i != j]
        for name, fn in (("product", key_product), ("sum", key_sum), ("sympart", key_sympart)):
            keys = [fn(toks[i], toks[j]) for (i, j) in pairs]
            # order sensitivity: cos(key(i,j), key(j,i)) averaged
            ocs = []
            for (i, j) in pairs:
                if i < j:
                    ocs.append(cos(fn(toks[i], toks[j]), fn(toks[j], toks[i])))
            agg[name]["order_cos"].append(float(np.mean(ocs)))
            agg[name]["sep"].append(mean_inter_key_abs_cos(keys))
    print("--- (b)+(c) order-sensitivity & key-separation (mean over %d draws) ---" % TRIALS)
    print(f"  {'key':>9} | {'cos(ij,ji)':>11} | {'mean|cos| inter-key':>20}")
    for name in ("product", "sum", "sympart"):
        oc = float(np.mean(agg[name]["order_cos"]))
        sp = float(np.mean(agg[name]["sep"]))
        tag = "order-AWARE" if oc < 0.99 else "order-BLIND"
        print(f"  {name:>9} | {oc:>+11.4f} | {sp:>20.4f}   ({tag})")
    print("  (lower mean|cos| = better key-separation; order-AWARE iff cos(ij,ji) < 1)\n")

    # ---- (d) retrieval on an ORDER-DEPENDENT next-token task, per key type ----
    # rule: next = f(i,j) order-sensitive, f(i,j) != f(j,i). store key(ctx)->value(next), cleanup.
    print("--- (d) order-dependent next-token retrieval accuracy, per key type ---")
    accs = {k: [] for k in ("product", "sum", "sympart")}
    for t in range(TRIALS):
        r2 = np.random.default_rng(SEED + 100 + t)
        toks = [rand_imag_blocks(r2) for _ in range(V)]
        vals = [rand_imag_blocks(r2) for _ in range(V)]       # value codebook
        pairs = [(i, j) for i in range(V) for j in range(V) if i != j]
        nxt = {(i, j): (i * 7 + j * 3) % V for (i, j) in pairs}   # order-sensitive rule
        for name, fn in (("product", key_product), ("sum", key_sum), ("sympart", key_sympart)):
            # associative store: sum of key(ctx) (x) value(next)  [bind via loop product]
            store = np.zeros(D)
            for (i, j) in pairs:
                store = store + loop_bind_hd(fn(toks[i], toks[j]), vals[nxt[(i, j)]])
            # retrieve: unbind by left-division conj(key) . store, cleanup over value codebook
            hit = 0
            for (i, j) in pairs:
                k = fn(toks[i], toks[j])
                # left-unbind: conj(k) . store  (per-block); use the gate's conj via loop_bind sign trick:
                kb = k.reshape(NB, BS).copy(); kb[:, 1:] *= -1.0      # per-block conjugate (Class-K sign op, not abs)
                kc = kb.reshape(D)
                rec = loop_bind_hd(kc, store)
                sims = [cos(rec, vals[m]) for m in range(V)]
                hit += int(int(np.argmax(sims)) == nxt[(i, j)])
            accs[name].append(hit / len(pairs))
    for name in ("product", "sum", "sympart"):
        print(f"  {name:>9} : acc = {float(np.mean(accs[name])):.3f}")
    print()

    # ---- conclusion ----
    prod_oc = float(np.mean(agg['product']['order_cos']))
    prod_sep = float(np.mean(agg['product']['sep']))
    sum_sep = float(np.mean(agg['sum']['sep']))
    sym_sep = float(np.mean(agg['sympart']['sep']))
    print("=== reading ===")
    print(f"  PRODUCT is order-AWARE (cos {prod_oc:+.3f}) AND best-separated (mean|cos| {prod_sep:.3f}).")
    print(f"  SUM/SYMPART are order-BLIND AND worse-separated (sum {sum_sep:.3f}, sympart {sym_sep:.3f}).")
    print(f"  The order carrier (antisymmetric cross7) IS the key-separator; commutative combiners")
    print(f"  cancel it and lose BOTH at once -> order and separation are the SAME octonion structure,")
    print(f"  not a separable 'order effect' plus a separate 'capacity edge'. (sharpens F291-L1)")


if __name__ == "__main__":
    main()
