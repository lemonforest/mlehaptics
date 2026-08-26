"""R-RBS-LM-223 — Larger-scale byte-level encode (~100x the R-RBS-LM-25 scale).

Closes the R-RBS-LM-25 §7 open thread "Larger-scale byte-level encode":

    "At 600 obs we mode-collapse. At 50,000 obs (full notebook; multi-threaded
     R-RBS-LM-11 path) the byte-byte transition statistics might be rich enough
     to support varied output. Not tested."  — R-RBS-LM-25 §7

R-RBS-LM-25 capped at ~10k bytes / ~621 obs and both byte-level variants
mode-collapsed to single-byte repetition. R-RBS-LM-19 characterised the ~3.3%
agreement ceiling as a *structural* WTE-projection-fidelity bound that three
architectural levers (scale, D, bundle/attention) did NOT lift. The byte-level
Class-A mint has no WTE clustering at all, so R-RBS-LM-25 fell BELOW the ceiling
to mode collapse.

THE SCALE PREDICTION UNDER TEST (pre-stated, two outcomes):
  (a) NULL (expected): mode-collapse PERSISTS at ~100x scale -> the R-RBS-LM-19
      ~3.3% structural ceiling holds at scale; more byte observations do not
      manufacture the content structure the WTE clustering supplied.
  (b) CRACK: byte-diversity / disambiguation RISES with scale -> the byte-byte
      transition statistics become rich enough to break the single-byte
      fixed point; first crack in the ceiling.

CORPUS: the in-tree srmech research notebook (real, ~700 KB, no external fetch).
Byte-encode it (UTF-8 bytes, stride 8 per R-RBS-LM-11 harvest stride) at a
SCALE SWEEP so the trend (not one point) is visible. Honest obs-count reporting:
if 100x is too heavy we scale to what runs in minutes and report the obs reached.

THREE srmech-native measurements at each scale point:
  1. Storage signature (F172): the byte co-occurrence Class-L Laplacian
     eigenspectrum (256 nodes = MAX_NATIVE_NODES; vocab-independent). Counter
     ONLY feeds dense_laplacian edge WEIGHTS (the discipline-sanctioned use),
     never as the storage proxy. Spectrum via jacobi_eigvals.
  2. Byte-diversity of emitted continuations: run the R-RBS-LM-25 autoregressive
     byte loop (encode_context_bytes -> bind(instrument,ctx) -> argmin-Hamming
     cleanup) on a fixed prompt set; measure distinct-byte ratio + mode-collapse
     (max single-byte run / single-byte-dominant fraction).
  3. Held-out next-byte top-k hit-rate vs random + byte-frequency baselines.

SIGN DISCIPLINE: similarity = 1 - 2*Hamming/D (no abs(); the cleanup is
argmin-Hamming / argmax-similarity, a Class-K pin-slot selection). Hamming via
np.bitwise_count (POPCOUNT). bind/bundle/similarity = srmech.amsc.hdc; vocab =
srmech Class-A mint; Laplacian/eigvals = srmech.amsc.laplacian.

Usage:
    /tmp/verify_srmech_rc22/venv/bin/python3 \\
        R-RBS-LM-223_larger_scale_byte_level_encode_100x.py
"""

import json
import multiprocessing as mp
import os
import sys
import time
from collections import Counter
from pathlib import Path

import numpy as np

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE.parent / "python"))
sys.path.insert(0, str(HERE))

from srmech.amsc import laplacian as L  # noqa: E402  Class L
from rbs_lm_encoder import CONTEXT_WINDOW, D, bind, hierarchical_bundle  # noqa: E402
from rbs_lm_bytes import (  # noqa: E402
    BYTE_VOCAB_SIZE,
    compute_byte_vocab_table,
    encode_context_bytes,
    encode_observation_bytes,
    text_to_bytes,
    vectorised_cleanup_bytes,
)

