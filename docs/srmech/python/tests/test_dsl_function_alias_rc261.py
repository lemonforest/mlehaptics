"""v0.9.0rc261 (§95.2 / #1407) — config-driven FUNCTION ALIASING (the domain-agnostic naming layer).

srmech already declares CLASSES (srmech.dsl.make_class) and PIPELINES (the [chain] DSL) in TOML;
rc261 adds the smallest missing rung — declaring a NAME BINDING. srmech.dsl.alias(name, target)
binds a user's own name to any srmech.* function; build_aliases_from_toml_str parses a [[alias]]
TOML array into {name: callable}. This makes the framework's own naming (e.g. the rc260
genome/plasmid rename) a non-issue at the user layer: anyone re-aliases to their domain vocabulary
in config, no code (ADR-0004).

Proven here: single + TOML-batch aliasing, byte-identical behaviour to the target, the introspection
handle, and the SECURITY restriction (a target must be srmech.* — a config cannot import/call an
arbitrary module). numpy-free.
"""
from __future__ import annotations

import pytest

from srmech import dsl
from srmech.amsc import genome as G
from srmech.amsc.hdc import klein4_expand


def _one(seed=7):
    return klein4_expand(64, seed)


def _kernels(n=3):
    return {"a": [klein4_expand(64, s) for s in range(n)]}


def _bl(hvs):
    return [x.tobytes() for x in hvs]


# ── 1. single alias ─────────────────────────────────────────────────────────

def test_alias_binds_a_name_to_a_srmech_function():
    build = dsl.alias("build", "srmech.amsc.genome.genome")
    assert build.__name__ == "build"
    assert build.srmech_alias_target == "srmech.amsc.genome.genome"
    one, kernels = _one(), _kernels()
    assert _bl(build(kernels, one)) == _bl(G.genome(kernels, one))   # byte-identical to target


def test_alias_preserves_the_target_docstring():
    plant = dsl.alias("plant", "srmech.amsc.genome.plasmid")
    assert (plant.__doc__ or "") == (G.plasmid.__doc__ or "")        # functools.wraps


# ── 2. TOML [[alias]] batch ─────────────────────────────────────────────────

def test_build_aliases_from_toml_str():
    names = dsl.build_aliases_from_toml_str(
        '[[alias]]\nname = "build"\ntarget = "srmech.amsc.genome.genome"\n'
        '[[alias]]\nname = "stick"\ntarget = "srmech.amsc.genome.plasmid"\n')
    assert set(names) == {"build", "stick"}
    one, kernels = _one(), _kernels()
    assert _bl(names["build"](kernels, one)) == _bl(G.genome(kernels, one))
    assert _bl(names["stick"](kernels, one)) == _bl(G.plasmid(kernels, one))


def test_load_aliases_toml_from_file(tmp_path):
    p = tmp_path / "aliases.toml"
    p.write_text('[[alias]]\nname = "recover"\ntarget = "srmech.amsc.genome.recover_diploid"\n',
                 encoding="utf-8")
    names = dsl.load_aliases_toml(p)
    assert names["recover"].srmech_alias_target == "srmech.amsc.genome.recover_diploid"


def test_empty_alias_doc_yields_empty_mapping():
    assert dsl.build_aliases_from_toml_str('[chain]\nname = "x"\n') == {}


# ── 3. security: srmech.*-restricted targets ────────────────────────────────

@pytest.mark.parametrize("bad", ["os.system", "subprocess.run", "builtins.eval",
                                 "shutil.rmtree", "notsrmech.foo"])
def test_alias_rejects_non_srmech_targets(bad):
    with pytest.raises(ValueError):
        dsl.alias("evil", bad)


def test_build_aliases_rejects_non_srmech_target_in_toml():
    with pytest.raises(ValueError):
        dsl.build_aliases_from_toml_str('[[alias]]\nname = "x"\ntarget = "os.system"\n')


# ── 4. malformed input ──────────────────────────────────────────────────────

def test_malformed_alias_entries_raise():
    with pytest.raises(ValueError):
        dsl.build_aliases_from_toml_str('[[alias]]\nname = "x"\n')          # no target
    with pytest.raises(ValueError):
        dsl.build_aliases_from_toml_str('[[alias]]\ntarget = "srmech.amsc.genome.genome"\n')  # no name
    with pytest.raises(ValueError):
        dsl.alias("", "srmech.amsc.genome.genome")                          # empty name
    with pytest.raises(TypeError):
        dsl.build_aliases_from_toml_str(123)                                # not a str


def test_alias_target_must_resolve_to_a_callable():
    with pytest.raises((ValueError, Exception)):
        dsl.alias("x", "srmech.amsc.genome.GENOME_FORMAT_VERSION")          # a constant, not callable
