#!/usr/bin/env bash
# ephemerides-spectral local smoke test
# ─────────────────────────────────────────────────────────────────────
# Mirrors the two key Linux CI checks before push:
#
#   1. Codegen reproducibility — snapshot SHA-256s of _data + _research,
#      run regenerate.py, snapshot again, diff. Catches the "edited
#      research/ source files but forgot to mirror to _research/" miss
#      that hit PR #286.
#
#   2. Test suite — pytest tests/. Catches ratchet asserts, manifest
#      SHA mismatches, and the runtime tests that broke when the new
#      saturn_rings pilot landed without the ratchet updates.
#
# Designed to run under WSL2 (Ubuntu) accessing the Windows-mounted
# repo at /mnt/d/GitHub/mlehaptics/. Also works under native Linux,
# macOS, or any environment with bash + python3 + git on PATH.
#
# What this DOES catch:
#   - Codegen drift (research/ → _research/ mirror missing or stale)
#   - Manifest SHA-256 mismatches against committed bytes
#   - All ratchet test asserts (source counts, adapter registry, etc.)
#   - Bridge / CLI surface contract regressions
#   - Adapter Protocol conformance
#
# What this does NOT catch:
#   - CRLF/LF mismatches between Windows working copy and git's stored
#     bytes (WSL2 sees the same working-copy bytes as Windows). Run
#     CI on push to catch those; the .gitattributes pin LF for the
#     paths that matter.
#   - Native (C) build or parity issues — the smoke uses pure-Python
#     fallback by default to avoid requiring gcc/cmake in WSL2.
#
# Usage:
#   bash docs/antikythera-maths/ephemerides-spectral/scripts/smoke_local.sh
#
# From Windows PowerShell:
#   wsl bash docs/antikythera-maths/ephemerides-spectral/scripts/smoke_local.sh
#
# First-run timing: ~30s for venv + install. Subsequent runs: ~60-90s
# end-to-end (codegen + 1900 tests).

set -euo pipefail

# ─────────────────────────────────────────────────────────────────────
# Locate package root + venv home
# ─────────────────────────────────────────────────────────────────────

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PKG_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
PYTHON_DIR="${PKG_DIR}/python"
CODEGEN_DIR="${PKG_DIR}/codegen"

# Venv outside the repo to avoid Windows-mount perf hit + accidental
# git-tracking. Cached across runs for fast re-execution.
VENV_HOME="${VENV_HOME:-${HOME}/.venvs}"
VENV_DIR="${VENV_HOME}/ephemerides-spectral-smoke"

# ─────────────────────────────────────────────────────────────────────
# Colour helpers
# ─────────────────────────────────────────────────────────────────────

if [[ -t 1 ]]; then
    C_GREEN=$'\033[32m'
    C_RED=$'\033[31m'
    C_BLUE=$'\033[34m'
    C_DIM=$'\033[2m'
    C_RESET=$'\033[0m'
else
    C_GREEN=""; C_RED=""; C_BLUE=""; C_DIM=""; C_RESET=""
fi

step()    { echo "${C_BLUE}==>${C_RESET} $*"; }
ok()      { echo "${C_GREEN}OK${C_RESET}    $*"; }
fail()    { echo "${C_RED}FAIL${C_RESET}  $*"; exit 1; }
note()    { echo "${C_DIM}      $*${C_RESET}"; }

# ─────────────────────────────────────────────────────────────────────
# Environment detection
# ─────────────────────────────────────────────────────────────────────

step "Detecting environment"
if grep -qi microsoft /proc/version 2>/dev/null; then
    note "Running under WSL2 — repo at $(realpath "${PKG_DIR}")"
elif [[ "$(uname -s)" == "Linux" ]]; then
    note "Running under native Linux — repo at ${PKG_DIR}"
elif [[ "$(uname -s)" == "Darwin" ]]; then
    note "Running under macOS — repo at ${PKG_DIR}"
else
    note "Running under $(uname -s)"
fi

if ! command -v python3 >/dev/null 2>&1; then
    fail "python3 not found on PATH. Install Python 3.11+ first."
fi

PY_VERSION="$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')"
note "python3 = $(which python3) (${PY_VERSION})"

