"""Permanent zero-numpy ratchet (v0.31.0rc4 capstone).

`ephemerides-spectral` is numpy-FREE: `pip install ephemerides-spectral`
pulls NO numpy, and the shipped package imports + runs with numpy not
installed at all. This guard fails CI if numpy ever sneaks back into the
package tree.

Two layers:

1. **Static scan** — walk every shipped ``ephemerides_spectral/**.py`` and
   assert there is no ``import numpy`` statement and no executable ``np.``
   attribute access. Comments and string literals (docstrings) are
   IGNORED via the tokenizer, so prose like "the old ``np.exp`` path" is
   allowed; only real code tokens trip the ratchet.

2. **Import-time probe** — importing ``ephemerides_spectral`` and its core
   modules must NOT import numpy. (When numpy is installed for some other
   reason, this checks the package didn't pull it in itself.)
"""

from __future__ import annotations

import io
import tokenize
from pathlib import Path

import pytest

_PKG_DIR = Path(__file__).resolve().parents[1] / "ephemerides_spectral"


def _python_files() -> list[Path]:
    out: list[Path] = []
    for p in _PKG_DIR.rglob("*.py"):
        if "__pycache__" in p.parts:
            continue
        out.append(p)
    return out


def _numpy_offences(path: Path) -> list[str]:
    """Return executable numpy offences in *path* (ignoring strings/comments).

    Catches:
      * ``import numpy`` / ``import numpy as np`` / ``from numpy import ...``
      * any ``np.<attr>`` attribute access in code (NAME 'np' followed by '.')
    """
    src = path.read_text(encoding="utf-8")
    offences: list[str] = []
    try:
        toks = list(tokenize.generate_tokens(io.StringIO(src).readline))
    except (tokenize.TokenError, IndentationError, SyntaxError) as exc:  # pragma: no cover
        return [f"tokenize error: {exc}"]

    for i, tok in enumerate(toks):
        if tok.type != tokenize.NAME:
            continue
        # `import numpy` / `from numpy import ...`
        if tok.string == "numpy":
            offences.append(f"line {tok.start[0]}: NAME 'numpy' in code")
            continue
        # `np.<attr>` — NAME 'np' immediately followed by an OP '.'
        if tok.string == "np":
            # Look at the next significant token.
            j = i + 1
            while j < len(toks) and toks[j].type in (
                tokenize.NL, tokenize.COMMENT, tokenize.INDENT, tokenize.DEDENT,
            ):
                j += 1
            if j < len(toks) and toks[j].type == tokenize.OP and toks[j].string == ".":
                offences.append(f"line {tok.start[0]}: executable 'np.' access")
    return offences


def test_no_executable_numpy_in_package_tree() -> None:
    """No shipped package module may import numpy or use an executable np.* token."""
    all_offences: dict[str, list[str]] = {}
    for path in _python_files():
        off = _numpy_offences(path)
        if off:
            rel = path.relative_to(_PKG_DIR).as_posix()
            all_offences[rel] = off
    assert not all_offences, (
        "numpy crept back into the package tree (executable tokens; "
        "comments/docstrings are allowed):\n"
        + "\n".join(
            f"  {f}:\n    " + "\n    ".join(v)
            for f, v in sorted(all_offences.items())
        )
    )


def test_importing_package_does_not_import_numpy() -> None:
    """Importing ephemerides_spectral + its core modules must not pull numpy.

    If numpy is already imported by the test runner / a sibling, we can't
    prove the package didn't import it — skip in that case. The hard
    numpy-ABSENT gate is the separate clean-venv suite run (where
    importing numpy raises). Here we assert the modules import cleanly.
    """
    import importlib
    import sys

    if "numpy" in sys.modules:
        pytest.skip("numpy already imported by the runner; clean-venv run is the hard gate")

    # Importing these must succeed without bringing in numpy.
    for mod in (
        "ephemerides_spectral",
        "ephemerides_spectral.bridge",
        "ephemerides_spectral._native_bip",
        "ephemerides_spectral._research.bip_instrument",
        "ephemerides_spectral._research.bip_hd_lift",
        "ephemerides_spectral._research.laplacian",
        "ephemerides_spectral._research.ephemeris_reference_instrument",
    ):
        importlib.import_module(mod)
    assert "numpy" not in sys.modules, (
        "importing ephemerides_spectral pulled in numpy — a dependency "
        "leaked numpy back into the import graph."
    )
