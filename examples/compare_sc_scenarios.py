from tires import tire_compounds
from external_factors import SafetyCar
from stochastic_dp import best_strategy_stochastic_dp
from dynamic_programming import best_strategy_dynamic_programming


def main():
    """
    Compare the strategy found by the stochastic DP under three different safety car risk levels 
    (unlikely, moderately likely, very likely), against the deterministic DP (no safety car risk) as a baseline.

    For each scenario, p_start is the per-lap probability that a safety car starts, and p_end is the per-lap 
    probability that an active safety car ends (implying an average duration of 1 / p_end laps).
    """
    race_length = 50

    baseline_strategy, baseline_time = best_strategy_dynamic_programming(race_length, tire_compounds)

    scenarios = {
        "Unlikely safety car": SafetyCar(p_start=0.005, p_end=0.33),
        "Moderately likely safety car": SafetyCar(p_start=0.02, p_end=0.33),
        "Very likely safety car": SafetyCar(p_start=0.08, p_end=0.33),
    }

    print(f"{'Scenario':<32}{'Expected time (s)':<19}{'vs. baseline':<14}{'Strategy'}")
    print("-" * 120)
    print(f"{'No safety car risk (baseline)':<32}{baseline_time:<19.2f}{'—':<14}{baseline_strategy}")

    for label, safety_car in scenarios.items():
        strategy, expected_time = best_strategy_stochastic_dp(race_length, tire_compounds, safety_car)
        delta = expected_time - baseline_time
        print(f"{label:<32}{expected_time:<19.2f}{'+' + f'{delta:.2f}':<14}{strategy}")

    print("\nSafety car risk parameters used:")
    for label, safety_car in scenarios.items():
        print(f"  {label}: {safety_car}")


if __name__ == "__main__":
    main()