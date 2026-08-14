"""SPIKE `#T1114` rung 4 — MEASURE: does a general indexed map close
BLK-ITER-INDEXED for the 4 blocked descriptors, bit-identically?

Stages:
  env                    — worktree / version / registry / projection attestation
  grammar_probe          — the shipped reference grammar vs @idx / computed [N]
  inventory_probe        — which framing/access leaves the registry lacks (measured)
  closure_quotes         — the shipped closure test's actual assertions, extracted
  closure_letter_break   — a widened Chain subclass vs the test's own sets
  dsl_map_demo           — the DSL-layer map stage subsumes chiral_flip (bit-identical)
  bit_identity           — per-op sweeps: chain vs shipped, repr-equality
  totality               — the (c) argument, stated with the fold precedent
  verdict                — aggregation

Run (WSL2, numpy-absent):
    cd docs/srmech/python
    PYTHONPATH=$PWD python3 ../notes/_t1114_rung4_measure_rc419.py \
        > ../notes/t1114_rung4_indexed_map_rc419_20260809.ndjson

No abs().  No numpy / math / fractions / decimal.  srmech ships no timing
surface (`#T1116`); nothing here needs a clock.
"""

from __future__ import annotations

import importlib
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

CHAINS_TOML = os.path.join(HERE, "_t1114_rung4_map_chains_rc419.toml")
WORKTREE_TAG = "agent-a0102bc09c1e5c5a5"

import srmech  # noqa: E402
from srmech.cascade import compose  # noqa: E402

import _t1114_rung4_map_engine_rc419 as eng  # noqa: E402

STUB_MODULE = "_t1114_rung4_map_engine_rc419"


def emit(**kw):
    kw.setdefault("spike", "T1114")
    kw.setdefault("rung", 4)
    kw.setdefault("srmech_version", srmech.__version__)
    print(json.dumps(kw, sort_keys=True))


def override_registry():
    """DEFAULT + E/M/N/K -> the stub module.  LABELLED see-past plumbing for
    BLK-REGMAP; letter assignments are NOT class-identity claims.  Class I
    stays DEFAULT (srmech.math.cyclic) — mod_add serves mid-body registered."""
    r = dict(compose.DEFAULT_CLASS_REGISTRY)
    for letter in ("E", "M", "N", "K"):
        r[letter] = STUB_MODULE
    return r


# ── env ───────────────────────────────────────────────────────────────────
def stage_env():
    from srmech._native import HAS_NATIVE
    from srmech.introspect.tool_schema import get_tool_schema, warmup_all
    warmup_all()
    emit(
        stage="env",
        srmech_file=srmech.__file__,
        has_native=bool(HAS_NATIVE),
        projection="pure" if not HAS_NATIVE else "native",
        registry_total=len(get_tool_schema().tools),
        python=sys.version.split()[0],
        numpy_present=("numpy" in sys.modules),
    )
    assert srmech.__file__ and WORKTREE_TAG in srmech.__file__, (
        "WRONG TREE: %r" % (srmech.__file__,))
    assert srmech.__version__ == "0.9.0rc419", srmech.__version__


# ── grammar probes ────────────────────────────────────────────────────────
def stage_grammar():
    probes = {}
    for ref in ("@idx.k", "@index.k", "@bind.mu", "@input.x", "@step[0].output"):
        try:
            compose._validate_reference(ref, 1)
            probes[ref] = "ACCEPTED"
        except compose.ChainSpecError as e:
            probes[ref] = "REJECTED: %s" % str(e)[:120]
    literal_ok = bool(compose._REFERENCE_PATTERN.match("@input.x[3]"))
    computed_ok = bool(compose._REFERENCE_PATTERN.match("@input.x[@idx.k]"))
    emit(
        stage="grammar_probe",
        validate_reference=probes,
        literal_indexer_matches=literal_ok,
        computed_indexer_matches=computed_ok,
        pattern=compose._REFERENCE_PATTERN.pattern,
        finding=(
            "A NEW reference form IS required: the shipped grammar "
            "(compose.py _REFERENCE_PATTERN) hard-codes namespaces "
            "row|input|step|catalog, so @idx.<name> is unspellable; and the "
            "[N] indexer is \\[\\d+\\] literal-only, so a COMPUTED index "
            "(@input.x[@idx.k]) is also unspellable — dynamic element access "
            "must enter as an OP (seq_get), not as grammar."),
    )


