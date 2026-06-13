"""SSoT: the bus connection-secret keyword is derived from the live API
signature, never hardcoded by callers.

The ``seed`` → ``dna`` rename once broke the ``srmech bus`` CLI because the CLI
spelled ``seed=`` by hand. :func:`srmech.bus.secret_kwargs` now reads the
keyword off :func:`srmech.bus.connect`'s signature, so a rename propagates to
every dynamic caller (the CLI included) with no edits — these tests lock that
contract.
"""
from __future__ import annotations

import inspect
from typing import Optional

import pytest

import srmech.bus as bus
from srmech.bus._params import _secret_param_name, secret_kwargs


def test_secret_kwargs_none_is_empty():
    assert secret_kwargs(None) == {}


def test_secret_kwargs_keyed_by_live_connect_signature():
    secret = b"k" * 32
    kw = secret_kwargs(secret)
    (name, value), = kw.items()           # exactly one kwarg
    assert value == secret
    # …named whatever connect's signature currently calls the secret
    assert name in inspect.signature(bus.connect).parameters


def test_connect_serve_aio_share_the_secret_keyword():
    # one derivation (against connect) is valid for every entry point the CLI
    # passes a secret to — so the CLI can splat the same dict into both.
    from srmech.bus import aio

    name, = secret_kwargs(b"x" * 32)
    for fn in (bus.connect, bus.serve, aio.connect, aio.serve):
        assert name in inspect.signature(fn).parameters, (fn.__name__, name)


def test_derivation_follows_a_rename():
    # The SSoT proof: rename the secret parameter and the derivation follows
    # it with NO caller edit — exactly the failure the CLI hit at seed→dna.
    def connect_renamed(
        name: str, *, queue: int = 8, secret_material: Optional[bytes] = None
    ):
        ...

    assert _secret_param_name(connect_renamed) == "secret_material"


def test_ambiguous_or_missing_secret_fails_loudly():
    # Two bytes-typed keywords → ambiguous → raise (never silently guess).
    def two_secrets(
        name: str, *, a: Optional[bytes] = None, b: Optional[bytes] = None
    ):
        ...

    with pytest.raises(RuntimeError):
        _secret_param_name(two_secrets)

    # No bytes-typed keyword → raise.
    def no_secret(name: str, *, count: int = 0):
        ...

    with pytest.raises(RuntimeError):
        _secret_param_name(no_secret)


def test_cli_does_not_hardcode_the_secret_keyword():
    # Ratchet: the bus CLI must route the secret through secret_kwargs(), never
    # spell connect(dna=...) / serve(dna=...) by hand again.
    from srmech.cli import bus as cli_bus

    src = inspect.getsource(cli_bus)
    assert "secret_kwargs(" in src
    assert "dna=" not in src, "bus CLI hardcodes the secret keyword again"
