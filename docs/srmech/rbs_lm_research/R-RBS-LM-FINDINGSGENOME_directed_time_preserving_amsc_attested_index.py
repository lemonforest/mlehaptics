r"""R-RBS-LM-FINDINGSGENOME (F1217; user "make findings srmech-discoverable via an AMSC-attested index — a genome,
precisely because some findings refute or build a previous; time is preserved in a linear record") — the research
findings as a DIRECTED, TIME-PRESERVING, AMSC-attested Class-L genome. LOCAL TEST (not a committed genome).

THE TEACHABLE MOMENT: a monolithic integration (one MFO/srmech-notebook doc of all findings) FLATTENS the curvature
that lives in the LINEAR findings — because TIME is preserved in a linear record. Each finding BUILDS (+) or REFUTES (−)
an earlier one; the finding NUMBER is the time index. So the findings are a DIRECTED SIGNED graph (F1209/F1210): the
build/refute sign is the CHARGE, the time order is the DIRECTION. A monolith keeps the METRIC (what is finally true)
and flattens the CURVATURE (which finding turned on which, when) — exactly the bag we spent this session fighting,
applied to our OWN knowledge record. This script measures how much of that curvature a monolith would discard.

AMSC attestation: each finding -> a record {id, title, file, sha256(content), links[]} (srmech-discoverable index).
Genome-native persist: the directed findings kernel (vocab=ids, edges, weights=metric, charge=build/refute) via
kernel_pack -> genome_save (content-addressed, LOCAL). srmech 0.9.0rc238; no numpy; no abs-builtin. Run:
  /tmp/srmech_v/venv/bin/python3 docs/srmech/rbs_lm_research/R-RBS-LM-FINDINGSGENOME_...py
"""
import json
import os
import re
import shutil
import tempfile
from fractions import Fraction
from pathlib import Path

from srmech.amsc import genome as G
from srmech.amsc import hdc
from srmech.amsc import laplacian as L
from srmech.amsc.format import sha256_bytes

HERE = Path(__file__).parent
OUTDIR = Path(os.environ.get("OUT", str(Path.home() / "corpora" / "findings_genome")))   # LOCAL test target
LEAF = 64
COUPLE = hdc.klein4_random(LEAF, seed=1217)
_FID = re.compile(r"FINDING_(\d+)_")
_FREF = re.compile(r"\bF(\d{2,4})\b")
_REFUTE = re.compile(r"corrects|refutes?|REFUTED|supersed|retract|rejected|replaces|wrong|the miss|fails|does not",
                     re.IGNORECASE)


def parse_findings():
    """Each finding -> {id, title, file, sha, refs:[(target_id, charge)]}. charge: +1 BUILD, -1 REFUTE (by keyword
    near the F#### reference on its line). id = the finding NUMBER = the time index."""
    recs = {}
    for f in sorted(HERE.glob("R-RBS-LM-FINDING_*.md")):
        m = _FID.search(f.name)
        if not m:
            continue
        fid = int(m.group(1))
        text = f.read_text(errors="ignore")
        title = next((ln[2:].strip() for ln in text.splitlines() if ln.startswith("# ")), f.stem)[:90]
        refs = []
        for ln in text.splitlines():
            charge = -1 if _REFUTE.search(ln) else 1                 # refute vs build, by the line's own words
            for r in _FREF.findall(ln):
                tgt = int(r)
                if tgt != fid:
                    refs.append((tgt, charge))
        recs[fid] = {"id": fid, "title": title, "file": f.name,
                     "sha": sha256_bytes(text.encode()), "refs": refs}
    return recs


