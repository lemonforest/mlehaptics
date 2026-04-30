"""§11.6.16 operator-workflow simulation — stateless API.

The operator interacts with the mechanism through a re-anchoring loop:

1. Start at a date → encode the dial state.
2. Crank forward (advance by ``delta_days``) → encoder propagates.
3. When a planet becomes observable (heliacal rising), read its
   actual sky position and re-anchor the dial → calibration delta
   captured.
4. Repeat.

This module exposes the loop as a *stateless* API: every function
takes the prior ``OperatorState`` dict in and returns a new one out.
No server-side mutation, no session ID; the caller round-trips state
through localStorage / Pyodide JSON / wherever it stores it. ADR
0006 documents the rationale.

``OperatorState`` schema (v1)::

    {
        "schema_version": 1,
        "current_jd": float,
        "D": int,
        "anchors": {dial_name: {"jd": float, "true_residue": int}},
        "history": [
            {"event": "advance" | "observe" | "start", "jd": float, ...},
            ...
        ],
    }
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict, List, Optional

import numpy as np

from antikythera_spectral._research.encode_ant import (
    DIAL_SPECS,
    D_CALLIPPIC,
    DialSpec,
    REFERENCE_JD,
)


_DIAL_BY_NAME: Dict[str, DialSpec] = {s.name: s for s in DIAL_SPECS}


def start_session(initial_jd: float, *,
                   D: int = D_CALLIPPIC,
                   dials: str = "all") -> Dict[str, Any]:
    """Initial OperatorState dict at ``initial_jd``."""
    return {
        "schema_version": 1,
        "current_jd": float(initial_jd),
        "D": int(D),
        "dials_filter": dials,
        "anchors": {},
        "history": [
            {"event": "start", "jd": float(initial_jd), "D": int(D)},
        ],
    }


def advance(state: Dict[str, Any], delta_days: float) -> Dict[str, Any]:
    """Advance the operator's current_jd by ``delta_days`` and log."""
    new_state = deepcopy(state)
    new_state["current_jd"] = float(state["current_jd"]) + float(delta_days)
    new_state["history"].append({
        "event": "advance",
        "from_jd": float(state["current_jd"]),
        "to_jd": new_state["current_jd"],
        "delta_days": float(delta_days),
    })
    return new_state


def observe(state: Dict[str, Any], dial: str,
             observed_residue: int) -> Dict[str, Any]:
    """Record an operator observation of `dial` at the current JD.

    The observed residue (read off the actual sky) is stored as the
    new anchor for that dial; subsequent ``operator_diagnostics`` calls
    measure drift relative to this anchor.
    """
    if dial not in _DIAL_BY_NAME:
        raise ValueError(f"unknown dial {dial!r}")
    new_state = deepcopy(state)
    new_state["anchors"][dial] = {
        "jd": float(state["current_jd"]),
        "true_residue": int(observed_residue),
    }
    new_state["history"].append({
        "event": "observe",
        "jd": float(state["current_jd"]),
        "dial": dial,
        "observed_residue": int(observed_residue),
    })
    return new_state


def diagnostics(state: Dict[str, Any]) -> Dict[str, Any]:
    """Per-dial drift diagnostics (days-since-anchor, drift-residue).

    For each anchored dial: compute the residue the encoder would emit
    today minus the anchor's true residue. Reported as both raw integer
    diff and equivalent angular drift.
    """
    out: Dict[str, Dict[str, Any]] = {}
    current_jd = float(state["current_jd"])
    for dial_name, anchor in state.get("anchors", {}).items():
        spec = _DIAL_BY_NAME.get(dial_name)
        if spec is None:
            continue
        encoded_now = spec.integer_residue(current_jd)
        days_since = current_jd - float(anchor["jd"])
        residue_diff = (encoded_now - int(anchor["true_residue"])) % spec.cycle_modulus
        # Wrap residue to symmetric [-modulus/2, +modulus/2)
        if residue_diff > spec.cycle_modulus / 2:
            residue_diff -= spec.cycle_modulus
        angle_drift_deg = 360.0 * residue_diff / spec.cycle_modulus
        out[dial_name] = {
            "days_since_anchor": float(days_since),
            "residue_diff": int(residue_diff),
            "angle_drift_deg": float(angle_drift_deg),
            "anchor_jd": float(anchor["jd"]),
            "anchor_residue": int(anchor["true_residue"]),
        }
    return {
        "current_jd": current_jd,
        "n_anchors": len(out),
        "per_dial": out,
    }


__all__ = ["start_session", "advance", "observe", "diagnostics"]
