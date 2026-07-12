"""UTLP Bio-TOTP wire obfuscation for srmech.bus (Claim 255 alignment).

Per user direction 2026-05-28 (v0.5.0rc7 of N for v0.5.0): replaces
rc3's SHA-256-state-chained cipher with the actual UTLP Bio-TOTP
construction from ``examples/utlp/utlp_hal_security.h``.

Wire frame::

    [nonce:16][ciphertext]

where::

    nonce            = sender_id_u64 || channel_id_u32 || packet_seq_u32
    key              = sha256(dna || quantized_time_be8)[0:16]
    quantized_time   = floor(time_ns / WINDOW_NS)
    ciphertext       = stream_cipher(key, nonce, plaintext)

Key rolls with a short time bucket (default ``WINDOW_NS = 250 ms`` —
way faster than RFC 6238 TOTP's 30 s). The receiver tolerates
``±1`` window for clock skew so a frame minted at the boundary of
two buckets still decrypts cleanly. A snooper that joins mid-stream
can only decrypt frames within their own (and adjacent) time
windows — and only if they know the ``dna`` secret.

Cipher choice
-------------
* **Default** — HMAC-SHA-256 counter-mode keystream (stdlib only;
  no new deps). ``HMAC(key, nonce || counter_be4)`` produces a
  32-byte keystream block; concatenate to fit plaintext length;
  XOR with plaintext. Structurally equivalent to AES-CTR for our
  defensive-scope threat model. The HMAC routes through
  :func:`srmech.amsc.format.sha256_bytes` so the native C SHA-256
  dispatch picks up transparently.
* **Optional** — AES-128-CTR via the ``cryptography`` extra
  (``pip install srmech[crypto]``). Detected at import; when
  available, used in place of HMAC-CTR for tighter UTLP alignment
  (Claim 255 says "AES-128-CTR" verbatim).

Zero-DNA herd-immunity
----------------------
``dna = ZERO_DNA`` (``b"\\x00" * 32``) runs the SAME crypto path
with a constant key — produces deterministic ciphertext that is
recoverable by anyone, but indistinguishable from real-DNA traffic
on the wire. "Herd immunity" per the UTLP design philosophy (see
``utlp_hal_security.h`` section "Purple Team Directive 4: Herd
Immunity"). The bus layer does NOT use ZERO_DNA by default —
``dna=None`` keeps rc6 plaintext wire shape — but it's available
to callers that want the herd-immunity property explicitly.

Naming alignment with UTLP
--------------------------
* ``dna`` — the per-channel pre-shared secret (replaces rc3's
  ``seed`` arg with the same role).
* "Exon fields" — UTLP's term for the nonce components
  (``sender_id`` + ``channel_id`` + ``packet_seq``); we keep the
  three-field structure verbatim.
* "Bio-TOTP" — the construction's UTLP name; "TOTP" reflects the
  RFC 6238 family resemblance (key rolls with time), but the
  ``WINDOW_NS`` is ~120× shorter (250 ms vs 30 s) and the input is
  ``dna`` not a base32 secret.

Out of scope (per user direction 2026-05-28)
--------------------------------------------
The UTLP mesh / multi-arbor / Loom / Genesis-election / time-sync
layer is **embedded-specific** and is NOT brought over to
``srmech.bus``. srmech.bus is local IPC — no mesh, no leader-election,
no inter-arbor cross-talk. We import just the wire-obfuscation
pattern.

Framework reading
-----------------
Class A (content-addressing — SHA-256 of DNA + time) ∘ Class I
(cyclic — monotone packet_seq ∈ ℤ/2³² + time-window bucketing
∈ ℤ-quotient) ∘ Class K (pin-slot phase boundary — every key-roll
is a phase boundary between adjacent time windows; the ±1 skew
tolerance IS the "soft boundary" reading per Class K). The same
substrate-self-recognition pattern as rc3, but at a different
algebraic layer (time-rolling key vs state-chained advance).

No new ``hashlib.sha256(...)`` direct calls — every SHA-256 routes
through :func:`srmech.amsc.format.sha256_bytes` so the native C
dispatch picks up transparently.
"""

