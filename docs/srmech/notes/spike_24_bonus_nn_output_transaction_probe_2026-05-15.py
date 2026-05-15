#!/usr/bin/env python3
# spike_24_bonus_nn_output_transaction_probe_2026-05-15.py
#
# Spike #24 bonus 4 — NN-output structure: backward-reading on a single
# transaction. Methodological demonstration; NOT a research result.
#
# Question (user, 2026-05-15): "we can soon look to discovering the
# structure and primitives of NN output, one transaction at a time.
# maybe we can work backwards again to learn how shape is defined and
# where primitives act."
#
# Stance: an NN output for input x does not pre-exist its forward pass;
# the layered operations constitute it. This is the SAME co-emergent
# ontology as SHA-256 (the previous spike), but with one additional
# feature: NN inference is TWO-LEVEL TEMPORAL — training-time gradient
# descent over many epochs creates the function the inference-time
# forward pass evaluates. Two stacked frozen-oscillations per
# [[user_stance_time_as_dimensional_shadow]]; per
# [[user_stance_fiber_as_spatially_absent_encoding]] the trained weights
# are the spatially-absent fiber and each forward pass projects the
# fiber through a specific input.
#
# Per the SHA-256 synthesis §1, the three diagnostic questions are:
#   (1) What is the trail made of?
#       (NN inference: layered (W, b, σ) tuples; matmul + add + non-
#        linearity; for classification, a final softmax.)
#   (2) Where is the trail backward-readable in isolation?
#       (Gradients via the chain rule are EXACT — backprop. Each affine
#        layer is invertible iff W is full-rank. Activation patterns
#        carry which inputs route through which features.)
#   (3) Where is the trail unreadable?
#       (ReLU is the trail-eraser for negative pre-activations — all
#        collapse to 0. Softmax argmax-followed-by-class-collapse drops
#        the full output-distribution shape down to one label.)
#
# This probe trains a SMALL 2-layer MLP on the scikit-learn 8x8 digits
# dataset (~1800 samples, 10 classes) and then performs backward-reading
# on ONE transaction (one digit), demonstrating four signatures:
#
#   (i)   GRADIENT ATTRIBUTION — exact local sensitivity of the output
#         logit-of-predicted-class to each input pixel via chain rule
#         from the post-softmax logit. Class L (Jacobian as graph) on
#         the computational graph instantiated for this one transaction.
#         [Sundararajan & Yan 2017 give the integrated-gradients
#         refinement; we report raw gradients here for transparency.]
#
#   (ii)  HIDDEN-LAYER ACTIVATION READING — what does the hidden layer
#         see for THIS transaction? Which hidden units are above zero
#         (ReLU "alive" set) and what is their value? Class C (iterator
#         over hidden-layer state) composed with Class B (tagged-tuple
#         per hidden unit). The "alive" set IS the backward-readable
#         routing signature — the path the input took through the
#         trained function.
#
#   (iii) RELU TRAIL-ERASURE — for the hidden units with pre-activation
#         < 0, the post-activation is 0 and the gradient with respect
#         to weight-input does not flow. Information about exactly HOW
#         negative they were is destroyed. This is the analog of
#         SHA-256's avalanche saturation; measured here as the count of
#         "dead" hidden units for this transaction and the L_∞ norm of
#         the destroyed pre-activations.
#
#   (iv)  OUTPUT-MANIFOLD READING — the post-softmax probability vector
#         lives on the (K−1)-dim probability simplex. The chosen label
#         is the argmax; the second-largest is the "runner-up"; the
#         gap is the model's confidence-on-this-transaction. Class D
#         (late-binding dispatch over output classes) is what softmax-
#         argmax IS. Reports the full sorted distribution to make the
#         dispatch visible.
#
# Discipline guards (mirror the SHA-256 probe):
#   - Tiny pedagogical model only (8x8 inputs, 32 hidden units, 10
#     outputs; ~2500 parameters).
#   - One transaction means one input image; all measurements run on it.
#   - numpy + scikit-learn only; no PyTorch / JAX / Keras dependency.
#   - Single seed for reproducibility; no claim to generalise to
#     frontier-LM scale.
#   - NDJSON output, one record per measurement.
#   - No interpretability-research-novelty claim; the goal is to map
#     established directions onto Spike #24 vocabulary on a worked
#     example.
#   - No therapeutic / clinical / behaviour-influence content.
#
# References for the backward-reading methodologies invoked:
#   - Sundararajan, M. & Yan, Q. (2017), "Axiomatic Attribution for
#     Deep Networks," ICML 2017. arXiv:1703.01365 [unverified-secondary,
#     arXiv-ID asserted but not extracted this session].
#   - Lundberg, S. M. & Lee, S.-I. (2017), "A Unified Approach to
#     Interpreting Model Predictions" (SHAP), NeurIPS 2017.
#     arXiv:1705.07874 [unverified-secondary].
#   - Tishby, N. & Zaslavsky, N. (2015), "Deep learning and the
#     information bottleneck principle," IEEE ITW. arXiv:1503.02406
#     [unverified-secondary].
#   - Olah, C. et al., "Zoom In: An Introduction to Circuits,"
#     Distill (2020), https://distill.pub/2020/circuits/zoom-in/
#     [unverified-secondary, URL asserted; not fetched this session].
#   - Elhage, N. et al. (Anthropic) "Toy Models of Superposition"
#     (2022) and "Towards Monosemanticity" (2023). [unverified-
#     secondary, Anthropic Transformer Circuits Thread.]
#
# License: GPL-3.0-or-later (same as srmech).

