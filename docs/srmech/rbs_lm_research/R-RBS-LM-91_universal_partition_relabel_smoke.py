"""R-RBS-LM-91 — Re-abstract human-discipline labels to biology-agnostic
universal-NN partitions, then falsify.

User direction 2026-05-27:
> "do research that you did with imposed human domain partitions (math
> science etc) and do it again by abstracting it to a label that is not
> for only human NN explanations. and then we can start to try to
> falsify those partitions to find where they are real for a neural
> net storage architecture and not human made"

The user's biology-agnostic partition proposal (must work for any NN
storage, not human-only):
  1. MATH                    — first-order pattern / quantity irrep
  2. COMMUNICATION           — inter-individual signal share
  3. STRUCTURE-AND-ORDER     — regularity detection in environment
  4. PLACES-AND-THINGS       — spatial cognition

Re-label the 13 K-12-style subjects by which universal-NN partition
they instantiate (where defensible). Some subjects may be unclear or
multi-partition.

Then do two things:
  (A) Aggregate signature vectors by universal partition; see if
      members within a partition cluster (similar signature shape)
  (B) Do unbiased hierarchical clustering on signature vectors WITHOUT
      using the partition labels; see if natural clusters emerge

If (A) and (B) agree → universal partitions are real-ish for NN storage
If (A) and (B) disagree → partition predictions need revision
If (B) shows no natural clusters → signatures themselves are noise

Falsification questions:
  - Does reading+composition cluster (both should be COMMUNICATION)?
  - Does grammar cluster WITH them or apart (is grammar a separate
    meta-introspection that's not biology-agnostic)?
  - Does science cluster apart (its own STRUCTURE-AND-ORDER signature)?
  - Where do geography/scouting/history land (all PLACES-AND-THINGS?
    or does history split off as time-substrate)?
  - Where do arts/music/games/sports/cooking land naturally?
"""

import json
from pathlib import Path

import numpy as np


# Universal-NN-partition labels per user direction
# (None = withheld for natural-clustering verification)
PROPOSED_PARTITION = {
    "math":        "MATH",
    "reading":     "COMMUNICATION",
    "grammar":     "COMMUNICATION",  # decode-introspect-produce all same partition
    "composition": "COMMUNICATION",
    "science":     "STRUCTURE-AND-ORDER",
    "geography":   "PLACES-AND-THINGS",
    "scouting":    "PLACES-AND-THINGS",
    "history":     "PLACES-AND-THINGS",  # events-in-time as locations-in-time
    # The following are NOT pre-assigned — let them cluster naturally
    "music":       None,
    "art":         None,
    "games":       None,
    "sports":      None,
    "cooking":     None,
}


def load_results():
    """Load R-RBS-LM-89 results (9-operator signature vectors)."""
    p = (Path(__file__).parent /
         "R-RBS-LM-89_e_catalog_results.json")
    with open(p) as f:
        data = json.load(f)
    return data["results"]


def build_signature_matrix(results):
    """Return subject_names list and N x 9 signature matrix."""
    ops = ["B", "H", "N", "C", "I", "J", "D", "E", "F"]
    subjects = list(results.keys())
    M = np.zeros((len(subjects), len(ops)))
    for i, subj in enumerate(subjects):
        for j, op in enumerate(ops):
            M[i, j] = results[subj][op]["score"]
    return subjects, ops, M


def cosine_similarity(M):
    """Pairwise cosine similarity between rows of M."""
    norms = np.linalg.norm(M, axis=1, keepdims=True)
    norms_safe = np.where(norms > 0, norms, 1.0)
    M_norm = M / norms_safe
    return M_norm @ M_norm.T


def hierarchical_cluster_from_sim(sim, names):
    """Greedy single-linkage hierarchical cluster from a similarity
    matrix. Returns merge history.

    We compute this by hand rather than depending on scipy so we keep
    srmech-side discipline and explicit operations."""
    n = len(names)
    # Convert similarity to distance
    dist = 1.0 - sim
    # Set diagonal to inf so we don't self-merge
    dist = dist + np.eye(n) * 1e10

    # Active clusters: each subject starts as its own cluster
    clusters = {i: [names[i]] for i in range(n)}
    active = set(range(n))
    next_id = n

    merges = []

    # Use a working copy of distance matrix (will grow as we merge)
    D = dist.copy()
    # Track which row/col index belongs to which cluster id
    idx_to_id = {i: i for i in range(n)}
    id_to_idx = {i: i for i in range(n)}

    while len(active) > 1:
        # Find min-distance pair among active
        D_active = D[list(active)][:, list(active)]
        min_idx = np.unravel_index(np.argmin(D_active), D_active.shape)
        active_list = sorted(active)
        a_idx = active_list[min_idx[0]]
        b_idx = active_list[min_idx[1]]
        if a_idx == b_idx:
            break

        merge_dist = D[a_idx, b_idx]
        a_id = idx_to_id[a_idx]
        b_id = idx_to_id[b_idx]
        a_members = clusters[a_id]
        b_members = clusters[b_id]
        new_members = a_members + b_members

        clusters[next_id] = new_members
        active.discard(a_idx)
        active.discard(b_idx)
        # Add new cluster as new index
        new_row = np.minimum(D[a_idx], D[b_idx])  # single-linkage
        # Extend D matrix
        new_D = np.full((D.shape[0] + 1, D.shape[1] + 1), 1e10)
        new_D[:-1, :-1] = D
        new_D[:-1, -1] = new_row
        new_D[-1, :-1] = new_row
        D = new_D
        new_idx = D.shape[0] - 1
        idx_to_id[new_idx] = next_id
        id_to_idx[next_id] = new_idx
        active.add(new_idx)

        merges.append({
            "step": len(merges) + 1,
            "merged_a": a_members,
            "merged_b": b_members,
            "merge_dist": float(merge_dist),
            "merge_sim": float(1.0 - merge_dist),
            "result": new_members,
        })
        next_id += 1

    return merges


