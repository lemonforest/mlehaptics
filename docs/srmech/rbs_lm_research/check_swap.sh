#!/usr/bin/env bash
# R-RBS-LM-30 — Swap configuration helper for large-model distillation.
#
# Per user direction 2026-05-25: *"Why can't we use swap for model
# conversion to RBS-LM? we aren't doing inference from it"*
#
# For Path D distillation (R-RBS-LM-25 / -29) we're doing one-shot
# generation, not real-time inference. The model only needs to be
# accessible during corpus generation; SLOW per-token rate via swap is
# acceptable for a cron-task pattern (R-RBS-LM-29 distill_cron.sh).
#
# This script reports current swap state, recommends a swap budget for
# a target model size, and optionally provisions an additional swapfile.
#
# Usage:
#   check_swap.sh                          # Report current state
#   check_swap.sh recommend MODEL_SIZE_GB  # Recommend swap for a target model
#   check_swap.sh add SIZE_GB [PATH]       # Create + activate an additional swapfile
#   check_swap.sh remove PATH              # Deactivate + delete a swapfile

set -euo pipefail

# ---- Helpers ------------------------------------------------------------

bytes_to_gb() { echo "scale=1; $1 / 1024 / 1024 / 1024" | bc; }

current_ram_total_gb() {
    awk '/^MemTotal:/ {printf "%.1f", $2 / 1024 / 1024}' /proc/meminfo
}

current_swap_total_gb() {
    local total_kb=0
    while read -r _name _type size _used _prio; do
        # /proc/swaps line: filename type size used priority
        total_kb=$((total_kb + size))
    done < <(tail -n +2 /proc/swaps 2>/dev/null)
    echo "scale=1; $total_kb / 1024 / 1024" | bc
}

disk_free_gb() {
    df -BG --output=avail / | tail -n1 | tr -d 'G '
}

# ---- Subcommand: status -------------------------------------------------

cmd_status() {
    local ram_gb=$(current_ram_total_gb)
    local swap_gb=$(current_swap_total_gb)
    local disk_free=$(disk_free_gb)
    local swappiness=$(cat /proc/sys/vm/swappiness)

    echo "=== Current memory / swap state ==="
    echo "  RAM total:        ${ram_gb} GB"
    echo "  Swap total:       ${swap_gb} GB"
    echo "  Disk free (root): ${disk_free} GB"
    echo "  Swappiness:       ${swappiness}  (60 = balanced; higher = more aggressive)"
    echo
    echo "  Active swap devices/files:"
    cat /proc/swaps | tail -n +2 | awk '{printf "    %s  (type %s; %.1f GB)\n", $1, $2, $3/1024/1024}'
    echo
    echo "  Reference: R-RBS-LM-30 swap-enabled distillation table"
    echo "    Path D doesn't need real-time inference; slow per-token rate is OK."
    echo "    fp16 model ≈ 2 bytes/param; Q4 GGUF ≈ 0.5 bytes/param."
}

# ---- Subcommand: recommend ----------------------------------------------

