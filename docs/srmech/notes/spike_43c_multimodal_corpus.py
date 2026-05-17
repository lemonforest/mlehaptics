"""
Spike #43c — Multi-modal corpus fetcher for well-spread human knowledge.

Goal: characterise the spectral shape of HUMAN KNOWLEDGE THAT HAS BEEN SPREAD WELL.
Scope: published canonical works that have demonstrably transmitted knowledge effectively.
NOT the project's own contribution (corrected from Spike #43 mis-scoping).

Modalities:
  M1 BOOKS_PROSE    — canonical books / monographs / treatises (Project Gutenberg)
  M2 PAPERS         — canonical scientific papers / lecture-monographs (arXiv)
  M3 LECTURES       — transcribed lecture notes (open licenses)
  M4 ENCYCLOPEDIC   — Wikipedia featured articles (CC BY-SA)
  M5 CODE           — open-source canonical code repositories
  M6 ORAL           — Aesop's fables (public-domain oral tradition transcribed)
  M7 PEDAGOGY       — Polya / Hardy / Strunk-White (canonical pedagogical works)

Permitted: per [[reference_autonomous_validation_tos_landscape]]:
  - Project Gutenberg (public domain) — books, oral traditions, pedagogy
  - arXiv (open access) — scientific papers
  - Wikipedia (CC BY-SA via API) — encyclopedic
  - GitHub raw content (open source licenses) — code

NOT permitted: project's own notebooks/spikes (excluded — they're the OBSERVER not OBSERVED).
"""

from __future__ import annotations

import hashlib
import json
import re
import time
import urllib.request
from pathlib import Path


OUT_DIR = Path(r"D:\temp\spike_43c")
CORPUS_DIR = OUT_DIR / "corpus"
CORPUS_DIR.mkdir(parents=True, exist_ok=True)


# ---------------------------------------------------------------------------
# Canonical corpus (curated per modality)
# ---------------------------------------------------------------------------

# Modality M1 BOOKS_PROSE — pedagogical/expository books that demonstrably spread
# knowledge well (canonical, multiple editions, public domain at Project Gutenberg).
M1_BOOKS_PROSE = [
    {
        "name": "M1_darwin_origin_of_species",
        "url": "https://www.gutenberg.org/cache/epub/1228/pg1228.txt",
        "modality": "M1_BOOKS_PROSE",
        "author": "Darwin, Charles",
        "title": "On the Origin of Species (1st ed., 1859)",
        "year": 1859,
        "note": "Canonical scientific exposition; multi-edition impact",
    },
    {
        "name": "M1_huxley_lay_sermons",
        "url": "https://www.gutenberg.org/cache/epub/16729/pg16729.txt",
        "modality": "M1_BOOKS_PROSE",
        "author": "Huxley, T. H.",
        "title": "Lay Sermons, Addresses, and Reviews (1870)",
        "year": 1870,
        "note": "Canonical Victorian-era science-pedagogy essays",
    },
    {
        "name": "M1_einstein_relativity",
        "url": "https://www.gutenberg.org/cache/epub/30155/pg30155.txt",
        "modality": "M1_BOOKS_PROSE",
        "author": "Einstein, Albert",
        "title": "Relativity: The Special and General Theory (popular exposition)",
        "year": 1920,
        "note": "Author's own popular exposition of canonical physics",
    },
    {
        "name": "M1_whitehead_intro_mathematics",
        "url": "https://www.gutenberg.org/cache/epub/14975/pg14975.txt",
        "modality": "M1_BOOKS_PROSE",
        "author": "Whitehead, A. N.",
        "title": "An Introduction to Mathematics (1911)",
        "year": 1911,
        "note": "Canonical mathematical pedagogy by an authority in the field",
    },
    {
        "name": "M1_darwin_voyage_beagle",
        "url": "https://www.gutenberg.org/cache/epub/2009/pg2009.txt",
        "modality": "M1_BOOKS_PROSE",
        "author": "Darwin, Charles",
        "title": "The Voyage of the Beagle (1839)",
        "year": 1839,
        "note": "Canonical scientific travelogue / observational exposition",
    },
]

