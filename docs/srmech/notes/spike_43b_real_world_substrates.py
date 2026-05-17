"""
Spike #43b — Real-world mixed-quality substrate ingestion.

User scope clarification 2026-05-17: spectral structure is META-DATA about text,
not trauma-targeting. Analysing imperfect-quality real-world material is legitimate
(knowing the bad shape lets us avoid making it).

Sources permitted per [[reference_autonomous_validation_tos_landscape]]:
  - Wikipedia (CC BY-SA 4.0)
  - Stack Exchange (CC BY-SA 4.0) -- via public api
  - arXiv lecture notes (open access)
  - OpenStax open textbooks (CC BY 4.0)

NO commercial-publisher PDF extraction. NO real-name targeting of individuals
as bad authors per [[feedback_trauma_informed_defensive_scope]]; analysing
material's spectral signature is legitimate (meta-data), naming/blaming
specific authors is not. We tag by source-class, not by author.
"""

from __future__ import annotations

import json
import re
import sys
import time
from pathlib import Path

import requests

OUT_DIR = Path(r"D:\temp\spike_43b\real_world_substrates")
OUT_DIR.mkdir(exist_ok=True, parents=True)


USER_AGENT = "Spike43b-Spectral-MetaAnalysis/1.0 (academic research; mlehaptics project)"


# ------------------------------------------------------------------------
# Wikipedia (using Action API; HTML extract for full article content)
# ------------------------------------------------------------------------


def fetch_wikipedia(title: str) -> str:
    """Fetch Wikipedia article wikitext via Action API, strip wiki markup roughly."""
    url = "https://en.wikipedia.org/w/api.php"
    params = {
        "action": "query",
        "format": "json",
        "titles": title,
        "prop": "extracts",
        "explaintext": "true",
        "exsectionformat": "wiki",
        "redirects": "1",
    }
    r = requests.get(url, params=params, headers={"User-Agent": USER_AGENT}, timeout=30)
    r.raise_for_status()
    data = r.json()
    pages = data["query"]["pages"]
    page = next(iter(pages.values()))
    extract = page.get("extract", "")
    # Convert Wikipedia's "wiki" section format (== heading == / === sub ===) to markdown
    converted_lines: list[str] = []
    for line in extract.split("\n"):
        m = re.match(r"^(=+)\s*(.+?)\s*\1$", line.strip())
        if m:
            lvl = len(m.group(1))
            heading = m.group(2)
            # Top-level Wikipedia section is '== Heading ==' which maps to H2 (##)
            converted_lines.append("#" * lvl + " " + heading)
        else:
            converted_lines.append(line)
    return "\n".join(converted_lines)


WIKIPEDIA_ARTICLES = [
    ("wp_laplacian_matrix", "Laplacian matrix"),
    ("wp_cauchy_distribution", "Cauchy distribution"),
    ("wp_spectral_theorem", "Spectral theorem"),
]


# ------------------------------------------------------------------------
# Stack Exchange API (math.stackexchange) - public, CC BY-SA
# ------------------------------------------------------------------------


def fetch_se_answer(question_id: int, site: str = "math.stackexchange") -> tuple[str, str]:
    """Fetch question + top-voted answer + low-voted answer by question id.

    Returns (high_text, low_text) - both as markdown bodies.
    """
    url = f"https://api.stackexchange.com/2.3/questions/{question_id}"
    params = {
        "site": site,
        "filter": "withbody",
    }
    r = requests.get(url, params=params, headers={"User-Agent": USER_AGENT}, timeout=30)
    r.raise_for_status()
    q_data = r.json()
    items = q_data.get("items", [])
    if not items:
        return "", ""
    q = items[0]
    q_title = q["title"]
    q_body = q.get("body", "")
    # Fetch answers
    a_url = f"https://api.stackexchange.com/2.3/questions/{question_id}/answers"
    a_params = {
        "site": site,
        "filter": "withbody",
        "sort": "votes",
        "order": "desc",
        "pagesize": 30,
    }
    r2 = requests.get(a_url, params=a_params, headers={"User-Agent": USER_AGENT}, timeout=30)
    r2.raise_for_status()
    answers = r2.json().get("items", [])
    if not answers:
        return "", ""
    # High-voted = first (sorted desc); low-voted = last that has any text
    high = answers[0]
    low = answers[-1] if len(answers) > 1 else high

    def html_to_text(html: str) -> str:
        # Strip HTML tags but preserve paragraph breaks; replace block tags with newlines
        s = re.sub(r"</?(p|div|blockquote|h[1-6]|li|ul|ol|pre|code)[^>]*>", "\n\n", html, flags=re.IGNORECASE)
        s = re.sub(r"<[^>]+>", "", s)
        s = re.sub(r"&nbsp;", " ", s)
        s = re.sub(r"&amp;", "&", s)
        s = re.sub(r"&lt;", "<", s)
        s = re.sub(r"&gt;", ">", s)
        s = re.sub(r"&quot;", '"', s)
        s = re.sub(r"&#39;", "'", s)
        # Collapse triple-newlines
        s = re.sub(r"\n{3,}", "\n\n", s)
        return s.strip()

    high_text = (
        f"## Question: {q_title}\n\n{html_to_text(q_body)}\n\n"
        f"## High-voted answer (score {high.get('score', '?')})\n\n{html_to_text(high.get('body', ''))}\n"
    )
    low_text = (
        f"## Question: {q_title}\n\n{html_to_text(q_body)}\n\n"
        f"## Low-voted answer (score {low.get('score', '?')})\n\n{html_to_text(low.get('body', ''))}\n"
    )
    return high_text, low_text


