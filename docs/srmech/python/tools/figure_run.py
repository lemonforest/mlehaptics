r"""THE REUSABLE FIGURE-RUN CORE — one run re-prints every figure a prose
entry quotes, and diffs the prose against it. (rc471, `#T1188`)

WHY THIS FILE EXISTS, AND WHY IT IS SEPARATE FROM ITS FIRST CALLER
------------------------------------------------------------------
``tools/rc470_figures.py`` established the rule and shipped the apparatus in one
file. The rule is not rc470's:

    Every figure in shipped prose is re-printed by ONE run executed after the
    LAST edit to the tree, and the prose is diffed against that run's output. A
    figure the final run cannot produce is DELETED, not adjusted. A figure
    carried from an earlier draft, an earlier commit's run, or another lane's
    report is INVENTED until re-printed.

Every later rc owes that run, so the apparatus is lifted here and the caller
keeps only its own figures. **The lift is the whole point: rc470's harness died
the moment rc470 merged**, because it read its comparison baseline from the
moving ref ``main``. A core that every rc depends on cannot carry a moving
part, so ``baseline_commit`` is a REQUIRED, IMMUTABLE parameter here and this
module refuses a ref that can move (see :func:`assert_immutable_baseline`).

WHAT THIS CORE FIXES THAT ITS FIRST CALLER GOT WRONG — each one measured
------------------------------------------------------------------------
* **A moving baseline.** ``_git("show", "main:…")`` — see above. REQUIRED SHA.
* **The ``== HEAD`` column could not return otherwise.** ``git hash-object``
  applies no clean filter, so on a CRLF checkout every instrument hashed
  differently from its LF ``HEAD`` blob and the column printed
  ``!= HEAD (uncommitted)`` for ALL NINE on a tree whose content is byte-
  identical to ``HEAD``. *An instrument that cannot return otherwise is not a
  measurement.* :func:`head_state` compares EOL-NORMALISED bytes, which is the
  same question ``git diff --ignore-cr-at-eol`` answers, and answers it
  identically under Windows git (``core.autocrlf=true``) and WSL git (unset) —
  which otherwise disagree about this tree by **1101 of 1111 tracked files**.
  The deliberate, disclosed insensitivity: a change that is ONLY line endings
  reads ``== HEAD``. That is the correct call here, because the repo's blobs
  are LF and every Windows checkout is CRLF by construction.
* **The prose file was re-read per figure.** 29 figures × a 4.27 MB CHANGELOG.
  :class:`FigureRun` caches prose by path (:func:`FigureRun.prose`).
* **The gate totals ran one pytest process per SET**, re-running shared files.
  :func:`FigureRun.union_pytest` runs the union ONCE with ``--junit-xml`` and
  recovers each set's tally by grouping test cases back onto their source file.
  ⚠️ The XML has **no ``file`` attribute** — a first parse that assumed one
  returned zeros. Grouping is on ``classname``; see :func:`_file_of_classname`.
* **The negation sweep read every ``.py`` twice**, once per regex.
  :func:`FigureRun.sweep` walks the population ONCE and applies every pattern.
* **The prose diff covered two files** while nine were hash-witnessed.
  ``where=`` takes a str or a tuple of paths, so a figure can be diffed against
  every file that quotes it.

THE DEPENDENCY-CLOSURE CHECK
----------------------------
A line-range extraction is checked for LINE COVERAGE, not for whether the names
those lines use came with them. The split that produced this file was measured
"0 unassigned non-blank lines" and still had a function in the CORE bucket using
``_native``, which was imported in the SPECIFIC bucket — a ``NameError`` on the
first run. :func:`self_check` walks every code object in a module, collects
every ``LOAD_GLOBAL``, and refuses any name that is neither a module-level
binding nor a builtin. It is called at the top of :meth:`FigureRun.header`, so
no caller can forget it, and it has its own can-fail in
``tests/test_figure_run_rc471.py``.

numpy-free. No ``abs()``. Every digest routes through
``srmech.amsc.format.sha256_bytes``.
"""

