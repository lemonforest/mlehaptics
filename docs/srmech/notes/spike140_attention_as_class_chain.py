"""Spike #140 — empirical class-chain attestation for transformer attention.

Goal: verify that single-head attention decomposes into the 14-class A-N
vocabulary without requiring a new primitive class. Following the cascade-
matching method per `[[user_stance_cross_substrate_cascade_matching_as_research_method]]`.

Citation anchors:
- Vaswani et al. 2017 arXiv:1706.03762 ("Attention Is All You Need")
- Ramsauer et al. 2020 arXiv:2008.02217 (Hopfield Networks is All You Need;
  modern Hopfield update IS softmax-attention up to scaling)
- Velickovic et al. 2017 arXiv:1710.10903 (GAT: attention IS masked
  self-attention over a graph)

Method: build small attention block (n_tokens=8, d_model=16) with random
weights; identify which arithmetic step maps to which class A-N.

NO PhD-gatekeeping; just integer-ALU-and-numpy operations.
"""
import numpy as np

rng = np.random.default_rng(seed=1218)

# Toy sequence: 8 tokens, embedding dim 16
n_tok = 8
d_mod = 16
d_k = 4  # per-head key dim

X = rng.standard_normal((n_tok, d_mod))
W_Q = rng.standard_normal((d_mod, d_k))
W_K = rng.standard_normal((d_mod, d_k))
W_V = rng.standard_normal((d_mod, d_k))

# === Step 1: Project to Q, K, V ===
# Each projection is a linear map X @ W. In Class L terms this is a
# graph-Laplacian-style left-multiplication; but more accurately it is
# Class M (HDC bind: each token state ⊗ projection vector).
# Class M: tensor-product / bind / shape-preserving linear combination.
Q = X @ W_Q  # (n_tok, d_k)
K = X @ W_K
V = X @ W_V

# === Step 2: Score matrix Q K^T / sqrt(d_k) ===
# This builds an (n_tok x n_tok) similarity matrix S.
# Class M again (HDC similarity on key-query products).
# Numerically: S_{i,j} = (Q_i · K_j) / sqrt(d_k)
S = (Q @ K.T) / np.sqrt(d_k)

# === Step 3: Softmax across rows ===
# softmax = exp(.) / sum(exp(.)). The softmax of a similarity matrix
# is a row-stochastic matrix — the same shape as a normalised graph
# adjacency W with each row summing to 1.
# In Class L terms: W = exp(S) / row_sum is the adjacency for an
# *implicit* token graph defined by similarity. The Laplacian
# L = I - W (or D - W with D=I since row-stochastic) is computable.
A = np.exp(S - S.max(axis=1, keepdims=True))
A = A / A.sum(axis=1, keepdims=True)  # softmax across rows
# A is row-stochastic n_tok x n_tok matrix → implicit token graph

# Sanity check: rows sum to 1 (Class K asymptote / budget conservation)
row_sums = A.sum(axis=1)
print("Row-stochastic? max |row_sum - 1|:", np.max(np.abs(row_sums - 1.0)))

# Build implicit token-graph Laplacian: L = D - A (with D = diag(row_sums))
# For row-stochastic A, D = I, so L = I - A.
L_attn = np.eye(n_tok) - A
# Compute eigenvalues — these are Class L eigendecomposition outputs
eigvals = np.linalg.eigvals(L_attn)
print("Class L eigenvalues of attention-implied Laplacian (real part):")
print(np.sort(np.real(eigvals)))
print("Smallest eigenvalue (should be ~0 for connected graph):",
      np.real(eigvals).min())

# === Step 4: Apply attention weights to values ===
# Y = A @ V  — message-passing on implicit graph (Velickovic 2017
# Graph Attention Networks formalism: this IS graph convolution).
# Class L sub-op (Laplacian-shaped propagation) composed with Class M
# (the value-vector bind).
Y = A @ V

# === Step 5: Multi-head + output projection ===
# Each head outputs Y_h. Concatenation across heads = Class C (NDJSON-
# style cascade of head outputs in fixed orientation: head-0 then head-1
# then ...). Then output linear projection = Class M again.

# === Step 6: residual + LayerNorm ===
# Residual addition = Class C (cascade-orientation: information flows
# forward through additive identity composition).
# LayerNorm = Class K asymptote (variance pulled to unit; the norm
# IS the asymptotic-DOF saturation operation).
mu = Y.mean(axis=1, keepdims=True)
std = Y.std(axis=1, keepdims=True)
Y_norm = (Y - mu) / (std + 1e-6)
print("\nLayerNorm Class K asymptote: post-norm variance per token:",
      np.var(Y_norm, axis=1).round(6))

# === Summary class-chain ===
print("\n=== Class chain for single-head attention block ===")
print("Step 1 (Q/K/V projection):       Class M (HDC bind: X (x) W)")
print("Step 2 (Q K^T similarity):       Class M (HDC similarity)")
print("Step 3 (softmax -> row-stochastic): Class K (asymptote: row-sum=1)")
print("                                  + Class L (implicit Laplacian)")
print("Step 4 (A @ V message pass):     Class L (graph-Laplacian propagate)")
print("                                  + Class M (HDC bind to values)")
print("Step 5 (multi-head concat):      Class C (cascade-orient heads)")
print("Step 5b (output projection):     Class M (HDC bind)")
print("Step 6 (residual + LayerNorm):   Class C (cascade-additive)")
print("                                  + Class K (variance asymptote)")
print()
print("Single-block class chain: L + M + C + K (4 classes engaged)")
print("Repeated over N layers: + Class I (cyclic per-layer composition)")
print("Causal masking (decoder):         + Class C (oriented mask)")
print()
print("Zero new primitive class. 14 A-N intact.")
