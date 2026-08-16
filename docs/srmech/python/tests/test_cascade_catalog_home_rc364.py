"""rc364 (`#T1034` / `#T1039`) — ADR-0010's first execution slice, instrumented.

WHAT MOVED. The built-in descriptor catalogs left ``srmech/amsc/_research/`` for
``srmech/cascade/catalogs/`` — ADR-0010's ``make_class`` re-homed clause, executed:
*"Move the built-in catalogs to ``srmech.cascade/catalogs/`` (the composition layer
owns them); the user-supplied dirs ``register_class_dir`` accepts become the
``srmech.external.*`` extension point."* ``srmech.cascade`` is the arc's FIRST new
top-level namespace, so the shape it takes is the shape the remaining slices follow.

WHAT THIS FILE IS FOR, in three parts:

1. **The home invariants** — the four catalog directories are where the ADR says,
   they are INSIDE the installed package, and ``amsc/_research/`` is gone. A move
   that left a copy behind, or that put a descriptor outside ``srmech/``, would be
   a move in name only.

2. **A LIVE WHEEL DEFECT, closed and pinned so it cannot reopen.**
   ``genome_type_aliases_legacy.toml`` is the documented migration path for
   rc271's BREAKING ``stick``→``plasmid`` / ``minted``→``nuclear`` rename, and its
   own header prints the exact call to make. That file lived under
   ``tests/data/``. ``tests/**`` is in ``sdist.include`` and NOT in the wheel
   (``wheel.packages = ["srmech"]``, no force-include, no ``MANIFEST.in``), so
   **install the wheel, follow the header, get ``FileNotFoundError``** — for 93
   rcs. The loader shipped; the thing it loads did not. rc362 then landed the
   tree's first ``[[alias]]`` descriptor in the same directory, for the same
   reason: there was no ``ALIAS_CATALOG_DIR`` to land it in.

   Both halves are tested here — the descriptors now live inside the package, AND
   the documented one-liners are EXECUTED rather than described.

3. **The registered alias directory** — ``ALIAS_CATALOG_DIR`` /
   ``register_alias_dir`` / ``list_alias_descriptors`` / ``resolve_alias_descriptor``,
   the shape ``CLASS_CATALOG_DIR`` / ``register_class_dir`` / ``list_classes`` /
   ``load_class_catalog`` has had since rc39. Its absence is why rc362's descriptor
   landed where it did *by default rather than by decision*.

⚠️ WHY A PATH ASSERTION IS THE RIGHT INSTRUMENT HERE, rather than building a wheel.
Wheel inclusion under BOTH backends follows from one fact — the file is inside a
directory named in ``packages``. Asserting the fact is a measurement of the thing
that decides the outcome; building a wheel in a unit test would measure one
backend, on one host, at one moment. So this file pins the fact AND pins the
config line that makes the fact load-bearing, and goes red if either moves.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

import srmech
from srmech import dsl
from srmech.biology import genome

_PKG = Path(srmech.__file__).resolve().parent
_PY_ROOT = _PKG.parent                       # docs/srmech/python
_CATALOGS = _PKG / "cascade" / "catalogs"

#: Every built-in catalog directory, and the descriptor count each held at rc364.
#: Counts are pinned so a descriptor cannot be lost in a later move without a red.
_CATALOG_COUNTS = {
    "class_catalog": 4,
    "cascade_catalog": 21,   # rc438 (`#T1140`): + klein4_from_one (ONE-A14)
    "alias_catalog": 2,
    "worked_instances": 1,
}


# ── 1. the home ─────────────────────────────────────────────────────────────

def test_the_four_catalogs_live_under_srmech_cascade_catalogs() -> None:
    """ADR-0010's clause, as an assertion about the tree."""
    assert _CATALOGS.is_dir(), (
        f"the composition layer's catalog root is missing at {_CATALOGS}. "
        "ADR-0010 moves the built-in [class]/[cascade] descriptors here.")
    for name, expected in _CATALOG_COUNTS.items():
        d = _CATALOGS / name
        assert d.is_dir(), f"catalog directory missing: {d}"
        found = len(list(d.glob("*.toml")))
        assert found == expected, (
            f"{name}: {found} descriptors, expected {expected}. If a descriptor "
            f"was deliberately added or removed, bump the pin WITH the reason; "
            f"if this fell to 0, a move dropped the payload and kept the "
            f"directory.")


def test_the_old_research_home_is_gone_not_merely_copied() -> None:
    """⚠️ A move that leaves the source behind is a COPY, and a copy drifts.

    Both loaders resolve by path, so a leftover ``amsc/_research/class_catalog/``
    would keep parsing fine while receiving no further edits — the silent-stale
    shape this tree keeps repairing. Asserted rather than assumed.
    """
    stale = _PKG / "amsc" / "_research"
    assert not stale.exists(), (
        f"{stale} still exists after the rc364 move. Delete it: the catalogs "
        f"live at {_CATALOGS} and a second copy can only diverge.")


