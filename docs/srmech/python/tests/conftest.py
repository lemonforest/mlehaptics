"""Shared pytest fixtures for srmech tests.

Each fixture builds a minimal self-contained descriptor.toml so the
tests don't depend on any external catalog SSOT (ephemerides-spectral
or otherwise). The shape mirrors the real EarthRef SC descriptor so
the html_scraper parse test exercises the same field-map structure.
"""

from __future__ import annotations

import os as _os
import shutil as _shutil
import sys as _sys
import tempfile as _tempfile
from array import array as _stdlib_array
from pathlib import Path
from typing import Any, List

import pytest


# ──────────────────────────────────────────────────────────────────────
# rc283 — the bus registry dir is a PROCESS-EXTERNAL SINGLETON; give each
# bus test module its own.
#
# `srmech.bus` registers endpoints at `~/.srmech/bus-<name>.sock` — a fixed
# HOME-based path, shared by every process on the box, xdist workers included.
# Endpoint NAMES are uuid-unique, so this is not a name collision; the shared
# thing is the DIRECTORY. `list_endpoints(cleanup_dead=True)` scans that whole
# directory and DELETES any endpoint it judges dead — and a socket that is bound
# but not yet accepting is indistinguishable from a dead one. So worker A's
# discovery sweep silently unlinks worker B's in-flight socket, and B then fails
# with `FileNotFoundError: no bus endpoint ...` or `BusError: reader exited;
# peer closed`. Observed exactly that way: `-n 4` run 1 was green, run 2 failed
# two `test_bus_aio.py` tests — an intermittent cross-worker race, not an
# ordering bug and not a product defect (the sweep is behaving as designed).
#
# Fix by REMOVING the singleton rather than serialising around it: point HOME
# (and USERPROFILE, for the Windows cell, where `Path.home()` reads that
# instead) at a private temp dir per bus module. `bus_dir()` resolves
# `Path.home()` at call time, so the redirect reaches the library and any
# subprocess that inherits the environment. This is preferred over an
# `xdist_group` pin, which would have forced the bus files onto one worker and
# given up their parallelism to work around a resource we can simply
# un-share.
#
# MODULE scope, not function scope, is deliberate: within one module the tests
# keep sharing a bus dir exactly as they do today (each cleans up its own
# endpoint via the `unique_name` fixture), so intra-module semantics are
# unchanged. Only the CROSS-worker sharing is removed.
# ──────────────────────────────────────────────────────────────────────

#: Test modules that create real on-disk bus endpoints. Verified by grepping
#: `sock_path` / `registry_path` / `bus_dir` / `seed_path` across `tests/` —
#: every other bus-adjacent module only inspects names or classifications and
#: never writes into the registry dir.
_BUS_REGISTRY_TEST_MODULES = {
    "test_bus", "test_bus_aio",
    # rc305 (`#920`) — the discovery-cleanup root-fix regression module binds
    # raw UDS sockets in the registry dir, so it needs the same private HOME.
    "test_bus_discovery_cleanup_rc305",
}

#: Longest endpoint NAME the bus suites build, with headroom.
#:
#: Worst case in the tree is `test_bus_aio`'s piped endpoint:
#:     f"aio-test-{uuid4().hex[:12]}" + "-sink"   = 9 + 12 + 5 = 26 chars
#: `test_bus`'s sync equivalent is 22 (`f"test-{...}"` + "-sink"). The `-src` /
#: `-sink` suffixes are IDENTICAL in both files — it is the async module's
#: `aio-` name prefix, not a longer suffix, that makes it the worst case. This
#: is exactly the endpoint that overflowed on macos-14 in CI
#: (`test_async_pipe_forwards_broadcasts`).
#:
#: Budgeted at 48, well above the current 26, so that adding a longer endpoint
#: name later cannot silently re-introduce the overflow — the assertion below
#: is checked against THIS budget, not against today's names.
_BUS_MAX_ENDPOINT_NAME = 48

#: Bytes the registry dir + filename add around that name:
#: `<home>` + `/.srmech/` + `bus-` + <name> + `.sock` (`.seed` is the same
#: length; `.txt` is shorter, and is Windows-only where AF_UNIX is not used).
_BUS_PATH_RESERVE = (
    len("/.srmech/") + len("bus-") + _BUS_MAX_ENDPOINT_NAME + len(".sock")
)


