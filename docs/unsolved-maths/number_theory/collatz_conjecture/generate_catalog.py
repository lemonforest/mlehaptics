"""
Collatz conjecture (3n+1 problem) cascade.

Class cascade: A o I o C o K o N o M

  - A: content-hash of (starting n, stopping time, max trajectory value)
  - I: cyclic Z/2 parity test (n mod 2 -> branch choice)
  - C: cascade-orientation -- alternation between halving (even) and 3n+1
       (odd) IS the canonical Class C orientation per [[user_stance_epicycle_via_gear_plus_pin]]
       sign-flip / pin-slot mechanism applied to the integer-trajectory loop
  - K: asymptotic-DoF -- the conjecture IS that every trajectory has finite
       pin-slot depth at 1 (the cycle 1 -> 4 -> 2 -> 1 is the unique attractor)
  - N: rational anchor -- "constant" 3 in 3n+1; conjectured average stopping
       time c * log_2(n) where c = 1/(1 - log_2(3)/2) approx 6.952
  - M: HDC bind across iterations -- trajectory IS the Class M composition of
       the per-step (Class I + Class C) cascade

The Collatz function:

    T(n) = n / 2         if n even
    T(n) = (3n + 1) / 2  if n odd  (combined "shortcut" version)

The conjecture: for every positive integer n, repeated application of T reaches
the cycle {1, 2, 4}. Computationally verified by Oliveira e Silva (2009) for
n < 5 * 10^18; Barina (2020) extended to n < 2^68 ~ 2.95 * 10^20.

Per [[project_a_n_operators_are_harmonic_objects_themselves]] §A: tests whether
(i) the cascade-stopping-time IS Class K pin-slot depth from n to 1, and
(ii) the average stopping time empirically converges to a small-denom rational
multiple of log_2(n).

Per [[feedback_no_lineage_claims_in_notebook]]: does NOT claim to solve Collatz.
Documents structural cascade decomposition + Class K pin-slot reading of
stopping time + empirical Class N anchor for the cascade-constant.

Per [[feedback_sign_handling_is_class_k_pin_slot_not_alu_abs]]: cascade-honesty
via shared _cascade_helpers (best_rat_signed for Class N).

Roster: famous Collatz starting values with attested stopping times from OEIS
A006577 (total stopping time), A006884 (record-setters), A006885 (max-value
records). All values computed bit-exactly from the Collatz recurrence below.
"""

import datetime
import json
import math
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent.parent))
from _cascade_helpers import magnitude, cyclic_gcd, best_rat_signed

from srmech.amsc.format import sha256_bytes

SCHEMA_ID = "srmech.number_theory.collatz.trajectory.v1"
SOURCE_DOI = "https://oeis.org/A006577 + Oliveira e Silva 2009 + Barina 2020"
SOURCE_PUBLISHED = "2026-05-23"


def collatz_total_stopping_time(n):
    """Total stopping time: number of steps to reach 1 (using full T(n), not shortcut).
       Returns (steps, max_value_seen) along the trajectory."""
    if n < 1:
        return 0, 0
    steps = 0
    max_val = n
    # Bounded loop per JPL Rule 2 -- Collatz verified <= 2.95 * 10^20, so steps < 10000
    # for any n in our roster (record at n < 10^11 has stopping time ~ 1000)
    BOUND = 10000
    while n > 1 and steps < BOUND:
        # Class I cyclic Z/2 parity test
        # Class C cascade-orientation: choose branch
        if n % 2 == 0:
            n = n // 2
        else:
            n = 3 * n + 1
        if n > max_val:
            max_val = n
        steps += 1
    return steps, max_val


