"""R-RBS-LM-22 — Storage management + check-before-fetch tooling.

Three small utilities for safe disk management on the 2009 Xeon E5530 hardware
(98 GB total disk; often at 90%+ used due to other long-running projects):

  disk_summary()         — read-only report of disk + research artefact sizes
  cleanup_caches()       — removes regenerable caches (vocab_table.npy first;
                           optional HF model caches by name)
  precheck_fetch(...)    — verifies free disk >= estimated_bytes + safety_margin
                           before any HF model download or large file fetch

Per user direction 2026-05-25: *"we will need to remove dense LLMs when we don't
need them anymore and we will need to check our storage space before fetching."*

Future-upstream as srmech.amsc.storage per R-RBS-LM-12 §6 (the srmech-fix
session that lands the v0.5.0rc release will move this into the package).

Usage:
    # Read-only summary
    python docs/srmech/rbs_lm_research/storage_management.py

    # Cleanup regenerable caches
    python docs/srmech/rbs_lm_research/storage_management.py --cleanup

    # Cleanup including HF model cache for gpt2
    python docs/srmech/rbs_lm_research/storage_management.py --cleanup --hf-model gpt2

    # Programmatic — call before fetching a HF model:
    from storage_management import precheck_fetch
    precheck_fetch(estimated_bytes=500 * 1024**2, safety_margin_gb=1.0)
"""

import argparse
import shutil
from pathlib import Path


# Paths managed by this module
RESEARCH_DIR = Path("docs/srmech/rbs_lm_research")
VOCAB_TABLE_PATH = RESEARCH_DIR / "vocab_table.npy"
HF_CACHE_DIR = Path.home() / ".cache" / "huggingface"
VENV_DIR = Path.home() / ".venvs" / "rbs-lm-research"


def _dir_size(path):
    """Sum size of all regular files under path; 0 if path doesn't exist."""
    if not path.exists():
        return 0
    if path.is_file():
        return path.stat().st_size
    total = 0
    for p in path.rglob("*"):
        try:
            if p.is_file() and not p.is_symlink():
                total += p.stat().st_size
        except (OSError, PermissionError):
            pass
    return total


def _gb(n_bytes):
    return n_bytes / 1024**3


def _mb(n_bytes):
    return n_bytes / 1024**2


def disk_summary(verbose=True):
    """Print disk usage + research artefact sizes. Returns dict of measured sizes."""
    usage = shutil.disk_usage("/")
    pct_used = 100 * usage.used / usage.total

    artefacts = {
        "vocab_table_npy": _dir_size(VOCAB_TABLE_PATH),
        "research_subtree": _dir_size(RESEARCH_DIR),
        "hf_cache": _dir_size(HF_CACHE_DIR),
        "venv": _dir_size(VENV_DIR),
    }

    instruments = sorted(RESEARCH_DIR.glob("rbs_lm_instrument_*.bin")) + \
                  sorted(RESEARCH_DIR.glob("rbs_lm_instrument_*.npy"))
    instruments_size = sum(p.stat().st_size for p in instruments)

    if verbose:
        print(f"=== Disk status ===")
        print(f"  /: {_gb(usage.used):.1f} GB used / {_gb(usage.total):.1f} GB total "
              f"({_gb(usage.free):.2f} GB free; {pct_used:.0f}% used)")
        if pct_used >= 95:
            print(f"  ⚠️  CRITICAL: disk >= 95% used — running fetch operations may fail")
        elif pct_used >= 85:
            print(f"  ⚠️  WARNING: disk >= 85% used — consider cleanup before fetching")
        print()
        print(f"=== Research artefacts ===")
        print(f"  vocab_table.npy:  {_mb(artefacts['vocab_table_npy']):.1f} MB  "
              f"(regenerable in ~4s; gitignored)")
        print(f"  rbs_lm_research/: {_mb(artefacts['research_subtree']):.1f} MB total "
              f"(includes the vocab table)")
        print(f"  committed instruments ({len(instruments)} files): "
              f"{_mb(instruments_size):.1f} MB")
        print()
        print(f"=== Caches ===")
        print(f"  HF cache:         {_mb(artefacts['hf_cache']):.1f} MB "
              f"(re-downloadable from HuggingFace)")
        print(f"  venv (rbs-lm):    {_mb(artefacts['venv']):.1f} MB "
              f"(keep — needed for our scripts)")

    return {
        "disk_total_bytes": usage.total,
        "disk_used_bytes": usage.used,
        "disk_free_bytes": usage.free,
        "disk_pct_used": pct_used,
        "artefacts": artefacts,
        "instruments_size_bytes": instruments_size,
        "n_instruments": len(instruments),
    }


