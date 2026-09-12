from tires import Tire
from strategy import Stint, Strategy, is_valid_strategy
from brute_force import generate_strategies, find_best_strategy


def test_generated_strategies_are_all_valid():
    race_length = 30
    compounds = ["SOFT", "MEDIUM", "HARD"]
    strategies = generate_strategies(race_length, compounds, n_stops=1, min_stint_length=5)
    assert len(strategies) > 0
    for strategy in strategies:
        assert is_valid_strategy(strategy, race_length, valid_compounds=compounds, require_two_compounds=True)


def test_generated_strategies_respect_min_stint_length():
    race_length = 30
    compounds = ["SOFT", "MEDIUM"]
    strategies = generate_strategies(race_length, compounds, n_stops=1, min_stint_length=5)
    for strategy in strategies:
        for stint in strategy.stints:
            assert stint.laps >= 5


def test_find_best_strategy_picks_the_fastest_one():
    tire_compounds = {
        "SOFT": Tire("SOFT", base_laptime=90.0, degradation_rate=0.0),
        "MEDIUM": Tire("MEDIUM", base_laptime=91.0, degradation_rate=0.0),
    }
    fast_strategy = Strategy(stints=[Stint("SOFT", 25), Stint("MEDIUM", 25)])
    slow_strategy = Strategy(stints=[Stint("MEDIUM", 25), Stint("SOFT", 25)])
    # both have the same total time here (no degradation), so use a
    # clearly slower third strategy to confirm the comparison logic
    slower_strategy = Strategy(stints=[Stint("MEDIUM", 10), Stint("SOFT", 10), Stint("MEDIUM", 30)])

    best_strategy, best_time = find_best_strategy(
        [fast_strategy, slow_strategy, slower_strategy], tire_compounds, pit_stop_loss=22.0, fuel_burn_gain_per_lap=0.0
    )

    assert best_strategy in (fast_strategy, slow_strategy)
    assert best_time < 91.0 * 10 + 90.0 * 10 + 91.0 * 30 + 2 * 22.0

if __name__ == "__main__":
    test_generated_strategies_are_all_valid()
    test_generated_strategies_respect_min_stint_length()
    test_find_best_strategy_picks_the_fastest_one()
    print("All tests passed.")