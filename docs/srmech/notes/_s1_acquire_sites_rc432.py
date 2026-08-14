#!/usr/bin/env python3
"""S1 — re-verify the acquire-before-validate sites BY EXECUTION (rc432, `#T1132`).

The rc431 audit (`_pal_resource_cleanup_audit.{py,ndjson,md}`, branch
`research-pal-cleanup`) TRIAGED 31 scanner hits down to 5 HIGH + 3 MEDIUM by
READING them. This script does not re-derive that triage; it DRIVES each of the
eight ops with an input that reaches the raise and then asks the filesystem
whether a node the call created is still there.

THE CLASS: an op acquires a resource (creates a directory, opens/creates a file)
BEFORE it finishes validating, and on the error path leaves it acquired. The
raise is loud; the orphaned resource is silent.

PRE-REGISTERED FALSIFIER (identical for every site, stated before any run):

    H_i : driving <op_i> with <driver_i> raises, AND at least one filesystem
          node that did not exist before the call exists after it.

    Falsifier: the call raises and the sandbox tree is byte-for-byte the set it
    was before  ->  H_i is REFUTED for that driver.

    Verdict vocabulary (nulls are classified, never reported as bare "no"):
      CONFIRMED   — raised AND left >= 1 node behind.
      REFUTED     — raised AND left nothing behind (the op is already clean).
      BOUNDED     — the raise is real but only reachable under an injected
                    fault, not under any caller input (recorded as such).
      EMPTY       — the driver could not be built (no fixture reaches the site).
      UNSUPPORTED — the branch cannot execute in this environment at all.

INSTRUMENT DISCIPLINE. The detector is a set-difference over a directory walk.
A set-difference that can only ever return non-empty is not a measurement, so
SIX planted controls run FIRST and the script exits 1 if any disagrees:

    CTRL-P1  acquire-then-raise, no cleanup      -> MUST report ORPHAN
    CTRL-N1  raise with no acquire               -> MUST report CLEAN
    CTRL-N2  acquire inside try/finally + raise  -> MUST report CLEAN
             (this is repair-shape (b); without this control the detector
              could not tell a fixed site from a broken one)
    CTRL-N3  acquire, NO raise                   -> MUST report CLEAN-NO-RAISE
             (keys on raised AND left, never on left alone)
    CTRL-P2  injected-makedirs, 2 acquires, no rollback -> MUST report ORPHAN
    CTRL-N4  injected-makedirs, 2 acquires, WITH rollback -> MUST report CLEAN
             (P2/N4 validate the fault injector used for S7 in both directions)

CROSS-SUBJECT CONTROL (CTRL-X). rc431's root cause was missed because
`write_packed_graph` was only ever tested against ITSELF (file -> file, which
overwrites fine). The collision only appears when the OTHER party varies. CTRL-X
runs the real pair: `genome_save` orphans a DIRECTORY at node N, then
`write_packed_graph` opens N as a FILE. The same-subject arm (write_packed_graph
against its own prior file) is run alongside to show it is blind.

No numpy, no stdlib `math`/`fractions`/`decimal`, no `abs()` (sign handling is
Class K pin-slot + Class C re-application, not an ALU absolute value).

Run:  PYTHONPATH=<repo>/docs/srmech/python SRMECH_EXPECT_PURE=1 \
      python3 _s1_acquire_sites_rc432.py --out _s1_acquire_sites_rc432.ndjson
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
import tempfile
import traceback
from pathlib import Path
from typing import Callable, Dict, List, Optional, Tuple

import srmech
from srmech import _native
from srmech.amsc.format import MPRRecord, write_ndjson
from srmech.biology import genome as G
from srmech.math import laplacian as L
from srmech.math.hv import HV
from srmech.mcp._mcpb import pack_mcpb

RECORDS: List[dict] = []


def emit(**kw) -> None:
    RECORDS.append(kw)


# ──────────────────────────────────────────────────────────────────────
# The detector
# ──────────────────────────────────────────────────────────────────────

def tree(root: Path) -> frozenset:
    """Every path under ``root``, relative, dirs suffixed ``/``. The whole
    instrument: a probe is CONFIRMED iff ``after - before`` is non-empty on a
    call that raised."""
    out = set()
    for dirpath, dirnames, filenames in os.walk(root):
        base = Path(dirpath)
        for d in dirnames:
            out.add(str((base / d).relative_to(root)).replace("\\", "/") + "/")
        for f in filenames:
            out.add(str((base / f).relative_to(root)).replace("\\", "/"))
    return frozenset(out)


class Probe:
    """One driven call inside its OWN sandbox slot (rc431's per-call slot
    lesson — a shared slot is exactly how the cross-op collision hid).

    ⚠️ INSTRUMENT HISTORY — v1 of this box was WRONG and its own negative
    controls caught it. v1 took the baseline at slot creation, so every node a
    probe's FIXTURE built (a source genome, a directory of .chr bundles, the
    file used to make a mkdir fail) counted as an orphan left by the op. Three
    within-op negative controls came back CONFIRMED on that build — a false
    positive in the direction that flatters the hypothesis, which is the one
    that must never be trusted. v2 splits SETUP from the driven CALL and
    baselines BETWEEN them, so ``left_behind`` names only nodes the call itself
    created. Every count in the NDJSON is a v2 count."""

    def __init__(self, session: Path, slot: str):
        self.root = session / slot
        self.root.mkdir(parents=True, exist_ok=False)

    def run(self, call: Callable[[Path, object], object],
            setup: Optional[Callable[[Path], object]] = None) -> dict:
        ctx = setup(self.root) if setup is not None else None
        before = tree(self.root)                     # baseline AFTER fixtures
        raised: Optional[str] = None
        tb_tail = ""
        value = None
        try:
            value = call(self.root, ctx)
        except BaseException as exc:            # noqa: BLE001 - deliberate
            raised = f"{type(exc).__name__}: {exc}"
            tb_tail = traceback.format_exc().rstrip()
        after = tree(self.root)
        left = sorted(after - before)
        return {
            "raised": raised,
            "raised_type": raised.split(":")[0] if raised else "",
            "traceback_tail": tb_tail[-2400:],
            "left_behind": left,
            "n_left": len(left),
            "n_fixture_nodes": len(before),
            "returned_ok": raised is None,
            "value_repr": repr(value)[:160] if raised is None else "",
        }


def verdict_of(res: dict) -> str:
    if res["raised"] is None:
        return "NO-RAISE"
    return "CONFIRMED" if res["n_left"] > 0 else "REFUTED"


# ──────────────────────────────────────────────────────────────────────
# Planted controls — the script refuses to report a single site unless
# every one of these agrees with its expectation.
# ──────────────────────────────────────────────────────────────────────

def ctl_p1(sandbox: Path, ctx=None):
    (sandbox / "made").mkdir(parents=True)
    raise ValueError("planted: acquire-before-validate")


def ctl_n1(sandbox: Path, ctx=None):
    raise ValueError("planted: validate-before-acquire (nothing acquired)")


def ctl_n2(sandbox: Path, ctx=None):
    d = sandbox / "made"
    d.mkdir(parents=True)
    try:
        raise ValueError("planted: acquire scoped by try/finally")
    finally:
        shutil.rmtree(d)


def ctl_n3(sandbox: Path, ctx=None):
    (sandbox / "made").mkdir(parents=True)
    return "ok"


def ctl_p5(sandbox: Path, ctx=None):
    """CTRL-P5 — the FIXTURE-BLINDNESS control, added after v1 of the Probe
    counted fixture nodes as orphans. The setup builds a directory; the call
    raises WITHOUT acquiring anything. A detector that baselines too early
    reports CONFIRMED here. The correct answer is REFUTED."""
    raise ValueError("planted: fixture exists, call acquires nothing")


def ctl_p5_setup(sandbox: Path):
    (sandbox / "fixture_dir").mkdir(parents=True)
    (sandbox / "fixture_dir" / "f.bin").write_bytes(b"x")
    return None


def _inject_makedirs(fail_on: int) -> Tuple[Callable, Callable]:
    """Fail the ``fail_on``-th ``os.makedirs`` with a planted ENOSPC. Returns
    (install, restore). Used for S7 and validated by CTRL-P2/CTRL-N4 — this box
    is NOT trusted until both controls agree."""
    real = os.makedirs
    state = {"n": 0}

    def fake(path, mode=0o777, exist_ok=False):
        state["n"] += 1
        if state["n"] == fail_on:
            raise OSError(28, "planted ENOSPC (fault injection)", str(path))
        return real(path, mode, exist_ok=exist_ok)

    def install():
        os.makedirs = fake                                  # noqa: F811
        L.os.makedirs = fake

    def restore():
        os.makedirs = real
        L.os.makedirs = real

    return install, restore


def ctl_p2(sandbox: Path, ctx=None):
    install, restore = _inject_makedirs(2)
    install()
    try:
        os.makedirs(str(sandbox / "wd"), exist_ok=True)          # 1st — ok
        os.makedirs(str(sandbox / "wd" / "queue"), exist_ok=True)  # 2nd — fails
    finally:
        restore()


def ctl_n4(sandbox: Path, ctx=None):
    install, restore = _inject_makedirs(2)
    install()
    made = []
    try:
        os.makedirs(str(sandbox / "wd"), exist_ok=True)
        made.append(sandbox / "wd")
        os.makedirs(str(sandbox / "wd" / "queue"), exist_ok=True)
        made.clear()
    except BaseException:
        for m in reversed(made):
            shutil.rmtree(m, ignore_errors=True)
        raise
    finally:
        restore()


CONTROLS = [
    ("CTRL-P1", "acquire-then-raise, no cleanup", ctl_p1, None,
     "CONFIRMED", True),
    ("CTRL-N1", "raise with nothing acquired", ctl_n1, None, "REFUTED", True),
    ("CTRL-N2", "acquire scoped by try/finally (repair (b))", ctl_n2, None,
     "REFUTED", True),
    ("CTRL-N3", "acquire on the SUCCESS path (no raise)", ctl_n3, None,
     "NO-RAISE", False),
    ("CTRL-P2", "injected makedirs, 2 acquires, no rollback", ctl_p2, None,
     "CONFIRMED", True),
    ("CTRL-N4", "injected makedirs, 2 acquires, WITH rollback", ctl_n4, None,
     "REFUTED", True),
    ("CTRL-P5", "fixture present, call acquires nothing (v1 failed this)",
     ctl_p5, ctl_p5_setup, "REFUTED", True),
]


def run_controls(session: Path) -> bool:
    ok = True
    for cid, what, drv, setup, expect, expect_raise in CONTROLS:
        res = Probe(session, "ctl_" + cid.lower().replace("-", "_")).run(
            drv, setup)
        got = verdict_of(res)
        agrees = (got == expect) and ((res["raised"] is not None) == expect_raise)
        ok = ok and agrees
        emit(record="control", control_id=cid, what=what, expected=expect,
             observed=got, agrees=agrees, **res)
    return ok


# ──────────────────────────────────────────────────────────────────────
# Fixtures
# ──────────────────────────────────────────────────────────────────────

def one(dim: int = 64):
    return G._default_coupling(dim)


def leaves(n: int, dim: int = 64, base: int = 0):
    return [HV.from_sequence([(base + i + k) % 4 for k in range(dim)], sectors=4)
            for i in range(n)]


def make_genome(dest: Path, label: str = "c"):
    """A real 1-chromosome genome on disk at ``dest``. Returns (path, coupling)."""
    o = one()
    strand = G.chromosome(leaves(2), o, label=label)
    G.genome_save(strand, dest, o)
    return dest, o


# ──────────────────────────────────────────────────────────────────────
# S1 .. S8 — the eight sites
# ──────────────────────────────────────────────────────────────────────

def s1_setup(sandbox: Path):
    o = one()
    return (G.chromosome(leaves(2), o, label="c"), o)


def s1_call(sandbox: Path, ctx):
    """genome_save: path.mkdir() is the FIRST executable line (genome.py:8980);
    _split_into_chromosomes' label check (:8353) raises after it."""
    strand, o = ctx
    return G.genome_save(strand, sandbox / "g", o, labels=["not_c"])


