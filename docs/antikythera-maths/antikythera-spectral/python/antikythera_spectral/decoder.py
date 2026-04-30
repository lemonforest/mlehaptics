"""Decoder facade.

Re-exports the per-encoder decode paths from ``_research.dial_decoder``.
"""

from __future__ import annotations

from antikythera_spectral._research.dial_decoder import (
    decode_all_dials_block_diagonal,
    decode_all_dials_dense,
    decode_dial_block_diagonal,
    decode_dial_dense,
    decode_dial_lcm,
    round_trip_block_diagonal,
    round_trip_dense,
    round_trip_lcm,
)

__all__ = [
    "decode_dial_dense",
    "decode_dial_lcm",
    "decode_dial_block_diagonal",
    "decode_all_dials_dense",
    "decode_all_dials_block_diagonal",
    "round_trip_dense",
    "round_trip_lcm",
    "round_trip_block_diagonal",
]