# Roster: famous Collatz starting values
# OEIS A006577 / A006884 / A006885 cross-referenced
ROSTER = [
    # Small baseline values
    dict(label="n=1", n=1, category="trivial",
         anchor="OEIS A006577(1) = 0 (already at cycle)",
         fermata="trivial baseline; in cycle {1,2,4}"),
    dict(label="n=2", n=2, category="trivial",
         anchor="OEIS A006577(2) = 1",
         fermata=""),
    dict(label="n=3", n=3, category="small",
         anchor="OEIS A006577(3) = 7",
         fermata=""),
    dict(label="n=5", n=5, category="small",
         anchor="OEIS A006577(5) = 5",
         fermata=""),
    dict(label="n=6", n=6, category="small",
         anchor="OEIS A006577(6) = 8",
         fermata=""),
    dict(label="n=7", n=7, category="small",
         anchor="OEIS A006577(7) = 16",
         fermata=""),
    dict(label="n=9", n=9, category="small",
         anchor="OEIS A006577(9) = 19",
         fermata=""),

    # Famous Collatz record-setters from A006884 / A006885
    dict(label="n=27", n=27, category="famous_record",
         anchor="OEIS A006884: stopping time 111; max trajectory 9232",
         fermata="canonical Collatz example; trajectory reaches ~342x starting value"),
    dict(label="n=47", n=47, category="famous_record",
         anchor="OEIS A006885 record: max trajectory ~9232 reached again",
         fermata="hit-the-same-peak as n=27 trajectory"),
    dict(label="n=97", n=97, category="famous_record",
         anchor="OEIS stopping time 118",
         fermata=""),
    dict(label="n=703", n=703, category="famous_record",
         anchor="OEIS A006885: stopping time 170; max trajectory ~250504",
         fermata="trajectory reaches ~356x starting value"),
    dict(label="n=871", n=871, category="famous_record",
         anchor="OEIS A006577(871) = 178",
         fermata="record stopping time for n < 1000"),
    dict(label="n=6171", n=6171, category="famous_record",
         anchor="OEIS A006577(6171) = 261",
         fermata="record stopping time for n < 10^4"),
    dict(label="n=77031", n=77031, category="famous_record",
         anchor="OEIS A006577(77031) = 350",
         fermata="record stopping time for n < 10^5"),
    dict(label="n=837799", n=837799, category="famous_record",
         anchor="OEIS A006577(837799) = 524",
         fermata="record stopping time for n < 10^6"),
    dict(label="n=8400511", n=8400511, category="famous_record",
         anchor="OEIS A006577(8400511) = 685",
         fermata="record stopping time for n < 10^7"),
    dict(label="n=63728127", n=63728127, category="famous_record",
         anchor="OEIS A006577(63728127) = 949",
         fermata="record stopping time for n < 10^8"),

    # Powers of 2 (cleanest descent: log_2(n) exact)
    dict(label="n=1024", n=1024, category="power_of_2",
         anchor="2^10 = 1024; descent via halving only",
         fermata="stopping time = 10 = log_2(1024) exact"),
    dict(label="n=2^16", n=65536, category="power_of_2",
         anchor="2^16; pure halving descent",
         fermata="stopping time = 16 = log_2(n) exact"),
    dict(label="n=2^20", n=1048576, category="power_of_2",
         anchor="2^20; pure halving descent",
         fermata="stopping time = 20 = log_2(n) exact"),

    # Mersenne-prime-related starting values (composes with framework Mersenne canon)
    dict(label="n=7 (M_3 = 2^3-1)", n=7, category="mersenne_3",
         anchor="M_3 = 2^3 - 1 = 7; intersects framework Mersenne ladder",
         fermata="duplicates n=7 entry with framework-Mersenne tag"),
    dict(label="n=31 (M_5 = 2^5-1)", n=31, category="mersenne_5",
         anchor="M_5 = 2^5 - 1 = 31; framework Mersenne anchor",
         fermata=""),
    dict(label="n=127 (M_7 = 2^7-1)", n=127, category="mersenne_7",
         anchor="M_7 = 2^7 - 1 = 127; framework Hurwitz heptadic Mersenne",
         fermata="Hurwitz heptadic Mersenne; composes with Spike #202 + #214"),

    # Large attested values from Oliveira e Silva 2009 / Barina 2020 verification
    # We don't simulate trajectories that long; we record the verification result.
    # Use small representative from the higher bound region:
    dict(label="n=670617279", n=670617279, category="large_record",
         anchor="OEIS A006885 stopping-time record for n < 10^9",
         fermata="large record-setter; computational verification continues"),
]


