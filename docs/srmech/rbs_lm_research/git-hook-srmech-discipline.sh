#!/usr/bin/env bash
# srmech/siona discipline pre-commit tripwire — blocks NEWLY ADDED stop-list idioms in staged
# code under docs/srmech/: the co-occurrence Counter, numpy, python abs, np.linalg eig/svd, and
# hashlib sha256, and builtin hash() (#1454/F1276 -- PYTHONHASHSEED-salted, and a BUILTIN so  # srmech-allow: this header names the idioms it blocks; .sh stays on the grep
# there is no import to block and nothing to pip-refuse; this gate is the only catch). Prose
# files (.md/.txt/.rst/.ndjson) are EXCLUDED so a finding may name the idioms it discusses.
# Diff-aware: only ADDED lines are checked, so existing uses are grandfathered
# (the AST ratchet check_srmech_discipline.py is the full-file audit). The co-occurrence Counter
# is stdlib so it can't be pip-blocked like numpy (no install to refuse) — this commit-gate is the
# equivalent guard. Escape a genuinely-legit line with a trailing  # srmech-allow: <reason>
# (e.g. the matrix_cascades einsum-label parse). NB: this script's prose avoids the literal
# idiom spellings on purpose so it does not flag itself; the grep patterns below are escaped.
#
# Install:  cp docs/srmech/rbs_lm_research/git-hook-srmech-discipline.sh "$(git rev-parse --git-path hooks)/pre-commit" && chmod +x "$(git rev-parse --git-path hooks)/pre-commit"
set -u
SCOPE="docs/srmech"

# A MERGE IS NOT AUTHORING. During a merge every file from the incoming branch appears as
# "added" in the staged diff, so this gate would re-scan all of main's work and block the sync.
# That is not hypothetical: it blocked the rc297 merge, and blocking merges is precisely how this
# branch drifted to rc256 and stayed there (#1454 s1). Incoming commits were gated on their own
# branch; this hook exists to gate what YOU write. Skip cleanly during a merge.
if [ -e "$(git rev-parse --git-path MERGE_HEAD)" ]; then
  echo "  (srmech discipline: merge in progress -- gate skipped; incoming work was gated upstream)"
  exit 0
fi
# .py -> AST (prose-safe by construction); the grep below keeps NON-Python files, where a
# textual match is unambiguous. See hook_staged_py_ast.py for why no regex can do the .py case.
AST_HELPER="docs/srmech/rbs_lm_research/hook_staged_py_ast.py"
if [ -f "$AST_HELPER" ]; then
  python3 "$AST_HELPER" || exit 1
fi
added=$(git diff --cached --unified=0 -- "$SCOPE" ':(exclude,glob)**/*.py' \
          ':(exclude)docs/srmech/python' ':(exclude)docs/srmech/c' \
          ':(exclude,glob)**/*.md' ':(exclude,glob)**/*.txt' \
          ':(exclude,glob)**/*.rst' ':(exclude,glob)**/*.ndjson' \
          ':(exclude,glob)*.md' ':(exclude,glob)*.txt' 2>/dev/null \
        | grep -E '^\+' | grep -vE '^\+\+\+' \
        | grep -vE 'srmech-allow')
hits=$(printf '%s\n' "$added" | grep -nE \
  '(\bCounter[[:space:]]*\()|(^\+.*\bimport[[:space:]]+numpy)|(^\+.*\bfrom[[:space:]]+numpy)|(\babs[[:space:]]*\()|(np\.linalg\.(eig|eigh|svd))|(numpy\.linalg\.(eig|eigh|svd))|(hashlib\.sha256)|(\bhash[[:space:]]*\()' \
  2>/dev/null)
if [ -n "$hits" ]; then
  echo "x srmech discipline: a NEW stop-list idiom was added under $SCOPE (CLAUDE.md s2 / s57 / #564 numpy purge)."
  echo "    co-occurrence count   -> srmech.amsc.text.cooccurrence_edges -> laplacian.dense_laplacian (NOT a count store)"
  echo "    relationship inference -> the resonator over the bound memory (NOT bigram counts; s57)"
  echo "    numpy                 -> gone (#564); every continuous-math op is a cascade of the 14"
  echo "    magnitude/eig/sha     -> cascade.magnitude / laplacian.* / format.sha256_bytes"
  echo "    Genuinely-legit line? -> append  # srmech-allow: <reason>  to it."
  echo "  offending ADDED lines:"
  printf '%s\n' "$hits" | sed 's/^/    /'
  exit 1
fi
exit 0