def _sun_path_cap() -> int:
    """Size of ``sockaddr_un.sun_path`` on this platform, in bytes.

    PLATFORM-SPECIFIC and NOT interchangeable: **108** on Linux
    (`/usr/include/.../sys/un.h`), **104** on macOS/BSD (XNU `bsd/sys/un.h`).
    Anything unrecognised gets the TIGHTER value — an over-strict cap costs a
    readable fixture error, an over-loose one costs an opaque `OSError` deep
    inside a bus test five minutes into a CI run.
    """
    return 108 if _sys.platform.startswith("linux") else 104


def _bus_home_base() -> str:
    """Pick a temp base whose longest endpoint path fits ``sun_path``.

    Prefers the platform default (so `TMPDIR` is respected wherever it fits —
    on Linux `gettempdir()` is already `/tmp`, so this is not a change there),
    and falls back to `/tmp` only when the default would overflow.

    That fallback is what macos-14 needs: GitHub's macOS runners set `TMPDIR`
    to the per-user `/var/folders/<xx>/<~30 chars>/T/` form (48 chars —
    confirmed from the failing job's own log), and 48 + `mkdtemp` (12) +
    `/.srmech/bus-aio-test-<12hex>-sink.sock` (44) = **104**, against a 104-byte
    cap whose last byte is the NUL. It overflowed by exactly one.

    `/tmp` is safe here, not merely short: POSIX requires it to exist and be
    writable, `mkdtemp` creates our directory mode 0700 so privacy does not
    depend on the parent's permissions, and on macOS — where `/tmp` is a
    symlink to `/private/tmp` — the kernel length-checks the `sun_path` bytes
    we actually pass, so the 4-char form is what counts (and even the resolved
    12-char `/private/tmp` would still fit with room to spare).
    """
    candidates = [_tempfile.gettempdir()]
    if _os.name == "posix" and "/tmp" not in candidates:
        candidates.append("/tmp")

    cap = _sun_path_cap()
    for base in candidates:
        # `mkdtemp` adds `/` + prefix + 8 random chars.
        projected = len(base) + 1 + len("srb") + 8 + _BUS_PATH_RESERVE
        if not _os.path.isdir(base):
            continue
        if _os.name != "posix" or projected < cap:
            return base

    raise AssertionError(
        "no usable temp base for the private bus registry dir: the longest "
        "endpoint path would exceed this platform's AF_UNIX sun_path cap of "
        f"{cap} bytes on every candidate. Tried: "
        + ", ".join(f"{b!r} (projected {len(b) + 12 + _BUS_PATH_RESERVE})"
                    for b in candidates)
        + ". Set TMPDIR to a shorter directory, or shorten "
          "_BUS_MAX_ENDPOINT_NAME if the endpoint names really are shorter."
    )


@pytest.fixture(autouse=True, scope="module")
def _private_bus_registry_home(request):
    """Give each bus-endpoint test module a private `~/.srmech/`."""
    mod = request.module.__name__.rsplit(".", 1)[-1]
    if mod not in _BUS_REGISTRY_TEST_MODULES:
        yield
        return

    # NOT `tmp_path_factory`: its nested dirs
    # (`<tmp>/pytest-of-<user>/pytest-<n>/<module><n>/`) overflow sun_path on
    # their own, before any TMPDIR question. A short `mkdtemp` under a base
    # chosen by `_bus_home_base()` keeps the whole endpoint path inside the cap.
    home = _tempfile.mkdtemp(prefix="srb", dir=_bus_home_base())

    # Make the length invariant EXPLICIT and LOUD. Without this, an environment
    # with a long TMPDIR does not fail here — it fails minutes later, inside one
    # bus test, as a bare `OSError: AF_UNIX path too long` with no indication of
    # which path or which limit. That is precisely how this reached CI.
    cap = _sun_path_cap()
    worst_path = _os.path.join(
        home, ".srmech", "bus-" + ("x" * _BUS_MAX_ENDPOINT_NAME) + ".sock"
    )
    if _os.name == "posix":
        assert len(worst_path) < cap, (
            "private bus registry dir would overflow this platform's AF_UNIX "
            f"sun_path cap: cap={cap} bytes (usable {cap - 1}), longest "
            f"endpoint path={len(worst_path)} bytes.\n"
            f"  path: {worst_path}\n"
            f"  base: {home!r} ({len(home)} bytes)\n"
            f"  reserve: {_BUS_PATH_RESERVE} bytes "
            f"(/.srmech/ + bus- + {_BUS_MAX_ENDPOINT_NAME}-char name + .sock)\n"
            "Bind would fail later as an opaque 'OSError: AF_UNIX path too "
            "long' inside a bus test; failing here instead."
        )

    saved = {k: _os.environ.get(k) for k in ("HOME", "USERPROFILE")}
    _os.environ["HOME"] = home
    _os.environ["USERPROFILE"] = home
    try:
        yield
    finally:
        for key, val in saved.items():
            if val is None:
                _os.environ.pop(key, None)
            else:
                _os.environ[key] = val
        _shutil.rmtree(home, ignore_errors=True)


