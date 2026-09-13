"""rc473 stage C (`#T1188`) — ``run_example_args.py`` DECLARES a pure cell and
does not ENFORCE one, and the difference is measurable in the ledger it writes.

``tools/run_example_args.py:214`` does::

    env.setdefault("SRMECH_EXPECT_PURE", "1")

``SRMECH_EXPECT_PURE`` is the tests' *declaration* channel
(``tests/_native_gate.py:53``) — it tells a native-parity test that a missing
library is expected rather than a defect. It does **not** unload a library that
is present, and the harvester does nothing else about it. So the same command,
run on the same tree at the same commit with the same interpreter, writes a
DIFFERENT ledger depending only on whether ``srmech/_native/libsrmech.so``
happens to be sitting beside the package.

Measured at rc473, CPython 3.10.21 under
``uv run --python 3.10 --no-project --offline``, WSL2, numpy absent, both runs
at the same HEAD:

  * **library present (HAS_NATIVE True)** — 100 rows move against the committed
    ledger: 91 ``def_blob`` stamps, plus
    ``srmech.cascade.magnitude`` / ``srmech.cascade.reorient`` whose captured
    float argument shifts by ONE ULP
    (``-0.07189024134555967`` -> ``-0.07189024134555966``, which is
    ``equation_of_centre(3.9, 0.0549)`` read from the C projection instead of
    the Q61 cascade), ``srmech.amsc.format.read_ndjson`` whose recorded error
    changes CLASS (``FileNotFoundError`` -> ``OSError: srmech_ndjson_iter(...)
    failed: IO``), and eight ``n_calls`` shifts.
  * **library moved aside (HAS_NATIVE False)** — 92 rows move: 91 ``def_blob``
    stamps and ``srmech.bus.decode_splice``, whose captured ``time_ns``
    argument is the WALL CLOCK and moves on every run.

The committed ledger's own content says which cell wrote it: it carried the
``...67`` float and the ``FileNotFoundError``, i.e. PURE. rc473 therefore
re-harvested it PURE, so that the only moves are the stamps the change earns
and one clock read — and this file records the alternative run rather than
discarding it, because "the tool was run" is not a condition and a ledger
harvested in the other cell would have read as four unattributable value
changes.

USAGE — the comparison, on any two ledger files::

    python3 notes/_rc473_args_ledger_cell_probe.py OLD.ndjson NEW.ndjson

Reproducing the two runs (the harvester always rewrites the whole ledger; keep
a copy before the second run)::

    cd docs/srmech/python
    export GIT_DIR=<repo>/.git/worktrees/<name>          # WSL git cannot read a
    export GIT_WORK_TREE=<worktree>                      # Windows gitdir pointer
    uv run --python 3.10 --no-project --offline python tools/run_example_args.py
    cp tests/example_args_ledger.ndjson /tmp/args_native_run.ndjson
    mv srmech/_native/libsrmech.so /tmp/hold.so
    uv run --python 3.10 --no-project --offline python tools/run_example_args.py
    mv /tmp/hold.so srmech/_native/libsrmech.so

numpy-free. No ``hashlib``. No ``abs()``.
"""

from __future__ import annotations

import collections
import json
import sys
from pathlib import Path


def _rows(path: Path):
    data: dict = {}
    meta = None
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        rec = json.loads(line)
        if rec.get("record") == "meta":
            meta = rec
            continue
        data[rec.get("op") or rec.get("name")] = rec
    return data, meta


def main(argv: list[str]) -> int:
    if len(argv) != 3:
        print(__doc__)
        return 2
    old_p, new_p = Path(argv[1]), Path(argv[2])
    old, om = _rows(old_p)
    new, nm = _rows(new_p)
    out = [{"kind": "meta_old", "path": str(old_p), "meta": om},
           {"kind": "meta_new", "path": str(new_p), "meta": nm},
           {"kind": "counts", "old_rows": len(old), "new_rows": len(new)}]

    by_fields: collections.defaultdict = collections.defaultdict(list)
    for key in sorted(set(old) | set(new)):
        a, b = old.get(key), new.get(key)
        if a is None:
            by_fields["ADDED"].append(key)
            continue
        if b is None:
            by_fields["REMOVED"].append(key)
            continue
        fields = sorted(f for f in set(a) | set(b) if a.get(f) != b.get(f))
        if fields:
            by_fields[",".join(fields)].append(key)
            if fields != ["def_blob"]:
                out.append({
                    "kind": "row_moved", "op": key, "fields": fields,
                    "old": {f: a.get(f) for f in fields},
                    "new": {f: b.get(f) for f in fields},
                })
    for fields, ops in sorted(by_fields.items()):
        out.append({"kind": "tally", "fields": fields, "n": len(ops),
                    "ops": ops if len(ops) <= 12 else ops[:12] + ["..."]})

    for row in out:
        print(json.dumps(row, sort_keys=True))
    dest = Path(__file__).resolve().parent / "_rc473_args_ledger_cell_probe.ndjson"
    with dest.open("w", encoding="utf-8", newline="\n") as fh:
        for row in out:
            fh.write(json.dumps(row, sort_keys=True) + "\n")
    print(f"wrote {len(out)} rows -> {dest}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
