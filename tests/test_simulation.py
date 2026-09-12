from tires import Tire
from strategy import Stint, Strategy
from simulation import simulate_race


def test_single_stint_no_degradation_no_pit_stop():
    tire_compounds = {"soft": Tire("soft", base_laptime=90.0, degradation_rate=0.0)}
    strategy = Strategy(stints=[Stint("soft", 10)])
    total_time = simulate_race(strategy, tire_compounds, pit_stop_loss=22.0, fuel_burn_gain_per_lap=0.0)
    assert total_time == 90.0 * 10


def test_two_stints_add_pit_stop_loss_once():
    tire_compounds = {
        "soft": Tire("soft", base_laptime=90.0, degradation_rate=0.0),
        "medium": Tire("medium", base_laptime=91.0, degradation_rate=0.0),
    }
    strategy = Strategy(stints=[Stint("soft", 10), Stint("medium", 10)])
    total_time = simulate_race(strategy, tire_compounds, pit_stop_loss=22.0, fuel_burn_gain_per_lap=0.0)
    expected = 90.0 * 10 + 91.0 * 10 + 22.0
    assert total_time == expected


def test_degradation_is_applied_within_a_stint():
    tire_compounds = {"soft": Tire("soft", base_laptime=90.0, degradation_rate=1.0)}
    strategy = Strategy(stints=[Stint("soft", 3)])
    # laps at tire_age 0, 1, 2 -> 90 + 91 + 92
    total_time = simulate_race(strategy, tire_compounds, pit_stop_loss=22.0, fuel_burn_gain_per_lap=0.0)
    assert total_time == 90.0 + 91.0 + 92.0


def test_fuel_effect_reduces_total_time():
    tire_compounds = {"soft": Tire("soft", base_laptime=90.0, degradation_rate=0.0)}
    strategy = Strategy(stints=[Stint("soft", 10)])
    time_without_fuel = simulate_race(strategy, tire_compounds, pit_stop_loss=22.0, fuel_burn_gain_per_lap=0.0)
    time_with_fuel = simulate_race(strategy, tire_compounds, pit_stop_loss=22.0, fuel_burn_gain_per_lap=0.05)
    assert time_with_fuel < time_without_fuel

if __name__ == "__main__":
    test_single_stint_no_degradation_no_pit_stop()
    test_two_stints_add_pit_stop_loss_once()
    test_degradation_is_applied_within_a_stint()
    test_fuel_effect_reduces_total_time()
    print("All tests passed.")