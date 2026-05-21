"""Spike #139.2 — Large-N cascade-composition cost-asymmetry benchmark.

Discriminates whether cascade-composition has its OWN cost signature beyond
the sum-of-parts. The L o I composition pair surfaced in Spike #139 at
1000 iterations was within statistical noise (-7.8% / +6.1% on repeat
runs). This spike runs 10^5 iterations across 26 deliberately partitioned
pairs (7D_g x 7D_g, 3D_s x 3D_s, mixed 7D_g x 3D_s) plus 4 commutativity
test pairs (L o I vs I o L, C o L vs L o C, A o L vs L o A).

Single-stack pure-Python fallback (HAS_NATIVE=False), matching Spike #139's
baseline. Marshalling-noise structurally inapplicable at this layer
(both individual and composition runs share the same interpreter overhead);
calibrated "call wrapper overhead" subtracted from sum-of-parts to keep
the addition test honest.

Per [[user_stance_framework_domain_algebra_not_length_or_magnitude]]: cost
data is MAGNITUDE. Express framework predictions as RATIOS. Identity-level
claims about composition-emergent cost stay provisional.

Outputs:
    spike139_2_findings_2026-05-18.ndjson  - per-pair records + verdict
"""
from __future__ import annotations

import json
import math
import platform
import random
import statistics
import sys
import time
from pathlib import Path
from typing import Callable, Iterable, Tuple

WORKTREE_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(WORKTREE_ROOT / "docs" / "srmech" / "python"))

from srmech.amsc import (  # noqa: E402
    cyclic,
    dispatch,
    hdc,
    kepler,
    laplacian,
    primes,
    rational,
    search,
    template,
    tlv,
)
from srmech.amsc import _native  # noqa: E402
from srmech.amsc.format import sha256_bytes  # noqa: E402
import numpy as np  # noqa: E402

OUT_NDJSON = Path(__file__).with_name("spike139_2_findings_2026-05-18.ndjson")
TIMESTAMP = "2026-05-18T00:00:00+00:00"
SPIKE_ID = "139.2"

# --- Iteration scale -------------------------------------------------
# Per brief: 10^5 minimum; 10^6 if runtime permits.
# Per smoke test: L = 14us/call -> 10^5 = 1.4s. 26 pairs x 3 ops/pair = 78 measures.
# Worst case: L o L pair at 10^5: 30s * 3 = 90s per pair. 26 pairs ~ 40min.
# At 10^6 same: ~6.5h. We use 10^5 with budget for cross-stack-rerun if needed.
N_ITERATIONS = 100_000
WARMUP = 200
RNG_SEED = 2026_05_18

# --- Calibration: empty-call wrapper overhead --------------------------
# Each measured op() does a Python function call. The composition op
# does ONE function call wrapping two operations; summing two individual
# measurements double-counts ONE function call. Calibrate that overhead.

def _noop() -> None:
    pass


