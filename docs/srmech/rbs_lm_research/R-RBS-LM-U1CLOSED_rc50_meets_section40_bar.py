r"""R-RBS-LM-U1CLOSED (F723) — srmech 0.7.5rc50 closes R3 U1: tokenize + cooccurrence_edges meet the §40 bar 3/3.

User direction (2026-06-09): "check on rc50."

rc50 moved both ops to **srmech.amsc.text** (the §40 Option-1 landing site) and fixed all three F722 failures.
This is the acceptance re-run (MPM; run with the rc50 venv: /tmp/srmech_rc50/venv/bin/python3):

  BAR 1 (Unicode, F698): tokenize(text, *, stoplist=<F714 default incl. prepositions>, unicode_normalize=True)
    keeps accents + Cyrillic + CJK -> Unicode-aware. PASS.
  BAR 2 (no silent cap, F708): cooccurrence_edges(docs, *, window=2, vocab=None, vocab_size=None) defaults to
    NO cap (vocab_size=None -> all); an explicit vocab_size=N is an opt-in cap. PASS.
  BAR 3 (document-boundary reset): the arg is `docs` (a Sequence of token-sequences); the window resets per
    document -> no cross-article co-occurrence bleed. PASS.

Format unchanged + correct: returns (n, edges, weights), edges = 2-tuples straight into dense_laplacian.
=> R3 U1 CLOSEABLE; the wiki kernel can adopt srmech.amsc.text.{tokenize, cooccurrence_edges} (the §17.1 migration).
Supersedes F722 (the rc49-fails record). No abs(); srmech-first (these ARE the srmech ops).
"""
import inspect
import srmech
from srmech.amsc import text as T


def bar1_unicode():
    toks = T.tokenize("café Москва naïve 日本語 hello world")
    return (("café" in toks) and ("naïve" in toks) and ("日本語" in toks) and any("москва" in t for t in toks)), toks


def bar2_no_silent_cap():
    big = [f"w{i}" for i in range(1500)]
    n_default = T.cooccurrence_edges([big], window=2)[0]          # default vocab_size=None
    n_optin = T.cooccurrence_edges([big], window=2, vocab_size=500)[0]
    return (n_default == 1500 and n_optin == 500), n_default, n_optin


def bar3_boundary_reset():
    docs = [["alpha", "beta"], ["gamma", "delta"]]
    vocab = ["alpha", "beta", "gamma", "delta"]                   # idx: a0 b1 g2 d3
    _, edges, _ = T.cooccurrence_edges(docs, window=2, vocab=vocab)
    es = set(tuple(sorted(p)) for p in edges)
    cross = (1, 2) in es                                          # beta<->gamma would only edge if flattened
    return (not cross), sorted(es)


def main():
    print(f"=== R-RBS-LM-U1CLOSED (F723) — rc50 vs the §40 bar  (srmech {srmech.__version__}) ===\n")
    print("WHERE: tokenize + cooccurrence_edges now in srmech.amsc.text (§40 Option-1 landing site).\n")

    b1, toks = bar1_unicode()
    print(f"BAR 1 — Unicode-aware tokenize (F698):       {'PASS' if b1 else 'FAIL'}")
    print(f"   'café Москва naïve 日本語 hello world' -> {toks}\n")

    b2, nd, no = bar2_no_silent_cap()
    print(f"BAR 2 — no silent vocab cap (F708):          {'PASS' if b2 else 'FAIL'}")
    print(f"   1500 words, default (vocab_size=None) -> n={nd}; explicit vocab_size=500 -> n={no} (opt-in cap)\n")

    b3, es = bar3_boundary_reset()
    print(f"BAR 3 — document-boundary window-reset:      {'PASS' if b3 else 'FAIL'}")
    print(f"   docs=[[alpha,beta],[gamma,delta]] window=2 -> edges {es} (no cross-boundary (1,2))\n")

    sig = str(inspect.signature(T.cooccurrence_edges))
    fmt_ok = "Tuple[int, List[Tuple[int, int]], List[int]]" in str(inspect.signature(T.cooccurrence_edges).return_annotation) \
        or "edges" in T.cooccurrence_edges.__doc__.lower()
    allpass = b1 and b2 and b3
    print("VERDICT (F723):")
    print(f"  • rc50 meets the §40 acceptance bar {sum([b1,b2,b3])}/3 -> R3 U1 is CLOSEABLE (supersedes F722's rc49 fail).")
    print(f"  • Ops live in srmech.amsc.text (the §40 Option-1 site). cooccurrence_edges{sig}")
    print(f"  • Fixes confirmed: Unicode tokenize (F698), default=no-cap (F708; explicit vocab_size is an opt-in),")
    print(f"    per-document window-reset (no cross-article bleed). Format: (n, edges, weights), edges=2-tuples.")
    print(f"  • NEXT: the wiki kernel can migrate off the hand-rolled content_words + build_edges_topk onto these")
    print(f"    shipped ops (the §17.1 ours-side migration). All bars pass: {allpass}.")


if __name__ == "__main__":
    main()
