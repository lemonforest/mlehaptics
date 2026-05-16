"""Spike #30B v4 — sweep K-signature across all 51 ephemerides bodies.

Test: does K-signature appear with consistent geometric-decay shape across
EVERY non-circular body? This is the strongest convergence test —
51 independent realisations of the same Kepler-shape signature.
"""

from __future__ import annotations

import json
import math
import sys

import numpy as np

sys.path.insert(0, "D:/GitHub/mlehaptics/docs/srmech/python")
from srmech.amsc import kepler  # noqa: E402


def eoc_signal(eps: float, n: int = 2048) -> np.ndarray:
    M_grid = np.linspace(0, 2 * math.pi, n, endpoint=False)
    out = np.zeros(n)
    for i, M in enumerate(M_grid):
        if eps >= 1.0:
            return None  # not orbital
        try:
            E = kepler.kepler_solve(M_rad=float(M), e=eps)
        except Exception:
            return None
        nu = 2.0 * math.atan2(
            math.sqrt(1 + eps) * math.sin(E / 2),
            math.sqrt(1 - eps) * math.cos(E / 2),
        )
        d = nu - M
        while d > math.pi:
            d -= 2 * math.pi
        while d < -math.pi:
            d += 2 * math.pi
        out[i] = d
    return out


def strict_kepler_test(coeffs: np.ndarray, k_max: int = 6) -> dict:
    abs_c = np.abs(coeffs)
    cs = abs_c[1: k_max + 1]
    ks = np.arange(1, len(cs) + 1)
    floor = max(1e-15, abs_c.max() * 1e-12)
    mask = cs > floor
    if mask.sum() < 3:
        return {"eps_fit": float("nan"), "r2": 0.0, "kepler_signature_present": False, "n_used": int(mask.sum())}
    ks_used = ks[mask]
    cs_used = cs[mask]
    log_c = np.log(cs_used)
    p = np.polyfit(ks_used, log_c, 1)
    eps_fit = math.exp(p[0])
    yhat = np.polyval(p, ks_used)
    ss_res = ((log_c - yhat) ** 2).sum()
    ss_tot = ((log_c - log_c.mean()) ** 2).sum()
    r2 = 1.0 - (ss_res / ss_tot if ss_tot > 1e-15 else 1.0)
    monotonic = bool(np.all(np.diff(cs_used) < 0))
    in_range = bool(0.001 < eps_fit < 0.5)
    high_r2 = bool(r2 > 0.99)
    return {
        "eps_fit": float(eps_fit),
        "r2": float(r2),
        "monotonic": monotonic,
        "in_range": in_range,
        "high_r2": high_r2,
        "kepler_signature_present": bool(monotonic and in_range and high_r2),
        "n_used": int(len(ks_used)),
    }


def fft_coeffs(signal: np.ndarray) -> np.ndarray:
    spec = np.fft.rfft(signal) / (len(signal) / 2)
    return np.abs(spec)


def main():
    # Load real ephemerides data
    path = "D:/GitHub/mlehaptics/docs/antikythera-maths/research/attested/secular_elements/row.ndjson"
    rows = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            try:
                row = json.loads(line)
                rows.append(row)
            except json.JSONDecodeError:
                pass
    print(f"Loaded {len(rows)} secular-element rows.")

    # Run K-test on each
    results = []
    for row in rows:
        body = row["body"]
        eps = row["e"]
        if eps <= 0:
            continue
        sig = eoc_signal(eps)
        if sig is None:
            continue
        c = fft_coeffs(sig)
        K = strict_kepler_test(c)
        results.append({
            "body": body,
            "e_actual": eps,
            **K,
        })

    # Summary
    print(f"\n{'Body':25s} {'e_actual':10s} {'eps_fit':10s} {'r2':10s} {'monoton':10s} "
          f"{'in_range':10s} {'high_r2':10s} {'KEPLER':10s}")
    print("-" * 110)
    n_kepler = 0
    for r in sorted(results, key=lambda r: r["e_actual"]):
        flag = "YES" if r["kepler_signature_present"] else "NO "
        if r["kepler_signature_present"]:
            n_kepler += 1
        print(f"{r['body']:25s} {r['e_actual']:10.4f} {r.get('eps_fit', float('nan')):10.4f} "
              f"{r['r2']:10.4f} {str(r.get('monotonic', 'NA')):10s} "
              f"{str(r.get('in_range', 'NA')):10s} {str(r.get('high_r2', 'NA')):10s} {flag:10s}")
    print(f"\nKepler-signature present: {n_kepler} / {len(results)} bodies tested")

    # NDJSON output
    with open("D:/temp/spike_30b/spike_30b_v4_cross_bodies.ndjson", "w") as f:
        for r in results:
            f.write(json.dumps(r) + "\n")
    print(f"\nWrote {len(results)} body records to spike_30b_v4_cross_bodies.ndjson")


if __name__ == "__main__":
    main()