def build_directed_graph(recs):
    """Directed SIGNED Class-L: node = finding id; a reference F_src -> F_tgt is a directed edge with the time arrow
    (later cites earlier = the research walk backward in time). Canonical (lo,hi) by id; edge_charge = net directional
    build/refute flow = (later->earlier builds) - (earlier->later) etc., signed by build(+)/refute(-)."""
    ids = sorted(recs)
    idx = {v: i for i, v in enumerate(ids)}
    fwd, bwd, sign = {}, {}, {}                                      # fwd: lo cites hi ; bwd: hi cites lo ; sign accum
    for fid, r in recs.items():
        for tgt, ch in r["refs"]:
            if tgt not in idx:
                continue                                            # dangling ref (a finding we don't have) — skip
        for tgt, ch in r["refs"]:
            if tgt not in idx:
                continue
            a, b = idx[fid], idx[tgt]
            lo, hi = (a, b) if a < b else (b, a)
            if a > b:                                               # later (fid) cites earlier (tgt): the normal build arrow
                bwd[(lo, hi)] = bwd.get((lo, hi), 0) + 1
            else:
                fwd[(lo, hi)] = fwd.get((lo, hi), 0) + 1
            sign[(lo, hi)] = sign.get((lo, hi), 0) + ch             # +build / -refute accumulation
    edges = sorted(set(fwd) | set(bwd) | set(sign))
    weights = [fwd.get(e, 0) + bwd.get(e, 0) for e in edges]        # METRIC = total citation count (undirected)
    charge = [bwd.get(e, 0) - fwd.get(e, 0) for e in edges]        # DIRECTION = time arrow (later->earlier dominant)
    refute = [1 if sign.get(e, 0) < 0 else 0 for e in edges]        # SIGN = build vs refute (the second charge channel)
    return ids, edges, weights, charge, refute


def amsc_index(recs, path):
    """The AMSC-attested findings index — NDJSON, one attested record per finding (srmech-discoverable). Content-
    addressed by each finding's sha256; the INDEX itself is sha256'd (the catalog fingerprint)."""
    lines = []
    for fid in sorted(recs):
        r = recs[fid]
        lines.append(json.dumps({"mpr_version": "1.0", "data": {"id": "F%d" % fid, "title": r["title"],
                     "refs": ["F%d" % t for t, _ in r["refs"] if t in recs]},
                     "attestation": {"file": r["file"], "response_sha256": r["sha"], "parser_version": "findingsgenome/1"},
                     "rendering": {"cite_as": "F%d — %s" % (fid, r["title"])}}))
    body = "\n".join(lines)
    path.write_text(body)
    return sha256_bytes(body.encode()), len(lines)


def measure_curvature(ids, edges, weights, charge, refute):
    """The teachable moment, measured. A MONOLITH keeps the METRIC (nodes + undirected citation) and flattens the two
    directional channels: the TIME arrow (charge) and the BUILD/REFUTE sign (refute). Quantify what it loses."""
    n_edges = len(edges)
    directional = sum(1 for c in charge if c != 0)                 # edges carrying a net time arrow
    refutes = sum(refute)
    builds = n_edges - refutes
    # a real CURVATURE read: cycle_holonomy of the build/refute sign around a small loop of recent findings, if one
    # closes (a research loop = build...then...refute...then...build back = a turn a monolith flattens).
    top = ids[-40:]                                                # the most recent 40 findings (this era)
    ti = {v: k for k, v in enumerate(top)}
    lo_hi = {}
    for e, r in zip(edges, refute):
        a, b = ids[e[0]], ids[e[1]]
        if a in ti and b in ti:
            lo_hi[(min(ti[a], ti[b]), max(ti[a], ti[b]))] = r
    tri_hol = None
    adj = {}
    for (i, j) in lo_hi:
        adj.setdefault(i, set()).add(j); adj.setdefault(j, set()).add(i)
    for u in sorted(adj):
        ns = sorted(x for x in adj[u] if x > u)
        done = False
        for a in range(len(ns)):
            for b in range(a + 1, len(ns)):
                v, w = ns[a], ns[b]
                if w in adj.get(v, ()):
                    ch = [Fraction(lo_hi.get((u, v), 0), 3), Fraction(lo_hi.get((min(v, w), max(v, w)), 0), 3),
                          Fraction(lo_hi.get((min(u, w), max(u, w)), 0), 3)]
                    tri_hol = L.cycle_holonomy([(0, 1), (1, 2), (2, 0)], charges=ch, n=3)
                    done = True; break
            if done:
                break
        if done:
            break
    return {"n_findings": len(ids), "n_edges": n_edges, "directional_edges": directional,
            "build_edges": builds, "refute_edges": refutes, "sample_loop_holonomy": tri_hol}


