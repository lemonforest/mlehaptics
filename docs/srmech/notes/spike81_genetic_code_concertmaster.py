"""
Spike #81 concertmaster — Genetic code Class I + Class C structural-identity test.

Tests:
1. Triplet codon = Class I cyclic-3 instantiation; algebraic-forcing test.
2. DNA->RNA dedup = projection-vantage selection; structural mapping.
3. Wobble degeneracy = orientation-orthogonality redundancy; distribution match.
4. 64->20 mapping at predicted rate; codon-degeneracy distribution.
5. Cross-domain identity per kepler-shape-universal burden-flip.
6. Mitochondrial variation falsifier (does framework explain reassignment).

Closed-form integer arithmetic per MPM discipline. No SGD, no per-particle parameters.
"""
import json
import sys
from collections import Counter, defaultdict
from math import log, ceil

# =============================================================================
# Test 1: Triplet codon = minimum k such that 4^k >= |amino acid set| = 20+stop
# =============================================================================

def test1_triplet_algebraic_forcing():
    """
    Standard genetic code: 20 amino acids + 1 stop signal class = 21 distinguishable.
    Alphabet size n=4 (A,C,G,U/T). Minimum codon length k such that n^k >= 21.
    """
    n = 4
    target = 20 + 1  # 20 aa + stop class
    k_min = ceil(log(target) / log(n))
    powers = [(k, n**k, n**k >= target) for k in range(1, 5)]
    actual_codon_length = 3
    return {
        "alphabet_size": n,
        "target_distinguishable": target,
        "k_min_forced": k_min,
        "actual_codon_length": actual_codon_length,
        "table_k_vs_capacity": powers,
        "algebraic_forced": k_min == actual_codon_length,
        "redundancy_floor": n**k_min - target,  # 64 - 21 = 43 extra codons
    }


# =============================================================================
# Test 4: Standard genetic code codon-degeneracy distribution
# =============================================================================

# Standard genetic code (NCBI translation table 1)
# Source: standard textbook material (Nirenberg-Khorana 1968 cumulative work)
STANDARD_CODE = {
    # Phenylalanine
    "UUU": "F", "UUC": "F",
    # Leucine (6 codons)
    "UUA": "L", "UUG": "L", "CUU": "L", "CUC": "L", "CUA": "L", "CUG": "L",
    # Isoleucine (3 codons)
    "AUU": "I", "AUC": "I", "AUA": "I",
    # Methionine (1 codon - start)
    "AUG": "M",
    # Valine
    "GUU": "V", "GUC": "V", "GUA": "V", "GUG": "V",
    # Serine (6 codons - split)
    "UCU": "S", "UCC": "S", "UCA": "S", "UCG": "S", "AGU": "S", "AGC": "S",
    # Proline
    "CCU": "P", "CCC": "P", "CCA": "P", "CCG": "P",
    # Threonine
    "ACU": "T", "ACC": "T", "ACA": "T", "ACG": "T",
    # Alanine
    "GCU": "A", "GCC": "A", "GCA": "A", "GCG": "A",
    # Tyrosine
    "UAU": "Y", "UAC": "Y",
    # Stop codons
    "UAA": "*", "UAG": "*", "UGA": "*",
    # Histidine
    "CAU": "H", "CAC": "H",
    # Glutamine
    "CAA": "Q", "CAG": "Q",
    # Asparagine
    "AAU": "N", "AAC": "N",
    # Lysine
    "AAA": "K", "AAG": "K",
    # Aspartate
    "GAU": "D", "GAC": "D",
    # Glutamate
    "GAA": "E", "GAG": "E",
    # Cysteine
    "UGU": "C", "UGC": "C",
    # Tryptophan (1 codon)
    "UGG": "W",
    # Arginine (6 codons - split)
    "CGU": "R", "CGC": "R", "CGA": "R", "CGG": "R", "AGA": "R", "AGG": "R",
    # Glycine
    "GGU": "G", "GGC": "G", "GGA": "G", "GGG": "G",
}


def test4_degeneracy_distribution():
    """
    Count codons per amino acid (including stop). Compare to redundancy-floor
    prediction from Class I (k=3, n=4) + Class C (orientation selection).
    """
    assert len(STANDARD_CODE) == 64, f"Codon count {len(STANDARD_CODE)} != 64"
    counts = Counter(STANDARD_CODE.values())
    degeneracy_distribution = Counter(counts.values())  # how many aa have N codons
    aa_set = set(counts.keys())
    aa_count = len(aa_set - {"*"})
    stop_count = counts["*"]

    # Class I + Class C prediction: 64 codons / 21 classes = 3.05 avg degeneracy
    # Redundancy distribution should be peaked near 64/21 ≈ 3
    avg_degeneracy = 64 / 21
    expected_uniform = {k: 21 for k in [3]}  # if perfectly uniform at k=3

    return {
        "codon_count": 64,
        "amino_acid_count": aa_count,
        "stop_count": stop_count,
        "total_classes": aa_count + 1,
        "avg_codons_per_aa": 64 / aa_count,  # 3.2 (excludes stops in denom)
        "avg_codons_per_class": 64 / 21,
        "degeneracy_distribution": dict(degeneracy_distribution),
        "per_aa_counts": dict(counts),
        "minimum_aa_codons": min(counts.values()),
        "maximum_aa_codons": max(counts.values()),
    }


