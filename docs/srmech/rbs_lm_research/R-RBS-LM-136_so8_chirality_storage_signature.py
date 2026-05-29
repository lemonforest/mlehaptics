"""R-RBS-LM-136 — does the SHIPPED so(8)/Spin(8)-triality chirality surface isolate
content-specific, translation-invariant storage where the HAND-BUILT K1-chiral did NOT?

F173 (R-RBS-LM-135) verdict: vocab-independent structure tracks FORM/GENRE not content;
the translation-invariant signal is lexical; the hand-built K1-chiral (directed γ₅-odd
antisymmetric Hermitian i·(A−Aᵀ) eigen-bundle) beat across-MAX (within 0.553 > across-max
0.465, ratio 1.46×) but gave NO advantage over the flat lexical eigen-bundle (within 0.667,
ratio 1.67×) — its chiral energy was near-uniform (0.77–0.90) across texts. The clean
"content-specific deep-structural storage" signature was NOT isolated by the hand-build.

THIS experiment swaps the hand-built chirality for srmech's SHIPPED so(8) chirality ops:
the Klein-4 (ℤ₂)² = (γ₅ × iω₇) bi-axial surface — 4 sectors × 7 = 28 = dim so(8). The ops
are srmech.amsc.hdc.{klein4_random, klein4_bind, klein4_bundle, klein4_similarity,
klein4_chirality_flip_gamma5/omega7, klein4_cpt_mirror, klein4_sector_count} plus the
Class-C cascade chirality srmech.amsc.cascade.{net_chirality, chiral_flip}.

KEY DESIGN POINT (the trap F173's brief warned about): klein4_chirality_flip_* are pure
XOR on the 2-bit sector label, so sim(K, flip(K)) ≡ 0 for ANY kernel — a self-vs-flip
triple is trivially (0,0,0) and discriminates nothing. The text-SPECIFIC signal must come
from STRUCTURE ACROSS the routed token vectors. So we route each token's Klein-4 vector
into one of the 4 (γ₅, iω₇) sectors by its DIRECTED co-occurrence parity (the word-ORDER
chirality the symmetric Laplacian discards), via the Klein-4 group action klein4_bind with a
constant-sector anchor. The text's so(8) chirality kernel is the frequency-weighted bundle
of these sector-routed token vectors. Three shipped-chirality signatures per text:

  (S1) BI-AXIAL OCCUPANCY profile  — klein4_sector_count(kernel) normalized: the
       [n_++, n_+-, n_-+, n_--] (γ₅,iω₇)-sector-occupancy 4-vector. Structural fingerprint
       of how the text's content distributes across the bi-axial chirality sectors.
  (S2) so(8) CHIRALITY KERNEL similarity — klein4_similarity(K_a, K_b): same content routed
       the same structural way → high klein4 overlap. The shipped-op analogue of the K1-chiral
       eigen-bundle. THIS is the head-to-head replacement for F173's hand-built K1-chiral.
  (S3) NET-CHIRALITY cascade reading — cascade.net_chirality over the per-token directed
       orientations (Class C conserved handedness) — a single signed invariant per text;
       reported descriptively (n=6 texts → the handedness vector compared across pair vs set).

CONTRAST (mirrors R-135 within_across): within-pair (Quran Yusuf vs Rodwell, SAME content)
vs across-content (all pairs among the 6 distinct texts). within beats across-MAX = the
isolation criterion. Baselines reported alongside: the F134 flat eigen-bundle (within 0.667,
across-max 0.572, 1.67×, BEATS) and the F135 hand-built K1-chiral (within 0.553, across-max
0.465, 1.46×, beats-max-but-no-advantage). Recomputed live, not hard-coded.

Confound-controlled by construction: VOCAB_SIZE=200 + matched token budget
(trim_chunks_to_budget; budget_tokens auto-clamped to min available). All rng seeded
(seed=42; per-token klein4 seeds are deterministic token-derived; klein4_random(...,seed=)).

SCOPE: STRUCTURAL test on TEXT OBJECTS only. Texts are structural test-objects. NO
doctrinal / truth / origin / ranking / clinical claims. MFO §VII.6.20 epistemic ceiling
(form-reading, not substrate-identity). n=1 same-content pair — a single datapoint, not a law.
Null counts: if the shipped chirality does NOT isolate (or only matches the flat bundle, as
F135 did), this reports that plainly.
"""
from __future__ import annotations

import argparse
import importlib.util
import itertools
import json
import sys
from collections import Counter
from pathlib import Path

