#!/usr/bin/env python3
"""Provenance: fetch the multi-script evaluation corpus + the UCD tables.

Every number in `glyph_stream_tokenizer_design.md` derives from what this
script fetches. Re-run it to reproduce the inputs; the sha256 of each UCD file
is recorded in `glyph_stream_tokenizer_design.ndjson` (kind="attestation").

Corpus  : per-language Wikipedia plain-text extracts (CC-BY-SA 4.0), one
          well-known article per language, via the MediaWiki action API.
          Chosen for REAL prose in each script — not hand-written toy strings.
UCD     : Unicode 16.0.0 auxiliary + emoji + derived-core property files,
          the ground truth for UAX #29 extended grapheme clusters.

Usage: python3 glyph_stream_tokenizer_fetch_corpus_script.py <out_dir>
Writes <out_dir>/wiki/*.txt and <out_dir>/ucd/*.txt.

Note: the MediaWiki API rate-limits; this script paces itself and retries.
No external libraries.
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
import time
import urllib.parse
import urllib.request

UA = "srmech-research/0.9 (glyph-stream tokenizer design spike)"

# (wiki code, article title) — one substantial article per script
LANGS = {
    "en": "Language",       "tr": "Türkiye",     "el": "Γλώσσα",
    "haw": "Hawaiʻi",       "ar": "لغة",          "he": "שפה",
    "hi": "भाषा",            "th": "ภาษา",         "zh": "汉语",
    "ja": "言語",            "ko": "언어",          "bi": "Bislama",
    "ru": "Язык",           "ta": "மொழி",         "bn": "ভাষা",
    "my": "ဘာသာစကား",        "km": "ភាសា",         "lo": "ພາສາ",
}

UCD_BASE = "https://www.unicode.org/Public/16.0.0/ucd"
UCD_FILES = (
    "auxiliary/GraphemeBreakProperty.txt",   # the GBP itself
    "auxiliary/GraphemeBreakTest.txt",       # official conformance suite
    "emoji/emoji-data.txt",                  # Extended_Pictographic (GB11)
    "DerivedCoreProperties.txt",             # InCB (GB9c, Unicode 15.1+)
)


def get(url, timeout=60):
    return urllib.request.urlopen(
        urllib.request.Request(url, headers={"User-Agent": UA}),
        timeout=timeout).read()


def fetch_wiki(out):
    os.makedirs(out, exist_ok=True)
    for code, title in LANGS.items():
        path = os.path.join(out, f"{code}.txt")
        if os.path.exists(path) and os.path.getsize(path) > 3000:
            continue
        q = urllib.parse.quote(title.encode("utf-8"))
        url = (f"https://{code}.wikipedia.org/w/api.php?action=query"
               f"&prop=extracts&explaintext=1&format=json&titles={q}")
        for attempt in range(4):
            try:
                pages = json.loads(get(url, 30))["query"]["pages"]
                txt = next(iter(pages.values())).get("extract", "")
                if len(txt) > 300:
                    with open(path, "w", encoding="utf-8") as fh:
                        fh.write(txt)
                    print(f"  {code:5} {len(txt):7d} chars")
                break
            except Exception as exc:                      # noqa: BLE001
                if attempt == 3:
                    print(f"  {code:5} FAIL {type(exc).__name__}")
                time.sleep(5 * (attempt + 1))
        time.sleep(3)


def fetch_ucd(out):
    os.makedirs(out, exist_ok=True)
    for rel in UCD_FILES:
        name = rel.rsplit("/", 1)[-1]
        path = os.path.join(out, name)
        if not os.path.exists(path):
            with open(path, "wb") as fh:
                fh.write(get(f"{UCD_BASE}/{rel}"))
        with open(path, "rb") as fh:
            blob = fh.read()
        print(f"  {name:32} {len(blob):8d} B  "
              f"sha256={hashlib.sha256(blob).hexdigest()}")


def main():
    root = sys.argv[1]
    print("UCD 16.0.0:")
    fetch_ucd(os.path.join(root, "ucd"))
    print("Wikipedia corpus:")
    fetch_wiki(os.path.join(root, "wiki"))


if __name__ == "__main__":
    main()