# ──────────────────────────────────────────────────────────────────────
# rc283 — signal_processing path-registry LEAK GUARD (order-independence).
#
# `srmech.signal_processing.path_registry.clear_registry()` is a destructive
# PROCESS-GLOBAL wipe, documented as a "test-isolation utility" — but it has
# no restore, and several tests (notably `test_signal_processing_scaffolding`,
# which calls it ~10× including in `finally:` blocks) leave the registry EMPTY
# when they finish. The eager registrations it destroys — `rfft`/`fft`/`ifft`/
# `pi_cascade`/`hdc_truncation` (registered by importing
# `srmech.signal_processing.path_b_ops`) and the `rbs_hdc_*` ops — do NOT come
# back on their own: those modules are already in `sys.modules`, so nothing
# re-imports and nothing re-registers. `_ensure_loaded()` cannot help either,
# because rfft has no lazy loader (it is eagerly imported).
#
# Serial runs hid this purely by alphabetical luck: `..._rfft.py` sorts BEFORE
# `..._scaffolding.py`, so the wipe happened after the tests that depend on the
# registrations. Under xdist, file→worker assignment is arbitrary, so a worker
# can run scaffolding first and the dependent tests then fail. The dependency
# is on TEST ORDER, not on xdist — `pytest tests/test_signal_processing_scaffolding.py
# tests/test_signal_processing_rfft.py` reproduces it serially.
#
# This fixture snapshots the registry before each test and restores it after,
# so no test can leak a wipe (or a stray registration) into any other. It makes
# the suite genuinely order-independent rather than accidentally-ordered. Cost
# is a dict copy of ~50 entries per test.
#
# `test_signal_processing_path_b_core.py` carries a hand-rolled version of this
# workaround (it re-runs `_register_path_b_core_ops()` defensively); that older
# local patch stays valid and harmless under this guard.
# ──────────────────────────────────────────────────────────────────────


@pytest.fixture(autouse=True)
def _restore_signal_processing_path_registry():
    """Snapshot/restore the signal_processing path registry around every test."""
    try:
        from srmech.signal_processing import path_registry as _reg
    except Exception:  # pragma: no cover - package unavailable in a slim env
        yield
        return

    saved = dict(_reg._REGISTRY)
    saved_lazy = dict(_reg._LAZY_LOADERS)
    try:
        yield
    finally:
        _reg._REGISTRY.clear()
        _reg._REGISTRY.update(saved)
        _reg._LAZY_LOADERS.clear()
        _reg._LAZY_LOADERS.update(saved_lazy)


# ──────────────────────────────────────────────────────────────────────
# rc131 — shared return-type AGREEMENT helper (used by both the immolation
# gate `test_immolation.py` and the §10.1 every-tool smoke `test_mcp.py`).
# Lives here so neither test module has to import the other (no cross-test
# import cycle). Carrier-aware: the advertised `returns.type` string is a
# possibly-union (`A | B`), possibly-parameterised (`tuple[Mat, Vec, Mat]`)
# handle; we check the RAW return matches AT LEAST ONE arm of the union.
# ──────────────────────────────────────────────────────────────────────

_SCALAR_TOKENS = {
    "complex": complex,
    "float": float,
    "int": int,
    "bool": bool,
    "str": str,
    "bytes": bytes,
}


def _tuple_elem_types(arm: str):
    """For a ``tuple[...]`` arm, the element-type tokens, or ``None`` if not a
    parameterised tuple. ``tuple[Mat, ...]`` → ``['Mat', '...']``."""
    arm = arm.strip()
    if not (arm.startswith("tuple[") and arm.endswith("]")):
        return None
    inner = arm[len("tuple["):-1]
    depth = 0
    parts: List[str] = []
    cur = ""
    for ch in inner:
        if ch == "[":
            depth += 1
        elif ch == "]":
            depth -= 1
        if ch == "," and depth == 0:
            parts.append(cur.strip())
            cur = ""
        else:
            cur += ch
    if cur.strip():
        parts.append(cur.strip())
    return parts


