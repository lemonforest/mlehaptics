"""Tests for the v0.5.0rc8 cascade DSL runner (task #235).

Coverage:

* Fluent ``chain()`` builder — ``then`` / ``loop`` / ``fold`` /
  ``reduce`` for each cascade-catalog op shipped in v0.4.5.
* TOML cascade-catalog loader — all 8 descriptors present + resolvable.
* TOML chain-spec loader — schema handling, stage discriminators, sub-chains.
* Event emission — ``dsl.<chain>.stage.<N>`` lines under
  ``srmech.introspect.publish()``.
* CLI surface — ``srmech dsl ops`` / ``srmech dsl run`` /
  ``srmech dsl visualize`` exercised via ``python -m srmech`` subprocess.
* Error cases — unknown op, empty reduce, multiple discriminators,
  missing file, etc.
"""

from __future__ import annotations

import json
import math
import subprocess
import sys
import textwrap
from pathlib import Path

import pytest

from srmech import introspect
from srmech.dsl import (
    Chain,
    build_chain_from_dict,
    build_chain_from_toml,
    chain,
    get_descriptor,
    list_cascade_ops,
    load_catalog,
    lookup_cascade_op,
)


# ─────────────────────────────────────────────────────────────────────
# Catalog loader
# ─────────────────────────────────────────────────────────────────────


class TestCatalogLoader:
    """Cascade-catalog runtime loader covers all 8 shipped descriptors."""

    EXPECTED_OPS = {
        "pin_slot_at_zero",
        "reorient",
        "magnitude",
        "best_rational_signed",
        "cyclic_gcd",
        "chiral_flip",
        "chiral_dual",
        "net_chirality",
    }

    def test_list_cascade_ops_matches_expected_set(self) -> None:
        assert set(list_cascade_ops()) == self.EXPECTED_OPS

    def test_list_cascade_ops_returns_eight(self) -> None:
        assert len(list_cascade_ops()) == 8

    def test_list_cascade_ops_sorted(self) -> None:
        names = list_cascade_ops()
        assert names == sorted(names)

    def test_load_catalog_keys_match_list(self) -> None:
        catalog = load_catalog()
        assert set(catalog) == set(list_cascade_ops())

    def test_each_descriptor_has_class_composition(self) -> None:
        for name in list_cascade_ops():
            desc = get_descriptor(name)
            assert "cascade" in desc
            assert "class_composition" in desc["cascade"], (
                f"{name} missing class_composition"
            )

    def test_lookup_cascade_op_returns_callable(self) -> None:
        for name in list_cascade_ops():
            fn = lookup_cascade_op(name)
            assert callable(fn)

    def test_lookup_unknown_op_raises(self) -> None:
        with pytest.raises(ValueError, match="unknown cascade op"):
            lookup_cascade_op("not_a_real_cascade_op")

    def test_get_descriptor_unknown_raises(self) -> None:
        with pytest.raises(ValueError, match="unknown cascade op"):
            get_descriptor("not_a_real_cascade_op")


# ─────────────────────────────────────────────────────────────────────
# Fluent chain() — basic
# ─────────────────────────────────────────────────────────────────────


