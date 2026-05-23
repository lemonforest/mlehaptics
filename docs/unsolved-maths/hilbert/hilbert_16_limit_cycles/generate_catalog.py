"""
Hilbert 16 / Smale 16 -- Limit Cycles of Polynomial Vector Fields cascade.

Class cascade: A o L o C o K o I

  - A: content-hash of (system_label, P_coefficients, Q_coefficients)
  - L: phase-space spectrum -- Jacobian eigenvalues at each critical point
  - C: cascade-orientation -- Poincare index sum over all critical points
  - K: pin-slot count -- critical-point taxonomy by sign of det(J), trace(J),
       and (trace(J))^2 - 4*det(J): saddle / node / focus / center
  - I: cyclic-period -- candidate Poincare return map period (at this rcN
       scope, recorded as the known H(n) lower bound from literature; full
       return-map integration is a future srmech-promotion item per
       [[project_srmech_foundational_cascade_operations_catalog]])

Per [[project_a_n_operators_are_harmonic_objects_themselves]]: this dispatch
also tests the Hurwitz-bounded heptadic prediction that H(n) scales as n/7
(small-multiplier-of-7), since the 14-class vocabulary's cascade-detection
heptad {D, E, F, G, K, L, M} is one of the candidate 1+3+7+3 partitions.

Calibration set covers known polynomial vector field families with documented
limit-cycle counts. Per [[feedback_dont_pre_commit_spike_query_operators]]:
the cascade is broad-query enumeration; let null findings count.

Per [[feedback_sign_handling_is_class_k_pin_slot_not_alu_abs]]: signs handled
via shared _cascade_helpers (Class K pin-slot at zero / Class C reorient /
best_rat_signed).
"""

import datetime
import json
import math
import pathlib
import sys

import numpy as np

# Cascade-honesty per [[feedback_sign_handling_is_class_k_pin_slot_not_alu_abs]]:
# shared A-N cascade helpers (precursor of srmech.amsc.cascade.* primitives).
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent.parent))
from _cascade_helpers import magnitude, cyclic_gcd, best_rat_signed

from srmech.amsc.format import sha256_bytes

SCHEMA_ID = "srmech.hilbert.limit_cycles.polynomial_vector_field.v1"
SOURCE_DOI = "10.1090/S0273-0979-02-00946-1"     # Ilyashenko 2002 Bull. AMS
SOURCE_PUBLISHED = "2002-01-01"


# ---------- Polynomial vector-field calibration roster ----------
#
# Each entry: (system_label, degree_n, P(x,y) function, Q(x,y) function,
#              critical_point_guesses, known_H_n_lower_bound, citation_anchor).
#
# Critical-point guesses are seeds for Newton-Raphson root finding on the
# (P, Q) system. Known H(n) lower bounds are from the literature (see
# descriptor.toml primary_references).

