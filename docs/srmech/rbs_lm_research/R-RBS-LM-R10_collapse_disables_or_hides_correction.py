"""#855/F352 follow-on — does the iω₇-COLLAPSE (the observable language/NN render, F350) DESTROY
the error-correction, or merely HIDE it from an observer confined to the collapsed sector?

Triality new-question (F352): "is the EC structure destroyed by the projection, or merely hidden
from the observer's vantage?" Ties F350 (collapse drops iω₇), F294 (codon render is k=2-DETECT,
no k=3-CORRECT), F353 (full store: correct 1 / detect 3).

Setup: the F259 CPT-orbit store (4 sectors s_i = flip_i(c)); corrupt 1 sector. Two observers:
  FULL    -- sees all 4 sectors, both axes (γ₅, iω₇). Per-coord majority over inverted views.
  COLLAPSED -- the bipolar render: collapse iω₇ (keep γ₅ only) BEFORE reconstructing.
Measure detect / correct for each, + a PURE-iω₇-corruption probe (corrupt only the iω₇ bit) to
test whether the collapsed observer can even SEE an iω₇-axis error.

klein-4: state = 2*(γ₅) + (iω₇); collapse = drop iω₇ = (v>>1)<<1.
srmech-native: klein4_random + klein4_chirality_flip_{gamma5,omega7}/cpt_mirror (involutions).

Run: /tmp/verify_srmech_v070rc25/bin/python docs/srmech/rbs_lm_research/R-RBS-LM-R10_collapse_disables_or_hides_correction.py
"""
import json
from pathlib import Path
import numpy as np
import srmech
from srmech.amsc import hdc

HERE = Path(__file__).parent
D, TRIALS = 512, 30


def flips():
    return [lambda v: v.copy(), hdc.klein4_chirality_flip_gamma5,
            hdc.klein4_chirality_flip_omega7, hdc.klein4_cpt_mirror]
def collapse(v): return (v >> 1) << 1           # drop iω₇ (the F350 bipolar render)
def per_coord_majority(cands):
    arr = np.stack(cands); out = np.zeros(arr.shape[1], dtype=arr.dtype)
    for j in range(arr.shape[1]):
        vals, cnts = np.unique(arr[:, j], return_counts=True); out[j] = vals[np.argmax(cnts)]
    return out


