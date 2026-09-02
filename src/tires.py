import math
from dataclasses import dataclass

class Tire:
  """Represent a tire compound with its base pace and its degradation rate"""
  
  def __init__(self, compound, base_laptime, degradation_rate):
    """
    Initialize a tire compound.

    Args:
      compound (str): tire type, e.g. "soft", "medium", "hard".
      base_laptime (float): lap time on a fresh tire, in seconds.
      degradation_rate (float): time lost per lap of tire wear, in seconds/lap.
    """
    self.compound = compound
    self.base_laptime = base_laptime
    self.degradation_rate = degradation_rate
  
  def laptime_on_lap(self, tyre_age):
      """
      Compute the lap time given the tire's current age.

      Args:
          tyre_age (int): number of laps completed on this tire.

      Returns:
          float: lap time in seconds.
      """
      return self.base_laptime + self.degradation_rate * tyre_age