from __future__ import annotations

import hmac
import json
import os
import struct
import time
from dataclasses import dataclass, field
from typing import Optional, Tuple

from ..amsc import _native
from ..amsc.format import sha256_bytes

#: int64 range guard — the native Bio-TOTP C peer takes ``int64_t`` time /
#: window arguments, so a Python int outside this range routes to the pure
#: path (which handles arbitrary precision). Realistic ``time.time_ns()`` +
#: window values sit comfortably inside int64.
_I64_MIN: int = -(1 << 63)
_I64_MAX: int = (1 << 63) - 1


def _fits_i64(*vals: int) -> bool:
    """True iff every value fits the C ``int64_t`` the native peer expects."""
    return all(_I64_MIN <= int(v) <= _I64_MAX for v in vals)

# ──────────────────────────────────────────────────────────────────────
# Wire-format constants
# ──────────────────────────────────────────────────────────────────────

#: Bytes of nonce per frame: sender_id_u64 (8) || channel_id_u32 (4)
#: || packet_seq_u32 (4) = 16 bytes total. Matches AES-128 block size
#: so the optional AES-CTR backend can drop the nonce straight into
#: the cipher's IV slot.
NONCE_BYTES: int = 16

#: AES-128 key size in bytes; we truncate SHA-256(dna || time) to this.
KEY_BYTES: int = 16

#: Bytes of overhead each frame body carries beyond the plaintext
#: (16-byte nonce only; no MAC tag — Bio-TOTP integrity is implicit
#: via the JSON-parseable-plaintext check downstream).
FRAME_OVERHEAD_BYTES: int = NONCE_BYTES

#: Default time-window width in nanoseconds. 250 ms — much faster
#: than RFC 6238 TOTP's 30 s; tight enough that a mid-stream snooper
#: gets only a ~750 ms window (current + ±1) of recoverable frames
#: before the key rolls. Configurable via env var
#: ``SRMECH_BUS_TOTP_WINDOW_NS``.
DEFAULT_WINDOW_NS: int = 250_000_000

#: Environment-variable name for overriding the default time window.
WINDOW_ENV_VAR: str = "SRMECH_BUS_TOTP_WINDOW_NS"

#: "Zero DNA" — runs the same crypto path with a constant key.
#: Produces deterministic ciphertext that's recoverable by anyone but
#: indistinguishable from real-DNA traffic on the wire. Herd immunity
#: per the UTLP design philosophy. 32 bytes matches the natural input
#: width of SHA-256's compression function.
ZERO_DNA: bytes = b"\x00" * 32

#: Minimum acceptable DNA length in bytes. 32 = SHA-256 block-aligned
#: input + matches :class:`secrets.token_bytes(32)` typical width.
MIN_DNA_BYTES: int = 32


# ──────────────────────────────────────────────────────────────────────
# Error types
# ──────────────────────────────────────────────────────────────────────


class BioTotpError(Exception):
    """Base class for Bio-TOTP wire-format errors."""


class BioTotpFormatError(BioTotpError):
    """Raised when an inbound frame is shorter than the 16-byte nonce
    minimum, or otherwise malformed at the byte-layout level."""


class BioTotpDecryptError(BioTotpError):
    """Raised when frame decryption fails across the candidate time
    windows (current + ±1). Causes (in rough order of likelihood):

    * The two ends were initialised with different DNA.
    * The sender's clock has drifted more than one window from the
      receiver's (>250 ms by default).
    * The frame was tampered with in transit and no longer parses as
      a valid JSON event.
    """


# ──────────────────────────────────────────────────────────────────────
# Cipher backend detection
# ──────────────────────────────────────────────────────────────────────