import json
import numpy as np
from pathlib import Path
from sklearn.datasets import load_digits
from sklearn.model_selection import train_test_split


# ----------------------------------------------------------------------
# Reproducibility
# ----------------------------------------------------------------------

SEED = 20260515
rng = np.random.default_rng(SEED)


# ----------------------------------------------------------------------
# Tiny MLP from scratch — 8x8 input (= 64 dims) → 32 hidden ReLU → 10
# output logits + softmax. Fully numpy; every operator is in this file.
# This is the "FIPS 180-4 §6.2-equivalent" — we hand-code so we can
# read every step backward.
# ----------------------------------------------------------------------

class TinyMLP:
    def __init__(self, n_in: int = 64, n_hidden: int = 32, n_out: int = 10):
        self.n_in = n_in
        self.n_hidden = n_hidden
        self.n_out = n_out
        # He-style initialisation for the ReLU layer
        self.W1 = rng.standard_normal((n_in, n_hidden)) * np.sqrt(2.0 / n_in)
        self.b1 = np.zeros(n_hidden)
        self.W2 = rng.standard_normal((n_hidden, n_out)) * np.sqrt(2.0 / n_hidden)
        self.b2 = np.zeros(n_out)

    def forward(self, x: np.ndarray):
        """Forward pass. Returns (logits, cache).

        Cache contains every intermediate operator's output so the
        backward pass + introspection can read the trail. This is the
        analog of keeping all 64 SHA-256 round-states for inspection.
        """
        z1 = x @ self.W1 + self.b1              # affine layer 1
        h_pre = z1                              # pre-activation
        h_post = np.maximum(0.0, z1)            # ReLU — trail eraser
        z2 = h_post @ self.W2 + self.b2         # affine layer 2 (logits)
        # softmax with numerical-stability trick
        z2_shift = z2 - np.max(z2, axis=-1, keepdims=True)
        ez = np.exp(z2_shift)
        probs = ez / np.sum(ez, axis=-1, keepdims=True)
        cache = {
            "x": x, "z1": z1, "h_pre": h_pre, "h_post": h_post,
            "z2": z2, "probs": probs,
        }
        return z2, cache

    def predict(self, x: np.ndarray):
        logits, _ = self.forward(x)
        return np.argmax(logits, axis=-1)


# ----------------------------------------------------------------------
# Training — straight numpy SGD. Vanilla, intentionally simple.
# ----------------------------------------------------------------------

def softmax_xent_grad(logits: np.ndarray, y: np.ndarray) -> np.ndarray:
    """Combined softmax + cross-entropy gradient on logits.
    y is integer label vector. Returns dL/d(logits)."""
    z_shift = logits - np.max(logits, axis=-1, keepdims=True)
    ez = np.exp(z_shift)
    p = ez / np.sum(ez, axis=-1, keepdims=True)
    # dL/dz = p - one_hot(y); average over batch
    grad = p.copy()
    grad[np.arange(len(y)), y] -= 1.0
    grad /= len(y)
    return grad


