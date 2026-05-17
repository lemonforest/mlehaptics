"""Spike #33 v2 — alternative substrate construction to test A1 more rigorously.

The v1 result: Gaussian-edge-weight perturbation on C_N produces near-isotropic
spectral shift. F1 candidate-falsification for the easy reading. But the question
is whether the SHAPE of the perturbation matters — a single-axis 'bundle base
direction' might need to be structurally different.

v2 tests three different perturbation types:
1. Single-vertex weight bump (delta-function in the diagonal): pure local node-mass
2. Single-edge weight cut (delta-function in off-diag): local connectivity break
3. Direction-aligned offset: 2D ring projection to 1D axis with offset 'e'
   (this most directly tests the pin-slot geometric primitive on a substrate)

For each, ask: does an off-center observer (analog: 'observer at AoE direction')
see Class K geometric decay in the spectral residual?
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import numpy as np

# Reuse K-test from v1
K_MIN_R2 = 0.99
K_EPS_LO = 0.001
K_EPS_HI = 0.5


def k_test_strict(signal_corrections: np.ndarray, M_grid: np.ndarray, max_k: int = 7) -> dict:
    N = len(M_grid)
    coefs = []
    for k in range(1, max_k + 1):
        c_k = (2.0 / N) * np.sum(signal_corrections * np.sin(k * M_grid))
        coefs.append(abs(c_k))
    coefs = np.array(coefs)
    if np.all(coefs == 0):
        return dict(r_squared=0.0, eps_fit=0.0, monotonic=False, in_range=False, present=False,
                    coefs=[0.0]*max_k)
    coef_k = coefs * np.arange(1, max_k + 1)
    nonzero_idx = coef_k > 1e-30
    if nonzero_idx.sum() < 3:
        return dict(r_squared=0.0, eps_fit=0.0, monotonic=False, in_range=False, present=False,
                    coefs=coefs.tolist())
    log_coef_k = np.log(coef_k[nonzero_idx])
    k_arr = np.arange(1, max_k + 1)[nonzero_idx]
    A = np.vstack([k_arr, np.ones_like(k_arr)]).T
    slope, intercept = np.linalg.lstsq(A, log_coef_k, rcond=None)[0]
    eps_fit = math.exp(slope)
    pred = slope * k_arr + intercept
    ss_res = np.sum((log_coef_k - pred) ** 2)
    ss_tot = np.sum((log_coef_k - log_coef_k.mean()) ** 2)
    r2 = 1.0 - ss_res / max(ss_tot, 1e-30)
    monotonic = bool(np.all(np.diff(coefs) <= 0))
    in_range = bool(K_EPS_LO < eps_fit < K_EPS_HI)
    present = bool(r2 > K_MIN_R2 and monotonic and in_range)
    return dict(
        r_squared=float(r2), eps_fit=float(eps_fit),
        monotonic=monotonic, in_range=in_range, present=present,
        coefs=coefs.tolist(),
    )


# ---------- pin-slot direct test ----------

def pin_slot_signature_at_eps(eps: float, N: int = 1024) -> dict:
    """Direct K-test on the bronze pin-slot algebra phi(M) = atan2(sin M, cos M - eps).
    This is the canonical positive control: it MUST pass strict K-test (Spike #30B verified)."""
    M = np.linspace(0, 2 * math.pi, N, endpoint=False)
    phi = np.arctan2(np.sin(M), np.cos(M) - eps)
    correction = phi - M  # equation-of-centre
    # Unwrap
    correction = np.unwrap(correction)
    correction -= correction.mean()
    return k_test_strict(correction, M, max_k=7)


# ---------- Type 3: ring with off-centre observer (pin-slot-shaped substrate) ----------

def substrate_with_offset_observer(N: int, eps: float, observer_offset: float) -> dict:
    """Build a 2D ring substrate (unit circle in R^2). Observer sits at offset
    distance from origin. The observer's 'view angle' phi to a point at angle M
    on the ring is given exactly by the pin-slot formula:
        phi = atan2(sin M, cos M - eps)
    when the observer is at radial distance eps from the centre.

    This is the geometric origin of the equation-of-centre Kepler series and the
    canonical Class K substrate. We test: does the angular spectrum carry a K
    signature visible from the observer's frame?
    """
    M = np.linspace(0, 2 * math.pi, N, endpoint=False)
    # Observer at radial distance observer_offset; point on unit ring at angle M
    # View vector: (cos M - observer_offset, sin M)
    phi = np.arctan2(np.sin(M), np.cos(M) - observer_offset)
    # The phase deficit
    correction = phi - M
    correction = np.unwrap(correction)
    correction -= correction.mean()
    k_result = k_test_strict(correction, M, max_k=7)
    return {
        "N": N,
        "observer_offset": observer_offset,
        "phi_minus_M_amplitude": float(np.abs(correction).max()),
        "k_signature": k_result,
    }


# ---------- Two-axis test: on-axis vs off-axis observation ----------

def two_axis_test(N: int, eps_AoE: float) -> dict:
    """Imagine the substrate has TWO observers:
    - Observer A: at radial offset eps_AoE from substrate centre (the AoE-pole observer;
                  sees the substrate with off-centre projection)
    - Observer B: at the substrate centre (the off-axis observer; sees pure circular motion)

    The on-axis observer SHOULD see Class K signature; the off-axis observer SHOULD NOT.
    This is the structural test of the 'AoE-direction-as-bundle-base' reading.
    """
    on_axis = substrate_with_offset_observer(N, eps_AoE, eps_AoE)
    off_axis = substrate_with_offset_observer(N, eps_AoE, 0.0)
    return {
        "eps_AoE": eps_AoE,
        "on_axis_observer": on_axis,
        "off_axis_observer": off_axis,
        "discriminator_works": (
            on_axis["k_signature"]["present"] and not off_axis["k_signature"]["present"]
        ),
    }


# ---------- main ----------

def emit(records: list[dict], out_path: Path) -> None:
    with out_path.open("w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r, sort_keys=True) + "\n")


def main() -> int:
    out_dir = Path("D:/temp/spike_33")
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "spike_33_v2_findings_2026-05-16.ndjson"

    records: list[dict] = []
    records.append({
        "spike": 33,
        "version": "v2",
        "kind": "meta",
        "framing": ("Pin-slot geometric primitive directly applied: AoE-pole observer "
                   "as off-centre vantage on substrate ring; off-axis observer as centred. "
                   "Tests whether observer-position-relative-to-substrate-centre is the "
                   "structural mechanism for Class K signature appearance."),
    })

    # Positive control: bronze pin-slot at Antikythera and lunar values
    pin_slot_freeth = pin_slot_signature_at_eps(0.1146)
    pin_slot_lunar = pin_slot_signature_at_eps(0.054)
    pin_slot_AoE_R3 = pin_slot_signature_at_eps(0.0506)  # eps_AoE from R3 reading
    pin_slot_AoE_R1 = pin_slot_signature_at_eps(0.157)
    pin_slot_AoE_R2 = pin_slot_signature_at_eps(0.331)
    records.extend([
        {"spike": 33, "version": "v2", "kind": "positive_control_freeth", "eps": 0.1146, "k": pin_slot_freeth},
        {"spike": 33, "version": "v2", "kind": "positive_control_lunar", "eps": 0.054, "k": pin_slot_lunar},
        {"spike": 33, "version": "v2", "kind": "AoE_R3_eps_test", "eps": 0.0506, "k": pin_slot_AoE_R3},
        {"spike": 33, "version": "v2", "kind": "AoE_R1_eps_test", "eps": 0.157, "k": pin_slot_AoE_R1},
        {"spike": 33, "version": "v2", "kind": "AoE_R2_eps_test", "eps": 0.331, "k": pin_slot_AoE_R2},
    ])

    print("Pin-slot direct K-test at canonical eccentricities:")
    for tag, eps, k in [("Freeth 2006", 0.1146, pin_slot_freeth),
                       ("lunar", 0.054, pin_slot_lunar),
                       ("AoE R3", 0.0506, pin_slot_AoE_R3),
                       ("AoE R1", 0.157, pin_slot_AoE_R1),
                       ("AoE R2", 0.331, pin_slot_AoE_R2)]:
        print(f"  {tag:<14s} eps={eps:.4f}  r2={k['r_squared']:.4f}  eps_fit={k['eps_fit']:.4f}  "
              f"K={'PASS' if k['present'] else 'fail'}")

    # Two-axis discriminator at the three Q2 eps values
    print()
    print("Two-axis discriminator (AoE observer sees K; off-axis sees pure circle):")
    for eps_val, label in [(0.0506, "R3 / 1-cos"),
                           (0.157, "R1 / sin/2"),
                           (0.331, "R2 / tan")]:
        result = two_axis_test(1024, eps_val)
        records.append({"spike": 33, "version": "v2", "kind": f"two_axis_test_{label.replace(' ', '_').replace('/', '_')}",
                       **result})
        on_k = result["on_axis_observer"]["k_signature"]["present"]
        off_k = result["off_axis_observer"]["k_signature"]["present"]
        disc = result["discriminator_works"]
        print(f"  eps_AoE={eps_val:.4f} ({label:<14s})  on-axis K={on_k}  off-axis K={off_k}  "
              f"discriminator={'WORKS' if disc else 'FAILS'}")

    # Sweep observer offset to find where K signature DOES emerge
    print()
    print("Observer-offset sweep — at what eps does K-signature first appear?")
    eps_grid = [0.001, 0.005, 0.01, 0.02, 0.05, 0.1, 0.157, 0.2, 0.3, 0.331, 0.4, 0.5]
    sweep_records = []
    for e in eps_grid:
        result = substrate_with_offset_observer(1024, e, e)
        sweep_records.append({"eps_observer": e, "k_signature": result["k_signature"]})
        k = result["k_signature"]
        print(f"  eps={e:.4f}  r2={k['r_squared']:.4f}  eps_fit={k['eps_fit']:.4f}  "
              f"mono={'Y' if k['monotonic'] else 'N'}  K={'PASS' if k['present'] else 'fail'}")
    records.append({"spike": 33, "version": "v2", "kind": "observer_offset_sweep",
                   "sweep": sweep_records})

    emit(records, out_path)
    print(f"\nv2 NDJSON written: {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