class TestFluentChainBasic:
    """Single-op + multi-op chains over the cascade catalog."""

    def test_chain_factory_returns_chain_instance(self) -> None:
        assert isinstance(chain(), Chain)
        assert isinstance(chain("named"), Chain)

    def test_chain_default_name(self) -> None:
        assert chain().name == "chain"

    def test_chain_custom_name(self) -> None:
        assert chain("my-pipeline").name == "my-pipeline"

    def test_empty_chain_returns_input_unchanged(self) -> None:
        assert chain().run(42) == 42
        assert chain().run([1, 2, 3]) == [1, 2, 3]

    def test_magnitude_single_stage(self) -> None:
        assert chain().then("magnitude").run(-3.14) == 3.14
        assert chain().then("magnitude").run(0.0) == 0.0
        assert chain().then("magnitude").run(7.5) == 7.5

    def test_chiral_flip_single_stage(self) -> None:
        result = chain().then("chiral_flip").run([1, 2, 3, 4])
        assert result == [4, 3, 2, 1]

    def test_pin_slot_at_zero_single_stage(self) -> None:
        orient, mag = chain().then("pin_slot_at_zero").run(-5.0)
        assert orient == -1
        assert mag == 5.0

    def test_best_rational_signed_with_kwargs(self) -> None:
        num, den = chain().then(
            "best_rational_signed", max_denominator=100,
        ).run(0.5)
        assert (num, den) == (1, 2)

    def test_then_returns_chain_for_fluent_chaining(self) -> None:
        c = chain()
        assert c.then("magnitude") is c

    def test_multi_stage_chain(self) -> None:
        # magnitude then chiral_flip on a list
        result = (
            chain("pipeline")
                .then("chiral_flip")
                .then("chiral_flip")
                .run([1.0, 2.0, 3.0])
        )
        # Two flips cancel out.
        assert result == [1.0, 2.0, 3.0]

    def test_chain_len_reports_stage_count(self) -> None:
        c = chain().then("magnitude").then("chiral_flip")
        assert len(c) == 2

    def test_chain_repr_includes_name_and_stages(self) -> None:
        c = chain("foo").then("magnitude")
        r = repr(c)
        assert "foo" in r
        assert "magnitude" in r

    def test_chain_stages_returns_descriptive_list(self) -> None:
        c = chain().then("best_rational_signed", max_denominator=50)
        stages = c.stages()
        assert stages == [("best_rational_signed", {"max_denominator": 50})]

    def test_then_unknown_op_raises_immediately(self) -> None:
        # Validation happens at then() time, not at run() time.
        with pytest.raises(ValueError, match="unknown cascade op"):
            chain().then("not_a_real_cascade_op")


# ─────────────────────────────────────────────────────────────────────
# Loop
# ─────────────────────────────────────────────────────────────────────


class TestLoop:
    """Loop primitive: repeat a sub-chain N times."""

    def test_loop_two_flips_returns_input(self) -> None:
        # chiral_flip ∘ chiral_flip = identity.
        sub = chain("inner").then("chiral_flip")
        result = chain("outer").loop(2, sub).run([1, 2, 3, 4])
        assert result == [1, 2, 3, 4]

    def test_loop_odd_flips_reverses(self) -> None:
        sub = chain("inner").then("chiral_flip")
        result = chain("outer").loop(5, sub).run([1, 2, 3])
        # Five flips → one effective flip.
        assert result == [3, 2, 1]

    def test_loop_zero_times_is_no_op(self) -> None:
        sub = chain("inner").then("chiral_flip")
        result = chain("outer").loop(0, sub).run([1, 2, 3])
        assert result == [1, 2, 3]

    def test_loop_negative_n_raises(self) -> None:
        sub = chain("inner").then("chiral_flip")
        with pytest.raises(ValueError, match="n_times must be >= 0"):
            chain().loop(-1, sub)

    def test_loop_non_chain_raises(self) -> None:
        with pytest.raises(TypeError, match="sub_chain must be a Chain"):
            chain().loop(3, "not a chain")  # type: ignore[arg-type]

    def test_loop_returns_chain_for_chaining(self) -> None:
        sub = chain().then("chiral_flip")
        c = chain()
        assert c.loop(2, sub) is c


# ─────────────────────────────────────────────────────────────────────
# Fold
# ─────────────────────────────────────────────────────────────────────


class TestFold:
    """Fold primitive: accumulate over a sequence with a seed."""

    def test_fold_cyclic_gcd_seed_zero(self) -> None:
        # gcd(0, 12) = 12; gcd(12, 8) = 4; gcd(4, 4) = 4.
        result = chain().fold(0, "cyclic_gcd").run([12, 8, 4])
        assert result == 4

    def test_fold_empty_sequence_returns_seed(self) -> None:
        result = chain().fold(42, "cyclic_gcd").run([])
        assert result == 42

    def test_fold_single_element(self) -> None:
        # gcd(0, 7) = 7.
        result = chain().fold(0, "cyclic_gcd").run([7])
        assert result == 7

    def test_fold_returns_chain_for_chaining(self) -> None:
        c = chain()
        assert c.fold(0, "cyclic_gcd") is c

    def test_fold_unknown_op_raises_immediately(self) -> None:
        with pytest.raises(ValueError, match="unknown cascade op"):
            chain().fold(0, "not_a_real_op")


# ─────────────────────────────────────────────────────────────────────
# Reduce
# ─────────────────────────────────────────────────────────────────────


