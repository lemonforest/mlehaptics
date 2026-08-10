"""SPIKE `#T1114` rung 4 — RESIDUAL CENSUS: classify all 41
srmech/signal_processing/closed_form_ops modules + the 20 cascade-catalog
descriptors by RECURSION SCHEME, and count what a general indexed map does
NOT close.

Scheme vocabulary (Bird-Meertens + the kernel's own five):
  apply            plain composition / delegation (incl. Class-L solves)
  bounded-iterate  loop_n-shaped repetition (descriptor- or parameter-count)
  map-elementwise  out[k] = f(x[k])
  map-indexed      out[k] = f(k, whole_input) over runtime n  (THE WIDENING)
  bounded-map      the existing <=4 Klein-4 fan-out
  fold / reduce    catamorphisms (with / without seed)
  scan             out[k] depends on out[k-1] / carried state (incl. REVERSE)
  unfold           consume-until-done / variable-advance production
  d&c              divide-and-conquer (radix-2 FFT) — cost-only here
  higher-order     an op-valued parameter (BLK-HIGHER-ORDER, rung 3)

Classification basis: the module's own pure-path source (read + line-cited);
the ``while_count`` per module is MEASURED from source here, and the table's
expectation is asserted against it, so a drifted classification fails loud.

Every classification row carries ``closed_after_indexed_map`` — the census
question the rung exists to answer.

Run (WSL2, numpy-absent):
    cd docs/srmech/python
    PYTHONPATH=$PWD python3 ../notes/_t1114_rung4_scheme_census_rc419.py \
        > ../notes/t1114_rung4_scheme_census_rc419_20260809.ndjson
"""

from __future__ import annotations

import importlib
import json
import os
import sys

import srmech  # noqa: E402

WORKTREE_TAG = "agent-a0102bc09c1e5c5a5"
RUNG3_NDJSON = (
    "/mnt/d/GitHub/mlehaptics/docs/srmech/notes/"
    "t1114_rung3_census_all20_rc419_20260809.ndjson")


def emit(**kw):
    kw.setdefault("spike", "T1114")
    kw.setdefault("rung", 4)
    kw.setdefault("srmech_version", srmech.__version__)
    print(json.dumps(kw, sort_keys=True))


