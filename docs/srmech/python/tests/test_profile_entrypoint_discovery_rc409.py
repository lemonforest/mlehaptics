"""rc409 (`#T1080`) — the REAL entry-point discovery path, end to end.

`tests/test_profile_loader.py` had five entry-point tests and **none of them
ever called `importlib.metadata.entry_points`**. Each replaces the WHOLE
`EntryPoint` object with a `types.SimpleNamespace(name=, value=, load=lambda:)`
and tests `_resolve_entry_point_toml` against it. That is a fine unit test of
the resolver; it is not a test of discovery. Census, basis named::

    git grep -c "MAX_ENUMERATED_PROFILES\\|ENTRY_POINT_GROUP\\|_enumerate_profiles" \\
        -- 'tests/*.py'
    -> ZERO references

So the machinery that finds a profile in the first place — the entry-point
group lookup, the enumeration loop, the smoke gate, the cache write, `Profile`
construction — had no coverage at all.

THE BLOCKER THAT WAS NOT ONE
============================
`tests/test_profile_loader.py` said, and had said for many rcs:

    "We can't easily exercise the full entry-point machinery in a unit test
     without pip-installing a fixture package"

**That is false, and this file is the refutation by execution.** A hand-written
``fakeprof-1.0.0.dist-info/`` containing `METADATA` + `entry_points.txt`, on a
directory placed on `sys.path`, drives the entire real path: discovery ->
resolve -> validate -> smoke -> cache -> `Profile`. Standard library only. No
pip, no network, no install step. The docstring is corrected in the same commit
as this file lands — **a cost had been written into the tree as a blocker**, and
left there it would keep deterring the next person from writing this test.

THE VACUOUS-PASS TRAP, WHICH IS WHY THE FIXTURE DECLARES A BRIDGE
================================================================
`_run_smoke_test` returns ``("passed", "", 0)`` for a profile that declares
neither a bridge nor catalogs — it counts assertions, and with nothing to check
it counts zero and reports success. A minimal descriptor therefore sails
through the smoke gate **without the gate ever having tested anything**, and a
test built on that fixture would assert `status == "ok"` while proving nothing.
This fixture declares a real bridge surface and asserts ``n_assertions > 0``, so
the gate is measured doing work.

EVERY INSTRUMENT HERE HAS A NEGATIVE CONTROL
============================================
`test_discovery_returns_nothing_when_the_group_is_wrong` renames the entry-point
group and re-runs the identical machinery, which must then find nothing. Without
it, all of the assertions below would also pass against a loader that hallucinated
the profile from the cache, or against a `sys.path` entry that happened to work
for an unrelated reason.
"""

from __future__ import annotations

import importlib
import importlib.metadata
import sys
from pathlib import Path

import pytest

import srmech.introspect.tool_schema as ts
from srmech import profile_loader as pl

_PROFILE_TOML = """\
profile_schema_version = "1.0"

[profile]
name = "fakeprof"
version = "1.0.0"
summary = "rc409 discovery fixture"
package = "fakeprof_pkg"
srmech_requires = ">=0.9"

# A REAL bridge surface. Without at least one of these the smoke gate counts
# zero assertions and returns "passed" vacuously -- see the module docstring.
# `json:dumps` is stdlib, importable and callable, so the gate genuinely
# resolves something rather than being handed a stub.
[profile.bridge]
render = "json:dumps"
"""

_ENTRY_POINTS_TXT = """\
[srmech.profiles]
fakeprof = fakeprof_pkg
"""

_METADATA = """\
Metadata-Version: 2.1
Name: fakeprof
Version: 1.0.0
Summary: rc409 discovery fixture
"""


def _build_distribution(root: Path, group: str = "srmech.profiles") -> None:
    """Write a real importable package + a real ``.dist-info`` under ``root``.

    This is exactly what `pip install` would leave on disk for a package
    declaring a ``srmech.profiles`` entry point — written by hand, because the
    only parts `importlib.metadata` needs are these two files.
    """
    pkg = root / "fakeprof_pkg"
    pkg.mkdir(parents=True, exist_ok=True)
    (pkg / "__init__.py").write_text("", encoding="utf-8")
    (pkg / "srmech_profile.toml").write_text(_PROFILE_TOML, encoding="utf-8")

    dist = root / "fakeprof-1.0.0.dist-info"
    dist.mkdir(parents=True, exist_ok=True)
    (dist / "METADATA").write_text(_METADATA, encoding="utf-8")
    (dist / "entry_points.txt").write_text(
        _ENTRY_POINTS_TXT.replace("srmech.profiles", group), encoding="utf-8")


