"""Diff two notes/_rc473_twin_d2_slot_sweep.py dumps (native vs pure). Classifies each row:
SAME (same verdict, same value or same exception text), SAME-VERDICT
(both serve different values, or both refuse with different type/text), or
SERVE-vs-REFUSE.

Usage: python m_d2_diff.py native.json pure.json
"""
import json
import sys

a = json.load(open(sys.argv[1]))
b = json.load(open(sys.argv[2]))
assert len(a["rows"]) == len(b["rows"])
counts = {"SAME": 0, "SAME-VERDICT": 0, "SERVE-vs-REFUSE": 0}
for ra, rb in zip(a["rows"], b["rows"]):
    assert (ra["op"], ra["slot"], ra["arg"]) == (rb["op"], rb["slot"], rb["arg"])
    pa, pb = ra["py"], rb["py"]
    if pa["ok"] != pb["ok"]:
        k = "SERVE-vs-REFUSE"
    elif pa["value"] == pb["value"]:
        k = "SAME"
    else:
        k = "SAME-VERDICT"
    counts[k] += 1
    if k != "SAME":
        print("%-16s %-12s %-14s %-24s\n    %s: %s\n    %s: %s%s" % (
            k, ra["op"], ra["slot"], ra["arg"], a["cell"], pa["value"][:140],
            b["cell"], pb["value"][:140],
            ("\n    C: %s" % ra["c"]) if "c" in ra else ""))
print("rows compared: %d  %s" % (len(a["rows"]), counts))
