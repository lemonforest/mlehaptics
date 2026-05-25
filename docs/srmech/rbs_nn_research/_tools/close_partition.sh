#!/usr/bin/env bash
# close_partition.sh — RBS-NN partition close-out wrapper
#
# Automates the mechanical close-out steps for an RBS-NN partition:
#   4. git add REPORT (+ extras) → git commit with structured body
#   5. git push
#   6. PATCH the rolling PR body to tick the partition checkbox + link REPORT
#
# Steps 1–3 (research, REPORT writing, worked-example authoring) remain manual.
# Step 7 (TaskUpdate in the harness) is called by Claude after this script returns.
#
# Usage:
#   close_partition.sh \
#       --id 3a \
#       --slug mlp_cascade \
#       --claim "<one-line closing claim>" \
#       [--report PATH] \
#       [--extra PATH] [--extra PATH ...] \
#       [--pr NUMBER]            # default: discover from current branch
#       [--dry-run]
#
# The script extracts the §8 Findings section from the REPORT verbatim
# for the commit body. It expects the REPORT structure used by
# R-RBS-NN-1 and R-RBS-NN-2 (§8 = Findings, §10 = closing).

set -euo pipefail

# --- defaults --------------------------------------------------------------
PARTITION_ID=""
SLUG=""
CLAIM=""
REPORT=""
EXTRA_FILES=()
PR_NUMBER=""
DRY_RUN=0
REPO="lemonforest/mlehaptics"
RESEARCH_DIR="docs/srmech/rbs_nn_research"

# --- arg parse -------------------------------------------------------------
while [[ $# -gt 0 ]]; do
    case "$1" in
        --id)        PARTITION_ID="$2"; shift 2 ;;
        --slug)      SLUG="$2"; shift 2 ;;
        --claim)     CLAIM="$2"; shift 2 ;;
        --report)    REPORT="$2"; shift 2 ;;
        --extra)     EXTRA_FILES+=("$2"); shift 2 ;;
        --pr)        PR_NUMBER="$2"; shift 2 ;;
        --dry-run)   DRY_RUN=1; shift ;;
        -h|--help)
            sed -n '2,30p' "$0"; exit 0 ;;
        *)
            echo "ERROR: unknown arg '$1'" >&2; exit 2 ;;
    esac
done

# --- validate required args -----------------------------------------------
[[ -n "$PARTITION_ID" ]] || { echo "ERROR: --id required" >&2; exit 2; }
[[ -n "$SLUG"         ]] || { echo "ERROR: --slug required" >&2; exit 2; }
[[ -n "$CLAIM"        ]] || { echo "ERROR: --claim required" >&2; exit 2; }

# Default REPORT path from id + slug
if [[ -z "$REPORT" ]]; then
    REPORT="$RESEARCH_DIR/R-RBS-NN-${PARTITION_ID}_${SLUG}_REPORT.md"
fi

[[ -f "$REPORT" ]] || { echo "ERROR: REPORT not found: $REPORT" >&2; exit 1; }

# Sanity check: REPORT should mark itself CLOSED
if ! grep -q 'Partition status:\*\* CLOSED' "$REPORT"; then
    echo "WARNING: REPORT does not contain 'Partition status:** CLOSED' — continuing anyway" >&2
fi

# --- discover PR from current branch if not given -------------------------
if [[ -z "$PR_NUMBER" ]]; then
    BRANCH="$(git rev-parse --abbrev-ref HEAD)"
    PR_NUMBER="$(gh pr list --repo "$REPO" --head "$BRANCH" --json number --jq '.[0].number // empty' 2>/dev/null || true)"
    [[ -n "$PR_NUMBER" ]] || { echo "ERROR: could not discover PR from branch '$BRANCH'" >&2; exit 1; }
fi
echo "[close] partition R-RBS-NN-$PARTITION_ID → PR #$PR_NUMBER"

# --- extract §8 Findings + §10 closing from the REPORT --------------------
# §8 Findings block: from a line starting "## §8 Findings" up to (but not
# including) the next "## §N" header.
FINDINGS_BLOCK="$(awk '
    /^## §8 Findings/        { capture=1; next }
    /^## §[0-9]/ && capture   { exit }
    capture                   { print }
