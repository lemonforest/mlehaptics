"""Siona's recall surface (the srmech-profile bridge): the de Bruijn fiber walk (F805/F818) + the full-body recall
path (F825), pure-Python and exact. Symbol-agnostic — operates on integer ids, so the same ops serve text tokens,
DNA bases (de Bruijn graphs ARE genome assembly), or any discrete stream.

rc1 recalls from the loose RBS-HDC instrument (an NDJSON of per-body shapes + a title→offset index). A native
single-file srmech genome (`srmech.amsc.genome`, PKG-3/F832/F833) was prototyped and recalls exactly, but the genome
format is blocked at corpus scale on two counts — it stores each 2-bit Klein-4 lane as a full byte (a flat 4× bloat)
and `genome_pack` is O(n²) in chromosome count — both filed upstream (UPSTREAM_NOTES §55). Native-genome bodies are
revisited once those land; rc1 ships on the loose store. The Klein-4 HV of a token is a deterministic *projection*
(`klein4_random(seed=hash(token))`) recomputed on demand at inference — the store holds the fiber (the sequence),
never a spatial HV per position (F833)."""
import json

__all__ = ["walk", "recall", "route", "two_mode_recall"]

# --- the recall MODE BOUNDARY (F851/F853, corrected by the F853 §CORRECTION) -------------------
# WALK / sequence mode -> read the FULL metric: walk()/recall() below, AND per-context walk-position
#   routing (the F840 vote). De-lensing the walk HURTS it (F849 generation 8%->3%; F853-corr the F840
#   vote 94.3%->68.6%) — the high-frequency tokens ARE the curvature the walk rides.
# ABOUT / meaning mode -> read the DE-LENSED metric: route() below — content/topic/aboutness queries
#   (snippet -> which tome). De-lensing HELPS this (F853 80%->90%): meaning is the anti-mass content;
#   mass is a distractor. The discriminator is "content/meaning query vs sequence/walk op," NOT
#   "routing vs generation" (some routing is walk-mode).
# two_mode_recall() is SCALE-COVARIANT (F851): the de-lensed route is the COARSE pass (which tome),
#   the full-metric walk is the FINE pass (within it). Resolve to the query's scale — coherence is a
#   DoF, there is no single fixed match target (F851).
# DESIGN, not yet wired (need the chirality-native encoder F844-F848, absent from this loose store):
#   (a) chiral cosets + route/scope for multi-domain stores (F848 — orthogonal cosets make cross-
#       domain contamination structurally impossible; "clump don't divide", within-domain sharing is
#       signal, F778); (b) coherence-GATED co-evolution ONLY (F851 — naive plastic recall runs away
#       76%->42%, so any walk-reshapes-store step must gate on confidence).
DELENS_MIN_LEN = 4       # de-lens heuristic: keep content words (len>=4); drops short function words
# DIM DISCIPLINE (F871; F811 prior): use 2^n, never a round decimal. 10000 is an unattested
#   MAGIC NUMBER kept ONLY because the live v082 instrument was encoded at it (flipping it
#   needs a full re-encode). New stores -> D=2^13=8192 (Class-A attested; packs the Klein-4
#   boolean belly, 2 bits/slot). Measured truth: capacity is DIMENSION-INDEPENDENT (~24-bind
#   SNR wall, 1/sqrt(N)) -> CHUNK for capacity, SIZE D for reliability (~sqrt(D)), 2^n for
#   attestation+packing. Do NOT grow D to fix capacity; it can't. Migrate to 8192 on re-encode.
_SUBSTRATE_D = 10000     # LEGACY magic dim — matches the v082 instrument; new work uses 8192 (F871)
_CS = None               # lazily-built ContextSubstrate singleton (token -> deterministic Klein-4 HV)


def walk(ids, k):
    """Reconstruct a sequence by walking its de Bruijn (k-1)-gram → successor map from the seed.
    `ids`: a list of hashable symbols (ints/strings); `k`: the window. Returns the reconstructed list
    (== `ids` when the walk is unique, i.e. k ≥ k*; otherwise the most-likely / first-seen-successor walk)."""
    if k < 2 or len(ids) < k:
        return list(ids)
    succ = {}
    for i in range(k - 1, len(ids)):
        succ.setdefault(tuple(ids[i - (k - 1):i]), ids[i])   # first successor wins (unique when k ≥ k*)
    out = list(ids[:k - 1])
    for _ in range(len(ids) - (k - 1)):
        nxt = succ.get(tuple(out[-(k - 1):]))
        if nxt is None:
            break
        out.append(nxt)
    return out


