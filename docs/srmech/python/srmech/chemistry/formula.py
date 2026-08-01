"""``srmech.chemistry.formula`` — the chemical-formula tokenizer.

:func:`parse_formula` turns a Hill-style formula string (``"Ca3(PO4)2"``) into
an element-count dict (``{"Ca": 3, "P": 2, "O": 8}``), the ergonomic input
:func:`srmech.chemistry.reactions.balance_reaction` accepts alongside a raw
element-count dict and an element×species ``QMat``.

Grammar (a bounded left-to-right scan with an explicit paren-multiplier
STACK — no recursion, so the algorithm maps 1:1 onto a future JPL-clean C
peer ``srmech_parse_formula``):

    formula   := group+
    group     := element count? | '(' formula ')' count?
    element   := [A-Z][a-z]*            ("Ca", "Cl", "O", "H")
    count     := [0-9]+                 (absent → 1)

**Class F/G** (Render / byte-search) — a template-shaped placeholder scan, the
same primitive family as ``srmech_template_render``. It is pure Python this rc
(`#T1050`); its C peer is a tracked immediate follow-up (see the module note in
``srmech.chemistry.reactions`` and the rc379 CHANGELOG entry).

DEFERRED (raised on, not silently mis-parsed): hydrate dots (``·`` / ``*``),
charges (``^2+`` / trailing ``+`` / ``-``), and isotope/bracket syntax
(``[13C]``). These are out of scope for `#T1050` and fail with a clear message
rather than corrupting the element counts.
"""
from __future__ import annotations

import ctypes

from .. import _native

__all__ = ["parse_formula"]

# Output symbol-buffer stride, mirroring SRMECH_ELEM_SYM_CAP in srmech.h.
_ELEM_SYM_CAP = 8

# ASCII-only classifiers on purpose: str.isupper()/isdigit() accept Unicode
# (e.g. a subscript '₂' is .isdigit() == True but int('₂') raises), which would
# turn a paste-mangled formula into a confusing failure deep in int().
_UPPER = frozenset("ABCDEFGHIJKLMNOPQRSTUVWXYZ")
_LOWER = frozenset("abcdefghijklmnopqrstuvwxyz")
_DIGIT = frozenset("0123456789")

# Deferred-syntax sentinels → a clear, specific error (never a silent mis-parse).
_DEFERRED = (
    ("·", "a hydrate dot ('·')"),
    ("*", "a hydrate dot ('*')"),
    ("^", "a charge ('^')"),
    ("[", "an isotope/bracket ('[')"),
    ("]", "an isotope/bracket (']')"),
    ("{", "a brace ('{')"),
    ("}", "a brace ('}')"),
)


def _read_count(s: str, i: int) -> tuple[int, int]:
    """Read an ASCII-digit run at ``s[i:]`` → ``(count, new_i)``; an absent run
    is the implicit multiplicity 1 (``H2O`` has one O)."""
    n = len(s)
    j = i
    while j < n and s[j] in _DIGIT:
        j += 1
    if j == i:
        return 1, i
    return int(s[i:j]), j


def parse_formula(formula: str) -> dict:
    """Parse a chemical formula string into an ``{element: count}`` dict.

    Handles multi-letter element symbols (``"Ca"``, ``"Cl"``), implicit and
    explicit counts (``"O"`` → 1, ``"O2"`` → 2), and arbitrarily NESTED
    parenthesised groups with a trailing multiplier (``"Ca3(PO4)2"`` →
    ``{"Ca": 3, "P": 2, "O": 8}``; ``"(OH)2"`` → ``{"O": 2, "H": 2}``).

    Args:
        formula: the formula string. Element = an uppercase letter then zero or
            more lowercase; count = a run of ASCII digits (default 1); groups
            nest with ``(`` … ``)`` and an optional trailing count.

    Returns:
        ``dict[str, int]`` mapping each element symbol to its total count.
        Repeated occurrences accumulate (``"CH3CH3"`` → ``{"C": 2, "H": 6}``).

    Raises:
        TypeError: ``formula`` is not a ``str``.
        ValueError: unbalanced parentheses, an unexpected character, an empty
            formula, or DEFERRED syntax — hydrate dots (``·`` / ``*``),
            charges (``^``), isotope/bracket notation (``[`` … ``]``). These are
            out of `#T1050` scope and are rejected, never silently mis-parsed.

    This is **Class F/G** (Render / byte-search): a bounded placeholder scan, the
    same primitive family as the shipped ``srmech_template_render``. Pure Python
    this rc; the JPL-clean C peer is a tracked follow-up.
    """
    if not isinstance(formula, str):
        raise TypeError(
            f"parse_formula: expected a str formula, got {type(formula).__name__}")
    for token, what in _DEFERRED:
        if token in formula:
            raise ValueError(
                f"parse_formula: {what} is not supported yet (`#T1050` defers "
                f"hydrates / charges / isotopes); got {formula!r}")

    native = _parse_formula_c(formula)
    if native is not None:
        return native
    return _parse_formula_pure(formula)


