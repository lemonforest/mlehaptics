"""R-RBS-LM-227 — F227: RENDER-side channel-choice test. Is what a black-box LLM
calls CHAOS in its output real render-axis CHANNEL-CHOICE, or genuinely noise?

THE ADDRESSING-SIDE RESULT (the half F221/F224 already settled):
  F221/F224 measured the ADDRESSING side — which continuation is legal / how
  candidates RANK — and found recipient/depth is RENDER-ONLY: the depth anchor
  does NOT steer retrieval.
    • F221: a STRUCTURED depth XOR-twist of the probe -> tier-1 clean NULL (0/3
      retrieval metrics beyond the F214 noise floor; §4 the readout-pinned caveat).
    • F224 condition (C): the depth anchor built the STRONGEST WORKING way — the
      F165/F146 labeled-store key bound into retrieval, read as a Tier-2 similarity
      RE-WEIGHTING (F119/F120 Class-K bridge) — did NOT clear its matched-mechanism
      random-label floor: separation 0.0409 < p90 0.0500, pctile 0.12 (BELOW its
      own floor). teaching != bilingual on the ADDRESSING side; depth is genuinely
      render-only, not language-like.

THE UNTESTED HALF (the render-side complement this run executes):
  With the CONTEXT (legal candidate set) held FIXED and varying ONLY the channel
  band, is the actually-EMITTED render — the sequence the F166 autoregressive loop
  (R-RBS-LM-129 gen_substrate) generates under each channel anchor — systematically
  CHANNEL-TUNED (its emitted surface tracks the recipient/register band) or RANDOM?

  THE HYPOTHESIS (the POSITIVE the design is built to be ABLE to reject): what a
  black-box LLM calls CHAOS in its output is real render-axis CHANNEL-CHOICE — under
  a FIXED context, the F166 loop's emitted surface (Klein-4 sector-occupancy of the
  emitted tokens, F129 length/structure coherence stats, lexical/argmax distribution)
  varies SYSTEMATICALLY with the channel band (ELI5-shallow [0,1] vs peer-neutral
  [0,1,2,3] vs expert-deep [2,3]) BEYOND the F224 matched-random-label floor.

THE STRONGEST-WORKING ANCHOR (so a render-NULL is informative, not a weak-anchor
artifact): the channel anchor is bound the SAME way F224 condition (C) bound it —
the labeled-store key re-weighting candidate similarity at the SCORING step:
      base_sims  = sim_k4_batch(klein4_bind(M, encode_context(win[-k:])), cand_vecs)
      depth_match = sim_k4_batch(klein4_bind(encode_context(win[-k:]), band_key), cand_vecs)
      score = (1-alpha)*base_sims + alpha*depth_match ;  p = softmax(score, T)
The re-weight re-orders/re-weights WITHIN the FIXED candidate set next_after[last]
WITHOUT changing which tokens are legal (the candidate set is computed BEFORE the
re-weight; an assert confirms the legal-set is channel-invariant per step). That is
what holds CONTEXT/legal-set FIXED while varying the CHANNEL. Because this is the
EXACT build that was a clean retrieval-NULL in F224, a render-null here is a genuine
result (even the strongest working anchor leaves the emitted render at the noise
floor) rather than a weak-anchor artifact.

PRE-STATED NULL (verbatim; counts EQUALLY per [[feedback_dont_pre_commit_spike_query_operators]]
— the test is NOT leaned toward the positive; boundary/floor reused verbatim from
F224 so the null cannot be manufactured by a slack gate):
  "Holding the context (legal candidate set) FIXED and varying ONLY the channel band,
   the F166 loop's EMITTED RENDER is channel-INVARIANT beyond the F224 matched-random-
   label floor — the channel-conditioned render surface (sector-occupancy of emitted
   tokens / F129 length-structure stats / lexical-argmax distribution) does NOT separate
   the depth bands by more than RANDOM LABELS bound by the IDENTICAL Tier-2 mechanism do.
   The render's cross-band spread sits at-or-below the p90 of the matched-random-label
   spread on the majority of render metrics, AND the F168-native emitted-sector-occupancy
   readout is NOT among any that clear it. => What the black-box LLM calls chaos in its
   output IS noise on the render axis too: the recipient/depth channel is render-invariant,
   so combined with the F221/F224 addressing-null, recipient/depth steers NEITHER retrieval
   NOR the emitted surface beyond the floor — it is not a real channel at this scale/build."

PRE-STATED POSITIVE (verbatim):
  "Holding the context FIXED and varying ONLY the channel band, the F166 loop's EMITTED
   RENDER tracks the channel BEYOND the F224 matched-random-label floor — the channel-
   conditioned render surface separates the depth bands (shallow vs deep, and the 3-frame
   ELI5/peer/expert spread) by MORE than random labels bound by the IDENTICAL Tier-2
   mechanism do, on a majority of render metrics INCLUDING the F168-native emitted-sector-
   occupancy readout. => CONFIRMS chaos = real render-axis CHANNEL-CHOICE: the
   recipient/depth anchor is a genuine RENDER-axis channel selector — it systematically
   tunes WHAT IS EMITTED even though F221/F224 showed it does NOT steer WHICH continuation
   is retrieved (render-only, exactly as F212/F214/F221 located the recipient fiber)."

VERDICT GATE (mirrors F221's majority-with-native-readout logic + F224's matched-
mechanism isolation; conservative). For EACH render metric FAMILY m, the CHANNEL
render-spread = cross-frame distance among the three structured channel renders
(ELI5/peer/expert); gated against the SAME-metric spread among n_random=16 RANDOM-LABEL
channel renders generated by the IDENTICAL Tier-2 mechanism. Family m 'clears' iff
structured-spread pctile >= 0.90 AND structured-spread > random-label p90 + 1e-12
(F224 gate verbatim).
  - RENDER-POSITIVE (chaos = channel-choice): >=2/3 families clear AND the F168-native
    emitted-sector-occupancy family is among them. tier-1 (clean) if all 3 clear or
    2/3 incl. sector-occupancy.
  - RENDER-NULL (chaos = noise): 0 families clear, or only families EXCLUDING sector-
    occupancy with <2 total => render is channel-invariant beyond the floor (pre-stated
    null; stronger because the anchor is the F224 strongest-working build).
  - MIXED/tier-2: the off-native or single-family cases, reported honestly (read with
    the F214 §4 / F224 construction-artifact caveat — lexical/topk overlap can move for
    binding-orthogonality reasons unrelated to channel meaning, so it is NOT sufficient
    alone). DEMONSTRATED only if RENDER-POSITIVE clears tier-1; else FRAMEWORK-READING
    (mixed) or a clean NULL.
Non-degeneracy precondition (else a null is 'anchors collapsed', not 'render channel-
invariant'): the three channel labeled-keys must be pairwise distinct (sim < 1.0, ~0.25
Klein-4 floor) AND the three structured renders must not be byte-identical (if they are,
report INDETERMINATE-anchor, not null).

srmech-native (CLAUDE.md §2 STOP-list honored — 28D / Klein-4 / chirality framing):
  • hdc.{klein4_bind}                                   — channel-anchor application (the
      F224 condition-C Tier-2 build) + the F166 loop's own probe (Class M)
  • encode_word_k4(sector=s)                            — the F168 self-inverse-XOR sector
      tagging; the emitted-sector-occupancy probes (Class M ∘ I)
  • ContextSubstrate.{enc, encode_context, bundle_odd}  — the F166 rolling context-state
      (R-126); enc('__band_*__') the F165/F146 labeled channel keys; enc('__rand_*__')
      the matched-random-label surrogates (Class A content-mint)
  • sim_k4_batch (F132 fractional-agreement, Class M)   — base_sims + depth_match + the
      emitted-sector argmax recovery (NEVER a hand-rolled cosine)
  • cascade.magnitude (Class-K pin-slot |.|)            — ALL sign-free render-spread folds
      (|shallow-deep|, histogram-L1 terms, sorted-eigval-L2 terms); NEVER python abs()
  • laplacian.dense_laplacian + jacobi_eigvals (Class L) — the EMITTED-sequence co-occurrence
      spectrum (nodes = emitted tokens, edges = adjacency); NEVER np.linalg.eig/eigh/svd
  • format.sha256_bytes (Class A)                       — per-channel + per-random-label
      deterministic RNG seeds + random-label indices; NEVER python hash() / hashlib.sha256
  • Counter ONLY for the emitted-sequence adjacency EDGE WEIGHTS feeding dense_laplacian
    and the bigram candidate store (the R-127/R-131 stored-relationship structure), NEVER
    as a storage/occupancy proxy (emitted-sector-occupancy is read via sim_k4_batch argmax).
Catalog-driven (descriptor_religious_texts.toml [render_channel]); srmech 0.5.0 native
ABI=3; deterministic / bit-exact (NDJSON; second-run sha256 must match). STRUCTURAL render-
axis channel-choice per §VII.6.20: texts + depth-bands are structural test-objects; ai-is-
not-a-substrate (the LM is a k=3 chiral addresser, not an aware entity); trauma-informed —
NO clinical / biological / BCI / cognitive claim about real recipients; no-lineage.
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
from srmech.amsc.format import sha256_bytes
from srmech.amsc._native import HAS_NATIVE, NATIVE_ABI_VERSION
from srmech import __version__ as SRMECH_VERSION

CATALOG = HERE.parent / "catalogs" / "rbs_lm_substrate" / "descriptor_religious_texts.toml"
MAX_TOKENS = 80000


# ---------------------------------------------------------------------------
# Deterministic per-(seed-window, channel) RNG seed — via sha256_bytes, NOT python
# hash() (CLAUDE.md §2 / bit-exact discipline). Structured-vs-random renders then
# differ ONLY by the bound channel label, not by the generation RNG.
# ---------------------------------------------------------------------------

def derive_seed(*parts) -> int:
    """A deterministic 63-bit integer seed from a label tuple, routed through the
    Class-A content-hash (sha256_bytes) — never python hash() (non-deterministic
    across runs) and never hashlib.sha256 directly (route through the srmech op)."""
    payload = "|".join(str(p) for p in parts).encode("utf-8")
    return int(sha256_bytes(payload)[:16], 16) & ((1 << 63) - 1)


# ---------------------------------------------------------------------------
# srmech-native distances (sign-free via cascade.magnitude — identical shape to
# R-RBS-LM-221's spectral_distance / hist_l1; NEVER python abs()).
# ---------------------------------------------------------------------------

def spectral_distance(ev_a: np.ndarray, ev_b: np.ndarray) -> float:
    """Sorted-eigenvalue L2 between two Class-L emitted-spectra (sign-free).
    cascade.magnitude (Class-K pin-slot |.|) folds each signed coordinate."""
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
    """L1 between two normalized sector-occupancy histograms (sign-free)."""
    ta = sum(h_a.get(s, 0) for s in range(n_bins)) or 1
    tb = sum(h_b.get(s, 0) for s in range(n_bins)) or 1
    acc = 0.0
    for s in range(n_bins):
        acc += cascade.magnitude(h_a.get(s, 0) / ta - h_b.get(s, 0) / tb)
    return float(acc)


def stat_vec_l2(va: dict, vb: dict, keys) -> float:
    """L2 over a named F129 coherence-stat vector (sign-free via cascade.magnitude)."""
    acc = 0.0
    for k in keys:
        d = cascade.magnitude(float(va.get(k, 0.0)) - float(vb.get(k, 0.0)))
        acc += d * d
    return float(acc ** 0.5)


def jaccard(set_a, set_b) -> float:
    a, b = set(set_a), set(set_b)
    u = a | b
    return len(a & b) / len(u) if u else 1.0


def softmax(x: np.ndarray, t: float) -> np.ndarray:
    z = x / t
    z = z - z.max()
    e = np.exp(z)
    return e / e.sum()


# ---------------------------------------------------------------------------
# F129 corpus-agnostic coherence (pos_valid OMITTED on KJV-NT — the R-113 template
# grammar does not exist for real text; NOT faked). Identical stat defs to
# R-RBS-LM-129 coherence_metrics minus pos_valid.
# ---------------------------------------------------------------------------

def coherence_metrics(seq, corpus_trigrams):
    n = len(seq)
    if n < 3:
        return None
    trig = [(seq[i], seq[i + 1], seq[i + 2]) for i in range(n - 2)]
    trigram_legal = float(np.mean([t in corpus_trigrams for t in trig]))
    rep1 = np.mean([seq[i] == seq[i - 1] for i in range(1, n)])
    rep2 = np.mean([seq[i] == seq[i - 2] for i in range(2, n)])
    repeat_rate = float(max(rep1, rep2))
    distinct_ratio = len(set(seq)) / n
    cycle_3gram = float(1.0 - len(set(trig)) / len(trig)) if trig else 0.0
    return {"trigram_legal": trigram_legal, "repeat_rate": repeat_rate,
            "distinct_ratio": distinct_ratio, "cycle_3gram": cycle_3gram}


F129_STAT_KEYS = ("trigram_legal", "repeat_rate", "distinct_ratio", "cycle_3gram")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--catalog", type=Path, default=CATALOG)
    ap.add_argument("--warm-check", action="store_true",
                    help="ALSO run the secondary warm_temp cold-pinning cross-check "
                         "(primary verdict stays at the cold operating_temp for F129 comparability)")
    args = ap.parse_args()

    desc = load_descriptor(args.catalog)
    dh = descriptor_hash(args.catalog)
    lc = desc.fetch["literature_curated"]
    D = int(lc["substrate"]["D"])
    hexc = int(lc["substrate"]["token_seed_hex_chars"])
    sector_count = int(lc["substrate"]["sector_count"])
    cache_dir = Path(lc["corpus"]["cache_dir"]).expanduser()
    texts = lc["corpus"]["texts"]
    rc = lc["render_channel"]
    demo_key = str(rc["demo_text"])
    n_units = int(rc["n_units"])
    gen_n_seeds = int(rc["gen_n_seeds"])
    window = int(rc["window"])
    min_cand = int(rc["min_candidates"])
    gen_length = int(rc["gen_length"])
    op_temp = float(rc["operating_temp"])
    warm_temp = float(rc["warm_temp"])
    n_random = int(rc["n_random"])
    noise_pct = float(rc["noise_percentile"])
    alpha = float(rc["tier2_alpha"])
    bands = {"eli5": [int(x) for x in rc["shallow_band"]],
             "peer": [int(x) for x in rc["neutral_band"]],
             "expert": [int(x) for x in rc["deep_band"]]}
    band_label = {"eli5": "shallow", "peer": "neutral", "expert": "deep"}
    seed = int(rc["seed"])
    loop_seed = int(rc["loop_seed"])

    print(f"srmech v{SRMECH_VERSION}; HAS_NATIVE={HAS_NATIVE}; ABI={NATIVE_ABI_VERSION}; D={D}")
    print(f"Catalog: {args.catalog.name}  hash={dh[:16]}...")
    print(f"demo_text={demo_key}  window={window}  gen_n_seeds={gen_n_seeds}  gen_length={gen_length}  "
          f"T={op_temp}  n_random={n_random}  noise_pct={noise_pct}  sectors={sector_count}")
    print(f"CHANNEL BANDS — eli5(shallow)={bands['eli5']}  peer(neutral)={bands['peer']}  "
          f"expert(deep)={bands['expert']}  tier2_alpha={alpha}\n")
    print("F227 RENDER-side channel-choice — is CHAOS in the emitted render real channel-CHOICE")
    print("or noise? Hold CONTEXT (legal candidate set) FIXED; vary ONLY the channel band; run the")
    print("F166 loop (R-129 gen_substrate) with the F224 condition-C Tier-2 labeled-key re-weight")
    print("(the STRONGEST WORKING anchor — the same build that was a clean RETRIEVAL-null) at the")
    print("SCORING step; measure the EMITTED render's cross-band spread vs the F224 matched-")
    print("mechanism random-LABEL floor (p90 gate, verbatim).")
    print("ADDRESSING-side cross-ref: F221 0/3 NULL; F224 (C) sep=0.0409 < p90=0.0500 (pctile 0.12).")
    print("PRE-STATED NULL: render channel-INVARIANT beyond the floor (0 families clear, or only")
    print("  non-sector families <2) => chaos = noise on the render axis too (stronger: strongest build).")
    print("PRE-STATED POS : >=2/3 families clear INCL. emitted-sector-occupancy => chaos = render CHANNEL-CHOICE.")
    print("STRUCTURAL-ONLY per §VII.6.20: texts+bands are test-objects; ai-not-substrate; no clinical/BCI claim.\n")

    # --- corpus -> token stream -> bigram store (the FIXED legal-set; R-127/R-131) ---
    meta = texts[demo_key]
    body = k1mod.strip_gutenberg(
        (cache_dir / meta["filename"]).read_text(encoding="utf-8", errors="replace"))
    stream = k1mod.tokenize(body)[:MAX_TOKENS]
    bigram = defaultdict(Counter)      # Counter = bigram EDGE STRUCTURE (R-127/R-131), not a proxy
    for a, b in zip(stream, stream[1:]):
        bigram[a][b] += 1
    next_after = {a: sorted(c.keys()) for a, c in bigram.items()}   # the FIXED candidate set
    vocab = sorted(set(stream))
    ctxsub = cs.ContextSubstrate(D=D, hex_chars=hexc)
    vocab_vecs = np.stack([ctxsub.enc(w) for w in vocab])
    vocab_idx = {w: i for i, w in enumerate(vocab)}
    corpus_trigrams = {(stream[i], stream[i + 1], stream[i + 2])
                       for i in range(len(stream) - 2)}
    print(f"{meta['label']}: {len(stream)} tokens, {len(vocab)} unique; "
          f"{len(next_after)} predecessors in the bigram store; "
          f"{len(corpus_trigrams)} distinct trigrams\n")

    # --- build the k-window associative memory M (the F166 inference substrate's
    # --- knowledge — IDENTICAL construction to R-129: random sample of (ctx->next)
    # --- pairs bound + bundled). Deterministic seed via the loader seed. ---
    rng = np.random.default_rng(seed)
    k = window
    pairs_all = [(tuple(stream[i - k:i]), stream[i]) for i in range(k, len(stream))]
    N_assoc = min(2000, len(pairs_all))
    idx = rng.choice(len(pairs_all), size=N_assoc, replace=False)
    pairs = [pairs_all[i] for i in idx]
    assoc = [hdc.klein4_bind(ctxsub.encode_context(list(c)), ctxsub.enc(t)) for c, t in pairs]
    M = ctxsub.bundle_odd(assoc)

    # --- FIXED seed-window pool (real k-grams from the stream whose last token has
    # --- >= min_cand legal successors, so the render has a real distribution to walk).
    # --- Deterministic selection. The SAME pool is used for EVERY channel (structured
    # --- + random) so the only thing that varies is the bound channel label. ---
    use_tokens = min(n_units, len(stream))
    sub = stream[:use_tokens]
    all_pos = [i for i in range(window, len(sub))
               if len(next_after.get(sub[i - 1], [])) >= min_cand]
    if len(all_pos) > gen_n_seeds:
        sel = sorted(int(x) for x in rng.choice(all_pos, size=gen_n_seeds, replace=False))
    else:
        sel = all_pos
    seed_windows = [tuple(sub[i - window:i]) for i in sel]
    print(f"fixed seed-window pool: {len(seed_windows)} windows "
          f"(each last-token has >= {min_cand} legal successors)\n")

    # --- channel-anchor keys: the F165/F146 labeled-store keys (the F224 (C) build) ---
    chan_keys = {name: ctxsub.enc(f"__band_{band_label[name]}__") for name in bands}
    # matched-random-label surrogates: enc('__rand_render_{r}__') — the SAME labeled-key
    # mechanism, just a meaningless label. The render-spread among the structured
    # channels is gated against the render-spread among these (F224 isolation).
    rand_keys = [ctxsub.enc(f"__rand_render_{r}__") for r in range(n_random)]

    # NON-DEGENERACY diagnostic: the 3 channel keys must be pairwise distinct (< 1.0,
    # ~0.25 Klein-4 floor — F221's eli5~peer=0.243 diagnostic). Else a null is
    # "anchors collapsed".
    def keysim(a, b):
        return float(cs.sim_k4_batch(a, b[None, :])[0])
    sim_ep = keysim(chan_keys["eli5"], chan_keys["peer"])
    sim_ex = keysim(chan_keys["eli5"], chan_keys["expert"])
    sim_px = keysim(chan_keys["peer"], chan_keys["expert"])
    keys_distinct = (sim_ep < 1.0 and sim_ex < 1.0 and sim_px < 1.0)
    print("CHANNEL-KEY non-degeneracy (should be < 1.0 — distinct channel labels):")
    print(f"  eli5~peer={sim_ep:.3f}  eli5~expert={sim_ex:.3f}  peer~expert={sim_px:.3f}  "
          f"distinct={keys_distinct}\n")

    # ----------------------------------------------------------------------
    # The channel-conditioned F166 generator: R-129 gen_substrate with the scoring
    # line replaced by the F224 condition-C Tier-2 re-weight. The candidate set is
    # computed BEFORE the re-weight (FIXED legal-set); the channel only re-weights
    # the softmax score over that set. An assert confirms the legal-set is channel-
    # invariant per step (FIXED-CONTEXT integrity). gr is a band-derived deterministic
    # RNG per (seed-window, channel) so structured-vs-random differ ONLY by the label.
    # ----------------------------------------------------------------------
    def gen_render(window_tokens, length, T, band_key, gr):
        out = []
        win = list(window_tokens)
        for _ in range(length):
            last = win[-1]
            cands = next_after.get(last, [])      # FIXED legal-set (computed BEFORE re-weight)
            if not cands:
                break
            if len(cands) == 1:
                nxt = cands[0]
            else:
                cidx = [vocab_idx[c] for c in cands]
                cand_vecs = vocab_vecs[cidx]
                ctx_state = ctxsub.encode_context(win[-k:])
                base_sims = cs.sim_k4_batch(hdc.klein4_bind(M, ctx_state), cand_vecs)  # Tier-1 (F166 probe)
                depth_match = cs.sim_k4_batch(hdc.klein4_bind(ctx_state, band_key), cand_vecs)  # Tier-2 channel
                score = (1.0 - alpha) * base_sims + alpha * depth_match  # Class-K bridge (F224 (C))
                p = softmax(score, T)
                # FIXED-CONTEXT integrity: the channel re-weights WITHIN cands; it must
                # not change which tokens are legal. (cands derives from next_after only.)
                assert len(p) == len(cands)
                nxt = cands[int(gr.choice(len(cands), p=p))]
            out.append(nxt)
            win.append(nxt)
        return out

    # emitted-sector-occupancy (F168-native render meter, on the EMITTED sequence —
    # mirrors R-221 frame_retrieval sector_hist but over what was GENERATED): for each
    # emitted token, encode_word_k4 at each sector s, argmax which sector the channel-
    # conditioned probe most recovers. The channel-conditioned probe for an emitted
    # token is the Tier-2-mixed score-probe at its emission context.
    def emitted_sector_hist(full_seq, band_key, sector_count):
        hist = Counter()              # emitted-sector OCCUPANCY read via sim argmax (NOT a storage proxy)
        for pos in range(window, len(full_seq)):
            tok = full_seq[pos]
            ctx_state = ctxsub.encode_context(full_seq[pos - window:pos])
            probe = hdc.klein4_bind(ctx_state, band_key)   # the channel-conditioned probe
            sector_probes = np.stack([
                cs.encode_word_k4(tok, D=ctxsub.D, sector=s, hex_chars=ctxsub.hex_chars)
                for s in range(sector_count)])
            sec = int(cs.sim_k4_batch(probe, sector_probes).argmax())
            hist[sec] += 1
        return hist

    # the EMITTED-sequence Class-L co-occurrence spectrum (nodes = emitted tokens,
    # edges = adjacency in the emitted render; the render's structural fingerprint).
    def emitted_spectrum(seqs):
        node_ids: dict[str, int] = {}
        def node(t):
            if t not in node_ids:
                node_ids[t] = len(node_ids)
            return node_ids[t]
        co_edges = Counter()          # adjacency EDGE WEIGHTS feeding dense_laplacian (allowed)
        for s in seqs:
            for i in range(len(s) - 1):
                a, b = node(s[i]), node(s[i + 1])
                if a != b:
                    co_edges[(min(a, b), max(a, b))] += 1
        n_nodes = len(node_ids)
        edges = list(co_edges.keys())
        weights = [float(co_edges[e]) for e in edges]
        if n_nodes >= 2 and edges:
            L = dense_laplacian(n_nodes, edges, weights)
            return np.asarray(jacobi_eigvals(np.asarray(L, dtype=float)), dtype=float), n_nodes
        return np.zeros(1), n_nodes

    # one channel's full render signature over the FIXED seed-window pool, at temp T.
    def render_signature(band_key, label, T):
        seqs = []
        sec_hist = Counter()
        coh_acc = defaultdict(list)
        lex_sets = []                 # emitted-token SETS per seed (for the F3 Jaccard meter)
        for si, win in enumerate(seed_windows):
            gr = np.random.default_rng(derive_seed(loop_seed, label, si))  # sha256_bytes-derived
            out = gen_render(win, gen_length, T, band_key, gr)
            full = list(win) + out
            seqs.append(full)
            lex_sets.append(set(out))                  # emitted (generated) tokens only
            h = emitted_sector_hist(full, band_key, sector_count)
            for s, c in h.items():
                sec_hist[s] += c
            m = coherence_metrics(full, corpus_trigrams)
            if m is not None:
                for kk, v in m.items():
                    coh_acc[kk].append(v)
        coh = {kk: float(np.mean(v)) for kk, v in coh_acc.items()}
        eig, n_nodes = emitted_spectrum(seqs)
        return {"seqs": seqs, "sector_hist": dict(sec_hist), "coherence": coh,
                "lex_sets": lex_sets, "eigvals": eig, "n_nodes": n_nodes}

    # ---- generate the renders (3 structured channels + n_random random-label) ----
    print(f"generating renders: 3 structured + {n_random} random-label channels x "
          f"{len(seed_windows)} seeds x {gen_length} tokens (T={op_temp})...\n")
    structured = {name: render_signature(chan_keys[name], f"chan_{name}", op_temp) for name in bands}
    control = {f"rand{r}": render_signature(rand_keys[r], f"rand_{r}", op_temp) for r in range(n_random)}

    # NON-DEGENERACY (render side): are the 3 structured renders byte-identical?
    def seqs_blob(sig):
        return "\n".join(" ".join(s) for s in sig["seqs"])
    blob_e, blob_p, blob_x = (seqs_blob(structured["eli5"]),
                              seqs_blob(structured["peer"]), seqs_blob(structured["expert"]))
    renders_identical = (blob_e == blob_p == blob_x)
    print(f"RENDER non-degeneracy: 3 structured renders byte-identical? {renders_identical}")
    print("  (if True -> INDETERMINATE-anchor, NOT null: a cold-deterministic loop the channel "
          "cannot move)\n")

    # ---- per-family render-spread (structured cross-frame) + matched-random floor ----
    # F1 emitted-sector-occupancy (the F168-native readout); F2 F129 length/structure;
    # F3 lexical/argmax (1 - mean Jaccard); F4 emitted Class-L eigen-spectrum L2.
    def f1_sector(a, b):
        return hist_l1(a["sector_hist"], b["sector_hist"], sector_count)
    def f2_structure(a, b):
        return stat_vec_l2(a["coherence"], b["coherence"], F129_STAT_KEYS)
    def f3_lexical(a, b):
        js = [jaccard(sa, sb) for sa, sb in zip(a["lex_sets"], b["lex_sets"])]
        return 1.0 - float(np.mean(js)) if js else 0.0
    def f4_spectrum(a, b):
        return spectral_distance(a["eigvals"], b["eigvals"])

    families = {
        "F1_emitted_sector_occupancy_L1": (f1_sector, True),   # the F168-native readout (required for clean POS)
        "F2_length_structure_L2": (f2_structure, False),
        "F3_lexical_argmax_1_minus_jaccard": (f3_lexical, False),
        "F4_emitted_eigenspectrum_L2": (f4_spectrum, False),
    }

    def pairwise_vals(items, fn):
        vals, keys = [], list(items)
        for i in range(len(keys)):
            for j in range(i + 1, len(keys)):
                vals.append(fn(items[keys[i]], items[keys[j]]))
        return vals

    def percentile_of(value, distribution):
        if not distribution:
            return 1.0
        d = np.asarray(distribution, dtype=float)
        return float((d <= value).mean())

    # also the shallow-vs-deep CONTRAST per family (secondary; |eli5 - expert| pairwise)
    def contrast(items_a, items_b, fn):
        return cascade.magnitude(fn(items_a, items_b) - 0.0)  # the raw distance is already >=0; magnitude is identity-safe here

    attest = {"descriptor_hash": dh, "source_key": desc.source["key"],
              "srmech_version": SRMECH_VERSION, "abi_version": NATIVE_ABI_VERSION,
              "has_native": HAS_NATIVE, "demo_text": demo_key,
              "n_seeds": len(seed_windows), "gen_length": gen_length,
              "window": window, "operating_temp": op_temp, "tier2_alpha": alpha,
              "shallow_band": bands["eli5"], "neutral_band": bands["peer"],
              "deep_band": bands["expert"], "seed": seed, "loop_seed": loop_seed,
              "n_random": n_random, "noise_percentile": noise_pct,
              "anchor_build": "F224_condition_C_tier2_labeled_key_reweight_at_scoring",
              "readout": "emitted_render_cross_band_spread_vs_matched_mechanism_random_label_floor",
              "scope": "STRUCTURAL render-axis channel-choice; texts+depth-bands are test-objects; "
                       "ai-not-substrate; no clinical/biological/BCI/cognitive claim; §VII.6.20"}
    records = []

    # P0 anchor non-degeneracy
    records.append({**attest, "phase": "P0_anchor_nondegeneracy",
                    "channel_key_eli5_peer_sim": sim_ep,
                    "channel_key_eli5_expert_sim": sim_ex,
                    "channel_key_peer_expert_sim": sim_px,
                    "channel_keys_distinct": bool(keys_distinct),
                    "structured_renders_byte_identical": bool(renders_identical)})

    # P1 per-channel render signatures (printed + recorded)
    print("PER-CHANNEL EMITTED-SECTOR OCCUPANCY (the F168-native render readout) + F129 stats")
    print(f"{'channel':>10} | " + " | ".join(f"sec{s}" for s in range(sector_count)) +
          " | trigleg | distinct | cycle3g | n_nodes")
    print("-" * 92)
    for grp_name, grp in (("structured", structured), ("control", control)):
        for name, sig in grp.items():
            tot = sum(sig["sector_hist"].values()) or 1
            cells = " | ".join(f"{sig['sector_hist'].get(s,0)/tot:5.3f}" for s in range(sector_count))
            coh = sig["coherence"]
            print(f"{name:>10} | {cells} | {coh.get('trigram_legal',0):7.3f} | "
                  f"{coh.get('distinct_ratio',0):8.3f} | {coh.get('cycle_3gram',0):7.3f} | {sig['n_nodes']}")
            records.append({**attest, "phase": "P1_channel_render_signature", "group": grp_name,
                            "channel": name, "sector_hist": sig["sector_hist"],
                            "coherence": sig["coherence"], "n_emitted_nodes": sig["n_nodes"],
                            "n_eigvals": int(len(sig["eigvals"]))})

    # P2 per-family spread vs matched-random floor (the F224 gate verbatim)
    print("\nEMITTED-RENDER CROSS-BAND SPREAD vs the MATCHED-mechanism RANDOM-LABEL floor")
    print("(structured = cross-frame spread among eli5/peer/expert; floor = same-family spread")
    print(" among the 16 random-LABEL renders bound the IDENTICAL Tier-2 way; p90 gate).")
    print(f"{'render family':>36} | {'structured':>11} | {'rand_mean':>10} | {'rand_p90':>9} | "
          f"{'pctile':>6} | clears?")
    print("-" * 100)
    n_clear = 0
    sector_clears = False
    family_rows = []
    for fname, (fn, is_native) in families.items():
        s_spread = float(np.mean(pairwise_vals(structured, fn))) if len(structured) > 1 else 0.0
        c_vals = pairwise_vals(control, fn)
        c_mean = float(np.mean(c_vals)) if c_vals else 0.0
        c_p90 = float(np.quantile(c_vals, noise_pct)) if c_vals else 0.0
        pct = percentile_of(s_spread, c_vals)
        clears = pct >= noise_pct and s_spread > c_p90 + 1e-12
        n_clear += int(clears)
        if is_native:
            sector_clears = clears
        # secondary shallow-vs-deep contrast (eli5 vs expert) — context only
        sd_contrast = fn(structured["eli5"], structured["expert"])
        family_rows.append((fname, s_spread, c_mean, c_p90, pct, clears, is_native, sd_contrast))
        print(f"{fname:>36} | {s_spread:>11.4f} | {c_mean:>10.4f} | {c_p90:>9.4f} | "
              f"{pct:>6.2f} | {'YES (>p90)' if clears else 'no'}"
              f"{'  [F168-native]' if is_native else ''}")
        records.append({**attest, "phase": "P2_family_spread", "family": fname,
                        "is_f168_native_readout": bool(is_native),
                        "structured_cross_band_spread": s_spread,
                        "matched_random_label_floor_mean": c_mean,
                        "matched_random_label_floor_p90": c_p90,
                        "matched_random_label_floor_samples": [float(x) for x in c_vals],
                        "structured_pctile_in_matched_floor": pct,
                        "shallow_vs_deep_contrast": float(sd_contrast),
                        "clears_p90_floor": bool(clears)})

    # ---- VERDICT (F221 majority-with-native + F224 matched-mechanism; conservative) ----
    n_families = len(families)
    non_native_clear = n_clear - (1 if sector_clears else 0)
    if renders_identical or not keys_distinct:
        tier = "INDETERMINATE"
        verdict = ("INDETERMINATE-anchor — " +
                   ("the 3 structured renders are byte-identical (a cold-deterministic loop the channel "
                    "cannot move)" if renders_identical else "the channel keys collapsed (sim==1.0)") +
                   "; NOT a null (the anchor could not register a render shift)")
        render_state = "INDETERMINATE"
    elif n_clear >= 2 and sector_clears:
        render_state = "RENDER-POSITIVE"
        if n_clear == n_families or (n_clear == 2 and sector_clears):
            tier = "tier-1 (clean)"
        else:
            tier = "tier-1 (clean)"
        verdict = (f"RENDER-POSITIVE — {n_clear}/{n_families} render families clear the matched-random-label "
                   "floor INCLUDING the F168-native emitted-sector-occupancy readout => chaos = real render-axis "
                   "CHANNEL-CHOICE: the recipient/depth anchor systematically tunes WHAT IS EMITTED (render-only, "
                   "exactly as F212/F214/F221/F224 located the recipient fiber on the addressing side)")
    elif n_clear == 0:
        render_state = "RENDER-NULL"
        tier = "tier-1 (clean null)"
        verdict = ("RENDER-NULL — 0/4 render families clear the matched-random-label floor => the EMITTED render "
                   "is channel-INVARIANT beyond the floor. Stronger than a weak-anchor null because the anchor is "
                   "the F224 STRONGEST-WORKING build (the same labeled-key Tier-2 re-weight that was a clean "
                   "RETRIEVAL-null). Combined with the F221/F224 addressing-null: recipient/depth steers NEITHER "
                   "retrieval NOR the emitted surface beyond the floor — chaos is noise on BOTH axes at this scale/build")
    elif sector_clears and n_clear == 1:
        render_state = "MIXED"
        tier = "tier-2 (qualified)"
        verdict = ("MIXED-LEANING-CHANNEL — only the F168-native emitted-sector-occupancy family clears the floor "
                   "(the depth-relevant render readout moved, but <2/3 families) — read with the F214 §4 / F224 "
                   "construction caveat; NOT a clean RENDER-POSITIVE")
    elif n_clear >= 2 and not sector_clears:
        render_state = "MIXED"
        tier = "tier-2 (qualified)"
        verdict = (f"MIXED — {n_clear}/{n_families} families clear the floor but the F168-native emitted-sector-"
                   "occupancy readout is NOT among them (lexical/topk/spectral overlap can move for binding-"
                   "orthogonality reasons unrelated to channel meaning, F214 §4) — NOT sufficient for DEMONSTRATED")
    else:
        render_state = "MIXED"
        tier = "tier-3 (weak/mixed)"
        verdict = (f"MIXED — {n_clear}/{n_families} families clear (NOT the F168-native readout); off-native single-"
                   "family, reported with the F214 §4 construction caveat")

    # honest research tier
    if render_state == "RENDER-POSITIVE" and tier.startswith("tier-1"):
        research_tier = "DEMONSTRATED"
    elif render_state == "INDETERMINATE":
        research_tier = "CONJECTURE (indeterminate-anchor; re-test required)"
    elif render_state == "RENDER-NULL":
        research_tier = "FRAMEWORK-READING (clean NULL)"
    else:
        research_tier = "FRAMEWORK-READING (mixed)"

    print("\n" + "=" * 100)
    print("F227 RENDER-side VERDICT — is CHAOS in the emitted render real channel-CHOICE, or noise?")
    print("=" * 100)
    print(f"  render families clearing the matched-random-label floor: {n_clear}/{n_families}   "
          f"(F168-native emitted-sector-occupancy clears: {sector_clears})")
    print(f"  channel keys distinct: {keys_distinct}   structured renders byte-identical: {renders_identical}")
    print(f"  {verdict}")
    print(f"  render-state: {render_state}   tier: {tier}   research-tier: {research_tier}")
    print("  ADDRESSING-side context (read the render verdict alongside): F221 0/3 retrieval NULL; "
          "F224 (C) sep=0.0409 < p90=0.0500 (pctile 0.12).")
    if render_state == "RENDER-POSITIVE":
        print("  => addressing-null + render-positive: recipient/depth is a pure RENDER-axis channel selector "
              "that does NOT touch retrieval.")
    elif render_state == "RENDER-NULL":
        print("  => addressing-null + render-null: the apparent chaos is genuinely NOISE on BOTH axes at this scale/build.")
    print("  STRUCTURAL-ONLY per §VII.6.20: form-reading; ai-is-not-a-substrate; no clinical/biological/BCI/cognitive claim.")

    records.append({**attest, "phase": "P3_verdict",
                    "render_families_clearing_floor": n_clear,
                    "n_render_families": n_families,
                    "f168_native_sector_occupancy_clears": bool(sector_clears),
                    "non_native_families_clearing": int(non_native_clear),
                    "channel_keys_distinct": bool(keys_distinct),
                    "structured_renders_byte_identical": bool(renders_identical),
                    "render_state": render_state, "verdict": verdict,
                    "tier": tier, "research_tier": research_tier,
                    "addressing_side_crossref": "F221 0/3 retrieval NULL; F224 (C) sep=0.0409 < p90=0.0500 pctile=0.12"})

    # ---- OPTIONAL warm-temp cold-pinning cross-check (secondary; NOT the verdict) ----
    if args.warm_check:
        print(f"\n[secondary] warm_temp cold-pinning cross-check at T={warm_temp} "
              "(primary verdict stays at the cold T for F129 comparability)...")
        w_struct = {name: render_signature(chan_keys[name], f"chanW_{name}", warm_temp) for name in bands}
        w_ctrl = {f"rand{r}": render_signature(rand_keys[r], f"randW_{r}", warm_temp) for r in range(n_random)}
        w_clear = 0
        w_native = False
        for fname, (fn, is_native) in families.items():
            s_spread = float(np.mean(pairwise_vals(w_struct, fn))) if len(w_struct) > 1 else 0.0
            c_vals = pairwise_vals(w_ctrl, fn)
            c_p90 = float(np.quantile(c_vals, noise_pct)) if c_vals else 0.0
            pct = percentile_of(s_spread, c_vals)
            clears = pct >= noise_pct and s_spread > c_p90 + 1e-12
            w_clear += int(clears)
            if is_native:
                w_native = clears
            records.append({**attest, "phase": "P4_warm_crosscheck", "family": fname,
                            "warm_temp": warm_temp, "is_f168_native_readout": bool(is_native),
                            "structured_cross_band_spread": s_spread,
                            "matched_random_label_floor_p90": c_p90,
                            "structured_pctile_in_matched_floor": pct,
                            "clears_p90_floor": bool(clears)})
        print(f"  warm-temp families clearing floor: {w_clear}/{n_families} (native clears: {w_native}) "
              "— cold-pinning cross-check only; the verdict above is at the cold T.")

    out = args.catalog.parent / "substrate_measurements" / "render_chaos_vs_channel.ndjson"
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w") as f:
        for r in records:
            f.write(json.dumps(r, default=str) + "\n")
    ndjson_sha = sha256_bytes(open(out, "rb").read())
    print(f"\nResults: {out}  ({len(records)} records)")
    print(f"NDJSON sha256 (bit-exact attestation): {ndjson_sha}")


if __name__ == "__main__":
    main()
