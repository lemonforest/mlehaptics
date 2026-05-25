"""R-RBS-NN-3a worked example — substrate-form MLP classifier.

Demonstrates that an MLP linear layer is structurally HDC similarity-against-
templates (§3.1, §6 of the REPORT), and that the full cascade A ∘ (M ∘ K)
stays at MFO Level 1 throughout when weights are bipolar/integer and the
activation is argmax-via-integer-compare.

The classifier here is the minimal demonstration: one layer, no hidden
units, argmax readout. It is NOT a generalizing classifier — substrate is
content-addressed (R-RBS-NN-2 §7 Demo 3), so a Kanerva-style bundle-of-
training-views template would not generalize semantically without explicit
relation binding. This demo shows the cascade STRUCTURE, not generalization.

Usage:
    PYTHONPATH=docs/srmech/python python3 \
        docs/srmech/rbs_nn_research/worked_example_mlp.py
"""

import sys

sys.path.insert(0, "docs/srmech/python")

from srmech.amsc.hdc import bind, bundle, similarity  # noqa: E402
from srmech.signal_processing.rbs_hdc_instrument import (  # noqa: E402
    D_DEFAULT,
    mint_vector,
)


# ---- 1-layer MLP in substrate form -------------------------------------
# An MLP linear layer `z_j = ⟨w_j, x⟩ + b_j` is structurally a Class M
# similarity-against-templates: each row w_j of W is a template; each output
# dimension is the similarity of input x to that template.
#
# In bipolar/binary form: similarity(x, w_j) = 1 - 2·popcount(x XOR w_j)/D
#                                            = (D - 2·hamming(x, w_j)) / D
# This is identical to (2x-1)·(2w_j-1)/D — the conventional dot product
# rescaled to [-1, +1]. The MLP linear layer IS HDC similarity.
#
# Activation: argmax = Class K per-position selection at the dominant index.
# Per R-RBS-NN-1 §4.8 row 1: argmax is Level 1, integer compare, ALU.

D = D_DEFAULT
print(f"D = {D} bits")


# ---- mint 4 class templates -------------------------------------------
# In a REAL classifier, templates would be the bundled training examples
# (Kanerva associative memory) or learned via some Level-1 training rule.
# Here we just mint 4 named templates to demonstrate the cascade structure.
class_labels = [
    "substrate.Level_1.cyclic",
    "substrate.Level_1.binding",
    "excitation.Level_2.rotation",
    "excitation.Level_2.normalization",
]
templates = [mint_vector(f"LoE.template.{c}", D=D) for c in class_labels]

print(f"\n4 class templates minted; pairwise orthogonality:")
for i in range(4):
    for j in range(i + 1, 4):
        sim = similarity(templates[i], templates[j])
        print(f"  sim(t_{i}, t_{j}) = {sim:+.4f}  (≈ 0 ± 0.011)")


# ---- classifier: argmax over similarity-against-templates --------------
def classify(x: bytes) -> tuple[int, float, list[float]]:
    """Substrate-form 1-layer MLP cascade: A ∘ M ∘ K.

    A — input was minted via Class A (caller's responsibility)
    M — similarity against each of the 4 templates (Class M)
    K — argmax across the 4 similarities (Class K)
    """
    sims = [similarity(x, w) for w in templates]
    # argmax is integer compare; Level 1 — Class K per R-RBS-NN-1 §4.8 row 1
    best = 0
    for i in range(1, len(sims)):
        if sims[i] > sims[best]:
            best = i
    return best, sims[best], sims


# ---- Demo 1: in-template input recovers exactly ------------------------
print("\n=== Demo 1 — in-template input recovers exactly (cascade is bit-exact) ===")
for true_class in [0, 2]:
    x = mint_vector(f"LoE.template.{class_labels[true_class]}", D=D)
    pred, conf, sims = classify(x)
    correct = "OK" if pred == true_class else "FAIL"
    print(f"  query = template {true_class} ('{class_labels[true_class]}')")
    print(f"    similarities: {[f'{s:+.4f}' for s in sims]}")
    print(f"    argmax pred = {pred}, confidence = {conf:+.4f}  [{correct}]")


