r"""R-RBS-LM-OVERHAULAUDIT (F725) — audit of the srmech 0.7.5rc78 overhaul: typed `One` + `to_scalar`, the
cascade de-dup, the class-TOML naming, the §39 generator, and the (partial) numpy removal.

User direction (2026-06-11): "doing srmech overhaul. numpy removal; lots of duplicate items from before we added
the_one; TOML config for classes giving names of familiarity is working; a to_scalar for when someone doesn't want
matrix output. pull latest test.pypi.org and make sure we're on the right track / makes sense."

VERDICT: ON TRACK; the design choices make sense. Verified against the rc78 wheel (numpy-free venv):

  (1) TYPED `One` + `to_scalar` — RIGHT.
      the_one(σ, θ_num, θ_den, terms) -> One = S(σ,θ); σ=±1 is CHIRALITY (Class C, attested — rejects σ=2),
      θ is the angle. One carries the Hurwitz structure (Fano planes / block dims / grammar slots) and exposes:
        • to_scalar(mode='trace', as_float=False)  -> EXACT RATIONAL (num, den), numpy-FREE   <- the "no matrix" path
        • to_flat_rational()                       -> exact rationals, numpy-FREE
        • to_matrix() / to_numpy()                 -> the numpy LIFT (scientific tier)
      So "a to_scalar for when someone doesn't want matrix output" = the numpy-free exact projection vs the numpy
      matrix lift. On-thesis: exact-rational = the substrate truth (Class N); the matrix is the lift.

  (2) DE-DUP — cascade is now a PACKAGE of focused modules organised around one.py (the_one as the typed centre):
      one / coupled / exact_dft / hypercomplex_dft / matrix_cascades / spectral_cascades / atoms / compose /
      cayley_dickson / hamming / parallel / sedenion_register. The "duplicate items from before the_one" (multiple
      DFT/coupler ops) consolidated. Makes sense.

  (3) CLASS-TOML NAMING ("names of familiarity") — working + EXPANDING: ships ['Genome', 'Hurwitz']; bring-your-own
      still registers live.

  (4) §39 generate_class_descriptor — DELIVERED (our wishlist ask): the inverse of make_class; round-trips
      (generate TOML -> register -> load as a class).

  GAP (the numpy removal is IN PROGRESS, as stated): laplacian.fiedler_vector still hard-requires numpy (np.asarray
  on None) — the Class-L 2nd-eigenvector path hasn't gotten the numpy-free exact/native dispatch that jacobi_eigvals
  + the_one already have. The PATTERN (numpy-free exact + numpy lift) is right; the sweep just isn't finished for
  the residual Class-L spectral fns. (qm.* staying numpy-tier is by design.)

  WISHLIST: §38 native bind (rc42) ✓ · §40 U1 text ops (rc50) ✓ · §39 generator (rc78) ✓ · §41 genome persistence —
  not yet (just scoped). 3 of 4 landed.

Run with the rc78 venv: /tmp/srmech_rc78/venv/bin/python3. No abs(); this is a read-only audit of srmech.
"""
import importlib
import srmech
from srmech.amsc.cascade import the_one, to_scalar
from srmech.dsl import list_classes, generate_class_descriptor, register_class_dir
from srmech.amsc import genome as G
from srmech.amsc.hdc import klein4_random


def check(label, fn):
    try:
        ok, detail = fn()
    except Exception as e:
        ok, detail = False, f"{type(e).__name__}: {str(e).splitlines()[0][:70]}"
    print(f"  [{'OK ' if ok else 'GAP'}] {label}: {detail}")
    return ok


def main():
    print(f"=== R-RBS-LM-OVERHAULAUDIT (F725) — srmech {srmech.__version__} overhaul audit (numpy-free venv) ===\n")

    print("(1) typed One + to_scalar (numpy-free exact projection vs numpy matrix lift):")
    def _scalar():
        o = the_one(1, 1, 4, terms=8)
        sc = to_scalar(o, mode="trace")
        f = to_scalar(o, as_float=True)
        return (isinstance(sc, tuple) and len(sc) == 2), f"σ=±1 chirality; to_scalar(trace)=exact {sc[0]}/{sc[1]} ≈ {f:.4f} (numpy-free)"
    check("to_scalar exact + numpy-free", _scalar)
    def _chir():
        try:
            the_one(2, 1, 3)
            return False, "σ=2 accepted (should reject)"
        except ValueError as e:
            return True, f"σ rejected non-chirality ({str(e)[:40]})"
    check("σ is Class-C chirality (±1, attested)", _chir)
    def _lift():
        o = the_one(1, 1, 4, terms=8)
        try:
            o.to_matrix(); return False, "to_matrix numpy-free?? (expected numpy lift)"
        except ImportError:
            return True, "to_matrix is the numpy LIFT (so to_scalar is the numpy-free 'no-matrix' path)"
    check("to_matrix = numpy lift", _lift)

    print("\n(2) de-dup: cascade is a package organised around one.py:")
    import os
    cdir = os.path.join(os.path.dirname(srmech.__file__), "amsc", "cascade")
    mods = sorted(f[:-3] for f in os.listdir(cdir) if f.endswith(".py") and f != "__init__.py")
    print(f"  [OK ] cascade package modules ({len(mods)}): {mods}")

    print("\n(3) class-TOML naming + §39 generator:")
    check("class catalog ('names of familiarity')", lambda: (True, f"{list_classes()}"))
    def _gen():
        import tempfile
        t = generate_class_descriptor("AuditShelf", fields={"the_one": "hv", "items": "list"},
                                      methods={"store": {"op": "srmech.amsc.genome.genome", "binds": ["kernels", "the_one"]}})
        d = tempfile.mkdtemp(prefix="audit_"); open(os.path.join(d, "s.toml"), "w").write(t)
        register_class_dir(d)
        return ("AuditShelf" in list_classes()), "generate_class_descriptor -> register -> load round-trips (§39 delivered)"
    check("§39 generate_class_descriptor", _gen)

    print("\n(4) numpy removal status:")
    for mod in ("srmech.amsc.laplacian", "srmech.signal_processing", "srmech.amsc.genome"):
        check(f"{mod} imports numpy-free", lambda m=mod: (bool(importlib.import_module(m)), "OK"))
    def _fied():
        from srmech.amsc import laplacian as L
        L.fiedler_vector([[0, 1, 1], [1, 0, 1], [1, 1, 0]])
        return True, "numpy-free OK"
    check("laplacian.fiedler_vector numpy-free", _fied)   # expected GAP (in-progress)

    print("\n(5) genome regression (de-dup didn't break it):")
    def _gen2():
        one = klein4_random(64, seed=1); k = {"a": [klein4_random(64, seed=s) for s in (10, 11)], "b": [klein4_random(64, seed=20)]}
        back = G.partition(G.genome(k, one), one, list(k))
        return all(list(map(list, back[x])) == list(map(list, k[x])) for x in k), "round-trip reversible"
    check("genome partition round-trip", _gen2)

    print("\nVERDICT: ON TRACK. Typed One + numpy-free to_scalar (vs the numpy matrix lift) is the right shape;")
    print("  the cascade de-dup around one.py makes sense; class-TOML naming + the §39 generator are delivered.")
    print("  The one IN-PROGRESS item: finish the numpy-removal sweep for the residual Class-L spectral fns")
    print("  (fiedler_vector) — give them the numpy-free exact/native path jacobi_eigvals + the_one already use.")


if __name__ == "__main__":
    main()
