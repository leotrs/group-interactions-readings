"""Gatherings, spreading and the sensor record, written from study/SIMULATION.md (main setting)."""

import numpy as np

N_PEOPLE = 200
T_END = 3 * 8 * 3600.0
GATHER_RATE = 0.0030220
SIZE_MIN, SIZE_MAX = 2, 6
MEAN_DURATION = 900.0
N_FIRST = 24
LAM = 1.3013e-4
MU = 1.0 / 900.0
SAMPLE_DT = 20.0
DETECT_P = 0.5

WORLDS = ("pairwise", "group", "mixed")


def world_rate(world, k):
    """Adoption rate of a person who has not adopted, in a gathering with k adopters."""
    if world == "pairwise":
        return LAM * k
    if world == "group":
        return MU if k >= 2 else 0.0
    if world == "mixed":
        return 0.5 * LAM * k + (0.5 * MU if k >= 2 else 0.0)
    raise ValueError(world)


def make_gatherings(rng):
    """Return a list of (start, end, members array)."""
    free_at = np.zeros(N_PEOPLE)
    gatherings = []
    t = 0.0
    while True:
        t += rng.exponential(1.0 / GATHER_RATE)
        if t >= T_END:
            break
        free = np.flatnonzero(free_at <= t)
        if len(free) < 2:
            continue
        size = min(int(rng.integers(SIZE_MIN, SIZE_MAX + 1)), len(free))
        members = np.sort(rng.choice(free, size=size, replace=False))
        end = min(t + rng.exponential(MEAN_DURATION), T_END)
        free_at[members] = end
        gatherings.append((t, end, members))
    return gatherings


def people_met_per_day(gatherings):
    day_len = T_END / 3
    totals = []
    for d in range(3):
        met = [set() for _ in range(N_PEOPLE)]
        for s, _, m in gatherings:
            if d * day_len <= s < (d + 1) * day_len:
                for i in m:
                    met[i].update(int(j) for j in m if j != i)
        totals.append(np.mean([len(x) for x in met]))
    return float(np.mean(totals))


def spread(gatherings, world, rng):
    """Exact event-driven spreading. Returns adoption times (0 for first adopters, inf if never)."""
    t_adopt = np.full(N_PEOPLE, np.inf)
    first = rng.choice(N_PEOPLE, size=N_FIRST, replace=False)
    t_adopt[first] = 0.0
    adopted = np.zeros(N_PEOPLE, dtype=bool)
    adopted[first] = True

    events = []
    for g, (s, e, _) in enumerate(gatherings):
        events.append((s, 1, g))
        events.append((e, 0, g))
    # Ends before starts at equal times, so a person is never in two gatherings at once.
    events.sort(key=lambda x: (x[0], x[1]))
    events.append((T_END, 2, -1))

    active = set()
    t = 0.0
    for t_next, kind, g in events:
        while True:
            groups = list(active)
            rates = np.empty(len(groups))
            for n, h in enumerate(groups):
                m = gatherings[h][2]
                k = int(adopted[m].sum())
                rates[n] = (len(m) - k) * world_rate(world, k)
            total = rates.sum() if len(groups) else 0.0
            if total <= 0.0:
                break
            dt = rng.exponential(1.0 / total)
            if t + dt >= t_next:
                break
            t += dt
            h = groups[rng.choice(len(groups), p=rates / total)]
            m = gatherings[h][2]
            at_risk = m[~adopted[m]]
            i = at_risk[rng.integers(len(at_risk))]
            adopted[i] = True
            t_adopt[i] = t
        t = t_next
        if kind == 1:
            active.add(g)
        elif kind == 0:
            active.discard(g)
    return t_adopt


def _components(n, pairs):
    parent = list(range(n))

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for a, b in pairs:
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[ra] = rb
    comps = {}
    for a, b in pairs:
        comps.setdefault(find(a), set()).update((a, b))
    return list(comps.values())


def make_sensor_record(gatherings, rng):
    """Return a list of contact windows (start, end, groups), one per sample with detections.

    Each group is (members array, neighbours dict person -> array of detected partners).
    """
    windows = []
    n_samples = int(np.ceil(T_END / SAMPLE_DT))
    by_sample = [[] for _ in range(n_samples)]
    for s, e, m in gatherings:
        first = int(np.ceil(s / SAMPLE_DT))
        for q in range(first, n_samples):
            ts = q * SAMPLE_DT
            if ts >= e:
                break
            by_sample[q].append(m)
    for q, present in enumerate(by_sample):
        if not present:
            continue
        ts = q * SAMPLE_DT
        groups = []
        for m in present:
            size = len(m)
            pairs = [(a, b) for a in range(size) for b in range(a + 1, size)
                     if rng.random() < DETECT_P]
            if not pairs:
                continue
            for comp in _components(size, pairs):
                nbrs = {}
                for a, b in pairs:
                    if a in comp:
                        nbrs.setdefault(int(m[a]), []).append(int(m[b]))
                        nbrs.setdefault(int(m[b]), []).append(int(m[a]))
                members = np.array(sorted(int(m[c]) for c in comp))
                groups.append((members, {k: np.array(v) for k, v in nbrs.items()}))
        if groups:
            windows.append((ts, min(ts + SAMPLE_DT, T_END), groups))
    return windows