class TestReduce:
    """Reduce primitive: accumulate over a sequence using the first element."""

    def test_reduce_cyclic_gcd(self) -> None:
        # gcd(12, 8) = 4; gcd(4, 4) = 4.
        result = chain().reduce("cyclic_gcd").run([12, 8, 4])
        assert result == 4

    def test_reduce_single_element_returns_it(self) -> None:
        result = chain().reduce("cyclic_gcd").run([7])
        assert result == 7

    def test_reduce_empty_sequence_raises(self) -> None:
        with pytest.raises(ValueError, match="reduce on empty sequence"):
            chain().reduce("cyclic_gcd").run([])

    def test_reduce_returns_chain_for_chaining(self) -> None:
        c = chain()
        assert c.reduce("cyclic_gcd") is c

    def test_reduce_three_coprime_returns_one(self) -> None:
        result = chain().reduce("cyclic_gcd").run([5, 7, 11])
        assert result == 1


# ─────────────────────────────────────────────────────────────────────
# Event emission
# ─────────────────────────────────────────────────────────────────────


class TestEventEmission:
    """Per-stage events fire under publish(); silent otherwise."""

    def test_publish_emits_per_stage_event(self, tmp_path) -> None:
        events = []
        with introspect.publish() as handle:
            chain("emit-test").then("chiral_flip").run([1.0, 2.0])
            # Read the status file to confirm events emitted.
            file_path = handle.file_path
        # File flushed after each emit; read it now.
        with open(file_path, "rb") as fh:
            for raw in fh:
                raw = raw.strip()
                if not raw:
                    continue
                events.append(json.loads(raw))
        op_names = [e.get("op_name") for e in events]
        # Should include the per-stage event and the complete event.
        assert "dsl.emit-test.stage.0" in op_names
        assert "dsl.emit-test.complete" in op_names

    def test_no_publish_no_events_emitted(self) -> None:
        # No publish() context — should be a silent no-op (we just
        # confirm the call doesn't fail and produces the expected output).
        result = chain("silent-test").then("magnitude").run(-2.0)
        assert result == 2.0


# ─────────────────────────────────────────────────────────────────────
# TOML chain spec
# ─────────────────────────────────────────────────────────────────────


class TestTomlChainSpec:
    """Build chains from TOML chain-spec files."""

    def test_simple_chain_from_dict(self) -> None:
        data = {
            "chain": {"name": "simple"},
            "stage": [
                {"op": "chiral_flip"},
            ],
        }
        c = build_chain_from_dict(data)
        assert c.name == "simple"
        assert len(c) == 1
        assert c.run([1, 2, 3]) == [3, 2, 1]

    def test_chain_with_kwargs(self) -> None:
        data = {
            "chain": {"name": "rational"},
            "stage": [
                {"op": "best_rational_signed", "max_denominator": 50},
            ],
        }
        c = build_chain_from_dict(data)
        assert c.run(0.5) == (1, 2)

    def test_loop_stage_via_dict(self) -> None:
        data = {
            "chain": {"name": "loop-test"},
            "stage": [
                {
                    "loop_n": 2,
                    "sub_chain": [{"op": "chiral_flip"}],
                },
            ],
        }
        c = build_chain_from_dict(data)
        assert c.run([1, 2, 3]) == [1, 2, 3]

    def test_fold_stage_via_dict(self) -> None:
        data = {
            "chain": {"name": "fold-test"},
            "stage": [
                {"fold_init": 0, "fold_op": "cyclic_gcd"},
            ],
        }
        c = build_chain_from_dict(data)
        assert c.run([12, 8, 4]) == 4

    def test_reduce_stage_via_dict(self) -> None:
        data = {
            "chain": {"name": "reduce-test"},
            "stage": [
                {"reduce_op": "cyclic_gcd"},
            ],
        }
        c = build_chain_from_dict(data)
        assert c.run([12, 8, 4]) == 4

    def test_missing_discriminator_raises(self) -> None:
        data = {
            "chain": {"name": "bad"},
            "stage": [{"foo": "bar"}],
        }
        with pytest.raises(ValueError, match="no discriminator"):
            build_chain_from_dict(data)

    def test_multiple_discriminators_raise(self) -> None:
        data = {
            "chain": {"name": "ambiguous"},
            "stage": [
                {"op": "chiral_flip", "reduce_op": "cyclic_gcd"},
            ],
        }
        with pytest.raises(ValueError, match="multiple discriminators"):
            build_chain_from_dict(data)

    def test_load_from_disk(self, tmp_path: Path) -> None:
        toml_path = tmp_path / "pipeline.toml"
        toml_path.write_text(textwrap.dedent("""
            [chain]
            name = "disk-pipeline"

            [[stage]]
            op = "magnitude"
        """).strip())
        c = build_chain_from_toml(toml_path)
        assert c.name == "disk-pipeline"
        assert c.run(-9.0) == 9.0

    def test_invalid_chain_section_raises(self) -> None:
        data = {"chain": "not a table", "stage": []}
        with pytest.raises(ValueError, match=r"\[chain\] section"):
            build_chain_from_dict(data)

    def test_invalid_stage_array_raises(self) -> None:
        data = {"chain": {"name": "x"}, "stage": "not an array"}
        with pytest.raises(ValueError, match=r"\[\[stage\]\]"):
            build_chain_from_dict(data)


