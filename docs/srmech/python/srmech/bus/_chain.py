"""State-chained wire format ("biological TOTP-like") for srmech.bus.

Per user direction 2026-05-28 (rc3 of N for v0.5.0): each frame N's
encoding depends on state_{N-1}; the receiver must walk the chain
from the seed to decode. Same-user-defensive forward-secrecy: a third
process that didn't initiate the channel cannot read mid-stream
(it has neither the seed nor the chain-state).

Cipher (stream cipher with chain advance + per-frame MAC):

    state_0     = sha256(seed || ":" || channel_id || ":" || direction)
    keystream_N = sha256(state_N || "ks" || counter_N_be8)   # 32 bytes
                  (repeat-truncate for plaintext lengths != 32)
    ciphertext_N = plaintext_N XOR keystream_N[:len(plaintext_N)]
    state_{N+1} = sha256(state_N || "st" || ciphertext_N)
    mac_N       = hmac_sha256(state_N || "mac", ciphertext_N || counter_N_be8)[:16]

Frame body layout (TLV length-prefix already supplied by _framing.py):

    [16-byte mac][8-byte counter_BE][ciphertext]

Decoder discipline:

    1. Read mac + counter + ciphertext from frame body.
    2. Verify counter > last_counter (replay protection — strict GT).
    3. Recompute the expected MAC against the held state; reject on
       mismatch.
    4. Compute keystream from current state + counter, XOR to
       plaintext.
    5. Advance state with the ciphertext + counter (so both sides
       walk identical chains).

Replay protection: monotone uint64 counter (wraps at 2^64 — practical
infinity for any bus channel's lifetime). Out-of-order delivery is
treated as tampering and rejected (req/rep over TCP / UDS / named
pipe is naturally ordered).

Framework reading: this is Class A (content-addressing — SHA-256
keystream + state derivation) ∘ Class I (cyclic — monotone counter
addition mod 2^64) ∘ Class K (pin-slot phase boundary — every frame
is a chain-advance event, the boundary between state_N and
state_{N+1}). Substrate-self-recognition is extended to the frame
chain: each frame's plaintext is recoverable only by an observer
that has been participating in the chain since state_0.

Threat model
------------
DEFENSIVE against same-user processes that did not initiate the
channel. NOT designed against an active local attacker who can read
the seed at rest (the discovery-file path is 0o600 but no kernel
isolation), nor against active MITM (no DH key exchange). If those
threats matter, see the v0.5.x / v0.6.0 roadmap for the AEAD + DH
key-establishment story.

Public API
----------

* :class:`ChainState` — per-direction cipher state. Each Channel
  holds two: outgoing + incoming. Use :meth:`encrypt` to wrap a
  plaintext into the wire body shape; :meth:`decrypt` to unwrap an
  inbound wire body.
* :func:`derive_state` — pure helper: produce ``state_0`` from
  ``seed`` + ``channel_id`` + ``direction`` byte.
* :func:`decode_splice` — inspectable pure-function decoder
  registered as a :class:`srmech.amsc.tool_schema.ToolEntry`. Takes
  a framed body + the matching held state + counter; returns
  ``(plaintext, new_state, new_counter)``. Suitable for LLM / agent
  introspection of mid-stream frames given the chain state at a
  point in time.

No new ``hashlib.sha256(...)`` direct calls — every SHA-256 routes
through :func:`srmech.amsc.format.sha256_bytes` so the native C
dispatch picks up transparently.
"""

from __future__ import annotations

import hmac
import struct
from typing import Tuple

from ..amsc.format import sha256_bytes

# ──────────────────────────────────────────────────────────────────────
# Wire-format constants
# ──────────────────────────────────────────────────────────────────────

#: Bytes of state used as the cipher carrier (SHA-256 = 32).
STATE_BYTES: int = 32

#: Bytes of the per-frame HMAC tag (truncated SHA-256 = 16 = 128 bits).
MAC_BYTES: int = 16

