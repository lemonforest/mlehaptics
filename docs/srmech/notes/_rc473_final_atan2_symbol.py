"""rc473 final round (`#T1188`): the srmech_atan2 / srmech_kepler_solve / srmech_pin_slot
values at the ctypes SYMBOL that rc473's CHANGELOG quotes, from a committed instrument.

Truth repair 1's CHANGELOG bullet on ``srmech.h`` v26 clause (b) grounded its symbol
figures on a scratch script (``t09_atan2_symbol.py``) that was never committed. This is
the committed replacement: it calls the exported C symbols directly through
``srmech._native.LIB`` (no Python wrapper in the path) and prints status and written
value for the non-finite rows the sentence names.

Refuses to run on a pure cell (exit 2): a symbol figure needs the symbol. It prints the
loaded library path and ABI first, so every figure carries its cell.

Usage (from docs/srmech/python, native cell):
    python3 ../notes/_rc473_final_atan2_symbol.py
numpy-free. No hashlib. No abs().
"""
import ctypes
import sys
from pathlib import Path

sys.path.insert(0, str(Path.cwd()))
from srmech import _native as N  # noqa: E402

if not N.HAS_NATIVE:
    print("pure cell: no symbol to call", N.LOAD_ERROR)
    sys.exit(2)
LIB = N.LIB
LIB.srmech_abi_version.restype = ctypes.c_int
print("lib", getattr(N, "_LIB_PATH", None) or LIB._name, "ABI", LIB.srmech_abi_version())

D = ctypes.c_double
atan2 = LIB.srmech_atan2
atan2.argtypes = [D, D, ctypes.POINTER(D)]
atan2.restype = ctypes.c_int
inf, nan = float("inf"), float("nan")
for y, x in ((inf, inf), (inf, -inf), (-inf, inf), (0.3, inf), (0.3, -inf),
             (inf, 1.0), (nan, 1.0), (1.0, nan)):
    out = D(0.0)
    st = atan2(y, x, ctypes.byref(out))
    print("srmech_atan2(%r, %r) -> (%d, %r)" % (y, x, st, out.value))

solve = LIB.srmech_kepler_solve
solve.argtypes = [D, D, D, ctypes.c_int, ctypes.POINTER(D)]
solve.restype = ctypes.c_int
half_pi = 1.5707963267948966
for e in (0.0549, 0.0):
    for tol in (nan, inf, -inf):
        out = D(half_pi)
        st = solve(half_pi, e, tol, 20, ctypes.byref(out))
        print("srmech_kepler_solve(pi/2, %r, tol=%r, 20) -> (%d, %r)" % (e, tol, st, out.value))

pin = LIB.srmech_pin_slot
pin.argtypes = [D, D, D, ctypes.POINTER(D)]
pin.restype = ctypes.c_int
for args in ((0.3, nan, 1.0), (0.3, inf, 1.0), (0.3, 1.0, nan), (0.0, 1.0, inf), (1.0, 0.0549, 1.0)):
    out = D(0.0)
    st = pin(*args, ctypes.byref(out))
    print("srmech_pin_slot%r -> (%d, %r)" % (args, st, out.value))
