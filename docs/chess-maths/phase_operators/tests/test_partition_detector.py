"""§11.6 partition_detector tests."""
import sys
import unittest
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from partition_detector import (  # noqa: E402
    pairwise_cosine,
    detect_clusters,
    run_partition_analysis,
    per_ply_features,
    PartitionResult,
)


class TestPairwiseCosine(unittest.TestCase):
    def test_identity_rows_similarity_one(self):
        enc = np.tile(np.array([1.0, 2.0, 3.0, 4.0]), (5, 1))
        sim = pairwise_cosine(enc)
        self.assertEqual(sim.shape, (5, 5))
        np.testing.assert_allclose(sim, np.ones((5, 5)), atol=1e-12)

    def test_antipodal_rows(self):
        v = np.array([1.0, 2.0, 3.0])
        enc = np.stack([v, -v])
        sim = pairwise_cosine(enc)
        np.testing.assert_allclose(sim[0, 0], 1.0, atol=1e-12)
        np.testing.assert_allclose(sim[1, 1], 1.0, atol=1e-12)
        np.testing.assert_allclose(sim[0, 1], -1.0, atol=1e-12)
        np.testing.assert_allclose(sim[1, 0], -1.0, atol=1e-12)

    def test_zero_row_graceful(self):
        enc = np.array([[1.0, 0.0], [0.0, 0.0], [1.0, 0.0]])
        sim = pairwise_cosine(enc)
        # Zero row should produce 0 for all pairs involving it.
        self.assertEqual(sim[1, 0], 0.0)
        self.assertEqual(sim[1, 2], 0.0)
        self.assertEqual(sim[0, 2], 1.0)


class TestDetectClusters(unittest.TestCase):
    def test_single_cluster_all_ones(self):
        n = 6
        sim = np.ones((n, n))
        cluster_ids, boundaries = detect_clusters(sim, 0.9)
        np.testing.assert_array_equal(cluster_ids, np.zeros(n, dtype=int))
        self.assertEqual(boundaries, [])

    def test_no_clustering_at_high_threshold(self):
        n = 5
        sim = 0.5 * np.ones((n, n))
        np.fill_diagonal(sim, 1.0)
        cluster_ids, boundaries = detect_clusters(sim, 0.9)
        np.testing.assert_array_equal(cluster_ids, np.arange(n))
        self.assertEqual(boundaries, [0, 1, 2, 3])

    def test_two_cluster_split(self):
        # 6 plies: {0,1,2} tight at 0.95, {3,4,5} tight at 0.95, cross
        # = 0.3.
        sim = np.full((6, 6), 0.3)
        for i in range(3):
            for j in range(3):
                sim[i, j] = 0.95
        for i in range(3, 6):
            for j in range(3, 6):
                sim[i, j] = 0.95
        np.fill_diagonal(sim, 1.0)
        cluster_ids, boundaries = detect_clusters(sim, 0.8)
        np.testing.assert_array_equal(
            cluster_ids, np.array([0, 0, 0, 1, 1, 1]))
        self.assertEqual(boundaries, [2])

    def test_empty_input(self):
        sim = np.zeros((0, 0))
        cluster_ids, boundaries = detect_clusters(sim, 0.5)
        self.assertEqual(cluster_ids.shape, (0,))
        self.assertEqual(boundaries, [])


class TestPerPlyFeatures(unittest.TestCase):
    def _two_cluster_result(self):
        sim = np.full((6, 6), 0.3)
        for i in range(3):
            for j in range(3):
                sim[i, j] = 0.95
        for i in range(3, 6):
            for j in range(3, 6):
                sim[i, j] = 0.95
        np.fill_diagonal(sim, 1.0)
        cluster_ids, boundaries = detect_clusters(sim, 0.8)
        return PartitionResult(
            similarity_matrix=sim,
            cluster_ids=cluster_ids,
            boundaries=boundaries,
            threshold=0.8,
        )

    def test_boundary_distance_signs_in_cluster_split(self):
        result = self._two_cluster_result()
        # Ply 0: first in cluster 0; no previous boundary → distance
        # is next-boundary-distance = 2 (positive).
        f0 = per_ply_features(result, 0)
        self.assertEqual(f0["cluster_id"], 0)
        self.assertEqual(f0["cluster_size"], 3)
        self.assertEqual(f0["distance_to_nearest_boundary"], 2)
        # Ply 2: boundary itself → 0.
        f2 = per_ply_features(result, 2)
        self.assertEqual(f2["distance_to_nearest_boundary"], 0)
        # Ply 3: first ply in cluster 1, boundary 2 is immediately
        # behind → -1.
        f3 = per_ply_features(result, 3)
        self.assertEqual(f3["cluster_id"], 1)
        self.assertEqual(f3["distance_to_nearest_boundary"], -1)

    def test_singleton_cluster_centroid_is_one(self):
        sim = np.eye(3)  # off-diagonal 0
        cluster_ids, boundaries = detect_clusters(sim, 0.5)
        result = PartitionResult(sim, cluster_ids, boundaries, 0.5)
        f1 = per_ply_features(result, 1)
        self.assertEqual(f1["cluster_size"], 1)
        self.assertEqual(f1["similarity_to_cluster_centroid"], 1.0)

    def test_cluster_centroid_mean_of_others(self):
        result = self._two_cluster_result()
        # Ply 1 in cluster 0: mean sim with plies 0 and 2 = (0.95 +
        # 0.95)/2 = 0.95.
        f1 = per_ply_features(result, 1)
        self.assertAlmostEqual(
            f1["similarity_to_cluster_centroid"], 0.95, places=6)


class TestDeterminism(unittest.TestCase):
    def test_run_partition_analysis_deterministic(self):
        rng = np.random.default_rng(0)
        enc = rng.normal(size=(40, 16))
        a = run_partition_analysis(enc, thresholds=(0.70, 0.85, 0.95))
        b = run_partition_analysis(enc, thresholds=(0.70, 0.85, 0.95))
        for tau in a:
            np.testing.assert_array_equal(
                a[tau].cluster_ids, b[tau].cluster_ids)
            self.assertEqual(a[tau].boundaries, b[tau].boundaries)
            np.testing.assert_array_equal(
                a[tau].similarity_matrix, b[tau].similarity_matrix)


if __name__ == "__main__":
    unittest.main()
