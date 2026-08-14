"""rc432 (`#T1132`) — THE EIGHT ACQUIRE-BEFORE-VALIDATE SITES, DRIVEN.

WHY THIS FILE IS THE RC'S HIGHEST-VALUE DELIVERABLE
===================================================
rc432 ships two source scanners as well (``test_unowned_acquisition_rc432.py``
and ``test_c_resource_ownership_rc432.py``). **Neither of them can see the defect
this rc repaired**, and each says so in its own docstring. A ceiling seeded at
the live population COUNTS the seed and therefore cannot fire on it; the C gates
have no referent for a created node in ``srmech_genome.c`` at all. Scanners pin a
result. They do not produce it.

This file produces it. Every test below DRIVES a real op down its real error
path, in its own sandbox, and asserts the sandbox is byte-unchanged afterwards.
That covers all eight sites plus two hazards — including the five sites the
Python scanner permanently misses (a branch-local acquisition, an attribute-call
raiser, and three inside a ``for`` loop).

THE INSTRUMENT, AND THE TWO WAYS IT WAS WRONG FIRST
===================================================
The detector is one line: a probe FAILS if ``after - before`` is non-empty on a
call that raised. Two things about it are load-bearing and are inherited from the
spike that built it (``docs/srmech/notes/_s1_acquire_sites_rc432.py``), because
both were discovered by being WRONG:

1. **Baseline BETWEEN fixture setup and the driven call, never at slot creation.**
   v1 of the spike baselined at creation, so every node a fixture built — a source
   genome, a directory of ``.chr`` bundles — counted as an orphan the op left.
   Three within-op negative controls came back CONFIRMED on that build: a false
   positive in the direction that flatters the hypothesis, which is the one that
   must never be trusted. :class:`_Probe` splits ``setup`` from ``call`` for
   exactly this reason, and ``CTRL_P5`` holds that failure.

2. **A leftover node alone is NOT evidence — the exception TYPE must be the one
   the code catches.** The S2 injection first raised
   ``NativeGenomeError("...")`` with one argument, which made ``__init__`` raise
   ``TypeError``, which sailed straight past the ``except _native.NativeGenomeError``
   the site is written around. It still orphaned ``dest/``, so the probe still went
   green — while measuring a path the op never takes.

A SAME-SUBJECT CONTROL CANNOT DETECT A CROSS-SUBJECT CONFLICT
=============================================================
``CTRL_X`` is here because it is why rc431's root cause was missed.
``write_packed_graph`` was exercised against ITSELF — file over file, which
overwrites perfectly well — and never against a node a DIFFERENT op had left as a
directory. The same-subject arm passes and is blind; the cross arm raises
``IsADirectoryError``. **When testing a collision, vary the OTHER party.**

WHAT EACH TEST ASSERTS, AND WHAT IT DOES NOT
============================================
Each asserts (a) the op still raises — the repairs move an acquisition, they never
loosen a validation — and (b) nothing survives the raise. Neither asserts anything
about the SUCCESS path, which is unchanged at all eight sites and is covered by
the existing per-op suites.
"""

from __future__ import annotations

import json
import os
import shutil
import tempfile
from pathlib import Path
from typing import Callable, Optional

import pytest

from srmech import _native
from srmech.amsc.format import MPRRecord, write_ndjson
from srmech.biology import genome as G
from srmech.math import laplacian as L
from srmech.math.hv import HV
from srmech.mcp._mcpb import pack_mcpb


# ────────────────────────────────────────────────────────────────────────
# The detector
# ────────────────────────────────────────────────────────────────────────

def _tree(root: Path) -> frozenset:
    """Every path under ``root``, relative, directories suffixed ``/``."""
    out = set()
    for dirpath, dirnames, filenames in os.walk(root):
        base = Path(dirpath)
        for d in dirnames:
            out.add(str((base / d).relative_to(root)).replace("\\", "/") + "/")
        for f in filenames:
            out.add(str((base / f).relative_to(root)).replace("\\", "/"))
    return frozenset(out)


