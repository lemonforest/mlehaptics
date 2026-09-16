"""rc473 instrument round (`#T1188`): cell identity and authenticity, printed before any figure.

Usage:  python3 notes/_rc473_instr_auth.py <python root>   (the directory holding srmech/)

Prints the interpreter, ``srmech.__file__``, ``srmech._native.__file__``, the version,
HAS_NATIVE and whether numpy is imported. On a native cell it also prints the loaded
library's path and sha256 prefix, its ABI and C version, and the rc473 proof line:
``srmech_rational_sqrt(NaN)`` at the ctypes symbol must return status 2 (an rc472
library returns 0). Exit 3 when the cell is native and not authentic; 0 otherwise.
Read-only. numpy-free; no abs(). The library digest uses srmech.amsc.format.sha256_bytes.
"""
import ctypes
import sys

sys.path.insert(0, sys.argv[1])

import srmech  # noqa: E402
from srmech import _native as nat  # noqa: E402

print("python          :", sys.version.split()[0])
print("srmech.__file__ :", srmech.__file__)
print("_native.__file__:", nat.__file__)
print("version         :", srmech.__version__)
print("HAS_NATIVE      :", nat.HAS_NATIVE)
print("numpy imported  :", "numpy" in sys.modules)
if nat.HAS_NATIVE:
    from srmech.amsc.format import sha256_bytes

    path = getattr(nat, "_LIB_PATH", None) or getattr(nat.LIB, "_name", None)
    print("lib path        :", path)
    with open(path, "rb") as fh:
        print("lib sha256      :", sha256_bytes(fh.read())[:16])
    nat.LIB.srmech_abi_version.restype = ctypes.c_int
    nat.LIB.srmech_version.restype = ctypes.c_char_p
    abi, ver = nat.LIB.srmech_abi_version(), nat.LIB.srmech_version().decode()
    fn = nat.LIB.srmech_rational_sqrt
    fn.argtypes = [ctypes.c_double, ctypes.POINTER(ctypes.c_double)]
    fn.restype = ctypes.c_int
    out = ctypes.c_double(0.0)
    status = fn(float("nan"), ctypes.byref(out))
    print("abi / c version :", abi, ver)
    print("AUTH srmech_rational_sqrt(NaN) -> status", status)
    authentic = status == 2 and abi == 26 and ver == "0.9.0rc473"
    print("AUTHENTIC       :", authentic)
    if not authentic:
        sys.exit(3)
