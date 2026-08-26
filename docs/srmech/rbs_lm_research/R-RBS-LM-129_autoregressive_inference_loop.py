"""R-RBS-LM-129 — F166 Walk Step 4: the autoregressive loop. THIS IS INFERENCE.

The four stones of Steps 1-3 assembled into the loop that makes the substrate a
language model:

    window = seed[-k:]
    repeat:
        ctx_state = encode_context(window)              # Step 1 (Class A∘M + position)
        sims      = sim(M ⊕ ctx_state, cand_vecs)        # Step 2 (Class M retrieve)
        p         = softmax(sims / T)                     # Step 3 (temperature dial)
        next_tok  = sample(candidates, p)                 # over next_after[last] (bigram-legal)
        emit next_tok; window = (window + [next_tok])[-k:]   # condition on OWN output

The substrate now generates conditioned on its own running output. The real
question (F166 §3 Step 4): does COHERENCE hold over many steps, or does it drift /
loop / collapse? Measured NATIVELY — never against a float LLM:

  trigram_legal  = fraction of generated trigrams (w_{i-1},w_i,w_{i+1}) that occur
                   in the corpus — does the k-window memory keep the walk on REAL
                   paths, beyond mere bigram-legality? (the substrate's value-add)
  pos_valid      = fraction of generated POS-bigrams licensed by the template
                   grammar (DET→SUBJ, SUBJ→VERB, VERB→OBJ/PREP, … , OBJ→DET) —
                   does it stay on the grammatical manifold?
  repeat_rate    = fraction of tokens equal to the token 1 or 2 back (loop/collapse)
  distinct_ratio = unique/total generated tokens (collapse detector)

Baseline = a pure bigram-walk at the same temperature (sample from P(next|last)).
If the k-window substrate beats the bigram on trigram-legality / pos-validity, the
context memory genuinely improves multi-step coherence — inference works AND is
better than the immediate-predecessor model.

Catalog-driven ([inference.loop]); shared ContextSubstrate; srmech 0.5.0 ABI=3.
Deterministic / bit-exact (seeded generation).
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))

import _canonical_substrate as cs

_spec = importlib.util.spec_from_file_location(
    "corpus_gen", HERE / "R-RBS-LM-113_larger_corpus_scaling.py")
corpus_gen = importlib.util.module_from_spec(_spec)
sys.modules["corpus_gen"] = corpus_gen
_spec.loader.exec_module(corpus_gen)

from srmech.amsc import load_descriptor, descriptor_hash, hdc
from srmech.amsc._native import HAS_NATIVE, NATIVE_ABI_VERSION
from srmech import __version__ as SRMECH_VERSION

CATALOG = HERE.parent / "catalogs" / "rbs_lm_substrate" / "descriptor_rbs_lm_inference.toml"

# ---- POS grammar derived from R-RBS-LM-113 templates (the corpus's generator) ----
POS = {
    "DET": set(corpus_gen.DETERMINERS),
    "SUBJ": set(corpus_gen.SUBJECTS_DET_THE) | set(corpus_gen.SUBJECTS_DET_A),
    "VERB": set(corpus_gen.VERBS_TRANSITIVE_4w),
    "OBJ": set(corpus_gen.OBJECTS),
    "PREP": set(corpus_gen.PREPOSITIONS),
    "ADJ": set(corpus_gen.ADJECTIVES),
}
# templates: DET SUBJ VERB OBJ / DET SUBJ VERB PREP OBJ /
#            DET SUBJ VERB PREP DET OBJ / DET SUBJ VERB PREP DET ADJ OBJ  (+ OBJ→DET boundary)
VALID_POS_BIGRAMS = {
    ("DET", "SUBJ"), ("SUBJ", "VERB"), ("VERB", "OBJ"), ("VERB", "PREP"),
    ("PREP", "OBJ"), ("PREP", "DET"), ("DET", "OBJ"), ("DET", "ADJ"),
    ("ADJ", "OBJ"), ("OBJ", "DET"),
}


def pos_tags(tok: str) -> set[str]:
    return {p for p, words in POS.items() if tok in words}


def pos_bigram_valid(a: str, b: str) -> bool:
    return any((pa, pb) in VALID_POS_BIGRAMS
               for pa in pos_tags(a) for pb in pos_tags(b))


def softmax(x: np.ndarray, t: float) -> np.ndarray:
    z = x / t
    z = z - z.max()
    e = np.exp(z)
    return e / e.sum()


def coherence_metrics(seq, corpus_trigrams):
    """Native coherence of a generated token sequence."""
    n = len(seq)
    if n < 3:
        return None
    trig = [(seq[i], seq[i + 1], seq[i + 2]) for i in range(n - 2)]
    trigram_legal = float(np.mean([t in corpus_trigrams for t in trig]))
    posb = [pos_bigram_valid(seq[i], seq[i + 1]) for i in range(n - 1)]
    pos_valid = float(np.mean(posb))
    rep1 = np.mean([seq[i] == seq[i - 1] for i in range(1, n)])
    rep2 = np.mean([seq[i] == seq[i - 2] for i in range(2, n)])
    repeat_rate = float(max(rep1, rep2))
    distinct_ratio = len(set(seq)) / n
    # cycle_3gram: 1 - distinct/total trigrams — high when the sequence loops on a
    # repeated cycle (the bigram-collapse failure mode); ~0 for diverse generation
    cycle_3gram = float(1.0 - len(set(trig)) / len(trig)) if trig else 0.0
    return {"trigram_legal": trigram_legal, "pos_valid": pos_valid,
            "repeat_rate": repeat_rate, "distinct_ratio": distinct_ratio,
            "cycle_3gram": cycle_3gram}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--catalog", type=Path, default=CATALOG)
    ap.add_argument("--show", type=int, default=4, help="sample sequences to print")
    args = ap.parse_args()

    desc = load_descriptor(args.catalog)
    dh = descriptor_hash(args.catalog)
    lc = desc.fetch["literature_curated"]
    D = int(lc["substrate"]["D"])
    hexc = int(lc["substrate"]["token_seed_hex_chars"])
    ic = lc["inference"]["context"]
    corpus_n = int(ic["corpus_n"])
    seed = int(ic["seed"])
    sc = lc["inference"]["sampling"]
    k = int(sc["sweep_k"])
    N = int(sc["sweep_n_assoc"])
    loopc = lc["inference"]["loop"]
    gen_lengths = list(loopc["gen_length_sweep"])
    op_temps = list(loopc["operating_temps"])
    n_seq = int(loopc["n_sequences"])
    loop_seed = int(loopc["loop_seed"])

    ctx = cs.ContextSubstrate(D=D, hex_chars=hexc)
    enc = ctx.enc

    print(f"srmech v{SRMECH_VERSION}; HAS_NATIVE={HAS_NATIVE}; ABI={NATIVE_ABI_VERSION}; D={D}")
    print(f"Catalog: {args.catalog.name}  hash={dh[:16]}...")
    print(f"k={k}  N={N}  gen_lengths={gen_lengths}  temps={op_temps}  n_seq={n_seq}\n")

    rng = np.random.default_rng(seed)
    corpus = corpus_gen.generate_corpus(corpus_n, rng)
    stream = [t for sent in corpus for t in sent]
    vocab = sorted(set(stream))
    vocab_vecs = np.stack([enc(w) for w in vocab])
    vocab_idx = {w: i for i, w in enumerate(vocab)}

    bigram_counts: dict[str, Counter] = defaultdict(Counter)
    for a, b in zip(stream, stream[1:]):
        bigram_counts[a][b] += 1
    next_after = {a: sorted(c.keys()) for a, c in bigram_counts.items()}
    corpus_trigrams = {(stream[i], stream[i + 1], stream[i + 2])
                       for i in range(len(stream) - 2)}

    # corpus-itself coherence (the ceiling): trigram-legal=1.0 by definition; pos baseline
    corpus_pos = float(np.mean([pos_bigram_valid(stream[i], stream[i + 1])
                                for i in range(len(stream) - 1)]))
    print(f"corpus: {len(corpus_trigrams)} distinct trigrams; "
          f"corpus pos-bigram validity = {corpus_pos:.3f} (the grammatical ceiling)\n")

    # build the k-window associative memory M (the inference substrate's knowledge)
    pairs_all = [(tuple(stream[i - k:i]), stream[i]) for i in range(k, len(stream))]
    idx = rng.choice(len(pairs_all), size=N, replace=False)
    pairs = [pairs_all[i] for i in idx]
    ctx_states = [ctx.encode_context(list(c)) for c, _ in pairs]
    assoc = [hdc.klein4_bind(ctx_states[i], enc(pairs[i][1])) for i in range(N)]
    M = ctx.bundle_odd(assoc)

    # seed pool: real k-grams from the stream that start at a sentence boundary
    # (DET as first token) so generation begins in-grammar
    seed_kgrams = [tuple(stream[i:i + k]) for i in range(len(stream) - k)
                   if stream[i] in POS["DET"] and "DET" in pos_tags(stream[i])]

    def gen_substrate(window, length, T, gr):
        out = []
        win = list(window)
        for _ in range(length):
            last = win[-1]
            cands = next_after.get(last, [])
            if not cands:
                break
            if len(cands) == 1:
                nxt = cands[0]
            else:
                cidx = [vocab_idx[c] for c in cands]
                probe = hdc.klein4_bind(M, ctx.encode_context(win[-k:]))
                p = softmax(cs.sim_k4_batch(probe, vocab_vecs[cidx]), T)
                nxt = cands[int(gr.choice(len(cands), p=p))]
            out.append(nxt)
            win.append(nxt)
        return out

    def gen_bigram(window, length, T, gr):
        out = []
        last = window[-1]
        for _ in range(length):
            cands = next_after.get(last, [])
            if not cands:
                break
            if len(cands) == 1:
                nxt = cands[0]
            else:
                cnt = np.array([bigram_counts[last][c] for c in cands], dtype=float)
                p = softmax(np.log(cnt), T)  # temperature over log-frequency
                nxt = cands[int(gr.choice(len(cands), p=p))]
            out.append(nxt)
            last = nxt
        return out

    attest = {"descriptor_hash": dh, "source_key": desc.source["key"],
              "srmech_version": SRMECH_VERSION, "abi_version": NATIVE_ABI_VERSION,
              "has_native": HAS_NATIVE, "k": k, "N": N}
    records = []

    print(f"{'T':>6} | {'L':>3} | {'model':>9} | {'trigram_legal':>13} | {'pos_valid':>9} | "
          f"{'cycle3g':>7} | {'distinct':>8}")
    print("-" * 80)
    sample_store = {}
    for T in op_temps:
        for L in gen_lengths:
            gr = np.random.default_rng(loop_seed)
            seed_idx = gr.choice(len(seed_kgrams), size=n_seq, replace=True)
            for model, gen in (("substrate", gen_substrate), ("bigram", gen_bigram)):
                agg = defaultdict(list)
                first_samples = []
                for si in seed_idx:
                    window = list(seed_kgrams[si])
                    out = gen(window, L, T, gr)
                    full = window + out
                    m = coherence_metrics(full, corpus_trigrams)
                    if m is None:
                        continue
                    for key, v in m.items():
                        agg[key].append(v)
                    if len(first_samples) < args.show:
                        first_samples.append(full)
                rec = {**attest, "phase": "P4_loop", "model": model, "T": T, "gen_length": L,
                       **{key: float(np.mean(v)) for key, v in agg.items()}, "n_seq": len(agg["pos_valid"])}
                records.append(rec)
                print(f"{T:>6.3f} | {L:>3} | {model:>9} | {rec['trigram_legal']:>13.3f} | "
                      f"{rec['pos_valid']:>9.3f} | {rec['cycle_3gram']:>7.3f} | "
                      f"{rec['distinct_ratio']:>8.3f}")
                if T == op_temps[1] and L == gen_lengths[1] and model == "substrate":
                    sample_store["substrate"] = first_samples
                if T == op_temps[1] and L == gen_lengths[1] and model == "bigram":
                    sample_store["bigram"] = first_samples
        print("-" * 78)

    # ------------------------------------------------------------------
    # Concrete generated sequences (aphantasia: show the inference output)
    # ------------------------------------------------------------------
    print("\n" + "=" * 78)
    print(f"GENERATED SEQUENCES (T={op_temps[1]}, L={gen_lengths[1]}) — the substrate inferring")
    print("=" * 78)
    for model in ("substrate", "bigram"):
        print(f"\n  [{model}]")
        for s in sample_store.get(model, []):
            print(f"    {' '.join(s)}")

    out = args.catalog.parent / "substrate_measurements" / "inference_step4_loop.ndjson"
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w") as f:
        for r in records:
            f.write(json.dumps(r, default=str) + "\n")
    print(f"\nResults: {out}  ({len(records)} records)")

    # headline: substrate vs bigram at the longest generation, coldest useful T
    def cell(model, T, L):
        return next(r for r in records if r["model"] == model and r["T"] == T and r["gen_length"] == L)
    Tsel, Lsel = op_temps[1], gen_lengths[-1]
    sub, big = cell("substrate", Tsel, Lsel), cell("bigram", Tsel, Lsel)
    print("\n" + "=" * 78)
    print(f"STEP 4 READING (inference works; coherence over {Lsel} steps at T={Tsel}):")
    print(f"  substrate: trigram-legal {sub['trigram_legal']:.3f}, pos-valid {sub['pos_valid']:.3f}, "
          f"cycle3g {sub['cycle_3gram']:.3f}, distinct {sub['distinct_ratio']:.3f}")
    print(f"  bigram   : trigram-legal {big['trigram_legal']:.3f}, pos-valid {big['pos_valid']:.3f}, "
          f"cycle3g {big['cycle_3gram']:.3f}, distinct {big['distinct_ratio']:.3f}")
    print(f"  pos-validity (grammaticality): substrate {sub['pos_valid']:.3f} | bigram {big['pos_valid']:.3f}"
          f"  — inference stays on the grammatical manifold")
    print(f"  anti-collapse (k-window value-add): distinct {sub['distinct_ratio']:.3f} vs "
          f"{big['distinct_ratio']:.3f} ({sub['distinct_ratio'] - big['distinct_ratio']:+.3f}), "
          f"cycle3g {sub['cycle_3gram']:.3f} vs {big['cycle_3gram']:.3f} "
          f"({sub['cycle_3gram'] - big['cycle_3gram']:+.3f}; lower=less looping)")


if __name__ == "__main__":
    main()
