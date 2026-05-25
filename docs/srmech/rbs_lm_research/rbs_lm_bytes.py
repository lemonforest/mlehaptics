"""R-RBS-LM-25 — Byte-level vocabulary + encoder for language-agnostic RBS-LM.

Per user direction 2026-05-25: *"if we can make every existing BPE model
become byte level is what I'm hoping to find out because we remove
english privilage."*

Three structural changes from R-RBS-LM-17 Path C:

  1. VOCAB SIZE 50,257 → 256 (one row per byte value).
  2. VOCAB SOURCE: not GPT-2 WTE projection — pure Class A content-mint of
     f"LoE.byte.{n}" for n in 0..255. No source-model dependency for the
     vocab; the substrate-native mint IS the embedding.
  3. TOKENIZER: not GPT-2 BPE — just `text.encode('utf-8')`. Covers all
     languages, all UTF-8-representable content (code, emoji, mixed
     scripts) identically.

Honest framework reading per `[[user_stance_ai_is_not_a_substrate]]` and
the user's 2026-05-25 stance: the 3.3% agreement ceiling characterized
in R-RBS-LM-18 is STRUCTURAL — driven by the continuous rotation that
multi-head attention performs and the discrete bind/bundle cascade
cannot replicate (R-RBS-LM-19 falsification: attention variant 2.2% <
bundle 3.3%). Byte-level WILL NOT lift this ceiling. The win is
elsewhere:

  - Language-agnostic surface (Chinese / Arabic / code / emoji equal)
  - 196× smaller vocab table (49.1 MB → 256 KB at D=8192)
  - Zero GPT-2 dependency at inference time (tokenizer drops too)
  - D/N capacity headroom doubles (ln V drops from 10.8 to 5.5)
  - "Remove English privilege" — the BPE-induced training-distribution
    bias is structurally absent

Two harvest variants in this partition:

  VARIANT A — GPU-less byte-level from text:
    next_byte = actual next byte in source text. No teacher model.

  VARIANT B — Distill BPE source to byte-level (Path D):
    Generate text from GPT-2 (or any BPE model); retokenize the generated
    text as UTF-8 bytes; encode (byte_context, next_byte) from those
    byte-sequences. The resulting instrument has byte-level vocab + byte-
    level inference; the BPE tokenization is stripped.

Usage:
    from rbs_lm_bytes import (
        byte_vec, encode_context_bytes, encode_observation_bytes,
        compute_byte_vocab_table, vectorised_cleanup_bytes,
    )
"""

import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE.parent / "python"))
sys.path.insert(0, str(HERE))

from rbs_lm_encoder import (  # noqa: E402
    CONTEXT_WINDOW, D, bind, bundle, hierarchical_bundle,
    mint_vector, position_vec, sentinel,
)


BYTE_VOCAB_SIZE = 256


_byte_cache: dict[int, bytes] = {}


def byte_vec(byte_value: int, D: int = D) -> bytes:
    """Class A content-mint for a single byte value (0..255).

    Pure substrate-native: f"LoE.byte.{n}" — no source-model dependency.
    """
    if byte_value not in _byte_cache:
        _byte_cache[byte_value] = mint_vector(f"LoE.byte.{byte_value}", D=D)
    return _byte_cache[byte_value]


def compute_byte_vocab_table(D: int = D) -> np.ndarray:
    """Build the (256, D//8) byte vocab table via Class A content-mint.

    Returns: uint8 numpy array shape (256, D//8); each row is the bipolar
    packed-bits representation of byte n.
    """
    rows = []
    for n in range(BYTE_VOCAB_SIZE):
        rows.append(np.frombuffer(byte_vec(n, D), dtype=np.uint8))
    return np.stack(rows, axis=0)


