r"""R-RBS-LM-WIKIINGEST (F745) — build an ATTESTED wiki-knowledge chromosome for Siona's genome.

Each article = one MPR row: data={title, key, text(=abstract)}, attestation={source_url, license CC-BY-SA-4.0,
retrieved_at, response_sha256(=sha256 of the abstract), parser_version}. Written as NDJSON OUTSIDE the repo
(~/corpora/wikipedia/wiki_knowledge_kernel.ndjson) — it is the wiki KNOWLEDGE kernel (title->abstract), distinct
from the prior enwiki_kernel_256.json which is a SPECTRAL fingerprint (co-occurrence edges of the top-256 words,
F640) and cannot answer questions.

FIRST CUT: a curated broad batch via the Wikipedia REST summary API (clean per-article attestation, immediate).
SCALE PATH (the "big wiki"): the same MPR row shape, bulk-extracted from enwiki-latest-abstract.xml.gz (title +
abstract, no wikitext parsing) -> millions of rows, sharded; Siona answers via the term-index (Class-E lookup),
never the dense O(vocab^2) etak-walk. This script's row schema IS that scale schema.

Run:  /tmp/srmech_rc149/venv/bin/python3 docs/srmech/rbs_lm_research/R-RBS-LM-WIKIINGEST_...py [N]
No abs(); no CAD; research-subtree scaffold (NOT a package edit). srmech 0.7.5rc149.
"""
import json
import sys
import time
import urllib.request
import urllib.parse
from datetime import datetime, timezone
from pathlib import Path
import srmech
from srmech.amsc.format import sha256_raw, write_ndjson, MPRRecord

OUT = Path.home() / "corpora" / "wikipedia" / "wiki_knowledge_kernel.ndjson"
API = "https://en.wikipedia.org/api/rest_v1/page/summary/"

# curated broad seed — general-knowledge breadth across domains (the first cut; the dump is the scale path)
SEED = [
    # mythology / culture / the dead-end the user hit
    "Dragon", "Griffin", "Phoenix_(mythology)", "Unicorn", "Mythology", "Folklore",
    # animals / biology
    "Lion", "Tiger", "Elephant", "Octopus", "Dolphin", "Whale", "Eagle", "Shark", "Honey_bee",
    "Cell_(biology)", "DNA", "Evolution", "Photosynthesis", "Bacterium", "Virus", "Brain", "Heart", "Immune_system",
    # physics / chemistry / astronomy
    "Gravity", "Light", "Electromagnetism", "Quantum_mechanics", "Atom", "Electron", "Energy", "Thermodynamics",
    "Black_hole", "Star", "Galaxy", "Solar_System", "Sun", "Moon", "Planet", "Big_Bang", "Periodic_table", "Oxygen",
    "Water", "Carbon", "Chemical_element",
    # math / computing
    "Mathematics", "Number", "Prime_number", "Geometry", "Calculus", "Algebra", "Pi", "Infinity", "Logic",
    "Computer", "Algorithm", "Artificial_intelligence", "Internet", "Cryptography", "Information",
    # earth / geography
    "Earth", "Ocean", "Mountain", "Volcano", "Earthquake", "Climate", "Weather", "Continent", "Africa", "Asia",
    "Europe", "Antarctica", "Amazon_rainforest", "Nile", "Mount_Everest",
    # history / society
    "History", "Ancient_Rome", "Ancient_Egypt", "Ancient_Greece", "Renaissance", "Industrial_Revolution",
    "World_War_II", "Democracy", "Philosophy", "Language", "Writing", "Money", "Music", "Art", "Religion",
    # people / fields
    "Albert_Einstein", "Isaac_Newton", "Charles_Darwin", "Leonardo_da_Vinci", "Marie_Curie", "Aristotle",
    # everyday
    "Tree", "Flower", "Fungus", "Bread", "Coffee", "Sleep", "Emotion", "Memory", "Dream",
]


def fetch(title):
    url = API + urllib.parse.quote(title)
    req = urllib.request.Request(url, headers={"accept": "application/json", "user-agent": "siona-wikiingest/0.1"})
    with urllib.request.urlopen(req, timeout=12) as r:
        d = json.loads(r.read().decode())
    extract = (d.get("extract") or "").strip()
    if not extract or d.get("type") == "disambiguation":
        return None
    src = (d.get("content_urls", {}).get("desktop", {}) or {}).get("page") or (API + urllib.parse.quote(title))
    return d.get("title", title), extract, src


def main():
    n = int(sys.argv[1]) if len(sys.argv) > 1 else len(SEED)
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    rows, seen = [], set()
    for i, t in enumerate(SEED[:n]):
        try:
            got = fetch(t)
        except Exception as ex:                                # network/404 — skip, log
            print(f"  skip {t}: {type(ex).__name__}")
            continue
        if not got:
            print(f"  skip {t}: no abstract / disambiguation")
            continue
        title, extract, src = got
        key = title.lower().replace(" ", "_")[:48]
        if key in seen:
            continue
        seen.add(key)
        rows.append(MPRRecord(
            mpr_version="1.0",
            data={"kernel": "wiki", "key": key, "title": title, "text": extract},
            data_schema_id="rbslm://schema/siona_wiki_knowledge/v1",
            attestation={"source_url": src, "license": "CC-BY-SA-4.0", "retrieved_at": now,
                         "response_sha256": sha256_raw(extract.encode()).hex(),
                         "parser_version": f"srmech {srmech.__version__}"},
            rendering={"name": f"wiki:{key}", "purpose": "wiki knowledge kernel", "cite_as": f"Wikipedia: {title}"}))
        print(f"  [{len(rows):3d}] {title}")
        time.sleep(0.12)                                       # be polite to the API
    OUT.parent.mkdir(parents=True, exist_ok=True)
    write_ndjson(OUT, rows)
    print(f"\nwrote {len(rows)} attested wiki articles -> {OUT}")
    print("each row: CC-BY-SA-4.0, source_url + retrieved_at + response_sha256 (per-article provenance).")


if __name__ == "__main__":
    main()
