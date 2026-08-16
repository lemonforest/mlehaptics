"""rc407 (`#T1076`) — ``srmech.introspect.__all__`` must be the export list.

TWO DEFECTS, ONE LIST. Through rc406 ``srmech/introspect/__init__.py`` closed
with a 16-name ``__all__`` that was wrong in both directions.

*It exported private names.* ``_PublishHandle`` and ``_maybe_auto_publish``
both sat in it. A leading underscore and a place in the public export list are
a contradiction, and the export bought nothing: the only in-tree consumer,
``srmech/__init__.py``, reaches ``_maybe_auto_publish`` by direct attribute
access — a path ``__all__`` does not govern — so removing them changes no
working call.

*It omitted the surfaces the package exists to publish.* ``tool_schema`` (the
per-op registry), ``carrier_schema`` (the operand carriers) and
``responsion_schema`` were all absent. Worse than absent for two of them: with
nothing importing them eagerly, plain ``srmech.introspect.carrier_schema``
raised ``AttributeError``. ``tool_schema`` only ever worked because
``srmech/__init__.py`` imports it as a side effect of package init.

WHY LAZY. Measured on this tree (WSL2, numpy-absent CPython, 5 fresh
interpreters): ``import srmech.introspect`` costs ~1.46 s and the two
submodules cost a further ~500 ms on top — ``carrier_schema`` alone ~470-600 ms,
``responsion_schema`` ~18 ms. Eager binding would tax every consumer ~34% for
surfaces most never touch, so rc407 binds them with a PEP-562 module
``__getattr__``. Both entry paths must work off that one mechanism, and this
file pins both.

FAILS BEFORE / PASSES AFTER: on the rc406 ``__init__.py`` every test here fails
except the ``import *`` binding of ``describe`` — ``__all__`` lacks all three
names, still carries the two underscored ones, and the fresh-interpreter
``getattr`` probe raises ``AttributeError`` for ``carrier_schema`` and
``responsion_schema``.
"""

import subprocess
import sys

import srmech.introspect as I

_SCHEMA_SURFACES = {"tool_schema", "carrier_schema", "responsion_schema"}


def test_the_three_schema_surfaces_are_exported():
    assert _SCHEMA_SURFACES <= set(I.__all__), (
        "the schema surfaces srmech.introspect exists to publish must be in "
        f"__all__; missing: {sorted(_SCHEMA_SURFACES - set(I.__all__))}"
    )


def test_no_private_name_is_exported():
    leaked = [n for n in I.__all__ if n.startswith("_")]
    assert leaked == [], f"__all__ exports private names: {leaked}"


def test_all_is_sorted_and_free_of_duplicates():
    """A hand-maintained export list drifts unless it has a shape.

    ASCII order (capitals first) — the order the list already had before
    rc407, kept so the new entries slot in rather than reshuffle it.
    """
    assert len(I.__all__) == len(set(I.__all__))
    assert I.__all__ == sorted(I.__all__)


def test_star_import_binds_every_exported_name():
    """``from srmech.introspect import *`` must bind all three surfaces.

    CPython resolves each ``__all__`` entry with ``getattr`` on the module, so
    this is the path that exercises the PEP-562 hook.
    """
    ns = {}
    exec("from srmech.introspect import *", ns)  # noqa: S102 - the surface under test

    for name in I.__all__:
        assert name in ns, f"'{name}' is in __all__ but 'import *' did not bind it"
    for name in _SCHEMA_SURFACES:
        assert ns[name] is not None
        assert ns[name].__name__ == f"srmech.introspect.{name}"


def test_plain_attribute_access_works_in_a_fresh_interpreter():
    """The other entry path — no ``import *``, no prior submodule import.

    Runs in a SUBPROCESS on purpose: within this session other tests have
    already populated ``sys.modules``, which would mask exactly the
    ``AttributeError`` this pins.
    """
    code = (
        "import srmech.introspect as I\n"
        "for n in ('tool_schema', 'carrier_schema', 'responsion_schema'):\n"
        "    m = getattr(I, n)\n"
        "    assert m.__name__ == 'srmech.introspect.' + n, (n, m.__name__)\n"
        "    assert getattr(I, n) is m, 'second access must return the same module'\n"
        "print('OK')\n"
    )
    proc = subprocess.run(
        [sys.executable, "-c", code], capture_output=True, text=True
    )
    assert proc.returncode == 0, proc.stderr
    assert "OK" in proc.stdout


def test_the_lazy_names_stay_visible_to_dir():
    """Lazy must not mean invisible — ``dir()`` is how a human finds them."""
    listing = dir(I)
    for name in _SCHEMA_SURFACES:
        assert name in listing, f"'{name}' vanished from dir(srmech.introspect)"


def test_unknown_attributes_still_raise_attribute_error():
    """The hook must not swallow real misses into an import error."""
    try:
        I.definitely_not_a_module
    except AttributeError as exc:
        assert "definitely_not_a_module" in str(exc)
    else:  # pragma: no cover - the hook is broken if we get here
        raise AssertionError("a missing attribute must raise AttributeError")


def test_removing_the_private_names_did_not_break_their_real_consumer():
    """``srmech/__init__.py`` uses direct attribute access, not ``__all__``."""
    assert hasattr(I, "_maybe_auto_publish")
    assert hasattr(I, "_PublishHandle")


def test_registry_size_is_unchanged_by_this_rc():
    """No public callable was added, removed or renamed here."""
    from srmech.introspect.tool_schema import get_tool_schema, warmup_all

    warmup_all()
    assert len(get_tool_schema().tools) == 661
