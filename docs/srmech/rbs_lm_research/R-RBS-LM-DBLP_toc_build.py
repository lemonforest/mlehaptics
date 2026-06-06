"""R-RBS-LM-DBLP — build an ATTESTED table-of-contents of peer-reviewed items
from the LOCAL dblp dump (F446 pilot; the AMSC/MPM-shape-of-a-bulk-dump insight).

Pipeline (parallel to R-RBS-LM-WIKI_extract):
  1. ANCHOR  — read dblp.xml.gz once; compute our SHA-256 (Class-A content anchor,
     via srmech.amsc.format.sha256_bytes) AND MD5 to cross-check the publisher
     dblp.xml.gz.md5 (re-verifiable attestation). MD5 here is ONLY for matching the
     publisher's own checksum format — it is not a cascade primitive; the Class-A
     anchor is the SHA-256.
  2. PARSE   — stream gzip + ElementTree XMLPullParser, root-cleared for bounded
     memory (scales to OpenAlex). dblp's DTD named entities (&uuml; &eacute; …) are
     substituted to their chars from html.entities BEFORE expat sees them, so no
     external-DTD load is needed (the classic dblp-parse gotcha, dependency-free).
  3. EMIT    — an NDJSON catalog (Class-E), one work per line keyed by the dblp key
     + DOI (both content-addresses, Class-A), plus an MPR attestation header.

  /tmp/verify_srmech_071_sci/bin/python R-RBS-LM-DBLP_toc_build.py \
    --dump /home/skirklan/corpora/dblp/dblp.xml.gz \
    --md5  /home/skirklan/corpora/dblp/dblp.xml.gz.md5 \
    --out  /home/skirklan/corpora/dblp
"""

import argparse
import gzip
import hashlib
import html.entities
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from xml.etree.ElementTree import XMLPullParser

import srmech
from srmech.amsc.format import sha256_bytes

RECORD_TAGS = {"article", "inproceedings", "proceedings", "book", "incollection",
               "phdthesis", "mastersthesis", "www", "data"}
KEEP_RAW = {"amp", "lt", "gt", "quot", "apos"}      # leave for expat
_ENTITY = {n: c for n, c in html.entities.entitydefs.items()}   # name -> char
_ENT_RE = re.compile(r"&([A-Za-z][A-Za-z0-9]*);")
_DOI_RE = re.compile(r"(?:https?://(?:dx\.)?doi\.org/|doi:)(10\.\d{4,9}/\S+)", re.I)


def subst_entities(line):
    def repl(m):
        name = m.group(1)
        if name in KEEP_RAW:
            return m.group(0)
        ch = _ENTITY.get(name)
        return ch if ch is not None else m.group(0)
    return _ENT_RE.sub(repl, line)


def anchor(dump_path, md5_path):
    data = Path(dump_path).read_bytes()
    our_sha256 = sha256_bytes(data)                 # Class-A content anchor
    our_md5 = hashlib.md5(data).hexdigest()         # publisher-format cross-check only
    pub_md5 = None
    verified = None
    if md5_path and Path(md5_path).exists():
        txt = Path(md5_path).read_text().strip()
        # dblp .md5 format: "<hex>  dblp.xml.gz"
        pub_md5 = txt.split()[0] if txt else None
        verified = (pub_md5 is not None and pub_md5.lower() == our_md5.lower())
    return {
        "response_sha256": our_sha256, "our_md5": our_md5,
        "publisher_md5": pub_md5, "publisher_md5_verified": verified,
        "dump_bytes": len(data),
    }


def doi_from_ee(ee_text):
    if not ee_text:
        return None
    m = _DOI_RE.search(ee_text)
    return m.group(1) if m else None


def localname(tag):
    return tag.rsplit("}", 1)[-1]