cmd_recommend() {
    local model_size_gb="${1:?usage: check_swap.sh recommend MODEL_SIZE_GB}"
    local ram_gb=$(current_ram_total_gb)
    local swap_gb=$(current_swap_total_gb)
    local disk_free=$(disk_free_gb)
    local overhead_gb=12  # working memory + buffers; rough estimate

    local need_kvbuf="$overhead_gb"
    local total_need=$(echo "scale=1; $model_size_gb + $need_kvbuf" | bc)
    local already=$(echo "scale=1; $ram_gb + $swap_gb" | bc)
    local shortfall=$(echo "scale=1; $total_need - $already" | bc)

    echo "=== Recommendation for ${model_size_gb} GB model ==="
    echo "  Target model:     ${model_size_gb} GB"
    echo "  Working overhead: ${overhead_gb} GB  (KV cache + activations + buffers)"
    echo "  Total need:       ${total_need} GB"
    echo "  Current capacity: ${already} GB  (${ram_gb} RAM + ${swap_gb} swap)"

    # bc returns 0/1 for comparisons
    local need_more=$(echo "$shortfall > 0" | bc)
    if [[ "$need_more" -eq 1 ]]; then
        local recommended=$(echo "scale=0; ($shortfall + 16) / 1" | bc)
        echo
        echo "  Shortfall:        ${shortfall} GB"
        echo "  Recommended:      ADD ${recommended} GB of swap (shortfall + 16 GB headroom)"
        echo "  Disk free:        ${disk_free} GB  (capacity sufficient: $([[ "$disk_free" -gt "$recommended" ]] && echo YES || echo "NO — increase disk first"))"
        echo
        echo "  Command:"
        echo "    sudo bash check_swap.sh add ${recommended} /swap_rbs_lm_30.img"
        echo
        echo "  Estimated per-token rate via swap on 2009 Xeon E5530 + HDD/SSD:"
        echo "    fp16 model loaded from swap: ~10-30 sec/token (highly variable)"
        echo "    For a 50,000-byte corpus (~12,500 tokens): ~1-4 days"
        echo "    Use distill_cron.sh start to launch unattended."
    else
        echo
        echo "  ✓ Current capacity sufficient. No additional swap needed."
        echo "    Headroom after model load: $(echo "scale=1; -1 * $shortfall" | bc) GB"
    fi
}

# ---- Subcommand: add ----------------------------------------------------

cmd_add() {
    local size_gb="${1:?usage: check_swap.sh add SIZE_GB [PATH]}"
    local path="${2:-/swap_rbs_lm_30.img}"

    if [[ "$EUID" -ne 0 ]]; then
        echo "ERROR: must run as root (sudo)" >&2
        return 1
    fi

    if [[ -e "$path" ]]; then
        echo "ERROR: $path already exists. Remove it first or pick another path." >&2
        return 1
    fi

    local disk_free=$(disk_free_gb)
    if [[ "$disk_free" -lt "$((size_gb + 5))" ]]; then
        echo "ERROR: disk_free=${disk_free} GB < ${size_gb} + 5 GB headroom" >&2
        return 1
    fi

    echo "Creating ${size_gb} GB swapfile at ${path}..."
    fallocate -l "${size_gb}G" "$path"
    chmod 600 "$path"
    mkswap "$path"
    swapon "$path"

    echo
    echo "Verifying..."
    swapon --show
    echo
    echo "Persistent across reboots: add to /etc/fstab:"
    echo "  ${path}  none  swap  sw  0  0"
    echo
    echo "(Currently active in this boot only.)"
}

# ---- Subcommand: remove -------------------------------------------------

cmd_remove() {
    local path="${1:?usage: check_swap.sh remove PATH}"

    if [[ "$EUID" -ne 0 ]]; then
        echo "ERROR: must run as root (sudo)" >&2
        return 1
    fi

    if [[ ! -e "$path" ]]; then
        echo "ERROR: $path does not exist" >&2
        return 1
    fi

    echo "Deactivating ${path}..."
    swapoff "$path"
    rm "$path"
    echo "Removed."
    echo
    echo "If you added it to /etc/fstab, remove that line too."
}

# ---- Subcommand: help ---------------------------------------------------

cmd_help() {
    sed -n '/^# Usage:/,/^# ---- Helpers/p' "$0" | sed 's/^# \{0,1\}//' | head -n -2
}

# ---- Dispatch -----------------------------------------------------------
cmd="${1:-status}"
shift || true
case "$cmd" in
    status) cmd_status ;;
    recommend) cmd_recommend "$@" ;;
    add) cmd_add "$@" ;;
    remove) cmd_remove "$@" ;;
    help|--help|-h) cmd_help ;;
    *) echo "unknown subcommand: $cmd"; cmd_help; exit 2 ;;
esac
