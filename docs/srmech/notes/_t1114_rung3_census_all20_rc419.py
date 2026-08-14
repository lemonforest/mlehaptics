"""SPIKE `#T1114` rung 3 — CENSUS: invert ALL 20 cascade-catalog descriptors
into executable ADR-0008 §2 chains, recording exactly where each stops.

Verdict criterion (mechanical): distinct-blocker count vs descriptors
attempted, in attempt order.  Converges -> generalized instrument; grows
linearly -> per-op retrofit.

Reuses the `#T1114` rung-1 machinery: the external stub module
`_rung1_spike_ops_rc419.py` (predecessor artifact, copied verbatim) and
`_rung1_best_rational_signed_chain_rc419.toml`.  Anything run under an
override registry or with external stubs is LABELLED and never counted
as a pass.

Attempt order maximises diversity of failure mode (brief §5), controls
first.

No `abs()`.  No `math` / `fractions` / `decimal` / `numpy`.  `time` /
`json` / `os` / `sys` / `traceback` are harness-side stdlib; srmech
ships no timing surface (`#T1116`) so no timing is needed here anyway.

Run (WSL2, numpy-absent):
    cd docs/srmech/python
    PYTHONPATH=$PWD python3 ../notes/_t1114_rung3_census_all20_rc419.py \
        > ../notes/t1114_rung3_census_all20_rc419_20260809.ndjson
"""

from __future__ import annotations

import importlib
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
CENSUS_TOML = os.path.join(HERE, "_t1114_rung3_census_chains_rc419.toml")
BRS_TOML = os.path.join(HERE, "_rung1_best_rational_signed_chain_rc419.toml")

import srmech  # noqa: E402
from srmech import _toml as _srmech_toml  # noqa: E402
from srmech.cascade import compose  # noqa: E402

WORKTREE_TAG = "agent-af47432679b6f30f9"


def emit(**kw):
    kw.setdefault("spike", "T1114")
    kw.setdefault("rung", 3)
    kw.setdefault("srmech_version", srmech.__version__)
    print(json.dumps(kw, sort_keys=True))


def _exc(e):
    return {"error_type": type(e).__name__, "error": str(e)[:300]}


# ── blocker ledger (attempt-order bookkeeping) ────────────────────────
DISTINCT: list = []          # blocker ids in first-seen order
SEQUENCE: list = []          # distinct-count after each attempt
ATTEMPTS: list = []          # descriptor names in attempt order


def note_blockers(descriptor, blocker_ids):
    for b in blocker_ids:
        if b not in DISTINCT:
            DISTINCT.append(b)
    ATTEMPTS.append(descriptor)
    SEQUENCE.append(len(DISTINCT))


# ── environment attestation ───────────────────────────────────────────
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


# ── reachability census: catalog NAME vs delegation TARGET ────────────
def _registry_modules():
    mods = {}
    for cid, modname in sorted(compose.DEFAULT_CLASS_REGISTRY.items()):
        mods[cid] = importlib.import_module(modname)
    return mods


def reach(mods, opname):
    return sorted(cid for cid, m in mods.items() if callable(getattr(m, opname, None)))


CATALOG_NAMES = [
    "autocorrelation", "best_rational_signed", "chiral_dual", "chiral_flip",
    "cyclic_gcd", "cyclic_mod_add", "cyclic_mod_inv", "cyclic_mod_mul",
    "cyclic_mod_mul_wide", "cyclic_mod_pow", "encode_loe_content",
    "kuramoto_step", "magnitude", "net_chirality", "octonion_dft",
    "parallel_sector_dispatch", "pin_slot_at_zero", "quaternion_dft",
    "reorient", "schur_complement",
]

# descriptor -> the op(s) a faithful inversion needs, with their homes
DELEGATION_TARGETS = {
    "cyclic_gcd": ["gcd"],
    "cyclic_mod_add": ["mod_add"], "cyclic_mod_mul": ["mod_mul"],
    "cyclic_mod_pow": ["mod_pow"], "cyclic_mod_inv": ["mod_inv"],
    "cyclic_mod_mul_wide": ["mod_mul_wide"],
    "schur_complement": ["schur_complement"],
}

SUB_OP_PROBES = [
    # multi-class decompositions probe these
    "pin_slot_at_zero", "reorient", "magnitude", "chiral_flip",
    "best_rational", "scale_round_half_even", "pair", "sin",
    "hypercomplex_exp", "quaternion_left_mult", "quaternion_right_mult",
    "mint_vector", "permute", "bind", "bundle", "sha256_bytes",
]


