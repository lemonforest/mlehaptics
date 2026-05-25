"""R-RBS-NN-5 worked example — sequence encoding + position-conditioned recovery.

Demonstrates §3.1 (bind-with-position-vector) — the canonical Kanerva HDC
sequence representation in srmech form — and §3.2 (Class I cyclic shift)
reversibility.

Both schemes are MFO Level 1 (ALU integer arithmetic; bit-exact at the
binding layer; cleanup-via-similarity is the only optional Level-2 readout).

Usage:
    PYTHONPATH=docs/srmech/python python3 \
        docs/srmech/rbs_nn_research/worked_example_position_binding.py
"""

import sys

sys.path.insert(0, "docs/srmech/python")

from srmech.amsc.hdc import bind, bundle, permute, similarity  # noqa: E402
from srmech.signal_processing.rbs_hdc_instrument import (  # noqa: E402
    D_DEFAULT,
    mint_vector,
)


D = D_DEFAULT
print(f"D = {D} bits")


# ---- Scheme A: bind-with-position-vector (Kanerva sequence) ------------
vocabulary_terms = [
    "Class A",
    "Class M",
    "Class K",
    "Class I",
    "Class L",
    "rotate-overlay",
    "sign flip",
    "pin slot",
    "substrate",
    "excitation",
]
vocab = {t: mint_vector(f"LoE.token.{t}", D=D) for t in vocabulary_terms}

sequence = [
    "Class A",
    "Class M",
    "Class K",
    "sign flip",
    "Class L",
    "rotate-overlay",
    "pin slot",
    "Class I",
    "substrate",
]  # length 9 — bundle majority requires odd count
L = len(sequence)
print(f"\nVocabulary: {len(vocab)} terms; encoding sequence of length L = {L}")

positions = [mint_vector(f"LoE.position.{k}", D=D) for k in range(L)]
bound = [bind(vocab[sequence[k]], positions[k]) for k in range(L)]
S_encoded = bundle(bound)
print(f"Encoded sequence S: {len(S_encoded)} bytes ({len(S_encoded)*8} bits)")


print("\n=== Scheme A — per-position recovery ===")
print(f"  pos | true token        | recovered         | sim     | OK")
print(f"  --- + ----------------- + ----------------- + ------- + ---")
n_correct = 0
for k in range(L):
    candidate = bind(S_encoded, positions[k])
    best_term, best_sim = None, -2.0
    for term, vec in vocab.items():
        s = similarity(candidate, vec)
        if s > best_sim:
            best_sim = s
            best_term = term
    correct = best_term == sequence[k]
    n_correct += correct
    print(
        f"   {k:2d} | {sequence[k]:17s} | {best_term:17s} | {best_sim:+.4f} | "
        f"{'OK' if correct else 'FAIL'}"
    )
print(f"\n  Accuracy: {n_correct}/{L} ({100*n_correct/L:.1f}%)")


# ---- Scheme B: cyclic shift of single token ----------------------------
print("\n=== Scheme B — cyclic shift (Class I) bit-exact reversibility ===")
base_token = mint_vector("LoE.token.base", D=D)
stride = 257  # Spike #170 / Spike #159 — coprime to D=8192 = 2^13
print(f"  stride = {stride} (coprime to D = {D})")
for k in [0, 1, 5, 13, 100]:
    rotated = permute(base_token, k * stride)
    recovered = permute(rotated, -k * stride)
    print(
        f"  k = {k:4d}: permute(base, k*stride) → reverse-permute recovers base: "
        f"{recovered == base_token}"
    )


# ---- Level inventory ---------------------------------------------------
print("\n=== Level-1 inventory ===")
print("  Scheme A (bind-with-position-vector):")
print("    Class A — mint_vector:   SHA-256 chain                 [ALU, L1]")
print("    Class M — bind:          byte-wise XOR                 [ALU, L1]")
print("    Class M — bundle:        bitwise majority              [ALU, L1]")
print("    Class M — similarity:    popcount XOR + Hamming        [ALU, L1]")
print("                              (final float rescale optional)")
print("  Scheme B (cyclic shift):")
print("    Class A — mint_vector:   SHA-256 chain                 [ALU, L1]")
print("    Class I — permute:       cyclic bit-rotation           [ALU, L1]")
print()
print("  Neither scheme requires FPU; both bit-exact at the binding layer.")
print("  The Level-2 lift (§4 rotate-overlay) is ontological by assignment,")
print("  not a compute requirement — permute itself is integer ALU.")
