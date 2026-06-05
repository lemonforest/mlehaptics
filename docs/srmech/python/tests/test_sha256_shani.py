"""v0.7.0rc18 — SHA-NI single-stream SHA-256 parity (F292 graft #3).

``srmech.amsc.format.sha256_bytes`` keeps returning the 64-char lowercase
hex digest, byte-identical to ``hashlib.sha256(d).hexdigest()`` — but now,
when the rc18 ``srmech_sha256_shani`` symbol is present, it dispatches
through the SHA-NI single-stream peer. On hosts that carry the Intel SHA
Extensions that runs the SHA-NI rnds2/msg1/msg2 kernel; on hosts without it
(dev + most CI), the symbol runs the SELF-CONTAINED SCALAR PATH inside the C
call, so every dispatch arm is bit-exact.

Coverage discipline (the user's "build SHA-NI in the GH runner, don't park
it" ask):
  * The SCALAR oracle is pinned on EVERY host (SRMECH_SHANI_FORCE_TIER=0).
  * The AUTO path is pinned on every host — on a SHA-NI runner this exercises
    the real kernel, elsewhere the scalar duplicate (either way == hashlib).
  * The "kernel actually ran" assertion is EXERCISE-IF-PRESENT / SKIP-WITH-LOG
    keyed on the native cpuid probe (``_native.has_shani()``), so we never
    silently claim SHA-NI coverage on a host that lacks the feature. The CI
    cpuid-dump step records which runs hit it.
"""

import hashlib
import os

import pytest

from srmech.amsc import _native
from srmech.amsc.format import sha256_bytes

# Lengths that hit every FIPS padding boundary: 0/1/2-block transitions
# (55->56 and 119->120 are where an extra padding block appears).
_LENS = [0, 1, 2, 3, 31, 32, 55, 56, 57, 63, 64, 65, 71, 72, 119, 120,
         127, 128, 129, 191, 192, 200, 256, 257, 511, 512]


def _msg(length: int, seed: int = 0) -> bytes:
    return bytes((i * 7 + length + seed) & 0xFF for i in range(length))


_HAS_SHANI_SYM = (
    _native.HAS_NATIVE
    and _native.LIB is not None
    and hasattr(_native.LIB, "srmech_sha256_shani")
)

_skip = pytest.mark.skipif(
    not _HAS_SHANI_SYM, reason="native srmech_sha256_shani unavailable")

_FORCE = "SRMECH_SHANI_FORCE_TIER"


# ──────────────────────────────────────────────────────────────────────
# Public surface (any host, any backend)
# ──────────────────────────────────────────────────────────────────────


def test_sha256_bytes_still_matches_hashlib():
    """The high-level dispatch (which now prefers the SHA-NI symbol when
    present) is byte-identical to hashlib across every padding boundary."""
    for L in _LENS:
        d = _msg(L)
        assert sha256_bytes(d) == hashlib.sha256(d).hexdigest(), L


def test_nist_anchors():
    anchors = {
        b"": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        b"abc": "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad",
    }
    for msg, want in anchors.items():
        assert sha256_bytes(msg) == want


# ──────────────────────────────────────────────────────────────────────
# Native peer (skipped when the rc18 symbol is unavailable)
# ──────────────────────────────────────────────────────────────────────


@_skip
def test_native_shani_auto_matches_hashlib():
    """AUTO dispatch (env unset): on a SHA-NI host this runs the kernel,
    elsewhere the scalar duplicate — bit-exact either way."""
    for L in _LENS:
        d = _msg(L, seed=5)
        assert _native.sha256_shani_c(d) == hashlib.sha256(d).hexdigest(), L


@_skip
def test_native_shani_matches_single_stream():
    """SHA-NI digest == the existing native scalar single-stream
    (sha256_hex_c) per message — the C/Python full-parity check."""
    for L in _LENS:
        d = _msg(L, seed=11)
        assert _native.sha256_shani_c(d) == _native.sha256_hex_c(d), L