from __future__ import annotations

import builtins
import dis
import os
import re
import subprocess
import sys
import time
import types
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, Iterable, Mapping, Sequence, Tuple

#: ``docs/srmech/python``. Resolved from THIS file so a caller in ``tools/``
#: never has to compute it.
PY_ROOT = Path(__file__).resolve().parents[1]

#: The repository root — ``docs/srmech/python`` → ``mlehaptics``.
REPO = PY_ROOT.parents[2]

#: Refs a baseline may NOT be. Each one moves, and a comparison against a ref
#: that moves is a comparison whose answer changes when nothing in this rc did.
#: ``main`` is the one that actually bit: ``tools/rc470_figures.py`` read
#: ``main:…/demotion_probe.py`` for a name rc470 itself removed, so the harness
#: died the moment rc470 merged into ``main``.
MOVING_REFS = ("main", "master", "HEAD", "ORIG_HEAD", "FETCH_HEAD")

_SHA_RE = re.compile(r"\A[0-9a-f]{7,40}\Z")


def assert_immutable_baseline(ref: str) -> str:
    """Refuse a baseline ref that can move; return it unchanged.

    A tag is refused too: a tag is a pointer, and the precedent this core
    follows (``tools/rc470_figures.py``'s ``fe3454677`` read of the
    ``def_blob`` drain) pins a raw commit SHA.
    """
    if not isinstance(ref, str) or not _SHA_RE.match(ref):
        raise ValueError(
            f"baseline_commit must be a hex commit SHA, got {ref!r}. "
            f"A baseline that can move is the defect this parameter exists to "
            f"prevent: rc470's harness read 'main:tools/demotion_probe.py' for "
            f"a name rc470 removed, and died the moment rc470 merged. "
            f"Refused refs: {', '.join(MOVING_REFS)}, and any tag.")
    return ref


def sha(data: bytes) -> str:
    """sha256, routed through the package's own hasher (never ``hashlib``)."""
    from srmech.amsc.format import sha256_bytes
    return sha256_bytes(data)


def git(*args: str) -> str:
    """``git -C <repo> …``, stdout only, decoded as UTF-8.

    ⚠️ The encoding is NOT a detail, and leaving it to the locale cost this
    core a silent ``None``. With ``text=True`` and no ``encoding=``, CPython
    decodes the child's stdout with the LOCALE codec — ``cp1252`` on Windows —
    so ``git show <sha>:tools/demotion_probe.py``, whose bytes are UTF-8, blew
    up inside ``subprocess``'s reader THREAD. A thread that dies does not
    propagate: ``.stdout`` came back ``None`` and surfaced 200 lines later as
    ``AttributeError: 'NoneType' object has no attribute 'split'``, with
    nothing naming git or the file. Every ASCII call (``rev-parse``,
    ``status --porcelain``, ``log -S``) worked, which is why a WSL build
    session and a Windows repair session disagreed about whether this core
    runs at all.

    ``errors="replace"`` rather than strict: git output can legitimately carry
    non-UTF-8 bytes (a foreign-encoded path), and a mangled character in a
    line this core only ever SEARCHES is a better answer than an exception —
    but a silent ``None`` is not, and that is what changed.
    """
    proc = subprocess.run(["git", "-C", str(REPO), *args],
                          capture_output=True)
    return proc.stdout.decode("utf-8", "replace")


def normalise_eol(data: bytes) -> bytes:
    """CRLF → LF. The one normalisation :func:`head_state` is allowed."""
    return data.replace(b"\r\n", b"\n")


def head_state_of(blob: bytes, live: bytes) -> str:
    """THE DECIDER, pure, so it can be shown to return otherwise.

    ``== HEAD`` iff the two byte strings agree once CRLF is normalised to LF.
    The I/O wrapper is :func:`head_state`; everything that decides the answer
    is here, which is what lets a test flip one byte and watch the verdict
    change without writing the shipped tree.
    """
    same = normalise_eol(blob) == normalise_eol(live)
    return "== HEAD" if same else "!= HEAD (content differs)"


