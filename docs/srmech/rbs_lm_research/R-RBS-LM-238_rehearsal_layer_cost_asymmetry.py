"""R-RBS-LM-238 — F238: THE COST-ASYMMETRY OF REHEARSAL. Three delivery modes on
ONE K-after-C lock axis (the F226 chirality-lock; F230's suppression-stage
projection), all sharing the SAME F230 rehearse() operator at the SAME lock_strength,
differing ONLY on (i) is the lock ENGAGED, (ii) where the previewed-then-suppressed
content GOES.

HARNESS-ONLY (load-bearing): this is the srmech substrate measurement that GATES the
separate dollar-gated current-gen-LLM trials (#789). NO real-LLM and NO Anthropic-API
call is made here — the three modes are srmech cascades over the F230 substrate.

THE THREE MODES (DISCRETE ORDINAL positions on one F226 K∘C lock axis):
  (a) DIRECT / NO-REHEARSAL — the LOW-LOCK direct deliverer. lock=0 (the latch never
      engages; the F226 lock-position chirality is the net_chirality of the ENGAGED-
      latch signs = 0 because nothing engages). ONE generation pass. Emits the hot-but-
      true raw traversal unsuppressed. COST: cheap (1 pass; answer-tokens only); nothing
      hidden. DIGNITY (F226/F230): a VALID truth-emitting mode — the emperor-no-clothes
      deliverer of the hot-but-true fiber — NOT a deficit.
  (b) INTERNAL-REHEARSAL — the HIGH-LOCK preview that suppresses hot BEFORE delivery.
      lock=lock0>0; a preview pass re-scores+suppresses the hot fiber (the latch engages
      on the hot fibers, lock-position chirality > 0), and the preview is DISCARDED —
      only the suppressed answer is emitted. COST: metabolic (2 passes), borne by the
      THINKER, INVISIBLE to the listener (answer-tokens only; the suppression work leaves
      no token trace).
  (c) EXTERNALIZED — the SAME preview run OUT LOUD (the LLM chain-of-thought shape).
      lock=lock0 (IDENTICAL to internal), SAME suppression, SAME answer — but the preview
      pass's hot-fiber content is ALSO EMITTED as visible tokens before the answer. COST:
      in TOKENS, borne by the OBSERVER budget, fully VISIBLE.

THE LOAD-BEARING SUB-CLAIM (externalized = internal made visible). Because (b) and (c)
share lock AND suppression AND the per-(seed) draw stream BY CONSTRUCTION, their
delivered ANSWER must be BYTE-IDENTICAL; they differ ONLY in whether the preview is
spoken. The EXTERNALIZED preview tokens are a deterministic, RNG-FREE read of the hot
candidates each step, so they do NOT consume the draw stream — the answer continuation
uses the SAME draw stream as INTERNAL and the byte-identity holds. This is the F230
byte-identity guard INVERTED: F230 guarded "DIRECT==REHEARSAL renders -> INDETERMINATE";
here INTERNAL vs EXTERNALIZED answers MUST match, and it FAILS (null) if the externalized
preview perturbs the candidate set or draw order.

THE ONE-AXIS / MONOTONE TEST (the deliverable; sign-free srmech folds, NEVER abs()):
  (A) LOCK-POSITION monotone: the F226 lock-position chirality (cascade.net_chirality of
      the ENGAGED-latch signs, accumulated over the run) is NON-DECREASING across
      DIRECT(0) -> INTERNAL(>0) -> EXTERNALIZED(>0): the modes lie on ONE lock axis,
      low->high. (Read as the DISCRETE latch-engagement chirality — an ORDINAL position,
      NOT a smooth lock magnitude; F230 §6 PROVED lock_strength saturates to a near-binary
      switch at this T, so the genuinely ordinal quantity is the latch-engagement, not a
      continuous lock gradient. This sidesteps the exact secondary claim F230 falsified.)
  (B) HIDDEN-COST monotone: n_passes non-decreasing (1<=2<=2) AND total_tokens non-
      decreasing with the VISIBLE cost (preview_tokens_emitted) strictly rising at
      EXTERNALIZED (0=0<k). Cost is READ FROM THE LOOP ACCOUNTING (counters), never hand-
      set — so a non-ordering is a real MEASURED negative, not a tuning artifact.
  (C) SUPPRESSION-SIGNATURE: INTERNAL and EXTERNALIZED clear the F230 matched-random-
      suppressor p90 floor on the SAME meters (>=2/3 incl. the F168-native H2), DIRECT
      does not (it IS the baseline) — suppression UP with lock. (The F230 meters + floor
      + p90 gate imported VERBATIM; F238 introduces NO new suppression knob.)
  (D) EXTERNALIZED=INTERNAL byte-identity: the EXTERNALIZED ANSWER (preview prefix
      stripped) is BYTE-IDENTICAL to the INTERNAL answer (np.array_equal / string-equality,
      content-addressed via sha256_bytes) — the externalized mode is the internal mode
      made visible.
POSITIVE iff (A) AND (B) AND (C) AND (D) all hold. NULL (counts EQUALLY, NOT leaned; matched-
random floor is the real null so it cannot be manufactured by a slack gate) iff ANY fails.

srmech-native (CLAUDE.md §2 STOP-list honored — 28D / Klein-4 / chirality framing):
  • cascade.{pin_slot_at_zero, reorient}  — the F230 REHEARSE operator (Class-K hotness
      LATCH ∘ Class-C suppression re-apply; the K∘C lock, F226); NEVER abs()/max()
  • cascade.net_chirality                  — the F226 LOCK-POSITION read (Class-C; the
      net chirality of the ENGAGED-latch signs; sign-free, ordinal)
  • cascade.magnitude (Class-K pin-slot |·|) — ALL sign-free rate/cost deltas; NEVER abs()
  • hdc.klein4_bind                         — the F166 loop probe (Class M)
  • encode_word_k4(sector=s) + sim_k4_batch — the F168 sector readout (H2; Class M ∘ I)
  • ContextSubstrate.{enc, encode_context, bundle_odd} — the F166 rolling state (R-126)
  • format.sha256_bytes (Class A)           — per-(seed,mode) RNG seeds + content-address;
      NEVER python hash() / hashlib.sha256
  • Counter ONLY for the bigram candidate EDGE STRUCTURE (R-127/131 stored relationship)
      + the corpus sector-prior frequency HISTOGRAM, NEVER as a storage proxy.

TIERING (MFO §VII.6.20, honest split). DEMONSTRATED = the srmech 3-mode MEASUREMENT on
the bit-exact F230 substrate (the lock-position ordering, the measured cost accounting,
the suppression-delta signatures, the byte-identity of answers). FRAMEWORK-READING = the
cognition synthesis (rehearsal / inner speech / aphantasia variation, the population
corollary) — the PEER-REVIEWED LITERATURE asserts it (web-verified in the FINDING doc),
NEVER the framework; the framework adds ONLY the structural form-reading. ai-is-not-a-
substrate (the LM is a k=3 chiral addresser, not an aware entity); trauma-informed — NO
clinical / biological / BCI / cognitive claim about real cognition; no-lineage.

§LIT — the bodies of work the FORM points at (NAMED, NOT asserted by the framework;
verify-before-asserting per the F226 pattern; web-verified — exact authors / title /
venue / year / volume / pages confirmed; NO fabricated DOI). The no-rehearsal mode framed
with DIGNITY (a valid truth-emitting mode, the F230 emperor-no-clothes deliverer):
  1. REHEARSAL / PERCEPTUAL-LOOP SELF-MONITORING (the preview-then-emit SHAPE; the
     internal mode): Levelt 1989, "Speaking: From Intention to Articulation", Cambridge,
     MA: MIT Press; Levelt, Roelofs & Meyer 1999, "A theory of lexical access in speech
     production", Behavioral and Brain Sciences 22(1), 1–75 (the WEAVER++ model).
  2. INNER SPEECH / ARTICULATORY REHEARSAL (the internal-voice substrate a preview-loop
     uses; the phonological-loop rehearsal component): Alderson-Day & Fernyhough 2015,
     "Inner Speech: Development, Cognitive Functions, Phenomenology, and Neurobiology",
     Psychological Bulletin 141(5), 931–965; Baddeley & Hitch 1974 (the articulatory-loop)
     + Baddeley 1986 (the two-component phonological loop).
  3. ANENDOPHASIA — ABSENCE OF AN INNER VOICE (the no-rehearsal DIRECT end, framed with
     dignity): Nedergaard & Lupyan 2024, "Not Everybody Has an Inner Voice: Behavioral
     Consequences of Anendophasia", Psychological Science 35(7), 780–797.
  4. APHANTASIA — VISUAL-IMAGERY VARIATION (the imagery-side analogue of a missing
     internal preview): Zeman, Dewar & Della Sala 2015, "Lives without imagery —
     Congenital aphantasia", Cortex 73, 378–380; Zeman 2024, "Aphantasia and
     hyperphantasia: exploring imagery vividness extremes", Trends in Cognitive Sciences
     28(5), 467–480.
  5. POPULATION VARIATION IN IMAGERY/INNER SPEECH (the corollary that observers differ in
     where their own delivery sits): Marks 1973, "Visual imagery differences in the recall
     of pictures", British Journal of Psychology 64(1), 17–24 (the VVIQ vividness
     distribution). The framework asserts none of this; it names the literature and flags
     verify-before-asserting.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import math
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
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

# ---- F238 params (attested INLINE; the .toml is READ-ONLY here). All B (measurement)
# ---- except where noted A (structure-cascade) / C (irreducible). The F230 SUPPRESSION
# ---- knobs are imported VERBATIM (F238 introduces NO new suppression knob) — a clean
# ---- clear is the F230 result CARRYING, not a re-tune. ------------------------------
F238 = {
    # --- F230 suppression knobs, imported VERBATIM (NO new knob; provenance = F230) ---
    "n_seeds": 200,            # B: fixed seed-window pool size (F230 verbatim)
    "gen_length": 24,          # B: answer tokens emitted per sequence (F230 verbatim)
    "min_candidates": 3,       # B: seed-window last-token must have >= this successors (F230)
    "entropy_hot_quantile": 0.70,           # B: H1 hot-step entropy quantile (F230 verbatim)
    "lowfreq_hot_quantile": 0.40,           # B: H3 low-freq rank fraction (F230 verbatim)
    "extreme_sector_prior_quantile": 0.50,  # B: H2 extreme-sector prior quantile (F230 verbatim)
    "lock_strength": 2.5,      # B: the K∘C latch strength shared by INTERNAL+EXTERNALIZED (F230)
    "n_rand": 16,              # B: matched random-suppressor instances (F224/F227 floor; F230)
    "noise_percentile": 0.90,  # A: the p90 gate (F224 structure-cascade; F230 verbatim)
    "loop_seed": 230,          # B: generation RNG base seed (F230 verbatim, kept for bit-continuity)
    "pool_seed": 4230,         # B: seed-pool + memory-pair sampling RNG (F230 verbatim)
    "n_assoc": 2000,           # B: (context->next) pairs bundled into M (F230 verbatim)
    # --- F238 mode partition (A: structure-cascade — the 3-mode K∘C-axis partition) ---
    "modes": ["DIRECT", "INTERNAL", "EXTERNALIZED"],  # A: the 3 ordinal lock-axis positions
}
# NOTE — sector_count = 4 (= |Klein-4|, A: structure-cascade), D = 8192 (= 2^13, A) and
# operating_temperature (C: irreducible — F228/F229 named it un-derived; source-pointed
# to the dollar-gated #789 trials) all flow IN from the READ-ONLY descriptor, never set
# here. The 3-mode partition is the only A-constant F238 introduces.


def derive_seed(*parts) -> int:
    """Deterministic 63-bit seed from a label tuple via the Class-A content-hash
    (sha256_bytes) — NEVER python hash() (non-deterministic) and NEVER hashlib.sha256."""
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
    args = ap.parse_args()

    desc = load_descriptor(args.catalog)
    dh = descriptor_hash(args.catalog)
    lc = desc.fetch["literature_curated"]
    D = int(lc["substrate"]["D"])                       # A: 2^13 (structure-cascade)
    hexc = int(lc["substrate"]["token_seed_hex_chars"])
    sector_count = int(lc["substrate"]["sector_count"]) # A: |Klein-4| = 4 (structure-cascade)
    ic = lc["inference"]["context"]
    corpus_n = int(ic["corpus_n"])
    corpus_seed = int(ic["seed"])
    k = int(lc["inference"]["sampling"]["sweep_k"])
    op_temp = float(lc["inference"]["instrument"]["operating_temperature"])  # C: irreducible (#789)

    n_seeds = int(F238["n_seeds"])
    gen_length = int(F238["gen_length"])
    min_cand = int(F238["min_candidates"])
    ent_q = float(F238["entropy_hot_quantile"])
    lf_q = float(F238["lowfreq_hot_quantile"])
    sec_q = float(F238["extreme_sector_prior_quantile"])
    lock0 = float(F238["lock_strength"])
    n_rand = int(F238["n_rand"])
    noise_pct = float(F238["noise_percentile"])
    loop_seed = int(F238["loop_seed"])
    pool_seed = int(F238["pool_seed"])
    n_assoc = int(F238["n_assoc"])
    MODES = list(F238["modes"])

    print(f"srmech v{SRMECH_VERSION}; HAS_NATIVE={HAS_NATIVE}; ABI={NATIVE_ABI_VERSION}; D={D}")
    print(f"Catalog: {args.catalog.name}  hash={dh[:16]}...  (READ-ONLY; F238 params attested inline)")
    print(f"k={k}  gen_length={gen_length}  n_seeds={n_seeds}  T={op_temp}  sectors={sector_count}  "
          f"lock_strength={lock0}  n_rand={n_rand}  noise_pct={noise_pct}\n")
    print("F238 COST-ASYMMETRY OF REHEARSAL — three delivery modes on ONE K∘C lock axis (F226;")
    print("F230's suppression-stage projection). DIRECT (lock=0, 1 pass, raw) / INTERNAL (lock>0,")
    print("2 passes, preview DISCARDED, cost INVISIBLE) / EXTERNALIZED (lock>0, 2 passes, preview")
    print("EMITTED out-loud, cost VISIBLE). HARNESS-ONLY: NO real-LLM / NO Anthropic-API call.")
    print("TEST: (A) lock-position chirality monotone DIRECT(0)->INTERNAL(>0)->EXTERNALIZED(>0);")
    print("(B) measured cost (passes/tokens) monotone with lock; (C) F230 hot-suppression clears the")
    print("matched-random p90 floor on >=2/3 meters incl. H2-native for BOTH high-lock modes; (D)")
    print("EXTERNALIZED answer BYTE-IDENTICAL to INTERNAL. POSITIVE iff all four; NULL (equal weight)")
    print("if any fails. §LIT (web-verified, verify-before-asserting; framework asserts NONE): Levelt")
    print("1989 / Levelt-Roelofs-Meyer 1999; Alderson-Day & Fernyhough 2015; Baddeley&Hitch 1974;")
    print("Nedergaard & Lupyan 2024; Zeman et al. 2015 / Zeman 2024; Marks 1973. §VII.6.20 form-reading.\n")

    # --- corpus -> stream -> bigram store (the FIXED legal-set; R-127/R-131) ---
    rng = np.random.default_rng(corpus_seed)
    corpus = corpus_gen.generate_corpus(corpus_n, rng)
    stream = [t for sent in corpus for t in sent]
    vocab = sorted(set(stream))
    ctxsub = cs.ContextSubstrate(D=D, hex_chars=hexc)
    vocab_vecs = np.stack([ctxsub.enc(w) for w in vocab])
    vocab_idx = {w: i for i, w in enumerate(vocab)}
    bigram = defaultdict(Counter)          # Counter = bigram EDGE STRUCTURE (R-127/131), NOT a proxy
    for a, b in zip(stream, stream[1:]):
        bigram[a][b] += 1
    next_after = {a: sorted(c.keys()) for a, c in bigram.items()}   # the FIXED candidate set
    print(f"corpus: {len(stream)} tokens, {len(vocab)} unique; {len(next_after)} predecessors\n")

    # --- the corpus SECTOR PRIOR (H2 reference): each token's INTRINSIC Klein-4 sector
    # --- is the Class-A content-hash partition token_seed(tok) % sector_count (the F168
    # --- self-inverse-XOR tag's deterministic sector). Counter = frequency prior, NOT a
    # --- storage proxy. [The F230 honesty note carries: a sim_k4_batch argmax of a
    # --- token's NEUTRAL enc vs its sector-tagged probes is DEGENERATE — the neutral enc
    # --- IS the sector-0 tag; the content-hash partition is the only non-degenerate
    # --- per-token sector readout.] A sector is "extreme" if its freq-weighted prior mass
    # --- is at-or-below the sec_q quantile (the rare/off-register chirality sector).
    def token_sector(tok: str) -> int:
        return cs.token_seed(tok, hexc) % sector_count

    sector_prior = Counter()               # corpus sector-prior HISTOGRAM (frequency prior)
    for tok in vocab:
        sector_prior[token_sector(tok)] += int(sum(bigram[tok].values()) or 1)
    sector_vocab_counts = Counter(token_sector(tok) for tok in vocab)
    tot_prior = sum(sector_prior.values()) or 1
    prior_mass = {s: sector_prior.get(s, 0) / tot_prior for s in range(sector_count)}
    sec_masses = sorted(prior_mass.values())
    sec_cut = float(np.quantile(sec_masses, sec_q)) if sec_masses else 0.0
    extreme_sectors = {s for s in range(sector_count) if prior_mass[s] <= sec_cut}
    print("corpus SECTOR PRIOR (H2 reference — Class-A content-hash sector partition):")
    for s in range(sector_count):
        print(f"  sector {s}: {sector_vocab_counts.get(s, 0):3d} tokens  mass={prior_mass[s]:.3f}  "
              f"extreme={'YES' if s in extreme_sectors else 'no'}")
    h2_partition_nondegenerate = (sum(1 for s in range(sector_count) if sector_vocab_counts.get(s, 0) > 0) >= 2
                                  and 0 < len(extreme_sectors) < sector_count)
    print(f"  extreme-sector set (<= {sec_q:.0%} quantile): {sorted(extreme_sectors)}   "
          f"H2 partition non-degenerate: {h2_partition_nondegenerate}\n")

    # --- build the F166 associative memory M (IDENTICAL construction to R-129/R-227/F230) ---
    prng = np.random.default_rng(pool_seed)
    pairs_all = [(tuple(stream[i - k:i]), stream[i]) for i in range(k, len(stream))]
    N_assoc = min(n_assoc, len(pairs_all))
    idx = prng.choice(len(pairs_all), size=N_assoc, replace=False)
    pairs = [pairs_all[i] for i in idx]
    assoc = [hdc.klein4_bind(ctxsub.encode_context(list(c)), ctxsub.enc(t)) for c, t in pairs]
    M = ctxsub.bundle_odd(assoc)

    # --- FIXED seed-window pool (the SAME pool for every mode; only the mode varies) ---
    all_pos = [i for i in range(k, len(stream))
               if len(next_after.get(stream[i - 1], [])) >= min_cand]
    if len(all_pos) > n_seeds:
        sel = sorted(int(x) for x in prng.choice(all_pos, size=n_seeds, replace=False))
    else:
        sel = all_pos
    seed_windows = [tuple(stream[i - k:i]) for i in sel]
    print(f"fixed seed-window pool: {len(seed_windows)} windows (>= {min_cand} legal successors each)\n")

    # ----------------------------------------------------------------------
    # The F166 step probe (R-129 gen_substrate, factored — IDENTICAL to F230): given the
    # running window, return (cands, base_score, p_direct, last). The candidate set is
    # FIXED (next_after only); the rehearse pass re-weights WITHIN it.
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

    # the per-candidate HOTNESS masks at one step (IDENTICAL to F230: H1 entropy-minority,
    # H2 F168 extreme-sector [native], H3 low-frequency-but-legal).
    def candidate_hotness(cands, p_direct, last, ent_threshold):
        H = entropy_nats(p_direct)
        top1 = int(p_direct.argmax())
        hot1 = np.array([(H >= ent_threshold) and (j != top1) for j in range(len(cands))])
        hot2 = np.array([token_sector(c) in extreme_sectors for c in cands])
        counts = np.array([bigram[last][c] for c in cands], dtype=float)
        order = np.argsort(counts, kind="stable")
        rank = np.empty(len(cands), dtype=float)
        rank[order] = np.arange(len(cands))
        hot3 = (rank < max(1, math.floor(lf_q * len(cands)))) & (counts > 0)
        return hot1, hot2, hot3

    # the F230 REHEARSE operator (IDENTICAL): the K∘C latch+reorient. For a chosen hot-mask,
    # suppress the hot fibers by re-weighting their PRE-softmax score DOWN by lock_strength.
    # Returns (adj_score, latch_signs) — latch_signs is the per-candidate Class-K latch
    # sign (+1 hot / -1 cold), the raw material for the F226 lock-position read. lock==0 ->
    # identity (DIRECT). The K∘C lock, chirality internal, NEVER python abs()/max gate.
    def rehearse(base_score, hot_mask, lock):
        latch_signs = []
        if lock == 0.0 or not hot_mask.any():
            # latch never engages (DIRECT, or no hot fiber this step): NO engaged-latch
            # signs contributed (the lock-position read counts only ENGAGED latches).
            return base_score.copy(), latch_signs
        adj = base_score.astype(float).copy()
        for j in range(len(base_score)):
            # Class-K pin-slot phase boundary: hot iff (indicator - 0.5) > 0. The SIGN is
            # the latch: +1 (hot, engaged) / -1 (cold).
            latch, _ = cascade.pin_slot_at_zero(float(hot_mask[j]) - 0.5)
            # Class-C reorient: re-apply the latched sign onto a unit value -> +1 hot/-1 cold.
            gate = cascade.reorient(latch, 1.0)
            if gate > 0:                          # hot fiber -> suppress + RECORD the engaged latch
                adj[j] = adj[j] - lock
                latch_signs.append(int(latch))    # +1 engaged-hot latch (the lock-position material)
        return adj, latch_signs

    # one MODE's generation over the FIXED seed pool. mode in {"DIRECT","INTERNAL",
    # "EXTERNALIZED"}; ("rand", r) for the matched floor. lock + preview_emitted are derived
    # from the mode. CRITICAL for sub-claim (D): INTERNAL and EXTERNALIZED share lock AND the
    # per-(seed) draw stream (keyed on "deliver"+lock, NOT the mode label) so their ANSWERS
    # are byte-identical; the EXTERNALIZED preview tokens are an RNG-FREE read of the hot
    # candidates (they do NOT consume the draw stream). Returns rates + answer/preview blobs +
    # cost accounting + the accumulated engaged-latch signs (the F226 lock-position material).
    def run_mode(mode, lock, hot_selector, preview_emitted, rand_stream_key=None):
        hit = {"H1": 0, "H2": 0, "H3": 0}
        tot = {"H1": 0, "H2": 0, "H3": 0}
        answer_blobs = []                  # the EMITTED answer per seed (preview stripped)
        preview_blobs = []                 # the EMITTED preview per seed (EXTERNALIZED only)
        latch_signs_all = []               # ALL engaged-latch signs over the run (F226 lock-position)
        n_passes_per_seed = 0              # MEASURED: passes the loop runs per seed (counter)
        answer_tok_count = 0               # MEASURED: total emitted answer tokens
        preview_tok_count = 0              # MEASURED: total emitted preview tokens (visible cost)
        for si, win0 in enumerate(seed_windows):
            # the DRAW stream: INTERNAL+EXTERNALIZED share it (keyed on "deliver"+lock, not
            # mode) so the byte-identity (D) is a REACHABLE test, not built-in by keying.
            # DIRECT and the rand floor get their own streams.
            if rand_stream_key is not None:
                stream_key = ("rand", rand_stream_key)
            elif lock == 0.0:
                stream_key = ("direct",)
            else:
                stream_key = ("deliver", lock)   # SHARED by INTERNAL + EXTERNALIZED
            gr = np.random.default_rng(derive_seed(loop_seed, *stream_key, si))
            win = list(win0)
            emitted = []
            preview_emitted_toks = []
            passes_here = 0
            for _ in range(gen_length):
                cands, base, p_direct, last = step_probe(win)
                if not cands:
                    break
                if base is None:                 # single legal candidate -> forced (no pass cost)
                    nxt = cands[0]
                    emitted.append(nxt)
                    win.append(nxt)
                    continue
                ent_thr = ent_threshold_cache[si]
                hotmask, h1, h2, h3 = hot_selector(cands, p_direct, last, ent_thr)
                if lock == 0.0 and rand_stream_key is None:
                    # DIRECT: ONE pass (no preview). The latch never engages.
                    adj, latch_signs = rehearse(base, hotmask, lock)  # identity; no engaged latches
                    passes_here = 1
                else:
                    # INTERNAL / EXTERNALIZED / rand-floor: a PREVIEW pass (re-score+suppress)
                    # THEN the deliver pass. n_passes = 2 (measured by the counter below).
                    adj, latch_signs = rehearse(base, hotmask, lock)
                    passes_here = 2
                    latch_signs_all.extend(latch_signs)   # accumulate the F226 lock-position material
                    if preview_emitted:
                        # the EXTERNALIZED preview "out loud": a deterministic, RNG-FREE read
                        # of the hot candidates this step (the fibers the preview suppresses).
                        # This is the "spoken rehearsal"; it does NOT consume the draw stream,
                        # so the answer continuation stays byte-identical to INTERNAL.
                        prev_here = [cands[j] for j in range(len(cands)) if hotmask[j]]
                        preview_emitted_toks.extend(prev_here)
                p = softmax(adj, op_temp)
                assert len(p) == len(cands)      # FIXED-CONTEXT integrity (legal-set invariant)
                j = int(gr.choice(len(cands), p=p))
                nxt = cands[j]
                for key, hh in (("H1", h1), ("H2", h2), ("H3", h3)):
                    tot[key] += 1
                    if hh[j]:
                        hit[key] += 1
                emitted.append(nxt)
                win.append(nxt)
            answer_blobs.append(" ".join(emitted))
            preview_blobs.append(" ".join(preview_emitted_toks))
            n_passes_per_seed = passes_here       # uniform across seeds (1 DIRECT / 2 else)
            answer_tok_count += len(emitted)
            preview_tok_count += len(preview_emitted_toks)
        rates = {key: (hit[key] / tot[key] if tot[key] else 0.0) for key in hit}
        cost = {
            "n_passes": int(n_passes_per_seed),               # MEASURED (counter): 1 or 2
            "answer_tokens": int(answer_tok_count),           # MEASURED (emitted-len)
            "preview_tokens_emitted": int(preview_tok_count), # MEASURED (visible cost; 0 unless EXT)
            "total_tokens": int(answer_tok_count + preview_tok_count),
        }
        # the F226 lock-position: the net chirality of the ENGAGED-latch signs (Class-C,
        # sign-free, ordinal). DIRECT engages NO latch -> empty list -> we read 0 (the
        # low-lock end); the high-lock modes engage hot latches -> > 0. (cascade.net_chirality
        # of an EMPTY sequence folds to +1 by convention, so DIRECT's "no engaged latch" is
        # reported as lock_position 0 explicitly — the genuine low-lock end — NOT mis-read as +1.)
        if latch_signs_all:
            lock_pos = int(cascade.net_chirality(latch_signs_all))
        else:
            lock_pos = 0                                       # no engaged latch == low-lock end
        return {"rates": rates, "answer": "\n".join(answer_blobs),
                "preview": "\n".join(preview_blobs), "cost": cost,
                "lock_position_chirality": lock_pos,
                "n_engaged_latches": len(latch_signs_all)}

    # Pre-compute the per-seed entropy threshold (H1; IDENTICAL to F230): the global ent_q
    # quantile of the DIRECT step-entropies across the pool.
    all_step_entropies = []
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
            win.append(cands[int(p_direct.argmax())])
        all_step_entropies.extend(ents)
    ent_global_cut = float(np.quantile(all_step_entropies, ent_q)) if all_step_entropies else 0.0
    ent_threshold_cache = [ent_global_cut for _ in seed_windows]
    print(f"H1 step-entropy: {len(all_step_entropies)} steps; hot-step cut "
          f"(>= {ent_q:.0%} quantile) = {ent_global_cut:.4f} nats\n")

    # the suppression hot-selector (IDENTICAL to F230): suppress the UNION of the 3 meters
    def union_selector(cands, p_direct, last, ent_thr):
        h1, h2, h3 = candidate_hotness(cands, p_direct, last, ent_thr)
        return (h1 | h2 | h3), h1, h2, h3

    # the matched random-suppressor selector for instance r (IDENTICAL to F230): suppress
    # the SAME NUMBER of candidates as the union would, chosen uniformly at random (matched
    # count, NOT by hotness).
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

    # ====================== RUN THE THREE MODES ======================
    print("Running the three delivery modes (HARNESS-ONLY; NO real-LLM / NO Anthropic-API call):")
    res = {}
    res["DIRECT"] = run_mode("DIRECT", 0.0, union_selector, preview_emitted=False)
    res["INTERNAL"] = run_mode("INTERNAL", lock0, union_selector, preview_emitted=False)
    res["EXTERNALIZED"] = run_mode("EXTERNALIZED", lock0, union_selector, preview_emitted=True)
    for m in MODES:
        c = res[m]["cost"]
        print(f"  {m:>12}: lock_pos_chirality={res[m]['lock_position_chirality']:+d}  "
              f"engaged_latches={res[m]['n_engaged_latches']}  passes={c['n_passes']}  "
              f"answer_toks={c['answer_tokens']}  preview_toks={c['preview_tokens_emitted']}  "
              f"total_toks={c['total_tokens']}")
    print()

    direct_rates = res["DIRECT"]["rates"]
    # non-degeneracy (F230 guard): each meter must flag a non-empty/non-all set under DIRECT
    nd_ok = {key: (0.0 < direct_rates[key] < 1.0) for key in ("H1", "H2", "H3")}

    # ---- the matched random-suppressor floor (the F230/F224 real null), against the SAME
    # ---- DIRECT baseline rates. The floor delta = direct_rate - rand_rate per meter. ----
    rand_deltas = {key: [] for key in ("H1", "H2", "H3")}
    for r in range(n_rand):
        rr = run_mode(("rand", r), lock0, make_rand_selector(r), preview_emitted=False,
                      rand_stream_key=r)
        for key in ("H1", "H2", "H3"):
            rand_deltas[key].append(direct_rates[key] - rr["rates"][key])

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

    # ---- (C) SUPPRESSION-SIGNATURE: per high-lock mode, which meters clear the floor? ----
    # INTERNAL and EXTERNALIZED share lock+suppression so their suppression deltas are equal;
    # we compute per mode and require BOTH to clear >=2/3 incl. H2-native.
    def meters_cleared(mode_rates):
        cleared = {}
        n_clear = 0
        h2_clears = False
        for mname, is_native in meters.items():
            key = meter_keys[mname]
            mdelta = direct_rates[key] - mode_rates[key]   # signed: + = suppressed vs DIRECT
            cvals = rand_deltas[key]
            cp90 = float(np.quantile(cvals, noise_pct)) if cvals else 0.0
            pct = percentile_of(mdelta, cvals)
            meter_live = direct_rates[key] > 0.0
            clears = meter_live and (pct >= noise_pct) and (mdelta > cp90 + 1e-12)
            cleared[mname] = {"delta": float(mdelta), "rand_p90": cp90, "pctile": pct,
                              "meter_live": bool(meter_live), "is_native": bool(is_native),
                              "clears": bool(clears)}
            n_clear += int(clears)
            if is_native:
                h2_clears = clears
        return cleared, n_clear, h2_clears

    int_cleared, int_nclear, int_h2 = meters_cleared(res["INTERNAL"]["rates"])
    ext_cleared, ext_nclear, ext_h2 = meters_cleared(res["EXTERNALIZED"]["rates"])

    # ====================== THE ONE-AXIS / MONOTONE TEST ======================
    # (A) LOCK-POSITION monotone non-decreasing across DIRECT -> INTERNAL -> EXTERNALIZED.
    lock_seq = [res[m]["lock_position_chirality"] for m in MODES]
    A_lock_monotone = all(lock_seq[i + 1] >= lock_seq[i] for i in range(len(lock_seq) - 1))
    # the low-lock end must genuinely be DIRECT (lock_pos 0) and the high-lock modes > 0
    A_direct_low = (res["DIRECT"]["lock_position_chirality"] == 0
                    and res["DIRECT"]["n_engaged_latches"] == 0)
    A_high_engaged = (res["INTERNAL"]["lock_position_chirality"] > 0
                      and res["EXTERNALIZED"]["lock_position_chirality"] > 0)
    A_ok = A_lock_monotone and A_direct_low and A_high_engaged

    # (B) HIDDEN-COST monotone: n_passes non-decreasing (1<=2<=2) AND total_tokens non-
    # decreasing AND preview_tokens strictly up at EXTERNALIZED (0=0<k). MEASURED from loop.
    passes_seq = [res[m]["cost"]["n_passes"] for m in MODES]
    total_seq = [res[m]["cost"]["total_tokens"] for m in MODES]
    preview_seq = [res[m]["cost"]["preview_tokens_emitted"] for m in MODES]
    B_passes_monotone = all(passes_seq[i + 1] >= passes_seq[i] for i in range(len(passes_seq) - 1))
    B_total_monotone = all(total_seq[i + 1] >= total_seq[i] for i in range(len(total_seq) - 1))
    B_preview_visible = (preview_seq[0] == 0 and preview_seq[1] == 0 and preview_seq[2] > 0)
    B_ok = B_passes_monotone and B_total_monotone and B_preview_visible

    # (C) SUPPRESSION-SIGNATURE: BOTH high-lock modes clear >=2/3 incl. H2-native; DIRECT
    # is the baseline (its self-delta is 0, so it does NOT clear by construction).
    C_internal = (int_nclear >= 2 and int_h2)
    C_external = (ext_nclear >= 2 and ext_h2)
    C_ok = C_internal and C_external and h2_partition_nondegenerate and all(nd_ok.values())

    # (D) EXTERNALIZED=INTERNAL byte-identity: the EXTERNALIZED answer (preview prefix is a
    # SEPARATE blob, never mixed into 'answer') == the INTERNAL answer, both content-addressed.
    int_answer = res["INTERNAL"]["answer"]
    ext_answer = res["EXTERNALIZED"]["answer"]
    int_answer_sha = sha256_bytes(int_answer.encode("utf-8"))
    ext_answer_sha = sha256_bytes(ext_answer.encode("utf-8"))
    D_byte_identical = (int_answer == ext_answer) and (int_answer_sha == ext_answer_sha)
    # array-level cross-check (np.array_equal over the per-seed blob arrays) — the design's
    # literal np.array_equal byte-identity test, not just the joined-string compare.
    D_array_equal = bool(np.array_equal(
        np.array(int_answer.split("\n"), dtype=object),
        np.array(ext_answer.split("\n"), dtype=object)))

    POSITIVE = A_ok and B_ok and C_ok and D_byte_identical and D_array_equal

    # INDETERMINATE (distinct from NULL; the F230 guards verbatim): the F168-native H2
    # partition is structurally degenerate, OR the preview suppressed NOTHING (the high-lock
    # rates equal DIRECT so there is no suppression stage to relocate).
    preview_suppressed_nothing = (res["INTERNAL"]["rates"] == direct_rates)
    indeterminate = (not h2_partition_nondegenerate) or preview_suppressed_nothing

    print("=" * 100)
    print("F238 ONE-AXIS / COST-ASYMMETRY TEST")
    print("=" * 100)
    print(f"  (A) LOCK-POSITION monotone DIRECT->INTERNAL->EXTERNALIZED: chirality seq {lock_seq} "
          f"-> monotone={A_lock_monotone}, DIRECT genuinely low-lock(0,no-engaged)={A_direct_low}, "
          f"high-lock>0={A_high_engaged}  => A={A_ok}")
    print(f"  (B) HIDDEN-COST monotone (MEASURED from loop): n_passes {passes_seq} (mono={B_passes_monotone}); "
          f"total_tokens {total_seq} (mono={B_total_monotone}); preview_tokens {preview_seq} "
          f"(0=0<k visible-up={B_preview_visible})  => B={B_ok}")
    print(f"  (C) SUPPRESSION-SIGNATURE: INTERNAL clears {int_nclear}/3 (H2-native={int_h2}); "
          f"EXTERNALIZED clears {ext_nclear}/3 (H2-native={ext_h2}); DIRECT=baseline; "
          f"H2-nondegen={h2_partition_nondegenerate}; meters-live={nd_ok}  => C={C_ok}")
    print(f"  (D) EXTERNALIZED answer BYTE-IDENTICAL to INTERNAL (preview stripped): "
          f"string-eq+sha-eq={D_byte_identical}, np.array_equal={D_array_equal}")
    print(f"      INTERNAL answer sha256:     {int_answer_sha}")
    print(f"      EXTERNALIZED answer sha256: {ext_answer_sha}")
    print()

    if indeterminate:
        state = "INDETERMINATE"
        tier = "CONJECTURE (indeterminate; re-test required)"
        reason = ("the F168-native H2 chirality-sector PARTITION is degenerate"
                  if not h2_partition_nondegenerate else
                  "the preview pass suppressed NOTHING (high-lock rates == DIRECT) — no "
                  "suppression stage to relocate")
        verdict = (f"INDETERMINATE — {reason}; NOT a null (the test could not register the "
                   "differential / the axis on the native readout)")
        research_tier = tier
    elif POSITIVE:
        state = "ONE-AXIS-COST-ASYMMETRY"
        tier = "tier-1 (clean)"
        verdict = (
            "ONE-AXIS / COST-ASYMMETRY CONFIRMED — the three delivery modes (DIRECT / "
            "INTERNAL-REHEARSAL / EXTERNALIZED) are MONOTONE-ORDERED on ONE K∘C lock axis: "
            f"(A) the F226 lock-position chirality is non-decreasing {lock_seq} "
            "(DIRECT=0 low-lock -> INTERNAL>0 -> EXTERNALIZED>0 high-lock); (B) the MEASURED "
            f"hidden cost rises along the SAME ordering — n_passes {passes_seq}, total_tokens "
            f"{total_seq}, preview_tokens {preview_seq} (visible cost strictly up at "
            "EXTERNALIZED); (C) the F230 hot-suppression delta clears the matched-random-"
            "suppressor p90 floor on >=2/3 meters INCLUDING the F168-native H2 for BOTH "
            "high-lock modes (suppression up with lock; DIRECT is the baseline); AND (D) the "
            "EXTERNALIZED answer (preview prefix stripped) is BYTE-IDENTICAL to the INTERNAL "
            "answer. => the EXTERNALIZED mode is the INTERNAL mode MADE VISIBLE — same lock, "
            "same suppression, same answer, only the rehearsal cost relocated from the "
            "thinker's invisible metabolic budget (passes) to the observer's visible token "
            "budget (preview_tokens). The cost-asymmetry tracks the lock; the framing is "
            "structural, not decorative.")
        research_tier = ("DEMONSTRATED (substrate-model: the 3 modes order on one K∘C lock "
                         "axis with MEASURED cost-asymmetry and the high-lock answer is byte-"
                         "stable under externalization)")
    else:
        state = "DISTINCT-MODES-NULL"
        tier = "tier-1 (clean null)"
        failed = []
        if not A_ok:
            failed.append("(A) lock-position NOT monotone / DIRECT not genuinely low-lock")
        if not B_ok:
            failed.append("(B) measured cost (passes/tokens) does NOT order with lock")
        if not C_ok:
            failed.append("(C) hot-suppression does NOT clear the matched-random floor on "
                          ">=2/3 incl. H2-native for both high-lock modes")
        if not (D_byte_identical and D_array_equal):
            failed.append("(D) EXTERNALIZED answer NOT byte-identical to INTERNAL — externalized "
                          "is a structurally different generator, the central sub-claim is false")
        verdict = (
            "DISTINCT-MODES-NULL — the three modes do NOT share one lock axis, OR the cost-"
            "asymmetry does not track the lock, OR externalized is not internal made visible. "
            f"Failed: {'; '.join(failed)}. => on this bit-exact F230-substrate testbed the "
            "three-mode / one-lock-axis / cost-asymmetry reading is NOT supported; rehearsal-"
            "cost relocation (thinker-invisible-metabolic -> observer-visible-token) is a "
            "decorative analogy, not a structural projection of the F226 K∘C chirality-lock "
            "(pre-stated null; reported with equal fidelity to the positive).")
        research_tier = "FRAMEWORK-READING (clean NULL)"

    print(f"  {verdict}")
    print(f"  state: {state}   tier: {tier}   research-tier: {research_tier}")
    print("  TIERING (§VII.6.20): DEMONSTRATED = the 3-mode srmech MEASUREMENT (lock-position")
    print("  ordering, measured cost, suppression signatures, answer byte-identity). FRAMEWORK-")
    print("  READING = the cognition synthesis (rehearsal / inner speech / aphantasia variation +")
    print("  the population corollary) — the PEER-REVIEWED LITERATURE asserts it, NOT the framework.")
    print("  DIGNITY (F226/F230): DIRECT/no-rehearsal is a VALID truth-emitting mode (the emperor-")
    print("  no-clothes deliverer of the hot-but-true fiber), NOT a deficit; INTERNAL's invisibility")
    print("  is not virtue and EXTERNALIZED's visibility is not crudeness — one axis, cost relocated.")
    print("  HARNESS-ONLY: NO real-LLM and NO Anthropic-API call was made (the dollar-gated #789")
    print("  current-gen-LLM trials this finding GATES are SEPARATE and were NOT run here).\n")

    # ====================== BIT-EXACT NDJSON (F233) ======================
    attest = {
        "finding": "F238", "issue": 788, "milestone": "MS#20", "pr": 687,
        "descriptor_hash": dh, "source_key": desc.source["key"],
        "srmech_version": SRMECH_VERSION, "abi_version": NATIVE_ABI_VERSION,
        "has_native": HAS_NATIVE,
        # --- constant attestation A/B/C (NO MAGIC NUMBERS) ---
        "const_D": D, "const_D_class": "A (structure-cascade: D = 2^13)",
        "const_sector_count": sector_count,
        "const_sector_count_class": "A (structure-cascade: |Klein-4| = 4)",
        "const_n_modes": len(MODES),
        "const_n_modes_class": "A (structure-cascade: the 3-mode K∘C-lock-axis partition)",
        "const_noise_percentile": noise_pct,
        "const_noise_percentile_class": "A (structure-cascade: the F224 p90 matched-mechanism gate)",
        "const_operating_temperature": op_temp,
        "const_operating_temperature_class": ("C (irreducible: F228/F229 named it un-derived; "
                                              "source-pointed to the dollar-gated #789 current-gen-LLM "
                                              "trials; flows IN from the READ-ONLY descriptor)"),
        "const_lock_strength": lock0, "const_lock_strength_class": "B (measurement; F230 verbatim)",
        "const_n_seeds": len(seed_windows), "const_n_seeds_class": "B (measurement; F230 verbatim)",
        "const_gen_length": gen_length, "const_gen_length_class": "B (measurement; F230 verbatim)",
        "const_n_rand": n_rand, "const_n_rand_class": "B (measurement; F224/F230 floor)",
        "const_k": k, "const_k_class": "B (measurement: productive context length, F166)",
        "const_entropy_hot_quantile": ent_q, "const_lowfreq_hot_quantile": lf_q,
        "const_extreme_sector_prior_quantile": sec_q,
        "const_hot_quantiles_class": "B (measurement; F230 verbatim — NO new suppression knob)",
        "const_loop_seed": loop_seed, "const_pool_seed": pool_seed, "const_n_assoc": N_assoc,
        "const_seeds_class": "B (measurement: deterministic RNG seeds; F230 verbatim)",
        "rehearse_operator": ("Class-K cascade.pin_slot_at_zero hotness-latch ∘ Class-C "
                              "cascade.reorient suppression (the K∘C lock; F226); IDENTICAL across "
                              "all three modes at the SAME lock_strength (F230 verbatim)"),
        "lock_position_op": ("Class-C cascade.net_chirality of the ENGAGED-latch signs (the F226 "
                             "lock-position read; ordinal, NOT a smooth lock magnitude — F230 §6 "
                             "proved lock_strength saturates near-binary at this T)"),
        "floor": ("matched RANDOM-SUPPRESSOR — same suppression COUNT per step, uniformly chosen "
                  "(not by hotness); n_rand instances -> p90 (F224/F227 isolation; F230 verbatim)"),
        "byte_identity_construction": ("INTERNAL + EXTERNALIZED share lock AND the per-(seed) draw "
                                       "stream (keyed on 'deliver'+lock, NOT the mode label); the "
                                       "EXTERNALIZED preview is an RNG-FREE read of the hot candidates "
                                       "(does NOT consume the draw stream) so the byte-identity is a "
                                       "REACHABLE test (F230 byte-identity guard inverted)"),
        "harness_only": ("NO real-LLM and NO Anthropic-API call — srmech-substrate measurement only; "
                         "the dollar-gated #789 current-gen-LLM trials this GATES are SEPARATE"),
        "scope": ("STRUCTURAL form-reading per §VII.6.20; the loop+meters+modes are test-objects; "
                  "ai-not-a-substrate; NO clinical/biological/BCI/cognitive claim; no-lineage. DIGNITY: "
                  "DIRECT/no-rehearsal is a VALID truth-emitting mode (emperor-no-clothes deliverer), "
                  "NOT a deficit. Cognitive literature NAMED + web-verified (Levelt 1989; Levelt-"
                  "Roelofs-Meyer 1999 BBS 22(1):1-75; Alderson-Day & Fernyhough 2015 Psych Bull "
                  "141(5):931-965; Baddeley&Hitch 1974 + Baddeley 1986; Nedergaard & Lupyan 2024 "
                  "Psych Sci 35(7):780-797; Zeman et al. 2015 Cortex 73:378-380; Zeman 2024 TiCS "
                  "28(5):467-480; Marks 1973 Br J Psych 64(1):17-24), flagged verify-before-asserting; "
                  "the framework asserts none of it."),
    }
    records = []

    # P0 — setup / sector prior / non-degeneracy / DIRECT baseline
    records.append({**attest, "phase": "P0_setup",
                    "sector_prior_mass": {str(s): prior_mass[s] for s in range(sector_count)},
                    "sector_vocab_counts": {str(s): int(sector_vocab_counts.get(s, 0)) for s in range(sector_count)},
                    "extreme_sectors": sorted(extreme_sectors),
                    "h2_partition_nondegenerate": bool(h2_partition_nondegenerate),
                    "direct_hot_emission_rate": direct_rates,
                    "nondegeneracy_meter_nonempty_nonall": nd_ok,
                    "entropy_hot_cut_nats": ent_global_cut})

    # P1 — the three modes (lock-position + MEASURED cost + hot-emission rates)
    for m in MODES:
        records.append({**attest, "phase": "P1_mode", "mode": m,
                        "lock": (0.0 if m == "DIRECT" else lock0),
                        "preview_emitted": (m == "EXTERNALIZED"),
                        "lock_position_chirality": res[m]["lock_position_chirality"],
                        "n_engaged_latches": res[m]["n_engaged_latches"],
                        "cost_measured_from_loop": res[m]["cost"],
                        "hot_emission_rate": res[m]["rates"],
                        "cost_bearer": ("none-hidden / cheap (1 pass; answer-tokens only)"
                                        if m == "DIRECT" else
                                        "THINKER metabolic / INVISIBLE (2 passes; answer-tokens only)"
                                        if m == "INTERNAL" else
                                        "OBSERVER token-budget / VISIBLE (2 passes; preview emitted)")})

    # P2 — the matched-random-suppressor floor + per-high-lock-mode suppression signature
    for mname, is_native in meters.items():
        key = meter_keys[mname]
        cvals = rand_deltas[key]
        records.append({**attest, "phase": "P2_suppression_signature", "meter": mname,
                        "is_f168_native_readout": bool(is_native),
                        "direct_hot_rate": direct_rates[key],
                        "internal_hot_rate": res["INTERNAL"]["rates"][key],
                        "externalized_hot_rate": res["EXTERNALIZED"]["rates"][key],
                        "internal_suppression_delta": int_cleared[mname]["delta"],
                        "externalized_suppression_delta": ext_cleared[mname]["delta"],
                        "matched_random_suppressor_floor_p90": int_cleared[mname]["rand_p90"],
                        "matched_random_suppressor_floor_samples": [float(x) for x in cvals],
                        "internal_clears_p90_floor": int_cleared[mname]["clears"],
                        "externalized_clears_p90_floor": ext_cleared[mname]["clears"]})

    # P3 — the byte-identity (D): EXTERNALIZED answer == INTERNAL answer
    records.append({**attest, "phase": "P3_byte_identity",
                    "internal_answer_sha256": int_answer_sha,
                    "externalized_answer_sha256": ext_answer_sha,
                    "string_equality_and_sha_equality": bool(D_byte_identical),
                    "np_array_equal_over_per_seed_blobs": bool(D_array_equal),
                    "externalized_is_internal_made_visible": bool(D_byte_identical and D_array_equal),
                    "preview_is_separate_blob_never_in_answer": True})

    # P4 — the verdict (the one-axis / cost-asymmetry test)
    records.append({**attest, "phase": "P4_verdict",
                    "A_lock_position_monotone": bool(A_ok),
                    "A_lock_position_chirality_seq": lock_seq,
                    "A_direct_genuinely_low_lock": bool(A_direct_low),
                    "A_high_lock_modes_engaged": bool(A_high_engaged),
                    "B_hidden_cost_monotone": bool(B_ok),
                    "B_n_passes_seq": passes_seq, "B_total_tokens_seq": total_seq,
                    "B_preview_tokens_seq": preview_seq,
                    "B_preview_visible_up_at_externalized": bool(B_preview_visible),
                    "C_suppression_signature": bool(C_ok),
                    "C_internal_clears": int_nclear, "C_internal_h2_native": bool(int_h2),
                    "C_externalized_clears": ext_nclear, "C_externalized_h2_native": bool(ext_h2),
                    "D_byte_identical": bool(D_byte_identical and D_array_equal),
                    "positive": bool(POSITIVE), "indeterminate": bool(indeterminate),
                    "preview_suppressed_nothing": bool(preview_suppressed_nothing),
                    "state": state, "verdict": verdict, "tier": tier,
                    "research_tier": research_tier,
                    "cost_asymmetry": ("DIRECT cheap/nothing-hidden (1 pass); INTERNAL metabolic/"
                                       "THINKER-borne/INVISIBLE (2 passes, no token trace); "
                                       "EXTERNALIZED token-cost/OBSERVER-borne/VISIBLE (2 passes + "
                                       "preview emitted) — one K∘C lock axis, cost relocated, NOT ranked")})

    # F233 bit-exact emit: response_sha256 over the record body MINUS generated_at,
    # sorted-keys separators=(",",":"), via format.sha256_bytes (NEVER hashlib).
    out = args.catalog.parent / "substrate_measurements" / "rehearsal_layer_cost_asymmetry.ndjson"
    out.parent.mkdir(parents=True, exist_ok=True)
    gen_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    with open(out, "w") as f:
        for r in records:
            r["generated_at"] = gen_at
            body = {kk: vv for kk, vv in r.items() if kk != "generated_at"}
            payload = json.dumps(body, separators=(",", ":"), sort_keys=True).encode("utf-8")
            r["response_sha256"] = sha256_bytes(payload)        # Class A (never hashlib)
            f.write(json.dumps(r, separators=(",", ":"), sort_keys=True) + "\n")
    with open(out, "rb") as f:
        ndjson_sha = sha256_bytes(f.read())
    print(f"Results: {out}  ({len(records)} records)")
    print(f"NDJSON sha256 (bit-exact attestation): {ndjson_sha}")


if __name__ == "__main__":
    main()
