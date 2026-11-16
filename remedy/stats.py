"""Sufficient statistics of the event-time likelihood.

For every model fitted here the rate of a person who has not adopted depends only on
a = adopters among the person's contacts and c = adopters in the person's current group.
So the log-likelihood needs only
  H[a, c]: person-seconds at risk spent with those counts,
  D[a, c]: adoptions that happened with those counts (just before the adoption).
"""

import numpy as np

from sim import N_PEOPLE, T_END

KMAX = 7


def log_windows(gatherings):
    """On the meeting log, contacts and group are both the other members of the gathering."""
    return [(s, e, [(m, None)]) for s, e, m in gatherings]


def exposure(windows, t_adopt):
    H = np.zeros((KMAX, KMAX))
    D = np.zeros((KMAX, KMAX))
    counted = np.zeros(N_PEOPLE, dtype=bool)
    for s, e, groups in windows:
        for members, nbrs in groups:
            t_mem = t_adopt[members]
            for idx, i in enumerate(members):
                ti = t_adopt[i]
                if ti <= s:
                    continue
                stop = min(e, ti)
                others = np.delete(t_mem, idx)
                t_nb = others if nbrs is None else t_adopt[nbrs[int(i)]]
                a = int((t_nb <= s).sum())
                c = int((others <= s).sum())
                changes = [(t, 1) for t in t_nb if s < t < stop]
                changes += [(t, 0) for t in others if s < t < stop]
                changes.sort()
                t0 = s
                for t, is_nb in changes:
                    H[a, c] += t - t0
                    t0 = t
                    if is_nb:
                        a += 1
                    else:
                        c += 1
                H[a, c] += stop - t0
                if ti < e:
                    D[a, c] += 1
                    counted[i] = True
    at_risk = t_adopt > 0
    total = np.minimum(t_adopt[at_risk], T_END).sum()
    H[0, 0] += total - H.sum()
    adopters = at_risk & np.isfinite(t_adopt)
    D[0, 0] += (adopters & ~counted).sum()
    return H, D