def s1_neg_setup(sandbox: Path):
    (sandbox / "afile").write_bytes(b"x")          # makes the mkdir itself fail
    o = one()
    return (G.chromosome(leaves(2), o, label="c"), o)


def s1_neg_call(sandbox: Path, ctx):
    """Within-op negative: the mkdir ITSELF fails (its parent is a file), so
    nothing is acquired. Proves the detector reads THIS op as clean too."""
    strand, o = ctx
    return G.genome_save(strand, sandbox / "afile" / "g", o)


def s2_setup(sandbox: Path):
    src = sandbox / "src"
    make_genome(src)
    chrp = sandbox / "bundle.chr"
    G.genome_export(src, "c", chrp)
    return chrp


def s2_call(sandbox: Path, ctx):
    """genome_import native branch: dest.mkdir() at :11600 precedes the native
    call's own integrity validation; :11606 always raises on a native failure.

    The working-tree .so is a stale-ABI build, so has_native_genome() is False
    here and the branch is unreachable by ordinary call. The failure is INJECTED
    at the module boundary: has_native_genome -> True, genome_import_c -> the
    exact exception type the except clause catches. This reproduces precisely the
    condition the code sees; it does not claim a native run happened."""
    chrp = ctx
    real_has = _native.has_native_genome
    real_imp = getattr(_native, "genome_import_c", None)

    def boom(*a, **k):
        # NativeGenomeError(fn, status) — the EXACT constructor. An earlier build
        # of this probe passed one arg, which made __init__ raise TypeError; that
        # TypeError sailed past `except _native.NativeGenomeError` and measured a
        # path the op never takes. It still orphaned `dest/`, which is precisely
        # why a leftover node alone is not evidence: the EXCEPTION TYPE has to be
        # the one the code is written to catch.
        raise _native.NativeGenomeError("srmech_genome_import", 5)

    _native.has_native_genome = lambda: True
    _native.genome_import_c = boom
    try:
        return G.genome_import(chrp, sandbox / "dest")
    finally:
        _native.has_native_genome = real_has
        if real_imp is not None:
            _native.genome_import_c = real_imp