def _matches_token(raw: Any, token: str):
    """Does ``raw`` match ONE simple advertised type token (carrier-aware)?
    Returns ``True`` / ``False``, or ``None`` if the token is not assertable."""
    # Lazy import so conftest stays cheap and srmech-load-order clean.
    from srmech.math.mat import Mat
    from srmech.math.vec import Vec
    from srmech.math.hv import HV
    from srmech.math.q import Q
    from srmech.math.complex128 import Complex128

    token = token.strip()
    if token == "...":
        return True
    if token.startswith("Mat"):
        return isinstance(raw, Mat)
    if token.startswith("Vec"):
        return isinstance(raw, Vec)
    if token.startswith("HV"):
        return isinstance(raw, HV)
    # Scalar carriers (v0.9.0): Q (exact rational) + Complex128 (float-complex),
    # the scalar peers of the Mat/Vec/HV array carriers. Checked before the
    # plain `complex`/`float` scalar tokens so an exact `Q` return is verified
    # as a `Q`, not skipped (F868 stay-rational return-type discipline).
    if token.startswith("Complex128"):
        return isinstance(raw, Complex128)
    # Exact polynomial carriers (rc113 — the q-row prose constructors RETURN
    # these). QPoly / QBiPoly MUST be checked before the bare "Q" scalar token
    # (the startswith prefix would otherwise mis-route them to the Q
    # isinstance); Poly gets its own genuine check too (it was previously an
    # unassertable None-skip).
    if token.startswith("QBiPoly"):
        from srmech.math.qbipoly import QBiPoly
        return isinstance(raw, QBiPoly)
    if token.startswith("QPoly"):
        from srmech.math.qpoly import QPoly
        return isinstance(raw, QPoly)
    if token.startswith("Poly"):
        from srmech.math.poly import Poly
        return isinstance(raw, Poly)
    if token.startswith("Q"):
        return isinstance(raw, Q)
    if token.startswith("array"):
        return isinstance(raw, _stdlib_array)
    if token.startswith("tuple"):
        elems = _tuple_elem_types(token)
        if not isinstance(raw, tuple):
            return False
        if elems is None:
            return True
        if len(elems) == 2 and elems[1] == "...":
            return all(_matches_token(e, elems[0]) for e in raw)
        if len(elems) != len(raw):
            return False
        return all(_matches_token(e, t) for e, t in zip(raw, elems))
    if token.startswith("list"):
        return isinstance(raw, list)
    if token.startswith("dict") or token.startswith("Mapping"):
        return isinstance(raw, dict)
    for tok, ty in _SCALAR_TOKENS.items():
        if token.startswith(tok):
            if tok == "int":
                return isinstance(raw, int) and not isinstance(raw, bool)
            return isinstance(raw, ty)
    return None


def return_type_agrees(raw: Any, advertised: str):
    """True/False if ``type(raw)`` (dis)agrees with the advertised type; ``None``
    when no arm of the advertised union carries an assertable token (so the
    caller skips — never a false failure on an unknown handle type)."""
    arms = [a.strip() for a in advertised.split("|")]
    # A ``None`` return against a MULTI-ARM ``X | None`` union agrees iff a ``None``
    # arm is present — a decision op (gosper / zeilberger / wz_certificate) returns
    # ``None`` when no result exists, and that must verify against ``dict | None``
    # instead of failing on the sibling ``dict`` arm (which reports False for None).
    # Scoped to the union case so a sole ``None``-advertised op is unaffected.
    if raw is None and len(arms) > 1 and any(a in ("None", "NoneType") for a in arms):
        return True
    any_assertable = False
    for arm in arms:
        m = _matches_token(raw, arm)
        if m is None:
            continue
        any_assertable = True
        if m:
            return True
    return False if any_assertable else None


# ──────────────────────────────────────────────────────────────────────
# rc106 — FORCED pure-Python riemann-theta path (the honest
# "pure_python_alone" mechanism). Before rc106 the theta test files'
# ``test_pure_python*alone*`` tests re-ran the DISPATCHED path under a
# pure-sounding name (no monkeypatch — on a native host they exercised
# the C peers again; on a no-C host they duplicated the primary gate
# byte-for-byte). This helper makes the claim real: every
# ``has_native_riemann_theta*`` availability gate is monkeypatched to
# ``False`` (so every carrier dispatch falls to the COMPLETE pure body)
# AND every ``riemann_theta*_c`` native binding is replaced by a sentinel
# that RECORDS + RAISES — the proof the pure body alone ran is that the
# test passes at all (a native hit would fail it loudly).
# ──────────────────────────────────────────────────────────────────────