def encode_context_bytes(byte_ids, vocab_table, D: int = D) -> bytes:
    """Kanerva sequence representation at byte level. Same structure as
    R-RBS-LM-17 Path C encode_context_path_c, just using the byte vocab
    table instead of the WTE-projected one.
    """
    if len(byte_ids) > CONTEXT_WINDOW:
        byte_ids = list(byte_ids[-CONTEXT_WINDOW:])
    n = len(byte_ids)
    if n == 0:
        return sentinel("empty_context", D)
    binds = [
        bind(vocab_table[int(b)].tobytes(), position_vec(k, D))
        for k, b in enumerate(byte_ids)
    ]
    if len(binds) == 1:
        return binds[0]
    if len(binds) % 2 == 0:
        binds.append(sentinel("context.pad", D))
    return bundle(binds)


def encode_observation_bytes(ctx, nxt, vocab_table, D: int = D) -> bytes:
    """One observation: bind(context_vec, next_byte_vec)."""
    return bind(
        encode_context_bytes(ctx, vocab_table, D),
        vocab_table[int(nxt)].tobytes(),
    )


def vectorised_cleanup_bytes(candidate: bytes, vocab_table: np.ndarray,
                              D: int = D, top_k: int = 1):
    """Class K cleanup — argmin Hamming over the 256-row byte vocab table.

    This is 196× cheaper than the BPE 50,257-row cleanup per generation step.
    """
    cand_bytes = np.frombuffer(candidate, dtype=np.uint8)
    xor = vocab_table ^ cand_bytes[np.newaxis, :]
    hamming = np.bitwise_count(xor).sum(axis=1).astype(np.int32)
    similarities = 1.0 - 2.0 * hamming / D
    idx = np.argsort(-similarities)[:top_k]
    return [(int(i), float(similarities[i])) for i in idx]


def text_to_bytes(text: str) -> list[int]:
    """Tokenize text as UTF-8 byte values. Language-agnostic; no BPE."""
    return list(text.encode("utf-8"))


def bytes_to_text(byte_ids) -> str:
    """Decode a byte-id list back to text. Uses errors='replace' so
    partial / mid-multi-byte-sequence outputs render as U+FFFD instead
    of raising; this is appropriate for transducer outputs that may
    produce structurally-malformed UTF-8."""
    return bytes(bytearray(byte_ids)).decode("utf-8", errors="replace")


if __name__ == "__main__":
    # Self-test: build vocab table; verify cleanup recovers identity
    print(f"=== R-RBS-LM-25 byte-level encoder self-test ===")
    print(f"  D = {D}; CONTEXT_WINDOW = {CONTEXT_WINDOW}")

    vt = compute_byte_vocab_table(D)
    print(f"  byte vocab table: {vt.shape}; {vt.nbytes/1024:.1f} KB")

    # Identity cleanup: hand the table row n; expect argmin to return n
    print(f"  identity cleanup smoke (10 samples):")
    n_ok = 0
    for n in [0, 1, 32, 65, 97, 128, 200, 255, 10, 200]:
        res = vectorised_cleanup_bytes(vt[n].tobytes(), vt, D, top_k=1)
        ok = res[0][0] == n
        n_ok += ok
        print(f"    byte {n} → top-1 ({res[0][0]}, {res[0][1]:+.3f}) {'OK' if ok else 'FAIL'}")
    print(f"  identity: {n_ok}/10 ok")

    # Mean pairwise similarity should be near 0 (random ±)
    print(f"\n  mean pairwise Hamming (10 random pairs):")
    rng = np.random.default_rng(0)
    hams = []
    for _ in range(10):
        i, j = int(rng.integers(0, 256)), int(rng.integers(0, 256))
        if i == j:
            continue
        xor = vt[i] ^ vt[j]
        hams.append(int(np.bitwise_count(xor).sum()))
    print(f"    Hamming: {np.mean(hams):.0f} ± {np.std(hams):.0f} (expect ~D/2 = {D//2})")

    # Tokenization round-trip — covers ASCII + Chinese + emoji
    print(f"\n  round-trip tokenization (language coverage):")
    for s in ["Hello", "你好", "مرحبا", "🌍", "f(x) = x**2 + 1"]:
        bs = text_to_bytes(s)
        rt = bytes_to_text(bs)
        print(f"    {s!r:25s} → {len(bs):3d} bytes → {rt!r}  "
              f"{'OK' if rt == s else 'FAIL'}")