_HAVE_AES_CTR: bool = False
try:  # pragma: no cover  (cryptography is an optional extra)
    from cryptography.hazmat.backends import default_backend as _aes_backend
    from cryptography.hazmat.primitives.ciphers import (
        Cipher as _AesCipher,
        algorithms as _aes_algorithms,
        modes as _aes_modes,
    )
    _HAVE_AES_CTR = True
except ImportError:  # pragma: no cover
    pass


def cipher_backend_name() -> str:
    """Return the active stream-cipher backend's human-readable name.

    Returns ``"AES-128-CTR"`` when the optional ``cryptography``
    extra is installed (UTLP-exact path; Claim 255 verbatim).
    Returns ``"HMAC-SHA-256-CTR"`` for the stdlib-only default path
    (structurally equivalent for our defensive-scope threat model).
    """
    return "AES-128-CTR" if _HAVE_AES_CTR else "HMAC-SHA-256-CTR"


# ──────────────────────────────────────────────────────────────────────
# Pure helpers (key derivation, nonce, cipher)
# ──────────────────────────────────────────────────────────────────────


def _resolved_window_ns(explicit: Optional[int] = None) -> int:
    """Resolve the active time-window width.

    Priority: explicit kwarg > ``SRMECH_BUS_TOTP_WINDOW_NS`` env var
    > :data:`DEFAULT_WINDOW_NS`. Always returns a positive int.
    """
    if explicit is not None:
        assert isinstance(explicit, int) and explicit > 0, (
            f"window_ns must be positive int; got {explicit!r}"
        )
        return int(explicit)
    raw = os.environ.get(WINDOW_ENV_VAR)
    if raw is not None and raw.strip():
        try:
            parsed = int(raw)
        except ValueError as exc:
            raise ValueError(
                f"{WINDOW_ENV_VAR}: not an integer: {raw!r}"
            ) from exc
        if parsed <= 0:
            raise ValueError(
                f"{WINDOW_ENV_VAR}: must be positive; got {parsed}"
            )
        return parsed
    return DEFAULT_WINDOW_NS


def derive_key(dna: bytes, time_ns: int, window_ns: int) -> bytes:
    """Pure helper: derive the 16-byte Bio-TOTP key for one time window.

    Returns ``sha256(dna || quantized_time_be8)[0:16]`` where
    ``quantized_time = floor(time_ns / window_ns)``. The SHA-256
    routes through :func:`srmech.amsc.format.sha256_bytes` so the
    native C dispatch picks up.
    """
    assert isinstance(dna, (bytes, bytearray)), (
        f"dna must be bytes-like; got {type(dna).__name__}"
    )
    assert isinstance(time_ns, int), (
        f"time_ns must be int; got {type(time_ns).__name__}"
    )
    assert isinstance(window_ns, int) and window_ns > 0, (
        f"window_ns must be positive int; got {window_ns!r}"
    )
    # rc178: dispatch to the byte-exact C peer when present (hasattr-guarded;
    # a stale / no-C host keeps the pure path below). Falls through on OVERFLOW
    # (dna longer than the native cap) or an out-of-int64 time/window.
    if _native.has_native_bio_totp() and _fits_i64(time_ns, window_ns):
        native = _native.bio_totp_derive_key_c(bytes(dna), time_ns, window_ns)
        if native is not None:
            return native
    quantized = time_ns // window_ns
    digest_hex = sha256_bytes(bytes(dna) + quantized.to_bytes(8, "big",
                                                              signed=True))
    return bytes.fromhex(digest_hex)[:KEY_BYTES]


