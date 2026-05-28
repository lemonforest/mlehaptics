"""The bundled `siona` co-name alias (v0.4.4): `import siona` == `import srmech`.

`siona` ships inside the srmech wheel (a top-level package alongside `srmech`),
so installing srmech makes both import names available, pointing at the SAME
module objects. srmech remains the single source of truth.
"""
import srmech
import siona


def test_siona_version_matches_srmech():
    assert siona.__version__ == srmech.__version__


def test_siona_top_level_reexports_srmech_public_surface():
    # Every public top-level srmech name is re-exported on siona.
    for name in dir(srmech):
        if not name.startswith("_"):
            assert hasattr(siona, name), f"siona missing re-export: {name}"


def test_siona_submodule_is_same_object_as_srmech():
    import siona.amsc.cascade
    import srmech.amsc.cascade
    assert siona.amsc.cascade is srmech.amsc.cascade


def test_siona_from_import_resolves():
    from siona.amsc import cascade as siona_cascade
    from srmech.amsc import cascade as srmech_cascade
    assert siona_cascade is srmech_cascade


def test_siona_attribute_access_chain():
    # plain attribute access (not just `import`) walks siona.amsc.format
    import siona  # noqa: F811
    assert siona.amsc.format is srmech.amsc.format


def test_siona_callable_works_through_alias():
    import siona.amsc.cascade as c
    # chiral_flip is the v0.4.4 cascade chirality op (rc1); reachable via siona.
    assert c.chiral_flip([1, 2, 3]) == [3, 2, 1]
