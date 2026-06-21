"""srmech.rbs_lm.substrate — Klein-4 chirality-level encode primitives + the
rolling context-state encoder (the F166 inference-substrate "hidden state").

Ported from the research subtree's ``_canonical_substrate`` (the F166 walk;
UPSTREAM_NOTES §9). The encode helpers and :class:`ContextSubstrate` are
deterministic: SHA-256 token seeds → fixed Klein-4 vectors, exact (F₂)²-XOR
bind, per-bit-majority bundle. **numpy-free as of v0.7.5rc113** (#564 carrier
arc) — the encode path is the framework-native ``hdc.klein4_*`` :class:`HV`
surface end-to-end, and the per-token vector seed is the stdlib
``random.Random(token_seed(word))`` stream (the §22 numpy-optional core) rather
than ``numpy.random.default_rng``. numpy was only ever an *incidental
deterministic source* here — never a correctness oracle — so the values are
re-baselined onto our own RNG ONCE and stay re-derivable forever after: same
corpus + params + ``srmech_version`` + seed → bit-identical output, now with no
numpy present at all.

Class composition: Class A (content-hash mint via ``token_seed``) ∘ Class M
(``klein4_bind`` / ``klein4_bundle``) ∘ Class I/iω₇ position keys. A named A-N
cascade under the 28-D chirality coordinate, NOT a bolted-on neural state.

The ``D`` and ``hex_chars`` are arguments, not module-level constants — they
flow in from the descriptor catalog (or an in-memory params dict).
"""
from __future__ import annotations

import random

from srmech.amsc import hdc, format as amsc_format
from srmech.amsc.hv import HV


# ---------------------------------------------------------------------------
# Encoding primitives — D and hex_chars are arguments, not module-level
# ---------------------------------------------------------------------------

def token_seed(name: str, hex_chars: int) -> int:
    """SHA-256 prefix → integer seed. Hex prefix width is catalog-controlled."""
    digest = amsc_format.sha256_bytes(name.encode("utf-8"))
    return int(digest[:hex_chars], 16)


def _sector_const(D: int, sector: int) -> bytes:
    """A length-``D`` Klein-4 constant vector with every position == ``sector``
    (the (F₂)²-XOR sector key). numpy-free; ``hdc.klein4_bind`` coerces bytes."""
    return bytes([sector]) * D


def encode_word_k4(word: str, *, D: int, sector: int, hex_chars: int) -> HV:
    base = hdc.klein4_random(D, seed=token_seed(word, hex_chars))
    return hdc.klein4_bind(base, _sector_const(D, sector))


def encode_word_byteglyph(word: str, *, D: int, sector: int) -> HV:
    """Byte-composed word vector — the C1 byte/glyph LM object (F900/F901/F916):
    ``klein4_bind(klein4_encode_bytes(word.utf8), sector_const(sector))``. The
    scale-invariant role-filler bundle over the word's UTF-8 bytes, with the
    sector channel preserved. This is the byte/glyph DUAL of the word-hash
    :func:`encode_word_k4`: it restores MORPHOLOGY (``sim('cat','cats')`` ≫ the
    ~0.25 chance level the word-hash gives, because shared prefix bytes occupy
    shared positions) and strips the word-atomic English/whitespace privilege
    (it hashes raw UTF-8, the universal-script alphabet). An empty token routes
    to a fixed neutral atom (``klein4_encode_bytes`` requires non-empty).
    ``hex_chars`` is intentionally absent — the bytes ARE the seed, not a
    sha256 prefix. numpy-free (Class M C1 ∘ Class C sector)."""
    data = word.encode("utf-8")
    if len(data) == 0:
        base = hdc.klein4_random(D, seed=0)  # the empty/pad atom
    else:
        base = hdc.klein4_encode_bytes(data, D)
    return hdc.klein4_bind(base, _sector_const(D, sector))


def encode_bigram_l1(word_a: str, word_b: str, *, D: int, hex_chars: int) -> HV:
    w_a = encode_word_k4(word_a, D=D, sector=0, hex_chars=hex_chars)
    w_b = encode_word_k4(word_b, D=D, sector=0, hex_chars=hex_chars)
    bound = hdc.klein4_bind(w_a, w_b)
    return hdc.klein4_bind(bound, _sector_const(D, 1))


def encode_skeleton_l2(
    first_bigram: tuple[str, str],
    last_bigram: tuple[str, str],
    *,
    D: int,
    hex_chars: int,
) -> HV:
    first_l1 = encode_bigram_l1(*first_bigram, D=D, hex_chars=hex_chars)
    last_l1 = encode_bigram_l1(*last_bigram, D=D, hex_chars=hex_chars)
    bound = hdc.klein4_bind(first_l1, last_l1)
    return hdc.klein4_bind(bound, _sector_const(D, 2))


def encode_sentence_l3(tokens, *, D: int, hex_chars: int) -> HV:
    accum = encode_word_k4(tokens[0], D=D, sector=0, hex_chars=hex_chars)
    for w in tokens[1:]:
        accum = hdc.klein4_bind(
            accum, encode_word_k4(w, D=D, sector=0, hex_chars=hex_chars)
        )
    return hdc.klein4_bind(accum, _sector_const(D, 3))


def sim_k4_batch(query, candidates):
    """Fractional-agreement similarity (F132 §3 standard) — one float per
    candidate. numpy-free: the Class-M ``hdc.klein4_similarity`` over each HV
    candidate (== the old ``(candidates == query).mean(axis=1)``)."""
    return [hdc.klein4_similarity(query, c) for c in candidates]