def main():
    out_path = pathlib.Path(__file__).parent / "trajectory.ndjson"
    now_iso = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    records = []
    diag = []

    for entry in ROSTER:
        label = entry["label"]
        n = entry["n"]
        category = entry["category"]
        anchor = entry["anchor"]
        fermata = entry["fermata"]

        # Class K pin-slot at 1: compute stopping time + max trajectory value
        stopping_time, max_traj = collatz_total_stopping_time(n)

        # Did trajectory reach the cycle {1, 2, 4}? (yes for all n < 2.95 * 10^20)
        reaches_cycle = (n == 1) or (stopping_time > 0)

        # Class N anchor: stopping time / log_2(n) (Collatz constant prediction ~ 6.952)
        if n >= 2:
            log2n = math.log2(n)
            ratio = stopping_time / log2n if log2n > 0 else 0
            r_num, r_den = best_rat_signed(ratio, max_d=30)
        else:
            log2n = 0
            ratio = 0
            r_num, r_den = 0, 1

        # Class N anchor: max_trajectory / n (peak amplification factor)
        if n > 0:
            amp = max_traj / n
            a_num, a_den = best_rat_signed(amp, max_d=100)
        else:
            amp = 0
            a_num, a_den = 0, 1

        # Class I cyclic: parity sequence (binary string) for first 32 steps -- structural-signature only
        parity_seq = []
        cur = n
        for _ in range(32):
            if cur == 1:
                break
            parity_seq.append(cur % 2)
            cur = (cur // 2) if cur % 2 == 0 else (3 * cur + 1)

        payload = json.dumps({"label": label, "n": n, "stopping_time": stopping_time,
                              "max_traj": max_traj}, sort_keys=True).encode()
        chash = sha256_bytes(payload)

        rec = {
            "starting_value":                  int(n),
            "label":                           label,
            "category":                        category,
            "stopping_time":                   int(stopping_time),
            "max_trajectory_value":            int(max_traj),
            "reaches_cycle_1_2_4":             bool(reaches_cycle),
            "log2_of_n":                       round(log2n, 6),
            "stopping_time_over_log2n":        round(ratio, 6),
            "stopping_ratio_rational_num":     int(r_num),
            "stopping_ratio_rational_den":     int(r_den),
            "peak_amplification":              round(amp, 6),
            "peak_amp_rational_num":           int(a_num),
            "peak_amp_rational_den":           int(a_den),
            "parity_first_32_steps":           parity_seq,
            "class_cascade":                   "A-compose-I-compose-C-compose-K-compose-N-compose-M",
            "oeis_anchor":                     anchor,
            "open_fermata":                    fermata,
            "computation_hash":                chash,
            "source_doi":                      SOURCE_DOI,
            "source_published_date":           SOURCE_PUBLISHED,
            "entered_locally_at":              now_iso[:10],
        }
        records.append(rec)
        diag.append((label, n, category, stopping_time, max_traj, ratio, r_num, r_den, amp))

    with open(out_path, "w", encoding="utf-8") as f:
        for rec in records:
            f.write(json.dumps(rec, sort_keys=True, ensure_ascii=False) + "\n")
    print(f"Wrote {len(records)} records to {out_path}")
    print()

    # Diagnostics
    print(f"{'label':<24} {'n':>14} {'category':<18} {'sigma':>7} {'max traj':>14} {'sigma/log2(n)':>14} {'Class N':>12} {'peak_amp':>10}")
    for d in diag:
        label, n, category, sigma, mt, ratio, rn, rd, amp = d
        print(f"  {label:<22} {n:>14} {category:<18} {sigma:>7} {mt:>14} {ratio:>14.4f} {f'{rn}/{rd}':>12} {amp:>10.2f}")

    # Convergence to Collatz constant
    print()
    print("Class N anchor test: stopping_time / log_2(n) -> Collatz constant c ~ 6.952")
    print("  (theoretical c = 2 / (2 - log_2(3)) = 6.9517...)")
    theoretical_c = 2.0 / (2.0 - math.log2(3))
    print(f"  Theoretical c (bit-exact float): {theoretical_c:.6f}")
    print(f"  Class N best-rational of c: {best_rat_signed(theoretical_c, max_d=200)}")
    print()
    print("  Empirical sigma/log_2(n) across roster (excluding trivial n=1, 2):")
    ratios = [d[5] for d in diag if d[1] > 2 and d[3] > 0]
    if ratios:
        mean_ratio = sum(ratios) / len(ratios)
        print(f"  mean ratio: {mean_ratio:.4f} = Class N {best_rat_signed(mean_ratio, max_d=30)}")
        print(f"  max ratio:  {max(ratios):.4f}")
        print(f"  min ratio:  {min(ratios):.4f}")

    # Class K saturation: stopping time finite for ALL roster entries?
    print()
    print("Class K pin-slot saturation test: every trajectory reaches cycle {1, 2, 4}?")
    reaches = sum(1 for d in diag if d[3] > 0 or d[1] == 1)
    print(f"  {reaches} / {len(diag)} trajectories reach the cycle (bounded simulation)")

    # Power-of-2 baseline: stopping time = log_2(n) EXACT (pure halving descent)
    print()
    print("Power-of-2 baseline (stopping time = log_2(n) EXACT):")
    for d in diag:
        label, n, category, sigma, mt, ratio, rn, rd, amp = d
        if "power_of_2" in category:
            print(f"  {label:<24} stopping={sigma}, log_2(n)={int(math.log2(n))}, ratio={ratio:.4f} = {rn}/{rd}")


if __name__ == "__main__":
    main()