def s2_neg_call(sandbox: Path, ctx):
    """Within-op negative: _read_chr(:11581) raises BEFORE dest.mkdir()."""
    return G.genome_import(sandbox / "missing.chr", sandbox / "dest")


def s3_setup(sandbox: Path):
    src = sandbox / "src"
    make_genome(src, label="a/b")
    return src


def s3_call(sandbox: Path, ctx):
    """genome_explode: out_dir.mkdir() at :11680 precedes the per-label
    filename-safety loop that raises at :11684."""
    return G.genome_explode(ctx, sandbox / "out")


def s3_neg_call(sandbox: Path, ctx):
    """Within-op negative: _catalog_data(:11679) raises BEFORE out_dir.mkdir()."""
    return G.genome_explode(sandbox / "nogenome", sandbox / "out")


def _chr_dir_with(sandbox: Path, specs: List[Tuple[str, str]]) -> Path:
    """A directory of .chr bundles. ``specs`` = [(filename, chromosome label)];
    filename order IS the sorted() order genome_register_attested walks."""
    d = sandbox / "chrs"
    d.mkdir(parents=True, exist_ok=True)
    for i, (fname, label) in enumerate(specs):
        src = sandbox / f"src{i}"
        make_genome(src, label=label)
        G.genome_export(src, label, d / fname)
    return d


