"""Combinator-kernel closure ratchet (v0.6.0rc16, MS #20; widened rc420).

The cascade DSL's control-flow combinators are a CLOSED, FINITE kernel —
the finite anharmonic-kernel tier of the package's two-tier SSoT. The
kernel is HARDCODED (here, in Python; mirrored co-equally in C); the
asymptotic cascade *instances* the kernel sequences are NOT hardcoded —
they live as TOML op-descriptors in the cascade catalog ("you can't
hardcode a continuum"). Kernel in code, continuum in catalog.

This module pins that closure mechanically so a new combinator cannot be
added silently: a new special form must be a CONSCIOUS widening of the
kernel (with this test updated in the same change). **v0.9.0rc420
(`#T1114`) IS that widening, executed as designed**: the census measured
the indexed map — ``out[k] = f(whole_input, k)`` — as the single dominant
missing recursion scheme (it blocked 4 of the 20 cascade-catalog
descriptors and 19 of the 41 closed_form_ops modules at the scheme
level), rung 4 proved the form closes all four blocked descriptors
bit-identically (42/42), and this file moved 5 → 6 in the same change as
the builder. The six forms are the Bird-Meertens recursion schemes:

    then              apply / compose         (op discriminator)
    loop              bounded iterate         (loop_n + sub_chain)
    fold              catamorphism-with-seed  (fold_init + fold_op)
    reduce            catamorphism            (reduce_op)
    parallel_sectors  Klein-4 map-fan-out     (parallel_body)
    map_indexed       indexed map             (map_op)                rc420

Data-dependent iteration (while / unfold — loop *until* a predicate) is
DELIBERATELY EXILED to the op-instance layer (a body op decides when to
stop), keeping the kernel total-by-construction at six forms. The indexed
map respects that line: it is data-SIZED (``n = len(input)`` fixed at
entry), never data-DEPENDENT — no predicate decides continuation, the
same totality class as fold's ``for elem in input_seq``. A future
while/unfold special form would be a SEVENTH combinator — another
conscious kernel widening, caught here. (`#T1114` rung 4 measured the
shipped corpus: every ``while`` in all 41 closed_form_ops modules is
structurally FUEL-BOUNDED; the true exile class — predicate-only
unbounded iteration — is EMPTY in shipped code.)

THE C CROSS-PIN (new at rc420, closing a measured gap)
======================================================
``_control_flow.py`` says the kernel is "mirrored co-equally in C", and
until rc420 that sentence was prose pinned by NOTHING: the C dispatcher's
own discriminator table (``dsl_stage_is_combinator`` in
``c/src/srmech_dsl_chain_run.c``) was a hardcoded string array no test
read, so a Python-side widening would fail here loudly while the C array
silently deferred the new form to pure — an ADR-0009 parity drift with no
symptom. :func:`test_c_discriminator_table_matches_python` now reads the
C source and asserts the two discriminator vocabularies agree, so the
next widening cannot ship half-mirrored.
"""
import inspect
import re
from pathlib import Path

import pytest

from srmech.dsl import Chain, build_chain_from_toml_str, chain
from srmech.dsl import _toml_chain


# The six combinator builders — the closed finite kernel (5 → 6 at rc420).
KERNEL_BUILDERS = frozenset({
    "then", "loop", "fold", "reduce", "parallel_sectors", "map_indexed",
})

# Public Chain methods that are NOT combinator builders (runner / inspector).
# Any NEW public Chain method must be classified into one of these two sets;
# that classification IS the conscious-widening checkpoint.
NON_BUILDER_PUBLIC = frozenset({"run", "stages"})

# The six mutually-exclusive TOML stage-discriminators the parser enforces.
TOML_DISCRIMINATORS = (
    "has_op", "has_loop", "has_fold", "has_reduce", "has_parallel",
    "has_map",
)

# The C dispatcher's stage-discriminator KEY vocabulary — the combinator
# keys `dsl_stage_is_combinator` must recognise (`op` is the fall-through
# leaf form on both sides, so it is deliberately not in this set).
C_COMBINATOR_KEYS = frozenset({
    "loop_n", "sub_chain", "fold_init", "fold_op", "reduce_op",
    "parallel_body", "map_op",
})