class _Probe:
    """One driven call in its own sandbox slot.

    The per-call slot is rc431's lesson made mechanical: a SHARED slot is exactly
    how the cross-op collision hid, because two ops writing into one directory
    cannot be told apart afterwards.
    """

    def __init__(self, root: Path) -> None:
        self.root = root

    def run(self, call: Callable, setup: Optional[Callable] = None) -> dict:
        ctx = setup(self.root) if setup is not None else None
        before = _tree(self.root)          # ← BASELINE AFTER FIXTURES. See §2 above.
        raised = None
        try:
            call(self.root, ctx)
        except BaseException as exc:       # noqa: BLE001 — deliberate: any exit counts
            raised = f"{type(exc).__name__}: {exc}"
        after = _tree(self.root)
        return {
            "raised": raised,
            "raised_type": raised.split(":")[0] if raised else "",
            "left_behind": sorted(after - before),
            "ctx": ctx,
        }


def _assert_clean(res: dict, site: str, expect_type: str) -> None:
    """The repaired site must still RAISE, with the same class of error, and must
    leave nothing behind."""
    assert res["raised"] is not None, (
        f"{site}: the driven call did NOT raise. The rc432 repairs move an "
        f"acquisition below a validation; they never loosen the validation. A "
        f"call that stopped failing is a DIFFERENT defect from the one measured."
    )
    assert res["raised_type"] == expect_type, (
        f"{site}: expected the call to fail with {expect_type}; got "
        f"{res['raised']!r}. A leftover node alone is not evidence — the "
        f"exception TYPE has to be the one the code is written around, or the "
        f"probe is measuring a path the op never takes (`#T1132`)."
    )
    assert not res["left_behind"], (
        f"{site}: the rejected call left {res['left_behind']} behind. An "
        f"acquisition above a validation is an ORPHAN on the error path: the "
        f"raise is loud and the node is silent, and the next op to touch that "
        f"path inherits a filesystem no caller asked for (`#T1132`)."
    )


@pytest.fixture()
def slot(tmp_path: Path) -> _Probe:
    root = tmp_path / "slot"
    root.mkdir()
    return _Probe(root)


# ────────────────────────────────────────────────────────────────────────
# Fixtures
# ────────────────────────────────────────────────────────────────────────

def _one(dim: int = 64):
    return G._default_coupling(dim)


def _leaves(n: int, dim: int = 64, base: int = 0):
    return [HV.from_sequence([(base + i + k) % 4 for k in range(dim)], sectors=4)
            for i in range(n)]


def _make_genome(dest: Path, label: str = "c"):
    o = _one()
    G.genome_save(G.chromosome(_leaves(2), o, label=label), dest, o)
    return dest, o


def _chr_dir_with(sandbox: Path, specs) -> Path:
    """A directory of ``.chr`` bundles. ``specs`` = ``[(filename, label)]``;
    filename order IS the ``sorted()`` order the register walks."""
    d = sandbox / "chrs"
    d.mkdir(parents=True, exist_ok=True)
    for i, (fname, label) in enumerate(specs):
        src = sandbox / f"src{i}"
        _make_genome(src, label=label)
        G.genome_export(src, label, d / fname)
    return d


def _inject_makedirs(fail_on: int):
    """Fail the ``fail_on``-th ``os.makedirs`` with a planted ENOSPC.

    Fault injection, not a caller-input case: ``recursive_cut``'s caller-input
    validation was ALREADY correct and already above every acquisition, so the
    only way to reach its setup sequence's error path is an I/O fault. That makes
    the S7 finding BOUNDED by construction, and the injector itself is validated
    by :func:`test_ctrl_injector_fires_and_rollback_silences_it` below — it is not
    trusted until both arms agree.
    """
    real = os.makedirs
    state = {"n": 0}

    def fake(path, mode=0o777, exist_ok=False):
        state["n"] += 1
        if state["n"] == fail_on:
            raise OSError(28, "planted ENOSPC (fault injection)", str(path))
        return real(path, mode, exist_ok=exist_ok)

    def install():
        os.makedirs = fake
        L.os.makedirs = fake

    def restore():
        os.makedirs = real
        L.os.makedirs = real

    return install, restore


