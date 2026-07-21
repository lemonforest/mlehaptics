"""srmech_import_guard — make banned modules genuinely UNIMPORTABLE, not merely linted.

WHY LINT WAS NOT ENOUGH. Two holes let numpy reach 312 imports across 310 files while both guards
reported clean:

  1. `check_srmech_discipline.py` never listed a BARE `import numpy` as HARD at all — only
     `np.linalg.*` CALLS. So a file could import numpy, use it for a hundred array ops, and the
     full-file ratchet counted zero violations.
  2. The pre-commit hook IS diff-aware by design (so existing debt is grandfathered), which is right
     for a ratchet and wrong as the only defence: every already-present import is permanently exempt,
     and nothing ever re-examines it.

A lint says "you should not". An import hook says "you cannot". `fractions` matters for the same
reason as numpy and is easier to miss: `Fraction` is the Python-native exact rational, so reaching
for it silently bypasses srmech's Class-N rational surface — the substitution is invisible in review
precisely because the result is *correct*, just not ours.

USAGE
  explicit (a single script):     import srmech_import_guard  # noqa: F401  -- first import in the file
  venv-wide (the real answer):    srmech_import_guard.install_sitecustomize("/path/to/venv")
  audit what would break:         python3 srmech_import_guard.py --audit .

ESCAPE HATCH, deliberately awkward. `SRMECH_ALLOW_IMPORTS=numpy,fractions` disables the block for the
named modules. It exists because 310 files cannot migrate atomically — but it is an environment
variable, so it appears in the command line of whatever used it, which is the point: an exemption you
can see beats an exemption you inherit.
"""
from __future__ import annotations

import os
import sys

# module -> what to use instead. The message is the whole value of the guard: a bare ImportError
# teaches nothing, so each one names the actual replacement op.
BANNED = {
    "numpy": ("srmech carriers Mat / Vec / HV (srmech.amsc.mat, .vec) and the Class-L ops in "
              "srmech.amsc.laplacian. numpy was REMOVED from srmech at #564 — every continuous-math "
              "op is a cascade of the 14."),
    "fractions": ("srmech.amsc.rational (Class N) — best_rational / the exact-rational Q carrier. "
                  "fractions.Fraction is the Python-native exact rational, so reaching for it "
                  "silently bypasses the Class-N surface while still producing a correct number, "
                  "which is what makes the substitution invisible in review."),
}


def _allowed() -> set[str]:
    raw = os.environ.get("SRMECH_ALLOW_IMPORTS", "")
    return {p.strip() for p in raw.split(",") if p.strip()}


class _BlockedImport(ImportError):
    pass


class SrmechImportGuard:
    """A sys.meta_path finder that refuses banned top-level modules.

    Placed FIRST on meta_path, so it is consulted before any real finder and the module is never
    located, let alone executed. Sub-imports (`numpy.linalg`) are caught too, since the check is on
    the top-level package name.
    """

    def find_module(self, fullname, path=None):        # legacy API, harmless to keep
        self.find_spec(fullname, path)
        return None

    def find_spec(self, fullname, path=None, target=None):
        top = fullname.split(".")[0]
        if top in BANNED and top not in _allowed():
            raise _BlockedImport(
                "`import %s` is BLOCKED by srmech_import_guard.\n"
                "    use instead: %s\n"
                "    If this is genuinely unavoidable, run with SRMECH_ALLOW_IMPORTS=%s — an "
                "exemption that shows up in the command line rather than one you inherit."
                % (fullname, BANNED[top], top)
            )
        return None


_INSTALLED = False


def install() -> bool:
    """Idempotent. Returns True if this call installed the guard."""
    global _INSTALLED
    if _INSTALLED:
        return False
    # Modules already in sys.modules were imported before the guard and cannot be un-imported;
    # report them rather than pretending the block is total.
    pre = sorted(m for m in BANNED if m in sys.modules)
    if pre:
        sys.stderr.write("srmech_import_guard: already imported before install, NOT blocked: %s\n" % pre)
    sys.meta_path.insert(0, SrmechImportGuard())
    _INSTALLED = True
    return True


def install_sitecustomize(venv_path: str) -> str:
    """Write a sitecustomize.py into a venv so the guard is active for EVERY process using it.

    This is what "can never even import" actually requires: Python imports sitecustomize
    automatically at startup, before any user code runs.
    """
    import glob as _glob
    hits = _glob.glob(os.path.join(venv_path, "lib", "python*", "site-packages"))
    if not hits:
        raise RuntimeError("no site-packages under %s" % venv_path)
    dst = os.path.join(hits[0], "sitecustomize.py")
    here = os.path.dirname(os.path.abspath(__file__))
    with open(dst, "w") as fh:
        fh.write("import sys\nsys.path.insert(0, %r)\n"
                 "import srmech_import_guard\nsrmech_import_guard.install()\n" % here)
    return dst


def audit(root: str = ".") -> int:
    """Report the blast radius WITHOUT blocking anything — what would break, and where."""
    import ast
    import collections
    import glob as _glob
    per = collections.Counter()  # srmech-allow: tallying import counts for a REPORT, not a co-occurrence storage proxy — nothing here feeds a Class-L object
    files = collections.defaultdict(list)
    for f in sorted(_glob.glob(os.path.join(root, "**", "*.py"), recursive=True)):
        try:
            tree = ast.parse(open(f).read())
        except (SyntaxError, UnicodeDecodeError):
            continue
        for n in ast.walk(tree):
            mods = []
            if isinstance(n, ast.Import):
                mods = [a.name.split(".")[0] for a in n.names]
            elif isinstance(n, ast.ImportFrom):
                mods = [(n.module or "").split(".")[0]]
            for m in mods:
                if m in BANNED:
                    per[m] += 1
                    if f not in files[m]:
                        files[m].append(f)
    print("=== srmech_import_guard audit: %s ===" % root)
    for m in BANNED:
        print("  %-12s %4d imports across %4d files" % (m, per[m], len(files[m])))
    print("\n  These would ALL fail under the guard. Migrate, or run them with")
    print("  SRMECH_ALLOW_IMPORTS=<module> while they are being migrated.")
    return 0


if __name__ == "__main__":
    if "--audit" in sys.argv:
        i = sys.argv.index("--audit")
        sys.exit(audit(sys.argv[i + 1] if len(sys.argv) > i + 1 else "."))
    sys.exit(audit("."))
