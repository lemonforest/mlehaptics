"""rc473 repair pass (`#T1188`) — the generating code for "The two cells,
byte-identical".

WHY THIS FILE EXISTS. The rc473 stage-C CONDITIONS block asserts *"Generating
code for every number below is committed under ``docs/srmech/notes/_rc473_*.py``
with its NDJSON beside it."* That was false for one section: no committed script
ran the library-moved-aside cell for the fourteen rows of "The two cells,
byte-identical", and one of its five control values —
``[0.03221088436188455, 0.6677891156381154]`` — occurred nowhere in the
repository except the CHANGELOG line stating it. It is reproducible only at
``dt=0.1``, which the entry did not state; the documented default ``dt=0.01``
gives ``[0.003221088436188455, 0.6967789115638116]``, a different pair.

A claim whose provenance sentence is false is the MPM defect this project
exists to prevent, so the repair is to ship the driver rather than to soften
the sentence.

HOW TO RUN IT — BOTH cells, and the cell is recorded, never inferred::

    cd docs/srmech/python
    PYTHONPATH=$PWD uv run --python 3.12 --no-project --offline \
        python ../notes/_rc473_two_cell_texts.py            # native
    mv srmech/_native/libsrmech.so /tmp/hold.so
    PYTHONPATH=$PWD uv run --python 3.12 --no-project --offline \
        python ../notes/_rc473_two_cell_texts.py            # pure
    mv /tmp/hold.so srmech/_native/libsrmech.so

Each run appends rows tagged with ``has_native``. The comparison the section
claims is then a join on ``row`` across the two ``has_native`` values, done by
:func:`compare` when the file is invoked with ``--compare``.

numpy-free. No ``hashlib``. No ``abs()``.
"""

from __future__ import annotations

import json
import platform
import sys
from pathlib import Path

from srmech import _native
from srmech.cascade import composites
from srmech.math import kepler, laplacian

OUT = Path(__file__).resolve().parent / "_rc473_two_cell_texts.ndjson"

TWO_POW_53_PLUS_1 = 2.0 ** 53 + 1
TWO_POW_55 = 2.0 ** 55
NAN = float("nan")


def _text(fn, *args, **kwargs):
    """``("ok", repr(value))`` or ``("raised", "TypeName: message")``.

    The TEXT is the subject: the section's claim is that both cells produce
    byte-identical refusal strings, so the message is compared verbatim rather
    than reduced to an exception class.
    """
    try:
        return "ok", repr(fn(*args, **kwargs))
    except Exception as exc:                      # noqa: BLE001 - classifying
        return "raised", f"{type(exc).__name__}: {exc}"