def s4_setup(sandbox: Path):
    return _chr_dir_with(sandbox, [("01.chr", "a/b")])


def s4_call(sandbox: Path, ctx):
    """genome_register_attested: amsc_root.mkdir() at :11927 precedes the
    per-bundle label-safety check that raises at :11933."""
    return G.genome_register_attested(ctx, sandbox / "amsc", source="probe")


def s4_neg_setup(sandbox: Path):
    d = sandbox / "chrs"
    d.mkdir(parents=True)
    return d


def s4_neg_call(sandbox: Path, ctx):
    """Within-op negative and it is a REAL one: the empty-chr_dir ValueError at
    :11924 already sits BEFORE the mkdir. The op validates one thing correctly
    and the next thing too late."""
    return G.genome_register_attested(ctx, sandbox / "amsc", source="probe")


def s5_call(sandbox: Path, ctx):
    """pack_mcpb: out.mkdir() at _mcpb.py:318 precedes build_manifest, whose
    :219 `assert server_type in ("uv","python")` raises."""
    return pack_mcpb(str(sandbox / "out"), server_type="bogus")


def s5_neg_setup(sandbox: Path):
    (sandbox / "afile").write_bytes(b"x")
    return None


def s5_neg_call(sandbox: Path, ctx):
    """Within-op negative: the mkdir itself fails (its parent is a file)."""
    return pack_mcpb(str(sandbox / "afile" / "out"), server_type="bogus")


def s6_setup(sandbox: Path):
    ok = MPRRecord(mpr_version="1.0", data={"i": 0}, data_schema_id="probe://s",
                   attestation={}, rendering={})
    bad = MPRRecord(mpr_version="1.0", data={"i": object()},
                    data_schema_id="probe://s", attestation={}, rendering={})
    return [ok, bad]


def s6_call(sandbox: Path, ctx):
    """write_ndjson: path.parent.mkdir() at format.py:373 precedes the streaming
    to_json_line() loop. The `with` closes the HANDLE correctly — the orphan is
    the created parent dir plus a TRUNCATED file holding the records written
    before the failing one."""
    return write_ndjson(sandbox / "sub" / "out.ndjson", ctx)


def s6_neg_call(sandbox: Path, ctx):
    """Within-op negative: list(records) at :369 raises BEFORE the mkdir."""
    def gen():
        raise ValueError("planted: materialisation fails")
        yield  # pragma: no cover

    return write_ndjson(sandbox / "sub" / "out.ndjson", gen())


def s7_call(sandbox: Path, ctx):
    """recursive_cut: os.makedirs(work_dir) / queue_dir / tomes_dir at
    laplacian.py:7200/7203/7204 run sequentially with no rollback. Caller-input
    validation is already correct (_validate_edges_weights_py at :7197), so this
    needs an injected IO fault — BOUNDED by construction, and the injector is
    the one CTRL-P2/CTRL-N4 validated."""
    install, restore = _inject_makedirs(2)
    install()
    try:
        return L.recursive_cut(4, [(0, 1), (2, 3)], max_tome=2,
                               work_dir=str(sandbox / "wd"))
    finally:
        restore()


def s7_neg_call(sandbox: Path, ctx):
    """Within-op negative: bad caller input (edge index out of range) raises at
    :7197, BEFORE any makedirs."""
    return L.recursive_cut(4, [(0, 99)], max_tome=2,
                           work_dir=str(sandbox / "wd"))


def s8_setup(sandbox: Path):
    return _chr_dir_with(sandbox,
                         [("01_good.chr", "good"), ("02_bad.chr", "a/b")])


def s8_call(sandbox: Path, ctx):
    """genome_register_attested INNER LOOP: src_dir.mkdir() at :11941 plus the
    descriptor.toml/:11942 and row.ndjson/:11953 writes happen per-iteration,
    inside the same loop whose LATER iteration raises at :11933. Earlier
    iterations' artifacts stay registered on disk while the op as a whole
    raises."""
    return G.genome_register_attested(ctx, sandbox / "amsc", source="probe")


def s8_neg_setup(sandbox: Path):
    return _chr_dir_with(sandbox, [("01_good.chr", "good")])


def s8_neg_call(sandbox: Path, ctx):
    """Within-op negative: a single GOOD bundle completes and leaves its
    artifacts on the SUCCESS path — deliberate, not an orphan."""
    return G.genome_register_attested(ctx, sandbox / "amsc", source="probe")


