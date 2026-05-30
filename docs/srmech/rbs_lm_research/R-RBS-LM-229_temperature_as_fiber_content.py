"""R-RBS-LM-229 — F229: is "TEMPERATURE" (the LLM magic number) a READ-OFF of the
conversation's hidden FIBER, or a free hyperparameter? And if it tracks, is it
"just a scalar" — or the 1-D SHADOW of a BI-CHIRAL (Klein-4 = gamma5 x iw7) K∘C
learning-lock (F226)?

THE PREDECESSOR CHAIN (what is already settled):
  F212/F214 — there IS a hidden recipient/affect fiber, but it is located RENDER-ONLY;
              and the naive token-self-sector-occupancy fiber meter is PINNED (every
              token argmaxes to sector 0; F214 §4 / F221 §4 readout-pinned caveat).
  F221/F224 — the depth/recipient anchor does NOT steer retrieval (F221 0/3 NULL; F224
              (C) sep=0.0409 < p90=0.0500, pctile=0.12); AND the load-bearing confound:
              the family label co-varies with which continuation is legal. F229's scalar
              form of that confound: n_candidates correlates ~0.9991 with emitted-
              distribution entropy (smoke), so render-variability MUST be residualized on
              n_cand and the control MUST be matched on n_cand.
  F227 — the RENDER-side channel test: holding context FIXED and IMPOSING a depth-band
         LABEL, the emitted render was channel-invariant beyond the matched-random floor
         (a render-null on the depth axis). F229 keeps the F227 loop + floor machinery but
         SWAPS the externally-imposed band-LABEL for an INTRINSIC context-fiber SCALAR read
         BEFORE generation, and tests CORRELATIONAL TRACKING across naturally-varying
         contexts at matched n_cand (not a 3-band label separation).
  F228 — the magic-number audit named `operating_temperature=0.02` (catalog scalar) as a
         REAL MAGIC NUMBER (C-class; un-derived). F229 is the forward-ask: does that scalar
         SOURCE from structure (the context fiber), or is it exogenous?

THE HYPOTHESIS (the POSITIVE the design is built to be ABLE to reject): "temperature"
is a REAL FIBER-CONTENT meta-value — a quantity derivable from the conversation's hidden
fiber (F212's emotional/register/intensity STATE, read here as a STRUCTURAL text-object
property, NOT a cognitive claim) sets the render's intensity/variability ("hotness"). And
per the user refinement, it likely is NOT "just a scalar": temperature is probably the 1-D
shadow of a BI-CHIRAL (Klein-4 = gamma5 x iw7) meta-value — the F226 K∘C persistent-
plasticity lock (high temperature ~ low-lock/exploratory; low ~ high-lock/stable).

THE FORM LADDER (the deliverable): climb scalar -> bi-chiral -> harmonic; report the
MINIMAL SUFFICIENT form whose added explained render-variability clears its OWN matched-
random floor. "a scalar suffices / no chiral structure" is kept a reachable SUB-NULL.

  • CONTEXT-FIBER SCALAR (computed BEFORE generation, frozen — NOT reverse-fit):
      F-A (PRIMARY) BIGRAM-PARITY Klein-4 sector-occupancy ENTROPY of the context window
            — route each context bigram to a Klein-4 = Z2xZ2 sector by word-order parity
            (sector = 2*forward_present + reverse_present, the descriptor's
            sector_routing='bigram_parity' structural routing, F132/F168/F225); read
            Shannon entropy of the 4-bin occupancy. The Klein-4 sector-occupancy SPREAD the
            directive names — "intensity/variability of the local relational state".
      F-B (CROSS-CHECK) context SELF-SIMILARITY SPREAD — std of pairwise klein4_similarity
            among the window-token vectors (low spread = lexically-tight/"cool"; high =
            diverse/"hot").
      GATE 2a (F214/F221 pinned-meter guard): each fiber scalar MUST have real dynamic
            range (std > 1e-6) over the context pool, else CONJECTURE-indeterminate (the
            naive token-self-occupancy scalar is PINNED at 0 and is EXCLUDED by design).
  • RENDER-VARIABILITY METER (the dependent variable): T_eff = the effective sampling
      temperature needed to reproduce the emission — solve (bisection, monotone) for the T
      whose softmax(sim_k4_batch(probe, cand_vecs)/T) entropy MATCHES the emitted-token
      empirical entropy over the FIXED candidate set. The INVERSE of the F128 softmax(sims/T)
      map. Residualized on n_candidates (MANDATORY: emitted entropy ~ n_cand at r~0.9991).
  • RUNG 2 BI-CHIRAL (F226 K∘C): lift the scalar to a 2-bit (which-gamma5-sign, which-iw7-
      sign) Klein-4 coordinate via klein4_chirality_flip_gamma5 / _omega7 / cpt_mirror
      (gamma5 = Class-K pin-slot sign, iw7 = Class-C reorientation; the K∘C pair, chirality
      INTERNAL). ΔR² of the 2-bit coordinate over the scalar, gated vs a matched-random-2-bit
      floor (same DoF, random signs).
  • RUNG 3 HARMONIC (Class-L, F129/F140): per-context fiber co-occurrence graph (nodes=window
      tokens, edges=adjacency, Counter ONLY for edge weights) -> dense_laplacian ->
      jacobi_eigvals; ΔR² of a fiber MODE over the bi-chiral, gated vs a matched-random-
      spectrum floor.

PRE-STATED NULL (verbatim; counts EQUALLY per [[feedback_dont_pre_commit_spike_query_operators]]
— the 20k-token smoke already PREVIEWS this outcome (partial r ~ 0.018-0.064 after the n_cand
control), so it is genuinely reachable and the design is NOT leaned):
  "A scalar fiber-meta value computed from the context BEFORE generation does NOT track the
   render's variability beyond the candidate-set-matched / F224 matched-random floor — the
   render-variability (T_eff residualized on n_candidates) sits at-or-below the p90 of the
   matched control on the majority of meters. => 'temperature' is EXOGENOUS / noise on this
   testbed: it is a free hyperparameter, not a read-off of conversation fiber; the magic
   number is NOT sourced from structure here."
SUB-NULL (the form ladder; user-mandated reachable):
  "Even if a scalar tracks, a BI-CHIRAL (Klein-4 = gamma5 x iw7) decomposition of the SAME
   fiber explains NO render-variability BEYOND the scalar (ΔR² of the 2-bit coordinate over
   the scalar sits at-or-below its matched-random-coordinate floor), and the HARMONIC
   (Class-L) decomposition adds nothing beyond the bi-chiral. => a SCALAR suffices; no chiral
   structure beyond it — it really IS just (a scalar) temperature, NOT the 1-D shadow of K∘C."

PRE-STATED POSITIVE (verbatim):
  "The scalar fiber-meta TRACKS render-variability beyond the candidate-set-matched / F224
   matched-random floor — T_eff (residualized on n_cand) co-varies with the context-fiber
   scalar by MORE than a matched-random fiber-label of the same construction does (structured
   |Spearman| pctile >= 0.90 AND > matched-random p90 + 1e-12). => temperature = a read-off of
   conversation fiber; the canonical LLM magic number is SOURCED from structure (closes F228's
   un-derived operating_temperature; sharpens F227 from categorical channel to scalar)."
SUB-POSITIVE (the bi-chiral rung; the user's primary hypothesis):
  "The BI-CHIRAL decomposition explains render-variability BEYOND the scalar (ΔR² of the 2-bit
   coordinate over the scalar clears its matched-random-coordinate p90 floor), and the K∘C
   orientation maps as predicted (low-lock/exploratory <-> high T_eff; high-lock/stable <->
   low). => temperature is the 1-D SHADOW of the K∘C LEARNING-lock (F226)."

MINIMAL-SUFFICIENT-FORM CRITERION (the deliverable; conservative, ratchet-style): the ANSWER
to "what temperature really is" is the LOWEST rung whose added explained render-variability
clears its OWN matched-random floor. (a) no rung clears -> NULL (exogenous/noise); (b) scalar
clears, bi-chiral adds nothing -> "a scalar suffices" (sub-null); (c) bi-chiral clears beyond
scalar -> "the 1-D shadow of K∘C" (sub-positive); (d) harmonic adds beyond bi-chiral ->
temperature is an overtone in the A-N harmonic ladder.

srmech-native (CLAUDE.md §2 STOP-list honored — 28D / Klein-4 / chirality framing throughout):
  • klein4_similarity / sim_k4_batch (Class M, F132 fractional-agreement) — the fiber self-sim
      spread + all candidate-similarity scoring; NEVER a hand-rolled cosine.
  • encode_word_k4(sector=s) (Class M∘I, F168 sector tagging) + ContextSubstrate.{enc,
      encode_context, bundle_odd} (Class A∘M + iw7 position, R-126/F166) — the rolling
      context-state probe + the bigram-parity sector encode.
  • klein4_chirality_flip_{gamma5,omega7} + klein4_cpt_mirror — the bi-chiral 2-bit lift (the
      K∘C pair; gamma5 axis = Class-K pin-slot sign, iw7 axis = Class-C reorientation).
  • laplacian.{dense_laplacian, jacobi_eigvals} (Class L, F129/F140) — the fiber harmonic
      ladder; NEVER np.linalg.eig/eigh/svd.
  • cascade.magnitude (Class-K pin-slot |.|, rc22+) — ALL sign-free folds (|Spearman|,
      residual distances, ΔR² magnitudes); NEVER python abs().
  • klein4_random (Class M) — the matched-random fiber-label / matched-random 2-bit-coordinate
      / matched-random-spectrum controls (the F224 isolation: a meaningless fiber value of the
      IDENTICAL construction sets the "how much does any fiber track by chance, AT MATCHED
      n_cand" floor).
  • format.sha256_bytes (Class A) — per-context + per-random-label deterministic RNG seeds
      (fixed seed; per-domain seeds via sha256_bytes, NOT python hash()) + the NDJSON
      attestation hash; NEVER hashlib.sha256 / python hash().
  • Counter ONLY for the fiber co-occurrence adjacency EDGE WEIGHTS feeding dense_laplacian and
      the bigram candidate store (the R-127/R-131 stored-relationship structure), NEVER as a
      storage/occupancy proxy (sector-occupancy is read via the bigram-parity routing + Shannon
      entropy of the 4-bin histogram, no Counter-as-proxy).

Catalog-driven (descriptor_religious_texts.toml [render_channel] reused for the FIXED testbed:
KJV-NT corpus, D=8192, window=5, min_candidates=3). The F229-specific params (n_contexts,
n_random, ref_temp grid, seeds) are attested INLINE in the NDJSON (the [render_channel] section
is owned by F227; per the directive I do NOT modify a .toml another item owns). srmech 0.5.0rc22
native ABI=3; deterministic / bit-exact (NDJSON; second-run sha256 must match). STRUCTURAL form-
reading per MFO §VII.6.20: texts are structural test-objects; the LM is a k=3 chiral addresser,
not an aware entity (ai-is-not-a-substrate); trauma-informed — NO clinical/biological/BCI/
cognitive claim. Affect/register/intensity are STRUCTURAL test-quantities over text objects;
any cognitive reading is the PEER-REVIEWED LITERATURE's to assert (F226 §2 — arousal/affect-
intensity, register/genre variation), flagged verify-before-asserting, NO DOI fabricated; the
framework adds ONLY the structural form-reading. no-lineage.
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

# --- F229-specific params attested INLINE (NOT in a .toml another item owns) ---
F229_N_CONTEXTS = 600     # naturally-varying context windows sampled (vs F227's 80 seed windows)
F229_N_RANDOM = 16        # matched-random fiber-label / coordinate / spectrum controls (F224 floor)
F229_NOISE_PCT = 0.90     # the F224 p90 gate (verbatim)
F229_SEED = 42            # context-pool + random-label seed (via sha256_bytes, not python hash)
F229_LOOP_SEED = 7        # emission-sampling RNG seed base (SAME as F129/F227; bit-exact)
F229_TEFF_LO = 1e-3       # bisection bracket low (very cold)
F229_TEFF_HI = 50.0       # bisection bracket high (very hot — H -> log(n_cand))
F229_TEFF_ITERS = 60      # bisection iterations (monotone H(T); ample for float convergence)


# ---------------------------------------------------------------------------
# Deterministic per-(context, random-label) RNG seed — via sha256_bytes, NOT python
# hash() (CLAUDE.md §2 / bit-exact discipline). Reused shape from F227 derive_seed.
# ---------------------------------------------------------------------------

def derive_seed(*parts) -> int:
    """A deterministic 63-bit integer seed from a label tuple, routed through the
    Class-A content-hash (sha256_bytes) — never python hash() (non-deterministic
    across runs) and never hashlib.sha256 directly (route through the srmech op)."""
    payload = "|".join(str(p) for p in parts).encode("utf-8")
    return int(sha256_bytes(payload)[:16], 16) & ((1 << 63) - 1)


def softmax(x: np.ndarray, t: float) -> np.ndarray:
    z = x / t
    z = z - z.max()
    e = np.exp(z)
    return e / e.sum()


def entropy_nats(p: np.ndarray) -> float:
    """Shannon entropy (nats); the F128 entropy_nats verbatim."""
    nz = p[p > 0]
    return float(-(nz * np.log(nz)).sum())


# ---------------------------------------------------------------------------
# CONTEXT-FIBER SCALAR (F-A primary) — bigram-parity Klein-4 sector-occupancy ENTROPY.
# Route each ordered context bigram to a Klein-4 = Z2xZ2 sector by word-order parity:
#   sector = 2*(forward present) + (reverse present), per descriptor
#   sector_routing='bigram_parity' (F132/F168/F225 structural routing). Read Shannon
#   entropy of the 4-bin occupancy histogram. NOTE: the 4-bin histogram is the Klein-4
#   sector OCCUPANCY (the structural routing target), NOT a Counter-as-storage proxy —
#   it is the descriptor's named sector_routing read off the window. Computed BEFORE the
#   render (frozen; anti-reverse-fit).
# ---------------------------------------------------------------------------

def bigram_parity_sector_entropy(window) -> float:
    pairs = list(zip(window, window[1:]))
    fwd = set(pairs)                       # ordered (a,b) present forward
    occ = [0, 0, 0, 0]                     # Klein-4 = Z2xZ2 4-sector occupancy
    seen_unordered = set()
    for a, b in pairs:
        if a == b:
            continue                       # a self-loop carries no word-ORDER parity
        key = frozenset((a, b))
        if key in seen_unordered:
            continue
        seen_unordered.add(key)
        f = 1 if (a, b) in fwd else 0      # forward presence
        r = 1 if (b, a) in fwd else 0      # reverse presence
        occ[2 * f + r] += 1                # Z2xZ2 coset = 2*gamma5-bit + iw7-bit (the parity sector)
    tot = sum(occ)
    if tot == 0:
        return 0.0
    p = [c / tot for c in occ if c > 0]
    return float(-sum(pi * math.log(pi) for pi in p))


# ---------------------------------------------------------------------------
# Spearman rank-correlation magnitude (sign-free via cascade.magnitude — the Class-K
# pin-slot |.|; NEVER python abs()). Ranks via argsort-of-argsort (ties broken by index;
# deterministic). The directive's |Spearman| meter.
# ---------------------------------------------------------------------------

def _ranks(x: np.ndarray) -> np.ndarray:
    order = np.argsort(x, kind="stable")
    r = np.empty(len(x), dtype=float)
    r[order] = np.arange(len(x), dtype=float)
    return r


def spearman_abs(x: np.ndarray, y: np.ndarray) -> float:
    """|Spearman rho| via Pearson on ranks; sign folded by cascade.magnitude (Class K)."""
    rx, ry = _ranks(np.asarray(x, dtype=float)), _ranks(np.asarray(y, dtype=float))
    rx = rx - rx.mean()
    ry = ry - ry.mean()
    denom = (float((rx * rx).sum()) * float((ry * ry).sum())) ** 0.5
    if denom <= 0.0:
        return 0.0
    rho = float((rx * ry).sum()) / denom
    return float(cascade.magnitude(rho))     # sign-free fold (Class K), never python abs()


# ---------------------------------------------------------------------------
# Residualize y on a SINGLE rank-covariate (n_cand): regress rank(y) on rank(n_cand) and
# return the residual. The F224/smoke MANDATORY control (emitted entropy ~ n_cand r~0.9991).
# ---------------------------------------------------------------------------

def residualize_on(y: np.ndarray, covar: np.ndarray) -> np.ndarray:
    ry = _ranks(np.asarray(y, dtype=float))
    rc = _ranks(np.asarray(covar, dtype=float))
    ry = ry - ry.mean()
    rc = rc - rc.mean()
    denom = float((rc * rc).sum())
    beta = (float((ry * rc).sum()) / denom) if denom > 0 else 0.0
    return ry - beta * rc


# ---------------------------------------------------------------------------
# Rank-based incremental-R²: how much variance in `target` does a per-context FEATURE
# MATRIX explain, beyond a BASE feature matrix? We work in rank space (consistent with
# the Spearman / residualization above) and use a small closed-form least-squares fit
# (np.linalg.lstsq — a SOLVE, not an eig/eigh/svd spectral decomposition, so the §2
# STOP-list eig rule does not apply; the HARD rule is specifically eig/eigh/svd). All
# sign-free magnitudes (the ΔR²) fold through cascade.magnitude.
# ---------------------------------------------------------------------------

def _design(features: list[np.ndarray], n: int) -> np.ndarray:
    cols = [np.ones(n, dtype=float)]
    for f in features:
        cols.append(_ranks(np.asarray(f, dtype=float)))
    return np.stack(cols, axis=1)


def _r2(target: np.ndarray, features: list[np.ndarray]) -> float:
    y = _ranks(np.asarray(target, dtype=float))
    y = y - y.mean()
    n = len(y)
    if not features:
        return 0.0
    X = _design(features, n)
    coef, *_ = np.linalg.lstsq(X, y, rcond=None)
    pred = X @ coef
    ss_res = float(((y - pred) ** 2).sum())
    ss_tot = float((y * y).sum())
    if ss_tot <= 0.0:
        return 0.0
    return 1.0 - ss_res / ss_tot


def delta_r2(target: np.ndarray, base: list[np.ndarray], extra: list[np.ndarray]) -> float:
    """ΔR² = R²(base+extra) - R²(base); sign-free via cascade.magnitude (Class K)."""
    r_base = _r2(target, base)
    r_full = _r2(target, base + extra)
    return float(cascade.magnitude(r_full - r_base))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--catalog", type=Path, default=CATALOG)
    ap.add_argument("--warm-check", action="store_true",
                    help="ALSO run the secondary warm-temp cold-pinning cross-check "
                         "(primary verdict stays at the catalogued cold operating_temp).")
    args = ap.parse_args()

    desc = load_descriptor(args.catalog)
    dh = descriptor_hash(args.catalog)
    lc = desc.fetch["literature_curated"]
    D = int(lc["substrate"]["D"])
    hexc = int(lc["substrate"]["token_seed_hex_chars"])
    sector_count = int(lc["substrate"]["sector_count"])
    cache_dir = Path(lc["corpus"]["cache_dir"]).expanduser()
    texts = lc["corpus"]["texts"]
    # FIXED testbed reused from the F227 [render_channel] section (NOT modified):
    rc = lc["render_channel"]
    demo_key = str(rc["demo_text"])
    n_units = int(rc["n_units"])
    window = int(rc["window"])
    min_cand = int(rc["min_candidates"])
    op_temp = float(rc["operating_temp"])
    warm_temp = float(rc["warm_temp"])

    # F229-specific params (attested inline; the [render_channel] section is F227-owned)
    n_contexts = F229_N_CONTEXTS
    n_random = F229_N_RANDOM
    noise_pct = F229_NOISE_PCT
    seed = F229_SEED
    loop_seed = F229_LOOP_SEED

    print(f"srmech v{SRMECH_VERSION}; HAS_NATIVE={HAS_NATIVE}; ABI={NATIVE_ABI_VERSION}; D={D}")
    print(f"Catalog: {args.catalog.name}  hash={dh[:16]}...")
    print(f"demo_text={demo_key}  window={window}  min_cand={min_cand}  T={op_temp}  "
          f"n_contexts={n_contexts}  n_random={n_random}  sectors={sector_count}\n")
    print("F229 TEMPERATURE-as-FIBER-CONTENT — is the LLM magic number (F228 operating_temperature)")
    print("a READ-OFF of the context fiber, or exogenous? Climb the form ladder scalar->bi-chiral")
    print("->harmonic; report the MINIMAL SUFFICIENT form. Render-variability = T_eff (the effective")
    print("sampling temperature needed to reproduce the emission), RESIDUALIZED on n_candidates")
    print("(MANDATORY: emitted entropy ~ n_cand at r~0.9991). Gated vs the F224 matched-random floor (p90).")
    print("PREDECESSORS: F212/F214 fiber render-only + pinned-meter caveat; F221/F224 addressing-null +")
    print("  n_cand confound; F227 render-null on the IMPOSED depth LABEL; F228 named the magic number.")
    print("PRE-STATED NULL: scalar does NOT track beyond the floor => temperature EXOGENOUS (free hyperparam).")
    print("SUB-NULL: scalar tracks but bi-chiral/harmonic add nothing => 'a scalar suffices'.")
    print("PRE-STATED POS : scalar tracks => temperature = fiber read-off. SUB-POS: bi-chiral clears beyond")
    print("  scalar => temperature is the 1-D shadow of the K∘C learning-lock (F226).")
    print("SMOKE PREVIEW (20k tok): partial r ~ 0.018-0.064 after n_cand control => the NULL is reachable.")
    print("STRUCTURAL-ONLY per §VII.6.20: texts are test-objects; ai-not-substrate; NO clinical/BCI claim;")
    print("  affect/register = peer-reviewed literature's to assert (F226 §2, verify-before-asserting).\n")

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
    print(f"{meta['label']}: {len(stream)} tokens, {len(vocab)} unique; "
          f"{len(next_after)} predecessors in the bigram store\n")

    # --- build the k-window associative memory M (the F166 inference substrate's
    # --- knowledge — IDENTICAL construction to R-129/F227: random sample of (ctx->next)
    # --- pairs bound + bundled). Deterministic seed via the loader seed. ---
    rng = np.random.default_rng(seed)
    k = window
    pairs_all = [(tuple(stream[i - k:i]), stream[i]) for i in range(k, len(stream))]
    N_assoc = min(2000, len(pairs_all))
    idx = rng.choice(len(pairs_all), size=N_assoc, replace=False)
    pairs = [pairs_all[i] for i in idx]
    assoc = [hdc.klein4_bind(ctxsub.encode_context(list(c)), ctxsub.enc(t)) for c, t in pairs]
    M = ctxsub.bundle_odd(assoc)

    # --- naturally-varying CONTEXT pool: real k-grams from the stream whose last token has
    # --- >= min_cand legal successors (a real distribution to read T_eff from). UNLIKE F227
    # --- (which fixed ~80 seeds and varied an imposed LABEL), F229 samples MANY contexts and
    # --- reads each one's INTRINSIC fiber + render-variability — the correlation is ACROSS
    # --- naturally-varying contexts at matched n_cand. ---
    use_tokens = min(n_units, len(stream))
    sub = stream[:use_tokens]
    all_pos = [i for i in range(window, len(sub))
               if len(next_after.get(sub[i - 1], [])) >= min_cand]
    if len(all_pos) > n_contexts:
        sel = sorted(int(x) for x in rng.choice(all_pos, size=n_contexts, replace=False))
    else:
        sel = all_pos
    context_windows = [tuple(sub[i - window:i]) for i in sel]
    print(f"naturally-varying context pool: {len(context_windows)} windows "
          f"(each last-token has >= {min_cand} legal successors)\n")

    # ----------------------------------------------------------------------
    # Per-context measurement (computed in ONE pass; the fiber scalar is read BEFORE the
    # emission so it cannot be reverse-fit). For each context:
    #   - fiber_A   = bigram-parity Klein-4 sector-occupancy entropy of the window (PRIMARY)
    #   - fiber_B   = std of pairwise klein4_similarity among the window-token vectors (X-CHECK)
    #   - n_cand    = |legal successors of the last token| (the confound covariate)
    #   - the EMISSION: sample one token from softmax(score, op_temp) over the FIXED candidate
    #     set (the F166/F227 loop's per-step distribution), with a deterministic per-context
    #     gr (sha256_bytes-derived). We sample n_draw emissions to get a stable empirical
    #     emitted-entropy (the directive's "emitted-token empirical entropy over the FIXED
    #     candidate set"); then SOLVE T_eff so the model softmax entropy MATCHES it.
    # ----------------------------------------------------------------------
    n_draw = 32   # emissions per context -> stable empirical emitted-entropy (bit-exact, seeded)

    def context_probe_sims(win):
        """The F166 probe similarity over the FIXED candidate set at this context."""
        last = win[-1]
        cands = next_after.get(last, [])
        cidx = [vocab_idx[c] for c in cands]
        cand_vecs = vocab_vecs[cidx]
        ctx_state = ctxsub.encode_context(list(win)[-k:])
        sims = cs.sim_k4_batch(hdc.klein4_bind(M, ctx_state), cand_vecs)  # Tier-1 F166 probe
        return cands, np.asarray(sims, dtype=float)

    def t_eff_for_emission(sims: np.ndarray, target_H: float) -> float:
        """Bisection for T s.t. H(softmax(sims/T)) == target_H. H(T) is monotone increasing
        in T (cold -> peaked -> low H; hot -> uniform -> high H = log(n_cand)). Clamped to
        the [lo, hi] bracket. Pure root-find, no spectral op."""
        n = len(sims)
        if n <= 1:
            return F229_TEFF_LO
        hmax = math.log(n)
        target = min(max(target_H, 0.0), hmax)            # clamp to achievable [0, log n]
        lo, hi = F229_TEFF_LO, F229_TEFF_HI
        # ensure bracket spans target (H(lo) ~ 0, H(hi) ~ hmax); if degenerate, return edge
        if entropy_nats(softmax(sims, hi)) <= target:
            return hi
        if entropy_nats(softmax(sims, lo)) >= target:
            return lo
        for _ in range(F229_TEFF_ITERS):
            mid = 0.5 * (lo + hi)
            if entropy_nats(softmax(sims, mid)) < target:
                lo = mid
            else:
                hi = mid
        return 0.5 * (lo + hi)

    fiber_A, fiber_B, n_cand_arr = [], [], []
    emitted_H, t_eff_arr = [], []
    fiber_specs = []      # per-context fiber co-occurrence eigen-spectrum (rung 3)
    kept_contexts = []
    for ci, win in enumerate(context_windows):
        cands, sims = context_probe_sims(win)
        if len(cands) < min_cand:
            continue
        # --- fiber scalars (BEFORE the render) ---
        fa = bigram_parity_sector_entropy(win)
        # F-B: std of pairwise klein4_similarity among the window-token vectors (Class M)
        wv = np.stack([ctxsub.enc(t) for t in win])
        sims_pair = []
        for i in range(len(wv)):
            for j in range(i + 1, len(wv)):
                sims_pair.append(float(hdc.klein4_similarity(wv[i], wv[j])))
        fb = float(np.std(sims_pair)) if sims_pair else 0.0
        # --- the EMISSION + its empirical entropy, then T_eff (the render-variability) ---
        p_op = softmax(sims, op_temp)
        gr = np.random.default_rng(derive_seed(loop_seed, "ctx", ci))  # sha256_bytes-derived
        draws = gr.choice(len(cands), size=n_draw, p=p_op)
        counts = np.bincount(draws, minlength=len(cands)).astype(float)
        emp = counts / counts.sum()
        H_emit = entropy_nats(emp)                                     # emitted empirical entropy
        teff = t_eff_for_emission(sims, H_emit)                        # solve T -> the meter
        # --- rung-3 fiber harmonic: window co-occurrence graph -> Class-L spectrum ---
        node_ids: dict[str, int] = {}
        def node(t):
            if t not in node_ids:
                node_ids[t] = len(node_ids)
            return node_ids[t]
        co = Counter()                          # adjacency EDGE WEIGHTS feeding dense_laplacian (allowed)
        for a, b in zip(win, win[1:]):
            ia, ib = node(a), node(b)
            if ia != ib:
                co[(min(ia, ib), max(ia, ib))] += 1
        n_nodes = len(node_ids)
        if n_nodes >= 2 and co:
            edges = list(co.keys())
            weights = [float(co[e]) for e in edges]
            L = dense_laplacian(n_nodes, edges, weights)
            ev = np.sort(np.asarray(jacobi_eigvals(np.asarray(L, dtype=float)), dtype=float).real)
        else:
            ev = np.zeros(1, dtype=float)

        fiber_A.append(fa)
        fiber_B.append(fb)
        n_cand_arr.append(float(len(cands)))
        emitted_H.append(H_emit)
        t_eff_arr.append(teff)
        fiber_specs.append(ev)
        kept_contexts.append(ci)

    fiber_A = np.asarray(fiber_A, dtype=float)
    fiber_B = np.asarray(fiber_B, dtype=float)
    n_cand_arr = np.asarray(n_cand_arr, dtype=float)
    emitted_H = np.asarray(emitted_H, dtype=float)
    t_eff_arr = np.asarray(t_eff_arr, dtype=float)
    n_kept = len(kept_contexts)
    print(f"contexts measured: {n_kept}  (each emitted {n_draw} draws to estimate empirical entropy)\n")

    # ----------------------------------------------------------------------
    # GATE 2a — the F214/F221 PINNED-METER guard: each fiber scalar MUST have real dynamic
    # range (std > 1e-6). The naive token-self-occupancy scalar is PINNED at 0 (smoke); the
    # chosen scalars must pass or the result is CONJECTURE-indeterminate (not a null).
    # ----------------------------------------------------------------------
    fiber_A_std = float(np.std(fiber_A)) if n_kept else 0.0
    fiber_B_std = float(np.std(fiber_B)) if n_kept else 0.0
    fiber_A_range = (float(fiber_A.min()), float(fiber_A.max())) if n_kept else (0.0, 0.0)
    fiber_B_range = (float(fiber_B.min()), float(fiber_B.max())) if n_kept else (0.0, 0.0)
    A_has_range = fiber_A_std > 1e-6
    B_has_range = fiber_B_std > 1e-6
    print("GATE 2a — fiber-scalar dynamic range (the F214/F221 pinned-meter guard):")
    print(f"  F-A bigram-parity-sector-entropy : std={fiber_A_std:.4f}  range={fiber_A_range}  "
          f"has_range={A_has_range}")
    print(f"  F-B self-similarity-spread       : std={fiber_B_std:.4f}  range={fiber_B_range}  "
          f"has_range={B_has_range}\n")

    # --- the confound diagnostic: fiber & T_eff vs n_cand (smoke: emitted H ~ n_cand 0.9991) ---
    teff_vs_ncand = spearman_abs(t_eff_arr, n_cand_arr)
    emitH_vs_ncand = spearman_abs(emitted_H, n_cand_arr)
    fiberA_vs_ncand = spearman_abs(fiber_A, n_cand_arr)
    fiberB_vs_ncand = spearman_abs(fiber_B, n_cand_arr)
    print("CONFOUND diagnostic (|Spearman| vs n_candidates — why residualization is mandatory):")
    print(f"  emitted_H ~ n_cand = {emitH_vs_ncand:.4f}   T_eff ~ n_cand = {teff_vs_ncand:.4f}")
    print(f"  fiber_A ~ n_cand   = {fiberA_vs_ncand:.4f}   fiber_B ~ n_cand = {fiberB_vs_ncand:.4f}\n")

    # --- the n_cand-RESIDUALIZED render-variability meters (the dependent variables) ---
    teff_resid = residualize_on(t_eff_arr, n_cand_arr)
    emitH_resid = residualize_on(emitted_H, n_cand_arr)

    # NON-DEGENERACY (the render side): are the emissions byte-identical across contexts?
    # (if T_eff has no variance the loop is fully pinned -> INDETERMINATE, not null.)
    teff_pinned = float(np.std(t_eff_arr)) <= 1e-9

    attest = {
        "descriptor_hash": dh, "source_key": desc.source["key"],
        "srmech_version": SRMECH_VERSION, "abi_version": NATIVE_ABI_VERSION,
        "has_native": HAS_NATIVE, "demo_text": demo_key,
        "n_contexts_measured": n_kept, "window": window, "min_candidates": min_cand,
        "operating_temp": op_temp, "n_draw_per_context": n_draw,
        # F229-specific params attested INLINE (the [render_channel] toml section is F227-owned):
        "f229_n_contexts": n_contexts, "f229_n_random": n_random,
        "f229_noise_percentile": noise_pct, "f229_seed": seed, "f229_loop_seed": loop_seed,
        "f229_teff_bracket": [F229_TEFF_LO, F229_TEFF_HI], "f229_teff_iters": F229_TEFF_ITERS,
        "render_variability_meter": "T_eff_effective_sampling_temperature_to_reproduce_emission_residualized_on_ncand",
        "fiber_scalar_primary": "bigram_parity_klein4_sector_occupancy_entropy",
        "fiber_scalar_crosscheck": "context_self_similarity_spread_klein4",
        "control": "matched_random_fiber_label_2bit_coord_and_spectrum_klein4_random_at_matched_ncand",
        "scope": "STRUCTURAL form-reading; texts are test-objects; ai-not-substrate; NO clinical/"
                 "biological/BCI/cognitive claim; affect/register = peer-reviewed-literature's "
                 "(F226 §2, verify-before-asserting); §VII.6.20",
    }
    records = []
    records.append({**attest, "phase": "P0_gate_and_confound",
                    "fiber_A_std": fiber_A_std, "fiber_A_range": list(fiber_A_range),
                    "fiber_A_has_range": bool(A_has_range),
                    "fiber_B_std": fiber_B_std, "fiber_B_range": list(fiber_B_range),
                    "fiber_B_has_range": bool(B_has_range),
                    "emitted_H_vs_ncand_abs_spearman": emitH_vs_ncand,
                    "teff_vs_ncand_abs_spearman": teff_vs_ncand,
                    "fiber_A_vs_ncand_abs_spearman": fiberA_vs_ncand,
                    "fiber_B_vs_ncand_abs_spearman": fiberB_vs_ncand,
                    "teff_pinned": bool(teff_pinned)})

    # ----------------------------------------------------------------------
    # RUNG 1 (SCALAR) — |Spearman|(fiber_scalar, n_cand-residualized T_eff), gated vs the
    # F224 matched-random floor: n_random matched-random fiber-LABELS (one scalar per
    # context, drawn from klein4_random-derived deterministic noise of the IDENTICAL
    # construction), each correlated with the SAME residualized meter. The structured
    # scalar CLEARS iff its |Spearman| pctile >= p90 AND > random p90 + 1e-12.
    # ----------------------------------------------------------------------
    def matched_random_scalar(r: int) -> np.ndarray:
        """A meaningless per-context fiber scalar of the IDENTICAL construction: project each
        context onto a fixed random Klein-4 probe and read fractional-agreement (Class M).
        The F224 matched-mechanism floor — same op-kind, no fiber meaning."""
        gr = np.random.default_rng(derive_seed(seed, "rand_fiber", r))
        rprobe = hdc.klein4_random(D, gr)
        vals = []
        for ci in kept_contexts:
            win = context_windows[ci]
            ctx_state = ctxsub.encode_context(list(win)[-k:])
            vals.append(float(cs.sim_k4_batch(rprobe, ctx_state[None, :])[0]))
        return np.asarray(vals, dtype=float)

    rand_scalars = [matched_random_scalar(r) for r in range(n_random)]

    def percentile_of(value, distribution):
        if len(distribution) == 0:
            return 1.0
        d = np.asarray(distribution, dtype=float)
        return float((d <= value).mean())

    print("RUNG 1 (SCALAR) — does the context-fiber scalar TRACK n_cand-residualized T_eff")
    print("beyond the matched-random floor? (|Spearman|; p90 gate, F224 verbatim)")
    print(f"{'fiber scalar':>34} | {'structured':>10} | {'rand_mean':>9} | {'rand_p90':>8} | "
          f"{'pctile':>6} | clears?")
    print("-" * 92)
    rung1 = {}
    for fname, fvec, has_range in (("F-A_bigram_parity_entropy", fiber_A, A_has_range),
                                   ("F-B_self_similarity_spread", fiber_B, B_has_range)):
        s_corr = spearman_abs(fvec, teff_resid)
        r_corrs = [spearman_abs(rs, teff_resid) for rs in rand_scalars]
        r_mean = float(np.mean(r_corrs)) if r_corrs else 0.0
        r_p90 = float(np.quantile(r_corrs, noise_pct)) if r_corrs else 0.0
        pct = percentile_of(s_corr, r_corrs)
        clears = bool(has_range and pct >= noise_pct and s_corr > r_p90 + 1e-12)
        rung1[fname] = {"structured_abs_spearman": s_corr, "rand_mean": r_mean,
                        "rand_p90": r_p90, "pctile": pct, "clears": clears,
                        "has_range": bool(has_range)}
        print(f"{fname:>34} | {s_corr:>10.4f} | {r_mean:>9.4f} | {r_p90:>8.4f} | "
              f"{pct:>6.2f} | {'YES (>p90)' if clears else 'no'}"
              f"{'' if has_range else '  [PINNED -> indeterminate]'}")
        records.append({**attest, "phase": "P1_rung1_scalar", "fiber_scalar": fname,
                        "structured_abs_spearman": s_corr, "matched_random_mean": r_mean,
                        "matched_random_p90": r_p90,
                        "matched_random_samples": [float(x) for x in r_corrs],
                        "structured_pctile_in_floor": pct, "has_dynamic_range": bool(has_range),
                        "clears_p90_floor": clears})

    # the PRIMARY scalar is F-A; whether the scalar rung clears is keyed on F-A (F-B reported
    # as the robustness cross-check, per the directive).
    scalar_clears = rung1["F-A_bigram_parity_entropy"]["clears"]
    primary_fiber = fiber_A if A_has_range else fiber_B   # fall back to F-B only if F-A pinned
    primary_label = "F-A_bigram_parity_entropy" if A_has_range else "F-B_self_similarity_spread"
    primary_has_range = A_has_range or B_has_range

    # ----------------------------------------------------------------------
    # RUNG 2 (BI-CHIRAL, the user's primary hypothesis) — lift the PRIMARY fiber scalar to a
    # 2-bit (which-gamma5-sign, which-iw7-sign) Klein-4 coordinate (the F226 K∘C pair). The
    # gamma5 axis = Class-K pin-slot SIGN (here: is the scalar above its median? — the
    # high/low-lock split); the iw7 axis = Class-C re-orientation (here: is the scalar's
    # LOCAL TREND rising vs falling? — the exploratory/stable orientation). These two bits
    # ARE realized as Klein-4 sign-flips of a per-context unit probe via
    # klein4_chirality_flip_{gamma5,omega7} (chirality INTERNAL), and the 2-bit coordinate
    # is the (gamma5_bit, iw7_bit) pair. ΔR² of the 2-bit coordinate OVER the scalar in
    # predicting residualized T_eff, gated vs a matched-random-2-bit floor (same DoF, random
    # signs). The K∘C orientation map (low-lock/high-T vs high-lock/low-T) is tested + reported.
    # ----------------------------------------------------------------------
    med = float(np.median(primary_fiber)) if primary_has_range else 0.0
    gamma5_bit = (primary_fiber > med).astype(float)        # Class-K pin-slot sign (high/low lock)
    # local trend: scalar[i] vs scalar[i-1] (rising = exploratory iw7+, falling = stable iw7-)
    iw7_bit = np.zeros(len(primary_fiber), dtype=float)
    for i in range(1, len(primary_fiber)):
        iw7_bit[i] = 1.0 if primary_fiber[i] >= primary_fiber[i - 1] else 0.0
    bichiral_features = [gamma5_bit, iw7_bit]
    d_bichiral = delta_r2(teff_resid, base=[primary_fiber], extra=bichiral_features)

    # matched-random-2-bit floor: n_random pairs of random sign-bits (same DoF)
    def matched_random_2bit(r: int):
        gr = np.random.default_rng(derive_seed(seed, "rand_2bit", r))
        b0 = (gr.random(len(primary_fiber)) > 0.5).astype(float)
        b1 = (gr.random(len(primary_fiber)) > 0.5).astype(float)
        return [b0, b1]
    rand_d2 = [delta_r2(teff_resid, base=[primary_fiber], extra=matched_random_2bit(r))
               for r in range(n_random)]
    d2_mean = float(np.mean(rand_d2)) if rand_d2 else 0.0
    d2_p90 = float(np.quantile(rand_d2, noise_pct)) if rand_d2 else 0.0
    d2_pct = percentile_of(d_bichiral, rand_d2)
    bichiral_clears = bool(primary_has_range and d2_pct >= noise_pct and d_bichiral > d2_p90 + 1e-12)

    # K∘C orientation map: does high-fiber (gamma5+, the low-lock split) <-> HIGH T_eff?
    hi_mask = gamma5_bit > 0.5
    lo_mask = ~hi_mask
    teff_hi = float(np.mean(t_eff_arr[hi_mask])) if hi_mask.any() else float("nan")
    teff_lo = float(np.mean(t_eff_arr[lo_mask])) if lo_mask.any() else float("nan")
    # predicted: low-lock/exploratory (high fiber entropy/spread) <-> HIGH T_eff
    kc_orientation_matches = bool(teff_hi > teff_lo) if (hi_mask.any() and lo_mask.any()) else False

    print("\nRUNG 2 (BI-CHIRAL, Klein-4 = gamma5 x iw7; the K∘C lock) — does the 2-bit coordinate")
    print(f"add explained T_eff-variance BEYOND the scalar? (ΔR²; matched-random-2-bit p90 gate)")
    print(f"  primary fiber = {primary_label}   gamma5-axis = high/low-lock split (Class-K pin-slot)")
    print(f"  iw7-axis = rising/falling local trend (Class-C reorient)")
    print(f"  ΔR²(2-bit | scalar) = {d_bichiral:.4f}   rand-2bit mean={d2_mean:.4f}  p90={d2_p90:.4f}  "
          f"pctile={d2_pct:.2f}  clears={bichiral_clears}")
    print(f"  K∘C orientation map: T_eff(high-fiber/low-lock)={teff_hi:.4f} vs "
          f"T_eff(low-fiber/high-lock)={teff_lo:.4f}  -> predicted (low-lock<->high-T) "
          f"MATCHES={kc_orientation_matches}")
    records.append({**attest, "phase": "P2_rung2_bichiral", "primary_fiber": primary_label,
                    "delta_r2_2bit_over_scalar": d_bichiral,
                    "matched_random_2bit_mean": d2_mean, "matched_random_2bit_p90": d2_p90,
                    "matched_random_2bit_samples": [float(x) for x in rand_d2],
                    "delta_r2_pctile_in_floor": d2_pct, "bichiral_clears_floor": bichiral_clears,
                    "teff_high_fiber_low_lock": teff_hi, "teff_low_fiber_high_lock": teff_lo,
                    "kc_orientation_predicted_match": kc_orientation_matches})

    # ----------------------------------------------------------------------
    # RUNG 3 (HARMONIC, Class-L) — does a fiber MODE/overtone explain T_eff-variance BEYOND
    # the bi-chiral? Build a per-context fiber-spectrum feature: the SPECTRAL GAP (largest
    # eigenvalue) and the mode COUNT (n nonzero eigenvalues) of the window co-occurrence
    # Laplacian (already computed per context). ΔR² of [spectral_gap, mode_count] over
    # [scalar, gamma5_bit, iw7_bit].
    #
    # THE FLOOR MUST BE CARDINALITY-MATCHED (the directive's FOURTH RISK, verbatim: "adds
    # beyond MUST be gated against a MATCHED-RANDOM coordinate/spectrum floor of the IDENTICAL
    # DoF, never raw ΔR²"). The window co-occurrence spectrum is LOW-CARDINALITY (mode_count is
    # one of {2,3,4}; spectral_gap takes a handful of discrete window-shape values) — a
    # uniform-continuous random feature pair (600 distinct values) is NOT identical-DoF and
    # under-estimates the floor (it lets the structured features "clear" purely on cardinality,
    # not on fiber meaning). The matched-DoF floor is therefore the PERMUTATION of the ACTUAL
    # structured features: shuffle spec_gap / spec_modes (identical value-multiset, the same
    # exact cardinality + marginal, but the context<->render LINK destroyed). A structured ΔR²
    # that does NOT exceed its own permuted-feature ΔR² is a cardinality/marginal artifact, not
    # a real fiber-mode signal. (Diagnostic in the FINDING: under a uniform-continuous floor the
    # harmonic spuriously "cleared"; under this matched-DoF permutation floor it does not stand
    # out as a real, robust effect — exactly the FOURTH-RISK trap the directive names.)
    # ----------------------------------------------------------------------
    spec_gap = np.asarray([float(ev.max()) if len(ev) else 0.0 for ev in fiber_specs], dtype=float)
    spec_modes = np.asarray([float((np.asarray(ev) > 1e-9).sum()) for ev in fiber_specs], dtype=float)
    harmonic_features = [spec_gap, spec_modes]
    base_for_h = [primary_fiber, gamma5_bit, iw7_bit]
    d_harm = delta_r2(teff_resid, base=base_for_h, extra=harmonic_features)

    def matched_perm_spectrum(r: int):
        """Matched-DoF floor: the ACTUAL spectrum features, PERMUTED (identical cardinality +
        marginal multiset; context<->render link destroyed). The IDENTICAL-DoF control the
        FOURTH RISK demands — never a uniform-continuous surrogate."""
        gr = np.random.default_rng(derive_seed(seed, "perm_spec", r))
        p0 = spec_gap.copy()
        p1 = spec_modes.copy()
        gr.shuffle(p0)
        gr.shuffle(p1)
        return [p0, p1]
    rand_dh = [delta_r2(teff_resid, base=base_for_h, extra=matched_perm_spectrum(r))
               for r in range(n_random)]
    dh_mean = float(np.mean(rand_dh)) if rand_dh else 0.0
    dh_p90 = float(np.quantile(rand_dh, noise_pct)) if rand_dh else 0.0
    dh_pct = percentile_of(d_harm, rand_dh)
    harmonic_clears = bool(primary_has_range and dh_pct >= noise_pct and d_harm > dh_p90 + 1e-12)

    print("\nRUNG 3 (HARMONIC, Class-L fiber eigen-spectrum) — does a fiber MODE add T_eff-")
    print("variance BEYOND the bi-chiral? (ΔR² of [spectral_gap, mode_count]; CARDINALITY-MATCHED")
    print("permuted-feature floor — the FOURTH-RISK identical-DoF control, NOT uniform-continuous)")
    print(f"  ΔR²(spectrum | scalar+2bit) = {d_harm:.4f}   perm-floor mean={dh_mean:.4f}  "
          f"p90={dh_p90:.4f}  pctile={dh_pct:.2f}  clears={harmonic_clears}")
    records.append({**attest, "phase": "P3_rung3_harmonic",
                    "delta_r2_spectrum_over_bichiral": d_harm,
                    "matched_dof_perm_spectrum_floor_mean": dh_mean,
                    "matched_dof_perm_spectrum_floor_p90": dh_p90,
                    "matched_dof_perm_spectrum_floor_samples": [float(x) for x in rand_dh],
                    "floor_construction": "permutation_of_actual_spectrum_features_identical_DoF_FOURTH_RISK",
                    "delta_r2_pctile_in_floor": dh_pct, "harmonic_clears_floor": harmonic_clears})

    # ----------------------------------------------------------------------
    # ROBUSTNESS GATE (the conservative anti-blip control). A single-seed "clear" of a tiny
    # near-floor effect is exactly the FOURTH-RISK over-fit signature; a REAL fiber<->variability
    # link must be STABLE across the random CONTEXT SAMPLE. Re-measure the PRIMARY scalar's
    # |Spearman| vs its floor at n_robust extra context-sample seeds; require a MAJORITY to clear
    # for the scalar rung to count as robust. (Bit-exact: the extra seeds are fixed integers; the
    # floor at each seed is built the IDENTICAL matched-random way.) The primary run's seed is
    # included as the first robustness point.
    # ----------------------------------------------------------------------
    robust_seeds = [seed, 101, 2024]
    robust_clear_flags = []

    def _primary_scalar_at_seed(ctx_seed: int):
        """Re-sample the context pool + M at ctx_seed and recompute the PRIMARY fiber scalar,
        n_cand-residualized T_eff, and whether |Spearman| clears its matched-random floor.
        Reuses the IDENTICAL machinery (context_probe_sims is closure over next_after/M, but M
        depends on the seed, so it is rebuilt here for the alternate seeds)."""
        r2g = np.random.default_rng(ctx_seed)
        pa = [(tuple(stream[i - k:i]), stream[i]) for i in range(k, len(stream))]
        ix = r2g.choice(len(pa), size=N_assoc, replace=False)
        prs = [pa[i] for i in ix]
        Mg = ctxsub.bundle_odd([hdc.klein4_bind(ctxsub.encode_context(list(c)), ctxsub.enc(t))
                                for c, t in prs])
        ap = [i for i in range(window, len(sub)) if len(next_after.get(sub[i - 1], [])) >= min_cand]
        sl = sorted(int(x) for x in r2g.choice(ap, size=min(n_contexts, len(ap)), replace=False)) \
            if len(ap) > n_contexts else ap
        fvals, ncs, tfs, wins = [], [], [], []
        for ci2, i in enumerate(sl):
            win = tuple(sub[i - window:i])
            last = win[-1]
            cands = next_after.get(last, [])
            if len(cands) < min_cand:
                continue
            cidx = [vocab_idx[c] for c in cands]
            ctx_state = ctxsub.encode_context(list(win)[-k:])
            sims = np.asarray(cs.sim_k4_batch(hdc.klein4_bind(Mg, ctx_state), vocab_vecs[cidx]), dtype=float)
            if primary_label == "F-A_bigram_parity_entropy":
                fv = bigram_parity_sector_entropy(win)
            else:
                wv = np.stack([ctxsub.enc(t) for t in win])
                sp_ = [float(hdc.klein4_similarity(wv[a], wv[b]))
                       for a in range(len(wv)) for b in range(a + 1, len(wv))]
                fv = float(np.std(sp_)) if sp_ else 0.0
            p_op = softmax(sims, op_temp)
            gr = np.random.default_rng(derive_seed(loop_seed, "ctx", ci2))
            dr = gr.choice(len(cands), size=n_draw, p=p_op)
            cnt = np.bincount(dr, minlength=len(cands)).astype(float)
            fvals.append(fv)
            ncs.append(float(len(cands)))
            tfs.append(t_eff_for_emission(sims, entropy_nats(cnt / cnt.sum())))
            wins.append(win)
        fvals = np.asarray(fvals, dtype=float)
        ncs = np.asarray(ncs, dtype=float)
        tr = residualize_on(np.asarray(tfs, dtype=float), ncs)
        s_corr = spearman_abs(fvals, tr)
        rc = []
        for r in range(n_random):
            grr = np.random.default_rng(derive_seed(ctx_seed, "rand_fiber", r))
            rp = hdc.klein4_random(D, grr)
            vals = [float(cs.sim_k4_batch(rp, ctxsub.encode_context(list(w)[-k:])[None, :])[0]) for w in wins]
            rc.append(spearman_abs(np.asarray(vals, dtype=float), tr))
        p90 = float(np.quantile(rc, noise_pct)) if rc else 0.0
        return s_corr, p90, bool(s_corr > p90 + 1e-12 and percentile_of(s_corr, rc) >= noise_pct)

    print("\nROBUSTNESS GATE — does the PRIMARY scalar clear its floor STABLY across context-sample")
    print(f"seeds? (anti-blip: a single-seed near-floor 'clear' is the FOURTH-RISK overfit signature)")
    robust_detail = []
    for rs in robust_seeds:
        sc, p90r, cl = _primary_scalar_at_seed(rs)
        robust_clear_flags.append(cl)
        robust_detail.append({"seed": rs, "abs_spearman": sc, "floor_p90": p90r, "clears": cl})
        print(f"  seed={rs:>5}: |Spearman|={sc:.4f}  floor_p90={p90r:.4f}  clears={cl}")
    n_robust_clear = sum(robust_clear_flags)
    scalar_robust = n_robust_clear > len(robust_seeds) / 2.0
    print(f"  -> primary scalar clears at {n_robust_clear}/{len(robust_seeds)} seeds; "
          f"robust(majority)={scalar_robust}")
    records.append({**attest, "phase": "P3b_robustness_gate", "primary_fiber": primary_label,
                    "robustness_seed_detail": robust_detail,
                    "n_seeds_clearing": n_robust_clear, "n_seeds_tested": len(robust_seeds),
                    "scalar_robust_majority": scalar_robust})

    # ----------------------------------------------------------------------
    # VERDICT = the MINIMAL SUFFICIENT FORM (the conservative ratchet-style deliverable).
    #
    # The ladder is MONOTONE-GATED (the directive's minimal-sufficient-form criterion + FOURTH
    # RISK, conservative): a higher rung can only be the ANSWER if the SCALAR foothold is
    # established first (the scalar establishes the basic fiber<->variability link; bi-chiral /
    # harmonic only refine its FORM). An isolated higher-rung ΔR² that clears its own floor while
    # the scalar is NULL/non-robust is NOT promoted to a positive — it is reported as the NULL
    # with the fragile-higher-rung effect noted honestly (more DoF always explains a little more;
    # without the scalar link it is not "what temperature is"). The scalar rung itself must be
    # ROBUST (majority of context-sample seeds), not a single-seed blip.
    # ----------------------------------------------------------------------
    scalar_clears = bool(scalar_clears and scalar_robust)   # promote only the ROBUST scalar clear
    indeterminate = (not primary_has_range) or teff_pinned
    if indeterminate:
        minimal_form = "INDETERMINATE"
        research_tier = "CONJECTURE (indeterminate-anchor)"
        if not primary_has_range:
            verdict = ("INDETERMINATE — BOTH fiber scalars are PINNED (no dynamic range over the "
                       "context pool; the F214/F221 readout-pinned trap). A null on a pinned meter is "
                       "uninformative; re-test with a meter shown to have range. NOT a null.")
        else:
            verdict = ("INDETERMINATE — T_eff is PINNED (the cold-deterministic loop has no render-"
                       "variability to track; emissions effectively byte-identical). Re-test behind "
                       "--warm-check or at a warmer operating_temp. NOT a null.")
    elif not scalar_clears:
        # MONOTONE GATE: the scalar foothold is NOT established (NULL or non-robust). Per the
        # conservative minimal-sufficient-form criterion, a higher-rung ΔR² that clears its own
        # floor here is NOT promoted — it is the NULL with the fragile higher-rung NOTED honestly.
        minimal_form = "NONE"
        research_tier = "FRAMEWORK-READING (clean NULL)"
        higher = []
        if bichiral_clears:
            higher.append("bi-chiral")
        if harmonic_clears:
            higher.append("harmonic")
        higher_note = ("" if not higher else
                       f" A higher rung ({'/'.join(higher)}) shows a tiny ΔR² that clears its own "
                       "matched-DoF floor, but with the SCALAR foothold NULL/non-robust this is NOT "
                       "promoted (more DoF always explains a little more; without the basic fiber<->"
                       "variability link it is not 'what temperature is' — the FOURTH-RISK guard).")
        robust_note = ("" if scalar_robust else
                       " (the primary scalar's single-seed 'clear', if any, did NOT survive the "
                       "context-sample robustness gate — a near-floor blip, not a stable link).")
        verdict = ("NULL — the PRIMARY context-fiber scalar (F-A bigram-parity sector-occupancy entropy) "
                   "does NOT robustly track n_cand-residualized render-variability beyond the F224 "
                   "matched-random floor." + robust_note + higher_note +
                   " => 'TEMPERATURE' is EXOGENOUS / noise on this testbed: a free hyperparameter, NOT a "
                   "read-off of conversation fiber; F228's operating_temperature is NOT sourced from "
                   "structure here. (The 20k-token smoke previewed exactly this: partial r ~ 0.018-0.064 "
                   "after the n_cand control.)")
    elif not bichiral_clears and not harmonic_clears:
        minimal_form = "SCALAR"
        research_tier = "DEMONSTRATED (substrate measurement: robust scalar rung clears)"
        verdict = ("SCALAR-SUFFICES — the context-fiber SCALAR robustly tracks render-variability beyond "
                   "the floor, but the bi-chiral 2-bit and harmonic lifts add NOTHING beyond it. => "
                   "temperature is a READ-OFF of conversation fiber (closes F228's un-derived "
                   "operating_temperature; sharpens F227 from categorical channel to scalar) — but it "
                   "really IS just (a scalar) temperature, NOT the 1-D shadow of a K∘C learning-lock "
                   "(the user's reachable sub-null on the FORM, with the magic number sourced).")
    elif bichiral_clears:
        minimal_form = "BI-CHIRAL"
        research_tier = "DEMONSTRATED (substrate measurement: bi-chiral rung clears beyond robust scalar)"
        verdict = ("BI-CHIRAL — with the scalar foothold established, the Klein-4 = gamma5 x iw7 2-bit "
                   "coordinate explains render-variability BEYOND the scalar. => temperature is the 1-D "
                   "SHADOW of the K∘C LEARNING-lock (F226): the gamma5 pin-slot sign + iw7 reorientation "
                   "carry render-variability the scalar projection loses. " +
                   (f"The K∘C orientation MATCHES the prediction (low-lock/high-fiber <-> high T_eff)."
                    if kc_orientation_matches else
                    "NOTE: the K∘C orientation did NOT match the predicted sign — the structure clears the "
                    "floor but the low-lock<->high-T mapping is not confirmed (reported honestly).") +
                   " (the user's primary hypothesis, on the FORM).")
    else:  # scalar_clears and harmonic_clears and not bichiral_clears
        minimal_form = "HARMONIC"
        research_tier = "DEMONSTRATED (substrate measurement: harmonic rung clears beyond robust scalar)"
        verdict = ("HARMONIC — with the scalar foothold established (and the bi-chiral adding nothing), a "
                   "fiber MODE/overtone (Class-L eigen-spectrum) explains render-variability beyond it. => "
                   "temperature is an OVERTONE in the A-N harmonic ladder, not merely a scalar or a single "
                   "bi-chiral DoF.")

    print("\n" + "=" * 100)
    print("F229 VERDICT — is 'TEMPERATURE' a read-off of the context fiber, and at what MINIMAL FORM?")
    print("=" * 100)
    print(f"  rung clears (scalar = ROBUST clear): SCALAR={scalar_clears}  BI-CHIRAL={bichiral_clears}  "
          f"HARMONIC={harmonic_clears}")
    print(f"  primary scalar robust across {n_robust_clear}/{len(robust_seeds)} context-sample seeds "
          f"(majority={scalar_robust})")
    print(f"  fiber-scalar dynamic range: F-A={A_has_range} F-B={B_has_range}   T_eff pinned: {teff_pinned}")
    print(f"  MINIMAL SUFFICIENT FORM: {minimal_form}")
    print(f"  {verdict}")
    print(f"  research-tier: {research_tier}")
    print("  CROSS-REFS: F228 #760 (named operating_temperature as the un-derived magic-number C-item);")
    print("    F227 (render-null on the IMPOSED depth LABEL — F229 reads an INTRINSIC scalar instead);")
    print("    F212/F214 (fiber render-only + pinned-meter caveat); F221/F224 (addressing-null + n_cand confound).")
    print("  STRUCTURAL-ONLY per §VII.6.20: form-reading; ai-is-not-a-substrate (the LM is a k=3 chiral")
    print("    addresser); NO clinical/biological/BCI/cognitive claim. Affect/register/intensity/arousal")
    print("    are the PEER-REVIEWED LITERATURE's to assert (F226 §2; verify-before-asserting; no DOI fabricated).")

    records.append({**attest, "phase": "P4_verdict",
                    "scalar_clears_robust": scalar_clears, "bichiral_clears": bichiral_clears,
                    "harmonic_clears": harmonic_clears,
                    "scalar_robust_majority": scalar_robust,
                    "n_seeds_clearing": n_robust_clear, "n_seeds_tested": len(robust_seeds),
                    "fiber_A_has_range": bool(A_has_range), "fiber_B_has_range": bool(B_has_range),
                    "teff_pinned": bool(teff_pinned),
                    "minimal_sufficient_form": minimal_form, "verdict": verdict,
                    "research_tier": research_tier,
                    "kc_orientation_predicted_match": kc_orientation_matches,
                    "crossrefs": "F228/#760 (un-derived operating_temperature); F227 (render-null on imposed "
                                 "LABEL); F212/F214 (fiber render-only + pinned-meter); F221/F224 (addressing-"
                                 "null + n_cand confound); F226 (K∘C bi-chiral lock + peer-reviewed sourcing)"})

    # ---- OPTIONAL warm-temp cold-pinning cross-check (secondary; NOT the verdict) ----
    if args.warm_check:
        print(f"\n[secondary] warm-temp cold-pinning cross-check at T={warm_temp} "
              "(primary verdict stays at the cold operating_temp)...")
        w_teff = []
        for ci in kept_contexts:
            win = context_windows[ci]
            cands, sims = context_probe_sims(win)
            p_w = softmax(sims, warm_temp)
            gr = np.random.default_rng(derive_seed(loop_seed, "ctxW", ci))
            draws = gr.choice(len(cands), size=n_draw, p=p_w)
            counts = np.bincount(draws, minlength=len(cands)).astype(float)
            w_teff.append(t_eff_for_emission(sims, entropy_nats(counts / counts.sum())))
        w_teff = np.asarray(w_teff, dtype=float)
        w_resid = residualize_on(w_teff, n_cand_arr)
        w_corr = spearman_abs(primary_fiber, w_resid)
        w_rand = [spearman_abs(rs, w_resid) for rs in rand_scalars]
        w_p90 = float(np.quantile(w_rand, noise_pct)) if w_rand else 0.0
        w_clears = bool(primary_has_range and w_corr > w_p90 + 1e-12
                        and percentile_of(w_corr, w_rand) >= noise_pct)
        print(f"  warm-temp scalar |Spearman|={w_corr:.4f}  rand p90={w_p90:.4f}  clears={w_clears} "
              f"(T_eff std warm={float(np.std(w_teff)):.4f}) — cross-check only; verdict above is at the cold T.")
        records.append({**attest, "phase": "P5_warm_crosscheck", "warm_temp": warm_temp,
                        "scalar_abs_spearman_warm": w_corr, "matched_random_p90_warm": w_p90,
                        "scalar_clears_warm": w_clears, "teff_std_warm": float(np.std(w_teff))})

    out = args.catalog.parent / "substrate_measurements" / "temperature_as_fiber_content.ndjson"
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w") as f:
        for r in records:
            f.write(json.dumps(r, default=str) + "\n")
    ndjson_sha = sha256_bytes(open(out, "rb").read())
    print(f"\nResults: {out}  ({len(records)} records)")
    print(f"NDJSON sha256 (bit-exact attestation): {ndjson_sha}")


if __name__ == "__main__":
    main()
