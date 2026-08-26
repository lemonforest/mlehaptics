r"""R-RBS-LM-RELEDGES (F756) — the relation-edges rung BEYOND the F754 undirected co-occurrence tier.

The F754 relational tier answers "what is X NEAR" via an UNDIRECTED, UNTYPED co-occurrence graph (dense_adjacency
symmetrises -> A[s][o] == A[o][s]; direction discarded). The user's rung-beyond: a typed/DIRECTED relation —
subject —relation→ object — which is what the input-ride (F753) already half-touches (the FRAME word steers) and what
current-gen LLMs implicitly carry. This prototype builds it srmech-natively and shows it holds information the
undirected tier throws away.

THE FRAMEWORK-NATIVE MAPPING (no hand-rolled direction math — every piece is a named srmech op / class):
  * DIRECTION   = Class-L DIRECTED Hermitian: srmech.amsc.laplacian.magnetic_laplacian (q-phase encodes a_ij - a_ji,
                  the net flow). The plain undirected co-occurrence (F754) is dense_adjacency = the SYMMETRIC part =
                  the chirality-COLLAPSED projection (phase discarded). F357/F372.
  * RELATION    = the FRAME word (F753): the function word(s) BETWEEN two content words label the edge (subject REL
                  object). F753 promoted the steer from "bias the walk" to "name the edge."
  * s<->o SWAP  = Class-C chiral flip; the undirected tier is |directed| with the chiral phase magnitude-collapsed
                  (Class-K). This is exactly F552: biology runs the chirality-COLLAPSED projection; the directed/typed
                  graph is the fuller-chirality object. The reading order of an English sentence (S-V-O) IS a
                  directional signal — the sentence is a directed story (the user's "etak-walk the input").

MEASUREMENTS:
  (1) extract directed typed triples (subject, relation, object) from real simplewiki sentences (reading order =
      direction; the intervening function words = relation label).
  (2) magnetic_laplacian (Class L) over the directed graph IS Hermitian -> real eigenvalues (verify) -> a valid
      spectral object, unlike a naive asymmetric adjacency.
  (3) the magnetic off-diagonal PHASE is non-zero exactly for the directionally-asymmetric pairs; dense_adjacency
      (the F754 tier) reports those same pairs symmetric -> direction GONE. Print the most-asymmetric pairs + a
      sample relation label for each.

srmech 0.7.5rc149. No abs() (Class-K magnitude via srmech where needed); no CAD; CC-BY-SA simplewiki source.
Run: /tmp/srmech_rc149/venv/bin/python3 docs/srmech/rbs_lm_research/R-RBS-LM-RELEDGES_...py
"""
import json
import re
from pathlib import Path
import srmech
from srmech.amsc import laplacian as L
from srmech.amsc import cascade

ART = Path.home() / "corpora" / "wikipedia" / "simplewiki_extracted" / "articles.jsonl"
N_ARTICLES = 400
TOPN = 160                       # content-word nodes (eig-tractable)
Q = 0.25                         # magnetic charge: phase = 2*pi*q*(a_ij - a_ji); q=0.25 -> net +-1 gives +-90deg
# function words = the RELATION-LABEL vocabulary (they name edges; they are never subjects/objects). Class-aligned with
# the F751 ROUTING_STOPLIST insight (delexical words carry relation, not topic).
FUNC = frozenset("""a an the is are was were be been being of in on to by with from as at for and or that which who
whom whose this these those it its their his her they he she we you i but not no than then so such into over under
between through during before after above below up down out off only also can could will would shall should may might
must do does did has have had having about against among around because while when where why how what whom""".split())


def sentences(text):
    for s in re.split(r"[.!?]+", text):
        yield s


def content_and_frame(sent):
    """Return the token stream tagged content/frame: [(word, is_content), ...] in reading order."""
    out = []
    for w in re.findall(r"[a-z]+", sent.lower()):
        if len(w) < 3:
            continue
        out.append((w, w not in FUNC))
    return out