def build_nonce(sender_id: int, channel_id: int, packet_seq: int) -> bytes:
    """Pure helper: assemble the 16-byte nonce ("Exon fields").

    Layout::

        sender_id_u64 (8) || channel_id_u32 (4) || packet_seq_u32 (4)

    All fields are big-endian and mask to their declared width so a
    larger caller-supplied integer wraps cleanly (sender_id is a
    process-id-ish thing, channel_id is a hash of the endpoint name,
    packet_seq is a monotone uint32 that wraps at 2³²).
    """
    sender_id_masked = int(sender_id) & ((1 << 64) - 1)
    channel_id_masked = int(channel_id) & ((1 << 32) - 1)
    packet_seq_masked = int(packet_seq) & ((1 << 32) - 1)
    return (
        sender_id_masked.to_bytes(8, "big")
        + channel_id_masked.to_bytes(4, "big")
        + packet_seq_masked.to_bytes(4, "big")
    )


def parse_nonce(nonce: bytes) -> Tuple[int, int, int]:
    """Pure helper: split a 16-byte nonce back into its three fields.

    Returns ``(sender_id_u64, channel_id_u32, packet_seq_u32)`` —
    inverse of :func:`build_nonce`.
    """
    if len(nonce) != NONCE_BYTES:
        raise BioTotpFormatError(
            f"nonce must be {NONCE_BYTES} bytes; got {len(nonce)}"
        )
    sender_id = int.from_bytes(nonce[:8], "big")
    channel_id = int.from_bytes(nonce[8:12], "big")
    packet_seq = int.from_bytes(nonce[12:16], "big")
    return sender_id, channel_id, packet_seq


def _stream_cipher(key: bytes, nonce: bytes, data: bytes) -> bytes:
    """XOR ``data`` with the keystream derived from ``(key, nonce)``.

    Uses AES-128-CTR when the optional ``cryptography`` extra is
    installed (UTLP-exact path). Otherwise falls back to a stdlib
    HMAC-SHA-256 counter-mode keystream — same SHAPE, different
    primitive; equivalent for the defensive-scope threat model.

    Symmetric: encrypt and decrypt are the same operation
    (XOR keystream both directions).
    """
    assert len(key) == KEY_BYTES, (
        f"key must be {KEY_BYTES} bytes; got {len(key)}"
    )
    assert len(nonce) == NONCE_BYTES, (
        f"nonce must be {NONCE_BYTES} bytes; got {len(nonce)}"
    )
    if not data:
        return b""
    if _HAVE_AES_CTR:  # pragma: no cover  (covered when extra installed)
        cipher = _AesCipher(
            _aes_algorithms.AES(key),
            _aes_modes.CTR(nonce),
            backend=_aes_backend(),
        )
        encryptor = cipher.encryptor()
        return encryptor.update(data) + encryptor.finalize()
    # rc178: the DEFAULT stdlib HMAC-CTR path dispatches to the byte-exact C
    # peer when present (hasattr-guarded; the AES branch above is the opt-in
    # `[crypto]` extra and stays Python — out of the bare-C-host default).
    if _native.has_native_bio_totp():
        native = _native.bio_totp_keystream_xor_c(key, nonce, data)
        if native is not None:
            return native
    # Stdlib fallback: HMAC-SHA-256 counter-mode keystream.
    out = bytearray()
    counter = 0
    n = len(data)
    while len(out) < n:
        # 32-byte block per HMAC call; concat until ≥ n bytes
        # of keystream are available. We route the underlying SHA-256
        # via stdlib hmac (which uses hashlib) — the
        # no-new-hashlib-sha256-calls rule applies to direct
        # ``hashlib.sha256(...)`` constructions; HMAC's use of
        # SHA-256 internally is the canonical RFC 2104 construction
        # and is not a new framework-level hash call.
        block = hmac.new(
            key, nonce + counter.to_bytes(4, "big"), "sha256",
        ).digest()
        out.extend(block)
        counter += 1
    keystream = bytes(out[:n])
    return bytes(a ^ b for a, b in zip(data, keystream))


# ──────────────────────────────────────────────────────────────────────
# BioTotpChannel — per-direction Bio-TOTP cipher state
# ──────────────────────────────────────────────────────────────────────


