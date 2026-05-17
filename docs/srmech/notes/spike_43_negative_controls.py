"""
Spike #43 — Negative controls

Constructed negative controls per [[feedback_trauma_informed_defensive_scope]]
(do NOT target real bad textbooks; use constructed controls).

Controls produced:
  C1 RANDOM_PARAGRAPH_PERMUTE — take MFO body, shuffle paragraphs across whole doc
  C2 CONCATENATED_UNRELATED — concatenate MFO + caffeine spike + cosmology spike body words at sentence level interleaved
  C3 WORD_SALAD — keep vocabulary of MFO but shuffle word order destroying syntax/coherence
  C4 LINEAR_ENUMERATION — bullet-list-flat construction (definition / definition / definition) without cross-references
  C5 LLM_GENERATED_FLAT — flat enumeration with no cascade or cross-reference (constructed proxy for low-quality LLM output)

For each control: emit a text file, then fingerprint it using the same signatures as
spike_43_literature_spectral_analysis. Compare to canonical-good baseline.
"""

from __future__ import annotations

import json
import random
import re
import sys
from dataclasses import asdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from spike_43_literature_spectral_analysis import (  # type: ignore
    Substrate,
    fingerprint_substrate,
    tokenize_chapters,
    tokenize_paragraphs,
    tokenize_sentences,
    tokenize_words,
    STOPWORDS,
)


GOOD_PATHS = {
    "mfo_notebook": r"D:\GitHub\mlehaptics\docs\antikythera-maths\mfo_spectral_research_notebook.md",
    "spike_38b": r"D:\GitHub\mlehaptics\docs\srmech\notes\spike_38b_caffeine_form_function_remnants_2026-05-17.md",
    "spike_42": r"D:\GitHub\mlehaptics\docs\srmech\notes\spike_42_imprinting_cascade_entropy_reposture_2026-05-17.md",
}


def control_C1_paragraph_permute(text: str, seed: int = 42) -> str:
    """Random paragraph permutation — keeps content, destroys ordering structure."""
    rng = random.Random(seed)
    chapters = tokenize_chapters(text)
    all_paras: list[str] = []
    for _, body in chapters:
        all_paras.extend(tokenize_paragraphs(body))
    rng.shuffle(all_paras)
    # group every 20 paragraphs as one "chapter" with synthetic heading
    chunks = []
    for i in range(0, len(all_paras), 20):
        chunk = all_paras[i : i + 20]
        chunks.append(f"## Section {i // 20 + 1}\n\n" + "\n\n".join(chunk))
    return "\n\n".join(chunks)


def control_C2_concatenated_unrelated(*texts: str, seed: int = 43) -> str:
    """Interleave paragraphs from unrelated documents — destroys topical cohesion."""
    rng = random.Random(seed)
    all_paras: list[str] = []
    for text in texts:
        chapters = tokenize_chapters(text)
        for _, body in chapters:
            all_paras.extend(tokenize_paragraphs(body))
    rng.shuffle(all_paras)
    chunks = []
    for i in range(0, len(all_paras), 20):
        chunk = all_paras[i : i + 20]
        chunks.append(f"## Mixed-Section {i // 20 + 1}\n\n" + "\n\n".join(chunk))
    return "\n\n".join(chunks)


def control_C3_word_salad(text: str, seed: int = 44) -> str:
    """Keep vocabulary, shuffle word order — destroys syntax + coherence; preserves Zipf approximately."""
    rng = random.Random(seed)
    words = tokenize_words(text)
    rng.shuffle(words)
    # build "sentences" of 15-25 words each
    out_sents = []
    i = 0
    while i < len(words):
        n = rng.randint(15, 25)
        sent = " ".join(words[i : i + n]).capitalize() + "."
        out_sents.append(sent)
        i += n
    # group every 12 sentences into a "paragraph", every 30 paragraphs into a chapter
    paras = []
    for i in range(0, len(out_sents), 12):
        paras.append(" ".join(out_sents[i : i + 12]))
    chunks = []
    for i in range(0, len(paras), 30):
        chunk = paras[i : i + 30]
        chunks.append(f"## Section {i // 30 + 1}\n\n" + "\n\n".join(chunk))
    return "\n\n".join(chunks)