def _parse_formula_c(formula: str):
    """Native fast path over ``srmech_parse_formula`` → the element-count dict,
    or ``None`` when the C symbol is absent, the formula is non-ASCII, or the C
    kernel declines (malformed / capacity / overflow) — in every ``None`` case
    the pure body below is the complete, byte-identical alternative (it also
    raises the precise structural error for malformed input)."""
    if not _native.has_native_parse_formula():
        return None
    try:
        data = formula.encode("ascii")
    except UnicodeEncodeError:
        return None                       # non-ASCII → pure path raises precisely
    n = len(data)
    ws_len = int(_native.LIB.srmech_parse_formula_ws_bound(ctypes.c_size_t(n)))
    ws = ctypes.create_string_buffer(ws_len if ws_len > 0 else 1)
    out_cap = n + 1
    out_syms = ctypes.create_string_buffer(out_cap * _ELEM_SYM_CAP)
    out_counts = (ctypes.c_int64 * out_cap)()
    out_n = ctypes.c_size_t(0)
    rc = _native.LIB.srmech_parse_formula(
        data, ctypes.c_size_t(n),
        ctypes.cast(ws, ctypes.c_void_p), ctypes.c_size_t(len(ws)),
        ctypes.cast(out_syms, ctypes.POINTER(ctypes.c_char)),
        ctypes.cast(out_counts, ctypes.POINTER(ctypes.c_int64)),
        ctypes.c_size_t(out_cap),
        ctypes.byref(out_n),
    )
    if rc != _native.SRMECH_OK:
        return None                       # malformed / overflow → pure path
    result = {}
    raw = out_syms.raw
    for i in range(out_n.value):
        chunk = raw[i * _ELEM_SYM_CAP:(i + 1) * _ELEM_SYM_CAP]
        symbol = chunk.split(b"\x00", 1)[0].decode("ascii")
        result[symbol] = int(out_counts[i])
    return result


def _parse_formula_pure(formula: str) -> dict:
    """The complete pure-Python body (and the parity oracle): an explicit
    paren-multiplier stack, no recursion — the algorithm the C peer mirrors. The
    caller (:func:`parse_formula`) has already handled the type / deferred-syntax
    checks; this body raises the precise STRUCTURAL errors."""
    # Explicit stack of partial element-count dicts. '(' pushes a fresh frame;
    # ')' pops it, multiplies by the trailing count, and merges into the parent.
    stack: list = [{}]
    i, n = 0, len(formula)
    while i < n:
        c = formula[i]
        if c == "(":
            stack.append({})
            i += 1
        elif c == ")":
            i += 1
            mult, i = _read_count(formula, i)
            top = stack.pop()
            if not stack:
                raise ValueError(
                    f"parse_formula: unbalanced ')' at position {i - 1} in "
                    f"{formula!r}")
            parent = stack[-1]
            for el, cnt in top.items():
                parent[el] = parent.get(el, 0) + cnt * mult
        elif c in _UPPER:
            j = i + 1
            while j < n and formula[j] in _LOWER:
                j += 1
            element = formula[i:j]
            count, i = _read_count(formula, j)
            frame = stack[-1]
            frame[element] = frame.get(element, 0) + count
        elif c in (" ", "\t"):
            i += 1
        else:
            raise ValueError(
                f"parse_formula: unexpected character {c!r} at position {i} in "
                f"{formula!r} (an element must start with an uppercase letter)")

    if len(stack) != 1:
        raise ValueError(
            f"parse_formula: unbalanced '(' in {formula!r} "
            f"({len(stack) - 1} group(s) never closed)")
    result = stack[0]
    if not result:
        raise ValueError(f"parse_formula: no element parsed from {formula!r}")
    return result