def aggregate_by_partition(subjects, M, partition_map):
    """Compute mean signature vector per partition."""
    partitions = {}
    for i, subj in enumerate(subjects):
        p = partition_map.get(subj)
        if p is None:
            continue
        partitions.setdefault(p, []).append((subj, M[i]))

    agg = {}
    for p, items in partitions.items():
        vecs = np.array([v for _, v in items])
        agg[p] = {
            "members": [s for s, _ in items],
            "mean": vecs.mean(axis=0),
            "std": vecs.std(axis=0),
            "n_members": len(items),
        }
    return agg


def within_partition_coherence(subjects, M, partition_map):
    """For each partition, compute mean pairwise cosine similarity
    among members. Higher = members signature-cluster together."""
    sim = cosine_similarity(M)
    name_to_idx = {s: i for i, s in enumerate(subjects)}

    coherence = {}
    partitions = {}
    for s, p in partition_map.items():
        if p is None or s not in name_to_idx:
            continue
        partitions.setdefault(p, []).append(name_to_idx[s])

    for p, idxs in partitions.items():
        if len(idxs) < 2:
            coherence[p] = {"members": [subjects[i] for i in idxs],
                             "mean_sim": None,
                             "n_pairs": 0}
            continue
        pair_sims = []
        for i in range(len(idxs)):
            for j in range(i + 1, len(idxs)):
                pair_sims.append(sim[idxs[i], idxs[j]])
        coherence[p] = {
            "members": [subjects[i] for i in idxs],
            "mean_sim": float(np.mean(pair_sims)),
            "min_sim": float(np.min(pair_sims)),
            "max_sim": float(np.max(pair_sims)),
            "n_pairs": len(pair_sims),
        }
    return coherence


def cross_partition_separation(subjects, M, partition_map):
    """Mean pairwise cosine similarity BETWEEN partitions.

    For partition pair (P, Q), compute mean sim across all (p_in_P,
    q_in_Q) pairs. Lower = better partition separation.
    """
    sim = cosine_similarity(M)
    name_to_idx = {s: i for i, s in enumerate(subjects)}
    partitions = {}
    for s, p in partition_map.items():
        if p is None or s not in name_to_idx:
            continue
        partitions.setdefault(p, []).append(name_to_idx[s])

    p_names = sorted(partitions.keys())
    cross = {}
    for i in range(len(p_names)):
        for j in range(i + 1, len(p_names)):
            P, Q = p_names[i], p_names[j]
            pair_sims = []
            for p_idx in partitions[P]:
                for q_idx in partitions[Q]:
                    pair_sims.append(sim[p_idx, q_idx])
            cross[(P, Q)] = float(np.mean(pair_sims))
    return cross


