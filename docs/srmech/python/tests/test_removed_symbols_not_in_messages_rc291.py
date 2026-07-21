"""rc291 (#921) — no runtime message may tell a caller to use a REMOVED op.

rc287 removed the public ``tokenize``. Two ``cooccurrence_*`` argument
guards kept raising ``"... not a raw str — tokenize() it first"``, so for
three rcs the package answered a wrong call with advice that could not be
followed: the op named in the fix had been deleted by the same rc that
should have updated the text. rc289 corrected both sites; rc291 makes the
class of defect mechanically unreachable instead of trusting the next
removal to remember.

**Why the existing ripple gate did not catch it.** That gate follows
CALLERS — imports, dispatch tables, registries, ``__all__``. It is a
reference graph, and a name inside a string literal is not an edge in it.
So a removal can be complete by every automated check the project runs and
still leave the package giving instructions to call something that no
longer exists.

**What this test does instead.** It walks the AST of every module under
``srmech/`` and looks only at ``raise`` sites and ``warnings.warn`` calls —
the strings a user actually receives at runtime — then asserts none of them
tells the reader to call a symbol in :data:`REMOVED`.

Working on the AST rather than on text is what keeps it from being brittle,
and the distinction is the whole design. A plain ``grep tokenize`` over the
tree returns 23 live hits, and every one of them is legitimate: the rc287
migration notice in ``text.py``, the "retired tokenizer" prose explaining
why the Unicode table is now vendored, the before/after example in the
``glyph_stream`` docstring, the ABI-7 removal record in ``_native.py``, the
unrelated ``corpus.tokenizer`` config enum, and the stdlib ``import
tokenize`` in a dozen tests. History must stay readable; a test that forced
those to be deleted would be worse than the defect. Docstrings and comments
are not ``raise`` arguments, so they are excluded structurally rather than
by a list of exceptions that would rot.

The ledger below IS the removal checklist step, in executable form: when an
rc removes a public callable, it adds a row here, and this test then proves
no message points at it.
"""

from __future__ import annotations

import ast
from pathlib import Path
from typing import Dict, List, Tuple

import pytest

PKG = Path(__file__).resolve().parent.parent / "srmech"


#: ``name -> (removed_in_rc, what_to_use_instead)``. Add a row whenever an
#: rc removes a public callable or public constant.
REMOVED: Dict[str, Tuple[str, str]] = {
    "tokenize": ("rc287", "glyph_stream"),
    "DEFAULT_STOPLIST": ("rc287", "(retired; glyph_stream has no stoplist)"),
    # the carrier consolidation — dtype-split + loose-input duplicates
    "dense_matvec_complex": ("carrier consolidation", "mat_matvec"),
    "dense_matmul_complex": ("carrier consolidation", "mat_matmul"),
    "dense_dot_complex": ("carrier consolidation", "mat_dot"),
    "dense_matmul_real": ("carrier consolidation", "mat_matmul"),
    "dense_matvec_real": ("carrier consolidation", "mat_matvec"),
    "dense_dot_real": ("carrier consolidation", "mat_dot"),
    "dense_norm": ("carrier consolidation", "mat_norm"),
    "dense_outer_complex": ("carrier consolidation", "mat_outer"),
    "dense_outer_real": ("carrier consolidation", "mat_outer"),
    "mat_dot_real": ("carrier consolidation", "mat_dot"),
    "mat_dot_complex": ("carrier consolidation", "mat_dot"),
    # rc292 (§102/F1259) — the STOCHASTIC klein4 regime, removed outright
    # rather than replaced: an unreproducible draw does not belong in the
    # public surface. A caller who wants one draws their own bytes.
    "klein4_random": ("rc292", "klein4_encode_bytes"),
}


def _modules() -> List[Path]:
    return sorted(p for p in PKG.rglob("*.py") if "__pycache__" not in p.parts)


def _literal_strings(node: ast.AST) -> List[str]:
    """Every string literal reachable inside ``node``.

    Covers plain constants, f-string literal segments, and ``+``
    concatenation. An f-string's *interpolations* are deliberately not
    evaluated — only their surrounding literal text can carry the advice.
    """
    out: List[str] = []
    for sub in ast.walk(node):
        if isinstance(sub, ast.Constant) and isinstance(sub.value, str):
            out.append(sub.value)
    return out


def _runtime_message_sites(tree: ast.AST):
    """``(lineno, text)`` for each string a user can be shown at runtime."""
    for node in ast.walk(tree):
        if isinstance(node, ast.Raise) and node.exc is not None:
            for s in _literal_strings(node.exc):
                yield node.lineno, s
        elif isinstance(node, ast.Call):
            fn = node.func
            name = getattr(fn, "attr", None) or getattr(fn, "id", None)
            if name == "warn":
                for s in _literal_strings(node):
                    yield node.lineno, s


def test_no_runtime_message_advises_a_removed_symbol():
    """The rc287→rc289 defect, made unreachable.

    A message may *mention* a removed name (an honest "X was removed in
    rc287" is useful); what it may not do is instruct the reader to CALL
    it, which is what ``name(`` in an error string means.
    """
    offences: List[str] = []
    for path in _modules():
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        except SyntaxError as exc:  # pragma: no cover — a real syntax error
            pytest.fail(f"{path}: {exc}")
        for lineno, text in _runtime_message_sites(tree):
            for name, (rc, instead) in REMOVED.items():
                if f"{name}(" in text:
                    rel = path.relative_to(PKG.parent)
                    offences.append(
                        f"{rel}:{lineno} tells the caller to use `{name}()`, "
                        f"removed in {rc} — say `{instead}` instead: "
                        f"{text.strip()[:120]!r}"
                    )
    assert not offences, (
        "runtime message(s) instruct the caller to use a symbol this "
        "package no longer has:\n  " + "\n  ".join(offences)
    )


def test_the_ledger_does_not_go_stale():
    """Every ledger row names something genuinely absent.

    Without this, a row could outlive the removal it records — a name gets
    reintroduced, and the test above starts forbidding correct advice about
    a symbol that exists. The ledger has to stay honest to stay useful.
    """
    import srmech.amsc.hdc as hdc
    import srmech.amsc.laplacian as laplacian
    import srmech.amsc.text as text

    # Every module a ledger row can name must be checked here, or the row is
    # recorded but never validated. rc292 added ``hdc`` for exactly that
    # reason — the klein4_random row would otherwise have been unverifiable.
    still_present = [
        name for name in REMOVED
        if hasattr(text, name) or hasattr(laplacian, name) or hasattr(hdc, name)
    ]
    assert not still_present, (
        f"ledger claims these were removed, but they exist: {still_present}. "
        f"Drop the row — the symbol is back."
    )


def test_the_rc287_sites_now_name_the_replacement():
    """The two messages that carried the defect, pinned by content.

    A regression here is a real user-facing one, so it is worth naming the
    sites rather than relying on the general scan alone.
    """
    import srmech.amsc.text as text

    with pytest.raises(TypeError) as topk:
        text.cooccurrence_topk("a raw string, not tokens")
    with pytest.raises(TypeError) as edges:
        text.cooccurrence_edges("a raw string, not tokens")

    for exc in (topk, edges):
        msg = str(exc.value)
        assert "glyph_stream()" in msg, (
            f"the guard must point at the op that exists; got {msg!r}"
        )
        assert "tokenize()" not in msg, (
            f"the guard still advises the removed op; got {msg!r}"
        )
