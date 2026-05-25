"""R-RBS-NN-2 worked example — user lexicon as native binding alphabet.

Demonstrates the Mechanism-1 bind path (MFO §VII.1.3 line 739, zero-cost
substrate-preservation) over a real user-vocabulary sample. All operations
stay at MFO Level 1 (ALU, integer arithmetic); no FPU operation in the
pipeline except the final similarity rescale, which is itself the Class K
substrate-to-shadow projection per §VII.1.3 line 743.

Reproduces R-RBS-NN-2 REPORT §7 numbers from in-tree srmech.

Usage:
    PYTHONPATH=docs/srmech/python python3 \
        docs/srmech/rbs_nn_research/worked_example_user_lexicon.py
"""

import sys

sys.path.insert(0, "docs/srmech/python")

from srmech.amsc.hdc import bind, bundle, similarity  # noqa: E402
from srmech.signal_processing.rbs_hdc_instrument import (  # noqa: E402
    D_DEFAULT,
    mint_vector,
)

print(f"D = {D_DEFAULT} bits = {D_DEFAULT // 8} bytes")
noise = 1.0 / (D_DEFAULT ** 0.5)
print(f"Orthogonality noise floor: 1/sqrt(D) = {noise:.6f}")


# ---- Demo 1: mint determinism (Spike #170 invariant 1) ----
print("\n=== Demo 1 — mint determinism ===")
v_a1 = mint_vector("LoE.token.Class K pin slot", D=D_DEFAULT)
v_a2 = mint_vector("LoE.token.Class K pin slot", D=D_DEFAULT)
print(f"  same string -> same vector: {v_a1 == v_a2}")


# ---- Demo 2: orthogonality of distinct user terms ----
print("\n=== Demo 2 — orthogonality of distinct user terms ===")
sample = [
    "Class A content-mint",
    "Class M XOR-bind",
    "Class K pin slot",
    "rotate-overlay",
    "sign flip",
    "substrate-native",
    "two-level ontology",
    "Hopf-compressed metric field",
    "1:3:7:3 substrate ordering",
    "RBS-HDC instrument",
]
vecs = [mint_vector(f"LoE.token.{t}", D=D_DEFAULT) for t in sample]
print(f"  vocabulary size: {len(sample)}")
sims = []
for i in range(len(vecs)):
    for j in range(i + 1, len(vecs)):
        sims.append(similarity(vecs[i], vecs[j]))
max_abs = max(abs(s) for s in sims)
mean_abs = sum(abs(s) for s in sims) / len(sims)
print(f"  pairwise similarities: n={len(sims)}")
print(f"  max |sim|  = {max_abs:.4f}")
print(f"  mean |sim| = {mean_abs:.4f}")
print(f"  expected ≈ 0 ± {noise:.4f}")


# ---- Demo 3: semantically-similar string pairs stay orthogonal ----
print("\n=== Demo 3 — similar-string pairs stay orthogonal at substrate ===")
print("  (substrate IS content-addressed; semantic similarity composes via binding, not via string)")
pairs = [
    ("Class K", "Class K pin slot"),
    ("sign flip", "sign-flip"),
    ("rotate-overlay", "rotate overlay"),
    ("Class M", "Class M XOR-bind"),
]
for a, b in pairs:
    va = mint_vector(f"LoE.token.{a}", D=D_DEFAULT)
    vb = mint_vector(f"LoE.token.{b}", D=D_DEFAULT)
    print(f"  '{a}' vs '{b}': sim = {similarity(va, vb):+.4f}")


# ---- Demo 4: bind composes; unbind recovers bit-exactly ----
print("\n=== Demo 4 — bind composes; unbind recovers bit-exactly (Spike #142) ===")
v_k = mint_vector("LoE.token.Class K", D=D_DEFAULT)
v_pin = mint_vector("LoE.token.pin slot", D=D_DEFAULT)
v_relation = bind(v_k, v_pin)
print(f"  sim(bind(K, pin), K)   = {similarity(v_relation, v_k):+.4f}  (expected ≈ 0; bind is substrate-projection)")
print(f"  sim(bind(K, pin), pin) = {similarity(v_relation, v_pin):+.4f}  (expected ≈ 0)")
v_recovered = bind(v_relation, v_k)
print(f"  bind(bind(K, pin), K) == pin: {v_recovered == v_pin}  (bit-exact unbind)")


# ---- Demo 5: bundle for superposition; recover via similarity ----
print("\n=== Demo 5 — bundle 5 terms; recover each above noise floor ===")
bundled = bundle(vecs[:5])
print("  in-bundle terms:")
for t, v in zip(sample[:5], vecs[:5]):
    print(f"    sim(bundle, '{t}') = {similarity(bundled, v):+.4f}")
print("  out-of-bundle terms (should be ≈ 0):")
for t, v in zip(sample[5:8], vecs[5:8]):
    print(f"    sim(bundle, '{t}') = {similarity(bundled, v):+.4f}")


# ---- Demo 6: bundle capacity scaling ----
print("\n=== Demo 6 — bundle capacity scaling ===")
def mint_anon(i):
    return mint_vector(f"LoE.token.anon{i:08d}", D=D_DEFAULT)


# 20 out-of-bundle controls for noise-floor measurement
controls = [mint_anon(10_000 + i) for i in range(20)]

for n in [3, 9, 33, 65, 129, 257]:
    test_vecs = [mint_anon(i) for i in range(n)]
    bundled_n = bundle(test_vecs)
    sims_in = [similarity(bundled_n, v) for v in test_vecs]
    sims_out = [similarity(bundled_n, c) for c in controls]
    min_in = min(sims_in)
    max_out = max(sims_out)
    margin = min_in - max_out
    print(
        f"  n={n:3d}: min sim(member) = {min_in:+.4f}, "
        f"max sim(non-member) = {max_out:+.4f}, margin = {margin:+.4f}"
    )


# ---- Demo 7: end-to-end pipeline stays at MFO Level 1 ----
print("\n=== Demo 7 — Level 1 verification ===")
print("  Pipeline ops:")
print("    1. mint_vector(name, D):  SHA-256(name||counter) chain  -> integer/byte")
print("    2. bind(a, b):            byte-wise XOR                 -> integer/byte")
print("    3. bundle(vectors):       bitwise majority (popcount)   -> integer/byte")
print("    4. similarity(a, b):      hamming distance → 1 - 2h/D   -> integer + final float rescale")
print("  No floating-point arithmetic except the final similarity rescale.")
print("  Per MFO §VII.1.3 line 743, the similarity rescale IS the Class K")
print("  substrate-to-shadow projection — the only ontologically-Level-2 step in the path.")