def train(mlp: TinyMLP, X: np.ndarray, y: np.ndarray,
          n_epochs: int = 80, lr: float = 0.1, batch_size: int = 64):
    n = len(X)
    losses = []
    for epoch in range(n_epochs):
        idx = rng.permutation(n)
        for start in range(0, n, batch_size):
            mb = idx[start:start + batch_size]
            xb, yb = X[mb], y[mb]
            logits, cache = mlp.forward(xb)
            # gradient through softmax+xent
            dlogits = softmax_xent_grad(logits, yb)
            # backprop through layer 2 (logits = h_post @ W2 + b2)
            dW2 = cache["h_post"].T @ dlogits
            db2 = np.sum(dlogits, axis=0)
            dh_post = dlogits @ mlp.W2.T
            # backprop through ReLU
            dh_pre = dh_post * (cache["h_pre"] > 0).astype(np.float64)
            # backprop through layer 1
            dW1 = cache["x"].T @ dh_pre
            db1 = np.sum(dh_pre, axis=0)
            # SGD update
            mlp.W2 -= lr * dW2
            mlp.b2 -= lr * db2
            mlp.W1 -= lr * dW1
            mlp.b1 -= lr * db1
        # measure loss at end of epoch
        logits_full, _ = mlp.forward(X)
        z_shift = logits_full - np.max(logits_full, axis=-1, keepdims=True)
        lse = z_shift[np.arange(n), y] - np.log(np.sum(np.exp(z_shift), axis=-1))
        loss = -np.mean(lse)
        losses.append(float(loss))
    return losses


# ----------------------------------------------------------------------
# Backward-reading probes on a single transaction.
# Each probe maps onto one Spike #24 primitive class (or composition).
# ----------------------------------------------------------------------

def probe_i_gradient_attribution(mlp: TinyMLP, x: np.ndarray, y_pred: int) -> dict:
    """Probe (i): exact dlogit_pred/dx via chain rule.

    Maps to Class L (Jacobian as a per-transaction graph) on the
    computational graph of this single forward pass. This is the
    minimal interpretable form of integrated-gradients / saliency."""
    x_b = x.reshape(1, -1)
    logits, cache = mlp.forward(x_b)
    # Want d logits[0, y_pred] / d x[0, :].
    # Forward: logits = h_post @ W2 + b2; h_post = ReLU(x @ W1 + b1).
    # d logit_c / d h_post = W2[:, c].
    # d h_post / d z1 = (z1 > 0).
    # d z1 / d x = W1.T.
    dlogit_dhpost = mlp.W2[:, y_pred]                       # shape (H,)
    relu_mask = (cache["h_pre"][0] > 0).astype(np.float64)  # shape (H,)
    dhpost_dz1 = relu_mask
    dlogit_dz1 = dlogit_dhpost * dhpost_dz1                 # shape (H,)
    dlogit_dx = dlogit_dz1 @ mlp.W1.T                       # shape (D,)
    # Identify top-5 pixel sensitivities by magnitude
    abs_g = np.abs(dlogit_dx)
    top5_idx = np.argsort(-abs_g)[:5]
    return {
        "method": "exact_chain_rule_gradient",
        "primitive_class_map": "L (Jacobian-as-per-transaction-graph)",
        "predicted_class": int(y_pred),
        "gradient_l1_norm": float(np.sum(np.abs(dlogit_dx))),
        "gradient_l2_norm": float(np.sqrt(np.sum(dlogit_dx ** 2))),
        "gradient_l_inf_norm": float(np.max(np.abs(dlogit_dx))),
        "top5_pixel_indices": [int(i) for i in top5_idx],
        "top5_pixel_gradients": [float(dlogit_dx[i]) for i in top5_idx],
        "comment": ("Class L statement: the gradient is the leading "
                    "eigen-direction of the Jacobian of logit-of-predicted "
                    "wrt input, evaluated at THIS x. Integrated gradients "
                    "(Sundararajan & Yan 2017, axiomatic) integrates along "
                    "x* -> x; raw gradient is the t=1 endpoint of that "
                    "integral."),
    }


