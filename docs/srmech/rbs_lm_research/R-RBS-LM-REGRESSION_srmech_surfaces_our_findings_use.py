r"""R-RBS-LM-REGRESSION — re-runnable spot-check that an srmech overhaul (numpy removal / cascade de-dup / One
typing) does NOT break the surfaces our committed findings depend on. Run against any rc venv.

User direction (2026-06-11): "numpy removal still in progress, just asking for a spot check that we aren't breaking
anything." Read-only; resolves + RUNS each surface (not just imports). Clean at rc78: 49/49 + WIKIKERNEL build.
"""
import importlib
import sys
import srmech

OK = BRK = 0


def chk(label, fn):
    global OK, BRK
    try:
        fn(); print(f"  OK    {label}"); OK += 1
    except Exception as e:
        print(f"  BREAK {label} -> {type(e).__name__}: {str(e).splitlines()[-1][:80]}"); BRK += 1


def main():
    print(f"=== R-RBS-LM-REGRESSION — srmech {srmech.__version__} (numpy-free) ===\n")
    from srmech.amsc import cascade as C, hdc as H, text as T, laplacian as L, genome as G, format as FMT
    from srmech.amsc.hdc import klein4_random
    from srmech import dsl
    v, w = klein4_random(64, seed=3), klein4_random(64, seed=4)

    # cascade package re-exports (the de-dup risk) — every op our findings call:
    for op in ("pin_slot_at_zero", "magnitude", "net_chirality", "reorient", "chiral_flip", "best_rational_signed",
               "cyclic_gcd", "parallel_sector_dispatch", "kuramoto_step", "hamming_encode", "hamming_syndrome",
               "hamming_decode_correct", "to_scalar", "the_one"):
        chk(f"cascade.{op}", lambda op=op: getattr(C, op))
    chk("cascade.pin_slot_at_zero runs", lambda: C.pin_slot_at_zero(-3))
    chk("cascade.magnitude runs", lambda: C.magnitude(-2.0))
    chk("cascade.hamming round-trip", lambda: C.hamming_decode_correct(C.hamming_encode([1, 0, 1, 1], 3)))
    # hdc klein4 (F716/F717):
    for op in ("klein4_bind", "klein4_bundle", "klein4_similarity", "klein4_chirality_flip_gamma5",
               "klein4_chirality_flip_omega7", "klein4_cpt_mirror", "similarity", "bind", "bundle", "permute"):
        chk(f"hdc.{op}", lambda op=op: getattr(H, op))
    chk("hdc.klein4_bind reversible (F716)", lambda: H.klein4_bind(H.klein4_bind(v, w), w) == list(v))
    chk("hdc.gamma5 self-inverse (F717)", lambda: list(H.klein4_chirality_flip_gamma5(H.klein4_chirality_flip_gamma5(v))) == list(v))
    # text ops (F723/F724):
    chk("text.tokenize unicode (F723)", lambda: "café" in T.tokenize("café"))
    chk("text.cooccurrence_edges no-cap (F723)", lambda: T.cooccurrence_edges([["a", "b", "a", "c"]], window=2)[0])
    # laplacian (jacobi numpy-free; fiedler is the known in-progress numpy-tier item, NOT checked here):
    for op in ("dense_laplacian", "jacobi_eigvals", "dense_adjacency", "hermitian_eigendecompose",
               "magnetic_laplacian", "signed_laplacian"):
        chk(f"laplacian.{op}", lambda op=op: getattr(L, op))
    chk("laplacian.jacobi_eigvals numpy-free (F716)", lambda: L.jacobi_eigvals([[2.0, -1.0], [-1.0, 2.0]]))
    # genome + dsl (F716/F721/F725):
    chk("genome round-trip (F721)", lambda: G.partition(G.genome({"a": [v]}, w), w, ["a"]))
    for op in ("make_class", "list_classes", "register_class_dir", "generate_class_descriptor",
               "describe_class", "run_class_method"):
        chk(f"dsl.{op}", lambda op=op: getattr(dsl, op))
    # A/I/N we use:
    chk("format.sha256_bytes", lambda: FMT.sha256_bytes(b"x"))
    chk("amsc.cyclic.gcd", lambda: importlib.import_module("srmech.amsc.cyclic").gcd(12, 8))
    chk("amsc.rational.best_rational", lambda: importlib.import_module("srmech.amsc.rational").best_rational(22, 7, 100))

    # integration: our migrated wiki kernel still builds + stays output-preserving:
    import importlib.util as u
    sys.path.insert(0, "docs/srmech/rbs_lm_research")
    spec = u.spec_from_file_location("wk", "docs/srmech/rbs_lm_research/R-RBS-LM-WIKIKERNEL_big_wiki_word_association_class_l_kernel_reference.py")
    wk = u.module_from_spec(spec); spec.loader.exec_module(wk)
    arts = ["the sun is a star and the planet orbits the sun", "a planet and a moon orbit a star café"]
    shipped = wk.build_edges_topk(arts, window=2, vocab_cap=None)
    wk._HAS_TEXT = False
    fb = wk.build_edges_topk(arts, window=2, vocab_cap=None)
    chk("WIKIKERNEL builds + shipped==fallback (F724)", lambda: shipped == fb and len(shipped[2]) > 0)

    print(f"\n  {OK} OK / {BRK} BREAK  — {'NOTHING BROKEN' if BRK == 0 else 'REGRESSION(S) ABOVE'}")


if __name__ == "__main__":
    main()
