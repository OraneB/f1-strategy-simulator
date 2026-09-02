from dataclasses import dataclass
from typing import List

@dataclass
class Stint:
  """A single stint: one tire compound driven for a number of laps."""
  compound: str
  laps: int

@dataclass
class Strategy:
  """A full race strategy: an ordered sequence of stints."""
  stints: List[Stint]

def is_valid_strategy(strategy: Strategy, race_length: int, valid_compounds=None, require_two_compounds=True):
  """
  Check that a strategy is valid (covers exactly the full race distance, has only positive 
  stint lengths, uses only known compounds, and (optionally) uses at least two different compounds, 
  per F1 regulations.

  Args:
    strategy (Strategy): the strategy to validate.
    race_length (int): total number of laps in the race.
    valid_compounds (iterable[str] | None): set of allowed compound names. If None, compound names are not checked.
    require_two_compounds (bool): if True, require at least two distinct compounds across the strategy.
  
  Returns:
    bool: True if the strategy is valid.
  """
  total_laps = 0
  compounds_used = set()

  for stint in strategy.stints:
    if stint.laps <= 0:
      return False

    if valid_compounds is not None:
      if stint.compound not in valid_compounds:
        return False

    total_laps += stint.laps
    compounds_used.add(stint.compound)

  if total_laps != race_length:
    return False
  
  return True
