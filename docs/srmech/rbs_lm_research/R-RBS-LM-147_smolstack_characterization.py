"""R-RBS-LM-147 — smol-stack substrate variant characterization (Phase C / #184).

Runs the canonical R-RBS-LM-122 unified characterization (P0..P7) on the
"smol-stack" catalog variant: a deliberately SMALL, multi-source curated stack
of 5 distinct-register texts (procedural / almanac / fable / aphorism /
travel-log), loaded from descriptor_smolstack.toml via srmech.amsc.load_descriptor.

This is the FIRST run of the unified characterization on a real-FILE (non-template)
corpus. R-122's build_corpus only knew "template"; this runner supplies a
"smol_stack" corpus loader and reuses R-122's phase functions unchanged (the
catalog IS the config; R-122 IS the characterization). It then adds the
smol-stack-specific result: a per-source substrate-signature comparison.

=== SMOKE STATUS (load-bearing honesty) ===
The five stack texts are SYNTHETIC fragments authored for this methodology run
(NOT a sourced external corpus). Each is attested by its real content SHA-256
(verified here via srmech.amsc.format.sha256_bytes against the descriptor).
Provenance is "synthesised by this run for methodology validation", NOT a
fabricated external citation. This run is a METHODOLOGY SMOKE — it validates
that the canonical characterization machinery consumes a multi-file real-text
stack and yields a stable substrate signature. It is NOT a data claim about any
natural corpus. (smoke_status='methodology_smoke', data_claim=false in catalog.)

=== PRE-STATED EXPECTATIONS + FALSIFIERS (spike-query discipline; nulls count) ===
Per F162, the canonical substrate is length- and dimension-independent with
recall 1.000 nearly everywhere on the *template* corpus. PRE-STATE:

  E1 (recall):  We EXPECT the smol-stack to also recall ~1.000 across the
                length/corpus/dimension sweeps (the substrate algebra is
                content-agnostic — F162). A SURPRISE/NULL would be recall < 1.0
                at these tiny corpus sizes (would indicate real-text collisions
                the template never produced, e.g. shared frame "the X the Y").

  E2 (signature, the headline): The smol-stack substrate-signature (sector
                occupancy of the bigram bundle + structural densities) is
                compared to the existing variants (template = F162 canonical;
                religious-texts = R-123). We PRE-STATE two falsifiable outcomes:
                  (a) DISTINCT — the smol-stack occupancy / density profile is
                      sharply different from the template baseline (small
                      multi-source curated stack leaves its own signature);
                  (b) INDISTINGUISHABLE — the smol-stack occupancy is flat
                      (~uniform 0.25 per sector) and its densities sit on the
                      same trend as template/religious, i.e. the substrate
                      signature is corpus-agnostic at this depth (a NULL for
                      "the stack has a distinguishing signature"; consistent
                      with the F172/F199 flat-spectral ceiling).
                Either is a legitimate finding. We do NOT lean toward (a).

  E3 (cross-register spread): WITHIN the smol-stack, do the 5 registers leave
                distinguishable per-source signatures, or is the spread small?
                Small spread => the substrate reads form-structure that the 5
                synthetic registers share; large spread => register leaves a
                mark. (Honest: synthetic texts share my authoring hand — a
                confound that BIASES toward small spread; flagged in the finding.)

SCOPE: structural/spectral ONLY; methodology smoke; no data claims about natural
text. srmech-native throughout (Klein-4 via srmech.amsc.hdc; SHA-256 via
srmech.amsc.format.sha256_bytes; descriptor via srmech.amsc.load_descriptor).
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
from collections import Counter
from pathlib import Path

import numpy as np

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))

# Reuse the canonical substrate library + the R-122 phase functions unchanged.
import _canonical_substrate as cs  # noqa: E402
import importlib.util as _ilu  # noqa: E402

_spec_r122 = _ilu.spec_from_file_location(
    "r122", HERE / "R-RBS-LM-122_substrate_characterization.py"
)
r122 = _ilu.module_from_spec(_spec_r122)
sys.modules["r122"] = r122
_spec_r122.loader.exec_module(r122)

from srmech import __version__ as SRMECH_VERSION  # noqa: E402
from srmech.amsc import load_descriptor, descriptor_hash, hdc, format as amsc_format  # noqa: E402
from srmech.amsc._native import HAS_NATIVE, NATIVE_ABI_VERSION  # noqa: E402

SMOLSTACK_CATALOG = HERE.parent / "catalogs" / "rbs_lm_substrate" / "descriptor_smolstack.toml"

_WORD = re.compile(r"[a-z]+")


# ---------------------------------------------------------------------------
# smol-stack corpus loading (the new corpus.source the canonical R-122 lacked)
# ---------------------------------------------------------------------------

def load_source_units(path: Path, strip_header: int) -> list[list[str]]:
    """Read one stack file, drop the N-line synthetic header, split to
    verse-line units (one non-empty line >= 1 bigram), tokenize lowercase."""
    raw = path.read_text(encoding="utf-8", errors="replace")
    lines = raw.splitlines()
    body = lines[strip_header:] if strip_header else lines
    units: list[list[str]] = []
    for line in body:
        toks = _WORD.findall(line.lower())
        if len(toks) >= 2:
            units.append(toks)
    return units


def load_smolstack(params, cache_dir: Path) -> tuple[list[list[str]], dict[str, list[list[str]]]]:
    """Pool all stack sources into one corpus (sorted by source key for
    determinism) + return the per-source unit lists for the signature compare."""
    corpus_cfg = params["corpus"]
    strip_header = int(corpus_cfg.get("strip_header_lines", 0))
    texts = corpus_cfg["texts"]
    per_source: dict[str, list[list[str]]] = {}
    pooled: list[list[str]] = []
    for key in sorted(texts.keys()):
        meta = texts[key]
        path = cache_dir / meta["filename"]
        units = load_source_units(path, strip_header)
        per_source[key] = units
        pooled.extend(units)
    return pooled, per_source


# A module-global the patched build_corpus closes over (set in main()).
_POOLED_CORPUS: list[list[str]] = []


def _smolstack_build_corpus(params, n_target: int, seed: int) -> list[list[str]]:
    """Drop-in replacement for r122.build_corpus when corpus.source=='smol_stack'.

    Deterministic, seed-stable subsample of the pooled stack to n_target
    (clamped to availability). Sentence ORDER is fixed; the subsample is a
    seeded permutation so corpus_sweep N values are nested-stable."""
    if params["corpus"]["source"] != "smol_stack":
        return r122._ORIG_BUILD_CORPUS(params, n_target, seed)  # type: ignore[attr-defined]
    pool = _POOLED_CORPUS
    if n_target >= len(pool):
        return [list(s) for s in pool]
    rng = np.random.default_rng(seed)
    idx = rng.choice(len(pool), size=int(n_target), replace=False)
    return [list(pool[i]) for i in sorted(idx)]


def _smolstack_build_vocab(params) -> list[str]:
    """Vocab pool for perturbation sentences = all tokens seen in the stack."""
    vocab: set[str] = set()
    for s in _POOLED_CORPUS:
        vocab.update(s)
    return sorted(vocab)


# ---------------------------------------------------------------------------
# Per-source substrate signature (the smol-stack-specific result, E2/E3)
# ---------------------------------------------------------------------------

def _bigram_sector(a: str, b: str, hex_chars: int) -> int:
    """Deterministic Klein-4 sector for a bigram, srmech-native (SHA-256 prefix
    mod 4). This is the hash null-control routing from R-123 — uniform sectors
    are the EXPECTED baseline; structure would show as departure from uniform."""
    digest = amsc_format.sha256_bytes(f"{a}\x1f{b}".encode("utf-8"))
    return int(digest[:hex_chars], 16) % 4


def source_signature(units: list[list[str]], params) -> dict:
    """Substrate signature for one source: structural densities + Klein-4 sector
    occupancy of the source's bigram bundle (built via srmech hdc.klein4_*)."""
    D = int(params["substrate"]["D"])
    hex_chars = int(params["substrate"]["token_seed_hex_chars"])

    words: set[str] = set()
    bigrams: list[tuple[str, str]] = []
    unique_bigrams: set[tuple[str, str]] = set()
    skeletons: set[tuple] = set()
    min_sk = int(params["substrate"]["min_skeleton_length"])
    n_tokens = 0
    for toks in units:
        n_tokens += len(toks)
        words.update(toks)
        for i in range(len(toks) - 1):
            bg = (toks[i], toks[i + 1])
            bigrams.append(bg)
            unique_bigrams.add(bg)
        if len(toks) >= min_sk:
            skeletons.add(((toks[0], toks[1]), (toks[-2], toks[-1])))

    # Klein-4 sector occupancy: route each bigram to a sector (hash-control),
    # bundle per sector via srmech hdc, record occupancy fraction + the bundle's
    # CPT-mirror self-similarity (a srmech-native chirality readout).
    occ = Counter()
    sector_vecs: dict[int, list[np.ndarray]] = {s: [] for s in range(4)}
    for a, b in bigrams:
        s = _bigram_sector(a, b, hex_chars)
        occ[s] += 1
        vec = cs.encode_bigram_l1(a, b, D=D, hex_chars=hex_chars)
        sector_vecs[s].append(hdc.klein4_bind(vec, np.full(D, s, dtype=np.uint8)))
    total = max(1, sum(occ.values()))
    occupancy = [occ.get(s, 0) / total for s in range(4)]

    all_tagged = [v for s in range(4) for v in sector_vecs[s]]
    if all_tagged:
        bundle = hdc.klein4_bundle(*all_tagged)
        cpt_self = float(hdc.klein4_similarity(bundle, hdc.klein4_cpt_mirror(bundle)))
        g5_self = float(hdc.klein4_similarity(bundle, hdc.klein4_chirality_flip_gamma5(bundle)))
    else:
        cpt_self = g5_self = 0.0

    n_units = len(units)
    n_bigrams = len(bigrams)
    return {
        "n_units": n_units,
        "n_tokens": n_tokens,
        "n_words": len(words),
        "n_bigrams": n_bigrams,
        "n_unique_bigrams": len(unique_bigrams),
        "n_skeletons": len(skeletons),
        "type_token_ratio": len(words) / max(1, n_tokens),
        "bigram_reuse": 1.0 - len(unique_bigrams) / max(1, n_bigrams),
        "sector_occupancy": occupancy,
        "cpt_self_sim": cpt_self,
        "gamma5_self_sim": g5_self,
    }


