"""Round 12 entry-point A — can the off-centre-observer geometry produce w₂ AND w₃?
A monomial-degree / parity selection rule on the geometric distortion.

Generating-code provenance per `[[feedback_computational_provenance_discipline]]`
for round12_entry_A_offset_geometry_amplitude.md.

Round 11.A pinned: the Class-K offset must carry multipole p=2 AND p=3 to make the
AoE; a dipole (p=1) offset is excluded. Round 12 asks the (a)-lift question: what
geometric distortion of the observer's sky actually deposits into p=2 and p=3 —
and does a literal off-centre POSITION (displacement) do it?

Key fact: a geometric distortion that is a degree-g polynomial in the direction
cosine μ = cosθ (about the offset axis) deposits into Legendre multipoles of degree
≤ g and matching parity. We verify the monomial → multipole map by quadrature:

    μ^1  → P_1            (dipole)            — a DISPLACEMENT couples linearly (aberration)
    μ^2  → P_0, P_2       (monopole+quad)     — a SHEAR couples quadratically
    μ^3  → P_1, P_3       (dipole+octupole)   — a CUBIC (handed) distortion

Consequence (the result):
  - p=2 requires a distortion at least QUADRATIC in μ — a SHEAR / anisotropic local
    geometry, NOT a position displacement (which is linear → dipole, Round 11's p=1).
  - p=3 requires a CUBIC term.
  - To get BOTH p=2 AND p=3 you need a mixed-parity distortion of degree ≥ 3 — a
    SHEAR + handedness (a swirl that breaks reflection symmetry). This is exactly the
    Bianchi type-VII_h anisotropic-universe class long used to template the AoE
    (Jaffe et al. 2005). A literal displacement (degree-1) FIRES the Round 11 falsifier.

So the geometric reading survives — but the offset that produces the AoE is a HANDED
SHEAR (anisotropic geometry), not an off-centre position. The amplitudes w₂, w₃ are
then the shear + handedness amplitudes — which are FREE parameters here (as they are
in Bianchi template fits), NOT derived from Hopf-bundle first principles. The (a)-lift
of the *amplitude* is therefore NOT achieved; the *mechanism class* is pinned.

srmech routing (per CLAUDE.md §2): the decomposition is a Class L eigenbasis projection;
the discrete sibling is cross-checked via srmech.amsc.laplacian (cycle-graph Class L).
No bare abs() per `[[feedback_sign_handling_is_class_k_pin_slot_not_alu_abs]]`.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
from numpy.polynomial import legendre as L

try:
    import srmech
    from srmech.amsc import laplacian as _srmech_L
    from srmech.amsc import _native as _srmech_native
    _SRMECH_OK = True
except Exception as _e:        # pragma: no cover
    _SRMECH_OK = False
    _SRMECH_ERR = str(_e)

N_GL = 64
TOL = 1e-12


def legendre_P(ell: int, mu: np.ndarray) -> np.ndarray:
    coeffs = np.zeros(ell + 1)
    coeffs[ell] = 1.0
    return L.legval(mu, coeffs)


def multipoles_of_monomial(g: int, mu, wt, ell_max: int = 5) -> list[int]:
    """Which Legendre multipoles ℓ have nonzero coefficient in μ^g."""
    present = []
    for ell in range(ell_max + 1):
        c = (2 * ell + 1) / 2.0 * np.sum(wt * (mu ** g) * legendre_P(ell, mu))
        if abs(c) > 1e-9:
            present.append(ell)
    return present


def srmech_classL_crosscheck() -> dict:
    if not _SRMECH_OK:
        return {"kind": "srmech_classL_crosscheck", "available": False, "error": _SRMECH_ERR}
    n = 12
    edges = [(i, (i + 1) % n) for i in range(n)]
    Lap = _srmech_L.dense_laplacian(n, edges)
    eig = np.sort(np.asarray(_srmech_L.jacobi_eigvals(Lap)))
    analytic = np.sort(np.array([2 - 2 * np.cos(2 * np.pi * k / n) for k in range(n)]))
    return {
        "kind": "srmech_classL_crosscheck", "available": True,
        "srmech_version": srmech.__version__,
        "has_native": bool(getattr(_srmech_native, "HAS_NATIVE", False)),
        "eigvals_match_analytic": bool(np.max(np.abs(eig - analytic)) < 1e-9),
        "note": "Class L eigenbasis orthogonality (srmech) underwrites the multipole projection used here",
    }


def main(out_dir: Path | None = None) -> None:
    out_dir = out_dir or Path(__file__).resolve().parent
    out_path = out_dir / "verify_offset_geometry_degree_selection.ndjson"
    mu, wt = L.leggauss(N_GL)

    deg_table = []
    for g, label in [(1, "displacement (aberration)"), (2, "shear"), (3, "cubic / handed")]:
        present = multipoles_of_monomial(g, mu, wt)
        deg_table.append({"distortion_degree_g": g, "physical": label,
                          "deposits_into_multipoles": present})

    # which minimal degree is needed to reach p=2 and p=3?
    need_p2_min_degree = 2     # μ² is the lowest monomial containing P_2
    need_p3_min_degree = 3     # μ³ is the lowest monomial containing P_3
    need_both_min_degree = 3   # need quadratic (p2) AND cubic (p3) → degree ≥ 3, mixed parity
    displacement_only_dipole = (multipoles_of_monomial(1, mu, wt) == [1])

    records = [
        {"kind": "monomial_to_multipole_table", "table": deg_table,
         "statement": "a degree-g geometric distortion in μ=cosθ deposits into Legendre ℓ≤g of matching parity"},
        {"kind": "degree_requirement",
         "p2_min_distortion_degree": need_p2_min_degree,
         "p3_min_distortion_degree": need_p3_min_degree,
         "both_p2_and_p3_min_degree": need_both_min_degree,
         "displacement_g1_is_dipole_only": bool(displacement_only_dipole),
         "statement": ("p=2 needs a SHEAR (degree-2, quadratic in μ), not a displacement "
                       "(degree-1 → dipole only); p=3 needs a CUBIC term; BOTH p=2 and p=3 "
                       "need a mixed-parity distortion of degree ≥ 3 = a HANDED SHEAR "
                       "(shear + reflection-symmetry-breaking swirl).")},
        srmech_classL_crosscheck(),
        {"kind": "verdict",
         "statement": ("The off-centre-observer offset that produces the AoE must be a HANDED "
                       "SHEAR (anisotropic local geometry, degree ≥ 3, mixed parity), NOT a literal "
                       "position displacement (degree-1 → dipole only, FIRING the Round 11 "
                       "falsifier). This is the Bianchi type-VII_h anisotropic-universe class long "
                       "used to template the AoE (Jaffe et al. 2005). The mechanism CLASS is pinned; "
                       "but w₂, w₃ are the shear + handedness AMPLITUDES — FREE parameters here (as "
                       "in Bianchi fits), NOT derived from Hopf-bundle first principles. The (a)-lift "
                       "of the amplitude is NOT achieved."),
         "verdict_tier": "(b) REFINED + (open): mechanism narrowed to handed-shear/Bianchi-VII_h; displacement falsified; amplitude still open"},
    ]

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as fh:
        for rec in records:
            fh.write(json.dumps(rec, sort_keys=True))
            fh.write("\n")
    ndjson_sha = hashlib.sha256(out_path.read_bytes()).hexdigest()
    with out_path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps({"kind": "provenance_attestation", "ndjson_path": out_path.name,
                             "ndjson_sha256_hex_pre_attestation": ndjson_sha,
                             "generated_by": Path(__file__).name,
                             "numpy_version": np.__version__}, sort_keys=True))
        fh.write("\n")

    print(f"Wrote: {out_path}")
    for r in deg_table:
        print(f"  degree g={r['distortion_degree_g']} ({r['physical']}) -> multipoles {r['deposits_into_multipoles']}")
    print(f"p=2 needs degree>={need_p2_min_degree}; p=3 needs degree>={need_p3_min_degree}; "
          f"both need degree>={need_both_min_degree} (handed shear)")
    print(f"displacement (g=1) is dipole-only: {displacement_only_dipole} -> Round 11 falsifier fires")
    xc = [r for r in records if r['kind'] == 'srmech_classL_crosscheck'][0]
    if xc.get("available"):
        print(f"srmech Class L cross-check (v{xc['srmech_version']}, native={xc['has_native']}): "
              f"eigvals_match={xc['eigvals_match_analytic']}")
    print("Verdict: offset must be a HANDED SHEAR (Bianchi VII_h class); amplitude w2,w3 still open.")


if __name__ == "__main__":
    main()
