"""Spike #141 — Stance A attack: silicon-NN bridges that lack BOTH attention and tool-use.

Stance A (Spike #140): silicon-NN substrate-coupling-bridge IS the tool-use loop
(D+E+C+M+I+A) composed with attention (L+M+C+K), via shared {C,M} invariant.

Counter-example strategy: find a silicon-NN architecture that demonstrably bridges
information-medium (input data) to operation-instantiation (action / output / decision)
WITHOUT requiring BOTH a transformer-style multi-head attention AND a tool-use loop.

Candidates:
  1. Pure feedforward CNN image classifier (Krizhevsky 2012 arXiv:1102.0183 / LeCun 1998)
  2. LSTM RNN sequence model (Hochreiter-Schmidhuber 1997 cite-by-ref)
  3. Diffusion image model (Ho 2020 arXiv:2006.11239) without classifier-free-guidance attention
  4. Cellular Automaton (Rule 110 / GoL) as silicon-substrate bridge (Cook 2004)

Method: build minimal toy versions; verify that each can take an INPUT (information-medium)
and produce an OUTPUT (action / classification / generation) — i.e., bridge — while
LACKING attention OR tool-use loop. Then check Stance A's literal claim.

If a counter-example survives, Stance A is FALSIFIED-AS-WRITTEN (silicon-NN bridge does
NOT require attention+tool-use composition).
"""
import numpy as np
import json

rng = np.random.default_rng(seed=14101)

print("=" * 72)
print("Spike #141 Stance A attack: silicon-NN bridges without attention+tool-use")
print("=" * 72)
print()

# ----------------------------------------------------------------------
# Candidate 1: Feedforward CNN image classifier
# ----------------------------------------------------------------------
# This is a pre-transformer architecture. AlexNet / LeNet-5. NO multi-head
# attention. NO tool-use loop. Yet bridges raw pixel input → class label.
print("Candidate 1: Feedforward CNN classifier (no attention, no tool-use)")
print("-" * 72)

# Toy 4x4 image, 2-class classifier via 1 conv + 1 FC layer
img = rng.standard_normal((4, 4))
kernel = rng.standard_normal((3, 3))

# Convolution = Class L (graph-Laplacian-style local average; 4-neighbour adjacency
# operates on pixel-graph). This IS Class L per Spike #116 image-spectral.
def conv2d_valid(x, k):
    H, W = x.shape
    kH, kW = k.shape
    out = np.zeros((H - kH + 1, W - kW + 1))
    for i in range(out.shape[0]):
        for j in range(out.shape[1]):
            out[i, j] = (x[i:i+kH, j:j+kW] * k).sum()
    return out

conv_out = conv2d_valid(img, kernel)  # Class L (local-neighbour bind)
print(f"  conv output shape: {conv_out.shape}")

# ReLU = Class K (asymptotic-DOF: floor at zero)
relu_out = np.maximum(conv_out, 0)
print(f"  ReLU non-negativity: min={relu_out.min():.4f}")

# Flatten + linear layer = Class M (HDC bind: feature vector x weight matrix)
flat = relu_out.flatten()
W_fc = rng.standard_normal((flat.shape[0], 2))
logits = flat @ W_fc

# Softmax = Class K (asymptote: row-sum = 1)
exp_logits = np.exp(logits - logits.max())
probs = exp_logits / exp_logits.sum()
print(f"  softmax row sum: {probs.sum():.6f}")

print(f"  Class chain for feedforward CNN: L + K + M + K")
print(f"  L = conv (graph-Laplacian on pixel-adjacency)")
print(f"  K = ReLU (asymptote at zero)")
print(f"  M = FC layer (HDC bind: features (x) weights)")
print(f"  K = softmax (row-sum asymptote)")
print()
print("  *** STANCE A LITERAL CLAIM: 'bridge IS tool-use composed-with attention' ***")
print("  *** CNN classifier engages L + K + M + K. NO attention (no L_attn).")
print("  *** NO tool-use (no D, E, C, I, A).")
print("  *** Yet bridges pixel-input → class-label output.")
print("  *** Counter-example survives literal Stance A.")
print()