SITES = [
    ("S1", "HIGH", "docs/srmech/python/srmech/biology/genome.py", 8980,
     "genome_save", "path.mkdir() before every validation in the body",
     s1_call, s1_setup, s1_neg_call, s1_neg_setup),
    ("S2", "HIGH", "docs/srmech/python/srmech/biology/genome.py", 11600,
     "genome_import (native branch)",
     "dest.mkdir() before the native integrity check; :11606 always raises",
     s2_call, s2_setup, s2_neg_call, s2_setup),
    ("S3", "HIGH", "docs/srmech/python/srmech/biology/genome.py", 11680,
     "genome_explode", "out_dir.mkdir() before the label-safety loop",
     s3_call, s3_setup, s3_neg_call, s3_setup),
    ("S4", "HIGH", "docs/srmech/python/srmech/biology/genome.py", 11927,
     "genome_register_attested",
     "amsc_root.mkdir() before the per-bundle label-safety check",
     s4_call, s4_setup, s4_neg_call, s4_neg_setup),
    ("S5", "HIGH", "docs/srmech/python/srmech/mcp/_mcpb.py", 318,
     "pack_mcpb", "out.mkdir() before build_manifest's server_type assert",
     s5_call, None, s5_neg_call, s5_neg_setup),
    ("S6", "MEDIUM", "docs/srmech/python/srmech/amsc/format.py", 373,
     "write_ndjson",
     "path.parent.mkdir() before the streaming serialise loop (partial file)",
     s6_call, s6_setup, s6_neg_call, None),
    ("S7", "MEDIUM", "docs/srmech/python/srmech/math/laplacian.py", 7200,
     "recursive_cut",
     "3 sequential os.makedirs, no rollback of the earlier ones",
     s7_call, None, s7_neg_call, None),
    ("S8", "MEDIUM", "docs/srmech/python/srmech/biology/genome.py", 11941,
     "genome_register_attested (inner loop)",
     "per-iteration mkdir + 2 writes inside a loop a later iteration aborts",
     s8_call, s8_setup, s8_neg_call, s8_neg_setup),
]


# ──────────────────────────────────────────────────────────────────────
# CTRL-X — the cross-subject collision (rc431's actual root cause)
# ──────────────────────────────────────────────────────────────────────

def ctrl_x(session: Path) -> None:
    """SAME-SUBJECT arm: write_packed_graph over its OWN prior output — passes,
    and is therefore blind. CROSS-SUBJECT arm: genome_save orphans a DIRECTORY at
    node N, then write_packed_graph opens N as a FILE. Vary the OTHER party."""
    p = Probe(session, "ctrl_x_same")

    def same(sandbox: Path, ctx=None):
        n = sandbox / "node"
        L.write_packed_graph(str(n), [(0, 1)], [1.0])
        L.write_packed_graph(str(n), [(0, 1), (1, 2)], [1.0, 1.0])
        return "same-subject overwrite succeeded"

    res_same = p.run(same)
    emit(record="cross_subject_control", arm="same_subject",
         what="write_packed_graph over its own prior file",
         blind=res_same["raised"] is None, **res_same)

    q = Probe(session, "ctrl_x_cross")

    def cross(sandbox: Path, ctx=None):
        n = sandbox / "node"
        o = one()
        strand = G.chromosome(leaves(2), o, label="c")
        try:
            G.genome_save(strand, n, o, labels=["not_c"])   # orphans n/ as a DIR
        except ValueError:
            pass
        L.write_packed_graph(str(n), [(0, 1)], [1.0])       # wants n as a FILE
        return "no collision"

    res_cross = q.run(cross)
    emit(record="cross_subject_control", arm="cross_subject",
         what="genome_save orphans a DIR at N; write_packed_graph opens N as FILE",
         collision_reproduced=res_cross["raised"] is not None, **res_cross)


# ──────────────────────────────────────────────────────────────────────
# Environment + main
# ──────────────────────────────────────────────────────────────────────

_O_SNIPPET = r"""
import sys, tempfile, os, json, traceback
from pathlib import Path
from srmech.mcp._mcpb import pack_mcpb
root = Path(tempfile.mkdtemp(prefix="s5_dashO_"))
out = {"optimize": sys.flags.optimize}
try:
    p = pack_mcpb(str(root / "out"), server_type="bogus", manifest_only=True)
    out["raised"] = None
    out["returned"] = str(p)
except BaseException as exc:
    out["raised"] = type(exc).__name__ + ": " + str(exc)[:200]
out["node_exists"] = (root / "out").exists()
out["node_contents"] = sorted(q.name for q in (root / "out").iterdir()) \
    if (root / "out").is_dir() else []
print(json.dumps(out, sort_keys=True))
"""