def riemann_theta_force_pure(mp: "pytest.MonkeyPatch") -> List[str]:
    """Monkeypatch (via ``mp``) the ENTIRE riemann-theta native surface OFF.

    Returns the (initially empty) list the sentinel appends to — after the
    pure-path work, assert it is still empty (``assert hits == []``)."""
    from srmech import _native as _n

    hits: List[str] = []

    def _gate_off() -> bool:
        return False

    def _make_sentinel(symbol: str):
        def _sentinel(*_a, **_k):
            hits.append(symbol)
            raise AssertionError(
                f"native {symbol} was invoked on the FORCED pure riemann-theta "
                f"path — the pure-python-alone claim would be false")
        return _sentinel

    for name in dir(_n):
        if name.startswith("has_native_riemann_theta"):
            mp.setattr(_n, name, _gate_off)
        elif name.startswith("riemann_theta") and name.endswith("_c"):
            mp.setattr(_n, name, _make_sentinel(name))
    return hits


@pytest.fixture
def pure_riemann_theta(monkeypatch) -> List[str]:
    """Function-scoped forced-pure riemann-theta path (see
    :func:`riemann_theta_force_pure`). Yields the sentinel hit-list; the
    teardown re-asserts no native symbol was ever reached."""
    hits = riemann_theta_force_pure(monkeypatch)
    yield hits
    assert hits == [], f"native riemann-theta symbols invoked: {hits}"

# Mirror of EarthRef SC's html_scraper descriptor — self-contained,
# usable from tmp_path without touching any external catalog.
_HTML_SCRAPER_DESCRIPTOR_TOML = """\
[source]
key = "fixture_sc"
human_readable_name = "Fixture Seamount Catalog"
purpose = "fixture ground-proof rows for srmech tests"
license = "CC-BY-4.0"
homepage = "https://example.com/SC/"
canonical_doi = "10.1029/test"

[fetch]
adapter = "html_scraper"
endpoint = "https://example.com/SC/catalog?page={page}"
rate_limit_rps = 0.5
robots_txt_compliant = true

[fetch.pagination]
type = "page_query"
start = 1
end_detected_by = "empty_page"

[parse]
table_selector = "table.sc_main"
row_selector = "tr.sc_row"
field_map = [
    { canonical = "name",          selector = "td.name",  type = "string" },
    { canonical = "latitude_deg",  selector = "td.lat",   type = "float"  },
    { canonical = "longitude_deg", selector = "td.lon",   type = "float"  },
    { canonical = "summit_depth_m", selector = "td.depth", type = "float" },
    { canonical = "summit_height_m", selector = "td.height", type = "float" },
]

[schema]
data_schema_id = "fixture_sc.seamount.v1"
data_schema_path = "seamount.schema.json"

[rendering]
cite_as_template = "Fixture Catalog; retrieved {retrieved_at:%Y-%m-%d}."
purpose_template = "fixture ground-proof row for {schema.regime_label} regime"

[attestation]
hash_response = true
hash_algorithm = "sha256"
required_fields = [
    "source_doi",
    "source_url",
    "license",
    "retrieved_at",
    "response_sha256",
    "parser_version",
    "parser_rule_hash",
    "collector_descriptor_path",
    "collector_descriptor_hash",
]

[gap_targeting]
regime_labels = ["bounded_local_laplacian_trajectory"]
"""


@pytest.fixture
def html_scraper_descriptor_path(tmp_path: Path) -> Path:
    """A self-contained html_scraper descriptor at
    ``tmp_path / "fixture_sc" / "descriptor.toml"``.

    Mirrors EarthRef SC's shape so the html_scraper parse test
    exercises the same five-field-map structure as in production.
    """
    catalog_dir = tmp_path / "fixture_sc"
    catalog_dir.mkdir()
    desc_path = catalog_dir / "descriptor.toml"
    desc_path.write_text(_HTML_SCRAPER_DESCRIPTOR_TOML, encoding="utf-8")
    return desc_path


@pytest.fixture
def attested_root_with_one_catalog(tmp_path: Path) -> Path:
    """A complete attested-root directory with one descriptor in it,
    suitable for `register_attested_root` tests.
    """
    catalog_dir = tmp_path / "fixture_sc"
    catalog_dir.mkdir()
    desc_path = catalog_dir / "descriptor.toml"
    desc_path.write_text(_HTML_SCRAPER_DESCRIPTOR_TOML, encoding="utf-8")
    return tmp_path