def stage_reachability():
    mods = _registry_modules()
    by_name = {n: reach(mods, n) for n in CATALOG_NAMES}
    reachable_by_name = sorted(n for n, v in by_name.items() if v)
    target_ok = {}
    for desc, targets in DELEGATION_TARGETS.items():
        target_ok[desc] = all(reach(mods, t) for t in targets)
    probes = {n: reach(mods, n) for n in SUB_OP_PROBES}
    # homes of the unreachable sub-ops (measured, not asserted)
    homes = {}
    for modpath, names in (
        ("srmech.cascade.hypercomplex_dft", ["hypercomplex_exp", "octonion_dft", "quaternion_dft"]),
        ("srmech.physics.qm.quaternion", ["quaternion_left_mult", "quaternion_right_mult"]),
        ("srmech.signal_processing.rbs_hdc_instrument", ["mint_vector", "encode_loe_content"]),
        ("srmech.cascade.atoms", ["pin_slot_at_zero", "reorient", "magnitude", "chiral_flip", "chiral_dual", "net_chirality"]),
        ("srmech.cascade.composites", ["best_rational_signed", "kuramoto_step", "autocorrelation", "cyclic_gcd"]),
        ("srmech.cascade.parallel", ["parallel_sector_dispatch"]),
    ):
        m = importlib.import_module(modpath)
        homes[modpath] = sorted(n for n in names if callable(getattr(m, n, None)))
    emit(
        stage="reachability_census",
        reachable_by_catalog_name=reachable_by_name,
        n_reachable_by_name=len(reachable_by_name),
        delegation_target_fully_reachable=sorted(
            d for d, ok in target_ok.items() if ok),
        n_delegation_target_reachable=sum(target_ok.values()),
        sub_op_probes={k: v for k, v in probes.items() if v},
        sub_op_probes_unreachable=sorted(k for k, v in probes.items() if not v),
        op_homes_measured=homes,
        note=("Brief said '1 of 20 reachable'. True for the catalog NAME. "
              "But 7 of 20 descriptors have their full delegation TARGET "
              "reachable under the primitive's own name (gcd, mod_*, "
              "schur_complement) — reachability-by-name undercounts "
              "invertibility."),
    )


# ── chain loading + execution helpers ─────────────────────────────────
def load_chains(path):
    with open(path, "rb") as fh:
        d = _srmech_toml.loads(fh.read().decode("utf-8"))
    return {c["name"]: c for c in d["catalog"]["operator_chain"]}


def try_chain(chain_dict, registry, inputs, label):
    """parse -> resolve -> run; returns (phase_reached, result_or_err)."""
    rec = {"stage": "chain_attempt", "chain": chain_dict.get("name"),
           "registry": label}
    try:
        spec = compose.parse_chain_spec(chain_dict)
        rec["parsed"] = True
    except Exception as e:  # noqa: BLE001
        rec.update(parsed=False, phase="parse", **_exc(e))
        emit(**rec)
        return "parse", None
    try:
        runner = compose.resolve_chain(spec, registry)
        rec["resolved"] = True
    except Exception as e:  # noqa: BLE001
        rec.update(resolved=False, phase="resolve", **_exc(e))
        emit(**rec)
        return "resolve", None
    try:
        out = runner(row=None, **inputs)
        rec.update(ran=True, output_type=type(out).__name__)
        emit(**rec)
        return "ran", out
    except Exception as e:  # noqa: BLE001
        rec.update(ran=False, phase="run", **_exc(e))
        emit(**rec)
        return "run", None


def bit_identity(runner_fn, oracle_fn, cases, label, via_repr=False):
    n_ok, mismatches = 0, []
    for name, kwargs in cases:
        try:
            ref = oracle_fn(**kwargs)
        except Exception as e:  # noqa: BLE001
            ref = ("RAISED", type(e).__name__)
        try:
            got = runner_fn(**kwargs)
        except Exception as e:  # noqa: BLE001
            got = ("RAISED", type(e).__name__)
        same = (repr(got) == repr(ref)) if via_repr else (got == ref)
        if same:
            n_ok += 1
        elif len(mismatches) < 10:
            mismatches.append({"case": name, "ref": repr(ref)[:120],
                               "got": repr(got)[:120]})
    emit(stage="bit_identity", variant=label, n_cases=len(cases),
         n_identical=n_ok, n_mismatch=len(cases) - n_ok,
         first_mismatches=mismatches)
    return n_ok == len(cases)


# override registries (EXTERNAL see-past instruments; labelled)
def override_atoms():
    r = dict(compose.DEFAULT_CLASS_REGISTRY)
    r["K"] = "srmech.cascade.atoms"
    r["C"] = "srmech.cascade.atoms"
    return r


def override_parallel():
    r = dict(compose.DEFAULT_CLASS_REGISTRY)
    r["C"] = "srmech.cascade.parallel"
    return r