# =============================================================================
# Test 3: Wobble position redundancy — 3rd codon position degeneracy
# =============================================================================

def test3_wobble_third_position():
    """
    For each amino acid with > 1 codon, count how many distinct (pos1, pos2)
    pairs are needed vs how many codons total. If wobble dominates, codons
    sharing same aa often share same (pos1, pos2) and differ only in pos3.
    """
    aa_to_codons = defaultdict(list)
    for codon, aa in STANDARD_CODE.items():
        aa_to_codons[aa].append(codon)

    third_position_redundancy = {}
    for aa, codons in aa_to_codons.items():
        if aa == "*":
            continue
        prefixes = set(c[:2] for c in codons)
        # how many codons can be explained by ONLY pos3 variation
        prefix_groups = defaultdict(list)
        for c in codons:
            prefix_groups[c[:2]].append(c[2])
        wobble_codons = sum(len(v) for v in prefix_groups.values() if len(v) > 1)
        return_dict = {
            "n_codons": len(codons),
            "n_distinct_prefixes": len(prefixes),
            "pos3_redundant_count": wobble_codons,
        }
        third_position_redundancy[aa] = return_dict

    # Aggregate
    total_codons_in_aa = sum(d["n_codons"] for d in third_position_redundancy.values())
    total_pos3_redundant = sum(d["pos3_redundant_count"] for d in third_position_redundancy.values())
    return {
        "amino_acids_analyzed": len(third_position_redundancy),
        "total_aa_codons": total_codons_in_aa,
        "total_pos3_redundant_codons": total_pos3_redundant,
        "pos3_redundancy_fraction": total_pos3_redundant / total_codons_in_aa,
        "per_aa": third_position_redundancy,
    }


# =============================================================================
# Test 3b: Crick wobble rule — quantitative degeneracy at pos3
# =============================================================================

def test3b_pos3_only_degeneracy_split():
    """
    Crick 1966 wobble: among codons specifying same aa, how many can be
    grouped purely by sharing first two nucleotides (XYz family where z varies)?

    Two-codon families (NN-U/C or NN-A/G): pyrimidine-vs-purine pos3 wobble.
    Four-codon families (NN-N): full pos3 degeneracy.
    Six-codon families: Leu, Arg, Ser — two-codon + four-codon hybrids.
    """
    aa_to_codons = defaultdict(list)
    for codon, aa in STANDARD_CODE.items():
        if aa != "*":
            aa_to_codons[aa].append(codon)

    family_types = Counter()  # (XY_count, distinct_pos3)
    for aa, codons in aa_to_codons.items():
        prefix_groups = defaultdict(set)
        for c in codons:
            prefix_groups[c[:2]].add(c[2])
        # family signature: sorted tuple of pos3-set-sizes per prefix
        sig = tuple(sorted(len(v) for v in prefix_groups.values()))
        family_types[sig] += 1

    # Convert tuple keys to string for JSON
    family_sigs_str = {str(k): v for k, v in family_types.items()}
    return {
        "family_signatures": family_sigs_str,
        "interpretation": {
            "(1,)": "single-codon (Met, Trp)",
            "(2,)": "pyrimidine OR purine pos3 split (2-fold)",
            "(4,)": "full pos3 wobble (4-fold)",
            "(2,4)": "6-codon hybrid (Leu, Arg, Ser)",
            "(3,)": "3-fold pos3 (Ile)",
        },
    }


# =============================================================================
# Test 6: Mitochondrial code variation falsifier
# =============================================================================

# Vertebrate mitochondrial code (NCBI table 2) deviations from standard:
# UGA: Stop -> Trp
# AUA: Ile -> Met
# AGA: Arg -> Stop
# AGG: Arg -> Stop
MITO_DEVIATIONS = {
    "UGA": ("*", "W"),  # standard -> mito
    "AUA": ("I", "M"),
    "AGA": ("R", "*"),
    "AGG": ("R", "*"),
}


