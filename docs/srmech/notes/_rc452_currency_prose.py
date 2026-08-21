"""rc452 (`#T1166`) scratch — the three GATED currency surfaces, moved to ABI 21.

These are the surfaces test_readme_currency_rc419 and test_notebook_currency_rc420
read. They are moved by REWRITING THE PROSE to the true state, never by
loosening the gate patterns — the gates' own diffs are down-only.

Exact-match with printed counts. Run from ``docs/srmech``.
"""
import sys
from pathlib import Path

ROOT = Path(".").resolve()
README = ROOT / "python" / "README.md"
NOTEBOOK = ROOT / "srmech_research_notebook.md"

NEW_BUMP = (
    "`SRMECH_ABI_VERSION` moves **20 → 21** at **v0.9.0rc452** (`#T1166`), and it "
    "is the first bump on this wire driven by a SILENT WRONG VALUE rather than a "
    "raise — and the first that adds no kind letter and moves no descriptor shape "
    "at all. What changes is WHO EMITS `q`. That kind has been on "
    "`srmech_chain_run`'s wire since long before this release (`cr_op_rat`, "
    "`cr_op_pow` and `cr_op_series` all build `CR_RATIONAL`, and two live attested "
    "catalogs dispatch them — measured at rc452, **39 `q` emissions over 51 "
    "catalog rows**). `cr_op_reorient` did not: handed a rational it fell through "
    "to the double arm, failed to read it, and returned `SRMECH_ERR_NOT_IMPL` so "
    "the chain deferred to pure. rc452 gives it a `CR_RATIONAL` arm, so the "
    "Class-C op ANSWERS an exact rational where it used to decline, and the Python "
    "reader rebuilds a `q` as `srmech.math.q.Q` where it used to rebuild a "
    "`(num, den)` tuple. Pair an rc452 library with rc451 Python and nothing "
    "raises: the chain returns a well-formed 2-tuple, which is also exactly how a "
    "Class-K pin pair and a Class-B `pair` step spell themselves, so a downstream "
    "consumer reads it happily and wrongly. v18 and v20 both bumped on the ground "
    "that an older reader RAISES mid-run; a raise stops and a wrong value "
    "propagates, so this one outranks them. `GENOME_FORMAT_VERSION` stays 20 — no "
    "on-disk format moves.\n\nThe PRIOR bump, **19 → 20** at **v0.9.0rc451** "
    "(gh #1653), is the *type* half of that issue."
)

SUBS = [
    (README,
     "(**ABI 20** at this release",
     "(**ABI 21** at this release", 1),
    (README,
     "v20 added the `{\"k\":\"t\"}` TUPLE value-descriptor kind to that same "
     "`srmech_chain_run` output wire and moved its `l` payload key from "
     "`\"items\"` to `\"v\"` so both chain wires spell that kind alike)",
     "v20 added the `{\"k\":\"t\"}` TUPLE value-descriptor kind to that same "
     "`srmech_chain_run` output wire and moved its `l` payload key from "
     "`\"items\"` to `\"v\"` so both chain wires spell that kind alike, and v21 "
     "gave `cr_op_reorient` a `CR_RATIONAL` arm so the Class-C op ANSWERS an "
     "exact rational — emitting the long-declared `q` kind — where it used to "
     "return `SRMECH_ERR_NOT_IMPL`, while the Python reader rebuilds that `q` as "
     "`srmech.math.q.Q` rather than as a `(num, den)` tuple)", 1),
    (README,
     "`SRMECH_ABI_VERSION` moves **19 → 20** at **v0.9.0rc451** (gh #1653), and "
     "it is the *type* half of the issue.",
     NEW_BUMP, 1),
    (README,
     "# {'has_native': True, 'dispatching': True, 'abi_version': 20,\n"
     "#  'expected_abi': 20, 'native_version': '0.9.0rc451', 'load_error': None}",
     "# {'has_native': True, 'dispatching': True, 'abi_version': 21,\n"
     "#  'expected_abi': 21, 'native_version': '0.9.0rc452', 'load_error': None}", 1),
    (NOTEBOOK,
     "*(Live at rc451: **`SRMECH_ABI_VERSION` is 20**, `c/include/srmech.h`.",
     "*(Live at rc452: **`SRMECH_ABI_VERSION` is 21**, `c/include/srmech.h`.", 1),
    (NOTEBOOK,
     "**rc451's v20 is v18's shape a second time on the SAME wire**",
     "**rc452's v21 is a NEW shape — the first on this wire driven by a silent "
     "wrong value rather than a raise, and the first that adds no kind letter at "
     "all**: `cr_op_reorient` gains a `CR_RATIONAL` arm, so the Class-C op ANSWERS "
     "an exact rational (emitting the long-declared `q`) where it used to return "
     "`SRMECH_ERR_NOT_IMPL`, and the Python reader rebuilds that `q` as "
     "`srmech.math.q.Q` instead of a `(num, den)` tuple — so an rc452 library "
     "against rc451 Python returns a well-formed 2-tuple and no error at all. "
     "Before it, **rc451's v20 is v18's shape a second time on the SAME wire**", 1),
]

fail = False
edits: dict = {}
for path, old, new, want in SUBS:
    with open(path, encoding="utf-8", newline="") as fh:
        raw = fh.read()
    nl = "\r\n" if "\r\n" in raw else "\n"
    s = edits.get(path, raw.replace("\r\n", "\n"))
    got = s.count(old)
    print("  %2d/%2d  %-12s %s" % (got, want, path.name, old[:60].replace("\n", " ")))
    if got != want:
        fail = True
        continue
    edits[path] = s.replace(old, new)
    edits.setdefault("_nl_" + str(path), nl)

if fail:
    print("MISMATCH — nothing written")
    sys.exit(1)

for path in (README, NOTEBOOK):
    nl = edits["_nl_" + str(path)]
    with open(path, "w", encoding="utf-8", newline="") as fh:
        fh.write(edits[path].replace("\n", nl))
    print("wrote %s (newline %r)" % (path.name, nl))