#: Bytes of the per-frame monotone counter (uint64 big-endian).
COUNTER_BYTES: int = 8

#: Bytes of overhead each frame body carries beyond the plaintext
#: (16-byte mac + 8-byte counter).
FRAME_OVERHEAD_BYTES: int = MAC_BYTES + COUNTER_BYTES

#: Direction tag — outgoing side.
DIRECTION_OUT: str = "out"

#: Direction tag — incoming side.
DIRECTION_IN: str = "in"

#: Valid direction tags. The two ends of a channel use OPPOSITE
#: tags so the keystreams never collide: client.send_state =
#: ``"out"`` matches server.recv_state = ``"out"``; client.recv_state
#: = ``"in"`` matches server.send_state = ``"in"``.
DIRECTIONS: frozenset = frozenset({DIRECTION_OUT, DIRECTION_IN})


# ──────────────────────────────────────────────────────────────────────
# Error types
# ──────────────────────────────────────────────────────────────────────


class ChainCipherError(Exception):
    """Base class for state-chained wire-format errors."""


class MacMismatchError(ChainCipherError):
    """Raised when the per-frame HMAC tag does not match.

    Causes (in rough order of likelihood):

    * The two ends were initialised with different seeds.
    * The two ends ran out-of-step (a frame was dropped between them).
    * The frame was tampered with in transit.
    """


class CounterReplayError(ChainCipherError):
    """Raised when an inbound frame's counter is not strictly greater
    than the last accepted counter on this direction (replay or
    reorder)."""


class ChainFormatError(ChainCipherError):
    """Raised when an inbound frame body is shorter than the minimum
    overhead (16-byte MAC + 8-byte counter)."""


# ──────────────────────────────────────────────────────────────────────
# Hash helpers
# ──────────────────────────────────────────────────────────────────────


def _sha256_raw(data: bytes) -> bytes:
    """SHA-256 over ``data`` returning raw 32 bytes.

    Routes through :func:`srmech.amsc.format.sha256_bytes` (which
    returns hex) and unhexes — keeps the JPL-discipline rule (no new
    direct ``hashlib.sha256`` calls) while exposing the raw-bytes
    surface the cipher needs.
    """
    return bytes.fromhex(sha256_bytes(data))


def _hmac_sha256(key: bytes, msg: bytes) -> bytes:
    """HMAC-SHA-256 with the standard RFC 2104 construction.

    Implemented in terms of :func:`_sha256_raw` (no direct
    ``hashlib.sha256`` calls) so the native C SHA-256 dispatch picks
    up transparently. The stdlib :mod:`hmac` module only supplies the
    XOR pad framework; the underlying hash primitive routes through
    srmech's discipline-compliant surface.
    """
    block_size = 64  # SHA-256 block size (bytes)
    if len(key) > block_size:
        key = _sha256_raw(key)
    # Pad key with zeros up to block size.
    key = key + b"\x00" * (block_size - len(key))
    o_key_pad = bytes(b ^ 0x5C for b in key)
    i_key_pad = bytes(b ^ 0x36 for b in key)
    inner = _sha256_raw(i_key_pad + msg)
    return _sha256_raw(o_key_pad + inner)


# Cross-check: stdlib hmac.compare_digest gives constant-time
# comparison for MAC verification. Bind it as a module-level helper
# so the receive path uses constant-time comparison (defensive
# against timing-oracle MAC attacks — defensive scope only).
_constant_time_eq = hmac.compare_digest


# ──────────────────────────────────────────────────────────────────────
# Keystream + state derivation
# ──────────────────────────────────────────────────────────────────────


def _counter_be8(counter: int) -> bytes:
    """Encode a uint64 counter as 8 big-endian bytes."""
    assert 0 <= counter < (1 << 64), (
        f"counter must fit in uint64; got {counter}"
    )
    return struct.pack(">Q", counter)