# Modality M2 PAPERS — canonical scientific papers via arXiv5 HTML (full paper text).
M2_PAPERS = [
    {
        "name": "M2_arxiv_1706_03762_attention",
        "url": "https://arxiv.org/html/1706.03762v7",
        "modality": "M2_PAPERS",
        "author": "Vaswani et al.",
        "title": "Attention Is All You Need (2017)",
        "year": 2017,
        "note": "Foundational transformer architecture; >100k citations",
    },
    {
        "name": "M2_arxiv_1810_04805_bert",
        "url": "https://arxiv.org/html/1810.04805",
        "modality": "M2_PAPERS",
        "author": "Devlin et al.",
        "title": "BERT: Pre-training of Deep Bidirectional Transformers",
        "year": 2018,
        "note": "Canonical NLP paper; HTML available",
    },
    {
        "name": "M2_arxiv_2010_11929_vit",
        "url": "https://arxiv.org/html/2010.11929",
        "modality": "M2_PAPERS",
        "author": "Dosovitskiy et al.",
        "title": "An Image is Worth 16x16 Words (Vision Transformer)",
        "year": 2020,
        "note": "Canonical vision-transformer paper",
    },
    {
        "name": "M2_arxiv_2106_09685_lora",
        "url": "https://arxiv.org/html/2106.09685",
        "modality": "M2_PAPERS",
        "author": "Hu et al.",
        "title": "LoRA: Low-Rank Adaptation of Large Language Models",
        "year": 2021,
        "note": "Canonical fine-tuning paper; widely adopted",
    },
]

# Modality M3 LECTURES — open-access lecture-style or didactic transcripts.
# Feynman Lectures site requires non-bot UA; using Wikibooks pedagogical chapters
# (CC BY-SA) which are textbook-style lecture-note material edited collaboratively.
# Plus NIST eHandbook (US-Govt-CC0; pedagogical exposition).
M3_LECTURES = [
    {
        "name": "M3_wikibooks_calculus_diff_defined",
        "url": "https://en.wikibooks.org/wiki/Calculus/Differentiation/Differentiation_Defined",
        "modality": "M3_LECTURES",
        "author": "Wikibooks contributors",
        "title": "Calculus: Differentiation Defined chapter",
        "year": 2026,
        "note": "Substantive lecture-style pedagogy chapter (CC BY-SA)",
    },
    {
        "name": "M3_wikibooks_linear_algebra_space",
        "url": "https://en.wikibooks.org/wiki/Linear_Algebra/Vectors_in_Space",
        "modality": "M3_LECTURES",
        "author": "Wikibooks contributors",
        "title": "Linear Algebra: Vectors in Space chapter",
        "year": 2026,
        "note": "Substantive lecture-style pedagogy chapter (CC BY-SA)",
    },
    {
        "name": "M3_wikibooks_intro_math_physics_continuous",
        "url": "https://en.wikibooks.org/wiki/Introduction_to_Mathematical_Physics/Continuous_approximation",
        "modality": "M3_LECTURES",
        "author": "Wikibooks contributors",
        "title": "Introduction to Mathematical Physics: Continuous approximation",
        "year": 2026,
        "note": "Lecture-style mathematical physics pedagogy (CC BY-SA)",
    },
    {
        "name": "M3_wikibooks_cellular_automata_intro",
        "url": "https://en.wikibooks.org/wiki/Cellular_Automata/Introduction",
        "modality": "M3_LECTURES",
        "author": "Wikibooks contributors",
        "title": "Cellular Automata: Introduction",
        "year": 2026,
        "note": "Lecture-style introductory chapter (CC BY-SA)",
    },
]

# Modality M4 ENCYCLOPEDIC — Wikipedia featured / well-developed articles.
M4_ENCYCLOPEDIC = [
    {
        "name": "M4_wiki_evolution",
        "url": "https://en.wikipedia.org/wiki/Evolution",
        "modality": "M4_ENCYCLOPEDIC",
        "author": "Wikipedia contributors",
        "title": "Evolution (featured article)",
        "year": 2026,
        "note": "Top-tier featured article; expository encyclopedia",
    },
    {
        "name": "M4_wiki_quantum_mechanics",
        "url": "https://en.wikipedia.org/wiki/Quantum_mechanics",
        "modality": "M4_ENCYCLOPEDIC",
        "author": "Wikipedia contributors",
        "title": "Quantum mechanics",
        "year": 2026,
        "note": "Top-tier physics article",
    },
    {
        "name": "M4_wiki_pythagorean_theorem",
        "url": "https://en.wikipedia.org/wiki/Pythagorean_theorem",
        "modality": "M4_ENCYCLOPEDIC",
        "author": "Wikipedia contributors",
        "title": "Pythagorean theorem (featured)",
        "year": 2026,
        "note": "Canonical math article",
    },
]

