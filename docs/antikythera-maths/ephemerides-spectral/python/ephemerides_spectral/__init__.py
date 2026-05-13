"""ephemerides-spectral — HDC instrument for the Sol Star System.

Public-API surface:

    ephemerides_spectral.bridge      — Pyodide-friendly JSON bridge
    ephemerides_spectral.cli         — `ephemerides-spectral` console script
    ephemerides_spectral._research   — frozen snapshots of the research code:
                                       laplacian, BIP + reference instruments,
                                       bodies, ephemeris loader

Top-level convenience::

    ephemerides_spectral.default_encode  — one-liner: encode a JD as a
                                           system state under the package's
                                           default backend ('bip', the
                                           bit-serialised integer ALU).
                                           Pass ``backend="complex128"`` to
                                           opt into the FPU reference.

Companion project: ``antikythera-spectral`` — sibling research notebook
under the same ``docs/antikythera-maths/`` folder. The two projects
share the spectral / cyclic-group framing and the Pyodide bridge
contract; ephemerides extends the model to the full DE441 ephemeris
with phase-dependent (breathing) couplings.
"""

from __future__ import annotations

from typing import Any

from ephemerides_spectral.version import __version__


# ──────────────────────────────────────────────────────────────────────
# AMSC bootstrap registration (Task #197 Phase 3)
# ──────────────────────────────────────────────────────────────────────
#
# Push ephemerides-spectral's catalog SSOT root + the gap_suggester's
# classifier + probe modules into the srmech.amsc framework. The
# framework lives in srmech (the AMSC-to-srmech refactor); the catalogs
# and the dynamical-regime classifier remain ephemerides-specific and
# live in ephemerides's ``_research/`` subpackage. Bootstrap binds the
# two at package-import time so any consumer importing
# ``ephemerides_spectral`` (or its bridge / cli / submodules) gets the
# correct cross-package wiring without thinking about it.
#
# Idempotent: re-importing ephemerides_spectral re-runs the bootstrap,
# but :func:`register_attested_root` / :func:`register_classifier` /
# :func:`register_probes` all handle re-registration cleanly (first-
# wins for roots; last-wins for classifier/probes).


def _bootstrap_amsc() -> None:
    """Register ephemerides-spectral's catalog root + gap_suggester
    dependencies with srmech.amsc."""
    from pathlib import Path

    from srmech.amsc import catalog as _amsc_catalog
    from srmech.amsc import gap_suggester as _amsc_gap

    # Register the attested catalog root.
    _research_dir = Path(__file__).resolve().parent / "_research"
    _attested_root = _research_dir / "attested"
    _amsc_catalog.register_attested_root(
        _attested_root, source="ephemerides-spectral"
    )

    # Register gap_suggester dependencies (Phase 2 Deviation #1
    # resolution: cross-package classifier + probes pushed by the
    # consumer at import time).
    from ephemerides_spectral._research import (
        dynamical_regime_catalog as _classifier_mod,
    )
    from ephemerides_spectral._research import (
        dynamical_regime_probes_data as _probes_mod,
    )
    _amsc_gap.register_classifier(_classifier_mod)
    _amsc_gap.register_probes(_probes_mod)


_bootstrap_amsc()


DEFAULT_BACKEND: str = "bip"
"""Module-level default for ``default_encode`` and the bridge's
``backend`` keyword.

Three backends are supported:

* ``"bip"`` (default) — pure-Python bit-serialised integer ALU.
  Always available; 305× speedup vs the FPU reference; 256 KB state
  at D=65536; 0.0002 rad Earth-phase floor at +20 yr.
* ``"complex128"`` — FPU complex128 reference encoder. Used for the
  algebraic identities (Syzygy operator, observer binding) and as
  the regression baseline.
* ``"c"`` (v0.3.1+) — native BIP encoder via the bundled C library.
  Byte-for-byte identical phases to ``"bip"``, faster hot loop.
  Falls back transparently to ``"bip"`` if the binary isn't loadable
  (sdist installs without a C toolchain, Pyodide / WASM, the
  pure-Python fallback wheel).
"""


def default_encode(
    jd: float,
    *,
    backend: str = DEFAULT_BACKEND,
    kernel: str = "de441",
    D: int = 65536,
) -> "Any":
    """Encode a Julian date as a system state under the chosen backend.

    Parameters
    ----------
    jd : float
        Julian Date (TDB). ``REFERENCE_JD = 2451545.0`` is the J2000
        anchor.
    backend : str, default ``"bip"``
        ``"bip"`` returns the per-body ``uint32`` phase residue array
        from :class:`ephemerides_spectral._research.bip_instrument.EphemerisBIPInstrument`.
        ``"complex128"`` returns the unit-norm complex state vector
        from :class:`ephemerides_spectral._research.ephemeris_reference_instrument.EphemerisHDCInstrument`.
    kernel : str, default ``"de441"``
        JPL DE-kernel for ephemeris calibration.
    D : int, default ``65536``
        Hypervector dimension; must be a power of 2.

    Returns
    -------
    numpy.ndarray
        Backend-appropriate encoded state. For ``"bip"`` this is
        ``uint32[n_bodies]`` (per-body phase residues in ``Z_{2^32}``);
        for ``"complex128"`` it is ``complex128[D]`` (unit-norm).

    See also
    --------
    :mod:`ephemerides_spectral.bridge` — JSON-friendly bridge surface
    that wraps the same backends with validation + Pyodide return shape.
    """
    if backend == "bip":
        from ephemerides_spectral._research.bip_instrument import (
            EphemerisBIPInstrument,
        )
        inst = EphemerisBIPInstrument(D=int(D), kernel=kernel)
        return inst.encode_state(float(jd))
    if backend == "c":
        from ephemerides_spectral import _native_bip
        if _native_bip.HAS_NATIVE:
            from ephemerides_spectral._research.ephemeris_reference_instrument import (
                REFERENCE_JD,
            )
            return _native_bip.encode_state(float(jd) - REFERENCE_JD)
        # Transparent fallback — same shape as backend="bip".
        from ephemerides_spectral._research.bip_instrument import (
            EphemerisBIPInstrument,
        )
        inst = EphemerisBIPInstrument(D=int(D), kernel=kernel)
        return inst.encode_state(float(jd))
    if backend == "complex128":
        from ephemerides_spectral._research.ephemeris_reference_instrument import (
            EphemerisHDCInstrument,
        )
        inst_ref = EphemerisHDCInstrument(D=int(D), kernel=kernel)
        return inst_ref.encode_state(float(jd))
    raise ValueError(
        f"backend must be 'bip', 'complex128', or 'c'; got {backend!r}"
    )


__all__ = [
    "__version__",
    "DEFAULT_BACKEND",
    "default_encode",
]
