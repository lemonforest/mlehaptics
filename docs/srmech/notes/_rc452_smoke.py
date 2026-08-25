"""rc452 (`#T1166`) scratch smoke — the acceptance/return contract, executed.

Run from ``docs/srmech/python`` with ``PYTHONPATH=.``.
"""
from srmech.math import rational as R
from srmech.math.q import Q
from srmech import _native

print("native:", _native.HAS_NATIVE, _native.NATIVE_ABI_VERSION,
      _native.EXPECTED_ABI_VERSION, _native.LOAD_ERROR)

print("\n-- CLOSURE: an op consumes its own output (both spellings mixed)")
s = R.rational_add((1, 2), (1, 3))
print("  rational_add((1,2),(1,3))        ->", repr(s), type(s).__name__)
print("  rational_add(Q, (0,1))           ->", repr(R.rational_add(s, (0, 1))))
print("  rational_add(Q, Q)               ->", repr(R.rational_add(s, s)))
print("  rational_mul(Q, [2,1])           ->", repr(R.rational_mul(s, [2, 1])))
print("  rational_div(Q, Q)               ->", repr(R.rational_div(s, s)))
print("  rational_pow_uint(Q, 2)          ->", repr(R.rational_pow_uint(s, 2)))
print("  rational_pow_uint((0,1), 0)      ->", repr(R.rational_pow_uint((0, 1), 0)))

print("\n-- ERROR CLASSES (the three rows test_input_contracts_rc431 pins)")
for call, args in [("rational_div", (5, (1, 1))),
                   ("rational_div", ((1, -2), (1, 1))),
                   ("rational_div", ((1, 2), (0, 1))),
                   ("rational_div", (("a", "b"), (1, 1))),
                   ("rational_add", (1, (1, 1))),
                   ("rational_pow_uint", ((1, 2), -1)),
                   ("rational_pow_uint", (5, 2)),
                   ("rational_add", ((1, 2, 3), (1, 1)))]:
    try:
        getattr(R, call)(*args)
        print("  %-18s %-22r -> NO RAISE" % (call, args))
    except Exception as exc:                             # noqa: BLE001
        print("  %-18s %-22r -> %s: %s" % (call, args, type(exc).__name__, exc))

print("\n-- A BARE INT AND A Fraction MUST STILL BE REFUSED (C parity)")
import fractions
for bad in (5, fractions.Fraction(1, 2)):
    try:
        R.rational_add(bad, (1, 1))
        print("  %-24r -> NO RAISE  <-- widened past the C arm" % (bad,))
    except TypeError as exc:
        print("  %-24r -> TypeError: %s" % (bad, exc))

print("\n-- NEGATIVE CONTROLS of the derived predicate (must STAY tuples)")
from srmech import cascade
print("  best_rational(3,4,10)   ->", type(R.best_rational(3, 4, 10)).__name__)
print("  pair(3,4)               ->", type(cascade.pair(3, 4)).__name__)
print("  pin_slot_at_zero(-7)    ->", type(cascade.pin_slot_at_zero(-7)).__name__)
print("  jacobi(1,2,1,2,4)       ->", R.jacobi_sncndn_series_truncate(1, 2, 1, 2, 4))

print("\n-- FORCED-PURE jacobi (the pure body, not the C peer)")
saved = (_native.HAS_NATIVE, _native.LIB)
_native.HAS_NATIVE, _native.LIB = False, None
try:
    print("  jacobi pure             ->", R.jacobi_sncndn_series_truncate(1, 2, 1, 2, 4))
    print("  exp pure                ->", repr(R.exp_series_truncate(1, 1, 10)))
finally:
    _native.HAS_NATIVE, _native.LIB = saved

print("\n-- THE HEADLINE, PYTHON HALF: rational_add -> reorient(-1)")
print("  reorient(rational_add((1,2),(1,3)), -1) ->",
      repr(cascade.reorient(R.rational_add((1, 2), (1, 3)), orientation=-1)))