# ──────────────────────────────────────────────────────────────────────
# rc170 — SHARED Rosetta transitive call-graph walk (the "standalone-C
# reachability" machinery). Lives here so BOTH the completeness ratchet
# (test_rosetta_completeness.py, the rc170 non_compute composes_c assert)
# and the transitive-standalone ratchet (test_rosetta_transitive_standalone.py)
# can walk the SAME callee graph without a cross-test import (tests/ is a
# package, so bare `import test_<sibling>` fails — `from conftest import` is
# the project's proven shared-helper path, cf. return_type_agrees /
# riemann_theta_force_pure above).
#
# The walk: from a function object, follow the srmech callables it references
# (through its globals AND function-local imports, and through
# `Class().method()` attribute calls), transitively, treating a
# c_dispatched / composition_of_c / non_compute LEDGER op as a LEAF (C-backed
# or validated-elsewhere — don't recurse into its fallback). Returns the set
# of ledger `defined_at` keys reached. A composition/non_compute op that
# reaches a NOT-READY leaf (python_only_debt / bignum_reference /
# c_exists_unbound) is hiding a Python kernel it claims not to.
# ──────────────────────────────────────────────────────────────────────

import ast as _ast
import importlib as _importlib
import inspect as _inspect
import json as _json
import pkgutil as _pkgutil
import textwrap as _textwrap

_ROSETTA_FIXTURE = Path(__file__).resolve().parent / "rosetta_classification.ndjson"

# rc361 (`#T1034`) — the walk roots are SINGLE-SOURCED in tests/rosetta_roots.py.
# They used to be a hardcoded 12-tuple here AND in test_rosetta_completeness.py
# AND in test_rosetta_transitive_standalone.py AND in notes/_rosetta_inventory.py,
# each carrying a comment asking the next author to keep all four in step. All
# four were measured identical before the collapse; ADR-0010 now moves ~73
# modules between namespaces and needs to edit the denominator ONCE.
#
# The sys.path guard is the same one test_rosetta_completeness.py uses for
# `from conftest import`: tests/ is a package, so pytest's prepend import-mode
# does not put this directory on sys.path, and conftest itself is imported as
# `tests.conftest` — under which a bare `import rosetta_roots` would fail.
_TESTS_DIR_FOR_ROOTS = str(Path(__file__).resolve().parent)
if _TESTS_DIR_FOR_ROOTS not in _sys.path:
    _sys.path.insert(0, _TESTS_DIR_FOR_ROOTS)
from rosetta_roots import ROSETTA_ROOTS as _ROSETTA_ROOTS  # noqa: E402

# Buckets that are NOT standalone-C-ready.
ROSETTA_NOT_READY = frozenset(
    ("bignum_reference", "python_only_debt", "c_exists_unbound")
)


def _rosetta_iter_submodules(root_name):
    root = _importlib.import_module(root_name)
    yield root
    if not hasattr(root, "__path__"):
        return
    for info in _pkgutil.walk_packages(root.__path__, root_name + "."):
        name = info.name
        tail = name.rsplit(".", 1)[-1]
        if tail.startswith("_") and tail != "__init__":
            continue
        # .adapters = the net/file-IO collector surface (requests + optional
        # netCDF4/rasterio) — the documented IO-exclusion, see ROSETTA_LEDGER.md.
        if any(p in name for p in ("._research", ".adapters", ".attested", "._native")):
            continue
        try:
            yield _importlib.import_module(name)
        except Exception:  # noqa: BLE001 — a module that won't import has no live ops
            continue


def rosetta_live_objects():
    """Map canonical ``defined_at`` (``<module>.<qualname>``) -> the object."""
    seen = {}
    for root_name in _ROSETTA_ROOTS:
        try:
            _importlib.import_module(root_name)
        except Exception:  # noqa: BLE001
            continue
        for mod in _rosetta_iter_submodules(root_name):
            names = getattr(mod, "__all__", None)
            if names is None:
                names = [n for n in dir(mod) if not n.startswith("_")]
            for n in names:
                obj = getattr(mod, n, None)
                if not callable(obj) or _inspect.isclass(obj):
                    continue
                objmod = getattr(obj, "__module__", "") or ""
                if not objmod.startswith("srmech"):
                    continue
                qual = getattr(obj, "__qualname__", n)
                seen.setdefault(f"{objmod}.{qual}", obj)
    return seen


def rosetta_load_classification():
    rows = [_json.loads(l) for l in _ROSETTA_FIXTURE.read_text(encoding="utf-8").splitlines()
            if l.strip()]
    return {r["defined_at"]: r["bucket"] for r in rows}


def _rosetta_key(obj):
    m = getattr(obj, "__module__", "") or ""
    return f"{m}.{getattr(obj, '__qualname__', '')}" if m.startswith("srmech") else None


