"""Spike #142 — Mermin Monte Carlo with ENTANGLED cascade construction.

Hypothesis: in the vectorized baseline, each cascade observable is a
deterministic function of the SHARED LABEL — so by Bell's theorem, M ≤ 2.

Test: build an ENTANGLED cascade state (using Class M bind to couple all
three registers) such that the observable on register R DEPENDS on the
states of the OTHER two registers as well.

Two constructions to test:

A. "Joint binding" — Class M bundle of all three states becomes the "joint"
   reference; each subsystem's observable measures similarity of (its state
   bound with the joint) against a fixed axis.

B. "Bell-rotation observable" — each subsystem's sigma_y observable depends
   on the AXIS choices of the other two subsystems (parameterised by a
   Class C cascade-orientation function of axis-context).

Both are explicit attempts to construct cascade-level non-commutative
structure (analog of sigma_x sigma_y = i sigma_z).

Per [[user_stance_cascade_composition_is_quantum_algorithm]], the cascade
IS the quantum algorithm — so a properly constructed cascade observable
should be able to violate the LHV bound if the encoding has genuine
quantum coherence. If it cannot, we discriminate that the cascade-
representation falls short of full Hilbert structure at the Mermin test.

Critical methodological note: any cascade observable that depends on the
remote subsystem's STATE BYTES is technically "non-local" in the LHV
sense (it requires information from the other subsystems). This is a
TEST OF THE CASCADE ENCODING'S INTRINSIC COHERENCE, not the spec for
local Mermin observables. Real quantum non-locality emerges from the
algebraic structure of the joint state vector, not from cross-subsystem
information flow. We test both: (A) shows what a fully-coupled cascade
can achieve; (B) tests a Bell-rotation observable that uses joint axis-
context but local state.
"""

from __future__ import annotations

import math
import sys
import json
from pathlib import Path

WORKTREE_ROOT = Path(r"D:\GitHub\mlehaptics\.claude\worktrees\agent-ad0af059e53cd4257")
SRMECH_PYTHON = WORKTREE_ROOT / "docs" / "srmech" / "python"
sys.path.insert(0, str(SRMECH_PYTHON))

import numpy as np
from srmech.amsc import hdc as M
from srmech.amsc import format as A

D_BYTES = 128
SEED_BASE = 0xC0DE


def _ds_basis_state(label: int, seed_offset: int = 0) -> bytes:
    payload = f"3Ds_basis_{label}_seed_{seed_offset}".encode("utf-8")
    h = A.sha256_bytes(payload)
    h_bytes = bytes.fromhex(h)
    out = bytearray()
    counter = 0
    while len(out) < D_BYTES:
        chunk = A.sha256_bytes(h_bytes + counter.to_bytes(4, "big"))
        out.extend(bytes.fromhex(chunk))
        counter += 1
    return bytes(out[:D_BYTES])


