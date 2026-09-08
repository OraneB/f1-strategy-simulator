from .strategy import Stint, Strategy, is_valid_strategy
from .simulation import simulate_race

def generate_compounds_sequences(n_stints, compounds):
  """
  Generate all possible compound sequences of length n_stints.

  Builds every combination of compounds for the given number of stints, without any 
  restriction (including repeated compounds back to back). Filtering for specific rules 
  (e.g. requiring at least two different compounds overall) should be done separately on 
  the result.

  Args:
    n_stints (int): number of stints in the sequence.
    compounds (list): available compound names, e.g. ["soft", "medium", "hard"].

  Returns:
    list: list of sequences, each a list of compound names of length n_stints.
  """
  
  if n_stints == 1:
    return [[c] for c in compounds]
  sequences = []
  shorter_sequences = generate_compounds_sequences(n_stints - 1, compounds)
  for seq in shorter_sequences:
    for c in compounds:
      sequences.append(seq + [c])
  return sequences
    
def generate_lap_splits(race_length, n_stints, min_stint_length):
  """
  Generate all ways to split race_length laps into n_stints stints,
  each with at least min_stint_length laps.

  Args:
    race_length (int): number of laps to split (the full race, or laps remaining when 
      called recursively).
    n_stints (int): number of stints to split the laps into.
    min_stint_length (int): minimum number of laps allowed per stint.

  Returns:
    list: list of splits, each a list of ints of length n_stints summing to race_length. 
      Empty list if no valid split exists.
  """
  
  if n_stints == 1:
    return [[race_length]] if race_length >= min_stint_length else []
  splits = []
  for first_stint_laps in range(min_stint_length, race_length - min_stint_length*(n_stints - 1) + 1):
    remaining_laps = race_length - first_stint_laps
    for rest in generate_lap_splits(remaining_laps, n_stints - 1, min_stint_length):
      splits.append([first_stint_laps] + rest)
  return splits

def generate_strategies(race_length, compounds, n_stops, min_stint_length = 5, min_two_compound = True):
  """
  Generate all valid strategies with exactly n_stops pit stops.

  Combines every valid compound sequence with every valid lap split to produce the full set 
  of candidate strategies for the given race.

  Args:
    race_length (int): total number of laps in the race.
    compounds (list): available compound names, e.g. ["soft", "medium", "hard"].
    n_stops (int): number of pit stops (number of stints is n_stops + 1).
    min_stint_length (int): minimum number of laps allowed per stint. Defaults to 5. It is a modelling choice:
      it prunes out strategies that would never be worth the pit stop time loss anyway, keeping the search space smaller.
    min_two_compound (bool): if True, only keep strategies using at least two different compounds 
      overall (F1 rule). Defaults to True.

  Returns:
    list: list of Strategy objects representing all valid candidate strategies.
  """
  strategies = []
  n_stints = n_stops + 1
  
  compound_sequences = generate_compounds_sequences(n_stints, compounds)
  if min_two_compound:
    compound_sequences = [seq for seq in compound_sequences if len(set(seq)) >= 2]
  
  lap_splits = generate_lap_splits(race_length, n_stints, min_stint_length)
  
  for compound_seq in compound_sequences:
    for lap_split in lap_splits:
      stints = [Stint(compound = c, laps = l) for c, l in zip(compound_seq, lap_split)]
      strategy = Strategy(stints = stints)
      assert(is_valid_strategy(strategy, race_length, valid_compounds=compounds, require_two_compounds=min_two_compound))
      strategies.append(strategy)
  
  return strategies

def find_best_strategy(strategies, tire_compounds, pit_stop_loss = 22.0, fuel_burn_gain_per_lap = 0.05):
  """
  Find the fastest strategy among a list of candidate strategies.

  Simulates every strategy in the list and returns the one with the
  lowest total race time, alongside that time.

  Args:
    strategies (list): list of Strategy objects to compare. The strategies must be valid.
    tire_compounds (dict): mapping from compound name (str) to its Tire instance.
    pit_stop_loss (float): time penalty for a pit stop, in seconds. Defaults to 22.0.
    fuel_burn_gain_per_lap (float): gain in fuel efficiency per lap, in seconds. Defaults to 0.05.

  Returns:
    tuple: (best_strategy, best_time), where best_strategy is the Strategy object with the lowest 
      total race time, and best_time is that time in seconds.
  """
  assert(strategies != [])
  best_strategy = strategies[0]
  best_time = simulate_race(strategies[0], tire_compounds, pit_stop_loss, fuel_burn_gain_per_lap)
  for strategy in strategies:
    time = simulate_race(strategy, tire_compounds, pit_stop_loss, fuel_burn_gain_per_lap)
    if time < best_time:
      best_time = time
      best_strategy = strategy
  return (best_strategy, best_time)  
