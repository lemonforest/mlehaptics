"""Hardening (iv): float operands (exact-rational parse; float only at the call boundary),
NAMED operands matched against the tool's own declared parameter names (schema-driven),
passed as KWARGS (keyword-only-safe). srmech returns the exact rational; we range-check it."""
import re
import siona


def test_float_and_named_kwargs():
    s = siona.Session()
    _, tag, out = s.turn("compute the cos of 1.5 with 12 terms")
    assert tag == "srmech"
    assert "cos(1.5, terms=12)" in out, out
    m = re.search(r"= (\d+)/(\d+)", out)   # srmech 0.9.0rc+ cos returns the EXACT rational
    if m:
        v = int(m.group(1)) / int(m.group(2))  # display-boundary collapse, test-side only
    else:                                       # older srmech floors return a float -- same value check
        m2 = re.search(r"= (0\.\d+)", out)
        assert m2, out
        v = float(m2.group(1))
    assert 0.069 < v < 0.072, v            # cos(1.5 rad) = 0.0707...
