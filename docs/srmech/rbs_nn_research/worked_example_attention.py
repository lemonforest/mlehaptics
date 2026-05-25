"""R-RBS-NN-3b worked example — hard attention preserves V bit-exactly.

Demonstrates the soft-vs-hard attention asymmetry from §3 + §7 of the REPORT.

Setup: a 4-token sequence with hand-crafted attention pattern (query i wants
the content at position expected[i]). Queries and keys are bound with the
same "lookup" marker so the marker cancels in similarity, leaving content
similarity to drive attention.

Hard attention (MFO Mechanism 3 / Class K per-position selection per §VII.1.3
line 743): argmax_j sim(Q_i, K_j); output = V[argmax]. Bit-exact at every step.

Soft attention (MFO Mechanism 2 bundle-of-rotations per §VII.1.3 line 741):
Σ softmax(S)_j · V_j. Float; carries ~6.9% bundle averaging cost; output is
NOT bit-equal to any single V[j].

Usage:
    PYTHONPATH=docs/srmech/python python3 \
        docs/srmech/rbs_nn_research/worked_example_attention.py
"""

import sys

sys.path.insert(0, "docs/srmech/python")

from srmech.amsc.hdc import bind, similarity  # noqa: E402
from srmech.signal_processing.rbs_hdc_instrument import (  # noqa: E402
    D_DEFAULT,
    mint_vector,
)


D = D_DEFAULT
n = 4
print(f"D = {D} bits, n_tokens = {n}")


# ---- Setup: 4 positions, distinct content; queries hand-crafted ---------
# Q_i = bind(content[expected[i]], lookup_marker)
# K_j = bind(content[j],            lookup_marker)
# The lookup_marker cancels in similarity (XOR identity), so:
#     sim(Q_i, K_j) ≈ +1 if j == expected[i], ≈ 0 otherwise (noise floor)

content = [mint_vector(f"LoE.content.position{i}", D=D) for i in range(n)]
lookup_marker = mint_vector("LoE.role.lookup", D=D)
value_marker = mint_vector("LoE.role.value", D=D)

K = [bind(content[j], lookup_marker) for j in range(n)]
V = [bind(content[j], value_marker) for j in range(n)]

expected = [2, 0, 3, 1]  # query i wants position expected[i]
Q = [bind(content[expected[i]], lookup_marker) for i in range(n)]


# ---- Attention score matrix S[i,j] = sim(Q_i, K_j) ----------------------
print("\n=== Attention scores S = sim(Q_i, K_j) ===")
print(f"  expected[i] = {expected} (query i should attend to position expected[i])")
header = "  " + " " * 22 + "  ".join(f"  K_{j}  " for j in range(n))
print(header)
S = [[similarity(Q[i], K[j]) for j in range(n)] for i in range(n)]
for i in range(n):
    row = "  ".join(f"{S[i][j]:+.4f}" for j in range(n))
    print(f"  Q_{i} (want pos {expected[i]}):   {row}")


# ---- Hard attention: Class K per-position selection ---------------------
print("\n=== Hard attention (Mechanism 3 / Class K per-position; no averaging) ===")
all_correct = True
all_bit_exact = True
for i in range(n):
    j_hard = max(range(n), key=lambda j: S[i][j])
    output_hard = V[j_hard]
    expected_v = V[expected[i]]
    arg_ok = j_hard == expected[i]
    bit_ok = output_hard == expected_v
    all_correct &= arg_ok
    all_bit_exact &= bit_ok
    print(
        f"  Q_{i}: argmax j = {j_hard} (expected {expected[i]}, {'OK' if arg_ok else 'FAIL'}), "
        f"output bit-equal V[{expected[i]}]: {bit_ok}"
    )
print(f"\n  All queries correctly routed: {all_correct}")
print(f"  All outputs bit-exact match V[expected[i]]: {all_bit_exact}")


# ---- Soft attention: structural description -----------------------------
print("\n=== Soft attention (Mechanism 2 bundle-of-rotations) ===")
print("  Formula: Σ_j softmax(S/√d_k)_j · V_j")
print("  - softmax requires exp + bundle-of-exponentials       [FPU, Level 2]")
print("  - Σ float_w · V_j averages V across positions          [FPU, Level 2]")
print("  - Carries ~6.9% bundle-of-rotations signature per MFO §VII.1.3 line 741")
print("  - Output is NOT bit-equal to any single V[j] — it is a weighted average")
print("  - Computation omitted; structurally requires float arithmetic on V bytes")


# ---- Level inventory for the hard-attention forward pass ----------------
print("\n=== Level-1 inventory for hard-attention path ===")
print("  Operations and compute home:")
print("    Class A — mint_vector:   SHA-256 chain               [ALU, L1]")
print("    Class M — bind:          byte-wise XOR               [ALU, L1]")
print("    Class M — similarity:    popcount XOR + Hamming      [ALU, L1]")
print("                              (final float rescale is cosmetic;")
print("                              integer Hamming argmax gives same result)")
print("    Class K — argmax:        integer compare across keys [ALU, L1]")
print("    select V:                 array index                [ALU, L1]")
print("  Soft attention adds:")
print("    Class K — softmax exp:   exp() per element           [FPU, L2]")
print("    Class M — bundle norm:   Σ float weights             [FPU, L2]")
print("    Class M — bundle V sum:  Σ w_j · V_j                 [FPU, L2]")
