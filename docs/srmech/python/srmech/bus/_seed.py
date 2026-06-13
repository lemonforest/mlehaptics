"""Seed-establishment sources for state-chained bus channels (rc3).

Three sources, in priority order (the higher source wins):

1. **Explicit argument** to :func:`srmech.bus.connect` /
   :func:`srmech.bus.serve` (``dna=b"..."``). Caller responsibility.
2. **Environment variable** ``SRMECH_BUS_SEED`` — hex-encoded 32+
   byte seed; both ends must have it set to the same value.
3. **0o600 discovery file** at ``~/.srmech/bus-{name}.seed``
   (binary 32 bytes). Server writes on :func:`serve` if neither
   explicit-arg nor env-var sources are populated; client reads on
   :func:`connect`. If no file exists either, the channel runs
   unencrypted (full rc2 back-compat).

This module is a pure-helper layer — no I/O is done implicitly;
callers explicitly request the resolution by calling
:func:`resolve_server_seed` or :func:`resolve_client_seed`.

Framework reading: the seed-resolution cascade is Class E (catalog
enumeration) over a three-element rationally-ordered catalog of
sources, with Class K (pin-slot) gating the boundary between "seed
found" and "back to unencrypted rc2 behavior". The 0o600 perms
attempt is Class K + Class C (sign-flip + re-orient) on the
filesystem-permission boundary.
"""

from __future__ import annotations

import logging
import os
import secrets
from pathlib import Path
from typing import Optional

from ._event import BUS_DIR_NAME, BUS_SOCK_PREFIX

logger = logging.getLogger("srmech.bus.seed")

#: Environment variable name for the cross-process seed override.
ENV_VAR: str = "SRMECH_BUS_SEED"

#: Filename suffix for the per-name binary-seed discovery file.
SEED_SUFFIX: str = ".seed"

#: Minimum acceptable seed length in bytes. 32 = SHA-256 block-aligned
#: input + matches the typical token width from
#: :func:`secrets.token_bytes`.
MIN_SEED_BYTES: int = 32


def _bus_dir() -> Path:
    """Local copy of :func:`srmech.bus._transport.bus_dir` to avoid
    circular import (transport imports _event; _seed only needs the
    dir-name constant)."""
    return Path.home() / BUS_DIR_NAME


def seed_path(name: str) -> Path:
    """Return the per-name seed discovery path:
    ``~/.srmech/bus-<name>.seed``."""
    return _bus_dir() / f"{BUS_SOCK_PREFIX}{name}{SEED_SUFFIX}"


def _read_env_seed() -> Optional[bytes]:
    """Read + validate the ``SRMECH_BUS_SEED`` env var.

    Returns the decoded bytes on success, ``None`` if the env var is
    unset / empty. Raises :class:`ValueError` on a non-hex value or
    a too-short seed.
    """
    hex_val = os.environ.get(ENV_VAR)
    if not hex_val:
        return None
    try:
        seed = bytes.fromhex(hex_val.strip())
    except ValueError as exc:
        raise ValueError(
            f"{ENV_VAR}: not a valid hex string: {exc}"
        ) from exc
    if len(seed) < MIN_SEED_BYTES:
        raise ValueError(
            f"{ENV_VAR}: seed too short ({len(seed)} < "
            f"{MIN_SEED_BYTES} bytes)"
        )
    return seed


def _read_file_seed(name: str) -> Optional[bytes]:
    """Read a per-name seed-file if present.

    Returns the bytes on success; ``None`` if the file does not
    exist. Raises :class:`ValueError` on a too-short file.
    """
    path = seed_path(name)
    if not path.exists():
        return None
    try:
        seed = path.read_bytes()
    except OSError as exc:
        logger.warning(
            "could not read seed file %s: %s — running unencrypted",
            path, exc,
        )
        return None
    if len(seed) < MIN_SEED_BYTES:
        raise ValueError(
            f"seed file {path}: too short ({len(seed)} < "
            f"{MIN_SEED_BYTES} bytes)"
        )
    return seed


