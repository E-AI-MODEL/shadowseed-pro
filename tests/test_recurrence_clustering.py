"""Product tests for cluster-based recurrence."""

from __future__ import annotations

import numpy as np

from shadowseed.recurrence_clustering import (
    RecurrenceClusterer,
    auto_calibrated_min_occurrences,
)


def test_paraphrases_cluster_unrelated_split():
    c = RecurrenceClusterer(threshold=0.6)
    a1 = np.array([1.0, 0.0, 0.0])
    a2 = np.array([0.9, 0.1, 0.0])
    a3 = np.array([0.85, 0.15, 0.0])
    b1 = np.array([0.0, 0.0, 1.0])
    ca = c.add("privacy", a1)
    assert c.add("datagebruik", a2) == ca
    assert c.add("vertrouwen", a3) == ca
    assert c.recurrence(ca) == 3
    cb = c.add("iets heel anders", b1)
    assert cb != ca and c.recurrence(cb) == 1


def test_bump_keeps_recurrence_separate_from_centroid_weight():
    c = RecurrenceClusterer(threshold=0.6)
    a = np.array([1.0, 0.0])
    b = np.array([0.8, 0.6])
    cid = c.add("A", a)
    assert c.add("B", b) == cid

    for _ in range(4):
        c.bump(cid)

    assert c.recurrence(cid) == 6
    assert c.centroid_counts[cid] == 2
    before = c.centroids[cid].copy()

    c_vec = np.array([1.0, 0.0])
    assert c.add("C", c_vec) == cid

    expected = (before * 2 + c_vec) / 3
    assert c.recurrence(cid) == 7
    assert c.centroid_counts[cid] == 3
    np.testing.assert_allclose(c.centroids[cid], expected)


def test_auto_calibrated_bar_clamped():
    assert auto_calibrated_min_occurrences(4) == 2
    assert auto_calibrated_min_occurrences(9) == 3
    assert auto_calibrated_min_occurrences(30) == 4