def main():
    print("=" * 78)
    print("R-RBS-LM-91 — Universal-NN-partition re-abstraction + falsification")
    print("=" * 78)
    print()

    results = load_results()
    subjects, ops, M = build_signature_matrix(results)

    print(f"Loaded {len(subjects)} subjects × {len(ops)} operators")
    print(f"Operators: {ops}")
    print()

    print("Proposed universal-NN partition map (per user direction):")
    print("-" * 78)
    for s in subjects:
        p = PROPOSED_PARTITION.get(s, "UNKNOWN")
        if p is None:
            p = "[withheld for natural clustering]"
        print(f"  {s:<14} -> {p}")
    print()

    # === (A) Partition-coherence test ===========================
    print("=" * 78)
    print("(A) WITHIN-PARTITION COHERENCE — do members of each universal")
    print("    partition share similar signature shape?")
    print("=" * 78)
    coherence = within_partition_coherence(subjects, M, PROPOSED_PARTITION)
    for p in sorted(coherence.keys()):
        c = coherence[p]
        members_str = ", ".join(c["members"])
        if c["n_pairs"] > 0:
            print(f"\n  [{p}]")
            print(f"    members: {members_str}")
            print(f"    mean pairwise sim: {c['mean_sim']:.3f}  "
                  f"(min={c['min_sim']:.3f}, max={c['max_sim']:.3f})  "
                  f"n_pairs={c['n_pairs']}")
        else:
            print(f"\n  [{p}]  single member: {members_str}  "
                  f"(no within-pairs)")

    # === (B) Cross-partition separation ==========================
    print()
    print("=" * 78)
    print("(B) CROSS-PARTITION SEPARATION — are partitions distinct")
    print("    from each other?")
    print("=" * 78)
    cross = cross_partition_separation(subjects, M, PROPOSED_PARTITION)
    if cross:
        print()
        for (P, Q), s in sorted(cross.items()):
            print(f"  {P:<22} <-> {Q:<22}  mean_sim={s:.3f}")
    else:
        print("  (insufficient partition members for pairwise test)")

    # === (C) Unbiased hierarchical clustering ======================
    print()
    print("=" * 78)
    print("(C) UNBIASED CLUSTERING — natural emergence without labels")
    print("=" * 78)
    sim = cosine_similarity(M)
    merges = hierarchical_cluster_from_sim(sim, subjects)
    print(f"\nMerge history (single-linkage, highest-similarity first):")
    for m in merges:
        a_str = "+".join(m["merged_a"]) if len(m["merged_a"]) <= 4 \
            else f"{len(m['merged_a'])}-cluster"
        b_str = "+".join(m["merged_b"]) if len(m["merged_b"]) <= 4 \
            else f"{len(m['merged_b'])}-cluster"
        print(f"  step {m['step']:2d}: sim={m['merge_sim']:.3f}  "
              f"merge ({a_str}) + ({b_str})")

    # === (D) Cluster stability at intermediate cuts ===============
    print()
    print("=" * 78)
    print("(D) CLUSTER STATES at falling similarity thresholds")
    print("=" * 78)
    # Reconstruct the cluster state at various cuts
    # Each merge raises the bar; below the merge similarity, the
    # subjects are in same cluster

    cuts = [0.95, 0.90, 0.80, 0.70, 0.60, 0.50, 0.40, 0.30]
    for cut in cuts:
        # Find which merges happened above this similarity
        active_clusters = [[s] for s in subjects]
        # Apply merges in order, keep those with sim > cut
        applied_merges = []
        active = {tuple(sorted(c)): list(c) for c in active_clusters}
        # Simpler: walk merges
        clusters = {i: [s] for i, s in enumerate(subjects)}
        next_id = len(subjects)
        for m in merges:
            if m["merge_sim"] < cut:
                break
            # Combine
            a_set, b_set = set(m["merged_a"]), set(m["merged_b"])
            # Find cluster ids holding these
            keys_to_remove = []
            for k, members in clusters.items():
                mset = set(members)
                if mset.issubset(a_set | b_set) and mset:
                    keys_to_remove.append(k)
            new_members = []
            for k in keys_to_remove:
                new_members.extend(clusters.pop(k))
            new_members = sorted(set(new_members))
            clusters[next_id] = new_members
            next_id += 1
        # Print
        n_clusters = len(clusters)
        print(f"\n  Cut sim={cut:.2f}: {n_clusters} clusters")
        for cid in sorted(clusters, key=lambda k: -len(clusters[k])):
            ms = clusters[cid]
            if len(ms) > 1:
                print(f"    {{{', '.join(ms)}}}")
            else:
                print(f"    [{ms[0]}]")

    # === (E) Match to proposed partitions =========================
    print()
    print("=" * 78)
    print("(E) NATURAL CLUSTERS vs PROPOSED PARTITIONS — match?")
    print("=" * 78)
    print()

    # At what similarity cut does each proposed partition appear as a
    # single cluster? Find that threshold per partition.
    partition_members = {}
    for s, p in PROPOSED_PARTITION.items():
        if p is None:
            continue
        partition_members.setdefault(p, []).append(s)

    for p, members in partition_members.items():
        if len(members) < 2:
            print(f"  [{p}] {members[0]}  — single member, can't test")
            continue
        # Find the merge step where ALL members are in a single cluster
        # for the first time
        seen_together = False
        for m in merges:
            combined = set(m["result"])
            if set(members).issubset(combined):
                seen_together = True
                # Check if this cluster contains ONLY these members
                # (clean partition) or includes others (impure)
                extra = combined - set(members)
                purity = len(members) / len(combined)
                print(f"  [{p}] members={members}")
                print(f"    first-united at sim={m['merge_sim']:.3f}  "
                      f"cluster_size={len(combined)}  purity={purity:.2f}")
                if extra:
                    print(f"    impurities at union: {sorted(extra)}")
                break
        if not seen_together:
            print(f"  [{p}] NEVER united in any cluster")

    # Save
    out_path = Path(__file__).parent / "R-RBS-LM-91_relabel_results.json"
    with open(out_path, "w") as f:
        json.dump({
            "proposed_partition": {k: v for k, v in PROPOSED_PARTITION.items()},
            "within_coherence": coherence,
            "cross_separation": {f"{P}|{Q}": s for (P, Q), s in cross.items()},
            "merge_history": merges,
        }, f, indent=2)
    print(f"\nResults saved: {out_path}")


if __name__ == "__main__":
    main()