# Common technical-domain vocabulary for constructed flat controls
FLAT_VOCAB = (
    "field operator class group spectral basis dimension manifold eigenstate "
    "particle wave matter energy mass charge interaction gauge symmetry transformation "
    "linear unitary hermitian observable measurement projection state superposition "
    "potential boundary condition asymptotic limit convergence series expansion "
    "graph laplacian eigenvalue eigenvector spectrum decomposition orthogonal "
    "function space topology metric connection curvature parallel transport "
    "noether conservation continuity flow stochastic deterministic causality "
    "quantum classical relativistic non-relativistic compact non-compact "
    "renormalization regularization anomaly fluctuation correlation propagator "
    "amplitude cross-section coupling constant scattering bound state resonance "
    "discrete continuous periodic aperiodic rational irrational algebraic transcendental"
).split()

DEFINITION_TEMPLATES = [
    "{} is defined as the {} of {}.",
    "We call {} a {} when it satisfies {}.",
    "By {} we mean any {} that admits {}.",
    "The {} is the {} corresponding to {}.",
    "A {} is said to be {} if and only if it has {}.",
    "Every {} induces a {} on its associated {}.",
]


def _fill_template(t: str, args: list[str]) -> str:
    n = t.count("{}")
    return t.format(*args[:n])


def control_C4_linear_enumeration(seed: int = 45, n_chapters: int = 16, n_paras_per_chapter: int = 25) -> str:
    """Linear flat enumeration — definitions without cross-reference, callback, or cascade.

    This is the SHAPE we hypothesise bad teaching material has: enumeration without
    weaving; flat; no cascade; no recurring threads tying chapters.
    """
    rng = random.Random(seed)
    chapters = []
    for ch_idx in range(1, n_chapters + 1):
        title = " ".join(rng.sample(FLAT_VOCAB, 3))
        paras = []
        for _ in range(n_paras_per_chapter):
            t = rng.choice(DEFINITION_TEMPLATES)
            args = rng.sample(FLAT_VOCAB, 5)
            sent1 = _fill_template(t, args)
            t2 = rng.choice(DEFINITION_TEMPLATES)
            args2 = rng.sample(FLAT_VOCAB, 5)
            sent2 = _fill_template(t2, args2)
            paras.append(sent1 + " " + sent2)
        chapters.append(f"## Chapter {ch_idx}: {title}\n\n" + "\n\n".join(paras))
    return "\n\n".join(chapters)


CASCADE_TEMPLATES = [
    "The {primitive_a} composes with {primitive_b} as established in Chapter {prev_ch}.",
    "Building on Chapter {prev_ch}'s {prev_concept}, we now introduce {new_concept}.",
    "Recall from Chapter {prev_ch} that {recur_concept} cascades into {new_concept}.",
    "As Chapter {prev_ch} showed, {recur_concept} threads through {new_concept}.",
]

CORE_THEMES = ["cascade", "primitive", "spectral", "manifold", "operator", "field"]


def control_C5_llm_generated_flat(seed: int = 46, n_chapters: int = 12, n_paras_per_chapter: int = 20) -> str:
    """Synthetic flat LLM-like enumeration with topic-locality but no inter-chapter weaving.

    Within a chapter, sentences share topical vocabulary (high local coherence). Across
    chapters, vocabulary is independent (no cross-references). Hypothesised bad-text shape:
    locally coherent, globally disconnected.
    """
    rng = random.Random(seed)
    chapters = []
    for ch_idx in range(1, n_chapters + 1):
        # each chapter picks 4-6 words and reuses them
        local_vocab = rng.sample(FLAT_VOCAB, 8)
        title = " ".join(local_vocab[:3])
        paras = []
        for _ in range(n_paras_per_chapter):
            sents = []
            for _ in range(rng.randint(3, 5)):
                t = rng.choice(DEFINITION_TEMPLATES)
                args = rng.sample(local_vocab, 5)
                sents.append(_fill_template(t, args))
            paras.append(" ".join(sents))
        chapters.append(f"## Chapter {ch_idx}: {title}\n\n" + "\n\n".join(paras))
    return "\n\n".join(chapters)


