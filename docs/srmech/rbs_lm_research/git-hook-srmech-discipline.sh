#!/usr/bin/env bash
# srmech/siona discipline pre-commit tripwire — blocks NEWLY ADDED stop-list idioms in staged
# code under docs/srmech/: the co-occurrence Counter, numpy, python abs, np.linalg eig/svd, and
# hashlib sha256. Diff-aware: only ADDED lines are checked, so existing uses are grandfathered
# (the AST ratchet check_srmech_discipline.py is the full-file audit). The co-occurrence Counter
# is stdlib so it can't be pip-blocked like numpy (no install to refuse) — this commit-gate is the
# equivalent guard. Escape a genuinely-legit line with a trailing  # srmech-allow: <reason>
# (e.g. the matrix_cascades einsum-label parse). NB: this script's prose avoids the literal
# idiom spellings on purpose so it does not flag itself; the grep patterns below are escaped.
#
# Install:  cp docs/srmech/rbs_lm_research/git-hook-srmech-discipline.sh "$(git rev-parse --git-path hooks)/pre-commit" && chmod +x "$(git rev-parse --git-path hooks)/pre-commit"
set -u
SCOPE="docs/srmech"
added=$(git diff --cached --unified=0 -- "$SCOPE" 2>/dev/null \
        | grep -E '^\+' | grep -vE '^\+\+\+' \
        | grep -vE 'srmech-allow')
hits=$(printf '%s\n' "$added" | grep -nE \
  '(\bCounter[[:space:]]*\()|(^\+.*\bimport[[:space:]]+numpy)|(^\+.*\bfrom[[:space:]]+numpy)|(\babs[[:space:]]*\()|(np\.linalg\.(eig|eigh|svd))|(numpy\.linalg\.(eig|eigh|svd))|(hashlib\.sha256)' \
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