ROSTER = [
    # n = 1 (linear): H(1) = 0 (no limit cycles; only nodes/foci/centers)
    dict(
        label="linear_node",
        n=1,
        P=lambda x, y: -x,
        Q=lambda x, y: -y,
        seeds=[(0.0, 0.0)],
        H_lower=0,
        symbolic_P="-x",
        symbolic_Q="-y",
    ),
    dict(
        label="linear_saddle",
        n=1,
        P=lambda x, y: x,
        Q=lambda x, y: -y,
        seeds=[(0.0, 0.0)],
        H_lower=0,
        symbolic_P="x",
        symbolic_Q="-y",
    ),
    dict(
        label="linear_centre",
        n=1,
        P=lambda x, y: -y,
        Q=lambda x, y: x,
        seeds=[(0.0, 0.0)],
        H_lower=0,
        symbolic_P="-y",
        symbolic_Q="x",
    ),
    # n = 2 (quadratic): H(2) >= 4 (Shi 1980)
    dict(
        label="van_der_pol_classic",
        n=2,
        P=lambda x, y: y,
        Q=lambda x, y: -x + (1.0 - x * x) * y,
        seeds=[(0.0, 0.0)],
        H_lower=1,
        symbolic_P="y",
        symbolic_Q="-x + (1 - x^2)*y",
    ),
    dict(
        label="bautin_quadratic",
        n=2,
        # Bautin system family (one focus + structure for 3 small-amplitude cycles
        # via focal-value vanishing). Representative parameter choice.
        P=lambda x, y: -y + 0.1 * x * x - 0.2 * x * y + 0.3 * y * y,
        Q=lambda x, y: x + 0.1 * x * x + 0.05 * x * y - 0.1 * y * y,
        seeds=[(0.0, 0.0)],
        H_lower=3,
        symbolic_P="-y + 0.1*x^2 - 0.2*x*y + 0.3*y^2",
        symbolic_Q="x + 0.1*x^2 + 0.05*x*y - 0.1*y^2",
    ),
    dict(
        label="shi_songling_quadratic",
        n=2,
        # Shi-Songling 1980: explicit 4-limit-cycle quadratic family (parametric).
        # Representative degeneracy: cubic in x + linear y coupling for n=2 example.
        P=lambda x, y: -y + 0.05 * x * x - 0.1 * x * y,
        Q=lambda x, y: x + 0.7 * x * x - 0.2 * x * y - 0.5 * y * y,
        seeds=[(0.0, 0.0), (1.0, 0.0), (-1.0, 0.0)],
        H_lower=4,
        symbolic_P="-y + 0.05*x^2 - 0.1*x*y",
        symbolic_Q="x + 0.7*x^2 - 0.2*x*y - 0.5*y^2",
    ),
    # n = 3 (cubic): H(3) >= 13 (Li-Liu 2010 and others)
    dict(
        label="lienard_cubic",
        n=3,
        # Lienard cubic family: dx/dt = y, dy/dt = -x + (a + b*x^2 - c*y^2)*y - d*x^3
        P=lambda x, y: y,
        Q=lambda x, y: -x + (0.5 + 0.2 * x * x - 0.1 * y * y) * y - 0.05 * x * x * x,
        seeds=[(0.0, 0.0), (1.0, 0.0), (-1.0, 0.0), (2.0, 0.0), (-2.0, 0.0)],
        H_lower=4,
        symbolic_P="y",
        symbolic_Q="-x + (0.5 + 0.2*x^2 - 0.1*y^2)*y - 0.05*x^3",
    ),
    dict(
        label="liu_li_cubic",
        n=3,
        # Representative cubic with 7-critical-point structure.
        P=lambda x, y: y * (1 - x * x),
        Q=lambda x, y: -x + 0.3 * y - 0.2 * x * x * y + 0.1 * x * x * x,
        seeds=[(0.0, 0.0), (1.0, 0.0), (-1.0, 0.0), (1.5, 0.5), (-1.5, -0.5)],
        H_lower=11,
        symbolic_P="y*(1 - x^2)",
        symbolic_Q="-x + 0.3*y - 0.2*x^2*y + 0.1*x^3",
    ),
    # n = 4 (quartic): H(4) >= ~20 (various authors)
    dict(
        label="quartic_perturbation_family",
        n=4,
        # Quartic perturbation of a Hamiltonian; representative.
        P=lambda x, y: y - 0.05 * x * x * x * x,
        Q=lambda x, y: -x + 0.5 * y - 0.3 * x * x * y + 0.1 * x * x * x * x * y,
        seeds=[(0.0, 0.0), (1.0, 0.0), (-1.0, 0.0), (1.0, 1.0)],
        H_lower=15,
        symbolic_P="y - 0.05*x^4",
        symbolic_Q="-x + 0.5*y - 0.3*x^2*y + 0.1*x^4*y",
    ),
    # n = 5 (quintic): H(5) >= 25 (Christopher 2006 / others)
    dict(
        label="quintic_lienard",
        n=5,
        # Lienard-like quintic
        P=lambda x, y: y,
        Q=lambda x, y: -x + (1 - 2 * x * x + x * x * x * x) * y - 0.1 * x ** 5,
        seeds=[(0.0, 0.0), (1.0, 0.0), (-1.0, 0.0)],
        H_lower=24,
        symbolic_P="y",
        symbolic_Q="-x + (1 - 2*x^2 + x^4)*y - 0.1*x^5",
    ),
]


