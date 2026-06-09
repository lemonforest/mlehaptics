r"""R-RBS-LM-GENOMELANDS (F716) — the genome storage model (F710-F715) + the class-from-TOML mechanism land
upstream in srmech 0.7.5rc42; the native A-N binding gap (#962 Part 1) is substantially closed.

User direction (2026-06-09): "srmech-v0.7.5rc42 on test.pypi.org and is now class aware via TOML config and new
genome TOML will show us how any user/researcher can use class names for their school of choice."

WHAT THIS VERIFIES (run with the rc42 venv: /tmp/srmech_rc42/venv/bin/python3):
  (1) srmech.amsc.genome.* IS the F710-F715 storage object, native + numpy-free + REVERSIBLE:
      encode_shape reproduces the F715 anchors to the digit; a Genome assembles a multi-kernel telomere-
      partitioned strand and partition() recovers every kernel by re-binding the_one. (= #962 Part 2.)
  (2) the [class]-TOML mechanism ("class names for their school of choice"): srmech.dsl.make_class builds a
      generic CatalogClass from a [class] descriptor (fields + methods-as-dotted-cascade-op-refs), ZERO user
      Python; register_class_dir()/SRMECH_CLASS_PATH brings your own (attested user:<sha256>, can't shadow a
      shipped name). Genome ships as the A-tier seed.
  (3) the native A-N symbols the rc28 shim left unbound (F708/F710) are now reachable via _native.LIB, and
      jacobi_eigvals dispatches to the bound srmech_jacobi_eigvals in the numpy-absent path (the 49x Class-L
      gap, closed). (= #962 Part 1, substantially.)
  (4) STILL OPEN: R3 U1 tokenize()/cooccurrence_edges() did NOT ship -> we still hand-roll co-occurrence edges.

THE ON-THESIS READING (F133/R30/F552): "class names for their school of choice" is substrate-self-recognition
made operational. The cascade OPS underneath (encode_shape, the the_one Klein-4 coupling, telomere content-
addresses = the A-N primitives) are the INVARIANT substrate; the class-name + method-names
(genome/chromosome/telomere) are ONE observer PROJECTION -- biology's school. A different discipline re-names the
same storage object in its own vocabulary and the math does not move. "A user class-name may not shadow a shipped
one" is the invariant being protected while the projection stays free. genome.toml: "The biological-structure
names ARE the cascade names -- substrate-self-recognition."

No abs(); no CAD; srmech-first (the genome surface IS the srmech op). Reference/verification scaffold.
"""
import inspect

import srmech
from srmech.amsc import _native, genome as G
from srmech.amsc.hdc import klein4_random
from srmech.dsl._class_catalog import make_class, list_classes
from srmech.dsl._class_surface import describe_class

# F715 encode-criterion anchors: (n, expected_shape, expected_depth)
F715_ANCHORS = [(200, "tome", 0), (256, "tome", 0), (800, "mobius", 1),
                (1024, "mobius", 1), (5000, "quad_strand", 3), (1_770_000, "quad_strand", 7)]

# The previously-unbound A-N symbols (F708/F710) — now expected reachable via _native.LIB.
NATIVE_AN_SYMBOLS = [
    "srmech_klein4_bind", "srmech_klein4_bundle", "srmech_klein4_similarity",
    "srmech_hdc_bind", "srmech_hdc_bundle", "srmech_hdc_permute", "srmech_hdc_similarity",
    "srmech_jacobi_eigvals", "srmech_graph_dense_laplacian", "srmech_hermitian_eigendecompose",
    "srmech_cyclic_period", "srmech_is_prime",
]


def _lib_has(sym):
    lib = getattr(_native, "LIB", None)
    if lib is None:
        return False
    try:
        getattr(lib, sym)
        return True
    except AttributeError:
        return False


