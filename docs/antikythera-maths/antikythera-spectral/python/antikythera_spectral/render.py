"""Rendering facade — Patch-3 (rendering-agnostic) projection from HDC state to 2D.

Re-exports from ``_research.rendering``. Two layouts:

- ``render_dial``     — concentric circular dials (Antikythera physical artefact).
- ``render_spatial``  — bodies at scaled orbital radii (orrery / planetarium).

Both consult static defaults: ``DIAL_LAYOUT_FREETH_2021`` and
``ORBITAL_RADII_AU``. The HDC state captured by the encoder is the
complete dynamic input; rendering is a static lookup that picks a
radial-parameter table.
"""

from __future__ import annotations

from antikythera_spectral._research.rendering import (
    DIAL_LAYOUT_FREETH_2021,
    ORBITAL_RADII_AU,
    render_dial,
    render_spatial,
)

__all__ = [
    "render_dial",
    "render_spatial",
    "DIAL_LAYOUT_FREETH_2021",
    "ORBITAL_RADII_AU",
]