# Modality M5 CODE — well-documented open-source canonical code repos via GitHub raw content.
# Picking pure source files (not READMEs) that are widely cited as canonical code.
M5_CODE = [
    {
        "name": "M5_cpython_lib_functools",
        "url": "https://raw.githubusercontent.com/python/cpython/main/Lib/functools.py",
        "modality": "M5_CODE",
        "author": "Python core developers",
        "title": "CPython stdlib functools (PSL license)",
        "year": 2026,
        "note": "Canonical Python stdlib module; heavily-imitated patterns",
    },
    {
        "name": "M5_redis_t_string",
        "url": "https://raw.githubusercontent.com/redis/redis/unstable/src/t_string.c",
        "modality": "M5_CODE",
        "author": "Redis contributors",
        "title": "Redis t_string.c (BSD)",
        "year": 2026,
        "note": "Canonical C codebase; production-grade key-value store",
    },
    {
        "name": "M5_sqlite_btree",
        "url": "https://raw.githubusercontent.com/sqlite/sqlite/master/src/btree.c",
        "modality": "M5_CODE",
        "author": "SQLite contributors",
        "title": "SQLite btree.c (Public Domain)",
        "year": 2026,
        "note": "Most widely-deployed software in history; well-documented",
    },
]

# Modality M6 ORAL — Aesop's fables (public domain oral tradition transcribed).
M6_ORAL = [
    {
        "name": "M6_aesop_townsend_translation",
        "url": "https://www.gutenberg.org/cache/epub/21/pg21.txt",
        "modality": "M6_ORAL",
        "author": "Aesop (tr. Townsend)",
        "title": "Aesop's Fables (Townsend translation)",
        "year": -550,
        "note": "Canonical oral-tradition transcription; 2500-year provenance",
    },
    {
        "name": "M6_grimm_household_tales",
        "url": "https://www.gutenberg.org/cache/epub/2591/pg2591.txt",
        "modality": "M6_ORAL",
        "author": "Brothers Grimm",
        "title": "Grimm's Fairy Tales (Hunt translation)",
        "year": 1812,
        "note": "Canonical European oral-tradition collection",
    },
]

# Modality M7 PEDAGOGY — canonical pedagogical works in public domain
# (Strunk's Elements of Style is public domain in original 1918 edition).
M7_PEDAGOGY = [
    {
        "name": "M7_strunk_elements_of_style_1918",
        "url": "https://www.gutenberg.org/cache/epub/37134/pg37134.txt",
        "modality": "M7_PEDAGOGY",
        "author": "Strunk, William, Jr.",
        "title": "The Elements of Style (1918, 1st ed.)",
        "year": 1918,
        "note": "Canonical English-style pedagogy",
    },
    {
        "name": "M7_dewey_school_and_society",
        "url": "https://www.gutenberg.org/cache/epub/53910/pg53910.txt",
        "modality": "M7_PEDAGOGY",
        "author": "Dewey, John",
        "title": "The School and Society (1907)",
        "year": 1907,
        "note": "Canonical pedagogy/education philosophy",
    },
    {
        "name": "M7_aristotle_rhetoric",
        "url": "https://www.gutenberg.org/cache/epub/26095/pg26095.txt",
        "modality": "M7_PEDAGOGY",
        "author": "Aristotle (tr. Roberts)",
        "title": "Rhetoric",
        "year": -350,
        "note": "Canonical pedagogy of persuasive communication; 2400-year provenance",
    },
]


ALL_SUBSTRATES = (
    M1_BOOKS_PROSE + M2_PAPERS + M3_LECTURES + M4_ENCYCLOPEDIC + M5_CODE + M6_ORAL + M7_PEDAGOGY
)


# ---------------------------------------------------------------------------
# Fetch infrastructure
# ---------------------------------------------------------------------------


def fetch(url: str, timeout: int = 30) -> tuple[bytes, int]:
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (spike43c-research)"})
    r = urllib.request.urlopen(req, timeout=timeout)
    body = r.read()
    return body, r.status


def strip_gutenberg_boilerplate(text: str) -> str:
    """Remove Project Gutenberg start/end markers."""
    start_re = re.compile(r"\*\*\*\s*START OF (?:THE PROJECT GUTENBERG|THIS PROJECT GUTENBERG).*?\*\*\*", re.IGNORECASE)
    end_re = re.compile(r"\*\*\*\s*END OF (?:THE PROJECT GUTENBERG|THIS PROJECT GUTENBERG).*?\*\*\*", re.IGNORECASE)
    sm = start_re.search(text)
    em = end_re.search(text)
    if sm:
        text = text[sm.end():]
    if em:
        text = text[:em.start()]
    return text