def scale_signature(parts):
    """Coherence == scale-invariance, made introspectable (F900). Returns the
    mean retained self-similarity of the composed whole vs each one-part-
    perturbed whole: compose the parts (C1, :func:`hdc.klein4_compose`), then for
    each position swap that part for a fixed neutral atom and measure how far the
    composite moves. A COHERENT (on-manifold) hierarchy degrades GRACEFULLY and
    uniformly — ~``(n-1)/n`` per perturbation, the SAME fractal signature at
    every scale (byte→word→phrase→sentence); an incoherent fold (chained-bind)
    collapses toward chance. The returned exact :class:`Q` rational in ``[0, 1]``
    is the mean retained similarity; a tight spread across positions IS the
    scale-invariance the byte/glyph LM is built on. numpy-free; composes
    :func:`hdc.klein4_compose` + :func:`hdc.klein4_similarity` (both native)."""
    parts = list(parts)
    if len(parts) < 2:
        raise ValueError("scale_signature: need at least 2 parts to perturb")
    D = len(parts[0])
    whole = hdc.klein4_compose(parts)
    neutral = hdc.klein4_random(D, seed=0)
    sims = []
    for i in range(len(parts)):
        perturbed = list(parts)
        perturbed[i] = neutral
        sims.append(hdc.klein4_similarity(whole, hdc.klein4_compose(perturbed)))
    return sum(sims) / len(sims)


# ---------------------------------------------------------------------------
# Rolling context-state encoder — the F166 inference-substrate "hidden state"
# ---------------------------------------------------------------------------

class ContextSubstrate:
    """Rolling context-state encoder (F166 walk; the inference "hidden state").

    The last-k tokens → ONE Klein-4 substrate state via positional role-filler
    binding: bundle_p[ klein4_bind(pos_key(p), enc(token_p)) ]. This is the
    state an autoregressive RBS-LM conditions its next-token distribution on
    (Steps 1-4 all share it). Catalog-driven (D, hex_chars from the descriptor's
    substrate section); deterministic / bit-exact.

    Class composition: Class A (content-hash mint via enc) ∘ Class M (klein4
    bind) ∘ Class I/iω₇ position keys, bundled. NOT a bolted-on neural state —
    a named A-N cascade under the 28D chirality coordinate.

    The even-count bundle pad (never DROP a real token) is the fix for the
    R-RBS-LM-126 first-run odd/even sawtooth artifact: klein4_bundle needs an
    ODD count (majority tie-break), so an even window APPENDS a fixed neutral
    pad vector rather than discarding a real token.
    """

    def __init__(self, *, D: int, hex_chars: int, sector: int = 0,
                 enc_mode: str = "byteglyph"):
        if enc_mode not in ("byteglyph", "wordhash"):
            raise ValueError(
                "ContextSubstrate: enc_mode must be 'byteglyph' (default — the "
                "C1 byte/glyph LM object, F916) or 'wordhash' (the fast atom "
                f"dual, the prior default); got {enc_mode!r}")
        self.D = int(D)
        self.hex_chars = int(hex_chars)
        self.sector = int(sector)
        self.enc_mode = enc_mode
        self._poskey: dict[int, HV] = {}
        self._pad = self.enc("__bundle_pad__")  # fixed neutral tie-breaker

    def enc(self, tok: str, sector: int | None = None) -> HV:
        """Encode ONE token → its Klein-4 word vector. ``enc_mode='byteglyph'``
        (default) byte-composes via :func:`encode_word_byteglyph` (the C1
        object); ``enc_mode='wordhash'`` mints the whole-word sha256 atom via
        :func:`encode_word_k4` (the prior behaviour, the content-address dual)."""
        sec = self.sector if sector is None else sector
        if self.enc_mode == "byteglyph":
            return encode_word_byteglyph(tok, D=self.D, sector=sec)
        return encode_word_k4(tok, D=self.D, sector=sec, hex_chars=self.hex_chars)

    def pos_key(self, p: int) -> HV:
        if p not in self._poskey:
            # Position role vectors are ALWAYS orthogonal word-hash atoms
            # (sha256 avalanche), enc_mode-INDEPENDENT: byte-composing the
            # near-identical "__ctx_pos_k__" labels would CORRELATE adjacent
            # roles (defeating the role-filler binding), and minting them this
            # way makes 'wordhash' mode reproduce the prior encode_context bytes
            # exactly (the behaviour-pin guarantee).
            self._poskey[p] = encode_word_k4(
                f"__ctx_pos_{p}__", D=self.D, sector=self.sector,
                hex_chars=self.hex_chars)
        return self._poskey[p]

    def bundle_odd(self, vecs) -> HV:
        """klein4_bundle requires an ODD count; APPEND a fixed neutral pad when
        the count is even — never DROP a real token (the 126 sawtooth fix)."""
        if len(vecs) == 1:
            return vecs[0]
        if len(vecs) % 2 == 0:
            vecs = list(vecs) + [self._pad]
        return hdc.klein4_bundle(*vecs)

    def encode_context(self, window) -> HV:
        """last-k tokens → ONE Klein-4 state (positional role-filler bind + bundle)."""
        bound = [hdc.klein4_bind(self.pos_key(p), self.enc(tok))
                 for p, tok in enumerate(window)]
        return self.bundle_odd(bound)
