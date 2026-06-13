"""SSoT helper: derive the bus connection-secret keyword from the live API
signature instead of hardcoding its name in every caller.

The per-channel pre-shared secret is passed to :func:`srmech.bus.connect` /
:func:`srmech.bus.serve` under a keyword (``dna`` as of the Bio-TOTP rename,
UTLP Claim 255). Any caller that resolves a secret *dynamically* — the
``srmech bus`` CLI, third-party tooling reading the :mod:`srmech.bus._seed`
discovery cascade — should NOT spell that keyword itself: a rename of the
parameter would then silently break every such caller (it did once: the
``seed`` → ``dna`` rename broke the CLI because it hardcoded ``seed=``).

:func:`secret_kwargs` reads the keyword off ``connect``'s **signature**, so the
function definition is the single source of truth and a rename propagates with
no caller edits. ``connect`` / ``serve`` / the ``aio`` twins all share the
secret keyword (guarded by ``test_bus_secret_kwarg_ssot``), so one derivation
is valid for every entry point.
"""
from __future__ import annotations

import inspect
import typing
from typing import Dict, Optional


def _secret_param_name(fn: typing.Callable) -> str:
    """Name of ``fn``'s per-channel pre-shared-secret parameter.

    Identified as the sole keyword parameter typed ``Optional[bytes]`` — the
    role-anchor, not the name — so a rename of the parameter is invisible here.
    Resolves string annotations (``from __future__ import annotations``) via
    :func:`typing.get_type_hints`. Raises if the secret cannot be identified
    unambiguously (zero or several ``Optional[bytes]`` keywords), so an API
    change that breaks the assumption fails loudly rather than silently
    picking the wrong keyword.
    """
    assert callable(fn), "fn must be callable"
    hints = typing.get_type_hints(fn)
    matches = [
        name
        for name, param in inspect.signature(fn).parameters.items()
        if param.kind in (param.KEYWORD_ONLY, param.POSITIONAL_OR_KEYWORD)
        and hints.get(name) == Optional[bytes]
    ]
    if len(matches) != 1:
        raise RuntimeError(
            f"cannot derive the bus pre-shared-secret keyword from "
            f"{fn.__name__}{inspect.signature(fn)}: expected exactly one "
            f"Optional[bytes] keyword parameter, found {matches!r}"
        )
    return matches[0]


def secret_kwargs(secret: Optional[bytes]) -> Dict[str, bytes]:
    """The :func:`connect` / :func:`serve` keyword arguments that carry a
    resolved per-channel pre-shared ``secret``, keyed by whatever the live API
    signature names that parameter (**SSoT** — derived, never hardcoded).

    Returns ``{}`` when ``secret`` is ``None`` (no encryption requested), so a
    caller can always splat it: ``connect(name, **secret_kwargs(secret))``.
    """
    assert secret is None or isinstance(secret, (bytes, bytearray)), (
        "secret must be bytes or None"
    )
    if secret is None:
        return {}
    from ._client import connect  # lazy import → no package import cycle

    return {_secret_param_name(connect): bytes(secret)}