NOTEBOOK = HERE.parent / "srmech_research_notebook.md"
STRIDE = 8                       # R-RBS-LM-11 harvest stride
OUT_NDJSON = HERE / "R-RBS-LM-223_results.ndjson"
N_WORKERS = min(16, os.cpu_count() or 8)   # R-RBS-LM-11 Opp 2: physical cores

# Scale sweep. R-RBS-LM-25 anchor ~621 obs (stride 16, 10k bytes). Here stride 8.
# bytes_used chosen so the obs-counts land roughly 1x / 10x / 30x / 50x of 621.
# n_obs ~= (bytes_used - CONTEXT_WINDOW) / STRIDE. (The top point can be pushed
# to ~100x = 500_000 bytes / ~62k obs with RBS223_MT=1 on an uncontended box;
# default tops out at a point that completes serially in minutes even under
# CPU contention -- honest obs-count reporting per the task.)
SCALE_BYTES = [
    5_000,     # ~620 obs   (~1x   R-RBS-LM-25 anchor)  -- full instrument point
    50_000,    # ~6.2k obs  (~10x)                       -- full instrument point
]
# Spectrum-only scale points: the F172 co-occurrence Class-L eigenspectrum is
# a property of the byte STREAM (computable in ~0.2s; no encode), so the
# storage-signature TREND is carried to higher scale here without paying the
# per-observation encode cost (which is the only scale-bound cost, ~15 obs/s on
# this contended box). Full-instrument continuation+hit-rate at 30x/50x/100x is
# encode-bound and untested HERE (set RBS223_MT=1 + add to SCALE_BYTES on an
# uncontended box -- the verdict at 1x/10x already establishes the NULL trend).
SPECTRUM_EXTRA_BYTES = [
    150_000,   # ~18.7k obs (~30x)  -- spectrum-only
    250_000,   # ~31k obs   (~50x)  -- spectrum-only
    500_000,   # ~62k obs   (~100x) -- spectrum-only
]

# Held-out tail of the notebook (NOT used for encoding) for the hit-rate test.
HELDOUT_BYTES = 20_000
HELDOUT_PROBE_STRIDE = 53        # subsample held-out positions (coprime-ish, cheap)
TOP_KS = (1, 3, 5, 10)

# Fixed continuation-probe prompts (mix: notebook-register English + the
# R-RBS-LM-25 hallucination-corpus style + non-English surface).
PROBE_PROMPTS = [
    "The storage signature is the ",
    "Seventeen multiplied by twenty-three equals",
    "The President of the United States in 2024 is",
    "def fibonacci(n):",
    "Class L is the graph Laplacian and ",
    "今天天气很好",
]
GEN_BYTES = 48                   # continuation length per probe


def byte_cooccurrence_eigenspectrum(byte_ids):
    """F172 storage signature: the Class-L Laplacian eigenspectrum of the
    adjacent-byte co-occurrence graph over the 256 byte values.

    Counter here is the EDGE-WEIGHT accumulator that feeds dense_laplacian
    (the discipline-sanctioned use, CLAUDE.md REVIEW item) — it is NOT the
    storage proxy. The storage proxy IS the eigenspectrum (Class L), per F172.

    Returns (eigvals_sorted, n_nodes_active, n_edges). The spectrum is
    L2-normalised so it is comparable across scales (vocab-independent).
    """
    # Accumulate undirected adjacent-byte co-occurrence weights.
    w = Counter()
    for a, b in zip(byte_ids, byte_ids[1:]):
        key = (a, b) if a <= b else (b, a)
        w[key] += 1
    edges = list(w.keys())
    weights = [float(w[e]) for e in edges]
    active = sorted({a for a, _ in edges} | {b for _, b in edges})
    # Class L: build the 256-node weighted Laplacian (256 == MAX_NATIVE_NODES).
    lap = L.dense_laplacian(BYTE_VOCAB_SIZE, edges, weights)
    eig = np.asarray(L.jacobi_eigvals(lap), dtype=np.float64)
    eig = np.sort(eig)
    return eig, len(active), len(edges)


