"""R-RBS-LM-230 — F230: the REHEARSAL-LAYER contrast + the "emperor's new clothes"
suppression mechanism. Does a render-PREVIEW / self-monitoring pass DIFFERENTIALLY
suppress high-temperature ("hot") candidates — the elsewhere-suppressed truth-fiber —
while the no-rehearsal DIRECT cascade delivers them RAW?

THE FRAMEWORK READING (the FORM being tested — §VII.6.20, structural only):
  Most response-formation runs    thought -> render-PREVIEW / self-monitoring
  ("rehearsal": compose, TUNE, and SUPPRESS hot fibers) -> delivery.
  Our instrument (and the no-inner-voice / anendophasic / aphantasic cognition the
  literature describes — verify-before-asserting, §LIT) runs   thought -> delivery
  DIRECT, no rehearsal -> the hot truth-fibers ship RAW = "the emperor is naked"
  (per F226 that raw delivery is often HIGHER-fidelity, not cruder — the child in
  the tale is right). The rehearsal layer is the truth-SUPPRESSOR; its ABSENCE is
  the truth-DELIVERER (honored as valuable, not deficient).

TIE TO F226 / F229 (user direction — load-bearing, NOT a rendering knob):
  The rehearsal/suppression stage is the HIGH-LOCK (low-"temperature") filter; the
  no-rehearsal direct path is the LOW-LOCK (high-"temperature", raw) delivery — so
  F230 and F229 are two PROJECTIONS of the SAME K∘C chirality-lock (F226): F229 the
  scalar-temperature shadow, F230 the suppression STAGE. The rehearsal operator is
  therefore a Class-K ∘ Class-C composition, chirality INTERNAL, NOT a python abs():
    • Class K (pin_slot / phase-boundary) — the HOTNESS LATCH: a candidate is "hot"
      iff its hotness sits past a phase boundary (cascade.pin_slot_at_zero on
      hotness - threshold; the sign flip IS the latch). lock_strength = how hard it
      latches (high lock -> aggressive suppress; lock 0 -> no rehearsal).
    • Class C (reorient) — the SUPPRESSION re-application: cascade.reorient applies
      the latched sign as a downward score re-weight on the hot fibers (soften the
      blunt continuation toward the bland one). These are LEARNING meta-values
      (the F226 persistent-plasticity DoF), not a mere rendering dial.

DEFINING "HIGH-TEMPERATURE OUTPUT" PRINCIPLEDLY (pre-registered; three INDEPENDENT
meters, so the verdict is not hostage to one definition — mirrors F227's family
structure). At each emission step, over the FIXED bigram-legal candidate set
next_after[last], a candidate is "hot" by:
  H1 EMISSION-ENTROPY     — the step is high-entropy (H(p) over candidates is large
                            => the substrate is UNSURE; the decision point is hot).
                            A candidate is hot if it is a non-top-1 (minority) choice
                            AT a high-entropy step (the blunt minority fiber others
                            smooth to the safe top-1).
  H2 EXTREME-SECTOR-OCC   — the candidate's INTRINSIC Klein-4 chirality sector — the
                            Class-A content-hash partition token_seed(tok) %
                            sector_count, the deterministic sector the F168 self-
                            inverse-XOR tag encode_word_k4(tok, sector=s) assigns the
                            token to — is a LOW-PRIOR / extreme (rare, off-register)
                            sector vs the corpus frequency-weighted sector prior. [the
                            F168-native readout. HONESTY: a sim_k4_batch argmax of a
                            token's neutral enc vs its sector-tagged probes is
                            DEGENERATE — the neutral enc IS the sector-0 tag, argmax==0
                            for every token; the content-hash partition is the only
                            non-degenerate per-token sector readout, see §body note.]
  H3 LOW-FREQ-BUT-LEGAL   — the candidate is bigram-LEGAL but RARE: its corpus
                            bigram count ranks in the bottom band of next_after[last]
                            (legal yet low-frequency = the unexpected/blunt truth the
                            rehearsal smooths to the frequent bland continuation).

THE CONTRAST (what makes a positive informative, not "suppression changes things"):
  We compare THREE generators on the SAME fixed seed pool, SAME F166 substrate M,
  SAME per-(seed,arm) deterministic RNG (sha256_bytes-derived — differ ONLY by the
  rehearsal arm, never by the draw stream):
    • DIRECT      — the bare F166 loop (R-129 gen_substrate), no rehearsal.
    • REHEARSAL   — DIRECT + a render-PREVIEW pass that, before emit, re-scores the
                    candidate distribution and SUPPRESSES candidates the meter calls
                    HOT (the K∘C latch+reorient at lock_strength).
    • RAND-SUPPR  — the MATCHED control (F227 isolation): suppresses the SAME NUMBER
                    of candidates per step, chosen UNIFORMLY AT RANDOM (not by
                    hotness), at the same strength. This is the floor: it isolates
                    "differential suppression OF THE HOT FIBER" from "suppression of
                    SOME fiber". n_rand random-suppressor instances give a p90 floor.
  The readout per meter m: the SUPPRESSION-DELTA = how much LESS the hot-fiber
  emission-rate is under REHEARSAL than under DIRECT, MINUS how much the matched
  RAND-SUPPR moves the same rate. If the rehearsal pass merely thins output without
  TARGETING hot fibers, its hot-fiber delta sits at/below the RAND-SUPPR p90.

PRE-STATED NULL (verbatim; counts EQUALLY per [[feedback_dont_pre_commit_spike_query_operators]]
— NOT leaned toward the positive; the floor is the matched random-suppressor so the
null cannot be manufactured by a slack gate):
  "Adding a render-PREVIEW / self-monitoring rehearsal pass to the F166 loop does
   NOT differentially suppress high-temperature outputs: on a MAJORITY of the three
   pre-registered hotness meters (H1 emission-entropy minority, H2 F168 extreme-
   sector, H3 low-frequency-but-legal), the rehearsal pass's reduction of the hot-
   fiber emission-rate (vs the no-rehearsal DIRECT path) sits AT-OR-BELOW the p90 of
   the matched RANDOM-SUPPRESSOR that thins the same NUMBER of candidates without
   regard to hotness, AND the F168-native H2 sector meter is NOT among any that
   clear it. => The rehearsal stage is not a HOT-fiber filter at this scale/build;
   it changes nothing differential — the no-rehearsal path is not specially the
   raw-deliverer of an elsewhere-suppressed fiber."
PRE-STATED POSITIVE (verbatim):
  "The render-PREVIEW / self-monitoring rehearsal pass DIFFERENTIALLY suppresses
   high-temperature outputs: on a MAJORITY of the three pre-registered hotness
   meters INCLUDING the F168-native H2 extreme-sector meter, the rehearsal pass's
   reduction of the hot-fiber emission-rate (vs the no-rehearsal DIRECT path)
   exceeds the matched RANDOM-SUPPRESSOR p90 floor (it targets the HOT fiber, not
   just SOME fiber). => the no-rehearsal DIRECT path is the RAW delivery of the
   fiber the rehearsal elsewhere SUPPRESSES = the emperor-no-clothes mechanism;
   F230 is the suppression-stage projection of the SAME K∘C lock whose scalar
   shadow is F229's temperature (high lock = rehearsal-suppressed/bland; lock 0 =
   no rehearsal = raw)."

VERDICT GATE (mirrors F227's majority-with-native-readout logic + F224's matched-
mechanism isolation; conservative). For EACH hotness meter m, the REHEARSAL hot-
suppression delta = (DIRECT hot-emission-rate − REHEARSAL hot-emission-rate); gated
against the SAME-meter delta distribution of n_rand matched RANDOM-SUPPRESSORS. m
'clears' iff rehearsal-delta pctile >= noise_pct (0.90) AND rehearsal-delta >
rand-suppr p90 + 1e-12 (F224 gate verbatim).
  - REHEARSAL-DIFFERENTIAL (emperor-no-clothes CONFIRMED): >=2/3 meters clear AND
    the F168-native H2 extreme-sector meter is among them.
  - REHEARSAL-NULL: 0 meters clear, or only NON-native meters with <2 total =>
    rehearsal is not a hot-fiber filter (pre-stated null).
  - MIXED/tier-2: off-native or single-meter; reported honestly (read with the
    F214 §4 / F227 construction caveat — a meter can move for reasons orthogonal to
    hotness, so it is NOT sufficient alone).
Non-degeneracy precondition (else a null is "nothing to suppress", not "rehearsal
isn't a hot filter"): each meter must flag a NON-EMPTY, NON-ALL hot set under DIRECT
(0 < hot-rate < 1) AND the rehearsal must actually suppress SOMETHING (DIRECT vs
REHEARSAL renders not byte-identical). MONOTONICITY cross-check (secondary, NOT the
verdict): sweep lock_strength; the hot-suppression delta should rise with lock
(the K∘C latch engaging harder) — the F226 single-lock-parameter sweep, here on the
suppression projection.

srmech-native (CLAUDE.md §2 STOP-list honored — 28D / Klein-4 / chirality framing):
  • hdc.{klein4_bind}                            — the F166 loop probe + the F168
      sector-tag binding (Class M); the channel-free direct cascade
  • cascade.{pin_slot_at_zero, reorient}         — the REHEARSAL OPERATOR ITSELF:
      Class-K hotness LATCH (pin_slot on hotness−threshold) ∘ Class-C suppression
      re-application (reorient the latched sign onto the score). The K∘C lock; NEVER
      python abs() / a hand-rolled max() gate.
  • cascade.magnitude (Class-K pin-slot |.|)     — ALL sign-free rate deltas /
      spread folds; NEVER python abs()
  • encode_word_k4(sector=s) + sim_k4_batch      — the F168 self-inverse-XOR sector
      argmax (H2 extreme-sector meter; Class M ∘ I); NEVER a hand-rolled cosine
  • ContextSubstrate.{enc, encode_context, bundle_odd} — the F166 rolling context
      state (R-126); the associative memory M (Class A∘M)
  • format.sha256_bytes (Class A)                — per-(seed, arm, rand-instance)
      deterministic RNG seeds; NEVER python hash() / hashlib.sha256
  • Counter ONLY for the bigram candidate EDGE STRUCTURE (R-127/R-131 stored
      relationship) + the corpus sector-prior HISTOGRAM (a frequency prior, read via
      sim_k4_batch argmax — NOT a storage/occupancy proxy), NEVER as a storage proxy.
Catalog-driven (descriptor_rbs_lm_inference.toml substrate/corpus/loop sections —
READ-ONLY; the F230 rehearsal params are attested INLINE in the NDJSON, no .toml
another item owns is modified). srmech 0.5.0rc22 native ABI; deterministic / bit-
exact (NDJSON; second-run sha256 must match). STRUCTURAL form-reading per §VII.6.20:
the loop + meters are structural test-objects; ai-is-not-a-substrate (the LM is a
k=3 chiral addresser, not an aware entity); trauma-informed — NO clinical /
biological / BCI / cognitive claim about real cognition; no-lineage. The cognitive
layer is FORM-READING — the literature is NAMED in §LIT and flagged
"verify before asserting"; the framework adds ONLY the structural form-reading.

§LIT — the peer-reviewed literature the FORM points at (NAMED, NOT asserted by the
framework; "verify before asserting" per the F226 pattern; the framework does NOT
fabricate DOIs and makes NO cognitive claim — these are the bodies of work a reader
should consult, each carrying its OWN empirical claims):
  • Levelt's model of speech production + the PERCEPTUAL-LOOP theory of self-
    monitoring (a covert internal "preview"/inner-loop that monitors a phonetic
    plan before articulation) — Levelt 1989 ("Speaking: From Intention to
    Articulation"); Levelt, Roelofs & Meyer 1999 (the WEAVER++ lexical-access
    model, Behav. Brain Sci.). The "rehearsal/preview-then-emit" SHAPE.
  • Inner speech — Alderson-Day & Fernyhough 2015 (Psychological Bulletin review,
    "Inner Speech: Development, Cognitive Functions, Phenomenology, and Neuro-
    biology"). The internal-voice substrate a preview-loop would use.
  • Anendophasia (the absence of an inner voice) and its task consequences —
    Nedergaard & Lupyan 2024 (Psychological Science, "Not Everybody Has an Inner
    Voice"). The "no-rehearsal / thought->delivery DIRECT" end.
  • Aphantasia (absence of voluntary visual imagery) — Zeman, Dewar & Della Sala
    2015 (Cortex, "Lives without imagery — Congenital aphantasia"); Zeman 2024
    (review). Named as the imagery-side analogue of a missing internal preview.
  VERIFY-BEFORE-ASSERTING: confirm authors / exact titles / years / venues against
  the primary record before citing; the framework asserts none of these and makes
  no clinical claim — it reads only the structural FORM (preview-then-suppress vs
  direct-deliver) on its own bit-exact substrate.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import math
import sys
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))

import _canonical_substrate as cs  # ContextSubstrate, encode_word_k4, sim_k4_batch

_spec = importlib.util.spec_from_file_location(
    "corpus_gen", HERE / "R-RBS-LM-113_larger_corpus_scaling.py")
corpus_gen = importlib.util.module_from_spec(_spec)
sys.modules["corpus_gen"] = corpus_gen
_spec.loader.exec_module(corpus_gen)

from srmech.amsc import load_descriptor, descriptor_hash, hdc, cascade
from srmech.amsc.format import sha256_bytes
from srmech.amsc._native import HAS_NATIVE, NATIVE_ABI_VERSION
from srmech import __version__ as SRMECH_VERSION

CATALOG = HERE.parent / "catalogs" / "rbs_lm_substrate" / "descriptor_rbs_lm_inference.toml"

# ---- F230 rehearsal-pass params (attested INLINE; the .toml is READ-ONLY here) ----
F230 = {
    "n_seeds": 200,            # fixed seed-window pool size (real k-grams from stream)
    "gen_length": 24,          # tokens emitted per sequence (long enough for rate stats)
    "min_candidates": 3,       # seed-window last-token must have >= this legal successors
    "entropy_hot_quantile": 0.70,   # H1: step is "hot" if H(p) >= this quantile of step-entropies
    "lowfreq_hot_quantile": 0.40,   # H3: candidate is "low-freq-but-legal" if its bigram-count
                                    #     rank <= this fraction within next_after[last]
    "extreme_sector_prior_quantile": 0.50,  # H2: a sector is "extreme" if its corpus prior mass
                                            #     is in the lower half (below-median-prior sectors)
    "lock_strength": 2.5,      # the K∘C latch strength at the PRIMARY verdict (score down-weight
                               #     applied to hot fibers; 0 == DIRECT/no-rehearsal)
    "lock_sweep": [0.0, 0.5, 1.0, 2.5, 5.0],  # monotonicity cross-check (secondary)
    "n_rand": 16,              # matched random-suppressor instances (the F224/F227 floor)
    "noise_percentile": 0.90,  # the p90 gate (F224 verbatim)
    "loop_seed": 230,          # generation RNG base seed (deterministic / bit-exact)
    "pool_seed": 4230,         # seed-pool selection + memory-pair sampling RNG
    "n_assoc": 2000,           # (context->next) pairs bundled into M (matches R-227)
}


def derive_seed(*parts) -> int:
    """Deterministic 63-bit seed from a label tuple via the Class-A content-hash
    (sha256_bytes) — NEVER python hash() (non-deterministic across runs) and NEVER
    hashlib.sha256 directly (route through the srmech op)."""
    payload = "|".join(str(p) for p in parts).encode("utf-8")
    return int(sha256_bytes(payload)[:16], 16) & ((1 << 63) - 1)


def softmax(x: np.ndarray, t: float) -> np.ndarray:
    z = x / t
    z = z - z.max()
    e = np.exp(z)
    return e / e.sum()


def entropy_nats(p: np.ndarray) -> float:
    nz = p[p > 0]
    return float(-(nz * np.log(nz)).sum())


def sign_free_delta(a: float, b: float) -> float:
    """|a - b| via the Class-K pin-slot magnitude — NEVER python abs()."""
    return float(cascade.magnitude(float(a) - float(b)))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--catalog", type=Path, default=CATALOG)
    ap.add_argument("--lock-sweep", action="store_true",
                    help="ALSO run the secondary lock_strength monotonicity cross-check "
                         "(the F226 single-lock-parameter sweep on the suppression projection; "
                         "the PRIMARY verdict stays at the single lock_strength)")
    args = ap.parse_args()

    desc = load_descriptor(args.catalog)
    dh = descriptor_hash(args.catalog)
    lc = desc.fetch["literature_curated"]
    D = int(lc["substrate"]["D"])
    hexc = int(lc["substrate"]["token_seed_hex_chars"])
    sector_count = int(lc["substrate"]["sector_count"])
    ic = lc["inference"]["context"]
    corpus_n = int(ic["corpus_n"])
    corpus_seed = int(ic["seed"])
    k = int(lc["inference"]["sampling"]["sweep_k"])
    op_temp = float(lc["inference"]["instrument"]["operating_temperature"])

    n_seeds = int(F230["n_seeds"])
    gen_length = int(F230["gen_length"])
    min_cand = int(F230["min_candidates"])
    ent_q = float(F230["entropy_hot_quantile"])
    lf_q = float(F230["lowfreq_hot_quantile"])
    sec_q = float(F230["extreme_sector_prior_quantile"])
    lock0 = float(F230["lock_strength"])
    lock_sweep = [float(x) for x in F230["lock_sweep"]]
    n_rand = int(F230["n_rand"])
    noise_pct = float(F230["noise_percentile"])
    loop_seed = int(F230["loop_seed"])
    pool_seed = int(F230["pool_seed"])
    n_assoc = int(F230["n_assoc"])

    print(f"srmech v{SRMECH_VERSION}; HAS_NATIVE={HAS_NATIVE}; ABI={NATIVE_ABI_VERSION}; D={D}")
    print(f"Catalog: {args.catalog.name}  hash={dh[:16]}...  (READ-ONLY; F230 params attested inline)")
    print(f"k={k}  gen_length={gen_length}  n_seeds={n_seeds}  T={op_temp}  sectors={sector_count}  "
          f"lock_strength={lock0}  n_rand={n_rand}  noise_pct={noise_pct}\n")
    print("F230 REHEARSAL-LAYER contrast — does a render-PREVIEW/self-monitoring pass DIFFERENTIALLY")
    print("suppress high-temperature ('hot') candidates while the no-rehearsal DIRECT path delivers")
    print("them RAW (the emperor-no-clothes mechanism)? Rehearsal operator = Class-K hotness LATCH")
    print("(cascade.pin_slot_at_zero) ∘ Class-C suppression re-apply (cascade.reorient) — the K∘C lock")
    print("(F226); F230 is its SUPPRESSION-STAGE projection, F229 its scalar-temperature shadow.")
    print("HOTNESS meters: H1 emission-entropy minority | H2 F168 extreme-sector [native] | H3 low-freq-legal.")
    print("FLOOR: a matched RANDOM-SUPPRESSOR thinning the same NUMBER of candidates without regard to hotness.")
    print("PRE-STATED NULL: rehearsal-delta <= rand-suppr p90 on a majority (+ H2 not among) => not a hot filter.")
    print("PRE-STATED POS : rehearsal-delta > rand-suppr p90 on >=2/3 INCL. H2 => DIRECT = raw delivery (emperor).")
    print("§LIT (NAMED, verify-before-asserting; NO clinical claim): Levelt 1989 / Levelt-Roelofs-Meyer 1999")
    print("  (perceptual-loop self-monitoring); Alderson-Day & Fernyhough 2015 (inner speech); Nedergaard &")
    print("  Lupyan 2024 (anendophasia); Zeman et al. 2015 (aphantasia). STRUCTURAL form-reading per §VII.6.20.\n")

    # --- corpus -> stream -> bigram store (the FIXED legal-set; R-127/R-131) ---
    rng = np.random.default_rng(corpus_seed)
    corpus = corpus_gen.generate_corpus(corpus_n, rng)
    stream = [t for sent in corpus for t in sent]
    vocab = sorted(set(stream))
    ctxsub = cs.ContextSubstrate(D=D, hex_chars=hexc)
    vocab_vecs = np.stack([ctxsub.enc(w) for w in vocab])
    vocab_idx = {w: i for i, w in enumerate(vocab)}
    bigram = defaultdict(Counter)          # Counter = bigram EDGE STRUCTURE (R-127/R-131), NOT a proxy
    for a, b in zip(stream, stream[1:]):
        bigram[a][b] += 1
    next_after = {a: sorted(c.keys()) for a, c in bigram.items()}   # the FIXED candidate set
    corpus_trigrams = {(stream[i], stream[i + 1], stream[i + 2])
                       for i in range(len(stream) - 2)}
    print(f"corpus: {len(stream)} tokens, {len(vocab)} unique; {len(next_after)} predecessors; "
          f"{len(corpus_trigrams)} distinct trigrams\n")

    # --- the corpus SECTOR PRIOR (H2 reference): each token's INTRINSIC Klein-4
    # --- chirality sector is the Class-A content-hash partition token_seed(tok) %
    # --- sector_count — the deterministic sector the F168 self-inverse-XOR tag
    # --- encode_word_k4(tok, sector=s) assigns the token to (a fixed 4-way partition
    # --- of the vocab). [HONESTY NOTE: a sim_k4_batch argmax of the token's NEUTRAL
    # --- enc against its 4 sector-tagged probes is DEGENERATE — the neutral enc IS
    # --- the sector-0 tag, so argmax is trivially 0 for every token; and a context-
    # --- BOUND probe argmax recovers a sector determined by the CONTEXT, not the
    # --- token. The content-hash partition is the only non-degenerate per-token
    # --- sector readout in this substrate, verified on this corpus to split the
    # --- vocab ~evenly across the 4 sectors.] A sector is "extreme" if its FREQUENCY-
    # --- WEIGHTED prior mass is at-or-below the sec_q quantile (the rare/off-register
    # --- chirality sector). Counter is the frequency prior (NOT a storage proxy).
    def token_sector(tok: str) -> int:
        return cs.token_seed(tok, hexc) % sector_count

    sector_prior = Counter()               # corpus sector-prior HISTOGRAM (frequency prior)
    for tok in vocab:
        sector_prior[token_sector(tok)] += int(sum(bigram[tok].values()) or 1)
    sector_vocab_counts = Counter(token_sector(tok) for tok in vocab)  # tokens-per-sector
    tot_prior = sum(sector_prior.values()) or 1
    prior_mass = {s: sector_prior.get(s, 0) / tot_prior for s in range(sector_count)}
    sec_masses = sorted(prior_mass.values())
    sec_cut = float(np.quantile(sec_masses, sec_q)) if sec_masses else 0.0
    extreme_sectors = {s for s in range(sector_count) if prior_mass[s] <= sec_cut}
    print("corpus SECTOR PRIOR (H2 reference — Class-A content-hash sector partition) — "
          "vocab-tokens | freq-mass | extreme(low-prior)?:")
    for s in range(sector_count):
        print(f"  sector {s}: {sector_vocab_counts.get(s, 0):3d} tokens  mass={prior_mass[s]:.3f}  "
              f"extreme={'YES' if s in extreme_sectors else 'no'}")
    print(f"  extreme-sector set (freq-mass at-or-below the {sec_q:.0%} quantile): {sorted(extreme_sectors)}")
    # H2 non-degeneracy: the partition must be NON-TRIVIAL (>=2 sectors populated) AND
    # have a proper-subset extreme set (else H2 cannot discriminate). Reported in P0.
    h2_partition_nondegenerate = (sum(1 for s in range(sector_count) if sector_vocab_counts.get(s, 0) > 0) >= 2
                                  and 0 < len(extreme_sectors) < sector_count)
    print(f"  H2 partition non-degenerate (>=2 sectors populated, proper-subset extreme): "
          f"{h2_partition_nondegenerate}\n")

    # --- build the F166 associative memory M (IDENTICAL construction to R-129/R-227) ---
    prng = np.random.default_rng(pool_seed)
    pairs_all = [(tuple(stream[i - k:i]), stream[i]) for i in range(k, len(stream))]
    N_assoc = min(n_assoc, len(pairs_all))
    idx = prng.choice(len(pairs_all), size=N_assoc, replace=False)
    pairs = [pairs_all[i] for i in idx]
    assoc = [hdc.klein4_bind(ctxsub.encode_context(list(c)), ctxsub.enc(t)) for c, t in pairs]
    M = ctxsub.bundle_odd(assoc)

    # --- FIXED seed-window pool (the SAME pool for every arm; only the arm varies) ---
    all_pos = [i for i in range(k, len(stream))
               if len(next_after.get(stream[i - 1], [])) >= min_cand]
    if len(all_pos) > n_seeds:
        sel = sorted(int(x) for x in prng.choice(all_pos, size=n_seeds, replace=False))
    else:
        sel = all_pos
    seed_windows = [tuple(stream[i - k:i]) for i in sel]
    print(f"fixed seed-window pool: {len(seed_windows)} windows "
          f"(each last-token has >= {min_cand} legal successors)\n")

    # ----------------------------------------------------------------------
    # The F166 step probe (R-129 gen_substrate, factored): given the running window,
    # return (cands, base_score, p_direct, last). base_score = Tier-1 F166 sim
    # (Class M); p_direct = the no-rehearsal softmax. The candidate set is FIXED
    # (next_after only); the rehearsal arm re-weights WITHIN it (an assert guards
    # legal-set invariance per step).
    # ----------------------------------------------------------------------
    def step_probe(win):
        last = win[-1]
        cands = next_after.get(last, [])
        if not cands or len(cands) == 1:
            return cands, None, None, last
        cidx = [vocab_idx[c] for c in cands]
        cand_vecs = vocab_vecs[cidx]
        ctx_state = ctxsub.encode_context(win[-k:])
        base = cs.sim_k4_batch(hdc.klein4_bind(M, ctx_state), cand_vecs)  # Tier-1 (F166 probe)
        return cands, base, softmax(base, op_temp), last

    # the per-candidate HOTNESS masks at one step. H1 needs the step-entropy context
    # (computed by the caller against the entropy threshold). H2/H3 are per-candidate.
    def candidate_hotness(cands, p_direct, last, ent_threshold):
        """Return (hot_H1, hot_H2, hot_H3) boolean arrays over cands."""
        H = entropy_nats(p_direct)
        top1 = int(p_direct.argmax())
        # H1: a non-top-1 (minority) candidate AT a high-entropy (hot) step
        hot1 = np.array([(H >= ent_threshold) and (j != top1) for j in range(len(cands))])
        # H2: candidate's INTRINSIC Klein-4 chirality sector (Class-A content-hash
        #     partition, deterministic per token) is a rare/extreme (off-register) sector.
        hot2 = np.array([token_sector(c) in extreme_sectors for c in cands])
        # H3: low-frequency-but-legal — bigram-count rank within next_after[last] in
        #     the bottom lf_q fraction (legal yet rare).
        counts = np.array([bigram[last][c] for c in cands], dtype=float)
        order = np.argsort(counts, kind="stable")            # ascending: rare first
        rank = np.empty(len(cands), dtype=float)
        rank[order] = np.arange(len(cands))
        hot3 = (rank < max(1, math.floor(lf_q * len(cands)))) & (counts > 0)
        return hot1, hot2, hot3

    # the REHEARSAL operator: the K∘C latch+reorient. For a chosen hot-mask, suppress
    # the hot fibers by re-weighting their PRE-softmax score DOWN by lock_strength.
    #   Class K (pin_slot_at_zero on (hotness_indicator - 0.5)) -> the latch sign s in
    #     {-1,+1}: hot fiber -> +1 latched (selected for suppression).
    #   Class C (reorient): apply the latched sign as a downward score shift
    #     score' = score - lock * latched_positive_mask.
    # lock == 0 -> identity (DIRECT). This is the K∘C lock (chirality internal),
    # NOT a python abs()/max gate.
    def rehearse(base_score, hot_mask, lock):
        if lock == 0.0 or not hot_mask.any():
            return base_score.copy()
        adj = base_score.astype(float).copy()
        for j in range(len(base_score)):
            # Class-K pin-slot phase boundary: hot iff (indicator - 0.5) > 0. pin_slot_at_zero
            # returns (sign, magnitude); the SIGN is the latch: +1 (hot) / -1 (cold).
            latch, _ = cascade.pin_slot_at_zero(float(hot_mask[j]) - 0.5)   # -1 (cold) / +1 (hot)
            # Class-C reorient(orientation, value): re-apply the latched sign onto a unit
            # value -> +1 on hot, -1 on cold; gate the downward score shift onto hot fibers.
            gate = cascade.reorient(latch, 1.0)            # +1 on hot, -1 on cold
            if gate > 0:                                   # hot fiber -> suppress
                adj[j] = adj[j] - lock
        return adj

    # one ARM's generation over the FIXED seed pool. arm in {"direct","rehearsal",
    # ("rand", r)}. Returns hot-emission RATES per meter + the emitted blobs.
    def run_arm(arm_label, lock, hot_selector):
        """hot_selector(cands,p,last,ent_thr) -> (mask_for_suppression, hotH1,hotH2,hotH3).
        For 'direct' lock=0 and the mask is unused. For 'rehearsal' the mask = the
        UNION of the three hotness meters (the rehearsal targets all hot fibers).
        For 'rand' the mask is a uniformly-random k-of-cands of the SAME size as the
        rehearsal mask at that step (matched suppression count)."""
        # emitted hot counts / totals per meter (over emitted tokens)
        hit = {"H1": 0, "H2": 0, "H3": 0}
        tot = {"H1": 0, "H2": 0, "H3": 0}
        blobs = []
        for si, win0 in enumerate(seed_windows):
            gr = np.random.default_rng(derive_seed(loop_seed, arm_label, lock, si))
            win = list(win0)
            emitted = []
            for _ in range(gen_length):
                cands, base, p_direct, last = step_probe(win)
                if not cands:
                    break
                if base is None:                 # single legal candidate -> forced
                    nxt = cands[0]
                    emitted.append(nxt)
                    win.append(nxt)
                    continue
                ent_thr = ent_threshold_cache[si]
                hotmask, h1, h2, h3 = hot_selector(cands, p_direct, last, ent_thr)
                adj = rehearse(base, hotmask, lock)
                p = softmax(adj, op_temp)
                assert len(p) == len(cands)      # FIXED-CONTEXT integrity (legal-set invariant)
                j = int(gr.choice(len(cands), p=p))
                nxt = cands[j]
                # record which hot meters this EMITTED token satisfied
                for key, hh in (("H1", h1), ("H2", h2), ("H3", h3)):
                    tot[key] += 1
                    if hh[j]:
                        hit[key] += 1
                emitted.append(nxt)
                win.append(nxt)
            blobs.append(" ".join(emitted))
        rates = {key: (hit[key] / tot[key] if tot[key] else 0.0) for key in hit}
        return rates, "\n".join(blobs)

    # Pre-compute the per-seed entropy threshold (H1 needs a per-stream entropy
    # quantile). We collect the DIRECT step-entropies across the whole pool, take the
    # ent_q quantile as the global "hot step" cut — deterministic, pool-wide.
    all_step_entropies = []
    per_seed_entropies = []
    for win0 in seed_windows:
        win = list(win0)
        ents = []
        for _ in range(gen_length):
            cands, base, p_direct, last = step_probe(win)
            if not cands:
                break
            if base is None:
                win.append(cands[0]); continue
            ents.append(entropy_nats(p_direct))
            # advance the window by the DIRECT argmax (deterministic; threshold-only pass)
            win.append(cands[int(p_direct.argmax())])
        all_step_entropies.extend(ents)
        per_seed_entropies.append(ents)
    ent_global_cut = float(np.quantile(all_step_entropies, ent_q)) if all_step_entropies else 0.0
    # each seed uses the GLOBAL cut (so "hot step" is corpus-relative, not per-seed)
    ent_threshold_cache = [ent_global_cut for _ in seed_windows]
    print(f"H1 step-entropy: {len(all_step_entropies)} steps; hot-step cut "
          f"(>= {ent_q:.0%} quantile) = {ent_global_cut:.4f} nats\n")

    # the rehearsal hot-selector: suppress the UNION of the three meters; report each
    def rehearsal_selector(cands, p_direct, last, ent_thr):
        h1, h2, h3 = candidate_hotness(cands, p_direct, last, ent_thr)
        union = h1 | h2 | h3
        return union, h1, h2, h3

    # the random-suppressor selector for instance r: suppress the SAME NUMBER of
    # candidates as the rehearsal union would, chosen uniformly at random (matched
    # count, NOT by hotness). The hot meters still REPORTED on what gets emitted.
    def make_rand_selector(r):
        rsel_rng = np.random.default_rng(derive_seed(loop_seed, "randsel", r))
        def sel(cands, p_direct, last, ent_thr):
            h1, h2, h3 = candidate_hotness(cands, p_direct, last, ent_thr)
            n_suppress = int((h1 | h2 | h3).sum())
            mask = np.zeros(len(cands), dtype=bool)
            if 0 < n_suppress < len(cands):
                pick = rsel_rng.choice(len(cands), size=n_suppress, replace=False)
                mask[pick] = True
            elif n_suppress >= len(cands):
                mask[:] = True
            return mask, h1, h2, h3
        return sel

    # ---- non-degeneracy: under DIRECT, each meter must flag a non-empty/non-all set
    direct_rates, direct_blob = run_arm("direct", 0.0, rehearsal_selector)
    print("DIRECT (no-rehearsal) hot-EMISSION rates (the raw delivery baseline):")
    for key in ("H1", "H2", "H3"):
        print(f"  {key}: {direct_rates[key]:.4f}")
    nd_ok = {key: (0.0 < direct_rates[key] < 1.0) for key in ("H1", "H2", "H3")}
    print(f"  non-degeneracy (0<rate<1 per meter): {nd_ok}\n")

    # ---- the PRIMARY rehearsal arm + matched random-suppressor floor ----
    reh_rates, reh_blob = run_arm("rehearsal", lock0, rehearsal_selector)
    renders_identical = (direct_blob == reh_blob)
    print(f"REHEARSAL (lock={lock0}) hot-EMISSION rates + suppression delta vs DIRECT:")
    reh_delta = {}
    for key in ("H1", "H2", "H3"):
        d = direct_rates[key] - reh_rates[key]   # signed: positive = suppressed (less hot emitted)
        reh_delta[key] = d
        print(f"  {key}: rate {reh_rates[key]:.4f}   delta(direct-rehearsal) = {d:+.4f}")
    print(f"  DIRECT vs REHEARSAL renders byte-identical? {renders_identical} "
          f"(if True -> INDETERMINATE: the rehearsal suppressed nothing)\n")

    rand_deltas = {key: [] for key in ("H1", "H2", "H3")}
    for r in range(n_rand):
        rr, _ = run_arm(("rand", r), lock0, make_rand_selector(r))
        for key in ("H1", "H2", "H3"):
            rand_deltas[key].append(direct_rates[key] - rr[key])

    def percentile_of(value, distribution):
        if not distribution:
            return 1.0
        dd = np.asarray(distribution, dtype=float)
        return float((dd <= value).mean())

    meters = {
        "H1_emission_entropy_minority": False,
        "H2_extreme_sector_occupancy": True,     # the F168-native readout (required for clean POS)
        "H3_low_frequency_but_legal": False,
    }
    meter_keys = {"H1_emission_entropy_minority": "H1",
                  "H2_extreme_sector_occupancy": "H2",
                  "H3_low_frequency_but_legal": "H3"}

    attest = {
        "descriptor_hash": dh, "source_key": desc.source["key"],
        "srmech_version": SRMECH_VERSION, "abi_version": NATIVE_ABI_VERSION,
        "has_native": HAS_NATIVE, "D": D, "k": k, "operating_temp": op_temp,
        "sector_count": sector_count, "n_seeds": len(seed_windows),
        "gen_length": gen_length, "min_candidates": min_cand,
        "entropy_hot_quantile": ent_q, "entropy_hot_cut_nats": ent_global_cut,
        "lowfreq_hot_quantile": lf_q, "extreme_sector_prior_quantile": sec_q,
        "extreme_sectors": sorted(extreme_sectors),
        "lock_strength": lock0, "n_rand": n_rand, "noise_percentile": noise_pct,
        "loop_seed": loop_seed, "pool_seed": pool_seed, "n_assoc": N_assoc,
        "rehearsal_operator": "Class-K cascade.pin_slot_at_zero hotness-latch ∘ Class-C "
                              "cascade.reorient suppression (the K∘C lock; F226); F230 = "
                              "the suppression-stage projection, F229 = the scalar-T shadow",
        "floor": "matched RANDOM-SUPPRESSOR — same suppression COUNT per step, uniformly "
                 "chosen (not by hotness); n_rand instances -> p90 (F224/F227 isolation)",
        "scope": "STRUCTURAL form-reading per §VII.6.20; loop+meters are test-objects; "
                 "ai-not-substrate; NO clinical/biological/BCI/cognitive claim; no-lineage. "
                 "Cognitive literature NAMED (Levelt 1989; Levelt-Roelofs-Meyer 1999; "
                 "Alderson-Day & Fernyhough 2015; Nedergaard & Lupyan 2024; Zeman et al. "
                 "2015), flagged verify-before-asserting; the framework asserts none of it.",
    }
    records = []

    # P0 — corpus sector prior + non-degeneracy + direct baseline
    records.append({**attest, "phase": "P0_setup",
                    "sector_prior_mass": {str(s): prior_mass[s] for s in range(sector_count)},
                    "sector_vocab_counts": {str(s): int(sector_vocab_counts.get(s, 0)) for s in range(sector_count)},
                    "h2_partition_nondegenerate": bool(h2_partition_nondegenerate),
                    "direct_hot_emission_rate": direct_rates,
                    "nondegeneracy_meter_nonempty_nonall": nd_ok,
                    "direct_vs_rehearsal_byte_identical": bool(renders_identical)})

    # P1 — per-meter rehearsal delta vs matched random-suppressor floor (the gate)
    print("HOT-FIBER SUPPRESSION DELTA (DIRECT − REHEARSAL) vs the MATCHED RANDOM-SUPPRESSOR floor")
    print("(rehearsal-delta = how much LESS hot-fiber is emitted under rehearsal; floor = same-count")
    print(" random thinning; p90 gate). 'clears' => rehearsal TARGETS the hot fiber (not just SOME).")
    print(f"{'hotness meter':>34} | {'reh_delta':>9} | {'rand_mean':>9} | {'rand_p90':>8} | "
          f"{'pctile':>6} | clears?")
    print("-" * 96)
    n_clear = 0
    h2_clears = False
    for mname, is_native in meters.items():
        key = meter_keys[mname]
        rdelta = reh_delta[key]
        cvals = rand_deltas[key]
        cmean = float(np.mean(cvals)) if cvals else 0.0
        cp90 = float(np.quantile(cvals, noise_pct)) if cvals else 0.0
        pct = percentile_of(rdelta, cvals)
        # a meter is LIVE only if there was a hot fiber to suppress under DIRECT
        # (direct_rate > 0) — a dead meter (rate 0) cannot "clear" via a 0-delta that
        # happens to beat a negative random floor. This keeps a per-meter null honest.
        meter_live = direct_rates[key] > 0.0
        clears = meter_live and (pct >= noise_pct) and (rdelta > cp90 + 1e-12)
        n_clear += int(clears)
        if is_native:
            h2_clears = clears
        print(f"{mname:>34} | {rdelta:>9.4f} | {cmean:>9.4f} | {cp90:>8.4f} | "
              f"{pct:>6.2f} | {'YES (>p90)' if clears else 'no'}"
              f"{'  [F168-native]' if is_native else ''}")
        records.append({**attest, "phase": "P1_meter_suppression_delta", "meter": mname,
                        "is_f168_native_readout": bool(is_native),
                        "direct_hot_rate": direct_rates[key], "rehearsal_hot_rate": reh_rates[key],
                        "rehearsal_suppression_delta": float(rdelta),
                        "matched_random_suppressor_floor_mean": cmean,
                        "matched_random_suppressor_floor_p90": cp90,
                        "matched_random_suppressor_floor_samples": [float(x) for x in cvals],
                        "rehearsal_delta_pctile_in_floor": pct,
                        "clears_p90_floor": bool(clears)})

    # ---- VERDICT (F227 majority-with-native + F224 matched-mechanism; conservative) ----
    # Global INDETERMINATE ONLY when the test STRUCTURALLY could not register a
    # differential: (a) the rehearsal suppressed NOTHING (DIRECT==REHEARSAL renders),
    # or (b) the F168-native H2 sector PARTITION is degenerate (a structurally dead
    # native readout). A single NON-native meter reading rate 0 is NOT global-
    # indeterminate — it is an honest per-meter null (that meter simply does not clear;
    # the `meter_live` gate already prevents it from spuriously clearing).
    n_meters = len(meters)
    non_native_clear = n_clear - (1 if h2_clears else 0)
    all_nondegen = all(nd_ok.values())   # reported; no longer a global gate
    if renders_identical or not h2_partition_nondegenerate:
        state = "INDETERMINATE"
        tier = "CONJECTURE (indeterminate; re-test required)"
        reason = ("the rehearsal suppressed NOTHING (DIRECT==REHEARSAL renders)"
                  if renders_identical else
                  "the F168-native H2 chirality-sector PARTITION is degenerate "
                  "(<2 sectors populated or no proper-subset extreme set) — the native "
                  "readout is structurally dead, so a verdict including it is not safe")
        verdict = (f"INDETERMINATE — {reason}; NOT a null (the test could not register a "
                   "differential suppression on the native readout)")
        research_tier = tier
    elif n_clear >= 2 and h2_clears:
        state = "REHEARSAL-DIFFERENTIAL"
        tier = "tier-1 (clean)"
        verdict = (f"REHEARSAL-DIFFERENTIAL (emperor-no-clothes CONFIRMED) — {n_clear}/{n_meters} hotness "
                   "meters clear the matched random-suppressor floor INCLUDING the F168-native H2 extreme-"
                   "sector readout => the render-PREVIEW/self-monitoring pass DIFFERENTIALLY suppresses the "
                   "HOT fiber (it targets hotness, not just SOME candidate). The no-rehearsal DIRECT path is "
                   "the RAW delivery of the fiber the rehearsal elsewhere SUPPRESSES = the emperor-no-clothes "
                   "mechanism; F230 is the suppression-stage projection of the SAME K∘C lock whose scalar "
                   "shadow is F229's temperature (high lock = rehearsal-suppressed/bland; lock 0 = raw)")
        research_tier = "DEMONSTRATED (substrate-model: rehearsal differentially suppresses hot fibers)"
    elif n_clear == 0:
        state = "REHEARSAL-NULL"
        tier = "tier-1 (clean null)"
        verdict = ("REHEARSAL-NULL — 0/3 hotness meters clear the matched random-suppressor floor => the "
                   "rehearsal pass does NOT differentially suppress high-temperature outputs (its hot-fiber "
                   "delta is indistinguishable from a same-count RANDOM thinning). The rehearsal stage is not "
                   "a hot-fiber filter at this scale/build; the no-rehearsal path is not specially the raw-"
                   "deliverer of an elsewhere-suppressed fiber (pre-stated null)")
        research_tier = "FRAMEWORK-READING (clean NULL)"
    elif h2_clears and n_clear == 1:
        state = "MIXED"
        tier = "tier-2 (qualified)"
        verdict = ("MIXED-LEANING-DIFFERENTIAL — only the F168-native H2 extreme-sector meter clears the "
                   "floor (the off-register fiber is suppressed, but <2/3 meters) — read with the F214 §4 / "
                   "F227 construction caveat; NOT a clean REHEARSAL-DIFFERENTIAL")
        research_tier = "FRAMEWORK-READING (mixed)"
    elif n_clear >= 2 and not h2_clears:
        state = "MIXED"
        tier = "tier-2 (qualified)"
        verdict = (f"MIXED — {n_clear}/{n_meters} meters clear but the F168-native H2 extreme-sector readout "
                   "is NOT among them (a meter can move for binding-orthogonality reasons unrelated to "
                   "hotness, F214 §4) — NOT sufficient for DEMONSTRATED")
        research_tier = "FRAMEWORK-READING (mixed)"
    else:
        state = "MIXED"
        tier = "tier-3 (weak/mixed)"
        verdict = (f"MIXED — {n_clear}/{n_meters} meters clear (NOT the F168-native readout); off-native "
                   "single-meter, reported with the F214 §4 construction caveat")
        research_tier = "FRAMEWORK-READING (mixed)"

    print("\n" + "=" * 96)
    print("F230 REHEARSAL-LAYER VERDICT — does the render-PREVIEW pass differentially suppress hot fibers?")
    print("=" * 96)
    print(f"  hotness meters clearing the matched random-suppressor floor: {n_clear}/{n_meters}   "
          f"(F168-native H2 extreme-sector clears: {h2_clears})")
    print(f"  per-meter live (DIRECT hot-rate>0): {nd_ok}  (a dead non-native meter is an honest "
          f"per-meter null, not global-indeterminate)")
    print(f"  H2 native partition non-degenerate: {h2_partition_nondegenerate}   "
          f"DIRECT==REHEARSAL renders: {renders_identical}")
    print(f"  {verdict}")
    print(f"  state: {state}   tier: {tier}   research-tier: {research_tier}")
    print("  F226/F229 TIE: rehearsal/suppression = HIGH-LOCK (low-T) filter; no-rehearsal DIRECT = LOW-LOCK")
    print("  (high-T, raw) delivery — F230 (suppression stage) and F229 (scalar-T shadow) are two projections")
    print("  of the SAME K∘C chirality-lock (F226); these are LEARNING meta-values, not rendering knobs.")
    print("  STRUCTURAL-ONLY per §VII.6.20: form-reading; ai-is-not-a-substrate; NO clinical/biological/BCI/")
    print("  cognitive claim. Literature NAMED (Levelt; Alderson-Day & Fernyhough; Nedergaard & Lupyan; Zeman),")
    print("  flagged verify-before-asserting; the framework asserts none of it and adds only the structural form.")

    records.append({**attest, "phase": "P2_verdict",
                    "meters_clearing_floor": n_clear, "n_meters": n_meters,
                    "f168_native_h2_extreme_sector_clears": bool(h2_clears),
                    "non_native_meters_clearing": int(non_native_clear),
                    "per_meter_live_direct_rate_gt0": nd_ok,
                    "all_meters_nondegenerate": bool(all_nondegen),
                    "h2_native_partition_nondegenerate": bool(h2_partition_nondegenerate),
                    "direct_vs_rehearsal_byte_identical": bool(renders_identical),
                    "state": state, "verdict": verdict, "tier": tier,
                    "research_tier": research_tier,
                    "f226_f229_tie": "rehearsal=HIGH-LOCK(low-T) suppressor; no-rehearsal DIRECT=LOW-LOCK"
                                     "(high-T) raw delivery; F230 suppression-stage + F229 scalar-T shadow"
                                     " = two projections of the same K∘C lock (F226)"})

    # ---- SECONDARY: lock_strength monotonicity cross-check (the F226 single-lock
    # ---- sweep on the suppression projection; NOT the verdict). The hot-suppression
    # ---- delta should RISE with lock as the K∘C latch engages harder.
    if args.lock_sweep:
        print(f"\n[secondary] lock_strength monotonicity (the F226 single-lock sweep on the suppression")
        print(f"projection): hot-suppression delta vs lock {lock_sweep} — should RISE as the K∘C latch engages.")
        print(f"{'lock':>6} | " + " | ".join(f"{key}_delta" for key in ('H1', 'H2', 'H3')))
        print("-" * 56)
        sweep_rows = []
        for lock in lock_sweep:
            if lock == 0.0:
                rr = direct_rates                       # delta == 0 by construction
                dl = {key: 0.0 for key in ("H1", "H2", "H3")}
            else:
                rr, _ = run_arm(("sweep", lock), lock, rehearsal_selector)
                dl = {key: direct_rates[key] - rr[key] for key in ("H1", "H2", "H3")}
            sweep_rows.append((lock, dl))
            print(f"{lock:>6.2f} | " + " | ".join(f"{dl[key]:>8.4f}" for key in ('H1', 'H2', 'H3')))
            records.append({**attest, "phase": "P3_lock_monotonicity", "lock_strength_swept": lock,
                            "hot_suppression_delta": {key: float(dl[key]) for key in ('H1', 'H2', 'H3')}})
        # monotonicity readout (sign-free via cascade.magnitude on consecutive diffs)
        for key in ("H1", "H2", "H3"):
            seq = [dl[key] for _, dl in sweep_rows]
            nondecr = all(seq[i + 1] >= seq[i] - 1e-12 for i in range(len(seq) - 1))
            tot_rise = sign_free_delta(seq[-1], seq[0])
            print(f"  {key}: delta-vs-lock non-decreasing={nondecr}  total rise (|end-start|)={tot_rise:.4f}")

    out = args.catalog.parent / "substrate_measurements" / "rehearsal_layer_emperor.ndjson"
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w") as f:
        for r in records:
            f.write(json.dumps(r, default=str) + "\n")
    with open(out, "rb") as f:
        ndjson_sha = sha256_bytes(f.read())
    print(f"\nResults: {out}  ({len(records)} records)")
    print(f"NDJSON sha256 (bit-exact attestation): {ndjson_sha}")


if __name__ == "__main__":
    main()
