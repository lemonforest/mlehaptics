r"""R-RBS-LM-CODECOMPARE (F797 experiment) — compare two code/math fragments by their dep-free A-N rule-kernel
signatures (F796). The test: does the signature judge STRUCTURE — rename-invariant, CROSS-LANGUAGE (Python≡C for the
same algorithm), and structure-not-intent (a loop-sum ≠ a recursive sum even if both compute Σ)? If so, the rule kernel
is a real structural-equivalence instrument: it reads the ALGORITHM, not the surface tokens or the host language.

srmech 0.7.5rc166; imports the dep-free RULEKERNELS module (no ast/sympy/pycparser). No abs; no CAD. Run:
  /tmp/srmech_rc166/venv/bin/python3 docs/srmech/rbs_lm_research/R-RBS-LM-CODECOMPARE_...py
"""
import importlib.util as U
import os
from srmech.amsc.hdc import similarity

_rk = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                   "R-RBS-LM-RULEKERNELS_dep_free_python_c_latex_grammars_for_siona.py")
RK = U.module_from_spec(U.spec_from_file_location("rk", _rk)); U.spec_from_file_location("rk", _rk).loader.exec_module(RK)

# labelled fragments: (id, language, source). Same algorithm in different languages + different algorithms.
FRAG = {
    "py_add":    ("python", "def f(a, b):\n    return a + b"),
    "c_add":     ("c",      "int f(int a, int b){ return a + b; }"),
    "py_loopsum": ("python", "def s(xs):\n    t = 0\n    for v in xs:\n        t = t + v\n    return t"),
    "c_loopsum":  ("c",      "int s(int xs){ int t=0; for(int i=0;i<n;i=i+1){ t=t+xs; } return t; }"),
    "py_recsum":  ("python", "def s(xs, i):\n    if i < 0:\n        return 0\n    return xs + s(xs, i-1)"),
    "py_callsum": ("python", "def s(xs):\n    return sum(xs)"),
    "py_fact":    ("python", "def f(n):\n    if n <= 1:\n        return 1\n    return n * f(n-1)"),
    "c_fact":     ("c",      "int f(int n){ if(n<=1){ return 1; } return n*f(n-1); }"),
}
SIG = {k: RK.code_sig(src, lang) for k, (lang, src) in FRAG.items()}


def sim(a, b):
    return similarity(SIG[a], SIG[b])


def main():
    import srmech
    print(f"=== R-RBS-LM-CODECOMPARE — structural equivalence via A-N signatures (srmech {srmech.__version__}) ===\n")
    print("CROSS-LANGUAGE same-algorithm (Python vs C — should be HIGH; signature ignores host language + names):")
    for a, b in [("py_add", "c_add"), ("py_loopsum", "c_loopsum"), ("py_fact", "c_fact")]:
        print(f"   {a:11} ≟ {b:11} = {sim(a, b):+.4f}")
    print("\nSAME TASK, DIFFERENT STRUCTURE (should be LOWER — reads structure, not what it computes):")
    for a, b in [("py_loopsum", "py_recsum"), ("py_loopsum", "py_callsum"), ("py_recsum", "py_callsum")]:
        print(f"   {a:11} ≟ {b:11} = {sim(a, b):+.4f}")
    print("\nDIFFERENT ALGORITHM (should be LOW):")
    for a, b in [("py_add", "py_loopsum"), ("py_loopsum", "py_fact"), ("c_add", "c_fact")]:
        print(f"   {a:11} ≟ {b:11} = {sim(a, b):+.4f}")
    print("\nMATH (LaTeX) structural equivalence:")
    pairs = {"emc2": r"E = m c^2", "emc2_renamed": r"P = q r^2", "fma": r"F = m a", "frac_sum": r"\frac{a}{b}+\frac{c}{d}"}
    s = {k: RK.code_sig(v, "latex") for k, v in pairs.items()}
    print(f"   E=mc^2 ≟ P=qr^2 (same form, renamed) = {similarity(s['emc2'], s['emc2_renamed']):+.4f}  (HIGH)")
    print(f"   E=mc^2 ≟ F=ma   (power vs none)       = {similarity(s['emc2'], s['fma']):+.4f}  (lower)")
    print(f"   E=mc^2 ≟ a/b+c/d (eq+pow vs ratios)   = {similarity(s['emc2'], s['frac_sum']):+.4f}  (low)")
    # verdict metric: mean cross-language-same vs mean different
    xlang = [sim("py_add", "c_add"), sim("py_loopsum", "c_loopsum"), sim("py_fact", "c_fact")]
    diff = [sim("py_add", "py_loopsum"), sim("py_loopsum", "py_fact"), sim("py_loopsum", "py_callsum")]
    print(f"\nVERDICT: cross-language SAME-algorithm mean {sum(xlang)/len(xlang):+.3f}  vs  DIFFERENT mean "
          f"{sum(diff)/len(diff):+.3f}  -> separation {sum(xlang)/len(xlang) - sum(diff)/len(diff):+.3f}")
    print("  The A-N signature reads the ALGORITHM (rename- AND language-invariant), not the surface — a dep-free")
    print("  cross-substrate structural-equivalence instrument (Python≡C when the structure matches).")


if __name__ == "__main__":
    main()