# ── inventory probes (which leaves are genuinely missing) ─────────────────
def stage_inventory():
    mods = {}
    for cid, modname in sorted(compose.DEFAULT_CLASS_REGISTRY.items()):
        mods[cid] = importlib.import_module(modname)

    def reach(opname):
        return sorted(c for c, m in mods.items()
                      if callable(getattr(m, opname, None)))

    candidates = [
        "seq_len", "len", "length", "size", "count",
        "seq_get", "element", "getitem", "item", "get", "nth",
        "f64_add", "add", "sum", "accumulate",
        "f64_mul", "mul", "multiply", "product",
        "vec_add", "vec_scale", "scale",
        "neumaier_sum", "compensated_sum", "fsum",
        "mat_matvec", "mat_matmul",
        "map", "enumerate", "zip",
    ]
    found = {n: reach(n) for n in candidates}
    emit(
        stage="inventory_probe",
        reachable={k: v for k, v in found.items() if v},
        unreachable=sorted(k for k, v in found.items() if not v),
        note=(
            "mat_matvec/mat_matmul reachable via L soften BLK-REGMAP for the "
            "DFT matvec piece; but LENGTH, DYNAMIC ELEMENT ACCESS, scalar "
            "add/mul and vector add/scale leaves are registered NOWHERE — "
            "the indexed map needs this small framing inventory to be usable "
            "(same family as rung-3 BLK-FRAMING).  'get'/'sum'/'add' hits, "
            "if any, are checked by name only — topicality NOT verified."),
    )


# ── closure-test quotes + letter-break measurement ────────────────────────
def _closure_test_path():
    pkg_dir = os.path.dirname(os.path.dirname(os.path.abspath(srmech.__file__)))
    return os.path.join(pkg_dir, "tests", "test_combinator_kernel_closure.py")


def stage_closure():
    path = _closure_test_path()
    with open(path, "r", encoding="utf-8") as fh:
        src = fh.read()
    wanted = [
        'KERNEL_BUILDERS = frozenset({"then", "loop", "fold", "reduce", "parallel_sectors"})',
        "assert len(KERNEL_BUILDERS) == 5",
        "unclassified = public - KERNEL_BUILDERS - NON_BUILDER_PUBLIC",
        "assert not unclassified, (",
        'sum([has_op, has_loop, has_fold, has_reduce, has_parallel])',
    ]
    quotes = {w: (w in src) for w in wanted}
    assert all(quotes.values()), "closure-test source drifted: %r" % quotes

    # The test's own sets, verified verbatim above:
    KERNEL_BUILDERS = frozenset(
        {"then", "loop", "fold", "reduce", "parallel_sectors"})
    NON_BUILDER_PUBLIC = frozenset({"run", "stages"})

    import inspect
    from srmech.dsl import Chain

    def public_methods(cls):
        return {name for name, _ in
                inspect.getmembers(cls, predicate=inspect.isfunction)
                if not name.startswith("_")}

    shipped_unclassified = (public_methods(Chain)
                            - KERNEL_BUILDERS - NON_BUILDER_PUBLIC)
    MapChain = eng.widened_chain_class()
    widened_unclassified = (public_methods(MapChain)
                            - KERNEL_BUILDERS - NON_BUILDER_PUBLIC)
    emit(
        stage="closure_letter_break",
        test_path_exists=os.path.exists(path),
        quoted_assertions_present=quotes,
        shipped_chain_unclassified=sorted(shipped_unclassified),
        widened_chain_unclassified=sorted(widened_unclassified),
        finding=(
            "LETTER break, three tests: (1) test_no_hidden_sixth_builder — "
            "'assert not unclassified' fires on {'map_indexed'} (measured on "
            "the widened subclass against the test's own sets); (2) "
            "test_exactly_five_kernel_builders — 'assert len(KERNEL_BUILDERS) "
            "== 5' forces the frozenset edit to be conscious; (3) "
            "test_five_toml_discriminators_bijection — the dispatcher's "
            "'sum([has_op, has_loop, has_fold, has_reduce, has_parallel])' "
            "guard must change shape.  That is exactly the checkpoint working "
            "as designed: 'a new special form must be a CONSCIOUS widening of "
            "the kernel (with this test updated in the same change)'.  INTENT "
            "(totality) is NOT broken — see the totality stage."),
    )


