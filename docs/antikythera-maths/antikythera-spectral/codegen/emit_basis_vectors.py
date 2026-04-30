"""Emit ``_data/basis_vectors_d{940,13440}.npz`` — deterministic HDC channel bases.

The HDC encoder in ``research.encode_ant`` uses one dense complex
unit-norm channel basis vector per (D, dial_idx). These bases are
deterministically seeded per (D, dial_index) so they're byte-reproducible
across runs. Pre-computing them at codegen time and shipping the NPZ in
the wheel saves the consumer the seeding-and-Gram-check cost on first
encode call (per-D Gram-matrix preflight is only done at codegen time).

Two NPZ files are emitted:

- ``basis_vectors_d940.npz``    — D=940 (Callippic variant)
- ``basis_vectors_d13440.npz``  — D=13440 (packing variant)

Each NPZ keys an array per supported dial:

- ``basis_<dial_name>``  — complex128 array of shape ``(D,)``
- ``meta``                 — JSON-encoded dict: ``{D, n_dials, dial_names,
                              gram_max_offdiag}``.

Run::

    python codegen/emit_basis_vectors.py
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

import numpy as np

from _paths import DATA_DIR, ensure_research_importable

ensure_research_importable()
from research.encode_ant import (  # noqa: E402
    DIAL_SPECS,
    D_CALLIPPIC,
    D_PACKING,
    channel_basis_gram_max_offdiag,
    get_channel_basis,
    supported_dials,
)


def _emit_for_d(D: int, label: str) -> Path:
    out_path = DATA_DIR / f"basis_vectors_d{D}.npz"
    out_path.parent.mkdir(parents=True, exist_ok=True)

    supported = supported_dials(D)
    arrays: Dict[str, Any] = {}
    for dial in supported:
        idx = DIAL_SPECS.index(dial)
        basis = get_channel_basis(D, idx)
        arrays[f"basis_{dial.name}"] = basis

    gram_max = channel_basis_gram_max_offdiag(D)
    meta = {
        "schema_version": 1,
        "D": D,
        "label": label,
        "n_dials": len(supported),
        "dial_names": [s.name for s in supported],
        "gram_max_offdiag": float(gram_max),
        "source_module": "research.encode_ant",
    }
    arrays["meta"] = np.array(json.dumps(meta, sort_keys=True), dtype=object)

    np.savez(out_path, **arrays)
    return out_path


def emit() -> Dict[int, Path]:
    return {
        D_CALLIPPIC: _emit_for_d(D_CALLIPPIC, "callippic"),
        D_PACKING: _emit_for_d(D_PACKING, "packing"),
    }


if __name__ == "__main__":
    paths = emit()
    for D, p in paths.items():
        print(f"wrote {p} ({p.stat().st_size} bytes, D={D})")
