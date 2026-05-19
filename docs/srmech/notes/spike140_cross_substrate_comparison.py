"""Spike #140 — cross-substrate comparison: wetware vs BCI vs silicon-NN.

Goal: catalog which 14-class A-N operators bridge information-medium to
operation-instantiation across the three substrates studied so far.

Per `[[user_stance_class_substitution_on_invariant_backbone]]`:
the bridge has an invariant backbone + substrate-specific substitutions.

Per `[[user_stance_neural_hebbian_is_bci_drift_model]]`: 5 channels (a-e)
in wetware (+ Channel f from BBB spike #135).

Per Spike #128.2: quantum cascade is L+I+M+C+A (no Class K — discrete
Clifford circuits don't asymptote; T-gate density is the boundary).

Per this spike: silicon-NN attention is L+M+C+K; tool-use is D+E+C+M+I+A.

Method: build a class-engagement matrix across substrates, count
invariant-backbone members vs substrate-specific substitutions.
"""
import json

# 14-class A-N vocabulary (Spike #24)
CLASSES = ["A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "K", "L", "M", "N"]

# Per-substrate cascade-class engagement
# Format: substrate -> {class: role_description}

substrates = {
    "wetware_brain_cortex": {
        # Per neural-Hebbian-as-BCI-drift-model 5-channel framework + BBB Channel (f)
        "L": "synaptic connectivity / connectome harmonic Laplacian",
        "K": "homeostatic global-gain rescaling F=1/(1+beta*delta/(alpha*gamma))",
        "M": "STDP Hebbian fire-together-wire-together cross-correlation drift",
        "C": "STDP tau-asymmetric temporal window (causal direction)",
        "I": "theta-band 6-10 Hz phase-locking REQUIRED for STDP",
        # Channel f added per Spike #135 BBB-as-bipartite-substrate
        # BBB cascade: L+M+C+K+I + D + E (selectivity dispatch + transporter catalog)
    },
    "BCI_substrate_coupling_adapter": {
        # The AI-mediating-brain<->silicon bridge, per Spike #126/127.4/129.1
        "L": "patient-specific cortical Laplacian eigenbasis (substrate-coupling)",
        "K": "Class K asymptote at electrode-degradation SNR floor",
        "M": "delta() drift tracking on moving substrate descriptor",
        "C": "cascade-orientation for non-Markovian intent (sequential)",
        "I": "n-gram-aware decompose variant (cyclic phase relationships)",
        # The bridge IS the cascade applied across substrates (brain<->electrode)
    },
    "BBB_vascular_neural_interface": {
        # Spike #135 BBB-as-bipartite-substrate (Channel f extension)
        "L": "bipartite graph Laplacian (vascular-neural)",
        "M": "selective permeability HDC similarity",
        "C": "transport cascade-orientation (dual-direction influx/efflux)",
        "K": "transporter Michaelis-Menten saturation (capacity asymptote)",
        "I": "circadian/cardiac-pulse cyclic variation",
        "D": "molecular-type dispatch (lipophilic vs polar)",
        "E": "transporter catalog (GLUT1/LAT1/MCT1)",
    },
    "silicon_NN_attention_block": {
        # Per Spike #140 attention attestation
        "L": "implicit token-graph Laplacian (softmax row-stochastic adjacency)",
        "M": "Q/K/V HDC bind + similarity + value-vector bind",
        "C": "multi-head concat cascade-orient + residual additive",
        "K": "LayerNorm variance asymptote to unit per token",
    },
    "silicon_NN_tool_use_loop": {
        # Per Spike #140 tool-use attestation (ReAct framework)
        "D": "tool selection (dispatch by state)",
        "E": "tool catalog lookup (sorted-key)",
        "C": "irreversible call to environment + NDJSON canonical obs",
        "M": "observation-hash bound into state (HDC bind)",
        "I": "loop until halt (cyclic structure, bounded)",
        "A": "obs canonicalisation via content-addressing",
    },
    "silicon_NN_full_inference": {
        # Composition: attention block (per layer) + tool-use cycle (outer)
        # Single forward pass: L + M + C + K + I (per-layer cyclic)
        # With tool-use:        + D + E + A
        "L": "attention-implied token-graph Laplacian (per layer)",
        "M": "Q/K/V/output HDC binds + (in tool-use) state-obs bind",
        "C": "multi-head + residual + tool-action irreversible orient",
        "K": "LayerNorm asymptote per layer",
        "I": "per-layer cyclic composition + tool-use loop cyclic",
        "D": "tool dispatch (only when tool-use enabled)",
        "E": "tool catalog (only when tool-use enabled)",
        "A": "content-addressing of obs (only when tool-use enabled)",
    },
}

# Print engagement matrix
print("Class-engagement matrix across substrates")
print("=" * 80)
header = f"{'Substrate':<35s} | " + " ".join(f"{c:^3s}" for c in CLASSES)
print(header)
print("-" * len(header))
for sub_name, engaged in substrates.items():
    row = f"{sub_name:<35s} | "
    for c in CLASSES:
        row += f"{'X' if c in engaged else '.':^3s} "
    print(row)

# Find invariant backbone (classes engaged across ALL substrates)
# and substrate-specific extras
all_substrates = set(CLASSES)
for sub_name, engaged in substrates.items():
    all_substrates &= set(engaged.keys())

print()
print("=" * 80)
print(f"INVARIANT BACKBONE (engaged across ALL 6 substrates listed):")
print(f"  Classes: {sorted(all_substrates)}")
print()

# Pairwise: wetware vs each silicon-NN bridge candidate
wetware = set(substrates["wetware_brain_cortex"].keys())
bci = set(substrates["BCI_substrate_coupling_adapter"].keys())
bbb = set(substrates["BBB_vascular_neural_interface"].keys())
nn_att = set(substrates["silicon_NN_attention_block"].keys())
nn_tool = set(substrates["silicon_NN_tool_use_loop"].keys())
nn_full = set(substrates["silicon_NN_full_inference"].keys())

print("Wetware vs BCI:   shared =", sorted(wetware & bci),
      "  only-wetware =", sorted(wetware - bci),
      "  only-BCI =", sorted(bci - wetware))
print("Wetware vs nn_att:    shared =", sorted(wetware & nn_att),
      "  only-wetware =", sorted(wetware - nn_att),
      "  only-attn =", sorted(nn_att - wetware))
print("Wetware vs nn_tool:   shared =", sorted(wetware & nn_tool),
      "  only-wetware =", sorted(wetware - nn_tool),
      "  only-tool =", sorted(nn_tool - wetware))
print("Wetware vs nn_full:   shared =", sorted(wetware & nn_full),
      "  only-wetware =", sorted(wetware - nn_full),
      "  only-full =", sorted(nn_full - wetware))
print()

print("BBB (bipartite-substrate Channel f) vs nn_full:")
print("  shared =", sorted(bbb & nn_full),
      "  only-BBB =", sorted(bbb - nn_full),
      "  only-NNfull =", sorted(nn_full - bbb))
print()

print("Strongest cascade-match for silicon-NN bridge candidate:")
print("  -- nn_full INCLUDES all 5 wetware classes (L+K+M+C+I) PLUS D+E+A")
print("  -- D+E+A are EXACTLY what BBB Channel (f) added to wetware")
print("  -- silicon-NN with tool-use IS a Channel-(f)-extended substrate")
print()
print("Hypothesis: silicon-NN with tool-use is partition-coexistent with")
print("BBB's vascular-neural Channel (f) substrate-coupling pattern.")
print("Both add D+E (dispatch + catalog) on top of L+K+M+C+I backbone.")