def _l1(a, b) -> float:
    """L1 distance over two equal-length numeric sequences. Sign of each
    coordinate difference is a Class-K fold: keep the positive branch via
    max(d, -d) (NOT python abs() — the cascade-honesty rule)."""
    total = 0.0
    for x, y in zip(a, b):
        d = x - y
        total += d if d >= 0 else -d   # Class-K pin-slot fold (named), not abs()
    return float(total)


def run_source_signatures(per_source, params, labels, registers, out_records, attestation):
    print()
    print("=" * 104)
    print("SMOL-STACK per-source substrate signature (E2/E3) — sector occupancy + densities")
    print("=" * 104)
    print(f"  {'source':>16} | {'units':>5} {'words':>5} {'bigr':>5} {'uniq':>5} {'skel':>5} | "
          f"{'TTR':>5} {'reuse':>5} | {'s0':>5} {'s1':>5} {'s2':>5} {'s3':>5} | {'cpt':>6}")
    print("  " + "-" * 100)
    sigs = {}
    for key in sorted(per_source.keys()):
        sig = source_signature(per_source[key], params)
        sigs[key] = sig
        occ = sig["sector_occupancy"]
        print(f"  {labels[key][:16]:>16} | {sig['n_units']:>5} {sig['n_words']:>5} "
              f"{sig['n_bigrams']:>5} {sig['n_unique_bigrams']:>5} {sig['n_skeletons']:>5} | "
              f"{sig['type_token_ratio']:>5.3f} {sig['bigram_reuse']:>5.3f} | "
              f"{occ[0]:>5.3f} {occ[1]:>5.3f} {occ[2]:>5.3f} {occ[3]:>5.3f} | {sig['cpt_self_sim']:>6.3f}")
        out_records.append({
            **attestation, "phase": "S1_source_signature", "source_key": key,
            "source_label": labels[key], "register": registers[key], **sig,
        })

    # Cross-source spread: max pairwise L1 over sector-occupancy + over a
    # normalized density vector (TTR, reuse).
    keys = sorted(sigs.keys())
    occ_dists, dens_dists = [], []
    for i in range(len(keys)):
        for j in range(i + 1, len(keys)):
            occ_dists.append(_l1(sigs[keys[i]]["sector_occupancy"], sigs[keys[j]]["sector_occupancy"]))
            dens_dists.append(_l1(
                [sigs[keys[i]]["type_token_ratio"], sigs[keys[i]]["bigram_reuse"]],
                [sigs[keys[j]]["type_token_ratio"], sigs[keys[j]]["bigram_reuse"]],
            ))
    occ_spread_mean = float(np.mean(occ_dists)) if occ_dists else 0.0
    occ_spread_max = float(np.max(occ_dists)) if occ_dists else 0.0
    dens_spread_mean = float(np.mean(dens_dists)) if dens_dists else 0.0
    dens_spread_max = float(np.max(dens_dists)) if dens_dists else 0.0

    # Pooled (whole-stack) signature = the smol-stack's variant-level signature
    pooled_sig = source_signature(_POOLED_CORPUS, params)

    print()
    print(f"  cross-register sector-occupancy L1 spread:  mean={occ_spread_mean:.4f}  max={occ_spread_max:.4f}")
    print(f"  cross-register density(TTR,reuse) L1 spread: mean={dens_spread_mean:.4f}  max={dens_spread_max:.4f}")
    print(f"  pooled stack occupancy = [{', '.join(f'{x:.3f}' for x in pooled_sig['sector_occupancy'])}]  "
          f"(uniform=0.25 each => flat null)")

    out_records.append({
        **attestation, "phase": "S0_signature_summary",
        "occupancy_spread_mean": occ_spread_mean, "occupancy_spread_max": occ_spread_max,
        "density_spread_mean": dens_spread_mean, "density_spread_max": dens_spread_max,
        "pooled_signature": pooled_sig,
    })
    return sigs, pooled_sig, occ_spread_mean, occ_spread_max