# ── the 41-module table ──────────────────────────────────────────────────
# (module, schemes, closed_after_indexed_map, expected_while_count, reason)
MODULES = [
    ("allpass", ["scan"], False, 0,
     "Delegates the IIR difference equation (local _lfilter_df1: "
     "acc -= a[k]*out[i-k], out[i] read back) — carried output state."),
    ("arithmetic_coding", ["fold", "scan"], False, 0,
     "ENCODE is a FOLD: acc=(lo,hi) rational interval narrowed once per "
     "symbol (lines 176-186), fixed-size output — NOT unfold (brief "
     "prediction corrected).  DECODE is a SCAN over range(length): (lo,hi) "
     "state + one emitted symbol per step + inner cum-table argfind "
     "(lines 138-158).  Fold half closes now (needs pair-accumulator "
     "framing); decode needs scan."),
    ("beamforming_fixed", ["map-indexed", "fold"], True, 0,
     "Delay-aligned gather D[i][m] = sig[m][d[m]+i] (line 93) is an indexed "
     "map with dynamic element access; then weighted matvec (map.fold)."),
    ("cross_spectral", ["map-indexed", "fold", "apply"], True, 0,
     "Welch frames: outer indexed map over frames (start = i*hop gather), "
     "windowed inner map, FFT delegate, per-bin conjugate-product map, "
     "frame-average FOLD (acc[k] += ..., lines 144-150)."),
    ("dct", ["map-indexed", "fold"], True, 0,
     "Cosine-matrix build = nested indexed map over (k, j) (lines 56-63); "
     "transform = matvec (map.fold); 2-D = maps over rows then cols."),
    ("esprit", ["apply", "map-indexed"], True, 0,
     "Class-L mat_hermitian_eigendecompose (registered, L) + sorted "
     "subspace gather maps + LS solve — apply-composition + indexed maps."),
    ("farrow", ["bounded-map", "map-indexed"], True, 0,
     "Static 4-tap Lagrange h_eff (bounded map, lines 102-105) + "
     "correlate delegate (Toeplitz indexed map.fold)."),
    ("fft", ["apply"], True, 0,
     "Delegates _fc.fft -> c-dispatched srmech_fft_c128 / pure "
     "spectral_cascades: radix-2 D&C recursion for 2^k N, direct O(n^2) "
     "DFT otherwise (spectral_cascades.py:91-93 nested indexed map).  As "
     "a LEAF: apply.  Decomposed: indexed map suffices for VALUE; d&c is "
     "COST-only."),
    ("fir", ["apply"], True, 0,
     "Delegates _dsp.convolve — the Toeplitz indexed map.fold "
     "(_dsp_cascades.py:136-138)."),
    ("fsk", ["map-indexed", "reduce"], True, 0,
     "Mod: nested indexed map (symbol x sample phase ramp).  Demod: "
     "indexed map over symbol frames + bounded map over M tones + "
     "argmax reduce (lines 126-141)."),
    ("hdc_truncation", ["apply", "scan"], False, 0,
     "M.bundle (registered) then the popcount TRUNCATION pass: the "
     "``kept`` counter threads sequentially across bits (lines 71-78) — "
     "a prefix-count SCAN (map + prefix-sum shape)."),
    ("heat_kernel", ["apply", "map-indexed", "fold"], True, 0,
     "Class-L eigendecompose + spectral project/scale/reconstruct sums "
     "(lines 83-88) — apply + indexed maps + folds."),
    ("huffman", ["unfold", "scan", "map-elementwise"], False, 1,
     "Tree build: priority-queue merge ``while len(heap) > 1`` (line 49) "
     "— an anamorphism over a shrinking heap, FUEL-BOUNDED (each step "
     "pops 2, pushes 1: |alphabet|-1 steps).  Encode emit: elementwise "
     "map + concat.  Decode: SCAN over bits with buf state + variable "
     "emission (lines 132-136)."),
    ("ica_jade", ["bounded-iterate", "apply", "map-indexed"], True, 0,
     "max_iter Jacobi sweeps (``for _it in range(max_iter)``, line 111 — "
     "PARAMETER-count bounded iterate) + Class-L eigendecompose + nested "
     "indexed maps (cumulant tensor, lines 222-229).  Note: defines a "
     "LOCAL ``_abs`` helper (line 53) rather than composing the Class-K "
     "atoms — a cascade-honesty observation, not a scheme gap."),
    ("ifft", ["apply"], True, 0, "Delegates _fc.ifft — as fft."),
    ("iir", ["scan"], False, 0,
     "DF2T: state z carries y history (lines 70-78); module docstring "
     "itself: 'inherently SEQUENTIAL and does NOT decompose into a "
     "matmul / FFT'."),
    ("jpeg", ["map-indexed", "apply"], True, 0,
     "Nested indexed map over the (bh x bw) block grid (lines 266-281 / "
     "229-244) with static 8x8 DCT matmuls per block."),
    ("lmmse", ["apply", "map-indexed"], True, 0,
     "Class-L mat_solve gain + gather/combine maps (lines 93-98)."),
    ("lz77", ["unfold", "scan"], False, 2,
     "ENCODE: ``while i < n`` with DATA-DEPENDENT advance i += "
     "best_length+1 (line 114) — consume-until-done, FUEL-BOUNDED (i "
     "strictly increases on a finite input; the inner match-extension "
     "while at line 122 is bounded by the lookahead).  DECODE: token scan "
     "whose output SELF-REFERENCES (out.append(out[start+i]), lines "
     "100-101) — history-carrying scan."),
    ("map_ml", ["apply", "map-indexed"], True, 0,
     "Class-L mat_solve x2 + mat_matmul + combine maps."),
    ("matched_filter", ["apply"], True, 0,
     "Delegates _dsp.correlate — Toeplitz indexed map.fold."),
    ("mimo_svd", ["apply"], True, 0, "Class-L mat_svd, plus row gathers."),
    ("mlse", ["scan"], False, 0,
     "Viterbi-over-ISI-trellis: forward DP (state metrics from t-1) + "
     "REVERSE traceback; memory==0 branch is map+argmin.  Sequential "
     "state both directions."),
    ("multirate", ["map-indexed", "apply"], True, 0,
     "Zero-insert upsample map (line 127), windowed-sinc tap build map, "
     "convolve delegate, strided decimate map."),
    ("multitaper", ["map-indexed", "fold"], True, 0,
     "Nested indexed map (taper x bin, lines 112-122) + spectrum-average "
     "fold."),
    ("music", ["apply", "map-indexed", "fold"], True, 0,
     "Class-L eigendecompose + noise-subspace gather + projection matmul "
     "+ per-steering-vector map with inner fold (lines 109-114)."),
    ("ofdm", ["map-indexed", "apply"], True, 0,
     "Indexed map over symbols (lines 89-113): per-symbol FFT delegate + "
     "cyclic-prefix gather map + serialize concat (framing leaf)."),
    ("pi_cascade", ["apply"], True, 0,
     "Delegates rational.pi_cascade_digits (internally a parameter-"
     "bounded doubling cascade — bounded-iterate at the leaf layer)."),
    ("polyphase", ["map-indexed", "apply"], True, 0,
     "Runtime-L component split (line 69), per-component convolve "
     "delegate, strided interleave/accumulate maps (lines 126-146)."),
    ("psk_qam", ["map-elementwise", "reduce"], True, 0,
     "Mod: elementwise constellation map.  Demod: elementwise map + "
     "bounded map over constellation + argmin reduce (lines 140-149)."),
    ("rfft", ["apply"], True, 0, "Delegates _fc.rfft — as fft."),
    ("rle", ["unfold", "map-elementwise"], False, 2,
     "ENCODE: ``while i < n`` with run-length advance i += count (line "
     "88; inner run-extension while at line 91 bounded by max_run and n) "
     "— FUEL-BOUNDED consume.  DECODE: per-token expansion (map + "
     "flatten/concat — stateless concatMap, closes with map + a flatten "
     "framing leaf)."),
    ("sign_quantise", ["map-elementwise"], True, 0,
     "Pure elementwise threshold map (lines 86-97) — already closable by "
     "an ELEMENTWISE map; the indexed map subsumes it."),
    ("sinc_interp", ["map-indexed", "apply"], True, 0,
     "Kernel build S[q][s] = sinc((t_q - t_s)/T) — nested indexed map — "
     "then mat_matvec (registered L).  The median gap estimate (line 120) "
     "needs an order-statistic/sort leaf (inventory, not a scheme)."),
    ("spectral_subtraction", ["apply", "map-elementwise"], True, 0,
     "fft delegate + per-bin floor/subtract map (lines 98-111) + ifft."),
    ("spectrogram", ["apply", "map-elementwise"], True, 0,
     "stft delegate + nested elementwise |z|^2 map (lines 61-71) — the "
     "brief's 'nested map' prediction CONFIRMED, and it closes."),
    ("stft", ["map-indexed", "apply"], True, 0,
     "Outer indexed map over frames (start = i*hop gather, lines "
     "127-130) + windowed inner map + per-frame FFT delegate — nested "
     "indexed map, CONFIRMED, closes."),
    ("vector_quantisation", ["map-elementwise", "reduce"], True, 0,
     "Per-row map + bounded map over codebook + argmin reduce (lines "
     "127-138)."),
    ("viterbi", ["scan"], False, 0,
     "Forward DP delta[t] <- delta[t-1] (lines 125-135) + REVERSE "
     "traceback path[t] <- path[t+1] (lines 136-138) — the brief's scan "
     "prediction CONFIRMED, including the reverse pass."),
    ("wavelet", ["bounded-iterate", "map-indexed", "apply"], True, 0,
     "``for _ in range(levels)`` (line 89 — parameter-count iterate) of "
     "banded-matrix build map + mat_matvec + even/odd split maps; "
     "per-level length halves (shrinking value, fixed iteration count)."),
    ("wiener", ["apply", "map-elementwise"], True, 0,
     "fft delegate + per-bin PSD gain map (lines 83-95) + ifft."),
]

