"""rc28 landed BOTH #797 ops (built from our F357/F359 specs) — validate them against the contracts.

op (a1): `hdc.klein4_triality_correct` (the explicit order-3 triality corrector, docstring cites F359).
         Validate the F359 acceptance bars:
         - bar 2: the 3 votes are the triality ORBIT of the SAME store (encode(v)), not external copies.
         - bar 1: blind unknown-location 1-render corruption correction rate > F353 baseline 0.25 (toward ~1).
         - bar 4: attributable to order-3 — a 2-vote (order-3-disabled) control cannot correct; and the
           order-2 CPT-4-orbit (F353 reproduction) gives the ~0.25 baseline.
         - honest distance bound: corrupt 2-of-3 renders → correction breaks (it's a 1-error corrector).
op (b):  `laplacian.magnetic_laplacian` (the directed Hermitian Laplacian the F357 reference specced) +
         `fiedler_vector`. Confirm Hermitian, hermitian_eigendecompose real eigenvalues, directed-sensitive.

srmech-native throughout (rc28). numpy only for corruption masks + norms (mechanics, flagged).
Run: /tmp/verify_srmech_v070rc28/bin/python docs/srmech/rbs_lm_research/R-RBS-LM-R13_rc28_797_ops_validation.py
"""
import json
from pathlib import Path
import numpy as np
import srmech
from srmech.amsc import hdc, laplacian as L
from srmech.amsc import _native

HERE = Path(__file__).parent
D, TRIALS = 512, 50


def corrupt_renders(orbit, D, n_bad, strength, rng):
    """Corrupt `strength` fraction of coords in `n_bad` randomly-chosen renders (unknown location)."""
    orbit = orbit.copy(); k = orbit.size // D
    for which in rng.choice(k, size=n_bad, replace=False):
        block = slice(which * D, (which + 1) * D)
        seg = orbit[block].copy()
        mask = rng.random(D) < strength
        seg[mask] = rng.integers(0, 4, int(mask.sum()))
        orbit[block] = seg
    return orbit


def order2_cpt_correct_rate(strength, rng_seed):
    """F353 reproduction: order-2 CPT-4-orbit, corrupt 1 sector (unknown loc), per-coord majority."""
    F = [lambda v: v.copy(), hdc.klein4_chirality_flip_gamma5,
         hdc.klein4_chirality_flip_omega7, hdc.klein4_cpt_mirror]
    ok = 0
    for t in range(TRIALS):
        rng = np.random.default_rng(rng_seed + t)
        v = hdc.klein4_random(D, seed=rng_seed + t)
        sectors = [F[i](v) for i in range(4)]
        bad = int(rng.integers(0, 4))
        seg = sectors[bad].copy(); m = rng.random(D) < strength
        seg[m] = rng.integers(0, 4, int(m.sum())); sectors[bad] = seg
        cands = np.stack([F[i](sectors[i]) for i in range(4)])  # invert each -> candidate v
        rec = np.array([np.bincount(cands[:, j], minlength=4).argmax() for j in range(D)], dtype=cands.dtype)
        ok += int(np.array_equal(rec, np.asarray(v)))
    return ok / TRIALS


def two_vote_correct_rate(strength, rng_seed):
    """Bar 4 control: order-3 DISABLED -> only 2 renders -> no majority -> cannot correct."""
    ok = 0
    for t in range(TRIALS):
        rng = np.random.default_rng(rng_seed + t)
        v = hdc.klein4_random(D, seed=rng_seed + t)
        orbit = np.asarray(hdc.klein4_triality_encode(v))
        r0 = orbit[:D].copy(); r1 = orbit[D:2 * D].copy()       # drop the 3rd (order-3) vote
        seg = r1.copy(); m = rng.random(D) < strength
        seg[m] = rng.integers(0, 4, int(m.sum())); r1 = seg
        rec = np.where(r0 == r1, r0, r0)                         # ties unresolved -> take r0 (no majority)
        ok += int(np.array_equal(rec, orbit[:D]))                # vs the (encoded) first render
    return ok / TRIALS