def parse_toc(dump_path, out_ndjson, max_records=0, log_every=500000):
    parser = XMLPullParser(events=("start", "end"))
    root = None
    n = 0
    by_type = {}
    with_doi = 0
    with gzip.open(dump_path, "rt", encoding="ISO-8859-1") as fh, \
         open(out_ndjson, "w", encoding="utf-8") as out:
        for raw in fh:
            parser.feed(subst_entities(raw))
            for event, elem in parser.read_events():
                tag = localname(elem.tag)
                if event == "start":
                    if root is None:
                        root = elem
                    continue
                if tag not in RECORD_TAGS:
                    continue
                # a record ended — extract fields
                authors = [a.text for a in elem.findall("author") if a.text]
                title_el = elem.find("title")
                title = "".join(title_el.itertext()).strip() if title_el is not None else None
                year_el = elem.find("year")
                year = year_el.text if year_el is not None else None
                venue = None
                for vtag in ("journal", "booktitle"):
                    v = elem.find(vtag)
                    if v is not None and v.text:
                        venue = v.text
                        break
                doi = None
                for ee in elem.findall("ee"):
                    doi = doi_from_ee(ee.text)
                    if doi:
                        break
                rec = {"key": elem.get("key"), "type": tag, "title": title,
                       "authors": authors, "year": year, "venue": venue, "doi": doi}
                out.write(json.dumps(rec, ensure_ascii=False) + "\n")
                n += 1
                by_type[tag] = by_type.get(tag, 0) + 1
                if doi:
                    with_doi += 1
                elem.clear()
                if root is not None:
                    root.clear()
                if n % log_every == 0:
                    print(f"  ...{n:,} records  (with-DOI {with_doi:,})")
                if max_records and n >= max_records:
                    return n, by_type, with_doi
    return n, by_type, with_doi


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dump", required=True)
    ap.add_argument("--md5", default=None)
    ap.add_argument("--out", required=True, help="output dir")
    ap.add_argument("--max-records", type=int, default=0, help="0 = all")
    ap.add_argument("--retrieved-at", default=None, help="ISO8601; default = file mtime")
    args = ap.parse_args()

    outdir = Path(args.out)
    outdir.mkdir(parents=True, exist_ok=True)
    print(f"=== R-RBS-LM-DBLP attested TOC  (srmech {srmech.__version__}) ===")

    print("  [1/3] anchoring dump (SHA-256 Class-A + publisher-MD5 cross-check)…")
    att = anchor(args.dump, args.md5)
    print(f"      bytes={att['dump_bytes']:,}  sha256={att['response_sha256'][:16]}…  "
          f"md5_verified={att['publisher_md5_verified']}")

    retrieved = args.retrieved_at or datetime.fromtimestamp(
        Path(args.dump).stat().st_mtime, tz=timezone.utc).isoformat()

    ndjson = outdir / "dblp_toc.ndjson"
    print(f"  [2/3] parsing → {ndjson.name} …")
    n, by_type, with_doi = parse_toc(args.dump, ndjson, args.max_records)

    mpr = {
        "mpr_version": "1.0",
        "data_schema_id": "dblp://toc/v1",
        "attestation": {
            "source_url": "https://dblp.org/xml/dblp.xml.gz",
            "license": "CC0-1.0 (primary); ODC-BY-1.0 (secondary)",
            "retrieved_at": retrieved,
            "response_sha256": att["response_sha256"],
            "publisher_md5": att["publisher_md5"],
            "publisher_md5_verified": att["publisher_md5_verified"],
            "dump_bytes": att["dump_bytes"],
            "parser_version": f"R-RBS-LM-DBLP / srmech {srmech.__version__}",
        },
        "rendering": {"name": "dblp attested TOC (peer-reviewed CS bibliography)",
                      "purpose": "local hash-checked citation index (F446)",
                      "cite_as": "dblp computer science bibliography, dblp.org, CC0 1.0"},
        "summary": {"n_records": n, "with_doi": with_doi,
                    "with_doi_fraction": round(with_doi / n, 4) if n else 0.0,
                    "by_type": by_type},
    }
    att_path = outdir / "dblp_toc.attestation.json"
    att_path.write_text(json.dumps(mpr, indent=2))
    print(f"  [3/3] attestation → {att_path.name}")
    print(f"\n  records={n:,}  with-DOI={with_doi:,} ({mpr['summary']['with_doi_fraction']:.1%})  "
          f"md5_verified={att['publisher_md5_verified']}")
    print(f"  by_type={by_type}")
    print(f"  TOC: {ndjson}  ({ndjson.stat().st_size:,} bytes)")


if __name__ == "__main__":
    main()
