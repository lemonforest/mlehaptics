"""rc473 A3 — SRMECH_NODISCARD, measured on a PLANTED header (`#T1188`).

WHAT THIS MEASURES, AND WHY IT IS A SCRATCH MEASUREMENT
------------------------------------------------------
rc473 adds ``SRMECH_NODISCARD`` — ``__attribute__((warn_unused_result))`` on
gcc / clang, empty elsewhere — to 14 declarations in ``c/include/srmech.h``.
The proof that the attribute lands on every callee is that the pedantic build,
with ``c/src`` **still unmodified**, produces exactly as many
``-Wunused-result`` diagnostics as the ``(void)srmech_*`` grep finds, at the
same ``file:line`` set.

That read does NOT require the tree to be modified, and committing it would be
worse than not committing it. With ``-Werror`` the diagnostics are errors, so
the **Build** step of the pedantic job fails on all three OSes, ``libsrmech``
and every test binary are never produced, and neither ctest nor the
asserts-live smoke can run at all. ``cmake --build -- -k`` keeps going and
still produces no library. So "the intermediate is expected red" is not a
statable position: it is a commit at which the rc cannot be measured by any
instrument it ships. The header and all 24 call-site repairs therefore land in
ONE commit, and this file is how the 24 is read without one.

The plant is a COPY of ``c/include`` with the attribute inserted; the repo is
untouched, and the script asserts that before it exits.

Usage::

    uv run --python 3.12 --no-project --offline \\
        python docs/srmech/notes/_rc473_nodiscard_plant.py

Output is NDJSON on stdout.
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_SRMECH = _HERE.parent
_C_INCLUDE = _SRMECH / "c" / "include"
_C_SRC = _SRMECH / "c" / "src"

#: The live pedantic flags, read from build/CMakeFiles/srmech.dir/flags.make on
#: this cell rather than quoted from a document:
#:   C_FLAGS = -O3 -DNDEBUG -std=c11 -fPIC -Wall -Wextra -Wpedantic -O2 -Werror
#: -Werror is dropped here ON PURPOSE: this run must COUNT diagnostics, and
#: -Werror stops the compile at the first one. The -Werror form is measured
#: separately by _ERROR_PROBE below.
_FLAGS = ["-O3", "-DNDEBUG", "-std=c11", "-fPIC",
          "-Wall", "-Wextra", "-Wpedantic", "-O2"]

#: The seven callees with live discards, plus the seven clean peers. Tagging
#: the clean seven costs nothing today (0 discards) and closes the family: a
#: future discard on any of them fails to compile instead of shipping.
_VIOLATED = (
    "srmech_sin", "srmech_cos", "srmech_atan", "srmech_atan2",
    "srmech_exp", "srmech_log", "srmech_rational_sqrt",
)
_CLEAN_PEERS = (
    "srmech_sin_q61", "srmech_cos_q61", "srmech_atan_q61",
    "srmech_winding_fold", "srmech_hypercomplex_exp_q61",
    "srmech_hypercomplex_couple_q61", "srmech_hypercomplex_couple_turn_q61",
)
_ROSTER = _VIOLATED + _CLEAN_PEERS

#: The grep the population is cross-checked against.
_DISCARD_RE = re.compile(
    r"\(void\)srmech_(?:sin|cos|atan|atan2|exp|log|rational_sqrt)\("
)

_MACRO_BLOCK = """
/* ------------------------------------------------------------------ *
 * SRMECH_NODISCARD  (rc473 PLANT — scratch only, not the shipped text)
 * ------------------------------------------------------------------ */
