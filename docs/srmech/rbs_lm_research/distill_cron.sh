#!/usr/bin/env bash
# R-RBS-LM-29 — Long-running distillation wrapper for cron / unattended runs.
#
# Per user direction 2026-05-25: *"bench how long tiny llama takes and then
# consider if we can script llama 30b or 70b as a cron task while we do
# other things, into RBS-LM native."*
#
# The pattern: run distillation in the background with nohup so it survives
# terminal close / session end; log to a labeled log file; provide --status
# to check progress; provide --reap to clean up source-model cache after
# success.
#
# Usage:
#   # Start a distillation in the background
#   distill_cron.sh start --source MODEL --gen-bytes N [--label TAG] [--stride S]
#
#   # Check status of a labeled distillation
#   distill_cron.sh status [LABEL]              # specific label, or all
#
#   # Tail the live log of a running distillation
#   distill_cron.sh tail LABEL
#
#   # Clean up source model from HF cache after distillation succeeds
#   distill_cron.sh reap LABEL                   # removes HF cache for that source
#
#   # Cancel a running distillation
#   distill_cron.sh cancel LABEL
#
# Examples:
#   # Llama 3.1 8B distillation (~50 min on 2009 Xeon)
#   distill_cron.sh start \
#       --source meta-llama/Llama-3.1-8B \
#       --gen-bytes 50000 \
#       --label llama3-8b
#
#   # Llama 3.1 70B distillation via GGUF (~10-12 hours)
#   distill_cron.sh start \
#       --source meta-llama/Llama-3.1-70B \
#       --gen-bytes 50000 \
#       --label llama3-70b
#
#   # Check status later — it will tell you if still running or done
#   distill_cron.sh status llama3-8b

set -euo pipefail

# ---- Paths ---------------------------------------------------------------
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../../.." && pwd)"
LOG_DIR="${SCRIPT_DIR}/log"
PID_DIR="${SCRIPT_DIR}/log/pids"
ENCODER="${SCRIPT_DIR}/encode_bytes_variant_b_generic.py"
VENV_PY="${HOME}/.venvs/rbs-lm-research/bin/python"
STORAGE_PY="${SCRIPT_DIR}/storage_management.py"

mkdir -p "${LOG_DIR}" "${PID_DIR}"

# ---- Subcommand: start --------------------------------------------------
cmd_start() {
    local source=""
    local gen_bytes=""
    local label=""
    local stride="8"
    local max_per_prompt="80"
    local est_model_gb=""

    while [[ $# -gt 0 ]]; do
        case "$1" in
            --source) source="$2"; shift 2 ;;
            --gen-bytes) gen_bytes="$2"; shift 2 ;;
            --label) label="$2"; shift 2 ;;
            --stride) stride="$2"; shift 2 ;;
            --max-per-prompt) max_per_prompt="$2"; shift 2 ;;
            --est-model-gb) est_model_gb="$2"; shift 2 ;;
            *) echo "unknown arg: $1" >&2; return 2 ;;
        esac
    done

    if [[ -z "$source" || -z "$gen_bytes" ]]; then
        echo "usage: distill_cron.sh start --source MODEL --gen-bytes N [--label TAG]" >&2
        return 2
    fi

    if [[ -z "$label" ]]; then
        label=$(echo "$source" | sed 's:/:__:g')
    fi
    if [[ -z "$est_model_gb" ]]; then
        # Default precheck size 5 GB if not specified (covers up to Llama-class 7B fp16)
        est_model_gb="5.0"
    fi

    local timestamp=$(date -u +%Y%m%dT%H%M%SZ)
    local log_file="${LOG_DIR}/distill_${label}_${timestamp}.log"
    local pid_file="${PID_DIR}/${label}.pid"

    if [[ -f "$pid_file" ]] && kill -0 "$(cat "$pid_file")" 2>/dev/null; then
        echo "ERROR: distillation labelled ${label} already running (pid $(cat "$pid_file"))" >&2
        echo "  cancel first: distill_cron.sh cancel ${label}" >&2
        return 1
    fi

    echo "Starting distillation:"
    echo "  source:     $source"
    echo "  gen-bytes:  $gen_bytes"
    echo "  label:      $label"
    echo "  stride:     $stride"
    echo "  log file:   $log_file"

    cd "$REPO_ROOT"
    nohup "$VENV_PY" "$ENCODER" \
        --source-model "$source" \
        --gen-bytes "$gen_bytes" \
        --stride "$stride" \
        --max-per-prompt "$max_per_prompt" \
        --est-model-gb "$est_model_gb" \
        >> "$log_file" 2>&1 &
    local pid=$!
    echo "$pid" > "$pid_file"
    echo "$source" > "${PID_DIR}/${label}.source"
    echo "$log_file" > "${PID_DIR}/${label}.log_path"

    echo
    echo "Started in background:"
    echo "  pid:        $pid"
    echo "  status:     distill_cron.sh status $label"
    echo "  tail:       distill_cron.sh tail $label"
    echo "  cancel:     distill_cron.sh cancel $label"
    echo "  reap (post-success): distill_cron.sh reap $label"
}