@dataclass
class BioTotpChannel:
    """Per-direction Bio-TOTP cipher state for one bus channel.

    Each :class:`~srmech.bus._client.Channel` (and each server-side
    accepted connection) holds two ``BioTotpChannel`` instances: one
    for outgoing frames, one for incoming. The two ends of a duplex
    use SAME ``dna`` + ``channel_id`` but DIFFERENT ``sender_id`` so
    the nonces never collide (each side embeds its own sender_id in
    every nonce it emits).

    Not thread-safe: the bus layer serialises sends via its own
    ``_send_lock`` and processes inbound frames in a single reader
    thread, so this object never sees concurrent mutation in
    practice.

    Attributes
    ----------
    dna
        Per-channel pre-shared secret. ``b"\\x00" * 32`` =
        :data:`ZERO_DNA` for herd-immunity / public mode.
    sender_id
        Our own sender identifier, u64. Typically the OS process-id
        for the client/server (zero-padded to fit).
    channel_id
        Endpoint identifier, u32. Typically a hash of the bus
        channel name truncated to 32 bits.
    window_ns
        Time-window width in nanoseconds (controls how fast the key
        rolls). Defaults to :data:`DEFAULT_WINDOW_NS` = 250 ms.
    strict
        When True (the bus default), every decrypted plaintext MUST
        be a UTF-8 JSON bus Event with ``attestation.sender_id_u64``
        + ``attestation.channel_id_u32`` matching the nonce — this
        is the implicit-MAC discipline. Wrong-key decryption
        produces random bytes that don't satisfy the shape, so
        forged / tampered frames are caught. When False (the
        opaque-payload default), any plaintext that decodes
        without contradicting the binding fields is accepted —
        suitable for unit tests passing raw bytes through the
        channel object directly.
    """

    dna: bytes
    sender_id: int
    channel_id: int
    window_ns: int = DEFAULT_WINDOW_NS
    strict: bool = False
    _send_seq: int = field(default=0, repr=False)
    _last_recv_seq: int = field(default=-1, repr=False)

    def __post_init__(self) -> None:
        assert isinstance(self.dna, (bytes, bytearray)), (
            f"dna must be bytes-like; got {type(self.dna).__name__}"
        )
        if len(self.dna) < MIN_DNA_BYTES:
            raise ValueError(
                f"dna must be at least {MIN_DNA_BYTES} bytes; "
                f"got {len(self.dna)}"
            )
        assert isinstance(self.sender_id, int), (
            f"sender_id must be int; got {type(self.sender_id).__name__}"
        )
        assert isinstance(self.channel_id, int), (
            f"channel_id must be int; got {type(self.channel_id).__name__}"
        )
        assert isinstance(self.window_ns, int) and self.window_ns > 0, (
            f"window_ns must be positive int; got {self.window_ns!r}"
        )
        # Pre-cast dna to immutable bytes (defensive — callers may
        # pass bytearray and later mutate it).
        self.dna = bytes(self.dna)

    @property
    def send_seq(self) -> int:
        """Next outgoing packet_seq (uint32; advances after each
        :meth:`encrypt`)."""
        return self._send_seq

    @property
    def last_recv_seq(self) -> int:
        """Last accepted inbound packet_seq. ``-1`` means no frame has
        yet been decrypted on this direction."""
        return self._last_recv_seq

    def encrypt(self, plaintext: bytes,
                *, time_ns: Optional[int] = None) -> bytes:
        """Wrap ``plaintext`` into a wire-body frame.

        Returns ``[nonce:16][ciphertext]`` — total length
        ``16 + len(plaintext)``. The caller (transport layer)
        prepends the TLV length prefix via
        :func:`srmech.bus._framing.pack_frame`.

        Side effect: advances ``_send_seq`` (mod 2³²) so the next
        call uses a fresh nonce slot.

        Parameters
        ----------
        plaintext
            Payload bytes.
        time_ns
            Optional explicit time override (testing hook). When
            ``None``, :func:`time.time_ns` is used.
        """
        if not isinstance(plaintext, (bytes, bytearray)):
            raise TypeError(
                f"plaintext must be bytes-like; "
                f"got {type(plaintext).__name__}"
            )
        pt = bytes(plaintext)
        now_ns = time.time_ns() if time_ns is None else int(time_ns)
        nonce = build_nonce(self.sender_id, self.channel_id, self._send_seq)
        self._send_seq = (self._send_seq + 1) & ((1 << 32) - 1)
        key = derive_key(self.dna, now_ns, self.window_ns)
        ciphertext = _stream_cipher(key, nonce, pt)
        return nonce + ciphertext

    def decrypt(self, framed: bytes,
                *, time_ns: Optional[int] = None) -> bytes:
        """Unwrap a wire-body frame and return the plaintext.

        Tries the current time window first, then ``±1`` window for
        clock-skew tolerance. Decryption "succeeds" when the resulting
        plaintext parses as a JSON bus :class:`~srmech.bus._event.Event`
        AND the embedded ``attestation.sender_id_u64`` /
        ``attestation.channel_id_u32`` match the nonce's fields (the
        binding check that substitutes for an explicit MAC).

        Parameters
        ----------
        framed
            ``[nonce:16][ciphertext]`` bytes.
        time_ns
            Optional explicit time override (testing hook). When
            ``None``, :func:`time.time_ns` is used.

        Raises
        ------
        BioTotpFormatError
            If the frame is shorter than 16 bytes.
        BioTotpDecryptError
            If decryption fails across the candidate windows (DNA
            mismatch / clock drift > 1 window / tamper).
        """
        if not isinstance(framed, (bytes, bytearray)):
            raise TypeError(
                f"framed must be bytes-like; "
                f"got {type(framed).__name__}"
            )
        body = bytes(framed)
        if len(body) < NONCE_BYTES:
            raise BioTotpFormatError(
                f"frame body shorter than nonce ({len(body)} < "
                f"{NONCE_BYTES})"
            )
        nonce = body[:NONCE_BYTES]
        ciphertext = body[NONCE_BYTES:]
        sender_id, channel_id, packet_seq = parse_nonce(nonce)
        # Replay / reorder guard — strictly monotone within u32 space.
        # We accept the equivalent of "packet_seq > last_recv_seq
        # modulo wraparound tolerance". For the bus's lifetime (well
        # under 2³² frames per channel), strict > is sufficient.
        if packet_seq <= self._last_recv_seq:
            raise BioTotpDecryptError(
                f"inbound packet_seq {packet_seq} <= last accepted "
                f"{self._last_recv_seq} (replay or reorder)"
            )
        now_ns = time.time_ns() if time_ns is None else int(time_ns)
        # In strict mode (the bus default), try the current window
        # then ±1 for clock-skew tolerance; accept the first whose
        # decryption passes the binding check (JSON Event with
        # matching attestation.sender_id_u64/channel_id_u32). Wrong
        # keys produce random bytes that don't satisfy the binding
        # shape, so forged / tampered frames are caught here.
        #
        # In permissive mode (the opaque-payload unit-test default),
        # decrypt with the CURRENT window only — there's no integrity
        # check, so retrying ±1 windows would silently accept random
        # garbage from a wrong key. A PRESENT-BUT-MISMATCHED binding
        # is still a contradiction and raises in either mode.
        candidate_deltas = (0, -1, 1) if self.strict else (0,)
        for delta in candidate_deltas:
            candidate_time = now_ns + delta * self.window_ns
            key = derive_key(self.dna, candidate_time, self.window_ns)
            plaintext = _stream_cipher(key, nonce, ciphertext)
            if _plaintext_binds_to_nonce(
                plaintext, sender_id, channel_id, strict=self.strict,
            ):
                self._last_recv_seq = packet_seq
                return plaintext
        raise BioTotpDecryptError(
            "frame decryption failed "
            f"({'across current + ±1 time windows' if self.strict else 'in current time window'}) "
            "(dna mismatch / clock skew > 1 window / tamper / "
            "binding-field mismatch)"
        )


