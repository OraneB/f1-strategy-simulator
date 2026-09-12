from tires import tire_compounds
from external_factors import SafetyCar
from dynamic_programming import best_strategy_dynamic_programming
from stochastic_dp import best_strategy_stochastic_dp
from simulation import simulate_race


def test_zero_safety_car_risk_matches_deterministic_dp():
    race_length = 20
    no_risk = SafetyCar(p_start=0.0, p_end=0.33)

    _, deterministic_time = best_strategy_dynamic_programming(race_length, tire_compounds)
    _, stochastic_time = best_strategy_stochastic_dp(race_length, tire_compounds, no_risk)

    assert abs(deterministic_time - stochastic_time) < 1e-6


def test_expected_time_increases_with_safety_car_risk():
    race_length = 20
    low_risk = SafetyCar(p_start=0.01, p_end=0.33)
    high_risk = SafetyCar(p_start=0.05, p_end=0.33)

    _, low_risk_time = best_strategy_stochastic_dp(race_length, tire_compounds, low_risk)
    _, high_risk_time = best_strategy_stochastic_dp(race_length, tire_compounds, high_risk)

    assert high_risk_time > low_risk_time


def test_stochastic_strategy_resimulates_close_to_expected_time():
    race_length = 20
    safety_car = SafetyCar(p_start=0.02, p_end=0.33)

    strategy, expected_time = best_strategy_stochastic_dp(race_length, tire_compounds, safety_car)
    # re-simulating without any safety car occurring should give a time
    # reasonably close to (and not wildly higher than) the expected time,
    # since the expectation already accounts for the possibility of no SC
    resimulated_time_without_sc = simulate_race(strategy, tire_compounds)

    assert resimulated_time_without_sc <= expected_time

if __name__ == "__main__":
    test_zero_safety_car_risk_matches_deterministic_dp()
    test_expected_time_increases_with_safety_car_risk()
    test_stochastic_strategy_resimulates_close_to_expected_time()
    print("All tests passed.")