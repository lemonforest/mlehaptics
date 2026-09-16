"""rc473 stage B — the BEFORE column, re-measured in the repair session (`#T1188`).

WHY THIS EXISTS. Stage A recorded the rc472 behaviour of every row rc473
repairs. Stage B quotes those figures in a CHANGELOG entry, a commit message
and several header comments — and the standing rule is that a figure is
re-printed in the session that quotes it, because "every wrong count in this
rc's history was a correct figure carried across a condition change". By the
time the repair is written the tree no longer HAS the old behaviour, so the
only honest way to re-print it is to rebuild the old library.

That is what this does: it exports `c/src` and `c/include` at a given git ref
with ``git archive`` (the worktree is never touched), compiles them into a
standalone shared object under a temporary directory, loads it with ctypes,
and reads the same rows the post-repair proof reads. The library's own
``srmech_abi_version()`` is printed first, so the artifact under test is
identified rather than assumed.

Default ref is ``b398b8c46`` — v0.9.0rc472, the tree rc473 branched from.

⚠️ WSL2 + A WINDOWS-CREATED WORKTREE. ``git archive`` needs a resolvable
gitdir, and a worktree created by Windows git writes an ABSOLUTE WINDOWS path
into its ``.git`` file (``D:/GitHub/...``), which git under WSL2 cannot follow —
measured: ``fatal: not a git repository: /mnt/d/.../D:/GitHub/mlehaptics/.git/
worktrees/...``. So the export half is skipped when a pre-exported tree is
supplied as the second argument, and the run records which route it took. The
export itself is then done by whichever git CAN read the repository.

Usage::

    uv run --python 3.12 --no-project --offline \\
        python docs/srmech/notes/_rc473_before_table.py [git-ref] [exported-c-root]

where ``exported-c-root`` is a directory containing ``include/`` and ``src/``
already extracted from that ref (``git archive <ref> docs/srmech/c/src
docs/srmech/c/include | tar -x -C <dir>`` from a checkout git can read).

Output is NDJSON on stdout.
"""

from __future__ import annotations

import ctypes
import json
import subprocess
import sys
import tarfile
import tempfile
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_SRMECH = _HERE.parent
_REPO = _SRMECH.parent.parent

DEFAULT_REF = "b398b8c46"

NAN = float("nan")
INF = float("inf")
_D = ctypes.c_double
_DP = ctypes.POINTER(ctypes.c_double)
_U32 = ctypes.c_uint32
_SIZE = ctypes.c_size_t
_I64 = ctypes.c_int64

#: The live pedantic flags, minus -Werror: this build must SUCCEED on the old
#: sources, and the old sources are exactly the ones with the 24 discards. The
#: attribute is not present at this ref, so there is nothing to error on.
_FLAGS = ["-O3", "-DNDEBUG", "-std=c11", "-fPIC",
          "-Wall", "-Wextra", "-Wpedantic", "-O2", "-shared"]


def _export(ref: str, dest: Path) -> Path:
    """git archive the C tree at `ref` into `dest`; return the c/ root."""
    tar_path = dest / "src.tar"
    with tar_path.open("wb") as fh:
        subprocess.run(
            ["git", "archive", ref, "docs/srmech/c/src", "docs/srmech/c/include"],
            cwd=str(_REPO), stdout=fh, check=True,
        )
    with tarfile.open(tar_path) as tf:
        tf.extractall(dest)          # noqa: S202 - our own archive, our own ref
    return dest / "docs" / "srmech" / "c"


def _build(croot: Path, dest: Path) -> Path:
    so = dest / "libsrmech_before.so"
    sources = sorted(str(p) for p in (croot / "src").glob("*.c"))
    proc = subprocess.run(
        ["gcc", *_FLAGS, f"-I{croot / 'include'}", f"-I{croot / 'src'}",
         *sources, "-o", str(so)],
        capture_output=True, text=True, check=False,
    )
    print(json.dumps({
        "kind": "build",
        "returncode": proc.returncode,
        "unused_result_diagnostics": proc.stderr.count("[-Wunused-result]"),
        "other_diagnostic_lines": sum(
            1 for ln in proc.stderr.splitlines()
            if ": warning:" in ln and "[-Wunused-result]" not in ln),
    }, sort_keys=True))
    if proc.returncode != 0:
        print(proc.stderr[:2000], file=sys.stderr)
        raise SystemExit("build of the BEFORE library failed")
    return so