def _rosetta_names_in(code):
    out = set(code.co_names)
    for const in code.co_consts:
        if _inspect.iscode(const):
            out |= _rosetta_names_in(const)
    return out


def _rosetta_local_imports(fn):
    out = {}
    try:
        src = _textwrap.dedent(_inspect.getsource(fn))
        tree = _ast.parse(src)
    except (OSError, TypeError, SyntaxError):
        return out
    pkg = (getattr(fn, "__module__", "") or "").rsplit(".", 1)[0]
    for node in _ast.walk(tree):
        if isinstance(node, _ast.ImportFrom):
            base = node.module
            if node.level:
                parts = pkg.split(".")
                base = ".".join(parts[: len(parts) - (node.level - 1)] or parts)
                base = base + ("." + node.module if node.module else "")
            for alias in node.names:
                try:
                    mod = _importlib.import_module(base)
                    out[alias.asname or alias.name] = getattr(mod, alias.name)
                except Exception:  # noqa: BLE001
                    continue
    return out


def _rosetta_direct_callees(fn):
    g = dict(getattr(fn, "__globals__", {}) or {})
    g.update(_rosetta_local_imports(fn))
    code = getattr(fn, "__code__", None)
    if code is None:
        return []
    names = _rosetta_names_in(code)
    out = []
    classes = []
    for name in names:
        obj = g.get(name)
        if obj is None:
            continue
        if _inspect.isclass(obj) and (getattr(obj, "__module__", "") or "").startswith("srmech"):
            classes.append(obj)
        elif callable(obj) and (getattr(obj, "__module__", "") or "").startswith("srmech"):
            out.append(obj)
    for cls in classes:
        for name in names:
            meth = getattr(cls, name, None)
            if callable(meth) and (getattr(meth, "__module__", "") or "").startswith("srmech"):
                out.append(meth)
    return out


def rosetta_reached_ledger_ops(start, cls):
    """Set of ledger ``defined_at`` keys transitively reachable from ``start``
    (a function object), recursing through non-ledger glue but treating a
    ``c_dispatched`` / ``composition_of_c`` / ``non_compute`` ledger op as a
    LEAF."""
    reached = set()
    seen_code = set()
    queue = [start]
    while queue:
        fn = queue.pop()
        code = getattr(fn, "__code__", None)
        if code is None or id(code) in seen_code:
            continue
        seen_code.add(id(code))
        for callee in _rosetta_direct_callees(fn):
            k = _rosetta_key(callee)
            if k is not None and k in cls:
                reached.add(k)
                if cls[k] in ("c_dispatched", "composition_of_c", "non_compute"):
                    continue
                continue
            queue.append(callee)
    return reached


# ──────────────────────────────────────────────────────────────────────
# rc282 — shared genome BOUNDED-I/O probe, split into its two terms.
# Lives here (not in a helper module) for the same reason the rc131 helper
# above does: neither demand-load test module has to import the other.
#
# Shared bounded-I/O probe for the genome demand-load ops (rc282).
#
# **Why this exists — the false green it replaces.** The §134/§98 demand-load tests
# prove a real guarantee: ``gene_express_plan``'s PATH variant reads only each region's
# head GATE cap, and a CONDENSED region is skipped having touched only its chromatin
# cap. They measured it by wrapping :func:`genome._open_body_ro` and summing the bytes
# read, then asserting an exact total (``== LEAF``, ``== 1+2+1 caps``, …).
#
# Before rc282 that sum was **silently incomplete**. ``_catalog_data``'s v12+ head-only
# branch reached the body through ``Path.read_bytes``, not through the ``_open_body_ro``
# seam — so the whole-body catalog scan that every one of those calls performs was
# invisible to the probe. The tests appeared to bound the WHOLE CALL while in fact
# bounding only the gate loop. rc282 routed every body read through the one seam, and
# the numbers jumped (``4924`` where ``256`` was asserted) — not a regression, the
# observation becoming honest.
#
# **The decomposition.** The fix is NOT to narrow the instrumentation back — that would
# restore the false green. It is to separate the two terms the old sum conflated, which
# map exactly onto the code:
#
# * the **plan term** — bytes read by the per-region gate loop. This is the guarantee the
#   chromatin work actually makes, and it is still asserted at full strength (exact byte
#   equalities, and that skipping a region genuinely *reduces* it).
# * the **catalog term** — the body scan that derives the chromosome table. A fixed cost,
#   independent of ``cell_state``, inherent to ADR-0003 (the chromosome array is a
#   plaintext table-of-contents and is never stored, so it is re-derived by scanning).
#   Asserted separately as a KNOWN cost rather than folded into a bound it was never
#   part of.
#
# Sessions are tagged **causally**, not by inference: the probe wraps ``_catalog_data``
# as well as ``_open_body_ro``, and any body handle opened while inside a catalog
# derivation is tagged ``catalog``. Reordering the code cannot mislabel them.
#
# **Probe liveness.** Every accessor here is paired with a session count, because an
# upper bound alone passes trivially at zero — a disconnected probe must be a RED test,
# not a green one. That is the same seam lesson rc282 learned from ``_open_body_ro``
# opening through ``builtins.open`` where the suite was hooking ``Path.open``.
# ──────────────────────────────────────────────────────────────────────

