"""logo_hdc — HDC primitives, structured atoms, and fiber machinery.

Public API:

    from logo_hdc import (
        HD, atom, bundle, bind, unbind, perm, sim, cleanup,
        build_vocab_codebook, build_rule_codebook,
        SplitObject, build_fiber_matrix, svd_report, fiber_to_hdc,
    )
"""
from __future__ import annotations

from .hd import (
    HD, DEFAULT_DIM,
    atom, bundle, bundle_sum, bind, unbind, perm, sim, cleanup,
    normalize, rng_for,
)
from .quantum_atoms import (
    COMMAND_QUANTUM, CATEGORIES, ARGTYPES, REVERSE_AXES, ROLE_NAMES,
    build_vocab_codebook, unbind_role, swap_role_value,
)
from .codebook import build_rule_codebook
from .split import SplitObject
from .fiber import build_fiber_matrix, svd_report, fiber_to_hdc, unbind_retrieve

__all__ = [
    "HD", "DEFAULT_DIM",
    "atom", "bundle", "bundle_sum", "bind", "unbind", "perm", "sim",
    "cleanup", "normalize", "rng_for",
    "COMMAND_QUANTUM", "CATEGORIES", "ARGTYPES", "REVERSE_AXES",
    "ROLE_NAMES",
    "build_vocab_codebook", "unbind_role", "swap_role_value",
    "build_rule_codebook",
    "SplitObject",
    "build_fiber_matrix", "svd_report", "fiber_to_hdc", "unbind_retrieve",
]