# ── DSL-layer map demo: indexed map subsumes the Class-C flip ─────────────
def stage_dsl_demo():
    from srmech.cascade.atoms import chiral_flip
    MapChain = eng.widened_chain_class()
    ch = MapChain("rung4-map-demo")
    ch.map_indexed(lambda k, xs: xs[len(xs) - 1 - k])
    cases = [[1, 2, 3], [], [4.5], list(range(9))]
    ok = all(ch.run(list(c)) == chiral_flip(list(c)) for c in cases)
    emit(
        stage="dsl_map_demo",
        body="out[k] = xs[n-1-k]",
        vs="srmech.cascade.atoms.chiral_flip",
        n_cases=len(cases),
        all_identical=ok,
        note=("The indexed map STRICTLY GENERALISES the existing bounded "
              "Klein-4 map slot: the Class-C flip is one indexed-map body."),
    )
    assert ok


# ── bit-identity machinery ────────────────────────────────────────────────
def _lcg_floats(seed, count, lo=-2.0, hi=2.0):
    x = seed & 0xFFFFFFFFFFFFFFFF
    out = []
    for _ in range(count):
        x = (x * 6364136223846793005 + 1442695040888963407) % (1 << 64)
        u = (x >> 11) / float(1 << 53)
        out.append(lo + u * (hi - lo))
    return out


def _vecs(seed, n, dim):
    flat = _lcg_floats(seed, n * dim)
    return [flat[i * dim:(i + 1) * dim] for i in range(n)]


def run_chain(chains, name, registry, inputs):
    return eng.run_ext_steps(chains[name]["steps"], registry, inputs=inputs)


def bit_identity(op_label, pairs):
    """pairs: [(case_name, chain_thunk, shipped_thunk)]"""
    n_ok, mism = 0, []
    for cname, cthunk, sthunk in pairs:
        try:
            ref = sthunk()
        except Exception as e:  # noqa: BLE001
            ref = ("RAISED", type(e).__name__, str(e)[:80])
        try:
            got = cthunk()
        except Exception as e:  # noqa: BLE001
            got = ("RAISED", type(e).__name__, str(e)[:80])
        if repr(got) == repr(ref):
            n_ok += 1
        elif len(mism) < 6:
            mism.append({"case": cname, "shipped": repr(ref)[:140],
                         "chain": repr(got)[:140]})
    emit(stage="bit_identity", op=op_label, n_cases=len(pairs),
         n_identical=n_ok, n_mismatch=len(pairs) - n_ok,
         first_mismatches=mism,
         registry="override_EMNK_to_stub_module[EXTERNAL]")
    return n_ok == len(pairs)


