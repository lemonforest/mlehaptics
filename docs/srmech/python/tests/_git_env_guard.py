"""The suite may not reach a repository the ENVIRONMENT names. (rc473 final round, `#T1188`)

Importing this module REMOVES every repository-selecting git variable from
``os.environ`` (the list, and why each name is on it, is
:data:`tests._git_env.GIT_REPO_LOCAL_ENV`). ``tests/conftest.py`` imports it
directly after ``import pytest`` — before collection, so before any test module
that runs git at import time (``test_shell_line_loop_rc468`` computes a
``skipif`` from ``git rev-parse`` at module level). Every in-process
``subprocess`` call inherits ``os.environ``, and so does every child process —
the nested pytest, ``tools/hooks/check_hooks.py``, the hooks it spawns — so after
this import no git anywhere in a pytest run can be steered to a repository by an
exported variable. Each xdist worker imports ``conftest`` and scrubs its own
copy.

It is also loadable as a plugin, ``-p tests._git_env_guard`` (with the package
root on ``PYTHONPATH``), which is how its can-fail test drives the SAME scrub
outside this tree's conftest: a planted one-line writer must move a sentinel
repository unguarded and must not move it guarded.

What it does NOT do: it does not replace a lookup. A git that could only read
the checkout because ``GIT_DIR`` was exported cannot read it after this runs;
the tools resolve the checkout per invocation instead
(:func:`tests._git_env.git_location_args`). And it reaches only pytest runs —
``check_hooks.py`` scrubs its own fixture and hook children for the operator who
runs it by hand.

numpy-free. No ``abs()``. No assertions (``test_assert_contract_gate_rc433``
scans ``tests/*.py``).
"""

from __future__ import annotations

import os

from . import _git_env

#: What the scrub removed from THIS process, name to value — ``{}`` in an
#: ordinary run. Printed by :func:`pytest_report_header` when loaded with ``-p``.
REMOVED = _git_env.scrub(os.environ)


def pytest_report_header(config):  # noqa: D401 - pytest hook; only under -p
    names = sorted(REMOVED)
    return "_git_env_guard removed: %s" % (", ".join(names) if names else "nothing")
