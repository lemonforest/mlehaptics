r"""R-RBS-LM-SIONAGENOMEHANDLER (F740-followon) — the genome-backed Siona /v1 handler + an AMSC update-check.
srmech 0.7.5rc149.

(1) chat_completion(request) — OpenAI-shaped, backed by the GENEPOOL genome (SionaGenepool from R-RBS-LM-SIONAGENEPOOL:
    introspect genome_catalog -> route -> etak-walk genome_genes -> render MPR payload / ask). SIONASERVER imports
    THIS instead of the hardcoded STORYAPI demo shelf -> the live /v1 reads from Siona's genepool.
(2) AMSC UPDATE-CHECK — Siona checks, via AMSC content-hashes, whether the srmech/MFO notebooks have DRIFTED from the
    persisted genome, and only re-bakes when stale. `check_updates()` re-hashes the live notebook sections and diffs
    them against the genome's recorded MPR `response_sha256`s (cheap; no rebuild). `sync_updates()` re-bakes the genome
    when stale. This is the efficient genome<-notebook refresh: bake-before-ship AND post-ship refresh when the
    notebooks change on GitHub. (Reusable shape: any AMSC-attested SSoT -> hash-diff -> request/apply update.)

HONEST scope: detection is the efficient part (hash-diff, no rebuild unless drifted). `sync_updates` today re-bakes the
whole genepool (genome_save); per-notebook IN-PLACE update via a multi-gene-aware genome_replace is the §45/§43.1
follow-on (the rc149 in-place edit ops take `leaves`, not `genes`). Research-subtree scaffold; NOT a package edit.

Run:  /tmp/srmech_rc149/venv/bin/python3 docs/srmech/rbs_lm_research/R-RBS-LM-SIONAGENOMEHANDLER_...py
"""
import json
import time
import importlib.util as _U
import os
from pathlib import Path
import srmech
from srmech.amsc import genome as g, hdc
from srmech.amsc.format import sha256_raw, read_ndjson

HERE = Path(__file__).parent
GENOME_DIR = os.environ.get("SIONA_GENOME", str(HERE / ".siona_genepool"))

# load the genepool builder + World (hyphenated filename -> importlib, the SIONASERVER pattern)
_spec = _U.spec_from_file_location(
    "sionagenepool", str(HERE / "R-RBS-LM-SIONAGENEPOOL_storyteller_etak_walk_over_genome_with_notebooks.py"))
_gp = _U.module_from_spec(_spec); _spec.loader.exec_module(_gp)

WORLDS = {"genepool": "the Siona genepool genome (identity + signwriting + era-dictionaries + MFO/srmech notebooks)"}


def _section_hashes(kernel):
    """live notebook -> {section_label: sha256(heading+summary)} (the AMSC content-state of the source)."""
    secs = _gp.parse_sections(_gp.NOTEBOOKS[kernel])
    return {lab: sha256_raw(f"{kernel}/{lab}/{head} — {summ}".strip(' —').encode()).hex() for lab, head, summ in secs}


def _recorded_hashes(kernel):
    """genome's persisted MPR response_sha256 per section (what Siona currently holds)."""
    out = {}
    for r in read_ndjson(Path(GENOME_DIR) / "genepool.ndjson"):
        if r.data.get("kernel") == kernel:
            out[r.data["key"]] = r.attestation.get("response_sha256")
    return out


def check_updates():
    """AMSC update-check: which notebook kernels have DRIFTED from the persisted genome? (cheap; no rebuild)."""
    report = {}
    for kernel in _gp.NOTEBOOKS:
        live, held = _section_hashes(kernel), _recorded_hashes(kernel)
        changed = sorted(k for k in live if k in held and live[k] != held[k])
        added = sorted(set(live) - set(held))
        removed = sorted(set(held) - set(live))
        if changed or added or removed:
            report[kernel] = {"changed": changed, "added": added, "removed": removed}
    return report                              # {} == up-to-date


def sync_updates():
    """re-bake the genome from the notebooks IF stale (today: full genepool rebuild; in-place per-notebook = §45 follow-on)."""
    if check_updates():
        _gp.build_genepool(GENOME_DIR)
        return True
    return False


def _ensure_genome():
    if not (Path(GENOME_DIR) / "genepool.ndjson").exists():
        _gp.build_genepool(GENOME_DIR)
    else:
        sync_updates()                          # refresh if the notebooks drifted since last bake
    return _gp.SionaGenepool(GENOME_DIR)


_WORLD = _ensure_genome()


def chat_completion(request):
    """OpenAI /v1/chat/completions handler, backed by the genepool genome."""
    model = request.get("model", "siona:genepool")
    last = next((m.get("content") or "" for m in reversed(request.get("messages", [])) if m.get("role") == "user"), "")
    answer = _WORLD.infer(last)
    return {"id": "chatcmpl-siona-genepool", "object": "chat.completion", "created": int(time.time()), "model": model,
            "choices": [{"index": 0, "message": {"role": "assistant", "content": answer}, "finish_reason": "stop"}],
            "usage": {"prompt_tokens": len(last.split()), "completion_tokens": len(answer.split()), "total_tokens": 0},
            "srmech": {"genome_backed": True, "compositional": True, "gpu_free": True}}


def main():
    print(f"=== R-RBS-LM-SIONAGENOMEHANDLER — genome-backed /v1 + AMSC update-check (srmech {srmech.__version__}) ===\n")
    print("genepool at:", GENOME_DIR, "| chromosomes:", [lab for lab, _ in _WORLD.introspect()])
    print("\n(1) genome-backed chat_completion (the /v1 surface reads the genepool):")
    for q in ["what is MFO about chirality?", "in modern english define awful", "translate this 1600s text: define nice"]:
        r = chat_completion({"model": "siona:genepool", "messages": [{"role": "user", "content": q}]})
        print(f"    Q: {q}\n     A: {r['choices'][0]['message']['content'][:130]}")
    print("\n(2) AMSC update-check (is the genome current vs the live notebooks?):")
    print("    check_updates():", check_updates() or "UP-TO-DATE (no drift)")
    print("    -> Siona only re-bakes when the AMSC content-hashes drift; detection is cheap (no rebuild). The")
    print("       post-ship path is identical: notebooks change on GitHub -> re-hash -> sync_updates re-bakes.")


if __name__ == "__main__":
    main()
