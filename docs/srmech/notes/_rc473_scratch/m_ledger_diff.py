"""Row-by-row diff of two NDJSON ledgers keyed by a field; reports which fields
moved and how many rows each.

Usage: python m_ledger_diff.py <old.ndjson> <new.ndjson> <key field>
"""
import collections
import json
import sys

key = sys.argv[3]


def load(p):
    meta, rows = None, {}
    for line in open(p, encoding="utf-8"):
        line = line.strip()
        if not line:
            continue
        r = json.loads(line)
        if r.get("record") == "meta":
            meta = r
        else:
            rows[r[key]] = r
    return meta, rows


om, orows = load(sys.argv[1])
nm, nrows = load(sys.argv[2])
print("file:", sys.argv[2])
print("  meta keys moved:", sorted(k for k in set(om) | set(nm) if om.get(k) != nm.get(k)),
      {k: (om.get(k), nm.get(k)) for k in set(om) | set(nm) if om.get(k) != nm.get(k) and k != "verified_at"})
print("  rows old %d new %d, added %d, removed %d" % (
    len(orows), len(nrows), len(set(nrows) - set(orows)), len(set(orows) - set(nrows))))
field_moves = collections.Counter()
moved_rows = []
for k in sorted(set(orows) & set(nrows)):
    diff = sorted(f for f in set(orows[k]) | set(nrows[k]) if orows[k].get(f) != nrows[k].get(f))
    if diff:
        moved_rows.append((k, diff))
        field_moves.update(diff)
print("  rows differing: %d  by field: %s" % (len(moved_rows), dict(field_moves)))
for k, diff in moved_rows:
    extra = ""
    if "status" in diff:
        extra = "  STATUS %s -> %s" % (orows[k].get("status"), nrows[k].get("status"))
    print("    %s: %s%s" % (k, diff, extra))
if "by_status" in (nm or {}):
    print("  by_status:", nm.get("by_status"))
