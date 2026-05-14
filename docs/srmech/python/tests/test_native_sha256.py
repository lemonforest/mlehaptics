"""Cross-language parity test for srmech_sha256_hex.

Task #201 Phase B3 — pins the native C implementation to byte-exact
agreement with Python's ``hashlib.sha256()`` across the matrix of
fixture inputs that cover the SHA-256 padding edge cases (full-block
boundary, two-padding-block boundary, etc.) plus a few representative
real-world-sized payloads.

The test is gracefully skipped when the native library isn't shipped
(pure-Python wheel install on Pyodide / WASM). In that case the
fallback path is the Python hashlib one, so the parity question is
moot.
"""

from __future__ import annotations

import hashlib

import pytest

from srmech.amsc import _native, format as srfmt


pytestmark = pytest.mark.skipif(
    not _native.HAS_NATIVE,
    reason=(
        "native srmech library not loaded "
        f"(LOAD_ERROR={_native.LOAD_ERROR}); "
        "this test pins C/Python parity, so a pure-Python wheel "
        "install legitimately skips it"
    ),
)


# ──────────────────────────────────────────────────────────────────────
# Fixture inputs covering the SHA-256 padding boundaries + a few
# representative sizes
# ──────────────────────────────────────────────────────────────────────
FIXTURES: list[tuple[str, bytes]] = [
    ("empty", b""),
    ("FIPS-B.2 'abc'", b"abc"),
    (
        "FIPS-B.3 two-block",
        b"abcdbcdecdefdefgefghfghighijhijkijkljklmklmnlmnomnopnopq",
    ),
    ("hello world", b"hello world"),
    ("55 'a' (single-tail-block boundary)", b"a" * 55),
    ("56 'a' (two-padding-block boundary)", b"a" * 56),
    ("63 'a' (one-byte-shy-of-full-block)", b"a" * 63),
    ("64 'a' (full-block boundary)", b"a" * 64),
    ("65 'a' (one-byte-into-second-block)", b"a" * 65),
    ("119 'a' (just-shy-of-two-blocks-plus-pad)", b"a" * 119),
    ("128 'a' (exactly-two-blocks)", b"a" * 128),
    ("1024 'a'", b"a" * 1024),
    ("all bytes 0..255", bytes(range(256))),
    ("64 KiB of 'x'", b"x" * 65536),
    ("256 KiB of 'y'", b"y" * (256 * 1024)),
]


@pytest.mark.parametrize("name,data", FIXTURES, ids=[n for n, _ in FIXTURES])
def test_native_matches_hashlib(name: str, data: bytes) -> None:
    """Native sha256_hex matches stdlib hashlib byte-for-byte."""
    py = hashlib.sha256(data).hexdigest()
    native = _native.sha256_hex_c(data)
    assert native == py, (
        f"{name}: native {native!r} != hashlib {py!r}"
    )


def test_format_sha256_bytes_dispatches_to_native() -> None:
    """The user-facing ``srmech.amsc.format.sha256_bytes`` dispatches
    through ``_native.sha256_hex_c`` when HAS_NATIVE is True. The
    result must still be byte-identical to hashlib (otherwise the
    dispatch silently introduced a regression)."""
    data = b"the quick brown fox jumps over the lazy dog"
    assert srfmt.sha256_bytes(data) == hashlib.sha256(data).hexdigest()


def test_native_version_and_abi() -> None:
    """The shipped C library reports the version + ABI we expect.

    The real invariant: the C-side ``srmech_version()`` string must
    match the Python-side ``srmech.__version__``. Both are derived
    from the SSOT (`pyproject.toml` + `c/include/srmech.h`); if they
    drift, the wheel was built against a stale header or a stale
    Python version file. Asserting equality here catches that
    drift across all future version bumps without per-version
    string churn in the test.
    """
    import srmech as _srmech
    assert _native.NATIVE_VERSION is not None
    assert _native.NATIVE_VERSION == _srmech.__version__, (
        f"C-side srmech_version() = {_native.NATIVE_VERSION!r} but "
        f"Python srmech.__version__ = {_srmech.__version__!r}; the "
        f"version SSOTs (c/include/srmech.h and "
        f"python/srmech/version.py) have drifted out of sync."
    )
    assert _native.NATIVE_ABI_VERSION == _native.EXPECTED_ABI_VERSION


def test_random_inputs_parity() -> None:
    """200 random byte strings of varying length all hash identically."""
    import random
    rng = random.Random(20260513)
    for _ in range(200):
        length = rng.randint(0, 4096)
        data = bytes(rng.randint(0, 255) for _ in range(length))
        assert _native.sha256_hex_c(data) == hashlib.sha256(data).hexdigest()