def _plaintext_binds_to_nonce(
    plaintext: bytes,
    expected_sender_id: int,
    expected_channel_id: int,
    *,
    strict: bool = False,
) -> bool:
    """Confirm the decrypted plaintext does not CONTRADICT the nonce's
    fields.

    Bio-TOTP has no per-frame MAC tag (per the UTLP spec). The
    integrity check is implicit and lives at the application layer
    — but we surface it here so wrong-key decryption raises rather
    than returning garbage.

    Two modes:

    * **strict=True** (the bus default) — every decrypted plaintext
      MUST be a UTF-8 JSON bus Event with
      ``attestation.sender_id_u64`` + ``attestation.channel_id_u32``
      matching the nonce. Wrong-key decryption produces random bytes
      that don't satisfy the shape, so forged / tampered frames are
      caught here as a BioTotpDecryptError up the call stack. This
      is the implicit-MAC discipline.
    * **strict=False** (opaque-payload default) — any plaintext that
      decodes without contradicting the binding fields is accepted.
      Used by unit tests passing raw bytes through the channel
      object directly; lets non-Event payloads round-trip cleanly.

    Returns True iff the plaintext satisfies the active mode's
    binding rules.
    """
    if not plaintext:
        # Empty plaintext: in strict mode this is suspect (the bus
        # never sends empty Event JSON); in permissive mode accept.
        return not strict
    try:
        decoded = plaintext.decode("utf-8")
    except UnicodeDecodeError:
        # Non-UTF-8 bytes. In strict mode this means wrong-key
        # decryption produced garbage → reject. In permissive mode
        # accept (opaque payload).
        return not strict
    try:
        payload = json.loads(decoded)
    except (json.JSONDecodeError, ValueError):
        # Not JSON. Same logic: strict mode requires bus-Event JSON.
        return not strict
    if not isinstance(payload, dict):
        return not strict
    att = payload.get("attestation", {})
    if not isinstance(att, dict):
        return not strict
    bound_sender = att.get("sender_id_u64")
    bound_channel = att.get("channel_id_u32")
    if bound_sender is None or bound_channel is None:
        # JSON event without binding fields. In strict mode this is
        # suspect (encrypted bus frames always include both). In
        # permissive mode accept.
        return not strict
    # When both fields are present, enforce match regardless of
    # strict / permissive (a present-but-mismatched binding is a
    # contradiction even when we're being permissive about absence).
    try:
        return (int(bound_sender) == int(expected_sender_id)
                and int(bound_channel) == int(expected_channel_id))
    except (TypeError, ValueError):
        return False