#if defined(__GNUC__) || defined(__clang__)
#define SRMECH_NODISCARD __attribute__((warn_unused_result))
#else
#define SRMECH_NODISCARD
#endif
"""

_ANCHOR = "#define SRMECH_THREAD_LOCAL\n#endif\n"


def _plant(dest: Path) -> tuple[Path, int]:
    """Copy c/include to dest and tag the roster. Returns (include dir, tagged)."""
    include = dest / "include"
    shutil.copytree(_C_INCLUDE, include)
    header = include / "srmech.h"
    text = header.read_text(encoding="utf-8")

    if _ANCHOR not in text:
        raise SystemExit(
            "plant anchor not found: the SRMECH_THREAD_LOCAL block has moved. "
            "Re-point the anchor; do not loosen it."
        )
    text = text.replace(_ANCHOR, _ANCHOR + _MACRO_BLOCK, 1)

    tagged = 0
    for name in _ROSTER:
        pattern = re.compile(
            r"^(srmech_status_t\s+%s\()" % re.escape(name), re.M
        )
        text, n = pattern.subn(r"SRMECH_NODISCARD \1", text)
        if n != 1:
            raise SystemExit(
                f"expected exactly 1 declaration of {name}; matched {n}. "
                "A declaration spelled differently is a silent hole in the "
                "attribute coverage, which is the failure this run exists to "
                "make visible."
            )
        tagged += n
    header.write_text(text, encoding="utf-8")
    return include, tagged


def _compile_all(include: Path) -> list[str]:
    """Compile every c/src/*.c against the planted header; return stderr lines."""
    lines: list[str] = []
    for src in sorted(_C_SRC.glob("*.c")):
        proc = subprocess.run(
            ["gcc", *_FLAGS, f"-I{include}", f"-I{_C_SRC}", "-c",
             str(src), "-o", "/dev/null"],
            capture_output=True, text=True, check=False,
        )
        lines.extend(proc.stderr.splitlines())
    return lines


def _classify(lines: list[str]) -> tuple[set[str], list[str]]:
    """Split diagnostics into unused-result sites and everything else."""
    sites: set[str] = set()
    others: list[str] = []
    for line in lines:
        if "[-Wunused-result]" in line:
            head = line.split(":")
            if len(head) >= 3:
                sites.add("%s:%s" % (Path(head[0]).name, head[1]))
            continue
        if re.search(r":\d+:\d+: (warning|error|note):", line):
            if ": note:" in line:
                continue
            others.append(line)
    return sites, others


def _grep_sites() -> set[str]:
    sites: set[str] = set()
    for src in sorted(_C_SRC.glob("*.c")):
        for n, line in enumerate(src.read_text(encoding="utf-8").splitlines(), 1):
            if _DISCARD_RE.search(line):
                sites.add("%s:%d" % (src.name, n))
    return sites


def main() -> int:
    before = (_C_INCLUDE / "srmech.h").read_bytes()

    with tempfile.TemporaryDirectory(prefix="rc473_plant_") as tmp:
        include, tagged = _plant(Path(tmp))
        print(json.dumps({"kind": "plant", "declarations_tagged": tagged,
                          "roster": len(_ROSTER)}, sort_keys=True))

        sites, others = _classify(_compile_all(include))
        grep = _grep_sites()

        print(json.dumps({
            "kind": "measurement",
            "unused_result_sites": len(sites),
            "grep_sites": len(grep),
            "sets_equal": sites == grep,
            "compiler_only": sorted(sites - grep),
            "grep_only": sorted(grep - sites),
            "other_diagnostics": len(others),
        }, sort_keys=True))
        for line in others[:20]:
            print(json.dumps({"kind": "other_diagnostic", "line": line}))
        for site in sorted(sites):
            print(json.dumps({"kind": "site", "at": site}, sort_keys=True))

        # The -Werror form, on one real file, so the CI failure mode is on the
        # record rather than inferred from the warning form.
        proc = subprocess.run(
            ["gcc", *_FLAGS, "-Werror", f"-I{include}", f"-I{_C_SRC}", "-c",
             str(_C_SRC / "srmech_kepler.c"), "-o", "/dev/null"],
            capture_output=True, text=True, check=False,
        )
        first = next((ln for ln in proc.stderr.splitlines() if "error:" in ln), "")
        print(json.dumps({
            "kind": "werror_probe",
            "file": "srmech_kepler.c",
            "returncode": proc.returncode,
            "first_error": first,
        }, sort_keys=True))

    after = (_C_INCLUDE / "srmech.h").read_bytes()
    print(json.dumps({
        "kind": "repo_untouched",
        "header_bytes_identical": before == after,
    }, sort_keys=True))
    if before != after:
        print("PLANT LEAKED INTO THE REPO", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
