from circuit_profiles import CIRCUIT_PROFILES
from dynamic_programming import best_strategy_dynamic_programming
from stochastic_dp import best_strategy_stochastic_dp


def main():
    """
    For each calibrated circuit profile, compute the optimal strategy
    both ignoring safety car risk (deterministic DP) and accounting for
    that circuit's own calibrated safety car risk (stochastic DP), and
    print a comparison.
    """
    print(f"{'Circuit':<12}{'Race length':<14}{'Best time (s)':<16}{'Expected time w/ SC (s)':<24}{'Strategy (w/ SC)'}")
    print("-" * 120)

    for circuit_name, profile in CIRCUIT_PROFILES.items():
        deterministic_strategy, deterministic_time = best_strategy_dynamic_programming(
            race_length=profile["race_length"],
            tire_compounds=profile["tire_compounds"],
            pit_stop_loss=profile["pit_stop_loss"],
            fuel_burn_gain_per_lap=profile["fuel_burn_gain_per_lap"],
        )

        stochastic_strategy, expected_time = best_strategy_stochastic_dp(
            race_length=profile["race_length"],
            tire_compounds=profile["tire_compounds"],
            safety_car=profile["safety_car"],
            pit_stop_loss=profile["pit_stop_loss"],
            fuel_burn_gain_per_lap=profile["fuel_burn_gain_per_lap"],
        )

        print(f"{circuit_name:<12}{profile['race_length']:<14}{deterministic_time:<16.2f}"
              f"{expected_time:<24.2f}{stochastic_strategy}")

    print("\n'Best time' ignores safety car risk entirely (deterministic DP).")
    print("'Expected time w/ SC' accounts for that circuit's own calibrated safety car risk (stochastic DP).")


if __name__ == "__main__":
    main()