@_skip
def test_native_shani_force_scalar_matches_hashlib(monkeypatch):
    """SRMECH_SHANI_FORCE_TIER=0 pins the self-contained SCALAR oracle on
    ANY host (this is the path dev + non-SHA-NI CI actually execute)."""
    monkeypatch.setenv(_FORCE, "0")
    for L in _LENS:
        d = _msg(L, seed=7)
        assert _native.sha256_shani_c(d) == hashlib.sha256(d).hexdigest(), L


@_skip
def test_native_shani_force_kernel_is_safe(monkeypatch):
    """SRMECH_SHANI_FORCE_TIER=1 requests the SHA-NI kernel: on a host WITH
    the feature it runs the kernel; on a host WITHOUT it the C code never
    enters the kernel (cpuid-guarded) and falls back to scalar. Either way
    the digest is correct — the force hook can never SIGILL."""
    monkeypatch.setenv(_FORCE, "1")
    for L in _LENS:
        d = _msg(L, seed=13)
        assert _native.sha256_shani_c(d) == hashlib.sha256(d).hexdigest(), L


@_skip
def test_native_shani_large_and_mixed():
    big = b"a" * 1_000_000
    assert _native.sha256_shani_c(big) == hashlib.sha256(big).hexdigest()
    pool = [0, 1, 56, 63, 64, 65, 120, 129, 200, 511, 512, 1000]
    for i, n in enumerate(pool):
        d = _msg(n, seed=i)
        assert _native.sha256_shani_c(d) == hashlib.sha256(d).hexdigest(), n


# ──────────────────────────────────────────────────────────────────────
# Exercise-if-present / skip-with-log: did the real SHA-NI kernel run?
# ──────────────────────────────────────────────────────────────────────


@_skip
def test_shani_kernel_exercised_if_host_supports_it(monkeypatch):
    """The explicit coverage statement. If this run's host carries the SHA
    feature, force tier 1 and assert the KERNEL output == hashlib over the
    full battery (the SHA-NI path really ran). If the host lacks SHA-NI, the
    kernel was compiled (target-attribute-guarded, builds everywhere) but
    cannot be exercised here — SKIP WITH A LOG rather than silently passing
    a scalar run off as kernel coverage. The CI cpuid-dump step reports
    which matrix cells actually have the feature."""
    host = _native.has_shani()
    if host is None:
        pytest.skip("native SHA-NI cpuid probe unavailable on this build")
    if host is False:
        pytest.skip(
            "host lacks the Intel SHA Extensions; the SHA-NI kernel is "
            "compiled (target-attribute-guarded) but NOT exercised on this "
            "runner — a SHA-NI-capable CI cell exercises it"
        )
    # host is True -> the kernel genuinely runs here.
    monkeypatch.setenv(_FORCE, "1")
    for L in _LENS:
        d = _msg(L, seed=21)
        assert _native.sha256_shani_c(d) == hashlib.sha256(d).hexdigest(), L
    # And the auto path (no force) also hits the kernel on this host.
    monkeypatch.delenv(_FORCE, raising=False)
    big = b"z" * 250_003
    assert _native.sha256_shani_c(big) == hashlib.sha256(big).hexdigest()


def test_has_shani_probe_shape():
    """The probe wrapper returns a tri-state: True / False from the native
    cpuid probe, or None when the native lib / probe symbol is absent."""
    val = _native.has_shani()
    assert val is None or isinstance(val, bool)
    # If the SHA-NI hashing symbol is present, the probe symbol should be too
    # (they ship together in rc18+), so the probe must be a concrete bool.
    if _HAS_SHANI_SYM and hasattr(_native.LIB, "srmech_simd_has_shani"):
        assert isinstance(val, bool)


def test_force_tier_env_not_leaked():
    """Guard: the force-tier env hook must not be set in the ambient
    environment (it would skew every other test's dispatch)."""
    assert _FORCE not in os.environ
