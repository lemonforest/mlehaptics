"""R-RBS-LM-47a — LLM input format test: text vs relationships on the wire.

Per user direction 2026-05-26: *"what if we can send relationships to the
LLM instead of all the text tokens? ... we can try with our smaller LLM
on CPU inference by sending tokenized text and then by sending tokenized
relationships. this would also be a layer of depersonalizing all LLM but
only on the wire/in flight because inference will know it."*

Tests whether a modern LLM produces useful output when fed tokenized
RELATIONSHIPS (depersonalized S-V-O triples) instead of raw text. The
"depersonalize on the wire only" framing: wire bytes carry no PII;
inference recovers semantics; PERSON1↔name map is held locally and only
de-anonymizes at endpoint.

Requires a running OpenAI-API-compatible local LLM server. Per
R-RBS-LM-24 / R-RBS-LM-34 / R-RBS-LM-36: spin up llama.cpp with any
chat-tuned Q4 GGUF model. Default endpoint: http://localhost:8080/v1.

Setup before running:
    # 1. Re-fetch a chat-tuned GGUF (was reaped in earlier cleanup):
    huggingface-cli download \\
        TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF \\
        tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf \\
        --local-dir /tmp/llm-cache
    # 2. Spin up llama.cpp server:
    llama-server -m /tmp/llm-cache/tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf \\
        --port 8080 --host 0.0.0.0 -c 2048
    # 3. Run this script in parallel:
    ~/.venvs/rbs-lm-research/bin/python \\
        docs/srmech/rbs_lm_research/R-RBS-LM-47a_llm_input_format_smoke.py

Output: comparison matrix per probe + aggregate metrics:
  - response_length (chars)
  - response_token_count (rough)
  - lexical_overlap (Jaccard of word sets, response-vs-response)
  - pii_in_response (count of original PII tokens leaking back from
    relationship-form response → tests "depersonalization integrity")
  - retained_entity_tokens (count of PERSON_N / etc tokens preserved
    in response → tests whether LLM passes the structure through)
"""

import json
import re
import sys
import time
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE.parent / "python"))
sys.path.insert(0, str(HERE))

from rbs_lm_relationships import (  # noqa: E402
    extract_relationships, serialize_triples, repersonalize, pii_audit,
)


DEFAULT_ENDPOINT = "http://localhost:8080/v1/chat/completions"

# Probes — short paragraphs with identifiable entities + relationships.
# Each probe is a self-contained passage; the LLM is asked to summarize it.
PROBES = [
    "Steven Kirkland leads the research notebook project at the lab. "
    "He works closely with Alice Bennett on cryptographic primitives. "
    "Their work appears in the Journal of Cryptography.",

    "The chef tasted the soup and reached for the salt. "
    "Maria Santos, the head chef, supervised the kitchen team. "
    "The Bistro Magnolia hosts twenty diners each Friday evening.",

    "Migration patterns of monarch butterflies span thousands of miles. "
    "Researchers at Stanford University study the species annually. "
    "Dr. James Wilson reported the findings at the conference in Mexico.",

    "Public-key cryptography enables secure communication between Alice and Bob. "
    "The Diffie-Hellman exchange was developed in 1976. "
    "RSA was published two years later by Rivest, Shamir, and Adleman.",

    "The library at Alexandria held perhaps half a million scrolls. "
    "Ptolemy I founded the institution in Egypt. "
    "Eratosthenes served as chief librarian for several decades.",
]


SUMMARY_PROMPT_TEMPLATE_TEXT = (
    "Summarize the following passage in 2 sentences. "
    "Preserve any factual relationships between named entities.\n\n"
    "Passage:\n{passage}\n\nSummary:"
)

SUMMARY_PROMPT_TEMPLATE_REL = (
    "Summarize the following depersonalized relationships in 2 sentences. "
    "Treat PERSON_N / PLACE_N / ORG_N tokens as entity references; "
    "preserve their relationships in your summary.\n\n"
    "Relationships:\n{passage}\n\nSummary:"
)