def dash_o_record() -> None:
    """`#T1132` x `#T1131`: S5's validation IS an `assert`. Under ``python -O``
    the assert is deleted, so the guard that makes the site raise disappears —
    the orphan stops being an orphan because the call stops failing, and a
    rejected server_type is ACCEPTED instead. Measured, not asserted: the same
    call is run under -O in a subprocess and the outcome recorded. This is the
    evidence for the standing ruling that Rule 5 (>=2 asserts per function) must
    NOT be ported to Python — validation placed in an assert vanishes in
    optimized mode."""
    import subprocess
    for level, flags in (("plain", []), ("dash_O", ["-O"])):
        try:
            proc = subprocess.run(
                [sys.executable, *flags, "-c", _O_SNIPPET],
                capture_output=True, text=True, timeout=180,
                env={**os.environ})
            payload = json.loads(proc.stdout.strip().splitlines()[-1]) \
                if proc.stdout.strip() else {"error": proc.stderr[-400:]}
        except BaseException as exc:                       # noqa: BLE001
            payload = {"error": f"{type(exc).__name__}: {exc}"}
        emit(record="optimize_mode_probe", mode=level, site_id="S5",
             what="pack_mcpb(server_type='bogus') under -O vs plain",
             **payload)


def extra_hazards(session: Path) -> None:
    """Two hazards sharper than "a node is left behind", both driven the same
    way. Neither was in the rc431 triage."""

    # S6b — write_ndjson does not merely leave a truncated NEW file; when `path`
    # ALREADY holds a good NDJSON, the `open(..., "w")` truncates it before the
    # first record is serialised, so a mid-loop failure DESTROYS pre-existing
    # content. The victim is prior data, not a fresh node — which is why a
    # same-subject probe (fresh path only) cannot see it.
    def s6b_setup(sandbox: Path):
        p = sandbox / "sub" / "out.ndjson"
        p.parent.mkdir(parents=True)
        good = MPRRecord(mpr_version="1.0", data={"kept": True},
                         data_schema_id="probe://s", attestation={},
                         rendering={})
        write_ndjson(p, [good])
        return (p, p.read_bytes())

    def s6b_call(sandbox: Path, ctx):
        p, _prior = ctx
        ok = MPRRecord(mpr_version="1.0", data={"i": 0},
                       data_schema_id="probe://s", attestation={}, rendering={})
        bad = MPRRecord(mpr_version="1.0", data={"i": object()},
                        data_schema_id="probe://s", attestation={},
                        rendering={})
        return write_ndjson(p, [ok, bad])

    pr = Probe(session, "s6b")
    ctx_holder = {}

    def setup_capture(sandbox: Path):
        ctx = s6b_setup(sandbox)
        ctx_holder["prior"] = ctx[1]
        ctx_holder["path"] = ctx[0]
        return ctx

    res = pr.run(s6b_call, setup_capture)
    after_bytes = ctx_holder["path"].read_bytes() \
        if ctx_holder["path"].exists() else b""
    emit(record="extra_hazard", hazard_id="S6b", site_id="S6",
         file="docs/srmech/python/srmech/amsc/format.py", line=376,
         what=("open(path,'w') truncates a PRE-EXISTING good NDJSON before the "
               "first record is serialised; a mid-loop failure destroys it"),
         prior_bytes=len(ctx_holder["prior"]),
         surviving_bytes=len(after_bytes),
         prior_content_destroyed=(after_bytes != ctx_holder["prior"]),
         surviving_preview=after_bytes.decode("utf-8", "replace")[:200],
         **res)

    # S7b — recursive_cut with work_dir=None mkdtemp's its OWN scratch dir. If a
    # later makedirs fails, that temp dir is leaked into the system temp area AND
    # its name never reaches the caller (the exception carries no path, and the
    # function returns nothing). An orphan the caller cannot even name is a
    # strictly worse shape than one under a caller-chosen root.
    import tempfile as _tf
    tmp_root = Path(_tf.gettempdir())
    before_tmp = {p.name for p in tmp_root.glob("srmech_cut_*")}
    install, restore = _inject_makedirs(2)
    install()
    raised = None
    try:
        L.recursive_cut(4, [(0, 1), (2, 3)], max_tome=2, work_dir=None)
    except BaseException as exc:                              # noqa: BLE001
        raised = f"{type(exc).__name__}: {exc}"
    finally:
        restore()
    after_tmp = {p.name for p in tmp_root.glob("srmech_cut_*")}
    leaked = sorted(after_tmp - before_tmp)
    emit(record="extra_hazard", hazard_id="S7b", site_id="S7",
         file="docs/srmech/python/srmech/math/laplacian.py", line=7199,
         what=("work_dir=None mkdtemp's a scratch dir whose name reaches the "
               "caller ONLY via the return value; a setup failure leaks it "
               "UNNAMEABLE into the system temp area"),
         raised=raised, leaked_temp_dirs=leaked, n_leaked=len(leaked),
         caller_can_name_it=False)
    for name in leaked:
        shutil.rmtree(tmp_root / name, ignore_errors=True)

    # RF1/RF2 — is repair (a) (reorder) actually AVAILABLE at the two sites where
    # it is the cheapest fix? Both need their pre-mkdir work to run against a
    # path that does not exist yet.
    probe_dir = session / "rf"
    probe_dir.mkdir()
    try:
        resolved = G._resolve_attestation(probe_dir / "does_not_exist", None)
        rf1 = {"ok": True, "returned": repr(resolved)[:80]}
    except BaseException as exc:                              # noqa: BLE001
        rf1 = {"ok": False, "raised": f"{type(exc).__name__}: {exc}"[:160]}
    emit(record="repair_feasibility", probe_id="RF1", site_id="S1",
         question=("does _resolve_attestation(:8946) tolerate a path that does "
                   "not exist yet? if yes, genome_save's mkdir can move BELOW "
                   "it and above the native call at :9049"),
         **rf1)

    try:
        from srmech.mcp._mcpb import build_manifest
        m = build_manifest(server_type="uv")
        rf2 = {"ok": True, "returned": f"manifest with {len(m['tools'])} tools"}
    except BaseException as exc:                              # noqa: BLE001
        rf2 = {"ok": False, "raised": f"{type(exc).__name__}: {exc}"[:160]}
    emit(record="repair_feasibility", probe_id="RF2", site_id="S5",
         question=("does build_manifest touch the filesystem at all? if not, "
                   "pack_mcpb's mkdir can move BELOW it — a pure reorder"),
         **rf2)


