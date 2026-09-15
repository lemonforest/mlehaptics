"""Planted regressions for the two new guard gates, each restored byte-for-byte.

For each plant: save the file's bytes, apply an exact-once replacement, run the named
gate, restore the saved bytes, and confirm the restore is byte-identical. The plant
MUST turn the gate red; the restore MUST turn it green again.
Usage: python plant_guards.py <docs/srmech/python>
"""
import subprocess
import sys
from pathlib import Path

PY = Path(sys.argv[1]).resolve()
CUR = PY / "srmech" / "introspect" / "_tool_docs_curated.py"
KEP = PY / "srmech" / "math" / "kepler.py"
PHRASE = "tests/test_kepler_identity_phrases_absent_rc473.py"
CITE = "tests/test_curated_line_citations_resolve_rc473.py"

PLANTS = [
    ("identity_back_py (the can-fail lens's plant)", KEP, PHRASE,
     b"+ PR #416 F2/F15/F17 read Kepler-equation algebra as pin-slot composition.",
     b"+ PR #416 F2/F15/F17: Kepler-equation algebra IS pin-slot composition."),
    ("same_shape_back_curated_only", CUR, PHRASE,
     b"or comparing a bronze linkage with Kepler's equation, which one stage matches through e**2 and departs from at e**3.",
     b"or demonstrating that a bronze linkage and an orbital equation are the SAME shape."),
    ("citation_shift_parallel_334_to_335", CUR, CITE,
     b"``cascade.parallel_sector_dispatch`` (``parallel.py:334``) already reports",
     b"``cascade.parallel_sector_dispatch`` (``parallel.py:335``) already reports"),
    ("citation_bare_followon_shift", CUR, CITE, None, None),
]


def run_gate(gate):
    proc = subprocess.run([sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", gate],
                          cwd=str(PY), stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                          env={**__import__("os").environ, "PYTHONDONTWRITEBYTECODE": "1",
                               "PYTHONIOENCODING": "utf-8"})
    text = proc.stdout.decode("utf-8", "replace").strip().splitlines()
    return proc.returncode, (text[-1] if text else ""), text


def bare_followon_needle(raw):
    """The first bare ``(:NNN)`` follow-on in the curated file, shifted by +1 line."""
    import re
    m = re.search(rb"\(``?:(\d+)``?\)", raw)
    if m is None:
        m = re.search(rb"\(:(\d+)\)", raw)
    old = m.group(0)
    new = old.replace(m.group(1), str(int(m.group(1)) + 1).encode())
    return old, new


for name, path, gate, old, new in PLANTS:
    saved = path.read_bytes()
    if old is None:
        old, new = bare_followon_needle(saved)
    n = saved.count(old)
    print("=" * 78)
    print("PLANT", name, "file", path.name, "needle count", n, "gate", gate)
    print("  old:", old[:120])
    print("  new:", new[:120])
    if n != 1:
        print("  REFUSED: needle must occur exactly once")
        continue
    path.write_bytes(saved.replace(old, new))
    try:
        code, last, text = run_gate(gate)
        print("  planted -> exit", code, "|", last)
        for line in text:
            if line.startswith("FAILED") or "shipped surface" in line or "judged" in line:
                print("   ", line[:200])
    finally:
        path.write_bytes(saved)
    print("  restored byte-identical:", path.read_bytes() == saved)
    code, last, _ = run_gate(gate)
    print("  restored -> exit", code, "|", last)