def main():
    print(f"#855 — does the iω₇-collapse DESTROY or HIDE error-correction (srmech {srmech.__version__}, D={D}, trials={TRIALS})")
    F = flips()
    agg = {k: 0.0 for k in ('full_correct', 'full_detect',
                            'coll_correct_g5', 'coll_correct_full', 'coll_detect',
                            'probe_g5_detect_full', 'probe_g5_detect_coll',
                            'probe_iw7_detect_full', 'probe_iw7_detect_coll')}
    rng0 = np.random.default_rng(20260604)
    for t in range(TRIALS):
        rng = np.random.default_rng(20260604 + t)
        c = hdc.klein4_random(D, seed=20260604 + t)
        sectors = [F[i](c) for i in range(4)]

        # --- random 1-sector corruption: FULL vs COLLAPSED reconstruction ---
        bad = int(rng.integers(0, 4))
        views = [sectors[i].copy() for i in range(4)]
        views[bad] = hdc.klein4_random(D, seed=int(rng.integers(1, 2**31)))
        # FULL observer
        full_c = [F[i](views[i]) for i in range(4)]
        rec_full = per_coord_majority(full_c)
        agg['full_correct'] += int(np.array_equal(rec_full, c))
        agg['full_detect'] += int(not all(np.array_equal(full_c[0], x) for x in full_c[1:]))
        # COLLAPSED observer (render iω₇-collapsed before reconstructing)
        coll_c = [collapse(F[i](collapse(views[i]))) for i in range(4)]
        rec_coll = per_coord_majority(coll_c)
        agg['coll_correct_g5'] += int(np.array_equal(rec_coll, collapse(c)))   # recovered the γ₅ axis?
        agg['coll_correct_full'] += int(np.array_equal(rec_coll, c))           # recovered full c? (iω₇ gone)
        agg['coll_detect'] += int(not all(np.array_equal(coll_c[0], x) for x in coll_c[1:]))

        # --- PURE-AXIS corruption probes: can each observer SEE a γ₅-only vs iω₇-only error? ---
        for axis, key in (('g5', 'probe_g5'), ('iw7', 'probe_iw7')):
            v2 = [sectors[i].copy() for i in range(4)]
            b = int(rng.integers(0, 4))
            # flip exactly one bit (one coordinate) on the chosen axis of sector b
            j = int(rng.integers(0, D))
            if axis == 'g5':
                v2[b][j] = v2[b][j] ^ 0b10   # toggle γ₅ bit
            else:
                v2[b][j] = v2[b][j] ^ 0b01   # toggle iω₇ bit
            fullc = [F[i](v2[i]) for i in range(4)]
            agg[f'{key}_detect_full'] += int(not all(np.array_equal(fullc[0], x) for x in fullc[1:]))
            collc = [collapse(F[i](collapse(v2[i]))) for i in range(4)]
            agg[f'{key}_detect_coll'] += int(not all(np.array_equal(collc[0], x) for x in collc[1:]))

    for k in agg: agg[k] /= TRIALS

    print("\n  1-sector corruption (unknown location):")
    print(f"    FULL observer (both axes):  correct(full c) {agg['full_correct']:.2f} | detect {agg['full_detect']:.2f}")
    print(f"    COLLAPSED observer (γ₅ only): correct(γ₅ axis) {agg['coll_correct_g5']:.2f} | correct(full c) {agg['coll_correct_full']:.2f} | detect {agg['coll_detect']:.2f}")
    print("\n  pure-axis corruption probes (can the observer SEE it?):")
    print(f"    γ₅-only error : FULL detect {agg['probe_g5_detect_full']:.2f} | COLLAPSED detect {agg['probe_g5_detect_coll']:.2f}")
    print(f"    iω₇-only error: FULL detect {agg['probe_iw7_detect_full']:.2f} | COLLAPSED detect {agg['probe_iw7_detect_coll']:.2f}")

    print("\n=== verdict ===")
    iw7_invisible = agg['probe_iw7_detect_coll'] < 0.2 and agg['probe_iw7_detect_full'] > 0.9
    g5_survives = agg['coll_correct_g5'] > 0.9 and agg['probe_g5_detect_coll'] > 0.9
    full_intact = agg['full_correct'] > 0.9
    print(f"  iω₇-axis errors INVISIBLE to the collapsed render (full sees them): {iw7_invisible}")
    print(f"  γ₅-axis EC SURVIVES the collapse (collapsed corrects/detects γ₅):   {g5_survives}")
    print(f"  FULL store still corrects (capability intact):                      {full_intact}")
    print(f"\n  ANSWER (destroyed vs hidden): AXIS-SPLIT.")
    print(f"   - The FULL store retains correct-1 ({agg['full_correct']:.2f}) -> the EC capability is NOT globally destroyed; it is")
    print(f"     HIDDEN from an observer confined to the collapsed (bipolar) render.")
    print(f"   - But the iω₇-AXIS EC is DESTROYED in the render: iω₇-only errors are invisible to it")
    print(f"     ({agg['probe_iw7_detect_coll']:.2f} vs full {agg['probe_iw7_detect_full']:.2f}), and full-c is unrecoverable ({agg['coll_correct_full']:.2f}).")
    print(f"   - The γ₅-AXIS EC SURVIVES ({agg['coll_correct_g5']:.2f}) -- the collapsed render is still a k>=2 detector on γ₅.")
    print(f"   => the collapse HIDES the cross-axis correction + DESTROYS the iω₇-axis half; matches F294 (observable")
    print(f"      render is detect-leaning / loses the order that would correct) and F350 (γ₅ kept, iω₇ destroyed).")

    out = {"partition": "R-RBS-LM-R10 (collapse: destroy vs hide EC)", "srmech_version": srmech.__version__,
           "D": D, "trials": TRIALS, "results": agg,
           "iw7_invisible_to_render": bool(iw7_invisible), "g5_ec_survives": bool(g5_survives),
           "full_store_intact": bool(full_intact)}
    (HERE / "R-RBS-LM-R10_results.json").write_text(json.dumps(out, indent=2, default=str))
    print(f"\n  Results: {HERE / 'R-RBS-LM-R10_results.json'}")


if __name__ == "__main__":
    main()
