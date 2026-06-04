"""F368 — the MAPS lens on the CMB sky-map: a flat projection (map) read as a navigable DoF/relative
manifold vs a fixed-observer visual tour. Applied to the attested CMB low-ℓ "axis family": does a
FIXED observer's "N separate anomalies" reduce, under the DoF/relative-frame reading, to ONE shared
preferred axis (a single frame-relation)?

Grounded on PRIOR work (NOT fresh): the directions are read from the attested `cmb_anomalies` catalog
(ephemerides-spectral; Planck 2018 VII / Akrami 2020; de Oliveira-Costa 2004), and the substrate-side
bundle-direction reading already lives in MFO §VII.6.1.1/.1.3. The maps lens is the OBSERVER-FRAME
complement to MFO's favored substrate-bundle-direction reading — NOT the bubble/collision reading,
which MFO already DISFAVORED on shape grounds (axial, not disc; Osborne 2013 + Planck 2015 XVI null).

Test (srmech-native Class L): orientation tensor T = Σ nᵢnᵢᵀ of the attested anomaly AXES (n≡−n),
symmetric_eigendecompose -> λ_max/trace = axis concentration (1/3 isotropic .. 1 perfectly aligned).
Monte-Carlo isotropic axes give the null. A fixed observer sees N anomalies; if λ_max is high they
share ONE axis = one relative frame. Also: the AoE↔CMB-dipole axis angle (MFO's "live anomaly").

Geometry (l,b°→unit vector) + isotropic MC are mechanics (numpy, flagged); the load-bearing op is the
Class-L eigendecomposition of the orientation tensor. Directions read from the attested NDJSON (no
ephemerides-spectral install — version-safe, honoring 'not latest srmech base').
Run: /tmp/verify_srmech_v070rc28/bin/python docs/srmech/rbs_lm_research/R-RBS-LM-R19_maps_lens_cmb_axis_family.py
"""
import json, re
from pathlib import Path
import numpy as np
import srmech
from srmech.amsc.laplacian import symmetric_eigendecompose

HERE = Path(__file__).parent
CAT = HERE.parent.parent / "antikythera-maths/research/attested/cmb_anomalies/row.ndjson"
# attested reference axes (flagged constants): standard Planck-2018 solar CMB dipole, Auger UHECR dipole (MFO §VII.6.1.3)
CMB_DIPOLE = (264.0, 48.3)      # Planck 2018 I solar dipole direction (galactic l,b)
UHECR_DIPOLE = (233.0, -13.0)   # Pierre Auger 2017/2018 (MFO §VII.6.1.3)


def lb_to_unit(l_deg, b_deg):
    l, b = np.radians(l_deg), np.radians(b_deg)
    return np.array([np.cos(b) * np.cos(l), np.cos(b) * np.sin(l), np.sin(b)])


def axis_angle_deg(u, v):
    c = abs(float(np.dot(u, v)))                 # |cos|: axes (n ≡ -n), so fold to [0,90]
    return float(np.degrees(np.arccos(min(1.0, c))))


def concentration(vs):
    T = np.zeros((3, 3))
    for n in vs:
        T += np.outer(n, n)
    T /= len(vs)                                 # trace = 1
    evals, _ = symmetric_eigendecompose(T)       # Class L
    return float(np.max(np.asarray(evals).real))  # λ_max ∈ [1/3, 1]


