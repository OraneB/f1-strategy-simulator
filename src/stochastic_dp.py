import math
from strategy import Stint, Strategy, is_valid_strategy
from simulation import simulate_race
from functools import lru_cache


def best_strategy_stochastic_dp(race_length, tire_compounds, safety_car, pit_stop_loss=22.0, fuel_burn_gain_per_lap=0.05):
    """
    Find the strategy minimising expected race time, accounting for the risk of a safety car period occurring at any
        point during the race.

    It minimises the expected total time, where the expectation is taken over the probabilistic safety car model
    (a two-state Markov process, see SafetyCar).

    Args:
        race_length (int): total number of laps in the race.
        tire_compounds (dict): mapping from compound name to Tire instance.
        safety_car (SafetyCar): probabilistic safety car model (p_start, p_end, laptime, sc_pit_stop_loss).
        pit_stop_loss (float): time penalty for a pit stop under normal racing conditions, in seconds. Defaults
            to 22.0.
        fuel_burn_gain_per_lap (float): time saved per lap already completed in the race, in seconds/lap, due
            to fuel burn. Defaults to 0.05.
    Returns:
        tuple: (best_strategy, expected_time), where best_strategy is the Strategy object minimising expected
            race time, and expected_time is that expected time in seconds.
    """

    @lru_cache(maxsize=None)
    def dynamic_programming(current_lap, compound, tire_age, compounds_used: frozenset, sc_active: bool):
        if current_lap == race_length:
            if len(compounds_used) >= 2:
                return (0, [Stint(compound=compound, laps=tire_age)])
            else:
                return (math.inf, [])

        if sc_active:
            p_switch, p_stay = safety_car.p_end, 1 - safety_car.p_end
        else:
            p_switch, p_stay = safety_car.p_start, 1 - safety_car.p_start

        def branch_costs(next_compound, next_tire_age, next_compounds_used):
            """
            Explore the two possible outcomes for the next lap (safety car state switches, or stays as-is), 
            only recursing into a branch when its probability is non-zero. This avoids ever exploring an 
            unreachable branch, both for performance (an entire subtree xan be skipped when a probability is 
            exactly 0) and correctness (a zero-probability branch never contributes to the expected time, 
            even if its value happens to be infinite/undefined).
            """
            if p_switch > 0:
                switch_time, switch_strategy = dynamic_programming(current_lap + 1, next_compound, next_tire_age, next_compounds_used, not sc_active)
                switch_contribution = p_switch * switch_time
            else:
                switch_time, switch_strategy = math.inf, []
                switch_contribution = 0.0

            if p_stay > 0:
                stay_time, stay_strategy = dynamic_programming(current_lap + 1, next_compound, next_tire_age, next_compounds_used, sc_active)
                stay_contribution = p_stay * stay_time
            else:
                stay_time, stay_strategy = math.inf, []
                stay_contribution = 0.0

            expected = switch_contribution + stay_contribution
            chosen_strategy = switch_strategy if p_switch >= p_stay else stay_strategy
            return expected, chosen_strategy

        fuel_term = -fuel_burn_gain_per_lap * current_lap

        if sc_active:
            expected_time, chosen_strategy = branch_costs(compound, tire_age, compounds_used)
            expected_time += safety_car.laptime + fuel_term
        else:
            expected_time, chosen_strategy = branch_costs(compound, tire_age + 1, compounds_used)
            expected_time += tire_compounds[compound].laptime_on_lap(tire_age) + fuel_term

        for new_compound in tire_compounds:
            new_compounds_used = compounds_used | frozenset({new_compound})
            pit_expected_time, pit_chosen_strategy = branch_costs(new_compound, 1, new_compounds_used)

            if sc_active:
                pit_expected_time += safety_car.laptime + safety_car.sc_pit_stop_loss + fuel_term
            else:
                pit_expected_time += tire_compounds[new_compound].laptime_on_lap(0) + pit_stop_loss + fuel_term

            strategy_with_pit_stop = [Stint(compound=compound, laps=tire_age)] + pit_chosen_strategy
            if pit_expected_time < expected_time:
                expected_time = pit_expected_time
                chosen_strategy = strategy_with_pit_stop

        return expected_time, chosen_strategy

    best_time = math.inf
    best_stints = []
    for starting_compound in tire_compounds:
        time, stints = dynamic_programming(0, starting_compound, 0, frozenset({starting_compound}), False)
        if time < best_time:
            best_time = time
            best_stints = stints

    best_strategy = Strategy(stints=best_stints)
    return best_strategy, best_time