def main():
    print(f"=== R-RBS-LM-RELEDGES — directed/typed relations (magnetic Laplacian) vs F754 undirected co-occurrence "
          f"(srmech {srmech.__version__}) ===\n")
    texts = []
    with open(ART) as f:
        for i, line in enumerate(f):
            if i >= N_ARTICLES:
                break
            try:
                texts.append(json.loads(line).get("text", ""))
            except ValueError:
                continue

    # (1) extract directed typed triples ----------------------------------------------------------------------
    freq = {}
    dcount = {}                                  # (subj, obj) -> directed count (reading order = direction)
    triples = {}                                 # (subj, rel, obj) -> count
    for t in texts:
        for sent in sentences(t):
            toks = content_and_frame(sent)
            last_c, rel_buf = None, []
            for w, is_c in toks:
                if is_c:
                    freq[w] = freq.get(w, 0) + 1
                    if last_c is not None and last_c != w:
                        rel = " ".join(rel_buf) if rel_buf else "·"
                        dcount[(last_c, w)] = dcount.get((last_c, w), 0) + 1
                        triples[(last_c, rel, w)] = triples.get((last_c, rel, w), 0) + 1
                    last_c, rel_buf = w, []
                else:
                    if last_c is not None:
                        rel_buf.append(w)
    top = sorted(freq, key=lambda w: -freq[w])[:TOPN]
    idx = {w: i for i, w in enumerate(top)}
    n = len(top)
    print(f"corpus: {len(texts)} simplewiki articles -> {len(freq)} content words, {len(dcount)} directed pairs, "
          f"{len(triples)} typed triples; spectral surface = top {n} content words\n")

    # directed edges among the top-N (asymmetric weights) + the symmetric collapse (the F754 tier)
    dedges, dweights = [], []
    sym = {}
    for (a, b), c in dcount.items():
        if a in idx and b in idx:
            dedges.append((idx[a], idx[b])); dweights.append(float(c))
            key = (idx[a], idx[b]) if idx[a] < idx[b] else (idx[b], idx[a])
            sym[key] = sym.get(key, 0.0) + c

    # (2) magnetic Laplacian (Class L, directed Hermitian) — verify Hermitian => real eigenvalues -----------
    Lm = L.magnetic_laplacian(n, dedges, dweights, q=Q)
    evals, _ = L.hermitian_eigendecompose(Lm)
    max_imag = cascade.magnitude(max((ev.imag if isinstance(ev, complex) else 0.0) for ev in evals)) \
        if any(isinstance(ev, complex) for ev in evals) else 0.0
    print("--- (2) the directed graph's magnetic Laplacian (Class L) is HERMITIAN => real spectrum ---")
    print(f"   n={n}, q={Q}; eigenvalues real? max|Im(λ)| = {max_imag:.2e}  (≈0 => Hermitian, a valid spectral object)")
    print(f"   λ range: [{min(ev.real if isinstance(ev,complex) else ev for ev in evals):.3f}, "
          f"{max(ev.real if isinstance(ev,complex) else ev for ev in evals):.3f}]\n")

    # (3) the asymmetric pairs: directed carries it, the F754 undirected tier collapses it ------------------
    asym = sorted(((a, b, c, dcount.get((b, a), 0)) for (a, b), c in dcount.items()
                   if a in idx and b in idx and c != dcount.get((b, a), 0)),
                  key=lambda r: -(r[2] - r[3]))[:8]
    print("--- (3) DIRECTION is real: the magnetic phase keeps s→o ≠ o→s; the F754 undirected tier collapses it ---")
    print(f"   {'subject':>12} {'object':<12} {'s→o':>4} {'o→s':>4}  {'magnetic Lᵢⱼ (re, im)':<26} sample relation")
    for a, b, cfwd, cbak in asym:
        i, j = idx[a], idx[b]
        e = Lm[i][j]
        re_, im_ = (e.real, e.imag) if isinstance(e, complex) else (e, 0.0)
        # a sample typed triple for this ordered pair (the FRAME word that labelled the edge)
        rels = sorted(((r, c) for (s, r, o), c in triples.items() if s == a and o == b), key=lambda x: -x[1])
        rel = rels[0][0] if rels else "·"
        symc = sym.get((i, j) if i < j else (j, i), 0.0)
        print(f"   {a:>12} {b:<12} {cfwd:>4} {cbak:>4}  re={re_:+.2f} im={im_:+.2f}  ({a} —{rel}→ {b}); "
              f"undirected={symc:.0f} both ways")
    print("\n   -> the off-diagonal phase ROTATES with the net direction (s→o − o→s); dense_adjacency (F754) reports the")
    print("      SAME pair symmetric ('undirected=… both ways') — direction GONE (the chirality-collapsed projection, F552).")
    print(f"   CAVEAT (honest): at fixed q={Q} the phase is periodic in net with period 1/q={int(1/Q)}, so LARGE net flows")
    print("      ALIAS (e.g. net=176 wraps back onto the real axis). Clean for small net (±1,±2); for a monotone read pick")
    print(f"      q < 1/(2·net_max). The robust fact: the Hermitian object DEPENDS on the directed counts; the F754")
    print("      undirected tier is blind to them. (Candidate UPSTREAM note: a net-normalised magnetic Laplacian.)")

    print("\n--- sample TYPED triples (subject —FRAME→ object), single frame-word label = the rung beyond 'X is near Y' ---")
    typed = [((s, r, o), c) for (s, r, o), c in triples.items() if r != "·" and " " not in r]
    for (s, r, o), c in sorted(typed, key=lambda x: -x[1])[:15]:
        print(f"   {s:>14} —{r:^6}→ {o:<14} (×{c})")
    print("   (crude first-cut extractor — captures the function word(s) between content words; 'the' rows are mostly")
    print("    'X of the Y' with the multi-word label dropped. 'than'/'before'/'and' rows are clean typed relations.)")

    print("\nVERDICT: the typed/directed relation graph is a Class-L magnetic-Laplacian object (Hermitian, real")
    print("  spectrum); its phase keeps subject→object direction + the FRAME word names the edge — both DISCARDED by")
    print("  the F754 undirected tier (= the symmetric/chirality-collapsed projection, F552). This is the rung beyond")
    print("  'what is X near': 'X does/has/is-part-of Y'. Next: wire a directed read into Siona (relation-typed answers).")


if __name__ == "__main__":
    main()