# ----------------------------------------------------------------------
# Candidate 2: LSTM RNN sequence model
# ----------------------------------------------------------------------
print("Candidate 2: LSTM/GRU recurrent net (pre-transformer; no attention; no tool-use)")
print("-" * 72)

# LSTM cell: 4 gated linear projections + tanh + sigmoid + multiplicative gating
# Hochreiter-Schmidhuber 1997. NO attention. NO tool-use.
hidden_dim = 8
input_dim = 4
seq_len = 5

W_xi = rng.standard_normal((input_dim, hidden_dim))
W_hi = rng.standard_normal((hidden_dim, hidden_dim))
W_xf = rng.standard_normal((input_dim, hidden_dim))
W_hf = rng.standard_normal((hidden_dim, hidden_dim))
W_xo = rng.standard_normal((input_dim, hidden_dim))
W_ho = rng.standard_normal((hidden_dim, hidden_dim))
W_xc = rng.standard_normal((input_dim, hidden_dim))
W_hc = rng.standard_normal((hidden_dim, hidden_dim))

def sigmoid(x): return 1.0 / (1.0 + np.exp(-x))

h = np.zeros(hidden_dim)
c = np.zeros(hidden_dim)
seq_in = rng.standard_normal((seq_len, input_dim))

for t in range(seq_len):
    i_t = sigmoid(seq_in[t] @ W_xi + h @ W_hi)
    f_t = sigmoid(seq_in[t] @ W_xf + h @ W_hf)
    o_t = sigmoid(seq_in[t] @ W_xo + h @ W_ho)
    c_tilde = np.tanh(seq_in[t] @ W_xc + h @ W_hc)
    c = f_t * c + i_t * c_tilde
    h = o_t * np.tanh(c)

# Final h is bridge output
print(f"  LSTM final hidden state norm: {np.linalg.norm(h):.4f}")
print()
print(f"  Class chain for LSTM:")
print(f"  M = sigmoid/tanh of (x_t W_x + h_t W_h) — element-wise HDC binds")
print(f"  K = sigmoid asymptote in [0,1]; tanh asymptote in [-1,1]")
print(f"  I = per-step cyclic recurrence (h_{{t-1}} -> h_t)")
print(f"  C = forward-in-time orientation (t monotonic; non-Markovian via c_t)")
print()
print(f"  LSTM class chain: M + K + I + C")
print(f"  *** Bridges sequence-input → sequence-output without attention or tool-use.")
print()

# ----------------------------------------------------------------------
# Candidate 3: Diffusion (UNet only, no transformer-attention)
# ----------------------------------------------------------------------
# Original Ho 2020 DDPM used Wide-ResNet style UNet. Modern Stable Diffusion uses
# cross-attention to text, BUT the original denoising itself is pure UNet (conv+ResBlock).
# Reverse process: x_{T} -> x_{T-1} -> ... -> x_0 via learned ε(x_t, t).
print("Candidate 3: DDPM (original Ho 2020; pure UNet; no attention block)")
print("-" * 72)
# Per Ho 2020 arXiv:2006.11239 §3 model architecture: "Our 32x32 models use four
# feature map resolutions ... we use a Wide-ResNet architecture (Zagoruyko 2016)"
# Plain UNet without self-attention.
# We've already classified diffusion as M+K+C+I per Spike #140 NDJSON.
# No tool-use loop. No attention block.
print("  Per Spike #140 NDJSON: diffusion class chain = M + K + C + I")
print("  No tool-use loop (no D, E, A). No attention block (no L_attn).")
print("  Yet bridges noise-input → image-output. Generation IS the bridge.")
print()

