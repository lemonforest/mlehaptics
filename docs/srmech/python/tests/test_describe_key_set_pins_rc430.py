"""rc430 repair (`#T1127`) — the describe() key-set pins, DERIVED not listed.

WHY THIS FILE EXISTS
────────────────────
rc430 added a thirteenth top-level ``describe()`` key (``frames``). Three test
files pin that key set EXHAUSTIVELY, so all three had to move together. The rc
shipped with all three red, after a GREEN local ``tools/ripple_check.py`` sweep.

The sweep was green because the ripple manifest names only ONE of the three
(``test_mcp.py``, and only by node id — and not the node that pins the key
set). The other two are not mentioned anywhere in it. Nothing was false in the
manifest; it simply did not say. An incomplete map of where to look survives
every check that reads what is present, which is why three separate reviewers
reading the manifest all reported the same single ripple.

So this gate does not add the two missing files to a list — a list is the thing
that failed. It DERIVES the pin sites from the tree and requires the manifest to
cover whatever it finds. A fourth pin site added later is caught without anyone
remembering this file exists.

WHAT A "PIN SITE" IS
────────────────────
A test file that spells the top-level key set out as a literal — detected by the
co-occurrence of three keys that appear together only in such a set literal.
The predicate is deliberately structural rather than a hard-coded roster; its
non-vacuity is proved below in both directions.
"""

from __future__ import annotations

import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_PKG_ROOT = _HERE.parent
_TOOLS = _PKG_ROOT / "tools"

if str(_TOOLS) not in sys.path:
    sys.path.insert(0, str(_TOOLS))

import ripple_check  # noqa: E402  (tools/ on sys.path above)

from srmech.introspect import describe  # noqa: E402

_MANIFEST = _TOOLS / "ripple_gates.txt"

# The three keys whose CO-OCCURRENCE identifies an exhaustive top-level pin.
# Any one of them alone appears in ordinary prose and unrelated assertions;
# all three in one file has only ever meant "this file spells out the key set".
_PIN_MARKERS = ('"handle_pending"', '"cascade_catalog"', '"tool_schema_version"')


def _is_pin_site(text: str) -> bool:
    return all(marker in text for marker in _PIN_MARKERS)


def _pin_functions(text: str) -> list[str]:
    """The ``test_*`` functions in ``text`` that actually spell the key set.

    Coverage has to be node-accurate, not file-accurate. ``test_mcp.py`` is in
    the manifest by NODE ID for two unrelated nodes, so a file-level check would
    call it covered while the sweep still never runs the node that holds the
    pin — the manifest would keep its green and CI would keep its red, which is
    the precise failure this file exists to end. A gate carrying the same defect
    it was written to catch is worse than none, because it certifies the gap.
    """
    names: list[str] = []
    current: str | None = None
    body: list[str] = []

    def _flush() -> None:
        if current and _is_pin_site("\n".join(body)):
            names.append(current)

    for line in text.splitlines():
        if line.startswith("def "):
            _flush()
            head = line[4:].split("(", 1)[0].strip()
            current, body = (head if head.startswith("test_") else None), []
        else:
            body.append(line)
    _flush()
    return names


def _pin_sites() -> dict[str, list[str]]:
    """``{"tests/<file>.py": [pinning test function names]}``."""
    found: dict[str, list[str]] = {}
    for path in sorted(_HERE.glob("test_*.py")):
        if path.name == Path(__file__).name:
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        if _is_pin_site(text):
            found[f"tests/{path.name}"] = _pin_functions(text)
    return found


def _manifest_targets() -> list[str]:
    lines = _MANIFEST.read_text(encoding="utf-8").splitlines()
    return [ln.strip() for ln in lines
            if ln.strip() and not ln.strip().startswith("#")]


def test_the_pin_site_detector_is_not_vacuous() -> None:
    """NON-VACUITY CONTROL, both directions. A detector that cannot say NO is
    not a detector, and one that cannot say YES would make every assertion
    below pass on an empty set."""
    assert _is_pin_site(
        'x = {"tool_schema_version", "handle_pending", "cascade_catalog"}')
    assert not _is_pin_site('assert d["handle_pending"] == []')
    assert not _is_pin_site("nothing to see here")


def test_at_least_the_three_known_pin_sites_are_found() -> None:
    """The detector must still see the sites we know about. If a rename or a
    refactor moves a pin somewhere this predicate cannot see, that is a real
    regression in the gate and it should be loud, not silent."""
    sites = _pin_sites()
    for known in ("tests/test_mcp.py",
                  "tests/test_describe_registry_pointer_rc407.py",
                  "tests/test_domain_classes_rc298.py"):
        assert known in sites, (
            f"{known} pins the describe() top-level key set but the detector "
            f"no longer finds it. Found: {sorted(sites)}")
        assert sites[known], (
            f"{known} is a pin site but no enclosing test function was "
            f"resolved — node-accurate coverage below would silently weaken "
            f"to file-accurate. Found functions: {sites[known]}")


def test_every_pin_site_is_covered_by_the_ripple_manifest() -> None:
    """THE GATE. Every file that pins the key set must be reachable from
    ``tools/ripple_gates.txt`` — as the whole file, or by a node id inside it.

    This is the check whose absence let rc430 ship three reds behind a green
    sweep. It is stated over the DERIVED set, so it also covers pin sites that
    do not exist yet.
    """
    targets = _manifest_targets()
    whole_files = {t for t in targets if "::" not in t}
    node_ids = {t for t in targets if "::" in t}
    sites = _pin_sites()
    assert sites, "no pin sites found — this gate would pass vacuously"

    missing = []
    for site, funcs in sorted(sites.items()):
        if site in whole_files:
            continue                       # whole file runs every node in it
        if any(f"{site}::{fn}" in node_ids for fn in funcs):
            continue                       # the PINNING node is named
        missing.append(f"{site}  (pinning node(s): {', '.join(funcs) or 'NONE'})")

    assert not missing, (
        "describe() key-set pin site(s) NOT covered by the ripple manifest:\n  "
        + "\n  ".join(missing)
        + f"\n\nAdd them to {_MANIFEST.name} — either the whole file, or the "
          "NAMED pinning node (preferable for slow files; a node id for some "
          "OTHER test in the same file does not count, because the sweep would "
          "still never run the pin). Any rc that adds a top-level describe() "
          "key ripples to EVERY one of these files at once; a manifest that "
          "names some of them reports green while CI goes red."
    )


def test_the_live_key_set_is_what_the_pins_pin() -> None:
    """The pins are only worth covering if they track the live surface. Asserts
    the live key count, so a key added without touching any pin file fails here
    even before the three pin sites are reached."""
    keys = set(describe())
    assert len(keys) == 13, sorted(keys)
    assert "frames" in keys, (
        "rc430's frame axis is missing from describe() — the key this whole "
        "ripple was about")