import numpy as np

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))

# reuse R-RBS-LM-124's faithful srmech-native machinery (strip_gutenberg, chunk_text,
# tokenize, build_vocab, trim_chunks_to_budget, build_K1_flat, build_K1_chiral, eigen_bundle,
# similarity, WINDOW, VOCAB_SIZE, K_EIG, M_VOCAB)
_spec = importlib.util.spec_from_file_location(
    "k124", HERE / "R-RBS-LM-124_k1_baseline_chirality_lift.py")
k124 = importlib.util.module_from_spec(_spec)
sys.modules["k124"] = k124
_spec.loader.exec_module(k124)

from srmech.amsc import load_descriptor, descriptor_hash
from srmech.amsc import format as amsc_format
from srmech.amsc.hdc import (
    klein4_random, klein4_bind, klein4_bundle, klein4_similarity,
    klein4_sector_count, klein4_chirality_flip_gamma5, klein4_chirality_flip_omega7,
    klein4_cpt_mirror,
)
from srmech.amsc.cascade import net_chirality, chiral_flip
from srmech.amsc._native import HAS_NATIVE, NATIVE_ABI_VERSION
from srmech import __version__ as SRMECH_VERSION

CATALOG = HERE.parent / "catalogs" / "rbs_lm_substrate" / "descriptor_religious_texts.toml"

D_KLEIN4 = 8192          # Klein-4 hypervector dimension (matches canonical substrate D)
SEED = 42

# Klein-4 sector labels: 2-bit value = (γ₅ bit << 1) | (iω₇ bit).
#   sector 0 = (γ₅=0, iω₇=0) = ++   sector 1 = (γ₅=0, iω₇=1) = +-
#   sector 2 = (γ₅=1, iω₇=0) = -+   sector 3 = (γ₅=1, iω₇=1) = --
# klein4_chirality_flip_gamma5 = XOR 2 (γ₅ axis); _omega7 = XOR 1 (iω₇ axis); cpt = XOR 3.


def _token_klein4(token: str) -> np.ndarray:
    """Deterministic per-token Klein-4 hypervector via the SHIPPED klein4_random, seeded by a
    stable token-derived integer. (sha256 used ONLY to derive an rng SEED — not as storage; the
    storage object is the klein4 vector. Routed by directed parity below, not by this hash.)"""
    seed = int(amsc_format.sha256_bytes(token.encode("utf-8"))[:8], 16)   # 32-bit from hex digest
    return klein4_random(D_KLEIN4, seed=seed % (2**32))