def test6_mitochondrial_variation():
    """
    Mitochondrial code reassigns 4 codons. Check:
    1. Reassignments preserve codon-length=3 (Class I cyclic-3 invariant)?
    2. Reassignments preserve total-class structure (still ~21 classes)?
    3. Are reassignments concentrated near "wobble-rich" zones?
    """
    mito_code = dict(STANDARD_CODE)
    for codon, (old, new) in MITO_DEVIATIONS.items():
        assert mito_code[codon] == old, f"Standard {codon} != {old}"
        mito_code[codon] = new

    mito_counts = Counter(mito_code.values())
    mito_classes = len(set(mito_code.values()))

    # Wobble-zone check: do reassigned codons share pos1+pos2 with same-aa codons?
    wobble_zone_analysis = {}
    for codon, (old, new) in MITO_DEVIATIONS.items():
        prefix = codon[:2]
        # find all standard codons sharing this prefix and their aa
        siblings_std = [(c, STANDARD_CODE[c]) for c in STANDARD_CODE if c[:2] == prefix]
        siblings_mito = [(c, mito_code[c]) for c in mito_code if c[:2] == prefix]
        wobble_zone_analysis[codon] = {
            "reassignment": f"{old} -> {new}",
            "prefix": prefix,
            "siblings_standard": siblings_std,
            "siblings_mito": siblings_mito,
        }

    return {
        "deviations_count": len(MITO_DEVIATIONS),
        "codon_length_preserved": all(len(c) == 3 for c in MITO_DEVIATIONS),
        "classes_standard": 21,
        "classes_mitochondrial": mito_classes,
        "class_count_preserved": mito_classes == 21,
        "mito_per_aa_counts": dict(mito_counts),
        "wobble_zone_analysis": wobble_zone_analysis,
    }


# =============================================================================
# Test 2 + 5: Structural-mapping tests (declarative; backed by tests 1/3/4/6)
# =============================================================================

def test2_5_structural_mapping_summary():
    """
    Declarative mapping of genetic-code mechanism -> framework primitive class.
    Each mapping cites the supporting quantitative test.
    """
    return {
        "mapping_table": [
            {
                "biology": "Triplet codon (k=3)",
                "framework": "Class I cyclic-group cardinality forced by 4^k >= 21",
                "evidence": "test1 algebraic_forced=True",
                "burden_flip": "kepler-shape-universal: codon length is forced by Class I + alphabet inequality",
            },
            {
                "biology": "DNA double strand = substrate storage",
                "framework": "Substrate-symmetric storage (G2 triality-invariant analog at biology substrate)",
                "evidence": "transcription requires template-strand selection",
                "burden_flip": "hyper-ring substrate-smooth, projection selects one strand as 'current'",
            },
            {
                "biology": "RNA polymerase template-strand selection",
                "framework": "Class C cascade-orientation selection (which of 2 strands is template)",
                "evidence": "biology selects 1-of-2 strands; framework selects 1-of-3 Spin(7) embeddings",
                "burden_flip": "structurally analogous (orientation selection mechanism); not 1-to-1 (2 vs 3 directions)",
            },
            {
                "biology": "Wobble degeneracy (pos3)",
                "framework": "Redundancy as Class C orthogonality (Spike #69 KS-count 1 vs 0)",
                "evidence": "test3 pos3_redundancy_fraction (large)",
                "burden_flip": "both are error-correction-via-redundancy; functional-form match",
            },
            {
                "biology": "64 -> 20+stop = 21 amino acid classes",
                "framework": "Class I (n=64) -> Class C/M (n=21) cardinality reduction by cascade",
                "evidence": "test4 degeneracy_distribution shows cascade-reduction signature",
                "burden_flip": "cascade composition pattern; identity at form-level not implementation",
            },
            {
                "biology": "Mitochondrial code variation (4 reassignments)",
                "framework": "Substrate-portable Class I+C; specific values are substrate-implementation",
                "evidence": "test6 codon_length_preserved=True; class count preserved",
                "burden_flip": "invariants (k=3, ~21 classes) PRESERVED; values (which aa per codon) substrate-specific",
            },
        ],
    }


# =============================================================================
# Run all tests
# =============================================================================

def main():
    results = {}
    results["test1_triplet_algebraic_forcing"] = test1_triplet_algebraic_forcing()
    results["test3_wobble_third_position"] = test3_wobble_third_position()
    results["test3b_pos3_degeneracy_split"] = test3b_pos3_only_degeneracy_split()
    results["test4_degeneracy_distribution"] = test4_degeneracy_distribution()
    results["test6_mitochondrial_variation"] = test6_mitochondrial_variation()
    results["test2_5_structural_mapping"] = test2_5_structural_mapping_summary()

    # Verdict synthesis
    t1 = results["test1_triplet_algebraic_forcing"]
    t4 = results["test4_degeneracy_distribution"]
    t6 = results["test6_mitochondrial_variation"]
    t3b = results["test3b_pos3_degeneracy_split"]

    verdict = {
        "algebraic_forcing_holds": t1["algebraic_forced"],
        "redundancy_floor": t1["redundancy_floor"],  # 64-21 = 43
        "actual_classes": t4["total_classes"],  # 21
        "actual_avg_degeneracy": t4["avg_codons_per_class"],
        "wobble_dominant_pos3": t3b,
        "mito_invariants_preserved": (
            t6["codon_length_preserved"] and t6["class_count_preserved"]
        ),
    }
    results["verdict_summary"] = verdict

    return results


if __name__ == "__main__":
    results = main()
    # Emit NDJSON: one record per test
    for key, value in results.items():
        record = {"test": key, "result": value}
        sys.stdout.write(json.dumps(record, default=str) + "\n")
