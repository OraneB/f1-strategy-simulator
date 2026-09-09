import time
from tires import tire_compounds
from brute_force import generate_strategies, find_best_strategy
from dynamic_programming import best_strategy_dynamic_programming
from simulation import simulate_race


def compare_brute_force_vs_dp(race_length, tire_compounds, max_n_stops=4, min_stint_length=5, pit_stop_loss=22.0, fuel_burn_gain_per_lap=0.05):
    """
    Compare brute-force search (for a range of n_stops) against the
    dynamic programming approach: best time found, computation time,
    and the resulting strategy for each method. Also checks that the
    DP's returned strategy, when re-simulated independently, gives back
    the same time it claims to achieve.

    Args:
        race_length (int): total number of laps in the race.
        tire_compounds (dict): mapping from compound name to Tire instance.
        max_n_stops (int): largest number of pit stops to test with brute-force.
        min_stint_length (int): minimum stint length allowed.
        pit_stop_loss (float): time penalty per pit stop, in seconds.
        fuel_burn_gain_per_lap (float): time saved per lap already completed
            in the race, in seconds/lap, due to fuel burn.
    """
    compounds = list(tire_compounds.keys())

    print(f"{'Method':<25}{'Best time (s)':<16}{'Compute time (s)':<20}{'Strategy'}")
    print("-" * 110)

    for n_stops in range(1, max_n_stops + 1):
        start = time.time()
        strategies = generate_strategies(race_length, compounds, n_stops=n_stops, min_stint_length=min_stint_length)
        best_strategy, best_time = find_best_strategy(
            strategies, tire_compounds, pit_stop_loss=pit_stop_loss,
            fuel_burn_gain_per_lap=fuel_burn_gain_per_lap
        )
        elapsed = time.time() - start
        print(f"{'Brute force (' + str(n_stops) + ' stops)':<25}{best_time:<16.2f}{elapsed:<20.4f}{best_strategy}")

    start = time.time()
    dp_strategy, dp_time = best_strategy_dynamic_programming(
        race_length, tire_compounds, min_stint_length=min_stint_length,
        pit_stop_loss=pit_stop_loss, fuel_burn_gain_per_lap=fuel_burn_gain_per_lap
    )
    elapsed = time.time() - start
    print(f"{'Dynamic programming':<25}{dp_time:<16.2f}{elapsed:<20.4f}{dp_strategy}")

    print("\nConsistency check:")
    resimulated_time = simulate_race(
        dp_strategy, tire_compounds, pit_stop_loss=pit_stop_loss,
        fuel_burn_gain_per_lap=fuel_burn_gain_per_lap
    )
    print(f"Re-simulating DP's strategy independently gives: {resimulated_time:.2f}s (should match {dp_time:.2f}s)")


if __name__ == "__main__":
    compare_brute_force_vs_dp(race_length=50, tire_compounds=tire_compounds, max_n_stops=4)