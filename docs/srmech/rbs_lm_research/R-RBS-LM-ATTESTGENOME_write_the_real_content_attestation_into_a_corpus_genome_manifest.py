r"""R-RBS-LM-ATTESTGENOME (#231/F1239) — write the REAL content attestation into a corpus genome's manifest.json.

`srmech.amsc.genome.genome_save` takes NO attestation argument, so it writes a generic PLACEHOLDER into the
manifest (`license: CC0`, `source_url: srmech.net/genome/persistence`, epoch timestamp) — that attests the
persistence FORMAT, not the CONTENT. An attested genome must point at its real source, exactly like an attested
knowledge kernel does (MPM). This patches the existing manifest's `attestation` + adds a `rendering`/cite block
IN PLACE (no second JSON) — the chromosome table / integrity fields are untouched, so `genome_load` is unaffected.

Defaults are the simplewiki directed co-occurrence genome (CC BY-SA 4.0). Override via env: GENOME, SOURCE_URL,
LICENSE, CITE_AS, RETRIEVED_FROM (a file whose mtime is the honest retrieved_at), COLLECTOR (the build script).

Run:  /tmp/srmech_v/venv/bin/python3 docs/srmech/rbs_lm_research/R-RBS-LM-ATTESTGENOME_...py
"""
import datetime
import json
import os
import sys
from pathlib import Path

from srmech.amsc import format as F

GENOME = Path(os.path.expanduser(os.environ.get("GENOME", str(Path.home() / "corpora" / "wikipedia" / "simplewiki_directed.genome"))))
SOURCE_URL = os.environ.get("SOURCE_URL", "https://dumps.wikimedia.org/simplewiki/")
LICENSE = os.environ.get("LICENSE", "CC-BY-SA-4.0")
CITE_AS = os.environ.get("CITE_AS", "Simple English Wikipedia (directed co-occurrence), CC BY-SA 4.0 — dumps.wikimedia.org/simplewiki")
NAME = os.environ.get("NAME", "Simple English Wikipedia — directed co-occurrence genome")
RETRIEVED_FROM = os.environ.get("RETRIEVED_FROM", str(Path.home() / "corpora" / "wikipedia" / "simplewiki_directed_sparse_kernel.json"))
COLLECTOR = os.environ.get("COLLECTOR", "docs/srmech/rbs_lm_research/R-RBS-LM-SIMPLEWIKIGENOME_build_the_real_body_instrument_as_one_native_genome.py")


def main():
    mp = GENOME / "manifest.json"
    if not mp.exists():
        print("no manifest at %s" % mp, flush=True)
        return 1
    m = json.loads(mp.read_text())
    body_sha = m.get("data", {}).get("body_sha256") or m.get("attestation", {}).get("response_sha256", "")
    csha = F.sha256_bytes(Path(COLLECTOR).read_bytes()) if Path(COLLECTOR).exists() else ""
    rf = Path(os.path.expanduser(RETRIEVED_FROM))
    retrieved = (datetime.datetime.fromtimestamp(rf.stat().st_mtime, datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
                 if rf.exists() else "1970-01-01T00:00:00Z")
    m["attestation"] = {
        "source_doi": "",                                          # a Wikipedia dump has no DOI (honest empty; the URL is the chain)
        "source_url": SOURCE_URL,
        "license": LICENSE,
        "retrieved_at": retrieved,
        "response_sha256": body_sha,                               # the genome body hash (what is served)
        "parser_version": m.get("attestation", {}).get("parser_version", "srmech"),
        "parser_rule_hash": m.get("attestation", {}).get("parser_rule_hash", ""),
        "collector_descriptor_path": COLLECTOR,
        "collector_descriptor_hash": csha,
    }
    m["rendering"] = {"human_readable_name": NAME, "cite_as": CITE_AS,
                      "purpose": "Siona's relational read: the #231 directed Class-L corpus store"}
    mp.write_text(json.dumps(m, indent=2, ensure_ascii=False))
    print("attested %s\n  license=%s  retrieved=%s\n  cite_as=%s" % (GENOME.name, LICENSE, retrieved, CITE_AS), flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