# ---- Subcommand: status -------------------------------------------------
cmd_status() {
    local target="${1:-}"

    if [[ -n "$target" ]]; then
        local labels=("$target")
    else
        local labels=()
        for f in "${PID_DIR}"/*.pid; do
            [[ -e "$f" ]] || continue
            labels+=("$(basename "$f" .pid)")
        done
        if [[ ${#labels[@]} -eq 0 ]]; then
            echo "No tracked distillations."
            return 0
        fi
    fi

    for label in "${labels[@]}"; do
        local pid_file="${PID_DIR}/${label}.pid"
        if [[ ! -f "$pid_file" ]]; then
            echo "[$label] NOT TRACKED"
            continue
        fi
        local pid=$(cat "$pid_file")
        local source=$(cat "${PID_DIR}/${label}.source" 2>/dev/null || echo "?")
        local log_path=$(cat "${PID_DIR}/${label}.log_path" 2>/dev/null || echo "?")

        if kill -0 "$pid" 2>/dev/null; then
            local elapsed=$(ps -o etime= -p "$pid" | tr -d ' ' || echo "?")
            local cpu_pct=$(ps -o %cpu= -p "$pid" | tr -d ' ' || echo "?")
            echo "[$label] RUNNING (pid $pid; elapsed $elapsed; cpu ${cpu_pct}%)"
        else
            # Process exited — see if instrument file landed
            local safe_src=$(echo "$source" | sed 's:/:__:g')
            local instrument="${SCRIPT_DIR}/rbs_lm_instrument_v29_distill_${safe_src}.bin"
            if [[ -f "$instrument" ]]; then
                local bytes=$(stat -c %s "$instrument")
                echo "[$label] DONE (instrument $instrument; ${bytes} bytes)"
            else
                echo "[$label] EXITED — instrument file NOT FOUND; check log: $log_path"
            fi
        fi
        echo "  source: $source"
        echo "  log:    $log_path"
    done
}

# ---- Subcommand: tail ---------------------------------------------------
cmd_tail() {
    local label="${1:?usage: distill_cron.sh tail LABEL}"
    local log_path=$(cat "${PID_DIR}/${label}.log_path" 2>/dev/null) || {
        echo "ERROR: no log path tracked for label '$label'" >&2; return 1
    }
    echo "Tailing $log_path (Ctrl-C to exit):"
    tail -n 20 -f "$log_path"
}

# ---- Subcommand: cancel -------------------------------------------------
cmd_cancel() {
    local label="${1:?usage: distill_cron.sh cancel LABEL}"
    local pid_file="${PID_DIR}/${label}.pid"
    [[ -f "$pid_file" ]] || { echo "no pid tracked for $label"; return 1; }
    local pid=$(cat "$pid_file")
    if kill -0 "$pid" 2>/dev/null; then
        echo "Cancelling $label (pid $pid)"
        kill -TERM "$pid"
        sleep 2
        kill -KILL "$pid" 2>/dev/null || true
    else
        echo "Process $pid not running"
    fi
    rm -f "$pid_file"
}

# ---- Subcommand: reap ---------------------------------------------------
cmd_reap() {
    local label="${1:?usage: distill_cron.sh reap LABEL}"
    local source=$(cat "${PID_DIR}/${label}.source" 2>/dev/null) || {
        echo "ERROR: no source tracked for label '$label'" >&2; return 1
    }
    local pid_file="${PID_DIR}/${label}.pid"
    if [[ -f "$pid_file" ]] && kill -0 "$(cat "$pid_file")" 2>/dev/null; then
        echo "ERROR: $label still running. Cancel first or wait for completion." >&2
        return 1
    fi

    echo "Reaping HF cache for source: $source"
    "$VENV_PY" -c "
import sys
sys.path.insert(0, '${SCRIPT_DIR}')
from storage_management import cleanup_caches, disk_summary
cleanup_caches(remove_vocab_table=False, hf_models=['$source'], verbose=True)
print()
print('Disk after cleanup:')
disk_summary(verbose=True)
"
    rm -f "${PID_DIR}/${label}.pid" "${PID_DIR}/${label}.source" "${PID_DIR}/${label}.log_path"
    echo
    echo "Reaped $label. Instrument bin retained; PID tracking removed."
}

# ---- Subcommand: help ---------------------------------------------------
cmd_help() {
    sed -n '/^# Usage:/,/^# Examples:/p' "$0" | sed 's/^# \{0,1\}//'
    echo
    sed -n '/^# Examples:/,/^set -e/p' "$0" | grep -v '^set' | sed 's/^# \{0,1\}//'
}

# ---- Dispatch -----------------------------------------------------------
cmd="${1:-help}"
shift || true
case "$cmd" in
    start)  cmd_start "$@" ;;
    status) cmd_status "$@" ;;
    tail)   cmd_tail "$@" ;;
    cancel) cmd_cancel "$@" ;;
    reap)   cmd_reap "$@" ;;
    help|--help|-h) cmd_help ;;
    *) echo "unknown subcommand: $cmd"; cmd_help; exit 2 ;;
esac