def directed_orientations(chunks_tokens, vocab):
    """DIRECTED co-occurrence → per-token Class-C orientation (the γ₅-odd word-ORDER chirality).

    Builds forward counts F[a][b] = (a precedes b within WINDOW). The antisymmetric flow
    out_a − in_a (net directed flow through token a) gives its handedness: predominantly
    PRECEDES (source, +1) vs predominantly FOLLOWS (sink, −1). Sign-flip is read via
    cascade.net_chirality (Class C handedness of the {+1,0,−1} edge orientations) — NOT
    python abs()/sign — per [[feedback_sign_handling_is_class_k_pin_slot_not_alu_abs]].

    A SECOND structural axis (iω₇) = parity of the token's directed degree imbalance rank,
    so the two Klein-4 bits carry two independent structural readings of word-order.
    Returns: orient[i] in {0,1,2,3} (the (γ₅,iω₇) sector for vocab index i), plus the
    net-chirality cascade reading and per-token out/in flow for attestation.
    """
    n = len(vocab)
    vidx = {t: i for i, t in enumerate(vocab)}
    # forward directed counts as an edge multiset (Counter is edge-construction only, R-124 style)
    fwd = Counter()
    for toks in chunks_tokens:
        ind = [vidx[t] for t in toks if t in vidx]
        for i in range(len(ind)):
            for j in range(i + 1, min(i + k124.WINDOW, len(ind))):
                a, b = ind[i], ind[j]
                if a != b:
                    fwd[(a, b)] += 1                       # DIRECTED: a precedes b
    out_flow = np.zeros(n, dtype=np.float64)
    in_flow = np.zeros(n, dtype=np.float64)
    for (a, b), w in fwd.items():
        out_flow[a] += w
        in_flow[b] += w

    # γ₅ bit: net directed flow handedness per token, via cascade.net_chirality.
    # Per token, orientations[i] = sign(out-in) expressed as the Class-C net handedness of the
    # two-element cascade [+out_edges, -in_edges] reduced to its {+1,0,-1} orientation pair.
    gamma5 = np.zeros(n, dtype=np.uint8)
    iomega7 = np.zeros(n, dtype=np.uint8)
    per_token_orient = []
    # iω₇ axis: rank-parity of |directed imbalance| — a second, magnitude-ordered structural
    # reading (independent of the γ₅ sign axis). Magnitude via cascade.magnitude (Class K), so
    # no python abs() touches the cascade.
    from srmech.amsc.cascade import magnitude as casc_magnitude
    imbalance_mag = np.array([casc_magnitude(float(out_flow[i] - in_flow[i])) for i in range(n)])
    rank_order = np.argsort(np.argsort(imbalance_mag))      # 0..n-1 rank by imbalance magnitude
    for i in range(n):
        # Class-C orientations for this token's directed role: out-going (+1) vs in-coming (−1).
        # net_chirality of [+1, -1] = -1 (mixed) → resolve handedness by which dominates: encode
        # the dominant direction as a single-op cascade orientation, read via net_chirality.
        net_out = float(out_flow[i])
        net_in = float(in_flow[i])
        if net_out > net_in:
            orient = +1            # source / left-handed (predominantly precedes)
        elif net_in > net_out:
            orient = -1            # sink / right-handed (predominantly follows)
        else:
            orient = 0
        per_token_orient.append(orient)
        # net_chirality of the single-orientation cascade is that orientation (Class C identity);
        # we route γ₅ from its sign: +1/0 → γ₅=0, −1 → γ₅=1.
        h = net_chirality([orient]) if orient != 0 else 0
        gamma5[i] = 1 if h < 0 else 0
        iomega7[i] = int(rank_order[i]) & 1                # parity of imbalance-magnitude rank

    sector = (gamma5.astype(np.uint8) << 1) | iomega7.astype(np.uint8)   # 0..3
    # net-chirality cascade reading for the WHOLE text: Class-C handedness of all token orientations
    net_text_chirality = int(net_chirality([o for o in per_token_orient if o != 0]
                                           or [0]))
    return sector, per_token_orient, net_text_chirality, out_flow, in_flow


def so8_chirality_kernel(chunks_tokens):
    """SHIPPED so(8)/Klein-4 chirality storage signature (+ a NO-ROUTE control kernel).

    Each token → klein4_random vector, ROUTED into its directed-parity (γ₅,iω₇) sector via the
    Klein-4 group action klein4_bind(v, sector_anchor). Frequency-weighted bundle (klein4_bundle)
    → the text's so(8) chirality kernel K. Also returns an UNWEIGHTED routed kernel (weighting
    robustness) and a NO-ROUTE kernel (raw klein4 token-bundle, no chirality routing) — the
    control that isolates whether the directed-parity routing HELPS or HURTS the lexical-overlap
    signal F172 showed carries translation-invariance.

    Returns (K_weighted, K_unweighted, K_noroute, occupancy[4], net_text_chirality).
    """
    vocab, vidx, n = k124.build_vocab(chunks_tokens)
    sector, _orient, net_text_chirality, _of, _if = directed_orientations(chunks_tokens, vocab)

    # token frequencies (within the matched vocab) for frequency-weighted bundling
    freq = Counter(t for toks in chunks_tokens for t in toks if t in vidx)

    # constant-sector anchors (the 4 Klein-4 group elements) — fixed, deterministic
    anchors = [np.full(D_KLEIN4, s, dtype=np.uint8) for s in range(4)]

    routed, raw, weights = [], [], []
    for tok, i in vidx.items():
        v = _token_klein4(tok)
        s = int(sector[i])
        routed.append(klein4_bind(v, anchors[s]))   # Klein-4 group action: place content in sector s
        raw.append(v)                                # NO-ROUTE control: same content, no chirality routing
        weights.append(freq.get(tok, 0))

    # frequency-weighted bundle: replicate each routed vector ~proportional to sqrt(freq) (bounded
    # so a single high-freq token can't dominate), then klein4_bundle (per-bit majority vote).
    bundle_inputs = []
    if weights:
        wmax = max(weights) or 1
        for rv, w in zip(routed, weights):
            reps = 1 + int(round(3.0 * (w / wmax) ** 0.5))   # 1..4 reps, sublinear in freq
            bundle_inputs.extend([rv] * reps)
    if not bundle_inputs:
        bundle_inputs = routed or [klein4_random(D_KLEIN4, seed=0)]
    K_weighted = klein4_bundle(*bundle_inputs)
    K_unweighted = klein4_bundle(*(routed or [klein4_random(D_KLEIN4, seed=0)]))
    K_noroute = klein4_bundle(*(raw or [klein4_random(D_KLEIN4, seed=0)]))

    occ = np.array(klein4_sector_count(K_weighted), dtype=np.float64)
    occ_norm = occ / (occ.sum() + 1e-12)
    return K_weighted, K_unweighted, K_noroute, occ_norm, net_text_chirality