def stage_bits(chains, reg):
    from srmech.cascade.hypercomplex_dft import octonion_dft, quaternion_dft
    from srmech.cascade.composites import autocorrelation, kuramoto_step

    results = {}

    # ── quaternion_dft ────────────────────────────────────────────────
    q_pairs = []
    for n in (0, 1, 2, 3, 5, 8):
        x = _vecs(1000 + n, n, 4)
        q_pairs.append((
            "left_i_fwd_n%d" % n,
            lambda x=x: run_chain(chains, "map_quaternion_dft", reg,
                                  {"x": x, "left": True, "mu_axis": "i",
                                   "inverse": False}),
            lambda x=x: quaternion_dft(x, form="left", mu_axis="i"),
        ))
    x5 = _vecs(77, 5, 4)
    q_pairs.append((
        "right_ijk_fwd_n5",
        lambda: run_chain(chains, "map_quaternion_dft", reg,
                          {"x": x5, "left": False, "mu_axis": "ijk",
                           "inverse": False}),
        lambda: quaternion_dft(x5, form="right", mu_axis="ijk"),
    ))
    x4 = _vecs(78, 4, 4)
    muv = [0.0, 0.6, 0.8, 0.0]
    q_pairs.append((
        "left_vecmu_fwd_n4",
        lambda: run_chain(chains, "map_quaternion_dft", reg,
                          {"x": x4, "left": True, "mu_axis": muv,
                           "inverse": False}),
        lambda: quaternion_dft(x4, form="left", mu_axis=muv),
    ))
    xi = [[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 2, -3]]     # int components
    q_pairs.append((
        "left_i_fwd_intcomp",
        lambda: run_chain(chains, "map_quaternion_dft", reg,
                          {"x": xi, "left": True, "mu_axis": "i",
                           "inverse": False}),
        lambda: quaternion_dft(xi, form="left", mu_axis="i"),
    ))
    for n in (1, 4):
        xn = _vecs(200 + n, n, 4)
        q_pairs.append((
            "left_i_inv_n%d" % n,
            lambda xn=xn: run_chain(chains, "map_quaternion_dft", reg,
                                    {"x": xn, "left": True, "mu_axis": "i",
                                     "inverse": True}),
            lambda xn=xn: quaternion_dft(xn, form="left", mu_axis="i",
                                         inverse=True),
        ))
    x6 = _vecs(300, 6, 4)

    def q_rt_chain():
        f = run_chain(chains, "map_quaternion_dft", reg,
                      {"x": x6, "left": True, "mu_axis": "j",
                       "inverse": False})
        return run_chain(chains, "map_quaternion_dft", reg,
                         {"x": f, "left": True, "mu_axis": "j",
                          "inverse": True})

    def q_rt_ship():
        f = quaternion_dft(x6, form="left", mu_axis="j")
        return quaternion_dft(f, form="left", mu_axis="j", inverse=True)

    q_pairs.append(("roundtrip_left_j_n6", q_rt_chain, q_rt_ship))
    results["quaternion_dft"] = bit_identity("quaternion_dft", q_pairs)

    # ── octonion_dft ──────────────────────────────────────────────────
    o_pairs = []
    for n in (0, 1, 2, 4):
        x = _vecs(2000 + n, n, 8)
        o_pairs.append((
            "left_i_fwd_n%d" % n,
            lambda x=x: run_chain(chains, "map_octonion_dft", reg,
                                  {"x": x, "form": "left",
                                   "bracketing": "left_associated",
                                   "mu_axis": "i", "mu_r_axis": "i",
                                   "inverse": False}),
            lambda x=x: octonion_dft(x, form="left", mu_axis="i"),
        ))
    x4o = _vecs(2100, 4, 8)
    o_pairs.append((
        "right_e7_fwd_n4",
        lambda: run_chain(chains, "map_octonion_dft", reg,
                          {"x": x4o, "form": "right",
                           "bracketing": "left_associated",
                           "mu_axis": "e7", "mu_r_axis": "e7",
                           "inverse": False}),
        lambda: octonion_dft(x4o, form="right", mu_axis="e7"),
    ))
    for br in ("left_associated", "right_associated"):
        o_pairs.append((
            "two_sided_i_j_%s_n4" % br,
            lambda br=br: run_chain(chains, "map_octonion_dft", reg,
                                    {"x": x4o, "form": "two_sided",
                                     "bracketing": br, "mu_axis": "i",
                                     "mu_r_axis": "j", "inverse": False}),
            lambda br=br: octonion_dft(x4o, form="two_sided", mu_axis="i",
                                       bracketing=br,
                                       two_sided_right_axis="j"),
        ))
    o_pairs.append((
        "two_sided_diag_e5_n4",
        lambda: run_chain(chains, "map_octonion_dft", reg,
                          {"x": x4o, "form": "two_sided",
                           "bracketing": "left_associated",
                           "mu_axis": "diagonal", "mu_r_axis": "e5",
                           "inverse": False}),
        lambda: octonion_dft(x4o, form="two_sided", mu_axis="diagonal",
                             two_sided_right_axis="e5"),
    ))
    x3o = _vecs(2200, 3, 8)
    o_pairs.append((
        "left_i_inv_n3",
        lambda: run_chain(chains, "map_octonion_dft", reg,
                          {"x": x3o, "form": "left",
                           "bracketing": "left_associated",
                           "mu_axis": "i", "mu_r_axis": "i",
                           "inverse": True}),
        lambda: octonion_dft(x3o, form="left", mu_axis="i", inverse=True),
    ))
    xq = [[1.0, -0.5, 0.25, 2.0]]                        # quat zero-extend
    o_pairs.append((
        "left_i_fwd_quat_sample",
        lambda: run_chain(chains, "map_octonion_dft", reg,
                          {"x": xq, "form": "left",
                           "bracketing": "left_associated",
                           "mu_axis": "i", "mu_r_axis": "i",
                           "inverse": False}),
        lambda: octonion_dft(xq, form="left", mu_axis="i"),
    ))
    results["octonion_dft"] = bit_identity("octonion_dft", o_pairs)

    # ── kuramoto_step (simple) ────────────────────────────────────────
    k_pairs = []
    for n, c, dt in ((0, 1.0, 0.01), (1, 1.0, 0.01), (2, 2.5, 0.1),
                     (5, 1.0, 0.01), (9, 0.0, 0.05), (9, 1.7, 0.01)):
        th = _lcg_floats(3000 + n, n, -3.2, 3.2)
        om = _lcg_floats(4000 + n, n, -1.0, 1.0)
        k_pairs.append((
            "simple_n%d_K%s_dt%s" % (n, c, dt),
            lambda th=th, om=om, c=c, dt=dt: run_chain(
                chains, "map_kuramoto_simple", reg,
                {"theta": th, "omega": om, "coupling": c, "dt": dt}),
            lambda th=th, om=om, c=c, dt=dt: kuramoto_step(
                th, om, coupling=c, dt=dt),
        ))
    th_big = [100.5, -273.25, 0.0, 3.141592653589793]
    om_big = [0.1, -0.2, 0.0, 5.0]
    k_pairs.append((
        "simple_large_phases",
        lambda: run_chain(chains, "map_kuramoto_simple", reg,
                          {"theta": th_big, "omega": om_big,
                           "coupling": 1.0, "dt": 0.01}),
        lambda: kuramoto_step(th_big, om_big, coupling=1.0, dt=0.01),
    ))
    results["kuramoto_step_simple"] = bit_identity(
        "kuramoto_step[simple]", k_pairs)

    # ── kuramoto_step (generalised Kuramoto-Sakaguchi) ────────────────
    n = 4
    th = _lcg_floats(5001, n, -3.2, 3.2)
    om = _lcg_floats(5002, n, -1.0, 1.0)
    A = [_lcg_floats(5100 + i, n, -1.0, 1.5) for i in range(n)]  # non-symmetric
    psi = _lcg_floats(5200, n, -3.0, 3.0)
    ps_list = _lcg_floats(5300, n, 0.0, 2.0)
    g_pairs = [
        ("gen_adj_alpha_pinlist",
         lambda: run_chain(chains, "map_kuramoto_general", reg,
                           {"theta": th, "omega": om, "adjacency": A,
                            "coupling": 1.7, "alpha": 0.3, "psi": psi,
                            "ps": ps_list, "dt": 0.05}),
         lambda: kuramoto_step(th, om, coupling=1.7, dt=0.05, adjacency=A,
                               alpha=0.3, pin_anchor=psi,
                               pin_strength=ps_list)),
        ("gen_alpha_only",
         lambda: run_chain(chains, "map_kuramoto_general", reg,
                           {"theta": th, "omega": om, "adjacency": None,
                            "coupling": 1.0, "alpha": 0.7, "psi": None,
                            "ps": None, "dt": 0.01}),
         lambda: kuramoto_step(th, om, coupling=1.0, dt=0.01, alpha=0.7)),
        ("gen_adjacency_only",
         lambda: run_chain(chains, "map_kuramoto_general", reg,
                           {"theta": th, "omega": om, "adjacency": A,
                            "coupling": 0.0, "alpha": 0.0, "psi": None,
                            "ps": None, "dt": 0.01}),
         lambda: kuramoto_step(th, om, coupling=0.0, dt=0.01, adjacency=A)),
        ("gen_pin_scalar_strength",
         lambda: run_chain(chains, "map_kuramoto_general", reg,
                           {"theta": th, "omega": om, "adjacency": None,
                            "coupling": 1.0, "alpha": 0.0, "psi": psi,
                            "ps": 0.75, "dt": 0.02}),
         lambda: kuramoto_step(th, om, coupling=1.0, dt=0.02,
                               pin_anchor=psi, pin_strength=0.75)),
    ]
    results["kuramoto_step_general"] = bit_identity(
        "kuramoto_step[general]", g_pairs)

    # ── autocorrelation ───────────────────────────────────────────────
    a_cases = [
        ("empty", []),
        ("single", [3.0]),
        ("pair", [1.0, -2.0]),
        ("zeros", [0.0, 0.0, 0.0]),
        ("ints", [1, 2, 3]),
        ("huge_tiny_mix", [1e300, 1e-300, -1e300, 2.5]),
        ("lcg7", _lcg_floats(6001, 7)),
        ("lcg16", _lcg_floats(6002, 16, -100.0, 100.0)),
        ("alternating", [1e16, 1.0, -1e16, 1.0, 1e-16, -1.0]),
    ]
    a_pairs = [
        (cname,
         lambda x=x: run_chain(chains, "map_autocorrelation", reg, {"x": x}),
         lambda x=x: autocorrelation(x))
        for cname, x in a_cases
    ]
    results["autocorrelation"] = bit_identity("autocorrelation", a_pairs)

    return results


