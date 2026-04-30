"""HDC encoder facade.

Re-exports the three D-variant encoders + the deterministic channel-basis
machinery from ``_research.encode_ant`` under a curated public API.

Example::

    >>> from antikythera_spectral.encoder import encode_ant_callippic, REFERENCE_JD
    >>> state = encode_ant_callippic(REFERENCE_JD)
    >>> state.shape
    (940,)
"""

from __future__ import annotations

from antikythera_spectral._research.encode_ant import (
    DIAL_SPECS,
    D_CALLIPPIC,
    D_PACKING,
    DialSpec,
    LCMState,
    REFERENCE_JD,
    UnsupportedDialError,
    advance_day,
    channel_basis_gram_max_offdiag,
    encode_ant_block_diagonal,
    encode_ant_callippic,
    encode_ant_lcm,
    encode_ant_packing,
    get_channel_basis,
    sigma_day,
    supported_dials,
)

# D=LCM is computed lazily because it depends on cycle data; expose
# the *function* not the value, so consumers don't pay for it on import.
from antikythera_spectral._research.encode_ant import _compute_d_lcm as compute_d_lcm  # noqa: WPS437

__all__ = [
    # Constants
    "DIAL_SPECS",
    "D_CALLIPPIC",
    "D_PACKING",
    "REFERENCE_JD",
    # Types
    "DialSpec",
    "LCMState",
    "UnsupportedDialError",
    # Encoders
    "encode_ant_callippic",
    "encode_ant_packing",
    "encode_ant_lcm",
    "encode_ant_block_diagonal",
    # Channel-basis API
    "supported_dials",
    "get_channel_basis",
    "channel_basis_gram_max_offdiag",
    # Time evolution
    "sigma_day",
    "advance_day",
    "compute_d_lcm",
]
