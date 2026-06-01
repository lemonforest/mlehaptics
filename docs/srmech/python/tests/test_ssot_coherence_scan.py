"""SSoT two-tier coherence ratchet (v0.6.0rc20, MS #20).

Scans the CONTINUUM tier as it grows and asserts the two-tier SSoT stays
coherent (the rc16 §3.29 boundary: kernel ops hardcoded; cascade INSTANCES in
TOML):

  * every ``worked_instances/*.toml`` is well-formed (name / purpose / ops);
  * every op a worked instance references resolves to a real callable;
  * the kernel tier (worked-instance names) and the continuum DSL catalog
    (``srmech.dsl`` cascade op-names) are DISJOINT name-spaces — a worked
    instance must not shadow a catalog op-name (the boundary can't silently
    erode as the surface grows);
  * every cascade-catalog op still resolves (the full two-tier picture, in one
    place).

The notebook-reference cross-check (every worked instance cites an existing
notebook section) is deferred (it would require parsing the notebook tree).
"""
import importlib
import sys
from pathlib import Path

import srmech
from srmech.dsl import load_catalog, lookup_cascade_op

if sys.version_info >= (3, 11):
    import tomllib as _toml
else:  # pragma: no cover — 3.10 back-port branch
    import tomli as _toml  # type: ignore[no-redef]


_WORKED_INSTANCES_DIR = (
    Path(srmech.__file__).resolve().parent
    / "amsc" / "_research" / "worked_instances"
)

# Ratchet: the worked-instance descriptor count. Bump CONSCIOUSLY when a new
# worked instance lands (mirrors the describe()-total ratchet discipline).
EXPECTED_WORKED_INSTANCE_COUNT = 1


def _worked_instance_paths():
    return sorted(_WORKED_INSTANCES_DIR.glob("*.toml"))


def _load(path):
    with open(path, "rb") as fh:
        return _toml.load(fh)["worked_instance"]


def _resolve(dotted):
    module, _, attr = dotted.rpartition(".")
    return getattr(importlib.import_module(module), attr)


def test_worked_instances_dir_present():
    assert _WORKED_INSTANCES_DIR.is_dir(), (
        f"worked_instances dir missing at {_WORKED_INSTANCES_DIR}"
    )


def test_worked_instance_count_ratchet():
    n = len(_worked_instance_paths())
    assert n == EXPECTED_WORKED_INSTANCE_COUNT, (
        f"worked-instance count is {n}, expected {EXPECTED_WORKED_INSTANCE_COUNT}"
        f"; a new worked instance is a CONSCIOUS continuum-tier addition — bump "
        f"EXPECTED_WORKED_INSTANCE_COUNT and confirm the scan covers it."
    )


def test_every_worked_instance_is_wellformed():
    for path in _worked_instance_paths():
        wi = _load(path)
        assert isinstance(wi.get("name"), str) and wi["name"], path.name
        assert isinstance(wi.get("purpose"), str) and wi["purpose"], path.name
        assert isinstance(wi.get("ops"), dict) and wi["ops"], (
            f"{path.name}: [worked_instance.ops] must be a non-empty table of "
            f"logical-name -> dotted srmech path"
        )


def test_every_worked_instance_op_resolves():
    for path in _worked_instance_paths():
        for logical, dotted in _load(path)["ops"].items():
            assert isinstance(dotted, str) and dotted.startswith("srmech."), (
                f"{path.name}:{logical} -> {dotted!r} must be a dotted srmech path"
            )
            assert callable(_resolve(dotted)), (
                f"{path.name}:{logical} -> {dotted} did not resolve to a callable"
            )


def test_kernel_and_continuum_tiers_are_disjoint():
    catalog_names = set(load_catalog())
    wi_names = {_load(p)["name"] for p in _worked_instance_paths()}
    overlap = catalog_names & wi_names
    assert not overlap, (
        f"the kernel/continuum boundary leaked: name(s) {sorted(overlap)} are in "
        f"BOTH the cascade DSL catalog and the worked-instance set. Worked "
        f"instances compose kernel ops; their names must not shadow catalog ops."
    )


def test_every_cascade_catalog_op_resolves():
    # the continuum DSL tier stays coherent too — re-affirmed in the same scan
    for name in load_catalog():
        assert callable(lookup_cascade_op(name)), f"catalog op {name} unresolved"
