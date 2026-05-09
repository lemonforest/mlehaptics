"""Body→kernel registry — phase C of v0.27.0 (notebook §22.6).

Stores the layer-2-to-layer-3 interface from the three-layer mechanism
architecture: a mapping of ``{body → (kernel_path, precision_tier)}``
that orbital-mechanics bridge surfaces consult before falling back to
the BODIES-distilled values codegen-derived from DE441.

The registry is **structural in v0.27.x phase C**: registrations are
tracked, hashed, and surfaced via bridge metadata, but the orbital-
mechanics surfaces fall back to BODIES for actual state lookups
because the binary kernels themselves are not yet readable. Phase B
(``binary_archive`` adapter + ``ephemeris_loader.py`` integration)
adds the kernel-reading capability that turns the registry from
metadata into behaviour.

The shape of the interface is locked here so phase A's
``literature_curated`` backfill, phase B's ``binary_archive`` adapter,
and the eventual integration tests can all target the same registry
abstraction. See notebook §22 for the architecture.

Reproducibility tier
--------------------
Like :func:`attested_collector_catalog.use_local_kernel`, the
registry is process-local module state. Within a single process,
queries are deterministic; across processes, the registry is empty
until ``register`` is called. ``state_hash`` provides the cache key
for module-load-time eigenbasis caches (body_architecture,
predict_itn_accessibility) so a user changing the registry forces
the right cache invalidations.
"""

from __future__ import annotations

import hashlib
import json
import os
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple


# ──────────────────────────────────────────────────────────────────────
# Precision-tier taxonomy
# ──────────────────────────────────────────────────────────────────────


PRECISION_TIER_JPL_PUBLISHED: str = "jpl_published"
"""The kernel is a published JPL ephemeris — DE441 family, sat441,
ura111, nep097, jup365, plu060, small-body kernels, etc."""

PRECISION_TIER_BODIES_FALLBACK: str = "bodies_fallback"
"""No kernel registered; orbital-mechanics surfaces read from the
BODIES-distilled values that codegen baked from DE441 at ship time.
This is the precision tier surfaces report when the registry has no
entry for a body."""

PRECISION_TIER_USER_FIT: str = "user_fit"
"""User-supplied orbital-element fit — for hypothetical bodies, or
bodies where no published kernel exists. Marked explicitly so
consumers can scope queries."""

VALID_PRECISION_TIERS: Tuple[str, ...] = (
    PRECISION_TIER_JPL_PUBLISHED,
    PRECISION_TIER_BODIES_FALLBACK,
    PRECISION_TIER_USER_FIT,
)


# ──────────────────────────────────────────────────────────────────────
# Registration record
# ──────────────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class BodyKernelRegistration:
    """One entry in the body→kernel registry.

    All fields participate in the canonical hash; touching any one
    forces eigenbasis cache invalidation in surfaces that key on
    ``state_hash()``.
    """
    body: str
    kernel_path: str
    precision_tier: str

    def to_dict(self) -> Dict[str, str]:
        return {
            "body": self.body,
            "kernel_path": self.kernel_path,
            "precision_tier": self.precision_tier,
        }


# ──────────────────────────────────────────────────────────────────────
# Module-level registry state
# ──────────────────────────────────────────────────────────────────────


_REGISTRY: Dict[str, BodyKernelRegistration] = {}
"""Body name → registration. Empty by default; populated by
:func:`register`."""


# ──────────────────────────────────────────────────────────────────────
# Public API
# ──────────────────────────────────────────────────────────────────────


