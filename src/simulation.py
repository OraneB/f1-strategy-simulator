def simulate_race(strategy: Strategy, tire_compounds: dict, pit_stop_loss: float = 22.0):
  """
  Simulate the total race time for a given strategy.
  
  Iterates through each stint of the strategy, summing lap times based on
  tire degradation, and adds a fixed time penalty for each pit stop
  (i.e. for every stint after the first one).
  
  Args:
      strategy (Strategy): the strategy to simulate, as an ordered list of stints.
      tire_compounds (dict): mapping from compound name (str) to its Tire instance.
      pit_stop_loss (float): time penalty for a pit stop, in seconds. Defaults to 22.0.
  
  Returns:
      float: total race time in seconds.
  """
  total_time = 0.0
  for i, stint in enumerate(strategy.stints):
    tire = tire_compounds[stint.compound]
    if i > 0:
      total_time += pit_stop_loss
    for tire_age in range(stint.laps):
      total_time += tire.laptime_on_lap(tire_age)
  return total_time