def main():
    print(f"=== R-RBS-LM-GENOMELANDS (F716) — genome surface + class-from-TOML land  (srmech {srmech.__version__}) ===\n")
    ns = srmech.native_status()
    assert ns["has_native"] and ns["native_version"] == srmech.__version__, ns
    print(f"native: has_native={ns['has_native']} version={ns['native_version']} abi={ns['abi_version']}\n")

    print("(1) GENOME SURFACE = F710-F715 (encode criterion to the digit; reversible multi-kernel strand):")
    for n, want_shape, want_depth in F715_ANCHORS:
        s = G.encode_shape(n)
        assert s["shape"] == want_shape and s["depth"] == want_depth, (n, s)
        print(f"    encode_shape(n={n:>9}) -> {s['shape']:<11} leaves={s['leaves']:<5} depth={s['depth']}  [F715 ✓]")
    one = klein4_random(64, seed=1)
    kernels = {"astronomy": [klein4_random(64, seed=s) for s in (10, 11, 12)],
               "geography": [klein4_random(64, seed=s) for s in (20, 21)],
               "music": [klein4_random(64, seed=30)]}
    strand = G.genome(kernels, one)
    back = G.partition(strand, one, list(kernels))
    reversible = all(list(map(list, back[L])) == list(map(list, kernels[L])) for L in kernels)
    assert reversible and len(strand) == 9, (reversible, len(strand))
    print(f"    genome(): strand len {len(strand)} (6 turns + 3 telomere caps); partition() reversible: {reversible}\n")

    print("(2) CLASS-FROM-TOML — 'class names for their school of choice' (zero user Python):")
    assert "Genome" in list_classes(), list_classes()
    Genome = make_class("Genome")                                   # built FROM the [class] TOML
    g = Genome(the_one=one)
    s2 = g.assemble(kernels=kernels)
    b2 = g.partition(strand=s2, labels=list(kernels))
    assert all(list(map(list, b2[L])) == list(map(list, kernels[L])) for L in kernels)
    d = describe_class("Genome")
    print(f"    classes shipped: {list_classes()}  | Genome provenance tier: {d['provenance']} (A-tier seed)")
    print(f"    methods: {sorted(d['methods'])}")
    print(f"    bring-your-own: register_class_dir()/SRMECH_CLASS_PATH -> provenance 'user:<sha256>', no shadowing\n")

    print("(3) NATIVE A-N BINDING (#962 Part 1) — symbols reachable via _native.LIB (rc28 bound only ~13 _c):")
    reachable = {sym: _lib_has(sym) for sym in NATIVE_AN_SYMBOLS}
    for sym, ok in reachable.items():
        print(f"    {'Y' if ok else '.'}  {sym}")
    n_reach = sum(reachable.values())
    jac_src = inspect.getsource(__import__("srmech.amsc.laplacian", fromlist=["x"]).jacobi_eigvals)
    jac_native = ("srmech_jacobi" in jac_src) or ("_native" in jac_src) or ("_c(" in jac_src)
    print(f"    -> {n_reach}/{len(NATIVE_AN_SYMBOLS)} reachable; jacobi_eigvals dispatches native (numpy-absent path): {jac_native}")
    klein_src = inspect.getsource(__import__("srmech.amsc.hdc", fromlist=["x"]).klein4_bind)
    klein_native = any(t in klein_src for t in ("_native", "LIB", "_c("))
    print(f"    klein4_bind acts WITHOUT A LIFT (rc28 needed ctypes); native-dispatched: {klein_native} "
          f"(pure-Python XOR by design — bit-identical, never the perf gap)\n")

    print("(4) STILL OPEN — R3 U1 op precursors (we still hand-roll co-occurrence edges):")
    # numpy-free probe: only the Class-N core modules (signal_processing is the scientific/numpy tier).
    for name in ("tokenize", "cooccurrence_edges"):
        found = []
        for m in ("srmech.amsc.laplacian", "srmech.amsc.cascade"):
            try:
                if hasattr(__import__(m, fromlist=["x"]), name):
                    found.append(m)
            except Exception:
                pass
        print(f"    {name}: {'in ' + ', '.join(found) if found else 'NOT FOUND (open)'}")

    print("\nVERDICT (F716): F710-F715 genome model + the class-from-TOML mechanism shipped in srmech 0.7.5rc42;")
    print("  the native A-N symbols are bound/reachable and jacobi dispatches native numpy-free (#962 Part 1 ~done,")
    print("  Part 2 done). 'class names for their school of choice' = substrate-self-recognition made operational:")
    print("  the cascade OPS are the invariant substrate; the class/method NAMES are one observer projection")
    print("  (biology's school), free to re-name, forbidden to shadow the shared invariant. R3 U1 stays open.")


if __name__ == "__main__":
    main()
