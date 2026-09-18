"""rc476 (`#T1188`) — the per-op accounting behind the decoded-channel re-pin.

``tests/test_namespace_prefix_decode_aware_rc361.py`` pins the number of
``srmech.physics.qm.`` references inside the DECODED channel of
``c/src/srmech_carrier_registry.c``. This release moves it 211 -> 214, and a
pin is only re-pinned with an accounting: WHICH op gained WHICH reference, and
why. This file produces that accounting, so the table in the test's comment is
a measurement with committed generating code rather than a claim
(`[[feedback_computational_provenance_discipline]]`).

WHAT IT DOES. It decodes BOTH artefacts through the gate's OWN ``decoded_blobs``
reader — the baseline (extract the pre-change file with ``git show <rev>:<path>``)
and the current tree's — counts ``srmech.physics.qm.<op>`` per BLOB rather than
per file, and differences them. Counting per blob is the point: the back-index
row is keyed by ``(op, CARRIER)``, and each carrier's row set lives in its own
hoisted byte array, so a per-blob delta NAMES the carrier that moved. The blob's
carrier is read off the blob itself — its own ``"name"`` field, MEASURED as
``cs_lstr_0`` HV / ``_1`` Mat / ``_2`` Q / ``_3`` float / ``_4`` int — and not
assumed from its index.

Usage (numpy-ABSENT, from ``docs/srmech/python``)::

    git show <baseline-rev>:docs/srmech/c/src/srmech_carrier_registry.c \\
        > /tmp/baseline_registry.c
    PYTHONDONTWRITEBYTECODE=1 python3 ../notes/_rc476_decode_accounting.py \\
        /tmp/baseline_registry.c ../c/src/srmech_carrier_registry.c \\
        ../notes/_rc476_decode_accounting.ndjson

With one artefact it reports the current counts only; with two it reports the
delta table. The third argument is optional and is where the NDJSON lands.
"""

import collections
import json
import os
import re
import sys
from pathlib import Path


sys.path.insert(0, os.path.join(os.getcwd(), "tests"))
from c_byte_arrays import decoded_blobs  # noqa: E402


OP_RE = re.compile(r"srmech\.physics\.qm\.[A-Za-z0-9_.]+")
# Each hoisted blob carries ONE carrier's record, and its own `"name"` field is
# what says which — read it rather than inferring the carrier from the blob
# index. MEASURED on the rc476 artefact: cs_lstr_0 HV / _1 Mat / _2 Q /
# _3 float / _4 int.
CARRIER_RE = re.compile(r'"name"\s*:\s*"([A-Za-z0-9_]+)"')
PREFIXES = ("srmech.physics.qm.", "srmech.math.", "srmech.cascade.", "srmech.amsc.")


def read(path):
    """-> (per_blob, blob_label, totals) for one carrier-registry artefact.

    ``decoded_blobs`` refuses anything that is not a ``.c`` path, so a baseline
    extracted with ``git show`` must keep that suffix.
    """
    blobs = list(decoded_blobs(Path(path)))
    per_blob = {}
    label = {}
    for name, text in blobs:
        per_blob[name] = collections.Counter(OP_RE.findall(text))
        hit = CARRIER_RE.search(text)
        label[name] = hit.group(1) if hit else ""
    joined = "\n".join(t for _, t in blobs)
    totals = {p: joined.count(p) for p in PREFIXES}
    totals["distinct_physics_qm_op_paths"] = len(set(OP_RE.findall(joined)))
    return per_blob, label, totals


def main(argv):
    if len(argv) < 2:
        print(__doc__)
        return 2

    out = []
    if len(argv) >= 3 and os.path.exists(argv[2]):
        base_path, cur_path = argv[1], argv[2]
        ndjson_path = argv[3] if len(argv) > 3 else None
    else:
        base_path, cur_path = None, argv[1]
        ndjson_path = argv[2] if len(argv) > 2 else None

    cur_blob, cur_label, cur_tot = read(cur_path)
    out.append({"kind": "artefact", "role": "current", "path": cur_path})
    out.append({"kind": "totals", "role": "current", **cur_tot})
    for name in sorted(cur_label):
        out.append(
            {
                "kind": "blob",
                "role": "current",
                "blob": name,
                "carrier": cur_label[name],
                "physics_qm_refs": sum(cur_blob[name].values()),
            }
        )

    if base_path is not None:
        base_blob, base_label, base_tot = read(base_path)
        out.append({"kind": "artefact", "role": "baseline", "path": base_path})
        out.append({"kind": "totals", "role": "baseline", **base_tot})
        for key in sorted(cur_tot):
            out.append(
                {
                    "kind": "delta_total",
                    "channel": key,
                    "baseline": base_tot.get(key),
                    "current": cur_tot[key],
                    "delta": cur_tot[key] - base_tot.get(key, 0),
                }
            )
        # per (op, blob) -> the (op, carrier) rows that actually moved
        ops = set()
        for counter in list(base_blob.values()) + list(cur_blob.values()):
            ops.update(counter)
        for op in sorted(ops):
            b_tot = sum(base_blob.get(n, {}).get(op, 0) for n in base_blob)
            c_tot = sum(cur_blob.get(n, {}).get(op, 0) for n in cur_blob)
            if b_tot == c_tot:
                continue
            rows = []
            for name in sorted(set(base_blob) | set(cur_blob)):
                b = base_blob.get(name, collections.Counter()).get(op, 0)
                c = cur_blob.get(name, collections.Counter()).get(op, 0)
                if b != c:
                    rows.append(
                        {
                            "blob": name,
                            "carrier": cur_label.get(name, ""),
                            "baseline": b,
                            "current": c,
                            "delta": c - b,
                        }
                    )
            out.append(
                {
                    "kind": "delta_op",
                    "op": op,
                    "baseline": b_tot,
                    "current": c_tot,
                    "delta": c_tot - b_tot,
                    "by_blob": rows,
                }
            )

    lines = [json.dumps(r, sort_keys=True) for r in out]
    if ndjson_path:
        with open(ndjson_path, "w", encoding="utf-8", newline="\n") as fh:
            for line in lines:
                fh.write(line + "\n")
    for line in lines:
        print(line)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