def _keystream(state: bytes, counter: int, n: int) -> bytes:
    """Produce ``n`` keystream bytes for the given state + counter.

    Construction: repeated SHA-256 over
    ``state || "ks" || counter_be8 || block_index_be4``. The
    block_index field defends against keystream reuse for plaintexts
    longer than 32 bytes; for the common case (n <= 32) only one
    block is emitted.
    """
    assert len(state) == STATE_BYTES, (
        f"state must be {STATE_BYTES} bytes; got {len(state)}"
    )
    assert n >= 0, f"keystream length must be non-negative; got {n}"
    if n == 0:
        return b""
    counter_field = _counter_be8(counter)
    out = bytearray()
    block_index = 0
    while len(out) < n:
        block = _sha256_raw(
            state + b"ks" + counter_field + struct.pack(">I", block_index)
        )
        out.extend(block)
        block_index += 1
    return bytes(out[:n])


def derive_state(
    seed: bytes,
    channel_id: bytes,
    direction: str = DIRECTION_OUT,
) -> bytes:
    """Compute the initial ``state_0`` for a chain.

    ``seed`` is the pre-shared cipher seed (caller-provided; min 1
    byte but 32 bytes recommended). ``channel_id`` identifies the
    endpoint by name (typically the bus channel name encoded as
    UTF-8). ``direction`` is ``"out"`` or ``"in"`` so the two ends
    derive disjoint keystreams for the two halves of the duplex.

    Returns the 32-byte ``state_0``.
    """
    assert isinstance(seed, (bytes, bytearray)), (
        f"seed must be bytes-like; got {type(seed).__name__}"
    )
    assert isinstance(channel_id, (bytes, bytearray)), (
        f"channel_id must be bytes-like; got {type(channel_id).__name__}"
    )
    if direction not in DIRECTIONS:
        raise ValueError(
            f"direction must be one of {sorted(DIRECTIONS)!r}; got {direction!r}"
        )
    if len(seed) == 0:
        raise ValueError("seed must be non-empty")
    direction_bytes = direction.encode("ascii")
    return _sha256_raw(
        bytes(seed) + b":" + bytes(channel_id) + b":" + direction_bytes
    )


def _advance_state(state: bytes, ciphertext: bytes) -> bytes:
    """Compute ``state_{N+1}`` from ``state_N`` + the ciphertext."""
    assert len(state) == STATE_BYTES, (
        f"state must be {STATE_BYTES} bytes; got {len(state)}"
    )
    return _sha256_raw(state + b"st" + ciphertext)


def _compute_mac(state: bytes, ciphertext: bytes, counter: int) -> bytes:
    """HMAC the (ciphertext || counter) under a per-state MAC key.

    The MAC key is ``state || "mac"`` — domain-separated from the
    keystream derivation (``"ks"``) and the state-advance (``"st"``).
    Returns 16 truncated bytes.
    """
    assert len(state) == STATE_BYTES, (
        f"state must be {STATE_BYTES} bytes; got {len(state)}"
    )
    mac_key = state + b"mac"
    full = _hmac_sha256(mac_key, ciphertext + _counter_be8(counter))
    return full[:MAC_BYTES]


# ──────────────────────────────────────────────────────────────────────
# ChainState — per-direction cipher state
# ──────────────────────────────────────────────────────────────────────


