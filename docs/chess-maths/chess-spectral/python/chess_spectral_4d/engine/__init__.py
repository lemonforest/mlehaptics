"""chess_spectral_4d.engine -- 4D position evaluation, search, tournament.

Phase 6 (v1.6) engine surface for the 4D spectral encoder. Mirrors
:mod:`chess_spectral.engine` (2D) at every level.

The engine namespace ships in stages:
  * ``eval.material`` (PR-2; in main)
  * ``eval.spectral`` (PR-3; in main)
  * ``eval.qm`` (PR-4; in flight)
  * ``search`` (PR-7-I; this PR -- the in-house bitboard-driven 4D
    search core, built on Board4D from PR-7-F)

This __init__ module imports whatever is present at the time of
load. When PR-7-I lands alongside the eval submodules, the
__init__ will register all of them; for now (this branch is
stacked on the spatial_4d arc which predates the eval merges),
only ``search`` is reachable here.
"""
from __future__ import annotations

from . import search  # noqa: F401

__all__ = ["search"]
