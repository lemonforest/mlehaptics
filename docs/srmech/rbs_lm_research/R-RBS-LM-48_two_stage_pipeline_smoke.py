"""R-RBS-LM-48 — Two-stage fp16-inference + Q4-rendering pipeline.

Per user direction 2026-05-26: *"if we can do structural relationship
inference on an fp16 or fp32 model, we have the precision we want. what
happens if we then feed that into a smaller model that knows how to use
words but is now forced to make those words from this fp32 shape of
things?"*

Tests whether splitting work between a precision-preserving Stage 1 (fp16
LLM doing structural inference) and a quantized Stage 2 (Q4 LLM doing
naming-layer rendering) approaches fp16-alone quality while being cheaper
at runtime than fp16-alone.

Three-way comparison, same TinyLlama-1.1B-Chat-v1.0 family for both:

  T1 — fp16 alone:     prompt → fp16 LLM → text_fp16    (gold reference)
  T2 — Q4 alone:       prompt → Q4 LLM   → text_q4      (degraded baseline)
  T3 — two-stage:      prompt → fp16 LLM → fp16_text
                       fp16_text → extract_relationships → rel_form
                       rel_form → Q4 LLM → text_2stage  (composed)

Maps to R-RBS-LM-43 two-substrate framework:
  - Stage 1 (fp16): M1-native structural inference; precision-bearing
  - Bridge (extract_relationships): canonicalize to relationship form;
    strips naming-layer cost; provides depersonalized "wire" form
  - Stage 2 (Q4): M2 naming-layer rendering; just makes words from
    the structure handed to it

Falsifications:
  ❌ If Jaccard(fp16, two-stage) ≤ Jaccard(fp16, Q4-alone) — two-stage
     adds no fidelity vs single-stage Q4; the precision argument fails
  ❌ If two-stage produces incoherent text — Q4 cannot recover naming
     from relationship form alone
  ✅ If Jaccard(fp16, two-stage) > Jaccard(fp16, Q4-alone) AND text is
     coherent — recipe validated; bonus is depersonalization-on-wire
     because rel_form between stages is PII-clean

Privacy framing per user direction: the rel_form passing between Stage 1
and Stage 2 carries no PII (depersonalization at extract). If both stages
ran on separate machines, only the depersonalized form crosses the wire.
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


FP16_MODEL_PATH = "/home/skirklan/.cache/huggingface/hub/manual-llm-cache/tinyllama-chat-fp16"
Q4_MODEL_PATH = "/home/skirklan/.cache/huggingface/hub/manual-llm-cache/tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf"


# Probes — passages with identifiable entities + multi-clause relationships.
# Same set as R-RBS-LM-47a for cross-comparison.
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


SUMMARY_PROMPT = (
    "Summarize the following passage in 2 sentences. "
    "Preserve any factual relationships between named entities.\n\n"
    "Passage:\n{passage}\n\nSummary:"
)

RENDER_PROMPT = (
    "Write a 2-sentence natural English summary from the following "
    "structured relationships. The relationship tokens (PERSON_N, "
    "PLACE_N, ORG_N) are entity references — preserve them as-is in "
    "your output.\n\n"
    "Relationships:\n{rel}\n\nSummary:"
)


# ----- Stage 1: fp16 via HF transformers (cached per process) -----

_FP16_MODEL = None
_FP16_TOKENIZER = None


def get_fp16(model_path):
    global _FP16_MODEL, _FP16_TOKENIZER
    if _FP16_MODEL is None:
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer
        print(f"  [fp16] loading from {model_path} ...")
        t0 = time.time()
        _FP16_TOKENIZER = AutoTokenizer.from_pretrained(model_path)
        _FP16_MODEL = AutoModelForCausalLM.from_pretrained(
            model_path, torch_dtype=torch.float16,
        )
        _FP16_MODEL.eval()
        torch.set_num_threads(16)
        print(f"  [fp16] loaded in {time.time()-t0:.1f}s")
    return _FP16_MODEL, _FP16_TOKENIZER


def call_fp16(prompt, model_path=FP16_MODEL_PATH, max_new_tokens=120):
    import torch
    model, tok = get_fp16(model_path)
    # Use the model's chat template if available; otherwise plain.
    # transformers 5.x returns BatchEncoding by default; unwrap explicitly.
    if hasattr(tok, "apply_chat_template") and tok.chat_template:
        messages = [{"role": "user", "content": prompt}]
        enc = tok.apply_chat_template(
            messages,
            return_tensors="pt",
            add_generation_prompt=True,
            return_dict=True,
        )
        input_ids = enc["input_ids"]
    else:
        input_ids = tok.encode(prompt, return_tensors="pt")
        if not torch.is_tensor(input_ids):
            input_ids = input_ids["input_ids"]
    eos_id = tok.eos_token_id if tok.eos_token_id is not None else tok.pad_token_id
    with torch.no_grad():
        out = model.generate(
            input_ids,
            max_new_tokens=max_new_tokens,
            do_sample=False,
            pad_token_id=eos_id,
        )
    new = out[0][input_ids.shape[1]:].tolist()
    text = tok.decode(new, skip_special_tokens=True).strip()
    return text


# ----- Stage 2: Q4 via llama-cpp-python (cached per process) -----

_Q4_LLM = None


def get_q4(model_path):
    global _Q4_LLM
    if _Q4_LLM is None:
        from llama_cpp import Llama
        print(f"  [Q4] loading from {model_path} ...")
        t0 = time.time()
        _Q4_LLM = Llama(
            model_path=model_path,
            n_ctx=2048,
            n_threads=16,
            verbose=False,
        )
        print(f"  [Q4] loaded in {time.time()-t0:.1f}s")
    return _Q4_LLM


def call_q4(prompt, model_path=Q4_MODEL_PATH, max_tokens=120):
    llm = get_q4(model_path)
    result = llm.create_chat_completion(
        messages=[{"role": "user", "content": prompt}],
        max_tokens=max_tokens,
        temperature=0.0,
    )
    return result["choices"][0]["message"]["content"].strip()


# ----- Metrics -----

def jaccard(a, b):
    sa = set(re.findall(r'\w+', a.lower()))
    sb = set(re.findall(r'\w+', b.lower()))
    if not sa and not sb:
        return 1.0
    return len(sa & sb) / max(len(sa | sb), 1)


def count_substring_hits(text, candidates):
    if not candidates:
        return 0
    return sum(1 for c in candidates if c in text)


# ----- Run one probe through all three pipelines -----

def run_probe(passage, fp16_path=FP16_MODEL_PATH, q4_path=Q4_MODEL_PATH,
              verbose=True):
    if verbose:
        print(f"\n--- T1: single-stage fp16 ---")
    t0 = time.time()
    text_T1 = call_fp16(SUMMARY_PROMPT.format(passage=passage), fp16_path)
    elapsed_T1 = time.time() - t0
    if verbose:
        print(f"    fp16 done in {elapsed_T1:.1f}s; out={len(text_T1)} chars")

    if verbose:
        print(f"--- T2: single-stage Q4 ---")
    t0 = time.time()
    text_T2 = call_q4(SUMMARY_PROMPT.format(passage=passage), q4_path)
    elapsed_T2 = time.time() - t0
    if verbose:
        print(f"    Q4 done in {elapsed_T2:.1f}s; out={len(text_T2)} chars")

    # Two-stage: fp16 -> extract_relationships -> Q4
    if verbose:
        print(f"--- T3: two-stage fp16 → extract → Q4 ---")
    t0 = time.time()
    # Stage 1: ask fp16 to summarize (creates the structural inference output)
    fp16_text = text_T1  # reuse T1's fp16 output to save compute
    # Bridge: extract relationships from fp16's output
    triples, entity_map = extract_relationships(fp16_text, depersonalize=True)
    rel_form = serialize_triples(triples)
    wire_pii = pii_audit(rel_form)
    # Stage 2: ask Q4 to render the relationships
    text_T3_raw = call_q4(RENDER_PROMPT.format(rel=rel_form), q4_path)
    # Repersonalize at endpoint
    text_T3 = repersonalize(text_T3_raw, entity_map)
    elapsed_T3 = time.time() - t0
    if verbose:
        print(f"    two-stage done in {elapsed_T3:.1f}s; out={len(text_T3)} chars; "
              f"wire-PII={len(wire_pii)}")

    # Original passage PII (for "wire would have leaked" reference)
    _, pas_entity_map = extract_relationships(passage, depersonalize=True)
    original_pii_names = list(pas_entity_map.keys())

    # Metrics
    metrics = {
        "passage_chars": len(passage),
        "T1_fp16_chars": len(text_T1),
        "T2_Q4_chars": len(text_T2),
        "T3_two_stage_chars": len(text_T3),
        "T1_fp16_seconds": round(elapsed_T1, 1),
        "T2_Q4_seconds": round(elapsed_T2, 1),
        "T3_two_stage_seconds": round(elapsed_T3, 1),
        "jaccard_fp16_vs_Q4_alone": round(jaccard(text_T1, text_T2), 3),
        "jaccard_fp16_vs_two_stage": round(jaccard(text_T1, text_T3), 3),
        "jaccard_fp16_vs_two_stage_wire": round(jaccard(text_T1, text_T3_raw), 3),
        "wire_form_pii_suspects": len(wire_pii),
        "rel_form_chars": len(rel_form),
        "rel_form_triples": len(triples),
        "pii_names_in_passage": len(original_pii_names),
        "pii_in_T1": count_substring_hits(text_T1, original_pii_names),
        "pii_in_T2": count_substring_hits(text_T2, original_pii_names),
        "pii_in_T3_wire_form": count_substring_hits(text_T3_raw, original_pii_names),
        "pii_in_T3_repersonalized": count_substring_hits(text_T3, original_pii_names),
        "text_T1_fp16": text_T1,
        "text_T2_Q4": text_T2,
        "text_T3_two_stage_wire": text_T3_raw,
        "text_T3_two_stage_repersonalized": text_T3,
        "rel_form_on_wire": rel_form,
        "entity_map_local_only": dict(entity_map),
    }
    return metrics


def main():
    print(f"=== R-RBS-LM-48 — Two-stage fp16-inference → Q4-rendering ===")
    print(f"  fp16 model: {FP16_MODEL_PATH}")
    print(f"  Q4 model:   {Q4_MODEL_PATH}")
    print(f"  probes: {len(PROBES)}\n")

    # Sanity: model files exist
    if not Path(FP16_MODEL_PATH).exists():
        print(f"  FATAL: fp16 model dir not found.")
        sys.exit(2)
    if not Path(Q4_MODEL_PATH).exists():
        print(f"  FATAL: Q4 model file not found.")
        sys.exit(2)

    results = []
    for i, passage in enumerate(PROBES):
        print(f"\n=== Probe {i+1}/{len(PROBES)} ===")
        print(f"  passage ({len(passage)} chars): {passage[:80]!r}...")
        try:
            m = run_probe(passage, verbose=True)
            results.append(m)
            print(f"  Jaccard(fp16, Q4):       {m['jaccard_fp16_vs_Q4_alone']:.3f}")
            print(f"  Jaccard(fp16, 2-stage):  {m['jaccard_fp16_vs_two_stage']:.3f}")
            print(f"  Wire-form PII suspects:  {m['wire_form_pii_suspects']}")
        except Exception as e:
            print(f"  ERROR: {type(e).__name__}: {e}")
            results.append({"error": f"{type(e).__name__}: {e}", "passage": passage})

    # Aggregate
    print(f"\n\n{'='*72}\n=== R-RBS-LM-48 aggregate\n{'='*72}\n")
    n = len(results)
    valid = [r for r in results if "error" not in r]
    n_valid = len(valid)
    if n_valid == 0:
        print(f"  No valid probes; cannot aggregate.")
        out_path = Path("docs/srmech/rbs_lm_research/R-RBS-LM-48_results.json")
        out_path.write_text(json.dumps({"results": results}, indent=2))
        return

    avg = {
        "T1_fp16_seconds": sum(r["T1_fp16_seconds"] for r in valid) / n_valid,
        "T2_Q4_seconds": sum(r["T2_Q4_seconds"] for r in valid) / n_valid,
        "T3_two_stage_seconds": sum(r["T3_two_stage_seconds"] for r in valid) / n_valid,
        "jaccard_fp16_vs_Q4_alone": sum(r["jaccard_fp16_vs_Q4_alone"] for r in valid) / n_valid,
        "jaccard_fp16_vs_two_stage": sum(r["jaccard_fp16_vs_two_stage"] for r in valid) / n_valid,
        "wire_form_pii_suspects": sum(r["wire_form_pii_suspects"] for r in valid) / n_valid,
        "pii_in_T1": sum(r["pii_in_T1"] for r in valid) / n_valid,
        "pii_in_T2": sum(r["pii_in_T2"] for r in valid) / n_valid,
        "pii_in_T3_wire_form": sum(r["pii_in_T3_wire_form"] for r in valid) / n_valid,
        "pii_in_T3_repersonalized": sum(r["pii_in_T3_repersonalized"] for r in valid) / n_valid,
    }

    print(f"  Wall time per probe (avg):")
    print(f"    T1 fp16 alone:      {avg['T1_fp16_seconds']:>6.1f}s")
    print(f"    T2 Q4 alone:        {avg['T2_Q4_seconds']:>6.1f}s")
    print(f"    T3 two-stage:       {avg['T3_two_stage_seconds']:>6.1f}s")
    print(f"  Fidelity to fp16 (Jaccard avg):")
    print(f"    Q4 alone:           {avg['jaccard_fp16_vs_Q4_alone']:.3f}")
    print(f"    Two-stage:          {avg['jaccard_fp16_vs_two_stage']:.3f}")
    delta = avg['jaccard_fp16_vs_two_stage'] - avg['jaccard_fp16_vs_Q4_alone']
    print(f"    Δ (2-stage − Q4):   {delta:+.3f}  "
          f"({'two-stage preserves more' if delta > 0.05 else 'wash' if abs(delta) < 0.05 else 'Q4-alone wins'})")
    print(f"  PII / depersonalization:")
    print(f"    Names in original:                     varies per probe")
    print(f"    PII in T1 fp16 output:                 {avg['pii_in_T1']:.2f}")
    print(f"    PII in T2 Q4 output:                   {avg['pii_in_T2']:.2f}")
    print(f"    PII in T3 wire form (Q4 input):        {avg['pii_in_T3_wire_form']:.2f}")
    print(f"    PII in T3 repersonalized output:       {avg['pii_in_T3_repersonalized']:.2f}")
    print(f"    Wire-form PII suspects (rel passed Q4): {avg['wire_form_pii_suspects']:.2f}")
    print(f"    → wire-form should be ~0 if depersonalization is clean")

    # Reading
    print(f"\n=== Reading ===")
    if delta > 0.05:
        print(f"  ✓ Two-stage preserves MORE fp16 fidelity than single-stage Q4 (+{delta:.3f})")
        print(f"    → Composition recipe validated; precision lives in Stage 1")
    elif delta < -0.05:
        print(f"  ✗ Two-stage preserves LESS fp16 fidelity than single-stage Q4 ({delta:.3f})")
        print(f"    → Bridge (extract_relationships) loses more than it preserves")
    else:
        print(f"  ≈ Two-stage ≈ single-stage Q4 (Δ={delta:+.3f})")
        print(f"    → No measurable fidelity gain; precision arg may not survive at this scale")

    if avg['wire_form_pii_suspects'] < 0.5:
        print(f"  ✓ Wire-form PII audit clean (<0.5 suspects avg) — depersonalization works")
    else:
        print(f"  ⚠ Wire-form PII suspects ≥0.5 — depersonalization leaks at this scale")

    output = {
        "partition": "R-RBS-LM-48",
        "fp16_model": FP16_MODEL_PATH,
        "q4_model": Q4_MODEL_PATH,
        "n_probes": n,
        "n_valid": n_valid,
        "results_per_probe": results,
        "aggregate": {k: round(v, 3) for k, v in avg.items()},
    }
    out_path = Path("docs/srmech/rbs_lm_research/R-RBS-LM-48_results.json")
    out_path.write_text(json.dumps(output, indent=2, ensure_ascii=False))
    print(f"\nResults: {out_path}")


if __name__ == "__main__":
    main()
