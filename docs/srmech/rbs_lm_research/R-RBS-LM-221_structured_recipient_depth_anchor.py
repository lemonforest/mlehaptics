"""R-RBS-LM-221 — F221 test: does a STRUCTURED recipient DEPTH-anchor thread into
RETRIEVAL where the F214 content-free twist did NOT?

This is the falsifiable next step F214 §8 demanded (issue #760). F214 falsified
ONE operationalization of the F212 recipient fiber: a rigid, CONTENT-FREE global
Class-C orientation of the F166 context-state (hdc.klein4_chirality_flip_*) is
indistinguishable from a random orientation in retrieval — a constant XOR-twist
re-labels every F168 sector uniformly, carrying no information about absorption
DEPTH. F214 §5 sharpened (not refuted) F212: the RECIPIENT anchor must carry
recipient-specific STRUCTURE — a WHICH-DEPTH operator over the F168 sector ladder
that selects sectors NON-RANDOMLY (ELI5 -> shallow 0-1; expert -> deep 2-3).

THE STRUCTURED ANCHOR (the F221 design — peer to the F165 DOMAIN labeled-store):
  Each recipient frame's anchor is a DEPTH-BIAS vector = the klein4 BUNDLE of
  encode_word_k4 depth-TAG vectors over the frame's target F168 sector band
  (the F168 / R-RBS-LM-131 sector tagging — encode_word_k4(sector=s) is the
  self-inverse XOR sector tag):
      ELI5   -> shallow band, sectors [0,1]   (word/bigram resolution depth)
      peer   -> neutral band, all sectors     (the native register)
      expert -> deep band,    sectors [2,3]   (the F168 load-bearing deep sectors)
  The anchor is BOUND into the F166 rolling context-state (klein4_bind) — the
  QUERY/hidden-state, NOT the render (F212 §4) — the SAME bind the F214 random
  control uses. The ONLY difference from the F214 content-free control is that
  the bound vector carries DEPTH STRUCTURE (it points at a sector band) instead
  of being a random orientation. So any shift beyond the floor is attributable
  to the absorption-depth STRUCTURE, not the kind of op (that is the F214->F221
  contrast made fair).

THE CONTROL (identical to F214): the SAME 16-frame shape-matched random Klein-4
orientations bound the SAME way (klein4_bind with a per-frame random vector).
The pairwise spread AMONG the random frames is the noise floor; the verdict is
gated on whether the structured spread exceeds its p90 percentile.

MEASURE, per frame, over the SAME fixed query set (F214 §3 — three retrieval
readouts + the noise floor):
  (1) Klein-4 SECTOR OCCUPANCY (F168): the recipient-conditioned probe's argmax
      continuation is bound into each of the 4 Klein-4 sectors; the most-recovered
      sector is the resolution depth the addressing chose. Cross-frame distance =
      L1 over normalized sector histograms. THIS is the F168-native depth readout
      a depth-anchor should move non-randomly (it was the clean NULL in F214).
  (2) Class-L EIGEN-PROJECTION: per-frame activation graph (nodes = candidate
      continuations; clique edge when both land in the probe's top-k) ->
      dense_laplacian -> jacobi_eigvals. Cross-frame distance = sorted-eigval L2
      (cascade.magnitude folds each signed coordinate; never python abs()).
  (3) WHICH stored relationships activate: top-k ranked candidate set per query.
      Cross-frame distance = 1 - mean Jaccard.

PRE-STATED NULL (STRONGER than F214's, F214 §8 / issue #760):
  "even the STRUCTURED depth-anchor does not exceed the noise floor in retrieval
   => the recipient-fiber is render-only EVEN WITH depth structure."
VERDICT (F212 §5, F221 design):
  - structured spread > random p90 on the retrieval metrics (majority >= 2/3,
    AND the F168-native sector-occupancy readout among them)
        => the recipient-DEPTH anchor threads into the QUERY/addressing
           => CONFIRMS F212: the RECIPIENT anchor belongs in the F166 context-
              state as a depth-operator (resolves #760).
  - structured ~<= random p90
        => NULL: recipient is render-only even structured (stronger F214 null).

srmech-native: hdc.{klein4_bind, klein4_bundle, klein4_random} (the anchor build +
orientation), encode_word_k4(sector=s) (the F168 sector tagging), sim_k4_batch
(Class-M retrieval), laplacian.dense_laplacian + jacobi_eigvals (Class-L eigen-
projection), cascade.magnitude (sign-free spectral / histogram distance; never
python abs()). Counter is used ONLY for bigram EDGE WEIGHTS feeding dense_laplacian
and the bigram candidate store (the stored-relationship structure, as in
R-127/R-131) — never as a storage proxy. Catalog-driven
(descriptor_religious_texts.toml [recipient_depth_anchor]); srmech 0.5.0 native
ABI=3; deterministic / bit-exact. STRUCTURAL-only per §VII.6.20.
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


# ---------------------------------------------------------------------------
# The STRUCTURED depth-anchor build (the F221 core — the F214 forward-ask)
# ---------------------------------------------------------------------------

def build_depth_anchor(ctxsub, band, n_tags, seed):
    """A recipient DEPTH-bias anchor = the klein4 BUNDLE of encode_word_k4 depth-TAG
    vectors over the target F168 sector band. This is NOT a content-free global
    twist (F214's null); it is a vector that POINTS at a sector band of the F168
    ladder, built from the same F168 sector-tagging primitive (encode_word_k4(
    sector=s)) used to hold the futures. n_tags tag-tokens per band give the band a
    stable, band-specific orientation; bundle requires an ODD count (majority
    tie-break — the ContextSubstrate.bundle_odd pad rule).

    band = [] (the empty / no-bias case) returns None -> identity (no anchor)."""
    if not band:
        return None
    rng = np.random.default_rng(seed)
    tags = []
    # deterministic per-band tag tokens, each tagged into a sector OF THE BAND, so
    # the anchor's mass sits in the band's sectors (the absorption-depth structure).
    for t in range(n_tags):
        s = int(band[t % len(band)])
        tok = f"__depth_tag_{'_'.join(map(str, band))}_{t}__"
        tags.append(cs.encode_word_k4(tok, D=ctxsub.D, sector=s, hex_chars=ctxsub.hex_chars))
    # decorrelate tag identities deterministically (seed is band-derived upstream)
    _ = rng  # rng reserved for future stochastic-tag variants; kept deterministic here
    return ctxsub.bundle_odd(tags)


def make_structured_frames(ctxsub, bands, n_tags, seed):
    """Three recipient frames as DEPTH-anchor orientations bound into the context-
    state (the QUERY, F212 §4). Each frame's orientation fn binds the frame's
    depth-anchor into the encoded context-state via klein4_bind — the SAME bind
    the F214 random control uses; the difference is the bound vector is a STRUCTURED
    depth-band bundle, not a random orientation."""
    anchors = {
        "eli5": build_depth_anchor(ctxsub, bands["shallow"], n_tags, seed + 1),
        "peer": build_depth_anchor(ctxsub, bands["neutral"], n_tags, seed + 2),
        "expert": build_depth_anchor(ctxsub, bands["deep"], n_tags, seed + 3),
    }

    def orient(anchor):
        if anchor is None:
            return lambda v: v
        return lambda v: hdc.klein4_bind(v, anchor)

    return {name: orient(a) for name, a in anchors.items()}, anchors


# ---------------------------------------------------------------------------
# srmech-native distances (identical to R-RBS-LM-214 — sign-free via cascade.magnitude)
# ---------------------------------------------------------------------------

def spectral_distance(ev_a: np.ndarray, ev_b: np.ndarray) -> float:
    """srmech-native sorted-eigenvalue L2 between two Class-L spectra (sign-free).
    cascade.magnitude (Class-K pin-slot |.|) folds each signed coordinate
    difference — never python abs() inside a cascade (CLAUDE.md §2)."""
    a = np.sort(np.asarray(ev_a, dtype=float).real)
    b = np.sort(np.asarray(ev_b, dtype=float).real)
    n = min(len(a), len(b))
    a, b = a[-n:], b[-n:]
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
    F166 rolling state, then apply the recipient DEPTH-anchor as a Class-M bind of
    that state. The anchor lives in the QUERY, NOT the render (F212 §4)."""
    state = ctxsub.encode_context(list(window))
    return orient_fn(state)


def frame_retrieval(ctxsub, queries, cand_cache, vocab_vecs, vocab_idx, sector_count,
                    top_k, orient_fn):
    """Run one recipient frame over all fixed queries; return its retrieval
    signature (sector occupancy / top-k activated set / activation co-occurrence
    graph). Identical readouts to R-RBS-LM-214 — only the orient_fn differs."""
    sector_hist = Counter()
    topk_sets = []
    co_edges = Counter()          # edge weights -> dense_laplacian (allowed Counter use)
    node_ids: dict[str, int] = {}

    def node(tok):
        if tok not in node_ids:
            node_ids[tok] = len(node_ids)
        return node_ids[tok]

    for window, _true_tok in queries:
        last = window[-1]
        candidates = cand_cache[last]
        cand_idx = [vocab_idx[c] for c in candidates]
        cand_vecs = vocab_vecs[cand_idx]

        probe = conditioned_probe(ctxsub, window, orient_fn)
        sims = cs.sim_k4_batch(probe, cand_vecs)        # Class-M similarity over the store
        order = np.argsort(-sims)
        top = [candidates[int(j)] for j in order[:top_k]]
        topk_sets.append(top)

        # (1) sector occupancy: which F168 sector the recipient-conditioned probe
        # most recovers for its argmax continuation — the resolution depth the
        # addressing chose (F168 self-inverse-XOR sector tagging).
        arg = top[0]
        sector_probes = np.stack([
            cs.encode_word_k4(arg, D=ctxsub.D, sector=s, hex_chars=ctxsub.hex_chars)
            for s in range(sector_count)
        ])
        sec = int(cs.sim_k4_batch(probe, sector_probes).argmax())
        sector_hist[sec] += 1

        # (3->graph) activation co-occurrence clique for the Class-L eigen-projection
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
    rd = lc["recipient_depth_anchor"]
    demo_key = str(rd["demo_text"])
    n_units = int(rd["n_units"])
    n_queries = int(rd["n_queries"])
    window = int(rd["window"])
    min_cand = int(rd["min_candidates"])
    top_k = int(rd["top_k_activate"])
    n_random = int(rd["n_random"])
    noise_pct = float(rd["noise_percentile"])
    n_tags = int(rd["n_anchor_tags"])
    bands = {"shallow": [int(x) for x in rd["shallow_band"]],
             "neutral": [int(x) for x in rd["neutral_band"]],
             "deep": [int(x) for x in rd["deep_band"]]}
    seed = int(rd["seed"])

    print(f"srmech v{SRMECH_VERSION}; HAS_NATIVE={HAS_NATIVE}; ABI={NATIVE_ABI_VERSION}; D={D}")
    print(f"Catalog: {args.catalog.name}  hash={dh[:16]}...")
    print(f"demo_text={demo_key}  window={window}  n_queries={n_queries}  top_k={top_k}  "
          f"n_random={n_random}  noise_pct={noise_pct}  sectors={sector_count}")
    print(f"DEPTH BANDS — eli5(shallow)={bands['shallow']}  peer(neutral)={bands['neutral']}  "
          f"expert(deep)={bands['deep']}  n_anchor_tags={n_tags}\n")
    print("F221 test — recipient frame as a STRUCTURED DEPTH-anchor (which-depth operator")
    print("over the F168 sector ladder) bound into the F166 QUERY (context-state), NOT render.")
    print("PRE-STATED NULL (stronger than F214): even the STRUCTURED depth-anchor does not")
    print("  exceed the noise floor in retrieval => recipient-fiber is render-only EVEN with depth.")
    print("STRUCTURAL-ONLY per §VII.6.20: text is a test-object; no doctrinal claims.\n")

    # --- corpus -> token stream -> bigram store (the stored relationships) ---
    meta = texts[demo_key]
    body = k1mod.strip_gutenberg(
        (cache_dir / meta["filename"]).read_text(encoding="utf-8", errors="replace"))
    stream = k1mod.tokenize(body)[:MAX_TOKENS]
    bigram = defaultdict(Counter)       # Counter for EDGE STRUCTURE (R-127/R-131), not a proxy
    for a, b in zip(stream, stream[1:]):
        bigram[a][b] += 1
    cand_cache = {a: sorted(c.keys()) for a, c in bigram.items()}
    vocab = sorted(set(stream))
    ctxsub = cs.ContextSubstrate(D=D, hex_chars=hexc)
    vocab_vecs = np.stack([ctxsub.enc(w) for w in vocab])
    vocab_idx = {w: i for i, w in enumerate(vocab)}
    print(f"{meta['label']}: {len(stream)} tokens, {len(vocab)} unique; "
          f"{len(cand_cache)} predecessors in the bigram store\n")

    # --- the FIXED query set (IDENTICAL construction to R-RBS-LM-214) ---
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

    # --- build the STRUCTURED depth-anchor frames + run them ---
    structured_fns, anchors = make_structured_frames(ctxsub, bands, n_tags, seed)
    # diagnostic: confirm the three depth-anchors are NON-degenerate (distinct
    # orientations) so any null is "structure doesn't steer", not "anchors collapsed".
    def anchor_sim(a, b):
        if a is None or b is None:
            return float("nan")
        return float(cs.sim_k4_batch(a, b[None, :])[0])
    print("DEPTH-ANCHOR pairwise similarity (should be < 1.0 — distinct band orientations):")
    print(f"  eli5~peer={anchor_sim(anchors['eli5'], anchors['peer']):.3f}  "
          f"eli5~expert={anchor_sim(anchors['eli5'], anchors['expert']):.3f}  "
          f"peer~expert={anchor_sim(anchors['peer'], anchors['expert']):.3f}\n")

    structured = {name: frame_retrieval(ctxsub, queries, cand_cache, vocab_vecs,
                                        vocab_idx, sector_count, top_k, fn)
                  for name, fn in structured_fns.items()}

    # shape-matched RANDOM control (IDENTICAL to R-RBS-LM-214): rigid random
    # Klein-4 orientations bound the SAME way (klein4_bind w/ a random vector).
    control = {}
    for r in range(n_random):
        orient_vec = hdc.klein4_random(D, np.random.default_rng(seed + 1000 + r))
        fn = (lambda ov: (lambda v: hdc.klein4_bind(v, ov)))(orient_vec)
        control[f"rand{r}"] = frame_retrieval(ctxsub, queries, cand_cache, vocab_vecs,
                                              vocab_idx, sector_count, top_k, fn)

    # --- cross-frame spreads, per metric (identical metric set to R-RBS-LM-214) ---
    def sec_d(a, b):
        return hist_l1(a["sector_hist"], b["sector_hist"], sector_count)

    def eig_d(a, b):
        return spectral_distance(a["eigvals"], b["eigvals"])

    def topk_d(a, b):
        js = [jaccard(sa, sb) for sa, sb in zip(a["topk_sets"], b["topk_sets"])]
        return 1.0 - float(np.mean(js)) if js else 0.0

    metrics = {"sector_occupancy_L1": sec_d, "eigenprojection_L2": eig_d,
               "activated_topk_1_minus_jaccard": topk_d}

    attest = {"descriptor_hash": dh, "source_key": desc.source["key"],
              "srmech_version": SRMECH_VERSION, "abi_version": NATIVE_ABI_VERSION,
              "has_native": HAS_NATIVE, "demo_text": demo_key,
              "n_queries": len(queries), "window": window, "top_k": top_k,
              "anchor_kind": "structured_depth_band_bundle",
              "shallow_band": bands["shallow"], "neutral_band": bands["neutral"],
              "deep_band": bands["deep"], "n_anchor_tags": n_tags,
              "scope": "STRUCTURAL recipient depth-anchor retrieval-vs-render; no doctrinal claims; §VII.6.20"}
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

    # record the depth-anchor diagnostic (non-degeneracy)
    records.append({**attest, "phase": "P1_anchor_diagnostic",
                    "eli5_peer_sim": anchor_sim(anchors["eli5"], anchors["peer"]),
                    "eli5_expert_sim": anchor_sim(anchors["eli5"], anchors["expert"]),
                    "peer_expert_sim": anchor_sim(anchors["peer"], anchors["expert"])})

    # Argmax-disagreement diagnostic (context; the VERDICT is the p90-gated spread).
    def argmax_disagree(a, b):
        diff = [sa[0] != sb[0] for sa, sb in zip(a["topk_sets"], b["topk_sets"])]
        return float(np.mean(diff)) if diff else 0.0

    s_argmax = mean_pairwise(structured, argmax_disagree)
    c_argmax = mean_pairwise(control, argmax_disagree)
    print(f"\nARGMAX-DISAGREEMENT (mean fraction of queries whose top-1 continuation differs):")
    print(f"  structured (depth anchors): {s_argmax:.3f}   random control: {c_argmax:.3f}")

    print("\nCROSS-FRAME SPREAD vs the random-spread DISTRIBUTION (the F214 noise floor)")
    print(f"{'metric':>34} | {'structured':>11} | {'rand_mean':>10} | {'rand_p90':>9} | "
          f"{'pctile':>6} | shift?")
    print("-" * 92)
    verdict_hits = 0
    sector_shift = False
    for mname, fn in metrics.items():
        s_spread = mean_pairwise(structured, fn)
        c_vals = pairwise_values(control, fn)         # the random-spread DISTRIBUTION
        c_mean = float(np.mean(c_vals)) if c_vals else 0.0
        c_p90 = float(np.quantile(c_vals, noise_pct)) if c_vals else 0.0
        pct = percentile_of(s_spread, c_vals)
        shift = pct >= noise_pct and s_spread > c_p90 + 1e-12
        verdict_hits += int(shift)
        if mname == "sector_occupancy_L1":
            sector_shift = shift
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
    # A metric counts only if structured spread exceeds the noise_pct percentile of
    # the random-spread distribution. F221 strengthens F214's verdict logic: the
    # F168-NATIVE sector-occupancy readout (the clean NULL in F214, the readout a
    # DEPTH-anchor is designed to move) must be among the hits for a clean confirm,
    # because top-k Jaccard is a construction artifact (F214 §4). Majority (>=2/3)
    # => retrieval-shift; conservative per [[feedback_dont_pre_commit_spike_query_operators]].
    retrieval_shift = verdict_hits >= 2
    clean_confirm = retrieval_shift and sector_shift
    if verdict_hits == 3:
        tier, verdict = "tier-1 (clean)", "RETRIEVAL-SHIFT — all 3 retrieval metrics exceed the F214 noise floor (>p90)"
    elif verdict_hits == 2 and sector_shift:
        tier, verdict = "tier-1 (clean)", "RETRIEVAL-SHIFT — 2/3 incl. the F168-native sector-occupancy readout exceed the >p90 noise floor"
    elif verdict_hits == 2:
        tier, verdict = "tier-2 (qualified)", "RETRIEVAL-SHIFT — 2/3 metrics exceed the >p90 noise floor (sector-occupancy NOT among them — read with the F214 §4 construction caveat)"
    elif verdict_hits == 1 and sector_shift:
        tier, verdict = "tier-2 (qualified)", "MIXED-LEANING-CONFIRM — only the F168-native sector-occupancy readout exceeds the >p90 noise floor (the depth-relevant metric moved)"
    elif verdict_hits == 1:
        tier, verdict = "tier-3 (weak/mixed)", "MIXED — only 1/3 metrics (NOT sector-occupancy) exceeds the >p90 noise floor"
    else:
        tier, verdict = "tier-1 (clean null)", "NULL — no retrieval metric exceeds the F214 noise floor (recipient is render-only even with depth structure)"

    print("\n" + "=" * 84)
    print("F221 VERDICT (F212 §5 / F214 §8 forward-ask — STRUCTURED depth-anchor)")
    print("=" * 84)
    print(f"  retrieval metrics beyond the F214 noise floor: {verdict_hits}/3   "
          f"(F168-native sector-occupancy moved: {sector_shift})")
    print(f"  {verdict}")
    print(f"  tier: {tier}")
    if retrieval_shift:
        print("  => the recipient-DEPTH anchor threads into the QUERY/addressing (NOT render-only).")
        print("     CONFIRMS F212: the RECIPIENT anchor belongs in the F166 context-state (resolves #760).")
    else:
        print("  => only the render differs even with depth structure (recipient is render-only here).")
        print("     NULL — stronger than F214: even a STRUCTURED depth-anchor stays at the noise floor.")
    print("  STRUCTURAL-ONLY per §VII.6.20: no doctrinal/cognitive claims.")

    records.append({**attest, "phase": "P3_verdict",
                    "retrieval_metrics_beyond_noise": verdict_hits,
                    "n_retrieval_metrics": len(metrics),
                    "sector_occupancy_shift": bool(sector_shift),
                    "noise_percentile_gate": noise_pct,
                    "structured_argmax_disagree": s_argmax,
                    "control_argmax_disagree": c_argmax,
                    "retrieval_shift": bool(retrieval_shift),
                    "clean_confirm_sector_native": bool(clean_confirm),
                    "verdict": verdict, "tier": tier})

    out = args.catalog.parent / "substrate_measurements" / "recipient_depth_anchor_retrieval_vs_render.ndjson"
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w") as f:
        for r in records:
            f.write(json.dumps(r, default=str) + "\n")
    print(f"\nResults: {out}  ({len(records)} records)")


if __name__ == "__main__":
    main()
