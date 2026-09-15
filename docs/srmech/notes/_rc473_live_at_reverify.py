"""rc473 — re-verify every `Live at` stamp BEFORE moving it (`#T1188`).

``tests/test_notebook_currency_rc420::test_live_at_rc_stamps_name_the_pinned_release``
requires the notebook's ``Live at rcNNN`` stamps to name the pinned release,
and its failure text states the obligation that comes with moving one: *"A
`Live at` sentence asserts a CURRENT value; re-verify it and move the stamp."*
Moving the token without re-reading the value is the exact defect its sibling
docstring records — *"rc447 shipped a false ABI stamp: fresh rcNNN token, stale
number."*

This prints each stamped quantity from the live tree, so the move is a
measurement rather than a find-and-replace.

Usage::

    PYTHONPATH=docs/srmech/python uv run --python 3.12 --no-project --offline \\
        python docs/srmech/notes/_rc473_live_at_reverify.py
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import srmech
from srmech import _native
from srmech.introspect.tool_schema import get_tool_schema

_HEADER = Path(__file__).resolve().parent.parent / "c" / "include" / "srmech.h"


def main() -> int:
    desc = srmech.describe()

    print(json.dumps({
        "stamp": "notebook 817 / 5463 — tool schema registry total",
        "len_get_tool_schema_tools": len(get_tool_schema().tools),
        "describe_tools_total": desc["tools"]["total"],
        "equal": len(get_tool_schema().tools) == desc["tools"]["total"],
    }, sort_keys=True))

    cat = desc["cascade_catalog"]
    print(json.dumps({
        "stamp": "notebook 5455 — cascade catalog",
        "total": cat.get("total"),
        "executable": cat.get("executable"),
        "leaf": cat.get("leaf"),
        "c_runnable": cat.get("c_runnable"),
    }, sort_keys=True))

    macro = re.search(r"^#define SRMECH_ABI_VERSION (\d+)",
                      _HEADER.read_text(encoding="utf-8"), re.M)
    print(json.dumps({
        "stamp": "notebook 5464 — ABI",
        "macro_in_srmech_h": int(macro.group(1)) if macro else None,
        "expected_abi_version": _native.EXPECTED_ABI_VERSION,
        "native_abi_version": _native.NATIVE_ABI_VERSION,
        "has_native": _native.HAS_NATIVE,
    }, sort_keys=True))

    print(json.dumps({
        "stamp": "python/README.md:188 — worked native_status block",
        "srmech_version": srmech.__version__,
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
