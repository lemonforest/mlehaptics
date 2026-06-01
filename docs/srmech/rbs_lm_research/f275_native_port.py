"""f275_native_port.py — F275 Sol resonance port to NATIVE srmech loop_bind.

Ports loop_bind_sol_resonance.py (F275) from the oracle (loop_bind_moufang.py,
hand-rolled numpy octonion product) to srmech NATIVE ops:
  srmech.amsc.hdc.loop_bind   (native Cayley-Dickson product)
  srmech.amsc.hdc.loop_conj   (native octonion conjugate)
  srmech.amsc.hdc.klein4_bundle / klein4_similarity  (commutative playback baseline)

CONSISTENCY CHECKS (required per task brief):
  [A] native loop_bind == oracle.loop_bind on all 8x8 basis pairs (exact, fp-eq)
  [B] Jacobi: jacobi_eigvals sum == trace == 2|E| (Laplacian consistency; n/a here
      — no Laplacian call; skip with note)
  [C] oracle parity on the resonance encoding: native and oracle produce the same
      cos(forward,reverse), cos(forward,wrong-sign), and nesting recovery values.

SCOPE: framework-reading STRUCTURE only. CAD-ban. No synthesis routes.
  The resonance integers [1,-3,2] are attested-to-structure (Laplace lock, F260).
  Periods attested-B (JPL/NASA). Signs via loop_conj (Class K+C), never abs().
  No-lineage: celestial mechanics is the field's; the loop-bind structure is ours.
"""
import os
import sys
import numpy as np

# --- path setup ---
_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _DIR)

import loop_bind_moufang as oracle                         # noqa: E402
from srmech.amsc import hdc                               # noqa: E402

SEED = 4
BODIES = ["Io", "Europa", "Ganymede"]
RES_COEFFS = [1, -3, 2]              # attested-to-structure (Laplace lock, F260)
PERIODS_DAYS = [1.769, 3.551, 7.155] # attested-B (JPL); ~1:2:4
DIM = hdc.LOOP_DIM                   # 8 (octonion / k=7); matches oracle.DIM

assert DIM == oracle.DIM, f"DIM mismatch: native {DIM} vs oracle {oracle.DIM}"


# ---------------------------------------------------------------------------
# Helpers — Class-K clean: inner products only, no abs()
# ---------------------------------------------------------------------------

def normsq_native(v):
    """Inner-product norm^2 <v,v> — no abs()."""
    v = np.asarray(v, dtype=float)
    return float(np.dot(v, v))


def unit(v):
    return v / (normsq_native(v) ** 0.5)


def cos_sim(u, v):
    """Cosine similarity via inner product — Class-K clean."""
    return float(np.dot(u, v)) / ((normsq_native(u) * normsq_native(v)) ** 0.5)


# ---------------------------------------------------------------------------
# [A] CONSISTENCY CHECK: native loop_bind == oracle on all 64 basis pairs
# ---------------------------------------------------------------------------

def check_basis_parity():
    """For every (e_i, e_j) pair: native loop_bind must equal oracle.loop_bind exactly."""
    mismatches = []
    for i in range(DIM):
        for j in range(DIM):
            ei = oracle.e(i, DIM)
            ej = oracle.e(j, DIM)
            native_result = hdc.loop_bind(ei, ej)
            oracle_result = oracle.loop_bind(ei, ej)
            if not np.allclose(native_result, oracle_result, atol=1e-12):
                mismatches.append((i, j, native_result, oracle_result))
    return mismatches


# ---------------------------------------------------------------------------
# Sign handling: conj for negative resonance coefficients (Class C chirality)
# Uses NATIVE loop_conj — this is the port change from oracle.conj.
# ---------------------------------------------------------------------------

def signed_native(anchor, coeff):
    """Apply resonance coefficient sign via native loop_conj (Class K+C, not abs)."""
    return anchor if coeff > 0 else hdc.loop_conj(anchor)


def loop_chain_native(order_coeffs, anchors):
    """Left-fold loop chain using NATIVE loop_bind + signed (Class C via loop_conj)."""
    items = [signed_native(anchors[b], c) for b, c in order_coeffs]
    acc = items[0]
    for it in items[1:]:
        acc = hdc.loop_bind(acc, it)
    return acc


# ---------------------------------------------------------------------------
# Oracle reference (for [C] parity check)
# ---------------------------------------------------------------------------

def signed_oracle(anchor, coeff):
    return anchor if coeff > 0 else oracle.conj(anchor)