def widen_stdout() -> str:
    """Make ``stdout`` able to carry this core's own banner. Returns the codec.

    Not cosmetic. Every banner line below prints ``⚠``/``…``/``─``, and on a
    console whose default codec is ``cp1252`` — the Windows default, and the
    one this rc's repair session ran on — the FIRST such ``print`` raises
    ``UnicodeEncodeError`` inside :meth:`FigureRun.header`, before a single
    figure is measured. An instrument that cannot print its own output cannot
    return a measurement, so the fix belongs here rather than in an ambient
    ``PYTHONIOENCODING`` the caller has to remember: a harness whose answer
    depends on an env var the reader does not set is a harness that reports
    nothing on half its hosts. ``errors`` is left strict so a genuinely
    unencodable figure still raises rather than silently rendering as ``?``.
    """
    stream = getattr(sys, "stdout", None)
    reconfigure = getattr(stream, "reconfigure", None)
    if reconfigure is not None and (
            getattr(stream, "encoding", "") or "").lower().replace("-", "") \
            not in ("utf8", "utf8mb4"):
        reconfigure(encoding="utf-8")
    return (getattr(sys.stdout, "encoding", "") or "?")


def git_available() -> bool:
    """Can ``git`` answer for :data:`REPO` at all?

    Not a nicety. ``git show HEAD:<path>`` fails with the SAME non-zero status
    when the path is absent from ``HEAD`` and when git cannot read the
    repository at all, so without this the witness reports every instrument as
    a brand-new file and the whole column becomes a silent "nothing to
    compare" — the shape ``head_blob_map()`` already ships one layer down,
    where a git failure stamped an empty blob on **428 of 428 ops** and looked
    like "nothing changed".
    """
    return subprocess.run(["git", "-C", str(REPO), "rev-parse", "HEAD"],
                          capture_output=True).returncode == 0


def head_state(rel: str) -> str:
    """``== HEAD`` / ``!= HEAD (content differs)`` / ``!= HEAD (not in HEAD)``.

    Compares EOL-NORMALISED bytes rather than blob ids. ``git hash-object``
    runs no clean filter, so on a CRLF working tree it disagrees with the LF
    ``HEAD`` blob for every file — which is how rc470's column came to print
    ``!= HEAD`` for all nine instruments on a tree ``git diff
    --ignore-cr-at-eol`` called empty.

    RAISES rather than degrading when git itself cannot answer; see
    :func:`git_available`.
    """
    blob = subprocess.run(
        ["git", "-C", str(REPO), "show", f"HEAD:docs/srmech/python/{rel}"],
        capture_output=True)
    if blob.returncode != 0:
        if not git_available():
            raise RuntimeError(
                f"git cannot read {REPO}, so the == HEAD column has nothing to "
                f"compare against. It is REFUSED rather than reported as "
                f"'not in HEAD', which is the same answer a genuinely new file "
                f"gets and would make every instrument look new. "
                f"git stderr: {blob.stderr.decode('utf-8', 'replace').strip()!r}")
        return "!= HEAD (not in HEAD)"
    return head_state_of(blob.stdout, Path(PY_ROOT, rel).read_bytes())


