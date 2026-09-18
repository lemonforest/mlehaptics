"""rc476 (`#T1188`) D1 — the cell banner every measuring process prints first.

Run from ``docs/srmech/python``::

    PYTHONDONTWRITEBYTECODE=1 python3 ../notes/_rc476_banner.py

Prints the loaded package file, the library path and sha256, the version, the
native flags and the ABI pair, so no number in this round can be attributed to
the wrong cell.  Nothing here writes.
"""
from __future__ import annotations

import hashlib
import pathlib
import sys


def main() -> int:
    import srmech
    from srmech import _native

    lib = getattr(_native, "_LIB_PATH", None) or getattr(_native, "LIB_PATH", None)
    if lib is None:
        # fall back to the bundled search directory
        cand = pathlib.Path(srmech.__file__).resolve().parent / "_native" / "libsrmech.so"
        lib = cand if cand.exists() else None
    digest = "n/a"
    if lib is not None and pathlib.Path(lib).exists():
        digest = hashlib.sha256(pathlib.Path(lib).read_bytes()).hexdigest()[:16]
    print(
        "CELL",
        srmech.__version__,
        "HAS_NATIVE",
        _native.HAS_NATIVE,
        "NATIVE_ABI",
        getattr(_native, "NATIVE_ABI_VERSION", None),
        "EXPECTED_ABI",
        getattr(_native, "EXPECTED_ABI_VERSION", None),
        "LOAD_ERROR",
        getattr(_native, "LOAD_ERROR", None),
    )
    print("  pkg ", srmech.__file__)
    print("  lib ", lib, "sha256", digest)
    print("  q61 ", _native.has_native_trans_q61())
    return 0


if __name__ == "__main__":
    sys.exit(main())