def _rows(lib: ctypes.CDLL) -> None:
    def bind(name, argtypes):
        fn = getattr(lib, name)
        fn.argtypes = argtypes
        fn.restype = ctypes.c_int
        return fn

    def row(label, st, val):
        print(json.dumps({"call": label, "status": st, "value": repr(val)},
                         sort_keys=True))

    print(json.dumps({"kind": "artifact",
                      "abi_version": lib.srmech_abi_version()}, sort_keys=True))

    fn = bind("srmech_equation_of_centre", [_D, _D, _U32, _DP])
    o = ctypes.c_double(0.0)
    row("equation_of_centre(2**53+1, 0.0549, 4)",
        fn(_D(2.0 ** 53 + 1), _D(0.0549), _U32(4), ctypes.byref(o)), o.value)

    fn = bind("srmech_pin_slot", [_D, _D, _D, _DP])
    o = ctypes.c_double(0.0)
    row("pin_slot(2**55, 0.5, 1.0)",
        fn(_D(2.0 ** 55), _D(0.5), _D(1.0), ctypes.byref(o)), o.value)

    fn = bind("srmech_kepler_solve", [_D, _D, _D, _U32, _DP])
    o = ctypes.c_double(0.0)
    row("kepler_solve(2**55, 0.3, 1e-12, 20)",
        fn(_D(2.0 ** 55), _D(0.3), _D(1e-12), _U32(20), ctypes.byref(o)), o.value)

    for name, x in (("srmech_sin", NAN), ("srmech_cos", NAN),
                    ("srmech_atan", NAN), ("srmech_exp", NAN),
                    ("srmech_log", NAN), ("srmech_rational_sqrt", NAN),
                    ("srmech_sin", 2.0 ** 55), ("srmech_cos", 2.0 ** 55),
                    ("srmech_rational_sqrt", -4.0),
                    ("srmech_atan", INF), ("srmech_atan", -INF)):
        f = bind(name, [_D, _DP])
        out = ctypes.c_double(-12345.0)
        row(f"{name}({x!r})", f(_D(x), ctypes.byref(out)), out.value)

    a2 = bind("srmech_atan2", [_D, _D, _DP])
    for y, x in ((NAN, 1.0), (1.0, NAN), (NAN, 0.0),
                 (INF, INF), (-INF, -INF), (INF, -INF), (-INF, INF)):
        out = ctypes.c_double(-12345.0)
        row(f"atan2({y!r}, {x!r})", a2(_D(y), _D(x), ctypes.byref(out)), out.value)

    ew = bind("srmech_elementwise_transcendental", [_U32, _DP, ctypes.c_int, _DP])
    for op_id, op_name, arg in ((1, "COS", 2.0 ** 55), (2, "SIN", NAN),
                                (0, "EXP", NAN), (3, "LOG", NAN)):
        arr = (ctypes.c_double * 1)(arg)
        out = (ctypes.c_double * 1)(-12345.0)
        st = ew(_U32(1), ctypes.cast(arr, _DP), ctypes.c_int(op_id),
                ctypes.cast(out, _DP))
        row(f"elementwise([{arg!r}], {op_name})", st, out[0])

    plain = bind("srmech_cascade_kuramoto_step_f64",
                 [_DP, _DP, _SIZE, _D, _D, _DP])
    for arg in (2.0 ** 55, INF, NAN):
        theta = (ctypes.c_double * 2)(0.0, arg)
        omega = (ctypes.c_double * 2)(0.0, 0.0)
        out = (ctypes.c_double * 2)(-12345.0, -12345.0)
        st = plain(ctypes.cast(theta, _DP), ctypes.cast(omega, _DP), _SIZE(2),
                   _D(1.0), _D(0.1), ctypes.cast(out, _DP))
        row(f"kuramoto_step_f64([0, {arg!r}])", st, [out[0], out[1]])

    wf = bind("srmech_winding_fold", [_D, ctypes.POINTER(_I64), _DP])
    for x in (NAN, 2.0 ** 55, INF):
        w = _I64(-1)
        o = ctypes.c_double(-12345.0)
        row(f"winding_fold({x!r})", wf(_D(x), ctypes.byref(w), ctypes.byref(o)),
            (w.value, o.value))


def main() -> int:
    ref = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_REF
    supplied = Path(sys.argv[2]).resolve() if len(sys.argv) > 2 else None
    print(json.dumps({"kind": "ref", "git_ref": ref,
                      "export_route": "pre-exported" if supplied else "git archive",
                      "exported_root": str(supplied) if supplied else None},
                     sort_keys=True))
    with tempfile.TemporaryDirectory(prefix="rc473_before_") as tmp:
        dest = Path(tmp)
        if supplied is None:
            croot = _export(ref, dest)
        else:
            croot = supplied
            for half in ("include", "src"):
                if not (croot / half).is_dir():
                    raise SystemExit(
                        f"{croot} has no {half}/ — supply the directory that "
                        "holds the exported include/ and src/, not its parent")
        so = _build(croot, dest)
        _rows(ctypes.CDLL(str(so)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