def self_check(module: types.ModuleType) -> None:
    """DEPENDENCY CLOSURE — every global a module's code loads must resolve.

    Walks every code object reachable from the module's constants, collects
    every ``LOAD_GLOBAL`` name, and refuses any that is neither bound at module
    level nor a builtin. This is the check a line-coverage split cannot make:
    the rc470 → rc471 extraction was "0 unassigned non-blank lines" and still
    put a use of ``_native`` in one bucket and its import in the other.
    """
    seen: set = set()
    used: set = set()

    def walk(code) -> None:
        if id(code) in seen:
            return
        seen.add(id(code))
        for ins in dis.get_instructions(code):
            if ins.opname == "LOAD_GLOBAL":
                name = ins.argval
                used.add(name[2:] if name.startswith("NULL + ") else name)
        for const in code.co_consts:
            if isinstance(const, type(walk.__code__)):
                walk(const)

    def owned(value) -> bool:
        # ⚠️ ONLY objects DEFINED HERE. A module-level ``from pathlib import
        # Path`` binds a class whose methods load globals out of *pathlib*'s
        # namespace (``_make_selector``, ``S_ISDIR``, …); walking those reports
        # 13 phantom unresolved names and the check becomes unusable.
        return getattr(value, "__module__", None) == module.__name__

    for value in vars(module).values():
        if not owned(value):
            continue
        code = getattr(value, "__code__", None)
        if code is not None:
            walk(code)
        elif isinstance(value, type):
            for attr in vars(value).values():
                sub = getattr(attr, "__code__", None)
                if sub is not None:
                    walk(sub)

    unresolved = sorted(n for n in used
                        if n not in vars(module) and not hasattr(builtins, n))
    if unresolved:
        raise NameError(
            f"{module.__name__}: {len(unresolved)} global name(s) are loaded by "
            f"its code but bound nowhere in it: {unresolved}. This is the "
            f"cross-bucket extraction defect — the lines came over, the name "
            f"they use did not.")


def _file_of_classname(classname: str) -> str:
    """Map a junit ``classname`` back to the ``.py`` that holds it.

    ⚠️ pytest's junit XML carries **no** ``file`` attribute on ``<testcase>``;
    a first parse that assumed one grouped every case under ``''`` and returned
    zeros for every gate. ``classname`` is the dotted module path, optionally
    with a test class appended (``tests.test_x`` or ``tests.test_x.TestY``), so
    the file is the longest dotted prefix that names a real file.
    """
    parts = classname.split(".")
    for i in range(len(parts), 0, -1):
        cand = Path(*parts[:i]).with_suffix(".py")
        if (PY_ROOT / cand).is_file():
            return cand.as_posix()
    return ""


def sweep_paths(paths: Iterable[Path],
                patterns: Mapping[str, "re.Pattern"]
                ) -> Dict[str, Tuple[int, int, int]]:
    """``{tag: (occurrences, lines, files)}`` over ``paths``, ONE read each.

    Pure over the path list so the fusion can be shown EQUIVALENT to the
    per-regex walk it replaces (``tests/test_figure_run_rc471.py``) without
    re-deriving the population.
    """
    out = {tag: [0, 0, 0] for tag in patterns}
    hit_files = {tag: set() for tag in patterns}
    for path in paths:
        lines = Path(path).read_text(encoding="utf-8",
                                     errors="replace").split("\n")
        for tag, rx in patterns.items():
            got = [len(rx.findall(s)) for s in lines if rx.search(s)]
            if got:
                hit_files[tag].add(str(path))
                out[tag][1] += len(got)
                out[tag][0] += sum(got)
    for tag in patterns:
        out[tag][2] = len(hit_files[tag])
    return {tag: tuple(v) for tag, v in out.items()}


#: The outcome keys :func:`parse_junit` reports per file. ``collected`` is
#: ``passed + skipped``, and it is the one a gate figure should be quoted
#: against: see :meth:`FigureRun.union_pytest`.
OUTCOME_KEYS = ("passed", "skipped", "failed", "error", "collected")


def parse_junit(xml_path: Path) -> Dict[str, Dict[str, int]]:
    """``{relative .py path: {passed, skipped, failed, error, collected}}``.

    ⚠️ ``passed`` alone is NOT a property of the tree. A row that skips because
    the native library is absent passes on a host that has one, so the same
    unchanged gate reports two different "N passed" figures on two hosts —
    MEASURED at 166 against 148 for one of the sets below. ``collected`` =
    ``passed + skipped`` is the figure that survives the cell, which is why it
    is computed here rather than left to each caller to remember.
    """
    root = ET.parse(str(xml_path)).getroot()
    tally: Dict[str, Dict[str, int]] = {}
    for case in root.iter("testcase"):
        rel = _file_of_classname(case.get("classname") or "")
        row = tally.setdefault(rel, {k: 0 for k in OUTCOME_KEYS})
        if case.find("error") is not None:
            row["error"] += 1
        elif case.find("failure") is not None:
            row["failed"] += 1
        elif case.find("skipped") is not None:
            row["skipped"] += 1
            row["collected"] += 1
        else:
            row["passed"] += 1
            row["collected"] += 1
    return tally


