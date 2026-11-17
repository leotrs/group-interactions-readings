import numpy as np

import records
from world import Gatherings


def _two_gatherings():
    return Gatherings(np.array([0.0, 100.0]), np.array([90.0, 500.0]),
                      [np.array([0, 1, 2]), np.array([2, 3])])


def test_sensors_that_detect_every_pair_record_the_meeting_log():
    g = _two_gatherings()
    rec = records.sensors(g, 1.0, np.random.default_rng(0), 1000.0, 20.0)
    log = records.meeting_log(g)
    assert rec.edges() == log.edges()
    assert rec.hyperedges() == log.hyperedges()
    # Samples at 0, 20, ..., 80 for the first gathering, each standing for 20 s.
    first = rec.group_start < 90
    assert list(rec.group_start[first]) == [0.0, 20.0, 40.0, 60.0, 80.0]
    assert rec.group_end[first][-1] == 100.0


def test_sensors_miss_a_gathering_between_two_samples():
    g = Gatherings(np.array([1.0]), np.array([15.0]), [np.array([0, 1])])
    rec = records.sensors(g, 1.0, np.random.default_rng(0), 100.0, 20.0)
    assert rec.edges() == set() and rec.hyperedges() == set()


def test_sensor_groups_by_gathering():
    g = _two_gatherings()
    rec = records.sensors(g, 1.0, np.random.default_rng(0), 1000.0, 20.0,
                          groups="gatherings")
    assert rec.hyperedges() == {(0, 1, 2), (2, 3)}
    assert list(rec.group_start) == [0.0, 100.0]
    assert list(rec.group_end) == [100.0, 500.0]


def test_components():
    parts = records.components([(0, 1), (1, 2), (5, 6)])
    assert sorted(parts) == [(0, 1, 2), (5, 6)]


def test_delayed_adoption_times():
    t = np.array([0.0, 10.0, np.inf, 990.0])
    out = records.recorded_times(t, [0], 100.0, np.random.default_rng(0), 1000.0)
    assert out[0] == 0.0 and np.isinf(out[2])
    assert out[1] > 10.0
    assert records.recorded_times(t, [0], 0.0, None, 1000.0).tolist() == t.tolist()