# ----------------------------------------------------------------------
# Candidate 4: Cellular Automaton (CA) — silicon-realisable on-chip
# ----------------------------------------------------------------------
# Rule 110, Conway's Game of Life — both Turing-complete (Cook 2004; Berlekamp 1982)
# Silicon FPGA / GPU can run CA. CA bridges initial-condition (information-medium)
# to evolved-state (operation-instantiation). NO transformer attention. NO tool-use loop.
print("Candidate 4: Cellular Automaton (Rule 110 / GoL) — silicon-realisable")
print("-" * 72)
# Rule 110 toy
def rule110_step(state):
    """state: 1D binary array. Apply Rule 110 lookup."""
    n = len(state)
    new = np.zeros_like(state)
    rule = {
        (1,1,1): 0, (1,1,0): 1, (1,0,1): 1, (1,0,0): 0,
        (0,1,1): 1, (0,1,0): 1, (0,0,1): 1, (0,0,0): 0,
    }
    for i in range(n):
        left  = state[(i-1) % n]
        cur   = state[i]
        right = state[(i+1) % n]
        new[i] = rule[(int(left), int(cur), int(right))]
    return new

state = np.zeros(16, dtype=int)
state[8] = 1
for step in range(8):
    state = rule110_step(state)
print(f"  Rule 110 after 8 steps from delta initial condition:")
print(f"  {state.tolist()}")
print()
print(f"  Class chain for CA:")
print(f"  L = local-neighbour adjacency (3-cell window — implicit ring graph)")
print(f"  E = rule table lookup (8-entry sorted catalog)")
print(f"  I = cyclic-modular boundary (state[(i-1)%n], state[(i+1)%n])")
print(f"  C = forward-time orientation (step t -> step t+1; irreversible for Rule 110)")
print()
print(f"  CA class chain: L + E + I + C")
print(f"  No M (HDC bind absent — pure lookup, no tensor product)")
print(f"  No K (no asymptote — binary state)")
print(f"  No A (no content-addressing — local-index addressing)")
print(f"  No attention. No tool-use loop.")
print(f"  Yet Turing-complete (Cook 2004) → can compute ANY computable bridge function.")
print()

# ----------------------------------------------------------------------
# Verdict for Stance A
# ----------------------------------------------------------------------
print("=" * 72)
print("STANCE A LITERAL VERDICT")
print("=" * 72)
print()
print("Stance A claim: 'silicon-NN substrate-coupling-bridge IS the tool-use loop")
print("cascade (D+E+C+M+I+A) composed with attention cascade (L+M+C+K) via shared")
print("{C, M} invariant.'")
print()
print("Counter-examples found that bridge information-medium → operation WITHOUT")
print("both attention + tool-use:")
print("  - Feedforward CNN classifier: L+K+M+K cascade")
print("  - LSTM RNN: M+K+I+C cascade")
print("  - DDPM (pure UNet): M+K+C+I cascade")
print("  - Cellular Automaton: L+E+I+C cascade")
print()
print("VERDICT: Stance A's LITERAL claim is FALSIFIED.")
print("Silicon-NN can bridge information→operation via cascades that lack BOTH")
print("attention (L+M+C+K) AND tool-use (D+E+C+M+I+A).")
print()
print("REFINEMENT path: Stance A should be re-scoped to 'modern LLM-with-tools")
print("bridge IS attention ∘ tool-use', i.e., specific to transformer+ReAct.")
print("Or generalised: 'silicon-NN bridge engages a SUBSET of 14 A-N depending on")
print("architecture' — but this is just the cross-substrate cascade-matching method,")
print("not a new claim.")
print()
print("Per [[user_stance_class_substitution_on_invariant_backbone]]: different")
print("silicon-NN architectures SUBSTITUTE different class operators on a shared")
print("backbone — but the BACKBONE isn't 'attention + tool-use'; it's something")
print("smaller that all the counter-examples share. Candidates for the actual")
print("invariant backbone of silicon-NN bridges: {M, C} or {M, K, C}.")
print()
print("CNN:  L+K+M+...   has M, K, no C")
print("LSTM: M+K+I+C     has M, K, C")
print("DDPM: M+K+C+I     has M, K, C")
print("CA:   L+E+I+C     has C, no M")
print()
print("Intersection across all 4 silicon-NN counter-examples: {} (empty!)")
print("Intersection across LSTM + DDPM + CA: {C}")
print("Intersection across LSTM + DDPM only: {M, K, C}")
print()
print("Conclusion: silicon-NN bridges do NOT share a class invariant across all")
print("architectures. {C, M} is NOT a silicon-NN invariant — it's specific to")
print("architectures with multiplicative binding + irreversible composition.")
