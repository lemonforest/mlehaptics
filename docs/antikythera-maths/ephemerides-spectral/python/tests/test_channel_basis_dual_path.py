"""v0.29.0rc1 — channel-basis dual-path tests (LEGACY vs COSPI).

Pins the v0.29.0rc1 spike-level invariants:

1. ``ES_BASIS_METHOD_LEGACY`` produces output **byte-identical** to the
   shipped ``es_channel_basis`` entry point (and therefore to the Python
   side via the existing Tier 2a byte-parity test). This guarantees
   adding the dispatch enum did not perturb the LEGACY route.

2. ``ES_BASIS_METHOD_COSPI`` produces a valid unit-magnitude basis with
   the same shape / dtype as LEGACY. When ``native_has_native_cospi()``
   is True (Apple libsystem or C23 libm), the COSPI bytes generally
   differ from LEGACY; when False (fallback toolchains), the two routes
   are byte-equivalent.

3. The COSPI route's per-element magnitude deviation from unity is no
   worse than LEGACY's. This is a soft ratchet — the bench script
   (`bench/cospi_basis_bench.py`) measures the quantitative delta;
   here we only fail on a regression where COSPI is *worse* than
   LEGACY.

These tests skip when the native binary isn't loaded (sdist installs
without a C toolchain, Pyodide / WASM environments).
"""

from __future__ import annotations

import numpy as np
import pytest

from ephemerides_spectral import _native_bip
from ephemerides_spectral._native_bip import (
    ES_BASIS_METHOD_COSPI,
    ES_BASIS_METHOD_LEGACY,
)


pytestmark = pytest.mark.skipif(
    not _native_bip.HAS_NATIVE,
    reason="native library not loaded; dual-path tests require C path",
)


# ──────────────────────────────────────────────────────────────────────
# (1) LEGACY route byte-identical to es_channel_basis
# ──────────────────────────────────────────────────────────────────────


@pytest.mark.parametrize("seed,D", [
    (2026, 1024),       # body 0 (sun)
    (2026 + 5, 1024),   # body 5 (e.g. jupiter)
    (777, 1024),        # syzygy node basis
    (9999, 1024),       # topocentric coord basis
    (2026, 65536),      # production-D
])
def test_legacy_method_byte_identical_to_default(seed: int, D: int) -> None:
    """The LEGACY route through the new dispatcher must produce
    byte-identical output to the existing es_channel_basis entry point.
    Any drift here would silently break Tier 2a parity with Python.
    """
    default = _native_bip.native_channel_basis(seed, D)
    legacy = _native_bip.native_channel_basis_method(
        seed, D, ES_BASIS_METHOD_LEGACY,
    )
    assert default.dtype == legacy.dtype == np.complex64
    assert default.shape == legacy.shape == (D,)
    assert np.array_equal(default, legacy), (
        f"LEGACY method drifted from default es_channel_basis at "
        f"seed={seed}, D={D}: max |delta| = {np.max(np.abs(default - legacy))}"
    )


# ──────────────────────────────────────────────────────────────────────
# (2) COSPI route — shape + dtype + unit-magnitude
# ──────────────────────────────────────────────────────────────────────


@pytest.mark.parametrize("seed,D", [
    (2026, 1024),
    (2026 + 5, 1024),
    (777, 1024),
    (9999, 1024),
])
def test_cospi_method_shape_and_dtype(seed: int, D: int) -> None:
    """The COSPI route must return the same shape / dtype as LEGACY."""
    cospi = _native_bip.native_channel_basis_cospi(seed, D)
    assert cospi.dtype == np.complex64
    assert cospi.shape == (D,)


@pytest.mark.parametrize("seed,D", [
    (2026, 4096),
    (2026 + 5, 4096),
    (777, 4096),
])
def test_cospi_unit_magnitude(seed: int, D: int) -> None:
    """Each COSPI basis element has |z| ≈ 1 (float32 ULP-level)."""
    cospi = _native_bip.native_channel_basis_cospi(seed, D)
    mags = np.abs(cospi)
    # float32 worst-case: cos² + sin² rounds to within ~1e-6 of 1.0.
    # Native cospi/sinpi should land tighter than this in many places;
    # we use the loose bound so the spike doesn't gate on toolchain.
    assert np.max(np.abs(mags - 1.0)) < 1e-6, (
        f"COSPI basis not unit-magnitude at seed={seed}, D={D}: "
        f"max|mag-1| = {np.max(np.abs(mags - 1.0))}"
    )


# ──────────────────────────────────────────────────────────────────────
# (3) Soft ratchet — COSPI magnitude error ≤ LEGACY's
# ──────────────────────────────────────────────────────────────────────


def test_cospi_magnitude_error_no_worse_than_legacy() -> None:
    """COSPI's max |mag - 1| ≤ LEGACY's max |mag - 1| (or ≤ with a
    small allowance). On native-cospi toolchains we expect strictly
    less; on fallback toolchains the two routes are byte-equivalent
    so the inequality holds trivially.
    """
    D = 65536
    seed = 2026
    legacy = _native_bip.native_channel_basis_method(seed, D, ES_BASIS_METHOD_LEGACY)
    cospi = _native_bip.native_channel_basis_cospi(seed, D)
    legacy_max = float(np.max(np.abs(np.abs(legacy) - 1.0)))
    cospi_max = float(np.max(np.abs(np.abs(cospi) - 1.0)))
    # Allowance: float32 LSB at unity (~6e-8) — fairness margin so
    # libm-version-pinned LEGACY isn't accidentally tighter than COSPI
    # by a single ULP on some toolchains.
    ALLOWANCE = 6e-8
    assert cospi_max <= legacy_max + ALLOWANCE, (
        f"COSPI magnitude error worse than LEGACY: "
        f"cospi={cospi_max:.2e}, legacy={legacy_max:.2e}, "
        f"allowance={ALLOWANCE:.0e}. Did the COSPI path regress?"
    )


# ──────────────────────────────────────────────────────────────────────
# (4) has_native_cospi is a stable bool
# ──────────────────────────────────────────────────────────────────────


def test_native_has_native_cospi_returns_bool() -> None:
    """The compile-time flag is exposed as a Python bool. Bench scripts
    label their reports with it; this test pins the API shape."""
    flag = _native_bip.native_has_native_cospi()
    assert isinstance(flag, bool)


# ──────────────────────────────────────────────────────────────────────
# (5) Method-enum dispatcher — invalid enum value rejected
# ──────────────────────────────────────────────────────────────────────


def test_invalid_method_enum_raises_runtime_error() -> None:
    """An out-of-range method value must be rejected (returns
    ES_ERR_INVALID_KIND = 5 from the C side, surfaced as RuntimeError)."""
    with pytest.raises(RuntimeError):
        _native_bip.native_channel_basis_method(2026, 64, method=99)