# ────────────────────────────────────────────────────────────────────────
# CONTROLS — the file refuses to be believed unless these agree
# ────────────────────────────────────────────────────────────────────────

def test_ctrl_p1_planted_orphan_is_detected(slot: _Probe) -> None:
    """POSITIVE CONTROL. A scanner that cannot report a defect is not an
    instrument, and a green suite over a blind detector is the worst outcome
    available. Plant the exact shape and require the detector to see it."""
    def planted(sandbox: Path, ctx=None):
        (sandbox / "made").mkdir(parents=True)
        raise ValueError("planted: acquire-before-validate")

    res = slot.run(planted)
    assert res["raised_type"] == "ValueError"
    assert res["left_behind"] == ["made/"], (
        "the detector did not see a directory created immediately before a "
        "raise. Every CLEAN verdict in this file is worthless until it does."
    )


def test_ctrl_n2_scoped_acquisition_reads_clean(slot: _Probe) -> None:
    """NEGATIVE CONTROL — repair shape (b). An acquisition inside a
    ``try/finally`` must read clean, or the detector is simply reporting
    'something raised'."""
    def scoped(sandbox: Path, ctx=None):
        d = sandbox / "made"
        d.mkdir(parents=True)
        try:
            raise ValueError("planted: raise inside the scope")
        finally:
            shutil.rmtree(d, ignore_errors=True)

    res = slot.run(scoped)
    assert res["raised_type"] == "ValueError"
    assert res["left_behind"] == []


def test_ctrl_p5_fixture_nodes_are_not_counted_as_orphans(slot: _Probe) -> None:
    """THE FIXTURE-BLINDNESS CONTROL — v1 of the spike's detector FAILED this.

    A fixture builds real nodes; the driven call then acquires nothing and
    raises. If the baseline is taken at slot creation instead of after setup, the
    fixture's own nodes are reported as orphans and the site comes back CONFIRMED
    when it is clean. That is a false positive in the direction that flatters the
    hypothesis."""
    def setup(sandbox: Path):
        (sandbox / "fixture").mkdir(parents=True)
        (sandbox / "fixture" / "f.bin").write_bytes(b"x")
        return None

    def acquires_nothing(sandbox: Path, ctx=None):
        raise ValueError("planted: raises without acquiring")

    res = slot.run(acquires_nothing, setup)
    assert res["raised_type"] == "ValueError"
    assert res["left_behind"] == [], (
        "fixture nodes were counted as orphans — the baseline is being taken "
        "before setup rather than between setup and the driven call."
    )


def test_ctrl_injector_fires_and_rollback_silences_it(slot: _Probe) -> None:
    """The S7 fault injector, validated from BOTH sides in one test: without a
    rollback the planted ENOSPC leaves the first directory behind; with one it
    does not. Neither arm alone would establish the injector works."""
    def no_rollback(sandbox: Path, ctx=None):
        install, restore = _inject_makedirs(2)
        install()
        try:
            os.makedirs(str(sandbox / "wd"), exist_ok=True)            # 1st — ok
            os.makedirs(str(sandbox / "wd" / "queue"), exist_ok=True)  # 2nd — fails
        finally:
            restore()

    res = slot.run(no_rollback)
    assert res["raised_type"] == "OSError"
    assert res["left_behind"] == ["wd/"], (
        "the injected ENOSPC did not fire, or the detector did not see its "
        "residue — the S7 measurement below rests on this box."
    )

    def with_rollback(sandbox: Path, ctx=None):
        install, restore = _inject_makedirs(2)
        install()
        made = []
        try:
            os.makedirs(str(sandbox / "wd2"), exist_ok=True)
            made.append(sandbox / "wd2")
            os.makedirs(str(sandbox / "wd2" / "queue"), exist_ok=True)
            made.clear()
        except BaseException:
            for m in reversed(made):
                shutil.rmtree(m, ignore_errors=True)
            raise
        finally:
            restore()

    res2 = slot.run(with_rollback)
    assert res2["raised_type"] == "OSError"
    assert res2["left_behind"] == []


