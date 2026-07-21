"""rc295 (§102 / F1265) — RE-MEASUREMENT of the shipped non-collapsing read, on
the NATIVE path.

Task ``#929`` (commit f5cceb635, harness ``task929_klein4_joint_vs_marginal.py``)
established that reading the already-shipped ``1 + 2*D`` accumulator SOFTLY
recovers most of what F1263 attributed to a 4xD joint count table — but it ran
**pure-Python** (``HAS_NATIVE=False`` in WSL2) and it scored an AD HOC table
built inside the measurement script. rc295 turned that table into a shipped op,
``hdc.klein4_bundle_sector_scores``. This re-runs the same protocol against the
SHIPPED op with the native library loaded.

Two things are therefore checked here that ``#929`` could not check:

1. **The shipped op IS the measured quantity.** Stage 1 rebuilds ``#929``'s ad
   hoc ``m3_marginal_prod`` table from the accumulator and asserts the shipped
   op reproduces it element-for-element. Without that, "rc295 delivers the #929
   lift" would be an assumption.
2. **Native and pure agree.** Both projections are computed and compared, so a
   number measured on one path is a number on the other.

**Honest scope of "on the native path".** The store construction
(``klein4_expand`` / ``klein4_bind`` / ``klein4_bundle_accumulate``) and the read
itself (``klein4_bundle_sector_scores``) dispatch to C. The recall@1 scoring
loop is Python in both runs — it is the measurement harness, not a shipped op.
So the native path changes how the store is BUILT and READ, not how it is
SCORED, and the recall numbers are expected to match ``#929`` exactly rather
than to improve. Matching IS the result: it shows the C peer is bit-faithful.

**Report per dimension, never one scalar.** F1264 (PR #687) and ``#929``'s own
D=1024 sweep both show these numbers are dimension-specific. Both dimensions run
here and both are reported.

Arms (all reduce to the same shape — a per-coordinate 4-entry integer table T
scored ``sum_i T[i][key[i] ^ cand[i]]`` — so they cost the same and differ only
in how T is filled):

  m1_bundle_hard      T[i][s] = 1 if s == resolve(acc)[i] else 0   SHIPPED (baseline)
  m2_sector_scores    T[i][s] = klein4_bundle_sector_scores(acc)   SHIPPED (rc295, NEW)
  m3_joint_hard       T[i][s] = 1 if s == argmax(C[i]) else 0      AD HOC
  m4_joint_soft       T[i][s] = C[i][s]                            AD HOC (F1263 treatment)

m3/m4 stay ad hoc because whether the 4xD joint deserves to be a shipped op is
the question rc295 defers, not the question it answers. They are here to price
what is LEFT after the read change, which is the only honest way to scope it.

Discipline: stdlib only — no numpy / math / fractions. Integer arithmetic
throughout; every arm ranks on integers, no division, no float. No ``abs()``
(every quantity is a non-negative count, so no sign boundary arises; one would
be Class-K pin-slot composed with Class-C).

Run:  python3 rc295_klein4_sector_scores_native.py --probes 400
"""

import argparse
import json
import sys
import time
from operator import add

from srmech.amsc import _native, hdc

METHODS = ("m1_bundle_hard", "m2_sector_scores", "m3_joint_hard", "m4_joint_soft")


def emit(rec):
    """One NDJSON record per line (project discipline: NDJSON, never indented)."""
    sys.stdout.write(json.dumps(rec, sort_keys=True) + "\n")
    sys.stdout.flush()


