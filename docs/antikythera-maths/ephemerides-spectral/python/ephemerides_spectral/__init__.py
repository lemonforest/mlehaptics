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


DEFAULT_BACKEND: str = "bip"
"""Module-level default for ``default_encode`` and the bridge's
``backend`` keyword. ``"bip"`` is the bit-serialised integer ALU (305×
speedup, 256 KB state, 0.0002 rad floor). ``"complex128"`` is the FPU
reference encoder, kept for the algebraic identities (Syzygy operator,
observer binding, regression baseline)."""


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
    if backend == "complex128":
        from ephemerides_spectral._research.ephemeris_reference_instrument import (
            EphemerisHDCInstrument,
        )
        inst_ref = EphemerisHDCInstrument(D=int(D), kernel=kernel)
        return inst_ref.encode_state(float(jd))
    raise ValueError(f"backend must be 'bip' or 'complex128'; got {backend!r}")


__all__ = [
    "__version__",
    "DEFAULT_BACKEND",
    "default_encode",
]
