#!/usr/bin/env python3
"""ADVERSARIAL: verify every file:line quote in _1653_readme_truth_audit.md
actually says what the report claims AT THAT LINE.

Round-1 experience: stale line numbers are the most common defect. This checks
each (path, line, needle) triple the report's tables assert. A needle is a
normalised substring of the claimed verbatim; the check is "does the needle
appear in the physical line, or in the 3-line window starting at that line"
(the report normalises wrapped source lines, which is legitimate, so both
verdicts are reported separately).
"""
from __future__ import annotations

import os
import re
import sys

SRMECH_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

# (report_section, path_relative_to_docs/srmech, line, needle)
CASES = [
    ("§1 R16-A", "python/README.md", 16, "Two implementations, one capability set."),
    ("§1 R16-B", "python/README.md", 16, "no Python present"),
    ("§1 R16-B", "python/README.md", 16, "can serve tools, run cascades, and speak the bus"),
    ("§1 R16-C", "python/README.md", 16, "in-C tool dispatch over the 663-entry tool registry"),
    ("§1 R16-D", "python/README.md", 16, "related by projection rather than by rank"),
    ("§1 R16-D", "python/README.md", 16, "neither is the reference"),
    ("§1 R16-E", "python/README.md", 16, "byte-identical results"),
    ("§1 R18", "python/README.md", 18, "the gap is enumerated rather than asserted away"),
    ("§1 R575", "python/README.md", 575, "ADR-0003 commits srmech to running standalone on a C host with no Python present"),
    ("§1 R575", "python/README.md", 575, "Neither is a claim that coverage is currently complete"),
    ("§1 R579", "python/README.md", 579, "As of v0.9.0rc334 that count is"),
    ("§1 R60", "python/README.md", 60, "reassembles the same exact rational from the peers"),
    ("§1 TD-expl", "python/srmech/introspect/_tool_docs_curated.py", 3834, "counts the catalog (17"),
    ("§1 TD-exam", "python/srmech/introspect/_tool_docs_curated.py", 3800, "any of the 17 executable"),
    ("§0/§1 CREG", "c/src/srmech_tool_registry.c", 16809, "any of the 17 executable descriptors"),
    ("ALT CREG", "c/src/srmech_tool_registry.c", 16807, "any of the 17 executable descriptors"),
    ("§3 MODEL", "python/srmech/introspect/_tool_docs_curated.py", 1960, "bounded Class-N C dispatch table"),
    ("§1 W-compose", "c/src/srmech_compose_run.c", 7, "BOUNDED set of"),
    ("§1 W-cat1341", "python/srmech/amsc/catalog.py", 1341, "A bare-C host lists / runs a"),
    ("§1 W-cat1311", "python/srmech/amsc/catalog.py", 1311, "The descriptor discovery + FS read stay host-side"),
    ("§1 W-cat89", "python/srmech/amsc/catalog.py", 89, "a bare-C host runs the catalog registry/kernel/"),
    ("§1 W-toml74", "python/srmech/dsl/_toml_chain.py", 74, "C-only-host chain-spec TOML->canonical-JSON front-end"),
    ("§1 CLI109", "python/srmech/cli/main.py", 109, "run (execute a TOML chain spec), ops (list"),
    ("§1 W-mcp321", "c/src/srmech_mcp.c", 321, "capability the invariant and the two projections co-equal"),
    ("§1 W-hdr342", "c/include/srmech.h", 342, "projections are co-equal. Rejecting the stale lib is the only safe read."),
    ("§1 CM451", "CLAUDE.md", 451, "full C parity for every primitive class, no exceptions"),
    ("§1 CM136", "CLAUDE.md", 136, "pure-Python (co-equal"),
    ("§1 CM464", "CLAUDE.md", 464, "manifests and TOML descriptors with no Python present"),
    ("§1 hdr", "python/pyproject.toml", 42, "readme"),
    ("§1 hdr", "python/pyproject.toml", 192, "README"),
    ("§6 vocab", "c/include/srmech.h", 3834, "runs the cascade"),
    ("§6 vocab", "c/src/srmech_explog.c", 9, "runs the cascade"),
    ("§6 vocab", "c/src/srmech_kuramoto.c", 21, "runs the cascade"),
    ("§6 vocab", "c/src/srmech_sqrt.c", 9, "runs the cascade"),
    ("§2.4 _tool_docs", "python/srmech/introspect/_tool_docs.py", 294, "17 executable"),
    ("§4 gen-hdr", "c/src/srmech_tool_registry.c", 1, "GENERATED"),
]


def norm(s):
    return re.sub(r"\s+", " ", s).strip()


def main():
    exact = window = miss = 0
    print("%-16s %-46s %6s %-8s %s" % ("SECTION", "FILE", "LINE", "VERDICT", "NEEDLE"))
    print("-" * 130)
    for sect, rel, ln, needle in CASES:
        full = os.path.join(SRMECH_ROOT, rel)
        if not os.path.exists(full):
            print("%-16s %-46s %6d %-8s %s" % (sect, rel, ln, "NOFILE", needle[:44]))
            miss += 1
            continue
        with open(full, "r", encoding="utf-8", errors="replace") as fh:
            lines = fh.read().split("\n")
        if ln > len(lines):
            print("%-16s %-46s %6d %-8s %s" % (sect, rel, ln, "PASTEOF", needle[:44]))
            miss += 1
            continue
        this = lines[ln - 1]
        win = " ".join(lines[ln - 1:ln + 3])
        n = norm(needle)
        if n in norm(this):
            v = "EXACT"
            exact += 1
        elif n in norm(win):
            v = "WRAP+3"
            window += 1
        else:
            v = "**MISS**"
            miss += 1
        print("%-16s %-46s %6d %-8s %s" % (sect, rel, ln, v, needle[:60]))
    print("-" * 130)
    print("EXACT=%d  WRAP+3=%d  MISS=%d  (total %d)"
          % (exact, window, miss, len(CASES)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