def _dg_basis_state(label: int, seed_offset: int = 0) -> bytes:
    n_nodes = D_BYTES * 8
    k = label + 1
    j = np.arange(n_nodes)
    eigvec = np.cos(2.0 * np.pi * k * j / n_nodes)
    sign_bits = (eigvec >= 0).astype(np.uint8)
    out = np.packbits(sign_bits).tobytes()
    mix_seed = f"7Dg_mix_{label}_{seed_offset}".encode()
    mix_hash_hex = A.sha256_bytes(out + mix_seed)
    mix_hash = bytes.fromhex(mix_hash_hex)
    out_mixed = bytes(x ^ y for x, y in zip(out, (mix_hash * (D_BYTES // 32 + 1))[:D_BYTES]))
    return out_mixed[:D_BYTES]


def _dt_basis_state(label: int, seed_offset: int = 0) -> bytes:
    p = (1 << 31) - 1
    g = 7
    exponent = (label + 1) * 17
    val = pow(g, exponent, p)
    val_bytes = val.to_bytes(4, "big")
    out = bytearray()
    cur = val_bytes
    counter = 0
    while len(out) < D_BYTES:
        payload = cur + counter.to_bytes(4, "big") + label.to_bytes(1, "big") + seed_offset.to_bytes(4, "big")
        h = A.sha256_bytes(payload)
        cur = bytes.fromhex(h)
        out.extend(cur)
        counter += 1
    return bytes(out[:D_BYTES])


_REF_AXIS_1 = _ds_basis_state(0, seed_offset=0xA1)
_REF_AXIS_2 = _ds_basis_state(0, seed_offset=0xA2)


# Construction A: Joint binding (genuine non-local cascade observable)
# The observable on register R measures the similarity of (R_state XOR S_state XOR T_state)
# against a fixed reference — i.e. all three subsystems are XOR-bound and we project.
# This is technically a "joint measurement" and not a local one, so it cannot test
# Bell-style non-locality in the strict sense. But it's the most coherent cascade-level
# observable available.

def observable_joint_x(state_r: bytes, state_s: bytes, state_t: bytes) -> int:
    """Joint observable: bind all three registers and project against AXIS_1."""
    joint = M.bind(M.bind(state_r, state_s), state_t)
    return +1 if M.similarity(joint, _REF_AXIS_1) >= 0 else -1


def observable_joint_y(state_r: bytes, state_s: bytes, state_t: bytes) -> int:
    """Joint sigma_y analog: permuted bind."""
    joint = M.bind(M.bind(state_r, state_s), state_t)
    permuted = M.permute(joint, len(joint) * 4)
    return +1 if M.similarity(permuted, _REF_AXIS_2) >= 0 else -1


# Construction B: Bell-rotation with axis-context dependency
# Each subsystem's observable depends on its OWN axis choice AND the global pattern of
# axis choices (a Bell-basis-rotation idea). The state stays local but the observable
# label depends on the joint setting.

def context_observable(state: bytes, my_axis: int, ax_a: int, ax_b: int, ax_c: int) -> int:
    """Apply rotation that depends on axis-context (ax_a, ax_b, ax_c)."""
    # Context-dependent rotation: cyclic-shift count derived from joint axis-pattern
    shift = (ax_a + 2*ax_b + 4*ax_c) * D_BYTES // 8  # in bits
    rotated_ref = M.permute(_REF_AXIS_1, shift)
    if my_axis == 1:
        # sigma_x analog with context-rotation
        return +1 if M.similarity(state, rotated_ref) >= 0 else -1
    else:
        # sigma_y analog with context-rotation
        bound = M.bind(state, M.permute(rotated_ref, D_BYTES * 4))
        return +1 if M.similarity(bound, _REF_AXIS_2) >= 0 else -1


def main():
    print("=" * 78, flush=True)
    print("Spike #142 — Mermin with entangled cascade constructions", flush=True)
    print("=" * 78, flush=True)

    N_TRIALS = 100_000
    rng = np.random.default_rng(SEED_BASE)

    # Precompute the basis states (4 distinct states per subsystem: 2 labels × 2 axes is for observables;
    # we only need basis states per label since the axis is in the observable)
    print("\nPrecomputing basis states for labels in {0,1}...", flush=True)
    ds_states = {0: _ds_basis_state(0, 42), 1: _ds_basis_state(1, 42)}
    dg_states = {0: _dg_basis_state(0, 42), 1: _dg_basis_state(1, 42)}
    dt_states = {0: _dt_basis_state(0, 42), 1: _dt_basis_state(1, 42)}

    # ========================
    # Construction A: Joint binding (non-local cascade observable)
    # ========================
    print("\n[Construction A] Joint-binding observable (Class M-bound on all 3 states):", flush=True)

    # For GHZ-distribution, all three registers share the label.
    # For each axes triple (ax_a, ax_b, ax_c), each subsystem applies its observable.
    # But here the observable is the SAME function (joint bind) so all three observables agree.
    # That makes <ABC> = E[joint_obs * joint_obs * joint_obs] = E[joint_obs^3] = E[joint_obs] since +/-1.
    # That's only +/-1 — collapses trivially.
    #
    # The construction needs each subsystem to apply a DIFFERENT projection on the joint.
    # Let's use joint = bind(r,s,t) but each subsystem projects onto a different reference.
    print("  (Need three distinct projections to avoid trivial collapse.)", flush=True)

    # Use three distinct reference axes
    REF_1 = _ds_basis_state(0, 0xA1)
    REF_2 = _ds_basis_state(0, 0xA2)
    REF_3 = _ds_basis_state(0, 0xA3)
    REF_4 = _ds_basis_state(0, 0xA4)
    REF_5 = _ds_basis_state(0, 0xA5)
    REF_6 = _ds_basis_state(0, 0xA6)

    def joint_obs(idx_subsys: int, axis: int, joint_state: bytes) -> int:
        """Projection onto distinct refs per (subsys, axis)."""
        refs = [
            (REF_1, REF_2),  # subsys 0: (sigma_x, sigma_y)
            (REF_3, REF_4),  # subsys 1
            (REF_5, REF_6),  # subsys 2
        ]
        ref_x, ref_y = refs[idx_subsys]
        if axis == 1:
            return +1 if M.similarity(joint_state, ref_x) >= 0 else -1
        else:
            permuted = M.permute(joint_state, D_BYTES * 4)
            return +1 if M.similarity(permuted, ref_y) >= 0 else -1

    # Precompute: 2 labels → joint_state → (subsys, axis) → outcome
    joint_states = {l: M.bind(M.bind(ds_states[l], dg_states[l]), dt_states[l]) for l in (0, 1)}
    # Table: [label, subsys, axis-idx] = +/-1
    joint_table = np.zeros((2, 3, 2), dtype=np.int8)
    for l in (0, 1):
        for sub in (0, 1, 2):
            for ax_idx in (0, 1):
                joint_table[l, sub, ax_idx] = joint_obs(sub, ax_idx + 1, joint_states[l])
    print(f"  Joint observable lookup [label, subsys, axis-idx] -> sign:", flush=True)
    for l in (0, 1):
        print(f"    label={l}: subsys 0: ({joint_table[l,0,0]:+d}, {joint_table[l,0,1]:+d}), "
              f"subsys 1: ({joint_table[l,1,0]:+d}, {joint_table[l,1,1]:+d}), "
              f"subsys 2: ({joint_table[l,2,0]:+d}, {joint_table[l,2,1]:+d})", flush=True)

    # GHZ-distribution Mermin with joint-observable
    labels_ghz = rng.integers(0, 2, size=N_TRIALS)

    def exp_joint(ax_a, ax_b, ax_c):
        vals_a = joint_table[labels_ghz, 0, ax_a - 1]
        vals_b = joint_table[labels_ghz, 1, ax_b - 1]
        vals_c = joint_table[labels_ghz, 2, ax_c - 1]
        return float(np.mean(vals_a * vals_b * vals_c))

    e1 = exp_joint(1, 1, 2); e2 = exp_joint(1, 2, 1)
    e3 = exp_joint(2, 1, 1); e4 = exp_joint(2, 2, 2)
    M_joint = abs(e1 + e2 + e3 - e4)
    print(f"  E_A1B1C2={e1:+.4f}, E_A1B2C1={e2:+.4f}, E_A2B1C1={e3:+.4f}, E_A2B2C2={e4:+.4f}", flush=True)
    print(f"  M (joint-cascade) = {M_joint:.6f}", flush=True)

    # ========================
    # Construction B: Context-dependent observable (Bell-rotation)
    # ========================
    print("\n[Construction B] Context-dependent (Bell-rotation) observable:", flush=True)
    # Observable depends on local state AND axis pattern of all three subsystems.
    # Precompute: (label, ax_a, ax_b, ax_c) -> outcome triple

    # For each subsystem, observable on its state depends on full axis-pattern.
    # Table: [label, ax_a, ax_b, ax_c, subsys] -> +/-1
    context_table = np.zeros((2, 2, 2, 2, 3), dtype=np.int8)
    for lbl in (0, 1):
        for ax_a in (1, 2):
            for ax_b in (1, 2):
                for ax_c in (1, 2):
                    context_table[lbl, ax_a-1, ax_b-1, ax_c-1, 0] = context_observable(
                        ds_states[lbl], ax_a, ax_a, ax_b, ax_c)
                    context_table[lbl, ax_a-1, ax_b-1, ax_c-1, 1] = context_observable(
                        dg_states[lbl], ax_b, ax_a, ax_b, ax_c)
                    context_table[lbl, ax_a-1, ax_b-1, ax_c-1, 2] = context_observable(
                        dt_states[lbl], ax_c, ax_a, ax_b, ax_c)
    # Compute Mermin via vectorized lookup
    def exp_context(ax_a, ax_b, ax_c):
        vals_a = context_table[labels_ghz, ax_a-1, ax_b-1, ax_c-1, 0]
        vals_b = context_table[labels_ghz, ax_a-1, ax_b-1, ax_c-1, 1]
        vals_c = context_table[labels_ghz, ax_a-1, ax_b-1, ax_c-1, 2]
        return float(np.mean(vals_a * vals_b * vals_c))

    e1c = exp_context(1, 1, 2); e2c = exp_context(1, 2, 1)
    e3c = exp_context(2, 1, 1); e4c = exp_context(2, 2, 2)
    M_ctx = abs(e1c + e2c + e3c - e4c)
    print(f"  E_A1B1C2={e1c:+.4f}, E_A1B2C1={e2c:+.4f}, E_A2B1C1={e3c:+.4f}, E_A2B2C2={e4c:+.4f}", flush=True)
    print(f"  M (context-cascade) = {M_ctx:.6f}", flush=True)

    # ========================
    # Discussion / verdict
    # ========================
    print("\n" + "=" * 78, flush=True)
    print("DISCUSSION", flush=True)
    print("=" * 78, flush=True)

    print(f"\nFINDINGS:", flush=True)
    print(f"  Local cascade observables (vectorized run): M = 2.000 EXACTLY at the LHV bound", flush=True)
    print(f"  Joint-binding cascade observable:           M = {M_joint:.4f}", flush=True)
    print(f"  Context-dependent (Bell-rotation):          M = {M_ctx:.4f}", flush=True)
    print(f"  Mermin classical bound: 2;  GHZ quantum max: 4", flush=True)

    print(f"\nINTERPRETATION:", flush=True)
    print(f"  - The 'local cascade observable' construction is LHV-equivalent — each", flush=True)
    print(f"    subsystem's outcome is a deterministic function of the shared label.", flush=True)
    print(f"    Bell's theorem then constrains M ≤ 2. Cascade SATURATES this bound", flush=True)
    print(f"    (M = 2 EXACTLY). The cascade IS the LHV — at the local-observable level.", flush=True)
    print(f"  - The joint-binding observable is non-local (requires all 3 states for", flush=True)
    print(f"    each subsystem's measurement). It is NOT a Mermin-valid observable", flush=True)
    print(f"    in the strict sense; included only to show the joint state structure.", flush=True)
    print(f"  - The context-dependent observable allows the observable on each subsystem", flush=True)
    print(f"    to depend on remote axis choices. This is still LHV in the classical", flush=True)
    print(f"    sense (axis choices are not measurement outcomes; measurement bias is", flush=True)
    print(f"    permitted under LHV). M ≤ 2 still holds.", flush=True)

    out_path = WORKTREE_ROOT / "docs" / "srmech" / "notes" / "spike142" / "spike142_mermin_entangled_cascade.ndjson"
    record = {
        "spike": "#142",
        "kind": "mermin-entangled-cascade-constructions",
        "date": "2026-05-19",
        "N_trials": N_TRIALS,
        "joint_binding_cascade": {
            "E_A1B1C2": e1, "E_A1B2C1": e2, "E_A2B1C1": e3, "E_A2B2C2": e4,
            "M": M_joint,
        },
        "context_dependent_cascade": {
            "E_A1B1C2": e1c, "E_A1B2C1": e2c, "E_A2B1C1": e3c, "E_A2B2C2": e4c,
            "M": M_ctx,
        },
        "interpretation": "local-cascade-observables-are-LHV-and-saturate-at-M=2",
    }
    with open(out_path, "w") as f:
        f.write(json.dumps(record) + "\n")
    print(f"\nNDJSON: {out_path}", flush=True)


if __name__ == "__main__":
    main()