# Selected SE questions: well-known technical topics with multiple answers of varying quality
SE_QUESTIONS = [
    # Linear algebra; well-trodden
    ("se_eigenvalues_intuition", 36815, "math.stackexchange"),  # "what is intuitive meaning of eigenvalues"
    # Probability; foundational (replaced unanswered q119272 with stats.SE q36027)
    ("se_cauchy_no_mean", 36027, "stats.stackexchange"),  # 9 answers; well-known Cauchy mean question
    # Spectral graph theory
    ("se_fiedler_vector", 1287555, "math.stackexchange"),  # Fiedler vector partition
]


# ------------------------------------------------------------------------
# arXiv lecture notes - open access; fetch abstract + intro from HTML page
# ------------------------------------------------------------------------


def fetch_arxiv_abs(arxiv_id: str) -> str:
    """Fetch arXiv abstract page text (NOT the PDF; per scope, abstract suffices)."""
    url = f"https://arxiv.org/abs/{arxiv_id}"
    r = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=30)
    r.raise_for_status()
    html = r.text
    # Extract title
    m_title = re.search(r'<meta name="citation_title" content="([^"]+)"', html)
    title = m_title.group(1) if m_title else f"arXiv:{arxiv_id}"
    # Extract abstract
    m_abs = re.search(r'<blockquote class="abstract[^"]*">.*?<span[^>]*>Abstract:?</span>(.*?)</blockquote>', html, re.DOTALL | re.IGNORECASE)
    if not m_abs:
        m_abs = re.search(r'<blockquote class="abstract[^"]*">(.*?)</blockquote>', html, re.DOTALL | re.IGNORECASE)
    abstract = m_abs.group(1) if m_abs else ""
    abstract = re.sub(r"<[^>]+>", "", abstract).strip()
    return f"## Title\n\n{title}\n\n## Abstract\n\n{abstract}\n"


# Selected arXiv lecture notes / surveys - varied authors, open access
ARXIV_NOTES = [
    ("arxiv_spectral_graph", "2406.16751"),  # spectral graph theory survey (recent open arXiv)
    ("arxiv_linear_alg_lecture", "1208.0848"),  # an open lecture-notes paper
]


# ------------------------------------------------------------------------
# OpenStax - CC BY 4.0 open textbooks
# ------------------------------------------------------------------------


def fetch_openstax_chapter(book_slug: str, chapter_path: str) -> str:
    """Fetch one OpenStax HTML chapter (via the OpenStax CNX or direct chapter URL).

    OpenStax 'College Algebra' etc. chapters are accessible at:
      https://openstax.org/books/<book-slug>/pages/<chapter-path>
    """
    url = f"https://openstax.org/books/{book_slug}/pages/{chapter_path}"
    r = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=30)
    r.raise_for_status()
    html = r.text
    # OpenStax pages have prose inside <main> ... <div class="os-text">; extract the body
    # Simpler approach: strip HTML tags, keep block structure
    body_m = re.search(r"<main[^>]*>(.*?)</main>", html, re.DOTALL | re.IGNORECASE)
    body = body_m.group(1) if body_m else html
    # Convert headings before stripping
    for lvl in range(1, 5):
        body = re.sub(
            rf"<h{lvl}[^>]*>(.*?)</h{lvl}>",
            lambda m, lvl=lvl: f"\n\n{'#' * lvl} {re.sub('<[^>]+>', '', m.group(1)).strip()}\n\n",
            body,
            flags=re.DOTALL | re.IGNORECASE,
        )
    # Convert paragraphs
    body = re.sub(r"</p>", "\n\n", body, flags=re.IGNORECASE)
    body = re.sub(r"<[^>]+>", "", body)
    body = re.sub(r"&nbsp;", " ", body)
    body = re.sub(r"&amp;", "&", body)
    body = re.sub(r"&lt;", "<", body)
    body = re.sub(r"&gt;", ">", body)
    body = re.sub(r"\n{3,}", "\n\n", body)
    return body.strip()