def _public_methods(cls):
    return {
        name
        for name, _ in inspect.getmembers(cls, predicate=inspect.isfunction)
        if not name.startswith("_")
    }


def test_exactly_six_kernel_builders():
    """The combinator kernel is exactly six builders — no more, no less.

    Five through rc419; six from rc420 (`#T1114` map_indexed — the
    conscious widening this file exists to force into the open)."""
    assert len(KERNEL_BUILDERS) == 6
    for name in KERNEL_BUILDERS:
        assert callable(getattr(Chain, name)), f"missing kernel builder {name!r}"


def test_no_hidden_seventh_builder():
    """Every public Chain method is a kernel builder or a known non-builder.

    A new public method (e.g. a ``while_`` 7th combinator) fails here until it
    is consciously classified — the kernel-widening checkpoint.
    """
    public = _public_methods(Chain)
    unclassified = public - KERNEL_BUILDERS - NON_BUILDER_PUBLIC
    assert not unclassified, (
        f"unclassified public Chain method(s): {sorted(unclassified)}. A new "
        f"combinator is a CONSCIOUS kernel widening — add it to KERNEL_BUILDERS "
        f"(and the TOML discriminator set) deliberately, or to "
        f"NON_BUILDER_PUBLIC if it is a runner/inspector."
    )


def test_six_toml_discriminators_bijection():
    """The TOML stage-discriminator set is exactly six and is summed as one.

    Read from the dispatcher source so the count is the REAL one the parser
    enforces, not a copy that could drift.
    """
    src = inspect.getsource(_toml_chain._apply_stage_to_chain)
    for d in TOML_DISCRIMINATORS:
        assert d in src, f"discriminator {d!r} missing from dispatcher"
    # the chosen-count guard sums exactly these six and nothing else
    assert (
        "sum([has_op, has_loop, has_fold, has_reduce, has_parallel,"
        in src and "has_map])" in src
    ), "the discriminator-count guard changed shape — re-confirm the bijection"


def test_c_discriminator_table_matches_python():
    """The C dispatcher's discriminator array carries the SAME combinator
    keys the Python TOML reader dispatches on. STRICT — both directions.

    Closes the rc420-measured gap: ``srmech_dsl_chain_run.c``'s
    ``disc[...]`` array was pinned by nothing, so a Python-side widening
    (exactly like rc420's ``map_op``) would leave the C peer silently
    deferring the new form to pure — the "mirrored co-equally in C"
    docstring going false with no symptom. Reading the C source here makes
    the next widening a TWO-surface conscious edit or a red build.
    """
    c_src_path = (
        Path(__file__).resolve().parent.parent.parent
        / "c" / "src" / "srmech_dsl_chain_run.c"
    )
    assert c_src_path.exists(), (
        f"C DSL chain runner not found at {c_src_path} — if the file moved, "
        f"update this cross-pin; do not delete it (it is the only thing "
        f"holding the C discriminator table to the Python one)."
    )
    src = c_src_path.read_text(encoding="utf-8")
    m = re.search(
        r"static\s+const\s+char\s*\*\s*disc\s*\[\s*\d+\s*\]\s*=\s*\{([^}]*)\}",
        src,
    )
    assert m, (
        "could not find the discriminator array `static const char *disc[N] "
        "= {...}` in srmech_dsl_chain_run.c — the C dispatcher changed "
        "shape; re-anchor this cross-pin on its new form."
    )
    c_keys = frozenset(re.findall(r'"([a-z_]+)"', m.group(1)))
    assert c_keys == C_COMBINATOR_KEYS, (
        f"C discriminator table {sorted(c_keys)} != Python combinator keys "
        f"{sorted(C_COMBINATOR_KEYS)} — the kernel is mirrored co-equally "
        f"in C (ADR-0009); widen or shrink BOTH in the same change."
    )


