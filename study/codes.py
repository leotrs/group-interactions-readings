"""Bits for writing down who met whom in a record: the structure part of the message
length.

The codes follow Proposition 7 of Rommens et al. (2026), extended to groups of mixed
sizes. A second graph code names cliques instead of pairs (their p. 18); the paper's
results hold under both. The codes count who met whom, not when, so the times in a
record are not coded.
"""

from collections import Counter, defaultdict
from itertools import combinations
from math import comb, lgamma, log, log2


def log2_comb(a, b):
    """log2 of (a choose b), computed without forming the large integer."""
    return (lgamma(a + 1) - lgamma(b + 1) - lgamma(a - b + 1)) / log(2)


def graph_bits(n, m):
    """Name the m pairs that met among the (n choose 2) possible ones, after stating m."""
    pairs = comb(n, 2)
    return log2(pairs + 1) + log2_comb(pairs, m)


def hypergraph_bits(n, hyperedges):
    """State the largest group size, then for each size k the number M_k of groups of
    that size and which of the (n choose k) possible groups they are."""
    counts = Counter(len(e) for e in hyperedges)
    bits = log2(n)
    for k in range(2, max(counts) + 1):
        subsets = comb(n, k)
        bits += log2(subsets + 1) + log2_comb(subsets, counts.get(k, 0))
    return bits


def clique_cover(edges) -> set:
    """Cliques of the graph that together contain every edge, found greedily: start
    from an edge not yet covered and add common neighbors, preferring those that cover
    the most uncovered edges."""
    adj = defaultdict(set)
    for i, j in edges:
        adj[i].add(j)
        adj[j].add(i)
    uncovered = {tuple(sorted(e)) for e in edges}
    cover = set()
    for e in sorted(uncovered):
        if e not in uncovered:
            continue
        clique = set(e)
        candidates = adj[e[0]] & adj[e[1]]
        while candidates:
            v = max(sorted(candidates), key=lambda v: sum(
                tuple(sorted((u, v))) in uncovered for u in clique))
            clique.add(v)
            candidates &= adj[v]
        clique = tuple(sorted(clique))
        cover.add(clique)
        uncovered -= set(combinations(clique, 2))
    return cover


def graph_clique_bits(n, edges):
    """A graph code that names the cliques of a cover, written with the hypergraph code.
    Rommens et al. (p. 18): such a code "avoids the factor, but it is then naming
    groups"."""
    return hypergraph_bits(n, clique_cover(edges)) if edges else log2(n)