OPENSTAX_CHAPTERS = [
    # College Algebra is a stable, long-published OpenStax book - good for our purpose
    ("ox_college_algebra_ch3", "college-algebra-2e", "3-1-functions-and-function-notation"),
]


# ------------------------------------------------------------------------
# Main
# ------------------------------------------------------------------------


def main():
    manifest = []

    # Wikipedia
    for slug, title in WIKIPEDIA_ARTICLES:
        try:
            text = fetch_wikipedia(title)
            out_path = OUT_DIR / f"{slug}.md"
            out_path.write_text(text, encoding="utf-8")
            manifest.append({
                "name": slug,
                "source_class": "wikipedia",
                "source_url": f"https://en.wikipedia.org/wiki/{title.replace(' ', '_')}",
                "license": "CC BY-SA 4.0",
                "title": title,
                "n_bytes": len(text.encode("utf-8")),
                "retrieved_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "path": str(out_path),
            })
            sys.stderr.write(f"[wiki] {slug}: {len(text)} bytes\n")
            time.sleep(0.5)
        except Exception as e:
            sys.stderr.write(f"[wiki ERROR] {slug}: {e}\n")

    # Stack Exchange
    for slug, qid, site in SE_QUESTIONS:
        try:
            high, low = fetch_se_answer(qid, site)
            if high:
                out_high = OUT_DIR / f"{slug}_high.md"
                out_high.write_text(high, encoding="utf-8")
                manifest.append({
                    "name": f"{slug}_high",
                    "source_class": "stack_exchange_high_voted",
                    "source_url": f"https://{site}.com/questions/{qid}",
                    "license": "CC BY-SA 4.0",
                    "title": f"SE question {qid} - high-voted answer",
                    "n_bytes": len(high.encode("utf-8")),
                    "retrieved_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                    "path": str(out_high),
                })
            if low and low != high:
                out_low = OUT_DIR / f"{slug}_low.md"
                out_low.write_text(low, encoding="utf-8")
                manifest.append({
                    "name": f"{slug}_low",
                    "source_class": "stack_exchange_low_voted",
                    "source_url": f"https://{site}.com/questions/{qid}",
                    "license": "CC BY-SA 4.0",
                    "title": f"SE question {qid} - low-voted answer",
                    "n_bytes": len(low.encode("utf-8")),
                    "retrieved_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                    "path": str(out_low),
                })
            sys.stderr.write(f"[SE] q{qid}: high={len(high)} low={len(low)}\n")
            time.sleep(1.0)
        except Exception as e:
            sys.stderr.write(f"[SE ERROR] {slug}: {e}\n")

    # arXiv
    for slug, aid in ARXIV_NOTES:
        try:
            text = fetch_arxiv_abs(aid)
            out_path = OUT_DIR / f"{slug}.md"
            out_path.write_text(text, encoding="utf-8")
            manifest.append({
                "name": slug,
                "source_class": "arxiv_abstract",
                "source_url": f"https://arxiv.org/abs/{aid}",
                "license": "arXiv non-exclusive open",
                "title": f"arXiv:{aid}",
                "n_bytes": len(text.encode("utf-8")),
                "retrieved_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "path": str(out_path),
            })
            sys.stderr.write(f"[arxiv] {slug}: {len(text)} bytes\n")
            time.sleep(1.0)
        except Exception as e:
            sys.stderr.write(f"[arxiv ERROR] {slug}: {e}\n")

    # OpenStax
    for slug, book, chap in OPENSTAX_CHAPTERS:
        try:
            text = fetch_openstax_chapter(book, chap)
            out_path = OUT_DIR / f"{slug}.md"
            out_path.write_text(text, encoding="utf-8")
            manifest.append({
                "name": slug,
                "source_class": "openstax",
                "source_url": f"https://openstax.org/books/{book}/pages/{chap}",
                "license": "CC BY 4.0",
                "title": f"OpenStax {book} - {chap}",
                "n_bytes": len(text.encode("utf-8")),
                "retrieved_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "path": str(out_path),
            })
            sys.stderr.write(f"[openstax] {slug}: {len(text)} bytes\n")
            time.sleep(1.0)
        except Exception as e:
            sys.stderr.write(f"[openstax ERROR] {slug}: {e}\n")

    # Write manifest as NDJSON
    manifest_path = Path(r"D:\temp\spike_43b\spike_43b_real_world_records_2026-05-17.ndjson")
    with manifest_path.open("w", encoding="utf-8") as f:
        for r in manifest:
            f.write(json.dumps(r) + "\n")
    sys.stderr.write(f"\nWrote {len(manifest)} manifest records to {manifest_path}\n")


if __name__ == "__main__":
    main()