@pytest.fixture
def installed_profile(tmp_path, monkeypatch):
    """A discoverable profile on `sys.path`, fully torn down afterwards.

    Isolation, each piece load-bearing:

    * ``SRMECH_PROFILE_CACHE_DIR`` -> tmp. `profile_loader._cache_dir` honours
      it; without it the smoke cache is written into the developer's real
      ``~/.cache/srmech/profile_smoke_tests/``.
    * ``reset_for_testing()`` BEFORE and AFTER. `_ENUMERATION` is a memoized
      module global, so a stale value makes discovery return the previous
      answer and the test passes without exercising anything.
    * ``invalidate_caches()``. `importlib.metadata` caches directory listings;
      a brand-new ``.dist-info`` is invisible without this.
    * `_REGISTRY` snapshot. `Profile.__init__` can register tool entries, and
      `tool_schema._REGISTRY` has no autouse restore in `conftest.py`.
    """
    def _make(group: str = "srmech.profiles") -> Path:
        root = tmp_path / group.replace(".", "_")
        _build_distribution(root, group=group)
        monkeypatch.syspath_prepend(str(root))
        importlib.invalidate_caches()
        pl.reset_for_testing()
        return root

    monkeypatch.setenv("SRMECH_PROFILE_CACHE_DIR", str(tmp_path / "cache"))
    registry_snapshot = dict(ts._REGISTRY)
    pl.reset_for_testing()
    try:
        yield _make
    finally:
        pl.reset_for_testing()
        sys.modules.pop("fakeprof_pkg", None)
        ts._REGISTRY.clear()
        ts._REGISTRY.update(registry_snapshot)


# ── the real path, one stage at a time ────────────────────────────────


def test_entry_point_group_is_actually_queried(installed_profile) -> None:
    """`importlib.metadata.entry_points(group=ENTRY_POINT_GROUP)` — untested
    until rc409. This is the stage all five existing tests stub past."""
    installed_profile()
    eps = importlib.metadata.entry_points(group=pl.ENTRY_POINT_GROUP)
    assert [(e.name, e.value) for e in eps] == [("fakeprof", "fakeprof_pkg")]


def test_enumeration_finds_the_installed_profile(installed_profile) -> None:
    """`_enumerate_profiles()` over a REAL entry point, not a SimpleNamespace."""
    installed_profile()
    assert "fakeprof" in pl._enumerate_profiles()


def test_list_profiles_reports_ok(installed_profile) -> None:
    """Discovery -> resolve -> validate -> smoke, surfaced through the public API."""
    installed_profile()
    statuses = pl.list_profiles()
    assert "fakeprof" in statuses
    assert statuses["fakeprof"].status == "ok", statuses["fakeprof"].diagnostic


def test_smoke_gate_actually_asserted_something(installed_profile) -> None:
    """THE VACUITY GUARD, and the reason the fixture declares a bridge.

    `_run_smoke_test` returns ``("passed", "", 0)`` when a profile declares no
    bridge and no catalogs — it passes by having nothing to check. Asserting
    ``status == "passed"`` alone would therefore prove nothing at all. Pin the
    assertion COUNT so the gate is measured doing work.
    """
    installed_profile()
    descriptor = pl._enumerate_profiles()["fakeprof"]
    status, failure, n_assertions = pl._run_smoke_test(descriptor)
    assert status == "passed", failure
    assert n_assertions > 0, (
        "the smoke gate passed with ZERO assertions - it checked nothing and "
        "this fixture has become the vacuous one the docstring warns about")


def test_profile_activates_and_binds_its_bridge(installed_profile) -> None:
    """`profile()` end to end: the activation body + a usable bridge surface."""
    installed_profile()
    p = pl.profile("fakeprof")
    assert (p.name, p.version) == ("fakeprof", "1.0.0")
    # The bridge resolved to the real stdlib callable and is invocable.
    assert p.render({"rc": 409}) == '{"rc": 409}'


def test_the_smoke_cache_is_written(installed_profile) -> None:
    """`_write_smoke_cache` — reached only through the real activation path."""
    installed_profile()
    pl.profile("fakeprof")
    cached = pl._read_smoke_cache("fakeprof", "1.0.0")
    assert cached is not None, "activation did not write a smoke cache entry"


# ── the negative control ──────────────────────────────────────────────


def test_discovery_returns_nothing_when_the_group_is_wrong(
        installed_profile) -> None:
    """THE INSTRUMENT MUST BE ABLE TO RETURN OTHERWISE.

    Identical fixture, identical machinery, one changed string: the entry point
    is declared under a group srmech does not read. Everything above must go
    quiet. Without this, every assertion in this file would also pass against a
    loader that never looked at `sys.path` at all.
    """
    installed_profile(group="srmech.NOT_profiles")
    assert list(importlib.metadata.entry_points(group=pl.ENTRY_POINT_GROUP)) == []
    assert "fakeprof" not in pl._enumerate_profiles()
    assert "fakeprof" not in pl.list_profiles()
    with pytest.raises(pl.ProfileNotFoundError):
        pl.profile("fakeprof")