# ─────────────────────────────────────────────────────────────────────
# Venv setup (cached)
# ─────────────────────────────────────────────────────────────────────

step "Setting up venv at ${VENV_DIR}"
if [[ ! -d "${VENV_DIR}" ]]; then
    note "creating fresh venv (one-time, ~10s)"
    mkdir -p "${VENV_HOME}"
    python3 -m venv "${VENV_DIR}"
else
    note "reusing existing venv"
fi

# shellcheck disable=SC1091
source "${VENV_DIR}/bin/activate"

# Pure-Python install — no native build deps required. This matches
# the "fallback (pure-Python, no native)" CI job and avoids requiring
# gcc/cmake/scikit-build-core in the local WSL2 environment.
step "Installing runtime + test deps (pure-Python; no native build)"
python -m pip install --upgrade --quiet pip
python -m pip install --quiet pytest numpy skyfield jplephem
# tomli for Python <3.11 (descriptor parsing); harmless on >=3.11.
python -m pip install --quiet 'tomli; python_version < "3.11"'
note "deps installed"

# Add the package source dir to PYTHONPATH so the tests find
# ephemerides_spectral without needing scikit-build-core.
export PYTHONPATH="${PYTHON_DIR}:${PYTHONPATH:-}"

# ─────────────────────────────────────────────────────────────────────
# Check 1 — Codegen reproducibility
# ─────────────────────────────────────────────────────────────────────

step "Codegen reproducibility check"

SNAPSHOT_DIR="$(mktemp -d)"
trap 'rm -rf "${SNAPSHOT_DIR}"' EXIT

DATA_DIR="${PYTHON_DIR}/ephemerides_spectral/_data"
RESEARCH_DIR="${PYTHON_DIR}/ephemerides_spectral/_research"

# Manifest + initial_phases JSON are excluded from the diff because
# they're regenerated each run with timestamps inside; CI's check
# uses the same exclusions.
snapshot() {
    find "${DATA_DIR}" "${RESEARCH_DIR}" -type f \
        -not -name manifest.json \
        -not -name initial_phases.json \
        -exec sha256sum {} \; | sort
}

snapshot > "${SNAPSHOT_DIR}/before.sha256"

note "running regenerate.py..."
( cd "${CODEGEN_DIR}" && python regenerate.py > "${SNAPSHOT_DIR}/regenerate.log" 2>&1 ) || {
    cat "${SNAPSHOT_DIR}/regenerate.log"
    fail "regenerate.py exited non-zero"
}

snapshot > "${SNAPSHOT_DIR}/after.sha256"

if diff -q "${SNAPSHOT_DIR}/before.sha256" "${SNAPSHOT_DIR}/after.sha256" >/dev/null; then
    ok "_research/ + _data/ are byte-identical after regenerate (no codegen drift)"
else
    note "codegen produced different output than what's committed:"
    diff "${SNAPSHOT_DIR}/before.sha256" "${SNAPSHOT_DIR}/after.sha256" | sed 's/^/      /'
    note "fix: commit the regenerated _research/ + _data/ files"
    fail "codegen drift detected"
fi

# ─────────────────────────────────────────────────────────────────────
# Check 2 — pytest
# ─────────────────────────────────────────────────────────────────────

step "Running pytest tests/ -q"

cd "${PYTHON_DIR}"
if pytest tests/ -q --tb=short 2>&1 | tee "${SNAPSHOT_DIR}/pytest.log"; then
    ok "all tests pass"
else
    fail "pytest reported failures (see output above)"
fi

# ─────────────────────────────────────────────────────────────────────
# Summary
# ─────────────────────────────────────────────────────────────────────

echo
echo "${C_GREEN}══════════════════════════════════════════════════════════════════${C_RESET}"
echo "${C_GREEN}  smoke_local.sh: PASS — pre-push checks clean${C_RESET}"
echo "${C_GREEN}══════════════════════════════════════════════════════════════════${C_RESET}"
echo
note "Reminder: smoke does NOT cover CRLF/LF discipline,"
note "platform-wheel build, or native (C) parity. Push to a feature"
note "branch + check CI for full coverage."