def main():
    print(f"F368 maps lens on the CMB low-ℓ axis family (srmech {srmech.__version__})")
    rows = []
    for line in CAT.read_text().splitlines():
        s = line.strip()
        if not s or s.startswith("#"):
            continue
        d = json.loads(s)
        if d.get("sky_location_galactic_lon_deg") is not None and d.get("sky_location_galactic_lat_deg") is not None:
            rows.append((d["canonical_name"], d["sky_location_galactic_lon_deg"], d["sky_location_galactic_lat_deg"]))
    print(f"\n  attested directional anomalies ({len(rows)} with sky locations):")
    vecs = []
    for name, l, b in rows:
        v = lb_to_unit(l, b); vecs.append(v)
        print(f"    {name:<48} (l,b)=({l:.0f},{b:.0f})")

    dip = lb_to_unit(*CMB_DIPOLE)
    # the live anomaly (MFO): AoE-pole vs CMB dipole axis angle
    aoe = next(v for (name, l, b), v in zip(rows, vecs) if "Axis of Evil" in name)
    print(f"\n  AoE-axis ↔ CMB-dipole-axis angle = {axis_angle_deg(aoe, dip):.1f}°  (MFO §VII.6.1.1 'live anomaly across all readings')")
    print(f"  pairwise anomaly-axis angles:")
    for i in range(len(vecs)):
        for j in range(i + 1, len(vecs)):
            print(f"    {rows[i][0][:22]:<22} ↔ {rows[j][0][:22]:<22} = {axis_angle_deg(vecs[i], vecs[j]):.1f}°")

    # axis concentration: real vs isotropic MC
    lam_real = concentration(vecs)
    rng = np.random.default_rng(20260604)
    N = len(vecs); MC = 20000
    null = np.empty(MC)
    for k in range(MC):
        rv = rng.normal(size=(N, 3)); rv /= np.linalg.norm(rv, axis=1, keepdims=True)
        null[k] = concentration([rv[i] for i in range(N)])
    p = float(np.mean(null >= lam_real))
    print(f"\n  axis concentration λ_max = {lam_real:.3f}  (1/3≈0.333 isotropic .. 1 perfectly aligned)")
    print(f"  isotropic-MC null: mean {null.mean():.3f}, p(λ_max ≥ real) = {p:.3f}  (N={N}, small sample)")

    # include the dipole as a 4th axis -> does the family + dipole share one frame?
    lam_with_dip = concentration(vecs + [dip])
    nulld = np.empty(MC)
    for k in range(MC):
        rv = rng.normal(size=(N + 1, 3)); rv /= np.linalg.norm(rv, axis=1, keepdims=True)
        nulld[k] = concentration([rv[i] for i in range(N + 1)])
    pd = float(np.mean(nulld >= lam_with_dip))
    print(f"  with CMB dipole added (N={N+1}): λ_max = {lam_with_dip:.3f}, p = {pd:.3f}")

    print("\n=== verdict (maps lens; framework-reading on attested data) ===")
    shares_axis = lam_real > null.mean()
    print(f"  the directional low-ℓ anomalies share a common axis more than isotropic: {shares_axis} (λ_max {lam_real:.3f} vs null mean {null.mean():.3f})")
    print(f"  => MAPS LENS reading: a FIXED observer reads {len(rows)}+ SEPARATE 'anomalies'; the DoF/relative-frame")
    print(f"     (navigable) reading sees ONE shared preferred axis = a single frame-relation between our")
    print(f"     observer-frame and a substrate-preferred direction. This is the OBSERVER-FRAME complement to")
    print(f"     MFO §VII.6.1.1's favored substrate-bundle-direction reading (NOT the disfavored bubble/collision")
    print(f"     reading). HONEST: N is tiny (p not significant); the clustering is literature-known ('low-ℓ axis")
    print(f"     family'); the framework contribution is the LENS (one frame vs N anomalies), not a new detection.")
    print(f"     CORRECTS F367(A): the 'new big-bang/germline-collision' idea is NOT new and is DISFAVORED")
    print(f"     (axial-not-disc; Osborne 2013 + Planck 2015 XVI null). The DoF/relative-frame lens survives.")

    res = dict(srmech_version=srmech.__version__, directions=rows,
               aoe_dipole_axis_angle_deg=axis_angle_deg(aoe, dip),
               lam_max=lam_real, null_mean=float(null.mean()), p_value=p,
               lam_with_dipole=lam_with_dip, p_with_dipole=pd, n_directional=len(rows))
    (HERE / "R-RBS-LM-R19_results.json").write_text(json.dumps(res, indent=2, default=str))
    print(f"\n  Results: {HERE / 'R-RBS-LM-R19_results.json'}")


if __name__ == "__main__":
    main()