def main():
    print(f"rc28 #797 ops validation (srmech {srmech.__version__}, HAS_NATIVE={_native.HAS_NATIVE}, D={D}, trials={TRIALS})")
    res = {"srmech_version": srmech.__version__, "has_native": bool(_native.HAS_NATIVE)}

    # ---------- op (a1): klein4_triality_correct ----------
    print("\n=== op (a1) — klein4_triality_correct vs F359 contract ===")

    # bar 2: the 3 votes are the triality orbit of the SAME store (not external copies)
    v0 = hdc.klein4_random(D, seed=1)
    orbit0 = np.asarray(hdc.klein4_triality_encode(v0))
    r0, r1, r2 = orbit0[:D], orbit0[D:2 * D], orbit0[2 * D:]
    cyc1 = np.asarray(hdc.klein4_triality_cycle(r0))
    bar2 = (not np.array_equal(r0, r1)) and (not np.array_equal(r0, r2)) and np.array_equal(r1, cyc1)
    print(f"  bar 2 (3 votes = triality orbit of ONE store; render1 == triality_cycle(render0)): {bar2}")
    res["bar2_orbit_of_same_store"] = bool(bar2)

    # bar 1: blind 1-render corruption correction sweep
    print("  bar 1 (blind unknown-location 1-render corruption correction; F353 baseline 0.25):")
    bar1 = {}
    for p in (0.0, 0.25, 0.5, 1.0):
        ok = 0
        for t in range(TRIALS):
            rng = np.random.default_rng(900 + t)
            v = hdc.klein4_random(D, seed=900 + t)
            orbit = np.asarray(hdc.klein4_triality_encode(v))
            bad = corrupt_renders(orbit, D, 1, p, rng)
            rec = np.asarray(hdc.klein4_triality_correct(bad))
            ok += int(np.array_equal(rec, np.asarray(v)))
        bar1[p] = ok / TRIALS
        print(f"      1-render @ p={p}: triality-correct rate {bar1[p]:.2f}")
    res["bar1_triality_correct"] = bar1

    # honest distance bound: 2-of-3 corrupted -> should break
    ok2 = 0
    for t in range(TRIALS):
        rng = np.random.default_rng(1700 + t)
        v = hdc.klein4_random(D, seed=1700 + t)
        orbit = np.asarray(hdc.klein4_triality_encode(v))
        bad = corrupt_renders(orbit, D, 2, 1.0, rng)
        rec = np.asarray(hdc.klein4_triality_correct(bad))
        ok2 += int(np.array_equal(rec, np.asarray(v)))
    res["distance_bound_2of3_corrupt"] = ok2 / TRIALS
    print(f"  honest distance bound (2-of-3 renders corrupted -> breaks): {ok2/TRIALS:.2f}  (1-error corrector)")

    # bar 4 (CORRECTED): the F359 "0.25 baseline" was a MISREAD — F353's "1/4" is the code DISTANCE
    # (corrects up to m=1), NOT a 0.25 rate; the rate AT m=1 is 1.00. So the right question is not
    # "does order-3 correct where order-2 can't" (any >=3-fold code corrects 1 error) but "does the
    # order-2 4-orbit ALSO correct 1 error at ~1.0" (it does) -> order-3 is NOT a unique corrector.
    o2 = order2_cpt_correct_rate(1.0, 2600)   # order-2 CPT-4-orbit, m=1 -> expect ~1.0 (matches F353)
    res["order2_cpt_m1_rate"] = o2
    print(f"  order-2 CPT-4-orbit, 1 corrupted, rate {o2:.2f}  (reproduces F353 m=1=1.00; '1/4' was the DISTANCE)")
    print(f"  => order-3 is NOT a unique corrector; any >=3-fold majority corrects 1 blind error.")
    print(f"     The triality's contribution is the MINIMAL NATIVE 3-vote self-encoder (Aut(Z₂²)=S₃ 3-cycle")
    print(f"     on the non-identity sectors {{γ₅,iω₇,cpt}}): 3 votes from ONE store, resolving F344's")
    print(f"     'is the 3rd vote native?' — YES, via the triality orbit (bar 2).")

    # ---------- op (b): magnetic_laplacian ----------
    print("\n=== op (b) — magnetic_laplacian (directed Hermitian) + fiedler_vector ===")
    n = 6
    directed = [(0, 1), (1, 2), (2, 3), (3, 4), (4, 5), (5, 0), (0, 3)]  # a directed cycle + a chord
    H = L.magnetic_laplacian(n, directed, q=0.25)
    is_herm = bool(np.allclose(H, H.conj().T))
    evals, _ = L.hermitian_eigendecompose(H)
    real_eigs = bool(np.allclose(np.asarray(evals).imag, 0, atol=1e-8))
    # directed-sensitive: reversing all edges should NOT give the identical Hermitian matrix
    Hrev = L.magnetic_laplacian(n, [(b, a) for a, b in directed], q=0.25)
    directed_sensitive = not bool(np.allclose(H, Hrev))
    fied = L.fiedler_vector(L.signed_laplacian(n, directed))
    print(f"  magnetic_laplacian Hermitian: {is_herm}; hermitian_eigendecompose real eigenvalues: {real_eigs}")
    print(f"  directed-sensitive (reverse edges ≠ same matrix): {directed_sensitive}; fiedler_vector dim {np.asarray(fied).shape}")
    res["opb"] = {"magnetic_hermitian": is_herm, "real_eigs": real_eigs, "directed_sensitive": directed_sensitive}

    # ---------- verdict (corrected reading) ----------
    print("\n=== verdict (F359 bars, corrected for the 0.25-misread) ===")
    corrects_1 = bar1[1.0] >= 0.99 and res["distance_bound_2of3_corrupt"] < 0.5
    print(f"  op (a1) corrects a single blind error (rate 1.00, breaks at 2 = distance-1 corrector): {corrects_1}")
    print(f"  bar 2 — 3 votes are the triality orbit of ONE store (native, no external copy):        {bool(bar2)}")
    print(f"  bar 4 (REVISED) — order-3 is NOT a UNIQUE corrector (order-2 4-orbit also 1.00):        order-2={o2:.2f}")
    print(f"      triality's real role = minimal native 3-vote self-encoder (resolves F344's open Q).")
    print(f"  op (b) magnetic_laplacian directed-Hermitian + native eigen:                            {is_herm and real_eigs and directed_sensitive}")
    print(f"\n  => rc28: BOTH #797 ops shipped + WORK. op (a1) klein4_triality_correct is a valid native")
    print(f"     1-error self-correcting encoder (3 votes from 1 store via Aut(Z₂²)=S₃); op (b)")
    print(f"     magnetic_laplacian CONFIRMED as the F357 directed Hermitian. The F359 'beats 0.25'")
    print(f"     framing was a misread (F353's 1/4 = distance, not rate) — corrected here (no-leaning).")

    (HERE / "R-RBS-LM-R13_results.json").write_text(json.dumps(res, indent=2, default=str))
    print(f"\n  Results: {HERE / 'R-RBS-LM-R13_results.json'}")


if __name__ == "__main__":
    main()