def occ_cos(a, b):
    """Descriptive cosine on the 4-vector bi-axial occupancy profile (same plain-dot readout
    R-134/R-135 use for the eigenspectrum cosine; edge/descriptive math, not a storage proxy)."""
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-12))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--catalog", type=Path, default=CATALOG)
    args = ap.parse_args()

    desc = load_descriptor(args.catalog)
    dh = descriptor_hash(args.catalog)
    lc = desc.fetch["literature_curated"]
    cache_dir = Path(lc["corpus"]["cache_dir"]).expanduser()
    budget = int(lc["confound_control"]["budget_tokens"])
    cc_seed = int(lc["confound_control"]["seed"])

    print(f"srmech v{SRMECH_VERSION}; HAS_NATIVE={HAS_NATIVE}; ABI={NATIVE_ABI_VERSION}")
    print(f"Catalog: {args.catalog.name}  hash={dh[:16]}...")
    print("R-136: SHIPPED so(8)/Klein-4 chirality storage signature vs F173 hand-built K1-chiral")
    print(f"  Klein-4 (ℤ₂)² = (γ₅ × iω₇); 4 sectors × 7 = 28 = dim so(8); D={D_KLEIN4}; "
          f"vocab={k124.VOCAB_SIZE} window={k124.WINDOW} seed={SEED}")
    print("  STRUCTURAL test on TEXT OBJECTS only; §VII.6.20; no doctrinal/clinical/ranking claims.\n")

    files = {
        "quran_yusuf": "quran_yusuf_ali.txt",      # PAIR member (same content)
        "quran_rodwell": "quran_rodwell.txt",      # PAIR member (same content)
        "kjv_ot": "kjv_old_testament.txt",
        "kjv_nt": "kjv_new_testament.txt",
        "bhagavad_gita": "bhagavad_gita.txt",
        "tao_legge": "tao_te_ching.txt",
        "dhammapada": "dhammapada.txt",
    }
    # tokenize + chunk; match token budget across all texts (length-control per F163/F169)
    chunks = {}
    for key, fn in files.items():
        body = k124.strip_gutenberg((cache_dir / fn).read_text(encoding="utf-8", errors="replace"))
        chunks[key] = [c for c in (k124.tokenize(c) for c in k124.chunk_text(body)) if c]
    budget = min(budget, min(sum(len(c) for c in v) for v in chunks.values()))
    chunks = {k: k124.trim_chunks_to_budget(v, budget) for k, v in chunks.items()}
    print(f"matched token budget = {budget}/text\n")

    # ---- build all signature families per text ----------------------------------------------
    so8_kernel, so8_unw, so8_noroute, occ, net_chir = {}, {}, {}, {}, {}
    flat_kernel, hand_chiral_kernel, hand_chiral_e = {}, {}, {}
    for key in files:
        ck = chunks[key]
        # SHIPPED so(8)/Klein-4 chirality signature (+ unweighted + no-route control)
        K, Kunw, Knoroute, occv, ntc = so8_chirality_kernel(ck)
        so8_kernel[key] = K
        so8_unw[key] = Kunw
        so8_noroute[key] = Knoroute
        occ[key] = occv
        net_chir[key] = ntc
        # BASELINES (recomputed live, not hard-coded): F134 flat eigen-bundle + F135 hand-built chiral
        kf, vocab = k124.build_K1_flat(ck)
        flat_kernel[key] = kf
        kc, ce = k124.build_K1_chiral(ck, vocab)
        hand_chiral_kernel[key] = kc
        hand_chiral_e[key] = ce
        print(f"  {key:14s} occupancy(++,+-,-+,--)=[{occv[0]:.3f} {occv[1]:.3f} "
              f"{occv[2]:.3f} {occv[3]:.3f}]  net_chirality={ntc:+d}  hand_chiral_E={ce:.3f}")
    print()

    pair = ("quran_yusuf", "quran_rodwell")
    distinct = ["quran_yusuf", "kjv_ot", "kjv_nt", "bhagavad_gita", "tao_legge", "dhammapada"]

    def within_across(simfn):
        w = simfn(pair[0], pair[1])
        prs = list(itertools.combinations(distinct, 2))
        a = [simfn(x, y) for x, y in prs]
        amax_i = int(np.argmax(a))
        return w, float(np.mean(a)), float(max(a)), a, prs[amax_i]

    # (S1) bi-axial occupancy profile cosine
    s1_w, s1_am, s1_ax, s1_a, s1_max = within_across(lambda x, y: occ_cos(occ[x], occ[y]))
    # (S2) so(8) chirality kernel klein4_similarity (the head-to-head vs hand-built K1-chiral)
    s2_w, s2_am, s2_ax, s2_a, s2_max = within_across(
        lambda x, y: float(klein4_similarity(so8_kernel[x], so8_kernel[y])))
    # (S2u) robustness: unweighted routed kernel (drop the sqrt-freq replication)
    s2u_w, s2u_am, s2u_ax, _s2u_a, _s2u_max = within_across(
        lambda x, y: float(klein4_similarity(so8_unw[x], so8_unw[y])))
    # (CTRL) NO-ROUTE control: raw klein4 token-bundle, NO chirality routing — isolates whether
    # the directed-parity routing helps or HURTS the lexical-overlap signal (F172's invariance carrier)
    ctrl_w, ctrl_am, ctrl_ax, _ctrl_a, _ctrl_max = within_across(
        lambda x, y: float(klein4_similarity(so8_noroute[x], so8_noroute[y])))
    # BASELINE F134 flat eigen-bundle
    fb_w, fb_am, fb_ax, fb_a, fb_max = within_across(
        lambda x, y: float(k124.similarity(flat_kernel[x], flat_kernel[y])))
    # BASELINE F135 hand-built K1-chiral
    hc_w, hc_am, hc_ax, hc_a, hc_max = within_across(
        lambda x, y: float(k124.similarity(hand_chiral_kernel[x], hand_chiral_kernel[y])))

    print(f"  across-MAX driven by:  (S1 occupancy) {s1_max}   (S2 so8-kernel) {s2_max}")
    print(f"                         (flat-bundle)  {fb_max}   (hand-chiral)   {hc_max}\n")

    print(f"{'signature':>38} | {'within':>7} | {'across-mean':>11} | {'across-max':>10} | ratio | beats-max?")
    print("-" * 100)

    def row(name, w, am, ax):
        print(f"{name:>38} | {w:>7.4f} | {am:>11.4f} | {ax:>10.4f} | "
              f"{(w/am if am else 0):>4.2f}x | {w > ax}")

    row("(S1) SHIPPED bi-axial occupancy", s1_w, s1_am, s1_ax)
    row("(S2) SHIPPED so(8) chirality kernel", s2_w, s2_am, s2_ax)
    row("(S2u) so(8) kernel, unweighted", s2u_w, s2u_am, s2u_ax)
    row("(CTRL) klein4 bundle, NO routing", ctrl_w, ctrl_am, ctrl_ax)
    print("-" * 100)
    row("[base F134] flat eigen-bundle", fb_w, fb_am, fb_ax)
    row("[base F135] hand-built K1-chiral", hc_w, hc_am, hc_ax)
    print(f"\n  klein4 random-orthogonal floor = 0.2500 (4 sectors); CTRL vs S2 shows routing's effect"
          f"\n  on the lexical-overlap signal: routing within {s2_w:.4f} vs no-route within {ctrl_w:.4f} "
          f"({'routing HURTS' if s2_w < ctrl_w else 'routing helps'})")

    # net-chirality handedness across pair vs set (descriptive)
    pair_match = net_chir[pair[0]] == net_chir[pair[1]]
    print(f"\n  (S3) net_chirality handedness: " +
          ", ".join(f"{k.split('_')[0]}={net_chir[k]:+d}" for k in files))
    print(f"       pair handedness match (Yusuf vs Rodwell): {pair_match}")

    # ---- attestation + NDJSON ----------------------------------------------------------------
    attest = {"descriptor_hash": dh, "source_key": desc.source["key"],
              "srmech_version": SRMECH_VERSION, "abi_version": NATIVE_ABI_VERSION,
              "has_native": HAS_NATIVE, "budget_tokens": budget, "seed": SEED,
              "confound_control_seed": cc_seed, "klein4_D": D_KLEIN4,
              "vocab_size": k124.VOCAB_SIZE, "window": k124.WINDOW,
              "chirality_ops": "srmech.amsc.hdc.klein4_* (so(8)/Spin(8)-triality, SHIPPED) "
                               "+ srmech.amsc.cascade.net_chirality (Class C)",
              "scope": "STRUCTURAL; text objects; §VII.6.20; no clinical/doctrinal claims"}

    rec_main = {**attest, "phase": "P1_so8_chirality_isolation", "pair_id": "quran",
                "s1_occupancy_within": s1_w, "s1_occupancy_across_mean": s1_am,
                "s1_occupancy_across_max": s1_ax, "s1_beats_max": bool(s1_w > s1_ax),
                "s1_across_max_pair": list(s1_max),
                "s2_so8_kernel_within": s2_w, "s2_so8_kernel_across_mean": s2_am,
                "s2_so8_kernel_across_max": s2_ax, "s2_beats_max": bool(s2_w > s2_ax),
                "s2_across_max_pair": list(s2_max), "s2_across": s2_a,
                "s2u_unweighted_within": s2u_w, "s2u_unweighted_across_mean": s2u_am,
                "s2u_unweighted_across_max": s2u_ax, "s2u_beats_max": bool(s2u_w > s2u_ax),
                "ctrl_noroute_within": ctrl_w, "ctrl_noroute_across_mean": ctrl_am,
                "ctrl_noroute_across_max": ctrl_ax, "ctrl_beats_max": bool(ctrl_w > ctrl_ax),
                "klein4_random_floor": 0.25, "routing_hurts_lexical_signal": bool(s2_w < ctrl_w),
                "baseline_flat_within": fb_w, "baseline_flat_across_mean": fb_am,
                "baseline_flat_across_max": fb_ax, "baseline_flat_beats_max": bool(fb_w > fb_ax),
                "baseline_hand_chiral_within": hc_w, "baseline_hand_chiral_across_mean": hc_am,
                "baseline_hand_chiral_across_max": hc_ax,
                "baseline_hand_chiral_beats_max": bool(hc_w > hc_ax),
                "net_chirality": {k: net_chir[k] for k in files},
                "net_chirality_pair_match": bool(pair_match),
                "hand_chiral_energy": hand_chiral_e}
    records = [rec_main]
    for k in files:
        records.append({**attest, "phase": "P2_per_text", "text_key": k,
                        "occupancy_gamma5pp_iomega7pp": occ[k].tolist(),
                        "net_chirality": net_chir[k]})

    out = args.catalog.parent / "substrate_measurements" / "so8_chirality_storage_signature.ndjson"
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w") as f:
        for r in records:
            f.write(json.dumps(r, default=str) + "\n")
    print(f"\nResults: {out}  ({len(records)} records)")

    # ---- verdict -----------------------------------------------------------------------------
    print("\n" + "=" * 100)
    print("R-136 READING — does the SHIPPED so(8) chirality surface ISOLATE content-specific,")
    print("translation-invariant storage BETTER than F173's hand-built K1-chiral?")
    print("=" * 100)
    for name, w, am, ax in (("(S1) SHIPPED bi-axial occupancy", s1_w, s1_am, s1_ax),
                            ("(S2) SHIPPED so(8) chirality kernel", s2_w, s2_am, s2_ax)):
        verdict = ("ISOLATES (within ABOVE across-max)" if w > ax
                   else "partial (within > mean, not max)" if w > am
                   else "no isolation (within ≤ mean)")
        print(f"  {name:>38}: within {w:.4f} vs across-max {ax:.4f} ({(w/am if am else 0):.2f}x) → {verdict}")
    print(f"\n  Comparison bars (recomputed live this run):")
    print(f"    F134 flat eigen-bundle : within {fb_w:.4f}, across-max {fb_ax:.4f}, "
          f"{(fb_w/fb_am if fb_am else 0):.2f}x, beats-max={fb_w>fb_ax}")
    print(f"    F135 hand-built chiral : within {hc_w:.4f}, across-max {hc_ax:.4f}, "
          f"{(hc_w/hc_am if hc_am else 0):.2f}x, beats-max={hc_w>hc_ax}")
    best_ship_ratio = max((s2_w / s2_am if s2_am else 0), (s1_w / s1_am if s1_am else 0))
    flat_ratio = fb_w / fb_am if fb_am else 0
    print(f"\n  n=1 same-content pair — a single datapoint, not a law. Null counts: if no shipped")
    print(f"  signature exceeds the F134 flat-bundle ratio ({flat_ratio:.2f}x), the shipped so(8)")
    print(f"  surface gives no advantage over lexical storage (same conclusion as F173).")


if __name__ == "__main__":
    main()
