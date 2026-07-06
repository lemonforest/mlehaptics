"""Goal-typing adapter: natural-language goal string -> math carrier-type name.

Maps a free-text goal (e.g. "I want a three-variable polynomial") to one of
the composition planner's carrier-type names:

    "Poly"              univariate polynomial
    "BiPoly"            bivariate polynomial
    "TriPoly"           trivariate polynomial
    "QPoly"             q-analog univariate polynomial
    "QBiPoly"           q-analog bivariate polynomial
    "float"             scalar / number / magnitude / norm / single value
    "Mat"               matrix
    "cayley_dickson:8"  octonion

Returns None when no cue matches — an honest "don't know", never a guess.
A q-cue with THREE variables also returns None (no q-trivariate carrier
exists in the planner's vocabulary). Pure standard library; case-insensitive.
"""

import re

__all__ = ["goal_carrier"]

_OCTONION = re.compile(r"\boctonions?\b")
_MATRIX = re.compile(r"\bmatri(?:x|ces)\b")
_Q_CUE = re.compile(r"\bq(?:-| )(?:analog(?:ue)?s?|series|poly(?:nomial)?s?)\b")
_POLY = re.compile(r"\bpoly(?:nomial)?s?\b")
_THREE_VAR = re.compile(r"\b(?:tri[- ]?variate|(?:three|3)[- ]variables?)\b")
_TWO_VAR = re.compile(r"\b(?:bi[- ]?variate|(?:two|2)[- ]variables?)\b")
_ONE_VAR = re.compile(r"\b(?:uni[- ]?variate|(?:one|1|single)[- ]variables?)\b")
_SCALAR = re.compile(r"\b(?:scalars?|numbers?|magnitudes?|norms?|values?)\b")


def goal_carrier(goal_text: str) -> str | None:
    """Map a natural-language goal string to a carrier-type name, or None."""
    text = goal_text.lower()
    if _OCTONION.search(text):
        return "cayley_dickson:8"
    if _MATRIX.search(text):
        return "Mat"
    n_vars = (3 if _THREE_VAR.search(text) else
              2 if _TWO_VAR.search(text) else
              1 if _ONE_VAR.search(text) else None)
    if _Q_CUE.search(text):
        if n_vars == 3:
            return None  # no q-trivariate carrier — don't downgrade to TriPoly
        return "QBiPoly" if n_vars == 2 else "QPoly"
    if n_vars == 3:
        return "TriPoly"
    if n_vars == 2:
        return "BiPoly"
    if n_vars == 1 or _POLY.search(text):
        return "Poly"
    if _SCALAR.search(text):
        return "float"
    return None


if __name__ == "__main__":
    cases = [
        ("I want a three-variable polynomial", "TriPoly"),
        ("give me the scalar magnitude", "float"),
        ("produce a matrix", "Mat"),
        ("I want an octonion", "cayley_dickson:8"),
        ("a two variable form", "BiPoly"),
        ("the norm as a number", "float"),
        ("something vague", None),
        ("just a polynomial", "Poly"),
        ("a univariate polynomial", "Poly"),
        ("a single variable polynomial", "Poly"),
        ("a 2 variable polynomial", "BiPoly"),
        ("a 3-variable polynomial", "TriPoly"),
        ("a trivariate polynomial", "TriPoly"),
        ("a q-analog polynomial", "QPoly"),
        ("a q-series in one variable", "QPoly"),
        ("a q-analog two-variable polynomial", "QBiPoly"),
        ("a q-analog three-variable polynomial", None),
        ("a single value", "float"),
        ("MATRICES please", "Mat"),
    ]
    failures = 0
    for text, want in cases:
        got = goal_carrier(text)
        ok = got == want
        failures += 0 if ok else 1
        print(f"[{'ok' if ok else 'FAIL'}] {text!r} -> {got!r} (want {want!r})")
    if failures:
        raise SystemExit(f"{failures} case(s) failed")
    print(f"all {len(cases)} cases passed")
