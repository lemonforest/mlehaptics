"""R-RBS-LM-28 — FFT-domain context grafting (surgical composition).

Per user direction 2026-05-25: *"the fft active context truncation. what I
was thinking is we should be able to surgically graft our context window,
so to speak."*

The framing shift from R-RBS-LM-24 chatter (FFT-as-truncation) to this
partition (FFT-as-graft) IS load-bearing:

  - Truncate: drop high-freq components → lossy. BAD for next-token prediction
    because the local syntax signal lives at high freq.
  - Graft: KEEP high-freq from recent window AND low-freq from longer buffer.
    Combine via frequency-domain surgery. The cascade sees a 64-token window
    whose CONTENTS have been surgically modified to carry long-context signal.

Class composition per the 14-class srmech vocabulary:
  - Class L (Laplacian / spectral) — the FFT decomposition step
  - Class M (HDC bind/bundle) — the existing cascade
  Composing L ∘ M is exactly the kind of cross-class operation the
  vocabulary was designed for.

Architecture:

  1. encode_context_with_graft(recent_tokens, long_buffer_tokens, vocab_table)
     - Build TWO (W, D) byte-stacked matrices: recent_W and long_buffer_W
     - FFT both along time-axis: gives (W, D) complex matrices
     - graft_frequencies(recent_fft, long_fft, cutoff) — combine
     - inverse FFT back to time domain (W, D)
     - bipolar-quantize the result (sign of real part)
     - bind each position with position_vec; bundle into context_vec

  2. The cascade (R-RBS-LM-25 byte-level or R-RBS-LM-17 Path C) sees
     context_vec the same way it does for non-grafted contexts. NO change
     to the cascade itself. The "graft" lives entirely in step 1's
     pre-processing.

Honest expectation per `[[user_stance_ai_is_not_a_substrate]]` + R-RBS-LM-19:
  - 3.3% structural ceiling probably holds for content disambiguation
  - The cascade may gain LONG-CONTEXT AWARENESS measurable via prompt
    sensitivity (does cascade output differ when long buffer is present
    vs absent? does it differ when long buffer is RELEVANT vs unrelated?)
  - Even if ceiling holds, this IS the architectural pattern that
    enables effective long-context without scaling the cascade itself

Usage:
    from rbs_lm_fft import encode_context_with_graft, graft_frequencies
    ctx_vec = encode_context_with_graft(
        recent_tokens=last_64_bytes,
        long_buffer_tokens=last_256_bytes,
        vocab_table=byte_vocab_table,
        cutoff_freq=16,  # keep low-freq < 16 from long buffer, high-freq >= 16 from recent
    )
"""

import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE.parent / "python"))
sys.path.insert(0, str(HERE))

from rbs_lm_encoder import (  # noqa: E402
    CONTEXT_WINDOW, D, bind, bundle, position_vec, sentinel,
)


# -------------------------------------------------------------------------
# Core FFT operations
# -------------------------------------------------------------------------

def stack_tokens_as_matrix(token_ids, vocab_table) -> np.ndarray:
    """Convert a token sequence to a (T, D//8) uint8 matrix.

    Each row is the bipolar-packed-bits vector for that token. Suitable
    input for FFT along the time (row) axis.
    """
    rows = [vocab_table[int(t)] for t in token_ids]
    return np.stack(rows, axis=0)


def bipolar_unpack(packed_matrix: np.ndarray) -> np.ndarray:
    """Convert (T, D//8) packed-bits matrix to (T, D) bipolar values {-1, +1}.

    FFT operates on real values; we unpack to signed integers in {-1, +1}
    for the time-axis FFT.
    """
    bits = np.unpackbits(packed_matrix, axis=1, bitorder="big")
    return (bits.astype(np.int8) * 2 - 1).astype(np.float32)


def bipolar_repack(bipolar_matrix: np.ndarray) -> np.ndarray:
    """Inverse of bipolar_unpack: (T, D) float → (T, D//8) packed uint8.

    Sign threshold at 0 — preserves the bipolar quantization the cascade
    expects. Used after FFT + graft + IFFT to fold back into the byte-vocab
    representation.
    """
    bits = (bipolar_matrix > 0).astype(np.uint8)
    return np.packbits(bits, axis=1, bitorder="big")