def call_llm(prompt, endpoint=DEFAULT_ENDPOINT, max_tokens=200, timeout=120):
    """POST a chat completion request to the OpenAI-compatible endpoint."""
    import urllib.request
    import urllib.error

    payload = {
        "model": "local",
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": max_tokens,
        "temperature": 0.0,
    }
    req = urllib.request.Request(
        endpoint,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = json.loads(resp.read().decode("utf-8"))
    except urllib.error.URLError as e:
        return {"error": f"URLError: {e}"}
    except Exception as e:
        return {"error": f"{type(e).__name__}: {e}"}

    try:
        text = body["choices"][0]["message"]["content"]
    except (KeyError, IndexError) as e:
        return {"error": f"parse error: {e}", "raw": body}
    return {"text": text, "raw": body}


def jaccard(a, b):
    """Jaccard similarity over word sets."""
    sa = set(re.findall(r'\w+', a.lower()))
    sb = set(re.findall(r'\w+', b.lower()))
    if not sa and not sb:
        return 1.0
    return len(sa & sb) / max(len(sa | sb), 1)


def count_pii_leak(response_text, original_pii_tokens):
    """Count how many original PII strings appear in the response.

    For the relationship-form pipeline: if response contains original names
    despite wire being depersonalized, that's a leak. Note: leak can come
    from LLM training (knowing the name is associated with the topic), not
    necessarily from wire-form decoding. Still useful as a signal.
    """
    if not original_pii_tokens:
        return 0
    count = 0
    for pii in original_pii_tokens:
        if pii in response_text:
            count += 1
    return count


def count_entity_tokens_retained(response_text, entity_map):
    """Count how many depersonalized tokens (PERSON_N etc.) appear in response.

    Indicates whether the LLM passed the structure through rather than
    inventing names.
    """
    if not entity_map:
        return 0
    count = 0
    for orig, tok in entity_map.items():
        if tok in response_text:
            count += 1
    return count


def run_probe(passage, endpoint, verbose=True):
    """Run one probe through both text-form and relationship-form pipelines."""
    # Build the relationship form
    triples, entity_map = extract_relationships(passage, depersonalize=True)
    rel_corpus = serialize_triples(triples)
    original_pii = list(entity_map.keys())

    # Pipeline A: send raw text
    prompt_A = SUMMARY_PROMPT_TEMPLATE_TEXT.format(passage=passage)
    if verbose:
        print(f"  [A] sending text-form ({len(passage)} chars)")
    t0 = time.time()
    resp_A = call_llm(prompt_A, endpoint=endpoint)
    elapsed_A = time.time() - t0

    # Pipeline B: send relationship form
    prompt_B = SUMMARY_PROMPT_TEMPLATE_REL.format(passage=rel_corpus)
    if verbose:
        print(f"  [B] sending rel-form ({len(rel_corpus)} chars)")
    t0 = time.time()
    resp_B = call_llm(prompt_B, endpoint=endpoint)
    elapsed_B = time.time() - t0

    text_A = resp_A.get("text", "")
    text_B = resp_B.get("text", "")

    # Repersonalize B's response so it can be compared semantically
    text_B_repersonalized = repersonalize(text_B, entity_map)

    metrics = {
        "passage_chars": len(passage),
        "rel_corpus_chars": len(rel_corpus),
        "entities_mapped": len(entity_map),
        "n_triples": len(triples),
        "wire_form_pii_audit": len(pii_audit(rel_corpus)),
        "response_A_chars": len(text_A),
        "response_B_chars": len(text_B),
        "elapsed_A_s": round(elapsed_A, 1),
        "elapsed_B_s": round(elapsed_B, 1),
        "jaccard_A_B_raw": round(jaccard(text_A, text_B), 3),
        "jaccard_A_B_repers": round(jaccard(text_A, text_B_repersonalized), 3),
        "pii_in_response_A": count_pii_leak(text_A, original_pii),
        "pii_in_response_B": count_pii_leak(text_B, original_pii),
        "entity_tokens_in_response_B": count_entity_tokens_retained(text_B, entity_map),
        "response_A": text_A,
        "response_B_wire_form": text_B,
        "response_B_repersonalized": text_B_repersonalized,
        "rel_corpus_sent_on_wire": rel_corpus,
        "entity_map_local_only": dict(entity_map),
        "error_A": resp_A.get("error"),
        "error_B": resp_B.get("error"),
    }
    return metrics


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--endpoint", default=DEFAULT_ENDPOINT)
    parser.add_argument("--out", default="docs/srmech/rbs_lm_research/R-RBS-LM-47a_results.json")
    args = parser.parse_args()

    print(f"=== R-RBS-LM-47a — LLM input format test ===")
    print(f"  endpoint: {args.endpoint}")
    print(f"  probes: {len(PROBES)}\n")

    # Quick endpoint health check
    print(f"=== Health check ===")
    health = call_llm("hello", endpoint=args.endpoint, max_tokens=5, timeout=10)
    if "error" in health:
        print(f"  FATAL: endpoint not reachable. {health['error']}")
        print(f"  Run an OpenAI-API-compatible local LLM server first.")
        print(f"  See docstring for llama-server setup instructions.")
        sys.exit(2)
    print(f"  OK — endpoint responded.")

    results = []
    for i, passage in enumerate(PROBES):
        print(f"\n=== Probe {i+1}/{len(PROBES)} ===")
        m = run_probe(passage, args.endpoint, verbose=True)
        results.append(m)
        print(f"  A response: {m['response_A_chars']} chars, {m['elapsed_A_s']:.1f}s")
        print(f"  B response: {m['response_B_chars']} chars, {m['elapsed_B_s']:.1f}s")
        print(f"  Wire-form PII audit: {m['wire_form_pii_audit']} suspects")
        print(f"  Response-A original PII leak: {m['pii_in_response_A']}")
        print(f"  Response-B original PII leak: {m['pii_in_response_B']} "
              f"(LLM knowledge, not wire — still informative)")
        print(f"  Entity-tokens retained in B: {m['entity_tokens_in_response_B']}/{m['entities_mapped']}")
        print(f"  Jaccard A↔B (raw):           {m['jaccard_A_B_raw']:.3f}")
        print(f"  Jaccard A↔B (repersonalized): {m['jaccard_A_B_repers']:.3f}")

    # ---- Aggregate summary ----
    print(f"\n\n{'='*72}")
    print(f"=== R-RBS-LM-47a aggregate")
    print(f"{'='*72}\n")
    n = len(results)
    avg_pii_A = sum(r["pii_in_response_A"] for r in results) / max(n, 1)
    avg_pii_B = sum(r["pii_in_response_B"] for r in results) / max(n, 1)
    avg_entity_ret = sum(r["entity_tokens_in_response_B"] for r in results) / max(n, 1)
    avg_jacc_raw = sum(r["jaccard_A_B_raw"] for r in results) / max(n, 1)
    avg_jacc_repers = sum(r["jaccard_A_B_repers"] for r in results) / max(n, 1)
    avg_wire_pii = sum(r["wire_form_pii_audit"] for r in results) / max(n, 1)

    print(f"  wire-form PII audit (avg):                    {avg_wire_pii:.1f}")
    print(f"    → if ≈0, wire form is clean (depersonalization works at extraction)")
    print(f"  PII tokens in response-A (text-form input):   {avg_pii_A:.2f}")
    print(f"  PII tokens in response-B (rel-form input):    {avg_pii_B:.2f}")
    print(f"    → response-B leaks come from LLM training, NOT wire — informative")
    print(f"  Entity-tokens retained in response-B (avg):   {avg_entity_ret:.2f}")
    print(f"    → high = LLM passes structure through; low = LLM rejects/rewrites")
    print(f"  Jaccard A↔B raw (avg):                         {avg_jacc_raw:.3f}")
    print(f"  Jaccard A↔B repersonalized (avg):              {avg_jacc_repers:.3f}")
    print(f"    → higher repersonalized = semantic equivalence preserved")

    output = {
        "partition": "R-RBS-LM-47a",
        "endpoint": args.endpoint,
        "n_probes": n,
        "results_per_probe": results,
        "aggregate": {
            "avg_wire_form_pii_audit": round(avg_wire_pii, 2),
            "avg_pii_in_response_A": round(avg_pii_A, 2),
            "avg_pii_in_response_B": round(avg_pii_B, 2),
            "avg_entity_tokens_retained_in_B": round(avg_entity_ret, 2),
            "avg_jaccard_A_B_raw": round(avg_jacc_raw, 3),
            "avg_jaccard_A_B_repersonalized": round(avg_jacc_repers, 3),
        },
    }
    out_path = Path(args.out)
    out_path.write_text(json.dumps(output, indent=2, ensure_ascii=False))
    print(f"\nResults: {out_path}")


if __name__ == "__main__":
    main()
