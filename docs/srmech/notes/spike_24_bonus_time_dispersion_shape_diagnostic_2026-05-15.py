"""Bonus 9 follow-up diagnostic — dispersion shape of the directed cascade.

The primary probe found h1_signature_present=True (95.2% complex eigenvalues,
healthy conjugate pairing) but KG dispersion R^2 = 0.239 (poor linear fit;
slope 2.51 vs expected 1.0). This diagnostic explores the dispersion SHAPE
to discriminate which hypothesis fits.

Algebraic preliminary:
  Cyclic-shift eigenvalue: omega_k = exp(2*pi*i*k/n)
  Directed Laplacian eigenvalue: lambda_k = 1 - omega_k = (1-cos) - i*sin
  Re(lambda_k) = 1 - cos(theta_k)
  Im(lambda_k) = -sin(theta_k)
  Identity: Re^2 + Im^2 = (1-cos)^2 + sin^2 = 2(1-cos) = 2*Re

So: Im^2 = 2*Re - Re^2  -- a CIRCLE in (Re, Im) space, not a HYPERBOLA.

Klein-Gordon dispersion: omega^2 = c^2 k^2 + m^2  -- a HYPERBOLA in (k^2, omega).

The directed cyclic-shift naturally produces CIRCULAR dispersion. Is this
compatible with KG (via some primitive class operation already in A-N)?
Or does the circular-vs-hyperbolic gap need a new primitive?

Three discriminators:
  (a) Re^2 + Im^2 vs 2*Re: how tightly does the circle identity hold?
      (Should be ~exact for individual factor eigenvalues; the sum-product
      composition will deform this.)
  (b) Im^2 vs Re (linear fit): slope close to 1 = KG-like; close to 2 = circle-like.
  (c) Im^2 vs Re^2: any quadratic-relation signature?
"""

from __future__ import annotations

import math
import json
from pathlib import Path
import numpy as np


SEED = 20260515
PROBE = "spike_24_bonus_time_dispersion_shape_diagnostic_2026-05-15"


def cyclic_shift_eigs(n: int) -> np.ndarray:
    k = np.arange(n)
    return np.exp(2.0j * math.pi * k / n)


def cyclic_dir_eigs(n: int, r: float = 1.0) -> np.ndarray:
    return (1.0 / r**2) * (1.0 - cyclic_shift_eigs(n))


def product_sum_complex(spectra, topN):
    cur = np.array(spectra[0], dtype=np.complex128)
    cur = cur[np.argsort(cur.real)]
    for sp in spectra[1:]:
        sp = np.array(sp, dtype=np.complex128)
        sp = sp[np.argsort(sp.real)]
        flat = (cur[:, None] + sp[None, :]).ravel()
        order = np.lexsort((np.abs(flat.imag), flat.real))
        flat = flat[order]
        keep = min(len(flat), max(topN, 4 * topN))
        cur = flat[:keep]
    order = np.lexsort((np.abs(cur.imag), cur.real))
    return cur[order][:topN]


def emit(path, rec):
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(rec, separators=(",", ":"), sort_keys=False))
        f.write("\n")


def analyze_dispersion(name, eigs, out_path):
    """Run the three discriminators on a complex eigenvalue array."""
    re = eigs.real
    im = eigs.imag
    n = len(eigs)

    # (a) Circle identity: Im^2 ?= 2*Re - Re^2 (at unit radius / r=1)
    circle_residual = np.abs(im**2 - (2 * re - re**2))
    circle_residual_median = float(np.median(circle_residual))
    circle_residual_max = float(circle_residual.max())

    # (b) Linear KG fit: Im^2 vs Re; mask Re > tiny
    mask = np.abs(re) > 1e-9
    if mask.sum() >= 4:
        coef_lin = np.polyfit(re[mask], im[mask]**2, deg=1)
        slope_lin = float(coef_lin[0])
        intercept_lin = float(coef_lin[1])
        pred = np.polyval(coef_lin, re[mask])
        ss_res = float(np.sum((im[mask]**2 - pred)**2))
        ss_tot = float(np.sum((im[mask]**2 - im[mask][mask.sum() and 0:].mean() if False else (im[mask]**2).mean())**2))
        # Simpler R^2 calc
        y = im[mask]**2
        r_sq_lin = 1.0 - ss_res / float(np.sum((y - y.mean())**2)) if y.var() > 0 else 0.0
    else:
        slope_lin = float("nan")
        intercept_lin = float("nan")
        r_sq_lin = float("nan")

    # (c) Quadratic in Re: Im^2 = a*Re + b*Re^2 + c (circle identity gives a=2, b=-1, c=0)
    if mask.sum() >= 4:
        re_m = re[mask]
        im2_m = im[mask]**2
        X = np.stack([re_m, re_m**2, np.ones_like(re_m)], axis=1)
        coefs, residuals, rank, _ = np.linalg.lstsq(X, im2_m, rcond=None)
        a_quad, b_quad, c_quad = float(coefs[0]), float(coefs[1]), float(coefs[2])
        pred = X @ coefs
        ss_res_q = float(np.sum((im2_m - pred)**2))
        ss_tot_q = float(np.sum((im2_m - im2_m.mean())**2))
        r_sq_quad = 1.0 - ss_res_q / ss_tot_q if ss_tot_q > 0 else 0.0
    else:
        a_quad = b_quad = c_quad = r_sq_quad = float("nan")

    # Min |lambda| (zero mode), max |lambda|
    mod = np.abs(eigs)
    mod_min = float(mod.min())
    mod_max = float(mod.max())

    rec = {
        "name": name,
        "n_eigenvalues": n,
        "n_complex": int(np.sum(np.abs(im) > 1e-9)),
        "re_min": float(re.min()),
        "re_max": float(re.max()),
        "im_abs_max": float(np.abs(im).max()),
        "mod_min": mod_min,
        "mod_max": mod_max,
        # Circle identity test
        "circle_identity_residual_median": circle_residual_median,
        "circle_identity_residual_max": circle_residual_max,
        "circle_identity_holds_to_1e6": bool(circle_residual_median < 1e-6),
        # Linear KG fit
        "lin_kg_slope": slope_lin,
        "lin_kg_intercept": intercept_lin,
        "lin_kg_r_squared": r_sq_lin,
        # Quadratic shape (a*Re + b*Re^2 + c)
        "quad_fit_a_coef": a_quad,           # circle: a=2
        "quad_fit_b_coef": b_quad,           # circle: b=-1
        "quad_fit_c_coef": c_quad,           # circle: c=0
        "quad_fit_r_squared": r_sq_quad,     # circle: R^2~1
    }
    emit(out_path, rec)
    return rec