def test_every_catalog_directory_is_a_package() -> None:
    """The wheel-inclusion declaration, made explicit rather than inherited.

    Both build backends copy the package tree, so a bare data directory does in
    fact ship today — ``worked_instances/`` had no ``__init__.py`` before rc364
    and shipped anyway. That is a heuristic holding, not a declaration, and rc364
    exists because an adjacent assumption of exactly that kind cost two alias
    descriptors their place in the wheel. Each catalog directory now declares
    itself.
    """
    missing = [n for n in _CATALOG_COUNTS
               if not (_CATALOGS / n / "__init__.py").is_file()]
    assert not missing, (
        f"catalog directories with no __init__.py marker: {missing}. The marker "
        f"is what makes inclusion a declaration rather than a backend heuristic, "
        f"and it is also where the directory documents itself.")


def test_the_loader_constants_point_at_the_new_home() -> None:
    """The three directory constants are peers and all three resolve here."""
    for const in (dsl.CLASS_CATALOG_DIR, dsl.CATALOG_DIR, dsl.ALIAS_CATALOG_DIR):
        assert const.is_dir(), f"loader constant does not resolve: {const}"
        assert const.parent == _CATALOGS, (
            f"{const} is not under {_CATALOGS} — the three catalog constants "
            f"must stay siblings, or 'the composition layer owns the built-in "
            f"catalogs' has stopped being true of one of them.")


def test_the_new_namespace_imports_and_exposes_the_flat_cascade_api() -> None:
    """``srmech.cascade`` imports cleanly and re-exports the flat cascade API.

    ⚠️ rc377 (`#T1034`, ADR-0010) is the slice this test's rc364 form anticipated.
    At rc364 the namespace held ONLY ``catalogs/`` (descriptors reached by PATH),
    so its ``__init__`` was empty and this test asserted it *stayed* empty "as
    later slices move ``compose`` / ``atoms`` in beside ``catalogs/``". rc377 IS
    that slice: ``srmech/amsc/cascade/`` (the lean-ISA atoms + composites tier)
    moved here, so the namespace is now the composition layer's CODE home, not a
    catalogs-only shell. Its ``__init__`` re-exports the flat API EAGERLY — exactly
    as ``srmech.amsc.cascade`` did before the move — so ``import srmech.cascade``
    costs what ``import srmech.amsc.cascade`` always did. The move PRESERVES the
    import cost; it does not add one. (The old "stays empty / costs nothing"
    invariant was a property of the transitional catalogs-only state and is
    correctly retired here, not weakened.)
    """
    import srmech.cascade as cascade
    import srmech.cascade.catalogs

    # The two tiers now resolve as submodules, and the flat re-exports are live.
    assert cascade.__all__, (
        "srmech/cascade/__init__.py no longer re-exports the flat cascade API. "
        "rc377 moved the atoms + composites tier in, so __all__ must be non-empty "
        "— an empty __all__ now means the move dropped the public surface.")
    for name in ("atoms", "composites", "pin_slot_at_zero", "cyclic_gcd",
                 "autocorrelation", "kuramoto_step"):
        assert hasattr(cascade, name), (
            f"srmech.cascade.{name} is not exposed — the rc377 atoms/composites "
            f"move did not carry the full flat surface across.")


# ── 2. the wheel defect ─────────────────────────────────────────────────────

def test_no_alias_descriptor_is_left_in_tests_data() -> None:
    """⚠️ THE DEFECT, pinned as a rule rather than as two filenames.

    ``tests/data/`` is a fine home for a FIXTURE. It is not a home for a
    descriptor a user is told to load, because it is outside every wheel. This
    catches the next one too.
    """
    data = _PY_ROOT / "tests" / "data"
    if not data.is_dir():                                  # pragma: no cover
        pytest.skip("no tests/data directory")
    strays = sorted(p.name for p in data.glob("*.toml")
                    if "alias" in p.name.lower())
    assert strays == [], (
        f"alias descriptor(s) still under tests/data/: {strays}. tests/** is in "
        f"sdist.include and NOT in the wheel, so a descriptor here ships to "
        f"nobody. Put it in {dsl.ALIAS_CATALOG_DIR} and load it by bare name.")


