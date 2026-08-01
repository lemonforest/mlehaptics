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

import ctypes
import random
from array import array

from srmech.amsc import _native, format as amsc_format
from srmech.math import hdc
from srmech.math.hv import HV


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


def _word_native_args_ok(word, D, sector, hex_chars) -> bool:
    """True iff the rc219 native word-encode can take these args — a FALSE
    routes to the pure body so validation errors surface pythonically (the
    pure path is the complete alternative, not a rescue)."""
    return (isinstance(word, str)
            and isinstance(D, int) and not isinstance(D, bool) and D >= 1
            and isinstance(sector, int) and not isinstance(sector, bool)
            and 0 <= sector <= 3
            and isinstance(hex_chars, int) and not isinstance(hex_chars, bool)
            and hex_chars >= 1)


def _encode_word_native(word: str, *, D: int, sector: int, hex_chars: int,
                        enc_mode: str) -> "HV | None":
    """ONE-crossing native word encode via ``srmech_rbs_lm_encode_word``
    (rc219; gh #827) — byte-identical to the pure byteglyph/wordhash
    composition — or ``None`` when the symbol is absent / the args don't fit
    the C contract / the call fails (pure-Python is the COMPLETE alternative,
    not a rescue). ``hex_chars`` beyond the 64-nibble sha256 digest clamps to
    64, exactly like the pure ``digest[:hex_chars]`` slice."""
    if not _native.has_native_rbs_lm_encode_word():
        return None
    if not _word_native_args_ok(word, D, sector, hex_chars):
        return None
    data = word.encode("utf-8")
    tok = ((ctypes.c_uint8 * len(data)).from_buffer_copy(data)
           if data else None)
    acc = (ctypes.c_uint32 * (1 + 2 * D))()
    scratch = (ctypes.c_uint8 * (3 * D))()
    out = (ctypes.c_uint8 * D)()
    rc = _native.LIB.srmech_rbs_lm_encode_word(
        tok, ctypes.c_size_t(len(data)), ctypes.c_uint32(D),
        ctypes.c_uint8(sector), ctypes.c_uint32(min(hex_chars, 64)),
        ctypes.c_uint32(0 if enc_mode == "byteglyph" else 1),
        acc, scratch, out)
    if rc != _native.SRMECH_OK:
        return None
    return HV(array("B", bytes(out)), sectors=4)