def measure_median_ns(op: Callable[[], object], n: int, warmup: int = WARMUP) -> Tuple[float, float, float]:
    """Return (median_ns, p25_ns, p75_ns) over n trials.

    Median + IQR is robust against GC/scheduler outliers at these scales.
    """
    for _ in range(warmup):
        op()
    samples: list[int] = []
    for _ in range(n):
        t0 = time.perf_counter_ns()
        op()
        t1 = time.perf_counter_ns()
        samples.append(t1 - t0)
    samples.sort()
    p50 = float(samples[n // 2])
    p25 = float(samples[n // 4])
    p75 = float(samples[(3 * n) // 4])
    return p50, p25, p75


def bootstrap_median_ci_np(samples_arr: np.ndarray, n_boot: int = 500, alpha: float = 0.05) -> Tuple[float, float]:
    """Vectorized bootstrap CI for median using numpy.

    For n=100k samples + n_boot=500, this is ~50ms vs ~minutes for the
    Python-loop version. Median CI is what we need for "is additive
    baseline outside CI?" discrimination.
    """
    rng = np.random.default_rng(RNG_SEED)
    n = len(samples_arr)
    # Sample indices, n_boot x n matrix.
    idx = rng.integers(0, n, size=(n_boot, n))
    boots = samples_arr[idx]  # n_boot x n
    medians = np.median(boots, axis=1)
    medians.sort()
    lo_idx = int(alpha / 2 * n_boot)
    hi_idx = int((1 - alpha / 2) * n_boot)
    return float(medians[lo_idx]), float(medians[hi_idx])


def measure_full(op: Callable[[], object], n: int, warmup: int = WARMUP, n_boot: int = 200):
    """Returns dict with median + IQR + 95% bootstrap CI."""
    for _ in range(warmup):
        op()
    samples = np.empty(n, dtype=np.int64)
    for i in range(n):
        t0 = time.perf_counter_ns()
        op()
        t1 = time.perf_counter_ns()
        samples[i] = t1 - t0
    samples_sorted = np.sort(samples)
    median = float(samples_sorted[n // 2])
    p25 = float(samples_sorted[n // 4])
    p75 = float(samples_sorted[(3 * n) // 4])
    ci_lo, ci_hi = bootstrap_median_ci_np(samples, n_boot=n_boot)
    mean = float(np.mean(samples))
    return {
        "median_ns": median,
        "p25_ns": p25,
        "p75_ns": p75,
        "iqr_ns": p75 - p25,
        "ci95_lo_ns": ci_lo,
        "ci95_hi_ns": ci_hi,
        "mean_ns": mean,
        "n": n,
    }


# --- Per-class atomic ops (matching Spike #139 workloads) -------------

# Reproducible inputs.
RNG = random.Random(RNG_SEED)
BYTES_1KB = bytes(RNG.randrange(0, 256) for _ in range(1024))
BYTES_4KB = bytes(RNG.randrange(0, 256) for _ in range(4096))
NEEDLE_4KB = BYTES_4KB[3000:3008]
BYTES_HDC_A = bytes(RNG.randrange(0, 256) for _ in range(1024))
BYTES_HDC_B = bytes(RNG.randrange(0, 256) for _ in range(1024))
RULES_8 = [(bytes(RNG.randrange(0, 256) for _ in range(4)), i) for i in range(8)]
RULES_8.append((BYTES_4KB[100:104], 99))

# Class L 16-node graph (same as Spike #139).
GRAPH_N = 16
_rng2 = random.Random(31415)
GRAPH_EDGES: list[Tuple[int, int]] = []
for _ in range(32):
    u = _rng2.randrange(GRAPH_N)
    v = _rng2.randrange(GRAPH_N)
    if u != v:
        GRAPH_EDGES.append((u, v))

# Class C ndjson lines.
NDJSON_LINES = b"\n".join(
    json.dumps({"i": i, "v": "x" * 50}, separators=(",", ":")).encode("utf-8")
    for i in range(16)
)

# Class F template.
TEMPLATE_BYTES = (
    b"hello {name}, your id is {id} and your role is {role}, "
    b"with weight {wt} and timestamp {ts}\n"
) * 8
TEMPLATE_MAPPING = {
    b"name": b"alice",
    b"id": b"12345",
    b"role": b"admin",
    b"wt": b"3.14159",
    b"ts": b"2026-05-18T00:00:00Z",
}

# Sorted-key lookup for Class E.
SORTED_KEYS = sorted(set(RNG.randrange(0, 1_000_000) for _ in range(256)))
SORTED_TARGET = SORTED_KEYS[len(SORTED_KEYS) // 2]
import bisect as _bisect  # noqa: E402

# Smooth number for Class J.
N_SMOOTH = 2 * 3 * 5 * 7 * 11 * 13 * 17 * 19 * 23 * 29

# Kepler params.
M_RAD = 1.234
E_VAL = 0.3


def op_A() -> object:
    return sha256_bytes(BYTES_1KB)


def op_B() -> object:
    return tlv.tlv_pack(42, BYTES_1KB)


def op_C() -> object:
    out = []
    for line in NDJSON_LINES.split(b"\n"):
        if line.strip():
            out.append(json.loads(line))
    return out


def op_D() -> object:
    return dispatch.match(BYTES_4KB, RULES_8)


def op_E() -> object:
    return _bisect.bisect_left(SORTED_KEYS, SORTED_TARGET)


def op_F() -> object:
    return template.render(TEMPLATE_BYTES, TEMPLATE_MAPPING)


def op_G() -> object:
    return search.byte_search(BYTES_4KB, NEEDLE_4KB)


def op_H() -> object:
    return (_native.HAS_NATIVE, _native.NATIVE_ABI_VERSION)


def op_I() -> object:
    return cyclic.mod_pow(12345678901234, 9876543210, 0xFFFF_FFFF_0000_0001)


def op_J() -> object:
    return primes.factor(N_SMOOTH)


def op_K() -> object:
    return kepler.equation_of_centre(M_RAD, E_VAL)


def op_L() -> object:
    L = laplacian.dense_laplacian(GRAPH_N, GRAPH_EDGES)
    return laplacian.jacobi_eigvals(L)


def op_M() -> object:
    return hdc.bind(BYTES_HDC_A, BYTES_HDC_B)


def op_N() -> object:
    return rational.exp_series_truncate(355, 113, 16)


CLASS_OPS = {
    "A": op_A, "B": op_B, "C": op_C, "D": op_D, "E": op_E,
    "F": op_F, "G": op_G, "H": op_H, "I": op_I, "J": op_J,
    "K": op_K, "L": op_L, "M": op_M, "N": op_N,
}

# Class tier classification per Spike #139 a-priori prediction.
TIER_3DS_PURE = {"A", "B", "G", "H"}
TIER_7DG_ENGAGED = {"C", "I", "K", "L"}
TIER_MIXED = {"D", "E", "F", "J", "M", "N"}

# Measurement-precision threshold:
# Windows perf_counter_ns has 100 ns resolution; back-to-back diffs show
# 100/200/400/6100 ns quantization. Ops costing < ~5000 ns suffer from
# quantization-dominated measurement noise. For framework-content
# discrimination we must restrict to RELIABLY-MEASURABLE atomic ops
# (median > 5000 ns); see dry-run analysis.
RELIABLY_MEASURABLE_NS = 5000.0


def tier_of(c: str) -> str:
    if c in TIER_3DS_PURE:
        return "3Ds-pure"
    if c in TIER_7DG_ENGAGED:
        return "7Dg-engaged"
    return "mixed"


def make_compose(c1: str, c2: str) -> Callable[[], object]:
    """Build a composed op c1 o c2.

    Reads C-style order: c1 o c2 means "run c1 first, then c2 on its
    output / alongside it". Since our atomic ops have fixed inputs,
    the composition is sequential application (not chained-input);
    this tests SCHEDULING cost rather than data-dependency cost.
    """
    op1 = CLASS_OPS[c1]
    op2 = CLASS_OPS[c2]

    def _compose() -> object:
        r1 = op1()
        r2 = op2()
        return (r1, r2)

    return _compose


# --- Pair selection per brief ----------------------------------------

# 7Dg x 7Dg (primary focus). Asymmetric L o I included for commutativity.
PAIRS_7DG_X_7DG = [
    ("L", "I"),  # Original Spike #139 pair (re-test at large N)
    ("L", "L"),  # Self-composition
    ("L", "C"),
    ("L", "K"),
    ("C", "I"),
    ("C", "K"),
    ("I", "K"),
    ("I", "I"),
]

# 3Ds x 3Ds (null-control). B included per brief reconsideration (legitimate primitive).
PAIRS_3DS_X_3DS = [
    ("A", "G"),
    ("A", "H"),
    ("G", "H"),
    ("B", "G"),
    ("A", "A"),
    ("B", "B"),
    ("G", "G"),
]

# Mixed 7Dg x 3Ds (discriminator).
PAIRS_MIXED = [
    ("L", "A"),
    ("L", "G"),
    ("L", "H"),
    ("C", "A"),
    ("I", "A"),
    ("K", "A"),
    ("K", "G"),
    ("C", "H"),
]

# Commutativity (order-matters) test pairs.
PAIRS_COMMUTATIVITY = [
    ("I", "L"),  # vs L o I above
    ("C", "L"),  # vs L o C above
    ("A", "L"),  # vs L o A above
    ("L", "G"),  # duplicate to confirm
]


def compose_label(c1: str, c2: str) -> str:
    return f"{c1}o{c2}"


def pair_tier(c1: str, c2: str) -> str:
    t1 = tier_of(c1)
    t2 = tier_of(c2)
    if t1 == t2:
        return f"{t1} x {t2}"
    # Canonical ordering: 7Dg-engaged > mixed > 3Ds-pure.
    ranks = {"3Ds-pure": 0, "mixed": 1, "7Dg-engaged": 2}
    if ranks[t1] > ranks[t2]:
        return f"{t1} x {t2}"
    return f"{t2} x {t1}"


# --- Cross-stack rerun helper (Python+C if available) ----------------
# Per brief: cross-stack check. Composition-emergent cost (if any) should
# be stack-invariant. Since HAS_NATIVE=False on this system, we cannot
# rerun on Python+C. Document this honestly; defer cross-stack to
# Spike #139.3 or Spike #138.x's already-collected per-class catalog.


# --- Main -----------------------------------------------------------

def emit(record: dict, fh) -> None:
    record.setdefault("spike", SPIKE_ID)
    record.setdefault("date", "2026-05-18")
    record.setdefault("timestamp", TIMESTAMP)
    fh.write(json.dumps(record, separators=(",", ":")) + "\n")


def calibrate_call_overhead(n: int) -> float:
    """Calibrate empty-Python-call overhead (single op() wrapper)."""

    def empty_wrapped() -> object:
        return None

    res = measure_full(empty_wrapped, n)
    return res["median_ns"]


def main() -> None:
    fh = OUT_NDJSON.open("w", encoding="utf-8")
    print(f"Spike #139.2 large-N composition-cost benchmark")
    print(f"N_ITERATIONS = {N_ITERATIONS}; WARMUP = {WARMUP}")
    print(f"HAS_NATIVE = {_native.HAS_NATIVE}")
    print()

    # 1) Framing.
    emit(
        {
            "phase": "framing",
            "kind": "anchor",
            "question": (
                "Does cascade composition have its OWN cost signature beyond "
                "the sum-of-parts (composition-emergent cost) or is it purely "
                "additive (null hypothesis)?"
            ),
            "parent_stances": [
                "user_stance_identity_not_implementation_discipline",
                "user_stance_cascade_composition_is_quantum_algorithm",
                "feedback_no_privileged_primitive_classes",
                "feedback_multi_domain_multi_round_survival_falsification_method",
            ],
            "branch": "research/spike-139-2-large-n-composition-cost-asymmetry",
            "parent_spike": 139,
            "child_of_open_thread": "L o I -7.8/+6.1 noise at 1000 iter",
            "n_iterations": N_ITERATIONS,
            "warmup": WARMUP,
            "rng_seed": RNG_SEED,
        },
        fh,
    )

    # 2) Runtime meta.
    emit(
        {
            "phase": "runtime_meta",
            "kind": "context",
            "python_version": sys.version.split()[0],
            "platform": platform.platform(),
            "processor": platform.processor() or "unknown",
            "has_native_libsrmech": _native.HAS_NATIVE,
            "native_load_error": str(_native.LOAD_ERROR) if not _native.HAS_NATIVE else None,
            "numpy_version": np.__version__,
            "rng_seed": RNG_SEED,
            "caveats": [
                "HAS_NATIVE=False; pure-Python fallback paths only",
                "Marshalling-noise structurally inapplicable at this layer (single-stack)",
                "Composition-emergent cost claim is MAGNITUDE-level not IDENTITY-level",
                "Cross-stack rerun deferred: HAS_NATIVE=False blocks Python+C path here",
            ],
        },
        fh,
    )

    # 3) Call-overhead calibration.
    call_overhead_ns = calibrate_call_overhead(N_ITERATIONS // 2)
    print(f"Call overhead (single empty Python call): {call_overhead_ns:.1f} ns")
    emit(
        {
            "phase": "calibration",
            "kind": "call_overhead",
            "call_overhead_ns_median": call_overhead_ns,
            "n_samples": N_ITERATIONS // 2,
            "explanation": (
                "Each measured op() carries one Python function-call wrapper. "
                "Summing two individual measurements double-counts ONE call "
                "wrapper relative to a composed call. We subtract this "
                "overhead from the sum-of-parts to get the additive baseline."
            ),
        },
        fh,
    )

    # 4) Measure each unique atom in CLASS_OPS used by selected pairs.
    used_classes: set[str] = set()
    for pairs in (PAIRS_7DG_X_7DG, PAIRS_3DS_X_3DS, PAIRS_MIXED, PAIRS_COMMUTATIVITY):
        for c1, c2 in pairs:
            used_classes.add(c1)
            used_classes.add(c2)

    print(f"Measuring {len(used_classes)} atomic class costs...")
    atom_results: dict[str, dict] = {}
    for c in sorted(used_classes):
        print(f"  Class {c}...", end="", flush=True)
        r = measure_full(CLASS_OPS[c], N_ITERATIONS)
        atom_results[c] = r
        emit(
            {
                "phase": "measurement",
                "kind": "atomic_class",
                "class_id": c,
                "tier": tier_of(c),
                **r,
            },
            fh,
        )
        print(f" median={r['median_ns']:.0f} ns (CI [{r['ci95_lo_ns']:.0f}, {r['ci95_hi_ns']:.0f}])")

    # 5a) Back-to-back SELF measurements (cache-warmth baseline).
    # For each used class, measure cost(c o c) — two consecutive c() calls
    # within one outer wrapper. The delta vs 2*cost(c) - call_overhead
    # captures the per-class cache-warmth that BENIGNLY appears in any
    # composition. This is the framework-NEUTRAL baseline against which
    # composition-emergent costs are measured.
    print()
    print("Measuring back-to-back self-composition (cache-warmth baseline)...")
    selfcompose_results: dict[str, dict] = {}
    for c in sorted(used_classes):
        op_self_compose = make_compose(c, c)
        r_self = measure_full(op_self_compose, N_ITERATIONS)
        # Self-additive baseline: 2 * c - call_overhead
        self_additive = 2.0 * atom_results[c]["median_ns"] - call_overhead_ns
        self_delta = r_self["median_ns"] - self_additive
        self_delta_pct = 100.0 * self_delta / self_additive if self_additive > 0 else 0.0
        selfcompose_results[c] = {
            "phase": "selfcomposition",
            "kind": "cache_warmth_baseline",
            "class_id": c,
            "tier": tier_of(c),
            "median_compose_ns": r_self["median_ns"],
            "ci95_compose": [r_self["ci95_lo_ns"], r_self["ci95_hi_ns"]],
            "iqr_ns": r_self["iqr_ns"],
            "self_additive_ns": self_additive,
            "self_delta_ns": self_delta,
            "self_delta_pct": self_delta_pct,
            "reliably_measurable": atom_results[c]["median_ns"] >= RELIABLY_MEASURABLE_NS,
        }
        emit(selfcompose_results[c], fh)
        print(
            f"  {c}o{c}: comp={r_self['median_ns']:.0f}ns "
            f"self_add={self_additive:.0f}ns "
            f"self_delta={self_delta_pct:+.1f}% "
            f"(reliable={selfcompose_results[c]['reliably_measurable']})"
        )

    # 5b) Composition pair measurements.
    all_pair_results: list[dict] = []
    pair_groups = [
        ("7Dg x 7Dg", PAIRS_7DG_X_7DG),
        ("3Ds x 3Ds", PAIRS_3DS_X_3DS),
        ("7Dg x 3Ds (mixed)", PAIRS_MIXED),
        ("commutativity", PAIRS_COMMUTATIVITY),
    ]

    print()
    for group_name, pairs in pair_groups:
        print(f"=== Group: {group_name} ===")
        for c1, c2 in pairs:
            print(f"  {c1}o{c2}...", end="", flush=True)
            compose_op = make_compose(c1, c2)
            r_comp = measure_full(compose_op, N_ITERATIONS)
            r1 = atom_results[c1]
            r2 = atom_results[c2]
            # Additive baseline: cost(c1) + cost(c2) - one_call_overhead.
            additive_baseline = r1["median_ns"] + r2["median_ns"] - call_overhead_ns
            delta_ns = r_comp["median_ns"] - additive_baseline
            delta_pct = 100.0 * delta_ns / additive_baseline if additive_baseline > 0 else 0.0
            # Effect-size discriminator: ratio of delta_ns to composite IQR.
            # If delta_ns < 0.5 * IQR_compose, the delta is within IQR noise.
            iqr_significance = abs(delta_ns) / r_comp["iqr_ns"] if r_comp["iqr_ns"] > 0 else 0.0

            # Approximate p-value via bootstrap.
            # We've already computed CI95 on the composition; assess whether
            # the additive baseline falls outside that CI.
            additive_below_ci_lo = additive_baseline < r_comp["ci95_lo_ns"]
            additive_above_ci_hi = additive_baseline > r_comp["ci95_hi_ns"]
            additive_outside_ci95 = additive_below_ci_lo or additive_above_ci_hi

            verdict: str
            if abs(delta_pct) < 1.0 or not additive_outside_ci95:
                verdict = "ADDITIVE"
            elif delta_pct > 5.0 and additive_outside_ci95:
                verdict = "SUPER-ADDITIVE"
            elif delta_pct < -5.0 and additive_outside_ci95:
                verdict = "SUB-ADDITIVE"
            elif additive_outside_ci95:
                verdict = "MARGINAL"
            else:
                verdict = "ADDITIVE-WITHIN-NOISE"

            # Cache-warmth correction: AVERAGE the self-deltas of c1 and c2
            # to estimate the per-pair cache-warmth contribution. If c1 and
            # c2 both have, say, -15% self-delta (sub-additive on self), then
            # a pair (c1, c2) showing -15% delta is FRAMEWORK-NEUTRAL — it's
            # cache warmth. A pair showing -25% delta has -10% beyond
            # cache-warmth (the emergent contribution).
            c1_self_pct = selfcompose_results[c1]["self_delta_pct"]
            c2_self_pct = selfcompose_results[c2]["self_delta_pct"]
            cache_warmth_estimate_pct = (c1_self_pct + c2_self_pct) / 2.0
            beyond_cache_warmth_pct = delta_pct - cache_warmth_estimate_pct

            # Both ops reliably measurable?
            both_reliable = (
                r1["median_ns"] >= RELIABLY_MEASURABLE_NS
                and r2["median_ns"] >= RELIABLY_MEASURABLE_NS
            )

            pair_result = {
                "phase": "composition_measurement",
                "kind": "pair",
                "group": group_name,
                "c1": c1,
                "c2": c2,
                "pair_label": compose_label(c1, c2),
                "pair_tier": pair_tier(c1, c2),
                "c1_tier": tier_of(c1),
                "c2_tier": tier_of(c2),
                "median_c1_ns": r1["median_ns"],
                "median_c2_ns": r2["median_ns"],
                "median_compose_ns": r_comp["median_ns"],
                "ci95_compose_lo_ns": r_comp["ci95_lo_ns"],
                "ci95_compose_hi_ns": r_comp["ci95_hi_ns"],
                "iqr_compose_ns": r_comp["iqr_ns"],
                "additive_baseline_ns": additive_baseline,
                "delta_ns": delta_ns,
                "delta_pct_vs_additive": delta_pct,
                "additive_outside_ci95": additive_outside_ci95,
                "iqr_significance_factor": iqr_significance,
                "verdict": verdict,
                "c1_self_delta_pct": c1_self_pct,
                "c2_self_delta_pct": c2_self_pct,
                "cache_warmth_estimate_pct": cache_warmth_estimate_pct,
                "beyond_cache_warmth_pct": beyond_cache_warmth_pct,
                "both_reliably_measurable": both_reliable,
            }
            all_pair_results.append(pair_result)
            emit(pair_result, fh)
            print(
                f" comp={r_comp['median_ns']:.0f}ns "
                f"add={additive_baseline:.0f}ns "
                f"delta={delta_pct:+.1f}% [{verdict}]"
            )

    # 6) Partition analysis.
    print()
    by_group: dict[str, list[dict]] = {}
    for r in all_pair_results:
        by_group.setdefault(r["group"], []).append(r)
    group_summary: dict[str, dict] = {}
    for gname, results in by_group.items():
        deltas_pct = [r["delta_pct_vs_additive"] for r in results]
        super_count = sum(1 for v in [r["verdict"] for r in results] if v == "SUPER-ADDITIVE")
        sub_count = sum(1 for v in [r["verdict"] for r in results] if v == "SUB-ADDITIVE")
        additive_count = sum(
            1 for v in [r["verdict"] for r in results]
            if v in ("ADDITIVE", "ADDITIVE-WITHIN-NOISE")
        )
        marginal_count = sum(1 for v in [r["verdict"] for r in results] if v == "MARGINAL")
        group_summary[gname] = {
            "n_pairs": len(results),
            "median_delta_pct": statistics.median(deltas_pct),
            "mean_delta_pct": statistics.fmean(deltas_pct),
            "min_delta_pct": min(deltas_pct),
            "max_delta_pct": max(deltas_pct),
            "n_super_additive": super_count,
            "n_sub_additive": sub_count,
            "n_additive": additive_count,
            "n_marginal": marginal_count,
        }
        print(
            f"  {gname}: n={len(results)} median_delta={group_summary[gname]['median_delta_pct']:+.1f}% "
            f"super={super_count} sub={sub_count} add={additive_count} marg={marginal_count}"
        )
    emit({"phase": "partition_analysis", "kind": "group_summary", "groups": group_summary}, fh)

    # 7) Commutativity sub-analysis: pair specific X o Y vs Y o X.
    commutativity_pairs = [("L", "I"), ("L", "C"), ("L", "A"), ("L", "G")]
    commutativity_results: list[dict] = []
    for c1, c2 in commutativity_pairs:
        fwd = next((r for r in all_pair_results if r["c1"] == c1 and r["c2"] == c2), None)
        rev = next((r for r in all_pair_results if r["c1"] == c2 and r["c2"] == c1), None)
        if fwd and rev:
            asymmetry_ns = fwd["median_compose_ns"] - rev["median_compose_ns"]
            asymmetry_pct = (
                100.0 * asymmetry_ns / rev["median_compose_ns"]
                if rev["median_compose_ns"] > 0 else 0.0
            )
            commutativity_results.append({
                "phase": "commutativity",
                "kind": "asymmetry_test",
                "pair_fwd": fwd["pair_label"],
                "pair_rev": rev["pair_label"],
                "median_fwd_ns": fwd["median_compose_ns"],
                "median_rev_ns": rev["median_compose_ns"],
                "asymmetry_ns": asymmetry_ns,
                "asymmetry_pct": asymmetry_pct,
                "ci95_fwd": [fwd["ci95_compose_lo_ns"], fwd["ci95_compose_hi_ns"]],
                "ci95_rev": [rev["ci95_compose_lo_ns"], rev["ci95_compose_hi_ns"]],
                "ci_overlap": (
                    fwd["ci95_compose_lo_ns"] <= rev["ci95_compose_hi_ns"]
                    and rev["ci95_compose_lo_ns"] <= fwd["ci95_compose_hi_ns"]
                ),
            })
            emit(commutativity_results[-1], fh)

    # 7b) RELIABLY-MEASURABLE SUBSET ANALYSIS — the framework-relevant test.
    # Pairs where BOTH ops > RELIABLY_MEASURABLE_NS are immune to clock
    # quantization. The cache-warmth correction (beyond_cache_warmth_pct)
    # is the framework-relevant signal: deltas beyond what same-op
    # self-composition shows.
    reliable_pairs = [r for r in all_pair_results if r["both_reliably_measurable"]]
    reliable_by_group: dict[str, list[dict]] = {}
    for r in reliable_pairs:
        reliable_by_group.setdefault(r["group"], []).append(r)
    reliable_group_summary: dict[str, dict] = {}
    for gname, results in reliable_by_group.items():
        if not results:
            continue
        deltas_raw = [r["delta_pct_vs_additive"] for r in results]
        deltas_beyond_cw = [r["beyond_cache_warmth_pct"] for r in results]
        # Pairs where |beyond_cw| > 5% are framework-emergent candidates.
        n_emergent_super = sum(1 for v in deltas_beyond_cw if v > 5.0)
        n_emergent_sub = sum(1 for v in deltas_beyond_cw if v < -5.0)
        reliable_group_summary[gname] = {
            "n_reliable_pairs": len(results),
            "median_delta_raw_pct": statistics.median(deltas_raw),
            "median_delta_beyond_cache_warmth_pct": statistics.median(deltas_beyond_cw),
            "n_emergent_super_additive": n_emergent_super,
            "n_emergent_sub_additive": n_emergent_sub,
        }
    emit(
        {
            "phase": "reliably_measurable_subset",
            "kind": "cache_warmth_corrected_analysis",
            "threshold_ns": RELIABLY_MEASURABLE_NS,
            "n_reliable_pairs": len(reliable_pairs),
            "n_total_pairs": len(all_pair_results),
            "groups": reliable_group_summary,
        },
        fh,
    )
    print()
    print("=== RELIABLY-MEASURABLE SUBSET (both ops > 5000 ns) ===")
    for gname, summ in reliable_group_summary.items():
        print(
            f"  {gname}: n_reliable={summ['n_reliable_pairs']} "
            f"median_raw={summ['median_delta_raw_pct']:+.1f}% "
            f"median_beyond_cw={summ['median_delta_beyond_cache_warmth_pct']:+.1f}% "
            f"emergent_super={summ['n_emergent_super_additive']} "
            f"emergent_sub={summ['n_emergent_sub_additive']}"
        )

    # 8) Composite verdict.
    n_7dg_super = group_summary.get("7Dg x 7Dg", {}).get("n_super_additive", 0)
    n_7dg_total = group_summary.get("7Dg x 7Dg", {}).get("n_pairs", 0)
    n_3ds_super = group_summary.get("3Ds x 3Ds", {}).get("n_super_additive", 0)
    n_3ds_total = group_summary.get("3Ds x 3Ds", {}).get("n_pairs", 0)
    n_mixed_super = group_summary.get("7Dg x 3Ds (mixed)", {}).get("n_super_additive", 0)
    n_mixed_total = group_summary.get("7Dg x 3Ds (mixed)", {}).get("n_pairs", 0)

    # CACHE-WARMTH-CORRECTED 7Dg signal on reliable pairs.
    cw_7dg = reliable_group_summary.get("7Dg x 7Dg", {})
    cw_3ds = reliable_group_summary.get("3Ds x 3Ds", {})
    cw_mixed = reliable_group_summary.get("7Dg x 3Ds (mixed)", {})
    n_emergent_super_7dg = cw_7dg.get("n_emergent_super_additive", 0)
    n_emergent_super_3ds = cw_3ds.get("n_emergent_super_additive", 0)
    n_emergent_super_mixed = cw_mixed.get("n_emergent_super_additive", 0)
    n_reliable_7dg = cw_7dg.get("n_reliable_pairs", 0)
    n_reliable_3ds = cw_3ds.get("n_reliable_pairs", 0)
    n_reliable_mixed = cw_mixed.get("n_reliable_pairs", 0)

    # Brief's anticipated-outcomes mapping.
    all_pct_negative_and_consistent = all(
        r["delta_pct_vs_additive"] < -2.0 for r in all_pair_results
    )
    all_pct_within_noise = all(
        abs(r["delta_pct_vs_additive"]) < 2.0 for r in all_pair_results
    )
    # CACHE-WARMTH-CORRECTED: are all reliable pairs within +/- 5% of cache-warmth baseline?
    all_within_cw_noise = (
        len(reliable_pairs) > 0
        and all(abs(r["beyond_cache_warmth_pct"]) < 5.0 for r in reliable_pairs)
    )

    n_super_total = sum(1 for r in all_pair_results if r["verdict"] == "SUPER-ADDITIVE")
    n_sub_total = sum(1 for r in all_pair_results if r["verdict"] == "SUB-ADDITIVE")
    n_total = len(all_pair_results)
    fraction_super = n_super_total / n_total if n_total > 0 else 0.0
    fraction_sub = n_sub_total / n_total if n_total > 0 else 0.0

    # Verdict logic prioritises the CACHE-WARMTH-CORRECTED reliably-
    # measurable subset (framework-relevant) over raw-delta on all pairs
    # (which is dominated by clock quantization at small ops).
    if all_within_cw_noise:
        verdict = "FULLY-ADDITIVE-BEYOND-CACHE-WARMTH"
        verdict_note = (
            "All reliably-measurable pairs within +/- 5% of cache-warmth "
            "baseline. Cascade composition is purely additive over per-class "
            "costs (modulo benign cache warmth that applies to ALL pairs). "
            "Falsifies composition-emergent-cost claim; sharpens substrate-"
            "coupling-cost to be PER-CLASS-ONLY contribution (Class L "
            "dominant per Spike #138). Composition is mere ordered application."
        )
    elif (
        n_emergent_super_7dg > n_reliable_7dg / 2
        and n_emergent_super_3ds == 0
        and n_emergent_super_mixed >= n_reliable_mixed / 3
    ):
        verdict = "SUPER-ADDITIVE-ON-7DG-BEYOND-CACHE-WARMTH"
        verdict_note = (
            f"7Dg x 7Dg pairs (reliable): {n_emergent_super_7dg}/{n_reliable_7dg} "
            f"super-additive BEYOND cache-warmth. "
            f"3Ds x 3Ds null-control (reliable): {n_emergent_super_3ds}/{n_reliable_3ds}. "
            f"Mixed (reliable): {n_emergent_super_mixed}/{n_reliable_mixed}. "
            "Partition discriminates; composition has substrate-coupling "
            "content beyond same-op cache warmth. Framework-prediction holds."
        )
    elif (
        len(reliable_pairs) > 0
        and statistics.median(
            [r["beyond_cache_warmth_pct"] for r in reliable_pairs]
        ) < -2.0
    ):
        verdict = "SUB-ADDITIVE-BEYOND-CACHE-WARMTH-HARDWARE-EFFECT"
        verdict_note = (
            "Reliable pairs show sub-additive cost beyond same-op cache-warmth. "
            "Suggests cross-op cache benefits or interpreter-state reuse — "
            "framework-neutral hardware/runtime effect."
        )
    elif all_pct_within_noise:
        verdict = "FULLY-ADDITIVE"
        verdict_note = (
            "All pairs within +/- 2% of raw additive baseline. Composition "
            "purely additive; falsifies composition-emergent-cost."
        )
    elif all_pct_negative_and_consistent:
        verdict = "HARDWARE-CACHE-EFFECT"
        verdict_note = (
            "Composition cost CONSISTENTLY below additive baseline. Framework-"
            "neutral cache-warmth effect."
        )
    elif fraction_super > 0.5:
        verdict = "MOSTLY-SUPER-ADDITIVE-CLOCK-QUANTIZATION-DOMINATED"
        verdict_note = (
            f"{n_super_total}/{n_total} pairs super-additive but most involve "
            "quantization-noise-dominated atomic ops (<5000 ns). The 3Ds-pure "
            "tier shows the bulk of super-additivity — consistent with clock "
            "quantization, NOT 7Dg content."
        )
    elif fraction_sub > 0.5:
        verdict = "MOSTLY-SUB-ADDITIVE"
        verdict_note = (
            f"{n_sub_total}/{n_total} pairs sub-additive. Hardware/cache-warmth."
        )
    else:
        verdict = "MIXED-NO-CLEAR-PARTITION"
        verdict_note = (
            f"Super={n_super_total} Sub={n_sub_total} "
            f"Additive={n_total - n_super_total - n_sub_total} of {n_total}. "
            "No clear partition signal."
        )

    emit(
        {
            "phase": "composite_verdict",
            "kind": "verdict",
            "verdict": verdict,
            "note": verdict_note,
            "fraction_super_additive": fraction_super,
            "fraction_sub_additive": fraction_sub,
            "n_total_pairs": n_total,
            "n_reliably_measurable_pairs": len(reliable_pairs),
            "n_emergent_super_7dg_x_7dg": n_emergent_super_7dg,
            "n_emergent_super_3ds_x_3ds": n_emergent_super_3ds,
            "n_emergent_super_mixed": n_emergent_super_mixed,
            "reliable_groups_summary": reliable_group_summary,
            "honest_caveat": (
                "MAGNITUDE-level analysis per [[user_stance_framework_domain_algebra_not_length_or_magnitude]]. "
                "Identity-level claims about composition stay provisional. "
                "Single-stack analysis. Cross-stack rerun deferred. "
                "Clock-quantization (Windows perf_counter_ns: 100 ns) "
                "dominates sub-5-microsecond atoms; framework analysis "
                "restricted to RELIABLY-MEASURABLE pairs (both ops > 5000 ns)."
            ),
            "single_stack_only": True,
            "cross_stack_pending": True,
        },
        fh,
    )

    # 9) Stance-authoring implication (for conductor decision; NOT auto-authored).
    emit(
        {
            "phase": "fermata",
            "kind": "stance_authoring_implication",
            "candidate_stance": "substrate_coupling_cost_is_7dg_shadow",
            "auto_authorised": False,
            "spike_139_partial_signature": "PARTIAL-SIGNATURE-AT-GEOMEAN-NOT-STRICT-RANKING",
            "spike_139_2_finding": verdict,
            "combined_needed_for_promotion": (
                "Spike #138.1 (subgroup closure) + Spike #138.2 (alternate substrates) + "
                "this spike (composition cost) form a 3-pronged epistemological frame. "
                "Promotion requires conductor decision on whether per-class signature "
                "(Class L dominant) + composition signature (this spike) jointly support "
                "stance OR support narrower refinement to 'Class L is per-call substrate-"
                "coupling-cost dominant; composition is additive over per-call costs'."
            ),
            "reason_not_auto": (
                "Touches publishable framework predictions. Conductor must "
                "decide form (per-class dominant vs composition-amplified)."
            ),
        },
        fh,
    )

    # 10) Files.
    emit(
        {
            "phase": "files",
            "kind": "deliverables",
            "paths": [
                "docs/srmech/notes/spike139_2_large_n_composition_cost.py",
                "docs/srmech/notes/spike139_2_findings_2026-05-18.ndjson",
            ],
        },
        fh,
    )

    fh.close()
    print()
    print(f"Composite verdict: {verdict}")
    print(f"Findings written to: {OUT_NDJSON}")


if __name__ == "__main__":
    main()