# ────────────────────────────────────────────────────────────────────────
# S1 .. S8 — the eight repaired sites
# ────────────────────────────────────────────────────────────────────────

def test_s1_genome_save_rejects_without_creating_its_target(slot: _Probe) -> None:
    """S1 — ``genome_save``. Its ``path.mkdir`` was the FIRST statement of the
    body, above every validation; a rejected save left a directory at the target.
    This is the seed defect: it is the node ``write_packed_graph`` then opened as
    a file and died on (the rc431 CI red)."""
    def setup(sandbox: Path):
        o = _one()
        return (G.chromosome(_leaves(2), o, label="c"), o)

    def call(sandbox: Path, ctx):
        strand, o = ctx
        return G.genome_save(strand, sandbox / "g", o, labels=["not_c"])

    _assert_clean(slot.run(call, setup), "S1 genome_save", "ValueError")


def test_s2_genome_import_native_branch_rolls_back_dest(slot: _Probe) -> None:
    """S2 — ``genome_import``'s native branch, repaired by SCOPE not reorder: the
    native seed save genuinely needs the directory to exist first, so the
    acquisition gets an owner instead of a new position.

    The failure is INJECTED at the module boundary because the working-tree
    ``.so`` is a stale-ABI build and the branch is otherwise unreachable. The
    injected exception is constructed with BOTH arguments on purpose — a one-arg
    ``NativeGenomeError`` raises ``TypeError`` from ``__init__`` and sails past the
    very ``except`` clause the site is written around."""
    def setup(sandbox: Path):
        src = sandbox / "src"
        _make_genome(src)
        chrp = sandbox / "bundle.chr"
        G.genome_export(src, "c", chrp)
        return chrp

    def call(sandbox: Path, ctx):
        real_has = _native.has_native_genome
        real_imp = getattr(_native, "genome_import_c", None)

        def boom(*a, **k):
            raise _native.NativeGenomeError("srmech_genome_import", 5)

        _native.has_native_genome = lambda: True
        _native.genome_import_c = boom
        try:
            return G.genome_import(ctx, sandbox / "dest")
        finally:
            _native.has_native_genome = real_has
            if real_imp is not None:
                _native.genome_import_c = real_imp

    _assert_clean(slot.run(call, setup), "S2 genome_import (native)",
                  "GenomeBoundingError")


def test_s3_genome_explode_rejects_unsafe_label_without_out_dir(
        slot: _Probe) -> None:
    """S3 — ``genome_explode``. A plain reorder: the label-safety loop reads only
    ``labels``, already derived above, so the ``mkdir`` moves below it."""
    def setup(sandbox: Path):
        src = sandbox / "src"
        _make_genome(src, label="a/b")
        return src

    def call(sandbox: Path, ctx):
        return G.genome_explode(ctx, sandbox / "out")

    _assert_clean(slot.run(call, setup), "S3 genome_explode", "ValueError")


def test_s4_register_attested_rejects_before_creating_amsc_root(
        slot: _Probe) -> None:
    """S4 — ``genome_register_attested``, outer acquisition."""
    def setup(sandbox: Path):
        return _chr_dir_with(sandbox, [("01.chr", "a/b")])

    def call(sandbox: Path, ctx):
        return G.genome_register_attested(ctx, sandbox / "amsc", source="probe")

    _assert_clean(slot.run(call, setup), "S4 genome_register_attested",
                  "ValueError")