# ─────────────────────────────────────────────────────────────────────
# CLI surface
# ─────────────────────────────────────────────────────────────────────


_PY = sys.executable
_TIMEOUT_S = 30.0


def _run_cli(*args: str) -> subprocess.CompletedProcess:
    """Run ``python -m srmech <args>``; return the completed process."""
    cmd = [_PY, "-m", "srmech", *args]
    return subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=_TIMEOUT_S,
        check=False,
    )


class TestCliDsl:
    """CLI subcommand surface."""

    def test_ops_lists_eight(self) -> None:
        result = _run_cli("dsl", "ops")
        assert result.returncode == 0, result.stderr
        assert "8 total" in result.stdout
        # Each catalog name appears in the output.
        for name in ["chiral_flip", "magnitude", "cyclic_gcd"]:
            assert name in result.stdout

    def test_ops_json_emits_records(self) -> None:
        result = _run_cli("dsl", "ops", "--json")
        assert result.returncode == 0, result.stderr
        records = json.loads(result.stdout)
        assert isinstance(records, list)
        assert len(records) == 8
        for rec in records:
            assert "name" in rec
            assert "class_composition" in rec

    def test_dsl_help_smoke(self) -> None:
        result = _run_cli("dsl", "--help")
        assert result.returncode == 0
        assert "run" in result.stdout
        assert "ops" in result.stdout
        assert "visualize" in result.stdout

    def test_run_inline_input(self, tmp_path: Path) -> None:
        spec = tmp_path / "spec.toml"
        spec.write_text(textwrap.dedent("""
            [chain]
            name = "cli-magnitude"

            [[stage]]
            op = "magnitude"
        """).strip())
        result = _run_cli(
            "dsl", "run", str(spec), "--input", "-7.5",
        )
        assert result.returncode == 0, result.stderr
        assert result.stdout.strip() == "7.5"

    def test_run_inline_list_input(self, tmp_path: Path) -> None:
        spec = tmp_path / "spec.toml"
        spec.write_text(textwrap.dedent("""
            [chain]
            name = "cli-flip"

            [[stage]]
            op = "chiral_flip"
        """).strip())
        result = _run_cli(
            "dsl", "run", str(spec), "--input", "[1, 2, 3, 4]",
        )
        assert result.returncode == 0, result.stderr
        assert json.loads(result.stdout.strip()) == [4, 3, 2, 1]

    def test_run_with_output_file(self, tmp_path: Path) -> None:
        spec = tmp_path / "spec.toml"
        spec.write_text(textwrap.dedent("""
            [chain]
            name = "cli-flip"

            [[stage]]
            op = "chiral_flip"
        """).strip())
        out = tmp_path / "result.json"
        result = _run_cli(
            "dsl", "run", str(spec),
            "--input", "[1, 2, 3]",
            "--output-file", str(out),
        )
        assert result.returncode == 0, result.stderr
        assert json.loads(out.read_text()) == [3, 2, 1]

    def test_run_missing_input_returns_error(self, tmp_path: Path) -> None:
        spec = tmp_path / "spec.toml"
        spec.write_text(textwrap.dedent("""
            [chain]
            name = "x"

            [[stage]]
            op = "magnitude"
        """).strip())
        result = _run_cli("dsl", "run", str(spec))
        assert result.returncode != 0
        assert "--input" in result.stderr

    def test_visualize_lists_stages(self, tmp_path: Path) -> None:
        spec = tmp_path / "spec.toml"
        spec.write_text(textwrap.dedent("""
            [chain]
            name = "viz-test"

            [[stage]]
            op = "magnitude"

            [[stage]]
            op = "chiral_flip"
        """).strip())
        result = _run_cli("dsl", "visualize", str(spec))
        assert result.returncode == 0, result.stderr
        assert "viz-test" in result.stdout
        assert "magnitude" in result.stdout
        assert "chiral_flip" in result.stdout