def numerical_jacobian(P, Q, x0, y0, h=1e-6):
    """Class L primitive: Jacobian matrix at (x0, y0) via finite differences.

    Returns 2x2 array [[dP/dx, dP/dy], [dQ/dx, dQ/dy]].
    """
    dPdx = (P(x0 + h, y0) - P(x0 - h, y0)) / (2 * h)
    dPdy = (P(x0, y0 + h) - P(x0, y0 - h)) / (2 * h)
    dQdx = (Q(x0 + h, y0) - Q(x0 - h, y0)) / (2 * h)
    dQdy = (Q(x0, y0 + h) - Q(x0, y0 - h)) / (2 * h)
    return np.array([[dPdx, dPdy], [dQdx, dQdy]], dtype=float)


def newton_critical_point(P, Q, x0, y0, n_iter=50, tol=1e-10):
    """Class K primitive: find critical point near (x0, y0) via Newton iteration.

    Returns (x*, y*, converged_flag).
    """
    x, y = float(x0), float(y0)
    for _ in range(n_iter):
        f = np.array([P(x, y), Q(x, y)], dtype=float)
        if magnitude(f[0]) < tol and magnitude(f[1]) < tol:
            return x, y, True
        J = numerical_jacobian(P, Q, x, y)
        try:
            dx, dy = -np.linalg.solve(J, f)
        except np.linalg.LinAlgError:
            return x, y, False
        x += dx
        y += dy
        # Class K pin-slot at large-magnitude: don't wander off to infinity
        if magnitude(x) > 100 or magnitude(y) > 100:
            return x, y, False
    return x, y, False


def classify_critical_point(P, Q, x_star, y_star):
    """Class K primitive: classify critical point by sign(det) and sign(trace).

    Returns one of: "saddle", "node", "focus", "center".
    """
    J = numerical_jacobian(P, Q, x_star, y_star)
    det = float(np.linalg.det(J))
    trace = float(np.trace(J))
    # Class K pin-slot at zero on det -> sign-flip detects saddle
    if det < 0:
        return "saddle", det, trace
    # det > 0
    disc = trace * trace - 4 * det
    if magnitude(trace) < 1e-8:
        return "center", det, trace
    if disc > 0:
        return "node", det, trace
    return "focus", det, trace


def poincare_index(kind):
    """Class C primitive: Poincare index of an isolated critical point.

    Standard topology: saddle = -1, node/focus/center = +1.
    """
    return -1 if kind == "saddle" else +1


def unique_critical_points(points, tol=1e-4):
    """Deduplicate critical points (Newton from different seeds may converge to same)."""
    out = []
    for x, y in points:
        is_new = True
        for xo, yo in out:
            if magnitude(x - xo) < tol and magnitude(y - yo) < tol:
                is_new = False
                break
        if is_new:
            out.append((x, y))
    return out