# ---- Demo 2: out-of-template input stays at noise floor ----------------
print("\n=== Demo 2 — out-of-template input stays at noise floor ===")
print("  (substrate does not hallucinate semantic similarity for novel terms)")
novel_terms = [
    "novel_term_alpha",
    "novel_term_beta",
    "novel_term_gamma",
]
for t in novel_terms:
    x = mint_vector(f"LoE.template.{t}", D=D)
    pred, conf, sims = classify(x)
    max_sim = max(sims)
    print(f"  query = '{t}': max |sim| = {max(abs(s) for s in sims):.4f}")
    print(f"    argmax pred = {pred} (essentially random; confidence at noise floor)")


# ---- Demo 3: the MLP linear layer IS HDC similarity ---------------------
print("\n=== Demo 3 — MLP linear layer IS HDC similarity (algebraic identity) ===")
print("  z_j = ⟨w_j, x⟩ in bipolar form  =  1 - 2·popcount(x XOR w_j)/D")
print("                                  =  similarity(x, w_j)")
x = mint_vector("LoE.template.substrate.Level_1.cyclic", D=D)
for j in range(4):
    s_via_srmech = similarity(x, templates[j])
    # Compute by hand from XOR + popcount to verify the identity
    xor = bytes(a ^ b for a, b in zip(x, templates[j]))
    hamming = sum(bin(byte).count("1") for byte in xor)
    s_by_hand = 1.0 - 2.0 * hamming / D
    match = abs(s_via_srmech - s_by_hand) < 1e-12
    print(
        f"  template {j}: srmech sim = {s_via_srmech:+.6f}, "
        f"by-hand sim = {s_by_hand:+.6f}, match = {match}"
    )


# ---- Demo 4: cascade composition is associative + reproducible ----------
print("\n=== Demo 4 — cascade A ∘ M ∘ K is bit-exact reproducible ===")
x = mint_vector("LoE.template.substrate.Level_1.cyclic", D=D)
pred_1, _, _ = classify(x)
pred_2, _, _ = classify(x)
x_remint = mint_vector("LoE.template.substrate.Level_1.cyclic", D=D)
pred_3, _, _ = classify(x_remint)
print(f"  classify(x) twice + classify(remint(name)) ⇒ all bit-exact match:")
print(f"    pred_1 = {pred_1}, pred_2 = {pred_2}, pred_3 = {pred_3}")
print(f"    all equal: {pred_1 == pred_2 == pred_3}")


# ---- Demo 5: Level-1 path inventory ------------------------------------
print("\n=== Demo 5 — Level-1 ops in the classification path ===")
print("  Forward-pass operations and their compute home:")
print("    Class A — mint_vector(name, D=8192):  SHA-256 chain (integer)   [ALU]")
print("    Class M — similarity(x, w):           popcount XOR (integer)    [ALU]")
print("                                          + final 1 - 2h/D rescale  [FPU, optional]")
print("    Class K — argmax:                     integer compare           [ALU]")
print()
print("  Per R-RBS-NN-1 §4.8 row 1: argmax is integer-compare, Level 1 (ALU).")
print("  The similarity float rescale is OPTIONAL for the classification path —")
print("  argmax across Hamming distances (smaller = more similar) gives the same")
print("  result without the float rescale. The float is only needed for human-")
print("  readable confidence reporting (per MFO §VII.1.3 line 743, that float IS")
print("  the substrate-to-shadow projection — the only ontologically-Level-2 step).")


# ---- Demo 6: integer-Hamming argmax produces same classification --------
print("\n=== Demo 6 — integer-Hamming argmax (no float, fully Level 1) ===")
def classify_integer(x: bytes) -> int:
    """Same classifier, but argmin over integer Hamming distance instead of
    argmax over float similarity. Smaller Hamming = more similar.
    NO float operations in this path."""
    best = 0
    xor = bytes(a ^ b for a, b in zip(x, templates[0]))
    best_hamming = sum(bin(byte).count("1") for byte in xor)
    for j in range(1, len(templates)):
        xor = bytes(a ^ b for a, b in zip(x, templates[j]))
        h = sum(bin(byte).count("1") for byte in xor)
        if h < best_hamming:
            best = j
            best_hamming = h
    return best


for true_class in [0, 1, 2, 3]:
    x = mint_vector(f"LoE.template.{class_labels[true_class]}", D=D)
    pred_float = classify(x)[0]
    pred_int = classify_integer(x)
    print(
        f"  query = template {true_class}: "
        f"float-argmax = {pred_float}, integer-Hamming-argmin = {pred_int}, "
        f"match = {pred_float == pred_int}"
    )