def test_the_shipped_descriptors_are_inside_the_installed_package() -> None:
    """Inclusion follows from being inside a directory named in ``packages``."""
    for name in sorted(dsl.list_alias_descriptors()):
        p = dsl.list_alias_descriptors()[name]
        assert _PKG in p.resolve().parents, (
            f"alias descriptor {name} resolves to {p}, which is OUTSIDE the "
            f"installed package root {_PKG} — so it does not ship.")


def test_both_build_backends_still_ship_the_package_tree() -> None:
    """⚠️ The config line the test above depends on, pinned.

    Everything here rests on ``packages = ["srmech"]`` in both pyprojects. If a
    future edit narrowed either to an explicit module list, the descriptors would
    silently stop shipping and every other assertion in this file would still
    pass — they read the SOURCE tree. So the config is asserted directly.
    """
    plat = (_PY_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    pure = (_PY_ROOT / "pyproject-pure.toml").read_text(encoding="utf-8")
    assert 'wheel.packages = ["srmech"]' in plat, (
        "scikit-build-core no longer declares wheel.packages = [\"srmech\"]; "
        "re-check that srmech/cascade/catalogs/**/*.toml still ships.")
    assert 'packages = ["srmech"]' in pure, (
        "hatchling no longer declares packages = [\"srmech\"]; re-check that "
        "srmech/cascade/catalogs/**/*.toml still ships in the pure wheel.")


def test_the_documented_genome_migration_one_liner_actually_runs() -> None:
    """⚠️ THE HEADER'S OWN INSTRUCTION, EXECUTED.

    ``genome_type_aliases_legacy.toml`` tells the reader, verbatim::

        genome.load_type_aliases_toml("genome_type_aliases_legacy.toml")

    A BARE FILENAME. Before rc364 that raised ``FileNotFoundError`` unless the
    caller happened to be sitting in ``tests/data/``. This runs the documented
    line and checks the documented effect.
    """
    try:
        mapping = genome.load_type_aliases_toml("genome_type_aliases_legacy.toml")
        assert mapping == {"nuclear": "minted", "plasmid": "stick"}, (
            f"the legacy value-alias mapping changed: {mapping}. It is the "
            f"documented migration path for rc271's BREAKING rename; changing it "
            f"silently breaks the users it exists for.")
    finally:
        genome.clear_type_aliases()

    # and the header instruction is still THE header instruction
    header = (dsl.ALIAS_CATALOG_DIR / "genome_type_aliases_legacy.toml").read_text(
        encoding="utf-8")
    assert 'load_type_aliases_toml("genome_type_aliases_legacy.toml")' in header, (
        "the descriptor's header no longer prints the bare-name call this test "
        "executes. Keep the two in step — a doc line nothing runs is how this "
        "defect shipped in the first place.")


def test_the_documented_music_vocabulary_one_liner_actually_runs() -> None:
    """The same, for rc362's ``[[alias]]`` descriptor: a domain SHIPS its words."""
    names = dsl.load_aliases_toml("music_domain_aliases")
    assert set(names) == {
        # the ACOUSTIC lane (rc362) — words for things you HEAR
        "partials", "bell_tuning", "overtone_series", "drum_modes",
        "temperament", "is_inharmonic", "overtone_period", "exactness",
        # the RELATIONAL lane (rc424) — words for relations you RECKON
        "p_limit", "comma", "tempers", "interval_content",
        "compact_rotation", "set_class",
        # and the §3.46.2 ℤ/7 walk, which earns a NAME but not an op
        "scale_step"}
    from srmech import music
    assert names["partials"]() == music.bell_partials(), (
        "the aliased name no longer forwards to its target — the binding is "
        "pure naming and must be value-identical.")
    assert names["comma"]((3, 2), 12, (2, 1))["comma"] == "531441/524288"
    assert names["set_class"]([0, 4, 7], "rahn") == (0, 3, 7)
    # the walk of §3.46.2: F -> C is the fifth, a single +4 step in ℤ/7
    assert names["scale_step"](6, 4, 7) == 3


# ── 3. the registered alias directory ───────────────────────────────────────

def test_bare_name_and_filename_both_resolve() -> None:
    for spelling in ("music_domain_aliases", "music_domain_aliases.toml"):
        p = dsl.resolve_alias_descriptor(spelling)
        assert p.is_file() and p.stem == "music_domain_aliases"


def test_an_explicit_path_still_wins_over_the_catalog(tmp_path: Path) -> None:
    """FILESYSTEM-FIRST, so rc364 changes no existing caller's meaning."""
    local = tmp_path / "music_domain_aliases.toml"
    local.write_text('[[alias]]\nname = "x"\ntarget = "srmech.music.common_period"\n',
                     encoding="utf-8")
    assert dsl.resolve_alias_descriptor(local) == local
    assert set(dsl.load_aliases_toml(local)) == {"x"}


def test_register_alias_dir_extends_the_search_without_shadowing(
        tmp_path: Path) -> None:
    """The ``srmech.external.*`` extension point, and the A-tier/B-tier rule.

    A user directory ADDS names; it does not take over a shipped one. That is
    ``load_class_catalog``'s no-shadow rule applied to the naming layer.
    """
    user = tmp_path / "vocab"
    user.mkdir()
    (user / "my_domain.toml").write_text(
        '[[alias]]\nname = "beat"\ntarget = "srmech.music.common_period"\n',
        encoding="utf-8")
    # a deliberate name-collision with a shipped descriptor
    (user / "music_domain_aliases.toml").write_text(
        '[[alias]]\nname = "hijacked"\ntarget = "srmech.music.common_period"\n',
        encoding="utf-8")

    from srmech.dsl import _alias as A
    saved = list(A._USER_ALIAS_DIRS)
    try:
        dsl.register_alias_dir(user)
        found = dsl.list_alias_descriptors()
        assert "my_domain" in found, "the registered directory was not searched"
        assert found["music_domain_aliases"].parent == dsl.ALIAS_CATALOG_DIR, (
            "a user descriptor SHADOWED a shipped one. Packaged descriptors are "
            "A-tier and win, as in load_class_catalog.")
        assert set(dsl.load_aliases_toml("my_domain")) == {"beat"}
    finally:
        A._USER_ALIAS_DIRS[:] = saved


def test_the_env_var_is_the_zero_api_equivalent(tmp_path: Path, monkeypatch) -> None:
    user = tmp_path / "envvocab"
    user.mkdir()
    (user / "from_env.toml").write_text(
        '[[alias]]\nname = "e"\ntarget = "srmech.music.common_period"\n',
        encoding="utf-8")
    monkeypatch.setenv("SRMECH_ALIAS_PATH", str(user))
    assert "from_env" in dsl.list_alias_descriptors()


def test_register_alias_dir_rejects_a_non_directory(tmp_path: Path) -> None:
    with pytest.raises(ValueError):
        dsl.register_alias_dir(tmp_path / "does_not_exist")


def test_an_unresolvable_name_names_what_IS_resolvable() -> None:
    """⚠️ NON-VACUITY of the discovery surface.

    The failure message is the only enumeration a caller gets today
    (``describe()`` still cannot see this layer — ADR-0012 clause C6 stays open),
    so it must actually list the catalog rather than merely refuse.
    """
    with pytest.raises(FileNotFoundError) as ei:
        dsl.resolve_alias_descriptor("no_such_vocabulary")
    msg = str(ei.value)
    assert "music_domain_aliases" in msg and "genome_type_aliases_legacy" in msg, (
        f"the not-found message does not enumerate the shipped descriptors, so a "
        f"caller who guesses wrong learns nothing: {msg}")
    assert "register_alias_dir" in msg


def test_the_alias_surface_is_exported_from_srmech_dsl() -> None:
    for name in ("ALIAS_CATALOG_DIR", "register_alias_dir",
                 "list_alias_descriptors", "resolve_alias_descriptor"):
        assert name in dsl.__all__, f"{name} missing from srmech.dsl.__all__"
        assert hasattr(dsl, name)


def test_every_shipped_descriptor_parses() -> None:
    """⚠️ Replaces a TAUTOLOGY this file shipped in its first pass.

    That assertion was ``"numpy" not in sys.modules``. numpy is not installed in
    any srmech environment — it is absent from every extra, and the suite runs
    numpy-absent by construction (#564) — so the assertion **cannot return
    otherwise**. A check that can only pass is not a measurement, which is the
    exact failure mode the rest of this file is written to avoid; and the real
    instrument for that property (``CEIL_NUMPY_CARRIER``) already exists and is
    not this file's job.

    What is worth asserting instead is a property the MOVE could actually have
    broken: every descriptor that now ships from the new home still parses. A
    directory move that corrupted an encoding, or that swept up a file that is
    not a descriptor, would land here.
    """
    if sys.version_info >= (3, 11):
        import tomllib as _toml
    else:                                    # pragma: no cover — 3.10 back-port
        import tomli as _toml                # type: ignore[no-redef]

    parsed = 0
    for name in _CATALOG_COUNTS:
        for toml_path in sorted((_CATALOGS / name).glob("*.toml")):
            raw = toml_path.read_bytes()
            doc = _toml.loads(raw.decode("utf-8"))
            assert isinstance(doc, dict) and doc, (
                f"{toml_path} parsed to an empty document")
            parsed += 1
    assert parsed == sum(_CATALOG_COUNTS.values()), (
        f"parsed {parsed} descriptors, expected {sum(_CATALOG_COUNTS.values())}")
