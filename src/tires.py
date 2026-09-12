import math

class Tire:
  """
  Represent a tire compound with its base pace and its degradation behavior.

  Degradation is linear up to `cliff_lap`, then switches to a steeper
  linear rate (`cliff_degradation_rate`) to model the tire "falling off
  a cliff" after too many laps of wear.
  """
  
  def __init__(self, compound, base_laptime, degradation_rate, cliff_lap = math.inf, cliff_degradation_rate = 0):
    """
    Initialize a tire compound.

    Args:
      compound (str): tire type, e.g. "SOFT", "MEDIUM", "HARD".
      base_laptime (float): lap time on a fresh tire, in seconds.
      degradation_rate (float): time lost per lap of tire wear, in seconds/lap.
      cliff_lap (int): tire age (in laps) at which degradation switches to the steeper cliff rate.
      cliff_degradation_rate (float): time lost per lap of tire wear after the cliff, in second/lap.
    """
    self.compound = compound
    self.base_laptime = base_laptime
    self.degradation_rate = degradation_rate
    self.cliff_lap = cliff_lap
    self.cliff_degradation_rate = cliff_degradation_rate
  
  def laptime_on_lap(self, tyre_age):
      """
      Compute the lap time given the tire's current age.

      Args:
          tyre_age (int): number of laps completed on this tire.

      Returns:
          float: lap time in seconds.
      """
      if tyre_age <= self.cliff_lap:
        return self.base_laptime + self.degradation_rate * tyre_age
      else:
        return self.base_laptime + self.cliff_lap*self.degradation_rate + self.cliff_degradation_rate*(tyre_age - self.cliff_lap)

tire_compounds = {
  "SOFT": Tire("SOFT", 90.0, 0.15, cliff_lap=12, cliff_degradation_rate=0.45),
  "MEDIUM": Tire("MEDIUM", 91.0, 0.08, cliff_lap=22, cliff_degradation_rate=0.25),
  "HARD": Tire("HARD", 92.0, 0.04, cliff_lap=35, cliff_degradation_rate=0.12),
}
