"""JPL DE-kernel facade.

Re-exports the lazy ephemeris loader from ``_research.ephemeris_loader``.

The kernel name is validated against an allowlist (``ALLOWED_KERNELS``)
**before** any URL or filesystem path is constructed — a CodeQL-aware
discipline that prevents user-controlled strings from reaching network
or path operations. See ADR ``0003-ephemeris-allowlist-codeql.md`` in
the package's ``docs/adr/`` directory.

Example::

    >>> from antikythera_spectral.ephemeris import load_ephemeris
    >>> bundle = load_ephemeris('de421')           # returns None if not on disk
    >>> bundle is None or bundle.eph is not None
    True

For Hellenistic-era queries (-200 BCE), use ``de441_part1`` (1.5 GB)
or ``de441`` (3 GB). The DE421 kernel only covers 1899-2053 and is
included as a modern control.
"""

from __future__ import annotations

from antikythera_spectral._research.ephemeris_loader import (
    EphemerisBundle,
    KernelSpec,
    available_kernels,
    covers_jd,
    download_kernel,
    is_available,
    kernel_for_jd_range,
    load_ephemeris,
)

# Keep the allowlist tuple small + frozen so CodeQL flow analysis can
# see the constant gate.
ALLOWED_KERNELS: tuple[str, ...] = (
    "de421", "de422", "de440", "de441", "de441_part1", "de441_part2",
)
"""Frozen allowlist of accepted JPL kernel names.

Bridge methods that take a kernel-name string MUST validate against
this tuple before constructing any URL or path. Any addition needs a
PR review (and an ADR update if the new kernel comes from a non-JPL
source).
"""

__all__ = [
    "ALLOWED_KERNELS",
    "EphemerisBundle",
    "KernelSpec",
    "available_kernels",
    "covers_jd",
    "download_kernel",
    "is_available",
    "kernel_for_jd_range",
    "load_ephemeris",
]