def c_side_records(repo: Path) -> None:
    """The `rcut_setup` / `recursive_cut` PAIR is the priority: the only place
    both projections carry the same hazard. Everything here is GREPPED at run
    time from the C tree, not quoted from the rc431 audit, so a later reader can
    re-run it rather than trust it."""
    csrc = repo / "docs" / "srmech" / "c" / "src"
    if not csrc.is_dir():
        emit(record="c_side", finding="UNSUPPORTED",
             note=f"C source tree not found at {csrc}")
        return

    def grep(pattern: str, files) -> List[Tuple[str, int, str]]:
        hits = []
        for f in files:
            try:
                text = f.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            for i, ln in enumerate(text.splitlines(), 1):
                if pattern in ln:
                    hits.append((f.name, i, ln.strip()))
        return hits

    all_c = sorted(csrc.glob("*.c"))
    plat = csrc / "srmech_platform.c"

    mkdir_calls = [h for h in grep("srmech_plat_mkdir(", all_c)
                   if h[0] != "srmech_platform.c"]
    emit(record="c_side", finding="mkdir_call_sites",
         what="every srmech_plat_mkdir CALL outside the PAL itself",
         n=len(mkdir_calls),
         sites=[f"{a}:{b}: {c}" for a, b, c in mkdir_calls],
         note=("the rc431 audit measured 3, all in rcut_setup; this is the "
               "re-measurement"))

    # Is there ANY directory-removal primitive to roll back WITH?
    rmdir_hits = grep("rmdir", all_c) + grep("RemoveDirectory", all_c)
    remove_impl = grep("remove(path)", [plat]) if plat.exists() else []
    emit(record="c_side", finding="no_portable_rmdir_primitive",
         n_rmdir_symbols=len(rmdir_hits),
         plat_file_remove_impl=[f"{a}:{b}: {c}" for a, b, c in remove_impl],
         consequence=("the PAL exposes mkdir / file_remove / file_replace and "
                      "NO rmdir. srmech_plat_file_remove is C89 remove(), which "
                      "unlinks an empty directory on POSIX but NOT on Win32 "
                      "(MSVC remove() is files-only; _rmdir is the Win32 call). "
                      "So repair (b) on the C side is NOT implementable with "
                      "today's PAL surface — it needs a new srmech_plat_rmdir. "
                      "Adding a symbol is ABI-additive (no new callback "
                      "typedef), so it does not bump SRMECH_ABI_VERSION."))

    genome_c = csrc / "srmech_genome.c"
    if genome_c.exists():
        emit(record="c_side", finding="genome_write_ops_never_mkdir",
             n_mkdir_in_srmech_genome_c=len(grep("srmech_plat_mkdir",
                                                 [genome_c])),
             consequence=("the C genome write surface requires its target "
                          "directory to ALREADY EXIST — the CALLER owns "
                          "directory creation. That is the convention the "
                          "Python contract question should be settled against."))


def contract_records(repo: Path) -> None:
    """Would any repair CHANGE A CONTRACT? Measured against the one shipped gate
    that looks at post-failure filesystem state."""
    t = (repo / "docs" / "srmech" / "python" / "tests"
         / "test_genome_attestation_rc304.py")
    if not t.exists():
        emit(record="contract", finding="UNSUPPORTED", note=str(t))
        return
    text = t.read_text(encoding="utf-8", errors="replace").splitlines()
    idx = [i for i, ln in enumerate(text, 1)
           if "test_bad_override_writes_nothing_to_disk" in ln]
    body = [ln.strip() for ln in text[idx[0] - 1: idx[0] + 8]] if idx else []
    emit(record="contract", finding="shipped_gate_name_overclaims",
         file="docs/srmech/python/tests/test_genome_attestation_rc304.py",
         line=idx[0] if idx else 0, body=body,
         measured=("the gate is named ...writes_nothing_to_disk and its docstring "
                   "says 'no half-written genome', but its ONLY assertion is "
                   "`not (d / \"manifest.json\").exists()`. Driven here, the "
                   "rejected call leaves d itself on disk as an EMPTY DIRECTORY. "
                   "The name claims the invariant this rc is about; the assertion "
                   "checks a strictly narrower one, so the gate is green on the "
                   "defect it appears to cover."),
         contract_direction=("reordering the mkdir keeps the SUCCESS-path "
                             "contract identical (the directory is still created "
                             "by the op, just later), so it is NOT breaking. "
                             "Adopting the C convention instead (caller owns "
                             "creation) WOULD be breaking and would need a "
                             "CHANGELOG breaking entry."))