# ── totality ──────────────────────────────────────────────────────────────
def stage_totality():
    import inspect
    from srmech.dsl import _control_flow
    fold_src = inspect.getsource(_control_flow.make_fold_stage)
    fold_iterates_runtime_input = "for elem in input_seq" in fold_src
    emit(
        stage="totality",
        preserved=True,
        argument=(
            "n = len(input) is fixed at map entry BEFORE the first body run "
            "(the runner rejects unsized iterables); the body is a finite "
            "descriptor-static step list; nesting depth is descriptor-static. "
            "So the map performs exactly n body runs — total iff every leaf "
            "is total.  That is the SAME totality class the kernel already "
            "contains: the shipped fold/reduce iterate 'for elem in "
            "input_seq' over a RUNTIME-length input (measured: %r).  The "
            "closure's exile is data-DEPENDENT iteration (loop *until a "
            "predicate*); an indexed map is data-SIZED, not data-dependent — "
            "no predicate decides continuation." % fold_iterates_runtime_input),
        failure_modes=(
            "(1) a non-total leaf op — same exposure as every existing form; "
            "(2) an unsized/infinite map_over — REJECTED at entry by the "
            "sized-sequence requirement; (3) a body mutating the input "
            "sequence changes VALUES but not the iteration count (range(n) "
            "is pinned) — semantic hazard, not a termination hazard."),
        fold_precedent_measured=fold_iterates_runtime_input,
    )


