"""Ephemeris Bridge for de441-spectral.

Provides secure downloading of JPL DE441 kernels and exposure to the HDC engine.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Optional

# This script lives in docs/antikythera-maths/de441-spectral/bridge/
_THIS = Path(__file__).resolve()
_RESEARCH = _THIS.parents[2] / "research"
sys.path.insert(0, str(_RESEARCH))

from ephemeris_loader import KERNEL_CATALOG, KernelSpec, download_kernel

# Explicitly add DE441 to the catalog
if "de441" not in KERNEL_CATALOG:
    KERNEL_CATALOG["de441"] = KernelSpec(
        name="de441",
        filename="de441.bsp",
        coverage_jd=(2316524.5, 2715456.5), # 1550 to 2650
        coverage_iso=("+1550-01-01", "+2650-01-25"),
        size_mb=3300,
        description="JPL DE441: High-precision planetary ephemeris (3.3 GB)."
    )

def main():
    import argparse
    p = argparse.ArgumentParser(description="Download JPL DE-series kernels.")
    p.add_argument("--kernel", default="de441", choices=sorted(KERNEL_CATALOG.keys()))
    p.add_argument("--dest", help="Destination directory for .bsp files.")
    
    args = p.parse_args()
    
    dest = args.dest or os.environ.get("SKYFIELD_DATA") or "."
    print(f"Downloading {args.kernel} to {dest}...")
    
    path = download_kernel(args.kernel, data_dir=dest)
    if path:
        print(f"Success: {path}")
    else:
        print("Download failed or aborted.")

if __name__ == "__main__":
    main()
