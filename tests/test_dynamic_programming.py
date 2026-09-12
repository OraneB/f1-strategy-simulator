from tires import tire_compounds
from brute_force import generate_strategies, find_best_strategy
from dynamic_programming import best_strategy_dynamic_programming
from simulation import simulate_race


def test_dp_matches_brute_force_optimal_time():
    race_length = 20  # kept small so brute-force stays fast in this test

    _, dp_time = best_strategy_dynamic_programming(race_length, tire_compounds, min_stint_length=5)

    best_brute_force_time = float("inf")
    for n_stops in (1, 2):
        strategies = generate_strategies(race_length, list(tire_compounds.keys()), n_stops=n_stops, min_stint_length=5)
        if strategies:
            _, best_time = find_best_strategy(strategies, tire_compounds)
            best_brute_force_time = min(best_brute_force_time, best_time)

    assert abs(dp_time - best_brute_force_time) < 1e-6


def test_dp_strategy_resimulates_to_the_same_time():
    race_length = 20

    dp_strategy, dp_time = best_strategy_dynamic_programming(race_length, tire_compounds, min_stint_length=5)
    resimulated_time = simulate_race(dp_strategy, tire_compounds)

    assert abs(resimulated_time - dp_time) < 1e-6

if __name__ == "__main__":
    test_dp_matches_brute_force_optimal_time()
    test_dp_strategy_resimulates_to_the_same_time()
    print("All tests passed.")