def spectrum_features(eig):
    """Vocab-independent storage-signature features from the eigenspectrum.

    Class-K/C sign discipline: spectral 'energy' uses the squared eigenvalues
    (a true magnitude, no abs() of a signed value); a graph Laplacian is PSD so
    eigenvalues are >= 0 to numerical noise anyway. Participation ratio measures
    how SPREAD the spectrum is (1 = one mode dominates -> degenerate/collapsed;
    higher = richer multi-scale structure)."""
    e = eig.copy()
    e[e < 0] = 0.0                              # PSD: clamp numerical -0 (no abs)
    total = float(e.sum())
    if total <= 0:
        return {"lambda_max": 0.0, "lambda_2": 0.0, "spectral_gap": 0.0,
                "participation_ratio": 0.0, "effective_rank": 0.0}
    p = e / total                               # normalised spectral mass
    # inverse participation ratio -> participation ratio (effective # of modes)
    ipr = float((p * p).sum())
    part_ratio = 1.0 / ipr if ipr > 0 else 0.0
    # effective rank (entropy of normalised eigenvalues, exp)
    nz = p[p > 1e-15]
    ent = float(-(nz * np.log(nz)).sum())
    eff_rank = float(np.exp(ent))
    # Fiedler value (smallest nonzero) = connectivity / lambda_2
    pos = e[e > 1e-9]
    lambda_2 = float(pos.min()) if pos.size else 0.0
    lambda_max = float(e.max())
    gap = float(np.sort(e)[1] - np.sort(e)[0]) if e.size > 1 else 0.0
    return {"lambda_max": lambda_max, "lambda_2": lambda_2, "spectral_gap": gap,
            "participation_ratio": part_ratio, "effective_rank": eff_rank}


# --- R-RBS-LM-11 Opp 2: multiprocessing byte-level encode -----------------
# spawn-safe worker; each process lazily rebuilds the 256-row byte vocab table
# once (R-RBS-LM-11 §4.3: spawn, NOT fork, with srmech/native state in parent).
_WORKER_VT = None


def _byte_encode_chunk(chunk):
    """Worker: encode a chunk of (ctx, next_byte) -> list[bytes]. The byte vocab
    table is the SAME deterministic Class-A mint in every process."""
    global _WORKER_VT
    if _WORKER_VT is None:
        _WORKER_VT = compute_byte_vocab_table(D)
    return [encode_observation_bytes(ctx, nxt, _WORKER_VT, D) for ctx, nxt in chunk]