def test_each_builder_appends_one_stage():
    """Each of the six builders materialises exactly one stage on the Chain."""
    assert len(chain().then("chiral_flip")) == 1
    assert len(chain().loop(2, chain().then("chiral_flip"))) == 1
    assert len(chain().fold(0, "cyclic_gcd")) == 1
    assert len(chain().reduce("cyclic_gcd")) == 1
    assert len(chain().parallel_sectors("chiral_flip")) == 1
    assert len(chain().map_indexed("srmech.cascade.leaves.seq_get")) == 1


def test_toml_roundtrip_all_six_forms():
    """A TOML spec exercising all six discriminators round-trips to a
    six-stage Chain — the whole kernel is reachable from config."""
    toml_str = """
    [chain]
    name = "kernel-closure-roundtrip"

    [[stage]]
    op = "chiral_flip"

    [[stage]]
    loop_n = 2
    [[stage.sub_chain]]
    op = "chiral_flip"

    [[stage]]
    fold_init = 0
    fold_op = "cyclic_gcd"

    [[stage]]
    reduce_op = "cyclic_gcd"

    [[stage]]
    parallel_body = "chiral_flip"
    n_sectors = 4
    combine = "bundle"

    [[stage]]
    map_op = "srmech.cascade.leaves.seq_get"
    """
    ch = build_chain_from_toml_str(toml_str)
    assert len(ch) == 6


def test_map_indexed_runs_and_is_total():
    """The sixth form executes: identity map via the data-first seq_get
    body, and the Class-C flip as an indexed-map body (the rung-4 demo:
    the indexed map STRICTLY GENERALISES the bounded Klein-4 map slot)."""
    ident = chain().map_indexed("srmech.cascade.leaves.seq_get")
    assert ident.run([7, 8, 9]) == [7, 8, 9]
    # n is pinned at entry: an unsized iterable fails AT THE STAGE BOUNDARY
    # (len raises), never by silent unbounded iteration.
    with pytest.raises(TypeError):
        ident.run(iter([1, 2, 3]))


def test_fold_binds_kw_only_atom_via_arg_names():
    """The rc420 fold-contract fix (`#T1114` BLK-ITER-COMPOSE wrinkle).

    MEASURED defect: ``fold(1, "reorient")`` raised ``TypeError: reorient()
    takes 1 positional argument but 2 were given`` — the one surface that
    HAD fold could not bind the canonical Class-C atom as shipped, because
    the fold call was binary-positional and ``reorient(value, *,
    orientation=)`` is kw-only. ``arg_names`` names the two slots."""
    with pytest.raises(TypeError):
        chain().fold(1, "reorient").run([1, -1, 1])
    fixed = chain().fold(1, "reorient", arg_names=("value", "orientation"))
    assert fixed.run([1, -1, 1]) == -1
    # NOTE the semantics: a bare reorient fold is sign-application, NOT
    # net_chirality — reorient's orientation == 0 branch is a NO-OP, not
    # absorbing (measured rc420: net_chirality([0, -1]) == 0 but this fold
    # gives -1). The net-chirality fold body is orientation_compose.
    assert fixed.run([0, -1]) == -1
    from srmech.cascade import net_chirality
    assert net_chirality([0, -1]) == 0
    absorbing = chain().fold(
        1, "srmech.cascade.leaves.orientation_compose")
    assert absorbing.run([0, -1]) == 0


def test_parallel_sectors_caps_at_klein4():
    """The parallel fan-out's default sector count is the |V4| = 4 Klein-4
    ceiling — the algebraic cap, not an arbitrary parallelism knob."""
    sig = inspect.signature(Chain.parallel_sectors)
    assert sig.parameters["n_sectors"].default == 4


def test_empty_stage_has_no_implicit_default_form():
    """A stage carrying none of the six discriminators is rejected — there is
    no implicit seventh / fallback form the parser silently applies."""
    with pytest.raises(ValueError, match="no discriminator"):
        build_chain_from_toml_str('[chain]\nname = "x"\n[[stage]]\nnonsense = 1\n')