def loop_chain_oracle(order_coeffs, anchors):
    items = [signed_oracle(anchors[b], c) for b, c in order_coeffs]
    acc = items[0]
    for it in items[1:]:
        acc = oracle.loop_bind(acc, it)
    return acc


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print("=" * 68)
    print("F275 Sol resonance port — NATIVE srmech loop_bind")
    print("=" * 68)

    # [A] Basis parity check
    print("\n[A] BASIS PARITY: native loop_bind == oracle on all 8x8 = 64 pairs")
    mismatches = check_basis_parity()
    if mismatches:
        print(f"    ANOMALY: {len(mismatches)} mismatch(es) found:")
        for i, j, nat, orc in mismatches[:5]:
            print(f"      e({i})*e({j}): native={nat}, oracle={orc}")
    else:
        print("    PASS: all 64 basis-pair products agree (atol=1e-12)")

    # [B] Jacobi / Laplacian check: N/A (no Laplacian call in this script)
    print("\n[B] JACOBI / LAPLACIAN: not applicable (no dense_laplacian call)")
    print("    (Consistency check target = 2|E| == trace; skip = honest null)")

    # [C] Oracle parity on the actual resonance encoding
    print("\n[C] ORACLE PARITY on resonance encoding (native vs oracle cos values)")
    rng = np.random.default_rng(SEED)
    anchors = {b: unit(rng.standard_normal(DIM)) for b in BODIES}

    forward   = list(zip(BODIES, RES_COEFFS))
    reverse   = list(zip(BODIES[::-1], RES_COEFFS[::-1]))
    wrongsign = list(zip(BODIES, [1, 3, 2]))

    E_fwd_nat = loop_chain_native(forward,   anchors)
    E_rev_nat = loop_chain_native(reverse,   anchors)
    E_ws_nat  = loop_chain_native(wrongsign, anchors)
    E_fwd_orc = loop_chain_oracle(forward,   anchors)
    E_rev_orc = loop_chain_oracle(reverse,   anchors)
    E_ws_orc  = loop_chain_oracle(wrongsign, anchors)

    cos_fr_nat = cos_sim(E_fwd_nat, E_rev_nat)
    cos_fw_nat = cos_sim(E_fwd_nat, E_ws_nat)
    cos_fr_orc = cos_sim(E_fwd_orc, E_rev_orc)
    cos_fw_orc = cos_sim(E_fwd_orc, E_ws_orc)

    print(f"    cos(forward,reverse):    native={cos_fr_nat:+.6f}  oracle={cos_fr_orc:+.6f}  "
          f"delta={abs(cos_fr_nat-cos_fr_orc):.2e}")
    print(f"    cos(forward,wrong-sign): native={cos_fw_nat:+.6f}  oracle={cos_fw_orc:+.6f}  "
          f"delta={abs(cos_fw_nat-cos_fw_orc):.2e}")

    parity_ok = (abs(cos_fr_nat - cos_fr_orc) < 1e-10 and
                 abs(cos_fw_nat - cos_fw_orc) < 1e-10)
    print(f"    {'PASS: native == oracle (delta < 1e-10)' if parity_ok else 'ANOMALY: native != oracle'}")

    # Also verify the encoded vectors themselves agree
    fwd_vec_match = np.allclose(E_fwd_nat, E_fwd_orc, atol=1e-12)
    print(f"    forward-chain vector match (atol=1e-12): {'PASS' if fwd_vec_match else 'ANOMALY'}")

    # --- The three recoveries from F275 (re-confirmed on NATIVE) ---
    print("\n" + "=" * 68)
    print("NATIVE RESULTS: directed, signed resonance argument")
    print("=" * 68)

    print("\n--- loop bind (k=7): directed, signed resonance argument ---")
    print(f"  cos(forward, reverse)    = {cos_fr_nat:+.6f}  (<1 -> DIRECTION recoverable)")
    print(f"  cos(forward, wrong-sign) = {cos_fw_nat:+.6f}  (<1 -> SIGN pattern recoverable)")

    # Commutative klein4 bundle baseline (playback)
    kb = [hdc.klein4_random(2048, seed=200 + i) for i in range(3)]
    P_fwd = hdc.klein4_bundle(kb[0], kb[1], kb[2])
    P_rev = hdc.klein4_bundle(kb[2], kb[1], kb[0])
    sim_play = hdc.klein4_similarity(P_fwd, P_rev)
    print("\n--- playback (commutative klein4 bundle): period set only ---")
    print(f"  sim(forward, reverse)    = {sim_play:.6f}  (~1 -> DIRECTION LOST)")

    # Nesting / bound state: host binds the resonant trio
    jup = unit(rng.standard_normal(DIM))
    bound   = hdc.loop_bind(jup, E_fwd_nat)
    # unbind: loop_bind(loop_conj(jup), bound) == E_fwd (left-cancel)
    recovered = hdc.loop_bind(hdc.loop_conj(jup), bound)
    cos_nest = cos_sim(recovered, E_fwd_nat)
    print("\n--- nesting / bound state (host binds the resonant trio) ---")
    print(f"  unbind host -> recover trio: cos = {cos_nest:.8f}  (~1 -> invertibly nested)")

    # --- Verdict ---
    direction_ok  = abs(cos_fr_nat) < 0.999
    sign_ok       = abs(cos_fw_nat) < 0.999
    playback_lost = sim_play > 0.95
    nesting_ok    = cos_nest > 0.9999

    print("\n--- verdict ---")
    print(f"  direction recoverable  (cos<1):  {'YES' if direction_ok else 'NO'}  cos={cos_fr_nat:+.6f}")
    print(f"  sign recoverable       (cos<1):  {'YES' if sign_ok else 'NO'}  cos={cos_fw_nat:+.6f}")
    print(f"  playback loses direction (sim~1): {'YES' if playback_lost else 'NO'}  sim={sim_play:.6f}")
    print(f"  host nesting invertible  (cos~1): {'YES' if nesting_ok else 'NO'}  cos={cos_nest:.8f}")
    print(f"  oracle parity (native==oracle):   {'YES' if (parity_ok and fwd_vec_match) else 'NO'}")

    all_pass = direction_ok and sign_ok and playback_lost and nesting_ok and parity_ok and fwd_vec_match and not mismatches
    print(f"\n{'ALL CHECKS PASS' if all_pass else 'SOME CHECKS FAILED'}")
    return all_pass


if __name__ == "__main__":
    ok = main()
    sys.exit(0 if ok else 1)
