import math
from .strategy import Stint, Strategy, is_valid_strategy
from .simulation import simulate_race
from functools import lru_cache

def best_strategy_dynamic_programming(race_length, tire_compounds, min_stint_length = 5, pit_stop_loss = 22.0, fuel_burn_gain_per_lap = 0.05):
    """
    This function implements a dynamic programming approach to optimize tire usage in a racing scenario.
    
    Args:
        race_length: The total number of laps in the race.
        tire_compounds: A dictionary mapping compound names to their respective Tire instances.
        min_stint_length: The minimum length of a stint before a pit stop is considered. Defaults to 5. It is a modelling choice:
            it prunes out strategies that would never be worth the pit stop time loss anyway, keeping the search space smaller.
        pit_stop_loss: The time penalty for a pit stop, in seconds. Defaults to 22.0.
        fuel_burn_gain_per_lap: The gain in fuel efficiency per lap, in seconds. Defaults to 0.05.
    Returns:
        tuple: (best_strategy, best_time), where best_strategy is the Strategy object with the lowest 
            total race time, and best_time is that time in seconds.
    """
    @lru_cache(maxsize=None)
    def dynamic_programming(current_lap, compound, tire_age, compounds_used: frozenset):
        if current_lap == race_length:
            if len(compounds_used) >= 2:
                return (0, [Stint(compound=compound, laps=tire_age)])
            else:
                return (math.inf, [])
        remaining_time, remaining_strategy = dynamic_programming(current_lap + 1, compound, tire_age + 1, compounds_used)
        best_option = (remaining_time + tire_compounds[compound].laptime_on_lap(tire_age) - fuel_burn_gain_per_lap * current_lap, remaining_strategy)
        if tire_age >= min_stint_length:
            for new_compound in tire_compounds:
                new_compounds_used = compounds_used | frozenset({new_compound})
                remaining_time, remaining_strategy = dynamic_programming(current_lap + 1, new_compound, 1, new_compounds_used)
                pit_stop_time = remaining_time + pit_stop_loss + tire_compounds[new_compound].laptime_on_lap(0) - fuel_burn_gain_per_lap * current_lap
                strategy_with_pit_stop = [Stint(compound=compound, laps=tire_age)] + remaining_strategy
                if pit_stop_time < best_option[0]:
                    best_option = (pit_stop_time, strategy_with_pit_stop)

        return best_option

    best_time = math.inf
    best_stints = []
    for starting_compound in tire_compounds:
        time, stints = dynamic_programming(0, starting_compound, 0, frozenset({starting_compound}))
        if time < best_time:
            best_time = time
            best_stints = stints

    best_strategy = Strategy(stints=best_stints)
    return best_strategy, best_time