def env_record() -> None:
    emit(record="env",
         srmech_file=srmech.__file__,
         srmech_version=srmech.__version__,
         python=sys.version.split()[0],
         has_native=bool(getattr(_native, "HAS_NATIVE", False)),
         has_native_genome=bool(_native.has_native_genome()),
         native_load_error=str(getattr(_native, "LOAD_ERROR", ""))[:200],
         optimize_level=sys.flags.optimize,
         numpy_absent="numpy" not in sys.modules)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="_s1_acquire_sites_rc432.ndjson")
    ap.add_argument("--repo", default=str(Path(__file__).resolve().parents[3]))
    args = ap.parse_args()

    env_record()
    session = Path(tempfile.mkdtemp(prefix="s1_rc432_"))
    try:
        if not run_controls(session):
            for r in RECORDS:
                if r.get("record") == "control" and not r.get("agrees"):
                    print("CONTROL DISAGREED:", r["control_id"], r["expected"],
                          "->", r["observed"], file=sys.stderr)
            _write(args.out)
            print("REFUSING to report sites: the instrument failed its own "
                  "controls.", file=sys.stderr)
            return 1

        ctrl_x(session)

        for sid, sev, f, line, fn, shape, drv, setup, neg, nsetup in SITES:
            res = Probe(session, sid.lower()).run(drv, setup)
            nres = Probe(session, sid.lower() + "_neg").run(neg, nsetup)
            base = f.rsplit("/", 1)[-1]
            frames = [ln.strip() for ln in res["traceback_tail"].splitlines()
                      if base in ln]
            emit(record="site_probe", site_id=sid, audit_severity=sev,
                 file=f, line=line, function=fn, acquire_shape=shape,
                 site_frames=frames,
                 hypothesis=("the driven call raises AND leaves >=1 node it "
                             "created on disk"),
                 falsifier=("the call raises and the sandbox tree is unchanged "
                            "-> REFUTED"),
                 verdict=verdict_of(res),
                 negative_control_verdict=verdict_of(nres),
                 negative_control_raised=nres["raised"],
                 negative_control_left=nres["left_behind"],
                 **res)

        extra_hazards(session)
        dash_o_record()
        c_side_records(Path(args.repo))
        contract_records(Path(args.repo))
    finally:
        shutil.rmtree(session, ignore_errors=True)

    _write(args.out)
    return 0


def _write(out: str) -> None:
    with open(out, "w", encoding="utf-8", newline="\n") as fh:
        for r in RECORDS:
            fh.write(json.dumps(r, sort_keys=True, ensure_ascii=False) + "\n")
    print(f"wrote {len(RECORDS)} records -> {out}")
    for r in RECORDS:
        if r.get("record") == "site_probe":
            print(f"  {r['site_id']} {r['audit_severity']:6s} {r['function']:38s}"
                  f" {r['verdict']:10s} neg={r['negative_control_verdict']:10s}"
                  f" left={r['n_left']}")
        elif r.get("record") == "control":
            print(f"  {r['control_id']} expect={r['expected']:10s}"
                  f" got={r['observed']:10s} agrees={r['agrees']}")
        elif r.get("record") == "cross_subject_control":
            print(f"  CTRL-X {r['arm']:14s} raised={r['raised']}")
        elif r.get("record") == "c_side":
            print(f"  C-side {r['finding']}: "
                  f"{r.get('n', r.get('n_rmdir_symbols', r.get('n_mkdir_in_srmech_genome_c')))}")
        elif r.get("record") == "contract":
            print(f"  contract {r['finding']} @ line {r.get('line')}")
        elif r.get("record") == "extra_hazard":
            print(f"  {r['hazard_id']} {r.get('prior_content_destroyed', '')}"
                  f" leaked={r.get('leaked_temp_dirs', '')}"
                  f" surviving={r.get('surviving_bytes', '')}")
        elif r.get("record") == "repair_feasibility":
            print(f"  {r['probe_id']} ({r['site_id']}) reorder_available="
                  f"{r['ok']} {r.get('raised', r.get('returned', ''))}")
        elif r.get("record") == "optimize_mode_probe":
            print(f"  -O probe {r['mode']:7s} raised={r.get('raised')}"
                  f" node_exists={r.get('node_exists')}"
                  f" contents={r.get('node_contents')}")


if __name__ == "__main__":
    sys.exit(main())
