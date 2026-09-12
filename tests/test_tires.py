import math
from tires import Tire


def test_laptime_without_cliff_is_linear():
    tire = Tire("SOFT", base_laptime=90.0, degradation_rate=0.1)
    assert tire.laptime_on_lap(0) == 90.0
    assert tire.laptime_on_lap(10) == 91.0
    assert tire.laptime_on_lap(50) == 95.0


def test_laptime_before_cliff_matches_linear_formula():
    tire = Tire("SOFT", base_laptime=90.0, degradation_rate=0.1, cliff_lap=15, cliff_degradation_rate=0.5)
    assert tire.laptime_on_lap(0) == 90.0
    assert tire.laptime_on_lap(15) == 90.0 + 0.1 * 15


def test_laptime_after_cliff_uses_steeper_rate():
    tire = Tire("SOFT", base_laptime=90.0, degradation_rate=0.1, cliff_lap=15, cliff_degradation_rate=0.5)
    value_at_cliff = 90.0 + 0.1 * 15
    # one lap past the cliff: value_at_cliff + steeper rate * 1 lap
    assert tire.laptime_on_lap(16) == value_at_cliff + 0.5 * 1
    # three laps past the cliff
    assert tire.laptime_on_lap(18) == value_at_cliff + 0.5 * 3


def test_default_cliff_lap_is_infinite():
    tire = Tire("HARD", base_laptime=92.0, degradation_rate=0.04)
    assert tire.cliff_lap == math.inf
    # even at a very high tire age, should stay on the linear formula
    assert tire.laptime_on_lap(1000) == 92.0 + 0.04 * 1000
    
if __name__ == "__main__":
    test_laptime_without_cliff_is_linear()
    test_laptime_before_cliff_matches_linear_formula()
    test_laptime_after_cliff_uses_steeper_rate()
    test_default_cliff_lap_is_infinite()
    print("All tests passed.")