def encode_word_k4(word: str, *, D: int, sector: int, hex_chars: int) -> HV:
    native = _encode_word_native(word, D=D, sector=sector,
                                 hex_chars=hex_chars, enc_mode="wordhash")
    if native is not None:
        return native
    base = hdc.klein4_expand(D, token_seed(word, hex_chars))
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
    sha256 prefix. numpy-free (Class M C1 ∘ Class C sector). rc219: dispatches
    the whole byte-compose to ``srmech_rbs_lm_encode_word`` in one C crossing
    when native is present (byte-identical; gh #827)."""
    native = _encode_word_native(word, D=D, sector=sector, hex_chars=1,
                                 enc_mode="byteglyph")
    if native is not None:
        return native
    data = word.encode("utf-8")
    if len(data) == 0:
        base = hdc.klein4_expand(D, 0)  # the empty/pad atom
    else:
        base = hdc.klein4_encode_bytes(data, D)
    return hdc.klein4_bind(base, _sector_const(D, sector))


def _ladder_word(word: str, *, D: int, hex_chars: int, enc_mode: str) -> HV:
    """One word vector for the L1/L2/L3 ladder. ``enc_mode='byteglyph'`` (default
    across the ladder) byte-composes via :func:`encode_word_byteglyph` (the C1
    object); ``'wordhash'`` mints the whole-word sha256 atom via
    :func:`encode_word_k4` (the prior behaviour, the content-address dual)."""
    if enc_mode == "byteglyph":
        return encode_word_byteglyph(word, D=D, sector=0)
    return encode_word_k4(word, D=D, sector=0, hex_chars=hex_chars)


def encode_bigram_l1(word_a: str, word_b: str, *, D: int, hex_chars: int,
                     enc_mode: str = "byteglyph") -> HV:
    """L1 bigram (F917 Part B / rc18): the scale-invariant role-filler COMPOSE
    (``hdc.klein4_compose``) of the two word vectors — was a chained
    ``klein4_bind`` (involutive, similarity-DESTROYING; a one-word change
    collapsed it to ~chance), now similarity-PRESERVING — with the level-1
    sector tag."""
    parts = [_ladder_word(w, D=D, hex_chars=hex_chars, enc_mode=enc_mode)
             for w in (word_a, word_b)]
    return hdc.klein4_bind(hdc.klein4_compose(parts), _sector_const(D, 1))


def encode_skeleton_l2(
    first_bigram: tuple[str, str],
    last_bigram: tuple[str, str],
    *,
    D: int,
    hex_chars: int,
    enc_mode: str = "byteglyph",
) -> HV:
    """L2 skeleton — the "coherent word-string before a sentence" fractal node
    (F900): the SAME compositor over the two L1 vectors (the recursive rung,
    parts at level n+1 = composed vectors of level n), with the level-2 tag."""
    first_l1 = encode_bigram_l1(*first_bigram, D=D, hex_chars=hex_chars,
                                enc_mode=enc_mode)
    last_l1 = encode_bigram_l1(*last_bigram, D=D, hex_chars=hex_chars,
                               enc_mode=enc_mode)
    return hdc.klein4_bind(hdc.klein4_compose([first_l1, last_l1]),
                           _sector_const(D, 2))


def encode_sentence_l3(tokens, *, D: int, hex_chars: int,
                       enc_mode: str = "byteglyph") -> HV:
    """L3 sentence: the SAME compositor over all token vectors (the top rung) —
    one scale-invariant operator end to end (byte→word→phrase→sentence) — with
    the level-3 sector tag."""
    parts = [_ladder_word(t, D=D, hex_chars=hex_chars, enc_mode=enc_mode)
             for t in tokens]
    return hdc.klein4_bind(hdc.klein4_compose(parts), _sector_const(D, 3))


def sim_k4_batch(query, candidates):
    """Fractional-agreement similarity (F132 §3 standard) — one float per
    candidate. numpy-free: the Class-M integer ``hdc.klein4_match_count`` over
    each HV candidate, divided once by ``D`` (== the old
    ``(candidates == query).mean(axis=1)``). Floats are correct + faster here:
    the only caller is the vocab-ranking argmax/sort in ``rbs_lm/inference.py``,
    where the per-candidate exact ``Q`` of ``hdc.klein4_similarity`` would
    allocate a rational per vocab entry in the inference hot-path. The integer
    match-count → one float division skips that allocation while preserving the
    ranking order (``klein4_similarity = match_count / D`` exactly)."""
    D = len(query)
    return [hdc.klein4_match_count(query, c) / D for c in candidates]  # int/int -> float


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
    neutral = hdc.klein4_expand(D, 0)
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

    #: Window-invariant mint-cache shape (rc219; gh #827): byteglyph position
    #: keys cached for token byte-lengths up to 64 (longer tokens mint the
    #: tail positions uncached — still correct), window position keys for
    #: window sizes up to 128, plus the full 256-entry byte vocab. Rows fill
    #: LAZILY in C and persist across calls on this instance — the C-side
    #: mirror of the pure path's per-instance ``_poskey`` dict. A cached mint
    #: is byte-identical to a fresh one by construction.
    _MINT_CACHE_BYTEPOS = 64
    _MINT_CACHE_CTXPOS = 128
    _MINT_CACHE_MAX_BYTES = 64 * 1024 * 1024

    def _mint_cache_pair(self):
        """The lazily-allocated per-instance (mint_cache, mint_flags) ctypes
        pair for the native window encode — or ``(None, None)`` when the cache
        would exceed the size cap (the C then mints uncached; same bytes)."""
        cached = getattr(self, "_c_mint_cache", None)
        if cached is not None:
            return cached
        n_rows = 256 + self._MINT_CACHE_BYTEPOS + self._MINT_CACHE_CTXPOS
        if n_rows * self.D > self._MINT_CACHE_MAX_BYTES:
            self._c_mint_cache = (None, None)
        else:
            self._c_mint_cache = (
                (ctypes.c_uint8 * (n_rows * self.D))(),   # rows (zeroed)
                (ctypes.c_uint8 * n_rows)(),              # flags (zeroed once)
            )
        return self._c_mint_cache

    def _encode_context_native(self, tokens) -> "HV | None":
        """ONE-crossing native window encode via
        ``srmech_rbs_lm_encode_context`` (rc219; gh #827) — the whole k-token
        loop (per-token encode + pos-key bind + odd-padded bundle) in one C
        call, byte-identical to the pure body — or ``None`` when the symbol is
        absent / the args don't fit the C contract / the call fails
        (pure-Python is the COMPLETE alternative, not a rescue). The cached
        ``self._pad`` rides along so the C never re-mints it, and the
        per-instance mint cache carries the window-invariant byte-vocab /
        position-key mints across calls."""
        if not _native.has_native_rbs_lm_encode_context():
            return None
        if not all(isinstance(t, str) for t in tokens):
            return None
        if not _word_native_args_ok("", self.D, self.sector, self.hex_chars):
            return None
        encoded = [t.encode("utf-8") for t in tokens]
        offs = [0]
        for e in encoded:
            offs.append(offs[-1] + len(e))
        if offs[-1] > 0xFFFFFFFF or len(tokens) > 0xFFFFFFFF:
            return None                      # u32 offset contract — pure path
        blob = b"".join(encoded)
        D = self.D
        tok_bytes = ((ctypes.c_uint8 * len(blob)).from_buffer_copy(blob)
                     if blob else None)
        tok_off = (ctypes.c_uint32 * len(offs))(*offs)
        pad = (ctypes.c_uint8 * D).from_buffer_copy(self._pad.tobytes())
        mint_cache, mint_flags = self._mint_cache_pair()
        acc_outer = (ctypes.c_uint32 * (1 + 2 * D))()
        acc_inner = (ctypes.c_uint32 * (1 + 2 * D))()
        scratch = (ctypes.c_uint8 * (4 * D))()
        out = (ctypes.c_uint8 * D)()
        rc = _native.LIB.srmech_rbs_lm_encode_context(
            tok_bytes, tok_off, ctypes.c_uint32(len(tokens)),
            ctypes.c_uint32(D), ctypes.c_uint8(self.sector),
            ctypes.c_uint32(min(self.hex_chars, 64)),
            ctypes.c_uint32(0 if self.enc_mode == "byteglyph" else 1),
            pad, mint_cache, mint_flags,
            ctypes.c_uint32(self._MINT_CACHE_BYTEPOS if mint_cache else 0),
            ctypes.c_uint32(self._MINT_CACHE_CTXPOS if mint_cache else 0),
            acc_outer, acc_inner, scratch, out)
        if rc != _native.SRMECH_OK:
            return None
        return HV(array("B", bytes(out)), sectors=4)

    def encode_context(self, window) -> HV:
        """last-k tokens → ONE Klein-4 state (positional role-filler bind + bundle).

        rc219 (gh #827): dispatches the WHOLE window to
        ``srmech_rbs_lm_encode_context`` in one C crossing when native is
        present — profile showed ~90%+ of the per-window latency was Python
        per-token orchestration + k FFI hops (127 ms → a few ms at D=4096,
        k=16), the cost that compounds to the multi-day enwiki estimate. The
        pure per-token body below is the COMPLETE, byte-identical alternative."""
        tokens = list(window)
        native = self._encode_context_native(tokens)
        if native is not None:
            return native
        bound = [hdc.klein4_bind(self.pos_key(p), self.enc(tok))
                 for p, tok in enumerate(tokens)]
        return self.bundle_odd(bound)
