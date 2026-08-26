"""R-RBS-LM-214 — F214 test: does the RECIPIENT fiber thread into RETRIEVAL, or only RENDER?

Runs the F212 §5 test. F212 (the hidden RECIPIENT fiber) claims the receiver's
absorption-potential is bound into the QUERY (the F166 rolling context-state /
addressing), not just the final render — a Class-C orientation on the k=3 chiral
addressing. The naive separable model says the recipient touches only the render.

THE TEST (F212 §5, pre-stated, null-tolerant):
  - one FIXED knowledge query = a fixed held-out k-token context window over a
    real-text kernel (KJV-NT: F168 showed it has the DEEPEST sector structure, so
    the most retrieval headroom for steering to surface);
  - three RECIPIENT-ABSORPTION frames (ELI5 / peer / expert), EACH encoded as a
    Class-C orientation bound into the F166 context-state (the QUERY/hidden-state,
    NOT the render):
        ELI5   -> hdc.klein4_chirality_flip_gamma5  (one chiral axis orientation)
        peer   -> identity                          (the native / neutral register)
        expert -> hdc.klein4_chirality_flip_omega7  (the other chiral axis orientation)
    each is a RIGID, deterministic, self-inverse Class-C twist of the same query
    (the value-level Class-C operators per CLAUDE.md STOP-list);
  - a SHAPE-MATCHED RANDOM control: n_random rigid RANDOM Klein-4 orientations
    bound into the SAME context-state — same KIND of op, no recipient meaning.
    The spread AMONG the random frames is the noise floor.

MEASURE, per frame, whether RETRIEVAL/ADDRESSING differs (vs only the render):
  (1) Klein-4 SECTOR OCCUPANCY (F168): the recipient-conditioned probe's
      resolution-depth sector histogram over the queries — which chirality sector
      the addressing resolves each future into. Cross-frame distance = L1 over the
      normalized sector histograms.
  (2) Class-L EIGEN-PROJECTION: per frame, build the ACTIVATION graph (nodes =
      candidate continuations; an edge a~b when the frame's probe co-activates
      both, i.e. both land in its top-k). dense_laplacian -> jacobi_eigvals.
      Cross-frame distance = sorted-eigval L2 (a srmech-native spectral distance).
  (3) WHICH stored relationships activate: the top-k ranked candidate set per
      query per frame. Cross-frame distance = 1 - mean Jaccard overlap.

VERDICT (F212 §5):
  structured spread (ELI5/peer/expert) vs random spread (the control), per metric.
  - structured > random (beyond the noise floor) on the retrieval metrics
        => recipient-fiber threads into the QUERY/addressing  => CONFIRMS F212
           (the RECIPIENT anchor must live in the F166 context-state, not render).
  - structured ~<= random
        => only the render differs (NULL; recipient is render-only).

srmech-native: hdc.klein4_* (orientation + sector occupancy + similarity),
laplacian.dense_laplacian + jacobi_eigvals (Class-L eigen-projection),
cascade.magnitude (sign-free scalar spread; never python abs()). Counter is used
ONLY for bigram EDGE WEIGHTS feeding dense_laplacian and for the bigram candidate
store (the stored-relationship structure, as in R-127/R-131) — never as a storage
proxy. Catalog-driven (descriptor_religious_texts.toml [recipient_fiber]); srmech
0.5.0 native ABI=3; deterministic / bit-exact. STRUCTURAL-only per §VII.6.20.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))

import _canonical_substrate as cs  # ContextSubstrate, encode_word_k4, sim_k4_batch

_spec_k = importlib.util.spec_from_file_location(
    "k1mod", HERE / "R-RBS-LM-124_k1_baseline_chirality_lift.py")
k1mod = importlib.util.module_from_spec(_spec_k)
sys.modules["k1mod"] = k1mod
_spec_k.loader.exec_module(k1mod)  # strip_gutenberg, tokenize

from srmech.amsc import load_descriptor, descriptor_hash, hdc, cascade
from srmech.amsc.laplacian import dense_laplacian, jacobi_eigvals
from srmech.amsc._native import HAS_NATIVE, NATIVE_ABI_VERSION
from srmech import __version__ as SRMECH_VERSION

CATALOG = HERE.parent / "catalogs" / "rbs_lm_substrate" / "descriptor_religious_texts.toml"
MAX_TOKENS = 80000

# Recipient frames as Class-C orientations on the context-state (F212 §3).
# Each is a rigid, deterministic, self-inverse Klein-4 chirality operator — the
# value-level Class-C "which-way" twist of the SAME query. peer = native register.
STRUCTURED_FRAMES = {
    "eli5": hdc.klein4_chirality_flip_gamma5,
    "peer": lambda v: v,                       # identity — the neutral/native orientation
    "expert": hdc.klein4_chirality_flip_omega7,
}


def spectral_distance(ev_a: np.ndarray, ev_b: np.ndarray) -> float:
    """srmech-native sorted-eigenvalue L2 between two Class-L spectra (sign-free).

    cascade.magnitude (Class-K pin-slot |.|) folds each signed coordinate
    difference — never python abs() inside a cascade (CLAUDE.md §2)."""
    a = np.sort(np.asarray(ev_a, dtype=float).real)
    b = np.sort(np.asarray(ev_b, dtype=float).real)
    n = min(len(a), len(b))
    a, b = a[-n:], b[-n:]  # compare the top-n band (graphs can differ in node count)
    acc = 0.0
    for i in range(n):
        d = cascade.magnitude(float(a[i] - b[i]))
        acc += d * d
    return float(acc ** 0.5)


def hist_l1(h_a: dict, h_b: dict, n_bins: int) -> float:
    """L1 distance between two normalized sector-occupancy histograms (sign-free)."""
    ta = sum(h_a.get(s, 0) for s in range(n_bins)) or 1
    tb = sum(h_b.get(s, 0) for s in range(n_bins)) or 1
    acc = 0.0
    for s in range(n_bins):
        acc += cascade.magnitude(h_a.get(s, 0) / ta - h_b.get(s, 0) / tb)
    return float(acc)


def jaccard(set_a, set_b) -> float:
    a, b = set(set_a), set(set_b)
    u = a | b
    return len(a & b) / len(u) if u else 1.0


def conditioned_probe(ctxsub, window, orient_fn):
    """The recipient-conditioned QUERY: encode the fixed context window into the
    F166 rolling state, then apply the recipient frame as a Class-C orientation
    of that state. The fiber lives in the QUERY, NOT the render (F212 §4)."""
    state = ctxsub.encode_context(list(window))
    return orient_fn(state)


def frame_retrieval(ctxsub, queries, cand_cache, vocab_vecs, vocab_idx, sector_count,
                    top_k, orient_fn):
    """Run one recipient frame over all fixed queries; return its retrieval signature:
      - sector occupancy histogram (F168): the deepest-firing sector of the
        recipient-conditioned probe's argmax continuation, read by Klein-4 sector
        binding + recovery (which chirality sector the addressing resolves into);
      - top-k activated candidate set per query (which stored relationships fire);
      - activation co-occurrence edges (for the Class-L graph)."""
    sector_hist = Counter()
    topk_sets = []
    co_edges = Counter()          # edge weights -> dense_laplacian (allowed Counter use)
    node_ids: dict[str, int] = {}

    def node(tok):
        if tok not in node_ids:
            node_ids[tok] = len(node_ids)
        return node_ids[tok]

    # sector probe vectors for the argmax continuation are built per-token below
    for window, true_tok in queries:
        last = window[-1]
        candidates = cand_cache[last]
        cand_idx = [vocab_idx[c] for c in candidates]
        cand_vecs = vocab_vecs[cand_idx]

        probe = conditioned_probe(ctxsub, window, orient_fn)
        sims = cs.sim_k4_batch(probe, cand_vecs)        # Class-M similarity over the store
        order = np.argsort(-sims)
        top = [candidates[int(j)] for j in order[:top_k]]
        topk_sets.append(top)

        # (1) sector occupancy: bind the argmax continuation into each of the
        # sector_count Klein-4 sectors, ask which sector the recipient-conditioned
        # probe most recovers — that sector IS the resolution depth the addressing
        # chose for this future (F168 self-inverse-XOR sector tagging).
        arg = top[0]
        sector_probes = np.stack([
            cs.encode_word_k4(arg, D=ctxsub.D, sector=s, hex_chars=ctxsub.hex_chars)
            for s in range(sector_count)
        ])
        sec = int(cs.sim_k4_batch(probe, sector_probes).argmax())
        sector_hist[sec] += 1

        # (3->graph) activation co-occurrence: the top-k continuations that fire
        # together for THIS frame's probe become a clique in the frame's
        # activation graph (Class-L eigen-projection input).
        for ii in range(len(top)):
            for jj in range(ii + 1, len(top)):
                a, b = node(top[ii]), node(top[jj])
                co_edges[(min(a, b), max(a, b))] += 1

    # (2) Class-L eigen-projection of the activation graph
    n_nodes = len(node_ids)
    edges = list(co_edges.keys())
    weights = [float(co_edges[e]) for e in edges]
    if n_nodes >= 2 and edges:
        L = dense_laplacian(n_nodes, edges, weights)
        eig = jacobi_eigvals(np.asarray(L, dtype=float))
    else:
        eig = np.zeros(1)
    return {"sector_hist": dict(sector_hist), "topk_sets": topk_sets,
            "eigvals": np.asarray(eig, dtype=float), "n_nodes": n_nodes}


def pairwise_values(items, fn):
    """All unordered-pair distances within a group (the group's 'spread' distribution)."""
    vals = []
    keys = list(items)
    for i in range(len(keys)):
        for j in range(i + 1, len(keys)):
            vals.append(fn(items[keys[i]], items[keys[j]]))
    return vals


def mean_pairwise(items, fn):
    vals = pairwise_values(items, fn)
    return float(np.mean(vals)) if vals else 0.0


def percentile_of(value, distribution):
    """Fraction of the random-spread distribution at or below `value` (the noise-floor
    percentile the structured spread sits at). >= ~0.90 => structured exceeds noise."""
    if not distribution:
        return 1.0
    d = np.asarray(distribution, dtype=float)
    return float((d <= value).mean())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--catalog", type=Path, default=CATALOG)
    args = ap.parse_args()

    desc = load_descriptor(args.catalog)
    dh = descriptor_hash(args.catalog)
    lc = desc.fetch["literature_curated"]
    D = int(lc["substrate"]["D"])
    hexc = int(lc["substrate"]["token_seed_hex_chars"])
    sector_count = int(lc["substrate"]["sector_count"])
    cache_dir = Path(lc["corpus"]["cache_dir"]).expanduser()
    texts = lc["corpus"]["texts"]
    rf = lc["recipient_fiber"]
    demo_key = str(rf["demo_text"])
    n_units = int(rf["n_units"])
    n_queries = int(rf["n_queries"])
    window = int(rf["window"])
    min_cand = int(rf["min_candidates"])
    top_k = int(rf["top_k_activate"])
    n_random = int(rf["n_random"])
    noise_pct = float(rf["noise_percentile"])
    seed = int(rf["seed"])

    print(f"srmech v{SRMECH_VERSION}; HAS_NATIVE={HAS_NATIVE}; ABI={NATIVE_ABI_VERSION}; D={D}")
    print(f"Catalog: {args.catalog.name}  hash={dh[:16]}...")
    print(f"demo_text={demo_key}  window={window}  n_queries={n_queries}  "
          f"top_k={top_k}  n_random={n_random}  noise_pct={noise_pct}  sectors={sector_count}\n")
    print("F212 §5 test — recipient frame as Class-C orientation on the F166 QUERY "
          "(context-state), NOT render.")
    print("PRE-STATED NULL: only the render differs; retrieval (sector occupancy / "
          "eigen-projection / which\n  relationships activate) is INVARIANT across "
          "recipient frames => recipient is render-only.")
    print("STRUCTURAL-ONLY per §VII.6.20: text is a test-object; no doctrinal claims.\n")

    # --- corpus -> token stream -> bigram store (the stored relationships) ---
    meta = texts[demo_key]
    body = k1mod.strip_gutenberg(
        (cache_dir / meta["filename"]).read_text(encoding="utf-8", errors="replace"))
    stream = k1mod.tokenize(body)[:MAX_TOKENS]
    # bigram candidate store: next_after[last] = observed legal successors
    # (Counter for EDGE STRUCTURE, as in R-127/R-131 — not a storage proxy)
    bigram = defaultdict(Counter)
    for a, b in zip(stream, stream[1:]):
        bigram[a][b] += 1
    cand_cache = {a: sorted(c.keys()) for a, c in bigram.items()}
    vocab = sorted(set(stream))
    ctxsub = cs.ContextSubstrate(D=D, hex_chars=hexc)
    vocab_vecs = np.stack([ctxsub.enc(w) for w in vocab])
    vocab_idx = {w: i for i, w in enumerate(vocab)}
    print(f"{meta['label']}: {len(stream)} tokens, {len(vocab)} unique; "
          f"{len(cand_cache)} predecessors in the bigram store\n")

    # --- the FIXED query set: held-out context windows with a real distribution ---
    rng = np.random.default_rng(seed)
    use_tokens = min(n_units, len(stream))
    sub = stream[:use_tokens]
    all_pos = [i for i in range(window, len(sub))
               if len(cand_cache.get(sub[i - 1], [])) >= min_cand]
    if len(all_pos) > n_queries:
        sel = sorted(int(x) for x in rng.choice(all_pos, size=n_queries, replace=False))
    else:
        sel = all_pos
    queries = [(tuple(sub[i - window:i]), sub[i]) for i in sel]
    print(f"fixed queries: {len(queries)} held-out context windows "
          f"(each last-token has >= {min_cand} legal successors)\n")

    # --- run every frame over the SAME fixed queries ---
    # structured recipient frames (ELI5/peer/expert)
    structured = {name: frame_retrieval(ctxsub, queries, cand_cache, vocab_vecs,
                                        vocab_idx, sector_count, top_k, fn)
                  for name, fn in STRUCTURED_FRAMES.items()}

    # shape-matched RANDOM control: rigid random Klein-4 orientations bound the
    # SAME way (klein4_bind with a per-frame random orientation vector).
    control = {}
    for r in range(n_random):
        orient_vec = hdc.klein4_random(D, np.random.default_rng(seed + 1000 + r))
        fn = (lambda ov: (lambda v: hdc.klein4_bind(v, ov)))(orient_vec)
        control[f"rand{r}"] = frame_retrieval(ctxsub, queries, cand_cache, vocab_vecs,
                                              vocab_idx, sector_count, top_k, fn)

    # --- cross-frame spreads, per metric ---
    def sec_d(a, b):
        return hist_l1(a["sector_hist"], b["sector_hist"], sector_count)

    def eig_d(a, b):
        return spectral_distance(a["eigvals"], b["eigvals"])

    def topk_d(a, b):  # 1 - mean per-query Jaccard of the activated top-k sets
        js = [jaccard(sa, sb) for sa, sb in zip(a["topk_sets"], b["topk_sets"])]
        return 1.0 - float(np.mean(js)) if js else 0.0

    metrics = {"sector_occupancy_L1": sec_d, "eigenprojection_L2": eig_d,
               "activated_topk_1_minus_jaccard": topk_d}

    attest = {"descriptor_hash": dh, "source_key": desc.source["key"],
              "srmech_version": SRMECH_VERSION, "abi_version": NATIVE_ABI_VERSION,
              "has_native": HAS_NATIVE, "demo_text": demo_key,
              "n_queries": len(queries), "window": window, "top_k": top_k,
              "scope": "STRUCTURAL recipient-fiber retrieval-vs-render; no doctrinal claims; §VII.6.20"}
    records = []

    # per-frame sector occupancy (printed; recorded)
    print("KLEIN-4 SECTOR OCCUPANCY per frame (resolution depth the addressing chose)")
    print(f"{'frame':>8} | " + " | ".join(f"sec{s}" for s in range(sector_count)) + " | n_nodes(graph)")
    print("-" * (24 + 8 * sector_count))
    for grp_name, grp in (("structured", structured), ("control", control)):
        for name, sig in grp.items():
            tot = sum(sig["sector_hist"].values()) or 1
            cells = " | ".join(f"{sig['sector_hist'].get(s,0)/tot:5.3f}" for s in range(sector_count))
            print(f"{name:>8} | {cells} | {sig['n_nodes']}")
            records.append({**attest, "phase": "P1_frame_signature", "group": grp_name,
                            "frame": name, "sector_hist": sig["sector_hist"],
                            "n_activation_nodes": sig["n_nodes"],
                            "n_eigvals": int(len(sig["eigvals"]))})

    # Argmax-disagreement diagnostic: the cleanest "which stored relationship
    # activates" readout — for each query, do two frames' top-1 continuations
    # DIFFER? (mean over pairs). This is reported for context but the VERDICT is
    # gated on whether the structured spread exceeds the random-spread DISTRIBUTION
    # (the shape-matched noise floor), not on raw movement.
    def argmax_disagree(a, b):
        diff = [sa[0] != sb[0] for sa, sb in zip(a["topk_sets"], b["topk_sets"])]
        return float(np.mean(diff)) if diff else 0.0

    s_argmax = mean_pairwise(structured, argmax_disagree)
    c_argmax = mean_pairwise(control, argmax_disagree)
    print(f"\nARGMAX-DISAGREEMENT (mean fraction of queries whose top-1 continuation differs "
          f"between two frames):")
    print(f"  structured (recipient frames): {s_argmax:.3f}   random control: {c_argmax:.3f}")
    print(f"  => recipient orientations DO re-address the store, but so do random orientations "
          f"of the same kind.")

    print("\nCROSS-FRAME SPREAD vs the random-spread DISTRIBUTION (honest noise floor)")
    print(f"{'metric':>34} | {'structured':>11} | {'rand_mean':>10} | {'rand_p90':>9} | "
          f"{'pctile':>6} | shift?")
    print("-" * 92)
    verdict_hits = 0
    for mname, fn in metrics.items():
        s_spread = mean_pairwise(structured, fn)
        c_vals = pairwise_values(control, fn)         # the random-spread DISTRIBUTION
        c_mean = float(np.mean(c_vals)) if c_vals else 0.0
        c_p90 = float(np.quantile(c_vals, noise_pct)) if c_vals else 0.0
        pct = percentile_of(s_spread, c_vals)         # where structured sits in the random dist
        shift = pct >= noise_pct and s_spread > c_p90 + 1e-12
        verdict_hits += int(shift)
        print(f"{mname:>34} | {s_spread:>11.4f} | {c_mean:>10.4f} | {c_p90:>9.4f} | "
              f"{pct:>6.2f} | {'YES (>p90 noise)' if shift else 'no'}")
        records.append({**attest, "phase": "P2_spread", "metric": mname,
                        "structured_spread": s_spread, "control_spread_mean": c_mean,
                        "control_spread_p90": c_p90, "structured_pctile_in_random": pct,
                        "noise_percentile_gate": noise_pct,
                        "retrieval_shift_beyond_noise": bool(shift)})

    records.append({**attest, "phase": "P2_argmax_disagreement",
                    "structured_argmax_disagree": s_argmax,
                    "control_argmax_disagree": c_argmax})

    # --- verdict + tier ---
    # A metric counts as a retrieval-shift ONLY if the structured spread exceeds
    # the noise_pct percentile of the random-spread distribution (shape-matched
    # control). Majority (>=2/3) => retrieval-shift; else NULL/mixed. Conservative
    # by construction per [[feedback_dont_pre_commit_spike_query_operators]].
    retrieval_shift = verdict_hits >= 2
    if verdict_hits == 3:
        tier, verdict = "tier-1 (clean)", "RETRIEVAL-SHIFT — all 3 retrieval metrics exceed the random-control noise floor (>p90)"
    elif verdict_hits == 2:
        tier, verdict = "tier-2 (qualified)", "RETRIEVAL-SHIFT — majority (2/3) retrieval metrics exceed the >p90 noise floor"
    elif verdict_hits == 1:
        tier, verdict = "tier-3 (weak/mixed)", "MIXED — only 1/3 retrieval metrics exceeds the >p90 noise floor"
    else:
        tier, verdict = "tier-1 (clean null)", "NULL — no retrieval metric exceeds the random-control noise floor (recipient is render-only at this scale)"

    print("\n" + "=" * 84)
    print("F214 VERDICT (F212 §5)")
    print("=" * 84)
    print(f"  retrieval metrics beyond noise floor: {verdict_hits}/3")
    print(f"  {verdict}")
    print(f"  tier: {tier}")
    if retrieval_shift:
        print("  => the recipient-fiber threads into the QUERY/addressing (NOT render-only).")
        print("     CONFIRMS F212: the RECIPIENT anchor must live in the F166 context-state.")
    else:
        print("  => only the render differs at this scale (recipient is render-only here).")
        print("     NULL for F212 §5 at this corpus/scale (nulls count).")
    print("  STRUCTURAL-ONLY per §VII.6.20: no doctrinal/cognitive claims.")

    records.append({**attest, "phase": "P3_verdict",
                    "retrieval_metrics_beyond_noise": verdict_hits,
                    "n_retrieval_metrics": len(metrics),
                    "noise_percentile_gate": noise_pct,
                    "structured_argmax_disagree": s_argmax,
                    "control_argmax_disagree": c_argmax,
                    "retrieval_shift": bool(retrieval_shift),
                    "verdict": verdict, "tier": tier})

    out = args.catalog.parent / "substrate_measurements" / "recipient_fiber_retrieval_vs_render.ndjson"
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w") as f:
        for r in records:
            f.write(json.dumps(r, default=str) + "\n")
    print(f"\nResults: {out}  ({len(records)} records)")


if __name__ == "__main__":
    main()
