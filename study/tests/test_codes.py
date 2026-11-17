from itertools import combinations
from math import comb, log2

import numpy as np
import pytest

import codes


def test_codes_follow_proposition_7():
    n, k, m = 1000, 4, 5
    groups = [tuple(range(k * j, k * j + k)) for j in range(m)]
    pairs = {pr for e in groups for pr in combinations(e, 2)}
    h = codes.hypergraph_bits(n, groups)
    g = codes.graph_bits(n, len(pairs))
    # Proposition 7 without the count terms, which the codes add.
    core_h = codes.log2_comb(comb(n, k), m)
    core_g = codes.log2_comb(comb(n, 2), m * comb(k, 2))
    extra_h = log2(n) + sum(log2(comb(n, j) + 1) for j in range(2, k + 1))
    assert h == pytest.approx(core_h + extra_h)
    assert g == pytest.approx(core_g + log2(comb(n, 2) + 1))
    assert core_g / core_h == pytest.approx(k - 1, rel=0.1)


def test_clique_cover_covers_every_edge_and_finds_disjoint_cliques():
    groups = {(0, 1, 2, 3), (4, 5, 6), (7, 8)}
    edges = {pr for e in groups for pr in combinations(e, 2)}
    assert codes.clique_cover(edges) == groups
    rng = np.random.default_rng(9)
    edges = {tuple(sorted(rng.choice(30, 2, replace=False))) for _ in range(120)}
    cover = codes.clique_cover(edges)
    assert {pr for c in cover for pr in combinations(c, 2)} >= edges
    assert all(pr in edges for c in cover for pr in combinations(c, 2))