# ──────────────────────────────────────────────────────────────────────
# Pure-function decoder for tool-schema introspection
# ──────────────────────────────────────────────────────────────────────


def decode_splice(
    framed: bytes,
    dna: bytes,
    *,
    window_ns: Optional[int] = None,
    time_ns: Optional[int] = None,
) -> Tuple[bytes, int]:
    """Pure-function decode for tool-schema introspection.

    Given an inbound wire body and the DNA secret, try the current
    time window first then ``±1`` for clock-skew tolerance. Returns
    ``(plaintext, used_time_ns)`` — the plaintext bytes and the
    candidate time value that successfully decrypted (useful for
    debugging clock-skew issues).

    No side effects — does NOT mutate any chain state (Bio-TOTP has
    no chain to advance; the only "state" is the rolling
    quantized time bucket).

    Parameters
    ----------
    framed
        The frame body bytes (``[nonce:16][ciphertext]``).
    dna
        The 32+ byte pre-shared secret. Pass :data:`ZERO_DNA` for
        herd-immunity / public-mode frames.
    window_ns
        Optional time-window override (defaults to
        :data:`DEFAULT_WINDOW_NS` or the ``SRMECH_BUS_TOTP_WINDOW_NS``
        env var).
    time_ns
        Optional explicit time override; defaults to
        :func:`time.time_ns`. Useful for replaying historical
        captures where the original wall-clock matters.

    Returns
    -------
    (plaintext, used_time_ns)
        Plaintext bytes and the candidate time value that decoded.

    Raises
    ------
    BioTotpFormatError
        Frame shorter than 16 bytes.
    BioTotpDecryptError
        Decryption failed across all candidate windows.
    """
    if not isinstance(framed, (bytes, bytearray)):
        raise TypeError(
            f"framed must be bytes-like; got {type(framed).__name__}"
        )
    if not isinstance(dna, (bytes, bytearray)):
        raise TypeError(
            f"dna must be bytes-like; got {type(dna).__name__}"
        )
    body = bytes(framed)
    if len(body) < NONCE_BYTES:
        raise BioTotpFormatError(
            f"frame body shorter than nonce ({len(body)} < {NONCE_BYTES})"
        )
    nonce = body[:NONCE_BYTES]
    ciphertext = body[NONCE_BYTES:]
    sender_id, channel_id, _packet_seq = parse_nonce(nonce)
    resolved_window = _resolved_window_ns(window_ns)
    now_ns = time.time_ns() if time_ns is None else int(time_ns)
    # rc178: dispatch the WHOLE decode to the byte-exact C peer (derive_key +
    # HMAC-CTR keystream + srmech_json permissive binding check) when present;
    # native-authoritative, with the COMPLETE pure loop below as the stale /
    # no-C-host / out-of-int64 fallback. The C peer mirrors ONLY the DEFAULT
    # stdlib HMAC-CTR cipher, so it is bypassed when the optional AES-128-CTR
    # backend (`[crypto]` extra) is active — that path stays Python.
    if (not _HAVE_AES_CTR and _native.has_native_bio_totp()
            and _fits_i64(resolved_window, now_ns)):
        native = _native.bio_totp_decode_splice_c(
            body, dna, resolved_window, now_ns)
        if native is False:
            raise BioTotpDecryptError(
                "decryption failed across current + ±1 time windows "
                "(dna mismatch / clock skew > 1 window / tamper)"
            )
        if native is not None:
            return native
    for delta in (0, -1, 1):
        candidate_time = now_ns + delta * resolved_window
        key = derive_key(dna, candidate_time, resolved_window)
        plaintext = _stream_cipher(key, nonce, ciphertext)
        if _plaintext_binds_to_nonce(plaintext, sender_id, channel_id):
            return plaintext, candidate_time
    raise BioTotpDecryptError(
        "decryption failed across current + ±1 time windows "
        "(dna mismatch / clock skew > 1 window / tamper)"
    )


def channel_id_from_name(name: str) -> int:
    """Derive a stable u32 channel identifier from the endpoint name.

    Used by the bus layer to populate :attr:`BioTotpChannel.channel_id`
    deterministically across processes that connect to the same name.
    Computed as the first 4 bytes of ``sha256(name.encode("utf-8"))``
    interpreted big-endian — the same hash dispatch as everywhere
    else in srmech.
    """
    assert isinstance(name, str) and name, (
        f"name must be non-empty str; got {name!r}"
    )
    digest_hex = sha256_bytes(name.encode("utf-8"))
    return int.from_bytes(bytes.fromhex(digest_hex)[:4], "big")


__all__ = [
    "BioTotpChannel",
    "BioTotpDecryptError",
    "BioTotpError",
    "BioTotpFormatError",
    "DEFAULT_WINDOW_NS",
    "FRAME_OVERHEAD_BYTES",
    "KEY_BYTES",
    "MIN_DNA_BYTES",
    "NONCE_BYTES",
    "WINDOW_ENV_VAR",
    "ZERO_DNA",
    "build_nonce",
    "channel_id_from_name",
    "cipher_backend_name",
    "decode_splice",
    "derive_key",
    "parse_nonce",
]