def test_s8_register_attested_leaves_no_partial_loop_artifacts(
        slot: _Probe) -> None:
    """S8 — the SAME op's inner loop, and the reason S4 needed a two-pass rather
    than a reorder.

    The bundles are named so ``sorted()`` walks the GOOD one first: through rc431
    the first iteration wrote ``amsc/good/``, its ``descriptor.toml`` and its
    ``row.ndjson``, and all three survived the second iteration's raise. Partial-
    loop orphaning is the same defect with a multiplier, and it is the shape the
    rc432 source scanner permanently cannot see — a loop body breaks the ordering
    proof the scanner's soundness rests on."""
    def setup(sandbox: Path):
        return _chr_dir_with(sandbox,
                             [("01_good.chr", "good"), ("02_bad.chr", "a/b")])

    def call(sandbox: Path, ctx):
        return G.genome_register_attested(ctx, sandbox / "amsc", source="probe")

    _assert_clean(slot.run(call, setup),
                  "S8 genome_register_attested (inner loop)", "ValueError")


def test_s5_pack_mcpb_rejects_server_type_without_creating_out_dir(
        slot: _Probe) -> None:
    """S5 — ``pack_mcpb``. Reorder, feasible because ``build_manifest`` is
    filesystem-free (measured: it walks the registry and touches no path)."""
    def call(sandbox: Path, ctx=None):
        return pack_mcpb(str(sandbox / "out"), server_type="bogus")

    _assert_clean(slot.run(call), "S5 pack_mcpb", "ValueError")


def test_s5_server_type_raises_valueerror_in_both_interpreter_modes() -> None:
    """S5's second half, and the argument for it is NOT the usual one.

    ``server_type`` was validated by an ``assert``, but this is NOT a `#T1131`
    instance: under ``python -O`` the site still rejected, because ``_server_block``
    raises ``ValueError`` further down. What was wrong is that the exception TYPE
    was interpreter-mode-dependent — ``AssertionError`` normally, ``ValueError``
    under ``-O`` — so a caller's ``except ValueError`` worked in optimized mode and
    not otherwise. Both modes now raise ``ValueError``.

    Driven in a SUBPROCESS because ``-O`` is an interpreter start-up flag: there is
    no way to ask the running interpreter this question."""
    import subprocess
    import sys

    snippet = (
        "import json, sys, tempfile\n"
        "from pathlib import Path\n"
        "from srmech.mcp._mcpb import pack_mcpb\n"
        "root = Path(tempfile.mkdtemp(prefix='s5_mode_'))\n"
        "out = {'optimize': sys.flags.optimize}\n"
        "try:\n"
        "    pack_mcpb(str(root / 'out'), server_type='bogus',"
        " manifest_only=True)\n"
        "    out['raised'] = None\n"
        "except BaseException as exc:\n"
        "    out['raised'] = type(exc).__name__\n"
        "out['node_exists'] = (root / 'out').exists()\n"
        "print(json.dumps(out, sort_keys=True))\n"
    )

    seen = {}
    for label, flags in (("plain", []), ("dash_O", ["-O"])):
        proc = subprocess.run([sys.executable, *flags, "-c", snippet],
                              capture_output=True, text=True, timeout=600)
        assert proc.returncode == 0, (
            f"{label} subprocess failed: {proc.stderr[-800:]}")
        seen[label] = json.loads(proc.stdout.strip().splitlines()[-1])

    assert seen["dash_O"]["optimize"] >= 1, (
        "the -O arm did not actually run optimized; the comparison is vacuous")
    for label, payload in seen.items():
        assert payload["raised"] == "ValueError", (
            f"{label}: expected ValueError, got {payload['raised']!r}. The "
            f"whole point of converting the assert is that the TYPE no longer "
            f"depends on the interpreter mode (`#T1132`).")
        assert not payload["node_exists"], (
            f"{label}: the rejected call left its out_dir behind")