def isqrt_int(v):
    """Integer square root by Newton iteration — ``math`` is banned."""
    if v <= 0:
        return 0
    x = 1 << ((v.bit_length() + 1) // 2)
    while True:
        y = (x + v // x) // 2
        if y >= x:
            return x
        x = y


def wilson_pm(hits, n):
    """Half-width of a ~95% normal-approximation interval on hits/n, in units of
    1/10000 (integer) — so a ratio of two tiny recalls cannot masquerade as a
    precise number."""
    if n == 0:
        return 0
    p4 = (hits * 10000) // n
    var = p4 * (10000 - p4) // n
    return (196 * isqrt_int(var)) // 100


# ------------------------------------------------------- the per-coordinate tables

def build_joint(vecs, dim):
    """AD HOC 4xD joint count matrix — F1263's ``superpose_counts``. Not shipped."""
    c = [[0, 0, 0, 0] for _ in range(dim)]
    for v in vecs:
        for i, s in enumerate(v):
            c[i][s] += 1
    return c


def table_bundle_hard(bundle, dim):
    return [[1 if s == bundle[i] else 0 for s in range(4)] for i in range(dim)]


def table_sector_scores(acc, dim):
    """The SHIPPED rc295 op, reshaped to the common per-coordinate table."""
    flat = hdc.klein4_bundle_sector_scores(acc)
    return [list(flat[4 * i:4 * i + 4]) for i in range(dim)]


def table_929_marginal_prod(acc, dim):
    """#929's AD HOC ``m3_marginal_prod``, rebuilt here verbatim so the shipped
    op can be checked against the thing that was actually measured."""
    n = acc[0]
    out = []
    for i in range(dim):
        c0 = acc[1 + i]
        c1 = acc[1 + dim + i]
        out.append([
            (c0 if (s & 1) else n - c0) * (c1 if ((s >> 1) & 1) else n - c1)
            for s in range(4)
        ])
    return out


def argmax_sector(counts):
    best_sym, best_val = 0, counts[0]
    for s in (1, 2, 3):
        if counts[s] > best_val:
            best_val, best_sym = counts[s], s
    return best_sym


def table_joint_hard(cmat, dim):
    return [[1 if s == argmax_sector(cmat[i]) else 0 for s in range(4)]
            for i in range(dim)]


def table_joint_soft(cmat, dim):
    return [list(cmat[i]) for i in range(dim)]


# ---------------------------------------------------------------------- scoring

def recall_at_1(table, keys, cols, probe_idx, n_cands, dim):
    """Score every candidate against ``table`` for each probed key; count argmax
    hits. ``cols[i]`` is the transposed candidate matrix so the inner
    accumulation runs at C level through ``map``."""
    hits = 0
    for j in probe_idx:
        key = keys[j]
        scores = [0] * n_cands
        for i in range(dim):
            ti = table[i]
            k = key[i]
            ui = (ti[k], ti[k ^ 1], ti[k ^ 2], ti[k ^ 3])
            scores = list(map(add, scores, map(ui.__getitem__, cols[i])))
        best_j, best_s = 0, scores[0]
        for jj in range(1, n_cands):
            if scores[jj] > best_s:
                best_s, best_j = scores[jj], jj
        if best_j == j:
            hits += 1
    return hits


# ------------------------------------- stage 1: the shipped op IS what #929 measured

def stage1_verify(dim_small=64, n_small=9):
    vecs = [hdc.klein4_expand(dim_small, seed=777_000 + i) for i in range(n_small)]
    acc = None
    for v in vecs:
        acc = hdc.klein4_bundle_accumulate(acc, v)

    shipped = hdc.klein4_bundle_sector_scores(acc)
    adhoc_929 = table_929_marginal_prod(acc, dim_small)
    flat_929 = [adhoc_929[i][s] for i in range(dim_small) for s in range(4)]

    # Both projections of the shipped op.
    saved = _native.HAS_NATIVE
    _native.HAS_NATIVE = False
    pure = hdc.klein4_bundle_sector_scores(acc)
    _native.HAS_NATIVE = saved

    # Collapsing the soft read must give the shipped hard read back.
    resolved = list(hdc.klein4_bundle_resolve(acc))
    argmax_of_soft = []
    for i in range(dim_small):
        best_s, best_v = 0, shipped[4 * i]
        for s in (1, 2, 3):
            if shipped[4 * i + s] > best_v:
                best_v, best_s = shipped[4 * i + s], s
        argmax_of_soft.append(best_s)

    emit({
        "record": "stage1_shipped_op_is_the_measured_quantity",
        "dim": dim_small,
        "n_folded": n_small,
        "shipped_len": len(shipped),
        "shipped_len_expected_4D": 4 * dim_small,
        "shipped_typecode": shipped.typecode,
        "shipped_equals_929_marginal_prod": list(shipped) == flat_929,
        "native_equals_pure": list(shipped) == list(pure),
        "argmax_of_soft_equals_resolve": argmax_of_soft == resolved,
        "note": (
            "If shipped_equals_929_marginal_prod is false, rc295 did not ship "
            "the arm #929 measured and every lift number below is misattributed. "
            "argmax_of_soft_equals_resolve pins that the soft read REFINES the "
            "hard read rather than replacing it with a different quantity."
        ),
    })
    return (list(shipped) == flat_929 and list(shipped) == list(pure)
            and argmax_of_soft == resolved)


# ------------------------------------------------------------------------- main

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dims", type=str, default="1024,4096")
    ap.add_argument("--probes", type=int, default=400)
    ap.add_argument("--loads", type=str, default="64,256,512,1200")
    args = ap.parse_args()

    dims = [int(x) for x in args.dims.split(",")]
    loads = [int(x) for x in args.loads.split(",")]

    import srmech

    emit({
        "record": "run_header",
        "task": "#932",
        "rc": "rc295",
        "ships": "srmech.amsc.hdc.klein4_bundle_sector_scores (§102 / F1265)",
        "re_measures": "task #929 (commit f5cceb635), which ran pure-Python",
        "srmech_version": srmech.__version__,
        "srmech_has_native": _native.HAS_NATIVE,
        "native_abi": _native.NATIVE_ABI_VERSION,
        "native_symbol_present": bool(
            _native.HAS_NATIVE
            and hasattr(_native.LIB, "srmech_klein4_bundle_sector_scores")),
        "python": sys.version.split()[0],
        "dims": dims,
        "loads": loads,
        "probes_per_load": args.probes,
        "metric": "recall@1 over all N stored values, key-bound probe (F1263 protocol)",
        "key_seed_base": 10000,
        "value_seed_base": 20000,
        "scoring_loop_is_python_on_both_paths": True,
        "note": (
            "The store build and the READ dispatch to C; the recall@1 scoring "
            "loop is harness Python on both paths. So these recalls are expected "
            "to MATCH #929's pure-path numbers, not to beat them — matching is "
            "the result, because it shows the C peer is bit-faithful."
        ),
    })

    if not _native.HAS_NATIVE:
        emit({"record": "ABORT", "reason": "HAS_NATIVE is False — this run must "
              "exercise the native path; a pure run would not re-measure anything "
              "#929 had not already measured."})
        return 2

    ok = stage1_verify()
    if not ok:
        emit({"record": "ABORT", "reason": "stage 1 failed — the shipped op is "
              "not the quantity #929 measured; lift numbers would be misattributed."})
        return 2

    for dim in dims:
        max_n = max(loads)
        keys = [hdc.klein4_expand(dim, seed=10_000 + i) for i in range(max_n)]
        vals = [hdc.klein4_expand(dim, seed=20_000 + i) for i in range(max_n)]

        # Storage, measured from the real objects rather than asserted.
        probe_acc = None
        for v in [hdc.klein4_bind(keys[i], vals[i]) for i in range(8)]:
            probe_acc = hdc.klein4_bundle_accumulate(probe_acc, v)
        scores_obj = hdc.klein4_bundle_sector_scores(probe_acc)
        emit({
            "record": "storage_cost",
            "dim": dim,
            "bundle_bytes": dim,
            "shipped_accumulator_bytes": len(probe_acc) * probe_acc.itemsize,
            "adhoc_joint_bytes": 4 * dim * probe_acc.itemsize,
            "sector_scores_READ_bytes": len(scores_obj) * scores_obj.itemsize,
            "note": (
                "sector_scores is a TRANSIENT read, derived from the "
                "(1 + 2*D) accumulator on demand — it is not a stored "
                "structure and no existing store is rebuilt to get it. The "
                "joint, by contrast, is a STORAGE change."
            ),
        })

        for n in loads:
            t0 = time.time()
            bound = [hdc.klein4_bind(keys[i], vals[i]) for i in range(n)]
            acc = None
            for v in bound:
                acc = hdc.klein4_bundle_accumulate(acc, v)
            bundle = hdc.klein4_bundle_resolve(acc)
            cmat = build_joint(bound, dim)

            tables = {
                "m1_bundle_hard": table_bundle_hard(bundle, dim),
                "m2_sector_scores": table_sector_scores(acc, dim),
                "m3_joint_hard": table_joint_hard(cmat, dim),
                "m4_joint_soft": table_joint_soft(cmat, dim),
            }

            cands = vals[:n]
            cols = [bytes(cands[j][i] for j in range(n)) for i in range(dim)]
            step = max(1, n // args.probes)
            probe_idx = list(range(0, n, step))[:args.probes]

            rec = {"record": "load_result", "dim": dim, "load": n,
                   "n_probes": len(probe_idx)}
            for m in METHODS:
                h = recall_at_1(tables[m], keys, cols, probe_idx, n, dim)
                rec["hits_" + m] = h
                rec["recall_" + m] = round(h / len(probe_idx), 4)
                rec["recall_pm_1e4_" + m] = wilson_pm(h, len(probe_idx))

            base = rec["hits_m1_bundle_hard"]
            for m in METHODS:
                rec["lift_vs_bundle_" + m] = (
                    None if base == 0 else round(rec["hits_" + m] / base, 3))

            gain_joint = rec["hits_m4_joint_soft"] - base
            gain_soft = rec["hits_m2_sector_scores"] - base
            rec["gain_joint_over_bundle"] = gain_joint
            rec["gain_sector_scores_over_bundle"] = gain_soft
            rec["fraction_of_joint_gain_captured_by_shipped_read"] = (
                None if gain_joint <= 0 else round(gain_soft / gain_joint, 4))
            rec["joint_hard_worse_than_shipped_soft"] = (
                rec["hits_m3_joint_hard"] < rec["hits_m2_sector_scores"])
            rec["elapsed_s"] = round(time.time() - t0, 1)
            emit(rec)

    emit({"record": "run_footer", "stage1_ok": ok,
          "note": "per-dimension results above; never quote a single scalar lift"})
    return 0


if __name__ == "__main__":
    sys.exit(main())