def main():
    out = Path(__file__).with_suffix(".ndjson")
    if out.exists():
        out.unlink()

    emit(out, {
        "phase": "stage0_setup",
        "kind": "preamble",
        "probe": PROBE,
        "purpose": (
            "Discriminate between H1 (cascade composition naturally encodes "
            "KG dispersion via Class C orientation) vs H3 (cascade composition "
            "encodes CIRCULAR dispersion that does not match KG without a "
            "further primitive). Algebraic prediction: cyclic-shift directed "
            "Laplacian eigenvalues satisfy Im^2 = 2*Re - Re^2 (circle of "
            "radius 1 centered at (1,0)), NOT Im^2 = Re + m^2 (hyperbola). "
            "Test how the cascade composition deforms this identity."
        ),
    })

    # Single-factor C_n directed eigenvalues — circle identity should hold exact.
    for n in [8, 16, 32, 64]:
        eigs = cyclic_dir_eigs(n, r=1.0)
        rec = analyze_dispersion(f"single_factor_C{n}", eigs, out)

    # Sum of 2 cyclic-32 factors (2D directed cascade)
    eigs_2D = product_sum_complex([cyclic_dir_eigs(32, 1.0), cyclic_dir_eigs(32, 1.0)], topN=400)
    analyze_dispersion("product_2x_C32_r1", eigs_2D, out)

    # Sum of 3 cyclic-32 factors (3D directed cascade — H1's spatial)
    eigs_3D = product_sum_complex([cyclic_dir_eigs(32, 1.0)] * 3, topN=400)
    analyze_dispersion("product_3x_C32_r1_3D_spatial", eigs_3D, out)

    # Full 10D directed cascade
    spatial = [cyclic_dir_eigs(32, 1.0)] * 3
    gauge_radii = [(3, 0.1), (3, 0.1), (2, 0.1), (5, 0.1), (7, 0.05), (11, 0.05), (13, 0.05)]
    gauge = [cyclic_dir_eigs(n, r) for n, r in gauge_radii]
    eigs_10D = product_sum_complex(spatial + gauge, topN=400)
    analyze_dispersion("product_10D_full_3+7_gauge_radii", eigs_10D, out)

    # Diagnostic: per-mode (Re, Im) for the 3D spatial directed cascade
    rec = {
        "phase": "stage1_per_mode_dump",
        "kind": "3D_spatial_first_40_modes",
        "samples": [
            {
                "i": int(i),
                "re": float(eigs_3D[i].real),
                "im": float(eigs_3D[i].imag),
                "im_sq": float(eigs_3D[i].imag**2),
                "re_predict_circle": float(2*eigs_3D[i].real - eigs_3D[i].real**2),
                "circle_residual": float(eigs_3D[i].imag**2 - (2*eigs_3D[i].real - eigs_3D[i].real**2)),
            }
            for i in range(min(40, len(eigs_3D)))
        ],
    }
    emit(out, rec)

    # The structural question: at what scales does the cascade-sum break the circle identity?
    rec_structural = {
        "phase": "stage2_structural_interpretation",
        "kind": "circle_vs_hyperbola_verdict",
        "single_factor_holds_circle": True,
        "two_factor_breaks_circle": None,  # populated below
        "three_factor_breaks_circle": None,
        "ten_factor_breaks_circle": None,
        "note": (
            "Single-factor directed Laplacian eigenvalues satisfy Im^2 = 2*Re - Re^2 "
            "exactly (algebraic). Direct-product sums introduce cross terms that "
            "deform this. The question is whether the deformation moves the "
            "spectrum toward KG hyperbola (Im^2 = Re + m^2) or stays close to the "
            "compounded-circle shape. If toward hyperbola: H1 wins. If stays "
            "circular: the cascade's intrinsic dispersion is circular, and "
            "matching to KG observed-physics requires a primitive that converts "
            "circular to hyperbolic — that primitive may be Class O or another."
        ),
    }
    emit(out, rec_structural)

    print(f"Diagnostic written to {out}")


if __name__ == "__main__":
    main()