def cleanup_caches(remove_vocab_table=True, hf_models=None, verbose=True):
    """Remove regenerable caches; report what was freed.

    Args:
        remove_vocab_table: delete vocab_table.npy (regenerable in ~4s)
        hf_models: list of HF model names to remove from cache; None to skip
                   (gpt2 → ~526 MB; deletion forces re-download next use)

    Returns: total bytes freed.
    """
    total_freed = 0

    if remove_vocab_table and VOCAB_TABLE_PATH.exists():
        size = VOCAB_TABLE_PATH.stat().st_size
        VOCAB_TABLE_PATH.unlink()
        total_freed += size
        if verbose:
            print(f"  removed {VOCAB_TABLE_PATH.name}: {_mb(size):.1f} MB freed")

    if hf_models:
        for model_name in hf_models:
            # HF cache uses a sanitized name pattern: models--{user}--{name}
            # For "gpt2" (no user prefix), it's models--gpt2
            cache_pattern = f"models--{model_name.replace('/', '--')}"
            model_dir = HF_CACHE_DIR / "hub" / cache_pattern
            if model_dir.exists():
                size = _dir_size(model_dir)
                shutil.rmtree(model_dir)
                total_freed += size
                if verbose:
                    print(f"  removed HF cache {cache_pattern}: {_mb(size):.1f} MB freed")
            else:
                if verbose:
                    print(f"  HF cache {cache_pattern} not found (already clean?)")

    if verbose:
        print(f"\n  TOTAL FREED: {_mb(total_freed):.1f} MB ({_gb(total_freed):.2f} GB)")
    return total_freed


def precheck_fetch(estimated_bytes, safety_margin_gb=1.0, label=""):
    """Verify enough disk space before a fetch operation.

    Raises StorageInsufficientError if free < estimated + safety_margin.
    Otherwise returns dict with the precheck measurements.

    Args:
        estimated_bytes: expected fetch size (e.g., from huggingface_hub
                        model_info().siblings[].size sum, or hardcoded estimate)
        safety_margin_gb: extra headroom required beyond the fetch (default 1 GB)
        label: short string for error/log messages (e.g., "gpt2 model fetch")

    Returns: dict with disk_free_bytes, estimated_bytes, safety_margin_bytes,
             headroom_after_fetch_bytes.
    """
    usage = shutil.disk_usage("/")
    free = usage.free
    safety_margin = int(safety_margin_gb * 1024**3)
    needed = estimated_bytes + safety_margin

    if free < needed:
        raise StorageInsufficientError(
            f"precheck_fetch[{label}]: free={_mb(free):.1f} MB; "
            f"need={_mb(needed):.1f} MB (est={_mb(estimated_bytes):.1f} MB "
            f"+ margin={_gb(safety_margin):.1f} GB)"
        )

    return {
        "disk_free_bytes": free,
        "estimated_bytes": estimated_bytes,
        "safety_margin_bytes": safety_margin,
        "headroom_after_fetch_bytes": free - needed,
    }


class StorageInsufficientError(RuntimeError):
    """Raised by precheck_fetch when disk space is insufficient."""


def _cli():
    parser = argparse.ArgumentParser(description="R-RBS-LM-22 storage tooling")
    parser.add_argument("--cleanup", action="store_true",
                        help="Remove regenerable caches (vocab_table.npy by default)")
    parser.add_argument("--hf-model", action="append", default=[],
                        help="HF model name to remove from cache (can repeat)")
    parser.add_argument("--no-vocab-cleanup", action="store_true",
                        help="Skip vocab_table.npy removal when --cleanup is given")
    args = parser.parse_args()

    summary = disk_summary(verbose=True)

    if args.cleanup:
        print()
        print(f"=== Cleanup ===")
        cleanup_caches(
            remove_vocab_table=not args.no_vocab_cleanup,
            hf_models=args.hf_model,
            verbose=True,
        )
        print()
        print(f"=== Disk status after cleanup ===")
        disk_summary(verbose=True)


if __name__ == "__main__":
    _cli()