_IDX_CACHE = {}


def _index(index_path):
    idx = _IDX_CACHE.get(index_path)
    if idx is None:
        with open(index_path) as f:
            idx = json.load(f)
        _IDX_CACHE[index_path] = idx
    return idx


def recall(title, instrument_path, index_path):
    """THE RECALL PATH: reconstruct an entire body by title. Resolve title → byte offset via the index, seek the
    NDJSON instrument, read the record (`s` = space-joined tokens, `k` = the unique-walk window), walk the de
    Bruijn shape. Returns {tokens, k, exact, native} or None if the title isn't in the instrument. The host
    supplies its own instrument + index paths — the op stays general (any RBS-HDC instrument, any process)."""
    off = _index(index_path).get(title.lower())
    if off is None:
        return None
    with open(instrument_path) as f:
        f.seek(off)
        rec = json.loads(f.readline())
    toks = rec["s"].split()
    k = rec["k"]
    out = walk(toks, k)
    return {"tokens": out, "k": k, "exact": out == toks, "native": False}


def _delens_bundle(tokens, mass):
    """ABOUT-mode de-lensed Klein-4 content bundle: drop the mass (high-frequency function-word
    background, F849/F850) + short tokens, mint each surviving content token to its deterministic
    Klein-4 HV (the on-demand projection), bundle. Returns the bundle HV, or None if no content
    survives. The mass is a distractor for *meaning*, so removed here (F853) — but NEVER for the
    walk (F853 §CORRECTION: de-lensing the walk/per-context route hurts)."""
    global _CS
    if _CS is None:
        from srmech.rbs_lm.substrate import ContextSubstrate
        _CS = ContextSubstrate(D=_SUBSTRATE_D, hex_chars=16)
    from srmech.amsc import hdc
    content = sorted({w for w in tokens if w not in mass and len(w) >= DELENS_MIN_LEN})
    if not content:
        return None
    hvs = [_CS.enc(w) for w in content]
    if len(hvs) == 1:
        return hvs[0]
    return hdc.klein4_bundle(*(hvs if len(hvs) % 2 else hvs + [hvs[0]]))   # klein4_bundle needs odd count


def route(query_tokens, candidates, mass=frozenset()):
    """ABOUT-MODE routing (F853): rank `candidates` by de-lensed Klein-4 content resonance to the
    query — "which tome is this about." `candidates`: iterable of (label, tokens). `mass`: the
    high-frequency function words to de-lens (the caller's corpus stoplist). Returns
    [(label, score), ...] sorted high→low. De-lensing sharpens aboutness (F853 80%->90%); this is the
    COARSE pass of scale-covariant recall — pair with walk-mode recall() for the fine reconstruction.
    Do NOT use this for walk-position routing — that stays full-metric (F853 §CORRECTION)."""
    from srmech.amsc import hdc
    q = _delens_bundle(query_tokens, mass)
    if q is None:
        return []
    scored = []
    for label, toks in candidates:
        b = _delens_bundle(toks, mass)
        scored.append((label, hdc.klein4_similarity(q, b) if b is not None else -1.0))
    scored.sort(key=lambda x: x[1], reverse=True)
    return scored


def two_mode_recall(query_tokens, candidates, instrument_path, index_path, mass=frozenset()):
    """SCALE-COVARIANT two-mode recall (F851/F853): COARSE about-mode route() (de-lensed) picks the
    tome, then FINE walk-mode recall() (full-metric de Bruijn shape walk) reconstructs within it.
    `candidates`: (label==title, tokens) the route ranks over (the caller's candidate tome-set — at
    corpus scale a clump/inverted-index pre-filter supplies these). Returns
    {routed_to, ranking, recall}. Resolve to the query's scale; no single fixed match target (F851)."""
    ranking = route(query_tokens, candidates, mass)
    if not ranking:
        return {"routed_to": None, "ranking": [], "recall": None}
    top = ranking[0][0]
    return {"routed_to": top, "ranking": ranking, "recall": recall(top, instrument_path, index_path)}
