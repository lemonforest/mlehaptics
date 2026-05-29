"""Deprecation shim for the rc3 ``_chain`` module — superseded by
``_bio_totp`` in v0.5.0rc7.

Per user direction 2026-05-28: rc3's SHA-256-state-chained cipher
was structurally related to UTLP Bio-TOTP (Claim 255) but **did
not implement the actual UTLP construction**. rc7 replaces it with
:mod:`srmech.bus._bio_totp`, which carries the real UTLP wire
pattern (time-rolling key + nonce-only frame).

This module remains importable for one rc cycle (rc7) so any
downstream consumer reading the old surface gets a clear pointer
to the new module. The old names are mapped through to Bio-TOTP
equivalents where the meaning carries over; the SHA-256-chain-
specific symbols (``derive_state``, ``MAC_BYTES``,
``MacMismatchError``, ``CounterReplayError``, ``ChainFormatError``,
``COUNTER_BYTES``, ``STATE_BYTES``) are kept as deprecated
re-exports of the closest Bio-TOTP analogues so the old import
shape doesn't import-error existing user code.

Removal target: v0.5.0 final (the next clean tag).
"""

from __future__ import annotations

import warnings

from ._bio_totp import (
    BioTotpChannel as _BioTotpChannel,
    BioTotpDecryptError as _BioTotpDecryptError,
    BioTotpError as _BioTotpError,
    BioTotpFormatError as _BioTotpFormatError,
    FRAME_OVERHEAD_BYTES,
    NONCE_BYTES as _NONCE_BYTES,
    decode_splice as _decode_splice_bio_totp,
    derive_key,
)

# One-shot module-level deprecation notice (fires on first import).
warnings.warn(
    "srmech.bus._chain is deprecated as of v0.5.0rc7; use "
    "srmech.bus._bio_totp instead (UTLP Bio-TOTP cipher per Claim 255). "
    "This shim will be removed in v0.5.0 final.",
    DeprecationWarning,
    stacklevel=2,
)


# ─────────────────────────────────────────────────────────────────────
# Constant aliases — same byte widths where they overlap, dropped
# where rc3 had a distinct concept that Bio-TOTP elides.
# ─────────────────────────────────────────────────────────────────────

#: Bytes of state in rc3's chain state. Bio-TOTP has no chain state;
#: kept as 32 (= SHA-256 digest width) for any code that read the
#: constant before checking ``derive_state`` existed.
STATE_BYTES: int = 32

#: rc3 MAC-tag width. Bio-TOTP has no per-frame MAC; kept as 0 so
#: code that did ``FRAME_OVERHEAD_BYTES - MAC_BYTES`` arithmetic
#: still works (the answer becomes the new
#: ``FRAME_OVERHEAD_BYTES``).
MAC_BYTES: int = 0

#: rc3 counter width. Bio-TOTP's packet_seq is a u32, but lives
#: INSIDE the nonce, so the per-frame overhead does not break it
#: out separately.
COUNTER_BYTES: int = 4

#: rc3 direction tag — outgoing side. Bio-TOTP doesn't separate
#: directions structurally (each side uses its own ``sender_id``),
#: so the OUT/IN constants degrade to documentation-only labels.
DIRECTION_OUT: str = "out"
DIRECTION_IN: str = "in"
DIRECTIONS: frozenset = frozenset({DIRECTION_OUT, DIRECTION_IN})


# ─────────────────────────────────────────────────────────────────────
# Error-class aliases
# ─────────────────────────────────────────────────────────────────────


class ChainCipherError(_BioTotpError):
    """Deprecated alias for :class:`BioTotpError`."""


class ChainFormatError(_BioTotpFormatError, ChainCipherError):
    """Deprecated alias for :class:`BioTotpFormatError`."""


class MacMismatchError(_BioTotpDecryptError, ChainCipherError):
    """Deprecated alias for :class:`BioTotpDecryptError` — Bio-TOTP
    has no MAC; the closest analogue is a failed decryption across
    all candidate windows."""


class CounterReplayError(_BioTotpDecryptError, ChainCipherError):
    """Deprecated alias for :class:`BioTotpDecryptError` — replay
    surfaces as a decrypt failure (packet_seq guard)."""


# ─────────────────────────────────────────────────────────────────────
# Pure-function aliases
# ─────────────────────────────────────────────────────────────────────


def derive_state(
    seed: bytes,
    channel_id: bytes,
    direction: str = DIRECTION_OUT,
) -> bytes:
    """Deprecated: rc3 helper that derived a chain state from
    ``(seed, channel_id, direction)``.

    Bio-TOTP has no chain state — the per-frame key is derived from
    ``(dna, quantized_time)`` instead. For compatibility, this shim
    returns a deterministic 32-byte digest of the inputs (so any
    test that asserted ``derive_state(...) != derive_state(...)``
    on different inputs still passes), but the value has no role in
    the Bio-TOTP wire path.
    """
    warnings.warn(
        "derive_state is rc3-only; Bio-TOTP uses derive_key(dna, "
        "time_ns, window_ns) instead.",
        DeprecationWarning, stacklevel=2,
    )
    if not isinstance(seed, (bytes, bytearray)):
        raise TypeError(
            f"seed must be bytes-like; got {type(seed).__name__}"
        )
    if not isinstance(channel_id, (bytes, bytearray)):
        raise TypeError(
            f"channel_id must be bytes-like; got {type(channel_id).__name__}"
        )
    if direction not in DIRECTIONS:
        raise ValueError(
            f"direction must be one of {sorted(DIRECTIONS)!r}; "
            f"got {direction!r}"
        )
    if len(seed) == 0:
        raise ValueError("seed must be non-empty")
    from ..amsc.format import sha256_bytes
    payload = (
        bytes(seed) + b":" + bytes(channel_id) + b":"
        + direction.encode("ascii")
    )
    return bytes.fromhex(sha256_bytes(payload))