def encode_instrument(byte_ids, vocab_table):
    """Harvest (ctx, next_byte) at STRIDE and bundle -> one instrument vector.
    next_byte = the ACTUAL next byte in the notebook (Variant-A / R-RBS-LM-25).
    Multiprocessing fan-out per R-RBS-LM-11 Opp 2 (spawn pool) so the ~100x
    scale point finishes in minutes, not hours."""
    observations = [
        (byte_ids[i:i + CONTEXT_WINDOW], byte_ids[i + CONTEXT_WINDOW])
        for i in range(0, len(byte_ids) - CONTEXT_WINDOW, STRIDE)
    ]
    t0 = time.time()
    # The C-native bind makes the serial encode ~110 obs/s; the R-RBS-LM-11
    # spawn pool's per-worker srmech-import + vocab-rebuild overhead only pays
    # off above ~50k obs AND on an uncontended box. Default serial (predictable
    # under CPU contention); opt into MT with RBS223_MT=1.
    use_mt = os.environ.get("RBS223_MT") == "1" and len(observations) >= 50_000
    if not use_mt:
        bindings = [encode_observation_bytes(c, n, vocab_table, D)
                    for c, n in observations]
    else:
        chunk_size = max(1, len(observations) // (N_WORKERS * 4))
        chunks = [observations[i:i + chunk_size]
                  for i in range(0, len(observations), chunk_size)]
        ctx = mp.get_context("spawn")
        with ctx.Pool(N_WORKERS) as pool:
            results = pool.map(_byte_encode_chunk, chunks)
        bindings = [v for chunk in results for v in chunk]   # preserves order
    enc_t = time.time() - t0
    instrument = hierarchical_bundle(bindings)
    return instrument, len(observations), enc_t


def continuation_diversity(instrument, vocab_table, prompts):
    """Run the R-RBS-LM-25 autoregressive byte loop on each prompt; measure
    byte-diversity + mode-collapse of the emitted continuations."""
    rows = []
    for prompt in prompts:
        tokens = text_to_bytes(prompt)
        emitted = []
        for _ in range(GEN_BYTES):
            ctx = tokens[-CONTEXT_WINDOW:] if len(tokens) > CONTEXT_WINDOW else tokens
            ctx_vec = encode_context_bytes(ctx, vocab_table, D)
            cand = bind(instrument, ctx_vec)           # extract next-byte
            res = vectorised_cleanup_bytes(cand, vocab_table, D, top_k=1)  # Class K
            nb = res[0][0]
            emitted.append(nb)
            tokens.append(nb)
        cnt = Counter(emitted)                         # diagnostic only, not storage
        distinct = len(cnt)
        top_byte, top_n = cnt.most_common(1)[0]
        # longest single-byte run (mode-collapse signature)
        max_run = run = 1
        for x, y in zip(emitted, emitted[1:]):
            run = run + 1 if x == y else 1
            max_run = max(max_run, run)
        rows.append({
            "prompt": prompt[:32],
            "distinct_bytes": distinct,
            "distinct_ratio": round(distinct / GEN_BYTES, 4),
            "dominant_byte": int(top_byte),
            "dominant_frac": round(top_n / GEN_BYTES, 4),
            "max_single_byte_run": int(max_run),
            "mode_collapsed": bool(max_run >= GEN_BYTES - 2 or top_n / GEN_BYTES >= 0.9),
            "sample": repr(bytes(emitted[:24]).decode("utf-8", "replace")),
        })
    agg_distinct = float(np.mean([r["distinct_ratio"] for r in rows]))
    agg_collapsed = sum(r["mode_collapsed"] for r in rows)
    return rows, agg_distinct, agg_collapsed


def heldout_hitrate(instrument, vocab_table, heldout_bytes):
    """Held-out next-byte top-k hit-rate vs two baselines:
       - uniform random: k / 256
       - byte-frequency: the k most-frequent held-out bytes (strong baseline).
    A real signal must beat BOTH (esp. the frequency baseline; mode-collapse
    is exactly the frequency baseline in disguise)."""
    positions = list(range(CONTEXT_WINDOW,
                           len(heldout_bytes) - 1,
                           HELDOUT_PROBE_STRIDE))
    if not positions:
        return None
    freq = Counter(heldout_bytes)
    by_freq_rank = [b for b, _ in freq.most_common()]
    hits = {k: 0 for k in TOP_KS}
    freq_hits = {k: 0 for k in TOP_KS}
    n = 0
    maxk = max(TOP_KS)
    for pos in positions:
        ctx = heldout_bytes[pos - CONTEXT_WINDOW:pos]
        true_nb = heldout_bytes[pos]
        ctx_vec = encode_context_bytes(ctx, vocab_table, D)
        cand = bind(instrument, ctx_vec)
        topk = vectorised_cleanup_bytes(cand, vocab_table, D, top_k=maxk)
        ranked = [t[0] for t in topk]                  # argmax-similarity order
        for k in TOP_KS:
            if true_nb in ranked[:k]:
                hits[k] += 1
            if true_nb in by_freq_rank[:k]:
                freq_hits[k] += 1
        n += 1
    out = {}
    for k in TOP_KS:
        out[f"top{k}"] = {
            "instrument": round(hits[k] / n, 4),
            "uniform_baseline": round(k / BYTE_VOCAB_SIZE, 4),
            "freq_baseline": round(freq_hits[k] / n, 4),
            "lift_vs_uniform": round((hits[k] / n) / (k / BYTE_VOCAB_SIZE), 3),
            "beats_freq": bool(hits[k] / n > freq_hits[k] / n),
        }
    out["n_probes"] = n
    return out


def main():
    # Line-buffer stdout so progress streams to the redirected log (the monitor
    # tails it) and nothing is lost in a block buffer if the run is interrupted.
    try:
        sys.stdout.reconfigure(line_buffering=True)
    except Exception:
        pass
    print("=== R-RBS-LM-223 larger-scale byte-level encode (~100x R-RBS-LM-25) ===")
    print(f"  corpus: {NOTEBOOK.name}")
    print(f"  D={D}; CONTEXT_WINDOW={CONTEXT_WINDOW}; STRIDE={STRIDE}; V={BYTE_VOCAB_SIZE}")
    mt_on = os.environ.get("RBS223_MT") == "1"
    print(f"  encode: {'R-RBS-LM-11 spawn pool ' + str(N_WORKERS) + ' workers (>=50k obs)' if mt_on else 'serial C-native bind (~110 obs/s; predictable under contention)'}")

    text = NOTEBOOK.read_text()
    all_bytes = text_to_bytes(text)
    print(f"  notebook bytes total: {len(all_bytes):,}")

    # Reserve a held-out TAIL (never encoded) for the hit-rate test.
    heldout = all_bytes[-HELDOUT_BYTES:]
    body = all_bytes[:-HELDOUT_BYTES]
    print(f"  encode body: {len(body):,} bytes; held-out tail: {len(heldout):,} bytes")

    vocab_table = compute_byte_vocab_table(D)
    print(f"  byte vocab table: {vocab_table.shape}; {vocab_table.nbytes/1024:.0f} KB\n")

    records = []
    anchor_obs = None
    for nb_cap in SCALE_BYTES:
        bytes_used = min(nb_cap, len(body))
        seg = body[:bytes_used]
        print(f"--- scale point: {bytes_used:,} bytes ---")

        # (1) storage signature BEFORE encode (it's a property of the byte stream)
        t0 = time.time()
        eig, n_active, n_edges = byte_cooccurrence_eigenspectrum(seg)
        feats = spectrum_features(eig)
        spec_t = time.time() - t0
        print(f"  [F172 spectrum] active_bytes={n_active}/256 edges={n_edges} "
              f"lambda_max={feats['lambda_max']:.3g} eff_rank={feats['effective_rank']:.2f} "
              f"part_ratio={feats['participation_ratio']:.2f}  ({spec_t:.1f}s)")

        # (2) encode the instrument at this scale
        instrument, n_obs, enc_t = encode_instrument(seg, vocab_table)
        if anchor_obs is None:
            anchor_obs = n_obs
        scale_x = round(n_obs / anchor_obs, 1)
        print(f"  [encode] n_obs={n_obs:,} ({scale_x}x anchor) in {enc_t:.1f}s "
              f"({n_obs/max(enc_t,1e-9):.0f}/s)")

        # (3) continuation diversity / mode-collapse
        t0 = time.time()
        cont_rows, agg_distinct, agg_collapsed = continuation_diversity(
            instrument, vocab_table, PROBE_PROMPTS)
        print(f"  [diversity] mean distinct-byte ratio={agg_distinct:.3f}; "
              f"mode-collapsed {agg_collapsed}/{len(PROBE_PROMPTS)} prompts "
              f"({time.time()-t0:.1f}s)")
        for r in cont_rows:
            print(f"      {r['prompt']!r:34s} distinct={r['distinct_bytes']:2d} "
                  f"dom_frac={r['dominant_frac']:.2f} max_run={r['max_single_byte_run']:2d} "
                  f"{'COLLAPSE' if r['mode_collapsed'] else 'varied'} {r['sample']}")

        # (4) held-out next-byte hit-rate vs baselines
        t0 = time.time()
        hr = heldout_hitrate(instrument, vocab_table, heldout)
        print(f"  [held-out hit-rate] ({hr['n_probes']} probes, {time.time()-t0:.1f}s):")
        for k in TOP_KS:
            d = hr[f"top{k}"]
            print(f"      top{k:<2d} instrument={d['instrument']:.4f} "
                  f"freq_base={d['freq_baseline']:.4f} unif_base={d['uniform_baseline']:.4f} "
                  f"lift_vs_unif={d['lift_vs_uniform']}x beats_freq={d['beats_freq']}")

        rec = {
            "partition": "R-RBS-LM-223",
            "bytes_used": bytes_used,
            "n_obs": n_obs,
            "scale_x_vs_anchor": scale_x,
            "stride": STRIDE,
            "D": D,
            "context_window": CONTEXT_WINDOW,
            "vocab_size": BYTE_VOCAB_SIZE,
            "f172_spectrum": {
                "n_active_bytes": n_active,
                "n_edges": n_edges,
                **feats,
                "eig_top12": [round(float(x), 4) for x in eig[-12:]],
            },
            "continuation_diversity": {
                "mean_distinct_ratio": round(agg_distinct, 4),
                "n_mode_collapsed": agg_collapsed,
                "n_prompts": len(PROBE_PROMPTS),
                "per_prompt": cont_rows,
            },
            "heldout_hitrate": hr,
            "encode_seconds": round(enc_t, 2),
        }
        records.append(rec)
        # Incrementally persist each completed scale point (re-write whole file
        # so it stays valid NDJSON even if a later scale point is interrupted).
        with open(OUT_NDJSON, "w") as fh:
            for r in records:
                fh.write(json.dumps(r) + "\n")
        print()

    # Spectrum-only scale points: extend the F172 storage-signature TREND to
    # higher scale (no encode -- spectrum is a property of the byte stream).
    spectrum_extra = []
    for nb_cap in SPECTRUM_EXTRA_BYTES:
        bytes_used = min(nb_cap, len(body))
        if bytes_used <= SCALE_BYTES[-1]:
            continue
        seg = body[:bytes_used]
        approx_obs = (bytes_used - CONTEXT_WINDOW) // STRIDE
        eig, n_active, n_edges = byte_cooccurrence_eigenspectrum(seg)
        feats = spectrum_features(eig)
        print(f"--- spectrum-only: {bytes_used:,} bytes (~{approx_obs:,} obs) ---")
        print(f"  [F172 spectrum] active_bytes={n_active}/256 edges={n_edges} "
              f"lambda_max={feats['lambda_max']:.3g} eff_rank={feats['effective_rank']:.2f} "
              f"part_ratio={feats['participation_ratio']:.2f}")
        spectrum_extra.append({
            "partition": "R-RBS-LM-223_SPECTRUM_ONLY",
            "bytes_used": bytes_used,
            "approx_n_obs": approx_obs,
            "scale_x_vs_anchor": round(approx_obs / records[0]["n_obs"], 1),
            "f172_spectrum": {"n_active_bytes": n_active, "n_edges": n_edges,
                              **feats,
                              "eig_top12": [round(float(x), 4) for x in eig[-12:]]},
        })

    # Verdict: did mode-collapse persist (NULL a) or did diversity rise (crack b)?
    first, last = records[0], records[-1]
    div_trend = last["continuation_diversity"]["mean_distinct_ratio"] - \
        first["continuation_diversity"]["mean_distinct_ratio"]
    collapse_last = last["continuation_diversity"]["n_mode_collapsed"]
    n_prompts = last["continuation_diversity"]["n_prompts"]
    # A real content signal must BEAT the byte-FREQUENCY baseline by a margin
    # exceeding probe noise (binomial SE ~ 1/sqrt(n)), and must NOT be a lone
    # top-1 blip contradicted by deeper k. Mode-collapse IS the frequency
    # baseline in disguise, so within-noise top-1 ties do NOT count as a crack.
    hr = last["heldout_hitrate"]
    n_probes = hr["n_probes"]
    se = (1.0 / n_probes) ** 0.5                       # ~binomial std-error scale
    margin_top1 = hr["top1"]["instrument"] - hr["top1"]["freq_baseline"]
    margin_top5 = hr["top5"]["instrument"] - hr["top5"]["freq_baseline"]
    beats_freq_meaningfully = (margin_top1 > 2 * se) and (margin_top5 > 0)
    lift_top1 = hr["top1"]["lift_vs_uniform"]
    diversity_rose = div_trend > 0.10 and collapse_last < n_prompts // 2

    crack = diversity_rose or beats_freq_meaningfully
    verdict = ("CRACK (b): byte-diversity / disambiguation rose with scale"
               if crack else
               "NULL (a): mode-collapse PERSISTS at scale; R-RBS-LM-19 ~3.3% "
               "structural ceiling holds for byte-level")
    print("=== VERDICT ===")
    print(f"  scale span: {first['n_obs']:,} obs -> {last['n_obs']:,} obs "
          f"({last['scale_x_vs_anchor']}x)")
    print(f"  distinct-byte-ratio trend (first->last): {div_trend:+.3f} "
          f"(diversity_rose={diversity_rose})")
    print(f"  mode-collapsed at largest scale: {collapse_last}/{n_prompts} prompts")
    print(f"  held-out vs FREQUENCY baseline: top1 margin={margin_top1:+.4f} "
          f"(2*SE={2*se:.4f}); top5 margin={margin_top5:+.4f}; "
          f"beats_freq_meaningfully={beats_freq_meaningfully}")
    print(f"  held-out top-1 lift_vs_uniform={lift_top1}x")
    print(f"  => {verdict}")

    summary = {
        "partition": "R-RBS-LM-223_SUMMARY",
        "anchor_obs": anchor_obs,
        "max_obs": last["n_obs"],
        "max_scale_x": last["scale_x_vs_anchor"],
        "distinct_ratio_trend": round(div_trend, 4),
        "diversity_rose": diversity_rose,
        "mode_collapsed_at_max_scale": f"{collapse_last}/{n_prompts}",
        "heldout_n_probes": n_probes,
        "heldout_top1_margin_vs_freq": round(margin_top1, 4),
        "heldout_top5_margin_vs_freq": round(margin_top5, 4),
        "heldout_2se": round(2 * se, 4),
        "beats_freq_meaningfully": beats_freq_meaningfully,
        "heldout_top1_lift_vs_uniform": lift_top1,
        "n_full_instrument_points": len(records),
        "n_spectrum_only_points": len(spectrum_extra),
        "max_spectrum_scale_x": (spectrum_extra[-1]["scale_x_vs_anchor"]
                                 if spectrum_extra else last["scale_x_vs_anchor"]),
        "eff_rank_trend": [round(r["f172_spectrum"]["effective_rank"], 2)
                           for r in records + spectrum_extra],
        "verdict": verdict,
    }
    with open(OUT_NDJSON, "w") as fh:
        for rec in records:
            fh.write(json.dumps(rec) + "\n")
        for rec in spectrum_extra:
            fh.write(json.dumps(rec) + "\n")
        fh.write(json.dumps(summary) + "\n")
    print(f"\n  wrote {len(records)+len(spectrum_extra)+1} records -> {OUT_NDJSON.name}")


if __name__ == "__main__":
    main()
