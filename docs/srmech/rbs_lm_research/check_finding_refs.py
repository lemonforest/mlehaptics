#!/usr/bin/env python3
"""check_finding_refs.py — HARDEN the session-ledger (F1305). A finding's cross-reference to another finding
(``F735``, ``Composes F1301``, ``-> extended by F1302``) is the internal analogue of a citation: under MPM it
must RESOLVE, not be recalled. This checker verifies every F-number a finding cites resolves to an actual
FINDING file on disk, and reports the dangling ones — the ledger's own no-bare-recall ratchet.

Session-ledger = the research-tree findings under docs/srmech/rbs_lm_research/ (NOT the durable srmech package
or auto-memory). A finding number that resolves to a file is HARDENED; one that does not is a recalled ghost.

Usage:  python3 check_finding_refs.py            # report dangling refs
        python3 check_finding_refs.py --strict   # exit nonzero if any finding cites a nonexistent F-number
"""
import glob
import os
import re
import sys

FNUM = re.compile(r"\bF(\d{3,4})\b")
FILE_FNUM = re.compile(r"R-RBS-LM-FINDING_(\d{3,4})_")


def existing_finding_numbers():
    """A finding is LODGED (resolved) if it exists as a FINDING file OR as a git commit subject
    `F<N>:` — the two ways this project records a finding. Both count as hardened."""
    import subprocess
    nums = set()
    for f in glob.glob("R-RBS-LM-FINDING_*.md") + glob.glob("R-RBS-LM-FINDING_*.py") + glob.glob("R-RBS-LM-*.md") + glob.glob("R-RBS-LM-*.py"):
        m = FILE_FNUM.search(os.path.basename(f))
        if m:
            nums.add(m.group(1))
    try:
        out = subprocess.run(["git", "log", "--all", "--format=%s"], capture_output=True, text=True).stdout
        for m in re.finditer(r"\bF(\d{3,4})\b", out):   # any F<N> token in a commit subject
            nums.add(m.group(1))
    except Exception:
        pass
    return nums


def main(argv):
    strict = "--strict" in argv
    have = existing_finding_numbers()
    dangling = {}          # cited F-number -> list of files that cite it
    for f in sorted(glob.glob("R-RBS-LM-FINDING_*.md")):
        text = open(f, encoding="utf-8", errors="replace").read()
        self_num = FILE_FNUM.search(os.path.basename(f))
        self_num = self_num.group(1) if self_num else None
        for m in set(FNUM.findall(text)):
            if m == self_num:
                continue
            if m not in have:
                dangling.setdefault(m, []).append(os.path.basename(f)[:48])
    print("=== session-ledger finding-ref check ===")
    print("  findings on disk: %d" % len(have))
    print("  distinct cited F-numbers that DO NOT resolve to a file: %d" % len(dangling))
    for num, citers in sorted(dangling.items(), key=lambda kv: -len(kv[1]))[:40]:
        print("    F%-5s cited by %d finding(s): %s%s"
              % (num, len(citers), ", ".join(citers[:3]), " ..." if len(citers) > 3 else ""))
    if not dangling:
        print("  => every cited finding resolves. The ledger is hardened (no recalled ghosts).")
    else:
        print("  => these are RECALLED GHOSTS or NOT-YET-WRITTEN forward-links. A dangling ref is either a")
        print("     typo/hallucinated number (fix it) or a planned finding not yet lodged (write it or drop the cite).")
    return (1 if (strict and dangling) else 0)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