# ---------------------------------------------------------------------------
# Driver
# ---------------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--catalog", type=Path, default=SMOLSTACK_CATALOG)
    ap.add_argument("--phases", default="1,2,3,4,5,6,7")
    ap.add_argument("--out", type=Path, default=None)
    args = ap.parse_args()

    desc = load_descriptor(args.catalog)
    dh = descriptor_hash(args.catalog)
    params = desc.fetch["literature_curated"]
    phases_to_run = {int(p.strip()) for p in args.phases.split(",") if p.strip()}

    if params["corpus"]["source"] != "smol_stack":
        print(f"ERROR: catalog corpus.source != 'smol_stack' ({params['corpus']['source']!r}); "
              f"this runner is smol-stack-specific.", file=sys.stderr)
        sys.exit(2)

    cache_dir = Path(params["corpus"]["cache_dir"]).expanduser()

    # --- attest each stack text by content SHA-256 (srmech-native) ---
    texts = params["corpus"]["texts"]
    labels = {k: texts[k]["label"] for k in texts}
    registers = {k: texts[k].get("register", "?") for k in texts}
    print(f"srmech v{SRMECH_VERSION}; HAS_NATIVE={HAS_NATIVE}; ABI={NATIVE_ABI_VERSION}")
    print(f"Catalog: {desc.path.name}  hash={dh[:16]}...")
    print(f"  smoke_status={params['corpus']['smoke_status']}  data_claim={params['corpus']['data_claim']}")
    print(f"  cache_dir={cache_dir}")
    all_ok = True
    for key in sorted(texts.keys()):
        meta = texts[key]
        path = cache_dir / meta["filename"]
        if not path.exists():
            print(f"  MISSING: {path}", file=sys.stderr)
            all_ok = False
            continue
        actual = amsc_format.sha256_bytes(path.read_bytes())
        ok = actual == meta["sha256"]
        all_ok = all_ok and ok
        print(f"  {meta['label'][:34]:34s} sha256✓={ok}  ({meta['filename']})")
    if not all_ok:
        print("ERROR: corpus SHA-256 attestation failed or file missing — aborting "
              "(do NOT run on unattested corpus).", file=sys.stderr)
        sys.exit(3)

    # --- load pooled + per-source corpora ---
    global _POOLED_CORPUS
    _POOLED_CORPUS, per_source = load_smolstack(params, cache_dir)
    print(f"  pooled stack: {len(_POOLED_CORPUS)} units across {len(per_source)} sources")

    # --- patch R-122's corpus/vocab builders to consume the smol-stack ---
    if not hasattr(r122, "_ORIG_BUILD_CORPUS"):
        r122._ORIG_BUILD_CORPUS = r122.build_corpus  # type: ignore[attr-defined]
    r122.build_corpus = _smolstack_build_corpus  # type: ignore[assignment]
    r122.build_vocab = _smolstack_build_vocab  # type: ignore[assignment]

    out_path = args.out
    if out_path is None:
        out_path = args.catalog.parent / desc.schema["ndjson_file"]
    out_path.parent.mkdir(parents=True, exist_ok=True)

    attestation = {
        "descriptor_path": str(desc.path),
        "descriptor_hash": dh,
        "source_key": desc.source["key"],
        "srmech_version": SRMECH_VERSION,
        "abi_version": NATIVE_ABI_VERSION,
        "has_native": HAS_NATIVE,
        "smoke_status": params["corpus"]["smoke_status"],
        "data_claim": bool(params["corpus"]["data_claim"]),
        "scope": "METHODOLOGY SMOKE; structural-only; synthetic stack; NOT a data claim about natural text",
    }

    vocab = r122.build_vocab(params)
    print(f"  vocab pool (perturbations) = {len(vocab)} tokens\n")

    out_records = [{
        **attestation, "phase": "P0_attestation_header",
        "substrate_params": params["substrate"],
        "generation_params": params["generation"],
        "grammar_mode": params["grammar"]["mode"],
        "corpus_source": params["corpus"]["source"],
        "n_pooled_units": len(_POOLED_CORPUS),
        "n_sources": len(per_source),
    }]

    t_start = time.time()
    # --- the smol-stack-specific result first (S0/S1) ---
    run_source_signatures(per_source, params, labels, registers, out_records, attestation)

    # --- the canonical R-122 unified characterization (P1..P7), unchanged ---
    if 1 in phases_to_run:
        r122.phase1_length_sweep(params, vocab, out_records, attestation)
    if 2 in phases_to_run:
        r122.phase2_corpus_sweep(params, out_records, attestation)
    if 3 in phases_to_run:
        r122.phase3_dimension_sweep(params, out_records, attestation)
    if 4 in phases_to_run:
        r122.phase4_bucket_sweep(params, out_records, attestation)
    if 5 in phases_to_run:
        r122.phase5_generation(params, out_records, attestation)
    if 6 in phases_to_run:
        r122.phase6_grammar(params, out_records, attestation)
    if 7 in phases_to_run:
        r122.phase7_plausibility(params, vocab, out_records, attestation)
    elapsed = time.time() - t_start

    with open(out_path, "w") as f:
        for rec in out_records:
            f.write(json.dumps(rec, default=str) + "\n")
    print(f"\nResults: {out_path}  ({len(out_records)} records)  [{elapsed:.1f}s]")
    print("SMOKE: methodology validation only — NOT a data claim about natural text.")


if __name__ == "__main__":
    main()