# ── the 20 cascade-catalog descriptors ───────────────────────────────────
# (name, schemes, closed_after_indexed_map, note)
DESCRIPTORS = [
    ("cyclic_gcd", ["apply"], True, "rung-3 PASS (delegation)"),
    ("cyclic_mod_add", ["apply"], True, "rung-3 PASS"),
    ("cyclic_mod_mul", ["apply"], True, "rung-3 PASS"),
    ("cyclic_mod_pow", ["apply"], True, "rung-3 PASS"),
    ("cyclic_mod_inv", ["apply"], True, "rung-3 PASS"),
    ("cyclic_mod_mul_wide", ["apply"], True, "rung-3 PASS"),
    ("schur_complement", ["apply"], True, "rung-3 PASS"),
    ("chiral_flip", ["apply"], True,
     "LEAF atom; ALSO one indexed-map body (measured: dsl_map_demo)"),
    ("pin_slot_at_zero", ["apply"], True, "LEAF atom"),
    ("reorient", ["apply"], True, "LEAF atom"),
    ("magnitude", ["apply"], True,
     "2-step apply chain (rung-3: idiom bit-identical; BLK-REGMAP only)"),
    ("best_rational_signed", ["apply"], True,
     "5-step apply chain; the continued-fraction loop lives INSIDE the "
     "registered Class-N leaf (the exile-to-op-instance pattern working); "
     "BLK-REGMAP + BLK-N-SCALE-ROUND + BLK-FRAMING remain (inventory)"),
    ("encode_loe_content", ["apply"], True,
     "4-step apply chain; BLK-REGMAP + BLK-FRAMING remain (inventory)"),
    ("net_chirality", ["reduce"], True,
     "Linear catamorphism — the EXISTING dsl fold/reduce form; only "
     "BLK-ITER-COMPOSE (compose-surface port) + the positional-vs-kw-only "
     "fold-contract wrinkle remain"),
    ("chiral_dual", ["higher-order", "apply"], False,
     "op-valued parameter — BLK-HIGHER-ORDER; NOT closed by indexed map"),
    ("parallel_sector_dispatch", ["higher-order", "bounded-map"], False,
     "op-valued body + Klein-4 fan-out — BLK-HIGHER-ORDER; NOT closed by "
     "indexed map"),
    ("quaternion_dft", ["map-indexed", "fold"], True,
     "MEASURED closed this rung: 12/12 bit-identical"),
    ("octonion_dft", ["map-indexed", "fold"], True,
     "MEASURED closed this rung: 10/10 bit-identical"),
    ("kuramoto_step", ["map-indexed", "fold"], True,
     "MEASURED closed this rung: 7/7 simple + 4/4 general bit-identical; "
     "the simple/general dispatch itself is a wrapper-layer branch (two "
     "chains)"),
    ("autocorrelation", ["map-indexed", "fold"], True,
     "MEASURED closed this rung: 9/9 bit-identical (compensated Sigma "
     "delegated as a leaf — a pair-accumulator fold, BLK-FRAMING)"),
]


