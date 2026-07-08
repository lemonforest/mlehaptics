"""Shared pytest fixtures for srmech tests.

Each fixture builds a minimal self-contained descriptor.toml so the
tests don't depend on any external catalog SSOT (ephemerides-spectral
or otherwise). The shape mirrors the real EarthRef SC descriptor so
the html_scraper parse test exercises the same field-map structure.
"""

from __future__ import annotations

from array import array as _stdlib_array
from pathlib import Path
from typing import Any, List

import pytest


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
    from srmech.amsc.mat import Mat
    from srmech.amsc.vec import Vec
    from srmech.amsc.hv import HV
    from srmech.amsc.q import Q
    from srmech.amsc.complex128 import Complex128

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
        from srmech.amsc.qbipoly import QBiPoly
        return isinstance(raw, QBiPoly)
    if token.startswith("QPoly"):
        from srmech.amsc.qpoly import QPoly
        return isinstance(raw, QPoly)
    if token.startswith("Poly"):
        from srmech.amsc.poly import Poly
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
    from srmech.amsc import _native as _n

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
# rc177 annex: mirror the test_rosetta_completeness._ROOTS extension to bus/dsl so
# the shared non_compute live-count walk (owed ceiling / composes_c reachability /
# dev_tooling allowlist) sees the +39 bus/dsl rows as live.
_ROSETTA_ROOTS = (
    "srmech.amsc", "srmech.qm", "srmech.signal_processing",
    "srmech.bus", "srmech.dsl",
)

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