def _write_file_seed(name: str, seed: bytes) -> Path:
    """Write a per-name seed file with 0o600 permissions.

    Idempotent: replaces any existing file at the same path. On
    POSIX, sets permissions to 0o600; on Windows, the equivalent
    ACL is left to the platform default (the file lives under
    ``%USERPROFILE%\\.srmech\\`` which is already user-private by
    default).
    """
    if len(seed) < MIN_SEED_BYTES:
        raise ValueError(
            f"seed too short ({len(seed)} < {MIN_SEED_BYTES} bytes)"
        )
    bus = _bus_dir()
    bus.mkdir(parents=True, exist_ok=True)
    path = seed_path(name)
    # Atomic-ish replace: write to tmp + rename.
    tmp = path.with_suffix(path.suffix + ".tmp")
    try:
        tmp.write_bytes(seed)
        try:
            os.chmod(str(tmp), 0o600)
        except OSError:
            pass
        os.replace(str(tmp), str(path))
    finally:
        try:
            if tmp.exists():
                tmp.unlink()
        except OSError:
            pass
    try:
        os.chmod(str(path), 0o600)
    except OSError:
        pass
    return path


def resolve_client_seed(
    name: str,
    *,
    explicit: Optional[bytes] = None,
) -> Optional[bytes]:
    """Resolve the client-side seed for the named channel.

    Priority (highest wins):
    1. ``explicit`` (caller-supplied)
    2. ``SRMECH_BUS_SEED`` env var
    3. ``~/.srmech/bus-<name>.seed`` discovery file
    4. None → unencrypted channel (rc2 back-compat)

    Returns the seed bytes or ``None``.
    """
    if explicit is not None:
        if len(explicit) < MIN_SEED_BYTES:
            raise ValueError(
                f"explicit seed too short ({len(explicit)} < "
                f"{MIN_SEED_BYTES} bytes)"
            )
        return bytes(explicit)
    env_seed = _read_env_seed()
    if env_seed is not None:
        return env_seed
    return _read_file_seed(name)


def resolve_server_seed(
    name: str,
    *,
    explicit: Optional[bytes] = None,
    write_discovery_file: bool = True,
) -> Optional[bytes]:
    """Resolve the server-side seed for the named channel.

    Priority (highest wins):
    1. ``explicit`` (caller-supplied)
    2. ``SRMECH_BUS_SEED`` env var
    3. ``~/.srmech/bus-<name>.seed`` discovery file (if pre-existing)
    4. None → unencrypted channel (rc2 back-compat)

    The server does NOT auto-generate a seed if none of the three
    sources fire — that would silently encrypt a channel with no
    way for the client to learn the seed. If callers want a fresh
    random seed published via the discovery file, they should
    explicitly call :func:`mint_and_write_seed` first.

    When ``write_discovery_file`` is True (default) and a seed was
    resolved from sources (1) or (2), write it to the discovery
    file so subsequent clients on the same machine can find it.
    """
    seed = resolve_client_seed(name, explicit=explicit)
    if seed is not None and write_discovery_file:
        try:
            _write_file_seed(name, seed)
        except (OSError, ValueError) as exc:
            logger.warning(
                "could not write seed file for %s: %s "
                "(channel still encrypted; clients on the same "
                "machine will need the env-var or explicit-arg "
                "source instead)",
                name, exc,
            )
    return seed


def mint_and_write_seed(name: str, *, n_bytes: int = MIN_SEED_BYTES) -> bytes:
    """Mint a fresh cryptographically-secure seed + write it to the
    per-name discovery file.

    Useful for the "I want encryption; auto-establish on first
    serve" pattern. Returns the freshly-minted seed bytes; the
    discovery file at ``~/.srmech/bus-<name>.seed`` now carries it
    with 0o600 permissions.
    """
    if n_bytes < MIN_SEED_BYTES:
        raise ValueError(
            f"n_bytes too short ({n_bytes} < {MIN_SEED_BYTES})"
        )
    seed = secrets.token_bytes(n_bytes)
    _write_file_seed(name, seed)
    return seed


def discard_seed_file(name: str) -> bool:
    """Best-effort unlink of the per-name seed discovery file.

    Returns True if a file was removed, False if no file existed or
    the unlink failed. The bus server can call this on
    :meth:`~srmech.bus._server.Endpoint.stop` to avoid leaving the
    seed on disk after the server shuts down (defensive scope:
    minimises the seed's at-rest exposure window).
    """
    path = seed_path(name)
    if not path.exists():
        return False
    try:
        path.unlink()
        return True
    except OSError as exc:
        logger.warning("could not unlink seed file %s: %s", path, exc)
        return False


__all__ = [
    "ENV_VAR",
    "MIN_SEED_BYTES",
    "SEED_SUFFIX",
    "discard_seed_file",
    "mint_and_write_seed",
    "resolve_client_seed",
    "resolve_server_seed",
    "seed_path",
]