def main():
    assert srmech.__file__ and WORKTREE_TAG in srmech.__file__, srmech.__file__
    assert srmech.__version__ == "0.9.0rc419", srmech.__version__

    pkg = "srmech.signal_processing.closed_form_ops"
    base = importlib.import_module(pkg)
    op_dir = os.path.dirname(os.path.abspath(base.__file__))
    on_disk = sorted(f[:-3] for f in os.listdir(op_dir)
                     if f.endswith(".py") and f != "__init__.py")
    table_names = sorted(m[0] for m in MODULES)
    emit(stage="module_inventory", n_on_disk=len(on_disk),
         n_in_table=len(table_names),
         disk_equals_table=(on_disk == table_names),
         missing_from_table=sorted(set(on_disk) - set(table_names)),
         extra_in_table=sorted(set(table_names) - set(on_disk)))
    assert on_disk == table_names, "table drifted from disk"

    scheme_counts: dict = {}
    n_closed = 0
    for name, schemes, closed, exp_while, reason in MODULES:
        mod = importlib.import_module(pkg + "." + name)
        assert callable(getattr(mod, "op", None)), name
        with open(mod.__file__, "r", encoding="utf-8") as fh:
            src = fh.read()
        wc = src.count("while ")
        assert wc == exp_while, (name, wc, exp_while)
        for s in schemes:
            scheme_counts[s] = scheme_counts.get(s, 0) + 1
        n_closed += bool(closed)
        emit(stage="module_row", module=name, schemes=schemes,
             closed_after_indexed_map=bool(closed),
             while_count_measured=wc, reason=reason)

    d_closed = 0
    for name, schemes, closed, note in DESCRIPTORS:
        d_closed += bool(closed)
        emit(stage="descriptor_row", descriptor=name, schemes=schemes,
             closed_after_indexed_map=bool(closed), note=note)

    # cross-check descriptor set against the catalog dir
    cat_dir = os.path.join(os.path.dirname(os.path.abspath(base.__file__)),
                           "..", "..", "cascade", "catalogs",
                           "cascade_catalog")
    cat_names = sorted(f[:-5] for f in os.listdir(os.path.abspath(cat_dir))
                       if f.endswith(".toml"))
    emit(stage="descriptor_inventory",
         catalog_equals_table=(cat_names == sorted(d[0] for d in DESCRIPTORS)),
         n_catalog=len(cat_names))
    assert cat_names == sorted(d[0] for d in DESCRIPTORS)

    # optional mechanical cross-check against the rung-3 census statuses
    rung3 = {"available": os.path.exists(RUNG3_NDJSON)}
    if rung3["available"]:
        blocked_by_iter = None
        with open(RUNG3_NDJSON, "r", encoding="utf-8") as fh:
            for line in fh:
                rec = json.loads(line)
                if rec.get("stage") == "blocker_catalogue":
                    for b in rec["catalogue"]:
                        if b["id"] == "BLK-ITER-INDEXED":
                            blocked_by_iter = sorted(b["blocks"])
        rung3["blk_iter_indexed_blocks"] = blocked_by_iter
        rung3["matches_measured_four"] = (blocked_by_iter == sorted(
            ["octonion_dft", "quaternion_dft", "kuramoto_step",
             "autocorrelation"]))
    emit(stage="rung3_crosscheck", **rung3)

    # ── the aggregation the rung exists for ──────────────────────────
    scan_ops = [m for m, s, c, _w, _r in MODULES if not c and "scan" in s]
    scan_only = [m for m, s, c, _w, _r in MODULES
                 if not c and "scan" in s and "unfold" not in s]
    unfold_ops = [m for m, s, c, _w, _r in MODULES if not c and "unfold" in s]
    hi_order = [d for d, s, c, _n in DESCRIPTORS if not c]
    emit(
        stage="residual",
        modules_total=len(MODULES),
        modules_closed_after_indexed_map=n_closed,
        modules_not_closed=len(MODULES) - n_closed,
        scheme_frequency=scheme_counts,
        still_missing={
            "scan": {
                "ops": sorted(scan_ops),
                "scan_only": sorted(scan_only),
                "n": len(scan_ops),
                "statement": (
                    "out[k] depends on carried state / out[k-1] (iir, "
                    "allpass, mlse+viterbi forward DP AND reverse "
                    "traceback, hdc_truncation prefix-count, "
                    "arithmetic_coding decode, huffman decode, lz77 "
                    "decode).  scan = mapAccumL: n steps over a runtime "
                    "input with threaded state — SAME totality class as "
                    "fold; a totality-preserving widening."),
            },
            "unfold": {
                "ops": sorted(unfold_ops),
                "n": len(unfold_ops),
                "statement": (
                    "consume-until-done producers (lz77/rle encode, "
                    "huffman tree build).  MEASURED SOFTENING: every "
                    "while in all 41 modules (5 total: rle 2, lz77 2, "
                    "huffman 1) is structurally FUEL-BOUNDED — the index "
                    "strictly advances on a finite input / the heap "
                    "strictly shrinks.  A fuel-bounded consume form "
                    "(structural-progress obligation) would stay total; "
                    "the closure's true exile class — predicate-only "
                    "unbounded while — is EMPTY in the shipped corpus."),
            },
            "higher-order": {
                "ops": hi_order,
                "n": len(hi_order),
                "statement": (
                    "op-valued parameters (chiral_dual, "
                    "parallel_sector_dispatch) — BLK-HIGHER-ORDER, a "
                    "NAMING gap (rung 3: runtime callable injection "
                    "works), orthogonal to iteration schemes."),
            },
            "d&c": {
                "ops": [], "n": 0,
                "statement": (
                    "radix-2 FFT is the only D&C in the corpus and the "
                    "direct O(n^2) DFT (already an indexed map) is "
                    "value-identical — D&C is COST-only, never required "
                    "for declarability."),
            },
        },
        inventory_not_scheme=(
            "concat/flatten (rle decode, huffman emit, ofdm serialize, "
            "polyphase interleave), pair/argreduce accumulators (argmin/"
            "argmax, Neumaier (sum,comp)), sort/order-statistic "
            "(sinc_interp median, esprit/music eigenvalue ordering) — all "
            "pointwise/finite LEAVES (BLK-FRAMING family), not recursion "
            "schemes."),
        verdict_shape=(
            "CLOSES_PARTIALLY: indexed map closes 4/4 blocked descriptors "
            "(measured bit-identical) and 32/41 closed_form_ops modules "
            "at the scheme level; the residual is TWO more schemes — scan "
            "(8 ops) and fuel-bounded unfold (3 ops, overlapping huffman/"
            "lz77 with scan) — plus the orthogonal higher-order naming "
            "gap (2 descriptors).  Phase 2 is THREE widenings, not one; "
            "all three can preserve total-by-construction."),
    )


if __name__ == "__main__":
    main()