def test_s6_write_ndjson_serialises_before_touching_the_filesystem(
        slot: _Probe) -> None:
    """S6 — ``write_ndjson``. The ``mkdir`` and the truncating ``open`` both sat
    above the serialise loop, so an unserialisable record left a created parent
    directory AND a partial file."""
    def setup(sandbox: Path):
        ok = MPRRecord(mpr_version="1.0", data={"i": 0},
                       data_schema_id="probe://s", attestation={}, rendering={})
        bad = MPRRecord(mpr_version="1.0", data={"i": object()},
                        data_schema_id="probe://s", attestation={},
                        rendering={})
        return [ok, bad]

    def call(sandbox: Path, ctx):
        return write_ndjson(sandbox / "sub" / "out.ndjson", ctx)

    _assert_clean(slot.run(call, setup), "S6 write_ndjson", "TypeError")


def test_s6b_write_ndjson_does_not_destroy_a_pre_existing_good_file(
        slot: _Probe) -> None:
    """S6b — THE WORSE HAZARD, and the one a same-subject probe cannot see.

    Destroying prior data outranks orphaning a fresh node. Measured through rc431:
    a 114-byte valid NDJSON came back as 108 bytes of a DIFFERENT file, because
    ``open(path, "w")`` TRUNCATES before the first record is serialised. A probe on
    a fresh path is blind to this — there is nothing there to lose — which is why
    the fixture here deliberately writes a good file first.

    ⚠️ BOUNDARY, and it is real: this covers SERIALISATION failure, not WRITE
    failure. An ENOSPC part-way through the write still truncates. That is the
    crash-durability class, owned by atomic write-and-replace, deferred to
    `#T1133` with its own falsifier (a ``kill -9`` mid-write) that rc432 did not
    measure and does not claim."""
    def setup(sandbox: Path):
        p = sandbox / "sub" / "out.ndjson"
        p.parent.mkdir(parents=True)
        good = MPRRecord(mpr_version="1.0", data={"kept": True},
                         data_schema_id="probe://s", attestation={},
                         rendering={})
        write_ndjson(p, [good])
        return (p, p.read_bytes())

    def call(sandbox: Path, ctx):
        p, _prior = ctx
        ok = MPRRecord(mpr_version="1.0", data={"i": 0},
                       data_schema_id="probe://s", attestation={}, rendering={})
        bad = MPRRecord(mpr_version="1.0", data={"i": object()},
                        data_schema_id="probe://s", attestation={},
                        rendering={})
        return write_ndjson(p, [ok, bad])

    res = slot.run(call, setup)
    path, prior = res["ctx"]
    assert res["raised_type"] == "TypeError", res["raised"]
    assert prior, "the fixture wrote nothing — the test cannot detect destruction"
    assert path.exists(), "the pre-existing good NDJSON was DELETED outright"
    assert path.read_bytes() == prior, (
        "write_ndjson destroyed a pre-existing good NDJSON while failing to "
        "serialise a record. Truncation happens at open(), so every byte of the "
        "caller's prior data is gone before the failure is even reached "
        "(`#T1132` S6b)."
    )


def test_s7a_caller_named_work_dir_is_left_alone_by_contract(
        slot: _Probe) -> None:
    """S7a — NOT-A-DEFECT, asserted rather than assumed.

    A CALLER-NAMED ``work_dir`` keeps what the call created, even on a raise. That
    is deliberate: the caller owns the directory, it is reused across calls, and
    the tomes already written are the bounded record. Removing it would be the
    framework deleting data it does not own. The docstring says so; this test
    pins the behaviour so a later 'tidy-up' cannot silently change it."""
    def call(sandbox: Path, ctx=None):
        install, restore = _inject_makedirs(2)
        install()
        try:
            return L.recursive_cut(4, [(0, 1), (2, 3)], max_tome=2,
                                   work_dir=str(sandbox / "wd"))
        finally:
            restore()

    res = slot.run(call)
    assert res["raised_type"] == "OSError", res["raised"]
    assert res["left_behind"] == ["wd/"], (
        f"a caller-named work_dir must be left as the caller's own on the error "
        f"path; got {res['left_behind']}. If this now reads [] the op has "
        f"started deleting a directory it does not own (`#T1132` S7a)."
    )