class FigureRun:
    """One figure run: measure, print, diff the prose, witness the tree.

    ``instruments`` are the files whose BYTES decide a figure. Each is hashed
    before and after the run and the two must agree — the direct evidence that
    nothing moved the tree DURING the measurement.

    ``baseline_commit`` is REQUIRED and must be an immutable commit SHA.
    """

    def __init__(self, *, title: str, instruments: Sequence[str],
                 baseline_commit: str, prose_default: str = "CHANGELOG.md"):
        self.title = title
        self.instruments = tuple(instruments)
        self.baseline_commit = assert_immutable_baseline(baseline_commit)
        self.prose_default = prose_default
        self.figures: list = []
        self.failures: list = []
        self._prose: Dict[str, str] = {}
        self._before: Dict[str, str] = {}
        self._t0 = time.time()

    # ── prose, read ONCE per path ────────────────────────────────────────────
    def prose(self, where: str) -> str:
        """The text of ``where``, cached. rc470 re-read a 4.27 MB file 29×."""
        if where not in self._prose:
            self._prose[where] = Path(PY_ROOT, where).read_text(encoding="utf-8")
        return self._prose[where]

    # ── the figure + prose diff ──────────────────────────────────────────────
    def figure(self, label, value, *needles, where="") -> None:
        """Record a measured figure and diff the prose against it.

        ``needles`` are format strings; ``{v}`` becomes the measured value.
        ``where`` is a path OR a tuple of paths — every rendered needle must
        occur in EVERY named file. rc470 witnessed nine instruments' hashes and
        diffed the prose of two, and the gap is why a stale comment survived
        its own freshness discipline.
        """
        import srmech
        self.figures.append((label, value))
        if isinstance(where, (tuple, list)):
            targets = tuple(where)
        else:
            targets = (where or self.prose_default,)
        bad = []
        for target in targets:
            text = self.prose(target)
            bad += [(target, n.format(v=value)) for n in needles
                    if n.format(v=value) not in text]
        mark = "OK " if not bad else "RED"
        print(f"  [{mark}] {label} = {value!r}   [srmech {srmech.__file__}]")
        for target, needle in bad:
            print(f"        MISSING FROM {target}: {needle!r}")
            self.failures.append((target, label, value, needle))

    # ── the static-tree witness ──────────────────────────────────────────────
    def snapshot(self) -> Dict[str, str]:
        return {rel: sha(Path(PY_ROOT, rel).read_bytes())
                for rel in self.instruments}

    def header(self) -> None:
        """Print the run banner, the environment and the BEFORE witness."""
        widen_stdout()
        self_check(sys.modules[__name__])
        import srmech
        from srmech import _native

        print("=" * 78)
        print(self.title)
        print("=" * 78)
        print(f"srmech.__version__ {srmech.__version__}")
        print(f"srmech.__file__    {srmech.__file__}")
        print(f"HAS_NATIVE         {_native.HAS_NATIVE}")
        print(f"stdout codec       {sys.stdout.encoding} (widened by "
              f"figure_run.widen_stdout)")
        for mod in ("numpy", "sympy"):
            try:
                __import__(mod)
                print(f"{mod:18} PRESENT  <-- every figure below is quoted "
                      f"numpy/sympy-ABSENT; this run is NOT comparable")
            except ModuleNotFoundError:
                print(f"{mod:18} absent (ModuleNotFoundError)")
        print(f"git HEAD           {git('rev-parse', 'HEAD').strip()}")
        print(f"git branch         {git('rev-parse', '--abbrev-ref', 'HEAD').strip()}")
        print(f"baseline_commit    {self.baseline_commit} (immutable, asserted)")

        print("\n-- STATIC-TREE WITNESS: instruments --")
        porcelain = git("status", "--porcelain", "--",
                        *[f"docs/srmech/python/{r}" for r in self.instruments])
        print("git status --porcelain (instruments):")
        print("  " + ("\n  ".join(porcelain.splitlines()) or "(clean)"))
        print("⚠️ git status is TOOLCHAIN-DEPENDENT on this tree (CRLF worktree, "
              "LF blobs); the == HEAD column below compares EOL-normalised "
              "CONTENT and is not.")
        self._before = self.snapshot()
        for rel, h in self._before.items():
            print(f"  {rel:44} sha256 {h[:32]}…  {head_state(rel)}")

    def footer(self) -> int:
        """Print the AFTER witness and the verdict; return the exit code."""
        print("\n-- STATIC-TREE WITNESS: instruments, AFTER --")
        after = self.snapshot()
        moved = [k for k in self._before if self._before[k] != after[k]]
        for rel in self.instruments:
            flag = "MOVED DURING THE RUN" if rel in moved else "unchanged"
            print(f"  {rel:44} sha256 {after[rel][:32]}…  {flag}")
        if moved:
            print(f"\n!! {len(moved)} INSTRUMENT(S) CHANGED WHILE THIS RUN WAS "
                  f"MEASURING: {moved}. EVERY FIGURE ABOVE IS VOID — the tree "
                  f"was not static. This is the exact condition that produced "
                  f"rc470's phantom `246 != 219`.")
            self.failures.append(("<tree>", "static-tree witness", moved,
                                  "unchanged"))

        print("\n" + "=" * 78)
        print(f"{len(self.figures)} figures, {len(self.failures)} disagreeing "
              f"with the prose, {time.time() - self._t0:.1f}s")
        if self.failures:
            print("\nPROSE DISAGREES WITH THIS TREE:")
            for where, label, value, needle in self.failures:
                print(f"  {where}: {label} measured {value!r}; prose does not "
                      f"contain {needle!r}")
            print("\nA figure the final run cannot produce is DELETED, not "
                  "adjusted. Fix the prose, then re-run this script LAST.")
            return 1
        print("Every figure in the prose is reproduced by this run.")
        return 0

    # ── ONE rglob pass, every pattern ────────────────────────────────────────
    def sweep(self, patterns: Mapping[str, "re.Pattern"],
              subtrees: Iterable[str] = ("srmech", "tests", "tools"),
              exclude: Iterable[Path] = ()) -> Dict[str, Tuple[int, int, int]]:
        """``{tag: (occurrences, lines, files)}`` from ONE walk of the tree.

        rc470 walked the whole ``.py`` population once per regex — 1020 files,
        2040 reads, 52.7 MB for two patterns. The population is identical for
        every pattern, so it is built once here and handed to
        :func:`sweep_paths`, which reads each file once.
        """
        excluded = {Path(p).resolve() for p in exclude}
        paths = [p for sub in subtrees
                 for p in sorted((PY_ROOT / sub).rglob("*.py"))
                 if p.resolve() not in excluded]
        return sweep_paths(paths, patterns)

    # ── ONE pytest process for every gate set ────────────────────────────────
    def union_pytest(self, sets: Sequence[Sequence[str]], xml_path: Path
                     ) -> Tuple[list, Dict[str, Dict[str, int]]]:
        """Run the UNION of ``sets`` in ONE pytest and split the tally back.

        Returns ``(per_set_outcomes, per_file_tally)``, each an
        :data:`OUTCOME_KEYS` dict. rc470 spent one process per set over 11
        file-slots covering 9 distinct files, re-running the two that appeared
        twice.

        ⚠️ **One agreeing run is not proof of order-independence.** A test whose
        outcome depends on module state left by a sibling file will differ
        between this union and the per-set runs. :func:`per_set_pytest` runs the
        old shape so a caller can diff the two; do that whenever the sets change.
        """
        union = sorted({f for group in sets for f in group})
        xml_path.parent.mkdir(parents=True, exist_ok=True)
        line = self._pytest(union, extra=[f"--junit-xml={xml_path}"])
        print(f"    union of {len(union)} files -> {line}")
        tally = parse_junit(xml_path)
        unmapped = tally.pop("", None)
        if unmapped:
            raise AssertionError(
                f"{unmapped} junit test case(s) could not be mapped back to a "
                f"source file. The XML has no `file` attribute; grouping is on "
                f"`classname`, and a classname that resolves to nothing means "
                f"the split is silently dropping cases — which is how a first "
                f"parse of this XML returned zeros.")
        per_set = [{k: sum(tally.get(f, {}).get(k, 0) for f in group)
                    for k in OUTCOME_KEYS} for group in sets]
        return per_set, tally

    def per_set_pytest(self, sets: Sequence[Sequence[str]]) -> list:
        """The OLD shape — one process per set. The order-independence control.

        Returns ``collected`` (``passed + skipped``) per set, so it compares
        like with like against :meth:`union_pytest`.
        """
        out = []
        for group in sets:
            line = self._pytest(group)
            got = {k: int(m.group(1)) for k, m in
                   ((k, re.search(r"(\d+) " + k, line)) for k in
                    ("passed", "skipped")) if m}
            out.append(got.get("passed", 0) + got.get("skipped", 0))
        return out

    # ── one pytest invocation ────────────────────────────────────────────────
    def _pytest(self, files: Sequence[str], mutant=None, module=None,
                extra: Sequence[str] = ()) -> str:
        env = dict(os.environ)
        if mutant is not None:
            env["CANFAIL_DIR"] = str(mutant)
            env["CANFAIL_MODULE"] = module or "demotion_probe"
            env["PYTHONPATH"] = str(PY_ROOT / "tools")
        cmd = [sys.executable, "-m", "pytest", *files, "-q",
               "-p", "no:cacheprovider", *extra]
        if mutant is not None:
            cmd += ["-p", "canfail_preload"]
        # encoding= explicitly, for the reason written out at :func:`git`:
        # `text=True` alone decodes with the LOCALE codec, and a cp1252 host
        # meeting one non-ASCII byte in a pytest summary loses the whole
        # capture inside subprocess's reader thread. Same defect class, same
        # file, so it is closed here rather than left as the one that had not
        # bitten yet.
        out = subprocess.run(cmd, cwd=str(PY_ROOT), capture_output=True,
                             text=True, encoding="utf-8", errors="replace",
                             env=env).stdout
        tail = [x for x in out.strip().split("\n")
                if "passed" in x or "failed" in x or "error" in x]
        return re.sub(r"\s+in\s+[\d.]+s.*$", "", tail[-1]) if tail else "<no result>"

    def pytest_line(self, files: Sequence[str], mutant=None,
                    module=None) -> str:
        """One pytest run, its summary line printed and returned."""
        line = self._pytest(files, mutant=mutant, module=module)
        print(f"    pytest {' '.join(Path(f).name for f in files)}"
              f"{' [MUTANT ' + mutant.name + ']' if mutant else ''} -> {line}")
        return line

    # ── the pinned baseline, read by SHA ─────────────────────────────────────
    def baseline_source(self, rel: str, expect_sha256: str = "") -> str:
        """The text of ``rel`` at ``baseline_commit``, optionally SHA-asserted.

        ``expect_sha256`` is how a caller proves it pinned the commit it meant:
        a SHA that resolves but whose file lacks the name the caller needs is a
        MISIDENTIFIED baseline, and it fails here with the digest rather than
        later with a ``KeyError``.
        """
        text = git("show", f"{self.baseline_commit}:docs/srmech/python/{rel}")
        if not text:
            raise AssertionError(
                f"baseline {self.baseline_commit} holds no "
                f"docs/srmech/python/{rel}")
        got = sha(text.encode("utf-8"))
        if expect_sha256 and got != expect_sha256:
            raise AssertionError(
                f"baseline {self.baseline_commit}:{rel} has sha256 {got}, "
                f"expected {expect_sha256} — the pin names a different tree "
                f"than the caller measured against.")
        return text