def decode_splice(framed, *args, **kwargs):
    """Deprecated: rc3 took ``(framed, state, counter)``; Bio-TOTP
    takes ``(framed, dna, *, window_ns=None, time_ns=None)``.

    For rc7 compatibility we accept either signature. If the
    second positional argument is 32 bytes AND no later argument
    looks like an int-counter, we treat it as a Bio-TOTP ``dna``
    arg and dispatch to :func:`srmech.bus._bio_totp.decode_splice`.
    The chain-shaped signature raises a clear error pointing at the
    new module.
    """
    warnings.warn(
        "srmech.bus._chain.decode_splice is deprecated; use "
        "srmech.bus._bio_totp.decode_splice (signature: "
        "(framed, dna, *, window_ns=None, time_ns=None)).",
        DeprecationWarning, stacklevel=2,
    )
    if len(args) >= 2 and isinstance(args[1], int):
        raise TypeError(
            "rc3 decode_splice signature (framed, state, counter) is "
            "no longer supported in rc7. Use "
            "srmech.bus._bio_totp.decode_splice(framed, dna, "
            "window_ns=..., time_ns=...) instead."
        )
    return _decode_splice_bio_totp(framed, *args, **kwargs)


# ─────────────────────────────────────────────────────────────────────
# ChainState — adapter onto BioTotpChannel
# ─────────────────────────────────────────────────────────────────────


class ChainState:
    """Deprecated: rc3 per-direction chain state.

    rc7 routes this through :class:`BioTotpChannel`. Constructor
    accepts the rc3 signature ``(seed, channel_id, direction)`` and
    derives a Bio-TOTP channel with ``dna = seed``, ``sender_id`` =
    deterministic hash of ``(channel_id, direction)`` so the two
    directions get distinct nonces (matching rc3's keystream-
    disjointness guarantee at a different algebraic layer).

    The MAC-mismatch / counter-replay error surfaces become
    Bio-TOTP-decrypt failures, but the same exception-class names
    are kept (via the alias classes above) so rc6-era except clauses
    still catch the failures.
    """

    __slots__ = ("_bio", "_direction")

    def __init__(
        self,
        seed: bytes,
        channel_id: bytes,
        direction: str,
    ) -> None:
        warnings.warn(
            "ChainState is rc3-only; use BioTotpChannel from "
            "srmech.bus._bio_totp instead.",
            DeprecationWarning, stacklevel=2,
        )
        if direction not in DIRECTIONS:
            raise ValueError(
                f"direction must be one of {sorted(DIRECTIONS)!r}; "
                f"got {direction!r}"
            )
        if not isinstance(seed, (bytes, bytearray)):
            raise TypeError(
                f"seed must be bytes-like; got {type(seed).__name__}"
            )
        if len(seed) == 0:
            raise ValueError("seed must be non-empty")
        if len(seed) < 32:
            raise ValueError(
                f"seed must be ≥ 32 bytes for Bio-TOTP; got {len(seed)}"
            )
        # Deterministic sender_id from (channel_id, direction) so the
        # OUT and IN halves don't collide on the wire — rc3 used
        # separate keystreams; we use distinct nonces.
        from ..amsc.format import sha256_bytes
        sender_seed = (
            bytes(channel_id) + b":" + direction.encode("ascii")
        )
        sender_id = int.from_bytes(
            bytes.fromhex(sha256_bytes(sender_seed))[:8], "big",
        )
        channel_id_int = int.from_bytes(
            bytes.fromhex(sha256_bytes(bytes(channel_id)))[:4], "big",
        )
        self._bio = _BioTotpChannel(
            dna=bytes(seed),
            sender_id=sender_id,
            channel_id=channel_id_int,
        )
        self._direction = direction

    @property
    def direction(self) -> str:
        return self._direction

    @property
    def state(self) -> bytes:
        """rc3 chain-state surface. Bio-TOTP has no chain state;
        returns a deterministic 32-byte derivation of the channel
        identity so legacy code reading the property doesn't error."""
        from ..amsc.format import sha256_bytes
        payload = (
            self._bio.dna
            + b":" + str(self._bio.sender_id).encode("ascii")
            + b":" + str(self._bio.channel_id).encode("ascii")
        )
        return bytes.fromhex(sha256_bytes(payload))

    @property
    def counter(self) -> int:
        """rc3 outbound-counter surface. Maps to Bio-TOTP's
        ``send_seq``."""
        return self._bio.send_seq

    @property
    def last_recv_counter(self) -> int:
        """rc3 inbound-counter surface. Maps to Bio-TOTP's
        ``last_recv_seq``."""
        return self._bio.last_recv_seq

    def encrypt(self, plaintext: bytes) -> bytes:
        return self._bio.encrypt(plaintext)

    def decrypt(self, framed: bytes) -> bytes:
        return self._bio.decrypt(framed)


__all__ = [
    "COUNTER_BYTES",
    "ChainCipherError",
    "ChainFormatError",
    "ChainState",
    "CounterReplayError",
    "DIRECTION_IN",
    "DIRECTION_OUT",
    "DIRECTIONS",
    "FRAME_OVERHEAD_BYTES",
    "MAC_BYTES",
    "MacMismatchError",
    "STATE_BYTES",
    "decode_splice",
    "derive_key",
    "derive_state",
]
