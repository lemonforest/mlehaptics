"""Fetch Wild, Alarcón-Nieto & Aplin (2024) great tit Dryad dataset.

DOI: 10.5061/dryad.x95x69ps8
Tries multiple endpoints. Designed for the Gap #1 Hodge-Laplacian spike
(research/comparative-ethology-age-sociality branch).
"""

from __future__ import annotations

import sys
import time
from pathlib import Path
from urllib import error, request

OUT_DIR = Path(__file__).resolve().parent.parent / "data" / "great_tit_wild_2024"
OUT_DIR.mkdir(parents=True, exist_ok=True)

# Curated file subset for the Hodge-Laplacian spike:
# - Mill.data.{season}.txt : per-season RFID feeder visits (raw)
# - fledgling_data.txt     : fledgling metadata (ages, IDs)
# - species_age.txt        : age-class labels keyed by individual
# - README.md              : column-schema documentation
TARGETS = [
    ("2981852", "README.md"),
    ("2981839", "species_age.txt"),
    ("2981818", "fledgling_data.txt"),
    ("2981843", "Mill.data.summer.txt"),
    ("2981840", "Mill.data.autumn.txt"),
    ("2981842", "Mill.data.winter.txt"),
    ("2981841", "Mill.data.spring.txt"),
]

ENDPOINTS = [
    "https://datadryad.org/downloads/file_stream/{id}",
    "https://datadryad.org/api/v2/files/{id}/download",
]

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": (
        "text/html,application/xhtml+xml,application/xml;q=0.9,"
        "image/avif,image/webp,*/*;q=0.8"
    ),
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://datadryad.org/dataset/doi:10.5061/dryad.x95x69ps8",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "same-origin",
}


def fetch_one(file_id: str, name: str) -> bool:
    out_path = OUT_DIR / name
    for tmpl in ENDPOINTS:
        url = tmpl.format(id=file_id)
        req = request.Request(url, headers=HEADERS)
        try:
            with request.urlopen(req, timeout=120) as resp:
                code = resp.getcode()
                body = resp.read()
                if code == 200 and len(body) > 200:
                    out_path.write_bytes(body)
                    print(f"  OK   {name}  {len(body):>10d}  via {tmpl}")
                    return True
                print(f"  WAIT {name}  code={code} len={len(body)}  via {tmpl}")
        except error.HTTPError as exc:
            print(f"  HTTP {exc.code} {name}  via {tmpl}: {exc.reason}")
        except Exception as exc:  # noqa: BLE001
            print(f"  ERR  {name}: {type(exc).__name__}: {exc}")
        time.sleep(1.0)
    return False


def main() -> int:
    failures = []
    for fid, name in TARGETS:
        ok = fetch_one(fid, name)
        if not ok:
            failures.append(name)
        time.sleep(0.5)
    if failures:
        print(f"FAILED to fetch: {failures}", file=sys.stderr)
        return 2
    print("ALL FETCHED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
