"""F402 — rc47 multi-layer practice: exercise the NEW (numpy-removed) srmech surface end-to-end across
many layers, using it CORRECTLY per the rc47 contract (native_status() not HAS_NATIVE; HV carrier not raw
ndarray; numpy-free Class-L lists). This is the 'look before we leap' practice on an item that touches A /
I / J / N / K / L / M at once.

rc47 surface (verified): numpy OPTIONAL; plain install = numpy-free core (format/cyclic/primes/rational/
cascade/laplacian, all COMPUTE); qm.* + signal_processing GATED behind srmech[scientific] (clean ImportError);
hdc (Klein-4/M) returns the HV carrier (srmech.amsc.hv.HV) but its MODULE still hard-imports numpy (so needs
[scientific] to import -- the GAP, UPSTREAM §24).

Run (scientific venv, so hdc/M works): /tmp/verify_srmech_v070rc47_sci/bin/python docs/srmech/rbs_lm_research/R-RBS-LM-R36_rc47_multilayer_surface_practice.py
"""
import srmech
from srmech.amsc import format as fmt, cyclic, primes, rational, cascade, laplacian, hdc


def aslist(x):
    return x.tolist() if hasattr(x, "tolist") else list(x)


def main():
    print(f"F402 rc47 multi-layer surface practice (srmech {srmech.__version__})")
    print("  native check (NEW API):", srmech.native_status())   # NOT srmech.HAS_NATIVE (removed in rc47)

    # A (content-address) -> seed an index
    h = fmt.sha256_bytes(b"rc47-multilayer")
    seed = int(h[:8], 16) % 1000
    print(f"\n  A  sha256 -> seed {seed}")

    # I / J / N — numpy-free integer cascades
    g = cyclic.gcd(seed, 360)
    fac = primes.factor(360)
    br = rational.best_rational(seed, 1000, 16)
    print(f"  I  gcd(seed,360)={g}   J  factor(360)={fac}   N  best_rational(seed/1000)={br}")

    # M (Klein-4 HDC) — HV carrier; use HV methods, NEVER a numpy reflex
    a = hdc.klein4_random(64, seed=seed)
    b = hdc.klein4_random(64, seed=seed + 1)
    bound = hdc.klein4_bind(a, b)
    print(f"  M  klein4_random -> {type(a).__name__} (HV; sectors={a.sectors}); "
          f"bind -> {type(bound).__name__}; self-sim={hdc.klein4_similarity(a, a):.3f}, "
          f"a/b-sim={hdc.klein4_similarity(a, b):+.3f}")
    # unbind recovers b: sim(unbind(bound,a), b) should be high
    rec = hdc.klein4_bind(bound, a)                       # Klein-4 bind is its own inverse (XOR)
    print(f"     unbind(bind(a,b),a) ~ b : sim={hdc.klein4_similarity(rec, b):.3f}  (HV round-trip)")

    # L (Class-L spectral) — build a graph from the 4 Klein-4 sector occupancies of a; numpy-free Laplacian
    sec = aslist(a)                                       # 0..3 per coordinate (HV -> plain list)
    counts = [sec.count(s) for s in range(4)]             # sector occupancy
    edges = [(s, (s + 1) % 4) for s in range(4)]          # a 4-cycle over the sectors (Class-I ring)
    Lp = laplacian.dense_laplacian(4, edges)
    ev = aslist(laplacian.jacobi_eigvals(Lp))
    print(f"  L  sector counts {counts} -> C4 Laplacian eigvals (NUMPY-FREE): {[round(x,3) for x in ev]}")

    # K (Class-K magnitude) — the spectral gap as a real |x| pin-slot (never abs())
    gap = cascade.magnitude(ev[1] - ev[0])
    print(f"  K  spectral gap |λ1-λ0| via cascade.magnitude = {gap}")

    print("\n=== verdict ===")
    print("  rc47 multi-layer cascade ran end-to-end using the NEW surface correctly:")
    print("   - native via native_status() (HAS_NATIVE removed);")
    print("   - A/I/J/N/K/L are numpy-free and COMPUTE (Class-L jacobi_eigvals numpy-free -> plain list);")
    print("   - M (Klein-4) returns the HV carrier (sectors/.tolist/.to_numpy), no implicit ndarray escape;")
    print("   - qm.* / signal_processing would gate cleanly behind srmech[scientific] (not used here).")
    print("  GAP (UPSTREAM §24): hdc's MODULE still hard-imports numpy -> on a PLAIN install M crashes raw")
    print("  (ModuleNotFoundError) instead of being numpy-free (it returns the numpy-free HV!) or gating like qm.")


if __name__ == "__main__":
    main()