#: (row-name, callable, args, kwargs). The eleven REFUSAL rows the section
#: names, then the five CONTROL rows it names — every control stated with the
#: keyword that produces it, which is the half the entry had left implicit.
ROWS = [
    ("equation_of_centre(2**53+1, .0549, 4)",
     kepler.equation_of_centre, (TWO_POW_53_PLUS_1, 0.0549, 4), {}),
    ("kepler_solve(2**55, .3)",
     kepler.kepler_solve, (TWO_POW_55, 0.3), {}),
    ("pin_slot(2**55, .5, 1)",
     kepler.pin_slot, (TWO_POW_55, 0.5, 1.0), {}),
    ("equation_of_centre(nan, .0549, 4)",
     kepler.equation_of_centre, (NAN, 0.0549, 4), {}),
    ("kepler_solve(nan, .3)",
     kepler.kepler_solve, (NAN, 0.3), {}),
    ("pin_slot(nan, .5, 1)",
     kepler.pin_slot, (NAN, 0.5, 1.0), {}),
    ("elementwise_transcendental([nan], 'cos')",
     laplacian.elementwise_transcendental, ([NAN], "cos"), {}),
    ("elementwise_transcendental([nan], 'exp')",
     laplacian.elementwise_transcendental, ([NAN], "exp"), {}),
    ("elementwise_transcendental([nan], 'log')",
     laplacian.elementwise_transcendental, ([NAN], "log"), {}),
    ("kuramoto_step([0, 2**55], [0, 0])",
     composites.kuramoto_step, ([0.0, TWO_POW_55], [0.0, 0.0]), {}),
    ("kuramoto_step([0, 2**55], [0, 0], alpha=0.1)",
     composites.kuramoto_step, ([0.0, TWO_POW_55], [0.0, 0.0]), {"alpha": 0.1}),
    # ---- controls: these must ANSWER, and answer identically -------------
    ("CONTROL equation_of_centre(0.5, .0549, 4)",
     kepler.equation_of_centre, (0.5, 0.0549, 4), {}),
    ("CONTROL kepler_solve(0.5, .3)",
     kepler.kepler_solve, (0.5, 0.3), {}),
    ("CONTROL pin_slot(0.5, .5, 1)",
     kepler.pin_slot, (0.5, 0.5, 1.0), {}),
    ("CONTROL elementwise_transcendental([0.5], 'cos')",
     laplacian.elementwise_transcendental, ([0.5], "cos"), {}),
    # dt=0.1 is STATED. The default dt=0.01 gives a different pair, and the
    # entry quoted the dt=0.1 pair without naming the keyword -- which is the
    # whole reason this file exists.
    ("CONTROL kuramoto_step([0, .7], [0, 0], dt=0.1)",
     composites.kuramoto_step, ([0.0, 0.7], [0.0, 0.0]), {"dt": 0.1}),
    ("CONTROL kuramoto_step([0, .7], [0, 0])  # documented default dt",
     composites.kuramoto_step, ([0.0, 0.7], [0.0, 0.0]), {}),
]


def harvest() -> list[dict]:
    cell = bool(_native.HAS_NATIVE)
    out = []
    for name, fn, args, kwargs in ROWS:
        kind, text = _text(fn, *args, **kwargs)
        out.append({
            "row": name,
            "has_native": cell,
            "outcome": kind,
            "text": text,
            "python": f"{sys.version_info[0]}.{sys.version_info[1]}."
                      f"{sys.version_info[2]}",
            "platform": platform.platform(),
        })
    return out


def compare() -> int:
    """Join the two cells on ``row`` and report every disagreement."""
    rows = [json.loads(l) for l in OUT.read_text(encoding="utf-8").splitlines()
            if l.strip()]
    native = {r["row"]: r for r in rows if r["has_native"]}
    pure = {r["row"]: r for r in rows if not r["has_native"]}
    missing = sorted(set(native) ^ set(pure))
    if missing or not native or not pure:
        print(f"INCOMPLETE: native={len(native)} pure={len(pure)} "
              f"unpaired={missing}")
        print("Run the file once in each cell before --compare.")
        return 2
    bad = 0
    for name in native:
        a, b = native[name], pure[name]
        same = (a["outcome"], a["text"]) == (b["outcome"], b["text"])
        if not same:
            bad += 1
        print(f"{'SAME ' if same else 'DIFF '} {name}")
        if not same:
            print(f"    native: {a['outcome']} {a['text']}")
            print(f"    pure  : {b['outcome']} {b['text']}")
    print(f"\nrows compared: {len(native)}   disagreements: {bad}")
    return 0 if bad == 0 else 1


def main() -> int:
    if "--compare" in sys.argv:
        return compare()
    rows = harvest()
    with OUT.open("a", encoding="utf-8") as fh:
        for r in rows:
            fh.write(json.dumps(r, sort_keys=True) + "\n")
    print(f"HAS_NATIVE {_native.HAS_NATIVE} — {len(rows)} rows appended to "
          f"{OUT.name}")
    for r in rows:
        print(f"  {r['outcome']:<6} {r['row']}")
        print(f"         {r['text'][:110]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
