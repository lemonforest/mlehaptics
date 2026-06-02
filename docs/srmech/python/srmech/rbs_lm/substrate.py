"""srmech.rbs_lm.substrate — Klein-4 chirality-level encode primitives + the
rolling context-state encoder (the F166 inference-substrate "hidden state").

Ported VERBATIM from the research subtree's ``_canonical_substrate`` (the F166
walk; UPSTREAM_NOTES §9). The encode helpers and :class:`ContextSubstrate` are
bit-exact: SHA-256 token seeds → fixed Klein-4 vectors, exact (F₂)²-XOR bind,
per-bit-majority bundle. The numpy-level encode semantics (NOT the bytes-based
``hdc.klein4_*`` public API) are preserved so generated sequences stay
re-derivable.

Class composition: Class A (content-hash mint via ``token_seed``) ∘ Class M
(``klein4_bind`` / ``klein4_bundle``) ∘ Class I/iω₇ position keys. A named A-N
cascade under the 28-D chirality coordinate, NOT a bolted-on neural state.

The ``D`` and ``hex_chars`` are arguments, not module-level constants — they
flow in from the descriptor catalog (or an in-memory params dict).
"""
from __future__ import annotations

import numpy as np

from srmech.amsc import hdc, format as amsc_format


# ---------------------------------------------------------------------------
# Encoding primitives — D and hex_chars are arguments, not module-level
# ---------------------------------------------------------------------------

def token_seed(name: str, hex_chars: int) -> int:
    """SHA-256 prefix → integer seed. Hex prefix width is catalog-controlled."""
    digest = amsc_format.sha256_bytes(name.encode("utf-8"))
    return int(digest[:hex_chars], 16)


def encode_word_k4(word: str, *, D: int, sector: int, hex_chars: int) -> np.ndarray:
    rng = np.random.default_rng(token_seed(word, hex_chars))
    base = hdc.klein4_random(D, rng)
    return hdc.klein4_bind(base, np.full(D, sector, dtype=np.uint8))


def encode_bigram_l1(word_a: str, word_b: str, *, D: int, hex_chars: int) -> np.ndarray:
    w_a = encode_word_k4(word_a, D=D, sector=0, hex_chars=hex_chars)
    w_b = encode_word_k4(word_b, D=D, sector=0, hex_chars=hex_chars)
    bound = hdc.klein4_bind(w_a, w_b)
    return hdc.klein4_bind(bound, np.full(D, 1, dtype=np.uint8))


def encode_skeleton_l2(
    first_bigram: tuple[str, str],
    last_bigram: tuple[str, str],
    *,
    D: int,
    hex_chars: int,
) -> np.ndarray:
    first_l1 = encode_bigram_l1(*first_bigram, D=D, hex_chars=hex_chars)
    last_l1 = encode_bigram_l1(*last_bigram, D=D, hex_chars=hex_chars)
    bound = hdc.klein4_bind(first_l1, last_l1)
    return hdc.klein4_bind(bound, np.full(D, 2, dtype=np.uint8))


def encode_sentence_l3(tokens, *, D: int, hex_chars: int) -> np.ndarray:
    accum = encode_word_k4(tokens[0], D=D, sector=0, hex_chars=hex_chars)
    for w in tokens[1:]:
        accum = hdc.klein4_bind(
            accum, encode_word_k4(w, D=D, sector=0, hex_chars=hex_chars)
        )
    return hdc.klein4_bind(accum, np.full(D, 3, dtype=np.uint8))


def sim_k4_batch(query: np.ndarray, candidates: np.ndarray) -> np.ndarray:
    """Fractional-agreement similarity (F132 §3 standard)."""
    return (candidates == query).mean(axis=1)


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

    def __init__(self, *, D: int, hex_chars: int, sector: int = 0):
        self.D = int(D)
        self.hex_chars = int(hex_chars)
        self.sector = int(sector)
        self._poskey: dict[int, np.ndarray] = {}
        self._pad = self.enc("__bundle_pad__")  # fixed neutral tie-breaker

    def enc(self, tok: str, sector: int | None = None) -> np.ndarray:
        return encode_word_k4(
            tok, D=self.D,
            sector=self.sector if sector is None else sector,
            hex_chars=self.hex_chars,
        )

    def pos_key(self, p: int) -> np.ndarray:
        if p not in self._poskey:
            self._poskey[p] = self.enc(f"__ctx_pos_{p}__")
        return self._poskey[p]

    def bundle_odd(self, vecs) -> np.ndarray:
        """klein4_bundle requires an ODD count; APPEND a fixed neutral pad when
        the count is even — never DROP a real token (the 126 sawtooth fix)."""
        if len(vecs) == 1:
            return vecs[0]
        if len(vecs) % 2 == 0:
            vecs = list(vecs) + [self._pad]
        return hdc.klein4_bundle(*vecs)

    def encode_context(self, window) -> np.ndarray:
        """last-k tokens → ONE Klein-4 state (positional role-filler bind + bundle)."""
        bound = [hdc.klein4_bind(self.pos_key(p), self.enc(tok))
                 for p, tok in enumerate(window)]
        return self.bundle_odd(bound)