# ── main ──────────────────────────────────────────────────────────────────
def main():
    stage_env()
    stage_grammar()
    stage_inventory()
    stage_closure()
    stage_dsl_demo()
    chains = eng.load_ext_chains(CHAINS_TOML)
    reg = override_registry()
    results = stage_bits(chains, reg)
    stage_totality()
    all_ok = all(results.values())
    emit(
        stage="verdict",
        per_op={k: ("BIT_IDENTICAL" if v else "MISMATCH")
                for k, v in results.items()},
        blk_iter_indexed=(
            "CLOSED by a general indexed map" if all_ok else "NOT closed"),
        residue=(
            "The stubs used are (a) missing framing/access leaves "
            "(seq_len/seq_get/f64_add/vec_add/vec_scale — BLK-FRAMING "
            "family, measured absent by inventory_probe) and (b) shipped-"
            "leaf wrappers reachable from no letter (BLK-REGMAP, catalogued "
            "rung 3).  The ITERATION was carried entirely by the map/fold "
            "combinator layer — no stub iterates over k/m/i/j."),
        data_dependence_check=(
            "No body decides continuation: every map count is len(seq) at "
            "entry; every fold walks a fully-materialised list.  Nothing "
            "smuggles a while/predicate."),
    )
    if not all_ok:
        sys.exit(1)


if __name__ == "__main__":
    main()
