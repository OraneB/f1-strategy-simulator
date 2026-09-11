import math
from strategy import Stint, Strategy, is_valid_strategy
from simulation import simulate_race
from functools import lru_cache

def best_strategy_stochastic_dp(race_length, tire_compounds, safety_car, pit_stop_loss = 22.0, fuel_burn_gain_per_lap = 0.05):
    """
    Find the strategy minimising expected race time, accounting for therisk of a safety car period occurring at any 
        point during the race.

    It minimises the expected total time, where the expectation is taken over the probabilistic safety car model 
    (a two-state Markov process, see SafetyCar).

    Args:
        race_length (int): total number of laps in the race.
        tire_compounds (dict): mapping from compound name to Tire instance.
        safety_car (SafetyCar): probabilistic safety car model (p_start, p_end, sc_laptime, sc_pit_stop_loss).
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
            continue_time, continue_strategy = dynamic_programming(current_lap + 1, compound, tire_age, compounds_used, True)
            end_time, end_strategy = dynamic_programming(current_lap + 1, compound, tire_age, compounds_used, False)
            expected_time = safety_car.laptime + safety_car.p_end * end_time + (1 - safety_car.p_end) * continue_time - fuel_burn_gain_per_lap * current_lap
            best_option = (expected_time, continue_strategy if safety_car.p_end < 1 - safety_car.p_end else end_strategy)
            for new_compound in tire_compounds:
                new_compounds_used = compounds_used | frozenset({new_compound})
                continue_time, continue_strategy = dynamic_programming(current_lap + 1, new_compound, 1, new_compounds_used, True)
                end_time, end_strategy = dynamic_programming(current_lap + 1, new_compound, 1, new_compounds_used, False)
                expected_time = safety_car.laptime + safety_car.p_end * end_time + (1 - safety_car.p_end) * continue_time + safety_car.sc_pit_stop_loss - fuel_burn_gain_per_lap * current_lap
                strategy_with_pit_stop = [Stint(compound=compound, laps=tire_age)] + (continue_strategy if safety_car.p_end < 1 - safety_car.p_end else end_strategy)
                if expected_time < best_option[0]:
                    best_option = (expected_time, strategy_with_pit_stop)
        else:
            continue_time, continue_strategy = dynamic_programming(current_lap + 1, compound, tire_age + 1, compounds_used, False)
            start_time, start_strategy = dynamic_programming(current_lap + 1, compound, tire_age + 1, compounds_used, True)
            expected_time = tire_compounds[compound].laptime_on_lap(tire_age) - fuel_burn_gain_per_lap * current_lap + safety_car.p_start * start_time + (1 - safety_car.p_start) * continue_time
            best_option = (expected_time, continue_strategy if safety_car.p_start < 1 - safety_car.p_start else start_strategy)
            for new_compound in tire_compounds:
                new_compounds_used = compounds_used | frozenset({new_compound})
                continue_time, continue_strategy = dynamic_programming(current_lap + 1, new_compound, 1, new_compounds_used, False)
                start_time, start_strategy = dynamic_programming(current_lap + 1, new_compound, 1, new_compounds_used, True)
                expected_time = tire_compounds[new_compound].laptime_on_lap(0) - fuel_burn_gain_per_lap * current_lap + pit_stop_loss + safety_car.p_start * start_time + (1 - safety_car.p_start) * continue_time
                strategy_with_pit_stop = [Stint(compound=compound, laps=tire_age)] + (continue_strategy if safety_car.p_start < 1 - safety_car.p_start else start_strategy)
                if expected_time < best_option[0]:
                    best_option = (expected_time, strategy_with_pit_stop)
        return best_option

    best_time = math.inf
    best_stints = []
    for starting_compound in tire_compounds:
        time, stints = dynamic_programming(0, starting_compound, 0, frozenset({starting_compound}), False)
        if time < best_time:
            best_time = time
            best_stints = stints

    best_strategy = Strategy(stints=best_stints)
    return best_strategy, best_time
    