class ChainState:
    """Per-direction cipher state for one channel.

    Each :class:`~srmech.bus._client.Channel` (and each server-side
    accepted connection) holds two ChainState instances: one for
    outgoing frames, one for incoming. They share the same seed +
    channel_id but use opposite direction tags so the two halves of
    the duplex have disjoint keystreams.

    Not thread-safe: the bus layer serialises sends via its own
    ``_send_lock`` and processes inbound frames in a single reader
    thread, so this object never sees concurrent mutation in
    practice.
    """

    __slots__ = ("_state", "_counter", "_last_recv_counter", "_direction")

    def __init__(
        self,
        seed: bytes,
        channel_id: bytes,
        direction: str,
    ) -> None:
        if direction not in DIRECTIONS:
            raise ValueError(
                f"direction must be one of {sorted(DIRECTIONS)!r}; "
                f"got {direction!r}"
            )
        self._state: bytes = derive_state(seed, channel_id, direction)
        # Outgoing-side counter starts at 0 (first frame uses counter=0).
        self._counter: int = 0
        # Incoming side tracks the last accepted counter so the next
        # frame must have a STRICTLY greater counter. Start at -1 so
        # counter=0 (the first ever frame) passes the > check.
        self._last_recv_counter: int = -1
        self._direction: str = direction

    @property
    def direction(self) -> str:
        return self._direction

    @property
    def state(self) -> bytes:
        """Current 32-byte chain state (the state that the NEXT
        operation will use). Read-only snapshot."""
        return self._state

    @property
    def counter(self) -> int:
        """Send-side: counter for the NEXT outgoing frame.
        Receive-side: not meaningful (use last_recv_counter instead)."""
        return self._counter

    @property
    def last_recv_counter(self) -> int:
        """Last accepted inbound counter on this direction. -1 means
        no inbound frame has yet been accepted."""
        return self._last_recv_counter

    def encrypt(self, plaintext: bytes) -> bytes:
        """Wrap ``plaintext`` into a wire-body frame.

        Returns a bytes object of length
        ``MAC_BYTES + COUNTER_BYTES + len(plaintext)`` with layout
        ``[mac][counter_be][ciphertext]``. The caller (transport
        layer) prepends the TLV length prefix via
        :func:`srmech.bus._framing.pack_frame`.

        Side effect: advances the chain (state ← state_{N+1};
        counter ← counter + 1) so the next call uses fresh material.
        """
        if not isinstance(plaintext, (bytes, bytearray)):
            raise TypeError(
                f"plaintext must be bytes-like; got {type(plaintext).__name__}"
            )
        pt = bytes(plaintext)
        ks = _keystream(self._state, self._counter, len(pt))
        ciphertext = bytes(p ^ k for p, k in zip(pt, ks))
        mac = _compute_mac(self._state, ciphertext, self._counter)
        body = mac + _counter_be8(self._counter) + ciphertext
        # Advance the chain.
        self._state = _advance_state(self._state, ciphertext)
        # uint64 wraparound after 2^64 frames is allowed but
        # practically unreachable for any bus channel's lifetime.
        self._counter = (self._counter + 1) & ((1 << 64) - 1)
        return body

    def decrypt(self, framed: bytes) -> bytes:
        """Unwrap a wire-body frame and return the plaintext.

        Raises :class:`ChainFormatError` if the frame body is too
        short to contain the mac + counter header.
        Raises :class:`CounterReplayError` if the counter is not
        strictly greater than the last accepted counter on this
        direction (replay / reorder / duplication).
        Raises :class:`MacMismatchError` if the per-frame MAC does
        not verify (tamper / seed-mismatch / chain de-sync).
        """
        if not isinstance(framed, (bytes, bytearray)):
            raise TypeError(
                f"framed must be bytes-like; got {type(framed).__name__}"
            )
        body = bytes(framed)
        if len(body) < FRAME_OVERHEAD_BYTES:
            raise ChainFormatError(
                f"frame body shorter than overhead "
                f"({len(body)} < {FRAME_OVERHEAD_BYTES})"
            )
        mac_recv = body[:MAC_BYTES]
        counter_field = body[MAC_BYTES:MAC_BYTES + COUNTER_BYTES]
        ciphertext = body[MAC_BYTES + COUNTER_BYTES:]
        (counter,) = struct.unpack(">Q", counter_field)
        # Replay / reorder guard — strictly monotone.
        if counter <= self._last_recv_counter:
            raise CounterReplayError(
                f"inbound counter {counter} <= last accepted "
                f"{self._last_recv_counter}"
            )
        # MAC verification (constant-time compare).
        mac_expected = _compute_mac(self._state, ciphertext, counter)
        if not _constant_time_eq(mac_recv, mac_expected):
            raise MacMismatchError(
                "per-frame HMAC mismatch (seed mismatch / chain "
                "de-sync / tamper)"
            )
        # Decrypt + advance.
        ks = _keystream(self._state, counter, len(ciphertext))
        plaintext = bytes(c ^ k for c, k in zip(ciphertext, ks))
        self._state = _advance_state(self._state, ciphertext)
        self._last_recv_counter = counter
        return plaintext


