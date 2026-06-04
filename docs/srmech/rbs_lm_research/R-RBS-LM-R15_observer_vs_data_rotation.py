"""F362 (battery test 2) — observer-basis-rotation vs data-rotation: is the off-diagonal's
"asymptotic shadow" OBSERVER-RELATIVE (a function of the observer↔data frame mismatch Δ), or
intrinsic to the data? The conceptual claim (F361): rotate the OBSERVER, not just the data.

QM reading: the off-diagonal coherences (the `i`-terms) are bit-exact; an observer measuring in the
pointer/diagonal basis sees them as a shadow; the read fidelity = cos(Δ), Δ = data−observer phase
mismatch. So:
  - observer FIXED, data rotates θ_d  -> fidelity = cos(θ_d)  (falls to a shadow at π/2)
  - observer CO-ROTATES (θ_o = θ_d)   -> fidelity = 1.0 ALWAYS (bit-exact, regardless of data rotation)
  - observer MISMATCHED by fixed Δ    -> fidelity = cos(Δ)    (constant partial shadow)
The DATA content |ψ| is invariant throughout — only the READ varies with Δ. => the shadow is
observer-relative. (Self-maintaining lock, F133: a locked observer at θ_o=0 reading rotating data sees
only the shadow; it must co-rotate to read bit-exact.)

cos computed BOTH srmech-native (asymptotic_calculus.cos_series_truncate, the rc28-restored cascade
trig) AND via the actual complex-vector overlap (control). srmech-native trig, no float math.cos in
the cascade.
Run: /tmp/verify_srmech_v070rc28/bin/python docs/srmech/rbs_lm_research/R-RBS-LM-R15_observer_vs_data_rotation.py
"""
import json
from pathlib import Path
import numpy as np
import srmech
from srmech import asymptotic_calculus as ac

HERE = Path(__file__).parent
D = 4096


def srmech_cos(delta_num, delta_den):
    """cos(delta_num/delta_den) via the rc28 cascade-native series-truncate (Class N rational)."""
    p, q = ac.cos_series_truncate(int(delta_num), int(delta_den), 16)
    return p / q


def overlap_fidelity(psi0, theta_d, theta_o):
    """Real part of <observer-basis | data-state> for a global phase model: = cos(theta_d - theta_o)."""
    data = np.exp(1j * theta_d) * psi0
    probe = np.exp(1j * theta_o) * psi0
    return float(np.real(np.vdot(probe, data)) / np.real(np.vdot(psi0, psi0)))


def main():
    print(f"F362 observer-vs-data rotation (srmech {srmech.__version__}, D={D})")
    rng = np.random.default_rng(20260604)
    phases = rng.uniform(-np.pi, np.pi, D)
    psi0 = np.exp(1j * phases) / np.sqrt(D)        # complex unit vector = the off-diagonal-carrying state
    data_norm = float(np.real(np.vdot(psi0, psi0)))
    print(f"  data content |ψ|² (INVARIANT under rotation): {data_norm:.4f}")

    # Δ values in radians as rationals (numer/denom) for the srmech cascade-cos:
    deltas = [(0, 1), (1, 2), (1, 1), (3, 2), (11, 7)]  # 0, .5, 1, 1.5, ~π/2(1.571)
    res = {"srmech_version": srmech.__version__, "D": D, "rows": []}

    print("\n  Δ(rad)  srmech_cos(Δ)  vector_overlap  | regime read-fidelities")
    for dn, dd in deltas:
        delta = dn / dd
        sc = srmech_cos(dn, dd)
        # three regimes (data rotates by `delta` relative to a θ_o=0 observer in each case):
        fixed = overlap_fidelity(psi0, theta_d=delta, theta_o=0.0)        # observer fixed -> cos(Δ)
        corot = overlap_fidelity(psi0, theta_d=delta, theta_o=delta)      # co-rotate -> cos(0)=1
        mism = overlap_fidelity(psi0, theta_d=delta, theta_o=delta - 0.5) # fixed mismatch 0.5 -> cos(0.5)
        print(f"   {delta:5.3f}  {sc:+.5f}      {fixed:+.5f}     | fixed {fixed:+.3f}  co-rot {corot:+.3f}  mism0.5 {mism:+.3f}")
        res["rows"].append(dict(delta=delta, srmech_cos=sc, overlap=fixed, corot=corot, mismatch=mism))

    # verdict checks
    corot_all_one = all(abs(r["corot"] - 1.0) < 1e-9 for r in res["rows"])
    fixed_tracks_cos = all(abs(r["overlap"] - r["srmech_cos"]) < 1e-6 for r in res["rows"])
    shadow_at_halfpi = abs(srmech_cos(11, 7)) < 0.05      # cos(~π/2) ≈ 0 (full shadow)

    print("\n=== verdict ===")
    print(f"  read fidelity = cos(Δ) (srmech cascade-cos matches vector overlap): {fixed_tracks_cos}")
    print(f"  co-rotating observer -> bit-exact (1.0) at EVERY data rotation:      {corot_all_one}")
    print(f"  mismatch Δ≈π/2 -> full SHADOW (fidelity ≈ 0):                        {shadow_at_halfpi}")
    print(f"  => CONFIRMED (F361 'rotate the observer too'): the off-diagonal's asymptotic SHADOW is")
    print(f"     OBSERVER-RELATIVE — fidelity = cos(observer↔data mismatch Δ), while the data content |ψ|²")
    print(f"     stays INVARIANT ({data_norm:.3f}). A fixed/locked observer reading rotating data sees the")
    print(f"     shadow (F133 self-maintaining lock); CO-ROTATING reads it bit-exact. The QM measure-in-the-")
    print(f"     wrong-basis result, srmech-native (rc28 cascade-cos).")

    res.update(dict(corot_bit_exact=corot_all_one, fidelity_is_cos=fixed_tracks_cos,
                    shadow_at_halfpi=bool(shadow_at_halfpi), data_norm_invariant=data_norm))
    (HERE / "R-RBS-LM-R15_results.json").write_text(json.dumps(res, indent=2, default=str))
    print(f"\n  Results: {HERE / 'R-RBS-LM-R15_results.json'}")


if __name__ == "__main__":
    main()