def persist_genome(ids, edges, weights, charge, path):
    """Genome-native (F1213 codec): serialize the directed findings kernel to klein4 symbols -> kernel_pack ->
    genome_save (content-addressed, LOCAL). The findings genome IS a directed Class-L object."""
    def zig(n): return (n << 1) if n >= 0 else ((-n) << 1) - 1
    out = [len(ids)] + list(ids) + [len(edges)]
    for (i, j), w, c in zip(edges, weights, charge):
        out += [i, j, w, zig(c)]
    syms = []
    for v in out:
        digs = []; x = v
        while True:
            digs.append(x & 3); x >>= 2
            if x == 0:
                break
        syms.append(len(digs) & 3); syms.append((len(digs) >> 2) & 3); syms += digs
    strand = G.kernel_pack(syms, leaf_dim=LEAF, label="findings", the_one=COUPLE)
    if path.exists():
        shutil.rmtree(path, ignore_errors=True)
    info = G.genome_save(strand, str(path), COUPLE, labels=["findings"])
    size = sum(f.stat().st_size for f in path.rglob("*") if f.is_file())
    return info.get("body_sha256"), size


def main():
    OUTDIR.mkdir(parents=True, exist_ok=True)
    print("=== R-RBS-LM-FINDINGSGENOME — the research record as a directed, AMSC-attested Class-L genome (LOCAL) ===\n")
    recs = parse_findings()
    print("(1) parsed %d findings (id = finding number = the TIME index)" % len(recs))
    ids, edges, weights, charge, refute = build_directed_graph(recs)
    print("(2) directed signed graph: %d nodes, %d edges" % (len(ids), len(edges)))
    sha_ix, nlines = amsc_index(recs, OUTDIR / "findings_index.ndjson")
    print("(3) AMSC-attested index -> findings_index.ndjson  (%d records, catalog sha %s..)" % (nlines, sha_ix[:12]))
    m = measure_curvature(ids, edges, weights, charge, refute)
    print("(4) THE TEACHABLE MOMENT — what a MONOLITH flattens:")
    print("     metric (a monolith KEEPS): %d findings, %d undirected citations" % (m["n_findings"], m["n_edges"]))
    print("     curvature (a monolith LOSES): %d directional (time-arrow) edges, %d BUILD vs %d REFUTE edges"
          % (m["directional_edges"], m["build_edges"], m["refute_edges"]))
    lh = m["sample_loop_holonomy"]
    if lh:
        print("     a research LOOP's build/refute holonomy = %s balanced=%s (nonzero => the record TURNED — a "
              "monolith presenting the final state erases this)" % (lh["holonomies"], lh["balanced"]))
    body_sha, size = persist_genome(ids, edges, weights, charge, OUTDIR / "findings.genome")
    print("(5) genome-native persist -> findings.genome (content-addressed body_sha %s.., %d B, LOCAL test)" % ((body_sha or "----")[:12], size))
    print("\nVERDICT: the findings are a DIRECTED, SIGNED, TIME-PRESERVING Class-L genome — srmech-discoverable (AMSC\n"
          "index) + genome-native. The %d REFUTE edges + the directional time-arrow ARE the curvature a monolithic\n"
          "MFO/notebook integration would flatten (it keeps the %d nodes + undirected citations = the metric, loses\n"
          "which-turned-on-which-when). Preserve the linear record AS a directed genome; integrate to MFO as a READ."
          % (m["refute_edges"], m["n_findings"]))


if __name__ == "__main__":
    main()
