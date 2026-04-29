# chess-spectral v1.5 --help discipline audit

**Date:** 2026-04-29
**Branch:** chess-spectral/v1.5-help-discipline-audit (from main @ 3148b7c)
**Scope:** all Python files with argparse surface added or substantively
modified since v1.3.2 (commit 775a571), plus the two console-script entry
points (`python/chess_spectral/cli.py`, `python/chess_spectral_4d/cli.py`)
which are explicit scope items per the audit task even when unchanged.

## Summary

- Files audited: **11** (every Python file under `python/` with an
  `argparse.ArgumentParser` or `add_argument` call)
- ArgumentParser calls checked: **11** (0 missing top-level `description`)
- add_argument calls checked: **76** (0 missing `help=`)
- Subparser entries checked: **15** (10 missing `description=` before fix; 0 after)
- **Total violations: 10 (all Medium severity, all auto-fixable)**

All 10 violations were the same shape: `subparsers.add_parser(name, help=...)`
with no `description=` argument. That's strictly weaker than §16.4 requires
("non-empty subcommand `description`"). The terse `help=` already gave a
one-liner for the parent's `--help`, but `<sub> --help` showed *no* prose
above the args list — the argparse default behavior when `description` is
unset is to render the args block immediately under the usage banner.

Per Task 4 case A (≤ 20 violations, all mechanical), fixes were applied
inline in the same audit branch.

## Findings

### Strong (release-blocking)

*(none)*

### Medium (should fix; description= missing on subparser)

All 10 violations were resolved in this audit branch. Each one had a
non-empty `help=` already; the gap was the longer-form `description=`
that argparse renders inside `<sub> --help`.

| # | File | Subcommand | Fix |
|---|---|---|---|
| 1 | `python/chess_spectral/cli.py:712` | `csv` | Added 4-line description covering CSV layout + sibling-NDJSON auto-detect |
| 2 | `python/chess_spectral/cli.py:725` | `encode` | Added description covering PGN/NDJSON/URL inputs + slicing flags |
| 3 | `python/chess_spectral/cli.py:751` | `encode-fen` | Added description noting `.spectralz`-suffix gzip inference |
| 4 | `python/chess_spectral/cli.py:792` | `version` | Added description naming all three printed fields |
| 5 | `python/chess_spectral/cli.py:796` | `compare` | Added description noting prefix-only comparison + float64 reduction |
| 6 | `python/chess_spectral/cli.py:804` | `query` | Added description listing the 10 channel names |
| 7 | `python/chess_spectral/cli.py:812` | `heatmap` | Added description naming color/glyph encoding |
| 8 | `python/chess_spectral/cli.py:834` | `export` | Added description noting C-binary parity + `%.6g` format |
| 9 | `python/chess_spectral_4d/cli.py:456` | `corpus-gen` | Added description naming the directory layout (ndjson/, spectralz/, manifest.json) |
| 10 | `python/chess_spectral_4d/cli.py:471` | `version` | Added description listing all five printed fields and the encoding-dim formula |

### Weak (style polish; not blocking)

*(none)*

## Per-file coverage table

Counts after the audit (all violations resolved).

| File | ArgumentParser desc | Total args | Args with `help=` | Subparsers (with `desc=`) | Status |
|---|---|---|---|---|---|
| `python/chess_spectral/cli.py` | yes | 30 | 30 | 10 / 10 | OK |
| `python/chess_spectral_4d/cli.py` | yes | 14 | 14 | 5 / 5 | OK |
| `python/analyze_stockfish_correlation.py` | yes | 8 | 8 | n/a | OK |
| `python/analyze_delta_sigma.py` | yes | 8 | 8 | n/a | OK |
| `python/analyze_stockfish_slices.py` | yes | 3 | 3 | n/a | OK |
| `python/staged_cosine.py` | yes | 1 | 1 | n/a | OK |
| `python/direct_orthogonality.py` | yes | 2 | 2 | n/a | OK |
| `python/analyze_fiber_rank_4d.py` | yes | 4 | 4 | n/a | OK |
| `python/analyze_safety.py` | yes (via `__doc__.split`) | 2 | 2 | n/a | OK |
| `python/analyze_channel_deltas.py` | yes (via `__doc__.split`) | 1 | 1 | n/a | OK |
| `python/tests/bench_encoder_4d.py` | yes (via `__doc__`) | 2 | 2 | n/a | OK |
| **Totals** | **11/11** | **75** | **75** | **15/15** | **clean** |

(Add-argument total of 75 above excludes the implicit `-h/--help` that
argparse injects on every parser; the Summary count of 76 includes it
once for the suite-level rollup.)

## Methodology

1. Enumerated every `.py` file under `docs/chess-maths/chess-spectral/python/`
   modified since `775a571` (chess-spectral v1.3.2): 48 files.
2. Filtered to those importing `argparse` or calling `add_argument` /
   `ArgumentParser`: only the 11 files in the table above. No script in
   `python/research/` uses argparse — all probes/demos there hard-code
   parameters in `main()`, so they're out of scope by the §16.4 rule
   (which targets CLI surface, not internal scripts).
3. For each in-scope file, walked every `ArgumentParser(...)`,
   `add_subparsers(...)`, `add_parser(...)`, and `add_argument(...)` call.
   Checked for non-empty `description=` (parent + every subparser) and
   non-empty `help=` (every argument).
4. Sanity-validated the fixes by running `<cli> <subcommand> --help` from
   the source tree for the four most-trafficked subcommands (`csv`,
   `version`, `corpus-gen`, `version` 4D); descriptions render as expected.

## Notes

- The audit treats `description=__doc__.split('\n', 1)[0]` and
  `description=__doc__` (used by `analyze_safety.py`,
  `analyze_channel_deltas.py`, `bench_encoder_4d.py`) as **valid**: the
  module docstring is non-empty in all three cases, so the rendered
  description is non-empty too. This idiom is fine — discipline §16.4
  requires *non-empty* description, not literal-string description.
- `add_subparsers(dest="cmd")` itself is unannotated in both 2D and 4D
  CLIs (no `description=`/`help=`/`title=` on the *grouping*). Per the
  task spec ("subparsers must have a `description` or `help` set on the
  **parent**"), and since both parent ArgumentParsers carry a
  description, this is fine. Annotating the subparsers-grouping itself
  would be additional polish but is not §16.4-required and was left
  alone to keep this audit minimal.
- Research scripts under `python/research/` were inspected: 13 files
  with `if __name__ == "__main__"` blocks, **none** uses argparse. All
  probes/demos hard-code their parameters. They are correctly out of
  §16.4 scope (not CLI surface).
- The two CLI files were unchanged on disk since v1.3.2 (`git diff
  775a571..HEAD -- python/chess_spectral/cli.py` and the 4D analogue
  both return empty), but the user's task lists them as explicit scope
  items, and §16.4 applies project-wide. The 10 missing descriptions
  were therefore long-standing gaps surfaced by this audit, not v1.5
  regressions.