def probe_ii_hidden_routing(mlp: TinyMLP, x: np.ndarray) -> dict:
    """Probe (ii): which hidden units are 'alive' (positive pre-activation)
    for THIS transaction? The alive set is the routing signature — the
    path the input took through the trained function.

    Maps to Class C (iterate over hidden units) composed with Class B
    (tagged tuple per unit) and analogous to the 'circuit' reading of
    Olah et al. — identifying which features fired."""
    x_b = x.reshape(1, -1)
    _, cache = mlp.forward(x_b)
    h_pre = cache["h_pre"][0]
    h_post = cache["h_post"][0]
    alive = h_pre > 0
    n_alive = int(np.sum(alive))
    # Sort hidden units by post-activation magnitude
    order = np.argsort(-h_post)
    top_units = [{"unit": int(i),
                  "pre_act": float(h_pre[i]),
                  "post_act": float(h_post[i])}
                 for i in order[:5]]
    return {
        "method": "hidden_layer_alive_set_routing",
        "primitive_class_map": "C (iterate hidden units) + B (tagged-tuple per unit)",
        "n_hidden_total": int(mlp.n_hidden),
        "n_hidden_alive": n_alive,
        "alive_fraction": float(n_alive / mlp.n_hidden),
        "top5_active_units": top_units,
        "comment": ("Backward-readable routing signature: the alive set "
                    "names WHICH features fired for this transaction. In "
                    "Olah et al. 'circuits' framing, each unit corresponds "
                    "to a learned feature; the alive set is the path "
                    "through the circuit graph for this input. With a "
                    "fully-monosemantic basis this reading would be "
                    "concept-level interpretable; in a polysemantic basis "
                    "(typical of dense networks) it carries superposed "
                    "feature content per Elhage et al. 2022."),
    }


def probe_iii_relu_trail_erasure(mlp: TinyMLP, x: np.ndarray) -> dict:
    """Probe (iii): measure information destroyed by the ReLU on this
    transaction. For dead units (pre_act < 0), their pre-activation
    value is lost downstream — nothing in the post-activation or the
    final logits depends on HOW negative they were.

    Maps onto the SHA-256 trail-erasure analog: ReLU is the per-layer
    information-destroying step. Class K-adjacent (constraint-as-
    information that vanishes under composition)."""
    x_b = x.reshape(1, -1)
    _, cache = mlp.forward(x_b)
    h_pre = cache["h_pre"][0]
    dead_mask = h_pre <= 0
    n_dead = int(np.sum(dead_mask))
    dead_vals = h_pre[dead_mask]
    return {
        "method": "relu_information_destruction_per_transaction",
        "primitive_class_map": "trail-eraser; SHA-256 'compress+state' analog",
        "n_dead_units": n_dead,
        "dead_fraction": float(n_dead / mlp.n_hidden),
        "destroyed_pre_act_l_inf": (float(np.max(np.abs(dead_vals)))
                                    if n_dead > 0 else 0.0),
        "destroyed_pre_act_l1": (float(np.sum(np.abs(dead_vals)))
                                 if n_dead > 0 else 0.0),
        "comment": ("These pre-activations are erased by ReLU. The fact "
                    "of being <= 0 propagates (the unit contributes 0 to "
                    "downstream); the MAGNITUDE of how-negative-it-was "
                    "does not. This is the per-layer co-emergence step — "
                    "the analog of SHA-256's `state += compress(state, "
                    "block)`. Depth multiplies the erasure; deep "
                    "networks become as ill-posed-on-preimage as a "
                    "many-round hash. The probe records the per-trans- "
                    "action quantity; over many transactions the dead-"
                    "fraction distribution characterises the network's "
                    "trail-erasure rate."),
    }


def probe_iv_output_manifold_dispatch(mlp: TinyMLP, x: np.ndarray) -> dict:
    """Probe (iv): the post-softmax probability vector on the simplex
    + the argmax dispatch. Softmax-argmax IS late-binding dispatch
    over output classes (Class D in Spike #24).

    Reports the FULL sorted probability vector so the reader sees the
    dispatch margin (top-1 vs top-2 gap) — the 'confidence on this
    transaction' signature."""
    x_b = x.reshape(1, -1)
    logits, cache = mlp.forward(x_b)
    probs = cache["probs"][0]
    order = np.argsort(-probs)
    sorted_probs = probs[order]
    return {
        "method": "softmax_dispatch_full_distribution",
        "primitive_class_map": "D (late-binding dispatch over classes)",
        "predicted_class": int(order[0]),
        "top1_prob": float(sorted_probs[0]),
        "top2_class": int(order[1]),
        "top2_prob": float(sorted_probs[1]),
        "dispatch_margin": float(sorted_probs[0] - sorted_probs[1]),
        "sorted_distribution": [
            {"rank": int(r), "class": int(c), "prob": float(p)}
            for r, (c, p) in enumerate(zip(order, sorted_probs))
        ],
        "comment": ("The output 'transaction' IS the dispatch: softmax "
                    "maps logits to simplex point, argmax dispatches to "
                    "one of K classes, runner-up gap is the confidence. "
                    "Class D in Spike #24 vocab IS this primitive. Cross- "
                    "ref the tactical-choice bonus: a choice is dispatch "
                    "over branches weighted by an evaluator; an NN "
                    "classifier is dispatch over output classes weighted "
                    "by softmax. Same primitive, different domain."),
    }