def override_loe():
    r = dict(compose.DEFAULT_CLASS_REGISTRY)
    r["M"] = "srmech.signal_processing.rbs_hdc_instrument"
    return r


def spike_registry():
    sys.path.insert(0, HERE)
    r = dict(compose.DEFAULT_CLASS_REGISTRY)
    for letter in ("K", "C", "N", "B"):
        r[letter] = "_rung1_spike_ops_rc419"
    return r


# ── the 20 attempts, in diversity order ───────────────────────────────
def main():
    stage_env()
    stage_reachability()
    chains = load_chains(CENSUS_TOML)
    from srmech.cascade import atoms, composites, parallel
    from srmech.math import laplacian

    # 1. CONTROL: cyclic_gcd ------------------------------------------
    phase, _ = try_chain(chains["inv_cyclic_gcd"], None,
                         {"a": 12, "b": 18}, "default")
    spec = compose.parse_chain_spec(chains["inv_cyclic_gcd"])
    runner = compose.resolve_chain(spec, None)
    ok = bit_identity(
        lambda a, b: runner(row=None, a=a, b=b),
        composites.cyclic_gcd,
        [("both_zero", {"a": 0, "b": 0}), ("a_zero", {"a": 0, "b": 7}),
         ("b_zero", {"a": 7, "b": 0}), ("simple", {"a": 12, "b": 18}),
         ("large", {"a": 2**64 - 1, "b": 600}),
         ("negative_raises", {"a": -4, "b": 6}),
         ("over_uint64_raises", {"a": 2**64, "b": 2})],
        "control/cyclic_gcd")
    emit(stage="attempt", n=1, descriptor="cyclic_gcd", strategy="delegate",
         status="PASS" if (phase == "ran" and ok) else "HARNESS_FAIL",
         blockers=[], control=True)
    assert phase == "ran" and ok, "CONTROL 1 FAILED — harness wrong, stop"
    note_blockers("cyclic_gcd", [])

    # 2. CONTROL: schur_complement ------------------------------------
    lap = laplacian.dense_laplacian(4, [(0, 1), (1, 2), (2, 3)])
    phase, out = try_chain(chains["inv_schur_complement"], None,
                           {"lap": lap, "boundary_idx": [0, 3]}, "default")
    ref = laplacian.schur_complement(lap, [0, 3])
    ok = (phase == "ran") and (repr(out) == repr(ref))
    emit(stage="attempt", n=2, descriptor="schur_complement",
         strategy="delegate",
         status="PASS" if ok else "HARNESS_FAIL",
         blockers=[], control=True,
         note="Only catalog op reachable from the default registry by "
              "its own name; carrier (Mat) threads through the engine "
              "with identity preserved.")
    assert ok, "CONTROL 2 FAILED — harness wrong, stop"
    note_blockers("schur_complement", [])

    # 3./4. octonion_dft / quaternion_dft -----------------------------
    for n, desc in ((3, "octonion_dft"), (4, "quaternion_dft")):
        emit(
            stage="attempt", n=n, descriptor=desc, strategy="decompose",
            status="BLOCKED",
            blockers=["BLK-ITER-INDEXED", "BLK-REGMAP"],
            first_blocker="BLK-ITER-INDEXED",
            detail=(
                "X[k] = SUM_m W(k,m)*x[m] is an INDEXED map over runtime "
                "N = len(x): every output element needs its index k, "
                "random access to the whole input, and a k*m twiddle. "
                "ADR-0008 SS2 has no iteration of any kind; the dsl "
                "[[stage]] kernel's five forms are apply/loop_n(static "
                "count)/fold/reduce/parallel — linear catamorphisms with "
                "no index and no random access, and _control_flow.py "
                "declares data-dependent iteration deliberately EXILED "
                "to the op-instance layer.  Second blocker: the sub-ops "
                "(hypercomplex_exp in srmech.cascade.hypercomplex_dft; "
                "quaternion_left_mult/right_mult in "
                "srmech.physics.qm.quaternion) are reachable from no "
                "letter (BLK-REGMAP).  Delegation-granularity chains DO "
                "run: predecessor rung 2 proved forward->inverse as a "
                "2-step chain bit-identical + roundtrip under an "
                "override registry — delegation, not decomposition."),
            oracle_note=("'generate the op' works (delegation); "
                         "'generate an oracle' does NOT — a delegation "
                         "chain calls the very op it would check."),
        )
        note_blockers(desc, ["BLK-ITER-INDEXED", "BLK-REGMAP"])

    # 5. kuramoto_step -------------------------------------------------
    mods = _registry_modules()
    sin_reach = reach(mods, "sin")
    emit(
        stage="attempt", n=5, descriptor="kuramoto_step",
        strategy="decompose", status="BLOCKED",
        blockers=["BLK-ITER-INDEXED", "BLK-REGMAP"],
        first_blocker="BLK-ITER-INDEXED",
        detail=(
            "out[i] = theta[i] + dt*(omega[i] + SUM_j A_ij*sin(theta[j]-"
            "theta[i]-alpha)): a MAP-OF-FOLDS over runtime n, each inner "
            "fold parameterized by the outer index i.  The engine has no "
            "way to bind an iteration count at all; the dsl loop_n binds "
            "a STATIC count at descriptor level while n = len(theta) is "
            "data-dependent; fold/reduce are linear and index-free.  "
            "sin itself is NOT a blocker: srmech.math.rational.sin"
            "(x: float) is registered and reachable via N = %r.  "
            "Delegation home srmech.cascade.composites reachable from no "
            "letter (BLK-REGMAP)." % (sin_reach,)),
    )
    note_blockers("kuramoto_step", ["BLK-ITER-INDEXED", "BLK-REGMAP"])

    # 6. encode_loe_content -------------------------------------------
    # Decomposition: A mint -> A stride -> C permute -> M bind.
    # permute/bind ARE reachable (M -> srmech.math.hdc).  mint_vector is
    # not (home srmech.signal_processing.rbs_hdc_instrument).  The
    # stride int.from_bytes(digest[:8], 'little') % D has no registered
    # byte-slice/int-parse op (mod alone would be expressible as the
    # I.mod_add(a, b=0, n=D) idiom).
    phase_def, _ = try_chain(chains["del_encode_loe_content"], None,
                             {"content": "census"}, "default")
    phase_ov, out = try_chain(chains["del_encode_loe_content"],
                              override_loe(), {"content": "census"},
                              "override_M_to_signal_processing[EXTERNAL]")
    from srmech.signal_processing.rbs_hdc_instrument import encode_loe_content
    deleg_ok = (phase_ov == "ran" and out == encode_loe_content("census"))
    emit(
        stage="attempt", n=6, descriptor="encode_loe_content",
        strategy="decompose", status="BLOCKED",
        blockers=["BLK-REGMAP", "BLK-FRAMING"],
        first_blocker="BLK-REGMAP",
        default_registry_phase=phase_def,
        delegation_seen_past_blocker=deleg_ok,
        detail=(
            "Decomposition A.mint_vector -> A.stride -> C/M.permute -> "
            "M.bind stops twice: (1) mint_vector lives in "
            "srmech.signal_processing.rbs_hdc_instrument — no letter "
            "reaches srmech.signal_processing.* (BLK-REGMAP, third "
            "unreachable home after cascade.* and physics.qm.*); "
            "(2) stride = int.from_bytes(sha256(content)[0:8], "
            "'little') %% D — no registered byte-slice / int-parse op "
            "(Class-B framing territory; BLK-FRAMING, same family as "
            "the missing pair op).  NOT blocked by iteration: permute + "
            "bind are whole-vector ops and D is descriptor-static.  "
            "hdc.permute and hdc.bind ARE reachable via M."),
    )
    note_blockers("encode_loe_content", ["BLK-REGMAP", "BLK-FRAMING"])

    # 7. parallel_sector_dispatch -------------------------------------
    phase_def, _ = try_chain(chains["del_parallel_sector_dispatch"], None,
                             {"x": [1.0, 2.0], "body": atoms.chiral_flip},
                             "default")
    phase_ov, out = try_chain(chains["del_parallel_sector_dispatch"],
                              override_parallel(),
                              {"x": [1.0, 2.0], "body": atoms.chiral_flip},
                              "override_C_to_parallel[EXTERNAL]")
    ref = parallel.parallel_sector_dispatch(atoms.chiral_flip, [1.0, 2.0],
                                            combine="sector0")
    runtime_injection_ok = (phase_ov == "ran"
                           and repr(out) == repr(ref))
    emit(
        stage="attempt", n=7, descriptor="parallel_sector_dispatch",
        strategy="delegate", status="BLOCKED",
        blockers=["BLK-HIGHER-ORDER", "BLK-REGMAP"],
        first_blocker="BLK-HIGHER-ORDER",
        runtime_callable_injection_ran=runtime_injection_ok,
        detail=(
            "kind = 'combinator': the body parameter is op-valued.  A "
            "step's `op` field is a static name (compose.py:398) and the "
            "reference grammar's namespaces are row|input|step|catalog "
            "only (compose.py:107) — there is no way for a DESCRIPTOR to "
            "name an op as a value.  Measured boundary: a CALLABLE "
            "passed as a runtime input threads fine through @input.body "
            "(the engine runs the dispatch bit-identically under an "
            "override registry), so the gap is descriptor-level naming, "
            "not engine-level plumbing.  The dsl surface resolves this "
            "with its parallel_body discriminator and rejects op= usage "
            "by design — a different surface."),
    )
    note_blockers("parallel_sector_dispatch",
                  ["BLK-HIGHER-ORDER", "BLK-REGMAP"])

    # 8. chiral_flip — LEAF -------------------------------------------
    phase_def, _ = try_chain(chains["leaf_chiral_flip"], None,
                             {"seq": [1, 2, 3]}, "default")
    phase_ov, out = try_chain(chains["leaf_chiral_flip"], override_atoms(),
                              {"seq": [1, 2, 3]},
                              "override_KC_to_atoms[EXTERNAL]")
    emit(stage="attempt", n=8, descriptor="chiral_flip", strategy="leaf",
         status="LEAF", blockers=[],
         default_registry_phase=phase_def,
         self_delegation_ran=(phase_ov == "ran" and out == [3, 2, 1]),
         detail=("The atom IS the Class-C primitive (seq[::-1]); nothing "
                 "lower-level is registered to compose.  Correctly "
                 "irreducible.  Even self-delegation fails under the "
                 "default registry (BLK-REGMAP already catalogued)."))
    note_blockers("chiral_flip", [])

    # 9. chiral_dual ---------------------------------------------------
    phase_ov, out = try_chain(chains["inv_chiral_dual_fixed_body"],
                              override_atoms(), {"x": [1, 2, 3]},
                              "override_KC_to_atoms[EXTERNAL]")
    ref = atoms.chiral_dual(atoms.chiral_flip, [1, 2, 3])
    fixed_ok = (phase_ov == "ran" and out == ref)
    emit(
        stage="attempt", n=9, descriptor="chiral_dual",
        strategy="decompose", status="BLOCKED",
        blockers=["BLK-HIGHER-ORDER", "BLK-REGMAP"],
        first_blocker="BLK-HIGHER-ORDER",
        fixed_body_chain_bit_identical=fixed_ok,
        detail=(
            "operation = chiral_flip(op(chiral_flip(x))) with `op` a "
            "PARAMETER.  With the body fixed the 3-step chain runs "
            "bit-identically (measured, override registry) — the only "
            "irreducible residue is the op-valued parameter, same "
            "blocker as parallel_sector_dispatch."),
    )
    note_blockers("chiral_dual", ["BLK-HIGHER-ORDER", "BLK-REGMAP"])

    # 10. net_chirality ------------------------------------------------
    # SS2 surface: no fold/reduce at all.  dsl surface: fold exists —
    # measure whether it can bind the shipped reorient as-is.
    from srmech.dsl._control_flow import make_fold_stage
    fold_result = None
    try:
        fold = make_fold_stage(1, atoms.reorient, {})
        fold_result = ("ran", fold([1, -1, 1]))
    except Exception as e:  # noqa: BLE001
        fold_result = ("raised", type(e).__name__, str(e)[:160])
    emit(
        stage="attempt", n=10, descriptor="net_chirality",
        strategy="decompose", status="BLOCKED",
        blockers=["BLK-ITER-COMPOSE", "BLK-REGMAP"],
        first_blocker="BLK-ITER-COMPOSE",
        dsl_fold_with_shipped_reorient=repr(fold_result),
        detail=(
            "reduce(reorient, orientations, 1) over a runtime-length "
            "list.  ADR-0008 SS2 has NO fold/reduce (SS11 deferral) — "
            "that is BLK-ITER-COMPOSE, distinct from BLK-ITER-INDEXED "
            "because the dsl surface's fold/reduce ARE linear "
            "catamorphisms over runtime sequences, i.e. this op IS "
            "expressible there in principle.  Measured wrinkle: the dsl "
            "fold contract calls op_fn(acc, elem) POSITIONALLY, and the "
            "shipped reorient is reorient(value, *, orientation=) — "
            "kw-only — so even the surface that has fold cannot bind "
            "the canonical Class-C atom as shipped (see "
            "dsl_fold_with_shipped_reorient).  Short-circuit-on-0 is "
            "NOT a blocker: 0 is absorbing, so the fold without early "
            "exit is value-identical (vacuous, like the rung-1 "
            "branching result)."),
    )
    note_blockers("net_chirality", ["BLK-ITER-COMPOSE", "BLK-REGMAP"])

    # 11. autocorrelation ---------------------------------------------
    emit(
        stage="attempt", n=11, descriptor="autocorrelation",
        strategy="decompose", status="BLOCKED",
        blockers=["BLK-ITER-INDEXED", "BLK-REGMAP"],
        first_blocker="BLK-ITER-INDEXED",
        detail=(
            "out[k] = SUM_i x[i]*x[(i+k) %% n]: indexed circular "
            "correlation over runtime n — same indexed/data-dependent "
            "map family as the DFTs and kuramoto (each output element "
            "needs its index and random access).  Delegation home "
            "srmech.cascade.composites unreachable (BLK-REGMAP)."),
    )
    note_blockers("autocorrelation", ["BLK-ITER-INDEXED", "BLK-REGMAP"])

    # 12. pin_slot_at_zero — LEAF -------------------------------------
    phase_def, _ = try_chain(chains["leaf_pin_slot_at_zero"], None,
                             {"x": -2.5}, "default")
    phase_ov, out = try_chain(chains["leaf_pin_slot_at_zero"],
                              override_atoms(), {"x": -2.5},
                              "override_KC_to_atoms[EXTERNAL]")
    emit(stage="attempt", n=12, descriptor="pin_slot_at_zero",
         strategy="leaf", status="LEAF", blockers=[],
         default_registry_phase=phase_def,
         self_delegation_ran=(phase_ov == "ran"
                              and out == atoms.pin_slot_at_zero(-2.5)),
         detail="The atom IS the Class-K primitive. Correctly irreducible.")
    note_blockers("pin_slot_at_zero", [])

    # 13. magnitude — the in-schema select idiom ----------------------
    phase_def, _ = try_chain(chains["inv_magnitude_idiom"], None,
                             {"x": -2.5}, "default")
    spec = compose.parse_chain_spec(chains["inv_magnitude_idiom"])
    runner = compose.resolve_chain(spec, override_atoms())
    mag_cases = [(lbl, {"x": v}) for lbl, v in
                 [("zero", 0.0), ("neg_zero", -0.0), ("sub_band", 1e-13),
                  ("sub_band_neg", -1e-13), ("half", 0.5), ("neg", -3.7),
                  ("pos", 3.7), ("inf", float("inf")),
                  ("neg_inf", float("-inf")), ("nan", float("nan"))]]
    ok = bit_identity(lambda x: runner(row=None, x=x), atoms.magnitude,
                      mag_cases, "override[EXTERNAL]/magnitude_idiom",
                      via_repr=True)
    emit(
        stage="attempt", n=13, descriptor="magnitude",
        strategy="decompose", status="BLOCKED",
        blockers=["BLK-REGMAP"], first_blocker="BLK-REGMAP",
        default_registry_phase=phase_def,
        idiom_chain_bit_identical=ok,
        detail=(
            "operation = pin_slot_at_zero(x)[1] — a real 2-step "
            "decomposition.  FINDING: the 'missing select op' is NOT a "
            "blocker: @step[0].output[1] indexing + reorient(value=..., "
            "orientation=1) (identity re-application) express the "
            "selection with SHIPPED ops only, bit-identical on the "
            "boundary sweep incl. -0.0/NaN/inf (measured).  The only "
            "blocker is reachability (BLK-REGMAP).  Contrast with pair: "
            "SELECT is soluble in-schema; PACK is not — nothing "
            "registered builds a tuple."),
    )
    note_blockers("magnitude", ["BLK-REGMAP"])

    # 14. reorient — LEAF ---------------------------------------------
    phase_def, _ = try_chain(chains["leaf_reorient"], None,
                             {"value": 5, "orientation": -1}, "default")
    phase_ov, out = try_chain(chains["leaf_reorient"], override_atoms(),
                              {"value": 5, "orientation": -1},
                              "override_KC_to_atoms[EXTERNAL]")
    emit(stage="attempt", n=14, descriptor="reorient", strategy="leaf",
         status="LEAF", blockers=[],
         default_registry_phase=phase_def,
         self_delegation_ran=(phase_ov == "ran" and out == -5),
         detail="The atom IS the Class-C primitive. Correctly irreducible.")
    note_blockers("reorient", [])

    # 15. best_rational_signed (predecessor rung-1 machinery reused) --
    brs = load_chains(BRS_TOML)
    phase_def, _ = try_chain(brs["best_rational_signed_c_with_pack"], None,
                             {"x": 0.5, "fine_scale": 1000000,
                              "max_denominator": 100}, "default")
    phase_ov, _ = try_chain(brs["best_rational_signed_c_with_pack"],
                            override_atoms(),
                            {"x": 0.5, "fine_scale": 1000000,
                             "max_denominator": 100},
                            "override_KC_to_atoms[EXTERNAL]")
    spike = spike_registry()
    phase_sp, _ = try_chain(brs["best_rational_signed_c_with_pack"], spike,
                            {"x": 0.5, "fine_scale": 1000000,
                             "max_denominator": 100},
                            "spike_ops[EXTERNAL_STUBS]")
    # full 219-case sweep vs the shipped op, stubs labelled
    cases = [(lbl, {"x": v}) for lbl, v in
             [("origin_plus", 0.0), ("origin_minus", -0.0),
              ("nan", float("nan")), ("sub_dead_band_pos", 1e-13),
              ("sub_dead_band_neg", -1e-13), ("dead_band_edge", 1e-12),
              ("half_boundary", 0.5), ("half_boundary_neg", -0.5),
              ("bankers_0p25", 0.25), ("bankers_0p75", 0.75),
              ("bankers_1p25", 1.25), ("bankers_1p75", 1.75),
              ("neg_simple", -0.3333333333), ("pos_simple", 0.3333333333),
              ("inf_pos", float("inf")), ("inf_neg", float("-inf")),
              ("overflow_ge_2_63", 1e19), ("overflow_neg", -1e19)]
             + [("sweep_%d" % k, k / 50.0) for k in range(-100, 101)]]
    spec = compose.parse_chain_spec(brs["best_rational_signed_c_with_pack"])
    runner = compose.resolve_chain(spec, spike)
    ok = bit_identity(
        lambda x: runner(row=None, x=x, fine_scale=1000000,
                         max_denominator=100),
        lambda x: composites.best_rational_signed(
            x, max_denominator=100, fine_scale=1000000),
        cases, "spike_ops[EXTERNAL_STUBS]/best_rational_signed_c")
    emit(
        stage="attempt", n=15, descriptor="best_rational_signed",
        strategy="decompose", status="BLOCKED",
        blockers=["BLK-REGMAP", "BLK-N-SCALE-ROUND", "BLK-FRAMING"],
        first_blocker="BLK-REGMAP",
        default_registry_phase=phase_def,
        override_registry_phase=phase_ov,
        stub_registry_phase=phase_sp,
        stubbed_chain_bit_identical_219=ok,
        detail=(
            "Rung-1 result re-verified: default registry stops at "
            "resolve (BLK-REGMAP); override registry stops at the "
            "unregistered Class-N scale_round_half_even "
            "(BLK-N-SCALE-ROUND); with the predecessor's two EXTERNAL "
            "stubs (scale_round_half_even + pair — the pair op is "
            "BLK-FRAMING, forced by last-step-only return, "
            "compose.py:853) the 5-step chain is bit-identical on "
            "219/219 boundary cases.  Stubs are labelled and NOT "
            "counted as a pass."),
    )
    note_blockers("best_rational_signed",
                  ["BLK-REGMAP", "BLK-N-SCALE-ROUND", "BLK-FRAMING"])

    # 16-20. cyclic_mod_* family --------------------------------------
    mod_plans = [
        (16, "cyclic_mod_add", "inv_cyclic_mod_add",
         composites.cyclic_mod_add,
         [("simple", {"a": 5, "b": 9, "n": 7}),
          ("wrap", {"a": 6, "b": 6, "n": 7}),
          ("n_one", {"a": 5, "b": 9, "n": 1}),
          ("zero_n_raises", {"a": 1, "b": 1, "n": 0})]),
        (17, "cyclic_mod_mul", "inv_cyclic_mod_mul",
         composites.cyclic_mod_mul,
         [("simple", {"a": 5, "b": 9, "n": 7}),
          ("big", {"a": 2**31, "b": 2**31, "n": 97}),
          ("zero", {"a": 0, "b": 9, "n": 7})]),
        (18, "cyclic_mod_pow", "inv_cyclic_mod_pow",
         composites.cyclic_mod_pow,
         [("simple", {"a": 3, "k": 4, "n": 7}),
          ("k_zero", {"a": 3, "k": 0, "n": 7}),
          ("fermat", {"a": 2, "k": 96, "n": 97})]),
        (19, "cyclic_mod_inv", "inv_cyclic_mod_inv",
         composites.cyclic_mod_inv,
         [("simple", {"a": 3, "n": 7}),
          ("non_coprime_raises", {"a": 6, "n": 9}),
          ("one", {"a": 1, "n": 97})]),
        (20, "cyclic_mod_mul_wide", "inv_cyclic_mod_mul_wide",
         composites.cyclic_mod_mul_wide,
         [("simple", {"a": 5, "b": 9, "n": 7}),
          ("wide", {"a": 2**63 - 1, "b": 2**63 - 1, "n": 2**61 - 1})]),
    ]
    for n, desc, chain_name, oracle, cases in mod_plans:
        phase, _ = try_chain(chains[chain_name], None, dict(cases[0][1]),
                             "default")
        spec = compose.parse_chain_spec(chains[chain_name])
        runner = compose.resolve_chain(spec, None)
        ok = bit_identity(lambda **kw: runner(row=None, **kw), oracle,
                          cases, "default/%s" % desc)
        status = "PASS" if (phase == "ran" and ok) else "HARNESS_FAIL"
        emit(stage="attempt", n=n, descriptor=desc, strategy="delegate",
             status=status, blockers=[])
        note_blockers(desc, [])

    # ── verdict data ──────────────────────────────────────────────────
    statuses = {}
    emit(
        stage="distinct_blocker_sequence",
        attempt_order=ATTEMPTS,
        sequence=SEQUENCE,
        distinct_blockers_first_seen_order=DISTINCT,
        n_distinct=len(DISTINCT),
        last_new_blocker_at_attempt=(
            max(i + 1 for i, v in enumerate(SEQUENCE)
                if v > (SEQUENCE[i - 1] if i else 0)) if DISTINCT else 0),
    )
    emit(
        stage="blocker_catalogue",
        catalogue=[
            {"id": "BLK-ITER-INDEXED",
             "surface": "BOTH declarative surfaces (absent from compose "
                        "SS2 entirely; deliberately excluded from the "
                        "dsl five-form kernel — _control_flow.py: "
                        "data-dependent iteration EXILED to the "
                        "op-instance layer)",
             "blocks": ["octonion_dft", "quaternion_dft", "kuramoto_step",
                        "autocorrelation"],
             "statement": "No indexed / data-dependent map: out[k] = "
                          "f(k, whole_input) over runtime n has no "
                          "declarative form; loop_n is static-count, "
                          "fold/reduce are index-free linear."},
            {"id": "BLK-REGMAP",
             "surface": "compose.py SS3.1 (ADR-0008)",
             "blocks": ["octonion_dft", "quaternion_dft", "kuramoto_step",
                        "encode_loe_content", "parallel_sector_dispatch",
                        "chiral_dual", "net_chirality", "autocorrelation",
                        "magnitude", "best_rational_signed",
                        "chiral_flip", "pin_slot_at_zero", "reorient"],
             "statement": "Fixed letter->ONE-module map: cascade op homes "
                          "(srmech.cascade.atoms/.composites/"
                          ".hypercomplex_dft/.parallel, "
                          "srmech.physics.qm.quaternion, "
                          "srmech.signal_processing.rbs_hdc_instrument) "
                          "are reachable from no letter; sharper form: "
                          "one letter maps to ONE module per resolution, "
                          "so two same-class ops in different modules "
                          "cannot coexist in one chain."},
            {"id": "BLK-FRAMING",
             "surface": "op inventory (Class B) + compose.py:853 "
                        "last-step-only return",
             "blocks": ["best_rational_signed", "encode_loe_content"],
             "statement": "No registered framing/assembly primitives: "
                          "tuple-pack (pair) and byte-slice/int-parse. "
                          "SELECT is NOT in this family — solved "
                          "in-schema (magnitude idiom)."},
            {"id": "BLK-HIGHER-ORDER",
             "surface": "compose SS2 schema (op field = static name, "
                        "compose.py:398; reference grammar has no @op "
                        "namespace, compose.py:107). dsl surface has "
                        "parallel_body/sub_chain discriminators.",
             "blocks": ["parallel_sector_dispatch", "chiral_dual"],
             "statement": "A descriptor cannot name an op as a VALUE; "
                          "runtime callable injection through @input "
                          "works (measured), so the gap is naming, not "
                          "plumbing."},
            {"id": "BLK-ITER-COMPOSE",
             "surface": "compose SS2 only (ADR-0008 SS11 deferral); the "
                        "dsl surface HAS fold/reduce",
             "blocks": ["net_chirality"],
             "statement": "No fold/reduce on the SS2 chain surface; the "
                          "op is a linear catamorphism and would be "
                          "expressible on the dsl surface (modulo the "
                          "measured positional-vs-kw-only fold-contract "
                          "mismatch with shipped reorient)."},
            {"id": "BLK-N-SCALE-ROUND",
             "surface": "op inventory (Class N)",
             "blocks": ["best_rational_signed"],
             "statement": "scale_round_half_even (int(round(mag * "
                          "fine_scale)), banker's rounding) is described "
                          "in prose but registered nowhere."},
        ],
        leaf_population=["chiral_flip", "pin_slot_at_zero", "reorient"],
        pass_population=["cyclic_gcd", "schur_complement", "cyclic_mod_add",
                         "cyclic_mod_mul", "cyclic_mod_pow",
                         "cyclic_mod_inv", "cyclic_mod_mul_wide"],
    )


if __name__ == "__main__":
    main()