# ──────────────────────────────────────────────────────────────────────
# Inspectable pure-function decoder (tool-schema surface)
# ──────────────────────────────────────────────────────────────────────


def decode_splice(
    framed: bytes,
    state: bytes,
    counter: int,
) -> Tuple[bytes, bytes, int]:
    """Pure-function decoder for one chain frame.

    Given an inbound wire body, the held chain state, and the
    last-accepted counter, returns
    ``(plaintext, new_state, new_counter)``. Suitable for LLM /
    agent introspection of mid-stream frames given the chain state
    at a point in time.

    No side effects — does NOT mutate any global state. The caller
    is responsible for holding the returned ``new_state`` +
    ``new_counter`` for the next call.

    Parameters
    ----------
    framed
        The frame body bytes (``[mac][counter_be][ciphertext]``).
    state
        The 32-byte chain state held by the caller (the state the
        sender used to generate this frame).
    counter
        Last-accepted counter on this direction (the next frame's
        counter must be strictly greater). Pass ``-1`` for the very
        first frame in a chain.

    Returns
    -------
    (plaintext, new_state, new_counter)
        Tuple of the decoded plaintext, the next chain state, and
        the just-accepted counter (use as the ``counter`` input for
        the next call).

    Raises
    ------
    ChainFormatError, CounterReplayError, MacMismatchError
        See :meth:`ChainState.decrypt`.
    """
    if not isinstance(framed, (bytes, bytearray)):
        raise TypeError(
            f"framed must be bytes-like; got {type(framed).__name__}"
        )
    if not isinstance(state, (bytes, bytearray)):
        raise TypeError(
            f"state must be bytes-like; got {type(state).__name__}"
        )
    if len(state) != STATE_BYTES:
        raise ValueError(
            f"state must be {STATE_BYTES} bytes; got {len(state)}"
        )
    if not isinstance(counter, int):
        raise TypeError(
            f"counter must be int; got {type(counter).__name__}"
        )
    body = bytes(framed)
    if len(body) < FRAME_OVERHEAD_BYTES:
        raise ChainFormatError(
            f"frame body shorter than overhead "
            f"({len(body)} < {FRAME_OVERHEAD_BYTES})"
        )
    mac_recv = body[:MAC_BYTES]
    counter_field = body[MAC_BYTES:MAC_BYTES + COUNTER_BYTES]
    ciphertext = body[MAC_BYTES + COUNTER_BYTES:]
    (frame_counter,) = struct.unpack(">Q", counter_field)
    if frame_counter <= counter:
        raise CounterReplayError(
            f"frame counter {frame_counter} <= last accepted {counter}"
        )
    state_bytes = bytes(state)
    mac_expected = _compute_mac(state_bytes, ciphertext, frame_counter)
    if not _constant_time_eq(mac_recv, mac_expected):
        raise MacMismatchError(
            "per-frame HMAC mismatch (seed mismatch / chain de-sync / tamper)"
        )
    ks = _keystream(state_bytes, frame_counter, len(ciphertext))
    plaintext = bytes(c ^ k for c, k in zip(ciphertext, ks))
    new_state = _advance_state(state_bytes, ciphertext)
    return plaintext, new_state, frame_counter


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
    "derive_state",
]