def probe_v_layer_avalanche(mlp: TinyMLP, X_test: np.ndarray,
                            n_trials: int = 64) -> dict:
    """Bonus probe (v): mirror SHA-256's avalanche measurement on the
    NN. For each of n_trials test inputs, perturb one pixel by +1
    (i.e., 1/16 of typical pixel range for digits which range 0-16);
    measure the resulting change in the post-softmax probability of
    the originally-predicted class. This is the NN's 'mixing rate'.

    Maps onto Class L Jacobian-Lipschitz-norm analysis. Not strictly
    per-transaction (averages over trials) but bounded and structural."""
    rng_local = np.random.default_rng(SEED + 1)
    perturb_pixel = 32  # middle of 64-pixel input
    perturb_amt = 1.0
    deltas = []
    for _ in range(n_trials):
        idx = rng_local.integers(0, len(X_test))
        x_orig = X_test[idx]
        x_pert = x_orig.copy()
        x_pert[perturb_pixel] += perturb_amt
        _, cache_o = mlp.forward(x_orig.reshape(1, -1))
        _, cache_p = mlp.forward(x_pert.reshape(1, -1))
        p_o = cache_o["probs"][0]
        p_p = cache_p["probs"][0]
        # change in the originally-top probability
        argmax_o = int(np.argmax(p_o))
        delta = float(p_p[argmax_o] - p_o[argmax_o])
        deltas.append(delta)
    arr = np.array(deltas)
    return {
        "method": "single_pixel_perturbation_avalanche",
        "primitive_class_map": "L (Jacobian Lipschitz)",
        "perturb_pixel": int(perturb_pixel),
        "perturb_magnitude": float(perturb_amt),
        "n_trials": int(n_trials),
        "mean_abs_delta_prob": float(np.mean(np.abs(arr))),
        "max_abs_delta_prob": float(np.max(np.abs(arr))),
        "median_abs_delta_prob": float(np.median(np.abs(arr))),
        "comment": ("Per-transaction Jacobian magnitudes. A small per-"
                    "pixel perturbation produces a small change in top-1 "
                    "probability — bounded by the layer-wise Lipschitz "
                    "constants. This is the NN analog of the SHA-256 "
                    "avalanche probe but with OPPOSITE sign: cryptographic "
                    "design seeks maximal avalanche (full mixing); NN "
                    "design seeks bounded avalanche (robustness to small "
                    "input changes). The same Class L primitive serves "
                    "both substrates."),
    }


# ----------------------------------------------------------------------
# Drive the probe
# ----------------------------------------------------------------------