from srmech.biology import genome as _G



class CountFile:
    """A read-only file proxy counting the bytes actually read (the bounded-I/O
    probe). One instance per ``_open_body_ro`` call == one SESSION."""

    def __init__(self, f, kind="plan"):
        self.f = f
        self.n = 0
        self.kind = kind            # "plan" | "catalog" — set causally by BodyReadProbe

    def seek(self, *a):
        return self.f.seek(*a)

    def read(self, *a):
        b = self.f.read(*a)
        self.n += len(b)
        return b

    def __enter__(self):
        return self

    def __exit__(self, *a):
        self.f.close()
        return False


class BodyReadProbe:
    """Tallies genome body reads, split into the PLAN term and the CATALOG term.

    Install with :func:`install`; read with :attr:`plan_bytes` / :attr:`catalog_bytes`.
    ``clear()`` between measured calls."""

    def __init__(self):
        self.sessions: list[CountFile] = []
        self._depth = 0             # > 0 while inside a _catalog_data derivation

    # ── installation ─────────────────────────────────────────────────────────
    def install(self, monkeypatch, *, force_pure=True):
        """Wrap the body-open seam AND the catalog derivation, so every session can be
        attributed to one or the other. ``force_pure`` pins the pure path, since the C
        path reads the same bytes by construction but does so through its own fopen,
        invisible to a Python seam."""
        from srmech import _native

        orig_open = _G._open_body_ro
        orig_catalog = _G._catalog_data

        def wrap_open(p):
            cf = CountFile(orig_open(p), "catalog" if self._depth > 0 else "plan")
            self.sessions.append(cf)
            return cf

        def wrap_catalog(path, coupling=None):
            self._depth += 1
            try:
                return orig_catalog(path, coupling)
            finally:
                self._depth -= 1

        monkeypatch.setattr(_G, "_open_body_ro", wrap_open)
        monkeypatch.setattr(_G, "_catalog_data", wrap_catalog)
        if force_pure:
            monkeypatch.setattr(_native, "has_native_genome", lambda: False)
        return self

    # ── tallies ──────────────────────────────────────────────────────────────
    def clear(self):
        self.sessions.clear()

    def _sum(self, kind):
        return sum(cf.n for cf in self.sessions if cf.kind == kind)

    def _count(self, kind):
        return sum(1 for cf in self.sessions if cf.kind == kind)

    @property
    def plan_bytes(self):
        """Bytes read by the per-region gate loop — the term the chromatin guarantee
        actually bounds."""
        return self._sum("plan")

    @property
    def catalog_bytes(self):
        """Bytes read deriving the chromosome table by scanning the body (ADR-0003).
        A fixed cost, independent of ``cell_state``."""
        return self._sum("catalog")

    @property
    def total_bytes(self):
        return sum(cf.n for cf in self.sessions)

    @property
    def n_plan_sessions(self):
        return self._count("plan")

    @property
    def n_catalog_sessions(self):
        return self._count("catalog")

    # ── liveness ─────────────────────────────────────────────────────────────
    def assert_live(self, *, plan=True, catalog=True):
        """A bound alone passes trivially at zero. Assert the probe actually FIRED, so
        a seam that silently stops observing goes red instead of green."""
        if plan:
            assert self.n_plan_sessions > 0 and self.plan_bytes > 0, (
                "the PLAN probe observed nothing — the body-open seam is disconnected "
                "(a bounded-I/O assertion on an unfired probe is vacuously true)")
        if catalog:
            assert self.n_catalog_sessions > 0 and self.catalog_bytes > 0, (
                "the CATALOG probe observed nothing — either the catalog derivation "
                "stopped reading the body (state that as a WIN and update the test) or "
                "it stopped going through _open_body_ro (the false-green rc282 fixed)")