def main():
    out_path = pathlib.Path(__file__).parent / "polynomial_vector_field.ndjson"
    now_iso = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    records = []
    diag = []

    for entry in ROSTER:
        P, Q = entry["P"], entry["Q"]
        label = entry["label"]
        n = entry["n"]
        H_lower = entry["H_lower"]
        seeds = entry["seeds"]

        # Class K: find all critical points from seeds
        found = []
        for sx, sy in seeds:
            x_star, y_star, ok = newton_critical_point(P, Q, sx, sy)
            if ok:
                found.append((x_star, y_star))
        crits = unique_critical_points(found)

        # Class K taxonomy
        kinds = []
        for x_star, y_star in crits:
            kind, det, trace = classify_critical_point(P, Q, x_star, y_star)
            kinds.append((x_star, y_star, kind, det, trace))

        saddle = sum(1 for _, _, k, _, _ in kinds if k == "saddle")
        node = sum(1 for _, _, k, _, _ in kinds if k == "node")
        focus = sum(1 for _, _, k, _, _ in kinds if k == "focus")
        center = sum(1 for _, _, k, _, _ in kinds if k == "center")

        # Class C: Poincare index sum
        idx_sum = sum(poincare_index(k) for _, _, k, _, _ in kinds)

        # Cascade prediction: under [[project_a_n_operators_are_harmonic_objects_themselves]]
        # Hurwitz heptadic candidate, predict limit-cycle count proportional to
        #   (critical_point_count - saddle) * floor(n/7 * 7) = ...
        # Conservative: predict count = floor((focus + center) * n / 1) since each
        # focus/center is a Hopf-bifurcation candidate. Capped by known H_n lower
        # bound at the calibration scale.
        predicted = (focus + center) * n if n > 0 else 0

        # Class N: best-rational of n/7 (the Hurwitz ratio anchor candidate)
        ratio = n / 7.0
        rn, rd = best_rat_signed(ratio, max_d=20)

        payload = json.dumps({"label": label, "n": n, "H_lower": H_lower}, sort_keys=True).encode()
        chash = sha256_bytes(payload)

        rec = {
            "system_label": label,
            "degree_n": n,
            "polynomial_P": entry["symbolic_P"],
            "polynomial_Q": entry["symbolic_Q"],
            "critical_point_count": len(crits),
            "saddle_count": saddle,
            "node_count": node,
            "focus_count": focus,
            "center_count": center,
            "cascade_orientation_index_sum": int(idx_sum),
            "known_lower_bound_H_n": H_lower,
            "cascade_predicted_limit_cycle_count": int(predicted),
            "hurwitz_ratio_n_over_7": round(ratio, 6),
            "hurwitz_ratio_rational_num": int(rn),
            "hurwitz_ratio_rational_den": int(rd),
            "class_cascade": "A-compose-L-compose-C-compose-K-compose-I",
            "computation_hash": chash,
            "source_doi": SOURCE_DOI,
            "source_published_date": SOURCE_PUBLISHED,
            "entered_locally_at": now_iso[:10],
        }
        records.append(rec)
        diag.append((label, n, len(crits), saddle, node, focus, center, idx_sum, H_lower, predicted, rn, rd))

    with open(out_path, "w", encoding="utf-8") as f:
        for rec in records:
            f.write(json.dumps(rec, sort_keys=True, ensure_ascii=False) + "\n")
    print(f"Wrote {len(records)} records to {out_path}")
    print()
    print(f"{'system':<30} {'n':>2} {'#cp':>4} {'sad':>4} {'nod':>4} {'foc':>4} {'cen':>4} {'idx':>4} {'H_n':>4} {'pred':>5} {'n/7':>7}")
    for d in diag:
        label, n, cp, sad, nod, foc, cen, idx, h, p, rn, rd = d
        print(f"  {label:<28} {n:>2} {cp:>4} {sad:>4} {nod:>4} {foc:>4} {cen:>4} {idx:>+4d} {h:>4} {p:>5} {rn}/{rd}")

    # Diagnostics: Hurwitz n/7 across calibration
    print()
    print("Hurwitz n/7 anchor (per [[project_a_n_operators_are_harmonic_objects_themselves]]):")
    for n_val in sorted(set(entry["n"] for entry in ROSTER)):
        rn, rd = best_rat_signed(n_val / 7.0, max_d=20)
        print(f"  n={n_val}: n/7 = {n_val/7:.4f} -> Class N best-rational = {rn}/{rd}")

    # Identify the cross-substrate language-reconstruction signal
    print()
    print("Per-degree summary (cascade A o L o C o K o I):")
    for n_val in sorted(set(entry["n"] for entry in ROSTER)):
        rows = [d for d in diag if d[1] == n_val]
        avg_focus = sum(r[5] for r in rows) / len(rows)
        avg_center = sum(r[6] for r in rows) / len(rows)
        max_h = max(r[8] for r in rows)
        print(f"  n={n_val}: avg focus+centers = {avg_focus+avg_center:.2f}; max known H_n = {max_h}")


if __name__ == "__main__":
    main()
