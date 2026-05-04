"""antikythera-spectral — HDC encoder + Pyodide bridge for the Antikythera mechanism.

Public-API surface:

    antikythera_spectral.bridge          -- 28-method Pyodide bridge (§5 of plan)
    antikythera_spectral.encoder         -- HDC encoder facade (complex128 reference)
    antikythera_spectral.decoder         -- HDC decoder facade
    antikythera_spectral.dials           -- dial / cycle accessor
    antikythera_spectral.dates           -- 4-calendar conversion
    antikythera_spectral.visibility      -- heliacal rising / setting
    antikythera_spectral.eclipses        -- frozen-data accessor
    antikythera_spectral.eclipses_search -- sky-driven eclipse enumeration
    antikythera_spectral.operator        -- §11.6.16 workflow simulation
    antikythera_spectral.compare         -- DE-kernel + model comparators
    antikythera_spectral.reconstructions -- Freeth / Wright / Price comparator
    antikythera_spectral.whatif          -- arbitrary-gear-ratio re-encoder
    antikythera_spectral.archaeology     -- fragment-keyed gear inventory
    antikythera_spectral.goalyear        -- Babylonian Goal-Year overlay
    antikythera_spectral.animation       -- time-series state export
    antikythera_spectral.hypotheses      -- H-battery facade
    antikythera_spectral.mars_models     -- Hellenistic Mars models (v0.3.0)
    antikythera_spectral.bit_alu         -- bit-packed binary HDC ALU (v0.3.0)

Top-level convenience::

    antikythera_spectral.default_encode  -- one-liner: encode JD as a state
                                            vector under the package's
                                            default backend.  v0.3.0 flips
                                            the default to the bit-packed
                                            ALU (ADR 0012); pass
                                            ``backend="complex128"`` for
                                            the legacy reference encoder.
"""

from __future__ import annotations

from typing import Any

import numpy as np

from antikythera_spectral.version import __version__


# ---------------------------------------------------------------------------
# Default-backend convenience (v0.3.0)
# ---------------------------------------------------------------------------

DEFAULT_BACKEND: str = "bit"
"""Module-level default for ``default_encode`` and the bridge's ``backend``
keyword.  v0.3.0 flips this from ``"complex128"`` to ``"bit"``; the bit-
packed ALU is the natural production backend per ADR 0012.

Backwards compatibility: every API that gained a ``backend`` keyword in
v0.3.0 accepts ``"complex128"`` explicitly to recover the v0.2.x return
shape (interleaved-Float32 state vectors).  The complex128 reference
encoder is preserved indefinitely for the H-battery's algebraic
identities (FHRR-style superposition) and for anyone needing the
unit-norm complex Gaussian basis."""


def default_encode(
    jd: float,
    *,
    D: int = 940,
    backend: str = DEFAULT_BACKEND,
) -> "np.ndarray":
    """Encode a Julian date as a hypervector under the chosen backend.

    Parameters
    ----------
    jd : float
        Julian Date (TDB).  ``REFERENCE_JD = 1684595.0`` is the
        Antikythera-era anchor.
    D : int, default 940
        Hypervector dimension.  ``940`` (Callippic) or ``13440``
        (packing) are supported by both backends.
    backend : str, default ``DEFAULT_BACKEND`` ("bit")
        ``"bit"`` → packed-uint64 binary HV via
        :func:`antikythera_spectral.bit_alu.encode_ant_bit`.  Returns
        ``numpy.ndarray`` of dtype ``uint64`` and shape
        ``(ceil(D/64),)``.  Memory: 120 B at D=940.

        ``"complex128"`` → unit-norm complex Gaussian HV via
        :func:`antikythera_spectral.encoder.encode_ant_callippic`
        (or ``encode_ant_packing`` at D=13440).  Returns
        ``numpy.ndarray`` of dtype ``complex128`` and shape ``(D,)``.
        Memory: 15 KB at D=940.

    Returns
    -------
    numpy.ndarray
        Backend-appropriate encoded state.  Both backends implement
        the same algebraic substrate (cyclic-group representation of
        the Antikythera dials); see ADR 0012 for the scope discipline.

    See also
    --------
    :mod:`antikythera_spectral.bit_alu` — primitives that operate on
    the bit-packed return.
    :mod:`antikythera_spectral.encoder` — the named complex128
    encoders (``encode_ant_callippic``, ``encode_ant_packing``,
    ``encode_ant_lcm``, ``encode_ant_block_diagonal``).
    """
    if backend == "bit":
        # Lazy import: keeps `import antikythera_spectral` cheap and
        # the bit_alu module's _research dependency tree off the hot
        # import path for users who only touch encoder / bridge.
        from antikythera_spectral.bit_alu import encode_ant_bit
        return encode_ant_bit(float(jd), int(D))
    if backend == "complex128":
        from antikythera_spectral.encoder import (
            D_CALLIPPIC,
            encode_ant_callippic,
            encode_ant_packing,
        )
        if D == D_CALLIPPIC:
            return encode_ant_callippic(float(jd))
        return encode_ant_packing(float(jd))
    raise ValueError(
        f"backend must be 'bit' or 'complex128'; got {backend!r}"
    )


__all__ = [
    "__version__",
    "DEFAULT_BACKEND",
    "default_encode",
]