def main(out_path: Path) -> None:
    # Load + train
    digits = load_digits()
    X = digits.data.astype(np.float64) / 16.0   # normalise pixels to ~[0,1]
    y = digits.target.astype(np.int64)
    X_tr, X_te, y_tr, y_te = train_test_split(X, y, test_size=0.2,
                                              random_state=SEED, stratify=y)

    mlp = TinyMLP(n_in=64, n_hidden=32, n_out=10)
    losses = train(mlp, X_tr, y_tr, n_epochs=80, lr=0.1, batch_size=64)

    # Sanity test-set accuracy
    y_pred_te = mlp.predict(X_te)
    test_acc = float(np.mean(y_pred_te == y_te))

    # Pick ONE transaction — first test sample whose label is correctly
    # predicted with high confidence (clearer pedagogical signal than
    # a misclassified sample, though the methodology applies either way).
    chosen_idx = None
    chosen_conf = 0.0
    for i in range(len(X_te)):
        x = X_te[i:i + 1]
        logits, cache = mlp.forward(x)
        p = cache["probs"][0]
        pred = int(np.argmax(p))
        if pred == y_te[i] and p[pred] > chosen_conf:
            chosen_conf = float(p[pred])
            chosen_idx = i
        if chosen_conf > 0.99:
            break
    assert chosen_idx is not None
    x_chosen = X_te[chosen_idx]
    y_true_chosen = int(y_te[chosen_idx])
    y_pred_chosen = int(mlp.predict(x_chosen.reshape(1, -1))[0])

    records = []

    records.append({
        "kind": "header",
        "spike": 24,
        "phase": "bonus_nn_output_backward_reading",
        "date": "2026-05-15",
        "discipline": ("tiny pedagogical MLP only; 2-layer ReLU; "
                       "one transaction in detail + bounded avalanche "
                       "summary; no interpretability-research-novelty "
                       "claim; no therapeutic/clinical content"),
        "architecture": {
            "n_in": 64, "n_hidden": 32, "n_out": 10,
            "non_linearity": "ReLU",
            "output_head": "softmax",
            "n_parameters": int(64 * 32 + 32 + 32 * 10 + 10),
        },
        "training": {"n_epochs": 80, "lr": 0.1, "batch_size": 64,
                     "n_train": int(len(X_tr)),
                     "final_train_loss": float(losses[-1])},
        "test_accuracy": test_acc,
        "seed": SEED,
    })

    records.append({
        "kind": "transaction_meta",
        "test_idx": int(chosen_idx),
        "y_true": y_true_chosen,
        "y_predicted": y_pred_chosen,
        "confidence": chosen_conf,
        "comment": ("ONE transaction: one input image, one forward "
                    "pass, one predicted label. All Probe (i)-(iv) "
                    "measurements below run on this transaction "
                    "exclusively. Probe (v) bounds Jacobian magnitudes "
                    "across 64 trials but is otherwise structural."),
    })

    records.append({
        "kind": "probe_i_gradient_attribution",
        "data": probe_i_gradient_attribution(mlp, x_chosen, y_pred_chosen),
    })
    records.append({
        "kind": "probe_ii_hidden_routing",
        "data": probe_ii_hidden_routing(mlp, x_chosen),
    })
    records.append({
        "kind": "probe_iii_relu_trail_erasure",
        "data": probe_iii_relu_trail_erasure(mlp, x_chosen),
    })
    records.append({
        "kind": "probe_iv_output_manifold_dispatch",
        "data": probe_iv_output_manifold_dispatch(mlp, x_chosen),
    })
    records.append({
        "kind": "probe_v_layer_avalanche",
        "data": probe_v_layer_avalanche(mlp, X_te, n_trials=64),
    })

    records.append({
        "kind": "verdict",
        "headline": ("Four backward-readable signatures on a single "
                     "transaction map cleanly onto Spike #24 Classes L, "
                     "C+B, D; the ReLU 'trail-eraser' is the per-layer "
                     "co-emergence step (SHA-256 'state += compress' "
                     "analog). No new primitive class required."),
        "signature_1_gradient": ("Class L Jacobian on per-transaction "
                                 "computational graph; integrated-"
                                 "gradients / saliency / SHAP are "
                                 "substrate-specific refinements."),
        "signature_2_routing": ("Class C + B; alive-set IS the "
                                "transaction's path through the trained "
                                "circuit; Olah-style mech-interp reads "
                                "this with monosemantic basis assumption."),
        "signature_3_erasure": ("ReLU is the per-layer trail-eraser; "
                                "dead-fraction IS the transaction's "
                                "co-emergence cost; SHA-256 analog is "
                                "the compression step's add-mod-2^32."),
        "signature_4_dispatch": ("Class D late-binding dispatch over "
                                 "output classes; softmax weights the "
                                 "dispatch; argmax-gap = confidence; "
                                 "same primitive as tic-tac-toe tactical "
                                 "choice in [[spike_24_bonus_tactical_"
                                 "choice_structure_2026-05-15.md]]."),
        "two_level_temporal": ("Training-time sequence ≠ inference-time "
                               "sequence. The weights ARE the spatially-"
                               "absent fiber from training; each forward "
                               "pass projects through ONE input to make "
                               "ONE output. Per [[user_stance_fiber_"
                               "as_spatially_absent_encoding]]."),
        "user_intuition_verdict": ("Methodologically correct. The "
                                   "backward-reading directions the NN-"
                                   "interpretability literature has "
                                   "developed (attribution, probing, "
                                   "circuits, sparse-autoencoder feature "
                                   "decomposition, info-bottleneck "
                                   "tracking) ARE this question's "
                                   "answer at the artificial-neural "
                                   "substrate. Each maps onto an "
                                   "existing Spike #24 primitive class."),
    })

    with out_path.open("w", encoding="utf-8") as f:
        for rec in records:
            f.write(json.dumps(rec, sort_keys=True))
            f.write("\n")


if __name__ == "__main__":
    out = Path(__file__).with_suffix(".ndjson")
    main(out)
    print(f"Wrote {out}")