def main(out_dir: str) -> None:
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)

    # Load good texts for content-based controls
    mfo_text = Path(GOOD_PATHS["mfo_notebook"]).read_text(encoding="utf-8")
    spike38b_text = Path(GOOD_PATHS["spike_38b"]).read_text(encoding="utf-8")
    spike42_text = Path(GOOD_PATHS["spike_42"]).read_text(encoding="utf-8")

    controls = {
        "C1_paragraph_permute_mfo": control_C1_paragraph_permute(mfo_text),
        "C2_concatenated_unrelated": control_C2_concatenated_unrelated(mfo_text, spike38b_text, spike42_text),
        "C3_word_salad_mfo": control_C3_word_salad(mfo_text),
        "C4_linear_enumeration": control_C4_linear_enumeration(),
        "C5_llm_generated_flat": control_C5_llm_generated_flat(),
    }

    for name, text in controls.items():
        ctrl_path = out / f"{name}.md"
        ctrl_path.write_text(text, encoding="utf-8")
        print(f"  [write] {ctrl_path}  chars={len(text):,}")

    # Fingerprint each control
    fingerprints = []
    for name, text in controls.items():
        s = Substrate(name=name, path=str(out / f"{name}.md"), text=text, is_canonical_good=False, notes="constructed negative control")
        fp = fingerprint_substrate(s)
        fingerprints.append(fp)

    records_path = out / "spike_43_controls_records.ndjson"
    with records_path.open("w", encoding="utf-8") as f:
        for fp in fingerprints:
            d = asdict(fp)
            base = {
                "date": "2026-05-17",
                "spike": 43,
                "substrate": d["substrate"],
                "is_canonical_good": d["is_canonical_good"],
                "notes": d["notes"],
                "n_chapters": d["n_chapters"],
                "n_paragraphs": d["n_paragraphs"],
                "n_sentences": d["n_sentences"],
                "n_words": d["n_words"],
            }
            for sig_key in [
                "s1_kepler_chapter_lengths",
                "s1_kepler_para_lengths",
                "s2_laplacian",
                "s3_zipf",
                "s4_streaming",
                "s5_cyclic_themes",
                "s6_cascade_beta",
                "s7_vocab_richness",
                "s8_hdc_fingerprint",
            ]:
                rec = dict(base)
                rec["signature"] = sig_key
                rec["fingerprint"] = d[sig_key]
                f.write(json.dumps(rec, default=float) + "\n")
    print(f"  [write] {records_path}")

    print("\n  --- control fingerprint summary ---\n")
    for fp in fingerprints:
        print(
            f"  {fp.substrate}  chapters={fp.n_chapters}  paras={fp.n_paragraphs}  "
            f"sent={fp.n_sentences}  words={fp.n_words}"
        )
        if fp.s3_zipf.get("valid"):
            print(
                f"    S3 Zipf slope={fp.s3_zipf['zipf_slope']:.3f} (target -1)  "
                f"r2={fp.s3_zipf['r2']:.4f}"
            )
        if fp.s2_laplacian.get("valid"):
            print(
                f"    S2 Laplacian fiedler={fp.s2_laplacian['fiedler_lambda_2']:.4f}  "
                f"mean_jaccard={fp.s2_laplacian['mean_jaccard']:.4f}"
            )
        if fp.s4_streaming.get("valid"):
            print(
                f"    S4 streaming mean_adj_jac={fp.s4_streaming['mean_adjacent_jaccard']:.4f}  "
                f"zero_frac={fp.s4_streaming['zero_overlap_fraction']:.4f}"
            )
        if fp.s6_cascade_beta.get("valid"):
            print(
                f"    S6 cascade beta={fp.s6_cascade_beta['beta_fit']:.3f}  "
                f"r2={fp.s6_cascade_beta['r2']:.4f}"
            )
        if fp.s7_vocab_richness.get("valid"):
            print(
                f"    S7 heaps alpha={fp.s7_vocab_richness['heaps_alpha']:.3f}  "
                f"hapax_frac={fp.s7_vocab_richness['hapax_fraction']:.3f}"
            )
        if fp.s8_hdc_fingerprint.get("valid"):
            print(
                f"    S8 HDC mean_cos={fp.s8_hdc_fingerprint['mean_pairwise_cosine']:.4f}  "
                f"in_band={fp.s8_hdc_fingerprint['in_cohere_but_differ_band']}"
            )


if __name__ == "__main__":
    main(r"D:\temp\spike_43")