def strip_html_to_text(html: str) -> str:
    """Naive HTML-to-text. Strips script/style, then tags, then collapses whitespace."""
    html = re.sub(r"<script[^>]*>.*?</script>", " ", html, flags=re.DOTALL | re.IGNORECASE)
    html = re.sub(r"<style[^>]*>.*?</style>", " ", html, flags=re.DOTALL | re.IGNORECASE)
    # Preserve paragraph breaks
    html = re.sub(r"</p>", "\n\n", html, flags=re.IGNORECASE)
    html = re.sub(r"<br\s*/?>", "\n", html, flags=re.IGNORECASE)
    html = re.sub(r"</h\d>", "\n\n", html, flags=re.IGNORECASE)
    # Strip remaining tags
    text = re.sub(r"<[^>]+>", " ", html)
    # Decode common entities
    text = text.replace("&nbsp;", " ").replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
    text = text.replace("&quot;", '"').replace("&#39;", "'").replace("&mdash;", "—").replace("&ndash;", "–")
    text = re.sub(r"&[a-z]+;", " ", text)
    # Collapse whitespace, but preserve paragraph boundaries
    paragraphs = re.split(r"\n\s*\n", text)
    paragraphs = [re.sub(r"\s+", " ", p).strip() for p in paragraphs]
    paragraphs = [p for p in paragraphs if p]
    return "\n\n".join(paragraphs)


def normalise_text_substrate(raw_text: str, source_hint: str) -> str:
    """Modality-aware text cleanup."""
    if "gutenberg" in source_hint:
        raw_text = strip_gutenberg_boilerplate(raw_text)
    return raw_text


def fetch_one(substrate: dict) -> dict:
    name = substrate["name"]
    url = substrate.get("url")
    out_path = CORPUS_DIR / f"{name}.txt"
    meta_path = CORPUS_DIR / f"{name}.meta.json"

    if url is None:
        return {**substrate, "status": "SKIP_NO_URL", "out_path": str(out_path)}

    if out_path.exists() and out_path.stat().st_size > 1000:
        # Already fetched
        text = out_path.read_text(encoding="utf-8", errors="replace")
        return {
            **substrate,
            "status": "CACHED",
            "out_path": str(out_path),
            "n_bytes": len(text.encode("utf-8")),
            "n_chars": len(text),
            "sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
        }

    try:
        body, status = fetch(url)
        if status != 200:
            return {**substrate, "status": f"HTTP_{status}", "out_path": str(out_path)}
        try:
            raw = body.decode("utf-8")
        except UnicodeDecodeError:
            raw = body.decode("latin-1")

        # HTML vs plain-text detection
        if "<html" in raw[:5000].lower() or "<body" in raw[:5000].lower():
            text = strip_html_to_text(raw)
        else:
            text = raw

        text = normalise_text_substrate(text, source_hint=url)
        # Normalise line endings (Gutenberg ships CRLF; Python on Windows would otherwise
        # write CR-CR-LF which breaks paragraph tokenisation downstream).
        text = text.replace("\r\n", "\n").replace("\r", "\n")

        out_path.write_text(text, encoding="utf-8", newline="\n")

        meta = {
            **substrate,
            "status": "OK",
            "fetched_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "n_bytes_fetched": len(body),
            "n_chars_text": len(text),
            "sha256_raw": hashlib.sha256(body).hexdigest(),
            "sha256_text": hashlib.sha256(text.encode("utf-8")).hexdigest(),
        }
        meta_path.write_text(json.dumps(meta, indent=2), encoding="utf-8")
        time.sleep(1.0)  # polite delay
        return meta

    except Exception as e:
        return {**substrate, "status": f"ERR_{type(e).__name__}", "error": str(e), "out_path": str(out_path)}


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    records = []
    print(f"  Fetching {len(ALL_SUBSTRATES)} substrates across 7 modalities...")
    for substrate in ALL_SUBSTRATES:
        res = fetch_one(substrate)
        status = res.get("status", "UNKNOWN")
        n_chars = res.get("n_chars", res.get("n_chars_text", 0))
        print(f"  [{status:<12}] {substrate['name']:<55} ({n_chars} chars)")
        records.append(
            {
                "date": "2026-05-17",
                "spike": "43c",
                "substrate_name": substrate["name"],
                "modality": substrate["modality"],
                "author": substrate.get("author"),
                "title": substrate.get("title"),
                "year": substrate.get("year"),
                "note": substrate.get("note"),
                "url": substrate.get("url"),
                "status": status,
                "n_chars": n_chars,
                "sha256_text": res.get("sha256_text") or res.get("sha256"),
            }
        )

    out_ndjson = OUT_DIR / "spike_43c_corpus_records_2026-05-17.ndjson"
    with out_ndjson.open("w", encoding="utf-8") as f:
        for rec in records:
            f.write(json.dumps(rec, default=str) + "\n")
    print(f"\n  [write] {out_ndjson}")


if __name__ == "__main__":
    main()