def fft_along_time(bipolar_matrix: np.ndarray) -> np.ndarray:
    """FFT along the time axis (axis 0). Returns (T, D) complex array.

    Each of the D hypervector dimensions is FFT'd independently across
    the T-token time series. This gives us per-dimension frequency-domain
    components.
    """
    return np.fft.fft(bipolar_matrix, axis=0)


def ifft_along_time(freq_matrix: np.ndarray) -> np.ndarray:
    """Inverse FFT along time axis. Returns (T, D) real array.

    Imaginary part should be ~0 if the frequency matrix is the result of
    a real-valued forward FFT; we take real part to discard FP noise.
    """
    return np.real(np.fft.ifft(freq_matrix, axis=0))


# -------------------------------------------------------------------------
# Graft operations (the load-bearing surgical step)
# -------------------------------------------------------------------------

def graft_frequencies(
    recent_fft: np.ndarray,
    long_fft: np.ndarray,
    cutoff_freq: int,
) -> np.ndarray:
    """Surgically combine frequency bands: low-freq from long buffer,
    high-freq from recent window.

    The fundamental graft operation. Result has SAME shape as recent_fft.

    Args:
      recent_fft:  (W_recent, D) complex — FFT of the recent window
                   (high-freq carries local next-token signal)
      long_fft:    (W_long, D) complex — FFT of the long buffer
                   (low-freq carries topic / conversation theme)
      cutoff_freq: bin index; frequencies < cutoff use LONG_FFT, >= use
                   RECENT_FFT

    The long_fft is resampled to W_recent length so the bins align.

    Returns: (W_recent, D) complex grafted matrix.
    """
    w_recent = recent_fft.shape[0]
    w_long = long_fft.shape[0]

    # Cap cutoff to half of the smaller window (positive freqs only;
    # the negative-freq mirror occupies the other half via FFT symmetry).
    # Beyond W//2 the bins overlap or invert ordering.
    effective_cutoff = min(cutoff_freq, w_recent // 2, w_long // 2)
    if effective_cutoff <= 0:
        return recent_fft.copy()

    # Resample long_fft to W_recent bins via frequency-domain decimation
    if w_long != w_recent:
        long_resampled = np.zeros_like(recent_fft)
        # Long buffer's low-freq bins (DC + lowest positive freqs)
        long_resampled[:effective_cutoff] = long_fft[:effective_cutoff] * (w_recent / w_long)
        # Mirror for negative freqs (FFT symmetry for real signals)
        long_resampled[-effective_cutoff:] = long_fft[-effective_cutoff:] * (w_recent / w_long)
        long_fft = long_resampled

    # Build the grafted matrix
    grafted = recent_fft.copy()
    grafted[:effective_cutoff] = long_fft[:effective_cutoff]
    grafted[-effective_cutoff:] = long_fft[-effective_cutoff:]

    return grafted


def drop_frequency_band(
    fft_matrix: np.ndarray,
    band_start: int,
    band_end: int,
) -> np.ndarray:
    """Zero out a frequency band (e.g., when topic switches).

    Useful for "forget the old topic" — drop the low-freq components
    of a context that was about an unrelated previous topic.
    """
    result = fft_matrix.copy()
    result[band_start:band_end] = 0
    # Mirror band for the negative-freq half (FFT symmetry)
    if band_end > 0:
        result[-band_end:-band_start if band_start > 0 else None] = 0
    return result


def add_system_prompt_fft(
    ctx_fft: np.ndarray,
    system_fft: np.ndarray,
    weight: float = 1.0,
) -> np.ndarray:
    """Add a system-prompt FFT signature to a context FFT (weighted add).

    The system prompt lives as a stable frequency-domain signature applied
    on every conversation. Adding (rather than grafting) lets it overlay
    without removing the conversation's own frequency content.
    """
    # Resample system_fft to ctx_fft length if needed
    if system_fft.shape[0] != ctx_fft.shape[0]:
        resampled = np.zeros_like(ctx_fft)
        n = min(system_fft.shape[0] // 2, ctx_fft.shape[0] // 2)
        resampled[:n] = system_fft[:n] * (ctx_fft.shape[0] / system_fft.shape[0])
        resampled[-n:] = system_fft[-n:] * (ctx_fft.shape[0] / system_fft.shape[0])
        system_fft = resampled
    return ctx_fft + weight * system_fft


# -------------------------------------------------------------------------
# End-to-end: graft into a context_vec the cascade can consume
# -------------------------------------------------------------------------

def multi_buffer_graft(
    recent_fft: np.ndarray,
    buffer_ffts,
    band_endpoints,
) -> np.ndarray:
    """R-RBS-LM-32 — Layered frequency-band composition across multiple buffers.

    Each layer gets a contiguous frequency band; layers are ordered from
    deepest/lowest-freq (most stable / topical) to shallowest/highest-freq
    (most local / recent). The recent_fft fills any bins above the last
    endpoint, preserving local syntax signal as in single-buffer graft.

    Args:
      recent_fft:     (W_recent, D) complex — FFT of the recent window
      buffer_ffts:    ordered list of (W_long, D) complex FFTs — each gets one band
      band_endpoints: ordered list of bin indices; bin range for buffer i is
                      [band_endpoints[i-1], band_endpoints[i])  (i>0)
                      and [0, band_endpoints[0])                (i=0).
                      The recent_fft fills [band_endpoints[-1], W_recent//2+1).

    Returns: (W_recent, D) complex grafted matrix; mirror bins handled for
    FFT real-signal symmetry.

    Example — 3-layer composition (system prompt + history + RAG + recent):
        multi_buffer_graft(
            recent_fft,
            buffer_ffts=[system_fft, history_fft, rag_fft],
            band_endpoints=[2, 8, 16],
        )
        # bins [0,  2): system_fft       (topic / stable instruction)
        # bins [2,  8): history_fft      (conversation arc)
        # bins [8, 16): rag_fft          (retrieved document content)
        # bins [16, W//2): recent_fft    (local syntax)
    """
    if len(buffer_ffts) != len(band_endpoints):
        raise ValueError(f"buffer_ffts ({len(buffer_ffts)}) and band_endpoints "
                         f"({len(band_endpoints)}) must have same length")
    if len(buffer_ffts) == 0:
        return recent_fft.copy()

    w_recent = recent_fft.shape[0]
    cap = w_recent // 2

    # Validate + clamp endpoints
    prev = 0
    clamped_endpoints = []
    for ep in band_endpoints:
        if ep < prev:
            raise ValueError(f"band_endpoints must be monotonically non-decreasing; "
                             f"got {band_endpoints}")
        clamped_endpoints.append(min(ep, cap))
        prev = ep

    grafted = recent_fft.copy()
    band_start = 0
    for buf_fft, band_end in zip(buffer_ffts, clamped_endpoints):
        if band_end <= band_start:
            continue  # empty band, skip
        # Resample this buffer's FFT to W_recent bins (energy-preserving scale)
        w_buf = buf_fft.shape[0]
        if w_buf == w_recent:
            buf_scaled = buf_fft
        else:
            buf_scaled = np.zeros_like(recent_fft)
            n = min(band_end, w_buf // 2)
            if n > 0:
                buf_scaled[:n] = buf_fft[:n] * (w_recent / w_buf)
                buf_scaled[-n:] = buf_fft[-n:] * (w_recent / w_buf)
        # Assign this band — positive freqs and mirror negative freqs
        grafted[band_start:band_end] = buf_scaled[band_start:band_end]
        if band_end > 0 and band_start >= 0:
            # Mirror: negative-freq bins corresponding to [band_start, band_end)
            # positive bins are at -W+band_start..-W+band_end-1 == W-band_end..W-band_start-1
            mirror_end = w_recent - band_start if band_start > 0 else w_recent
            mirror_start = w_recent - band_end
            grafted[mirror_start:mirror_end] = buf_scaled[mirror_start:mirror_end]
        band_start = band_end

    return grafted


def encode_context_with_multi_buffer_graft(
    recent_tokens,
    layered_buffer_tokens,
    layered_end_cutoffs,
    vocab_table,
    D: int = D,
) -> bytes:
    """R-RBS-LM-32 — End-to-end multi-buffer FFT-grafted context vector.

    Args:
      recent_tokens:           the last CONTEXT_WINDOW bytes the cascade sees
      layered_buffer_tokens:   ordered list of byte-token sequences, lowest-freq first
      layered_end_cutoffs:     bin-index endpoints, ordered low-to-high; parallel to
                               layered_buffer_tokens
      vocab_table:             byte vocab table (R-RBS-LM-25)

    Returns: D/8 byte hypervector suitable as ctx_vec for the cascade.

    If layered_buffer_tokens is empty, falls back to standard byte-level
    encode_context (no graft).
    """
    # Truncate recent to CONTEXT_WINDOW
    if len(recent_tokens) > CONTEXT_WINDOW:
        recent_tokens = recent_tokens[-CONTEXT_WINDOW:]
    if len(recent_tokens) == 0:
        return sentinel("empty_context", D)

    # Fallback: no buffers → standard encode
    if not layered_buffer_tokens:
        return _bundle_token_matrix(stack_tokens_as_matrix(recent_tokens, vocab_table), D)

    # Build recent FFT
    recent_matrix = bipolar_unpack(stack_tokens_as_matrix(recent_tokens, vocab_table))
    recent_fft = fft_along_time(recent_matrix)

    # Build each buffer's FFT
    buffer_ffts = []
    for buf_tokens in layered_buffer_tokens:
        if not buf_tokens:
            # Empty buffer — substitute recent's FFT for this slot (will be no-op)
            buffer_ffts.append(recent_fft)
            continue
        buf_matrix = bipolar_unpack(stack_tokens_as_matrix(buf_tokens, vocab_table))
        buffer_ffts.append(fft_along_time(buf_matrix))

    # Multi-buffer graft
    grafted_fft = multi_buffer_graft(recent_fft, buffer_ffts, layered_end_cutoffs)

    # IFFT back to time domain
    grafted_time = ifft_along_time(grafted_fft)
    grafted_packed = bipolar_repack(grafted_time)

    return _bundle_token_matrix(grafted_packed, D)


def encode_context_with_graft(
    recent_tokens,
    long_buffer_tokens,
    vocab_table,
    cutoff_freq: int = 16,
    D: int = D,
) -> bytes:
    """The load-bearing API: produce a context_vec hypervector with the
    long buffer's topic signal grafted into the recent window's local signal.

    Returns: D/8 byte hypervector suitable for use as ctx_vec in the
    existing cascade (bind(instrument, ctx_vec) → candidate → cleanup).
    """
    # Truncate to CONTEXT_WINDOW; pad if shorter
    if len(recent_tokens) > CONTEXT_WINDOW:
        recent_tokens = recent_tokens[-CONTEXT_WINDOW:]
    if len(recent_tokens) == 0:
        return sentinel("empty_context", D)

    # If no long buffer or it's the same as recent, fall back to standard
    if not long_buffer_tokens or list(long_buffer_tokens) == list(recent_tokens):
        return _bundle_token_matrix(stack_tokens_as_matrix(recent_tokens, vocab_table), D)

    # Stack both sequences as bipolar (T, D) matrices
    recent_matrix = bipolar_unpack(stack_tokens_as_matrix(recent_tokens, vocab_table))
    long_matrix = bipolar_unpack(stack_tokens_as_matrix(long_buffer_tokens, vocab_table))

    # FFT both along time axis
    recent_fft = fft_along_time(recent_matrix)
    long_fft = fft_along_time(long_matrix)

    # GRAFT: low-freq from long buffer (topic), high-freq from recent (local syntax)
    grafted_fft = graft_frequencies(recent_fft, long_fft, cutoff_freq)

    # IFFT back to time domain; bipolar-quantize
    grafted_time = ifft_along_time(grafted_fft)
    grafted_packed = bipolar_repack(grafted_time)

    # Now bundle the grafted (W, D) matrix into a single context_vec
    return _bundle_token_matrix(grafted_packed, D)


def _bundle_token_matrix(packed_matrix: np.ndarray, D: int) -> bytes:
    """Bundle a (W, D/8) packed-bits matrix into a single D/8 hypervector
    via position-binding + bundle. Mirrors the standard encode_context
    pipeline but takes a pre-built matrix instead of token_ids.
    """
    n = packed_matrix.shape[0]
    if n == 0:
        return sentinel("empty_context", D)
    if n == 1:
        return packed_matrix[0].tobytes()
    binds = [
        bind(packed_matrix[k].tobytes(), position_vec(k, D))
        for k in range(n)
    ]
    if len(binds) % 2 == 0:
        binds.append(sentinel("context.pad", D))
    return bundle(binds)


# -------------------------------------------------------------------------
# Self-test
# -------------------------------------------------------------------------

def _self_test():
    print(f"=== R-RBS-LM-28 FFT context grafting self-test ===\n")

    from rbs_lm_bytes import compute_byte_vocab_table
    vocab_table = compute_byte_vocab_table(D)
    print(f"  byte vocab table: {vocab_table.shape}")

    # Build two distinct byte sequences
    recent = list("the quick brown fox jumps".encode("utf-8"))
    long_buffer = list((
        "The morning sun cast long shadows across the cobblestones. "
        "A baker carried fresh bread from the oven, its warm scent "
        "drifting through the open window. The quick brown fox jumps"
    ).encode("utf-8"))
    print(f"  recent tokens:  {len(recent)} bytes")
    print(f"  long buffer:    {len(long_buffer)} bytes")

    # Test 1: stack tokens → bipolar unpack → FFT → IFFT → repack — round-trip
    print(f"\n  Test 1: FFT round-trip preserves matrix")
    M = stack_tokens_as_matrix(recent, vocab_table)
    Mb = bipolar_unpack(M)
    Mf = fft_along_time(Mb)
    Mr = ifft_along_time(Mf)
    Mrp = bipolar_repack(Mr)
    n_diff = int(np.bitwise_count(M ^ Mrp).sum())
    print(f"    stack shape: {M.shape}; bipolar shape: {Mb.shape}; fft shape: {Mf.shape}")
    print(f"    round-trip bit-diff: {n_diff} (expected ~0 for FFT round-trip)")

    # Test 2: graft frequencies at various cutoffs
    print(f"\n  Test 2: graft frequencies at varied cutoffs")
    recent_matrix = bipolar_unpack(stack_tokens_as_matrix(recent, vocab_table))
    long_matrix = bipolar_unpack(stack_tokens_as_matrix(long_buffer, vocab_table))
    recent_fft = fft_along_time(recent_matrix)
    long_fft = fft_along_time(long_matrix)
    for cutoff in [0, 2, 4, 8, 16, recent_fft.shape[0] // 2]:
        grafted = graft_frequencies(recent_fft, long_fft, cutoff)
        # How much does the grafted matrix differ from pure-recent at each cutoff?
        diff = float(np.abs(grafted - recent_fft).sum())
        print(f"    cutoff={cutoff:3d}: graft-vs-recent magnitude diff: {diff:.1f}")

    # Test 3: end-to-end encode_context_with_graft
    print(f"\n  Test 3: end-to-end encode_context_with_graft")
    for cutoff in [0, 8, 16, 24, 32]:
        ctx_vec = encode_context_with_graft(
            recent, long_buffer, vocab_table,
            cutoff_freq=cutoff, D=D,
        )
        # Compare to non-grafted (cutoff=0 equivalent)
        from rbs_lm_bytes import encode_context_bytes
        ctx_plain = encode_context_bytes(recent, vocab_table, D)
        h = int(np.bitwise_count(
            np.frombuffer(ctx_vec, dtype=np.uint8) ^
            np.frombuffer(ctx_plain, dtype=np.uint8)
        ).sum())
        sim = 1.0 - 2.0 * h / D
        print(f"    cutoff={cutoff:3d}: |ctx_vec|={len(ctx_vec)} bytes; "
              f"sim-to-plain-recent = {sim:+.4f}")

    # Test 4: drop frequency band
    print(f"\n  Test 4: drop frequency band (e.g., topic switch)")
    full_fft = fft_along_time(bipolar_unpack(stack_tokens_as_matrix(recent, vocab_table)))
    dropped = drop_frequency_band(full_fft, 0, 4)
    diff = float(np.abs(dropped - full_fft).sum())
    print(f"    drop low-freq band [0,4): magnitude diff from full: {diff:.1f}")

    # Test 5: multi-buffer graft — R-RBS-LM-32
    print(f"\n  Test 5: multi-buffer graft (R-RBS-LM-32)")
    system_prompt = list("You are a helpful assistant.".encode("utf-8"))
    history = list("User: Tell me about cooking. Assistant: Cooking is the practice of preparing food.".encode("utf-8"))
    rag = list(("Beating eggs incorporates air into the mixture. "
                "Use a whisk or fork in a steady motion.").encode("utf-8"))
    # 3-layer composition
    ctx_multi = encode_context_with_multi_buffer_graft(
        recent_tokens=recent,
        layered_buffer_tokens=[system_prompt, history, rag],
        layered_end_cutoffs=[2, 6, 10],
        vocab_table=vocab_table,
        D=D,
    )
    # Compare to plain (no graft)
    from rbs_lm_bytes import encode_context_bytes
    ctx_plain = encode_context_bytes(recent, vocab_table, D)
    h_plain = int(np.bitwise_count(
        np.frombuffer(ctx_multi, dtype=np.uint8) ^
        np.frombuffer(ctx_plain, dtype=np.uint8)
    ).sum())
    sim_plain = 1.0 - 2.0 * h_plain / D
    print(f"    3-layer graft (system+history+rag, endpoints [2,6,10]):")
    print(f"      sim-to-plain-recent = {sim_plain:+.4f}")

    # Compare to single-buffer graft at equivalent cutoff (10)
    ctx_single = encode_context_with_graft(recent, rag, vocab_table, cutoff_freq=10, D=D)
    h_single = int(np.bitwise_count(
        np.frombuffer(ctx_multi, dtype=np.uint8) ^
        np.frombuffer(ctx_single, dtype=np.uint8)
    ).sum())
    sim_single = 1.0 - 2.0 * h_single / D
    print(f"    sim-to-single-buffer-graft (rag only, cutoff=10) = {sim_single:+.4f}")
    print(f"    → If sim_single < 0.95: layering is doing real work, not just last-buffer wins.")

    # Edge case: empty buffer list
    ctx_empty = encode_context_with_multi_buffer_graft(
        recent_tokens=recent,
        layered_buffer_tokens=[],
        layered_end_cutoffs=[],
        vocab_table=vocab_table, D=D,
    )
    n_diff = int(np.bitwise_count(
        np.frombuffer(ctx_empty, dtype=np.uint8) ^
        np.frombuffer(ctx_plain, dtype=np.uint8)
    ).sum())
    print(f"    empty buffer list: bit-diff from plain = {n_diff} (expected 0)")

    # Edge case: single buffer should equal single-buffer graft
    ctx_one = encode_context_with_multi_buffer_graft(
        recent_tokens=recent,
        layered_buffer_tokens=[rag],
        layered_end_cutoffs=[10],
        vocab_table=vocab_table, D=D,
    )
    h_eq = int(np.bitwise_count(
        np.frombuffer(ctx_one, dtype=np.uint8) ^
        np.frombuffer(ctx_single, dtype=np.uint8)
    ).sum())
    sim_eq = 1.0 - 2.0 * h_eq / D
    print(f"    single-buffer-as-multi (rag, ep=[10]) vs single-buffer-graft sim: {sim_eq:+.4f}")
    print(f"    → Expected ≈ +1.0 (multi-buffer with one layer ≡ single-buffer graft)")


if __name__ == "__main__":
    _self_test()