def register(
    body: str,
    kernel_path: str,
    *,
    precision_tier: str = PRECISION_TIER_JPL_PUBLISHED,
) -> Dict[str, Any]:
    """Register a kernel path for a specific body.

    Parameters
    ----------
    body
        Body name (e.g. ``"jupiter"``, ``"luna"``, ``"bennu"``).
        Validated against the BODIES roster lazily — bodies not in
        the roster are accepted (small-body / hypothetical use case)
        and simply have no scaffold-side surfaces that consult them
        until the roster is extended via a separate codegen step.
    kernel_path
        Filesystem path to the kernel file (e.g. a JPL .bsp). The
        path is stored verbatim; phase C does not validate the file
        exists or that it is a valid kernel — that validation happens
        in phase B's ``binary_archive`` adapter when the kernel is
        actually loaded.
    precision_tier
        One of ``PRECISION_TIER_JPL_PUBLISHED``,
        ``PRECISION_TIER_BODIES_FALLBACK``, or
        ``PRECISION_TIER_USER_FIT``. Default is
        ``"jpl_published"``.

    Returns
    -------
    dict
        ``{"ok": True, "body": ..., "kernel_path": ...,
        "precision_tier": ..., "registry_size": int,
        "state_hash": str}`` on success;
        ``{"ok": False, "error": str}`` on validation failure.
    """
    if not isinstance(body, str) or not body:
        return {"ok": False, "error": f"body must be a non-empty string, got {body!r}"}
    if not isinstance(kernel_path, str) or not kernel_path:
        return {"ok": False, "error": f"kernel_path must be a non-empty string, got {kernel_path!r}"}
    if precision_tier not in VALID_PRECISION_TIERS:
        return {
            "ok": False,
            "error": (
                f"precision_tier must be one of {VALID_PRECISION_TIERS}, "
                f"got {precision_tier!r}"
            ),
        }
    registration = BodyKernelRegistration(
        body=body,
        kernel_path=kernel_path,
        precision_tier=precision_tier,
    )
    _REGISTRY[body] = registration
    return {
        "ok": True,
        "body": body,
        "kernel_path": kernel_path,
        "precision_tier": precision_tier,
        "registry_size": len(_REGISTRY),
        "state_hash": state_hash(),
    }


def lookup(body: str) -> Optional[BodyKernelRegistration]:
    """Return the registration for a body, or ``None`` if unregistered."""
    return _REGISTRY.get(body)


def clear(body: Optional[str] = None) -> Dict[str, Any]:
    """Clear one body's registration, or the entire registry.

    Parameters
    ----------
    body
        Body to clear. ``None`` (default) clears every registration.

    Returns
    -------
    dict
        ``{"ok": True, "cleared": int, "registry_size": int,
        "state_hash": str}``.
    """
    if body is None:
        cleared = len(_REGISTRY)
        _REGISTRY.clear()
        return {
            "ok": True,
            "cleared": cleared,
            "registry_size": 0,
            "state_hash": state_hash(),
        }
    if body in _REGISTRY:
        del _REGISTRY[body]
        return {
            "ok": True,
            "cleared": 1,
            "registry_size": len(_REGISTRY),
            "state_hash": state_hash(),
        }
    return {
        "ok": True,
        "cleared": 0,
        "registry_size": len(_REGISTRY),
        "state_hash": state_hash(),
    }


def state() -> Dict[str, Any]:
    """Return the current registry state envelope.

    Used by orbital-mechanics surfaces to surface registry metadata
    in their response envelopes. The envelope is JSON-serialisable
    and Pyodide-safe.
    """
    registrations = [_REGISTRY[k].to_dict() for k in sorted(_REGISTRY)]
    return {
        "active": len(_REGISTRY) > 0,
        "registry_size": len(_REGISTRY),
        "registrations": registrations,
        "state_hash": state_hash(),
    }


def state_hash() -> str:
    """SHA-256 over the canonical-serialised registry state.

    The hash participates as a cache key in module-load-time
    eigenbasis caches (body_architecture's Fiedler partition;
    predict_itn_accessibility's hybrid Fiedler eigenvector).
    Touching any registration forces a re-compute when the cache
    detects the hash change.

    Empty registry → SHA-256("[]") so the empty case is a fixed,
    well-defined hash that v0.26.0-equivalent code paths can target
    in their byte-stable tests.
    """
    canonical = json.dumps(
        [_REGISTRY[k].to_dict() for k in sorted(_REGISTRY)],
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def is_active() -> bool:
    """Convenience: True iff at least one body has a registration."""
    return len(_REGISTRY) > 0


def all_bodies() -> List[str]:
    """Sorted list of registered body names. Useful for surfaces that
    want to enumerate the registered set without iterating the full
    state envelope."""
    return sorted(_REGISTRY.keys())


__all__ = [
    "PRECISION_TIER_JPL_PUBLISHED",
    "PRECISION_TIER_BODIES_FALLBACK",
    "PRECISION_TIER_USER_FIT",
    "VALID_PRECISION_TIERS",
    "BodyKernelRegistration",
    "register",
    "lookup",
    "clear",
    "state",
    "state_hash",
    "is_active",
    "all_bodies",
]