' "$REPORT")"

if [[ -z "$FINDINGS_BLOCK" ]]; then
    echo "WARNING: could not extract §8 Findings from $REPORT — using --claim only as body" >&2
fi

# --- compose commit message ------------------------------------------------
SUBJECT="research(R-RBS-NN-${PARTITION_ID} CLOSED): ${CLAIM}"

BODY_FILE="$(mktemp)"
trap 'rm -f "$BODY_FILE"' EXIT

# git commit -F treats the first line of the file as the subject. We want
# "research(R-RBS-NN-${id} CLOSED): ${claim}" as the subject, so the file
# starts with $SUBJECT (not $CLAIM).
{
    echo "${SUBJECT}"
    echo ""
    if [[ -n "$FINDINGS_BLOCK" ]]; then
        echo "Findings (verbatim from §8 of $(basename "$REPORT")):"
        echo ""
        echo "$FINDINGS_BLOCK"
    fi
    echo ""
    echo "REPORT: $REPORT"
    if [[ ${#EXTRA_FILES[@]} -gt 0 ]]; then
        echo "Additional artefacts:"
        for f in "${EXTRA_FILES[@]}"; do echo "  - $f"; done
    fi
    echo ""
    echo "Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>"
} > "$BODY_FILE"

# --- dry-run preview -------------------------------------------------------
if [[ $DRY_RUN -eq 1 ]]; then
    echo "[close] DRY RUN — no changes will be made"
    echo "--- commit subject ---"
    echo "$SUBJECT"
    echo "--- commit body (first 60 lines) ---"
    head -60 "$BODY_FILE"
    echo "--- end ---"
    echo "[close] files that would be added:"
    echo "  - $REPORT"
    for f in "${EXTRA_FILES[@]}"; do echo "  - $f"; done
    exit 0
fi

# --- 4. git add + commit ---------------------------------------------------
git add "$REPORT"
for f in "${EXTRA_FILES[@]}"; do
    [[ -f "$f" ]] || { echo "ERROR: extra file not found: $f" >&2; exit 1; }
    git add "$f"
done

# Bail if nothing staged (REPORT already committed)
if git diff --cached --quiet; then
    echo "ERROR: nothing staged — REPORT already committed?" >&2
    exit 1
fi

git commit -F "$BODY_FILE"

# --- 5. git push -----------------------------------------------------------
git push

# --- 6. PATCH PR body to tick checkbox + link REPORT ----------------------
PR_BODY_FILE="$(mktemp)"
trap 'rm -f "$BODY_FILE" "$PR_BODY_FILE"' EXIT

gh api "repos/${REPO}/pulls/${PR_NUMBER}" --jq '.body' > "$PR_BODY_FILE"

# Replace the partition checkbox line. We accept both unticked and already-ticked
# (idempotent re-run) but only patch in the REPORT link if not already present.
# The line shape in PR body: `- [ ] **R-RBS-NN-3a** — MLP cascade decomposition through A-N`
REPORT_REL="${REPORT}"
SED_PATTERN="s|- \[ \] \*\*R-RBS-NN-${PARTITION_ID}\*\* \(.*\)|- [x] **R-RBS-NN-${PARTITION_ID}** \1 ([REPORT](${REPORT_REL}))|"

if grep -q "R-RBS-NN-${PARTITION_ID}\*\* .*REPORT" "$PR_BODY_FILE"; then
    echo "[close] checkbox already linked — skipping PR body update"
else
    sed -i "$SED_PATTERN" "$PR_BODY_FILE"
    gh api -X PATCH "repos/${REPO}/pulls/${PR_NUMBER}" -F body=@"$PR_BODY_FILE" --jq '.html_url' | tail -1
fi

echo "[close] R-RBS-NN-${PARTITION_ID} closed. PR #${PR_NUMBER} updated."
echo "[close] next: have Claude run TaskUpdate to mark the partition task completed."
