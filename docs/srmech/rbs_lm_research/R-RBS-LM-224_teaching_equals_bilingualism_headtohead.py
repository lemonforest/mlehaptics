"""R-RBS-LM-224 — DECISIVE head-to-head: is "teaching" the SAME cascade as
"bilingualism" on the ADDRESSING side? (The #760 forward-asks #1 + #2 combined.)

THE CONJECTURE (R-RBS-LM-54 Rosetta cross-encoding-projection cascade):
  teaching ≡ bilingualism — both "hold one content in two encodings, project
  across via a Class-C which-way selector + an anchor bound into the query
  (Class M)." ONLY the anchor's AXIS differs:
    • BILINGUAL : two encodings = two LANGUAGES; anchor = which-LANGUAGE label
                  = a DOMAIN axis (F165 labeled-store). EMPIRICALLY WORKS —
                  the F165 domain anchor orthogonalizes + persists to N=8192
                  (+0.388, F222).
    • TEACHING  : two encodings = two DEPTH-REGISTERS (expert ↔ learner) over
                  the F168 sector ladder; anchor = which-DEPTH operator = the
                  RECIPIENT/ELI5 axis (F212). EMPIRICALLY NULL SO FAR — F221
                  built it as an XOR-twist of the probe → tier-1 render-only
                  null (0/3); F221 §4 showed the null was PARTLY anchor (the
                  XOR-bind disperses the bias across the bundle) and PARTLY
                  meter (the F168 sector-occupancy readout was pinned at the
                  ~0.25 Klein-4 chance floor with near-zero dynamic range).

THE DECISIVE TEST (the falsifiable prediction):
  IF teaching ≡ bilingualism (same cascade, anchor on a different axis), THEN
  building the depth-anchor the SAME WAY the working DOMAIN/language anchor is
  built — a labeled-store key bound into retrieval, read as a Tier-2 similarity
  RE-WEIGHTING (F119/F120 two-tier; the Class-K bridge), NOT an XOR-twist of the
  probe — AND reading it with a meter that has REAL DYNAMIC RANGE — should make
  the DEPTH axis steer/separate retrieval LIKE THE LANGUAGE axis does.

THREE CONDITIONS, identical testbed (same KJV-NT corpus, same fixed held-out
queries, same shape-matched random-orientation noise floor / p90 gate as F221).
The ONLY difference across conditions is HOW the depth anchor is built / read:
  (A) DOMAIN/language anchor — F165/F146-style labeled-store key bound into the
      retrieval key the WORKING way: key = klein4_bind(ctx_state, enc("__band_{B}__")).
      The depth-band identity is carried as a DOMAIN label on the F165 axis (the
      "which-language" surface, here re-pointed at the depth bands). KNOWN-WORKING
      binding mechanism.
  (B) RECIPIENT depth XOR-twist — F221-style: depth-band BUNDLE of
      encode_word_k4(sector=s) tags, klein4_bind-ed INTO the probe (the QUERY).
      The KNOWN-NULL baseline (F221).
  (C) NEW — RECIPIENT depth as a read-side Tier-2 RE-WEIGHTING — the depth-band
      labeled key (built like (A)) is applied at SCORING time as a Class-K Tier-2
      bridge: candidate similarity is re-weighted by depth-band match
      (sim(depth_key ⊕ ctx, cand)), NOT mixed into the Tier-1 probe. This is
      F221 §8 / #760 forward-ask #2 (the read-side Tier-2 anchor per F120),
      built the way (A) is built, NOT an XOR twist of the probe.

THE READOUT (replaces F221's saturated argmax-into-4-sectors recovery; this is
#760 forward-ask #1 — a readout with REAL DYNAMIC RANGE):
  a band-conditioned RANKING-SEPARATION meter, gated the FAIR way. NOTE (the
  F214 §4 / F221 §3 construction-artifact, re-encountered + corrected): a raw
  shallow-vs-deep rank divergence SATURATES near the two-independent-random-
  orientation ceiling for the (A) labeled-key and (B) XOR-twist mechanisms (both
  bind distinct orientations into the probe → near-orthogonal rankings regardless
  of depth meaning), so a FREE-random-orientation floor is unbeatable by ANY anchor
  incl. the KNOWN-WORKING one and is the wrong gate. The FAIR meter (the same
  isolation F222 used for the DOMAIN anchor — structured label vs random label
  UNDER THE IDENTICAL MECHANISM): per query, take the un-conditioned Tier-1 baseline
  ranking (context→candidate similarity, no band), then measure how differently the
  SHALLOW band and the DEEP band DISPLACE that baseline:
      separation = | rankdisp(shallow, baseline) - rankdisp(deep, baseline) |
  (rankdisp = (1 - Spearman rho)/2, sign-free via cascade.magnitude — never abs()).
  A depth axis that STEERS makes shallow and deep move the baseline by DIFFERENT
  amounts (separation large); a render-only axis moves both the same (separation ~
  a random label's). The gate: each condition's structured separation vs the p90 of
  the separation produced by RANDOM LABELS bound by THAT condition's OWN mechanism.

  HEAD-TO-HEAD verdict: does (C) behave like (A) [its separation clears ITS p90 floor
  → teaching ≡ bilingual on the addressing side] or like (B) [stays at ITS floor →
  depth is genuinely not language-like]?

PRE-STATED OUTCOMES (per [[feedback_dont_pre_commit_spike_query_operators]] —
NULLS COUNT; the test is NOT leaned toward the positive; A/B/C are maximally
fair — identical corpus/queries/readout/floor; the ONLY difference is how the
anchor is built/read):
  • NULL: "(C) the Tier-2 depth re-weighting stays at the noise floor / does NOT
    separate shallow-vs-deep rankings beyond what (B) did → teaching ≠ bilingual
    on the addressing side; the depth axis is genuinely render-only, not
    language-like." (A clean null is a real result — it would mean depth is
    genuinely NOT a language-like axis, refining the conjecture.)
  • POSITIVE: "(C) separates shallow-vs-deep rankings / steers retrieval beyond
    the floor, behaving like (A) the DOMAIN/language axis → CONFIRMS teaching ≡
    bilingual on the addressing side; resolves #760 forward-ask #2."

srmech-native (CLAUDE.md §2 STOP-list honored):
  • hdc.{klein4_bind, klein4_bundle, klein4_random}    — anchor build / orientation (Class M / C)
  • encode_word_k4(sector=s)                            — the F168 sector tagging (Class M ∘ I)
  • ContextSubstrate.{enc, encode_context, bundle_odd}  — the F166 rolling state (R-126)
  • cs.sim_k4_batch                                     — Class-M similarity (NEVER hand-rolled cosine)
  • cascade.magnitude                                   — sign-free rank-displacement (NEVER python abs())
  • Counter ONLY for bigram EDGE STRUCTURE (the R-127/R-131 candidate store), never as a storage proxy.
Catalog-driven (descriptor_religious_texts.toml [recipient_tier2]); srmech 0.5.0
native ABI=3; deterministic / bit-exact. STRUCTURAL-only per §VII.6.20 (texts +
languages are structural test-objects; NO clinical / cognitive / BCI claim).
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
from srmech.amsc._native import HAS_NATIVE, NATIVE_ABI_VERSION
from srmech import __version__ as SRMECH_VERSION

CATALOG = HERE.parent / "catalogs" / "rbs_lm_substrate" / "descriptor_religious_texts.toml"
MAX_TOKENS = 80000


# ---------------------------------------------------------------------------
# The depth-band anchor builds (the three conditions share the SAME band defs)
# ---------------------------------------------------------------------------

def depth_band_bundle(ctxsub, band, n_tags):
    """F221-style depth-band BUNDLE: klein4 bundle of encode_word_k4 depth-TAG
    vectors over a target F168 sector band. Used as the XOR-twist anchor (B) and,
    in conditions (A)/(C), as the depth-band labeled KEY's content. n_tags is odd
    (klein4_bundle majority tie-break via ContextSubstrate.bundle_odd).

    Deterministic: tag tokens are band-derived, so the bundle is bit-exact."""
    tags = []
    for t in range(n_tags):
        s = int(band[t % len(band)])
        tok = f"__depth_tag_{'_'.join(map(str, band))}_{t}__"
        tags.append(cs.encode_word_k4(tok, D=ctxsub.D, sector=s, hex_chars=ctxsub.hex_chars))
    return ctxsub.bundle_odd(tags)


def band_label_key(ctxsub, band_name):
    """The F165/F146 labeled-store DOMAIN key for a depth band: ctx.enc('__band_{B}__').
    This is EXACTLY the F146 HierarchicalMemory._dom_vec mechanism (Class A
    content-mint of a label), here labeling a depth band rather than a structural
    family. Conditions (A) and (C) carry the depth axis as THIS label (the working
    DOMAIN-anchor surface), NOT as an XOR twist of the probe."""
    return ctxsub.enc(f"__band_{band_name}__")


# ---------------------------------------------------------------------------
# Per-query candidate RANKINGS under shallow / deep conditioning, per condition
# ---------------------------------------------------------------------------

# Each ranking fn takes (ctx_state, cand_vecs, base_sims, base_order) and returns the
# band-conditioned candidate ORDER (best first). base_sims/base_order are the
# un-conditioned Tier-1 ranking, shared so every mechanism is measured against the
# SAME no-band baseline (the fair-separation readout).

def ranking_domain_key(ctxsub, ctx_state, cand_vecs, base_sims, base_order, band_key):
    """(A) DOMAIN/language anchor: the F165/F146 binding — the band label is bound
    INTO the retrieval key (key = klein4_bind(ctx_state, band_key)); candidates are
    ranked by Class-M similarity to that key. The WORKING binding mechanism
    (F222: persists to N=8192, +0.388)."""
    key = hdc.klein4_bind(ctx_state, band_key)            # Class M (the F146 _key)
    sims = cs.sim_k4_batch(key, cand_vecs)
    return np.argsort(-sims)


def ranking_xor_twist(ctxsub, ctx_state, cand_vecs, base_sims, base_order, band_bundle):
    """(B) RECIPIENT depth XOR-twist (F221): the depth-band BUNDLE is klein4_bind-ed
    INTO the probe (the QUERY/hidden-state), then candidates ranked by similarity to
    that twisted probe. The KNOWN-NULL operationalization."""
    probe = hdc.klein4_bind(ctx_state, band_bundle)       # the F221 XOR twist
    sims = cs.sim_k4_batch(probe, cand_vecs)
    return np.argsort(-sims)


def ranking_tier2_reweight(ctxsub, ctx_state, cand_vecs, base_sims, base_order,
                           band_key, alpha):
    """(C) NEW — RECIPIENT depth as a read-side Tier-2 RE-WEIGHTING (F119/F120;
    Class-K bridge). The depth-band labeled key (built like (A)) is NOT mixed into
    the Tier-1 probe; it conditions the SCORING. Tier-1 score = base_sims (the
    un-conditioned context→candidate similarity). Tier-2 weight = the depth-band
    match: how well the band-keyed query (klein4_bind(ctx_state, band_key)) matches
    each candidate. The Class-K bridge composes them additively:
        score(c) = (1-alpha)*base_sims(c) + alpha*depth_match(c)
    so the depth band RE-WEIGHTS the candidate similarity at retrieval time (F221
    §8 / #760 forward-ask #2 — the anchor conditions the scoring, not the probe)."""
    key = hdc.klein4_bind(ctx_state, band_key)            # the SAME key as (A)
    depth_match = cs.sim_k4_batch(key, cand_vecs)         # Tier-2 depth-band match
    score = (1.0 - alpha) * base_sims + alpha * depth_match  # Class-K Tier-1↔Tier-2 bridge
    return np.argsort(-score)


# ---------------------------------------------------------------------------
# The RANKING-DISPLACEMENT readout (real dynamic range; sign-free)
# ---------------------------------------------------------------------------
#
# WHY a shallow-vs-deep divergence ALONE is not the meter (the F214 §4 / F221 §3
# construction-artifact, re-encountered + corrected here): binding two DISTINCT
# orientations into a probe (the (A) labeled-key and (B) XOR-twist mechanisms both
# do this) drives the two rankings toward near-orthogonality, so shallow-vs-deep
# divergence SATURATES near the two-independent-random-orientation ceiling (~0.5,
# Spearman rho ~ 0) REGARDLESS of whether the bands carry depth meaning. A free-
# random-orientation floor is therefore unbeatable by ANY anchor (incl. the
# KNOWN-WORKING one), so "beyond the free-random floor" is the wrong gate.
#
# THE FAIR GATE (the same isolation F222 used for the DOMAIN anchor: structured
# label vs random label UNDER THE IDENTICAL MECHANISM): for each condition we
# compare the DEPTH-band re-ranking to a RANDOM-label re-ranking built + applied by
# THAT condition's OWN binding. The quantity is the displacement of the band-
# conditioned ranking FROM THE UN-CONDITIONED Tier-1 baseline ranking — "how far
# does adding this band move retrieval from the no-band ranking." A language-like
# axis (the F165 DOMAIN surface) re-ranks STRUCTURALLY: the depth band displaces the
# baseline DIFFERENTLY from a random label of the same construction (the structured
# displacement separates from the random-label displacement). A render-only axis:
# the depth band displaces the baseline NO differently from a random label. The gate
# is whether the SHALLOW-vs-DEEP structured separation (how differently shallow vs
# deep move the baseline) exceeds the p90 of the RANDOM-label-pair separation under
# the matched mechanism. This is interpretable AND has real dynamic range.

def rank_displacement(order_a: np.ndarray, order_b: np.ndarray) -> float:
    """Normalized rank-displacement between two rankings of the SAME candidate set:
    1 - Spearman rank-correlation, scaled to [0,1] (0 = identical ranking, 1 =
    perfectly reversed). Real dynamic range (the F221 §8 forward-ask #1 — replaces
    the argmax-into-4-sectors recovery pinned at the Klein-4 floor). Sign-free via
    cascade.magnitude — never python abs() inside the cascade (CLAUDE.md §2).

    rank_a[i] = position of candidate i in order_a. The squared-rank-difference sum
    is the Spearman numerator; 1 - rho maps to [0,2], /2 to [0,1]."""
    n = len(order_a)
    if n < 2:
        return 0.0
    rank_a = np.empty(n, dtype=float)
    rank_b = np.empty(n, dtype=float)
    rank_a[order_a] = np.arange(n, dtype=float)
    rank_b[order_b] = np.arange(n, dtype=float)
    d2 = 0.0
    for i in range(n):
        d = cascade.magnitude(float(rank_a[i] - rank_b[i]))   # Class-K |.|, never abs()
        d2 += d * d
    rho = 1.0 - (6.0 * d2) / (n * (n * n - 1.0))              # Spearman rho
    return float((1.0 - rho) / 2.0)                          # → [0,1]


def band_separation(ctxsub, queries, cand_cache, vocab_vecs, vocab_idx,
                    rank_fn_shallow, rank_fn_deep):
    """The condition's STRUCTURED shallow-vs-deep SEPARATION, measured the fair way:
    per query, take the UN-CONDITIONED Tier-1 baseline ranking (context→candidate
    similarity, no band), then the shallow-band ranking and the deep-band ranking
    under this condition's mechanism. The SEPARATION is how DIFFERENTLY shallow vs
    deep displace the baseline:
        sep = | displacement(shallow, baseline) - displacement(deep, baseline) |
    PLUS the direct shallow-vs-deep divergence (secondary). A depth axis that STEERS
    makes shallow and deep move the baseline by DIFFERENT amounts / directions (sep
    large); a render-only axis moves both the same way (sep ~ 0, indistinguishable
    from a random label). rank_fn_* take (ctx_state, cand_vecs, base_sims, base_order)
    and return the band-conditioned candidate order. Returns (mean_separation,
    mean_shallow_deep_divergence, mean_top1_disagree)."""
    seps, divs, t1 = [], [], []
    for window, _true_tok in queries:
        last = window[-1]
        candidates = cand_cache[last]
        cand_idx = [vocab_idx[c] for c in candidates]
        cand_vecs = vocab_vecs[cand_idx]
        ctx_state = ctxsub.encode_context(list(window))
        base_sims = cs.sim_k4_batch(ctx_state, cand_vecs)          # Tier-1 baseline
        base_order = np.argsort(-base_sims)
        order_s = rank_fn_shallow(ctx_state, cand_vecs, base_sims, base_order)
        order_d = rank_fn_deep(ctx_state, cand_vecs, base_sims, base_order)
        disp_s = rank_displacement(order_s, base_order)            # shallow moves baseline by..
        disp_d = rank_displacement(order_d, base_order)            # deep moves baseline by..
        seps.append(cascade.magnitude(disp_s - disp_d))           # Class-K |.|, never abs()
        divs.append(rank_displacement(order_s, order_d))          # direct shallow-vs-deep
        t1.append(1.0 if int(order_s[0]) != int(order_d[0]) else 0.0)
    return (float(np.mean(seps)) if seps else 0.0,
            float(np.mean(divs)) if divs else 0.0,
            float(np.mean(t1)) if t1 else 0.0)


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
    rt = lc["recipient_tier2"]
    demo_key = str(rt["demo_text"])
    n_units = int(rt["n_units"])
    n_queries = int(rt["n_queries"])
    window = int(rt["window"])
    min_cand = int(rt["min_candidates"])
    n_random = int(rt["n_random"])
    noise_pct = float(rt["noise_percentile"])
    n_tags = int(rt["n_anchor_tags"])
    alpha = float(rt["tier2_alpha"])
    shallow_band = [int(x) for x in rt["shallow_band"]]
    deep_band = [int(x) for x in rt["deep_band"]]
    seed = int(rt["seed"])

    print(f"srmech v{SRMECH_VERSION}; HAS_NATIVE={HAS_NATIVE}; ABI={NATIVE_ABI_VERSION}; D={D}")
    print(f"Catalog: {args.catalog.name}  hash={dh[:16]}...")
    print(f"demo_text={demo_key}  window={window}  n_queries={n_queries}  "
          f"n_random={n_random}  noise_pct={noise_pct}  sectors={sector_count}")
    print(f"DEPTH BANDS — shallow={shallow_band}  deep={deep_band}  n_anchor_tags={n_tags}  "
          f"tier2_alpha={alpha}\n")
    print("F224 DECISIVE head-to-head — is TEACHING the SAME cascade as BILINGUALISM")
    print("on the ADDRESSING side? Build the depth anchor 3 ways; read with a band-conditioned")
    print("RANKING-SEPARATION meter (real dynamic range, #760 ask #1) gated against EACH")
    print("condition's OWN matched-mechanism random-label floor (the fair F222-style isolation):")
    print("  (A) DOMAIN/language labeled-store key bound into the key (KNOWN-WORKING, F165/F222)")
    print("  (B) RECIPIENT depth XOR-twist of the probe       (KNOWN-NULL, F221)")
    print("  (C) RECIPIENT depth as read-side Tier-2 re-weight (NEW; #760 ask #2, F120 Class-K)")
    print("PRE-STATED NULL: (C) stays at its floor like (B) => teaching != bilingual on addressing.")
    print("PRE-STATED POS : (C) clears its floor like (A) => CONFIRMS teaching == bilingual on addressing.")
    print("STRUCTURAL-ONLY per §VII.6.20: texts + languages are test-objects; no cognitive/doctrinal claim.\n")

    # --- corpus -> token stream -> bigram store (the stored relationships) ---
    meta = texts[demo_key]
    body = k1mod.strip_gutenberg(
        (cache_dir / meta["filename"]).read_text(encoding="utf-8", errors="replace"))
    stream = k1mod.tokenize(body)[:MAX_TOKENS]
    bigram = defaultdict(Counter)       # Counter = bigram EDGE STRUCTURE (R-127/R-131), not a proxy
    for a, b in zip(stream, stream[1:]):
        bigram[a][b] += 1
    cand_cache = {a: sorted(c.keys()) for a, c in bigram.items()}
    vocab = sorted(set(stream))
    ctxsub = cs.ContextSubstrate(D=D, hex_chars=hexc)
    vocab_vecs = np.stack([ctxsub.enc(w) for w in vocab])
    vocab_idx = {w: i for i, w in enumerate(vocab)}
    print(f"{meta['label']}: {len(stream)} tokens, {len(vocab)} unique; "
          f"{len(cand_cache)} predecessors in the bigram store\n")

    # --- FIXED query set (IDENTICAL construction to F214/F221) ---
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

    # --- the depth-band anchors (shared shallow/deep defs across conditions) ---
    bundle_shallow = depth_band_bundle(ctxsub, shallow_band, n_tags)   # (B) XOR content
    bundle_deep = depth_band_bundle(ctxsub, deep_band, n_tags)
    key_shallow = band_label_key(ctxsub, "shallow")                    # (A)/(C) labeled key
    key_deep = band_label_key(ctxsub, "deep")

    # non-degeneracy diagnostic: the shallow/deep anchors must be DISTINCT, else a
    # null is "anchors collapsed", not "axis doesn't steer".
    bundle_sim = float(cs.sim_k4_batch(bundle_shallow, bundle_deep[None, :])[0])
    key_sim = float(cs.sim_k4_batch(key_shallow, key_deep[None, :])[0])
    print(f"ANCHOR non-degeneracy (should be < 1.0 — distinct shallow vs deep):")
    print(f"  XOR-bundle shallow~deep = {bundle_sim:.3f}   labeled-key shallow~deep = {key_sim:.3f}\n")

    # ---- each condition: STRUCTURED shallow-vs-deep separation + its OWN matched-
    # ---- mechanism RANDOM-LABEL floor (the fair F222-style isolation) ----
    # The gate for a condition is whether its DEPTH-band shallow-vs-deep SEPARATION
    # (how differently shallow vs deep displace the Tier-1 baseline) exceeds the p90
    # of the separation produced by RANDOM LABELS bound by the SAME mechanism. So we
    # ask, per condition: "does the depth STRUCTURE re-rank more than a meaningless
    # label does, under this exact binding?" — the same way F222 isolated the DOMAIN
    # anchor (structured family label vs no/other label, identical hierarchical op).
    # n_random random-label pairs per condition give that condition's floor.

    def random_labels(prefix, r):
        """Two random label vectors (shallow/deep surrogates) for the labeled-key
        mechanisms (A)/(C) — a random DOMAIN label bound the F165 way."""
        ls = ctxsub.enc(f"__rand_{prefix}_s_{r}__")
        ld = ctxsub.enc(f"__rand_{prefix}_d_{r}__")
        return ls, ld

    def random_bundles(r):
        """Two random orientation vectors for the XOR-twist mechanism (B) — the
        SAME random-orientation kind F221/F214 used as its control."""
        bs = hdc.klein4_random(D, np.random.default_rng(seed + 3000 + 2 * r))
        bd = hdc.klein4_random(D, np.random.default_rng(seed + 3000 + 2 * r + 1))
        return bs, bd

    # (A) DOMAIN/language labeled-store key (KNOWN-WORKING)
    A_sep, A_div, A_t1 = band_separation(
        ctxsub, queries, cand_cache, vocab_vecs, vocab_idx,
        lambda c, cv, bs, bo: ranking_domain_key(ctxsub, c, cv, bs, bo, key_shallow),
        lambda c, cv, bs, bo: ranking_domain_key(ctxsub, c, cv, bs, bo, key_deep))
    A_floor = []
    for r in range(n_random):
        ls, ld = random_labels("A", r)
        s, _, _ = band_separation(
            ctxsub, queries, cand_cache, vocab_vecs, vocab_idx,
            (lambda lv: lambda c, cv, bs, bo: ranking_domain_key(ctxsub, c, cv, bs, bo, lv))(ls),
            (lambda lv: lambda c, cv, bs, bo: ranking_domain_key(ctxsub, c, cv, bs, bo, lv))(ld))
        A_floor.append(s)

    # (B) RECIPIENT depth XOR-twist (KNOWN-NULL, F221)
    B_sep, B_div, B_t1 = band_separation(
        ctxsub, queries, cand_cache, vocab_vecs, vocab_idx,
        lambda c, cv, bs, bo: ranking_xor_twist(ctxsub, c, cv, bs, bo, bundle_shallow),
        lambda c, cv, bs, bo: ranking_xor_twist(ctxsub, c, cv, bs, bo, bundle_deep))
    B_floor = []
    for r in range(n_random):
        bs_v, bd_v = random_bundles(r)
        s, _, _ = band_separation(
            ctxsub, queries, cand_cache, vocab_vecs, vocab_idx,
            (lambda ov: lambda c, cv, bs, bo: ranking_xor_twist(ctxsub, c, cv, bs, bo, ov))(bs_v),
            (lambda ov: lambda c, cv, bs, bo: ranking_xor_twist(ctxsub, c, cv, bs, bo, ov))(bd_v))
        B_floor.append(s)

    # (C) NEW — RECIPIENT depth as read-side Tier-2 RE-WEIGHTING (#760 ask #2)
    C_sep, C_div, C_t1 = band_separation(
        ctxsub, queries, cand_cache, vocab_vecs, vocab_idx,
        lambda c, cv, bs, bo: ranking_tier2_reweight(ctxsub, c, cv, bs, bo, key_shallow, alpha),
        lambda c, cv, bs, bo: ranking_tier2_reweight(ctxsub, c, cv, bs, bo, key_deep, alpha))
    C_floor = []
    for r in range(n_random):
        ls, ld = random_labels("C", r)
        s, _, _ = band_separation(
            ctxsub, queries, cand_cache, vocab_vecs, vocab_idx,
            (lambda lv: lambda c, cv, bs, bo: ranking_tier2_reweight(ctxsub, c, cv, bs, bo, lv, alpha))(ls),
            (lambda lv: lambda c, cv, bs, bo: ranking_tier2_reweight(ctxsub, c, cv, bs, bo, lv, alpha))(ld))
        C_floor.append(s)

    def gate(sep, floor):
        pct = percentile_of(sep, floor)
        p90 = float(np.quantile(floor, noise_pct)) if floor else 0.0
        beyond = pct >= noise_pct and sep > p90 + 1e-12
        return pct, p90, bool(beyond)

    A_pct, A_p90, A_beyond = gate(A_sep, A_floor)
    B_pct, B_p90, B_beyond = gate(B_sep, B_floor)
    C_pct, C_p90, C_beyond = gate(C_sep, C_floor)

    print("DEPTH-band STRUCTURED shallow-vs-deep SEPARATION vs each condition's OWN")
    print("matched-mechanism RANDOM-LABEL floor (the fair F222-style isolation; p90 gate).")
    print("SEPARATION = | how-much-shallow-moves-baseline - how-much-deep-moves-baseline |;")
    print("a depth axis that STEERS separates shallow from deep beyond a random label of the same kind.")
    print(f"{'condition':>52} | {'sep':>7} | {'rand_p90':>8} | {'pctile':>6} | {'s~d div':>7} | beyond?")
    print("-" * 104)
    rows = [
        ("(A) DOMAIN/language labeled-store key [WORKING]", A_sep, A_p90, A_pct, A_div, A_beyond),
        ("(B) RECIPIENT depth XOR-twist of probe [NULL,F221]", B_sep, B_p90, B_pct, B_div, B_beyond),
        ("(C) RECIPIENT depth Tier-2 re-weight [NEW,#760-2]", C_sep, C_p90, C_pct, C_div, C_beyond),
    ]
    for name, sep, p90, pct, div, beyond in rows:
        print(f"{name:>52} | {sep:>7.4f} | {p90:>8.4f} | {pct:>6.2f} | {div:>7.4f} | "
              f"{'YES (>p90)' if beyond else 'no'}")

    # ---- HEAD-TO-HEAD: does (C) behave like (A) or like (B)? ----
    # A is the known-working axis (clears its floor => the labeled-store binding DOES
    # carry a structured re-ranking the language axis exploits); B is the known-null
    # axis (stays at its floor). C confirms teaching==bilingual iff it clears its
    # floor like A; teaching!=bilingual iff it stays at its floor like B.
    if C_beyond and A_beyond:
        verdict = ("CONFIRMED — (C) the Tier-2 depth re-weight CLEARS its matched-mechanism floor like (A) "
                   "the DOMAIN/language axis => teaching == bilingual on the ADDRESSING side (resolves #760 ask #2)")
        teaching_eq = "CONFIRMED"
    elif (not C_beyond) and (not B_beyond):
        verdict = ("NULL — (C) the Tier-2 depth re-weight stays at its matched-mechanism floor like (B) the "
                   "XOR-twist => teaching != bilingual on the ADDRESSING side; the depth axis is genuinely "
                   "render-only, not language-like (pre-stated null; counts)")
        teaching_eq = "NULL"
    elif C_beyond and (not A_beyond):
        verdict = ("BORDERLINE — (C) clears its floor but the KNOWN-WORKING (A) did NOT clear its own — the "
                   "readout under-discriminates even the language axis at this scale; read with caution")
        teaching_eq = "BORDERLINE"
    else:
        verdict = ("BORDERLINE — (C) does not cleanly match either baseline (A beyond={}, B beyond={}, "
                   "C beyond={}); inconclusive on the addressing side").format(A_beyond, B_beyond, C_beyond)
        teaching_eq = "BORDERLINE"

    # Secondary continuous cross-check: is C's separation closer to A's or to B's?
    dA = cascade.magnitude(C_sep - A_sep)
    dB = cascade.magnitude(C_sep - B_sep)
    closer = "A (language-like)" if dA < dB else ("B (render-only)" if dB < dA else "tie")

    print("\n" + "=" * 104)
    print("F224 HEAD-TO-HEAD VERDICT — is TEACHING the SAME cascade as BILINGUALISM (addressing side)?")
    print("=" * 104)
    print(f"  (A) WORKING DOMAIN/language axis beyond its floor: {A_beyond}   (B) KNOWN-NULL XOR axis beyond its floor: {B_beyond}")
    print(f"  (C) NEW Tier-2 depth re-weight beyond its floor  : {C_beyond}")
    print(f"  separation proximity: |C-A|={dA:.4f}  |C-B|={dB:.4f}  => C is closer to {closer}")
    print(f"  TEACHING == BILINGUAL (addressing side): {teaching_eq}")
    print(f"  {verdict}")
    print("  STRUCTURAL-ONLY per §VII.6.20: form-reading; no cognitive / doctrinal / BCI claim.")

    # ---- attested NDJSON records ----
    attest = {"descriptor_hash": dh, "source_key": desc.source["key"],
              "srmech_version": SRMECH_VERSION, "abi_version": NATIVE_ABI_VERSION,
              "has_native": HAS_NATIVE, "demo_text": demo_key,
              "n_queries": len(queries), "window": window,
              "shallow_band": shallow_band, "deep_band": deep_band,
              "n_anchor_tags": n_tags, "tier2_alpha": alpha, "seed": seed,
              "n_random": n_random, "noise_percentile": noise_pct,
              "readout": "band_separation_of_baseline_displacement_with_matched_mechanism_random_label_floor",
              "separation_def": "abs(rankdisp(shallow,baseline) - rankdisp(deep,baseline)); rankdisp = (1 - spearman_rho)/2",
              "scope": "STRUCTURAL teaching==bilingualism addressing-side head-to-head; "
                       "texts+languages are test-objects; no cognitive/doctrinal/BCI claim; §VII.6.20"}
    records = []

    records.append({**attest, "phase": "P0_anchor_diagnostic",
                    "xor_bundle_shallow_deep_sim": bundle_sim,
                    "labeled_key_shallow_deep_sim": key_sim})

    for name, kind, sep, div, t1, pct, p90, floor, beyond in [
        ("A_domain_language_labeled_key", "working_F165_F146",
         A_sep, A_div, A_t1, A_pct, A_p90, A_floor, A_beyond),
        ("B_recipient_depth_xor_twist", "known_null_F221",
         B_sep, B_div, B_t1, B_pct, B_p90, B_floor, B_beyond),
        ("C_recipient_depth_tier2_reweight", "new_F120_classK_760ask2",
         C_sep, C_div, C_t1, C_pct, C_p90, C_floor, C_beyond),
    ]:
        records.append({**attest, "phase": "P1_condition",
                        "condition": name, "condition_kind": kind,
                        "structured_band_separation": sep,
                        "shallow_vs_deep_divergence": div,
                        "top1_disagreement": t1,
                        "matched_random_label_floor_p90": p90,
                        "matched_random_label_floor_mean": float(np.mean(floor)),
                        "matched_random_label_floor_samples": [float(x) for x in floor],
                        "pctile_in_matched_floor": pct,
                        "beyond_p90_floor": beyond})

    records.append({**attest, "phase": "P2_verdict",
                    "A_beyond_floor": A_beyond, "B_beyond_floor": B_beyond,
                    "C_beyond_floor": C_beyond,
                    "A_separation": A_sep, "B_separation": B_sep, "C_separation": C_sep,
                    "C_minus_A_abs": float(dA), "C_minus_B_abs": float(dB),
                    "C_closer_to": closer,
                    "teaching_equals_bilingual_addressing": teaching_eq,
                    "verdict": verdict})

    out = args.catalog.parent / "substrate_measurements" / "teaching_equals_bilingualism_headtohead.ndjson"
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w") as f:
        for r in records:
            f.write(json.dumps(r, default=str) + "\n")
    print(f"\nResults: {out}  ({len(records)} records)")


if __name__ == "__main__":
    main()