def test_s7b_work_dir_none_leaks_no_unnameable_scratch_dir() -> None:
    """S7b — S7's REAL defect, and the one the read-only triage could not see.

    With ``work_dir=None`` the scratch directory's name is minted by ``mkdtemp``
    INSIDE the call and reaches the caller only through the return value. When the
    call raises, the return never arrives: the caller holds an orphan it cannot
    NAME, in the system temp area, that no party could ever clean up. That is
    strictly worse than a caller-named directory left behind, and it is why S7's
    two branches got opposite rulings from one repair.

    Not a sandbox probe — the subject is the system temp area itself, which is the
    whole point."""
    tmp_root = Path(tempfile.gettempdir())
    before = {p.name for p in tmp_root.glob("srmech_cut_*")}

    install, restore = _inject_makedirs(2)
    install()
    raised = None
    try:
        L.recursive_cut(4, [(0, 1), (2, 3)], max_tome=2, work_dir=None)
    except BaseException as exc:                       # noqa: BLE001
        raised = f"{type(exc).__name__}: {exc}"
    finally:
        restore()

    after = {p.name for p in tmp_root.glob("srmech_cut_*")}
    leaked = sorted(after - before)
    for name in leaked:                                # never leave our own mess
        shutil.rmtree(tmp_root / name, ignore_errors=True)

    assert raised is not None and raised.startswith("OSError"), (
        f"the injected fault did not reach recursive_cut; got {raised!r}")
    assert leaked == [], (
        f"recursive_cut(work_dir=None) leaked {leaked} into {tmp_root}. The "
        f"caller cannot learn those names — the return value that would have "
        f"carried them never arrived (`#T1132` S7b)."
    )


# ────────────────────────────────────────────────────────────────────────
# CTRL-X — the cross-subject collision that IS rc431's root cause
# ────────────────────────────────────────────────────────────────────────

def test_ctrl_x_same_subject_arm_passes_and_is_therefore_blind(
        slot: _Probe) -> None:
    """The arm that shipped rc431's red. ``write_packed_graph`` over its OWN
    prior output succeeds — file over file overwrites perfectly well — so a
    same-subject probe reports green and sees nothing.

    This test asserts the BLINDNESS, deliberately. It is here so the next reader
    cannot mistake the green arm below for coverage."""
    def same(sandbox: Path, ctx=None):
        n = sandbox / "node"
        L.write_packed_graph(str(n), [(0, 1)], [1.0])
        L.write_packed_graph(str(n), [(0, 1), (1, 2)], [1.0, 1.0])

    res = slot.run(same)
    assert res["raised"] is None, (
        "the same-subject arm started failing — it is supposed to pass, which is "
        "exactly why it is blind to the cross-subject collision")


def test_ctrl_x_cross_subject_collision_no_longer_occurs(slot: _Probe) -> None:
    """The arm that would have caught it. ``genome_save`` is driven down its
    REJECT path at node N, then ``write_packed_graph`` opens N as a file.

    Through rc431 this raised ``IsADirectoryError``, because the rejected save had
    left N behind as a directory. After the S1 repair the rejected save leaves
    nothing, so N is free and the second op succeeds. **When testing a collision,
    vary the OTHER party.**"""
    def cross(sandbox: Path, ctx=None):
        n = sandbox / "node"
        o = _one()
        strand = G.chromosome(_leaves(2), o, label="c")
        with pytest.raises(ValueError):
            G.genome_save(strand, n, o, labels=["not_c"])
        assert not n.exists(), (
            "the rejected genome_save left node N behind — the collision is "
            "still armed")
        L.write_packed_graph(str(n), [(0, 1)], [1.0])   # wants N as a FILE
        assert n.is_file()

    res = slot.run(cross)
    assert res["raised"] is None, (
        f"the cross-subject collision still occurs: {res['raised']}. This is "
        f"the rc431 CI red reproduced (`#T1132`).")
